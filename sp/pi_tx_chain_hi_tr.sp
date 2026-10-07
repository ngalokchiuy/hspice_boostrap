* TX-line pi 10 segments
V1 in 0 PULSE(0 0.8 10p 200p 5.7p 1600p 1600p)
.ic v(in)=0
        
.subckt pi in out gnd R=100 C=10p
C0 in gnd c='C/2'
R0 in out r='R'
C1 out gnd c='C/2'
.ends pi
        X0 in 2 0 pi R=10.0 C=1e-13
X1 2 3 0 pi R=10.0 C=1e-13
X2 3 4 0 pi R=10.0 C=1e-13
X3 4 5 0 pi R=10.0 C=1e-13
X4 5 6 0 pi R=10.0 C=1e-13
X5 6 7 0 pi R=10.0 C=1e-13
X6 7 8 0 pi R=10.0 C=1e-13
X7 8 9 0 pi R=10.0 C=1e-13
X8 9 10 0 pi R=10.0 C=1e-13
X9 10 out 0 pi R=10.0 C=1e-13
.tran 0.01p 500p
.meas tran delay trig v(in) val=0.504 rise=1 targ v(out) val=0.504 rise=1

.option post=2 
.option delmax=0.01p  
*tighter tolerance
.option reltol=1e-6    
.option absv=1e-6      
.end

        
