import graphing as graph
import hspice_parser as hp
import argparse
import pathlib as pl
import subprocess
import matplotlib.pyplot as plt
import build_deck as build
import numpy as np

class inv_7x:
    def __init__(self, sp_filename:str="inv_7x.sp"):

        self.base_name = pl.Path(sp_filename).stem
        self.sp_path = f"sp/{self.base_name}.sp"
        self.mt_path = f"logs/{self.base_name}.mt0"
        self.lis_path = f"logs/{self.base_name}.lis"
        for dir in ["logs", "graphs", "data", "md"]:
            pl.Path(dir).mkdir(parents=True, exist_ok=True)
        pass

    #in the future could write a def write_deck() function instead of writing it manually
    #enter rise time in ps

    def run_sim(self):
        #make sure you source the proper hspice binaries first
        subprocess.run(["hspice",self.sp_path,"-o",self.lis_path])
        self.df = hp.parse_mto(self.mt_path) #get output data 
        return
    
    def get_series(self):
        # print(df.head()) #testing functionality
        self.k_vals = self.df['k'].values
        self.tplh_vals = self.df['tplh'].values * 1e12 #ps
        self.tphl_vals = self.df['tphl'].values * 1e12
        self.tr_vals = self.df['tr'].values * 1e12
        self.tf_vals = self.df['tf'].values * 1e12
        self.diff_tp_vals = self.df['diff_tplh_tphl'].values * 1e12
        self.diff_tr_tf_vals = self.df['diff_tr_tf'].values * 1e12

        # get k for max tp sym and k for max tf and tf sym
        self.min_diff_tp = self.df['diff_tplh_tphl'].min() * 1e12
        self.min_diff_tr_tf = self.df['diff_tr_tf'].min() * 1e12
        self.best_k_tp = self.df.loc[self.df['diff_tplh_tphl'].idxmin(),'k']
        self.best_k_tr_tf = self.df.loc[self.df['diff_tr_tf'].idxmin(),'k']

    def plot_inv_7x(self, graph_dir:str="graphs"):
        self.get_series()
        tp_dict = {"tplh (ps)": self.tplh_vals, "tphl (ps)": self.tphl_vals}
        tr_tf_dict = {"tr (ps)": self.tr_vals, "tf (ps)": self.tf_vals}
        diff_dict = {"|tplh-tphl| (ps)": self.diff_tp_vals, "|tr-tf| (ps)": self.diff_tr_tf_vals}

        best_k_tp_ary = np.array([self.best_k_tp, self.best_k_tp])
        best_k_tr_tf_ary = np.array([self.best_k_tr_tf, self.best_k_tr_tf])
        tp_array = np.array([
            np.min([self.tphl_vals.min(), self.tplh_vals.min()]),
            np.max([self.tphl_vals.max(), self.tplh_vals.max()])
        ])

        tr_tf_array = np.array([
            np.min([self.tr_vals.min(), self.tf_vals.min()]),
            np.max([self.tr_vals.max(), self.tf_vals.max()])
        ])

        diff_array = np.array([
            np.min([self.diff_tp_vals.min(), self.diff_tr_tf_vals.min()]),
            np.max([self.diff_tp_vals.max(), self.diff_tr_tf_vals.max()])
        ])
        extra_x1 = {f"k={self.best_k_tp} @ min|tphl-tplh|={self.min_diff_tp:.3f}p": best_k_tp_ary}
        extra_y1 = {f"k={self.best_k_tp} @ min|tphl-tplh|={self.min_diff_tp:.3f}p": tp_array}
        extra_x2 = {f"k={self.best_k_tr_tf} @ min|tr-tf|={self.min_diff_tr_tf:.3f}p": best_k_tr_tf_ary}
        extra_y2 = {f"k={self.best_k_tr_tf} @ min|tr-tf|={self.min_diff_tr_tf:.3f}p": tr_tf_array}
        extra_x3 = {
            f"k={self.best_k_tp} @ min|tphl-tplh|={self.min_diff_tp:.3f}p": best_k_tp_ary,
            f"k={self.best_k_tr_tf} @ min|tr-tf|={self.min_diff_tr_tf:.3f}p": best_k_tr_tf_ary
        }
        extra_y3 = {
            f"k={self.best_k_tp} @ min|tphl-tplh|={self.min_diff_tp:.3f}p": diff_array,
            f"k={self.best_k_tr_tf} @ min|tr-tf|={self.min_diff_tr_tf:.3f}p": diff_array
        }
        plt.figure(1)
        self.graph_path1 = f"{graph_dir}/{self.base_name}_tp_vs_k.png"
        graph.plot_series(
            x_data=self.k_vals,
            y_dict=tp_dict,
            extra_x_dict=extra_x1,
            extra_y_dict=extra_y1,
            xlabel="k",
            ylabel="t (ps)",
            title="tphl and tplh (ps) vs. k",
            filename=self.graph_path1
        )
        plt.clf()
        plt.figure(2)
        self.graph_path2 = f"{graph_dir}/{self.base_name}_tr_tf_vs_k.png"
        graph.plot_series(
            x_data=self.k_vals,
            y_dict=tr_tf_dict,
            extra_x_dict=extra_x2,
            extra_y_dict=extra_y2,
            xlabel="k",
            ylabel="t (ps)",
            title="tr and tf (ps) vs. k",
            filename=self.graph_path2
        )
        plt.clf()
        plt.figure(3)
        self.graph_path3 = f"{graph_dir}/{self.base_name}_diff_tp_vs_k.png"
        graph.plot_series(
            x_data=self.k_vals,
            y_dict=diff_dict,
            extra_x_dict=extra_x3,
            extra_y_dict=extra_y3,
            xlabel="k",
            ylabel="t (ps)",
            title="|tphl-tphl| and |tr-tf| (ps) vs. k",
            filename=self.graph_path3
        )
        plt.clf()
        return

    def tabulate_inv_7x(self, data_dir:str="data"):
        self.df.to_csv(f"{data_dir}/{self.base_name}.csv", index=False)
        md_table_str = self.df.to_markdown(index=False)
        with open (f"{data_dir}/{self.base_name}.md", 'w') as md:
            print(md_table_str, file=md)
        return

    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("--sp_filename",default="inv_7x.sp", type=str)
    parser.add_argument("--run_sim", default=True, type=bool)
    parser.add_argument("--write_deck", default=True, type=bool)
    args=parser.parse_args()

    if args.write_deck: 
        build.write_inv_7x(output_file="sp/inv_7x_10p.sp", input_rise_time=10)

    deck_10p = inv_7x("inv_7x_10p")
    if args.run_sim: #run spice sim
        deck_10p.run_sim()
    deck_10p.plot_inv_7x()
    deck_10p.tabulate_inv_7x()

    if args.write_deck: 
        build.write_inv_7x(output_file="sp/inv_7x_6p.sp", input_rise_time=5.7)
    
    deck_6p = inv_7x("inv_7x_6p")
    if args.run_sim: #run spice sim
        deck_6p.run_sim()
    deck_6p.plot_inv_7x()
    deck_6p.tabulate_inv_7x()
