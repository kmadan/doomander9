import sys
import os

# Add omgifol to path
current_dir = os.path.dirname(os.path.abspath(__file__))
omgifol_path = os.path.abspath(os.path.join(current_dir, "../../tools/omgifol"))
if omgifol_path not in sys.path:
    sys.path.append(omgifol_path)

from omg import *
from omg.mapedit import MapEditor, Vertex, Linedef, Sidedef, Sector, Thing

class WadBuilder:
    def __init__(self):
        self.wad = WAD()
        # Create a new map (MAP01)
        self.editor = MapEditor()
        
    def draw_rectangle(self, x, y, width, height, floor_tex="FLOOR4_8", ceil_tex="CEIL3_5", wall_tex="STARTAN3", floor_height=0, ceil_height=128, light=160):
        """
        Draws a rectangular sector.
        x, y: Bottom-Left coordinates.
        """
        sector = Sector()
        sector.tx_floor = floor_tex
        sector.tx_ceil = ceil_tex
        sector.z_floor = floor_height
        sector.z_ceil = ceil_height
        sector.light = light
        
        sidedef = Sidedef()
        sidedef.tx_mid = wall_tex
        
        # Vertices in Counter-Clockwise order to ensure Front Side points Inward
        points = [
            (x, y),             # Bottom-Left
            (x + width, y),     # Bottom-Right
            (x + width, y + height), # Top-Right
            (x, y + height)     # Top-Left
        ]
        
        self.editor.draw_sector(points, sector, sidedef)

    def draw_polygon(self, points, floor_tex="FLOOR4_8", ceil_tex="CEIL3_5", wall_tex="STARTAN3", floor_height=0, ceil_height=128, light=160, tag=0):
        """
        Draws a polygonal sector from a list of (x, y) tuples.
        Points should be in Counter-Clockwise order.
        """
        sector = Sector()
        sector.tx_floor = floor_tex
        sector.tx_ceil = ceil_tex
        sector.z_floor = floor_height
        sector.z_ceil = ceil_height
        sector.light = light
        sector.tag = tag
        
        sidedef = Sidedef()
        sidedef.tx_mid = wall_tex
        
        self.editor.draw_sector(points, sector, sidedef)
        
    def add_player_start(self, x, y, angle=0):
        thing = Thing()
        thing.x = int(x)
        thing.y = int(y)
        thing.angle = angle
        thing.type = 1 # Player 1 Start
        thing.flags = 7 # Easy, Medium, Hard
        self.editor.things.append(thing)

    def save(self, filename):
        self.wad.maps["MAP01"] = self.editor.to_lumps()
        self.wad.to_file(filename)
