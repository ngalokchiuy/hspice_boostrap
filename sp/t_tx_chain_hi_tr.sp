* TX-line T 10 segments
V1 in 0 PULSE(0 0.8 10p 200p 5.7p 1600p 1600p)
.ic v(in)=0
        
.subckt T in out gnd R=100 C=10p
R0 in mid r='R/2'
C0 mid gnd c='C'
R1 mid out r='R/2'
.ends T
        X0 in 2 0 T R=10.0 C=1e-13
X1 2 3 0 T R=10.0 C=1e-13
X2 3 4 0 T R=10.0 C=1e-13
X3 4 5 0 T R=10.0 C=1e-13
X4 5 6 0 T R=10.0 C=1e-13
X5 6 7 0 T R=10.0 C=1e-13
X6 7 8 0 T R=10.0 C=1e-13
X7 8 9 0 T R=10.0 C=1e-13
X8 9 10 0 T R=10.0 C=1e-13
X9 10 out 0 T R=10.0 C=1e-13
.tran 0.01p 500p
.meas tran delay trig v(in) val=0.504 rise=1 targ v(out) val=0.504 rise=1

.option post=2 
.option delmax=0.01p  
*tighter tolerance
.option reltol=1e-6    
.option absv=1e-6      
.end

        
