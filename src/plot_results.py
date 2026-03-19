# plot_results.py — IoT Version
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import *

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "font.size":        11,
})


def load_results():
    """Load IoT results CSV."""
    path = os.path.join(RESULTS_DIR,
                         "results_IoT_6T.csv")
    if not os.path.exists(path):
        print("❌ Run optimize.py first")
        return None
    df = pd.read_csv(path)
    print(f"✅ Loaded {len(df)} results")
    return df


def plot_pareto_curve(df):
    """Leakage vs DRV Pareto curve."""

    valid  = df[df["leakage_nW"].notna() &
                df["DRV_V"].notna()]
    pareto = df[df["pareto_optimal"] == True]

    fig, ax = plt.subplots(figsize=(10, 7))

    ax.scatter(valid["leakage_nW"],
               valid["DRV_V"],
               c="steelblue", alpha=0.6,
               s=100, label="All sizings",
               zorder=2)

    if len(pareto) > 0:
        ax.scatter(pareto["leakage_nW"],
                   pareto["DRV_V"],
                   c="red", s=200,
                   marker="*", zorder=4,
                   label="Pareto optimal ★")

        ps = pareto.sort_values("leakage_nW")
        ax.plot(ps["leakage_nW"],
                ps["DRV_V"],
                "r--", alpha=0.7,
                linewidth=1.5)

        for _, row in ps.iterrows():
            ax.annotate(
                f"WP={row['WP_nm']:.0f}n/"
                f"WN={row['WN_nm']:.0f}n",
                xy=(row["leakage_nW"],
                    row["DRV_V"]),
                xytext=(6, 6),
                textcoords="offset points",
                fontsize=8, color="darkred"
            )

    ax.set_xlabel(
        "Leakage Power (nW) — Lower = Longer Battery ←"
    )
    ax.set_ylabel(
        "Data Retention Voltage (V) — Lower = Better ↓"
    )
    ax.set_title(
        "IoT SRAM Optimization — Pareto Curve\n"
        "6T Cell 45nm | Leakage vs DRV Tradeoff"
    )
    ax.legend()

    ax.text(
        0.02, 0.98,
        "★ Pareto optimal = cannot reduce leakage\n"
        "   without increasing DRV",
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round",
                  facecolor="wheat", alpha=0.4)
    )

    path = os.path.join(FIGURES_DIR,
                         "pareto_iot.png")
    plt.savefig(path, dpi=300,
                bbox_inches="tight")
    print(f"✅ Pareto curve saved: {path}")
    plt.show()
