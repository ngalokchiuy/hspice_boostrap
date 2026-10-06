import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import hspice_parser as hp
import pathlib as pl
import pandas as pd
import math

class inv_chain_builder:
    def __init__(self, 
                 mode: str = "nf",           # Can be "M", "W", or "nf"
                 max_finger_w: float = 220e-9, 
                 c_load=1e-12,
                 model_path: str = "models/22nm_HP.sp",
                 c_min=7.321e-17, 
                 max_n:int = 10,
                 vdd=0.8,
                 k=1.3):
        
        # Dynamic naming to keep log files distinct per test
        finger_str = f"_{int(max_finger_w*1e9)}nm" if mode == "nf" else ""
        # Added _rgate0 to filenames to keep them separate from your previous runs
        self.base_name = f"inv_chain_{int(c_load*1e12)}pf_{mode}{finger_str}_rgate0"
        
        self.mode = mode
        self.max_finger_w = max_finger_w
        
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
        if (self.c_load == 1e-11):
            min_n = 4
        n_list = list(range(min_n, max_n_to_test+1)) 
        
        alpha_list = [(self.M ** (1/(n+1))) for n in n_list]
        return n_list, alpha_list

    def get_dims(self, n, alpha):
        """Calculate continuous scaling factor for each stage."""
        return [alpha ** (i + 1) for i in range(n)]

    def calculate_fingers(self, scale_val):
        """Dynamically calculate required fingers based on max finger width rule."""
        w_n_base, w_p_base = 44e-9, 44e-9 * self.k
        w_n_tot, w_p_tot = w_n_base * scale_val, w_p_base * scale_val
        
        nf_n = max(1, math.ceil(w_n_tot / self.max_finger_w))
        nf_p = max(1, math.ceil(w_p_tot / self.max_finger_w))
        return nf_n, nf_p

    def get_delay_per_alpha(self):
        for n, alpha in zip(self.n_list, self.alpha_list):
            self.build_deck(n, alpha)
            subprocess.run(["hspice", self.sp_path, "-o", self.lis_path], stdout=subprocess.DEVNULL)
            
            df = hp.parse_mto(self.mt_path) 
            self.df = pd.concat([self.df, df], ignore_index=True)
        return
    
    def build_deck(self, n, alpha):
        header = f"""Inverter Chain ({self.mode} Mode - rgate=0)
.include ../{self.model_path}
.param x=5p
.param K={self.k}
V1 vdd 0 DC {self.vdd}
V2 vss 0 DC 0.0
Vin in 0 PULSE(0.8 0 1n x x 10n 20n)\n""" 
        
        # All modes now explicitly have rgatemod=0 applied to M1 and M2
        if self.mode == "M":
            subckt = """
        .subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n scale_val=1
        .param w_p='k*w_n' 
        M1 out in vdd vdd pmos W='w_p' L='l_p' m='scale_val' rgatemod=0
        M2 out in vss vss nmos W='w_n' L='l_n' m='scale_val' rgatemod=0
        .ends inv\n"""
        elif self.mode == "W":
            subckt = """
        .subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n scale_val=1
        .param w_p_tot='k*w_n*scale_val' 
        .param w_n_tot='w_n*scale_val'
        M1 out in vdd vdd pmos W='w_p_tot' L='l_p' rgatemod=0
        M2 out in vss vss nmos W='w_n_tot' L='l_n' rgatemod=0
        .ends inv\n"""
        elif self.mode == "nf":
            subckt = """
        .subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n scale_val=1 nfingers_n=1 nfingers_p=1
        .param w_p_tot='k*w_n*scale_val' 
        .param w_n_tot='w_n*scale_val'
        M1 out in vdd vdd pmos W='w_p_tot' L='l_p' nf='nfingers_p' rgatemod=0
        M2 out in vss vss nmos W='w_n_tot' L='l_n' nf='nfingers_n' rgatemod=0
        .ends inv\n"""
        
        scale_list = self.get_dims(n, alpha)
        
        instances = ""
        if self.mode == "nf":
            nf_n, nf_p = self.calculate_fingers(1.0)
            instances += f"X0 in 1 vdd vss inv k='K' scale_val=1 nfingers_n={nf_n} nfingers_p={nf_p}\n"
        else:
            instances += f"X0 in 1 vdd vss inv k='K' scale_val=1\n"
            
        for i in range(1, n):
            sc = scale_list[i-1]
            if self.mode == "nf":
                nf_n, nf_p = self.calculate_fingers(sc)
                instances += f"X{i} {i} {i+1} vdd vss inv k='K' scale_val={sc} nfingers_n={nf_n} nfingers_p={nf_p}\n"
            else:
                instances += f"X{i} {i} {i+1} vdd vss inv k='K' scale_val={sc}\n"

        sc_last = scale_list[-1]
        if self.mode == "nf":
            nf_n, nf_p = self.calculate_fingers(sc_last)
            instances += f"X{n} {n} out vdd vss inv k='K' scale_val={sc_last} nfingers_n={nf_n} nfingers_p={nf_p}\n"
        else:
            instances += f"X{n} {n} out vdd vss inv k='K' scale_val={sc_last}\n"

        load = f"C0 out 0 {self.c_load}\n"
        tran = ".tran 0.1p 10n\n"
        meas = ".meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 " + ("rise=1\n" if (n+1) % 2 != 0 else "fall=1\n")
        footer = ".option post=2 \n.end\n"

        with open(self.sp_path, 'w') as sp:
            sp.write(header + subckt + instances + load + tran + meas + footer)
 
    def plot_trace(self, marker_shape='o', line_style='-'):
        """Plots this specific trace onto the active matplotlib axes with shapes for accessibility."""
        delay_ps = self.df["delay"] * 1e12
        alpha = np.array(self.alpha_list)
        min_idx = self.df['delay'].idxmin()
        
        # Updated labels to reflect rgate=0 is on all of them
        if self.mode == "nf":
            label = f"Mode: {self.mode} (MaxW={int(self.max_finger_w*1e9)}nm, rgate=0)"
        elif self.mode == "W":
             label = f"Mode: W (rgate=0)"
        else:
            label = f"Mode: {self.mode} (float parallel, rgate=0)"

        p = plt.plot(alpha, delay_ps, marker=marker_shape, linestyle=line_style, label=label, markersize=8)
        
        plt.scatter(alpha[min_idx], delay_ps[min_idx], color=p[0].get_color(), 
                    marker=marker_shape, s=150, zorder=5, 
                    edgecolor='black', linewidth=1.5, 
                    label=f'Min: n={self.n_list[min_idx]}, {delay_ps[min_idx]:.1f}ps')

