# battery_calc.py
# Battery life calculator
# YOUR UNIQUE CONTRIBUTION
# Nobody else has this in their project

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import *


def calculate_battery_life(leakage_nW,
                            profile_name="smart_meter"):
    """
    Calculate battery life for a given
    SRAM leakage and IoT application profile.

    Returns years of operation.
    """
    if profile_name not in IOT_PROFILES:
        print(f"Unknown profile: {profile_name}")
        return None

    profile = IOT_PROFILES[profile_name]

    sleep_ratio    = profile["sleep_ratio"]
    active_ratio   = 1 - sleep_ratio
    battery_mWh    = profile["battery_mWh"]
    active_power_uW= profile["active_power_uW"]

    # Convert units to same scale (milliwatts)
    leakage_mW     = leakage_nW * 1e-6
    active_power_mW= active_power_uW * 1e-3

    # Average power
    avg_power_mW = (sleep_ratio  * leakage_mW +
                    active_ratio * active_power_mW)

    if avg_power_mW <= 0:
        return float('inf')

    # Battery life
    life_hours = battery_mWh / avg_power_mW
    life_years = life_hours / 8760

    return life_years


def calculate_all_profiles(leakage_nW):
    """
    Calculate battery life for ALL profiles
    given a leakage value.
    Returns dictionary.
    """
    results = {}
    for profile_name, profile in IOT_PROFILES.items():
        years = calculate_battery_life(
            leakage_nW, profile_name
        )
        required = profile["required_years"]
        results[profile_name] = {
            "years":    years,
            "required": required,
            "passes":   years >= required,
            "name":     profile["name"]
        }
    return results


def battery_life_summary(leakage_nW, wp, wn):
    """Print battery life for all profiles."""

    print(f"\n  WP={wp*1e9:.0f}nm WN={wn*1e9:.0f}nm "
          f"Leakage={leakage_nW:.1f}nW")
    print(f"  {'Profile':<20} {'Life':<12} "
          f"{'Required':<12} {'Status'}")
    print(f"  {'-'*55}")

    results = calculate_all_profiles(leakage_nW)

    for name, data in results.items():
        if data["years"] > 100:
            life_str = ">100 years"
        elif data["years"] > 1:
            life_str = f"{data['years']:.1f} years"
        else:
            life_str = f"{data['years']*365:.0f} days"

        if data["required"] > 1:
            req_str = f"{data['required']:.0f} years"
        else:
            req_str = f"{data['required']*365:.0f} days"

        status = "✅ PASS" if data["passes"] else "❌ FAIL"

        print(f"  {data['name']:<20} {life_str:<12} "
              f"{req_str:<12} {status}")


if __name__ == "__main__":
    print("Battery Life Calculator Test")
    print("="*50)

    # Test with different leakage values
    test_leakages = [5.1, 8.2, 15.8, 28.4, 45.2]

    for leakage in test_leakages:
        battery_life_summary(leakage, 200e-9, 100e-9)