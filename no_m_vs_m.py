import subprocess
import pathlib as pl
import hspice_parser as hp

def run_m_test():
    # Ensure directories exist
    for d in ["sp", "logs"]:
        pl.Path(d).mkdir(parents=True, exist_ok=True)

    # 1. Deck WITH m=1
    deck_m1 = """Inverter Test m=1
.include ../models/22nm_HP.sp
.param x=5p
V1 vdd 0 DC 0.8
V2 vss 0 DC 0.0
Vin in 0 PULSE(0.8 0 1n x x 10n 20n)

.subckt inv in out vdd vss k=1 w_n=44n l_n=22n l_p=22n
.param w_p='k*w_n' 
M1 out in vdd vdd pmos W='w_p' L='l_p' m=1
M2 out in vss vss nmos W='w_n' L='l_n' m=1
.ends inv

X1 in 1 vdd vss inv
X2 1 out vdd vss inv
C0 out 0 10p

.tran 0.1p 2000n
.meas tran delay trig v(in) val=0.4 fall=1 targ v(out) val=0.4 fall=1
.option post=2
.end
"""
    with open("sp/test_m1.sp", "w") as f:
        f.write(deck_m1)
    
    # 2. Deck WITHOUT m
    deck_nom = deck_m1.replace(" m=1", "")
    with open("sp/test_nom.sp", "w") as f:
        f.write(deck_nom.replace("Inverter Test m=1", "Inverter Test no m"))

    # 3. Run simulations
    subprocess.run(["hspice", "sp/test_m1.sp", "-o", "logs/test_m1.lis"])
    subprocess.run(["hspice", "sp/test_nom.sp", "-o", "logs/test_nom.lis"])

    # 4. Parse and compare results
    df_m1 = hp.parse_mto("logs/test_m1.mt0")
    df_nom = hp.parse_mto("logs/test_nom.mt0")

    delay_m1 = df_m1['delay'].values[0]
    delay_nom = df_nom['delay'].values[0]

    print("\n--- RESULTS ---")
    print(f"Delay with m=1: {delay_m1} seconds")
    print(f"Delay with no m: {delay_nom} seconds")
    
    if delay_m1 == delay_nom:
        print("Success: The simulation results are exactly identical!")

if __name__ == "__main__":
    run_m_test()