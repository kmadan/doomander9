#"standard.h"
#"doom.h"

-- vanilla_conveyor.wl pattern: box() then move() to advance cursor

main {
  -- Player start
  pushpop(movestep(64, 64) thing)
  
  -- Corridor
  floor("FLAT1")
  ceil("CEIL1_1")
  box(0, 128, 160, 256, 256)
  move(256)  -- Advance cursor forward 256 units
  
  -- Door
  mid("DOORTRAK")
  top("BIGDOOR2")
  linetype(1, 0)
  box(0, 0, 160, 16, 256)  -- Closed door
  linetype(0, 0)
  move(16)  -- Advance cursor forward 16 units
  
  -- Room
  floor("FLOOR0_1")
  ceil("CEIL1_1")
  box(0, 128, 160, 256, 256)
}
