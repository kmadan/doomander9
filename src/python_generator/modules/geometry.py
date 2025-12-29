from .element import Element

class Room(Element):
    def __init__(self, x: int, y: int, width: int, height: int, floor_tex: str = "FLOOR4_8", wall_tex: str = "STARTAN3", ceil_tex: str = "CEIL3_5", floor_height: int = 0, ceil_height: int = 128, tag: int = 0) -> None:
        super().__init__(x, y)
        self.width = width
        self.height = height
        self.floor_tex = floor_tex
        self.wall_tex = wall_tex
        self.ceil_tex = ceil_tex
        self.floor_height = floor_height
        self.ceil_height = ceil_height
        self.tag = tag
        self.cuts = {
            'top': [],
            'bottom': [],
            'left': [],
            'right': []
        }
        self.furniture = []
        
    def add_cut(self, side, offset):
        try:
            off = int(offset)
        except Exception:
            off = offset

        # Cuts at the exact endpoints (0 or full span) are redundant because the
        # corner vertices already exist. Keeping them can introduce zero-length
        # edges / duplicate points, which in turn can prevent connectors (notably
        # portals) from becoming properly two-sided.
        if side in ('left', 'right'):
            if off <= 0 or off >= int(self.height):
                return
        elif side in ('top', 'bottom'):
            if off <= 0 or off >= int(self.width):
                return

        if off not in self.cuts[side]:
            self.cuts[side].append(off)
            
    def add_furniture(self, item):
        # Adjust item coordinates to be absolute if they are relative?
        # For now assume absolute.
        self.furniture.append(item)
            
    def build(self, builder):
        # Build Geometry
        self._build_geometry(builder)
        
        # Build Furniture
        for item in self.furniture:
            item.build(builder)
            
    def _build_geometry(self, builder):
        for side in self.cuts:
            self.cuts[side].sort()
            
        points = []
        # Bottom (Left -> Right)
        points.append((self.x, self.y))
        for cut in self.cuts['bottom']:
            points.append((self.x + cut, self.y))
        points.append((self.x + self.width, self.y))
        
        # Right (Bottom -> Top)
        for cut in self.cuts['right']:
            points.append((self.x + self.width, self.y + cut))
        points.append((self.x + self.width, self.y + self.height))
        
        # Top (Right -> Left)
        for cut in reversed(self.cuts['top']):
            points.append((self.x + cut, self.y + self.height))
        points.append((self.x, self.y + self.height))
        
        # Left (Top -> Bottom)
        for cut in reversed(self.cuts['left']):
            points.append((self.x, self.y + cut))
            
        # Filter unique
        unique_points = []
        for p in points:
            if not unique_points or unique_points[-1] != p:
                unique_points.append(p)
        if len(unique_points) > 0 and unique_points[0] == unique_points[-1]:
            unique_points.pop()
            
        builder.draw_polygon(unique_points, 
                             floor_tex=self.floor_tex, 
                             ceil_tex=self.ceil_tex, 
                             wall_tex=self.wall_tex,
                             floor_height=self.floor_height,
                             ceil_height=self.ceil_height,
                             tag=self.tag)

class Corridor(Room):
    def __init__(self, x, y, width, height, floor_tex="FLOOR0_1", wall_tex="STONE2", ceil_tex="CEIL3_5"):
        super().__init__(x, y, width, height, floor_tex, wall_tex, ceil_tex)

class Lawn(Room):
    def __init__(self, x, y, width, height, floor_tex="PYGRASS", wall_tex="BRICK7"):
        super().__init__(x, y, width, height, floor_tex, wall_tex, ceil_tex="F_SKY1", ceil_height=256)
