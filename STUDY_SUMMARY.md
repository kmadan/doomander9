# WadC Study Summary - Critical Insights

## Documentation Sources Analyzed

### Primary References
- **reference.adoc** (1046 lines): Complete WadC language reference
- **tutorial.adoc** (333 lines): Step-by-step learning guide  
- **standard.h** (162 lines): Core utility functions (box, pushpop, movestep, etc.)
- **basic.h** (367 lines): Structural components (segments, stairs, placement)
- **doom.h**: Doom-specific texture/line/sector types

### Key Examples Studied
1. **entryway.wl** (889 lines): Doom 2 MAP01 recreation - shows real door implementation
2. **vanilla_conveyor.wl** (78 lines): Simple door demonstration with testdoor()
3. **blockmap.wl** (200 lines): Random room generation with connectivity
4. **Tutorial examples** (1.wl through 13.wl): Progressive learning from box to complex layouts

## Core WadC Concepts

### Turtle Graphics Model

**Cursor State:**
- Position: (x, y) coordinates
- Orientation: North (0°), East (90°), South (180°), West (270°)
- Pen: up (moving only) or down (drawing linedefs)
- Properties: current textures, floor/ceiling heights, light level, line types

**Movement Commands:**
- `step(forward, right)`: Draw linedef from current position
- `straight(n)`: Draw n units forward  
- `left(n)`, `right(n)`: Draw n units left/right (turns 90° after)
- `movestep(fwd, right)`: Move without drawing
- `rotleft`, `rotright`: Rotate orientation 90°
- `turnaround`: Rotate 180°

**State Management:**
- `!name`: Store position, orientation, textures to variable
- `^name`: Restore saved state
- `pushpop(x)`: Execute x, then restore original position/orientation

### Sector Creation Pattern

**Fundamental Rule:** Sectors are closed loops of linedefs

```wl
-- Draw closed loop (example: rectangle)
straight(256)   -- South edge
right(512)      -- East edge
right(256)      -- North edge  
right(512)      -- West edge (completes loop back to start)

rightsector(floor_height, ceiling_height, light_level)
```

**Sector Assignment:**
- `rightsector(f,c,l)`: Assigns RIGHT side of linedefs to new sector
- `leftsector(f,c,l)`: Assigns LEFT side of linedefs to new sector
- `innerrightsector(f,c,l)`: Creates inner sector, outer side connects to previous sector
- `innerleftsector(f,c,l)`: Same but traversing counter-clockwise

**Critical Constraint:** Each sidedef can only be assigned to ONE sector. Trying to assign twice causes "sidedef already assigned" error.

### The box() Function

From standard.h lines 95-105:
```wl
box(floor,ceil,light,x,y) {
  straight(x)      -- Forward edge (width)
  right(y)         -- Right edge (height)
  right(x)         -- Back edge
  right(y)         -- Left edge (completes rectangle)
  rightsector(floor,ceil,light)
  rotright         -- Rotate 90° at end!
}
```

**Important:** 
- Always creates **complete 4-sided closed rectangle**
- Cursor ends rotated 90° right from starting orientation
- Cannot create openings or passages - always closes loop

### ibox() Pattern

From standard.h lines 107-112:
```wl
ibox(floor,ceil,light,x,y) {
  right(y)         -- Traverses BACKWARDS (clockwise from outside)
  left(x)
  left(y)
  left(x)
  innerleftsector(floor,ceil,light)  -- Assigns inner sector
  turnaround
}
```

**Used for:** Platforms, pillars, or inset areas within existing sector

## Door Implementation - The Complete Pattern

### Door Requirements

A functional door needs:
1. **Door sector**: Thin rectangular sector with floor == ceiling (closed)
2. **Connection**: Shared linedefs with adjacent sectors
3. **Linetype**: Special type on approaching linedef (usually DR = type 1)
4. **Textures**: BIGDOOR2 (face), DOORTRAK (sides/frame)

### Pattern from entryway.wl (lines 288-299)

```wl
movestep(-128,128)          -- Position at door location
ceil("FLAT20")              
floor("FLOOR3_3")           
unpegged                    
mid("DOORTRAK")             -- Frame texture
straight(-8)                -- Door depth (8 units)
top("BIGDOOR1")             -- Door face
left(128)                   -- Door width (128 units)
right(8)                    -- Complete rectangle
unpegged                    
rightsector(56,56,224)      -- floor=56, ceil=56 = CLOSED DOOR
```

**Key insight:** `rightsector(56,56,224)` creates door sector with **floor == ceiling**, making it closed (zero height when shut).

### Linetype Application

From entryway.wl lines 279-282:
```wl
straight(128)
top("BIGDOOR1") 
linetype(31,0)              -- D1 door type (opens once, stays open)
right(128) -- Door
linetype(0,0)               -- ALWAYS reset linetype after!
```

**Common linetypes:**
- `1`: DR - Use to open, auto-close
- `31`: D1 - Use to open, stays open  
- See lines.h for full list

### Three-Sector Architecture

```
[Approaching Area] → [Door Sector] → [Destination Area]
    (normal)          (floor=ceil)       (normal)
```

All three must share edges at boundaries.

## vanilla_conveyor.wl Pattern

Simple closed door:
```wl
testdoor(tag) {
  sectortype(0,tag)
  box(add(lowest, 32), add(lowest, 32), 160, 16, 128)
  sectortype(0,0)
  move(16)
}
```

