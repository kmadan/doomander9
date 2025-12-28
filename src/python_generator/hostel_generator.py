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

        # 2. Generate Left Wing (West)
        # Place the corridor on the OUTSIDE edge so the stairs can attach to a clean wall
        # (avoids overlaps with room doors/windows).
        # Wing rooms are 256 wide; keep a wall_thickness gap between rooms and the lawn.
        left_wing_x = self.start_x - 256 - wall_thickness
        left_wing = Wing(left_wing_x, self.start_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=False)
        left_corridor = left_wing.generate(self.level, lawn, floor_height=0, ceil_height=128, story_tag=0)
        
        # 3. Generate Right Wing (East)
        # Flipped: rooms adjacent to lawn, corridor on the outside (East)
        right_rooms_x = self.start_x + lawn_width + 16
        right_wing = Wing(right_rooms_x, self.start_y, side='right', num_rooms_per_side=7, corridor_on_lawn_side=False)
        right_corridor = right_wing.generate(self.level, lawn, floor_height=0, ceil_height=128, story_tag=0)
        
        # 4. Cross Corridor (North)
        # Connects Left Wing, Right Wing, Lawn, and Mess Hall
        lawn_top_y = self.start_y + lawn_height
        cross_y = lawn_top_y + wall_thickness
        cross_height = 128
        # Width spans from Left Wing Corridor Left Edge to Right Wing Corridor Right Edge
        # Left Wing Corridor X: left_wing_x
        # Right Wing Corridor X: right_wing_x
        # Right Wing Corridor Width: 128
        cross_x = left_corridor.x
        cross_width = (right_corridor.x + 128) - left_corridor.x
        
        cross_corridor = self.level.add_room(Corridor(cross_x, cross_y, cross_width, cross_height))
        
        # Connect Left Wing to Cross Corridor (Opening in the gap)
        self.level.add_connector(Window(left_corridor.x, lawn_top_y, 128, wall_thickness, left_corridor, cross_corridor, sill_height=0, window_height=128))
        
        # Connect Right Wing to Cross Corridor (Opening in the gap)
        self.level.add_connector(Window(right_corridor.x, lawn_top_y, 128, wall_thickness, right_corridor, cross_corridor, sill_height=0, window_height=128))
        
        # Connect Lawn to Cross Corridor (Wide opening in the gap)
        lawn_conn_width = 256
        lawn_conn_x = self.start_x + (lawn_width // 2) - (lawn_conn_width // 2)
        self.level.add_connector(Window(lawn_conn_x, lawn_top_y, lawn_conn_width, wall_thickness, lawn, cross_corridor, sill_height=0, window_height=128))
        
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
        # Place inside Cross Corridor near the door
        switch_x = door_x - 64
        switch_y = cross_top_y - 64
        self.level.add_connector(Switch(switch_x, switch_y, action=42, tag=mh_tag)) # 42 = SR Door Close
        
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
        gate1_x = self.start_x + 64 # Near Left Wing
        self.level.add_connector(Door(gate1_x, self.start_y - wall_thickness, gate_width, wall_thickness, outside, lawn, texture="BIGDOOR2", state='open', tag=gate1_tag, linedef_action=0))
        
        # Switch for Gate 1
        switch1_x = gate1_x - 32
        switch1_y = self.start_y + 64
        self.level.add_connector(Switch(switch1_x, switch1_y, action=42, tag=gate1_tag))
        
        # Gate 2 (Right)
        gate2_tag = self.level.get_new_tag()
        gate2_x = self.start_x + lawn_width - 64 - gate_width # Near Right Wing
        self.level.add_connector(Door(gate2_x, self.start_y - wall_thickness, gate_width, wall_thickness, outside, lawn, texture="BIGDOOR2", state='open', tag=gate2_tag, linedef_action=0))
        
        # Switch for Gate 2
        switch2_x = gate2_x + gate_width + 16
        switch2_y = self.start_y + 64
        self.level.add_connector(Switch(switch2_x, switch2_y, action=42, tag=gate2_tag))

        # 7. Stairs + off-map 2nd floor connected via line portals
        # The 2nd floor is a separate copy of the building placed off-map, so doors
        # are fully independent per floor. We connect at the top of the stairs using
        # Line_SetPortal so it feels seamless.
        stair_w = 64
        step_depth = 64
        steps = 7
        rise = 20

        # Off-map placement for the 2nd floor so it is visible in automap.
        # Place it north of the main area (same X footprint).
        second_floor_offset_y = -6000
        second_floor_floor = steps * rise  # 140
        second_floor_ceil = second_floor_floor + 128

        # Generate a disconnected 2nd-floor copy of the wings.
        lawn2 = self.level.add_room(Lawn(self.start_x, self.start_y + second_floor_offset_y, lawn_width, lawn_height, floor_tex="PYGRASS"))
        left_wing_2 = Wing(left_wing_x, self.start_y + second_floor_offset_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=False)
        left_corridor_2 = left_wing_2.generate(self.level, lawn2, floor_height=second_floor_floor, ceil_height=second_floor_ceil, story_tag=0)
        right_wing_2 = Wing(right_rooms_x, self.start_y + second_floor_offset_y, side='right', num_rooms_per_side=7, corridor_on_lawn_side=False)
        right_corridor_2 = right_wing_2.generate(self.level, lawn2, floor_height=second_floor_floor, ceil_height=second_floor_ceil, story_tag=0)

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
        right_portal_ids = (40001, 40002)
        left_portal_ids = (40003, 40004)

        # Place stairs near the north end of the corridor (toward the cross-corridor / mess hall).
        # Keep them off the room-door wall as much as possible.
        stairs_h = steps * step_depth
        north_attach_pad = 64
        right_attach_y = int(right_corridor.y + right_corridor.height - wall_thickness - stairs_h - north_attach_pad)
        left_attach_y = int(left_corridor.y + left_corridor.height - wall_thickness - stairs_h - north_attach_pad)

        right_attach_y_2 = int(right_corridor_2.y + right_corridor_2.height - wall_thickness - stairs_h - north_attach_pad)
        left_attach_y_2 = int(left_corridor_2.y + left_corridor_2.height - wall_thickness - stairs_h - north_attach_pad)

        # Main floor stairwells.
        # Attach to the OUTSIDE wall of each corridor (a clean wall with no room-door cuts
        # and, if present, fewer window cuts), to avoid overlapping openings that can
        # create blocking geometry.
        # - Right wing corridor is on the outside east; outside wall is east  => side_dir = +1
        # - Left wing corridor is on the outside west; outside wall is west  => side_dir = -1
        add_stairwell_to_corridor(
            right_corridor,
            side_dir=1,
            attach_y=right_attach_y,
            set_spawn=True,
            portal_target_corridor=right_corridor_2,
            portal_pair_ids=right_portal_ids,
        )

        # Off-map portal entry corresponding to the stairwell top.
        add_second_floor_portal_entry(
            right_corridor_2,
            side_dir=1,
            attach_y=right_attach_y_2,
            portal_pair_ids=right_portal_ids,
        )

        # Left wing: add the same stairs + portal connection to its off-map 2nd floor.
        add_stairwell_to_corridor(
            left_corridor,
            side_dir=-1,
            attach_y=left_attach_y,
            set_spawn=False,
            portal_target_corridor=left_corridor_2,
            portal_pair_ids=left_portal_ids,
        )
        add_second_floor_portal_entry(
            left_corridor_2,
            side_dir=-1,
            attach_y=left_attach_y_2,
            portal_pair_ids=left_portal_ids,
        )
        
        return self.level
