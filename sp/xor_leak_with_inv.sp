
.include ../models/22nm_HP.sp
.include ../models/hi_vt_22nm_HP.sp
.param w_n=44n l_n=22n w_p='k*w_n' l_p=22n
.param K=1.25

V1 vdd 0 DC 0.8
V2 vss 0 DC 0.0 
Va a 0 DC 0.8
Vb b 0 DC 0.8
        Mfoot foot_out vss vss vss nmos_hvt W='w_n' L='l_n'

.subckt xor A B out head_out foot_out pbulk nbulk k=1
.param w_n=44n l_n=22n w_p='k*w_n' l_p=22n

* Inverters for A and B (only used for use_inv == Flase!)
M5 A_b A head_out pbulk pmos W='w_p' L='l_p'
M6 A_b A foot_out nbulk nmos W='w_n' L='l_n'
M7 B_b B head_out pbulk pmos W='w_p' L='l_p'
M8 B_b B foot_out nbulk nmos W='w_n' L='l_n'

* XOR PMOS Network
M1 mid_p1 A head_out pbulk pmos W='w_p' L='l_p'
M2 out B_b mid_p1 pbulk pmos W='w_p' L='l_p'
M3 mid_p2 A_b head_out pbulk pmos W='w_p' L='l_p'
M4 out B mid_p2 pbulk pmos W='w_p' L='l_p'

* XOR NMOS Network
M9 mid_n1 A foot_out nbulk nmos W='w_n' L='l_n'
M10 out B mid_n1 nbulk nmos W='w_n' L='l_n'
M11 mid_n2 A_b foot_out nbulk nmos W='w_n' L='l_n'
M12 out B_b mid_n2 nbulk nmos W='w_n' L='l_n'

.ends xor

X0 a b out head_out foot_out vdd vss xor k='K'
        Mhead head_out vdd vdd vdd pmos_hvt W='w_p' L='l_p'
.tran 0.1p 10p
.meas tran i_leak avg I(V1) from=2p to=10p

.option post=2 reltol=1e-4 abstol=1e-15 gmindc=1e-15
.end
        
