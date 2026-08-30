Inverter 7x Chain -- Exercise 1.a, hspice
.include ../models/22nm_HP.sp
.param K=1.324
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

.ic v(in)='gnd_val'

    x0 in 2 vdd vss inv k='K' 
x1 2 3 vdd vss inv k='K' 
x2 3 in vdd vss inv k='K' 

* adding sweep
.tran 0.01p 10000p SWEEP gnd_val LIN 40 0.0 0.4
    
.meas tran T trig v(in) val=0.4 fall=1 targ v(in) val=0.4 fall=2


.meas tran f param='1/T'
.meas tran T_over_42 param'T/42'

*save output in ascii format
.option post=2 
.option probe
.probe tran v(in)
.end
    
