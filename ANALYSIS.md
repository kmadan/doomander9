# WadC Door Architecture - Key Discoveries

## The Fundamental Insight

**DOORS ARE NOT SEPARATE OVERLAPPING BOXES!**

Doors are drawn as part of the boundary geometry while constructing adjacent sectors.

## How WadC Sectors and Doors Work

### Sector Creation Pattern

1. **Sectors are closed loops of linedefs**
   - Each linedef has two sides (left/right)
   - Each side must be assigned to exactly ONE sector
   - `rightsector(floor, ceil, light)` assigns the right side of drawn linedefs to a new sector
   - `leftsector(floor, ceil, light)` assigns the left side

2. **The Turtle Graphics Model**
   - Cursor has position (x,y) and orientation (N/E/S/W)
   - `step(forward, right)` draws a linedef from current position
   - `box(floor, ceil, light, width, height)` is syntactic sugar that draws 4 linedefs then calls `rightsector()`
   - After `box()` cursor is rotated 90° right and positioned at starting corner

### Door Mechanics

A door is a **special sector** where:
- Floor height == Ceiling height when closed (zero height sector)
- Line type 1 (DR) on entrance: "Door opens on Use, closes after delay"
- Textures: `BIGDOOR2` on door face, `DOORTRAK` on sides

### The Correct Door Pattern

From `vanilla_conveyor.wl`:
```wl
testdoor(tag)
{
  sectortype(0,tag)
  box(add(lowest, 32), add(lowest, 32), 160, 16, 128)
  sectortype(0,0)
  move(16)
}
```

Key: `floor = ceiling = add(lowest, 32)` creates closed door sector.

From `entryway.wl`:
```wl
movestep(-128,128)
ceil("FLAT20")
floor("FLOOR3_3") 
unpegged
mid("DOORTRAK") 
straight(-8)          -- Draw 8 units forward (door thickness)
top("BIGDOOR1") 
left(128)             -- Draw 128 units to left (door width)
right(8)              -- Draw back to close rectangle
unpegged
rightsector(56,56,224) -- floor=56, ceil=56 = closed door!
```

## Why My Approach Failed

### Attempt 1: Overlapping box spanning from lawn into room
```wl
movestep(lawn_edge_position)
box(0, 0, 160, door_width, door_depth*2)  -- Overlaps lawn by door_d, room by door_d
```

**Problem**: This creates a **standalone rectangular sector** with 4 complete sides. The sector has linedefs on all edges - left, right, front, back. Player can walk around all 4 sides because it's not integrated into the lawn/room boundary.

**Why it appears as a pillar**: The door sector's linedefs don't share edges with lawn or room properly. They're separate, parallel linedefs creating a gap between door and both adjacent sectors.

### The Root Cause

`box()` **ALWAYS** creates a complete 4-sided closed loop and assigns `rightsector()` to the interior. It cannot create an opening/passage between existing sectors.

## The Correct Approach

### Option 1: Draw door manually as part of room construction

Instead of:
1. Draw complete lawn box (512x512)
2. Draw complete room box (256x256)  
3. Try to add door box between them ❌

Do this:
1. Draw lawn with **gap/opening** in boundary
2. From gap opening, draw door sector (thin connector)
3. From door sector, draw room

### Option 2: Use adjacent sector pattern

Draw rooms side-by-side with shared wall, then cut doorway:
1. Draw lawn
2. Draw room **adjacent** (sharing a wall edge)
3. Draw thin door sector at junction with special handling

### Key Primitives to Study

- `innerleftsector()` / `innerrightsector()` - create sector inside another
- `pushpop()` - save/restore cursor position
- `movestep(forward, right)` - move without drawing
- Manual linedef drawing with `step()` + `rightsector()` instead of `box()`

## Examples to Study Further

1. **entryway.wl** - Lines 285-315: Door between corridor and room
2. **vanilla_conveyor.wl** - testdoor() function: Simple door box
3. **blockmap.wl** - possible_future_room() shows connectivity planning

## Next Steps

1. Study how to draw sectors with **openings** (incomplete boundaries)
2. Learn how shared linedefs connect adjacent sectors
3. Implement proper doorway pattern: lawn → door → room as connected sectors
4. Test in-game to verify proper blocking and traversal
