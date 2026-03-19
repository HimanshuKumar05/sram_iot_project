# test_setup.py
# Run this FIRST before anything else
# python3 test_setup.py

import os
import sys
import subprocess

print("\n" + "="*50)
print("  IoT PROJECT SETUP CHECK")
print("="*50)

# Python version
print(f"\n✅ Python {sys.version.split()[0]}")

# Libraries
for lib in ["numpy","pandas","matplotlib","scipy"]:
    try:
        __import__(lib)
        print(f"✅ {lib}")
    except:
        print(f"❌ {lib} — run: pip install {lib}")

# NGSpice
for path in ["/opt/homebrew/bin/ngspice",
             "/usr/local/bin/ngspice"]:
    if os.path.exists(path):
        print(f"✅ NGSpice at {path}")
        break
else:
    print("❌ NGSpice — run: brew install ngspice")

# Folders
base = os.path.expanduser("~/sram_iot_project")
for folder in ["models","netlists/generated",
               "results","figures","src"]:
    path = os.path.join(base, folder)
    if os.path.exists(path):
        print(f"✅ Folder: {folder}")
    else:
        print(f"❌ Folder missing: {folder}")
        print(f"   Run: mkdir -p {path}")

# Model file
model = os.path.join(base,"models","45nm_bulk.lib")
if os.path.exists(model):
    print("✅ 45nm model file")
else:
    print("❌ Model file missing")
    print("   Download from: http://ptm.asu.edu/")
    print(f"   Save to: {model}")

print("\n" + "="*50)
print("  All green → run: python3 main.py")
print("="*50 + "\n")