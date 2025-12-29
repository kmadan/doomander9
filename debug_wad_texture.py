import sys
import os

# Add omgifol to path
current_dir = os.path.dirname(os.path.abspath(__file__))
omgifol_path = os.path.abspath(os.path.join(current_dir, "tools/omgifol"))
if omgifol_path not in sys.path:
    sys.path.append(omgifol_path)

from omg import *

def check_wad(wad_path):
    print(f"Checking WAD: {wad_path}")
    try:
        wad = WAD(wad_path)
        print("ZTextures:")
        for name in wad.ztextures:
            print(f"  {name}")
        
        if "PLUTOSGN" in wad.ztextures:
            print("SUCCESS: PLUTOSGN found in ztextures.")
        else:
            print("FAILURE: PLUTOSGN NOT found in ztextures.")
            
    except Exception as e:
        print(f"Error reading WAD: {e}")

if __name__ == "__main__":
    check_wad("build/py_hostel_full_raw.wad")
