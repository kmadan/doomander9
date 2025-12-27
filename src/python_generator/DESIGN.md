# Procedural Hostel Generator Design Document

## 1. Objective
Create a Python-based procedural generation tool to construct Doom WAD files representing hostel environments. The tool will generate rooms, corridors, doors, windows, lawns, and larger structures like wings and halls.

## 2. Technology Stack
*   **Language**: Python 3.x
*   **Library**: `omgifol` (for WAD I/O and low-level map manipulation)
*   **Target Format**: Doom Binary Format (Vanilla/Boom compatible) or UDMF (GZDoom). *Recommendation: Start with Binary for broad compatibility, upgrade to UDMF if complex geometry is needed.*

## 3. Architecture

### 3.1. Core Abstraction (`WadBuilder`)
A wrapper around `omgifol` to handle the low-level details of WAD creation.
*   Manages lists of `Vertex`, `Linedef`, `Sidedef`, `Sector`, `Thing`.
*   Provides helper methods: `draw_sector(polygon, properties)`, `join_sectors(line1, line2)`.
*   Handles texture alignment and default properties.

### 3.2. Geometry Primitives
*   `Point(x, y)`
*   `Line(p1, p2)`
*   `Rectangle(x, y, width, height)`
*   `Polygon(points)`

### 3.3. Architectural Components
These classes represent the high-level concepts requested.

*   **`Element` (Base Class)**
    *   Properties: `position`, `rotation`, `tags`.
    *   Method: `build(builder)` - writes itself to the `WadBuilder`.

*   **`Room` (Inherits `Element`)**
    *   Attributes: `width`, `height`, `floor_texture`, `ceil_texture`, `wall_texture`.
    *   Logic: Generates a rectangular sector. Places default furniture (Things) like beds/desks.

*   **`Corridor` (Inherits `Element`)**
    *   Attributes: `length`, `width`, `shape` (straight, L-turn, T-junction).
    *   Logic: Connects two or more points/rooms.

*   **`Door` (Inherits `Element`)**
    *   Attributes: `type` (normal, locked, open), `texture`.
    *   Logic: Creates a thin sector between two other sectors. Sets linedef actions (e.g., Action 1: DR Door Open Wait Close).

*   **`Window` (Inherits `Element`)**
    *   Attributes: `height`, `texture`.
    *   Logic: Modifies a wall linedef to have a mid-texture or creates a "window sector" for depth.

*   **`Lawn` (Inherits `Room`)**
    *   Attributes: `grass_texture`, `sky_ceiling`.
    *   Logic: Outdoor sector with sky ceiling and grass floor.

*   **`Gate` (Inherits `Door`)**
    *   Attributes: `width`, `style`.
    *   Logic: Large door or bars texture.

### 3.4. Composite Structures
*   **`Wing`**
    *   Logic: Generates a row of `Room`s connected by a `Corridor`.
*   **`Hall`**
    *   Logic: Large central room connecting multiple `Wing`s.
*   **`Hostel`**
    *   Logic: The root container. Manages the overall layout of Halls and Wings.

## 4. Procedural Logic (The "Director")
A `LayoutEngine` class will be responsible for:
1.  **Blueprint Generation**: creating a logical graph of the layout (nodes = rooms, edges = connections).
2.  **Placement**: Assigning coordinates to the nodes to prevent overlap.
3.  **Realization**: Instantiating the Component classes based on the blueprint.

## 5. Implementation Plan

### Phase 1: Basic Room & WAD Output
*   Setup `omgifol`.
*   Implement `WadBuilder`.
*   Create a single `Room` and compile to WAD.

### Phase 2: Connections
*   Implement `Corridor` and `Door`.
*   Test connecting two rooms with a door.

### Phase 3: Hostel Features
*   Implement `Window`, `Lawn`, `Gate`.
*   Add "Things" (Player start, decorations).

### Phase 4: Procedural Generation
*   Implement `Wing` generator (loop to create N rooms).
*   Implement `Hostel` layout logic.

## 6. Resources
*   **omgifol**: `tools/omgifol`
*   **WAD Format**: [Doom Wiki - WAD](https://doomwiki.org/wiki/WAD)
