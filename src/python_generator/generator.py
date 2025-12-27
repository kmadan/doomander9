from builder import WadBuilder

class Level:
    def __init__(self):
        self.rooms = []
        self.connectors = []
        
    def add_room(self, room):
        self.rooms.append(room)
        return room
        
    def add_door(self, door):
        self.connectors.append(door)
        return door

    def add_window(self, window):
        self.connectors.append(window)
        return window
        
    def build(self, builder):
        # First, register cuts
        for conn in self.connectors:
            conn.register_cuts()
            
        # Build rooms
        for room in self.rooms:
            room.build(builder)
            
        # Build connectors
        for conn in self.connectors:
            conn.build(builder)

class Room:
    def __init__(self, x, y, width, height, floor_tex="FLOOR4_8", wall_tex="STARTAN3", ceil_tex="CEIL3_5", floor_height=0, ceil_height=128):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.floor_tex = floor_tex
        self.wall_tex = wall_tex
        self.ceil_tex = ceil_tex
        self.floor_height = floor_height
        self.ceil_height = ceil_height
        self.cuts = {
            'top': [],
            'bottom': [],
            'left': [],
            'right': []
        }
        
    def add_cut(self, side, offset):
        if offset not in self.cuts[side]:
            self.cuts[side].append(offset)
            
    def build(self, builder):
        for side in self.cuts:
            self.cuts[side].sort()
            
        points = []
        # Bottom (Left -> Right)
        points.append((self.x, self.y))
        for cut in self.cuts['bottom']:
            points.append((self.x + cut, self.y))
        points.append((self.x + self.width, self.y))
        
        # Right (Bottom -> Top)
        for cut in self.cuts['right']:
            points.append((self.x + self.width, self.y + cut))
        points.append((self.x + self.width, self.y + self.height))
        
        # Top (Right -> Left)
        for cut in reversed(self.cuts['top']):
            points.append((self.x + cut, self.y + self.height))
        points.append((self.x, self.y + self.height))
        
        # Left (Top -> Bottom)
        for cut in reversed(self.cuts['left']):
            points.append((self.x, self.y + cut))
            
        # Filter unique
        unique_points = []
        for p in points:
            if not unique_points or unique_points[-1] != p:
                unique_points.append(p)
        if len(unique_points) > 0 and unique_points[0] == unique_points[-1]:
            unique_points.pop()
            
        builder.draw_polygon(unique_points, 
                             floor_tex=self.floor_tex, 
                             ceil_tex=self.ceil_tex, 
                             wall_tex=self.wall_tex,
                             floor_height=self.floor_height,
                             ceil_height=self.ceil_height)

class Connector:
    def __init__(self, x, y, width, height, room1, room2):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.room1 = room1
        self.room2 = room2

    def register_cuts(self):
        # Determine relationship with room1
        if self.room1: self._add_cut_to_room(self.room1)
        if self.room2: self._add_cut_to_room(self.room2)
        
    def _add_cut_to_room(self, room):
        # Check overlap with room edges
        # If Connector Left == Room Right
        if self.x == room.x + room.width:
            # Touching Right Edge
            room.add_cut('right', self.y - room.y)
            room.add_cut('right', (self.y + self.height) - room.y)
        # If Connector Right == Room Left
        elif self.x + self.width == room.x:
            # Touching Left Edge
            room.add_cut('left', self.y - room.y)
            room.add_cut('left', (self.y + self.height) - room.y)
        # If Connector Bottom == Room Top
        elif self.y == room.y + room.height:
            # Touching Top Edge
            room.add_cut('top', self.x - room.x)
            room.add_cut('top', (self.x + self.width) - room.x)
        # If Connector Top == Room Bottom
        elif self.y + self.height == room.y:
            # Touching Bottom Edge
            room.add_cut('bottom', self.x - room.x)
            room.add_cut('bottom', (self.x + self.width) - room.x)

class Door(Connector):
    def __init__(self, x, y, width, height, room1, room2, texture="BIGDOOR2"):
        super().__init__(x, y, width, height, room1, room2)
        self.texture = texture
            
    def build(self, builder):
        # Draw door sector (Closed: Ceiling = Floor)
        
        # Capture the sector index before drawing (it will be the next one appended)
        door_sector_index = len(builder.editor.sectors)
        
        points = [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height)
        ]
        
        builder.draw_polygon(points, 
                             floor_tex="FLOOR4_8", 
                             ceil_tex="FLAT20", # Door ceiling
                             wall_tex="DOORTRAK", # Side walls
                             floor_height=0, 
                             ceil_height=0) # Closed
                             
        # Iterate ALL linedefs to find those belonging to this door
        for ld in builder.editor.linedefs:
            # Check if this linedef is connected to the door sector
            front_sector = builder.editor.sidedefs[ld.front].sector
            back_sector = -1
            if ld.back != 0xFFFF:
                back_sector = builder.editor.sidedefs[ld.back].sector
                
            is_door_face = False
            
            if front_sector == door_sector_index and back_sector != -1 and back_sector != door_sector_index:
                # Front is Door, Back is Room.
                # This means the "Room Side" is the Back Side.
                # We want the texture on the Back Side Upper.
                builder.editor.sidedefs[ld.back].tx_up = self.texture
                is_door_face = True
                
            elif back_sector == door_sector_index and front_sector != door_sector_index:
                # Back is Door, Front is Room.
                # This means the "Room Side" is the Front Side.
                # We want the texture on the Front Side Upper.
                builder.editor.sidedefs[ld.front].tx_up = self.texture
                is_door_face = True
                
            if is_door_face:
                # Set Action
                ld.action = 1 # DR Door Open Wait Close
                # Set Unpegged
                ld.upper_unpeg = True
                # Ensure the door side has no mid texture (it might have been swapped in)
                # And ensure the room side has no mid texture
                # (Actually, omgifol might have moved the room's wall texture to Upper/Lower, which is what we want for the room side)
                # But we just overwrote the Room Side Upper with the Door Texture.
                pass