Where `lowest = -32768` (from vanilla_conveyor.h)

**Creates:** 16 wide × 128 deep box with floor == ceiling = -32736 (closed)

## Critical Failures in Original Approach

### Why Overlapping Box Failed

```wl
-- WRONG: Creates standalone pillar
movestep(position)
box(0, 0, 160, 96, 32)  -- Draws complete 4-sided rectangle
```

**Problem:** 
- Box draws all 4 edges as linedefs
- Creates separate sector not integrated with lawn/room boundaries  
- Player can walk around it because it's not blocking the passage
- Appears as "free-standing pillar" or "walkable-around narrow area"

### Why Simple Box Cannot Work

`box()` **always** creates complete closed loop. Cannot create passage/opening because:
1. All 4 sides are drawn
2. `rightsector()` assigns interior
3. No shared edges with adjacent sectors
4. No way to create "gap" in boundary

## Correct Implementation Strategy

### Option A: Sequential Connected Boxes

Draw three sectors that share edges:

```wl
!mark
box(f1,c1,l1, w1,h1)      -- Sector 1

^mark
movestep(w1, 0)           -- Position for sector 2 (sharing edge)
box(f2,c2,l2, w2,h1)      -- Sector 2 (same h aligns edges)

^mark  
movestep(add(w1,w2), 0)   -- Position for sector 3
box(f3,c3,l3, w3,h1)      -- Sector 3
```

If middle sector has f2==c2, it's a door!

### Option B: Manual Linedef Drawing

Don't use `box()` - draw linedefs with `step()` and `straight()`:

```wl
-- Lawn with gap for door
straight(512)                          -- South edge
right(sub(div(512,2), div(128,2)))    -- East edge up to gap
-- GAP: don't draw here!
movestep(0, 128)                       -- Skip gap
right(sub(div(512,2), div(128,2)))    -- East edge after gap
right(512)                             -- North edge
right(512)                             -- West edge
rightsector(0, 128, 160)              -- Create lawn

-- Door fills the gap
^mark_gap_position
straight(8)         -- Door depth
left(128)           -- Door width
right(8)            -- Back edge
right(128)          -- Bottom (shares edge with lawn)
rightsector(0, 0, 160)  -- Closed door

-- Room beyond door
movestep(8, 0)
box(0, 128, 160, 256, 256)
```

## Helper Functions Worth Using

### From standard.h:
- `pushpop(x)`: Execute x, restore position
- `movestep(f,r)`: Move without drawing  
- `move(n)`: Move n forward without drawing
- `twice(x)`, `triple(x)`, `quad(x)`: Repeat x
- `for(from,to,body)`: Loop construct

### From basic.h:
- `place(s,r,x)`: Execute x at offset position, then restore
- `seg(wall)`: Generic corridor segment builder  
- `stairs(steps,tex,up)`: Staircase generator

## Texture Management

**Setting textures:**
```wl
floor("GRASS1")      -- Floor flat
ceil("F_SKY1")       -- Ceiling flat  
mid("DOORTRAK")      -- Middle texture (both sides)
top("BIGDOOR2")      -- Upper texture
bot("STEP2")         -- Lower texture
wall("TEXTURE")      -- Sets mid, top, bot together
```

**Texture offsets:**
```wl
xoff(offset)         -- Horizontal offset
yoff(offset)         -- Vertical offset
undefx               -- Use world-coordinate auto-alignment
```

**Texture behaviors:**
```wl
unpegged             -- Toggle upper/lower unpegged
midtex               -- Toggle mid-texture on 2-sided lines
```

## Common Patterns

### Player Start:
```wl
pushpop(movestep(x,y) thing)  -- Place at offset, restore cursor
```

### Inner Platform:
```wl
pushpop(
  movestep(x,y)
  ibox(raised_floor, ceiling, light, w, h)
)
```

### Tagged Sector:
```wl
sectortype(special, tag)
box(f,c,l,w,h)
sectortype(0,0)  -- Reset
```

### Tagged Line:
```wl
linetype(special, tag)
straight(length)
linetype(0,0)  -- Reset
```

## Next Steps for Implementation

1. ✅ **Complete**: Deep study of examples and documentation
2. **Next**: Implement Approach B (manual linedef drawing with gap)
3. Test minimal lawn → door → room
4. Verify door functionality in-game
5. Extract working pattern into reusable function
6. Expand to full H9 hostel layout with multiple rooms/doors
7. Add corridors, bathrooms, mess hall per original design

## Key Takeaways

1. **Doors are sectors**, not line decorations or objects
2. **Floor == Ceiling** makes door closed
3. **Shared edges** connect sectors - crucial for passages
4. **box() always closes** - cannot create openings
5. **Manual drawing** required for complex connectivity
6. **Cursor state** (position + orientation) must be carefully tracked
7. **Always reset** linetypes, sectortypes after special lines
8. **Position restoration** with `!name` and `^name` is essential

## Resources Created

- `ANALYSIS.md`: Problem diagnosis and root cause
- `DOOR_PATTERN.md`: Three-sector architecture explanation  
- `COMPLETE_DOOR_GUIDE.md`: Implementation guide with code
- `STUDY_SUMMARY.md`: This comprehensive reference (current file)
