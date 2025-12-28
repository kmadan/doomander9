# Doomander9 – Map Generator Onboarding

This repo generates a playable Doom II map (UDMF) from Python code. The primary goal is fast iteration on layout + traversal while keeping geometry valid (no overlaps/HOM) and openings (doors/windows) consistently cut.

## TL;DR (Quick Start)

1. Ensure the external tools paths in the batch files match your machine:
   - `compile_py_map.bat` (nodebuilder path: `zdbsp.exe`)
   - `run_map.bat` / `run_map_nobuild.bat` (UZDoom exe + DOOM2 IWAD)
2. Build and run:
   - `compile_py_map.bat` → generates `build/py_hostel_full.wad`
   - `run_map.bat` → builds then launches the map
   - `run_map_nobuild.bat` → launches the last built WAD

## Prerequisites (New Machine Setup)

You need three “external” things to iterate:

- **Python 3** available as `py -3` (Windows Python Launcher).
- **Nodebuilder**: `zdbsp.exe` (path configured in `compile_py_map.bat`).
- **Engine**: UZDoom + an IWAD (paths configured in `run_map.bat` / `run_map_nobuild.bat`).

Optional but recommended:

- A virtualenv in `.venv/` if you run helper scripts directly. The generator itself vendors `tools/omgifol/` and doesn’t require pip installs.

## Repository Layout

- `src/python_generator/`
  - `main_hostel.py`: entry point used by `compile_py_map.bat`
  - `hostel_generator.py`: *the* layout orchestrator (wings, lawns, cross-corridor, stairs, portals)
  - `builder.py`: WAD builder and UDMF conversion/post-process
  - `modules/`
    - `level.py`: holds rooms/connectors and build order
    - `geometry.py`: `Room`, `Corridor`, `Lawn` primitives
    - `wing.py`: procedural wing generator (rooms + corridor + corridor lookouts)
    - `connectors.py`: `Door`, `Window`, `Portal` (they cut openings + add special behavior)
    - `prefabs.py`: `Bedroom`, `Bathroom`, `CommonRoom` (room textures + furniture)

- `build/`
  - Output WADs (raw and final).

- `tools/omgifol/`
  - Vendored `omgifol` library used for WAD I/O and map editing.

- `wadc/` and `src/scripts/`
  - WadC tooling + scripts (older/parallel experimentation). The current “mainline” generator is Python.

## Tooling & Build Pipeline

### Python → raw WAD → nodebuild → playable WAD

The primary pipeline is:

1. `src/python_generator/main_hostel.py`
   - Creates a `WadBuilder` and calls `HostelGenerator.generate()`.
   - Builds the `Level` into classic Doom map lumps.
   - Saves a *raw* UDMF-ready WAD to `build/py_hostel_full_raw.wad`.

2. `compile_py_map.bat`
   - Runs the generator (`py -3 src\python_generator\main_hostel.py`).
   - Runs `zdbsp` to build nodes and emit `build/py_hostel_full.wad`.

3. `run_map.bat` / `run_map_nobuild.bat`
   - Launches UZDoom with `-iwad DOOM2.WAD -file build\py_hostel_full.wad -warp 1`.

### Other helpful scripts

- `run_stairs_test.bat` / `compile_py_stairs_test.bat`: smaller focused test map for stairs experiments.
- `run_map_nobuild.bat`: fastest loop when you’ve already built.

### WadC pipeline (optional)

There’s also a WadC-based route:
- `compile_map.bat` builds `src/scripts/hostel_layout.wl` into `build/hostel.wad` via Java.
- `launch_wadc_gui.bat` launches the WadC GUI for exploring `.wl` scripts.

## Coordinate System & Sizing

All generator geometry is axis-aligned.

- Coordinates are in Doom map units.
- By convention, `start_x=0, start_y=0` is the **south-west corner of the central lawn**.
- $+y$ is “north” (cross-corridor is placed at `y = lawn_height + wall_thickness`).

Key constants in `HostelGenerator.generate()`:

- `wall_thickness = 16`
- Room size: `256×256`
- Corridor width: `128`
- Wing total height:
  - There are 16 vertical “units” (7 rooms + bathroom block + 7 rooms)
  - Each unit is `(room_height + wall_thickness)`
  - Plus a final `wall_thickness`
  - Result: `wing_height = 4368`
- Central lawn: `512×4368`

## Map Layout (Mental Model)

The map is designed around a central outdoor lawn and three wings connected by a north “cross corridor”. The layout is assembled in `src/python_generator/hostel_generator.py`.

### Blueprint (high-level)

This is not to scale, but it’s the best “first read” mental model:

