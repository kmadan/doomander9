import os
from builder import WadBuilder
from generator import Level, Room, Door, Corridor, Lawn, Window

def main():
    print("Initializing WadBuilder...")
    builder = WadBuilder()
    
    level = Level()
    
    print("Creating Layout...")
    # Scale Factor: 3x
    
    # Room A (Hostel Room)
    # Original: 128x128 -> New: 384x384
    room_a = level.add_room(Room(0, 0, 384, 384, floor_tex="FLOOR0_1", wall_tex="BROWN96"))
    
    # Corridor
    # Original: 256x128 -> New: 768x384
    # Position: X=144 -> X=432 (384 + 48 gap? No, let's align it)
    # Let's place Corridor to the Right of Room A with a wall in between.
    # Room A ends at X=384.
    # Let's put Corridor at X=400 (16 unit wall thickness).
    corridor = level.add_room(Corridor(400, 0, 768, 384, floor_tex="CEIL5_2", wall_tex="STONE2"))
    
    # Door connecting Room A and Corridor
    # Position: X=384, Y=160 (Centered vertically in Room A? 384/2 = 192. Door width 64. Y=192-32=160)
    # Size: 16x64
    level.add_door(Door(384, 160, 16, 64, room_a, corridor))
    
    # Window connecting Room A and Corridor (just for fun/testing)
    # Position: X=384, Y=256
    # Size: 16x64
    level.add_window(Window(384, 256, 16, 64, room_a, corridor, sill_height=48, window_height=64))
    
    # Lawn
    # Original: 256x256 -> New: 768x768
    # Position: Right of Corridor? Or Below?
    # Let's put it below the Corridor.
    # Corridor Y=0 to 384.
    # Lawn Y = -784 (768 + 16 wall).
    lawn = level.add_room(Lawn(400, -784, 768, 768, floor_tex="RROCK19", wall_tex="BRICK7"))
    
    # Door connecting Corridor and Lawn
    # Position: X=784 (Centered in Corridor X=400+384=784), Y=-16 (Between 0 and -16)
    # Size: 64x16
    level.add_door(Door(752, -16, 64, 16, corridor, lawn, texture="SP_DUDE4"))
    
    print("Building Level...")
    level.build(builder)
    
    print("Adding Player Start...")
    builder.add_player_start(192, 192, 90)
    
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../build/py_hostel_test.wad"))
    print(f"Saving to {output_path}...")
    
    # Ensure build directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    builder.save(output_path)
    print("Done.")

if __name__ == "__main__":
    main()
