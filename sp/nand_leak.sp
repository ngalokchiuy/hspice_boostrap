
.include ../models/22nm_HP.sp
.include ../models/hi_vt_22nm_HP.sp
.param w_n=44n l_n=22n w_p='k*w_n' l_p=22n
.param K=1.25

V1 vdd 0 DC 0.8
V2 vss 0 DC 0.0 
Va a 0 DC 0.8
Vb b 0 DC 0.8
        Mfoot foot_out vss vss vss nmos_hvt W='w_n' L='l_n'

.subckt nand A B out head_out foot_out pbulk nbulk k=1
.param w_n=44n l_n=22n w_p='k*w_n' l_p=22n

M1 out A head_out pbulk pmos W='w_p' L='l_p'
M2 out B head_out pbulk pmos W='w_p' L='l_p'

M3 mid A foot_out nbulk nmos W='w_n' L='l_n'
M4 out B mid nbulk nmos W='w_n' L='l_n'

.ends nand

X0 a b out head_out foot_out vdd vss nand k='K'
        Mhead head_out vdd vdd vdd pmos_hvt W='w_p' L='l_p'
.tran 0.1p 10p
.meas tran i_leak avg I(V1) from=2p to=10p

.option post=2 
.end
        
