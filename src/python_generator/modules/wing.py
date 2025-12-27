from .level import Level
from .geometry import Room, Corridor, Lawn
from .connectors import Door, Window
from .prefabs import Bedroom, Bathroom

class Wing:
    def __init__(self, x, y, side='left', num_rooms_per_side=7):
        self.x = x
        self.y = y
        self.side = side # 'left' means rooms are to the left of the corridor
        self.num_rooms_per_side = num_rooms_per_side
        self.room_width = 256
        self.room_height = 256
        self.corridor_width = 128
        self.wall_thickness = 16
        self.bathroom_width = 256 # Same as room for alignment, but maybe wider?
        self.bathroom_height = 512 # Double height? Or just a big room in the sequence?
        # "7 rooms on either side of the central large shared bathroom"
        # Sequence: 7 Rooms, Bathroom, 7 Rooms.
        
    def generate(self, level, lawn):
        # Calculate dimensions
        # We build vertically (North-South)
        
        # 1. Create Corridor
        # Total height = (RoomHeight + Wall) * (7 + 1 + 7) + Walls?
        # Actually, let's build rooms and calculate corridor height dynamically or just sum it up.
        # Bathroom height? Let's make it equal to 2 rooms? Or just 1 large room?
        # "Large shared bathroom". Let's make it 512 height (2 rooms worth).
        
        total_units = self.num_rooms_per_side * 2 + 2 # 7 rooms + 7 rooms + 2 slots for bathroom
        total_height = (self.room_height + self.wall_thickness) * total_units + self.wall_thickness
        
        corridor_x = self.x
        if self.side == 'left':
            # Rooms are Left (West) of Corridor.
            # Corridor X is self.x. Rooms are at self.x - RoomWidth - Wall.
            rooms_x = self.x - self.room_width - self.wall_thickness
            lawn_interface_x = self.x + self.corridor_width # East side of corridor faces lawn
        else:
            # Rooms are Right (East) of Corridor.
            # Corridor X is self.x. Rooms are at self.x + CorridorWidth + Wall.
            rooms_x = self.x + self.corridor_width + self.wall_thickness
            lawn_interface_x = self.x # West side of corridor faces lawn
            
        corridor = level.add_room(Corridor(corridor_x, self.y, self.corridor_width, total_height))
        
        # 2. Generate Rooms & Bathroom
        current_y = self.y + self.wall_thickness
        
        # First block of rooms
        for i in range(self.num_rooms_per_side):
            self._create_room(level, rooms_x, current_y, corridor)
            current_y += self.room_height + self.wall_thickness
            
        # Bathroom (Central)
        # Let's make it double height
        bath_height = self.room_height * 2 + self.wall_thickness
        bathroom = level.add_room(Bathroom(rooms_x, current_y, self.room_width, bath_height))
        
        # Door to Bathroom
        door_y = current_y + (bath_height // 2) - 32
        if self.side == 'left':
            door_x = corridor_x - self.wall_thickness
            level.add_connector(Door(door_x, door_y, self.wall_thickness, 64, bathroom, corridor))
        else:
            door_x = corridor_x + self.corridor_width
            level.add_connector(Door(door_x, door_y, self.wall_thickness, 64, bathroom, corridor))
            
        current_y += bath_height + self.wall_thickness
        
        # Second block of rooms
        for i in range(self.num_rooms_per_side):
            self._create_room(level, rooms_x, current_y, corridor)
            current_y += self.room_height + self.wall_thickness
            
        # 3. Corridor Windows to Lawn
        # Place windows along the lawn-facing side of the corridor
        # We can place one large window or multiple segments.
        # Let's place a window segment for every room unit to keep it structured.
        
        win_y = self.y + self.wall_thickness
        segment_height = self.room_height + self.wall_thickness
        
        for i in range(total_units):
            # Window Position
            # If side is left, corridor faces lawn on Right (East).
            # If side is right, corridor faces lawn on Left (West).
            
            wx = lawn_interface_x
            if self.side == 'right':
                wx -= self.wall_thickness # Adjust for wall thickness if on left side
                
            # Window connecting Corridor and Lawn
            # We need a "Lawn" sector or just open air?
            # The user said "The corridor looks upon a large lawn".
            # We should connect it to the 'lawn' object passed in.
            
            # Window height? Large panoramic windows.
            # Sill 32, Height 96.
            
            level.add_connector(Window(wx, win_y + 32, self.wall_thickness, 192, corridor, lawn, sill_height=32, window_height=96))
            
            win_y += segment_height
            
        return corridor

    def _create_room(self, level, x, y, corridor):
        room = level.add_room(Bedroom(x, y, self.room_width, self.room_height))
        
        # Door to Corridor
        # Centered vertically relative to room
        door_y = y + (self.room_height // 2) - 32
        
        if self.side == 'left':
            # Door on Right of Room
            door_x = x + self.room_width
            level.add_connector(Door(door_x, door_y, self.wall_thickness, 64, room, corridor))
            
            # Window on Left of Room (Opposite)
            # Needs an exterior sector. For now, let's create a small "WindowWell" lawn strip?
            # Or just let it look into void (which might look bad if sky isn't set).
            # Let's create a dummy exterior lawn for the back of the wing.
            pass # TODO: Exterior Window
        else:
            # Door on Left of Room
            door_x = x - self.wall_thickness
            level.add_connector(Door(door_x, door_y, self.wall_thickness, 64, room, corridor))
            
            # Window on Right of Room
            pass # TODO: Exterior Window
            
        # Create Exterior Window
        # We need a sector to connect to.
        # Let's create a local "Exterior" sector for this room.
        # It's a bit expensive to have 1 lawn per room.
        # Maybe the Wing should generate a "Backyard" lawn strip.
        
        # For now, let's create a small "Window Box" sector (Lawn type) attached to the window.
        window_box_depth = 64
        if self.side == 'left':
            # Window on Left (West)
            wb_x = x - window_box_depth
            wb = level.add_room(Lawn(wb_x, y, window_box_depth, self.room_height))
            level.add_connector(Window(wb_x + window_box_depth, y + 64, self.wall_thickness, 128, wb, room, sill_height=48, window_height=64))
        else:
            # Window on Right (East)
            wb_x = x + self.room_width + self.wall_thickness
            wb = level.add_room(Lawn(wb_x, y, window_box_depth, self.room_height))
            level.add_connector(Window(wb_x - self.wall_thickness, y + 64, self.wall_thickness, 128, wb, room, sill_height=48, window_height=64))
