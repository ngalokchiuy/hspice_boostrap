Inverter Chain
.include ../models/22nm_HP.sp
.param x=5p
.param K=1.3
V1 vdd 0 DC 0.8
V2 vss 0 DC 0.0
        Vin in 0 PULSE(0.8 0 1n x x 10n 20n)

        .subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n m_inv=1
        .param w_p='k*w_n' 
        M1 out in vdd vdd pmos W='w_p' L='l_p' m='m_inv'
        M2 out in vss vss nmos W='w_n' L='l_n' m='m_inv'
        .ends inv

        X0 in 1 vdd vss inv k='K' m_inv=1
X1 1 2 vdd vss inv k='k' m_inv=2.37655650660739
X2 2 3 vdd vss inv k='k' m_inv=5.648020829097922
X3 3 4 vdd vss inv k='k' m_inv=13.422840650846734
X4 4 5 vdd vss inv k='k' m_inv=31.90013928592398
X5 5 6 vdd vss inv k='k' m_inv=75.81248358164466
X6 6 7 vdd vss inv k='k' m_inv=180.17265113802355
X7 7 8 vdd vss inv k='k' m_inv=428.1904863747733
X8 8 9 vdd vss inv k='k' m_inv=1017.6188864613505
X9 9 10 vdd vss inv k='k' m_inv=2418.428785866289
X10 10 out vdd vss inv  k='k' m_inv=5747.532666817141
C0 out 0 1e-12
.tran 0.1p 10n
.meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 rise=1

.option post=2 
.end

        
