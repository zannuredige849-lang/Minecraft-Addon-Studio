#!/usr/bin/env python3
"""Regenerate the sample 16x16 pixel-art slime texture (RGBA, hard alpha, no anti-aliasing).

Usage: python3 scripts/generate_sample_texture.py [output.png]
Requires Pillow (pip install pillow). Output defaults to the demo resource pack.
"""
import os
import sys

from PIL import Image

PALETTE = {
    ".": (0, 0, 0, 0),
    "o": (40, 110, 40, 255),
    "g": (80, 170, 70, 255),
    "l": (150, 230, 120, 255),
    "d": (25, 70, 25, 255),
    "e": (15, 15, 20, 255),
    "w": (235, 245, 235, 255),
}

ROWS = [
    "................",
    "................",
    ".....oooooo.....",
    "...oogggggggo...",
    "..ogglllggggo...",
    ".ogglwwlgggggo..",
    ".oggwwwlgggggo..",
    ".ogggggggggggo..",
    "oggggggggggggdo.",
    "oggggggggggggdo.",
    "ogggeegggeeggdo.",
    "ogggeegggeeggdo.",
    "ogggggggggggddo.",
    ".odggggggggddo..",
    "..oddddddddoo...",
    "................",
]

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(
    HERE, "..", "resource_packs", "studio_demo_rp", "textures", "entity", "pixel_slime.png"
)


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    assert all(len(r) == 16 for r in ROWS) and len(ROWS) == 16, "sample must be 16x16"
    img = Image.new("RGBA", (16, 16))
    for y, row in enumerate(ROWS):
        for x, ch in enumerate(row):
            img.putpixel((x, y), PALETTE[ch])
    img.save(out)
    print(f"wrote {os.path.normpath(out)} ({img.size[0]}x{img.size[1]} RGBA)")


if __name__ == "__main__":
    main()
