#!/usr/bin/env python3
"""Regenerate the raster favicon assets from the same geometry as favicon.svg.

Browsers never load a webfont for a favicon, so the MIZOKI3 "M" is drawn as
geometry (a stroked polyline) rather than text — identical to
``assets/img/favicon.svg``. Modern browsers take the SVG via
``<link rel="icon" type="image/svg+xml">``; the .ico exists so that bare
``GET /favicon.ico`` (crawlers, older clients, Windows) returns a real icon
instead of a 404, and the PNG covers iOS home-screen bookmarks.

Pure stdlib — no Pillow, no cairosvg. Run from the site root:

    python3 scripts/generate_favicon.py

Outputs (all committed):
    assets/img/favicon.ico          16 + 32 + 48 px, PNG-encoded ICO
    assets/img/apple-touch-icon.png 180 px
"""

from __future__ import annotations

import math
import pathlib
import struct
import zlib

OUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "assets" / "img"

# --- Brand geometry, in the 64x64 space used by favicon.svg --------------------
VIEWBOX = 64.0
BG = (0x04, 0x06, 0x0F)          # --bg-0
INK = (0xF3, 0xF5, 0xFC)         # --ink
NEXUS = (0x4C, 0xC9, 0xFF)       # --nexus
CORNER_R = 14.0
STROKE_W = 7.0
# The "M": down the left stem, into the valley, back up, down the right stem.
STROKE_PTS = [(16.0, 46.0), (16.0, 18.0), (32.0, 36.0), (48.0, 18.0), (48.0, 46.0)]
SS = 4  # supersampling factor per axis (16x coverage samples per pixel)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _mark_colour(t: float) -> tuple[int, int, int]:
    """favicon.svg's mz-mark gradient: ink until 55%, then ramp to nexus."""
    if t <= 0.55:
        return INK
    k = (t - 0.55) / 0.45
    return tuple(int(round(_lerp(INK[i], NEXUS[i], k))) for i in range(3))


def _dist_to_segment(px: float, py: float, ax: float, ay: float,
                     bx: float, by: float) -> float:
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    seg_len_sq = vx * vx + vy * vy
    t = 0.0 if seg_len_sq == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / seg_len_sq))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def _inside_rounded_rect(x: float, y: float, size: float, r: float) -> bool:
    cx = min(max(x, r), size - r)
    cy = min(max(y, r), size - r)
    return math.hypot(x - cx, y - cy) <= r or (r <= x <= size - r) or (r <= y <= size - r)


def render_rgba(size: int) -> bytes:
    """Supersampled render of the mark at `size`x`size`, returned as RGBA rows."""
    scale = VIEWBOX / size
    radius = CORNER_R / scale
    half_stroke = (STROKE_W / 2.0) / scale
    pts = [(x / scale, y / scale) for x, y in STROKE_PTS]

    rows = bytearray()
    for py in range(size):
        for px in range(size):
            plate_hits = 0
            mark_acc = [0.0, 0.0, 0.0]
            mark_hits = 0
            for sy in range(SS):
                for sx in range(SS):
                    x = px + (sx + 0.5) / SS
                    y = py + (sy + 0.5) / SS
                    if not _inside_rounded_rect(x, y, float(size), radius):
                        continue
                    plate_hits += 1
                    best = min(
                        _dist_to_segment(x, y, *pts[i], *pts[i + 1])
                        for i in range(len(pts) - 1)
                    )
                    if best <= half_stroke:
                        colour = _mark_colour(((x / size) + (y / size)) / 2.0)
                        for c in range(3):
                            mark_acc[c] += colour[c]
                        mark_hits += 1

            total = SS * SS
            alpha = int(round(255 * plate_hits / total))
            if plate_hits == 0:
                rows += bytes((0, 0, 0, 0))
                continue
            cover = mark_hits / plate_hits
            if mark_hits:
                mark = [mark_acc[c] / mark_hits for c in range(3)]
            else:
                mark = [0.0, 0.0, 0.0]
            rgb = tuple(
                int(round(_lerp(BG[c], mark[c], cover))) for c in range(3)
            )
            rows += bytes((*rgb, alpha))
    return bytes(rows)


def encode_png(size: int, rgba: bytes) -> bytes:
    raw = bytearray()
    stride = size * 4
    for y in range(size):
        raw.append(0)  # filter type 0 (None)
        raw += rgba[y * stride:(y + 1) * stride]

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def encode_ico(pngs: list[tuple[int, bytes]]) -> bytes:
    header = struct.pack("<HHH", 0, 1, len(pngs))
    offset = 6 + 16 * len(pngs)
    entries, blobs = bytearray(), bytearray()
    for size, png in pngs:
        entries += struct.pack(
            "<BBBBHHII",
            0 if size >= 256 else size, 0 if size >= 256 else size,
            0, 0, 1, 32, len(png), offset,
        )
        blobs += png
        offset += len(png)
    return header + bytes(entries) + bytes(blobs)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ico_sizes = [16, 32, 48]
    pngs = [(s, encode_png(s, render_rgba(s))) for s in ico_sizes]
    ico_path = OUT_DIR / "favicon.ico"
    ico_path.write_bytes(encode_ico(pngs))
    print(f"wrote {ico_path.name} ({', '.join(str(s) for s in ico_sizes)} px,"
          f" {ico_path.stat().st_size} bytes)")

    touch_path = OUT_DIR / "apple-touch-icon.png"
    touch_path.write_bytes(encode_png(180, render_rgba(180)))
    print(f"wrote {touch_path.name} (180 px, {touch_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
