# generate_netlist.py FIXED
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import *

def generate_6T_cell(wp, wn):
    wa = wn * 1.0
    return f"""* 6T SRAM Cell
MP1 Q   QB  VDD VDD pmos W={wp:.3e} L={L_MIN:.3e}
MP2 QB  Q   VDD VDD pmos W={wp:.3e} L={L_MIN:.3e}
MN1 Q   QB  0   0   nmos W={wn:.3e} L={L_MIN:.3e}
MN2 QB  Q   0   0   nmos W={wn:.3e} L={L_MIN:.3e}
MA1 BL  WL  Q   0   nmos W={wa:.3e} L={L_MIN:.3e}
MA2 BLB WL  QB  0   nmos W={wa:.3e} L={L_MIN:.3e}
"""

def generate_leakage_netlist(wp, wn, temp=27, vdd=None):
    if vdd is None:
        vdd = VDD
    filename = f"leakage_wp{int(wp*1e9)}_wn{int(wn*1e9)}_t{temp}.cir"
    filepath = os.path.join(GENERATED_DIR, filename)
    netlist = f"""* Leakage Power Simulation
.include '{MODEL_FILE}'
{generate_6T_cell(wp, wn)}
Vdd VDD 0 {vdd}
Vwl WL  0 0
Vbl  BL  0 {vdd}
Vblb BLB 0 {vdd}
.ic V(Q)={vdd} V(QB)=0
.temp {temp}
.op
* Leakage read directly from .op output
* p value in Watts under Vsource section
.save V(Q) V(QB) I(Vdd)
.end
"""
    with open(filepath, "w") as f:
        f.write(netlist)
    return filepath

def generate_drv_netlist(wp, wn, temp=27):
    """DRV using transient ramp method."""
    filename = f"drv_wp{int(wp*1e9)}_wn{int(wn*1e9)}_t{temp}.cir"
    filepath = os.path.join(GENERATED_DIR, filename)
    vdd_start = VDD
    netlist = f"""* DRV Transient Method
.include '{MODEL_FILE}'
MP1 Q   QB  VDD VDD pmos W={wp:.3e} L={L_MIN:.3e}
MP2 QB  Q   VDD VDD pmos W={wp:.3e} L={L_MIN:.3e}
MN1 Q   QB  0   0   nmos W={wn:.3e} L={L_MIN:.3e}
MN2 QB  Q   0   0   nmos W={wn:.3e} L={L_MIN:.3e}
MA1 BL  WL  Q   0   nmos W={wn*1.5:.3e} L={L_MIN:.3e}
MA2 BLB WL  QB  0   nmos W={wn*1.5:.3e} L={L_MIN:.3e}
Vdd VDD 0 PWL(0 {vdd_start} 100n 0.1)
Vwl WL  0 0
Vbl  BL  0 {vdd_start}
Vblb BLB 0 {vdd_start}
.ic V(Q)={vdd_start} V(QB)=0.0
.temp {temp}
.tran 100p 100n
.measure tran T_FLIP when V(Q)={{0.3*{vdd_start}}} fall=1
.save V(Q) V(QB) V(VDD)
.end
"""
    with open(filepath, "w") as f:
        f.write(netlist)
    return filepath

def generate_snm_low_vdd_netlist(wp, wn, temp=27, low_vdd=0.5):
    """SNM via inverter switching point at low VDD."""
    filename = f"snm_lowvdd_wp{int(wp*1e9)}_wn{int(wn*1e9)}_t{temp}.cir"
    filepath = os.path.join(GENERATED_DIR, filename)
    half_vdd = low_vdd / 2
    netlist = f"""* SNM Low VDD via inverter VM
.include '{MODEL_FILE}'
MP_inv OUT IN VDD VDD pmos W={wp:.3e} L={L_MIN:.3e}
MN_inv OUT IN 0   0   nmos W={wn:.3e} L={L_MIN:.3e}
Vdd VDD 0 {low_vdd}
Vin IN  0 0
.temp {temp}
.dc Vin 0 {low_vdd} 0.005
.measure dc VM find V(OUT) when V(OUT)={half_vdd:.3f} fall=1
.save V(OUT) V(IN)
.end
"""
    with open(filepath, "w") as f:
        f.write(netlist)
    return filepath

