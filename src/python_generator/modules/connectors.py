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

        # Doors must be operable from either side. To avoid depending on linedef
        # front/back orientation, we assign the door sector a (usually unique)
        # tag and have the door linedefs target that tag.
        #
        # If both adjacent rooms share a non-zero tag (used here as the "story" tag
        # for the 3D-floor second story), we still want the door sector to receive
        # the 3D floor even if we give it a unique action tag.
        shared_story_tag = 0
        t1 = getattr(self.room1, 'tag', 0) if self.room1 is not None else 0
        t2 = getattr(self.room2, 'tag', 0) if self.room2 is not None else 0
        if t1 and t1 == t2:
            shared_story_tag = int(t1)

        if self.tag:
            door_sector_tag = int(self.tag)
        else:
            door_sector_tag = int(builder.alloc_sector_tag())
            if shared_story_tag:
                builder.register_extra_3d_floor_target_tag(door_sector_tag)
        
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
                             tag=door_sector_tag) # Closed or Open
                             
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
                # Always set a tag so the UDMF conversion can target the door sector
                # reliably from either side.
                ld.tag = int(door_sector_tag)
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

        # If both adjacent rooms share the same non-zero tag, propagate it so
        # UDMF 3D floors can span through this opening.
        window_tag = 0
        t1 = getattr(self.room1, 'tag', 0) if self.room1 is not None else 0
        t2 = getattr(self.room2, 'tag', 0) if self.room2 is not None else 0
        if t1 and t1 == t2:
            window_tag = int(t1)

        builder.draw_polygon(points, 
                             floor_tex=self.floor_tex, 
                             ceil_tex=self.ceil_tex, 
                             wall_tex=self.wall_tex, # Side walls (jambs)
                             floor_height=base_floor + self.sill_height, 
                             ceil_height=base_floor + self.sill_height + self.window_height,
                             tag=window_tag)
                             
        # Iterate ALL linedefs to find those belonging to this window
        for ld in builder.editor.linedefs:
            front_sector = builder.editor.sidedefs[ld.front].sector
            back_sector = -1
            if ld.back != 0xFFFF:
                back_sector = builder.editor.sidedefs[ld.back].sector
                
            is_window_face = False
            
            # Case 1: Front is Window, Back is Room.
            if front_sector == window_sector_index and back_sector != -1 and back_sector != window_sector_index:
                # Clear mid texture on BOTH sides so the opening is not rendered as a solid wall.
                builder.editor.sidedefs[ld.front].tx_mid = "-"
                builder.editor.sidedefs[ld.back].tx_mid = "-"
                is_window_face = True
                
            # Case 2: Back is Window, Front is Room.
            elif back_sector == window_sector_index and front_sector != window_sector_index:
                # Clear mid texture on BOTH sides so the opening is not rendered as a solid wall.
                builder.editor.sidedefs[ld.front].tx_mid = "-"
                builder.editor.sidedefs[ld.back].tx_mid = "-"
                is_window_face = True
                
            if is_window_face:
                pass


class Portal(Connector):
    def __init__(
        self,
        x,
        y,
        width,
        height,
        room1,
        room2,
        *,
        source_line_id: int,
        target_line_id: int,
        type: int = 1,
        planeanchor: int = 1,
        floor_tex="FLOOR4_8",
        ceil_tex="CEIL3_5",
        wall_tex="STARTAN3",
    ):
        super().__init__(x, y, width, height, room1, room2)
        self.source_line_id = int(source_line_id)
        self.target_line_id = int(target_line_id)
        self.type = int(type)
        self.planeanchor = int(planeanchor)
        self.floor_tex = floor_tex
        self.ceil_tex = ceil_tex
        self.wall_tex = wall_tex

    def build(self, builder):
        # Create a simple passable connector sector between room1 and room2.
        portal_sector_index = len(builder.editor.sectors)

        points = [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height),
        ]

        base_floor = 0
        if getattr(self.room1, 'floor_height', None) is not None:
            base_floor = self.room1.floor_height
        elif getattr(self.room2, 'floor_height', None) is not None:
            base_floor = self.room2.floor_height

        ceil_h = base_floor + 128
        c1 = getattr(self.room1, 'ceil_height', None)
        c2 = getattr(self.room2, 'ceil_height', None)
        if c1 is not None or c2 is not None:
            ceil_h = max(int(c1 or 0), int(c2 or 0))

        builder.draw_polygon(
            points,
            floor_tex=self.floor_tex,
            ceil_tex=self.ceil_tex,
            wall_tex=self.wall_tex,
            floor_height=int(base_floor),
            ceil_height=int(ceil_h),
        )

        # Tag exactly one linedef between room1 and the portal sector so it becomes
        # a line portal source after UDMF conversion.
        #
        # We identify the intended shared edge geometrically.
        # (room1 touching portal left/right/top/bottom determines which portal edge is shared.)
        edge = None
        if self.room1 is not None:
            if self.x == self.room1.x + self.room1.width:
                edge = ((self.x, self.y), (self.x, self.y + self.height))
            elif self.x + self.width == self.room1.x:
                edge = ((self.x + self.width, self.y), (self.x + self.width, self.y + self.height))
            elif self.y == self.room1.y + self.room1.height:
                edge = ((self.x, self.y), (self.x + self.width, self.y))
            elif self.y + self.height == self.room1.y:
                edge = ((self.x, self.y + self.height), (self.x + self.width, self.y + self.height))

        def _v_xy(v):
            vx = int(getattr(v, 'x', 0))
            vy = int(getattr(v, 'y', 0))
            return (vx, vy)

        tagged = False
        if edge is not None:
            (ax, ay), (bx, by) = edge
            axy = (int(ax), int(ay))
            bxy = (int(bx), int(by))
            for ld in builder.editor.linedefs:
                if ld.back == 0xFFFF:
                    continue
                v1 = builder.editor.vertexes[ld.vx_a]
                v2 = builder.editor.vertexes[ld.vx_b]
                p1 = _v_xy(v1)
                p2 = _v_xy(v2)
                if not ((p1 == axy and p2 == bxy) or (p1 == bxy and p2 == axy)):
                    continue

                front_sector = builder.editor.sidedefs[ld.front].sector
                back_sector = builder.editor.sidedefs[ld.back].sector
                if portal_sector_index not in (front_sector, back_sector):
                    continue

                ld.tag = int(self.source_line_id)
                builder.editor.sidedefs[ld.front].tx_mid = "-"
                builder.editor.sidedefs[ld.back].tx_mid = "-"
                tagged = True
                break

        if not tagged:
            # Fallback: tag the first two-sided boundary line that touches the portal sector.
            for ld in builder.editor.linedefs:
                if ld.back == 0xFFFF:
                    continue
                front_sector = builder.editor.sidedefs[ld.front].sector
                back_sector = builder.editor.sidedefs[ld.back].sector
                if (front_sector == portal_sector_index and back_sector != portal_sector_index) or (back_sector == portal_sector_index and front_sector != portal_sector_index):
                    ld.tag = int(self.source_line_id)
                    builder.editor.sidedefs[ld.front].tx_mid = "-"
                    builder.editor.sidedefs[ld.back].tx_mid = "-"
                    tagged = True
                    break

        if not tagged:
            raise RuntimeError("Failed to tag portal linedef")

        builder.register_udmf_line_portal(
            source_line_id=self.source_line_id,
            target_line_id=self.target_line_id,
            type=self.type,
            planeanchor=self.planeanchor,
        )
