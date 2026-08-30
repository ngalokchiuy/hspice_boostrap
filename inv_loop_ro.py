import graphing as graph
import hspice_parser as hp
import argparse
import pathlib as pl
import subprocess
import matplotlib.pyplot as plt
import build_deck as build
import numpy as np

class inv_loop_ro:
    def __init__(self, sp_filename:str="inv_loop_ro.sp"):

        self.base_name = pl.Path(sp_filename).stem
        self.sp_path = f"sp/{self.base_name}.sp"
        self.mt_path = f"logs/{self.base_name}.mt0"
        self.lis_path = f"logs/{self.base_name}.lis"
        for dir in ["logs", "graphs", "data", "md"]:
            pl.Path(dir).mkdir(parents=True, exist_ok=True)
        pass

    def run_sim(self):
        #make sure you source the proper hspice binaries first
        subprocess.run(["hspice",self.sp_path,"-o",self.lis_path])
        self.df = hp.parse_mto(self.mt_path) #get output data 
        return

    def get_series(self):
        self.gnd_vals = self.df['gnd_val'].values
        self.f_vals = self.df['f'].values * 1e-9 #GHz
        self.t_over_42 = self.df.loc[self.df['gnd_val'].idxmin(), 't_over_42'] * 1e12 #convert to ps

    def plot_inv_loop_ro(self, graph_dir:str="graphs"):
        self.get_series()
        f_dict = {f"f (Ghz), when GND=0V T/42 = {self.t_over_42:.4f}ps": self.f_vals}
        plt.figure(1)
        self.graph_path1 = f"{graph_dir}/{self.base_name}_f_vs_v.png"
        graph.plot_series(
            x_data=self.gnd_vals,
            y_dict=f_dict,
            xlabel="Ground Node Voltage (V)",
            ylabel="f (GHz)",
            title="Inv 21x Ring Oscillator Frequency vs. GND Node Voltage",
            filename=self.graph_path1
        )
        plt.clf()

    def tabulate_inv_loop_ro(self, data_dir:str="data"):
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

    # if args.write_deck: 
    #     build.write_inv_loop(output_file="sp/inv_loop_21x.sp", input_rise_time=5.7, K=1.324)

    #     deck = inv_loop_ro("inv_loop_21x.sp")
    # if args.run_sim: #run spice sim
    #     deck.run_sim()
    # deck.plot_inv_loop_ro()
    # deck.tabulate_inv_loop_ro()

    if args.write_deck: 
        build.write_inv_loop(output_file="sp/inv_loop_3x.sp", input_rise_time=5.7, K=1.324, inv_count=3)

        deck2 = inv_loop_ro("inv_loop_3x.sp")
    if args.run_sim: #run spice sim
        deck2.run_sim()
    deck2.plot_inv_loop_ro()
    deck2.tabulate_inv_loop_ro()

    