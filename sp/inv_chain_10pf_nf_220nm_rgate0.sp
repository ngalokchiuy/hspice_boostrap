Inverter Chain (nf Mode - rgate=0)
.include ../models/22nm_HP.sp
.param x=5p
.param K=1.3
V1 vdd 0 DC 0.8
V2 vss 0 DC 0.0
Vin in 0 PULSE(0.8 0 1n x x 10n 20n)

        .subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n scale_val=1 nfingers_n=1 nfingers_p=1
        .param w_p_tot='k*w_n*scale_val' 
        .param w_n_tot='w_n*scale_val'
        M1 out in vdd vdd pmos W='w_p_tot' L='l_p' nf='nfingers_p' rgatemod=0
        M2 out in vss vss nmos W='w_n_tot' L='l_n' nf='nfingers_n' rgatemod=0
        .ends inv
X0 in 1 vdd vss inv k='K' scale_val=1 nfingers_n=1 nfingers_p=1
X1 1 2 vdd vss inv k='K' scale_val=2.9299299402707484 nfingers_n=1 nfingers_p=1
X2 2 3 vdd vss inv k='K' scale_val=8.584489454894952 nfingers_n=2 nfingers_p=3
X3 3 4 vdd vss inv k='K' scale_val=25.151952675835233 nfingers_n=6 nfingers_p=7
X4 4 5 vdd vss inv k='K' scale_val=73.69345920120261 nfingers_n=15 nfingers_p=20
X5 5 6 vdd vss inv k='K' scale_val=215.9166725157244 nfingers_n=44 nfingers_p=57
X6 6 7 vdd vss inv k='K' scale_val=632.6207234074552 nfingers_n=127 nfingers_p=165
X7 7 8 vdd vss inv k='K' scale_val=1853.5343983472428 nfingers_n=371 nfingers_p=482
X8 8 9 vdd vss inv k='K' scale_val=5430.725929039315 nfingers_n=1087 nfingers_p=1412
X9 9 10 vdd vss inv k='K' scale_val=15911.646496896963 nfingers_n=3183 nfingers_p=4138
X10 10 out vdd vss inv k='K' scale_val=46620.00947026258 nfingers_n=9325 nfingers_p=12122
C0 out 0 1e-11
.tran 0.1p 10n
.meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 rise=1
.option post=2 
.end