class Window(Connector):
    def __init__(self, x, y, width, height, room1, room2, sill_height=32, window_height=64):
        super().__init__(x, y, width, height, room1, room2)
        self.sill_height = sill_height
        self.window_height = window_height
        
    def build(self, builder):
        # Draw window sector
        # Floor = Sill Height
        # Ceiling = Sill Height + Window Height
        
        window_sector_index = len(builder.editor.sectors)
        
        points = [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height)
        ]
        
        builder.draw_polygon(points, 
                             floor_tex="FLOOR4_8", 
                             ceil_tex="CEIL3_5", 
                             wall_tex="STARTAN3", # Side walls (jambs)
                             floor_height=self.sill_height, 
                             ceil_height=self.sill_height + self.window_height)
                             
        # Iterate ALL linedefs to find those belonging to this window
        for ld in builder.editor.linedefs:
            front_sector = builder.editor.sidedefs[ld.front].sector
            back_sector = -1
            if ld.back != 0xFFFF:
                back_sector = builder.editor.sidedefs[ld.back].sector
                
            is_window_face = False
            
            # We need to ensure the Upper and Lower textures are set on the Room Side
            # to fill the gap above and below the window.
            # omgifol's draw_sector might have already set some defaults, but let's be sure.
            
            # Usually, if there is a height difference, the engine renders the Upper/Lower texture 
            # of the sidedef facing the sector with the height difference.
            
            # Case 1: Front is Window, Back is Room.
            if front_sector == window_sector_index and back_sector != -1 and back_sector != window_sector_index:
                # Room is Back.
                # We want Back Upper and Back Lower to be the Room's wall texture.
                # (Assuming Room class sets wall_tex on its sidedefs, which it does).
                # But we might want to override or ensure it.
                # Also, we might want to clear the Mid texture if it's an open window.
                builder.editor.sidedefs[ld.back].tx_mid = "-"
                is_window_face = True
                
            # Case 2: Back is Window, Front is Room.
            elif back_sector == window_sector_index and front_sector != window_sector_index:
                # Room is Front.
                builder.editor.sidedefs[ld.front].tx_mid = "-"
                is_window_face = True
                
            if is_window_face:
                # Ensure impassable is FALSE (it's a window, maybe jumpable?)
                # If it's too high, the engine handles it.
                # But we must ensure the linedef is two-sided (it is).
                pass

class Wing:
    def __init__(self, x, y, num_rooms, room_width=128, room_height=128, corridor_width=64, wall_thickness=16):
        self.x = x
        self.y = y
        self.num_rooms = num_rooms
        self.room_width = room_width
        self.room_height = room_height
        self.corridor_width = corridor_width
        self.wall_thickness = wall_thickness
        self.rooms = []
        self.corridor = None
        
    def generate(self, level):
        # Create Corridor
        # Length = (Room Width + Wall) * Num Rooms + Wall
        total_length = (self.room_width + self.wall_thickness) * self.num_rooms + self.wall_thickness
        
        # Corridor is below the rooms
        corridor_y = self.y - self.corridor_width - self.wall_thickness
        self.corridor = level.add_room(Corridor(self.x, corridor_y, total_length, self.corridor_width))
        
        current_x = self.x + self.wall_thickness
        
        for i in range(self.num_rooms):
            # Create Room
            room = level.add_room(Room(current_x, self.y, self.room_width, self.room_height))
            self.rooms.append(room)
            
            # Create Door connecting Room to Corridor
            # Door X centered in room
            door_x = current_x + (self.room_width // 2) - 32 # 64 width door
            door_y = self.y - self.wall_thickness
            
            level.add_door(Door(door_x, door_y, 64, self.wall_thickness, room, self.corridor))
            
            current_x += self.room_width + self.wall_thickness

class Corridor(Room):
    def __init__(self, x, y, width, height, floor_tex="FLOOR0_1", wall_tex="STONE2", ceil_tex="CEIL3_5"):
        super().__init__(x, y, width, height, floor_tex, wall_tex, ceil_tex)

class Lawn(Room):
    def __init__(self, x, y, width, height, floor_tex="RROCK19", wall_tex="BRICK7"):
        super().__init__(x, y, width, height, floor_tex, wall_tex, ceil_tex="F_SKY1", ceil_height=256)

