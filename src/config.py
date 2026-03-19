# config.py — IoT Low Power SRAM Project
import os

# ============================================
# NGSPICE PATH — Mac
# ============================================
NGSPICE_PATH = "/opt/homebrew/bin/ngspice"
# If above fails try:
# NGSPICE_PATH = "/usr/local/bin/ngspice"

# ============================================
# PROJECT FOLDERS
# ============================================
BASE_DIR      = os.path.expanduser("~/sram_iot_project")
MODELS_DIR    = os.path.join(BASE_DIR, "models")
NETLISTS_DIR  = os.path.join(BASE_DIR, "netlists")
GENERATED_DIR = os.path.join(BASE_DIR, "netlists", "generated")
RESULTS_DIR   = os.path.join(BASE_DIR, "results")
FIGURES_DIR   = os.path.join(BASE_DIR, "figures")
SRC_DIR       = os.path.join(BASE_DIR, "src")

# ============================================
# MODEL FILE
# ============================================
MODEL_FILE = os.path.join(MODELS_DIR, "45nm_bulk.lib")

# ============================================
# TECHNOLOGY
# ============================================
VDD      = 1.1      # Volts — 45nm nominal
L_MIN    = 45e-9    # 45nm channel length
TEMP_NOM = 27       # Room temperature

# ============================================
# SIZING COMBINATIONS TO SWEEP
# ============================================
WP_VALUES = [150e-9, 200e-9, 300e-9, 400e-9, 500e-9]
WN_VALUES = [100e-9, 150e-9, 200e-9, 250e-9]

# ============================================
# TEMPERATURES
# ============================================
TEMPERATURES = [37]

# ============================================
# IoT APPLICATION PROFILES
# ============================================
IOT_PROFILES = {
   
    "smart_meter": {
        "name":           "Smart Meter",
        "sleep_ratio":    0.999,
        "battery_mWh":    300,
        "active_power_uW":150,
        "temp_range":     [-20, 60],
        "required_years": 10,
        "description":    "Electricity/water/gas meters"
    },
    "medical": {
        "name":           "Medical Wearable",
        "sleep_ratio":    0.95,
        "battery_mWh":    150,
        "active_power_uW":500,
        "temp_range":     [30, 45],
        "required_years": 0.019,  # 7 days
        "description":    "Glucose monitors, cardiac"
    },
    "agricultural": {
        "name":           "Agricultural Sensor",
        "sleep_ratio":    0.99,
        "battery_mWh":    3000,
        "active_power_uW":200,
        "temp_range":     [-20, 85],
        "required_years": 5,
        "description":    "Soil, weather, crop sensors"
    },
    "industrial": {
        "name":           "Industrial Sensor",
        "sleep_ratio":    0.90,
        "battery_mWh":    1000,
        "active_power_uW":300,
        "temp_range":     [-40, 85],
        "required_years": 3,
        "description":    "Factory, oil/gas sensors"
    },
    "wearable": {
        "name":           "Consumer Wearable",
        "sleep_ratio":    0.80,
        "battery_mWh":    300,
        "active_power_uW":1000,
        "temp_range":     [10, 45],
        "required_years": 0.00274,  # 1 day
        "description":    "Smartwatch, fitness band"
    }
}

# ============================================
# QUALITY THRESHOLDS
# ============================================
MIN_HOLD_SNM  = 0.20   # Volts
MIN_READ_SNM  = 0.12   # Volts
MAX_LEAKAGE = 5000e-9  # 5000 nanoWatts
MAX_DRV       = 0.40   # Volts maximum DRV
MAX_WAKEUP    = 100e-9 # 100 nanoseconds

# ============================================
# SIMULATION SETTINGS
# ============================================
SNM_STEP   = 0.001    # DC sweep step
TRAN_STEP  = 1e-12    # 1 picosecond
TRAN_STOP  = 50e-9    # 50 nanoseconds

print("✅ IoT Config loaded")