from modules.level import Level
from modules.geometry import Corridor, Lawn, Room
from modules.connectors import Door, Switch, Window
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
        lawn = self.level.add_room(Lawn(self.start_x, self.start_y, lawn_width, lawn_height))

        # A shared tag applied to wing sectors so we can add a real 2nd-story 3D floor
        # *inside the building*, without covering the lawn (sky stays visible).
        self.level.second_floor_tag = self.level.get_new_tag()
        
        # 2. Generate Left Wing (West)
        left_wing_x = self.start_x - 128 - 16
        left_wing = Wing(left_wing_x, self.start_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)
        left_corridor = left_wing.generate(self.level, lawn, floor_height=0, ceil_height=128, story_tag=self.level.second_floor_tag)
        
        # 3. Generate Right Wing (East)
        # Flipped: rooms adjacent to lawn, corridor on the outside (East)
        right_rooms_x = self.start_x + lawn_width + 16
        right_wing = Wing(right_rooms_x, self.start_y, side='right', num_rooms_per_side=7, corridor_on_lawn_side=False)
        right_corridor = right_wing.generate(self.level, lawn, floor_height=0, ceil_height=128, story_tag=self.level.second_floor_tag)
        
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

        # 7. Stairs to the real 2nd story (no teleports)
        # Build the staircase on the *outer* side of the right corridor (no corridor windows there),
        # and use a small tagged "hall" sector so you can step from the stair top onto the
        # 3D-floor second story inside the corridor.
        stair_w = 64
        step_depth = 64
        steps = 7
        rise = 20

        def add_stairwell_to_corridor(src_corridor, side_dir: int, *, set_spawn: bool):
            attach_y = src_corridor.y + 64
            hall_h = steps * step_depth

            # A thin "hall" right outside the corridor, tagged for the 3D-floor second story.
            if side_dir > 0:
                hall_x = src_corridor.x + src_corridor.width + wall_thickness
            else:
                hall_x = src_corridor.x - wall_thickness - 64
            hall_y = attach_y
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
                tag=self.level.second_floor_tag,
            ))

            # Steps adjacent to the hall, with an explicit gap + connector per step.
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
            self.level.add_connector(Window(
                (src_corridor.x + src_corridor.width) if side_dir > 0 else (src_corridor.x - wall_thickness),
                hall_y,
                wall_thickness,
                hall_h,
                src_corridor,
                hall,
                sill_height=0,
                window_height=320,
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

        # Right wing: corridor is on outside edge, so put stairs further outward (east)
        add_stairwell_to_corridor(right_corridor, side_dir=1, set_spawn=True)
        # Left wing: corridor is on lawn side, so put stairs on outside edge (west)
        add_stairwell_to_corridor(left_corridor, side_dir=-1, set_spawn=False)
        
        return self.level
