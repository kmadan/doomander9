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
    def __init__(self, x, y, action, tag, room=None, room2=None):
        super().__init__(x, y)
        self.action = action
        self.tag = tag
        self.room = room
        self.room2 = room2
        self.width = 16
        self.height = 16
        
    def register_cuts(self):
        rooms = []
        if self.room: rooms.append(self.room)
        if self.room2: rooms.append(self.room2)
        
        for room in rooms:
            # Check overlap with room edges
            # If Switch Left == Room Right
            if self.x == room.x + room.width:
                room.add_cut('right', self.y - room.y)
                room.add_cut('right', (self.y + self.height) - room.y)
            # If Switch Right == Room Left
            elif self.x + self.width == room.x:
                room.add_cut('left', self.y - room.y)
                room.add_cut('left', (self.y + self.height) - room.y)
            # If Switch Bottom == Room Top
            elif self.y == room.y + room.height:
                room.add_cut('top', self.x - room.x)
                room.add_cut('top', (self.x + self.width) - room.x)
            # If Switch Top == Room Bottom
            elif self.y + self.height == room.y:
                room.add_cut('bottom', self.x - room.x)
                room.add_cut('bottom', (self.x + self.width) - room.x)
        
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
        
        # Identify the "Back" face of the switch (where the texture should be).
        # The switch is a niche. The "Back" is the wall furthest from the room it faces.
        # If it faces North (Lawn), the Back is South.
        # If it faces South, the Back is North.
        # If it faces East, the Back is West.
        # If it faces West, the Back is East.
        
        # Heuristic: The switch is usually placed "in the wall".
        # The "Back" face is the one shared with the "Outside" room (or just the one that is NOT the opening).
        # If we have room/room2, we can check which one is the "target" room (Lawn/Corridor) and which is the "backing" room (Outside/Wall).
        # But simpler: The switch texture should only be on 1-sided lines OR lines shared with a "solid" sector?
        # Actually, if it's a niche, the opening line (shared with Lawn) should have NO mid texture.
        # The other lines (sides and back) should have textures.
        
        # Let's assume the switch is always accessed from the "North" (Lawn) or "South" (Corridor).
        # In our case:
        # Gate Switches: Accessed from North (Lawn). Back is South (y = self.y).
        # Mess Hall Switch: Accessed from South (Corridor). Back is North (y = self.y + height).
        
        # We can try to detect which line is the "opening".
        # The opening is the line shared with the "main" room (Lawn or Corridor).
        # If we passed `room2=lawn`, then the line shared with `lawn` is the opening.
        
        opening_room = self.room2 if self.room2 else self.room
        
        for ld in builder.editor.linedefs:
            if builder.editor.sidedefs[ld.front].sector == sector_index:
                ld.action = self.action
                ld.tag = self.tag
                
                # Check if this line connects to the opening room
                is_opening = False
                if opening_room:
                    # Check if line vertices match opening room edge
                    # This is hard to check directly without geometric math.
                    # Instead, check the back sector.
                    if ld.back != 0xFFFF:
                        back_sector_idx = builder.editor.sidedefs[ld.back].sector
                        # We don't easily know the sector index of opening_room here because it might have been created earlier.
                        # But we can check if the line is 2-sided.
                        
                        # If it is 2-sided, it's likely the opening OR the backing (if backing is also a sector like Outside).
                        # If it's the opening to the Lawn (Ceil 256), we definitely don't want a Mid Texture blocking it.
                        # If it's the backing to Outside (Ceil 256), we DO want a Mid Texture (to make it look like a wall).
                        
                        # How to distinguish?
                        # The Opening is usually "open" (passable).
                        # The Backing is usually "closed" (blocking).
                        # But here both are just sectors.
                        
                        # Let's use the geometric position.
                        # Gate Switches: y=-16. Opening is Top (North, y=0). Back is Bottom (South, y=-16).
                        # Mess Hall Switch: y=... Opening is Bottom (South). Back is Top (North).
                        
                        # We can infer orientation from the "room" argument?
                        # If room is "Outside", that's the backing.
                        # If room2 is "Lawn", that's the opening.
                        
                        pass
                
                # Apply texture logic:
                # If it's a 2-sided line, we generally DON'T want a mid texture unless it's a solid wall.
                # But for the Switch Back, we DO want it.
                # For the Switch Opening, we DON'T.
                
                # Hack: For now, let's just clear the mid texture on the North face for Gate Switches?
                # Gate Switches are at y=-16. North face is at y=0.
                # Mess Hall Switch is at y=... North of corridor.
                
                # Better: Check if the line is on the boundary of the "opening room".
                # If the line is shared with `self.room2` (Lawn), clear texture.
                # If the line is shared with `self.room` (Outside), keep texture.
                
                # We need to know which sector index corresponds to which room.
                # We can't easily know that.
                
                # Alternative: Use the coordinates.
                # Gate Switches: Opening is at y = self.y + self.height.
                # Mess Hall Switch: Opening is at y = self.y.
                
                # Let's assume the "Opening" is the side that touches the room with the higher ceiling?
                # Or just clear Mid Texture if the back sector has a high ceiling?
                # No, Outside also has high ceiling.
                
                # Let's use the `room2` argument as the "Opening Room".
                # If `room2` is provided, any line touching `room2` is an opening.
                
                is_opening_face = False
                if self.room2:
                    # Check if this line is shared with room2
                    # We can check if the line segment is on the edge of room2
                    v1 = builder.editor.vertexes[ld.vx_a]
                    v2 = builder.editor.vertexes[ld.vx_b]
                    
                    # Check if v1 and v2 are on the boundary of room2
                    # (Simple AABB check or exact edge check)
                    # room2.x, room2.y, room2.width, room2.height
                    
                    # Check if both vertices are on the same edge of room2
                    on_left = (v1.x == self.room2.x and v2.x == self.room2.x)
                    on_right = (v1.x == self.room2.x + self.room2.width and v2.x == self.room2.x + self.room2.width)
                    on_top = (v1.y == self.room2.y + self.room2.height and v2.y == self.room2.y + self.room2.height)
                    on_bottom = (v1.y == self.room2.y and v2.y == self.room2.y)
                    
                    if on_left or on_right or on_top or on_bottom:
                        is_opening_face = True
                
                if is_opening_face:
                    builder.editor.sidedefs[ld.front].tx_mid = "-"
                    if ld.back != 0xFFFF:
                        builder.editor.sidedefs[ld.back].tx_mid = "-"
                else:
                    # It's a wall or the back of the switch.
                    builder.editor.sidedefs[ld.front].tx_mid = "SW1STRTN"
                    # If it's 2-sided (backing to Outside), we need to ensure it blocks?
                    # Or just has the texture.
                    # If it has the texture, it will look like a wall.
                    pass

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


