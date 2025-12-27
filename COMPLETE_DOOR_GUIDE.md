# Complete WadC Door Implementation Guide

## The Full Pattern - Entryway.wl Analysis

### Door Sector from entryway.wl (lines 288-299)

```wl
movestep(-128,128)          -- Position cursor at door location
ceil("FLAT20")              -- Set ceiling texture
floor("FLOOR3_3")           -- Set floor texture
unpegged                    -- Set texture behavior
mid("DOORTRAK")             -- Door frame texture (sides)
straight(-8)                -- Draw 8 units forward (door thickness/depth)
top("BIGDOOR1")             -- Door face texture
left(128)                   -- Draw 128 units left (door width)  
right(8)                    -- Draw 8 units right (complete rectangle)
unpegged                    -- Reset unpegged
rightsector(56,56,224)      -- Create sector: floor=56, ceil=56 = CLOSED DOOR
```

**Key Properties:**
- Door sector dimensions: 8 units thick × 128 units wide
- Floor height = Ceiling height = 56 (CLOSED - zero internal height)
- This creates a small rectangular sector
- The sector itself IS the door

### How Linetype Makes It Work

The door sector exists, but where's the linetype(1,0)? Look at lines 279-282:

```wl
straight(128)
top("BIGDOOR1") 
linetype(31,0)              -- Line type 31 = D1 (door opens once, stays open)
right(128) -- Door
linetype(0,0)
```

This is applied to an ADJACENT sector that connects TO the door! The linetype marks which linedef triggers the door action.

## The Complete Three-Sector Architecture

```
Corridor Sector                  Door Sector            Room Sector
(floor=56, ceil=128)             (floor=56, ceil=56)    (floor=56, ceil=152)

+----------------------------+   +--------+             +------------------+
|                            |   |        |             |                  |
|                            |   |        |             |                  |
|                            +---+        +-------------+                  |
|                                                                          |
+----------------------------+   +--------+             +------------------+
      Linedef with                  Door                    Room
      linetype(31,0)               AnimatesHere             Normal sector
```

### Drawing Sequence:

1. **Draw Corridor** - normal sector connecting to door
2. **Draw Door Sector** - thin rectangle, floor=ceil
3. **Draw Room** - normal sector on other side
4. **Apply linetype** to linedef between corridor and door

## Simplified Pattern for Our Hostel

### What We Need:
- Lawn (outdoor): 512×512, floor=0, ceil=128
- Door: 8 thick × 128 wide, floor=0, ceil=0 (closed)
- Room: 256×256, floor=0, ceil=128

### Implementation Strategy:

```wl
#"standard.h"
#"doom.h"

main {
  !start
  
  -- === LAWN (Outdoor area) ===
  floor("GRASS1")
  ceil("F_SKY1")
  box(0, 128, 160, 512, 512)
  
  -- === DOOR (Positioned on east edge of lawn) ===
  -- After box(), cursor is at starting corner facing east
  -- box() calls rotright at end, so we're now facing north
  
  ^start
  rotright  -- Face east
  movestep(512, sub(div(512,2), div(128,2)))  -- Move to door position
  
  -- Draw door sector (8 deep × 128 wide, CLOSED)
  floor("FLOOR0_1")
  ceil("CEIL1_1")
  mid("DOORTRAK")
  top("BIGDOOR2")
  
  straight(8)        -- Door thickness
  left(128)          -- Door width  
  right(8)           -- Back edge
  right(128)         -- Bottom edge (completes rectangle)
  
  rightsector(0, 0, 160)  -- floor=ceil=0 = CLOSED
  
  -- Mark the entrance linedef with door type
  turnaround         -- Face back toward lawn
  linetype(1, 0)     -- DR = Use to open, auto close
  straight(8)        -- Redraw entrance edge with linetype
  linetype(0, 0)     -- Reset
  
  -- === ROOM (Beyond the door) ===
  turnaround         -- Face east again
  movestep(8, 0)     -- Move past door
  
  floor("FLOOR0_1")
  ceil("CEIL1_1")
  box(0, 128, 160, 256, 256)
  
  -- === PLAYER START ===
  ^start
  pushpop(movestep(256, 256) thing)
}
```

### Key Corrections from Previous Attempts:

1. **Position matters**: Must position at exact edge where sectors should connect
2. **Rotation matters**: After `box()`, cursor rotates 90° right
3. **Shared edges**: Door sector must share edges with both lawn and room
4. **Linetype placement**: Apply `linetype(1,0)` to the linedef facing the direction you approach from
5. **Floor=Ceiling**: Door sector MUST have floor==ceiling to be closed

## Testing Checklist

When compiled and loaded:
- [ ] Can see lawn (grass floor, sky ceiling)  
- [ ] Can see room entrance (door visible from lawn)
- [ ] Door texture shows BIGDOOR2
- [ ] Door sides show DOORTRAK
- [ ] Door blocks passage when closed
- [ ] Pressing Use (E) near door makes it open
- [ ] Can walk through when open
- [ ] Room visible beyond door
- [ ] Room has proper indoor textures

## References

- **entryway.wl**: Lines 279-315 show complete door pattern
- **vanilla_conveyor.wl**: testdoor() shows floor=ceil pattern
- **reference.adoc**: Lines 498-527 explain rightsector/leftsector
- **standard.h**: Lines 95-105 show box() implementation

## Common Pitfalls

1. ❌ Using `box()` for door creates standalone 4-sided sector (pillar)
2. ❌ Overlapping boxes creates sidedef conflicts
3. ❌ Forgetting to set floor=ceiling makes "open" door
4. ❌ Wrong linetype placement - must be on approaching side
5. ❌ Not resetting linetype with `linetype(0,0)` after door
6. ❌ Incorrect orientation after `box()` - always rotates right
7. ❌ Not using shared edges - creates gaps/disconnected geometry
