Inverter Chain Using nf
.include ../models/22nm_HP.sp
.param x=5p
.param K=1.3
V1 vdd 0 DC 0.8
V2 vss 0 DC 0.0
        Vin in 0 PULSE(0.8 0 1n x x 10n 20n)

        .subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n w_scale=1 nfingers_n=1 nfingers_p=1
        .param w_p_tot='k*w_n*w_scale' 
        .param w_n_tot='w_n*w_scale'
        M1 out in vdd vdd pmos W='w_p_tot' L='l_p' nf='nfingers_p'
        M2 out in vss vss nmos W='w_n_tot' L='l_n' nf='nfingers_n'
        .ends inv

        X0 in 1 vdd vss inv k='K' w_scale=1 nfingers_n=1 nfingers_p=1
X1 1 2 vdd vss inv k='K' w_scale=2.37655650660739 nfingers_n=1 nfingers_p=1
X2 2 3 vdd vss inv k='K' w_scale=5.648020829097922 nfingers_n=2 nfingers_p=2
X3 3 4 vdd vss inv k='K' w_scale=13.422840650846734 nfingers_n=3 nfingers_p=4
X4 4 5 vdd vss inv k='K' w_scale=31.90013928592398 nfingers_n=7 nfingers_p=9
X5 5 6 vdd vss inv k='K' w_scale=75.81248358164466 nfingers_n=16 nfingers_p=20
X6 6 7 vdd vss inv k='K' w_scale=180.17265113802355 nfingers_n=37 nfingers_p=47
X7 7 8 vdd vss inv k='K' w_scale=428.1904863747733 nfingers_n=86 nfingers_p=112
X8 8 9 vdd vss inv k='K' w_scale=1017.6188864613505 nfingers_n=204 nfingers_p=265
X9 9 10 vdd vss inv k='K' w_scale=2418.428785866289 nfingers_n=484 nfingers_p=629
X10 10 out vdd vss inv k='K' w_scale=5747.532666817141 nfingers_n=1150 nfingers_p=1495
C0 out 0 1e-12
.tran 0.1p 10n
.meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 rise=1

.option post=2 
.end

        
