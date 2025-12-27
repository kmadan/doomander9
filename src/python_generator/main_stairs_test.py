import os
import sys

# Add src to path to find modules
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, ".."))
if src_path not in sys.path:
    sys.path.append(src_path)

from builder import WadBuilder


def main():
    print("Initializing WadBuilder...")
    builder = WadBuilder()

    # A minimal test map to validate true stepped stairs (adjacent sectors with
    # increasing floor heights).
    #
    # Layout: a long strip of rectangular sectors. Each sector shares a full edge
    # with the next, so MapEditor.draw_sector can merge the shared linedef into a
    # two-sided boundary. Floor heights rise by 8 units per segment.
    # Make stairs narrower + steeper per request.
    seg_w = 64
    seg_h = 256
    n_steps = 7
    step_rise = 20

    base_x = 0
    base_y = 0

    # Start platform
    builder.draw_rectangle(
        base_x + 0 * seg_w,
        base_y,
        seg_w,
        seg_h,
        floor_height=0,
        ceil_height=160,
        floor_tex="FLOOR4_8",
        ceil_tex="CEIL3_5",
        wall_tex="STARTAN3",
        light=192,
    )

    # Stair run
    for i in range(1, n_steps + 1):
        builder.draw_rectangle(
            base_x + i * seg_w,
            base_y,
            seg_w,
            seg_h,
            floor_height=i * step_rise,
            ceil_height=160,
            floor_tex="FLOOR4_8",
            ceil_tex="CEIL3_5",
            wall_tex="STARTAN3",
            light=192,
        )

    # Top landing
    top_floor = (n_steps + 1) * step_rise
    builder.draw_rectangle(
        base_x + (n_steps + 1) * seg_w,
        base_y,
        seg_w,
        seg_h,
        floor_height=top_floor,
        ceil_height=160,
        floor_tex="FLOOR4_8",
        ceil_tex="CEIL3_5",
        wall_tex="STARTAN3",
        light=192,
    )

    # HUD labels (on-screen) via ZScript: place a MapSpot marker.
    builder.add_label_spot(
        x=base_x + (n_steps + 1) * seg_w + seg_w // 2,
        y=base_y + seg_h // 2,
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../build/py_stairs_test_raw.wad"))
    print(f"Saving to {output_path}...")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    builder.save(output_path)

    print("Done.")


if __name__ == "__main__":
    main()
