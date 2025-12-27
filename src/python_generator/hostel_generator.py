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
        
        # 2. Generate Left Wing (West)
        left_wing_x = self.start_x - 128 - 16
        left_wing = Wing(left_wing_x, self.start_y, side='left', num_rooms_per_side=7)
        left_corridor = left_wing.generate(self.level, lawn)
        
        # 3. Generate Right Wing (East)
        right_wing_x = self.start_x + lawn_width + 16
        right_wing = Wing(right_wing_x, self.start_y, side='right', num_rooms_per_side=7)
        right_corridor = right_wing.generate(self.level, lawn)
        
        # 4. Cross Corridor (North)
        # Connects Left Wing, Right Wing, Lawn, and Mess Hall
        lawn_top_y = self.start_y + lawn_height
        cross_y = lawn_top_y + wall_thickness
        cross_height = 128
        # Width spans from Left Wing Corridor Left Edge to Right Wing Corridor Right Edge
        # Left Wing Corridor X: left_wing_x
        # Right Wing Corridor X: right_wing_x
        # Right Wing Corridor Width: 128
        cross_x = left_wing_x
        cross_width = (right_wing_x + 128) - left_wing_x
        
        cross_corridor = self.level.add_room(Corridor(cross_x, cross_y, cross_width, cross_height))
        
        # Connect Left Wing to Cross Corridor (Opening in the gap)
        self.level.add_connector(Window(left_wing_x, lawn_top_y, 128, wall_thickness, left_corridor, cross_corridor, sill_height=0, window_height=128))
        
        # Connect Right Wing to Cross Corridor (Opening in the gap)
        self.level.add_connector(Window(right_wing_x, lawn_top_y, 128, wall_thickness, right_corridor, cross_corridor, sill_height=0, window_height=128))
        
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
        
        return self.level
