import graphing as graph
import hspice_parser as hp
import build_deck as build
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import pathlib as pl
import argparse
import pandas as pd

class cd_char:
    def __init__(self, sp_filename:str="nmos_cd_char.sp"):

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
        subprocess.run(["hspice",self.sp_path,"-o",self.lis_path])
        self.df = hp.parse_nested_ac0(self.ac_path) #<------------now nested
        print(self.df)
        return

    def get_series(self):
        self.df = self.df.drop_duplicates()
        f = self.df['HERTZ'].values[0]
        s = f * 2 * 3.14159
        vac = self.df['vr(vd'].values[0] # changed: vg to vd
        cd = []
        for i in self.df['ii(vd'].values: # changed: vg to vd
            cd.append(abs(i)/(vac*s) * 1e15) #fF
        self.cd = np.array(cd)
        self.vd = self.df['vd_val'] # changed: vg_val to vd_val
        self.df["diff_cap"] = self.cd # changed: gate_cap to diff_cap
        print("diff cap: ", cd) # changed: gate cap to diff cap
        return

    def graph(self, type="nmos", graph_dir:str="graphs"): # changed: type default to nmos
        self.get_series()

        return

    
    def tabulate(self, data_dir:str="data"):
        self.get_series()
        self.df.to_csv(f"{data_dir}/{self.base_name}.csv", index=False)
        md_table_str = self.df.to_markdown(index=False)
        with open (f"{data_dir}/{self.base_name}.md", 'w') as md:
            print(md_table_str, file=md)
        
        small_df = pd.DataFrame({
            "Vd (v)": self.df["vd_val"].values,
            "diff cap (fF)": self.df["diff_cap"].values 
        })
        print(small_df)
        small_md_str = small_df.to_markdown(index=False)
        with open(f"{data_dir}/{self.base_name}_small_table.md", 'w') as md:
            print(small_md_str, file=md)
        return small_md_str




            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_sim", default=True, type=bool)
    parser.add_argument("--write_deck", default=True, type=bool)
    args=parser.parse_args()

    with open ("results/Exercise_5b.md", 'w') as results:
        header = """# Execercise 5b, Diffusion Cap Results

This was done using the dimensions shown in exercise 8
```
.param as_n = 'w_n * l_n*1.5'
.param as_p = 'w_p * l_p*1.5'
.param ad_n = 'w_n * l_n*1.5'
.param ad_p = 'w_p * l_p*1.5'
.param ps_n = 'w_n + 3*l_n'
.param ps_p = 'w_p + 3*l_p'
.param pd_n = 'w_n + 3*l_n'
.param pd_p = 'w_p + 3*l_p'
```\n"""
        results.write(header)
        # nmos first 
        if args.write_deck: 
            build.write_cd_char(output_file="sp/nmos_cd_char.sp", type="nmos")

        nmos = cd_char("nmos_cd_char.sp")
        nmos.run_sim()
        results.write("## NMOS Diffusion Capicatnace with As Ad Ps Pd specified\n")
        results.write(nmos.tabulate())
        results.write("\n\n\n")

        if args.write_deck: 
            build.write_cd_char(output_file="sp/pmos_cd_char.sp", type="pmos")
        
        pmos = cd_char("pmos_cd_char.sp")
        pmos.run_sim()
        results.write("## PMOS Diffusion Capicatnace with As Ad Ps Pd specified\n")
        results.write(pmos.tabulate())
        results.write("\n\n\n")


        #compare to providing no as ad ps pd args

        # nmos first 
        if args.write_deck: 
            build.write_cd_char(output_file="sp/nmos_cd_char_NO_DIFF_DIMESIONS.sp", type="nmos", use_area_and_perimeter=False)

        nmos = cd_char("sp/pmos_cd_char_NO_DIFF_DIMENSIONS.sp")
        nmos.run_sim()
        results.write("## NMOS Diffusion Capicatnace WITHOUT As Ad Ps Pd specified\n")
        results.write(nmos.tabulate())
        results.write("\n\n\n")

        if args.write_deck: 
            build.write_cd_char(output_file="sp/pmos_cd_char_NO_DIFF_DIMENSIONS.sp", type="pmos", use_area_and_perimeter=False)
        
        pmos = cd_char("sp/pmos_cd_char_NO_DIFF_DIMENSIONS.sp")
        pmos.run_sim()
        results.write("## PMOS Diffusion Capicatnace WITHOUT As Ad Ps Pd specified\n")
        results.write(pmos.tabulate())
        results.write("\n\n\n")

        if args.write_deck: 
            build.write_cd_char(output_file="sp/nmos_cd_char_EDIT_AREA.sp", type="nmos",edit_area=True)

        nmos = cd_char("sp/nmos_cd_char_EDIT_AREA.sp")
        nmos.run_sim()
        results.write("## NMOS Diffusion Capicatnace with As Ad Ps Pd edited\n")
        results.write(nmos.tabulate())
        results.write("\n\n\n")