```
       [ Mess Hall ]
         |
         | (door + switch)
   [West Wing] -- [ Cross Corridor ] -- [East Wing]
     |               |
     |               | (wide opening)
     |            [ Central Lawn ]
     |
   [Brown Strip]
     |
   [Middle Wing]  (between Brown Strip and Lawn)

Notes:
- The Brown Strip is between West Wing and Middle Wing.
- Middle Wing corridor faces the Lawn, but it uses a *buffer strip* so the lookouts
  actually open to an outdoor sector and don’t overlap the stair bump-out.
```

### Nomenclature (use these consistently)

- **East Wing**: wing east of the central lawn.
- **Middle Wing**: wing directly west of the central lawn.
- **West Wing**: far-left wing.
- **Central Lawn**: the main outdoor area (grass).
- **Cross Corridor**: north corridor connecting wings + lawn + mess hall.
- **Brown Strip**: outdoor strip (brown flat) between West Wing and Middle Wing.
- **Middle Buffer Strip**: narrow grass strip between Middle Wing corridor and the central lawn (exists to make corridor lookouts “open” and to reserve space for stairs).
- **West Outside Yard**: large inaccessible outdoor area west of West Wing (for room windows to look onto).

### What connects to what

- Cross Corridor connects to:
  - West Wing corridor
  - Middle Wing corridor
  - East Wing corridor
  - Central lawn (wide opening)
  - Brown strip (opening)
  - Mess hall (door + switch)

- Corridor “lookouts”:
  - Middle Wing corridor lookouts target the **Middle Buffer Strip**, which in turn opens into the central lawn.
  - West Wing corridor lookouts target the **west half of the Brown Strip**, segmented around the stair reserved span.

- Bedroom windows:
  - Middle Wing bedrooms face the **Brown Strip (east half)**.
  - West Wing bedrooms face the **West Outside Yard**.

### Why the buffer strips exist

A recurring issue in Doom geometry is that “windows” and “openings” only work if there is actually an outdoor sector adjacent to the cut. If a corridor window is cut straight into the edge of a huge lawn sector without a gap/connector sector, you can end up with what looks like a solid wall.

So we often insert a thin outdoor strip sector and connect strip→lawn with explicit openings.

## Generator Architecture (How Pieces Fit)

### `Level` build order

`src/python_generator/modules/level.py` builds the map in a strict order:

1. Connectors register their “cuts” against adjacent rooms.
2. Rooms build their polygons with those cuts applied.
3. Connectors build their own geometry (door/window sectors, portal lines).

This order is critical: rooms must know where openings are before they draw their boundary polygons.

### Rooms and cuts

`src/python_generator/modules/geometry.py` defines `Room`/`Corridor`/`Lawn`.

Each `Room` maintains cut lists (`top`, `bottom`, `left`, `right`) as offsets along its edges. When building geometry, it inserts extra vertices at cut points so openings exist in the polygon.

### Connectors

`src/python_generator/modules/connectors.py` defines:

- `Door`: creates a thin door sector in a wall gap, then tags linedefs so UDMF conversion can apply the correct action.
- `Window`: creates a thin “jamb” sector and clears mid textures on both sides so the opening is not rendered as a solid wall.
- `Portal`: records line IDs for a post-process step that applies `Line_SetPortal` in UDMF.

**Important:** A connector only registers a cut if it exactly touches the target room’s boundary.

For example, a connector touches the right edge of a room only when:

- `connector.x == room.x + room.width`

If you place it “almost” adjacent (off by 1, or overlapping), the cut won’t register and you will get solid walls.

### `Wing`

`src/python_generator/modules/wing.py` creates:

- One corridor (vertical strip)
- 7 rooms
- 1 central bathroom (double height)
- 7 rooms
- Doors from rooms/bathroom into the corridor
- Optional corridor lookouts (windows) on the lawn-facing side

Corridor lookouts support:

- `corridor_window_skip_ranges`: world-Y spans where lookouts are not allowed (used to reserve stairwell spans)
- `corridor_window_targets`: optional per-Y-range targets so lookouts can open to a buffer strip or segmented outdoor area

## Second Floor & Stairs (Portals)

This project implements a “second floor” as an off-map copy of the building, connected via line portals.

- The off-map copy is placed at `second_floor_offset_y = -6000`.
- Stairs are built as an “outside bump-out” from each corridor (to avoid overlapping door cuts on the corridor interior wall).
- The portal connection is created at the top landing/threshold.

The WAD builder (`src/python_generator/builder.py`) converts classic lumps to UDMF and rewrites a small set of specials into ZDoom actions. It also applies the post-process portal and 3D-floor steps.

### What `builder.py` actually does (important for debugging)

