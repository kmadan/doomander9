from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from modules.level import Level
from modules.geometry import Corridor, Lawn, Room
from modules.connectors import Door, Switch, Window


# Keep these aligned with `modules/wing.py` defaults.
DEFAULT_ROOM_W: int = 256
DEFAULT_CORRIDOR_W: int = 128


@dataclass(frozen=True)
class BrownStripResult:
    east: Room
    west_default: Room
    west_south: Optional[Room]
    west_north: Optional[Room]

    brown_width: int
    half_w: int
    gap_w: int

    west_x: int
    east_x: int
    halves_gap_x: int

    corridor_window_targets_west: List[Tuple[int, int, Room]]


@dataclass(frozen=True)
class BufferStripResult:
    south: Optional[Room]
    north: Optional[Room]
    corridor_window_targets: List[Tuple[int, int, Room]]


@dataclass(frozen=True)
class GateAndOutsideResult:
    outside: Room


@dataclass(frozen=True)
class BrownWestHalfResult:
    west_default: Room
    west_south: Optional[Room]
    west_north: Optional[Room]
    corridor_window_targets_west: List[Tuple[int, int, Room]]


def build_brown_west_half_segments(
    level: Level,
    *,
    west_x: int,
    start_y: int,
    height: int,
    half_w: int,
    reserved_y0: int,
    reserved_y1: int,
    floor_tex: str = "RROCK19",
) -> BrownWestHalfResult:
    """Build only the west-half segments of the brown strip (south/north around a reserved span).

    This matches the off-map 2nd-floor behavior, where we only need outdoor space
    for West Wing corridor lookouts and do not create/bridge the east half.
    """

    west_south_h = int(reserved_y0 - int(start_y))
    west_south: Optional[Room] = None
    if west_south_h > 0:
        west_south = level.add_room(Lawn(int(west_x), int(start_y), int(half_w), int(west_south_h), floor_tex=str(floor_tex)))

    west_north_y = int(reserved_y1)
    west_north_h = int((int(start_y) + int(height)) - west_north_y)
    west_north: Optional[Room] = None
    if west_north_h > 0:
        west_north = level.add_room(Lawn(int(west_x), int(west_north_y), int(half_w), int(west_north_h), floor_tex=str(floor_tex)))

    west_default = west_south or west_north
    if west_default is None:
        raise RuntimeError("West half of brown strip is empty")

    targets_west: List[Tuple[int, int, Room]] = []
    if west_south is not None:
        targets_west.append((west_south.y, west_south.y + west_south.height, west_south))
    if west_north is not None:
        targets_west.append((west_north.y, west_north.y + west_north.height, west_north))

    return BrownWestHalfResult(
        west_default=west_default,
        west_south=west_south,
        west_north=west_north,
        corridor_window_targets_west=targets_west,
    )


def compute_stair_attach_and_reserved_span(
    *,
    start_y: int,
    wing_height: int,
    wall_thickness: int,
    stairs_h: int,
    hall_h: int,
    step_depth: int,
    north_attach_pad: int,
) -> Tuple[int, int, int]:
    """Compute (attach_y, reserved_y0, reserved_y1) for corridor window skip-ranges."""

    attach_y = int(start_y + wing_height - wall_thickness - stairs_h - int(north_attach_pad))
    reserved_y0 = int(attach_y)
    reserved_y1 = int(attach_y + hall_h + wall_thickness + step_depth + wall_thickness + step_depth)
    return attach_y, reserved_y0, reserved_y1


def build_central_lawn(level: Level, *, x: int, y: int, width: int, height: int, floor_tex: str = "PYGRASS") -> Room:
    return level.add_room(Lawn(int(x), int(y), int(width), int(height), floor_tex=str(floor_tex)))


def build_brown_strip(
    level: Level,
    *,
    start_y: int,
    height: int,
    wall_thickness: int,
    middle_wing_x: int,
    brown_width: int,
    west_stair_reserved_y0: int,
    west_stair_reserved_y1: int,
    floor_tex: str = "RROCK19",
) -> BrownStripResult:
    """Build the traversable brown strip between Middle and West wings.

    Matches the original behavior:
    - east half: continuous full-height strip
    - west half: split into south/north segments around the west stairwell span
    - halves are connected via Window connectors through a wall-thickness gap
    """

    half_w = (int(brown_width) - int(wall_thickness)) // 2
    gap_w = int(wall_thickness)

    brown_ground_x = int(middle_wing_x) - DEFAULT_ROOM_W - int(wall_thickness) - int(brown_width) - int(wall_thickness)
    west_x = brown_ground_x
    east_x = brown_ground_x + half_w + gap_w
    halves_gap_x = west_x + half_w

    east = level.add_room(Lawn(east_x, int(start_y), half_w, int(height), floor_tex=str(floor_tex)))

    west_half = build_brown_west_half_segments(
        level,
        west_x=west_x,
        start_y=int(start_y),
        height=int(height),
        half_w=half_w,
        reserved_y0=int(west_stair_reserved_y0),
        reserved_y1=int(west_stair_reserved_y1),
        floor_tex=str(floor_tex),
    )
    west_south = west_half.west_south
    west_north = west_half.west_north
    west_default = west_half.west_default

    # Connect halves so the strip is traversable.
    if west_south is not None:
        level.add_connector(
            Window(
                halves_gap_x,
                west_south.y,
                int(wall_thickness),
                west_south.height,
                west_south,
                east,
                sill_height=0,
                window_height=256,
                floor_tex=str(floor_tex),
                ceil_tex="F_SKY1",
            )
        )
    if west_north is not None:
        level.add_connector(
            Window(
                halves_gap_x,
                west_north.y,
                int(wall_thickness),
                west_north.height,
                west_north,
                east,
                sill_height=0,
                window_height=256,
                floor_tex=str(floor_tex),
                ceil_tex="F_SKY1",
            )
        )

    targets_west = list(west_half.corridor_window_targets_west)

    return BrownStripResult(
        east=east,
        west_default=west_default,
        west_south=west_south,
        west_north=west_north,
        brown_width=int(brown_width),
        half_w=half_w,
        gap_w=gap_w,
        west_x=west_x,
        east_x=east_x,
        halves_gap_x=halves_gap_x,
        corridor_window_targets_west=targets_west,
    )


