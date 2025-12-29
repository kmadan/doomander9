from typing import List, TYPE_CHECKING, Union, Optional, Tuple
import os

if TYPE_CHECKING:
    from .geometry import Room
    from .connectors import Connector, Switch

class Level:
    def __init__(self) -> None:
        self.rooms: List['Room'] = []
        self.connectors: List[Union['Connector', 'Switch']] = []
        self.next_tag: int = 1
        self.test_spawn: Optional[Tuple[int, int, int]] = None

        # (x, y, text) tuples used by WadBuilder.add_label_spot during build.
            # Removed label spot support
        
    def get_new_tag(self) -> int:
        tag = self.next_tag
        self.next_tag += 1
        return tag
        
    def add_room(self, room: 'Room') -> 'Room':
        self.rooms.append(room)
        return room
        
    def add_connector(self, connector: Union['Connector', 'Switch']) -> None:
        self.connectors.append(connector)
        return connector
        
    def build(self, builder):
        # Optional debug validation: Doom geometry cannot have overlapping sectors in 2D.
        # Enable with `H9_VALIDATE_OVERLAPS=1`.
        if str(os.environ.get('H9_VALIDATE_OVERLAPS', '')).strip() not in ('', '0', 'false', 'False'):
            self._validate_no_room_overlaps()

        # First, register cuts
        for conn in self.connectors:
            conn.register_cuts()
            
        # Build rooms
        for room in self.rooms:
            room.build(builder)
            
        # Build connectors
        for conn in self.connectors:
            conn.build(builder)

            # Removed label spot processing

    def _validate_no_room_overlaps(self) -> None:
        rooms = list(self.rooms)
        overlaps: list[tuple[int, int, int, int, int, int]] = []

        def _rect(r):
            x0 = int(getattr(r, 'x', 0))
            y0 = int(getattr(r, 'y', 0))
            x1 = x0 + int(getattr(r, 'width', 0))
            y1 = y0 + int(getattr(r, 'height', 0))
            return x0, y0, x1, y1

        for i in range(len(rooms)):
            a = rooms[i]
            ax0, ay0, ax1, ay1 = _rect(a)
            for j in range(i + 1, len(rooms)):
                b = rooms[j]
                bx0, by0, bx1, by1 = _rect(b)

                ix0 = max(ax0, bx0)
                iy0 = max(ay0, by0)
                ix1 = min(ax1, bx1)
                iy1 = min(ay1, by1)
                if ix0 < ix1 and iy0 < iy1:
                    overlaps.append((i, j, ix0, iy0, ix1, iy1))

        if overlaps:
            details = []
            for i, j, ix0, iy0, ix1, iy1 in overlaps[:50]:
                a = rooms[i]
                b = rooms[j]
                details.append(
                    f"overlap {i} {type(a).__name__}@({a.x},{a.y},{a.width},{a.height}) "
                    f"vs {j} {type(b).__name__}@({b.x},{b.y},{b.width},{b.height}) "
                    f"=> ({ix0},{iy0})-({ix1},{iy1})"
                )
            raise RuntimeError(
                "Detected overlapping rooms (invalid Doom 2D geometry). "
                "Set H9_VALIDATE_OVERLAPS=0 to disable.\n" + "\n".join(details)
            )
