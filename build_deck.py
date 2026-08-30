# helper functions for writing decks
import os
def write_inv_7x(output_file:str="sp/inv_7x.sp",
        model_path:str="models/22nm_HP.sp",
        input_rise_time:float=10,
        vdd:float=0.8,
        k_start:float=0.5, k_stop:float=4, k_res:float=0.1
        ):

    header = f"""Inverter 7x Chain -- Exercise 1.a, hspice
.include ../{model_path}
.param K=0.5
.param x={input_rise_time}p
"""

    subckt = f"""
.subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n
    .param w_p='k*w_n'
    M1 out in vdd vdd pmos w='w_p' L='l_p'
    M2 out in vss vss nmos w='w_n' l='l_n'
.ends inv
"""
    ckt = f"""
* make the sources
V0 vdd 0 DC {vdd}
v1 vss 0 dc 0.0

X0 1 2 vdd vss inv k='K'
X1 2 3 vdd vss inv k='K'
X2 3 in vdd vss inv k='K'
X3 in out vdd vss inv k='K'
X4 out 6 vdd vss inv k='K'
X5 6 7 vdd vss inv k='K'
X6 7 8 vdd vss inv k='K'

Vin 1 0 PULSE(0.8 0 10p x x 80p 200p)
"""
    tran = f"""
* adding sweep
.tran 0.01p 200p SWEEP K LIN {(k_stop - k_start)/k_res} {k_start} {k_stop}
"""

    meas = """
.meas tran tplh trig v(in) val=0.4 fall=1 targ v(out) val=0.4 rise=1
.meas tran tphl trig v(in) val=0.4 rise=1 targ v(out) val=0.4 fall=1

* tr and tf using 10% & 90% of vdd=0.8 
.meas tran tr trig v(out) val=0.08 rise=1 targ v(out) val=0.72 rise=1
.meas tran tf trig v(out) val=0.72 fall=1 targ v(out) val=0.08 fall=1

.meas tran diff_tplh_tphl param='abs(tplh-tphl)'
.meas tran diff_tr_tf param='abs(tr-tf)'

*save output in ascii fomrat
.option post=2 
.option probe
* only save transient output of inverter of interest. Verify this works
.probe tran v(in) 
.probe tran v(out)
.end
"""

    deck = header + subckt + ckt + tran + meas
    with open (output_file, 'w') as out_sp:
        print(deck, file=out_sp)

    return

def write_inv_loop(output_file:str="sp/inv_loop.sp",
                    model_path:str="models/22nm_HP.sp",
                    inv_count:int=21,
                    input_rise_time:float=5.7,
                    vdd:float=0.8,
                    K:float=1.324,
                    gnd_start:float=0.0, gnd_stop:float=0.4, gnd_res:float=0.01):

    header = f"""Inverter 7x Chain -- Exercise 1.a, hspice
.include ../{model_path}
.param K={K}
.param x={input_rise_time}p
.param gnd_val=0
    """
    
    subckt = f"""
.subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n
    .param w_p='k*w_n'
    M1 out in vdd vdd pmos w='w_p' L='l_p'
    M2 out in vss vss nmos w='w_n' l='l_n'
.ends inv
    """
    ckt = f"""
* make the sources
V0 vdd 0 DC {vdd}
v1 vss 0 dc 'gnd_val'

.ic v(in)='gnd_val'\n
    """
    for i in range(inv_count):
        in_node = f"{i+1}"
        out_node = f"{i+2}"
        if i==0:
            in_node="in"
        if i==(inv_count-1):
            out_node="in" #<--------------should be easy to switch to a chain builder later using "out" instead
        ckt += f"x{i} {in_node} {out_node} vdd vss inv k='K' \n"
        


    tran = f"""
* adding sweep
.tran 0.01p 10000p SWEEP gnd_val LIN {int((gnd_stop-gnd_start)/gnd_res)} {gnd_start} {gnd_stop}
    """
    
    meas = """
.meas tran T trig v(in) val=0.4 fall=1 targ v(in) val=0.4 fall=2


.meas tran f param='1/T'
.meas tran T_over_42 param'T/42'

*save output in ascii format
.option post=2 
.option probe
.probe tran v(in)
.end
    """

    
    deck = header + subckt + ckt + tran + meas
    with open (output_file, 'w') as out_sp:
        print(deck, file=out_sp)

    return


def write_inv_loop_1x(output_file:str="sp/inv_loop.sp",
                    model_path:str="models/22nm_HP.sp",
                    input_rise_time:float=5.7,
                    vdd:float=0.8,
                    K:float=1.324,
                    k_start:float=0.3, k_stop:float=10, k_res:float=0.1):

    header = f"""Inverter SWP 1x loop
.include ../{model_path}
.param K={K}
.param x={input_rise_time}p
.param gnd_val=0
    """
    
    subckt = f"""
.subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n
    .param w_p='k*w_n'
    M1 out in vdd vdd pmos w='w_p' L='l_p'
    M2 out in vss vss nmos w='w_n' l='l_n'
.ends inv
    """
    ckt = f"""
* make the sources
V0 vdd 0 DC {vdd}
v1 vss 0 dc 'gnd_val'
"""
    
    ckt += f"x0 in in vdd vss inv k='K' \n"
        


    analysis = f"""
* secondary/nested sweeps require sweep keyword
.dc k start={k_start} stop={k_stop} step={k_res}
    """
    
    meas = """
*save output in ascii format
.option post=2 
.option probe
.probe V(in)
.end
    """

    
    deck = header + subckt + ckt + analysis + meas
    with open (output_file, 'w') as out_sp:
        print(deck, file=out_sp)

    return