def build_middle_lawn_buffer(
    level: Level,
    *,
    start_y: int,
    height: int,
    wall_thickness: int,
    middle_wing_x: int,
    lawn: Room,
    reserved_y0: int,
    reserved_y1: int,
    floor_tex: str = "PYGRASS",
    connect_window_height: int = 256,
    connect_sill_height: int = 0,
    connect_floor_tex: str = "PYGRASS",
    connect_ceil_tex: str = "F_SKY1",
    pass_window_textures: bool = True,
) -> BufferStripResult:
    """Build the thin outdoor buffer strip between the Middle Wing corridor and lawn.

    This exists to guarantee outdoor adjacency for corridor lookouts and to reserve
    space for the stair bump-out (by splitting around the reserved span).
    """

    buffer_x = int(middle_wing_x) + DEFAULT_CORRIDOR_W + int(wall_thickness)
    buffer_right = int(lawn.x) - int(wall_thickness)
    buffer_w = int(buffer_right - buffer_x)
    if buffer_w <= 0:
        raise RuntimeError("Middle Wing lawn buffer has non-positive width")

    south_h = int(reserved_y0 - int(start_y))
    south: Optional[Room] = None
    if south_h > 0:
        south = level.add_room(Lawn(buffer_x, int(start_y), buffer_w, south_h, floor_tex=str(floor_tex)))
        if pass_window_textures:
            level.add_connector(
                Window(
                    buffer_right,
                    int(start_y),
                    int(wall_thickness),
                    south_h,
                    south,
                    lawn,
                    sill_height=int(connect_sill_height),
                    window_height=int(connect_window_height),
                    floor_tex=str(connect_floor_tex),
                    ceil_tex=str(connect_ceil_tex),
                )
            )
        else:
            # Preserve connector defaults (no explicit floor/ceil textures).
            level.add_connector(
                Window(
                    buffer_right,
                    int(start_y),
                    int(wall_thickness),
                    south_h,
                    south,
                    lawn,
                    sill_height=int(connect_sill_height),
                    window_height=int(connect_window_height),
                )
            )

    north_y = int(reserved_y1)
    north_h = int((int(start_y) + int(height)) - north_y)
    north: Optional[Room] = None
    if north_h > 0:
        north = level.add_room(Lawn(buffer_x, north_y, buffer_w, north_h, floor_tex=str(floor_tex)))
        if pass_window_textures:
            level.add_connector(
                Window(
                    buffer_right,
                    north_y,
                    int(wall_thickness),
                    north_h,
                    north,
                    lawn,
                    sill_height=int(connect_sill_height),
                    window_height=int(connect_window_height),
                    floor_tex=str(connect_floor_tex),
                    ceil_tex=str(connect_ceil_tex),
                )
            )
        else:
            # Preserve connector defaults (no explicit floor/ceil textures).
            level.add_connector(
                Window(
                    buffer_right,
                    north_y,
                    int(wall_thickness),
                    north_h,
                    north,
                    lawn,
                    sill_height=int(connect_sill_height),
                    window_height=int(connect_window_height),
                )
            )

    targets: List[Tuple[int, int, Room]] = []
    if south is not None:
        targets.append((south.y, south.y + south.height, south))
    if north is not None:
        targets.append((north.y, north.y + north.height, north))

    return BufferStripResult(south=south, north=north, corridor_window_targets=targets)


