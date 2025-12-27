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
