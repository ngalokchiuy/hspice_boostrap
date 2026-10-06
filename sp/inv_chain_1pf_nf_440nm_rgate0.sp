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
X1 1 2 vdd vss inv k='K' scale_val=2.37655650660739 nfingers_n=1 nfingers_p=1
X2 2 3 vdd vss inv k='K' scale_val=5.648020829097922 nfingers_n=1 nfingers_p=1
X3 3 4 vdd vss inv k='K' scale_val=13.422840650846734 nfingers_n=2 nfingers_p=2
X4 4 5 vdd vss inv k='K' scale_val=31.90013928592398 nfingers_n=4 nfingers_p=5
X5 5 6 vdd vss inv k='K' scale_val=75.81248358164466 nfingers_n=8 nfingers_p=10
X6 6 7 vdd vss inv k='K' scale_val=180.17265113802355 nfingers_n=19 nfingers_p=24
X7 7 8 vdd vss inv k='K' scale_val=428.1904863747733 nfingers_n=43 nfingers_p=56
X8 8 9 vdd vss inv k='K' scale_val=1017.6188864613505 nfingers_n=102 nfingers_p=133
X9 9 10 vdd vss inv k='K' scale_val=2418.428785866289 nfingers_n=242 nfingers_p=315
X10 10 out vdd vss inv k='K' scale_val=5747.532666817141 nfingers_n=575 nfingers_p=748
C0 out 0 1e-12
.tran 0.1p 10n
.meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 rise=1
.option post=2 
.end
