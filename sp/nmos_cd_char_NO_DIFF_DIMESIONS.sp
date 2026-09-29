nmos Diffusion capacitance characteristics
.include ../models/22nm_HP.sp
.param K=1.3
.param w_n=44n 
.param l_n=22n
.param l_p=22n
.param w_p='k*w_n'
.param vd_val=0
.param vac_val=0.001
    
* added from bootstrap notes part 8
* it doesn't seem we count twice for the perimeter
.param as_n = 'w_n * l_n*1.5'
.param as_p = 'w_p * l_p*1.5'
.param ad_n = 'w_n * l_n*1.5'
.param ad_p = 'w_p * l_p*1.5'
.param ps_n = 'w_n + 3*l_n'
.param ps_p = 'w_p + 3*l_p'
.param pd_n = 'w_n + 3*l_n'
.param pd_p = 'w_p + 3*l_p'
* make the sources
    V0 vdd 0 DC 0.8
    v1 vss 0 dc 0
    vg vg 0 dc 0
    vd vd 0 DC vd_val AC 0.001
    M1 vd vg vss vss nmos w='w_n' l='l_n'
.ac lin 1 1Meg 1Meg SWEEP vd_val 0 0.8 0.2

*save output in ascii format
.option post=2 
.option probe
*taking imaginary portion of output
.probe Ii(vd) Ir(vd) Vi(vd) vr(vd)
    .end
