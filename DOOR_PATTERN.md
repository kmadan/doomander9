# WadC Door Pattern - The Correct Approach

## The Three-Sector Pattern

A working door requires THREE connected sectors:

```
  Lawn Sector          Door Sector        Room Sector
  +--------------+     +------+          +--------------+
  |              |     |      |          |              |
  |              |     |      |          |              |
  |              +-----+      +----------+              |
  |                                                     |
  |              Shared    Shared                      |
  |              Edge      Edge                        |
  +--------------+     +------+          +--------------+
```

### Sector Properties

1. **Lawn**: floor=0, ceil=128 (normal height)
2. **Door**: floor=0, ceil=0 (CLOSED - zero height), linetype=1 (DR - opens on use)
3. **Room**: floor=0, ceil=128 (normal height)

## Key WadC Concepts from Study

### box() Limitations

`box(floor, ceil, light, width, height)` expands to:
```wl
straight(width)
right(height)
right(width)
right(height)
rightsector(floor, ceil, light)
rotright
```

**Always creates a complete 4-sided closed rectangle!** Cannot be used for passages.

### Manual Sector Drawing Pattern

From `entryway.wl` analysis:

```wl
-- Start at some position
step(x1, y1)     -- Draw linedef to point 1
step(x2, y2)     -- Draw linedef to point 2
step(x3, y3)     -- etc, drawing a closed loop
rightsector(floor, ceil, light)  -- Assign right side to new sector
```

The cursor draws linedefs connecting vertices. When loop closes, `rightsector()` creates sector.

### Shared Edge Pattern

Two sectors share an edge when:
1. **Same vertices** at both endpoints of linedef
2. One sector assigned to **left** side, other to **right** side
3. Both sectors drawn in sequence from same line

Example from vanilla_conveyor.wl:
```wl
box(floor1, ceil1, light1, 128, 768)  -- Draws outer area
movestep(128, 0)  -- Move to position for next sector
box(floor2, ceil2, light2, 16, 128)   -- Door sector adjacent
```

After first `box()`, cursor is at corner. Moving and drawing next box creates **adjacent** sector.

## Three Approaches to Implement Door

### Approach A: Sequential Box Pattern (SIMPLEST)

Draw three boxes in a row:

```wl
main {
  !start
  
  -- Lawn (512x512, grass floor, sky ceiling)
  floor("GRASS1") ceil("F_SKY1")
  box(0, 128, 160, 512, 512)
  
  -- Position for door (on east edge of lawn, centered)
  ^start
  movestep(512, sub(div(512,2), div(128,2)))  -- Move to center of east edge
  
  -- Door (8 units thick, 128 wide, closed)
  floor("FLOOR0_1") ceil("CEIL1_1")
  mid("DOORTRAK") top("BIGDOOR2")
  box(0, 0, 160, 8, 128)  -- floor=ceil=0 = closed door
  
  -- Mark door as DR type (opens on use)
  ^start
  movestep(512, sub(div(512,2), div(128,2)))
  straight(8)  -- Redraw front edge
  linetype(1, 0)  -- DR door type
  linetype(0, 0)  -- Reset
  
  -- Room (256x256, indoor textures)  
  movestep(8, 0)  -- Move past door
  floor("FLOOR0_1") ceil("CEIL1_1")
  box(0, 128, 160, 256, 256)
  
  -- Player start in lawn
  ^start
  pushpop(movestep(256, 256) thing)
}
```

**Problem**: This likely still creates three SEPARATE boxes, not connected sectors.

### Approach B: Integrated Drawing (CORRECT)

Draw lawn with gap, then door, then room:

```wl
main {
  !start
  
  floor("GRASS1") ceil("F_SKY1")
  
  -- Draw lawn as manual loop with GAP for door
  straight(512)  -- South edge
  right(sub(div(512,2), div(128,2)))  -- East edge, up to door gap
  -- GAP HERE (128 units) - no linedef drawn!
  movestep(0, 128)  -- Skip over door opening
  right(sub(div(512,2), div(128,2)))  -- East edge, after door gap
  right(512)  -- North edge
  right(512)  -- West edge  
  rightsector(0, 128, 160)  -- Create lawn sector
  
  -- Now draw door sector from the gap
  ^start
  movestep(512, div(sub(512, 128), 2))  -- Position at door gap
  
  floor("FLOOR0_1") ceil("CEIL1_1")
  mid("DOORTRAK") top("BIGDOOR2")
  straight(8)  -- Door depth (thickness)
  linetype(1, 0)  -- Mark as DR door
  right(128)  -- Door width
  right(8)  -- Back face
  right(128)  -- Close the rectangle
  linetype(0, 0)  -- Reset linetype
  rightsector(0, 0, 160)  -- Closed door (floor=ceil=0)
  
  -- Draw room from other side of door
  movestep(8, 0)  -- Move past door
  floor("FLOOR0_1") ceil("CEIL1_1")  
  box(0, 128, 160, 256, 256)
  
  -- Player start
  ^start
  pushpop(movestep(256, 256) thing)
}
```

### Approach C: Study Existing Door Helper Functions

Look for WadC includes that might have door helpers:

- `#"basic.h"` - seg2(), segtrigger()
- `#"lines.h"` - door line types
- Custom door function from examples

## Next Implementation Steps

1. **Test Approach B first** - manual drawing with gap
2. Study cursor position after each drawing command with prints/debugging
3. Verify in-game that door:
   - Blocks passage when closed
   - Opens with Use key (E)
   - Has visible BIGDOOR2 texture
   - Actually connects lawn to room
4. Once working, extract into reusable `make_door_passage()` function
5. Expand to full H9 hostel layout with multiple doors

## Study References

- `entryway.wl` lines 275-315: Manual sector drawing with doors
- `vanilla_conveyor.wl` testdoor(): Simple door box
- Reference manual section on leftsector/rightsector (lines 498-527)
- Tutorial examples 8-13: ibox() for inner sectors
