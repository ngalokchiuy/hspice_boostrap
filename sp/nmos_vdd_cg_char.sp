nmos_vdd gate capacitance characteristics
.include ../models/22nm_HP.sp
.param K=1.3
.param w_n=44n 
.param l_n=22n
.param l_p=22n
.param w_p='k*w_n'
.param vg_val=0.2
    * make the sources
    V0 vdd 0 DC 0.8
    v1 vss 0 dc 0
    vg vg 0 DC vg_val AC 0.001
    M1 vdd vg vss vdd nmos w='w_n' l='l_n'
.ac lin 1 1Meg 1Meg SWEEP vg_val 0.2 0.8 0.2

*save output in ascii format
.option post=2 
.option probe
*taking imaginary portion of output
.probe Ii(vg) Ir(vg) Vi(vg) vr(vg)
.end
    
