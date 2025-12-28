from modules.level import Level
from modules.geometry import Corridor, Lawn, Room
from modules.connectors import Door, Switch, Window, Portal
from modules.prefabs import Bedroom, CommonRoom, Bathroom
from modules.wing import Wing
 

class HostelGenerator:
    def __init__(self, start_x=0, start_y=0):
        self.start_x = start_x
        self.start_y = start_y
        self.level = Level()
        
    def generate(self):
        # Configuration
        wall_thickness = 16
        # Calculate Wing Height to match Lawn Height
        # Wing: 7 rooms + Bathroom (2 rooms) + 7 rooms = 16 units
        # Unit = 256 + 16 = 272
        # Total = 16 * 272 + 16 = 4368
        wing_height = 4368
        lawn_width = 512
        lawn_height = wing_height 
        
        # 1. Create Central Lawn
        lawn = self.level.add_room(Lawn(self.start_x, self.start_y, lawn_width, lawn_height, floor_tex="PYGRASS"))

        # Stairs configuration (used both for geometry and for reserving corridor window spans).
        stair_w = 64
        step_depth = 64
        steps = 7
        rise = 20
        stairs_h = steps * step_depth
        hall_h = stairs_h

        # 2. Generate Middle Wing (West of the lawn)
        # Naming convention used across this project:
        # - West Wing   : far-left wing
        # - Middle Wing : wing directly west of the central lawn
        # - East Wing   : wing east of the central lawn
        #
        # Middle Wing corridor faces the lawn; rooms are on the outside.
        # We intentionally leave a wider outdoor gap on the lawn-facing side so the Middle Wing stairwell
        # can "bump out" outside the building without overlapping the lawn sector.
        # (Wing corridor width is 128.)
        stair_bumpout_clearance = wall_thickness + 64 + wall_thickness + 64 + wall_thickness
        middle_wing_x = self.start_x - 128 - stair_bumpout_clearance
        middle_wing = Wing(middle_wing_x, self.start_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)

        # 2b. Add the West Wing, with a brown outdoor ground strip between it and the Middle Wing.
        # The strip is just an outdoor sector (sky ceiling) with a brown ground flat.
        # Leave a wall-thickness gap so Middle Wing room windows can open onto it.
        #
        # We split the strip into two halves (west/east):
        # - East half: continuous full-height strip used by Middle Wing bedroom windows.
        # - West half: used by West Wing corridor lookouts, with a vertical cut-out where West Wing stairs bump out.
        brown_width = 512
        # Keep the total strip width constant, but leave a wall-thickness gap between halves so the
        # east<->west connection can be a real opening (a connector sector) that touches BOTH sides.
        # (If there is no gap, the connector overlaps one side and doesn't register a cut there.)
        brown_half_w = (brown_width - wall_thickness) // 2  # 248
        brown_gap_w = wall_thickness
        brown_ground_x = middle_wing_x - middle_wing.room_width - wall_thickness - brown_width - wall_thickness
        brown_ground_west_x = brown_ground_x
        brown_ground_east_x = brown_ground_x + brown_half_w + brown_gap_w
        brown_halves_gap_x = brown_ground_west_x + brown_half_w

        # West Wing stairs attach point (used to carve out the brown strip so the stair bump-out doesn't overlap it).
        west_north_attach_pad = 224
        west_attach_y = int(self.start_y + wing_height - wall_thickness - stairs_h - west_north_attach_pad)
        west_stair_reserved_y0 = int(west_attach_y)
        west_stair_reserved_y1 = int(west_attach_y + hall_h + wall_thickness + step_depth + wall_thickness + step_depth)

        # East half: continuous, full height (for Middle Wing room windows).
        brown_ground_east = self.level.add_room(Lawn(brown_ground_east_x, self.start_y, brown_half_w, lawn_height, floor_tex="RROCK19"))

        # West half: split into south/north segments around the stairwell cut-out.
        brown_west_south_h = int(west_stair_reserved_y0 - self.start_y)
        brown_west_south = None
        if brown_west_south_h > 0:
            brown_west_south = self.level.add_room(Lawn(brown_ground_west_x, self.start_y, brown_half_w, brown_west_south_h, floor_tex="RROCK19"))

        brown_west_north_y = int(west_stair_reserved_y1)
        brown_west_north_h = int((self.start_y + lawn_height) - brown_west_north_y)
        brown_west_north = None
        if brown_west_north_h > 0:
            brown_west_north = self.level.add_room(Lawn(brown_ground_west_x, brown_west_north_y, brown_half_w, brown_west_north_h, floor_tex="RROCK19"))

        brown_ground_west_default = brown_west_south or brown_west_north
        if brown_ground_west_default is None:
            raise RuntimeError("West half of brown strip is empty")

        # Connect the brown strip east<->west halves so the strip is traversable.
        # (We split the west half for the stair cut-out; without these openings, the halves are separated by a wall.)
        if brown_west_south is not None:
            self.level.add_connector(Window(
                brown_halves_gap_x,
                brown_west_south.y,
                wall_thickness,
                brown_west_south.height,
                brown_west_south,
                brown_ground_east,
                sill_height=0,
                window_height=256,
                floor_tex="RROCK19",
                ceil_tex="F_SKY1",
            ))
        if brown_west_north is not None:
            self.level.add_connector(Window(
                brown_halves_gap_x,
                brown_west_north.y,
                wall_thickness,
                brown_west_north.height,
                brown_west_north,
                brown_ground_east,
                sill_height=0,
                window_height=256,
                floor_tex="RROCK19",
                ceil_tex="F_SKY1",
            ))

        corridor_window_targets_west = []
        if brown_west_south is not None:
            corridor_window_targets_west.append((brown_west_south.y, brown_west_south.y + brown_west_south.height, brown_west_south))
        if brown_west_north is not None:
            corridor_window_targets_west.append((brown_west_north.y, brown_west_north.y + brown_west_north.height, brown_west_north))

        # Generate the Middle Wing now that the brown strip exists, so room windows can look onto it.
        # Re-enable corridor lookouts toward the lawn, but skip the vertical span where the stairwell bump-out attaches.
        middle_north_attach_pad = 224
        middle_attach_y = int(self.start_y + wing_height - wall_thickness - stairs_h - middle_north_attach_pad)
        # The stairwell occupies more than just the hall span: it includes a landing + portal threshold above.
        # Reserve that full vertical span so outdoor buffer sectors never overlap it.
        middle_stair_reserved_y0 = int(middle_attach_y)
        middle_stair_reserved_y1 = int(middle_attach_y + hall_h + wall_thickness + step_depth + wall_thickness + step_depth)
        # Build a "buffer" outdoor strip between the Middle Wing corridor and the main lawn so:
        # - corridor lookouts actually open to outdoor space (instead of a solid lawn boundary wall)
        # - the stairwell bump-out occupies the gap without overlapping any outdoor sector
        buffer_x = middle_wing_x + 128 + wall_thickness  # corridor right + wall
        buffer_right = -wall_thickness
        buffer_w = int(buffer_right - buffer_x)
        if buffer_w <= 0:
            raise RuntimeError("Middle Wing lawn buffer has non-positive width")

        # South buffer segment
        buffer_south_h = int(middle_stair_reserved_y0 - self.start_y)
        buffer_south = None
        if buffer_south_h > 0:
            buffer_south = self.level.add_room(Lawn(buffer_x, self.start_y, buffer_w, buffer_south_h, floor_tex="PYGRASS"))
            # Open connection to the main lawn through the wall-thickness gap.
            self.level.add_connector(Window(
                buffer_right,
                self.start_y,
                wall_thickness,
                buffer_south_h,
                buffer_south,
                lawn,
                sill_height=0,
                window_height=256,
                floor_tex="PYGRASS",
                ceil_tex="F_SKY1",
            ))

        # North buffer segment
        buffer_north_y = int(middle_stair_reserved_y1)
        buffer_north_h = int((self.start_y + lawn_height) - buffer_north_y)
        buffer_north = None
        if buffer_north_h > 0:
            buffer_north = self.level.add_room(Lawn(buffer_x, buffer_north_y, buffer_w, buffer_north_h, floor_tex="PYGRASS"))
            self.level.add_connector(Window(
                buffer_right,
                buffer_north_y,
                wall_thickness,
                buffer_north_h,
                buffer_north,
                lawn,
                sill_height=0,
                window_height=256,
                floor_tex="PYGRASS",
                ceil_tex="F_SKY1",
            ))

        corridor_window_targets = []
        if buffer_south is not None:
            corridor_window_targets.append((buffer_south.y, buffer_south.y + buffer_south.height, buffer_south))
        if buffer_north is not None:
            corridor_window_targets.append((buffer_north.y, buffer_north.y + buffer_north.height, buffer_north))

        middle_corridor = middle_wing.generate(
            self.level,
            lawn,
            floor_height=0,
            ceil_height=128,
            story_tag=0,
            exterior_area=brown_ground_east,
            add_corridor_windows=True,
            corridor_window_skip_ranges=[(middle_stair_reserved_y0, middle_stair_reserved_y1)],
            corridor_window_targets=corridor_window_targets,
        )

        # Place the West Wing corridor facing the brown strip.
        # For a left-side wing with corridor_on_lawn_side=True, windows use x = corridor_x + 128
        # with width=wall_thickness, so brown_ground_x must equal corridor_x + 128 + wall_thickness.
        west_wing_x = brown_ground_x - (128 + wall_thickness)
        west_wing = Wing(west_wing_x, self.start_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)

        # Vacant, inaccessible outdoor area west of the West Wing.
        # This gives the West Wing room windows something to look out onto.
        west_outside_width = 768
        west_outside_x = west_wing_x - west_wing.room_width - wall_thickness - west_outside_width - wall_thickness
        west_outside = self.level.add_room(Lawn(west_outside_x, self.start_y, west_outside_width, lawn_height, floor_tex="PYGRASS"))

        west_corridor = west_wing.generate(
            self.level,
            brown_ground_west_default,
            floor_height=0,
            ceil_height=128,
            story_tag=0,
            exterior_area=west_outside,
            add_corridor_windows=True,
            corridor_window_skip_ranges=[(west_stair_reserved_y0, west_stair_reserved_y1)],
            corridor_window_targets=corridor_window_targets_west,
        )
        
        # 3. Generate East Wing (East of the lawn)
        # Flipped: rooms adjacent to lawn, corridor on the outside (East)
        east_rooms_x = self.start_x + lawn_width + wall_thickness
        east_wing = Wing(east_rooms_x, self.start_y, side='right', num_rooms_per_side=7, corridor_on_lawn_side=False)
        east_corridor = east_wing.generate(self.level, lawn, floor_height=0, ceil_height=128, story_tag=0)
        
        # 4. Cross Corridor (North)
        # Connects West Wing, Middle Wing, East Wing, Lawn, and Mess Hall
        lawn_top_y = self.start_y + lawn_height
        cross_y = lawn_top_y + wall_thickness
        cross_height = 128
        # Width spans from West Wing Corridor Left Edge to East Wing Corridor Right Edge
        # (Wing corridor width is 128.)
        cross_x = west_corridor.x
        cross_width = (east_corridor.x + 128) - west_corridor.x
        
        cross_corridor = self.level.add_room(Corridor(cross_x, cross_y, cross_width, cross_height))

        # Connect West Wing to Cross Corridor (Opening in the gap)
        self.level.add_connector(Window(west_corridor.x, lawn_top_y, 128, wall_thickness, west_corridor, cross_corridor, sill_height=0, window_height=128))
        
        # Connect Middle Wing to Cross Corridor (Opening in the gap)
        self.level.add_connector(Window(middle_corridor.x, lawn_top_y, 128, wall_thickness, middle_corridor, cross_corridor, sill_height=0, window_height=128))
        
        # Connect East Wing to Cross Corridor (Opening in the gap)
        self.level.add_connector(Window(east_corridor.x, lawn_top_y, 128, wall_thickness, east_corridor, cross_corridor, sill_height=0, window_height=128))
        
        # Connect Lawn to Cross Corridor (Wide opening in the gap)
        lawn_conn_width = 256
        lawn_conn_x = self.start_x + (lawn_width // 2) - (lawn_conn_width // 2)
        self.level.add_connector(Window(lawn_conn_x, lawn_top_y, lawn_conn_width, wall_thickness, lawn, cross_corridor, sill_height=0, window_height=128))

        # Connect Brown Ground Strip to Cross Corridor (so it is accessible like the lawn is).
        self.level.add_connector(Window(
            brown_ground_east_x,
            lawn_top_y,
            brown_half_w,
            wall_thickness,
            brown_ground_east,
            cross_corridor,
            sill_height=0,
            window_height=128,
        ))
        
        # 5. Mess Hall (North of Cross Corridor)
        mess_hall_height = 512
        cross_top_y = cross_y + cross_height
        mess_hall_y = cross_top_y + wall_thickness
        mess_hall = self.level.add_room(Room(self.start_x, mess_hall_y, lawn_width, mess_hall_height, floor_tex="FLOOR0_1", wall_tex="STONE2"))
        
        # Door to Mess Hall (Open, Tagged)
        mh_tag = self.level.get_new_tag()
        door_width = 128
        door_x = self.start_x + (lawn_width // 2) - (door_width // 2)
        # Door sector sits in the wall gap between cross corridor and mess hall.
        # It starts open, and the switch closes it (so we don't want a use-activated door action).
        self.level.add_connector(Door(door_x, cross_top_y, door_width, wall_thickness, cross_corridor, mess_hall, state='open', tag=mh_tag, linedef_action=0))
        
        # Switch for Mess Hall
        # Place inside Cross Corridor near the door -> Move to wall to avoid overlap
        switch_x = door_x - 64
        switch_y = cross_top_y
        self.level.add_connector(Switch(switch_x, switch_y, action=42, tag=mh_tag, room=cross_corridor)) # 42 = SR Door Close
        
        # 6. Gates (South)
        # "Gates on one side of the lawn from the outside campus"
        # "The two gates... need to be on the lawn ground on left and right"
        # Create "Outside Campus" sector
        outside_height = 256
        outside_y = self.start_y - outside_height - wall_thickness
        outside = self.level.add_room(Lawn(self.start_x, outside_y, lawn_width, outside_height, floor_tex="PYGRASS"))
        
        # Gate 1 (Left)
        gate1_tag = self.level.get_new_tag()
        gate_width = 128
        gate1_x = self.start_x + 64 # Near Middle Wing
        self.level.add_connector(Door(gate1_x, self.start_y - wall_thickness, gate_width, wall_thickness, outside, lawn, texture="BIGDOOR2", state='open', tag=gate1_tag, linedef_action=0))
        
        # Switch for Gate 1
        # Place switch in the wall gap, attached to the outside lawn AND the main lawn
        switch1_x = gate1_x - 32
        switch1_y = self.start_y - wall_thickness
        self.level.add_connector(Switch(switch1_x, switch1_y, action=42, tag=gate1_tag, room=outside, room2=lawn))
        
        # Gate 2 (Right)
        gate2_tag = self.level.get_new_tag()
        gate2_x = self.start_x + lawn_width - 64 - gate_width # Near East Wing
        self.level.add_connector(Door(gate2_x, self.start_y - wall_thickness, gate_width, wall_thickness, outside, lawn, texture="BIGDOOR2", state='open', tag=gate2_tag, linedef_action=0))
        
        # Switch for Gate 2
        # Place switch in the wall gap, attached to the outside lawn AND the main lawn
        switch2_x = gate2_x + gate_width + 16
        switch2_y = self.start_y - wall_thickness
        self.level.add_connector(Switch(switch2_x, switch2_y, action=42, tag=gate2_tag, room=outside, room2=lawn))

        # 7. Stairs + off-map 2nd floor connected via line portals
        # The 2nd floor is a separate copy of the building placed off-map, so doors
        # are fully independent per floor. We connect at the top of the stairs using
        # Line_SetPortal so it feels seamless.
        # Off-map placement for the 2nd floor so it is visible in automap.
        # Place it north of the main area (same X footprint).
        second_floor_offset_y = -6000
        second_floor_floor = steps * rise  # 140
        second_floor_ceil = second_floor_floor + 128

        # Generate a disconnected 2nd-floor copy of the wings.
        lawn2 = self.level.add_room(Lawn(self.start_x, self.start_y + second_floor_offset_y, lawn_width, lawn_height, floor_tex="PYGRASS"))

        # West Wing off-map copy + its outdoor areas.
        west_wing_2 = Wing(west_wing_x, self.start_y + second_floor_offset_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)
        west_attach_y_2 = int((self.start_y + second_floor_offset_y) + wing_height - wall_thickness - stairs_h - west_north_attach_pad)
        west_stair_reserved_y0_2 = int(west_attach_y_2)
        west_stair_reserved_y1_2 = int(west_attach_y_2 + hall_h + wall_thickness + step_depth + wall_thickness + step_depth)

        # Off-map brown strip west-half segments for West Wing corridor lookouts.
        brown_west_south_h_2 = int(west_stair_reserved_y0_2 - (self.start_y + second_floor_offset_y))
        brown_west_south_2 = None
        if brown_west_south_h_2 > 0:
            brown_west_south_2 = self.level.add_room(Lawn(brown_ground_west_x, self.start_y + second_floor_offset_y, brown_half_w, brown_west_south_h_2, floor_tex="RROCK19"))

        brown_west_north_y_2 = int(west_stair_reserved_y1_2)
        brown_west_north_h_2 = int(((self.start_y + second_floor_offset_y) + lawn_height) - brown_west_north_y_2)
        brown_west_north_2 = None
        if brown_west_north_h_2 > 0:
            brown_west_north_2 = self.level.add_room(Lawn(brown_ground_west_x, brown_west_north_y_2, brown_half_w, brown_west_north_h_2, floor_tex="RROCK19"))

        brown_ground_west_default_2 = brown_west_south_2 or brown_west_north_2
        if brown_ground_west_default_2 is None:
            raise RuntimeError("West half of off-map brown strip is empty")

        corridor_window_targets_west_2 = []
        if brown_west_south_2 is not None:
            corridor_window_targets_west_2.append((brown_west_south_2.y, brown_west_south_2.y + brown_west_south_2.height, brown_west_south_2))
        if brown_west_north_2 is not None:
            corridor_window_targets_west_2.append((brown_west_north_2.y, brown_west_north_2.y + brown_west_north_2.height, brown_west_north_2))

        west_outside_2 = self.level.add_room(Lawn(west_outside_x, self.start_y + second_floor_offset_y, west_outside_width, lawn_height, floor_tex="PYGRASS"))
        west_corridor_2 = west_wing_2.generate(
            self.level,
            brown_ground_west_default_2,
            floor_height=second_floor_floor,
            ceil_height=second_floor_ceil,
            story_tag=0,
            exterior_area=west_outside_2,
            add_corridor_windows=True,
            corridor_window_skip_ranges=[(west_stair_reserved_y0_2, west_stair_reserved_y1_2)],
            corridor_window_targets=corridor_window_targets_west_2,
            door_state='open',
        )

        middle_wing_2 = Wing(middle_wing_x, self.start_y + second_floor_offset_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)
        middle_attach_y_2 = int((self.start_y + second_floor_offset_y) + wing_height - wall_thickness - stairs_h - middle_north_attach_pad)
        middle_stair_reserved_y0_2 = int(middle_attach_y_2)
        middle_stair_reserved_y1_2 = int(middle_attach_y_2 + hall_h + wall_thickness + step_depth + wall_thickness + step_depth)

        # Off-map buffer strip between Middle corridor and off-map lawn2 (same geometry as main floor, shifted by offset).
        buffer_x_2 = middle_wing_x + 128 + wall_thickness
        buffer_right_2 = -wall_thickness
        buffer_w_2 = int(buffer_right_2 - buffer_x_2)
        if buffer_w_2 <= 0:
            raise RuntimeError("Middle Wing off-map lawn buffer has non-positive width")

        buffer_south_h_2 = int(middle_stair_reserved_y0_2 - (self.start_y + second_floor_offset_y))
        buffer_south_2 = None
        if buffer_south_h_2 > 0:
            buffer_south_2 = self.level.add_room(Lawn(buffer_x_2, self.start_y + second_floor_offset_y, buffer_w_2, buffer_south_h_2, floor_tex="PYGRASS"))
            self.level.add_connector(Window(
                buffer_right_2,
                self.start_y + second_floor_offset_y,
                wall_thickness,
                buffer_south_h_2,
                buffer_south_2,
                lawn2,
                sill_height=0,
                window_height=second_floor_ceil - second_floor_floor,
            ))

        buffer_north_y_2 = int(middle_stair_reserved_y1_2)
        buffer_north_h_2 = int(((self.start_y + second_floor_offset_y) + lawn_height) - buffer_north_y_2)
        buffer_north_2 = None
        if buffer_north_h_2 > 0:
            buffer_north_2 = self.level.add_room(Lawn(buffer_x_2, buffer_north_y_2, buffer_w_2, buffer_north_h_2, floor_tex="PYGRASS"))
            self.level.add_connector(Window(
                buffer_right_2,
                buffer_north_y_2,
                wall_thickness,
                buffer_north_h_2,
                buffer_north_2,
                lawn2,
                sill_height=0,
                window_height=second_floor_ceil - second_floor_floor,
            ))

        corridor_window_targets_2 = []
        if buffer_south_2 is not None:
            corridor_window_targets_2.append((buffer_south_2.y, buffer_south_2.y + buffer_south_2.height, buffer_south_2))
        if buffer_north_2 is not None:
            corridor_window_targets_2.append((buffer_north_2.y, buffer_north_2.y + buffer_north_2.height, buffer_north_2))

        middle_corridor_2 = middle_wing_2.generate(
            self.level,
            lawn2,
            floor_height=second_floor_floor,
            ceil_height=second_floor_ceil,
            story_tag=0,
            add_corridor_windows=True,
            corridor_window_skip_ranges=[(middle_stair_reserved_y0_2, middle_stair_reserved_y1_2)],
            corridor_window_targets=corridor_window_targets_2,
            door_state='open',
        )
        east_wing_2 = Wing(east_rooms_x, self.start_y + second_floor_offset_y, side='right', num_rooms_per_side=7, corridor_on_lawn_side=False)
        east_corridor_2 = east_wing_2.generate(self.level, lawn2, floor_height=second_floor_floor, ceil_height=second_floor_ceil, story_tag=0, door_state='open')

        def add_stairwell_to_corridor(src_corridor, side_dir: int, *, attach_y: int, set_spawn: bool, portal_target_corridor=None, portal_pair_ids=None):
            hall_h = steps * step_depth

            # A thin "hall" right outside the corridor.
            if side_dir > 0:
                hall_x = src_corridor.x + src_corridor.width + wall_thickness
            else:
                hall_x = src_corridor.x - wall_thickness - 64
            hall_y = int(attach_y)
            hall_w = 64
            hall = self.level.add_room(Room(
                hall_x,
                hall_y,
                hall_w,
                hall_h,
                floor_tex=src_corridor.floor_tex,
                wall_tex=src_corridor.wall_tex,
                ceil_tex=src_corridor.ceil_tex,
                floor_height=0,
                ceil_height=320,
            ))

            # Steps adjacent to the hall, with an explicit gap + connector per step.
            last_step_room = None
            for i in range(steps):
                step_floor = (i + 1) * rise
                step_y = hall_y + i * step_depth
                if side_dir > 0:
                    step_x = hall_x + hall_w + wall_thickness
                    gap_x = hall_x + hall_w
                else:
                    step_x = hall_x - wall_thickness - stair_w
                    gap_x = hall_x - wall_thickness

                step_room = self.level.add_room(Room(
                    step_x,
                    step_y,
                    stair_w,
                    step_depth,
                    floor_tex=src_corridor.floor_tex,
                    wall_tex=src_corridor.wall_tex,
                    ceil_tex=src_corridor.ceil_tex,
                    floor_height=step_floor,
                    ceil_height=320,
                ))

                if i == steps - 1:
                    last_step_room = step_room

                # Opening between hall <-> this step slice.
                self.level.add_connector(Window(
                    gap_x,
                    step_y,
                    wall_thickness,
                    step_depth,
                    hall,
                    step_room,
                    sill_height=0,
                    window_height=320,
                    floor_tex=src_corridor.floor_tex,
                    ceil_tex=src_corridor.ceil_tex,
                    wall_tex=src_corridor.wall_tex,
                ))

            # Opening between corridor -> hall (through the wall thickness gap).
            # Use a single doorway-sized opening so we don't collide with room-door cuts.
            corridor_door_h = 96
            corridor_door_y = hall_y + 32
            self.level.add_connector(Window(
                (src_corridor.x + src_corridor.width) if side_dir > 0 else (src_corridor.x - wall_thickness),
                corridor_door_y,
                wall_thickness,
                corridor_door_h,
                src_corridor,
                hall,
                sill_height=0,
                window_height=320,
                floor_tex=src_corridor.floor_tex,
                ceil_tex=src_corridor.ceil_tex,
                wall_tex=src_corridor.wall_tex,
            ))

            # Landing at the top of the stairs (height 140), separated by a wall gap so it can be connected.
            landing_y = hall_y + hall_h + wall_thickness
            if side_dir > 0:
                landing_x = hall_x + hall_w + wall_thickness
            else:
                landing_x = hall_x - wall_thickness - stair_w
            landing_h = step_depth
            landing = self.level.add_room(Room(
                landing_x,
                landing_y,
                stair_w,
                landing_h,
                floor_tex=src_corridor.floor_tex,
                wall_tex=src_corridor.wall_tex,
                ceil_tex=src_corridor.ceil_tex,
                floor_height=steps * rise,
                ceil_height=320,
            ))

            # Connect the last step slice to the landing through a wall-thickness gap.
            if last_step_room is not None:
                self.level.add_connector(Window(
                    landing_x,
                    hall_y + hall_h,
                    stair_w,
                    wall_thickness,
                    last_step_room,
                    landing,
                    sill_height=0,
                    window_height=320,
                    floor_tex=src_corridor.floor_tex,
                    ceil_tex=src_corridor.ceil_tex,
                    wall_tex=src_corridor.wall_tex,
                ))

            # Portal threshold sector beyond the landing, separated by a wall gap.
            portal_y = landing_y + landing_h
            threshold_y = portal_y + wall_thickness
            threshold = self.level.add_room(Room(
                landing_x,
                threshold_y,
                stair_w,
                step_depth,
                floor_tex=src_corridor.floor_tex,
                wall_tex=src_corridor.wall_tex,
                ceil_tex=src_corridor.ceil_tex,
                floor_height=steps * rise,
                ceil_height=320,
            ))

            if portal_target_corridor is not None and portal_pair_ids is not None:
                src_line_id, dst_line_id = portal_pair_ids
                # Portal between landing and threshold.
                self.level.add_connector(Portal(
                    landing_x,
                    portal_y,
                    stair_w,
                    wall_thickness,
                    landing,
                    threshold,
                    source_line_id=src_line_id,
                    target_line_id=dst_line_id,
                    type=1,
                    planeanchor=1,
                    floor_tex=src_corridor.floor_tex,
                    ceil_tex=src_corridor.ceil_tex,
                    wall_tex=src_corridor.wall_tex,
                ))

            # Record a good test spawn at the base of the stairwell (in the hall), facing the steps.
            if set_spawn and not hasattr(self.level, "test_spawn"):
                spawn_x = hall_x + (hall_w // 2)
                spawn_y = hall_y + 32
                spawn_angle = 0 if side_dir > 0 else 180
                self.level.test_spawn = (int(spawn_x), int(spawn_y), int(spawn_angle))

        # Create a matching portal landing on the off-map second floor and connect it into the corridor.
        def add_second_floor_portal_entry(dst_corridor, side_dir: int, *, attach_y: int, portal_pair_ids):
            hall_h = steps * step_depth
            if side_dir > 0:
                hall_x = dst_corridor.x + dst_corridor.width + wall_thickness
            else:
                hall_x = dst_corridor.x - wall_thickness - 64
            hall_y = int(attach_y)
            hall_w = 64
            hall = self.level.add_room(Room(
                hall_x,
                hall_y,
                hall_w,
                hall_h,
                floor_tex=dst_corridor.floor_tex,
                wall_tex=dst_corridor.wall_tex,
                ceil_tex=dst_corridor.ceil_tex,
                floor_height=second_floor_floor,
                ceil_height=second_floor_ceil,
            ))

            # Connect off-map corridor -> hall (doorway-sized opening).
            corridor_door_h = 96
            corridor_door_y = hall_y + 32
            self.level.add_connector(Window(
                (dst_corridor.x + dst_corridor.width) if side_dir > 0 else (dst_corridor.x - wall_thickness),
                corridor_door_y,
                wall_thickness,
                corridor_door_h,
                dst_corridor,
                hall,
                sill_height=0,
                window_height=second_floor_ceil - second_floor_floor,
                floor_tex=dst_corridor.floor_tex,
                ceil_tex=dst_corridor.ceil_tex,
                wall_tex=dst_corridor.wall_tex,
            ))

            # Flat "step" slices (all at 2nd-floor height) so the portal landing is reachable.
            last_step_room = None
            for i in range(steps):
                step_floor = second_floor_floor
                step_y = hall_y + i * step_depth
                if side_dir > 0:
                    step_x = hall_x + hall_w + wall_thickness
                    gap_x = hall_x + hall_w
                else:
                    step_x = hall_x - wall_thickness - stair_w
                    gap_x = hall_x - wall_thickness

                step_room = self.level.add_room(Room(
                    step_x,
                    step_y,
                    stair_w,
                    step_depth,
                    floor_tex=dst_corridor.floor_tex,
                    wall_tex=dst_corridor.wall_tex,
                    ceil_tex=dst_corridor.ceil_tex,
                    floor_height=step_floor,
                    ceil_height=second_floor_ceil,
                ))
                if i == steps - 1:
                    last_step_room = step_room

                self.level.add_connector(Window(
                    gap_x,
                    step_y,
                    wall_thickness,
                    step_depth,
                    hall,
                    step_room,
                    sill_height=0,
                    window_height=second_floor_ceil - second_floor_floor,
                    floor_tex=dst_corridor.floor_tex,
                    ceil_tex=dst_corridor.ceil_tex,
                    wall_tex=dst_corridor.wall_tex,
                ))

            landing_y = hall_y + hall_h + wall_thickness
            if side_dir > 0:
                landing_x = hall_x + hall_w + wall_thickness
            else:
                landing_x = hall_x - wall_thickness - stair_w
            landing_h = step_depth
            landing = self.level.add_room(Room(
                landing_x,
                landing_y,
                stair_w,
                landing_h,
                floor_tex=dst_corridor.floor_tex,
                wall_tex=dst_corridor.wall_tex,
                ceil_tex=dst_corridor.ceil_tex,
                floor_height=second_floor_floor,
                ceil_height=second_floor_ceil,
            ))

            if last_step_room is not None:
                self.level.add_connector(Window(
                    landing_x,
                    hall_y + hall_h,
                    stair_w,
                    wall_thickness,
                    last_step_room,
                    landing,
                    sill_height=0,
                    window_height=second_floor_ceil - second_floor_floor,
                    floor_tex=dst_corridor.floor_tex,
                    ceil_tex=dst_corridor.ceil_tex,
                    wall_tex=dst_corridor.wall_tex,
                ))

            portal_y = landing_y + landing_h
            threshold_y = portal_y + wall_thickness
            threshold = self.level.add_room(Room(
                landing_x,
                threshold_y,
                stair_w,
                step_depth,
                floor_tex=dst_corridor.floor_tex,
                wall_tex=dst_corridor.wall_tex,
                ceil_tex=dst_corridor.ceil_tex,
                floor_height=second_floor_floor,
                ceil_height=second_floor_ceil,
            ))

            src_line_id, dst_line_id = portal_pair_ids
            # Reverse portal (off-map back down to main).
            self.level.add_connector(Portal(
                landing_x,
                portal_y,
                stair_w,
                wall_thickness,
                landing,
                threshold,
                source_line_id=dst_line_id,
                target_line_id=src_line_id,
                type=1,
                planeanchor=1,
                floor_tex=dst_corridor.floor_tex,
                ceil_tex=dst_corridor.ceil_tex,
                wall_tex=dst_corridor.wall_tex,
            ))

        # Portal ids (unique, large values to avoid clashing with sector tags)
        east_portal_ids = (40001, 40002)
        middle_portal_ids = (40003, 40004)
        west_portal_ids = (40005, 40006)

        # Place stairs near the north end of the corridor (toward the cross-corridor / mess hall).
        # Keep them off the room-door wall as much as possible.
        # Stairs should not overlap bedroom/bathroom door cuts along the corridor wall.
        # The East Wing corridor wall we attach to is a clean outside wall, so we can stay near the north end.
        east_north_attach_pad = 64

        east_attach_y = int(east_corridor.y + east_corridor.height - wall_thickness - stairs_h - east_north_attach_pad)

        # Middle attach_y values were computed earlier so we could reserve corridor window spans.
        east_attach_y_2 = int(east_corridor_2.y + east_corridor_2.height - wall_thickness - stairs_h - east_north_attach_pad)

        # Main floor stairwells.
        # Attach to the OUTSIDE wall of each corridor (a clean wall with no room-door cuts
        # and, if present, fewer window cuts), to avoid overlapping openings that can
        # create blocking geometry.
        # - West Wing stairs bump out into the brown-strip gap (east)        => side_dir = +1
        # - East Wing corridor is on the outside east; outside wall is east  => side_dir = +1
        # - Middle Wing stairs bump out into the lawn-side gap (east)        => side_dir = +1

        add_stairwell_to_corridor(
            west_corridor,
            side_dir=1,
            attach_y=west_attach_y,
            set_spawn=False,
            portal_target_corridor=west_corridor_2,
            portal_pair_ids=west_portal_ids,
        )

        add_second_floor_portal_entry(
            west_corridor_2,
            side_dir=1,
            attach_y=west_attach_y_2,
            portal_pair_ids=west_portal_ids,
        )

        add_stairwell_to_corridor(
            east_corridor,
            side_dir=1,
            attach_y=east_attach_y,
            set_spawn=True,
            portal_target_corridor=east_corridor_2,
            portal_pair_ids=east_portal_ids,
        )

        # Off-map portal entry corresponding to the stairwell top.
        add_second_floor_portal_entry(
            east_corridor_2,
            side_dir=1,
            attach_y=east_attach_y_2,
            portal_pair_ids=east_portal_ids,
        )

        # Middle Wing: add the same stairs + portal connection to its off-map 2nd floor.
        # DEBUG: Disable Middle Wing Portal to test blackout.
        add_stairwell_to_corridor(
            middle_corridor,
            side_dir=1,
            attach_y=middle_attach_y,
            set_spawn=False,
            portal_target_corridor=middle_corridor_2,
            portal_pair_ids=None, # middle_portal_ids,
        )
        add_second_floor_portal_entry(
            middle_corridor_2,
            side_dir=1,
            attach_y=middle_attach_y_2,
            portal_pair_ids=middle_portal_ids, # Keep this to generate the room, but portal won't link?
        )
        
        return self.level
