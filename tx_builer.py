# pi and t line builder
import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import graphing as graph
import hspice_parser as hp
import pathlib as pl
import pandas as pd
from math import exp

class tx_builder:
    def __init__(self, sp_filename:str="tx_line",
                type:str="pi",
                R=100, C=1e-12,
                n_max:int=10,
                n_tran:int=10,
                max_time:int = 150, #ps, this default only makes sense for low tr
                rise_time:float = 5.7, #ps, how fast input pulse is 
                vdd:float = 0.8,
                vdd_ratio:float =0.63 #.632
                ):
        self.base_name = pl.Path(sp_filename).stem
        self.type = type
        self.R = R
        self.C = C
        self.n_max = n_max
        self.n_tran = n_tran
        self.max_time = max_time
        self.tr = rise_time
        self.v_trig = vdd*vdd_ratio #how full do we need to be

        self.sp_path = f"sp/{self.base_name}.sp"
        self.mt_path = f"logs/{self.base_name}.mt0"
        self.lis_path = f"logs/{self.base_name}.lis"
        self.tr0_path = f"logs/{self.base_name}.tr0"

        self.n_list = list(range(1, n_max+1))
        self.df = pd.DataFrame(columns=['delay', 'temper', 'alter#'])
        self.tr_df = pd.DataFrame(columns=['delay', 'temper', 'alter#'])
        self.tran_df = None

        for dir in ["logs", "graphs", "data", "md", "sp"]:
            pl.Path(dir).mkdir(parents=True, exist_ok=True)
        pass

    def build_deck(self, n=None, rise_time=None, max_sim_time=None): #max in ps
        if rise_time==None:
            rise_time = self.tr # keep this for fixed tr
        if n == None:
            n = 10 #keep this for fixed n
        if max_sim_time==None:
            max_sim_time = self.max_time #<--------------------only have it change if updated by tr sweep
        header = f"""* TX-line {self.type} {n} segments
V1 in 0 PULSE(0 0.8 10p {rise_time}p 5.7p {max_sim_time}p {max_sim_time}p)
.ic v(in)=0
        """
        
        pi_subckt = """
.subckt pi in out gnd R=100 C=10p
C0 in gnd c='C/2'
R0 in out r='R'
C1 out gnd c='C/2'
.ends pi
        """
        
        t_subckt = """
.subckt T in out gnd R=100 C=10p
R0 in mid r='R/2'
C0 mid gnd c='C'
R1 mid out r='R/2'
.ends T
        """
        
        if self.type == "pi":
            subckt = pi_subckt
        elif self.type == "T":
            subckt = t_subckt

        tx = ""
        seg_R = self.R / n
        seg_C = self.C / n
        
        for i in range(n):
            subckt_in = f"{i+1}"
            subckt_out = f"{i+2}"
            if i == 0: 
                subckt_in = "in"
            if i == (n-1): 
                subckt_out = "out"
            tx += f"X{i} {subckt_in} {subckt_out} 0 {self.type} R={seg_R} C={seg_C}\n"

        step_size = max(0.01, max_sim_time / 10000)
        tran = f".tran {step_size}p {max_sim_time}p\n"
        meas = f".meas tran delay trig v(in) val={self.v_trig} rise=1 targ v(out) val={self.v_trig} rise=1\n"
        
        footer = f"""
.option post=2 
.option delmax=0.01p  
*tighter tolerance
.option reltol=1e-6    
.option absv=1e-6      
.end\n
        """
        spice_str = header + subckt + tx + tran + meas + footer
        with open(self.sp_path, 'w') as sp:
            print(spice_str, file=sp)
        return

    def get_delay_per_tr(self):
        #build deck should now take in tr as a parameter
        min_t = 0.1 #.1 ps
        max_t = 1000# 1 second
        self.tr_list = np.linspace(min_t, max_t, 40)
        for tr in self.tr_list:
            self.build_deck(rise_time=tr, max_sim_time=(10 + tr + 150)) #these are entered in ps 
            subprocess.run(["hspice", self.sp_path, "-o", self.lis_path])
            tr_df = hp.parse_mto(self.mt_path)  
            tr_df['tr'] = tr #<--------------------------------in ps
            print(f"for type = {self.type} and tr = {tr}")
            print(tr_df)

            self.tr_df = pd.concat([self.tr_df, tr_df], ignore_index=True)
        
        print("Final tr Df:")
        print(self.tr_df)
        return

    def graph_delay_vs_tr(self, graph_dir:str="graphs"):
        delay = self.tr_df["delay"]
        delay = delay * 1e12 
        tr_data = (self.tr_df["tr"].to_numpy()) #<----------- in ps

        plt.figure(1)
        graph.plot_series(
            x_data=tr_data,
            y_dict={"delay (ps)": delay},
            xlabel="tr (ps)",
            ylabel="Delay (ps)",
            title=f"Delay vs. {self.type.capitalize()} Segments TX-line",
            filename=f"{graph_dir}/{self.base_name}_delay_vs_tr.png"
        )
        plt.clf()
        return


    def get_delay_per_n(self):
        for n in self.n_list:
            self.build_deck(n)
            subprocess.run(["hspice", self.sp_path, "-o", self.lis_path])
            df = hp.parse_mto(self.mt_path) 
            
            df['n'] = n
            print(f"for type = {self.type} and n = {n}")
            print(df)

            self.df = pd.concat([self.df, df], ignore_index=True)
        
        print("Final Df:")
        print(self.df)
        return

        
    def get_transient(self):
        self.build_deck(self.n_tran)
        subprocess.run(["hspice", self.sp_path, "-o", self.lis_path])
        self.tran_df = hp.parse_tr0(self.tr0_path)
        return

    def graph(self, graph_dir:str="graphs"):
        delay = self.df["delay"]
        delay = delay * 1e12 
        n_data = self.df["n"].to_numpy()
        
        rc_2 = ((self.R * self.C) / 2) * 1e12

        extra_x = {f"RC/2 (ps) = {rc_2}": np.array([1, self.n_max])}
        extra_y = {f"RC/2 (ps) = {rc_2}": np.array([rc_2, rc_2])}

        plt.figure(1)
        graph.plot_series(
            x_data=n_data,
            y_dict={"delay (ps)": delay},
            extra_x_dict=extra_x,
            extra_y_dict=extra_y,
            xlabel="n",
            ylabel="Delay (ps)",
            title=f"Delay vs. {self.type.capitalize()} Segments TX-line",
            filename=f"{graph_dir}/{self.base_name}_delay_vs_n.png"
        )
        plt.clf()
        return

    # def tran_graph_original(self, graph_dir:str="graphs"): #in ps
    #     time_ps = self.tran_df['TIME'] * 1e12
    #     y_dict = {}
    #     y_dict["V(in)"] = self.tran_df['v(in']
    #     y_dict["V(out)"] = self.tran_df['v(out']
        
    #     for i in range(2, self.n_tran):
    #         col_name = f"v({i}"
    #         if col_name in self.tran_df.columns:
    #             y_dict[f"V({i})"] = self.tran_df[col_name]

    #     max_sim_time = max(time_ps)
    #     # max_sim_time = max_time 
    #     print("max_sim_time = ", time_ps)
        
    #     extra_x = { 
    #         "0.5Vdd":  np.array([1, max_sim_time]),
    #         "0.63Vdd":  np.array([1, max_sim_time]),
    #     }
        
    #     extra_y = { 
    #         "0.5Vdd": np.array([0.4, 0.4]),
    #         "0.63Vdd":  np.array([0.504, 0.504]),
    #     }

    #     plt.figure(2)
    #     graph.plot_series(
    #         x_data=time_ps,
    #         y_dict=y_dict,
    #         # extra_x_dict=extra_x,
    #         # extra_y_dict=extra_y,
    #         xlabel="t (ps)",
    #         ylabel="V (V)",
    #         title=f"Transient Simulation for {self.type} Segment TX-line",
    #         filename=f"{graph_dir}/{self.base_name}_tran.png"
    #     )
    #     plt.clf()
    #     return

    def tabulate(self, data_dir:str="data"):
        self.df.to_csv(f"{data_dir}/{self.base_name}.csv", index=False)
        md_table_str = self.df.to_markdown(index=False)
        with open (f"{data_dir}/{self.base_name}.md", 'w') as md:
            print(md_table_str, file=md)
        
        small_df = pd.DataFrame({
            "n": self.df['n'],
            "Delay (ps)": self.df['delay'] * 1e12
        })
        print(small_df)
        small_md_str = small_df.to_markdown(index=False)
        with open(f"{data_dir}/{self.base_name}_small_table.md", 'w') as md:
            print(small_md_str, file=md)
        return

    def tabulate_tr(self, data_dir:str="data"):
        small_df = pd.DataFrame({
            "tr": self.tr_df['tr'],
            "Delay (ps)": self.tr_df['delay'] * 1e12
        })
        print(small_df)
        small_md_str = small_df.to_markdown(index=False)
        with open(f"{data_dir}/{self.base_name}_delay_vs_tr.md", 'w') as md:
            print(small_md_str, file=md)
        return

    #trying to make a special graph
    def tran_graph(self, graph_dir:str="graphs", include_extras:bool=True, x_limit:int=160):
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        
        time_ps = self.tran_df['TIME'] * 1e12
        max_sim_time = max(time_ps)
        
        #Theoretical V_rc Step Response using elmore delay
        Vs = 0.8    
        tau = (self.R * self.C * 1e12) / 2  
        
        # Based on PULSE(0 0.8 10p 5.7p ...), the step begins at 10ps. 
        # Shift x_0 by half the rise time (5.7ps / 2 = 2.85ps) for a fair comparison
        x_0 = 10.0 + (5.7 / 2.0) 
        
        # y_vs = Vs * (1 - e^(-t/tau))
        y_vs = np.where(time_ps < x_0, 0, Vs * (1 - np.exp(-(time_ps - x_0) / tau)))

        plt.figure(figsize=(8, 6), dpi=300)

        # Plot V(in) solid vlack
        plt.plot(time_ps, self.tran_df['v(in'], color='black', linestyle='-', 
                 linewidth=2.5, marker='o', markevery=max(1, len(time_ps)//20), 
                 label='V(in)', zorder=10)

        # intermediate nodes with gradient and dotted lines
        num_intermediates = self.n_tran - 2 # e.g., nodes 2 through 9
        
        # Create a colormap sequence. Greys(0.8) is dark, Greys(0.3) is light
        # This will make V(2) dark and fade to a lighter grey at V(9)
        colors = cm.Greys(np.linspace(0.8, 0.3, num_intermediates))

        for idx, i in enumerate(range(2, self.n_tran)):
            col_name = f"v({i}"
            if col_name in self.tran_df.columns:
                plt.plot(time_ps, self.tran_df[col_name], 
                         color=colors[idx], 
                         linestyle=':',     # Small dotted lines
                         linewidth=2,
                         label=f'V({i})', zorder=5)

        # Plot V(out) - Solid dark grey with square markers
        plt.plot(time_ps, self.tran_df['v(out'], color='#404040', linestyle='-', 
                 linewidth=2.5, marker='s', markevery=max(1, len(time_ps)//20), 
                 label='V(out)', zorder=9)

        if include_extras:
            # Plot Theoretical V_RC - Solid Red line
            plt.plot(time_ps, y_vs, color='red', linestyle='-', linewidth=2.5, 
                    label='V_RC(t) Eq.', zorder=11)

            # Horizontal reference lines
            # plt.axhline(0.4, color='#d95f02', linestyle='--', label='0.5Vdd', zorder=1)
            plt.axhline(0.504, color='#0072b2', linestyle='--', label='0.63Vdd', zorder=1)

        # Formatting to match your style
        plt.xlabel("t (ps)", fontweight='bold')
        plt.ylabel("V (V)", fontweight='bold')
        plt.title(f"Transient Simulation for {self.type.capitalize()} Segment TX-line", fontweight='bold')
        plt.grid(True, linestyle=':', alpha=0.7)
        
        # Create a nice legend
        plt.legend(loc='lower right', framealpha=1.0, edgecolor='black', fontsize=9)
        
        # Lock the axes so you can see the ramp up clearly (adjust limits as needed)
        plt.xlim(-5, x_limit)
        plt.ylim(-0.04, 0.84)
        
        plt.tight_layout()
        plt.savefig(f"{graph_dir}/{self.base_name}_tran.png")
        plt.clf()
        return


    
if __name__ == "__main__":
    R = 100
    C = 1e-12
    n_max = 10
    n_tran = 10

    # rise time = 5.7 ps, sim time = 150ps, vdd ratio = 0.63, graph these
    pi_builder = tx_builder(sp_filename="pi_tx_chain", type="pi", n_max=n_max, n_tran=n_tran, R=R, C=C, 
                            vdd_ratio=0.63) #testing with tr=2
    # pi_builder.get_delay_per_n()
    # pi_builder.get_transient()
    # pi_builder.graph()
    # pi_builder.tran_graph()
    # pi_builder.tabulate()

 
    t_builder = tx_builder(sp_filename="t_tx_chain", type="T", n_max=n_max, n_tran=n_tran, R=R, C=C,
                            vdd_ratio=0.63)
    # t_builder.get_delay_per_n()
    # t_builder.get_transient()
    # t_builder.graph()
    # t_builder.tran_graph()
    # t_builder.tabulate()

 
    # don't graph just get delay for vdd_ratio = 0.5
    pi_builder = tx_builder(sp_filename="pi_tx_chain_half", type="pi", n_max=n_max, n_tran=n_tran, R=R, C=C, 
                            vdd_ratio=0.5)
    # pi_builder.get_delay_per_n()
    # pi_builder.get_transient()
    # pi_builder.tabulate()

    #added for last experiment 
    pi_builder.get_delay_per_tr()
    pi_builder.graph_delay_vs_tr()
    pi_builder.tabulate_tr()

    t_builder = tx_builder(sp_filename="t_tx_chain_half", type="T", n_max=n_max, n_tran=n_tran, R=R, C=C,
                            vdd_ratio=0.5)
    # t_builder.get_delay_per_n()
    # t_builder.get_transient()
    # t_builder.tabulate()

    # added for one last experiment
    t_builder.get_delay_per_tr()
    t_builder.graph_delay_vs_tr()
    t_builder.tabulate_tr()

    # # making rise time >> tr
    # # try 200 ps
    # hi_tr_pi_builder = tx_builder(sp_filename="pi_tx_chain_hi_tr", type="pi",n_max=n_max, n_tran=n_tran, R=R, C=C, 
    #                         max_time=500, rise_time=200)
    # hi_tr_pi_builder.get_delay_per_n()
    # hi_tr_pi_builder.get_transient()
    # hi_tr_pi_builder.graph()
    # hi_tr_pi_builder.tran_graph(include_extras=False, x_limit=300)
    # hi_tr_pi_builder.tabulate()

    # hi_tr_t_builder = tx_builder(sp_filename="t_tx_chain_hi_tr", type="T", n_max=n_max, n_tran=n_tran, R=R, C=C,
    #                              max_time=500, rise_time=200)
    # hi_tr_t_builder.get_delay_per_n()
    # hi_tr_t_builder.get_transient()
    # hi_tr_t_builder.graph()
    # hi_tr_t_builder.tran_graph(include_extras=False, x_limit=300)
    # hi_tr_t_builder.tabulate()