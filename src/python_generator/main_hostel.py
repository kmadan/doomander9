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

    # Visible "second floor" over the lawn (UDMF 3D floor).
    # The actual playable second-floor wings are still connected via the stair teleports,
    # but this makes the upper level visible from the lawn.
    if hasattr(level, "lawn_tag"):
        builder.add_3d_floor_platform(
            target_sector_tag=level.lawn_tag,
            z=140,
            thickness=16,
            floor_tex="FLOOR4_8",
            ceil_tex="CEIL3_5",
            wall_tex="STARTAN3",
        )
    
    print("Adding Player Start...")
    # Place player in the corridor
    builder.add_player_start(128, 64, 0)

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