def plot_battery_life(df):
    """
    Battery life bar chart per application.
    YOUR MOST POWERFUL VISUAL OUTPUT.
    Shows years of operation for each sizing.
    """

    pareto = df[df["pareto_optimal"] == True].copy()

    if len(pareto) == 0:
        print("❌ No Pareto data for battery chart")
        return

    profiles    = list(IOT_PROFILES.keys())
    profile_names = [IOT_PROFILES[p]["name"]
                     for p in profiles]

    # Use best overall sizing (min leakage Pareto)
    best = pareto.sort_values("leakage_nW").iloc[0]

    years = []
    for p in profiles:
        col = f"life_{p}_yrs"
        val = best.get(col, 0)
        years.append(min(val, 50))  # cap at 50 for display

    required = [IOT_PROFILES[p]["required_years"]
                for p in profiles]

    fig, ax = plt.subplots(figsize=(12, 7))

    x      = np.arange(len(profiles))
    width  = 0.35

    bars1 = ax.bar(x - width/2, years,
                    width, label="Achieved",
                    color="steelblue", alpha=0.8)
    bars2 = ax.bar(x + width/2, required,
                    width, label="Required",
                    color="orange", alpha=0.8)

    # Add value labels on bars
    for bar, val in zip(bars1, years):
        label = (f"{val:.1f}yr"
                 if val >= 1
                 else f"{val*365:.0f}d")
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 0.3,
                label, ha="center",
                fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(profile_names, rotation=15)
    ax.set_ylabel("Years of Operation")
    ax.set_title(
        f"Battery Life Per IoT Application\n"
        f"Optimal Sizing: WP={best['WP_nm']:.0f}nm "
        f"WN={best['WN_nm']:.0f}nm | "
        f"Leakage={best['leakage_nW']:.1f}nW"
    )
    ax.legend()

    # Add green check or red X
    for i, (ach, req) in enumerate(zip(years, required)):
        symbol = "✅" if ach >= req else "❌"
        ax.text(i, max(ach, req) + 1,
                symbol, ha="center", fontsize=14)

    plt.tight_layout()

    path = os.path.join(FIGURES_DIR,
                         "battery_life.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    print(f"✅ Battery life chart saved: {path}")
    plt.show()


def plot_leakage_comparison(df):
    """Bar chart of leakage for all sizings."""

    valid = df[df["leakage_nW"].notna()].copy()
    valid["sizing"] = (
        valid["WP_nm"].astype(int).astype(str) +
        "n/" +
        valid["WN_nm"].astype(int).astype(str) + "n"
    )
    valid = valid.sort_values("leakage_nW")

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ["green" if l <= MAX_LEAKAGE * 1e9
              else "red"
              for l in valid["leakage_nW"]]

    bars = ax.barh(valid["sizing"],
                    valid["leakage_nW"],
                    color=colors, alpha=0.8)

    for bar, val in zip(bars, valid["leakage_nW"]):
        ax.text(bar.get_width() + 0.2,
                bar.get_y() + bar.get_height()/2,
                f"{val:.1f}nW",
                va="center", fontsize=9)

    ax.axvline(x=MAX_LEAKAGE * 1e9,
               color="red", linestyle="--",
               linewidth=2,
               label=f"Max threshold "
                     f"({MAX_LEAKAGE*1e9:.0f}nW)")

    ax.set_xlabel("Leakage Power (nW)")
    ax.set_ylabel("WP/WN Sizing")
    ax.set_title(
        "Leakage Power — All Sizings\n"
        "Green = Within Budget | Red = Exceeds Budget"
    )
    ax.legend()
    plt.tight_layout()

    path = os.path.join(FIGURES_DIR,
                         "leakage_comparison.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    print(f"✅ Leakage comparison saved: {path}")
    plt.show()


def plot_drv_comparison(df):
    """DRV comparison across sizings."""

    valid = df[df["DRV_V"].notna()].copy()

    if len(valid) == 0:
        print("❌ No DRV data available")
        return

    valid["sizing"] = (
        valid["WP_nm"].astype(int).astype(str) +
        "n/" +
        valid["WN_nm"].astype(int).astype(str) + "n"
    )
    valid = valid.sort_values("DRV_V")

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ["green" if d <= MAX_DRV
              else "red"
              for d in valid["DRV_V"]]

    bars = ax.barh(valid["sizing"],
                    valid["DRV_V"],
                    color=colors, alpha=0.8)

    for bar, val in zip(bars, valid["DRV_V"]):
        ax.text(bar.get_width() + 0.002,
                bar.get_y() + bar.get_height()/2,
                f"{val:.3f}V",
                va="center", fontsize=9)

    ax.axvline(x=MAX_DRV, color="red",
               linestyle="--", linewidth=2,
               label=f"Max DRV ({MAX_DRV}V)")

    ax.set_xlabel("Data Retention Voltage (V) "
                  "— Lower is Better")
    ax.set_ylabel("WP/WN Sizing")
    ax.set_title(
        "Data Retention Voltage — All Sizings\n"
        "Lower DRV = Can sleep at lower voltage "
        "= Less leakage"
    )
    ax.legend()
    plt.tight_layout()

    path = os.path.join(FIGURES_DIR,
                         "drv_comparison.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    print(f"✅ DRV comparison saved: {path}")
    plt.show()




def plot_write_margin(df):
    """
    Shows which sizings pass/fail write margin.
    This is the KEY graph that shows why
    smallest transistors are NOT always best.
    """
    if "write_ok" not in df.columns:
        print("❌ No write margin data")
        return

    import matplotlib.patches as mpatches

    fig, ax = plt.subplots(figsize=(12, 7))

    pass_df = df[df["write_ok"] == True].copy()
    fail_df = df[df["write_ok"] == False].copy()
    none_df = df[df["write_ok"].isna()].copy()

    # Plot by leakage with color = write status
    if len(pass_df) > 0:
        pass_df["sizing"] = (
            pass_df["WP_nm"].astype(int).astype(str)
            + "n/" +
            pass_df["WN_nm"].astype(int).astype(str)
            + "n"
        )
        pass_df = pass_df.sort_values("leakage_nW")
        bars = ax.barh(pass_df["sizing"],
                       pass_df["leakage_nW"],
                       color="green", alpha=0.8,
                       label="Write OK ✅")
        for bar, val in zip(bars,
                            pass_df["leakage_nW"]):
            ax.text(bar.get_width() + 20,
                    bar.get_y() + bar.get_height()/2,
                    f"{val:.0f}nW",
                    va="center", fontsize=8)

    if len(fail_df) > 0:
        fail_df["sizing"] = (
            fail_df["WP_nm"].astype(int).astype(str)
            + "n/" +
            fail_df["WN_nm"].astype(int).astype(str)
            + "n"
        )
        fail_df = fail_df.sort_values("leakage_nW")
        bars2 = ax.barh(fail_df["sizing"],
                        fail_df["leakage_nW"],
                        color="red", alpha=0.8,
                        label="Write FAIL ❌")
        for bar, val in zip(bars2,
                            fail_df["leakage_nW"]):
            ax.text(bar.get_width() + 20,
                    bar.get_y() + bar.get_height()/2,
                    f"{val:.0f}nW",
                    va="center", fontsize=8,
                    color="red")

    ax.set_xlabel("Leakage Power (nW)")
    ax.set_ylabel("WP/WN Sizing")
    ax.set_title(
        "Write Margin vs Leakage — The Real Tradeoff\n"
        "Green = passes write (usable) | "
        "Red = write fails (unusable despite low leakage)"
    )
    ax.legend(fontsize=11)

    # Add explanation box
    ax.text(
        0.98, 0.02,
        "Key insight:\n"
        "Smallest transistors have lowest leakage\n"
        "BUT may fail write operation\n"
        "Optimal sizing must PASS write AND\n"
        "have minimum leakage",
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        horizontalalignment="right",
        bbox=dict(boxstyle="round",
                  facecolor="lightyellow",
                  alpha=0.8)
    )

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR,
                         "write_margin.png")
    plt.savefig(path, dpi=300,
                bbox_inches="tight")
    print(f"✅ Write margin graph saved: {path}")
    plt.show()

def generate_all_plots():
    """Generate every plot at once."""
    os.makedirs(FIGURES_DIR, exist_ok=True)
    df = load_results()
    if df is None:
        return
    print("\n📊 Generating all plots...")
    plot_pareto_curve(df)
    plot_battery_life(df)
    plot_leakage_comparison(df)
    plot_drv_comparison(df)
    plot_write_margin(df)
    print(f"\n✅ All figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    generate_all_plots()