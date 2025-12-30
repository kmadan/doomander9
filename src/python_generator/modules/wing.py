from typing import Optional, List, Tuple
from .level import Level
from .geometry import Room, Corridor, Lawn
from .connectors import Door, Window
from .prefabs import Bedroom, Bathroom

class Wing:
    def __init__(self, x: int, y: int, side: str = 'left', num_rooms_per_side: int = 7, corridor_on_lawn_side: bool = True) -> None:
        self.x = x
        self.y = y
        self.side = side # 'left' means rooms are to the left of the corridor
        self.num_rooms_per_side = num_rooms_per_side
        # If False, corridor is placed on the outside edge and rooms are between corridor and lawn.
        self.corridor_on_lawn_side = corridor_on_lawn_side
        self.room_width = 256
        self.room_height = 256
        self.corridor_width = 128
        self.wall_thickness = 16
        self.bathroom_width = 256 # Same as room for alignment, but maybe wider?
        self.bathroom_height = 512 # Double height? Or just a big room in the sequence?
        # "7 rooms on either side of the central large shared bathroom"
        # Sequence: 7 Rooms, Bathroom, 7 Rooms.
        
    def generate(
        self,
        level: Level,
        lawn: Room,
        floor_height: int = 0,
        ceil_height: int = 128,
        story_tag: int = 0,
        exterior_area: Optional[Room] = None,
        add_corridor_windows: bool = True,
        corridor_window_skip_ranges: Optional[List[Tuple[int, int]]] = None,
        corridor_window_targets: Optional[List[Tuple[int, int, Room]]] = None,
        door_state: str = 'closed',
    ) -> Corridor:
        # If we are creating a 3D-floor second story inside these sectors, the
        # ceiling must be higher than the 2nd-floor height.
        if story_tag:
            # 3 floors: base 0..128, floor2 ~140..268, floor3 ~280..408
            # Keep extra headroom so exterior openings don't get clipped.
            ceil_height = max(int(ceil_height), 384)
        # Calculate dimensions
        # We build vertically (North-South)
        
        # 1. Create Corridor
        # Total height = (RoomHeight + Wall) * (7 + 1 + 7) + Walls?
        # Actually, let's build rooms and calculate corridor height dynamically or just sum it up.
        # Bathroom height? Let's make it equal to 2 rooms? Or just 1 large room?
        # "Large shared bathroom". Let's make it 512 height (2 rooms worth).
        
        total_units = self.num_rooms_per_side * 2 + 2 # 7 rooms + 7 rooms + 2 slots for bathroom
        total_height = (self.room_height + self.wall_thickness) * total_units + self.wall_thickness
        
        # Corridor/room placement.
        # side == 'left'  => lawn is East of the wing
        # side == 'right' => lawn is West of the wing
        if self.side == 'left':
            if self.corridor_on_lawn_side:
                corridor_x = self.x
                rooms_x = corridor_x - self.room_width - self.wall_thickness
                door_side = 'right'
                lawn_interface_x = corridor_x + self.corridor_width
            else:
                rooms_x = self.x
                corridor_x = rooms_x - self.corridor_width - self.wall_thickness
                door_side = 'left'
                lawn_interface_x = corridor_x
        else:
            if self.corridor_on_lawn_side:
                corridor_x = self.x
                rooms_x = corridor_x + self.corridor_width + self.wall_thickness
                door_side = 'left'
                lawn_interface_x = corridor_x
            else:
                # Flipped: rooms adjacent to lawn, corridor on outside (East)
                rooms_x = self.x
                corridor_x = rooms_x + self.room_width + self.wall_thickness
                door_side = 'right'
                lawn_interface_x = corridor_x + self.corridor_width
            
        corridor = level.add_room(Corridor(corridor_x, self.y, self.corridor_width, total_height))
        corridor.floor_height = floor_height
        corridor.ceil_height = ceil_height
        if story_tag:
            corridor.tag = int(story_tag)
        
        # 2. Generate Rooms & Bathroom
        current_y = self.y + self.wall_thickness
        
        # First block of rooms (south half): windows bias away from the shared bathroom.
        # Bathroom is in the middle; for the south half, "away" means toward the south.
        for _i in range(self.num_rooms_per_side):
            self._create_room(
                level,
                rooms_x,
                current_y,
                corridor,
                door_side,
                lawn=lawn,
                exterior_area=exterior_area,
                floor_height=floor_height,
                ceil_height=ceil_height,
                story_tag=story_tag,
                door_state=door_state,
                window_bias=-1,
            )
            current_y += self.room_height + self.wall_thickness
            
        # Bathroom (Central)
        # Let's make it double height
        bath_height = self.room_height * 2 + self.wall_thickness
        bathroom = level.add_room(Bathroom(rooms_x, current_y, self.room_width, bath_height))
        bathroom.floor_height = floor_height
        bathroom.ceil_height = ceil_height
        if story_tag:
            bathroom.tag = int(story_tag)
        
        # Door to Bathroom
        door_y = current_y + (bath_height // 2) - 32
        if door_side == 'right':
            door_x = rooms_x + self.room_width
            level.add_connector(Door(door_x, door_y, self.wall_thickness, 64, bathroom, corridor, state=door_state))
        else:
            door_x = rooms_x - self.wall_thickness
            level.add_connector(Door(door_x, door_y, self.wall_thickness, 64, bathroom, corridor, state=door_state))
            
        current_y += bath_height + self.wall_thickness
        
        # Second block of rooms (north half): windows bias away from the shared bathroom.
        # For the north half, "away" means toward the north.
        for _i in range(self.num_rooms_per_side):
            self._create_room(
                level,
                rooms_x,
                current_y,
                corridor,
                door_side,
                lawn=lawn,
                exterior_area=exterior_area,
                floor_height=floor_height,
                ceil_height=ceil_height,
                story_tag=story_tag,
                door_state=door_state,
                window_bias=+1,
            )
            current_y += self.room_height + self.wall_thickness
            
        # 3. Corridor Windows to Lawn
        # Place windows along the lawn-facing side of the corridor.
        # Optionally disabled by the caller (e.g., when that outside space is used by a stairwell bump-out).
        
        win_y = self.y + self.wall_thickness
        segment_height = self.room_height + self.wall_thickness
        
        skip_ranges = corridor_window_skip_ranges or []
        targets = corridor_window_targets or []

        def _overlaps_skip(y0: int, y1: int) -> bool:
            for a, b in skip_ranges:
                ay0 = int(a)
                ay1 = int(b)
                if y0 < ay1 and y1 > ay0:
                    return True
            return False

        def _resolve_target_room(y0: int, y1: int):
            # If provided, targets are (y0, y1, room) tuples in world coordinates.
            # Prefer the target that overlaps this window span the most.
            # (Strict containment is brittle and can cause windows to fall back
            # to a non-adjacent lawn sector, producing blocked/boxed windows.)
            best_room = None
            best_overlap = 0
            for ty0, ty1, room in targets:
                ay0 = int(ty0)
                ay1 = int(ty1)
                overlap = min(int(y1), ay1) - max(int(y0), ay0)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_room = room

            if best_room is not None and best_overlap > 0:
                return best_room

            # If the caller provided explicit targets (e.g., buffer-strip segments),
            # falling back to `lawn` can create a non-adjacent window target and
            # the window will appear fully blocked. Prefer *some* provided target
            # over the default lawn in this case.
            if targets:
                return targets[0][2]

            return lawn

        if add_corridor_windows and self.corridor_on_lawn_side:
            for i in range(total_units):
                # Half-size window span along wall, and offset away from the
                # shared bathroom for each wing half.
                # Segment height is (room_height + wall_thickness) = 272.
                span = 96
                base_off = (segment_height - span) // 2
                # Windows MUST always be offset opposite direction from the
                # shared bathroom for that wing section.
                # - south half (first rooms): bias toward south  => -1
                # - bathroom span: no bias
                # - north half (second rooms): bias toward north => +1
                if i < self.num_rooms_per_side:
                    bias = -1
                elif i >= self.num_rooms_per_side + 2:
                    bias = +1
                else:
                    bias = 0
                bias_amt = 32
                wy0 = int(win_y + base_off + bias * bias_amt)
                wy0 = int(max(win_y, min(wy0, win_y + segment_height - span)))
                wy1 = int(wy0 + span)
                if _overlaps_skip(wy0, wy1):
                    win_y += segment_height
                    continue

                target_room = _resolve_target_room(wy0, wy1)
                if target_room is None:
                    win_y += segment_height
                    continue

                wx = lawn_interface_x
                if self.side == 'right':
                    wx -= self.wall_thickness

                # Vertical opening (Z): keep consistent per-floor.
                # IMPORTANT: stretching facade windows to span multiple stories
                # reads as one continuous slit (your screenshot). Keep it to a
                # normal window height and rely on real per-floor windows in the
                # actual floor copies if needed.
                sill_h = 48
                win_h = 48
                level.add_connector(Window(
                    wx,
                    wy0,
                    self.wall_thickness,
                    span,
                    corridor,
                    target_room,
                    sill_height=sill_h,
                    window_height=win_h,
                    floor_tex=corridor.floor_tex,
                    ceil_tex=corridor.ceil_tex,
                ))
                win_y += segment_height
            
        return corridor

    def _create_room(self, level: Level, x: int, y: int, corridor: Room, door_side: str, lawn: Optional[Room] = None, exterior_area: Optional[Room] = None, floor_height: int = 0, ceil_height: int = 128, story_tag: int = 0, door_state: str = 'closed', window_bias: int = 0) -> None:
        room = level.add_room(Bedroom(x, y, self.room_width, self.room_height))
        room.floor_height = floor_height
        room.ceil_height = ceil_height
        if story_tag:
            room.tag = int(story_tag)
        
        # Door to Corridor
        # Centered vertically relative to room
        door_y = y + (self.room_height // 2) - 32
        
        if door_side == 'right':
            door_x = x + self.room_width
            level.add_connector(Door(door_x, door_y, self.wall_thickness, 64, room, corridor, state=door_state))
        else:
            door_x = x - self.wall_thickness
            level.add_connector(Door(door_x, door_y, self.wall_thickness, 64, room, corridor, state=door_state))
            
        # Create Exterior Window
        # We need a sector to connect to.
        # Let's create a local "Exterior" sector for this room.
        # It's a bit expensive to have 1 lawn per room.
        # Maybe the Wing should generate a "Backyard" lawn strip.
        
        # For flipped wings (rooms adjacent to lawn), connect window directly to lawn through the wall gap.
        # Bedroom window sizing.
        # NOTE: The connector's *thickness* (its `width` on left/right walls)
        # must remain equal to `wall_thickness` so cuts register on both rooms.
        # The visible window "size" we tune here is:
        # - the opening span along the wall (connector `height` on left/right walls)
        # - the vertical opening height (Window.window_height)
        #
        # Make windows half-size vs the previous defaults, and shift slightly
        # off-center (not perfectly centered on the wall).
        window_segment = 48  # was 96
        center_off = (self.room_height - window_segment) // 2
        bias_amt = 32
        window_offset_y = int(center_off + int(max(-1, min(1, int(window_bias)))) * bias_amt)
        window_offset_y = int(max(0, min(window_offset_y, self.room_height - window_segment)))
        # Vertical opening height (Z). Keep consistent across actual floors.
        window_height = 48

        # Facade pass: on the ground-floor footprint, keep the *same 2D window span*
        # (so cuts register cleanly), and make the opening tall enough to reveal
        # the 3D-floor stories from outside, but keep a sill + lintel so the wall
        # doesn't look completely missing/transparent.
        window_sill = 48

        if (not self.corridor_on_lawn_side) and (lawn is not None):
            if door_side == 'right':
                # Window on Left (toward lawn)
                win_x = x - self.wall_thickness
                level.add_connector(Window(
                    win_x,
                    y + window_offset_y,
                    self.wall_thickness,
                    window_segment,
                    lawn,
                    room,
                    sill_height=window_sill,
                    window_height=window_height,
                    floor_tex=room.floor_tex,
                    ceil_tex=room.ceil_tex,
                ))
            else:
                # Window on Right (toward lawn)
                win_x = x + self.room_width
                level.add_connector(Window(
                    win_x,
                    y + window_offset_y,
                    self.wall_thickness,
                    window_segment,
                    room,
                    lawn,
                    sill_height=window_sill,
                    window_height=window_height,
                    floor_tex=room.floor_tex,
                    ceil_tex=room.ceil_tex,
                ))
            return

        # If this wing's rooms face an exterior strip/yard, connect windows directly to it.
        # This avoids the "tiny window box" look and makes the view feel continuous.
        if (self.corridor_on_lawn_side) and (exterior_area is not None):
            if door_side == 'right':
                # Window on Left (outside)
                win_x = x - self.wall_thickness
                level.add_connector(Window(
                    win_x,
                    y + window_offset_y,
                    self.wall_thickness,
                    window_segment,
                    exterior_area,
                    room,
                    sill_height=window_sill,
                    window_height=window_height,
                    floor_tex=room.floor_tex,
                    ceil_tex=room.ceil_tex,
                ))
            else:
                # Window on Right (outside)
                win_x = x + self.room_width
                level.add_connector(Window(
                    win_x,
                    y + window_offset_y,
                    self.wall_thickness,
                    window_segment,
                    room,
                    exterior_area,
                    sill_height=window_sill,
                    window_height=window_height,
                    floor_tex=room.floor_tex,
                    ceil_tex=room.ceil_tex,
                ))
            return

        # Default: create a small "Window Box" sector (Lawn type) attached to the window.
        window_box_depth = 64
        if door_side == 'right':
            # Window on Left
            wb_x = x - window_box_depth
            wb = level.add_room(Lawn(wb_x, y, window_box_depth, self.room_height))
            level.add_connector(Window(wb_x + window_box_depth, y + window_offset_y, self.wall_thickness, window_segment, wb, room, sill_height=48, window_height=window_height))
        else:
            # Window on Right
            wb_x = x + self.room_width + self.wall_thickness
            wb = level.add_room(Lawn(wb_x, y, window_box_depth, self.room_height))
            level.add_connector(Window(wb_x - self.wall_thickness, y + window_offset_y, self.wall_thickness, window_segment, wb, room, sill_height=48, window_height=window_height))