- The generator builds geometry using `omgifol`’s classic `MapEditor` APIs, then converts to UDMF (`UMapEditor`).
- During conversion, a small set of classic Doom line actions are rewritten into ZDoom UDMF specials:
  - Doom line type `1` (DR Door) → ZDoom `Door_Raise` (special 12)
  - Doom line type `42` (SR Door Close) → ZDoom `Door_Close` (special 10)
  - Doom line type `97` (WR Teleport) → ZDoom `Teleport` (special 70)

If a door/switch “stops working” after a refactor, it’s often because:
- the linedef didn’t get tagged correctly, or
- the action number changed but the rewrite logic didn’t.

## Textures

- Outdoor grass uses `PYGRASS`.
  - `WadBuilder.save()` ensures `PYGRASS` exists as a procedural flat to avoid missing-flat fallbacks.
- Sky ceilings use `F_SKY1` (via the `Lawn` class).
- Brown strip uses floor flat `RROCK19`.

## Common Failure Modes (and how to avoid them)

### 1) HOM / “moving sky” / flickering surfaces

Almost always caused by **overlapping sectors** or “cuts” that don’t resolve into a valid polygon.

Rules of thumb:
- Never overlap rooms/sectors in world space.
- When connecting two areas, leave a **real wall-thickness gap** (16 units) and place the connector in that gap.
- Don’t make connectors wider/taller than the regions they are supposed to connect.

Fast diagnosis:
- If you see flicker between two different wall textures (brick/gray), suspect *two sectors fighting for the same space* or a connector sector that overshoots bounds.

### 2) “Solid wall where a window should be”

Typical causes:
- Connector does not align exactly with room boundary → cut not registered.
- There is no outdoor sector on the far side (window opens into nothing).
- The opening is attempted on a boundary without a gap/connector sector.

Fix pattern:
- Insert a thin outdoor strip sector.
- Add `Window` connectors strip↔target to guarantee adjacency.

Also confirm alignment:
- In `modules/connectors.py`, cuts are registered only when connector edges match room edges **exactly**.
- “Off by 16” is the most common mistake (forgot to account for `wall_thickness`).

### 3) Stairs become blocked / dead-end at top

Usually caused by overlaps between:
- stairwell bump-out geometry
- outdoor buffer strips
- portal landing/threshold

Fix pattern:
- Expand “reserved spans” to include hall + landing + portal threshold.
- Use `corridor_window_skip_ranges` so corridor lookouts never overlap stair spans.

## Debugging Tips

- Rebuild often: `compile_py_map.bat` is the canonical build.
- Launch without rebuild when iterating quickly: `run_map_nobuild.bat`.
- If you suspect missing textures/flats, inspect the WAD lumps (see `tools/omgifol/` and the existing debug scripts in `tools/`).
- If you suspect overlaps, compute AABB overlaps in Python (there are ad-hoc scripts/one-liners used during development).

### Debugging checklist (when something looks wrong)

1. **Is it a geometry overlap?**
  - Symptoms: flicker, HOM, “moving sky”, random solid walls.
  - Action: check AABB overlaps for the suspect areas.

2. **Is it a missing cut (connector didn’t register)?**
  - Symptoms: a doorway/window is a solid wall.
  - Action: verify connector is in a 16-unit gap and exactly touches the room edge.

3. **Is it an outdoor adjacency issue?**
  - Symptoms: corridor lookouts become a solid wall even though a window exists.
  - Action: ensure the window opens into an actual outdoor sector (buffer strip patterns).

4. **Is it a portal/special rewrite issue?**
  - Symptoms: doors/switches/teleports don’t work, but geometry looks fine.
  - Action: confirm the underlying classic action types are the ones `builder.py` rewrites.

## Common Engineering Tasks

- **Add a new outdoor area**: create a `Lawn(...)` with `ceil_tex=F_SKY1` (the `Lawn` class defaults this) and connect it with `Window` connectors placed in a 16-unit gap.
- **Change where corridor lookouts open**: use `corridor_window_targets` in `hostel_generator.py` to map Y-ranges to a specific outdoor room.
- **Temporarily disable corridor lookouts**: pass `add_corridor_windows=False` to `Wing.generate(...)`.
- **Reserve space for stairs**: expand the reserved Y-span to include hall + landing + portal threshold and pass it via `corridor_window_skip_ranges`.

## “Where do I make changes?”

- Layout/topology changes (wings placement, outdoor areas, cross corridor, stairs):
  - `src/python_generator/hostel_generator.py`

- Wing internals (how rooms/corridor/windows are generated):
  - `src/python_generator/modules/wing.py`

- How openings and specials behave:
  - `src/python_generator/modules/connectors.py`

- How geometry becomes WAD + UDMF:
  - `src/python_generator/builder.py`

---

If you’re new to Doom mapping pitfalls: the single most important mental model is that this generator is doing constructive solid geometry by *exact edge alignment*. One-unit mistakes (or overlaps) don’t fail loudly; they show up as solid walls, flicker, or HOM.
