import graphing as graph
import hspice_parser as hp
import build_deck as build
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import pathlib as pl
import argparse

class iv_char:
    def __init__(self, sp_filename:str="nmos_iv_char.sp"):

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
        self.df = hp.parse_nested_sw0(self.sw_path) #<------------now nested
        print(self.df)
        return

    def get_series(self):
        self.df = self.df.dropna()
        self.ids = {}
        self.vds = {}
        self.vgs = self.df['0:vg'].drop_duplicates().values
        for vgs in self.vgs:
            ids = self.df[self.df['0:vg']==vgs]["i(vds"].values * -1e6 # convert to uA
            vds = self.df[self.df['0:vg']==vgs]["VOLTS"].values
            self.ids[f"Vgs={vgs}"] = ids
            self.vds[f"Vgs={vgs}"] = vds
            print(f" for vgs = {vgs}")
            print(f"ids = {ids}, len={len(ids)}")
            print(f"vds={vds}, len = {len(vds)}")
        print(len(self.vds.keys()))
        print(len(self.ids.keys()))
        return
    
    def get_ron(self, ids_ary, vds_ary, type="nmos"):
        if type == "nmos":
            delta_ids = (ids_ary[1] - ids_ary[0]) * 1e-6 #convert to A
            delta_vds = vds_ary[1] - vds_ary[0]
        if type == "pmos":
            delta_ids = (ids_ary[-1] - ids_ary[-2]) * 1e-6 #convert to A
            delta_vds = vds_ary[-1] - vds_ary[-2]
        ron = delta_vds/delta_ids
        # slope for graph
        ron_slope = (delta_ids * 1e6) / delta_vds
        if type == "pmos":
            ron_vds = np.array([0,-0.4])
        else:
            ron_vds = np.array([0, 0.3])
        ron_ids = np.array([0, ron_slope*ron_vds[1]])
        self.ron_xdata = {f"Ron = {ron:.2f}": ron_vds}
        self.ron_ydata = {f"Ron = {ron:.2f}": ron_ids}
        print("ron =", ron, "ron slope = ", ron_slope)
        print("ron_vds = ", ron_vds)
        print("ron_ids = ", ron_ids)
        return

    def graph_iv(self, type="nmos", graph_dir:str="graphs"):
        self.get_series()
        if type == "nmos":
            last_vgs = self.vgs[-1] # should be 0.8
        else:
            last_vgs = self.vgs[0] # should be 0.8
        print("last_vgs", last_vgs)
        last_ids = self.ids[f"Vgs={last_vgs}"]
        last_vds = self.vds[f"Vgs={last_vgs}"]
        self.get_ron(last_ids, last_vds, type)

        plt.figure(1)
        self.graph_path1 = f"{graph_dir}/{self.base_name}.png"
        graph.plot_series(
            x_data=last_vds, #only supply one sereies
            y_dict=self.ids,
            extra_x_dict=self.ron_xdata,
            extra_y_dict=self.ron_ydata,
            xlabel="Vds (V)",
            ylabel="Ids (uA)",
            title=f"{type} IV curve",
            filename=self.graph_path1
        )
        plt.clf()
        return

    
    def tabulate_iv(self, data_dir:str="data"):
        self.df.to_csv(f"{data_dir}/{self.base_name}.csv", index=False)
        md_table_str = self.df.to_markdown(index=False)
        with open (f"{data_dir}/{self.base_name}.md", 'w') as md:
            print(md_table_str, file=md)
        return




            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_sim", default=True, type=bool)
    parser.add_argument("--write_deck", default=True, type=bool)
    args=parser.parse_args()

    # Pmos first 
    if args.write_deck: 
        build.write_iv_char(output_file="sp/pmos_iv_char.sp", type="pmos")
        build.write_iv_char(output_file="sp/nmos_iv_char.sp", type="nmos")

    pmos = iv_char("pmos_iv_char.sp")
    nmos = iv_char("nmos_iv_char.sp")
    if args.run_sim:
        nmos.run_sim()
        pmos.run_sim()
    nmos.graph_iv()
    pmos.graph_iv(type="pmos")
    nmos.tabulate_iv()
    pmos.tabulate_iv()