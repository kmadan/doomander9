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
    
    # Import custom textures
    assets_dir = os.path.abspath(os.path.join(current_dir, "../../assets"))
    gem_path = os.path.join(assets_dir, "pluto-gemini-1.png")
    if os.path.exists(gem_path):
        builder.import_texture("PLUTOGEM", gem_path)
    else:
        print(f"Warning: Sign texture not found at {gem_path}")

    print("Generating Hostel Layout...")
    generator = HostelGenerator(start_x=0, start_y=0)
    level = generator.generate()
    
    print("Building Level...")
    level.build(builder)

    # --- Visual facade: add 3D floors for main-floor wings ---
    # The main-floor wing sectors are tagged with 200 (see HostelGenerator).
    # We also apply the same 3D floors to any door sectors that received unique
    # action tags but still need the story floors (recorded by Door.build).
    facade_story_tag = 200
    facade_floor_zs = (128, 256)
    target_tags = [facade_story_tag] + sorted(builder.get_extra_3d_floor_target_tags())
    for tag in target_tags:
        for z in facade_floor_zs:
            builder.add_3d_floor_platform(
                target_sector_tag=int(tag),
                z=int(z),
                thickness=16,
                floor_tex="FLOOR4_8",
                ceil_tex="CEIL3_5",
                wall_tex="STONE2",
                alpha=255,
                flags=0,
            )

    # Second floor is now implemented as a disconnected/off-map area connected
    # via line portals (so doors can be independent per floor).
    
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
