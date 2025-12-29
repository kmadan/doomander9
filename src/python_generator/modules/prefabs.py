from .geometry import Room
from .furniture import Bed, Table, Chair, Plant

class Bedroom(Room):
    def __init__(self, x: int, y: int, width: int = 256, height: int = 256) -> None:
        super().__init__(x, y, width, height, floor_tex="FLOOR5_2", wall_tex="BROWN96")
        
        # Add Bed (Top Left Corner)
        self.add_furniture(Bed(x + 48, y + height - 48))
        
        # Add Desk/Chair (Bottom Right)
        self.add_furniture(Table(x + width - 48, y + 48))
        self.add_furniture(Chair(x + width - 80, y + 48, angle=180))

class CommonRoom(Room):
    def __init__(self, x: int, y: int, width: int = 384, height: int = 384) -> None:
        super().__init__(x, y, width, height, floor_tex="FLOOR4_8", wall_tex="STONE2")
        
        # Add Large Table (Center)
        cx, cy = x + width // 2, y + height // 2
        self.add_furniture(Table(cx, cy))
        
        # Add Chairs around
        self.add_furniture(Chair(cx - 48, cy, angle=0))
        self.add_furniture(Chair(cx + 48, cy, angle=180))
        self.add_furniture(Chair(cx, cy - 48, angle=270))
        self.add_furniture(Chair(cx, cy + 48, angle=90))
        
        # Plants in corners
        self.add_furniture(Plant(x + 32, y + 32))
        self.add_furniture(Plant(x + width - 32, y + 32))
        self.add_furniture(Plant(x + 32, y + height - 32))
        self.add_furniture(Plant(x + width - 32, y + height - 32))

class Bathroom(Room):
    def __init__(self, x: int, y: int, width: int = 128, height: int = 192) -> None:
        super().__init__(x, y, width, height, floor_tex="FLOOR0_1", wall_tex="STARGR1")
        # Add "Stalls" (represented by pillars for now)
        self.add_furniture(Plant(x + 32, y + height - 32)) # Sink?
