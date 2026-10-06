Inverter Test m=1
.include ../models/22nm_HP.sp
.param x=5p
V1 vdd 0 DC 0.8
V2 vss 0 DC 0.0
Vin in 0 PULSE(0.8 0 1n x x 10n 20n)

.subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n
.param w_p='k*w_n' 
M1 out in vdd vdd pmos W='w_p' L='l_p' m=1
M2 out in vss vss nmos W='w_n' L='l_n' m=1
.ends inv

X1 in 1 vdd vss inv
X2 1 out vdd vss inv
C0 out 0 10p

.tran 0.1p 2000n
.meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 fall=1
.option post=2
.end
