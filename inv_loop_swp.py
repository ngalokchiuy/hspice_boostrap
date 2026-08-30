#inv loop Switch point

import graphing as graph
import hspice_parser as hp
import argparse
import pathlib as pl
import subprocess
import matplotlib.pyplot as plt
import build_deck as build
import numpy as np

class inv_loop_swp:
    def __init__(self, sp_filename:str="inv_loop_swp.sp"):

        self.base_name = pl.Path(sp_filename).stem
        self.sp_path = f"sp/{self.base_name}.sp"
        self.mt_path = f"logs/{self.base_name}.mt0"
        self.sw_path = f"logs/{self.base_name}.sw0"
        self.lis_path = f"logs/{self.base_name}.lis"
        for dir in ["logs", "graphs", "data", "md"]:
            pl.Path(dir).mkdir(parents=True, exist_ok=True)
        pass

    def run_sim(self):
        #make sure you source the proper hspice binaries first
        subprocess.run(["hspice",self.sp_path,"-o",self.lis_path])
        self.df = hp.parse_sw0(self.sw_path)
        return

    def get_series(self):
        self.df = self.df.dropna()
        self.v_swp_vals = self.df['v(in'].values
        self.k_vals = self.df['k'].values
        self.df['|v(in)-vdd/2|'] = abs(self.df['v(in'] - 0.4)
        self.k_sym = self.df.loc[self.df['|v(in)-vdd/2|'].idxmin(), 'k']

    def plot_inv_loop_swp(self, graph_dir:str="graphs"):
        self.get_series()
        v_swp_dict = {f"V_swp vs. K": self.v_swp_vals}
        k_sym_ary= np.array([self.k_sym, self.k_sym])
        
        v_swp_ary = np.array([self.v_swp_vals.min(), self.v_swp_vals.max()])
        print(v_swp_ary)
        extra_x = {f"V_swp = VDD/2 @ k={self.k_sym}": k_sym_ary}
        extra_y = {f"V_swp = VDD/2 @ k={self.k_sym}": v_swp_ary}
        plt.figure(1)
        self.graph_path1 = f"{graph_dir}/{self.base_name}.png"
        graph.plot_series(
            x_data=self.k_vals,
            y_dict=v_swp_dict,
            extra_x_dict=extra_x,
            extra_y_dict=extra_y,
            xlabel="k",
            ylabel="V_swp (V)",
            title="Single Looped Inverter Switchpoint vs. K",
            filename=self.graph_path1
        )
        plt.clf()

    def tabulate_inv_loop_swp(self, data_dir:str="data"):
            self.df.to_csv(f"{data_dir}/{self.base_name}.csv", index=False)
            md_table_str = self.df.to_markdown(index=False)
            with open (f"{data_dir}/{self.base_name}.md", 'w') as md:
                print(md_table_str, file=md)
            return
        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_sim", default=True, type=bool)
    parser.add_argument("--write_deck", default=True, type=bool)
    args=parser.parse_args()

    if args.write_deck: 
        build.write_inv_loop_1x(output_file="sp/inv_loop_swp.sp")

        deck = inv_loop_swp("inv_loop_swp.sp")
    if args.run_sim: #run spice sim
        deck.run_sim()
    
    deck.plot_inv_loop_swp()
    print(deck.df.head())
    deck.tabulate_inv_loop_swp()
