# main.py — IoT SRAM Project
# THIS IS THE FILE YOU RUN
# python3 main.py

import os
import sys
sys.path.append(os.path.join(
    os.path.dirname(__file__), "src"
))

from config import *
from optimize import (run_full_optimization,
                       print_recommendations)
from plot_results import generate_all_plots


def setup_folders():
    """Create all project folders."""
    for folder in [MODELS_DIR, NETLISTS_DIR,
                   GENERATED_DIR, RESULTS_DIR,
                   FIGURES_DIR, SRC_DIR]:
        os.makedirs(folder, exist_ok=True)


def check_model_file():
    """Check if PTM model file exists."""
    if not os.path.exists(MODEL_FILE):
        print("\n❌ Model file not found!")
        print(f"   Expected at: {MODEL_FILE}")
        print("\n   Please download from:")
        print("   http://ptm.asu.edu/")
        print("   Click: Bulk CMOS → 45nm")
        print(f"   Save as: {MODEL_FILE}")
        return False
    print(f"✅ Model file found")
    return True


def check_ngspice():
    """Check if NGSpice is installed."""
    if not os.path.exists(NGSPICE_PATH):
        print(f"\n❌ NGSpice not found at: {NGSPICE_PATH}")
        print("   Run: brew install ngspice")
        print("   Then run: which ngspice")
        print("   Update NGSPICE_PATH in src/config.py")
        return False
    print(f"✅ NGSpice found")
    return True


def main():

    print("\n" + "="*60)
    print("  IoT LOW POWER SRAM OPTIMIZATION FRAMEWORK")
    print("  BTech Final Year Project")
    print("="*60)

    # Setup
    setup_folders()

    # Checks
    if not check_ngspice():
        return
    if not check_model_file():
        return

    # Choose temperature
    print("\n  Choose simulation temperature:")
    print("  1. Room temperature only (27°C) — fastest")
    print("  2. Hot temperature (85°C) — IoT field test")
    print("  3. Both (27°C and 85°C)")
    print("  4. Full range (all 5 temperatures)")

    choice = input("\n  Enter choice (1/2/3/4): ").strip()

    if choice == "2":
        temps = [85]
    elif choice == "3":
        temps = [27, 85]
    elif choice == "4":
        temps = TEMPERATURES
    else:
        temps = [27]

    # Run optimization for each temperature
    all_dfs = []
    for temp in temps:
        df = run_full_optimization(temp=temp)
        all_dfs.append(df)
        print_recommendations(df)

    # Use room temperature results for plots
    import pandas as pd
    main_df = all_dfs[0]

    # Generate all plots
    print("\n  Generating plots...")
    generate_all_plots()

    # Final summary
    print("\n" + "="*60)
    print("  PROJECT OUTPUTS READY")
    print("="*60)
    print(f"\n  📄 Data:    {RESULTS_DIR}/results_IoT_6T.csv")
    print(f"  📊 Graphs:  {FIGURES_DIR}/")
    print("\n  Graphs generated:")
    for f in os.listdir(FIGURES_DIR):
        if f.endswith(".png"):
            print(f"    → {f}")

    print("\n" + "="*60)
    print("  USE THESE FOR YOUR REPORT AND PRESENTATION")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()