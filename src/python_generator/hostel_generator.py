import os

from typing import Tuple, Optional, Dict
from modules.level import Level
from modules.geometry import Lawn, Room
from modules.connectors import Window, Portal
from modules.wing import Wing

from layout.stairs import (
    StairsSpec,
    add_second_floor_portal_entry,
    add_stair_extension,
    add_stairwell_to_corridor,
)

from layout.hostel_layout import (
    build_brown_west_half_segments,
    build_brown_strip,
    build_central_lawn,
    build_cross_corridor_and_connections,
    build_mess_hall_with_door_and_switch,
    build_middle_lawn_buffer,
    build_south_gates_and_outside,
    compute_stair_attach_and_reserved_span,
    DEFAULT_CORRIDOR_W,
    DEFAULT_ROOM_W,
)
 

class HostelGenerator:
    def __init__(self, start_x: int = 0, start_y: int = 0) -> None:
        self.start_x = start_x
        self.start_y = start_y
        self.level = Level()
        
        # Configuration
        self.wall_thickness = 16
        self.stair_w = 64
        self.step_depth = 64
        self.steps = 7
        self.rise = 20
        self.stairs_h = self.steps * self.step_depth
        self.hall_h = self.stairs_h

        # Centralize stair geometry defaults so the layout can call into
        # modular stair builders without duplicating constants.
        self.stairs_spec = StairsSpec(
            wall_thickness=self.wall_thickness,
            stair_w=self.stair_w,
            step_depth=self.step_depth,
            steps=self.steps,
            rise=self.rise,
        )

    def _create_stairwell(self, src_corridor: Room, side_dir: int, *, attach_y: int, set_spawn: bool, portal_target_corridor: Optional[Room] = None, portal_pair_ids: Optional[Tuple[int, int]] = None) -> Dict[str, Room]:
        hall_h = self.steps * self.step_depth

        # A thin "hall" right outside the corridor.
        if side_dir > 0:
            hall_x = src_corridor.x + src_corridor.width + self.wall_thickness
        else:
            hall_x = src_corridor.x - self.wall_thickness - 64
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
            floor_height=src_corridor.floor_height,
            ceil_height=320,
        ))

        # Steps adjacent to the hall, with an explicit gap + connector per step.
        last_step_room = None
        for i in range(self.steps):
            step_floor = src_corridor.floor_height + (i + 1) * self.rise
            step_y = hall_y + i * self.step_depth
            if side_dir > 0:
                step_x = hall_x + hall_w + self.wall_thickness
                gap_x = hall_x + hall_w
            else:
                step_x = hall_x - self.wall_thickness - self.stair_w
                gap_x = hall_x - self.wall_thickness

            step_room = self.level.add_room(Room(
                step_x,
                step_y,
                self.stair_w,
                self.step_depth,
                floor_tex=src_corridor.floor_tex,
                wall_tex=src_corridor.wall_tex,
                ceil_tex=src_corridor.ceil_tex,
                floor_height=step_floor,
                ceil_height=320,
            ))

            if i == self.steps - 1:
                last_step_room = step_room

            # Opening between hall <-> this step slice.
            self.level.add_connector(Window(
                gap_x,
                step_y,
                self.wall_thickness,
                self.step_depth,
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
            (src_corridor.x + src_corridor.width) if side_dir > 0 else (src_corridor.x - self.wall_thickness),
            corridor_door_y,
            self.wall_thickness,
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
        landing_y = hall_y + hall_h + self.wall_thickness
        landing_h = self.step_depth
        if side_dir > 0:
            landing_x = hall_x + hall_w + self.wall_thickness
        else:
            landing_x = hall_x - self.wall_thickness - self.stair_w
        landing = self.level.add_room(Room(
            landing_x,
            landing_y,
            self.stair_w,
            landing_h,
            floor_tex=src_corridor.floor_tex,
            wall_tex=src_corridor.wall_tex,
            ceil_tex=src_corridor.ceil_tex,
            floor_height=src_corridor.floor_height + self.steps * self.rise,
            ceil_height=320,
        ))

        # Connect the last step slice to the landing through a wall-thickness gap.
        if last_step_room is not None:
            self.level.add_connector(Window(
                landing_x,
                hall_y + hall_h,
                self.stair_w,
                self.wall_thickness,
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
        threshold_y = portal_y + self.wall_thickness
        threshold = self.level.add_room(Room(
            landing_x,
            threshold_y,
            self.stair_w,
            self.step_depth,
            floor_tex=src_corridor.floor_tex,
            wall_tex=src_corridor.wall_tex,
            ceil_tex=src_corridor.ceil_tex,
            floor_height=src_corridor.floor_height + self.steps * self.rise,
            ceil_height=320,
        ))

        if portal_target_corridor is not None and portal_pair_ids is not None:
            src_line_id, dst_line_id = portal_pair_ids
            # Portal between landing and threshold.
            self.level.add_connector(Portal(
                landing_x,
                portal_y,
                self.stair_w,
                self.wall_thickness,
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
        
        return {'hall': hall, 'landing': landing, 'threshold': threshold}

    def _create_portal_landing(self, dst_corridor: Room, side_dir: int, *, attach_y: int, portal_pair_ids: Tuple[int, int]) -> Dict[str, Room]:
        hall_h = self.steps * self.step_depth
        if side_dir > 0:
            hall_x = dst_corridor.x + dst_corridor.width + self.wall_thickness
        else:
            hall_x = dst_corridor.x - self.wall_thickness - 64
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
            floor_height=dst_corridor.floor_height,
            ceil_height=dst_corridor.ceil_height,
        ))

        # Connect off-map corridor -> hall (doorway-sized opening).
        corridor_door_h = 96
        corridor_door_y = hall_y + 32
        self.level.add_connector(Window(
            (dst_corridor.x + dst_corridor.width) if side_dir > 0 else (dst_corridor.x - self.wall_thickness),
            corridor_door_y,
            self.wall_thickness,
            corridor_door_h,
            dst_corridor,
            hall,
            sill_height=0,
            window_height=dst_corridor.ceil_height - dst_corridor.floor_height,
            floor_tex=dst_corridor.floor_tex,
            ceil_tex=dst_corridor.ceil_tex,
            wall_tex=dst_corridor.wall_tex,
        ))

        # Flat "step" slices (all at 2nd-floor height) so the portal landing is reachable.
        last_step_room = None
        for i in range(self.steps):
            step_floor = dst_corridor.floor_height
            step_y = hall_y + i * self.step_depth
            if side_dir > 0:
                step_x = hall_x + hall_w + self.wall_thickness
                gap_x = hall_x + hall_w
            else:
                step_x = hall_x - self.wall_thickness - self.stair_w
                gap_x = hall_x - self.wall_thickness

            step_room = self.level.add_room(Room(
                step_x,
                step_y,
                self.stair_w,
                self.step_depth,
                floor_tex=dst_corridor.floor_tex,
                wall_tex=dst_corridor.wall_tex,
                ceil_tex=dst_corridor.ceil_tex,
                floor_height=step_floor,
                ceil_height=dst_corridor.ceil_height,
            ))
            if i == self.steps - 1:
                last_step_room = step_room

            self.level.add_connector(Window(
                gap_x,
                step_y,
                self.wall_thickness,
                self.step_depth,
                hall,
                step_room,
                sill_height=0,
                window_height=dst_corridor.ceil_height - dst_corridor.floor_height,
                floor_tex=dst_corridor.floor_tex,
                ceil_tex=dst_corridor.ceil_tex,
                wall_tex=dst_corridor.wall_tex,
            ))

        landing_y = hall_y + hall_h + self.wall_thickness
        landing_h = self.step_depth
        if side_dir > 0:
            landing_x = hall_x + hall_w + self.wall_thickness
        else:
            landing_x = hall_x - self.wall_thickness - self.stair_w
        landing = self.level.add_room(Room(
            landing_x,
            landing_y,
            self.stair_w,
            landing_h,
            floor_tex=dst_corridor.floor_tex,
            wall_tex=dst_corridor.wall_tex,
            ceil_tex=dst_corridor.ceil_tex,
            floor_height=dst_corridor.floor_height,
            ceil_height=dst_corridor.ceil_height,
        ))

        if last_step_room is not None:
            self.level.add_connector(Window(
                landing_x,
                hall_y + hall_h,
                self.stair_w,
                self.wall_thickness,
                last_step_room,
                landing,
                sill_height=0,
                window_height=dst_corridor.ceil_height - dst_corridor.floor_height,
                floor_tex=dst_corridor.floor_tex,
                ceil_tex=dst_corridor.ceil_tex,
                wall_tex=dst_corridor.wall_tex,
            ))

        portal_y = landing_y + landing_h
        threshold_y = portal_y + self.wall_thickness
        threshold = self.level.add_room(Room(
            landing_x,
            threshold_y,
            self.stair_w,
            self.step_depth,
            floor_tex=dst_corridor.floor_tex,
            wall_tex=dst_corridor.wall_tex,
            ceil_tex=dst_corridor.ceil_tex,
            floor_height=dst_corridor.floor_height,
            ceil_height=dst_corridor.ceil_height,
        ))

        src_line_id, dst_line_id = portal_pair_ids
        # Reverse portal (off-map back down to main).
        self.level.add_connector(Portal(
            landing_x,
            portal_y,
            self.stair_w,
            self.wall_thickness,
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
        
        return {'hall': hall, 'landing': landing, 'threshold': threshold}

    def _extend_staircase(self, start_room: Room, portal_pair_ids: Tuple[int, int], floor_height: int, ceil_height: int) -> Room:
        # Extends stairs from the North side of start_room.
        # start_room is assumed to be the Landing of the previous flight.
        # We build Steps -> Landing -> Threshold going North (+Y).
        
        start_y = start_room.y + start_room.height + self.wall_thickness
        start_x = start_room.x
        
        # Steps
        # We use gaps between steps to allow for connectors (Windows).
        current_y = start_y
        prev_room = start_room
        
        for i in range(self.steps):
            step_floor = floor_height + (i + 1) * self.rise
            
            # Gap/Connector
            # We need a connector between prev_room and this step.
            # But Window creates the connector sector.
            # So we place the step at current_y + self.wall_thickness.
            
            step_y = current_y + self.wall_thickness
            step_room = self.level.add_room(Room(
                start_x,
                step_y,
                self.stair_w,
                self.step_depth,
                floor_tex=start_room.floor_tex,
                wall_tex=start_room.wall_tex,
                ceil_tex=start_room.ceil_tex,
                floor_height=step_floor,
                ceil_height=ceil_height,
            ))
            
            self.level.add_connector(Window(
                start_x,
                current_y,
                self.stair_w,
                self.wall_thickness,
                prev_room,
                step_room,
                sill_height=0,
                window_height=ceil_height,
                floor_tex=start_room.floor_tex,
                ceil_tex=start_room.ceil_tex,
                wall_tex=start_room.wall_tex,
            ))
            
            prev_room = step_room
            current_y = step_y + self.step_depth

        # Landing
        landing_y = current_y + self.wall_thickness
        landing = self.level.add_room(Room(
            start_x,
            landing_y,
            self.stair_w,
            self.step_depth,
            floor_tex=start_room.floor_tex,
            wall_tex=start_room.wall_tex,
            ceil_tex=start_room.ceil_tex,
            floor_height=floor_height + self.steps * self.rise,
            ceil_height=ceil_height,
        ))
        
        self.level.add_connector(Window(
            start_x,
            current_y,
            self.stair_w,
            self.wall_thickness,
            prev_room,
            landing,
            sill_height=0,
            window_height=ceil_height,
            floor_tex=start_room.floor_tex,
            ceil_tex=start_room.ceil_tex,
            wall_tex=start_room.wall_tex,
        ))
        
        # Threshold
        threshold_y = landing_y + self.step_depth + self.wall_thickness
        threshold = self.level.add_room(Room(
            start_x,
            threshold_y,
            self.stair_w,
            self.step_depth,
            floor_tex=start_room.floor_tex,
            wall_tex=start_room.wall_tex,
            ceil_tex=start_room.ceil_tex,
            floor_height=floor_height + self.steps * self.rise,
            ceil_height=ceil_height,
        ))
        
        self.level.add_connector(Portal(
            start_x,
            landing_y + self.step_depth,
            self.stair_w,
            self.wall_thickness,
            landing,
            threshold,
            source_line_id=portal_pair_ids[0],
            target_line_id=portal_pair_ids[1],
            type=1,
            planeanchor=1,
            floor_tex=start_room.floor_tex,
            ceil_tex=start_room.ceil_tex,
            wall_tex=start_room.wall_tex,
        ))
        
        return threshold
        
    def generate(self) -> Level:
        # Calculate Wing Height to match Lawn Height
        # Wing: 7 rooms + Bathroom (2 rooms) + 7 rooms = 16 units
        # Unit = 256 + 16 = 272
        # Total = 16 * 272 + 16 = 4368
        wing_height = 4368
        lawn_width = 512
        lawn_height = wing_height 
        
        # 1. Create Central Lawn
        lawn = build_central_lawn(self.level, x=self.start_x, y=self.start_y, width=lawn_width, height=lawn_height, floor_tex="PYGRASS")

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
        stair_bumpout_clearance = self.wall_thickness + 64 + self.wall_thickness + 64 + self.wall_thickness
        middle_wing_x = self.start_x - DEFAULT_CORRIDOR_W - stair_bumpout_clearance
        middle_wing = Wing(middle_wing_x, self.start_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)

        # 2b. Add the West Wing, with a brown outdoor ground strip between it and the Middle Wing.
        # The strip is just an outdoor sector (sky ceiling) with a brown ground flat.
        # Leave a wall-thickness gap so Middle Wing room windows can open onto it.
        #
        # We split the strip into two halves (west/east):
        # - East half: continuous full-height strip used by Middle Wing bedroom windows.
        # - West half: used by West Wing corridor lookouts, with a vertical cut-out where West Wing stairs bump out.
        brown_width = 512

        # West Wing stairs attach point (used to carve out the brown strip so the stair bump-out doesn't overlap it).
        west_north_attach_pad = 224
        west_attach_y, west_stair_reserved_y0, west_stair_reserved_y1 = compute_stair_attach_and_reserved_span(
            start_y=self.start_y,
            wing_height=wing_height,
            wall_thickness=self.wall_thickness,
            stairs_h=self.stairs_h,
            hall_h=self.hall_h,
            step_depth=self.step_depth,
            north_attach_pad=west_north_attach_pad,
        )

        brown = build_brown_strip(
            self.level,
            start_y=self.start_y,
            height=lawn_height,
            wall_thickness=self.wall_thickness,
            middle_wing_x=middle_wing_x,
            brown_width=brown_width,
            west_stair_reserved_y0=west_stair_reserved_y0,
            west_stair_reserved_y1=west_stair_reserved_y1,
            floor_tex="RROCK19",
        )

        # Preserve original local names (used later for 2nd-floor generation).
        brown_half_w = brown.half_w
        brown_ground_west_x = brown.west_x
        brown_ground_east_x = brown.east_x
        brown_ground_east = brown.east
        brown_ground_west_default = brown.west_default
        corridor_window_targets_west = brown.corridor_window_targets_west
        brown_ground_x = brown_ground_west_x

        # Generate the Middle Wing now that the brown strip exists, so room windows can look onto it.
        # Re-enable corridor lookouts toward the lawn, but skip the vertical span where the stairwell bump-out attaches.
        middle_north_attach_pad = 224
        middle_attach_y, middle_stair_reserved_y0, middle_stair_reserved_y1 = compute_stair_attach_and_reserved_span(
            start_y=self.start_y,
            wing_height=wing_height,
            wall_thickness=self.wall_thickness,
            stairs_h=self.stairs_h,
            hall_h=self.hall_h,
            step_depth=self.step_depth,
            north_attach_pad=middle_north_attach_pad,
        )

        buffer = build_middle_lawn_buffer(
            self.level,
            start_y=self.start_y,
            height=lawn_height,
            wall_thickness=self.wall_thickness,
            middle_wing_x=middle_wing_x,
            lawn=lawn,
            reserved_y0=middle_stair_reserved_y0,
            reserved_y1=middle_stair_reserved_y1,
            floor_tex="PYGRASS",
            connect_window_height=256,
            connect_floor_tex="PYGRASS",
            connect_ceil_tex="F_SKY1",
        )

        corridor_window_targets = buffer.corridor_window_targets

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
        # with width=self.wall_thickness, so brown_ground_x must equal corridor_x + 128 + self.wall_thickness.
        west_wing_x = brown_ground_x - (DEFAULT_CORRIDOR_W + self.wall_thickness)
        west_wing = Wing(west_wing_x, self.start_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)

        # Vacant, inaccessible outdoor area west of the West Wing.
        # This gives the West Wing room windows something to look out onto.
        west_outside_width = 768
        west_outside_x = west_wing_x - DEFAULT_ROOM_W - self.wall_thickness - west_outside_width - self.wall_thickness
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
        east_rooms_x = self.start_x + lawn_width + self.wall_thickness
        east_wing = Wing(east_rooms_x, self.start_y, side='right', num_rooms_per_side=7, corridor_on_lawn_side=False)
        east_corridor = east_wing.generate(self.level, lawn, floor_height=0, ceil_height=128, story_tag=0)
        
        # 4. Cross Corridor (North)
        # Connects West Wing, Middle Wing, East Wing, Lawn, and Mess Hall
        lawn_top_y = self.start_y + lawn_height
        cross_height = 128
        cross_corridor = build_cross_corridor_and_connections(
            self.level,
            west_corridor=west_corridor,
            middle_corridor=middle_corridor,
            east_corridor=east_corridor,
            lawn=lawn,
            lawn_top_y=lawn_top_y,
            wall_thickness=self.wall_thickness,
            brown_ground_east=brown_ground_east,
            brown_half_w=brown_half_w,
            brown_ground_east_x=brown_ground_east_x,
            cross_height=cross_height,
        )
        
        # 5. Mess Hall (North of Cross Corridor)
        cross_y = lawn_top_y + self.wall_thickness
        build_mess_hall_with_door_and_switch(
            self.level,
            start_x=self.start_x,
            cross_corridor=cross_corridor,
            lawn_width=lawn_width,
            wall_thickness=self.wall_thickness,
            cross_y=cross_y,
            cross_height=cross_height,
            mess_hall_height=512,
        )
        
        # 6. Gates (South)
        build_south_gates_and_outside(
            self.level,
            start_x=self.start_x,
            start_y=self.start_y,
            lawn_width=lawn_width,
            wall_thickness=self.wall_thickness,
            lawn=lawn,
            outside_height=256,
        )

        # 7. Stairs + off-map 2nd floor connected via line portals
        # The 2nd floor is a separate copy of the building placed off-map, so doors
        # are fully independent per floor. We connect at the top of the stairs using
        # Line_SetPortal so it feels seamless.
        # Off-map placement for the 2nd floor so it is visible in automap.
        # Place it north of the main area (same X footprint).
        second_floor_offset_y = -6000
        second_floor_floor = self.steps * self.rise  # 140
        second_floor_ceil = second_floor_floor + 128

        # Generate a disconnected 2nd-floor copy of the wings.
        lawn2 = build_central_lawn(
            self.level,
            x=self.start_x,
            y=self.start_y + second_floor_offset_y,
            width=lawn_width,
            height=lawn_height,
            floor_tex="PYGRASS",
        )
        # Off-map outdoor areas stay at floor 0 so upper floors feel elevated,
        # but we ensure ceilings are high enough for 2nd-floor window openings.
        lawn2.floor_height = 0
        lawn2.ceil_height = max(int(getattr(lawn2, 'ceil_height', 0) or 0), int(second_floor_ceil))

        # West Wing off-map copy + its outdoor areas.
        west_wing_2 = Wing(west_wing_x, self.start_y + second_floor_offset_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)
        west_attach_y_2, west_stair_reserved_y0_2, west_stair_reserved_y1_2 = compute_stair_attach_and_reserved_span(
            start_y=self.start_y + second_floor_offset_y,
            wing_height=wing_height,
            wall_thickness=self.wall_thickness,
            stairs_h=self.stairs_h,
            hall_h=self.hall_h,
            step_depth=self.step_depth,
            north_attach_pad=west_north_attach_pad,
        )

        # Middle/West have an additional F2->F3 stair extension. It starts from the
        # F2 portal-entry landing and runs north, so we must extend the *upper*
        # reserved bound to avoid building outdoor sectors in that space.
        stair_ext_span_h = int(
            (int(self.stairs_spec.steps) + 2) * (int(self.stairs_spec.wall_thickness) + int(self.stairs_spec.step_depth))
            + int(self.stairs_spec.step_depth)
        )
        west_stair_reserved_y1_2_ext = int(west_stair_reserved_y1_2 + stair_ext_span_h)

        # Reserved span is used to carve out outdoor sectors where the stairwell
        # bump-out sits (prevents overlaps).

        # Off-map brown strip west-half segments for West Wing corridor lookouts.
        brown_west_2 = build_brown_west_half_segments(
            self.level,
            west_x=brown_ground_west_x,
            start_y=self.start_y + second_floor_offset_y,
            height=lawn_height,
            half_w=brown_half_w,
            reserved_y0=west_stair_reserved_y0_2,
            reserved_y1=west_stair_reserved_y1_2_ext,
            floor_tex="RROCK19",
        )

        brown_ground_west_default_2 = brown_west_2.west_default
        corridor_window_targets_west_2 = brown_west_2.corridor_window_targets_west

        # Off-map outdoor segments: keep floor low but raise ceiling for F2 windows.
        for _r in (brown_west_2.west_default, brown_west_2.west_south, brown_west_2.west_north):
            if _r is None:
                continue
            _r.floor_height = 0
            _r.ceil_height = max(int(getattr(_r, 'ceil_height', 0) or 0), int(second_floor_ceil))

        west_outside_2 = self.level.add_room(Lawn(west_outside_x, self.start_y + second_floor_offset_y, west_outside_width, lawn_height, floor_tex="PYGRASS"))
        west_outside_2.floor_height = 0
        west_outside_2.ceil_height = max(int(getattr(west_outside_2, 'ceil_height', 0) or 0), int(second_floor_ceil))
        west_corridor_2 = west_wing_2.generate(
            self.level,
            brown_ground_west_default_2,
            floor_height=second_floor_floor,
            ceil_height=second_floor_ceil,
            story_tag=0,
            exterior_area=west_outside_2,
            add_corridor_windows=True,
            corridor_window_skip_ranges=[(west_stair_reserved_y0_2, west_stair_reserved_y1_2_ext)],
            corridor_window_targets=corridor_window_targets_west_2,
            door_state='closed',
        )

        middle_wing_2 = Wing(middle_wing_x, self.start_y + second_floor_offset_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)
        middle_attach_y_2, middle_stair_reserved_y0_2, middle_stair_reserved_y1_2 = compute_stair_attach_and_reserved_span(
            start_y=self.start_y + second_floor_offset_y,
            wing_height=wing_height,
            wall_thickness=self.wall_thickness,
            stairs_h=self.stairs_h,
            hall_h=self.hall_h,
            step_depth=self.step_depth,
            north_attach_pad=middle_north_attach_pad,
        )

        middle_stair_reserved_y1_2_ext = int(middle_stair_reserved_y1_2 + stair_ext_span_h)

        # Off-map buffer strip between Middle corridor and off-map lawn2.
        # Important: preserve connector texture defaults by not passing floor/ceil textures.
        buffer_2 = build_middle_lawn_buffer(
            self.level,
            start_y=self.start_y + second_floor_offset_y,
            height=lawn_height,
            wall_thickness=self.wall_thickness,
            middle_wing_x=middle_wing_x,
            lawn=lawn2,
            reserved_y0=middle_stair_reserved_y0_2,
            reserved_y1=middle_stair_reserved_y1_2_ext,
            floor_tex="PYGRASS",
            # Keep the buffer→lawn connection at ground level so it doesn't show up
            # as a raised "grass ledge" (floating strip) from the upper corridor.
            # Ceiling is still high enough for 2nd-floor sightlines.
            connect_window_height=int(second_floor_ceil),
            connect_sill_height=0,
            # Use sky ceiling for elevated outdoor connectors to avoid visible
            # "floating ceiling" strips against the sky.
            pass_window_textures=True,
        )

        # Outdoor buffer segments stay at floor 0 but need tall ceilings.
        for _r in (buffer_2.south, buffer_2.north):
            if _r is None:
                continue
            _r.floor_height = 0
            _r.ceil_height = max(int(getattr(_r, 'ceil_height', 0) or 0), int(second_floor_ceil))

        # Middle Wing bedroom windows (outside-facing) should look out into the
        # brown strip, not into per-room "window boxes".
        brown_ground_east_2 = self.level.add_room(
            Lawn(
                int(brown_ground_east_x),
                int(self.start_y + second_floor_offset_y),
                int(brown_half_w),
                int(lawn_height),
                floor_tex="RROCK19",
            )
        )
        brown_ground_east_2.floor_height = 0
        brown_ground_east_2.ceil_height = max(int(getattr(brown_ground_east_2, 'ceil_height', 0) or 0), int(second_floor_ceil))

        # Connect west-half brown segments to the east-half so Middle Wing bedroom
        # windows don't stare at a solid partition wall.
        # We make the connection an elevated opening at the 2nd-floor height so
        # the outdoor ground remains far below but sightlines reach the West Wing.
        halves_gap_x_2 = int(brown_ground_west_x) + int(brown_half_w)
        connect_h_2 = int(second_floor_ceil - second_floor_floor)
        for _seg in (brown_west_2.west_south, brown_west_2.west_north):
            if _seg is None:
                continue
            self.level.add_connector(
                Window(
                    halves_gap_x_2,
                    int(_seg.y),
                    int(self.wall_thickness),
                    int(_seg.height),
                    _seg,
                    brown_ground_east_2,
                    sill_height=int(second_floor_floor),
                    window_height=connect_h_2,
                    floor_tex=str(_seg.floor_tex),
                    ceil_tex="F_SKY1",
                )
            )

        corridor_window_targets_2 = buffer_2.corridor_window_targets

        middle_corridor_2 = middle_wing_2.generate(
            self.level,
            lawn2,
            floor_height=second_floor_floor,
            ceil_height=second_floor_ceil,
            story_tag=0,
            exterior_area=brown_ground_east_2,
            add_corridor_windows=True,
            corridor_window_skip_ranges=[(middle_stair_reserved_y0_2, middle_stair_reserved_y1_2_ext)],
            corridor_window_targets=corridor_window_targets_2,
            door_state='closed',
        )
        east_wing_2 = Wing(east_rooms_x, self.start_y + second_floor_offset_y, side='right', num_rooms_per_side=7, corridor_on_lawn_side=False)
        east_corridor_2 = east_wing_2.generate(self.level, lawn2, floor_height=second_floor_floor, ceil_height=second_floor_ceil, story_tag=0, door_state='closed')

        # Stair/portal builders were extracted to `layout/stairs.py`.

        # Portal ids (unique, large values to avoid clashing with sector tags)
        east_portal_ids = (40001, 40002)
        middle_portal_ids = (40003, 40004)
        west_portal_ids = (40005, 40006)
        east_portal_ids_2_3 = (40007, 40008)
        middle_portal_ids_2_3 = (40009, 40010)
        west_portal_ids_2_3 = (40011, 40012)

        # Place stairs near the north end of the corridor (toward the cross-corridor / mess hall).
        # Keep them off the room-door wall as much as possible.
        # Stairs should not overlap bedroom/bathroom door cuts along the corridor wall.
        # The East Wing corridor wall we attach to is a clean outside wall, so we can stay near the north end.
        east_north_attach_pad = 64

        east_attach_y = int(east_corridor.y + east_corridor.height - self.wall_thickness - self.stairs_h - east_north_attach_pad)

        # Middle attach_y values were computed earlier so we could reserve corridor window spans.
        east_attach_y_2 = int(east_corridor_2.y + east_corridor_2.height - self.wall_thickness - self.stairs_h - east_north_attach_pad)

        # Main floor stairwells.
        # Attach to the OUTSIDE wall of each corridor (a clean wall with no room-door cuts
        # and, if present, fewer window cuts), to avoid overlapping openings that can
        # create blocking geometry.
        # - West Wing stairs bump out into the brown-strip gap (east)        => side_dir = +1
        # - East Wing corridor is on the outside east; outside wall is east  => side_dir = +1
        # - Middle Wing stairs bump out into the lawn-side gap (east)        => side_dir = +1

        add_stairwell_to_corridor(
            self.level,
            west_corridor,
            side_dir=1,
            attach_y=west_attach_y,
            set_spawn=False,
            portal_target_corridor=west_corridor_2,
            portal_pair_ids=west_portal_ids,
            spec=self.stairs_spec,
        )

        f2_arrival_west = add_second_floor_portal_entry(
            self.level,
            west_corridor_2,
            side_dir=1,
            attach_y=west_attach_y_2,
            portal_pair_ids=west_portal_ids,
            spec=self.stairs_spec,
        )

        add_stairwell_to_corridor(
            self.level,
            east_corridor,
            side_dir=1,
            attach_y=east_attach_y,
            set_spawn=True,
            portal_target_corridor=east_corridor_2,
            portal_pair_ids=east_portal_ids,
            spec=self.stairs_spec,
        )

        # Off-map portal entry corresponding to the stairwell top.
        f2_arrival = add_second_floor_portal_entry(
            self.level,
            east_corridor_2,
            side_dir=1,
            attach_y=east_attach_y_2,
            portal_pair_ids=east_portal_ids,
            spec=self.stairs_spec,
        )

        # Middle Wing: add the same stairs + portal connection to its off-map 2nd floor.
        add_stairwell_to_corridor(
            self.level,
            middle_corridor,
            side_dir=1,
            attach_y=middle_attach_y,
            set_spawn=False,
            portal_target_corridor=middle_corridor_2,
            portal_pair_ids=middle_portal_ids,
            spec=self.stairs_spec,
        )
        f2_arrival_middle = add_second_floor_portal_entry(
            self.level,
            middle_corridor_2,
            side_dir=1,
            attach_y=middle_attach_y_2,
            portal_pair_ids=middle_portal_ids,
            spec=self.stairs_spec,
        )

        # Fast iteration spawn (optional): set `H9_SPAWN=middle_f2` to start at the
        # Middle-wing F2->F3 landing.
        if str(os.environ.get('H9_SPAWN', '')).lower().strip() in ("middle_f2", "mid_f2"):
            self.level.test_spawn = (
                int(f2_arrival_middle['landing'].x + (self.stairs_spec.stair_w // 2)),
                int(f2_arrival_middle['landing'].y + (self.stairs_spec.step_depth // 2)),
                270,
            )

        # 8. Third Floor (full copy matching 2nd floor semantics)
        third_floor_offset_y = -12000
        third_floor_floor = 2 * self.steps * self.rise
        third_floor_ceil = third_floor_floor + 128

        lawn3 = build_central_lawn(
            self.level,
            x=self.start_x,
            y=self.start_y + third_floor_offset_y,
            width=lawn_width,
            height=lawn_height,
            floor_tex="PYGRASS",
        )
        lawn3.floor_height = 0
        lawn3.ceil_height = max(int(getattr(lawn3, 'ceil_height', 0) or 0), int(third_floor_ceil))

        # West Wing 3rd floor copy + outdoors
        west_attach_y_3, west_stair_reserved_y0_3, west_stair_reserved_y1_3 = compute_stair_attach_and_reserved_span(
            start_y=self.start_y + third_floor_offset_y,
            wing_height=wing_height,
            wall_thickness=self.wall_thickness,
            stairs_h=self.stairs_h,
            hall_h=self.hall_h,
            step_depth=self.step_depth,
            north_attach_pad=west_north_attach_pad,
        )

        brown_west_3 = build_brown_west_half_segments(
            self.level,
            west_x=brown_ground_west_x,
            start_y=self.start_y + third_floor_offset_y,
            height=lawn_height,
            half_w=brown_half_w,
            reserved_y0=west_stair_reserved_y0_3,
            reserved_y1=west_stair_reserved_y1_3,
            floor_tex="RROCK19",
        )
        for _r in (brown_west_3.west_default, brown_west_3.west_south, brown_west_3.west_north):
            if _r is None:
                continue
            _r.floor_height = 0
            _r.ceil_height = max(int(getattr(_r, 'ceil_height', 0) or 0), int(third_floor_ceil))

        west_outside_3 = self.level.add_room(
            Lawn(west_outside_x, self.start_y + third_floor_offset_y, west_outside_width, lawn_height, floor_tex="PYGRASS")
        )
        west_outside_3.floor_height = 0
        west_outside_3.ceil_height = max(int(getattr(west_outside_3, 'ceil_height', 0) or 0), int(third_floor_ceil))

        west_wing_3 = Wing(west_wing_x, self.start_y + third_floor_offset_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)
        west_corridor_3 = west_wing_3.generate(
            self.level,
            brown_west_3.west_default,
            floor_height=third_floor_floor,
            ceil_height=third_floor_ceil,
            story_tag=0,
            exterior_area=west_outside_3,
            add_corridor_windows=True,
            corridor_window_skip_ranges=[(west_stair_reserved_y0_3, west_stair_reserved_y1_3)],
            corridor_window_targets=brown_west_3.corridor_window_targets_west,
            door_state='closed',
        )

        # Middle Wing 3rd floor copy + buffer + brown east half (for bedroom windows)
        middle_attach_y_3, middle_stair_reserved_y0_3, middle_stair_reserved_y1_3 = compute_stair_attach_and_reserved_span(
            start_y=self.start_y + third_floor_offset_y,
            wing_height=wing_height,
            wall_thickness=self.wall_thickness,
            stairs_h=self.stairs_h,
            hall_h=self.hall_h,
            step_depth=self.step_depth,
            north_attach_pad=middle_north_attach_pad,
        )

        buffer_3 = build_middle_lawn_buffer(
            self.level,
            start_y=self.start_y + third_floor_offset_y,
            height=lawn_height,
            wall_thickness=self.wall_thickness,
            middle_wing_x=middle_wing_x,
            lawn=lawn3,
            reserved_y0=middle_stair_reserved_y0_3,
            reserved_y1=middle_stair_reserved_y1_3,
            floor_tex="PYGRASS",
            connect_window_height=int(third_floor_ceil),
            connect_sill_height=0,
            pass_window_textures=True,
        )
        for _r in (buffer_3.south, buffer_3.north):
            if _r is None:
                continue
            _r.floor_height = 0
            _r.ceil_height = max(int(getattr(_r, 'ceil_height', 0) or 0), int(third_floor_ceil))

        brown_ground_east_3 = self.level.add_room(
            Lawn(
                int(brown_ground_east_x),
                int(self.start_y + third_floor_offset_y),
                int(brown_half_w),
                int(lawn_height),
                floor_tex="RROCK19",
            )
        )
        brown_ground_east_3.floor_height = 0
        brown_ground_east_3.ceil_height = max(int(getattr(brown_ground_east_3, 'ceil_height', 0) or 0), int(third_floor_ceil))

        # Connect brown halves at elevated window height for sightlines.
        halves_gap_x_3 = int(brown_ground_west_x) + int(brown_half_w)
        connect_h_3 = int(third_floor_ceil - third_floor_floor)
        for _seg in (brown_west_3.west_south, brown_west_3.west_north):
            if _seg is None:
                continue
            self.level.add_connector(
                Window(
                    halves_gap_x_3,
                    int(_seg.y),
                    int(self.wall_thickness),
                    int(_seg.height),
                    _seg,
                    brown_ground_east_3,
                    sill_height=int(third_floor_floor),
                    window_height=connect_h_3,
                    floor_tex=str(_seg.floor_tex),
                    ceil_tex="F_SKY1",
                )
            )

        middle_wing_3 = Wing(middle_wing_x, self.start_y + third_floor_offset_y, side='left', num_rooms_per_side=7, corridor_on_lawn_side=True)
        middle_corridor_3 = middle_wing_3.generate(
            self.level,
            lawn3,
            floor_height=third_floor_floor,
            ceil_height=third_floor_ceil,
            story_tag=0,
            exterior_area=brown_ground_east_3,
            add_corridor_windows=True,
            corridor_window_skip_ranges=[(middle_stair_reserved_y0_3, middle_stair_reserved_y1_3)],
            corridor_window_targets=buffer_3.corridor_window_targets,
            door_state='closed',
        )

        # East Wing 3rd floor copy
        east_wing_3 = Wing(east_rooms_x, self.start_y + third_floor_offset_y, side='right', num_rooms_per_side=7, corridor_on_lawn_side=False)
        east_corridor_3 = east_wing_3.generate(self.level, lawn3, floor_height=third_floor_floor, ceil_height=third_floor_ceil, story_tag=0, door_state='closed')

        # Extend stairs from F2 arrivals up to F3, then add corresponding portal entries on F3.
        add_stair_extension(
            self.level,
            f2_arrival['landing'],
            portal_pair_ids=east_portal_ids_2_3,
            floor_height=second_floor_floor,
            ceil_height=third_floor_ceil,
            direction="east",
            spec=self.stairs_spec,
        )

        # Middle/West: the F1<->F2 portal line sits on the landing's north edge.
        # Starting an extension directly north of that landing would immediately
        # hit the portal. Starting west/east causes x-sweeping overlaps.
        #
        # Instead, add a small pad off the landing side and run the extension
        # north from that pad.
        pad_w = int(self.stairs_spec.stair_w)
        pad_h = int(self.stairs_spec.step_depth)
        pad_wall = int(self.stairs_spec.wall_thickness)

        def _add_f2_to_f3_pad(arrival: Dict[str, Room]) -> Room:
            landing = arrival['landing']
            pad_x = int(landing.x - pad_wall - pad_w)
            pad_y = int(landing.y)
            pad = self.level.add_room(
                Room(
                    pad_x,
                    pad_y,
                    pad_w,
                    pad_h,
                    floor_tex=landing.floor_tex,
                    wall_tex=landing.wall_tex,
                    ceil_tex=landing.ceil_tex,
                    floor_height=int(getattr(landing, 'floor_height', 0) or 0),
                    ceil_height=int(getattr(landing, 'ceil_height', 0) or 0),
                )
            )

            opening_h = int(max(1, int(getattr(landing, 'ceil_height', 0) or 0) - int(getattr(landing, 'floor_height', 0) or 0)))
            self.level.add_connector(
                Window(
                    int(landing.x - pad_wall),
                    pad_y,
                    pad_wall,
                    pad_h,
                    pad,
                    landing,
                    sill_height=0,
                    window_height=opening_h,
                    floor_tex=landing.floor_tex,
                    ceil_tex=landing.ceil_tex,
                    wall_tex=landing.wall_tex,
                )
            )
            return pad

        middle_pad = _add_f2_to_f3_pad(f2_arrival_middle)
        add_stair_extension(
            self.level,
            middle_pad,
            portal_pair_ids=middle_portal_ids_2_3,
            floor_height=second_floor_floor,
            ceil_height=third_floor_ceil,
            direction="north",
            spec=self.stairs_spec,
        )

        west_pad = _add_f2_to_f3_pad(f2_arrival_west)
        add_stair_extension(
            self.level,
            west_pad,
            portal_pair_ids=west_portal_ids_2_3,
            floor_height=second_floor_floor,
            ceil_height=third_floor_ceil,
            direction="north",
            spec=self.stairs_spec,
        )

        east_attach_y_3 = int(east_corridor_3.y + east_corridor_3.height - self.wall_thickness - self.stairs_h - east_north_attach_pad)
        add_second_floor_portal_entry(
            self.level,
            east_corridor_3,
            side_dir=1,
            attach_y=east_attach_y_3,
            portal_pair_ids=east_portal_ids_2_3,
            spec=self.stairs_spec,
        )
        add_second_floor_portal_entry(
            self.level,
            middle_corridor_3,
            side_dir=1,
            attach_y=middle_attach_y_3,
            portal_pair_ids=middle_portal_ids_2_3,
            spec=self.stairs_spec,
        )
        add_second_floor_portal_entry(
            self.level,
            west_corridor_3,
            side_dir=1,
            attach_y=west_attach_y_3,
            portal_pair_ids=west_portal_ids_2_3,
            spec=self.stairs_spec,
        )
        
        return self.level
