Mos VI characteristics
.include ../models/22nm_HP.sp
.param K=1.3
.param w_n=44n 
.param l_n=22n
.param l_p=22n
.param w_p='k*w_n'
    * make the sources
V0 vdd 0 DC 0.8
v1 vss 0 dc 0
vg vg 0 DC 0.8
vds vds 0 DC 0.8
M1 vds vg vss vss pmos w='w_p' L='l_p'
.dc vds start=-0.8 stop=0 step=0.1 vg start=-0.8 stop=-0.4 step=0.1

*save output in ascii format
.option post=2 
.option probe
.probe I(vds)
.end
    
