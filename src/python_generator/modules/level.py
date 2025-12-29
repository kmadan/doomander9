from typing import List, TYPE_CHECKING, Union, Optional, Tuple

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
