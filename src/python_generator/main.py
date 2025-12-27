import os
from builder import WadBuilder
from generator import Level, Room, Door, Corridor, Lawn, Window, Wing

def main():
    print("Initializing WadBuilder...")
    builder = WadBuilder()
    
    level = Level()
    
    print("Creating Layout...")
    
    # --- Manual Test Area ---
    
    # Room A (Hostel Room)
    room_a = level.add_room(Room(0, 0, 384, 384, floor_tex="FLOOR0_1", wall_tex="BROWN96"))
    
    # Corridor (Right)
    corridor = level.add_room(Corridor(400, 0, 768, 384, floor_tex="CEIL5_2", wall_tex="STONE2"))
    
    # Door connecting Room A and Corridor (Right Wall)
    level.add_door(Door(384, 160, 16, 64, room_a, corridor))
    
    # Lawn (Left) - For the window to look at
    # Room A X=0. Lawn ends at X=-16.
    lawn_left = level.add_room(Lawn(-400, 0, 384, 384, floor_tex="RROCK19", wall_tex="BRICK7"))
    
    # Window connecting Room A and Lawn (Left Wall)
    # Position: X=-16, Y=160
    level.add_window(Window(-16, 160, 16, 64, lawn_left, room_a, sill_height=48, window_height=64))
    
    # Lawn (Bottom)
    lawn_bottom = level.add_room(Lawn(400, -784, 768, 768, floor_tex="RROCK19", wall_tex="BRICK7"))
    
    # Door connecting Corridor and Lawn Bottom
    level.add_door(Door(752, -16, 64, 16, corridor, lawn_bottom, texture="SP_DUDE4"))
    
    # --- Procedural Wing Test ---
    print("Generating Wing...")
    # Place a wing somewhere else, e.g., above Room A
    wing = Wing(x=0, y=512, num_rooms=3, room_width=256, room_height=256)
    wing.generate(level)
    
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
