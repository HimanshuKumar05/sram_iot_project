# optimize.py — IoT Version
import os
import sys
import time
import pandas as pd
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import *
from generate_netlist import (generate_leakage_netlist,
                               generate_drv_netlist,
                               generate_snm_low_vdd_netlist,
                               generate_wakeup_netlist,
                               generate_write_margin_netlist)
from battery_calc import calculate_all_profiles
import subprocess


def run_ngspice(netlist_path, timeout=60):
    """Run NGSpice and return output text directly."""
    if not os.path.exists(netlist_path):
        return False, ""
    try:
        result = subprocess.run(
            [NGSPICE_PATH, "-b", netlist_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout + result.stderr
        # Also save to log file for debugging
        log_path = netlist_path.replace(".cir", ".log")
        with open(log_path, "w") as f:
            f.write(output)
        return True, output
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def parse_output(output, key):
    """Parse NGSpice output. Handles all formats."""
    if not output:
        return None

    lines = output.split("\n")

    # For leakage: find 'p' value under Vsource section
    # Format: "        p          -1.52258e-06"
    if key.lower() == "pleakage":
        found_vsource = False
        for line in lines:
            s = line.strip()
            if "vsource" in s.lower() or "vdd" in s.lower():
                found_vsource = True
            if found_vsource:
                parts = s.split()
                if len(parts) == 2 and parts[0] == "p":
                    try:
                        return abs(float(parts[1]))
                    except:
                        pass
        # Fallback: find last 'p' value anywhere
        for line in reversed(lines):
            s = line.strip()
            parts = s.split()
            if len(parts) == 2 and parts[0] == "p":
                try:
                    return abs(float(parts[1]))
                except:
                    pass

    # For measure outputs: "key = value"
    for line in lines:
        s = line.strip()
        if key.lower() in s.lower() and "=" in s:
            try:
                val = s.split("=")[1].strip().split()[0]
                return float(val)
            except:
                pass

    return None
def run_single_sizing(wp, wn, temp=27):
    """Run all simulations for one sizing."""

    result = {
        "WP_nm":        wp * 1e9,
        "WN_nm":        wn * 1e9,
        "temp_C":       temp,
        "leakage_nW":   None,
        "DRV_V":        None,
        "SNM_low_V":    None,
        "wakeup_ns":    None,
        "write_ok":     None,
        "q_min_write":  None,
        "sim_success":  False,
        "valid":        False
    }

    # Simulation 1 — Leakage Power
    try:
        netlist  = generate_leakage_netlist(wp, wn, temp)
        success, output = run_ngspice(netlist)
        if success and output:
            # Try measure output first
            power = parse_output(output, 'pleakage')
            if power is None:
                # Fall back to raw .op output
                # Look for 'p' value under Vsource
                for line in output.split('\n'):
                    s = line.strip()
                    if s.startswith('p ') or s.startswith('p\t'):
                        try:
                            power = abs(float(s.split()[1]))
                            break
                        except:
                            pass
            if power is not None:
                # p value from NGSpice is in watts
                result["leakage_nW"] = power * 1e9  # W to nW
    except Exception as e:
        print(f"    ⚠️  Leakage failed: {e}")

    # Simulation 2 — DRV (transient ramp method)
    try:
        netlist  = generate_drv_netlist(wp, wn, temp)
        success, output = run_ngspice(netlist)
        if success and output:
            # Find T_FLIP from transient output
            t_flip = None
            for line in output.split("\n"):
                s = line.strip()
                if "t_flip" in s.lower() and "=" in s:
                    try:
                        val = s.split("=")[1].strip().split()[0]
                        t_flip = float(val)
                    except:
                        pass
            if t_flip is not None:
                # VDD ramps 1.1V to 0.1V over 100ns
                drv = VDD - (t_flip / 100e-9) * (VDD - 0.1)
                result["DRV_V"] = round(drv, 3)
            else:
                # No flip = excellent retention
                result["DRV_V"] = 0.1
    except Exception as e:
        print(f"    ⚠️  DRV failed: {e}")

    # Simulation 3 — SNM via inverter VM at low VDD
    try:
        netlist  = generate_snm_low_vdd_netlist(wp, wn, temp)
        success, output = run_ngspice(netlist)
        if success and output:
            # VM = inverter switching point
            # SNM = deviation from ideal (VDD/2)
            vm = None
            for line in output.split("\n"):
                s = line.strip()
                if "vm" in s.lower() and "=" in s:
                    try:
                        val = s.split("=")[1].strip().split()[0]
                        vm = float(val)
                    except:
                        pass
            if vm is not None:
                # SNM approximation
                # Better VM symmetry = better SNM
                low_vdd = 0.5
                ideal_vm = low_vdd / 2
                snm = abs(vm - ideal_vm)
                result["SNM_low_V"] = round(snm, 4)
    except Exception as e:
        print(f"    ⚠️  SNM failed: {e}")

    # Simulation 4 — Wakeup
    try:
        netlist  = generate_wakeup_netlist(wp, wn, temp)
        success, output = run_ngspice(netlist)
        if success and output:
            wakeup = parse_output(output, 'wakeup_time')
            if wakeup is not None:
                result["wakeup_ns"] = abs(wakeup) * 1e9
    except Exception as e:
        print(f"    ⚠️  Wakeup failed: {e}")

    # Simulation 4 — Write Margin
    try:
        netlist = generate_write_margin_netlist(
            wp, wn, temp
        )
        success, output = run_ngspice(netlist)
        if success and output:
            q_min = None
            for line in output.split("\n"):
                s = line.strip()
                if "q_min" in s.lower() and "=" in s:
                    try:
                        val = s.split("=")[1].strip().split()[0]
                        q_min = float(val)
                    except:
                        pass
            if q_min is not None:
                result["q_min_write"] = q_min
                # Write succeeds if Q drops below 0.3V
                result["write_ok"] = q_min < 0.3
    except Exception as e:
        print(f"    ⚠️  Write margin failed: {e}")

    # Check success
    result["sim_success"] = result["leakage_nW"] is not None
    if result["sim_success"]:
        leakage_ok = (result["leakage_nW"] is not None and
                      result["leakage_nW"] <= MAX_LEAKAGE * 1e9)
        # Write must succeed for design to be valid
        write_ok = (result["write_ok"] is True)
        result["valid"] = leakage_ok and write_ok

    return result


def run_full_optimization(temp=27):
    """
    Run complete IoT SRAM optimization.
    Sweeps all WP/WN combinations.
    Returns DataFrame with all results.
    """

    total = len(WP_VALUES) * len(WN_VALUES)

    print("\n" + "="*60)
    print("  IoT LOW POWER SRAM OPTIMIZATION")
    print("="*60)
    print(f"  Technology:   45nm CMOS")
    print(f"  Cell:         6T SRAM")
    print(f"  Temperature:  {temp}°C")
    print(f"  Combinations: {total}")
    print(f"  Simulations:  {total * 4} total")
    print("="*60 + "\n")

    all_results = []
    completed   = 0
    start_time  = time.time()

    for wp in WP_VALUES:
        for wn in WN_VALUES:

            print(f"  [{completed+1}/{total}] "
                  f"WP={wp*1e9:.0f}nm "
                  f"WN={wn*1e9:.0f}nm...")

            result = run_single_sizing(wp, wn, temp)

            # Add battery life for each profile
            if result["leakage_nW"] is not None:
                battery_results = calculate_all_profiles(
                    result["leakage_nW"]
                )
                for profile, data in battery_results.items():
                    result[f"life_{profile}_yrs"] = (
                        data["years"]
                    )
                    result[f"pass_{profile}"] = (
                        data["passes"]
                    )

            all_results.append(result)
            completed += 1

            # Status line
            leak_str = (f"{result['leakage_nW']:.1f}nW"
                        if result["leakage_nW"]
                        else "N/A")
            drv_str  = (f"DRV={result['DRV_V']:.2f}V"
                        if result["DRV_V"]
                        else "DRV=N/A")

            elapsed   = time.time() - start_time
            remaining = (total-completed)*(elapsed/max(completed,1))

            print(f"         ✅ Leakage={leak_str} "
                  f"{drv_str} "
                  f"~{remaining:.0f}s left")

    # Convert to DataFrame
    df = pd.DataFrame(all_results)

    # Find Pareto optimal
    df = find_pareto(df)

    # Save results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    outfile = os.path.join(RESULTS_DIR,
                            "results_IoT_6T.csv")
    df.to_csv(outfile, index=False)

    total_time = time.time() - start_time

    print("\n" + "="*60)
    print("  OPTIMIZATION COMPLETE")
    print("="*60)
    print(f"  Time:    {total_time:.1f} seconds")
    print(f"  Valid:   {df['valid'].sum()} designs")
    print(f"  Pareto:  {df['pareto_optimal'].sum()} optimal")
    print(f"  Saved:   {outfile}")
    print("="*60)

    return df


def find_pareto(df):
    """
    Find Pareto optimal points.
    CONSTRAINT: write_ok must be True
    OPTIMIZE: minimize leakage AND minimize DRV
    
    This creates a REAL tradeoff:
    - Too small WN: low leakage BUT write fails
    - Too large WN: write passes BUT high leakage
    - Optimal: passes write with minimum leakage
    """
    df["pareto_optimal"] = False

    # CRITICAL: Only consider designs where write works
    # This is what makes smallest NOT always best
    if "write_ok" in df.columns:
        write_valid = df[df["write_ok"] == True]
        if len(write_valid) == 0:
            print("⚠️  No designs pass write margin")
            print("    Using all designs as fallback")
            write_valid = df.copy()
    else:
        write_valid = df.copy()

    valid = write_valid[
        write_valid["leakage_nW"].notna() &
        write_valid["DRV_V"].notna()
    ].copy()

    if len(valid) == 0:
        valid = write_valid[
            write_valid["leakage_nW"].notna()
        ].copy()
        if len(valid) == 0:
            return df
        min_idx = valid["leakage_nW"].idxmin()
        df.loc[min_idx, "pareto_optimal"] = True
        return df

    leak = valid["leakage_nW"].values
    drv  = valid["DRV_V"].values
    idx  = valid.index.values

    pareto = []
    for i in range(len(idx)):
        dominated = False
        for j in range(len(idx)):
            if i == j:
                continue
            if (leak[j] <= leak[i] and
                drv[j]  <= drv[i] and
                (leak[j] < leak[i] or
                 drv[j]  < drv[i])):
                dominated = True
                break
        if not dominated:
            pareto.append(idx[i])

    df.loc[pareto, "pareto_optimal"] = True
    return df

def print_recommendations(df):
    """Print sizing recommendations per application."""

    print("\n" + "="*70)
    print("  SIZING RECOMMENDATIONS PER IoT APPLICATION")
    print("="*70)

    pareto_df = df[df["pareto_optimal"] == True].copy()

    if len(pareto_df) == 0:
        print("  No Pareto optimal designs found")
        return

    for profile_name, profile in IOT_PROFILES.items():
        col = f"pass_{profile_name}"
        if col not in df.columns:
            continue

        passing = pareto_df[
            pareto_df[col] == True
        ].copy()

        if len(passing) == 0:
            print(f"\n  {profile['name']}: "
                  f"No sizing meets requirement ❌")
            continue

        # Best = minimum leakage that passes
        best = passing.sort_values(
            "leakage_nW"
        ).iloc[0]

        life_col = f"life_{profile_name}_yrs"
        life_val = best.get(life_col, 0)

        if life_val > 100:
            life_str = ">100 years"
        elif life_val > 1:
            life_str = f"{life_val:.1f} years"
        else:
            life_str = f"{life_val*365:.0f} days"

        print(f"\n  {profile['name']} "
              f"({profile['description']}):")
        print(f"  → Recommended: "
              f"WP={best['WP_nm']:.0f}nm "
              f"WN={best['WN_nm']:.0f}nm")
        print(f"  → Leakage:     "
              f"{best['leakage_nW']:.1f} nW")
        print(f"  → Battery life:{life_str} ✅")

    print("\n" + "="*70)


if __name__ == "__main__":
    df = run_full_optimization(temp=27)
    print_recommendations(df)