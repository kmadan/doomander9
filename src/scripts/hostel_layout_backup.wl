#"standard.h"

-- Basic dimensions
room_w { 128 }
room_d { 128 }
bath_w { 256 }
corr_w { 64 }
lawn_w { 1800 }

-- Door slab thickness (east-west)
door_d { 16 }

main {
  set("door_tag", 10)

  -- Player Start (in the lawn)
  pushpop(
    movestep(256, 0)
    thing
  )

  -- Central Lawn
  pushpop(
    movestep(0, sub(0, 256))
    ceil("F_SKY1")
    floor("GRASS1")
    box(0, 512, 192, lawn_w, 640)
  )

  -- North Wing (Top)
  pushpop(
    movestep(0, 384) -- Top edge of lawn

    -- Corridor
    pushpop(
      floor("FLOOR0_1") 
      ceil("CEIL1_1")
      box(0, 128, 160, lawn_w, corr_w)
    )

    -- Rooms (Above corridor)
    -- Leave space for a door sector between corridor and rooms
    movestep(0, add(corr_w, door_d))
    wing_north
  )

  -- South Wing (Bottom)
  pushpop(
    movestep(0, sub(0, 256)) -- Bottom edge of lawn

    -- Corridor (Below lawn edge, so move down first)
    movestep(0, sub(0, corr_w))
    pushpop(
      floor("FLOOR0_1") 
      ceil("CEIL1_1")
      box(0, 128, 160, lawn_w, corr_w)
    )

    -- Rooms (Below corridor)
    -- Leave space for a door sector between corridor and rooms
    movestep(0, sub(0, add(room_d, door_d)))
    wing_south
  )

  -- Mess Hall (simple open connection for now)
  pushpop(
    movestep(lawn_w, sub(0, 64)) -- Right side of lawn

    -- Connecting corridor/doorway stub
    box(0, 128, 160, 32, 256)

    -- The Hall itself
    movestep(32, sub(0, 64))
    box(0, 160, 160, 512, 384)
  )
}

wing_north {
  -- Left block
  room_n movestep(room_w, 0)
  room_n movestep(room_w, 0)
  room_n movestep(room_w, 0)
  room_n movestep(room_w, 0)
  room_n movestep(room_w, 0)
  room_n movestep(room_w, 0)

  -- Bathroom
  bathroom_west movestep(bath_w, 0)

  -- Right block
  room_n movestep(room_w, 0)
  room_n movestep(room_w, 0)
  room_n movestep(room_w, 0)
  room_n movestep(room_w, 0)
  room_n movestep(room_w, 0)
  room_n movestep(room_w, 0)
}

wing_south {
  -- Left block
  room_s movestep(room_w, 0)
  room_s movestep(room_w, 0)
  room_s movestep(room_w, 0)
  room_s movestep(room_w, 0)
  room_s movestep(room_w, 0)
  room_s movestep(room_w, 0)

  -- Bathroom
  bathroom_east movestep(bath_w, 0)
}

room_n {
  pushpop(
    box(0, 128, 160, room_w, room_d)

    -- Simple door sector between corridor (west) and this room (east)
    -- Room width is room_w (north-south). Center a 64-wide door.
    pushpop(
      movestep(32, sub(0, door_d))
      make_door(64)
    )
  )
}

room_s {
  pushpop(
    box(0, 128, 160, room_w, room_d)

    -- Simple door sector between corridor (east) and this room (west)
    pushpop(
      movestep(32, room_d)
      make_door(64)
    )
  )
}

bathroom_west {
  pushpop(
    box(0, 128, 160, bath_w, room_d)

    pushpop(
      movestep(96, sub(0, door_d))
      make_door(64)
    )
  )
}

bathroom_east {
  pushpop(
    box(0, 128, 160, bath_w, room_d)

    pushpop(
      movestep(96, room_d)
      make_door(64)
    )
  )
}

-- Create a vertical door sector of width w (north-south) and thickness door_d (east-west).
-- Uses an incrementing sector tag so each door can be operated independently.
make_door(w) {
  set("t", get("door_tag"))
  inc("door_tag", 1)
  wall("BIGDOOR2")
  typesector(0, get("t"),
    typeline(1, get("t"),
      box(0, 0, 160, w, door_d)
    )
  )
}
