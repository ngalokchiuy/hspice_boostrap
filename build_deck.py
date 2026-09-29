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

Vin 1 0 PULSE(0.8 0 1n x x 1n 2n)
"""
    tran = f"""
* adding sweep
.tran 0.01p 3n SWEEP K LIN {(k_stop - k_start)/k_res + 1} {k_start} {k_stop}
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
                    K:float=1.3,
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
                    K:float=1.3,
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

def write_iv_char(output_file:str="sp/nmos_iv_char.sp",
                model_path:str="models/22nm_HP.sp",
                vdd:float=0.8,
                K:float=1.3,
                type:str="nmos", #or pmos
                vgs_start:float=0.4, vgs_stop:float=0.8, vgs_res:float=0.1,
                vds_start:float=0, vds_stop:float=0.8, vds_res:float=0.1):

    header = f"""Mos VI characteristics
.include ../{model_path}
.param K={K}
.param w_n=44n 
.param l_n=22n
.param l_p=22n
.param w_p='k*w_n'
    """
    ckt = f"""* make the sources
V0 vdd 0 DC {vdd}
v1 vss 0 dc 0
vg vg 0 DC 0.8
vds vds 0 DC 0.8
"""
    if type == "nmos":
        ckt += "M1 vds vg vss vss nmos w='w_n' l='l_n'\n"
        analysis = f".dc vds start={vds_start} stop={vds_stop} step={vds_res} vg start={vgs_start} stop={vgs_stop} step={vgs_res}\n"
    else:
        ckt += "M1 vds vg vss vss pmos w='w_p' L='l_p'\n"
        analysis = f".dc vds start={-1*vds_stop} stop={-1*vds_start} step={vds_res} vg start={-vgs_stop} stop={-vgs_start} step={vgs_res}\n"
    meas = """
*save output in ascii format
.option post=2 
.option probe
.probe I(vds)
.end
    """
    deck = header+ ckt + analysis + meas
    with open (output_file, 'w') as out_sp:
        print(deck, file=out_sp)

    return

def write_cg_char(output_file:str="sp/nmos_gnd_cg_char.sp",
                model_path:str="models/22nm_HP.sp",
                vdd:float=0.8,
                vac:float=0.001, #1 mv
                K:float=1.3,
                type:str="nmos_gnd", # nmos_vdd, pmos_vdd, pmos_gnd
                vg_start:float=0.25*0.8, vg_stop:float=0.8, vg_res:float=0.25*0.8):

    header = f"""{type} gate capacitance characteristics
.include ../{model_path}
.param K={K}
.param w_n=44n 
.param l_n=22n
.param l_p=22n
.param w_p='k*w_n'
.param vg_val={vg_start}
    """
    ckt = f"""* make the sources
    V0 vdd 0 DC {vdd}
    v1 vss 0 dc 0
    vg vg 0 DC vg_val AC {vac}
    """
    if type == "nmos_gnd":
        ckt += "M1 vss vg vss vss nmos w='w_n' l='l_n'\n"
    elif type == "nmos_vdd":
        ckt += "M1 vdd vg vdd vss nmos w='w_n' l='l_n'\n"
    elif type == "pmos_gnd":
        ckt += "M1 vss vg vss vdd pmos w='w_p' l='l_p'\n"
    elif type == "pmos_vdd":
        ckt += "M1 vdd vg vdd vdd pmos w='w_p' l='l_p'\n"

    analysis = f".ac lin 1 1Meg 1Meg SWEEP vg_val {vg_start} {vg_stop} {vg_res}\n"

    meas = """
*save output in ascii format
.option post=2 
.option probe
*taking imaginary portion of output
.probe Ii(vg) Ir(vg) Vi(vg) vr(vg)
.end
    """
#     meas = """
# .meas ac v_g 'Imag(V(vg))'
# .meas ac C_gate PARAM='(Imag(i(vg))/(image(V(vg)))/(2*3.1415*1Meg)'
# """
    deck = header+ ckt + analysis + meas
    with open (output_file, 'w') as out_sp:
        print(deck, file=out_sp)

    return


def write_cd_char(output_file:str="sp/nmos_cd_char.sp",
                model_path:str="models/22nm_HP.sp",
                vdd:float=0.8,
                vac:float=0.001, #1 mv
                K:float=1.3,
                type:str="nmos", # or pmos. Only two types now 
                vd_start:float=0, vd_stop:float=0.8, vd_res:float=0.25*0.8,
                use_area_and_perimeter:bool =True,
                edit_area:bool=False): # <-------------------------test with as ad ps and pd 

    # now must turn off gate. Measure diffusion using gnd or vdd on S and D

    header = f"""{type} Diffusion capacitance characteristics
.include ../{model_path}
.param K={K}
.param w_n=44n 
.param l_n=22n
.param l_p=22n
.param w_p='k*w_n'
.param vd_val={vd_start}
.param vac_val={vac}
    """
    diffusion_area = f"""
* added from bootstrap notes part 8
* it doesn't seem we count twice for the perimeter
.param as_n = 'w_n * l_n*1.5'
.param as_p = 'w_p * l_p*1.5'
.param ad_n = 'w_n * l_n*1.5'
.param ad_p = 'w_p * l_p*1.5'
.param ps_n = 'w_n + 3*l_n'
.param ps_p = 'w_p + 3*l_p'
.param pd_n = 'w_n + 3*l_n'
.param pd_p = 'w_p + 3*l_p'
"""
    if edit_area:
        diffusion_area = f"""
* added from bootstrap notes part 8
* it doesn't seem we count twice for the perimeter
.param as_n = 'w_n * l_n*1'
.param as_p = 'w_p * l_p*1'
.param ad_n = 'w_n * l_n*1'
.param ad_p = 'w_p * l_p*1'
.param ps_n = '2*w_n + 2*l_n'
.param ps_p = '2*w_p + 2*l_p'
.param pd_n = '2*w_n + 2*l_n'
.param pd_p = '2*w_p + 2*l_p'
        """

    ckt = f"""* make the sources
    V0 vdd 0 DC {vdd}
    v1 vss 0 dc 0
    vg vg 0 dc {0 if type=="nmos" else vdd}
    vd vd 0 DC vd_val AC {vac}
    """



    if type == "nmos":
        ckt += "M1 vd vg vss vss nmos w='w_n' l='l_n'"
    elif type == "pmos":
        ckt += "M1 vd vg vdd vdd pmos w='w_p' l='l_p'"
    if use_area_and_perimeter:
        ckt+= "ad='ad_n' as='as_n' pd='pd_n' ps='ps_n'\n"
    else:
        ckt += "\n"

    analysis = f".ac lin 1 1Meg 1Meg SWEEP vd_val {vd_start} {vd_stop} {vd_res}\n"

    meas = """
*save output in ascii format
.option post=2 
.option probe
*taking imaginary portion of output
.probe Ii(vd) Ir(vd) Vi(vd) vr(vd)
    """
# trying to get to work
#     meas += """
#     * Measure capacitance directly: C_diff = IMAG(I_vd) / (2 * pi * freq * V_ac)
#     .meas ac c_diff PARAM='abs(IMAG(I(vd))) / (2 * 3.14159265 * 1Meg * vac_val)'
# """

    deck = header+ diffusion_area + ckt + analysis + meas + ".end"
    with open (output_file, 'w') as out_sp:
        print(deck, file=out_sp)
    return