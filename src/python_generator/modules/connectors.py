from .element import Element

class Connector(Element):
    def __init__(self, x, y, width, height, room1, room2):
        super().__init__(x, y)
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
    def __init__(self, x, y, width, height, room1, room2, texture="BIGDOOR2", state='closed', tag=0, linedef_action=1):
        super().__init__(x, y, width, height, room1, room2)
        self.texture = texture
        self.state = state
        self.tag = tag
        self.linedef_action = linedef_action
            
    def build(self, builder):
        # Draw door sector (Closed: Ceiling = Floor)
        base_floor = 0
        if getattr(self.room1, 'floor_height', None) is not None:
            base_floor = self.room1.floor_height
        elif getattr(self.room2, 'floor_height', None) is not None:
            base_floor = self.room2.floor_height

        ceil_h = base_floor
        if self.state == 'open':
            ceil_h = base_floor + 128
        
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
                             floor_height=base_floor, 
                             ceil_height=ceil_h,
                             tag=self.tag) # Closed or Open
                             
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
                # Set Action (optional)
                if self.linedef_action is not None and self.linedef_action != 0:
                    ld.action = self.linedef_action
                if self.tag:
                    ld.tag = self.tag
                # Set Unpegged
                ld.upper_unpeg = True
                pass

class Switch(Element):
    def __init__(self, x, y, action, tag):
        super().__init__(x, y)
        self.action = action
        self.tag = tag
        
    def register_cuts(self):
        pass
        
    def build(self, builder):
        # Build a small pillar
        width = 16
        height = 16
        
        points = [
            (self.x, self.y),
            (self.x + width, self.y),
            (self.x + width, self.y + height),
            (self.x, self.y + height)
        ]
        
        builder.draw_polygon(points, 
                             floor_tex="FLOOR4_8", 
                             ceil_tex="CEIL3_5", 
                             wall_tex="SW1STRTN", # Switch texture
                             floor_height=0, 
                             ceil_height=64)
                             
        # Find the sector (last one)
        sector_index = len(builder.editor.sectors) - 1
        
        for ld in builder.editor.linedefs:
            if builder.editor.sidedefs[ld.front].sector == sector_index:
                ld.action = self.action
                ld.tag = self.tag
                # Make sure texture is switch
                builder.editor.sidedefs[ld.front].tx_mid = "SW1STRTN"

class Window(Connector):
    def __init__(self, x, y, width, height, room1, room2, sill_height=32, window_height=64, floor_tex="FLOOR4_8", ceil_tex="CEIL3_5", wall_tex="STARTAN3"):
        super().__init__(x, y, width, height, room1, room2)
        self.sill_height = sill_height
        self.window_height = window_height
        self.floor_tex = floor_tex
        self.ceil_tex = ceil_tex
        self.wall_tex = wall_tex
        
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
        
        base_floor = 0
        if getattr(self.room1, 'floor_height', None) is not None:
            base_floor = self.room1.floor_height
        elif getattr(self.room2, 'floor_height', None) is not None:
            base_floor = self.room2.floor_height

        builder.draw_polygon(points, 
                             floor_tex=self.floor_tex, 
                             ceil_tex=self.ceil_tex, 
                             wall_tex=self.wall_tex, # Side walls (jambs)
                             floor_height=base_floor + self.sill_height, 
                             ceil_height=base_floor + self.sill_height + self.window_height)
                             
        # Iterate ALL linedefs to find those belonging to this window
        for ld in builder.editor.linedefs:
            front_sector = builder.editor.sidedefs[ld.front].sector
            back_sector = -1
            if ld.back != 0xFFFF:
                back_sector = builder.editor.sidedefs[ld.back].sector
                
            is_window_face = False
            
            # Case 1: Front is Window, Back is Room.
            if front_sector == window_sector_index and back_sector != -1 and back_sector != window_sector_index:
                builder.editor.sidedefs[ld.back].tx_mid = "-"
                is_window_face = True
                
            # Case 2: Back is Window, Front is Room.
            elif back_sector == window_sector_index and front_sector != window_sector_index:
                builder.editor.sidedefs[ld.front].tx_mid = "-"
                is_window_face = True
                
            if is_window_face:
                pass
