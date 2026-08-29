import graphing as graph
import hspice_parser as hp
import argparse
import pathlib as pl
import subprocess
import matplotlib.pyplot as plt

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
        self.diff_tr_tf = self.df['diff_tr_tf'].values * 1e12

    def plot_inv_7x(self, graph_dir:str="graphs"):
        self.get_series()
        tp_dict = {"tplh (ps)": self.tplh_vals, "tphl (ps)": self.tphl_vals}
        tr_tf_dict = {"tr (ps)": self.tr_vals, "tf (ps)": self.tf_vals}
        diff_dict = {"|tplh-tphl| (ps)": self.diff_tp_vals, "|tr-tf| (ps)": self.diff_tr_tf}

        plt.figure(1)
        self.graph_path1 = f"{graph_dir}/{self.base_name}_tp_vs_k.png"
        graph.plot_series(
            x_data=self.k_vals,
            y_dict=tp_dict,
            xlabel="k",
            ylabel="t (ps)",
            title="tphl and tplh (ps) vs. k",
            filename=self.graph_path1
        )
        plt.figure(2)
        self.graph_path2 = f"{graph_dir}/{self.base_name}_tr_tf_vs_k.png"
        graph.plot_series(
            x_data=self.k_vals,
            y_dict=tr_tf_dict,
            xlabel="k",
            ylabel="t (ps)",
            title="tr and tf (ps) vs. k",
            filename=self.graph_path2
        )

        plt.figure(3)
        self.graph_path3 = f"{graph_dir}/{self.base_name}_diff_tp_vs_k.png"
        graph.plot_series(
            x_data=self.k_vals,
            y_dict=diff_dict,
            xlabel="k",
            ylabel="t (ps)",
            title="|tphl-tphl| and |tr-tf| (ps) vs. k",
            filename=self.graph_path3
        )
        return

    def tabulate_inv_7x(self, data_dir:str="data"):
        self.df.to_csv(f"{data_dir}/{self.base_name}.csv", index=False)
        return

    def get_md_table(self) -> str:
        md_table_str = self.df.to_markdown(index=False)
        return md_table_str

    def write_md(self, md_dir:str="md"):
        #automatically calls both plot and get_md_table, tabulates data
        self.plot_inv_7x() # populates graphs/
        self.tabulate_inv_7x() # populates data/
        table = self.get_md_table() #returns an md table string
        with open (f"{md_dir}/{self.base_name}.md", 'w') as md:
            print(f"# {self.base_name} output", file=md)
            print(table, file=md)
            print(f"## Graphical Ouputs", file=md)
            images = f"""
<p align="center">
    <img src="../graphs/{self.base_name}_tp_vs_k.png" alt="tphl and tplh (ps) vs. k" width="500">
</p>
<p align="center">
    <img src="../graphs/{self.base_name}_tr_tf_vs_k.png" alt="tr and tf (ps) vs. k" width="500">
</p>
<p align="center">
    <img src="../graphs/{self.base_name}_diff_tp_vs_k.png" alt="tr and tf (ps) vs. k" width="500">
</p>
            """
            print(images, file=md)
        return    
    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sp_filename",default="inv_7x.sp", type=str)
    parser.add_argument("--run_sim", default=True, type=bool)
    args=parser.parse_args()

    deck = inv_7x(args.sp_filename)
    if args.run_sim: #run spice sim
        deck.run_sim()
    
    # output plots and tables to md file 
    # plots pngs will populate "graphs"
    # csvs will populate "data"
    deck.write_md()