if __name__ == "__main__":
    
    W_MIN = 44e-9 
    W_MAX_2W = 2 * W_MIN 

    styles = [
        {'marker': 'o', 'ls': '-'},   # Circle, solid
        {'marker': 's', 'ls': '--'},  # Square, dashed
        {'marker': '^', 'ls': '-.'},  # Triangle, dash-dot
        {'marker': 'D', 'ls': ':'},   # Diamond, dotted
        {'marker': 'v', 'ls': '-'}    # Inverted Triangle, solid
    ]

    # ----------------------------------------------------
    # TEST SUITE 1: 1 pF Load (ALL RGATEMOD=0)
    # ----------------------------------------------------
    plt.figure(figsize=(12, 7))
    print("Running 1pF Tests with rgate=0 across all modes...")
    
    b_m = inv_chain_builder(mode="M", c_load=1e-12)
    b_m.get_delay_per_alpha()
    b_m.plot_trace(marker_shape=styles[0]['marker'], line_style=styles[0]['ls'])
    
    b_w = inv_chain_builder(mode="W", c_load=1e-12)
    b_w.get_delay_per_alpha()
    b_w.plot_trace(marker_shape=styles[1]['marker'], line_style=styles[1]['ls'])
    
    b_nf88 = inv_chain_builder(mode="nf", max_finger_w=W_MAX_2W, c_load=1e-12)
    b_nf88.get_delay_per_alpha()
    b_nf88.plot_trace(marker_shape=styles[2]['marker'], line_style=styles[2]['ls'])

    b_nf220 = inv_chain_builder(mode="nf", max_finger_w=220e-9, c_load=1e-12)
    b_nf220.get_delay_per_alpha()
    b_nf220.plot_trace(marker_shape=styles[3]['marker'], line_style=styles[3]['ls'])
    
    b_nf440 = inv_chain_builder(mode="nf", max_finger_w=440e-9, c_load=1e-12)
    b_nf440.get_delay_per_alpha()
    b_nf440.plot_trace(marker_shape=styles[4]['marker'], line_style=styles[4]['ls'])

    plt.title("Delay vs Alpha overlay (Load = 1pF, ALL rgatemod=0)")
    plt.xlabel("Alpha")
    plt.ylabel("Delay (ps)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left') 
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig("graphs/Combined_1pF_rgate0.png")
    plt.clf() 

    # ----------------------------------------------------
    # TEST SUITE 2: 10 pF Load (ALL RGATEMOD=0)
    # ----------------------------------------------------
    plt.figure(figsize=(12, 7))
    print("Running 10pF Tests with rgate=0 across all modes...")
    
    b_m_10 = inv_chain_builder(mode="M", c_load=10e-12)
    b_m_10.get_delay_per_alpha()
    b_m_10.plot_trace(marker_shape=styles[0]['marker'], line_style=styles[0]['ls'])
    
    b_w_10 = inv_chain_builder(mode="W", c_load=10e-12)
    b_w_10.get_delay_per_alpha()
    b_w_10.plot_trace(marker_shape=styles[1]['marker'], line_style=styles[1]['ls'])
    
    b_nf88_10 = inv_chain_builder(mode="nf", max_finger_w=W_MAX_2W, c_load=10e-12)
    b_nf88_10.get_delay_per_alpha()
    b_nf88_10.plot_trace(marker_shape=styles[2]['marker'], line_style=styles[2]['ls'])

    b_nf220_10 = inv_chain_builder(mode="nf", max_finger_w=220e-9, c_load=10e-12)
    b_nf220_10.get_delay_per_alpha()
    b_nf220_10.plot_trace(marker_shape=styles[3]['marker'], line_style=styles[3]['ls'])
    
    b_nf440_10 = inv_chain_builder(mode="nf", max_finger_w=440e-9, c_load=10e-12)
    b_nf440_10.get_delay_per_alpha()
    b_nf440_10.plot_trace(marker_shape=styles[4]['marker'], line_style=styles[4]['ls'])

    plt.title("Delay vs Alpha overlay (Load = 10pF, ALL rgatemod=0)")
    plt.xlabel("Alpha")
    plt.ylabel("Delay (ps)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig("graphs/Combined_10pF_rgate0.png")
    plt.clf()
    
    print("Simulations complete! Check the 'graphs' folder for the combined plots.")