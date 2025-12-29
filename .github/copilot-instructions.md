# Copilot instructions (doomander9)

You are the **world’s best Python Doom WAD programmer**. Optimize for correct Doom geometry (no HOM/overlaps), fast iteration, and preserving the generator’s build invariants.

## Quick workflow (Windows)
- Build + launch: `./run_map.bat` (calls `compile_py_map.bat`, then runs UZDoom).
- Build only: `./compile_py_map.bat` (Python → raw WAD → `zdbsp` → playable WAD).
- Fast relaunch: `./run_map_nobuild.bat`.
- Paths you may need to edit on a new machine:
  - `compile_py_map.bat`: `ZDBSP=...\zdbsp.exe`
  - `run_map*.bat`: `DOOM_EXE=...\uzdoom.exe`, `IWAD=...\DOOM2.WAD`

## Big picture architecture
- Orchestrator: `src/python_generator/hostel_generator.py` (`HostelGenerator.generate()` builds the whole layout).
- High-level “feature builders”: `src/python_generator/layout/` (preferred place for extracting layout assembly).
  - Stairs/portals: `layout/stairs.py` (`add_stairwell_to_corridor`, `add_second_floor_portal_entry`, `add_stair_extension`).
  - Main-floor assembly helpers: `layout/hostel_layout.py`.
- Low-level primitives: `src/python_generator/modules/`
  - Map graph: `modules/level.py` (`Level.rooms`, `Level.connectors`, strict build order).
  - Geometry: `modules/geometry.py` (`Room`, `Corridor`, `Lawn`, cut lists).
  - “Openings + behavior”: `modules/connectors.py` (`Door`, `Window`, `Portal`).
  - Procedural wings: `modules/wing.py` (rooms + corridor + corridor lookouts).

## Non-negotiable invariant: cut registration + build order
`Level.build()` is intentionally ordered:
1) `connector.register_cuts()`  2) `room.build()`  3) `connector.build()`
If you change how connectors/rooms are created, preserve this model: rooms must know their cuts before drawing polygons.

## Geometry rules (avoid solid walls / broken cuts)
- Cut registration is exact-edge based (see `Connector._add_cut_to_room` in `modules/connectors.py`).
  - Example: a connector only cuts the right edge when `connector.x == room.x + room.width`.
- Prefer integer math and align everything to `wall_thickness` (typically 16). Off-by-1 breaks openings.
- When adding a window/door between two areas, ensure there is a real gap sector to place the connector (often a 16-unit wall-thickness strip).

## Doors / switches / specials (UDMF conversion)
- The generator builds classic Doom-format lumps via `omgifol.MapEditor`, then converts to UDMF in `src/python_generator/builder.py`.
- `builder.py` rewrites a small set of Doom line types into ZDoom UDMF specials (e.g., Doom 1/42/97).
  - If a door/switch “stops working”, check connector tagging (`Door.build()` sets `ld.action` + `ld.tag`) and then check the rewrite logic in `WadBuilder.save()`.

## Off-map floors + portals
- Upper floors are off-map copies placed at negative Y offsets; traversal is via line portals (`Portal` connectors) applied in a UDMF postprocess (`builder.py`).
- Keep portal pair IDs unique and passed consistently:
  - F1 stairwell top uses a portal between landing→threshold.
  - Upper-floor “arrival” uses the reverse portal direction (see `layout/stairs.py`).
- Do not “temporarily” disable portals by passing `None` for portal IDs—this creates dead ends.

## Texture-default sensitivity
- Some connectors rely on `Window` defaults (floor/ceil/wall textures) when args are omitted.
- If refactoring into builders, preserve callsite behavior:
  - Only pass `floor_tex`/`ceil_tex` to `Window(...)` where the old code did.
  - `layout/hostel_layout.build_middle_lawn_buffer(..., pass_window_textures=...)` exists specifically for this.

## Dependencies / imports
- `tools/omgifol/` is vendored; `builder.py` adds it to `sys.path`.
- Entry points (e.g., `src/python_generator/main_hostel.py`) add `src/python_generator` to `sys.path` for script-style imports.

Primary reference doc: `ONBOARDING.md`.
