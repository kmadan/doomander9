from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from modules.level import Level
from modules.geometry import Room
from modules.connectors import Window, Portal


@dataclass(frozen=True)
class StairsSpec:
    """Parameters controlling the stairwell/portal geometry.

    Defaults are chosen to match the existing hostel layout.
    """

    wall_thickness: int = 16
    stair_w: int = 64
    step_depth: int = 64
    steps: int = 7
    rise: int = 20

    hall_w: int = 64

    corridor_door_h: int = 96
    corridor_door_y_offset: int = 32

    # For main-floor stairwell volumes we keep a tall ceiling so the ascent is
    # never blocked by low ceilings.
    main_stairs_ceil_height: int = 320

    @property
    def stairs_h(self) -> int:
        return int(self.steps * self.step_depth)

    @property
    def hall_h(self) -> int:
        return self.stairs_h

    @property
    def reserved_span_h(self) -> int:
        # Matches the skip-range math used in hostel_generator.py:
        # hall + gap + landing + gap + threshold
        return int(self.hall_h + self.wall_thickness + self.step_depth + self.wall_thickness + self.step_depth)


def add_stairwell_to_corridor(
    level: Level,
    src_corridor: Room,
    side_dir: int,
    *,
    attach_y: int,
    set_spawn: bool,
    portal_target_corridor: Optional[Room] = None,
    portal_pair_ids: Optional[Tuple[int, int]] = None,
    spec: StairsSpec = StairsSpec(),
) -> Dict[str, Room]:
    """Build main-floor stairs (ascending) and optional portal threshold."""

    hall_h = spec.hall_h

    if side_dir > 0:
        hall_x = src_corridor.x + src_corridor.width + spec.wall_thickness
    else:
        hall_x = src_corridor.x - spec.wall_thickness - spec.hall_w

    hall_y = int(attach_y)
    hall = level.add_room(
        Room(
            hall_x,
            hall_y,
            spec.hall_w,
            hall_h,
            floor_tex=src_corridor.floor_tex,
            wall_tex=src_corridor.wall_tex,
            ceil_tex=src_corridor.ceil_tex,
            floor_height=src_corridor.floor_height,
            ceil_height=spec.main_stairs_ceil_height,
        )
    )

    last_step_room: Optional[Room] = None
    for i in range(spec.steps):
        step_floor = src_corridor.floor_height + (i + 1) * spec.rise
        step_y = hall_y + i * spec.step_depth
        if side_dir > 0:
            step_x = hall_x + spec.hall_w + spec.wall_thickness
            gap_x = hall_x + spec.hall_w
        else:
            step_x = hall_x - spec.wall_thickness - spec.stair_w
            gap_x = hall_x - spec.wall_thickness

        step_room = level.add_room(
            Room(
                step_x,
                step_y,
                spec.stair_w,
                spec.step_depth,
                floor_tex=src_corridor.floor_tex,
                wall_tex=src_corridor.wall_tex,
                ceil_tex=src_corridor.ceil_tex,
                floor_height=step_floor,
                ceil_height=spec.main_stairs_ceil_height,
            )
        )

        if i == spec.steps - 1:
            last_step_room = step_room

        level.add_connector(
            Window(
                gap_x,
                step_y,
                spec.wall_thickness,
                spec.step_depth,
                hall,
                step_room,
                sill_height=0,
                window_height=spec.main_stairs_ceil_height,
                floor_tex=src_corridor.floor_tex,
                ceil_tex=src_corridor.ceil_tex,
                wall_tex=src_corridor.wall_tex,
            )
        )

    # Corridor -> hall opening.
    corridor_door_y = hall_y + spec.corridor_door_y_offset
    level.add_connector(
        Window(
            (src_corridor.x + src_corridor.width) if side_dir > 0 else (src_corridor.x - spec.wall_thickness),
            corridor_door_y,
            spec.wall_thickness,
            spec.corridor_door_h,
            src_corridor,
            hall,
            sill_height=0,
            window_height=spec.main_stairs_ceil_height,
            floor_tex=src_corridor.floor_tex,
            ceil_tex=src_corridor.ceil_tex,
            wall_tex=src_corridor.wall_tex,
        )
    )

    landing_y = hall_y + hall_h + spec.wall_thickness
    landing_x = (hall_x + spec.hall_w + spec.wall_thickness) if side_dir > 0 else (hall_x - spec.wall_thickness - spec.stair_w)
    landing = level.add_room(
        Room(
            landing_x,
            landing_y,
            spec.stair_w,
            spec.step_depth,
            floor_tex=src_corridor.floor_tex,
            wall_tex=src_corridor.wall_tex,
            ceil_tex=src_corridor.ceil_tex,
            floor_height=src_corridor.floor_height + spec.steps * spec.rise,
            ceil_height=spec.main_stairs_ceil_height,
        )
    )

    if last_step_room is not None:
        level.add_connector(
            Window(
                landing_x,
                hall_y + hall_h,
                spec.stair_w,
                spec.wall_thickness,
                last_step_room,
                landing,
                sill_height=0,
                window_height=spec.main_stairs_ceil_height,
                floor_tex=src_corridor.floor_tex,
                ceil_tex=src_corridor.ceil_tex,
                wall_tex=src_corridor.wall_tex,
            )
        )

    portal_y = landing_y + spec.step_depth
    threshold_y = portal_y + spec.wall_thickness
    threshold = level.add_room(
        Room(
            landing_x,
            threshold_y,
            spec.stair_w,
            spec.step_depth,
            floor_tex=src_corridor.floor_tex,
            wall_tex=src_corridor.wall_tex,
            ceil_tex=src_corridor.ceil_tex,
            floor_height=src_corridor.floor_height + spec.steps * spec.rise,
            ceil_height=spec.main_stairs_ceil_height,
        )
    )

    if portal_target_corridor is not None and portal_pair_ids is not None:
        src_line_id, dst_line_id = portal_pair_ids
        level.add_connector(
            Portal(
                landing_x,
                landing_y + spec.step_depth,
                spec.stair_w,
                spec.wall_thickness,
                landing,
                threshold,
                source_line_id=src_line_id,
                target_line_id=dst_line_id,
                type=1,
                planeanchor=1,
                floor_tex=src_corridor.floor_tex,
                ceil_tex=src_corridor.ceil_tex,
                wall_tex=src_corridor.wall_tex,
            )
        )

    if set_spawn and not hasattr(level, "test_spawn"):
        spawn_x = hall_x + (spec.hall_w // 2)
        spawn_y = hall_y + spec.corridor_door_y_offset
        spawn_angle = 0 if side_dir > 0 else 180
        level.test_spawn = (int(spawn_x), int(spawn_y), int(spawn_angle))

    return {"hall": hall, "landing": landing, "threshold": threshold}


def add_second_floor_portal_entry(
    level: Level,
    dst_corridor: Room,
    side_dir: int,
    *,
    attach_y: int,
    portal_pair_ids: Tuple[int, int],
    spec: StairsSpec = StairsSpec(),
) -> Dict[str, Room]:
    """Build the off-map portal arrival/departure structure on upper floors."""

    hall_h = spec.hall_h

    if side_dir > 0:
        hall_x = dst_corridor.x + dst_corridor.width + spec.wall_thickness
    else:
        hall_x = dst_corridor.x - spec.wall_thickness - spec.hall_w

    hall_y = int(attach_y)
    hall = level.add_room(
        Room(
            hall_x,
            hall_y,
            spec.hall_w,
            hall_h,
            floor_tex=dst_corridor.floor_tex,
            wall_tex=dst_corridor.wall_tex,
            ceil_tex=dst_corridor.ceil_tex,
            floor_height=dst_corridor.floor_height,
            ceil_height=dst_corridor.ceil_height,
        )
    )

    corridor_door_y = hall_y + spec.corridor_door_y_offset
    level.add_connector(
        Window(
            (dst_corridor.x + dst_corridor.width) if side_dir > 0 else (dst_corridor.x - spec.wall_thickness),
            corridor_door_y,
            spec.wall_thickness,
            spec.corridor_door_h,
            dst_corridor,
            hall,
            sill_height=0,
            window_height=dst_corridor.ceil_height - dst_corridor.floor_height,
            floor_tex=dst_corridor.floor_tex,
            ceil_tex=dst_corridor.ceil_tex,
            wall_tex=dst_corridor.wall_tex,
        )
    )

    last_step_room: Optional[Room] = None
    for i in range(spec.steps):
        step_y = hall_y + i * spec.step_depth
        if side_dir > 0:
            step_x = hall_x + spec.hall_w + spec.wall_thickness
            gap_x = hall_x + spec.hall_w
        else:
            step_x = hall_x - spec.wall_thickness - spec.stair_w
            gap_x = hall_x - spec.wall_thickness

        step_room = level.add_room(
            Room(
                step_x,
                step_y,
                spec.stair_w,
                spec.step_depth,
                floor_tex=dst_corridor.floor_tex,
                wall_tex=dst_corridor.wall_tex,
                ceil_tex=dst_corridor.ceil_tex,
                floor_height=dst_corridor.floor_height,
                ceil_height=dst_corridor.ceil_height,
            )
        )

        if i == spec.steps - 1:
            last_step_room = step_room

        level.add_connector(
            Window(
                gap_x,
                step_y,
                spec.wall_thickness,
                spec.step_depth,
                hall,
                step_room,
                sill_height=0,
                window_height=dst_corridor.ceil_height - dst_corridor.floor_height,
                floor_tex=dst_corridor.floor_tex,
                ceil_tex=dst_corridor.ceil_tex,
                wall_tex=dst_corridor.wall_tex,
            )
        )

    landing_y = hall_y + hall_h + spec.wall_thickness
    landing_x = (hall_x + spec.hall_w + spec.wall_thickness) if side_dir > 0 else (hall_x - spec.wall_thickness - spec.stair_w)
    landing = level.add_room(
        Room(
            landing_x,
            landing_y,
            spec.stair_w,
            spec.step_depth,
            floor_tex=dst_corridor.floor_tex,
            wall_tex=dst_corridor.wall_tex,
            ceil_tex=dst_corridor.ceil_tex,
            floor_height=dst_corridor.floor_height,
            ceil_height=dst_corridor.ceil_height,
        )
    )

    if last_step_room is not None:
        level.add_connector(
            Window(
                landing_x,
                hall_y + hall_h,
                spec.stair_w,
                spec.wall_thickness,
                last_step_room,
                landing,
                sill_height=0,
                window_height=dst_corridor.ceil_height - dst_corridor.floor_height,
                floor_tex=dst_corridor.floor_tex,
                ceil_tex=dst_corridor.ceil_tex,
                wall_tex=dst_corridor.wall_tex,
            )
        )

    portal_y = landing_y + spec.step_depth
    threshold_y = portal_y + spec.wall_thickness
    threshold = level.add_room(
        Room(
            landing_x,
            threshold_y,
            spec.stair_w,
            spec.step_depth,
            floor_tex=dst_corridor.floor_tex,
            wall_tex=dst_corridor.wall_tex,
            ceil_tex=dst_corridor.ceil_tex,
            floor_height=dst_corridor.floor_height,
            ceil_height=dst_corridor.ceil_height,
        )
    )

    src_line_id, dst_line_id = portal_pair_ids
    # Reverse portal direction compared to main-floor stairwell portal.
    level.add_connector(
        Portal(
            landing_x,
            portal_y,
            spec.stair_w,
            spec.wall_thickness,
            landing,
            threshold,
            source_line_id=dst_line_id,
            target_line_id=src_line_id,
            type=1,
            planeanchor=1,
            floor_tex=dst_corridor.floor_tex,
            ceil_tex=dst_corridor.ceil_tex,
            wall_tex=dst_corridor.wall_tex,
        )
    )

    return {"hall": hall, "landing": landing, "threshold": threshold}


def add_stair_extension(
    level: Level,
    start_room: Room,
    *,
    portal_pair_ids: Tuple[int, int],
    floor_height: int,
    ceil_height: int,
    spec: StairsSpec = StairsSpec(),
) -> Room:
    """Build an additional flight of stairs starting north of `start_room`.

    Returns the created threshold room.
    """

    start_y = start_room.y + start_room.height + spec.wall_thickness
    start_x = start_room.x

    current_y = int(start_y)
    prev_room: Room = start_room

    for i in range(spec.steps):
        step_floor = int(floor_height + (i + 1) * spec.rise)

        step_y = current_y + spec.wall_thickness
        step_room = level.add_room(
            Room(
                start_x,
                step_y,
                spec.stair_w,
                spec.step_depth,
                floor_tex=start_room.floor_tex,
                wall_tex=start_room.wall_tex,
                ceil_tex=start_room.ceil_tex,
                floor_height=step_floor,
                ceil_height=ceil_height,
            )
        )

        level.add_connector(
            Window(
                start_x,
                current_y,
                spec.stair_w,
                spec.wall_thickness,
                prev_room,
                step_room,
                sill_height=0,
                window_height=ceil_height,
                floor_tex=start_room.floor_tex,
                ceil_tex=start_room.ceil_tex,
                wall_tex=start_room.wall_tex,
            )
        )

        prev_room = step_room
        current_y = int(step_y + spec.step_depth)

    landing_y = current_y + spec.wall_thickness
    landing = level.add_room(
        Room(
            start_x,
            landing_y,
            spec.stair_w,
            spec.step_depth,
            floor_tex=start_room.floor_tex,
            wall_tex=start_room.wall_tex,
            ceil_tex=start_room.ceil_tex,
            floor_height=int(floor_height + spec.steps * spec.rise),
            ceil_height=ceil_height,
        )
    )

    level.add_connector(
        Window(
            start_x,
            current_y,
            spec.stair_w,
            spec.wall_thickness,
            prev_room,
            landing,
            sill_height=0,
            window_height=ceil_height,
            floor_tex=start_room.floor_tex,
            ceil_tex=start_room.ceil_tex,
            wall_tex=start_room.wall_tex,
        )
    )

    threshold_y = landing_y + spec.step_depth + spec.wall_thickness
    threshold = level.add_room(
        Room(
            start_x,
            threshold_y,
            spec.stair_w,
            spec.step_depth,
            floor_tex=start_room.floor_tex,
            wall_tex=start_room.wall_tex,
            ceil_tex=start_room.ceil_tex,
            floor_height=int(floor_height + spec.steps * spec.rise),
            ceil_height=ceil_height,
        )
    )

    level.add_connector(
        Portal(
            start_x,
            landing_y + spec.step_depth,
            spec.stair_w,
            spec.wall_thickness,
            landing,
            threshold,
            source_line_id=int(portal_pair_ids[0]),
            target_line_id=int(portal_pair_ids[1]),
            type=1,
            planeanchor=1,
            floor_tex=start_room.floor_tex,
            ceil_tex=start_room.ceil_tex,
            wall_tex=start_room.wall_tex,
        )
    )

    return threshold