def build_cross_corridor_and_connections(
    level: Level,
    *,
    west_corridor: Room,
    middle_corridor: Room,
    east_corridor: Room,
    lawn: Room,
    lawn_top_y: int,
    wall_thickness: int,
    brown_ground_east: Room,
    brown_half_w: int,
    brown_ground_east_x: int,
    cross_height: int = 128,
) -> Room:
    """Build the north cross corridor and connect it to wings + outdoors."""

    cross_y = int(lawn_top_y) + int(wall_thickness)
    cross_x = int(west_corridor.x)
    cross_width = int((east_corridor.x + DEFAULT_CORRIDOR_W) - west_corridor.x)

    cross = level.add_room(Corridor(cross_x, cross_y, cross_width, int(cross_height)))

    level.add_connector(Window(west_corridor.x, int(lawn_top_y), DEFAULT_CORRIDOR_W, int(wall_thickness), west_corridor, cross, sill_height=0, window_height=128))
    level.add_connector(Window(middle_corridor.x, int(lawn_top_y), DEFAULT_CORRIDOR_W, int(wall_thickness), middle_corridor, cross, sill_height=0, window_height=128))
    level.add_connector(Window(east_corridor.x, int(lawn_top_y), DEFAULT_CORRIDOR_W, int(wall_thickness), east_corridor, cross, sill_height=0, window_height=128))

    lawn_conn_width = 256
    lawn_conn_x = int(lawn.x) + (int(lawn.width) // 2) - (lawn_conn_width // 2)
    level.add_connector(Window(lawn_conn_x, int(lawn_top_y), lawn_conn_width, int(wall_thickness), lawn, cross, sill_height=0, window_height=128))

    level.add_connector(
        Window(
            int(brown_ground_east_x),
            int(lawn_top_y),
            int(brown_half_w),
            int(wall_thickness),
            brown_ground_east,
            cross,
            sill_height=0,
            window_height=128,
        )
    )

    return cross


def build_mess_hall_with_door_and_switch(
    level: Level,
    *,
    start_x: int,
    cross_corridor: Room,
    lawn_width: int,
    wall_thickness: int,
    cross_y: int,
    cross_height: int,
    mess_hall_height: int = 512,
) -> Room:
    """Build the mess hall north of the cross corridor, plus its door + switch."""

    cross_top_y = int(cross_y) + int(cross_height)
    mess_hall_y = cross_top_y + int(wall_thickness)
    mess_hall = level.add_room(Room(int(start_x), mess_hall_y, int(lawn_width), int(mess_hall_height), floor_tex="FLOOR0_1", wall_tex="STONE2"))

    mh_tag = level.get_new_tag()
    door_width = 128
    door_x = int(start_x) + (int(lawn_width) // 2) - (door_width // 2)
    level.add_connector(Door(door_x, cross_top_y, door_width, int(wall_thickness), cross_corridor, mess_hall, state="open", tag=mh_tag, linedef_action=0))

    switch_x = door_x - 64
    switch_y = cross_top_y
    level.add_connector(Switch(switch_x, switch_y, action=42, tag=mh_tag, room=cross_corridor))

    return mess_hall


def build_south_gates_and_outside(
    level: Level,
    *,
    start_x: int,
    start_y: int,
    lawn_width: int,
    wall_thickness: int,
    lawn: Room,
    outside_height: int = 256,
) -> GateAndOutsideResult:
    """Build the outside campus sector + 2 gates + switches + sign alcove."""

    outside_y = int(start_y) - int(outside_height) - int(wall_thickness)
    outside = level.add_room(Lawn(int(start_x), outside_y, int(lawn_width), int(outside_height), floor_tex="PYGRASS"))

    gate1_tag = level.get_new_tag()
    gate_width = 128
    gate1_x = int(start_x) + 64
    level.add_connector(
        Door(
            gate1_x,
            int(start_y) - int(wall_thickness),
            gate_width,
            int(wall_thickness),
            outside,
            lawn,
            texture="BIGDOOR2",
            state="open",
            tag=gate1_tag,
            linedef_action=0,
        )
    )

    sign_x = gate1_x + gate_width
    sign_width = 128
    level.add_connector(
        Window(
            sign_x,
            int(start_y) - 8,
            sign_width,
            8,
            lawn,
            None,
            sill_height=0,
            window_height=128,
            wall_tex="PLUTOSGN",
            floor_tex="PYGRASS",
            ceil_tex="F_SKY1",
        )
    )

    switch1_x = gate1_x - 32
    switch1_y = int(start_y) - int(wall_thickness)
    level.add_connector(Switch(switch1_x, switch1_y, action=42, tag=gate1_tag, room=outside, room2=lawn))

    gate2_tag = level.get_new_tag()
    gate2_x = int(start_x) + int(lawn_width) - 64 - gate_width
    level.add_connector(
        Door(
            gate2_x,
            int(start_y) - int(wall_thickness),
            gate_width,
            int(wall_thickness),
            outside,
            lawn,
            texture="BIGDOOR2",
            state="open",
            tag=gate2_tag,
            linedef_action=0,
        )
    )

    switch2_x = gate2_x + gate_width + 16
    switch2_y = int(start_y) - int(wall_thickness)
    level.add_connector(Switch(switch2_x, switch2_y, action=42, tag=gate2_tag, room=outside, room2=lawn))

    return GateAndOutsideResult(outside=outside)
