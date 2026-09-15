# gate capacitance characteristics 
import graphing as graph
import hspice_parser as hp
import build_deck as build
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import pathlib as pl
import argparse
import pandas as pd

class cg_char:
    def __init__(self, sp_filename:str="nmos_gnd_cg_char.sp"):

        self.base_name = pl.Path(sp_filename).stem
        self.sp_path = f"sp/{self.base_name}.sp"
        self.mt_path = f"logs/{self.base_name}.mt0"
        self.sw_path = f"logs/{self.base_name}.sw0"
        self.ac_path = f"logs/{self.base_name}.ac0"
        self.lis_path = f"logs/{self.base_name}.lis"
        for dir in ["logs", "graphs", "data", "md"]:
            pl.Path(dir).mkdir(parents=True, exist_ok=True)
        pass

    def run_sim(self):
        #make sure you source the proper hspice binaries first
        subprocess.run(["hspice",self.sp_path,"-o",self.lis_path])
        self.df = hp.parse_nested_ac0(self.ac_path) #<------------now nested
        print(self.df)
        return

    def get_series(self):
        self.df = self.df.drop_duplicates()
        f = self.df['HERTZ'].values[0]
        s = f * 2 * 3.14159
        vac = self.df['vr(vg'].values[0]
        cg = []
        for i in self.df['ii(vg'].values:
            cg.append(abs(i)/(vac*s) * 1e15) #fF
        self.cg = np.array(cg)
        self.vg = self.df['vg_val']
        self.df["gate_cap"] = self.cg
        print("gate cap: ", cg)
        return

    def graph(self, type="nmos_gnd", graph_dir:str="graphs"):
        self.get_series()

        return

    
    def tabulate(self, data_dir:str="data"):
        self.df.to_csv(f"{data_dir}/{self.base_name}.csv", index=False)
        md_table_str = self.df.to_markdown(index=False)
        with open (f"{data_dir}/{self.base_name}.md", 'w') as md:
            print(md_table_str, file=md)
        
        small_df = pd.DataFrame({
            "Vg (v)": self.df["vg_val"].values,
            "gate cap (fF)": self.df["gate_cap"].values
        })
        print(small_df)
        small_md_str = small_df.to_markdown(index=False)
        with open(f"{data_dir}/{self.base_name}_small_table.md", 'w') as md:
            print(small_md_str, file=md)
        return




            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_sim", default=True, type=bool)
    parser.add_argument("--write_deck", default=True, type=bool)
    args=parser.parse_args()

    # nmos first 
    if args.write_deck: 
        build.write_cg_char(output_file="sp/nmos_gnd_cg_char.sp", type="nmos_gnd")

    nmos_gnd = cg_char("nmos_gnd_cg_char.sp")
    if args.run_sim:
        nmos_gnd.run_sim()
    nmos_gnd.graph("nmos_gnd")
    nmos_gnd.tabulate()

    if args.write_deck: 
        build.write_cg_char(output_file="sp/nmos_vdd_cg_char.sp", type="nmos_vdd")

    nmos_gnd = cg_char("nmos_vdd_cg_char.sp")
    if args.run_sim:
        nmos_gnd.run_sim()
    nmos_gnd.graph("nmos_vdd")
    nmos_gnd.tabulate()

    if args.write_deck: 
            build.write_cg_char(output_file="sp/pmos_gnd_cg_char.sp", type="pmos_gnd")
    
    nmos_gnd = cg_char("pmos_gnd_cg_char.sp")
    if args.run_sim:
        nmos_gnd.run_sim()
    nmos_gnd.graph("pmos_gnd")
    nmos_gnd.tabulate()

    if args.write_deck: 
        build.write_cg_char(output_file="sp/pmos_vdd_cg_char.sp", type="pmos_vdd")
    
    nmos_gnd = cg_char("pmos_vdd_cg_char.sp")
    if args.run_sim:
        nmos_gnd.run_sim()
    nmos_gnd.graph("pmos_vdd")
    nmos_gnd.tabulate()

