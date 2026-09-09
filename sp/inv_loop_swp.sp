Inverter SWP 1x loop
.include ../models/22nm_HP.sp
.param K=1.3
.param x=5.7p
.param gnd_val=0
    
.subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n
    .param w_p='k*w_n'
    M1 out in vdd vdd pmos w='w_p' L='l_p'
    M2 out in vss vss nmos w='w_n' l='l_n'
.ends inv
    
* make the sources
V0 vdd 0 DC 0.8
v1 vss 0 dc 'gnd_val'
x0 in in vdd vss inv k='K' 

* secondary/nested sweeps require sweep keyword
.dc k start=0.3 stop=10 step=0.1
    
*save output in ascii format
.option post=2 
.option probe
.probe V(in)
.end
    
