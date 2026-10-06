import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import graphing as graph
import hspice_parser as hp
import pathlib as pl
import pandas as pd

class inv_chain_builder:
    def __init__(self, sp_filename:str="inv_alpha_chain_scale_w.sp",
                model_path: str = "models/22nm_no.sp",
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

    # Renamed and modified to return scaling factors for W
    def get_dims(self, n, alpha):
        w_scales = []
        for i in range(n):
            w_scale = alpha ** (i + 1)
            w_scales.append(w_scale)
        return w_scales

    def get_delay_per_alpha(self):
        for i in range(len(self.alpha_list)):
            n = self.n_list[i]
            alpha = self.alpha_list[i]
            
            self.build_deck(n, alpha)
                
            subprocess.run(["hspice", self.sp_path, "-o", self.lis_path])
            df = hp.parse_mto(self.mt_path) 
            
            print(f"for alpha = {alpha} and n ={n}")
            print(df)

            self.df = pd.concat([self.df, df], ignore_index=True)
      
        print("Final Df:")
        print(self.df)
        return
    
    def build_deck(self, n, alpha):
        header = f"""Inverter Chain
.include ../{self.model_path}
.param x=5p
.param K={self.k}
V1 vdd 0 DC {self.vdd}
V2 vss 0 DC 0.0
        """
        pwl = "Vin in 0 PULSE(0.8 0 1n x x 10n 20n)\n" 
        
        # Scales W via w_scale parameter. Sets rgatemod=0 onto the instance level.
        subckt = """
        .subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n w_scale=1
        .param w_p_scaled='k*w_n*w_scale' 
        .param w_n_scaled='w_n*w_scale'
        M1 out in vdd vdd pmos W='w_p_scaled' L='l_p' rgatemod=0
        M2 out in vss vss nmos W='w_n_scaled' L='l_n' rgatemod=0
        .ends inv\n
        """
        
        scale_list = self.get_dims(n, alpha)

        first_inv = f"X0 in 1 vdd vss inv k='K' w_scale=1\n" 

        middle_invs = ""
        for i in range(1, n):
            w_scale = scale_list[i-1]
            next_inv = f"X{i} {i} {i+1} vdd vss inv k='K' w_scale={w_scale}\n"
            middle_invs += next_inv

        last_inv = f"X{n} {n} out vdd vss inv k='K' w_scale={scale_list[-1]}\n" 

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
        # Note: log_x function call is removed to yield a standard linear scale
        graph.plot_series(
            x_data=alpha,
            y_dict={"delay (ps)":delay},
            extra_x_dict=extra_x,
            extra_y_dict=extra_y,
            xlabel="alpha",
            ylabel="delay (ps)",
            title=f"Delay versus Alpha for C_load = {self.c_load*1e12}pf, M={self.M:.5f}",
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
    # Test execution (Removed the separate log graphs here as well)
    builder = inv_chain_builder(sp_filename="inv_chain_1pf_Wscale", model_path="models/22nm_HP.sp", c_load=1e-12, max_n=10)
    builder.get_delay_per_alpha()
    builder.graph()
    builder.tabulate()

    builder = inv_chain_builder(sp_filename="inv_chain_10pf_Wscale", model_path="models/22nm_HP.sp", c_load=10e-12, max_n=10)
    builder.get_delay_per_alpha()
    builder.graph()
    builder.tabulate()