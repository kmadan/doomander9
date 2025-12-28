import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "omgifol")))
from omg import WAD  # type: ignore

wad_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build", "py_hostel_full.wad"))
w = WAD(wad_path)

m = next(iter(w.udmfmaps.keys()))
t = w.udmfmaps[m]["TEXTMAP"].data.decode("utf-8", errors="replace")

print("WAD:", wad_path)
print("UDMF map lump:", m)
print("Has any 'texturefloor = \"F_SKY1\"'?")
print("texturefloor = \"F_SKY1\"" in t)
print("Has any 'textureceiling = \"F_SKY1\"'?")
print("textureceiling = \"F_SKY1\"" in t)
