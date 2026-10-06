import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import graphing as graph
import hspice_parser as hp
import pathlib as pl
import pandas as pd
import math

class inv_chain_builder:
    def __init__(self, sp_filename:str="inv_alpha_chain_nf",
                model_path: str = "models/22nm_HP.sp",
                c_load=1e-12,
                c_min=7.321e-17, #from exercise 4
                max_n:int = 10,
                vdd=0.8,
                k=1.3):
        self.base_name = pl.Path(sp_filename).stem
        self.model_path = model_path 
        self.sp_path = f"sp/{self.base_name}.sp"
        self.mt_path = f"logs/{self.base_name}.mt0" 
        self.lis_path = f"logs/{self.base_name}.lis"
        self.vdd = vdd
        self.k = k
        self.c_load = c_load
        self.c_min = c_min
        self.M = c_load / c_min
        self.n_list, self.alpha_list = self.get_valid_alpha_n(max_n)
        self.df = pd.DataFrame(columns=['delay', 'temper', 'alter#'])

        for dir in ["logs", "graphs", "data", "md", "sp"]:
            pl.Path(dir).mkdir(parents=True, exist_ok=True)

    def get_valid_alpha_n(self, max_n_to_test):
        if self.M < 1:
            raise ValueError("Error: M must be greater than 1.")
        min_n = 3
        if (self.c_load == 1e-11) :
            min_n = 4
        n_list = list(range(min_n, max_n_to_test+1)) 
        
        alpha_list = []
        for n in n_list:
            alpha = self.M ** (1/(n+1))
            alpha_list.append(alpha)
        return n_list, alpha_list

    def get_dims(self, n, alpha):
        """Calculate continuous scaling factor for total W for each stage."""
        w_scales = []
        for i in range(n):
            w_scale = alpha ** (i + 1)
            w_scales.append(w_scale)
        return w_scales

    def calculate_fingers(self, w_scale):
        """
        Dynamically calculate required fingers based on the 220nm maximum rule.
        Returns (nf_nmos, nf_pmos).
        """
        w_n_base = 44e-9
        w_p_base = w_n_base * self.k
        
        w_n_tot = w_n_base * w_scale
        w_p_tot = w_p_base * w_scale
        
        max_finger_w = 220e-9
        
        # Ceil ensures we always have at least enough fingers so no finger > 220nm
        nf_n = max(1, math.ceil(w_n_tot / max_finger_w))
        nf_p = max(1, math.ceil(w_p_tot / max_finger_w))
        
        return nf_n, nf_p

    def get_delay_per_alpha(self):
        for i in range(len(self.alpha_list)):
            n = self.n_list[i]
            alpha = self.alpha_list[i]
            
            self.build_deck(n, alpha)
                
            subprocess.run(["hspice", self.sp_path, "-o", self.lis_path])
            df = hp.parse_mto(self.mt_path) 
            
            print(f"for alpha = {alpha:.3f} and n = {n}")
            print(df)

            self.df = pd.concat([self.df, df], ignore_index=True)
      
        print("Final Df:")
        print(self.df)
        return
    
    def build_deck(self, n, alpha):
        header = f"""Inverter Chain Using nf
.include ../{self.model_path}
.param x=5p
.param K={self.k}
V1 vdd 0 DC {self.vdd}
V2 vss 0 DC 0.0
        """
        pwl = "Vin in 0 PULSE(0.8 0 1n x x 10n 20n)\n" 
        
        # No rgatemod=0 needed. Fingers automatically put Rgate in parallel accurately.
        subckt = """
        .subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n w_scale=1 nfingers_n=1 nfingers_p=1
        .param w_p_tot='k*w_n*w_scale' 
        .param w_n_tot='w_n*w_scale'
        M1 out in vdd vdd pmos W='w_p_tot' L='l_p' nf='nfingers_p'
        M2 out in vss vss nmos W='w_n_tot' L='l_n' nf='nfingers_n'
        .ends inv\n
        """
        
        scale_list = self.get_dims(n, alpha)

        # Stage 0 (First inverter, scale = 1)
        nf_n0, nf_p0 = self.calculate_fingers(1.0)
        first_inv = f"X0 in 1 vdd vss inv k='K' w_scale=1 nfingers_n={nf_n0} nfingers_p={nf_p0}\n" 

        # Middle inverters
        middle_invs = ""
        for i in range(1, n):
            w_scale = scale_list[i-1]
            nf_n, nf_p = self.calculate_fingers(w_scale)
            next_inv = f"X{i} {i} {i+1} vdd vss inv k='K' w_scale={w_scale} nfingers_n={nf_n} nfingers_p={nf_p}\n"
            middle_invs += next_inv

        # Last inverter
        w_scale_last = scale_list[-1]
        nf_n_last, nf_p_last = self.calculate_fingers(w_scale_last)
        last_inv = f"X{n} {n} out vdd vss inv k='K' w_scale={w_scale_last} nfingers_n={nf_n_last} nfingers_p={nf_p_last}\n" 

        load = f"C0 out 0 {self.c_load}\n"
        tran = ".tran 0.1p 10n\n"

        total_invs = n + 1
        if (total_invs % 2) != 0: 
            meas = ".meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 rise=1\n"
        else:
            meas = ".meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 fall=1\n"

        footer = f"""
.option post=2 
.end\n
        """
        spice_str = header + pwl + subckt + first_inv + middle_invs + last_inv + load + tran + meas + footer
        with open(self.sp_path, 'w') as sp:
            print(spice_str, file=sp)
        return 
 
    def graph(self, graph_dir:str="graphs"):
        delay = self.df["delay"]
        delay = delay * 1e12 #convert to ps
        alpha = np.array(self.alpha_list)
        min_idx = self.df['delay'].idxmin()
        alpha_best = np.array([self.alpha_list[min_idx]])
        n_best = self.n_list[min_idx]
        delay_best = np.array([self.df['delay'].min() * 1e12])
    
        print(f"delay_best = {delay_best[0]:.2f} ps")
    
        extra_x = {f"(alpha, n) = ({alpha_best[0]:.2f},{n_best})": alpha_best}
        extra_y = {f"(alpha, n) = ({alpha_best[0]:.2f},{n_best})": delay_best}
        
        plt.figure(1)
        graph.plot_series(
            x_data=alpha,
            y_dict={"delay (ps)":delay},
            extra_x_dict=extra_x,
            extra_y_dict=extra_y,
            xlabel="alpha",
            ylabel="delay (ps)",
            title=f"Delay versus Alpha (nf-based) for C_load = {self.c_load*1e12}pf",
            filename=f"{graph_dir}/{self.base_name}.png"
        )
        plt.clf()
        return
    
    def tabulate(self, data_dir:str="data"):
        self.df.to_csv(f"{data_dir}/{self.base_name}.csv", index=False)
        md_table_str = self.df.to_markdown(index=False)
        with open (f"{data_dir}/{self.base_name}.md", 'w') as md:
            print(md_table_str, file=md)
        
        small_df = pd.DataFrame({
            "Alpha": np.array(self.alpha_list),
            "n": np.array(self.n_list),
            "Delay (ps)": self.df['delay']
        })
        print(small_df)
        small_md_str = small_df.to_markdown(index=False)
        with open(f"{data_dir}/{self.base_name}_small_table.md", 'w') as md:
            print(small_md_str, file=md)
        return

if __name__ == "__main__":
    # Test execution
    builder = inv_chain_builder(sp_filename="inv_chain_1pf_nf", model_path="models/22nm_HP.sp", c_load=1e-12, max_n=10)
    builder.get_delay_per_alpha()
    builder.graph()
    builder.tabulate()

    builder = inv_chain_builder(sp_filename="inv_chain_10pf_nf", model_path="models/22nm_HP.sp", c_load=10e-12, max_n=10)
    builder.get_delay_per_alpha()
    builder.graph()
    builder.tabulate()