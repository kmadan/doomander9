from modules.level import Level
from modules.geometry import Corridor, Lawn, Room
from modules.connectors import Door, Switch, Window
from modules.prefabs import Bedroom, CommonRoom, Bathroom
from modules.wing import Wing
from modules.furniture import TeleportDestination

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
        lawn = self.level.add_room(Lawn(self.start_x, self.start_y, lawn_width, lawn_height))

        # Give the lawn a unique tag so we can target it for a ZDoom UDMF 3D floor.
        # This creates a visible "second floor" platform over the lawn.
        self.level.lawn_tag = self.level.get_new_tag()
        lawn.tag = self.level.lawn_tag
        
        # 2. Generate Left Wing (West)
        left_wing_x = self.start_x - 128 - 16
        left_wing = Wing(left_wing_x, self.start_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)
        left_corridor = left_wing.generate(self.level, lawn, floor_height=0, ceil_height=128)
        
        # 3. Generate Right Wing (East)
        # Flipped: rooms adjacent to lawn, corridor on the outside (East)
        right_rooms_x = self.start_x + lawn_width + 16
        right_wing = Wing(right_rooms_x, self.start_y, side='right', num_rooms_per_side=7, corridor_on_lawn_side=False)
        right_corridor = right_wing.generate(self.level, lawn, floor_height=0, ceil_height=128)
        
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
        outside = self.level.add_room(Lawn(self.start_x, outside_y, lawn_width, outside_height))
        
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

        # 7. Second Floors (per-wing, no cross corridor, no mess hall)
        # NOTE: This generator outputs classic Doom-format maps (no Hexen args),
        # so true GZDoom 3D-floor room-over-room isn't available here.
        # Instead, we place the 2nd-floor wings off-map and connect via teleports
        # so it plays like stairs/elevator up/down.
        second_floor_offset_x = 12000
        second_floor_offset_y = 0
        # Keep the "second floor" off-map for now, but make its height align with
        # a 20-unit rise stair run (7 steps => 140 height).
        second_floor_height = 140

        lawn2 = self.level.add_room(Lawn(
            second_floor_offset_x,
            second_floor_offset_y,
            lawn_width,
            lawn_height,
        ))
        lawn2.floor_height = second_floor_height
        lawn2.ceil_height = second_floor_height + 256

        # Second-floor Left Wing
        left2_wing_x = second_floor_offset_x - 128 - wall_thickness
        left2_wing = Wing(left2_wing_x, second_floor_offset_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)
        left2_corridor = left2_wing.generate(self.level, lawn2, floor_height=second_floor_height, ceil_height=second_floor_height + 128)

        # Second-floor Right Wing (flipped like ground)
        right2_rooms_x = second_floor_offset_x + lawn_width + wall_thickness
        right2_wing = Wing(right2_rooms_x, second_floor_offset_y, side='right', num_rooms_per_side=7, corridor_on_lawn_side=False)
        right2_corridor = right2_wing.generate(self.level, lawn2, floor_height=second_floor_height, ceil_height=second_floor_height + 128)

        # Teleport up/down for each wing at the SOUTH end of the corridor
        def add_wing_elevator_pair(ground_corridor, upper_corridor):
            # Create tags for destinations
            up_tag = self.level.get_new_tag()
            down_tag = self.level.get_new_tag()

            # Tag the destination corridors and add teleport landing things
            upper_corridor.tag = up_tag
            upper_corridor.add_furniture(TeleportDestination(upper_corridor.x + 64, upper_corridor.y + 64, angle=0))
            ground_corridor.tag = down_tag
            ground_corridor.add_furniture(TeleportDestination(ground_corridor.x + 64, ground_corridor.y + 64, angle=180))

            # Replace the old "teleport elevator" doorway with an actual step staircase
            # on the main map. At the top of the stairs, a teleport portal takes you
            # to the off-map second floor.
            stair_w = 64
            step_depth = 64
            steps = 7
            rise = 20

            def add_stairs_to_teleport(src_corridor, dest_tag, label_prefix: str):
                # Center stairs under the corridor.
                stair_x = src_corridor.x + (128 - stair_w) // 2
                # First step sits just south of the corridor, separated by wall thickness.
                first_step_y = src_corridor.y - wall_thickness - step_depth

                first_step_room = None
                for i in range(steps):
                    step_floor = (i + 1) * rise
                    step_room = self.level.add_room(Room(
                        stair_x,
                        first_step_y - (i * step_depth),
                        stair_w,
                        step_depth,
                        floor_tex=src_corridor.floor_tex,
                        wall_tex=src_corridor.wall_tex,
                        ceil_tex=src_corridor.ceil_tex,
                        floor_height=step_floor,
                        ceil_height=step_floor + 128,
                    ))
                    if first_step_room is None:
                        first_step_room = step_room

                top_floor = steps * rise
                top_y = first_step_y - (steps * step_depth)
                top_landing = self.level.add_room(Room(
                    stair_x,
                    top_y,
                    stair_w,
                    step_depth,
                    floor_tex=src_corridor.floor_tex,
                    wall_tex=src_corridor.wall_tex,
                    ceil_tex=src_corridor.ceil_tex,
                    floor_height=top_floor,
                    ceil_height=top_floor + 128,
                ))

                # Opening from corridor -> first step (in the wall gap).
                self.level.add_connector(Window(
                    stair_x,
                    src_corridor.y - wall_thickness,
                    stair_w,
                    wall_thickness,
                    src_corridor,
                    first_step_room,
                    sill_height=0,
                    window_height=128,
                ))

                # Portal sector south of landing (same floor), with a teleport doorway between.
                portal_h = 64
                portal = self.level.add_room(Room(
                    stair_x,
                    top_y - portal_h - wall_thickness,
                    stair_w,
                    portal_h,
                    floor_tex=src_corridor.floor_tex,
                    wall_tex=src_corridor.wall_tex,
                    ceil_tex=src_corridor.ceil_tex,
                    floor_height=top_floor,
                    ceil_height=top_floor + 128,
                ))

                self.level.add_connector(Door(
                    stair_x,
                    top_y - wall_thickness,
                    stair_w,
                    wall_thickness,
                    portal,
                    top_landing,
                    state='open',
                    tag=dest_tag,
                    linedef_action=97,  # WR Teleport
                ))

                # HUD labels: one at corridor entry and one at portal.
                top_center_x = stair_x + stair_w // 2
                # Removed label spots

            add_stairs_to_teleport(ground_corridor, up_tag, "STAIRS UP")
            add_stairs_to_teleport(upper_corridor, down_tag, "STAIRS DOWN")

        add_wing_elevator_pair(left_corridor, left2_corridor)
        add_wing_elevator_pair(right_corridor, right2_corridor)
        
        return self.level
