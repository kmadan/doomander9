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
    
    print("Adding Player Start...")
    # Place player in the corridor
    builder.add_player_start(128, 64, 0)
    
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../build/py_hostel_full.wad"))
    print(f"Saving to {output_path}...")
    
    # Ensure build directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    builder.save(output_path)
    print("Done.")

if __name__ == "__main__":
    main()
