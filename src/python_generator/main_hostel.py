import os
import sys

# Add src to path to find modules
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, ".."))
if src_path not in sys.path:
    sys.path.append(src_path)

from builder import WadBuilder
from hostel_generator import HostelGenerator

def main():
    print("Initializing WadBuilder...")
    builder = WadBuilder()
    
    print("Generating Hostel Layout...")
    generator = HostelGenerator(start_x=0, start_y=0)
    level = generator.generate()
    
    print("Building Level...")
    level.build(builder)

    # Real 2nd story inside the building (UDMF 3D floor), not over the lawn.
    # Some sectors (notably door sectors) need unique tags for reliable door
    # behavior; we still apply the 3D floor to those tags too.
    if hasattr(level, "second_floor_tag"):
        tags = {int(level.second_floor_tag)}
        tags |= set(getattr(builder, "get_extra_3d_floor_target_tags", lambda: set())())
        for t in sorted(tags):
            builder.add_3d_floor_platform(
                target_sector_tag=t,
                z=140,
                thickness=16,
                floor_tex="FLOOR4_8",
                ceil_tex="CEIL3_5",
                wall_tex="STARTAN3",
            )
    
    print("Adding Player Start...")
    # Spawn point is chosen by the generator (for fast iteration/testing).
    spawn = getattr(level, "test_spawn", None)
    if spawn and isinstance(spawn, (tuple, list)) and len(spawn) >= 2:
        sx = int(spawn[0])
        sy = int(spawn[1])
        sa = int(spawn[2]) if len(spawn) >= 3 else 0
        builder.add_player_start(sx, sy, sa)
    else:
        # Fallback: a safe spot in the lawn.
        builder.add_player_start(256, 64, 0)

    # Always-visible debugging labels.
    
    # Write a raw UDMF map WAD. A nodebuilder (zdbsp) should post-process this into
    # the final playable WAD.
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../build/py_hostel_full_raw.wad"))
    print(f"Saving to {output_path}...")
    
    # Ensure build directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    builder.save(output_path)
    print("Done.")

if __name__ == "__main__":
    main()