def generate_wakeup_netlist(wp, wn, temp=27):
    filename = f"wakeup_wp{int(wp*1e9)}_wn{int(wn*1e9)}_t{temp}.cir"
    filepath = os.path.join(GENERATED_DIR, filename)
    netlist = f"""* Wakeup Simulation
.include '{MODEL_FILE}'
{generate_6T_cell(wp, wn)}
Vdd VDD 0 PWL(0 0.3 1n {VDD} 50n {VDD})
Vwl WL  0 0
Vbl  BL  0 {VDD}
Vblb BLB 0 {VDD}
.ic V(Q)=0.3 V(QB)=0.05
.temp {temp}
.tran 1e-12 50n
.measure tran WAKEUP_TIME trig V(VDD) val=0.55 rise=1 targ V(Q) val=0.99 rise=1
.save V(Q) V(QB) V(VDD)
.end
"""
    with open(filepath, "w") as f:
        f.write(netlist)
    return filepath

if __name__ == "__main__":
    os.makedirs(GENERATED_DIR, exist_ok=True)
    f1 = generate_leakage_netlist(200e-9, 100e-9)
    print(f"Generated: {f1}")
    f2 = generate_drv_netlist(200e-9, 100e-9)
    print(f"Generated: {f2}")
    f3 = generate_snm_low_vdd_netlist(200e-9, 100e-9)
    print(f"Generated: {f3}")
    f4 = generate_wakeup_netlist(200e-9, 100e-9)
    print(f"Generated: {f4}")
    print("Done")


def generate_write_margin_netlist(wp, wn, temp=27):
    """
    Write margin simulation.
    Tests if cell can be written successfully.
    Small WN = weak access transistor = write fails.
    This creates the REAL tradeoff:
    Small WN = low leakage BUT may fail write
    Large WN = passes write BUT high leakage
    """
    wa = wn * 1.0
    filename = (f"write_wp{int(wp*1e9)}"
                f"_wn{int(wn*1e9)}_t{temp}.cir")
    filepath = os.path.join(GENERATED_DIR, filename)

    netlist = f"""* Write Margin Test
* Tests if access transistor is strong enough
* to overpower pull-up PMOS during write
.include '{MODEL_FILE}'

MP1 Q   QB  VDD VDD pmos W={wp:.3e} L={L_MIN:.3e}
MP2 QB  Q   VDD VDD pmos W={wp:.3e} L={L_MIN:.3e}
MN1 Q   QB  0   0   nmos W={wn:.3e} L={L_MIN:.3e}
MN2 QB  Q   0   0   nmos W={wn:.3e} L={L_MIN:.3e}
MA1 BL  WL  Q   0   nmos W={wa:.3e} L={L_MIN:.3e}
MA2 BLB WL  QB  0   nmos W={wa:.3e} L={L_MIN:.3e}

* Write 0 into cell storing 1
* BL=0 BLB=VDD WL=VDD
Vdd  VDD 0 {VDD}
Vwl  WL  0 {VDD}
Vbl  BL  0 0
Vblb BLB 0 {VDD}

* Cell starts storing 1
.ic V(Q)={VDD} V(QB)=0.05

.temp {temp}
.tran 1e-12 5n

* Q must drop below 0.3V for write success
.measure tran Q_MIN  min V(Q)
.measure tran Q_FINAL find V(Q) at=4n

.save V(Q) V(QB) V(WL)
.end
"""
    with open(filepath, "w") as f:
        f.write(netlist)
    return filepath
