from __future__ import annotations

import os
import re
import sys
from collections import Counter
from typing import Any, Iterable, Mapping, Optional, Protocol, TypedDict, TypeVar, cast


class _Lump(Protocol):
    data: bytes


SectorInfo = tuple[
    Optional[str],
    Optional[str],
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[str],
    Optional[str],
]


class SidedefInfo(TypedDict):
    texturemiddle: Optional[str]
    texturetop: Optional[str]
    texturebottom: Optional[str]
    sector: Optional[int]


LinedefArgs = tuple[int, int, int, int, int]
LinedefInfo = tuple[int, LinedefArgs, Optional[int], int]


class LinedefFull(TypedDict):
    id: Optional[int]
    special: int
    args: LinedefArgs
    flags: int
    sidefront: Optional[int]
    sideback: Optional[int]
    v1: Optional[int]
    v2: Optional[int]


class PortalSample(TypedDict, total=False):
    id: Optional[int]
    special: int
    args: LinedefArgs
    flags: int
    sidefront: Optional[int]
    sideback: Optional[int]
    two_sided: bool
    v1: Optional[int]
    v2: Optional[int]
    x1: float
    y1: float
    x2: float
    y2: float


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    wad_path = os.path.join(repo_root, "build", "py_hostel_full.wad")

    sys.path.append(os.path.join(repo_root, "tools", "omgifol"))
    from omg import WAD  # type: ignore

    # `omgifol` ships without type hints; isolate it behind `Any`/casts.
    w: Any = WAD(wad_path)
    udmfmaps: Mapping[str, Mapping[str, _Lump]] = cast(Mapping[str, Mapping[str, _Lump]], getattr(w, "udmfmaps", {}))

    if not udmfmaps:
        print("No UDMF maps found in:", wad_path)
        return 1

    mapname: str = next(iter(udmfmaps.keys()))
    textmap = udmfmaps[mapname].get("TEXTMAP")
    if not textmap:
        print("UDMF map is missing TEXTMAP in:", wad_path)
        return 1

    text: str = textmap.data.decode("utf-8", errors="replace")

    print("WAD:", wad_path)
    print("UDMF map:", mapname)

    suspects = []
    for key in [
        "fadecolor",
        "colormap",
        "fogdensity",
        "lightmode",
        "lightlevel",
        "special",
        "damageamount",
        "damagetype",
        "renderstyle",
        "alpha",
    ]:
        if key in text:
            suspects.append(key)
    print("Contains keys:", suspects)

    sectors: list[SectorInfo] = []

    def get_str(block: str, k: str) -> Optional[str]:
        m = re.search(rf"\b{k}\s*=\s*\"([^\"]*)\"\s*;", block)
        return m.group(1) if m else None

    def get_int(block: str, k: str) -> Optional[int]:
        m = re.search(rf"\b{k}\s*=\s*(-?\d+)\s*;", block)
        return int(m.group(1)) if m else None

    # UDMF blocks are typically written like:
    #   sector // 123
    #   {
    #     ...
    #   }
    # Important: avoid matching `sector = 0;` (a sidedef property).
    sector_pat = re.compile(r"(?ms)^\s*sector\b[^\r\n]*\r?\n\{(.*?)\r?\n\}")
    for m in sector_pat.finditer(text):
        block = m.group(1)
        floor_tex = get_str(block, "texturefloor")
        ceil_tex = get_str(block, "textureceiling")
        light = get_int(block, "lightlevel")
        zf = get_int(block, "heightfloor")
        zc = get_int(block, "heightceiling")
        sec_id = get_int(block, "id")  # sector tag in UDMF
        special = get_int(block, "special")
        fade = get_str(block, "fadecolor")
        cmap = get_str(block, "colormap")
        sectors.append((floor_tex, ceil_tex, light, zf, zc, sec_id, special, fade, cmap))

    print("Total sectors:", len(sectors))

    T = TypeVar("T")

    def summarize(label: str, items: Iterable[T]) -> None:
        items_list = list(items)
        print(f"{label}: {len(items_list)}")
        for row in items_list[:20]:
            print(" ", row)

    # Texture names can vary in case depending on tooling; treat floor texture checks case-insensitively.
    def norm_tex(v: str | None) -> str:
        return (v or "").strip().upper()

    py = [s for s in sectors if norm_tex(s[0]) == "PYGRASS"]
    print("PYGRASS sectors:", len(py))

    summarize("PYGRASS with lightlevel<=32", [s for s in py if (s[2] is not None and s[2] <= 32)])
    summarize("Any sectors with fadecolor/colormap", [s for s in sectors if (s[7] or s[8])])
    summarize("Any sectors with lightlevel==0", [s for s in sectors if s[2] == 0])
    summarize("Any sectors with ceiling <= 50", [s for s in sectors if (s[4] is not None and s[4] <= 50)])

    # Sanity: sectors with non-positive height (floor >= ceiling) can cause severe render issues.
    bad_heights = [
        (i, s)
        for i, s in enumerate(sectors)
        if (s[3] is not None and s[4] is not None and s[3] >= s[4])
    ]
    summarize("Any sectors with floor >= ceiling", bad_heights)

    # Lawn ceiling sanity: all outdoor grass sectors should have F_SKY1 ceilings and a decent height.
    py_ceil = Counter(norm_tex(s[1]) for s in py)
    py_zc = Counter(s[4] for s in py)
    print("PYGRASS ceiling textures:")
    for tex, cnt in py_ceil.most_common(10):
        print(f"  {cnt:4d} {tex}")
    print("PYGRASS ceiling heights:")
    for z, cnt in py_zc.most_common(10):
        print(f"  {cnt:4d} {z}")

    sector_specials = Counter((s[6] or 0) for s in sectors)
    print("Sector specials present:")
    for sp, cnt in sector_specials.most_common(10):
        print(f"  {cnt:4d} special={sp}")

    lawn_specials = Counter((s[6] or 0) for s in py)
    if py:
        print("PYGRASS sector specials:")
        for sp, cnt in lawn_specials.most_common(10):
            print(f"  {cnt:4d} special={sp}")

    # Show floor texture distribution to spot if lawns are using a different flat than expected.
    floor_textures = [norm_tex(s[0]) for s in sectors]
    print("Unique floor textures:", len(set(floor_textures)))
    grass_like = sorted({t for t in floor_textures if "GRASS" in t})
    print("Grass-like floor textures:", grass_like)
    print("Top 15 floor textures:")
    for tex, cnt in Counter(floor_textures).most_common(15):
        print(f"  {cnt:4d} {tex}")

    # Scan sidedefs for empty texture strings (""), which can produce weird visuals.
    empty_tex = 0
    sidedef_pat = re.compile(r"(?ms)^\s*sidedef\b[^\r\n]*\r?\n\{(.*?)\r?\n\}")
    sidedefs: list[SidedefInfo] = []
    for m in sidedef_pat.finditer(text):
        block = m.group(1)
        tex_mid = get_str(block, "texturemiddle")
        tex_top = get_str(block, "texturetop")
        tex_bot = get_str(block, "texturebottom")
        sec = get_int(block, "sector")
        sidedef: SidedefInfo = {
            "texturemiddle": tex_mid,
            "texturetop": tex_top,
            "texturebottom": tex_bot,
            "sector": sec,
        }
        sidedefs.append(sidedef)
        for k in ["texturetop", "texturemiddle", "texturebottom"]:
            if re.search(rf"\b{k}\s*=\s*\"\"\s*;", block):
                empty_tex += 1
    print('Empty texture fields count (""):', empty_tex)

    # Parse vertices so we can locate portal linedefs in world space.
    vertex_pat = re.compile(r"(?ms)^\s*vertex\b[^\r\n]*\r?\n\{(.*?)\r?\n\}")
    vertices: list[tuple[float, float]] = []
    for m in vertex_pat.finditer(text):
        block = m.group(1)
        mx = re.search(r"\bx\s*=\s*([-0-9.]+)\s*;", block)
        my = re.search(r"\by\s*=\s*([-0-9.]+)\s*;", block)
        if not (mx and my):
            continue
        vertices.append((float(mx.group(1)), float(my.group(1))))

    # Analyze linedef specials (3D floors / portals live here, not in sectors).
    linedef_pat = re.compile(r"(?ms)^\s*linedef\b[^\r\n]*\r?\n\{(.*?)\r?\n\}")
    linedefs: list[LinedefInfo] = []
    linedefs_full: list[LinedefFull] = []
    hom_prone = 0
    hom_samples: list[dict[str, Any]] = []
    portal_samples: list[PortalSample] = []
    for m in linedef_pat.finditer(text):
        block = m.group(1)
        special = get_int(block, "special") or 0
        args: LinedefArgs = tuple((get_int(block, f"arg{i}") or 0) for i in range(5))  # type: ignore[assignment]
        lid = get_int(block, "id")
        flags = get_int(block, "flags") or 0
        sf = get_int(block, "sidefront")
        sb = get_int(block, "sideback")
        v1 = get_int(block, "v1")
        v2 = get_int(block, "v2")
        linedefs.append((special, args, lid, flags))
        linedef_full: LinedefFull = {
            "id": lid,
            "special": special,
            "args": args,
            "flags": flags,
            "sidefront": sf,
            "sideback": sb,
            "v1": v1,
            "v2": v2,
        }
        linedefs_full.append(linedef_full)

        # Capture portals (Line_SetPortal) locations.
        if special == 156 and len(portal_samples) < 50:
            entry: PortalSample = {
                "id": lid,
                "special": special,
                "args": args,
                "flags": flags,
                "sidefront": sf,
                "sideback": sb,
                "two_sided": (sb is not None and sb != -1),
                "v1": v1,
                "v2": v2,
            }
            if v1 is not None and v2 is not None and 0 <= v1 < len(vertices) and 0 <= v2 < len(vertices):
                (x1, y1) = vertices[v1]
                (x2, y2) = vertices[v2]
                entry.update({"x1": x1, "y1": y1, "x2": x2, "y2": y2})
            portal_samples.append(entry)

        # HOM detector: one-sided linedef (no sideback) with missing mid texture.
        # In UDMF, missing sideback is typically absent or -1.
        if sf is not None and (sb is None or sb == -1):
            if 0 <= sf < len(sidedefs):
                mid = (sidedefs[sf].get("texturemiddle") or "").strip()
                if mid in ("", "-"):
                    hom_prone += 1
                    if len(hom_samples) < 25:
                        hom_samples.append({
                            "linedef_id": lid,
                            "special": special,
                            "sidefront": sf,
                            "midtex": mid,
                            "sector": sidedefs[sf].get("sector"),
                        })

    nonzero = [ld for ld in linedefs if ld[0] != 0]
    print("Total linedefs:", len(linedefs))
    print("Linedefs with special!=0:", len(nonzero))

    specials = Counter(ld[0] for ld in nonzero)
    print("Top linedef specials:")
    for sp, cnt in specials.most_common(15):
        print(f"  {cnt:4d} special={sp}")
    print("All linedef specials present:")
    for sp in sorted(specials.keys()):
        print(f"  {specials[sp]:4d} special={sp}")

    # Flag any nonzero specials that target tag 0 (arg0==0). This is a common mistake
    # that can unintentionally affect many sectors (including outdoor lawns).
    bad_arg0 = [ld for ld in nonzero if ld[1][0] == 0]
    print("Nonzero specials with arg0==0:", len(bad_arg0))
    for sp, args, lid, flags in bad_arg0[:20]:
        print(" ", {"special": sp, "args": args, "id": lid, "flags": flags})

    if portal_samples:
        portal_count = len([p for p in portal_samples if p.get("special") == 156])
        print("Line portals (special 156):", portal_count)

        # Portal linking sanity:
        # In many UDMF setups, Line_SetPortal arg0 is the destination line id.
        # Validate that each portal line points to another portal line, ideally bidirectionally.
        by_line_id: dict[int, PortalSample] = {int(p["id"]): p for p in portal_samples if p.get("id") is not None}
        bad_links: list[dict[str, Any]] = []
        for lid, p in sorted(by_line_id.items()):
            target = int(p.get("args", (0, 0, 0, 0, 0))[0])
            if target not in by_line_id:
                bad_links.append({"line": lid, "target": target, "reason": "missing target"})
                continue
            back = int(by_line_id[target].get("args", (0, 0, 0, 0, 0))[0])
            if back != lid:
                bad_links.append({"line": lid, "target": target, "reason": f"non-bidirectional (target arg0={back})"})

        if bad_links:
            print("Portal link issues (lineid -> arg0):")
            for row in bad_links[:50]:
                print(" ", row)

        print("First 20 portal linedefs:")
        for p in portal_samples[:20]:
            print(" ", p)

    # Build approximate sector bounding boxes by attributing each linedef's endpoints
    # to the sectors referenced by its sidedefs. This lets us locate large regions
    # like lawns by coordinates.
    sector_bboxes: dict[int, list[float]] = {}

    def _bbox_add(sec_index: int, x: float, y: float) -> None:
        bb = sector_bboxes.get(sec_index)
        if bb is None:
            sector_bboxes[sec_index] = [x, y, x, y]
        else:
            bb[0] = min(bb[0], x)
            bb[1] = min(bb[1], y)
            bb[2] = max(bb[2], x)
            bb[3] = max(bb[3], y)

    if vertices:
        for ld in linedefs_full:
            v1 = ld.get("v1")
            v2 = ld.get("v2")
            if v1 is None or v2 is None or not (0 <= v1 < len(vertices) and 0 <= v2 < len(vertices)):
                continue
            (x1, y1) = vertices[v1]
            (x2, y2) = vertices[v2]

            for side_key in ("sidefront", "sideback"):
                sref = ld.get(side_key)
                if sref is None or sref == -1 or not (0 <= sref < len(sidedefs)):
                    continue
                sec_index = sidedefs[sref].get("sector")
                if sec_index is None:
                    continue
                _bbox_add(int(sec_index), x1, y1)
                _bbox_add(int(sec_index), x2, y2)

    if sector_bboxes:
        # Print the largest grass-sector regions; these are the most likely candidates
        # for the lawn and its buffer strips.
        pygrass_sector_indices = [i for i, s in enumerate(sectors) if norm_tex(s[0]) == "PYGRASS"]
        pygrass_with_bbox = []
        for i in pygrass_sector_indices:
            bb = sector_bboxes.get(i)
            if not bb:
                continue
            w = float(bb[2] - bb[0])
            h = float(bb[3] - bb[1])
            pygrass_with_bbox.append((w * h, w, h, i, bb))

        pygrass_with_bbox.sort(reverse=True)
        if pygrass_with_bbox:
            print("PYGRASS sector bounding boxes (largest first):")
            for area, w, h, sec_index, bb in pygrass_with_bbox[:25]:
                s = sectors[sec_index]
                print(
                    " ",
                    {
                        "sector_index": sec_index,
                        "tag_id": s[5],
                        "zf": s[3],
                        "zc": s[4],
                        "w": round(w, 1),
                        "h": round(h, 1),
                        "area": round(area, 1),
                        "bbox": [round(bb[0], 1), round(bb[1], 1), round(bb[2], 1), round(bb[3], 1)],
                    },
                )

    # If there are zero-height sectors, try to locate them spatially by building bounding boxes
    # from the linedefs that reference them.
    bad_sector_indices = {i for i, _ in bad_heights}
    if bad_sector_indices and sector_bboxes:
        bboxes = {i: sector_bboxes[i] for i in bad_sector_indices if i in sector_bboxes}
        if bboxes:
            minx = min(bb[0] for bb in bboxes.values())
            miny = min(bb[1] for bb in bboxes.values())
            maxx = max(bb[2] for bb in bboxes.values())
            maxy = max(bb[3] for bb in bboxes.values())
            print("Bad-height sector bbox overall extent:", [round(minx, 1), round(miny, 1), round(maxx, 1), round(maxy, 1)])

            print("Bad-height sector bounding boxes (largest first):")
            sortable = []
            for sec_index, bb in bboxes.items():
                w = float(bb[2] - bb[0])
                h = float(bb[3] - bb[1])
                sortable.append((w * h, w, h, sec_index, bb))
            sortable.sort(reverse=True)

            for area, w, h, sec_index, bb in sortable[:50]:
                s = sectors[sec_index]
                print(" ", {
                    "sector_index": sec_index,
                    "tag_id": s[5],
                    "floor": norm_tex(s[0]),
                    "ceil": norm_tex(s[1]),
                    "zf": s[3],
                    "zc": s[4],
                    "w": round(w, 1),
                    "h": round(h, 1),
                    "area": round(area, 1),
                    "bbox": [round(bb[0], 1), round(bb[1], 1), round(bb[2], 1), round(bb[3], 1)],
                })

    # Analyze Sector 0 (Lawn) geometry
    print("\n--- Sector 0 (Lawn) Analysis ---")
    if 0 < len(sectors):
        s0 = sectors[0]
        print(f"Sector 0: {s0}")
        
        # Find all linedefs for Sector 0
        s0_lines = []
        for i, ld in enumerate(linedefs_full):
            sf_idx = ld.get("sidefront")
            sb_idx = ld.get("sideback")
            
            f = sidedefs[sf_idx] if sf_idx is not None and sf_idx != -1 else None
            b = sidedefs[sb_idx] if sb_idx is not None and sb_idx != -1 else None
            
            fs = f["sector"] if f else -1
            bs = b["sector"] if b else -1
            
            if fs == 0 or bs == 0:
                v1_idx = ld.get("v1")
                v2_idx = ld.get("v2")
                if v1_idx is not None and v2_idx is not None:
                    v1 = vertices[v1_idx]
                    v2 = vertices[v2_idx]
                    s0_lines.append({
                        "id": i,
                        "v1": (v1[0], v1[1]),
                        "v2": (v2[0], v2[1]),
                        "sides": (fs, bs),
                        "special": ld.get("special"),
                        "args": ld.get("args")
                    })
        
        print(f"Sector 0 has {len(s0_lines)} linedefs.")
        print("Linedefs inside the bounding box (excluding boundary):")
        bbox = [0.0, 0.0, 512.0, 4368.0]
        epsilon = 1.0
        for ld in s0_lines:
            # Check if line is strictly inside (not on the edge)
            # A line is on the edge if both points are on the same edge
            v1x, v1y = ld["v1"]
            v2x, v2y = ld["v2"]
            
            on_left = abs(v1x - bbox[0]) < epsilon and abs(v2x - bbox[0]) < epsilon
            on_right = abs(v1x - bbox[2]) < epsilon and abs(v2x - bbox[2]) < epsilon
            on_bottom = abs(v1y - bbox[1]) < epsilon and abs(v2y - bbox[1]) < epsilon
            on_top = abs(v1y - bbox[3]) < epsilon and abs(v2y - bbox[3]) < epsilon
            
            if not (on_left or on_right or on_bottom or on_top):
                print(f"  Internal Line {ld['id']}: {ld['v1']} -> {ld['v2']} Sides: {ld['sides']} Special: {ld['special']}")

        # Check for overlapping sectors
        print("\nChecking for overlapping sectors in Lawn area:")
        for i, bb in sector_bboxes.items():
            if i == 0: continue
            # Check intersection
            # bbox is [minx, miny, maxx, maxy]
            # Overlap if not (r1_minx > r2_maxx or r1_maxx < r2_minx or ...)
            if not (bb[0] >= bbox[2] or bb[2] <= bbox[0] or bb[1] >= bbox[3] or bb[3] <= bbox[1]):
                # Potential overlap
                # Check if it's just touching edges
                touching = (abs(bb[0] - bbox[2]) < epsilon or abs(bb[2] - bbox[0]) < epsilon or
                            abs(bb[1] - bbox[3]) < epsilon or abs(bb[3] - bbox[1]) < epsilon)
                if not touching:
                    print(f"  Sector {i} overlaps Lawn: {bb} Area: {sectors[i]}")

    print("One-sided linedefs with missing mid texture (HOM-prone):", hom_prone)
    for row in hom_samples:
        print(" ", row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
