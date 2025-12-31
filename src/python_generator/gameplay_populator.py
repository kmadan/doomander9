from __future__ import annotations

# pyright: reportMissingImports=false
# pyright: reportUnknownVariableType=false

import random
import os
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Optional, cast

from builder import WadBuilder
from modules.level import Level
from modules.geometry import Corridor, Lawn, Room
from modules.connectors import Door, ExitLine

# Make the vendored `omgifol` library importable (mirrors modules/furniture.py).
try:
    from omg.mapedit import Thing  # type: ignore
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    omgifol_path = os.path.abspath(os.path.join(current_dir, "..", "..", "tools", "omgifol"))
    if omgifol_path not in sys.path:
        sys.path.append(omgifol_path)
    from omg.mapedit import Thing  # type: ignore


@dataclass(frozen=True)
class GameplayConfig:
    seed: int = 0x4839_4750  # "H9GP"


def _room_center(r: Room) -> tuple[int, int]:
    return int(r.x + r.width // 2), int(r.y + r.height // 2)


def _clamp_point_in_room(r: Room, x: int, y: int, pad: int = 48) -> tuple[int, int]:
    x0 = int(r.x) + int(pad)
    y0 = int(r.y) + int(pad)
    x1 = int(r.x + r.width) - int(pad)
    y1 = int(r.y + r.height) - int(pad)
    return int(max(x0, min(x, x1))), int(max(y0, min(y, y1)))


def _add_thing(builder: WadBuilder, *, type_id: int, x: int, y: int, angle: int = 0, flags: int = 7) -> None:
    th: Any = Thing()
    th.x = int(x)
    th.y = int(y)
    th.angle = int(angle)
    th.type = int(type_id)
    th.flags = int(flags)
    editor: Any = getattr(builder, 'editor')
    editor.things.append(th)


def _find_room_containing_point(level: Level, x: int, y: int) -> Room | None:
    for r in _iter_rooms(level):
        if int(getattr(r, 'floor_height', 0) or 0) != 0:
            continue
        if int(r.x) <= int(x) <= int(r.x + r.width) and int(r.y) <= int(y) <= int(r.y + r.height):
            return r
    return None


def _nearest_main_room(level: Level, x: int, y: int) -> Room | None:
    main_rooms: list[Room] = [
        r for r in _iter_rooms(level)
        if int(getattr(r, 'floor_height', 0) or 0) == 0 and int(getattr(r, 'y', 0)) >= 0
    ]
    if not main_rooms:
        return None

    def _d2(r: Room) -> int:
        cx, cy = _room_center(r)
        dx = cx - int(x)
        dy = cy - int(y)
        return dx * dx + dy * dy

    return min(main_rooms, key=_d2)


def _iter_rooms(level: Level) -> Iterable[Room]:
    for r in getattr(level, "rooms", []) or []:
        if isinstance(r, Room):
            yield r


def _iter_corridors(level: Level) -> Iterable[Room]:
    for r in _iter_rooms(level):
        # Wing corridors are Corridor, but some other hallways are plain Room.
        if isinstance(r, Corridor):
            yield r
        elif type(r).__name__ == "Room" and int(getattr(r, "width", 0)) == 128:
            # Heuristic: connector corridors (cross connectors) often use DEFAULT_CORRIDOR_W.
            yield r


def populate(level: Level, builder: WadBuilder, *, config: GameplayConfig | None = None) -> None:
    """Inject Things and gameplay hooks into the generated map.

    Call this *before* `level.build(builder)` so it can:
    - mark certain Door connectors as secret (affects linedef flags during build)
    - add any gameplay connectors (e.g., an exit line trigger)
    """

    cfg = config or GameplayConfig()
    rng = random.Random(int(cfg.seed))

    # --- Player start: trust generator's suggested spawn (main gate campus road) ---
    spawn_raw = getattr(level, "test_spawn", None)
    spawn = cast(Optional[tuple[int, int, int]], spawn_raw) if spawn_raw is not None else None
    if spawn and len(spawn) >= 2:
        sx = int(spawn[0])
        sy = int(spawn[1])
        sa = int(spawn[2]) if len(spawn) >= 3 else 90
        # Ensure the player start exists even if main_hostel.py changes.
        _add_thing(builder, type_id=1, x=sx, y=sy, angle=sa)

        # Hard guarantee: spawn at least one visible enemy + one pickup right by the start.
        # This protects against any future layout changes making the initial skirmish land in
        # an unexpected room/area.
        _add_thing(builder, type_id=3001, x=sx + 192, y=sy, angle=180)   # Imp
        _add_thing(builder, type_id=2011, x=sx + 96, y=sy + 64, angle=0) # Stimpack
    else:
        # Fallback: a safe spot in the lawn.
        _add_thing(builder, type_id=1, x=256, y=64, angle=0)
        _add_thing(builder, type_id=3001, x=448, y=64, angle=180)
        _add_thing(builder, type_id=2011, x=320, y=128, angle=0)

    # --- Make enemies immediately visible ---
    # Add a small guaranteed skirmish near the start so you see monsters quickly.
    if spawn and len(spawn) >= 2:
        sx = int(spawn[0])
        sy = int(spawn[1])
        start_room = _find_room_containing_point(level, sx, sy) or _nearest_main_room(level, sx, sy)
        if start_room is not None:
            # 2 imps + 2 zombiemen, spread in the start room.
            cx, cy = _room_center(start_room)
            spots = [
                (cx - 128, cy),
                (cx + 128, cy),
                (cx, cy - 128),
                (cx, cy + 128),
            ]
            for idx, (px, py) in enumerate(spots):
                x, y = _clamp_point_in_room(start_room, int(px), int(py), pad=96)
                mon = 3001 if idx < 2 else 3004  # Imp, Zombieman
                _add_thing(builder, type_id=mon, x=x, y=y, angle=rng.choice((0, 90, 180, 270)))

    # Outdoors: place imps in lawns so you definitely see them.
    lawns: list[Lawn] = [r for r in _iter_rooms(level) if isinstance(r, Lawn) and int(getattr(r, 'y', 0)) >= 0]
    for lawn in lawns:
        lw = int(getattr(lawn, 'width', 0) or 0)
        lh = int(getattr(lawn, 'height', 0) or 0)
        if lw < 256 or lh < 256:
            # Skip tiny lawn strips (often used as buffers) to avoid bad placement.
            continue

        # Light scatter across the lawn; keep away from walls.
        pad = min(192, max(96, min(lw, lh) // 6))
        min_x = int(lawn.x) + pad
        max_x = int(lawn.x + lawn.width) - pad
        min_y = int(lawn.y) + pad
        max_y = int(lawn.y + lawn.height) - pad
        if min_x >= max_x or min_y >= max_y:
            continue

        count = 10 if (lw * lh) >= (1400 * 1400) else 6
        for _ in range(count):
            x = int(rng.randint(min_x, max_x))
            y = int(rng.randint(min_y, max_y))
            x, y = _clamp_point_in_room(lawn, x, y, pad=pad)
            _add_thing(builder, type_id=3001, x=x, y=y, angle=rng.choice((0, 90, 180, 270)))

    # --- Identify key spaces ---
    # Mess hall is a large STONE2 room north of the cross corridor.
    mess_hall: Optional[Room] = None
    for r in _iter_rooms(level):
        if type(r).__name__ != "Room":
            continue
        if str(getattr(r, "wall_tex", "")).upper() != "STONE2":
            continue
        if int(getattr(r, "height", 0)) >= 384 and int(getattr(r, "width", 0)) >= 768:
            mess_hall = r
            break

    # Bedrooms are close-quarters rooms.
    bedrooms: list[Room] = [r for r in _iter_rooms(level) if type(r).__name__ == "Bedroom"]

    # Main-map rooms only (ignore off-map portal floors for "dungeon crawl" distance computations).
    main_rooms: list[Room] = [
        r for r in _iter_rooms(level)
        if int(getattr(r, "floor_height", 0) or 0) == 0 and int(getattr(r, "y", 0)) >= 0
    ]

    # Choose a "back gate" goal point as the farthest main-map room from spawn.
    goal_room: Optional[Room] = None
    if main_rooms and spawn and len(spawn) >= 2:
        sx = int(spawn[0])
        sy = int(spawn[1])

        def _d2(r: Room) -> int:
            cx, cy = _room_center(r)
            dx = cx - sx
            dy = cy - sy
            return dx * dx + dy * dy

        goal_room = max(main_rooms, key=_d2)

    # --- Weapons (progression) ---
    # Doom2 pickup IDs:
    # 2001 Shotgun, 2002 Chaingun, 2003 Rocket Launcher
    if mess_hall is not None:
        mx, my = _room_center(mess_hall)
        mx, my = _clamp_point_in_room(mess_hall, mx, my, pad=96)
        _add_thing(builder, type_id=2001, x=mx, y=my, angle=0)

        # "Arena" feel: surround the shotgun with pinkies + barrels.
        for ox, oy in ((-128, 0), (128, 0), (0, -128), (0, 128)):
            x, y = _clamp_point_in_room(mess_hall, mx + ox, my + oy, pad=64)
            _add_thing(builder, type_id=3002, x=x, y=y, angle=rng.choice((0, 90, 180, 270)))  # Pinky
        for ox, oy in ((-96, -96), (96, -96), (-96, 96), (96, 96)):
            x, y = _clamp_point_in_room(mess_hall, mx + ox, my + oy, pad=64)
            _add_thing(builder, type_id=2035, x=x, y=y, angle=0)  # Barrel

    # Chaingun: put it in a "warden office" stand-in: the northernmost bedroom.
    if bedrooms:
        warden = max(bedrooms, key=lambda r: int(getattr(r, "y", 0)))
        wx, wy = _room_center(warden)
        wx, wy = _clamp_point_in_room(warden, wx, wy, pad=64)
        _add_thing(builder, type_id=2002, x=wx, y=wy, angle=0)

    # Rocket launcher: reward climbing by placing on 3rd floor middle wing corridor.
    # We approximate "middle" by picking a corridor with floor_height ~280 closest to x=0.
    third_floor_corridors = [r for r in _iter_corridors(level) if int(getattr(r, "floor_height", 0) or 0) >= 280]
    if third_floor_corridors:
        middle_c = min(third_floor_corridors, key=lambda r: abs(int(getattr(r, "x", 0))))
        rx, ry = _room_center(middle_c)
        rx, ry = _clamp_point_in_room(middle_c, rx, ry, pad=64)
        _add_thing(builder, type_id=2003, x=rx, y=ry, angle=0)

    # --- Enemies ---
    # Corridors: Pinkies spaced along the long axis.
    for cor in _iter_corridors(level):
        pad = 64
        cx, cy = _room_center(cor)
        long_is_y = int(getattr(cor, "height", 0)) >= int(getattr(cor, "width", 0))
        span = int(getattr(cor, "height" if long_is_y else "width", 0))
        if span < 640:
            continue
        step = 512
        n = max(1, min(8, span // step))
        for i in range(1, n + 1):
            if long_is_y:
                x, y = _clamp_point_in_room(cor, cx, int(cor.y + pad + i * (span - 2 * pad) / (n + 1)), pad=pad)
            else:
                x, y = _clamp_point_in_room(cor, int(cor.x + pad + i * (span - 2 * pad) / (n + 1)), cy, pad=pad)
            _add_thing(builder, type_id=3002, x=x, y=y, angle=rng.choice((0, 90, 180, 270)))

    # Bedrooms: Zombiemen / Shotgun Guys near corners.
    for br in bedrooms:
        # Keep it light so rooms aren't jammed.
        if rng.random() < 0.35:
            continue
        corners = [
            (int(br.x) + 64, int(br.y) + 64),
            (int(br.x + br.width) - 64, int(br.y) + 64),
            (int(br.x) + 64, int(br.y + br.height) - 64),
            (int(br.x + br.width) - 64, int(br.y + br.height) - 64),
        ]
        rng.shuffle(corners)
        count = 1 if rng.random() < 0.75 else 2
        for (x, y) in corners[:count]:
            mon = 3004 if rng.random() < 0.6 else 9
            _add_thing(builder, type_id=mon, x=x, y=y, angle=rng.choice((0, 90, 180, 270)))

    # Stairwells (choke points): Hell Knights near off-map floor entrances.
    for cor in _iter_corridors(level):
        fh = int(getattr(cor, "floor_height", 0) or 0)
        if fh not in (140, 280):
            continue
        # Place near the south end of the corridor.
        x, y = _clamp_point_in_room(cor, *_room_center(cor), pad=64)
        y = int(max(int(cor.y) + 96, min(y, int(cor.y) + 160)))
        _add_thing(builder, type_id=64, x=x, y=y, angle=0)

    # --- Secrets ---
    # Pick 3 random bedroom doors and mark as secret; place reward inside.
    bedroom_doors: list[Door] = []
    for conn in getattr(level, "connectors", []) or []:
        if not isinstance(conn, Door):
            continue
        r1 = getattr(conn, "room1", None)
        r2 = getattr(conn, "room2", None)
        if type(r1).__name__ == "Bedroom" or type(r2).__name__ == "Bedroom":
            bedroom_doors.append(conn)

    rng.shuffle(bedroom_doors)
    secret_doors = bedroom_doors[:3]
    for idx, d in enumerate(secret_doors):
        setattr(d, "secret", True)
        br = d.room1 if type(getattr(d, "room1", None)).__name__ == "Bedroom" else d.room2
        if br is None:
            continue
        bx, by = _room_center(br)
        bx, by = _clamp_point_in_room(br, bx, by, pad=64)
        reward = 2013 if (idx % 2) == 0 else 8
        _add_thing(builder, type_id=reward, x=bx, y=by, angle=0)

    # Doom/ZDoom secrets are tracked via *secret sectors* (special 9), not secret linedefs.
    # Mark at least one bedroom as a real secret sector so the intermission totals are non-zero.
    if bedrooms:
        secret_room = rng.choice(bedrooms)
        setattr(secret_room, 'special', 9)

    # --- Exit objective ---
    if goal_room is not None:
        gx, gy = _room_center(goal_room)
        gx, gy = _clamp_point_in_room(goal_room, gx, gy, pad=96)

        # Add an exit trigger directly onto an existing boundary wall segment.
        # This avoids creating a new sector (no overlap risk).
        span = 128
        if hasattr(goal_room, 'width') and hasattr(goal_room, 'height'):
            if goal_room.width >= span + 64:
                side = 'top'
                offset = int(max(32, goal_room.width // 2 - span // 2))
            elif goal_room.height >= span + 64:
                side = 'right'
                offset = int(max(32, goal_room.height // 2 - span // 2))
            else:
                side = 'top'
                offset = 32
        else:
            side = 'top'
            offset = 32

        level.connectors.append(
            ExitLine(
                room=goal_room,
                side=side,
                offset=offset,
                span=span,
                texture='SW1STRTN',
            )
        )

        # Guard with a high-tier enemy.
        _add_thing(builder, type_id=3003, x=gx + 96, y=gy, angle=180)  # Baron

    # --- Debug summary (helps catch "100%/nothing spawned" reports) ---
    try:
        editor: Any = getattr(builder, 'editor')
        things = list(getattr(editor, 'things', []) or [])
        types = [int(getattr(t, 'type', 0) or 0) for t in things]
        monsters = sum(1 for t in types if t in (9, 3001, 3002, 3003, 3004, 64))
        pickups = sum(1 for t in types if t in (8, 2001, 2002, 2003, 2011, 2012, 2013))
        print(f"Gameplay populated: things={len(things)} monsters~={monsters} pickups~={pickups} secret_rooms={1 if bedrooms else 0}")
    except Exception:
        pass
