## Code for iverter sizing chain originall for ngspice, converting to HSPICE
## Since this code requires iterative deck building, I am not building the chain seperately in build_deck
import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import graphing as graph
import hspice_parser as hp
# import build_deck as build <-- not used
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import pathlib as pl
import argparse
import pandas as pd


class inv_chain_builder:
    def __init__(self, sp_filename:str="inv_alpha_chain.sp",
                model_path: str = "models/22nm_HP.sp",
                c_load=1e-12,
                c_min=7.321e-17, #from exercise 4
                max_n:int = 10,
                vdd=0.8,
                # w_min=44e-9,
                # l_min=22e-9,
                k=1.3):
        self.base_name = pl.Path(sp_filename).stem
        self.model_path = model_path #used in builder
        self.sp_path = f"sp/{self.base_name}.sp"
        self.mt_path = f"logs/{self.base_name}.mt0" #only transient
        self.lis_path = f"logs/{self.base_name}.lis"
        self.vdd = vdd
        # self.w_min = w_min
        # self.l_min = l_min
        self.k = k
        self.c_load=c_load
        self.c_min=c_min
        self.M = c_load / c_min
        self.n_list, self.alpha_list = self.get_valid_alpha_n(max_n)
        self.df = pd.DataFrame(columns=[ 'delay', 'temper', 'alter#'  ])

        for dir in ["logs", "graphs", "data", "md"]:
            pl.Path(dir).mkdir(parents=True, exist_ok=True)
        pass

        # convert delay and alpha to arrays in main

        

    def get_valid_alpha_n(self, max_n_to_test):
        """get value pairs of (alpha, n) such that"""
        if self.M < 1:
            raise ValueError("Error: M must be greater than 1.")
        # n has to be integers
        n_list = list(range(3,max_n_to_test+1)) # <------------------------------chaning min n
        alpha_list = []

        for n in n_list:
            alpha = self.M ** (1/(n+1))
            alpha_list.append(alpha)
        return n_list, alpha_list

    # not called by main <------------------------------------- changed now to use multiplier for finger calc, not width
    def get_dims(self, n, alpha):
            """Calculate scaled MULTIPLIER (m) for each inverter. W and L are constant."""
            m_list = []
            for i in range(n):
                # The multiplier is simply alpha raised to the stage index
                m_scale = alpha ** (i + 1)
                m_list.append(m_scale)
            return m_list

    #TODO: recalibrate this for hspice
    def get_delay_per_alpha(self):
        for i in range(len(self.alpha_list)):
            n = self.n_list[i]
            alpha = self.alpha_list[i]
            
            # build netlist, write to sp_file
            self.build_deck( n, alpha)
                
            # run sim
            subprocess.run(["hspice",self.sp_path,"-o",self.lis_path])
            df = hp.parse_mto(self.mt_path) #get output data 
            #for debugging
            print(f"for alpha = {alpha} and n ={n}")
            print(self.df)

            # Concatenate DataFrames
            self.df = pd.concat([self.df, df], ignore_index=True)
      
            # print(f"for (alpha, n) = ({alpha, n}), delay = {self.delay_list[i]*1e12:.2f} ps")
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
        
        # use m, number of fingers/transistors in parallel. Weff ~ w*m
        # can't size indefinitely, found this out originally
        subckt = """
        .subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n m_inv=1
        .param w_p='k*w_n' 
        M1 out in vdd vdd pmos W='w_p' L='l_p' m='m_inv'
        M2 out in vss vss nmos W='w_n' L='l_n' m='m_inv'
        .ends inv\n
        """
        
        m_list = self.get_dims(n, alpha)

        first_inv = f"X0 in 1 vdd vss inv k='K' m_inv=1\n" # w_n={self.w_min} l_n={self.l_min}

        middle_invs = ""
        for i in range(1, n):
            m_scale = m_list[i-1]
            next_inv = f"X{i} {i} {i+1} vdd vss inv k='k' m_inv={m_scale}\n" #w_n={self.w_min} l_n={self.l_min}
            middle_invs += next_inv

        last_inv = f"X{n} {n} out vdd vss inv  k='k' m_inv={m_list[-1]}\n" # w_n={self.w_min} l_n={self.l_min} 

        load = f"C0 out 0 {self.c_load}\n"
        tran = ".tran 0.1p 10n\n"

        total_invs = n + 1
        if (total_invs % 2) != 0: #check if even or odd number inverters to see which edge we should catch on
            meas = ".meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 rise=1\n"
        else:
            meas = ".meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 fall=1\n"

        footer = f"""
.option post=2 
.end\n
        """
        spice_str = header + pwl + subckt + first_inv + middle_invs + last_inv + load + tran + meas +footer
        with open(self.sp_path, 'w') as sp:
            print(spice_str, file=sp)
        return 
 
    def graph(self, graph_dir:str="graphs"):
        # self.get_series() # nothing complicated, just load from df here
        delay = self.df["delay"]
        delay = delay * 1e12 #convert to ps
        alpha = np.array(self.alpha_list)
        min_idx = self.df['delay'].idxmin() #switched to pandas function
        alpha_best = np.array([self.alpha_list[min_idx]])
        n_best = self.n_list[min_idx]
        delay_best = np.array([self.df['delay'].min() *1e12])
    
        print(f"delay_best = {delay_best[0]} ps")
    
        extra_x = {f"(alpha, n) = ({alpha_best[0]:.2f},{n_best})": alpha_best}
        extra_y = {f"(alpha, n) = ({alpha_best[0]:.2f},{n_best})": delay_best}
        
        # Plot results
        plt.figure(1)
        graph.plot_series(
            x_data=alpha,
            y_dict={"delay (ps)":delay}, # Now contains multiple arrays!
            extra_x_dict=extra_x,
            extra_y_dict=extra_y,
            xlabel="alpha",
            ylabel="delay (ps)",
            title=f"Delay versus Alpha for C_load = 10pf, M={builder.M:.5f}",
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
    # Test execution
    builder = inv_chain_builder(sp_filename="inv_chain_1pf", model_path="models/22nm_HP.sp", c_load=1e-12, max_n=10)
    builder.get_delay_per_alpha()
    builder.graph()
    builder.tabulate()
    builder = inv_chain_builder(sp_filename="inv_chain_10pf", model_path="models/22nm_HP.sp", c_load=10e-12, max_n=10)
    builder.get_delay_per_alpha()
    builder.graph()
    builder.tabulate()
 
    