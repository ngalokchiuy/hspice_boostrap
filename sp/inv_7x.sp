Inverter 7x Chain -- Exercise 1.a, hspice
.include ../models/22nm_HP.sp
.param K=0.5
.param x=10p

.subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n
    .param w_p='k*w_n'
    M1 out in vdd vdd pmos w='w_p' L='l_p'
    M2 out in vss vss nmos w='w_n' l='l_n'
.ends inv

* make the sources
V0 vdd 0 DC 0.8
v1 vss 0 dc 0.0

X0 1 2 vdd vss inv k='K'
X1 2 3 vdd vss inv k='K'
X2 3 in vdd vss inv k='K'
X3 in out vdd vss inv k='K'
X4 out 6 vdd vss inv k='K'
X5 6 7 vdd vss inv k='K'
X6 7 8 vdd vss inv k='K'

Vin 1 0 PULSE(0.8 0 10p x x 80p 200p)

* adding sweep
.tran 0.01p 200p SWEEP K LIN 35 0.5 4.0

.meas tran tplh trig v(in) val=0.4 fall=1 targ v(out) val=0.4 rise=1
.meas tran tphl trig v(in) val=0.4 rise=1 targ v(out) val=0.4 fall=1

* tr and tf using 10% & 90% of vdd=0.8 
.meas tran tr trig v(out) val=0.08 rise=1 targ v(out) val=0.72 rise=1
.meas tran tf trig v(out) val=0.72 fall=1 targ v(out) val=0.08 fall=1

.meas tran diff_tplh_tphl param='abs(tplh-tphl)'
.meas tran diff_tr_tf param='abs(tr-tf)'

.option post=2 *save output in ascii fomrat
.option probe
.probe tran v(in) * only save transient output of inverter of interest. Verify this works
.probe tran v(out)
