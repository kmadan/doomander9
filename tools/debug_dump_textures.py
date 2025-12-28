import os
import sys
from collections import Counter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "omgifol")))
from omg import WAD  # type: ignore

wad_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build", "py_hostel_full.wad"))
wad = WAD(); wad.from_file(wad_path)

# For UDMF maps, omgifol stores them under `udmfmaps` (TEXTMAP...ENDMAP)
map_name = None
for name in wad.udmfmaps.keys():
    map_name = name
    break

if not map_name:
    raise RuntimeError("No UDMF maps found in WAD")

textmap = wad.udmfmaps[map_name]["TEXTMAP"].data.decode("utf-8", errors="replace")

print("WAD:", wad_path)
print("GRASS1 occurrences in TEXTMAP:", textmap.count('"GRASS1"'))
print("F_SKY1 occurrences in TEXTMAP:", textmap.count('"F_SKY1"'))

floors: list[str] = []
ceils: list[str] = []

# UDMF emitted by omgifol uses:
#   sector // 0
#   {
#     texturefloor = "...";
#     ...
#   }
pending_sector = False
in_sector = False
for line in textmap.splitlines():
    s = line.strip()
    if not in_sector and s.startswith("sector"):
        pending_sector = True
        continue
    if pending_sector and s == "{":
        in_sector = True
        pending_sector = False
        continue
    if in_sector:
        if s.startswith("texturefloor"):
            floors.append(s.split("=", 1)[1].strip().strip(";").strip().strip('"'))
        elif s.startswith("textureceiling"):
            ceils.append(s.split("=", 1)[1].strip().strip(";").strip().strip('"'))
        elif s == "}":
            in_sector = False

print("\nTop floor textures:")
for tex, count in Counter(floors).most_common(20):
    print(f"  {tex}: {count}")

print("\nTop ceiling textures:")
for tex, count in Counter(ceils).most_common(20):
    print(f"  {tex}: {count}")
