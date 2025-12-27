#"standard.h"

main {
  -- Draw a first box, then try to attach a second box sharing an edge.
  box(0, 128, 160, 64, 64)

  -- Move "forward" by 64 units and draw another box.
  movestep(64, 0)
  box(0, 128, 160, 64, 64)
}
