# view_results.py
# Simple clean output viewer
# python3 view_results.py

import os, sys, pandas as pd
sys.path.append("src")
from config import *
from battery_calc import calculate_battery_life

def view():
    csv = os.path.join(RESULTS_DIR,"results_IoT_6T.csv")
    if not os.path.exists(csv):
        print("No results. Run python3 main.py first")
        return

    df = pd.read_csv(csv)

    # ----------------------------------------
    # SUMMARY
    # ----------------------------------------
    print("\n" + "="*55)
    print("  SIMULATION SUMMARY")
    print("="*55)
    print(f"  Combinations simulated: {len(df)}")
    print(f"  Pareto optimal:         "
          f"{df['pareto_optimal'].sum()}")
    if "write_ok" in df.columns:
        print(f"  Write pass:             "
              f"{(df['write_ok']==True).sum()}")
        print(f"  Write fail:             "
              f"{(df['write_ok']==False).sum()}")

    # ----------------------------------------
    # ALL RESULTS TABLE
    # ----------------------------------------
    print("\n" + "="*55)
    print("  ALL RESULTS")
    print("="*55)
    print(f"  {'WP':>6} {'WN':>6} "
          f"{'Leak(nW)':>10} {'DRV(V)':>7} "
          f"{'Write':>6} {'Opt':>4}")
    print("  " + "-"*43)

    for _, r in df.sort_values("leakage_nW").iterrows():
        leak  = f"{r['leakage_nW']:.0f}" if pd.notna(r['leakage_nW']) else "N/A"
        drv   = f"{r['DRV_V']:.3f}"      if pd.notna(r['DRV_V'])      else "N/A"
        write = ("OK" if r.get('write_ok')==True
                 else "FAIL" if r.get('write_ok')==False
                 else "?")
        opt   = "★" if r['pareto_optimal'] else ""
        print(f"  {r['WP_nm']:>5.0f}n "
              f"{r['WN_nm']:>5.0f}n "
              f"{leak:>10} "
              f"{drv:>7} "
              f"{write:>6} "
              f"{opt:>4}")

    # ----------------------------------------
    # PARETO OPTIMAL ONLY
    # ----------------------------------------
    print("\n" + "="*55)
    print("  PARETO OPTIMAL SIZING RECOMMENDATIONS")
    print("="*55)

    pareto = df[df["pareto_optimal"]==True].sort_values("leakage_nW")

    print(f"\n  {'WP':>6} {'WN':>6} "
          f"{'Leak(nW)':>10} {'DRV(V)':>7} "
          f"{'Best For'}")
    print("  " + "-"*55)

    labels = ["Min leakage",
              "Balanced",
              "Low DRV",
              "Min DRV"]

    for i,(_, r) in enumerate(pareto.iterrows()):
        label = labels[i] if i < len(labels) else ""
        print(f"  {r['WP_nm']:>5.0f}n "
              f"{r['WN_nm']:>5.0f}n "
              f"{r['leakage_nW']:>10.0f} "
              f"{r['DRV_V']:>7.3f}  "
              f"{label}")

    # ----------------------------------------
    # BATTERY LIFE FOR PARETO DESIGNS
    # ----------------------------------------
    print("\n" + "="*55)
    print("  BATTERY LIFE — PARETO DESIGNS")
    print("="*55)

    for _, r in pareto.iterrows():
        print(f"\n  WP={r['WP_nm']:.0f}nm "
              f"WN={r['WN_nm']:.0f}nm "
              f"| Leakage={r['leakage_nW']:.0f}nW "
              f"DRV={r['DRV_V']:.3f}V")
        print(f"  {'Application':<22} "
              f"{'Battery Life':<14} "
              f"{'Required':<12} {'Status'}")
        print("  " + "-"*55)
        for name, p in IOT_PROFILES.items():
            life = calculate_battery_life(
                r["leakage_nW"], name
            )
            req  = p["required_years"]
            ls   = (f"{life:.1f} yrs"
                    if life > 1
                    else f"{life*365:.0f} days")
            rs   = (f"{req:.0f} yrs"
                    if req > 1
                    else f"{req*365:.0f} days")
            st   = "PASS" if life >= req else "FAIL"
            print(f"  {p['name']:<22} "
                  f"{ls:<14} {rs:<12} {st}")

    # ----------------------------------------
    # GRAPHS
    # ----------------------------------------
    print("\n" + "="*55)
    print("  SAVED GRAPHS")
    print("="*55)
    for f in sorted(os.listdir(FIGURES_DIR)):
        if f.endswith(".png"):
            sz = os.path.getsize(
                os.path.join(FIGURES_DIR,f)
            )//1024
            print(f"  {f:<35} {sz}KB")
    print(f"\n  Open: open {FIGURES_DIR}/*.png")
    print("="*55 + "\n")

if __name__ == "__main__":
    view()
