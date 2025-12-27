import sys
import os

# Add omgifol to path
current_dir = os.path.dirname(os.path.abspath(__file__))
omgifol_path = os.path.abspath(os.path.join(current_dir, "../../tools/omgifol"))
if omgifol_path not in sys.path:
    sys.path.append(omgifol_path)

from omg import *
from omg.mapedit import MapEditor, Vertex, Linedef, Sidedef, Sector, Thing
from omg.udmf import UMapEditor

class WadBuilder:
    def __init__(self):
        self.wad = WAD()
        # Create a new map (MAP01)
        self.editor = MapEditor()

        # Post-processing steps applied after converting the classic Doom-format map
        # to UDMF (TEXTMAP). Each entry is a dict with:
        #   control_line_id: unique line id to locate after conversion
        #   target_sector_tag: sector tag to receive the 3D floor
        #   type/flags/alpha: Sector_Set3dFloor args
        self._udmf_3dfloor_specs: list[dict] = []

        # Line portal postprocess (Line_SetPortal). Each entry is a dict with:
        #   source_line_id: line ID (UDMF) to apply portal to
        #   target_line_id: destination line ID
        #   type: 0 visual, 1 teleporter, 2 interactive, 3 static
        #   planeanchor: alignment mode
        self._udmf_line_portal_specs: list[dict] = []

        # Teleport destination postprocess: in classic Doom format, things don't
        # have TIDs. We record the teleport destination coordinates during build
        # and assign the UDMF thing `id` after conversion.
        self._udmf_teleport_dest_specs: list[dict] = []

        # Extra sector tags that should also receive the in-building 3D floor.
        # This is used when we must give some sectors (e.g. door sectors) unique
        # tags for actions, but still want them to have the second-story 3D floor.
        self._udmf_extra_3dfloor_target_tags: set[int] = set()

        # Unique sector tags allocated during build (avoid clashing with Level tags).
        self._next_sector_tag: int = 1000

        # Unique ids for UDMF postprocess control linedefs.
        self._next_control_line_id: int = 10000

    def alloc_sector_tag(self) -> int:
        tag = int(self._next_sector_tag)
        self._next_sector_tag += 1
        return tag

    def register_extra_3d_floor_target_tag(self, tag: int):
        if tag:
            self._udmf_extra_3dfloor_target_tags.add(int(tag))

    def get_extra_3d_floor_target_tags(self) -> set[int]:
        return set(self._udmf_extra_3dfloor_target_tags)

    def register_teleport_destination(self, *, x: int, y: int, tid: int):
        self._udmf_teleport_dest_specs.append({
            'x': int(x),
            'y': int(y),
            'tid': int(tid),
        })

    def register_udmf_3d_floor(self, *, control_line_id: int, target_sector_tag: int, type: int = 1, flags: int = 0, alpha: int = 255):
        self._udmf_3dfloor_specs.append({
            'control_line_id': int(control_line_id),
            'target_sector_tag': int(target_sector_tag),
            'type': int(type),
            'flags': int(flags),
            'alpha': int(alpha),
        })

    def register_udmf_line_portal(self, *, source_line_id: int, target_line_id: int, type: int = 1, planeanchor: int = 1):
        self._udmf_line_portal_specs.append({
            'source_line_id': int(source_line_id),
            'target_line_id': int(target_line_id),
            'type': int(type),
            'planeanchor': int(planeanchor),
        })

    def add_3d_floor_platform(self, *, target_sector_tag: int, z: int, thickness: int = 16,
                              floor_tex: str = "FLOOR4_8", ceil_tex: str = "CEIL3_5", wall_tex: str = "STARTAN3",
                              alpha: int = 255, flags: int = 0):
        """Create a simple solid 3D-floor platform (ZDoom UDMF) inside target sectors.

        This draws an off-map control sector and marks one control linedef with a
        unique id. During `save()`, that linedef is converted to Sector_Set3dFloor
        to apply the 3D floor to all sectors tagged with `target_sector_tag`.
        """
        control_line_id = self._next_control_line_id
        self._next_control_line_id += 1

        # Off-map control sector location.
        cx = 20000 + (control_line_id - 10000) * 128
        cy = 20000
        w = 64
        h = 64

        sector_index = len(self.editor.sectors)
        self.draw_rectangle(
            cx,
            cy,
            w,
            h,
            floor_tex=floor_tex,
            ceil_tex=ceil_tex,
            wall_tex=wall_tex,
            floor_height=int(z),
            ceil_height=int(z + thickness),
            light=160,
        )

        # Tag exactly one linedef of the control sector so we can find it after UDMF conversion.
        tagged = False
        for ld in self.editor.linedefs:
            if tagged:
                break
            if ld.back == 0xFFFF:
                front_sector = self.editor.sidedefs[ld.front].sector
                if front_sector == sector_index:
                    ld.tag = int(control_line_id)
                    tagged = True

        if not tagged:
            raise RuntimeError("Failed to tag 3D-floor control linedef")

        self.register_udmf_3d_floor(
            control_line_id=control_line_id,
            target_sector_tag=int(target_sector_tag),
            type=1,
            flags=int(flags),
            alpha=int(alpha),
        )

        return control_line_id
        
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
        # Build classic map lumps first (we rely on MapEditor.draw_sector convenience)
        classic_lumps = self.editor.to_lumps()

        # Convert to UDMF so we can use Hexen-style specials w/ args (e.g. Sector_Set3dFloor)
        umap = UMapEditor(classic_lumps, namespace="ZDoom")

        # Translate legacy Doom-format line types used by this generator into
        # UDMF/ZDoom action specials.
        #
        # Important: when we convert a Doom-format map to UDMF, the original linedef
        # `action` field becomes `special` verbatim. That is *not* what we want,
        # because Doom-format line type numbers do not match ZDoom action-special
        # numbers. We rewrite the few types we rely on.
        for ld in umap.linedefs:
            # 1 in Doom format = DR Door (open-wait-close)
            if getattr(ld, 'special', 0) == 1:
                # Map to Door_Raise(tag, speed, delay, lighttag)
                door_tag = int(getattr(ld, 'arg0', 0))
                ld.special = 12
                ld.arg0 = door_tag
                ld.arg1 = 16     # speed
                ld.arg2 = 150    # delay
                ld.arg3 = 0      # lighttag
                ld.arg4 = 0
                # Trigger flags (ZDoom/Hexen-style in UDMF)
                ld.playeruse = True
                ld.repeatspecial = True
                ld.monsteractivate = True

            # 42 in Doom format = SR Door Close
            elif getattr(ld, 'special', 0) == 42:
                # The converter preserves the original linedef tag in ld.arg0.
                # Map to Door_Close(tag, speed, lighttag)
                door_tag = getattr(ld, 'arg0', 0)
                ld.special = 10
                ld.arg0 = door_tag
                ld.arg1 = 16
                ld.arg2 = 0
                ld.arg3 = 0
                ld.arg4 = 0
                ld.playeruse = True
                ld.repeatspecial = True

            # 97 in Doom format = WR Teleport
            elif getattr(ld, 'special', 0) == 97:
                # Converter stores the original Doom tag in ld.arg0.
                # Use Teleport(tid, 0) to avoid any dependence on sector-tag lookup.
                dest_tag = int(getattr(ld, 'arg0', 0))
                dest_tid = 1000 + dest_tag
                # Map to Teleport(tid, tag, nosourcefog)
                ld.special = 70
                ld.arg0 = dest_tid
                ld.arg1 = 0
                ld.arg2 = 0
                ld.arg3 = 0
                ld.arg4 = 0
                ld.playercross = True
                ld.repeatspecial = True
                ld.monsteractivate = True

        # Assign TIDs to teleport destination things (TeleportDest, DoomEdNum 14).
        # Match by exact coordinates (the generator uses integer coordinates).
        for spec in self._udmf_teleport_dest_specs:
            target_x = float(spec['x'])
            target_y = float(spec['y'])
            matched = False
            for th in umap.things:
                if getattr(th, 'type', 0) == 14 and getattr(th, 'x', None) == target_x and getattr(th, 'y', None) == target_y:
                    th.id = int(spec['tid'])
                    matched = True
                    break
            if not matched:
                raise RuntimeError(f"UDMF postprocess failed: could not find TeleportDest at ({spec['x']}, {spec['y']})")

        # Apply any requested 3D-floor control linedefs.
        # Our control lines are created in classic format with a unique linedef tag.
        # During conversion, omg.udmf maps that tag onto both `id` and `arg0`.
        # We match by `id`.
        for spec in self._udmf_3dfloor_specs:
            control_line_id = spec['control_line_id']
            target_sector_tag = spec['target_sector_tag']
            matched = False
            for ld in umap.linedefs:
                if getattr(ld, 'id', -1) == control_line_id:
                    ld.special = 160  # Sector_Set3dFloor
                    ld.arg0 = target_sector_tag
                    ld.arg1 = spec['type']
                    ld.arg2 = spec['flags']
                    ld.arg3 = spec['alpha']
                    ld.arg4 = 0
                    matched = True
                    break
            if not matched:
                raise RuntimeError(f"UDMF postprocess failed: could not find control linedef id={control_line_id}")

        # Apply any requested line portals.
        # We create source portal lines in classic format with a unique linedef tag.
        # During conversion, omg.udmf maps that tag onto `id`. We match by `id`.
        for spec in self._udmf_line_portal_specs:
            source_line_id = spec['source_line_id']
            target_line_id = spec['target_line_id']
            matched = False
            for ld in umap.linedefs:
                if getattr(ld, 'id', -1) == source_line_id:
                    # 156: Line_SetPortal(targetline, thisline, type, planeanchor)
                    ld.special = 156
                    ld.arg0 = int(target_line_id)
                    ld.arg1 = 0
                    ld.arg2 = int(spec['type'])
                    ld.arg3 = int(spec['planeanchor'])
                    ld.arg4 = 0
                    matched = True
                    break
            if not matched:
                raise RuntimeError(f"UDMF postprocess failed: could not find portal linedef id={source_line_id}")

        self.wad.udmfmaps["MAP01"] = umap.to_lumps()

        self.wad.to_file(filename)
