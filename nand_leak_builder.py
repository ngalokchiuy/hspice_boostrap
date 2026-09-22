import os
import subprocess
import numpy as np
import pathlib as pl
import pandas as pd
import graphing as graph
import hspice_parser as hp

class nand_leak_builder:
    def __init__(self, sp_filename:str="nand_leak.sp",
                 model_path: str = "models",
                 vdd = 0.8, k = 1.25):
        
        self.base_name = pl.Path(sp_filename).stem
        self.model_path = model_path
        
        self.sp_path = f"sp/{self.base_name}.sp"
        self.mt_path = f"logs/{self.base_name}.mt0" 
        self.lis_path = f"logs/{self.base_name}.lis"
        
        self.vdd = vdd
        self.k = k
        
        for directory in ["logs", "graphs", "data", "sp"]:
            pl.Path(directory).mkdir(parents=True, exist_ok=True)
            
        self.ab_truth_table = {"circuit A" : [],
                               "circuit B" : [],
                               "circuit C" : [],
                               "circuit D" : []}

    def build_nand(self, footer:bool=False, header:bool=False):
        pmos_s = "vdd"
        nmos_s = "vss"
        if footer:
            nmos_s = "foot_out"
        if header:
            pmos_s = "head_out"
            
        nand = f"""
.subckt nand A B out {pmos_s} {nmos_s} pbulk nbulk k=1
.param w_n=44n l_n=22n w_p='k*w_n' l_p=22n

M1 out A {pmos_s} pbulk pmos W='w_p' L='l_p'
M2 out B {pmos_s} pbulk pmos W='w_p' L='l_p'

M3 mid A {nmos_s} nbulk nmos W='w_n' L='l_n'
M4 out B mid nbulk nmos W='w_n' L='l_n'

.ends nand

X0 a b out {pmos_s} {nmos_s} vdd vss nand k='K'
        """
        return nand

    def build_deck(self, footer:bool=False, header:bool=False, a="0.0", b="0.0"):
        spice_header = f"""
.include ../{self.model_path}/22nm_HP.sp
.include ../{self.model_path}/hi_vt_22nm_HP.sp
.param w_n=44n l_n=22n w_p='k*w_n' l_p=22n
.param K={self.k}

V1 vdd 0 DC {self.vdd}
V2 vss 0 DC 0.0 
Va a 0 DC {a}
Vb b 0 DC {b}
        """

        nand = self.build_nand(footer, header)

        foot = ""
        head = ""
        if header:
            head = "Mhead head_out vdd vdd vdd pmos_hvt W='w_p' L='l_p'\n"
        if footer:
            foot = "Mfoot foot_out vss vss vss nmos_hvt W='w_n' L='l_n'\n"

        sim_mode = ".tran 0.1p 10p\n"
        meas = ".meas tran i_leak avg I(V1) from=2p to=10p\n"
        
        footer_spice = """
.option post=2 
.end
        """ 
        
        spice_str = spice_header + foot + nand + head + sim_mode + meas + footer_spice
        
        with open(self.sp_path, 'w') as sp:
            print(spice_str, file=sp)
            
        return

    def run_sim(self, footer:bool=False, header:bool=False):
        i_out = []
        
        for a in ["0.0", str(self.vdd)]:
            for b in ["0.0", str(self.vdd)]:
                
                self.build_deck(footer, header, a=a, b=b)
                subprocess.run(["hspice", self.sp_path, "-o", self.lis_path])
                
                try:
                    df = hp.parse_mto(self.mt_path)
                    leakage = abs(float(df['i_leak'].iloc[0]))
                    i_out.append(leakage)
                except Exception as e:
                    print(f"Error parsing mt0 file or extracting data: {e}")
                    i_out.append(float('nan'))
                    
        return i_out

if __name__=="__main__":
    builder = nand_leak_builder()
    
    builder.ab_truth_table["circuit A"] = builder.run_sim(0,0) 
    builder.ab_truth_table["circuit B"] = builder.run_sim(0,1)
    builder.ab_truth_table["circuit C"] = builder.run_sim(1,0)
    builder.ab_truth_table["circuit D"] = builder.run_sim(1,1)

    print("For ab = 00, 01, 10, 11, currents are...")
    for key, value in builder.ab_truth_table.items():
        val_str = "|"
        for current in value:
            val_str += f" {current:.4e} |"
        print(f"{key}: {val_str}")
        print("")

    graph.generate_leakage_heatmap(builder.ab_truth_table, "graphs/nand_leak.png")