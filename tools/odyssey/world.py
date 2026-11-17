"""Build the map: the places of the film on an open sea, as a Bedrock world (.mcworld) with both packs inside.

    python3.12 -m venv .venv && .venv/bin/pip install amulet-core          # once (Amulet needs Python <= 3.12)
    .venv/bin/python -m tools.odyssey.world [--minimap docs/odyssey-map.png]  # writes dist/The_Odyssey_v<version>.mcworld

The places, and what lives in each, come from world_plan.py (the script reads the same plan). Every place is built on a
canvas (one array of block indices) with a height field, then structures and trees; the sea and the sea floor fill the rest
of the region. The world is a flat world whose layers are the same sea floor, so the sea simply goes on past the edge.
"""
import json
import math
import os
import shutil
import sys
import zipfile

import numpy as np

from . import world_plan as WP

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
Y0, Y1 = -64, 128                   # the layers kept in the arrays (nothing is built higher)
NY = Y1 - Y0
SEA_FLOOR = 39                      # top stone block of the sea floor
WATER_TOP = WP.SEA - 1              # last water block: the surface is at y = 62
FLAT_LAYERS = {"biome_id": 1, "block_layers": [
    {"block_name": "minecraft:bedrock", "count": 1}, {"block_name": "minecraft:stone", "count": SEA_FLOOR - Y0},
    {"block_name": "minecraft:water", "count": WATER_TOP - SEA_FLOOR}],
    "encoding_version": 6, "structure_options": None, "world_version": "version.post_1_18"}

# name -> (universal block name, properties)
BLOCKS = {
    "air": ("air", {}), "stone": ("stone", {}), "bedrock": ("bedrock", {}), "dirt": ("dirt", {}), "grass": ("grass_block", {}),
    "sand": ("sand", {}), "sandstone": ("sandstone", {}), "gravel": ("gravel", {}),
    "water": ("water", {"falling": "false", "level": "0"}),
    "cobble": ("cobblestone", {}), "mossy_cobble": ("mossy_cobblestone", {}), "bricks": ("stone_bricks", {}),
    "mossy_bricks": ("mossy_stone_bricks", {}), "andesite": ("andesite", {}), "polished_andesite": ("polished_andesite", {}),
    "smooth_stone": ("smooth_stone", {}), "planks": ("oak_planks", {}), "spruce_planks": ("spruce_planks", {}),
    "log": ("oak_log", {"axis": "y"}), "spruce_log": ("spruce_log", {"axis": "y"}), "dark_log": ("dark_oak_log", {"axis": "y"}),
    "leaves": ("oak_leaves", {"persistent": "true"}), "spruce_leaves": ("spruce_leaves", {"persistent": "true"}),
    "hay": ("hay_block", {"axis": "y"}), "fence": ("oak_fence", {}), "lodestone": ("lodestone", {}),
    "soul_soil": ("soul_soil", {}), "soul_sand": ("soul_sand", {}), "black_powder": ("black_concrete_powder", {}),
    "glowstone": ("glowstone", {}), "quartz": ("quartz_block", {}), "smooth_quartz": ("smooth_quartz", {}),
    "quartz_pillar": ("quartz_pillar", {"axis": "y"}), "podzol": ("podzol", {}), "dandelion": ("dandelion", {}),
    "poppy": ("poppy", {}), "terracotta": ("terracotta", {}), "tuff": ("tuff", {}), "calcite": ("calcite", {}),
    "white_concrete": ("white_concrete", {}),
}
# Blocks Amulet's universal format has no plain name for are given the way its Bedrock translator knows them
# (namespace, name, properties); an untranslated block would be written as an unknown block and show up as dirt.
SPECIAL = {
    "planks": ("minecraft", "planks", {"wood_type": "oak"}),
    "spruce_planks": ("minecraft", "planks", {"wood_type": "spruce"}),
    "log": ("universal_minecraft", "log", {"axis": "y", "material": "oak", "stripped": "false"}),
    "spruce_log": ("universal_minecraft", "log", {"axis": "y", "material": "spruce", "stripped": "false"}),
    "dark_log": ("universal_minecraft", "log", {"axis": "y", "material": "dark_oak", "stripped": "false"}),
    "leaves": ("minecraft", "leaves", {"old_leaf_type": "oak", "persistent_bit": "1", "update_bit": "0"}),
    "spruce_leaves": ("minecraft", "leaves", {"old_leaf_type": "spruce", "persistent_bit": "1", "update_bit": "0"}),
    "fence": ("universal_minecraft", "fence", {"material": "oak", "east": "false", "north": "false", "south": "false", "west": "false"}),
    "black_powder": ("minecraft", "concrete_powder", {"color": "black"}),
    "white_concrete": ("minecraft", "concrete", {"color": "white"}),
    "dandelion": ("universal_minecraft", "plant", {"plant_type": "dandelion"}),
    "poppy": ("minecraft", "red_flower", {"flower_type": "poppy"}),
    "mossy_bricks": ("universal_minecraft", "stone_bricks", {"variant": "mossy"}),
}
BLOCKS.pop("polished_andesite", None)
NAMES = list(BLOCKS)
IDX = {n: i for i, n in enumerate(NAMES)}
MAP_COLORS = {"water": (40, 90, 150), "sand": (226, 214, 156), "grass": (92, 140, 70), "stone": (130, 130, 130),
              "black_powder": (30, 30, 34), "gravel": (110, 106, 100), "bricks": (150, 150, 140), "planks": (170, 130, 80),
              "andesite": (140, 140, 138), "spruce_leaves": (40, 80, 50), "leaves": (60, 120, 50), "hay": (200, 170, 60),
              "quartz": (236, 232, 224), "lodestone": (255, 80, 80), "glowstone": (255, 230, 120), "soul_soil": (70, 56, 46),
              "dark_log": (60, 40, 25), "log": (110, 82, 48), "spruce_log": (80, 56, 34), "cobble": (120, 120, 120),
              "tuff": (110, 110, 100), "dirt": (120, 86, 60), "fence": (150, 110, 70), "mossy_bricks": (110, 130, 100),
              "smooth_stone": (170, 170, 170), "smooth_quartz": (230, 226, 218), "quartz_pillar": (228, 224, 216),
              "spruce_planks": (110, 80, 50), "white_concrete": (240, 240, 240), "air": (0, 0, 0)}


def smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


class Canvas:
    """The blocks of one place: a (W, NY, D) array of palette indices over chunk-aligned world bounds."""

    def __init__(self, plan, margin=44, seed=1):
        self.p = plan
        self.cx, self.cz, self.r = plan["x"], plan["z"], plan["r"]
        half = self.r + margin
        self.x0 = (self.cx - half) // 16 * 16
        self.x1 = ((self.cx + half) // 16 + 1) * 16
        self.z0 = (self.cz - half) // 16 * 16
        self.z1 = ((self.cz + half) // 16 + 1) * 16
        self.W, self.D = self.x1 - self.x0, self.z1 - self.z0
        self.a = np.full((self.W, NY, self.D), IDX["air"], np.uint8)
        self.X, self.Z = np.meshgrid(np.arange(self.x0, self.x1), np.arange(self.z0, self.z1), indexing="ij")
        self.H = np.full((self.W, self.D), SEA_FLOOR, int)
        self.rng = np.random.default_rng(seed)
        self.phase = self.rng.uniform(0, 6.28, 8)
        self.keep_clear = []                      # (x, z, radius): no trees there

    # ---- coordinates
    def ix(self, x): return x - self.x0
    def iz(self, z): return z - self.z0
    def iy(self, y): return y - Y0

    def ground(self, x, z):
        return int(self.H[self.ix(x), self.iz(z)])

    def inside(self, x, z):
        return self.x0 <= x < self.x1 and self.z0 <= z < self.z1

    def noise(self, scale=24.0, octaves=3):
        n = np.zeros_like(self.X, float)
        for o in range(octaves):
            k = 2.0 ** o
            n += np.sin(self.X / scale * k + self.phase[o]) * np.cos(self.Z / scale * k * 1.3 + self.phase[o + 3]) / k
        return n / 1.75

    # ---- terrain
    def island(self, R, peak, plateau, Y, ox=0, oz=0, wobble=0.12, amp=1.6, hills=2):
        """Raise a roughly round island: flat at Y inside the plateau, falling gently to the shore, with a few hills out on
        the slopes (never around the plateau, which would make it a crater), then sloping away under water to the deep
        floor so no shelf ends in a square step at the edge of the canvas."""
        dx, dz = self.X - (self.cx + ox), self.Z - (self.cz + oz)
        d, ang = np.hypot(dx, dz), np.arctan2(dz, dx)
        wob = 1 + wobble * np.sin(3 * ang + self.phase[0]) + 0.5 * wobble * np.sin(5 * ang + self.phase[1])
        de = d / wob
        coast = 0.86 * R
        prof = smooth((de - plateau) / max(coast - plateau, 1.0))
        land = Y - (Y - WATER_TOP) * prof
        lo, hi = plateau + 8, coast - 10
        bumps = np.zeros_like(d)
        if hi > lo + 6 and peak > Y:
            for _ in range(hills):
                a_, dist = self.rng.uniform(0, 6.28), self.rng.uniform(lo, hi)
                hx, hz = self.cx + ox + math.cos(a_) * dist, self.cz + oz + math.sin(a_) * dist
                hr, hh = max(10.0, (hi - lo) * 0.9), (peak - Y) * self.rng.uniform(0.6, 1.0)
                bumps = np.maximum(bumps, hh * smooth(1 - np.hypot(self.X - hx, self.Z - hz) / hr))
        inland = smooth((coast - de) / (0.25 * R)) * smooth((de - plateau) / 8.0)       # flat plateau, calm shore
        h_land = land + (bumps + self.noise(18.0) * amp) * inland
        sea = np.clip(WATER_TOP - (de - coast) * 0.55, SEA_FLOOR, WATER_TOP)
        w = smooth((de - coast) / (0.06 * R))
        h = h_land * (1 - w) + sea * w
        self.H = np.maximum(self.H, np.rint(h).astype(int))
        return d, wob

    def finish_terrain(self, top=None, sub=None, subdepth=3, under=("sand", "gravel")):
        """Fill the columns from the height field; the sea floor and anything that lies under water is sand."""
        H = self.H
        land = H >= WP.SEA
        if top is None:
            top = np.where(H <= WP.SEA + 1, IDX["sand"], IDX["grass"])
        top = np.where(land, top, np.where(H >= SEA_FLOOR + 1, IDX[under[0]], IDX[under[1]]))
        sub = np.where(land, IDX["dirt"] if sub is None else sub, np.where(H >= SEA_FLOOR + 1, IDX[under[0]], IDX[under[1]]))
        sub = np.where(land & (top == IDX["sand"]), IDX["sand"], sub)
        Y = np.arange(Y0, Y1)[None, :, None]
        Hh = H[:, None, :]
        a = np.where(Y > Hh, np.where(Y <= WATER_TOP, IDX["water"], IDX["air"]),
                     np.where(Y == Hh, top[:, None, :], np.where(Y >= Hh - subdepth, sub[:, None, :], IDX["stone"])))
        a[:, 0, :] = IDX["bedrock"]
        self.a = a.astype(np.uint8)

    # ---- painting (inclusive world coordinates)
    def _sl(self, lo, hi, off, n):
        return max(lo - off, 0), min(hi - off + 1, n)

    def box(self, x0, y0, z0, x1, y1, z1, name, only=None):
        xs, xe = self._sl(min(x0, x1), max(x0, x1), self.x0, self.W)
        ys, ye = self._sl(min(y0, y1), max(y0, y1), Y0, NY)
        zs, ze = self._sl(min(z0, z1), max(z0, z1), self.z0, self.D)
        if xs >= xe or ys >= ye or zs >= ze:
            return
        view = self.a[xs:xe, ys:ye, zs:ze]
        if only is None:
            view[:] = IDX[name]
        else:
            m = np.isin(view, [IDX[o] for o in only])
            view[m] = IDX[name]

    def set(self, x, y, z, name, only=None):
        if self.inside(x, z) and Y0 <= y < Y1:
            if only is None or self.a[self.ix(x), self.iy(y), self.iz(z)] in [IDX[o] for o in only]:
                self.a[self.ix(x), self.iy(y), self.iz(z)] = IDX[name]

    def get(self, x, y, z):
        return NAMES[self.a[self.ix(x), self.iy(y), self.iz(z)]] if self.inside(x, z) and Y0 <= y < Y1 else "air"

    def ellipsoid(self, cx, cy, cz, rx, ry, rz, name, only=None):
        xs, xe = self._sl(int(cx - rx), int(cx + rx) + 1, self.x0, self.W)
        ys, ye = self._sl(int(cy - ry), int(cy + ry) + 1, Y0, NY)
        zs, ze = self._sl(int(cz - rz), int(cz + rz) + 1, self.z0, self.D)
        if xs >= xe or ys >= ye or zs >= ze:
            return
        X = (np.arange(xs, xe) + self.x0 - cx)[:, None, None] / rx
        Y = (np.arange(ys, ye) + Y0 - cy)[None, :, None] / ry
        Z = (np.arange(zs, ze) + self.z0 - cz)[None, None, :] / rz
        m = X * X + Y * Y + Z * Z <= 1.0
        view = self.a[xs:xe, ys:ye, zs:ze]
        if only is not None:
            m &= np.isin(view, [IDX[o] for o in only])
        view[m] = IDX[name]

    def cylinder(self, cx, cz, y0, y1, r, name, only=None):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r + 1:
                    self.box(cx + dx, y0, cz + dz, cx + dx, y1, cz + dz, name, only)

    def ring(self, cx, cz, y0, y1, r, name, thick=1, gap=None):
        """A wall around (cx, cz); gap = (angle, half-width in radians) leaves an opening."""
        for ang in np.linspace(0, 2 * math.pi, int(2 * math.pi * r * 3)):
            if gap and abs((ang - gap[0] + math.pi) % (2 * math.pi) - math.pi) < gap[1]:
                continue
            for t in range(thick):
                x, z = int(round(cx + math.cos(ang) * (r + t))), int(round(cz + math.sin(ang) * (r + t)))
                self.box(x, y0, z, x, y1, z, name)

    # ---- things
    def clear(self, x, z, r):
        self.keep_clear.append((x, z, r))

    def clear_of(self, x, z, pad=0):
        return all(math.hypot(x - cx, z - cz) > r + pad for cx, cz, r in self.keep_clear)

    def tree(self, x, z, kind="oak"):
        if not self.inside(x, z) or not self.clear_of(x, z, 1):
            return False
        g = self.ground(x, z)
        if g < WP.SEA + 2 or self.get(x, g, z) not in ("grass", "dirt", "podzol", "black_powder", "soul_soil"):
            return False
        h = int(self.rng.integers(5, 8))
        if kind == "oak":
            self.box(x, g + 1, z, x, g + h, z, "log")
            self.ellipsoid(x, g + h, z, 3, 2.6, 3, "leaves", only=("air",))
            self.ellipsoid(x, g + h + 2, z, 1.8, 1.5, 1.8, "leaves", only=("air",))
        elif kind == "spruce":
            h += 3
            self.box(x, g + 1, z, x, g + h, z, "spruce_log")
            for k, r in enumerate((3, 3, 2, 2, 1)):
                y = g + h - 1 - k * 2
                self.box(x - r, y, z - r, x + r, y, z + r, "spruce_leaves", only=("air",))
            self.set(x, g + h + 1, z, "spruce_leaves", only=("air",))
        elif kind == "dead":
            self.box(x, g + 1, z, x, g + h, z, "dark_log")
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if self.rng.random() < 0.6:
                    self.box(x + dx, g + h - 1, z + dz, x + 2 * dx, g + h, z + 2 * dz, "dark_log")
        return True

    def scatter(self, n, kind, region, tries=6):
        placed = 0
        for _ in range(n * tries):
            if placed >= n:
                break
            ang, rr = self.rng.uniform(0, 6.28), math.sqrt(self.rng.uniform(0, 1)) * region[1] + region[0]
            if self.tree(int(self.cx + math.cos(ang) * rr), int(self.cz + math.sin(ang) * rr), kind):
                placed += 1

    def flowers(self, n, region):
        for _ in range(n):
            ang, rr = self.rng.uniform(0, 6.28), math.sqrt(self.rng.uniform(0, 1)) * region[1] + region[0]
            x, z = int(self.cx + math.cos(ang) * rr), int(self.cz + math.sin(ang) * rr)
            if self.inside(x, z) and self.clear_of(x, z):
                g = self.ground(x, z)
                if self.get(x, g, z) == "grass" and self.get(x, g + 1, z) == "air":
                    self.set(x, g + 1, z, "dandelion" if self.rng.random() < 0.5 else "poppy")

    def lamp(self, x, z, h=3):
        g = self.ground(x, z)
        self.box(x, g + 1, z, x, g + h, z, "bricks")
        self.set(x, g + h + 1, z, "glowstone")

    def hut(self, x0, z0, w, d, h, wall="spruce_planks", base="cobble", roof="hay", door="south", floor=True, ground=None):
        """A small house: x0, z0 the south-west corner; the door is a 2-high gap in the chosen wall."""
        g = ground if ground is not None else int(self.H[self.ix(x0): self.ix(x0) + w, self.iz(z0): self.iz(z0) + d].max())
        self.box(x0, g - 3, z0, x0 + w - 1, g, z0 + d - 1, base)
        self.box(x0, g + 1, z0, x0 + w - 1, g + h, z0 + d - 1, wall)
        self.box(x0 + 1, g + 1, z0 + 1, x0 + w - 2, g + h, z0 + d - 2, "air")
        if floor:
            self.box(x0 + 1, g, z0 + 1, x0 + w - 2, g, z0 + d - 2, "planks")
        self.box(x0 - 1, g + h + 1, z0 - 1, x0 + w, g + h + 1, z0 + d, roof)
        self.box(x0, g + h + 2, z0, x0 + w - 1, g + h + 2, z0 + d - 1, roof)
        mx, mz = x0 + w // 2, z0 + d // 2
        gate = {"south": (mx, z0), "north": (mx, z0 + d - 1), "west": (x0, mz), "east": (x0 + w - 1, mz)}[door]
        self.box(gate[0], g + 1, gate[1], gate[0], g + 2, gate[1], "air")
        for cx_, cz_ in ((x0, z0), (x0 + w - 1, z0), (x0, z0 + d - 1), (x0 + w - 1, z0 + d - 1)):
            self.box(cx_, g + 1, cz_, cx_, g + h, cz_, "log")


# ================================================================== the places
def site_ogygia(c):
    Y = c.p["y"]
    c.island(R=44, peak=71, plateau=26, Y=Y)
    c.finish_terrain()
    c.clear(c.cx, c.cz, 10); c.clear(c.cx + 7, c.cz + 5, 6)
    # the shrine: a stone dais with the lodestone that tells the script this is the map
    c.box(c.cx - 3, Y - 2, c.cz - 3, c.cx + 3, Y, c.cz + 3, "bricks")
    c.box(c.cx - 4, Y - 1, c.cz - 4, c.cx + 4, Y - 1, c.cz + 4, "cobble")
    c.set(c.cx, Y, c.cz, "lodestone")
    for sx, sz in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        c.lamp(c.cx + sx, c.cz + sz)
    # Calypso's house, a lotus pool, trees
    c.clear(c.cx + 17, c.cz + 13, 7)
    c.hut(c.cx + 14, c.cz + 10, 8, 7, 4, wall="planks", roof="hay", door="west", ground=Y)
    c.box(c.cx - 14, Y - 2, c.cz + 6, c.cx - 10, Y - 1, c.cz + 10, "water")
    c.scatter(26, "oak", (16, 24)); c.flowers(60, (6, 26))


def site_troy(c):
    Y = c.p["y"]
    c.island(R=38, peak=64, plateau=24, Y=Y, wobble=0.07, amp=0.6, hills=0)
    c.finish_terrain(top=np.full_like(c.H, IDX["sand"]), sub=IDX["sand"])
    c.clear(c.cx, c.cz, 9)
    c.box(c.cx - 6, Y - 1, c.cz - 6, c.cx + 6, Y, c.cz + 6, "planks")            # the horse's platform
    for ang in np.linspace(math.radians(200), math.radians(340), 140):          # the walls of Troy, behind the horse
        r = 31
        x, z = int(round(c.cx + math.cos(ang) * r)), int(round(c.cz + math.sin(ang) * r))
        if abs(ang - math.radians(270)) < 0.17:
            continue                                                             # the gate
        c.box(x, Y - 2, z, x + 1, Y + 10, z + 1, "bricks")
    for ang in (math.radians(200), math.radians(340)):
        x, z = int(round(c.cx + math.cos(ang) * 31)), int(round(c.cz + math.sin(ang) * 31))
        c.cylinder(x, z, Y - 2, Y + 15, 3, "bricks"); c.box(x - 1, Y + 16, z - 1, x + 1, Y + 16, z + 1, "glowstone")
    for sx, sz in ((-8, -8), (8, -8), (-8, 8), (8, 8)):
        c.lamp(c.cx + sx, c.cz + sz, 4)


def site_cyclops(c):
    Y = c.p["y"]
    c.island(R=76, peak=80, plateau=26, Y=Y, ox=18, oz=0, wobble=0.1)
    # the hill he lives in, to the west: steep sides, a high top, and a cave in its east foot
    d = np.hypot(c.X - (c.cx - 30), c.Z - c.cz)
    k = smooth((36 - d) / 12.0)
    c.H = np.maximum(c.H, np.where(k > 0, np.rint(Y + 44 * k + c.noise(16) * 1.5 * k).astype(int), 0))
    c.finish_terrain()
    gx = c.cx + 18
    c.clear(gx, c.cz, 20)
    mouth, depth = c.cx + 6, 46
    c.box(mouth - depth, Y + 1, c.cz - 6, mouth, Y + 15, c.cz + 6, "air")                       # the cave
    c.ellipsoid(mouth - depth, Y + 8, c.cz, 10, 9, 9, "air")
    c.box(mouth - depth - 8, Y, c.cz - 9, mouth + 2, Y, c.cz + 9, "stone")
    c.ellipsoid(c.cx + 11, Y + 6, c.cz + 14, 6, 6, 6, "stone", only=("air",))                  # the boulder that closes it
    for sx in (-1, 1):
        c.lamp(mouth + 3, c.cz + sx * 8, 3)
    c.ring(gx, c.cz, Y + 1, Y + 1, 14, "fence", gap=(math.pi, 0.45))                           # the sheepfold, open toward the cave
    c.scatter(14, "oak", (30, 30)); c.flowers(50, (10, 50))


def site_telepylus(c):
    Y = c.p["y"]
    c.island(R=70, peak=84, plateau=32, Y=Y, wobble=0.1, hills=5)
    d = np.hypot(c.X - (c.cx + 8), c.Z - (c.cz + 44))                                          # the harbour, cut into the south
    c.H = np.where(d < 21, np.minimum(c.H, WP.SEA - 3 + (d / 21) * 2), c.H)
    c.finish_terrain(top=np.where(c.H <= WP.SEA + 1, IDX["sand"], IDX["podzol"]), sub=IDX["dirt"])
    c.clear(c.cx, c.cz, 14)
    c.box(c.cx - 16, Y - 3, c.cz + 14, c.cx + 26, Y, c.cz + 21, "bricks")                      # the quay
    c.box(c.cx - 2, Y - 1, c.cz - 2, c.cx + 2, Y, c.cz + 2, "mossy_bricks")
    for lx in (-14, 0, 14, 24):
        c.lamp(c.cx + lx, c.cz + 13, 4)
    for hx, hz in ((-30, -4), (-24, 24), (26, -16)):                                           # houses built for giants
        c.clear(c.cx + hx + 5, c.cz + hz + 5, 9)
        c.hut(c.cx + hx, c.cz + hz, 11, 11, 9, wall="bricks", base="cobble", roof="spruce_planks", door="south",
              ground=int(c.H[c.ix(c.cx + hx + 5), c.iz(c.cz + hz + 5)]))
    c.scatter(90, "spruce", (18, 40))


def site_aeaea(c):
    Y = c.p["y"]
    c.island(R=46, peak=69, plateau=26, Y=Y, wobble=0.09, amp=1.0)
    c.finish_terrain()
    c.clear(c.cx, c.cz + 4, 8)
    c.clear(c.cx - 12, c.cz - 8, 8)
    c.hut(c.cx - 16, c.cz - 12, 9, 8, 4, wall="bricks", base="cobble", roof="hay", door="east", ground=Y)   # Circe's cottage
    c.box(c.cx - 17, Y + 5, c.cz - 12, c.cx - 17, Y + 8, c.cz - 12, "cobble")                                # chimney
    c.ring(c.cx + 10, c.cz + 6, Y + 1, Y + 1, 6, "fence", gap=(math.pi, 0.4))                                 # the pigs' pen
    c.box(c.cx - 10, Y, c.cz - 4, c.cx - 6, Y, c.cz - 4, "dirt"); c.box(c.cx - 10, Y + 1, c.cz - 4, c.cx - 6, Y + 1, c.cz - 4, "poppy")
    c.scatter(22, "oak", (22, 16)); c.flowers(80, (4, 34))


def site_hades(c):
    Y = c.p["y"]
    c.island(R=46, peak=67, plateau=26, Y=Y, wobble=0.1, amp=0.8)
    # the river Oceanus: a channel from the south sea up into the island
    ch = (np.abs(c.X - (c.cx + 22)) < 5) & (c.Z > c.cz - 6)
    c.H = np.where(ch, np.minimum(c.H, WP.SEA - 4), c.H)
    c.finish_terrain(top=np.where(c.H >= WP.SEA, IDX["black_powder"], IDX["gravel"]), sub=IDX["soul_soil"], subdepth=3)
    c.clear(c.cx - 5, c.cz + 5, 9)
    for k in range(18):                                                                         # the altar for the blood
        ang = k / 18 * 2 * math.pi
        c.box(int(c.cx - 5 + math.cos(ang) * 5), Y, int(c.cz + 5 + math.sin(ang) * 5),
              int(c.cx - 5 + math.cos(ang) * 5), Y + 1, int(c.cz + 5 + math.sin(ang) * 5), "cobble")
    c.box(c.cx - 6, Y, c.cz + 4, c.cx - 4, Y, c.cz + 6, "smooth_stone")
    c.scatter(18, "dead", (10, 34), tries=10)


def site_sirens(c):
    c.finish_terrain()
    cr = c.rng
    for _t, dx, dz in c.p["creatures"]:                                                         # the rocks they lie on
        x, z = c.cx + dx, c.cz + dz
        c.ellipsoid(x, 48, z, 11, 15.5, 11, "stone")                                           # a broad base from the sea floor
        c.cylinder(x, z, 48, 63, 6, "stone")                                                   # the pillar up to the shelf
        c.cylinder(x, z, 63, 63, 6, "andesite")                                                # the shelf (y = 63) she lies on
        c.box(x - 6, 64, z - 6, x + 6, 80, z + 6, "air")
        for k in range(6):                                                                     # jagged spires around it
            a = cr.uniform(0, 6.28)
            r = cr.uniform(6.8, 9.6)
            sx, sz = int(x + math.cos(a) * r), int(z + math.sin(a) * r)
            c.ellipsoid(sx, 60, sz, cr.uniform(1.6, 2.6), int(cr.integers(8, 16)), cr.uniform(1.6, 2.6), "stone")
    for _ in range(18):                                                                         # reefs and spires in the mist
        a, rr = cr.uniform(0, 6.28), cr.uniform(22, 58)
        x, z = int(c.cx + math.cos(a) * rr), int(c.cz + math.sin(a) * rr)
        c.ellipsoid(x, 50, z, cr.uniform(1.5, 3.5), int(cr.integers(12, 24)), cr.uniform(1.5, 3.5),
                    "tuff" if cr.random() < 0.3 else "stone", only=("water", "air"))


def site_strait(c):
    Y = c.p["y"]
    # two headlands face each other across the strait (it runs north-south); Scylla's cave is at the foot of the west one
    rough = c.noise(34, 2) * 7
    tz = smooth(1 - (np.abs(c.Z - c.cz) / 80.0) ** 2.5)                      # round ends, not walls
    def cliff(dist, top, slope, length):
        dist = dist + rough - (1 - tz) * 28
        face = smooth(dist / 9.0)                                            # the steep face: 9 blocks from sea to top
        end = smooth((length - dist) / 20.0)                                 # and the headland ends in a slope to the sea
        return SEA_FLOOR + (top - SEA_FLOOR + np.maximum(dist - 9, 0) * slope + c.noise(26) * 5) * face * tz * end
    west = cliff(c.cx + 8 - c.X, Y + 40, 0.14, 96)
    east = cliff(c.X - c.cx - 62, Y + 28, 0.16, 54)
    c.H = np.maximum(c.H, np.rint(np.maximum(west, east)).astype(int))
    ledge = (c.X > c.cx - 20) & (c.X <= c.cx + 10) & (np.abs(c.Z - c.cz) < 16)
    c.H = np.where(ledge, np.maximum(c.H, Y), c.H)
    c.finish_terrain(top=np.where(c.H >= WP.SEA, IDX["stone"], IDX["gravel"]), sub=IDX["stone"], under=("gravel", "gravel"))
    c.box(c.cx - 20, Y - 3, c.cz - 16, c.cx + 10, Y, c.cz + 16, "stone")                      # the ledge she sits on
    c.box(c.cx - 22, Y + 1, c.cz - 12, c.cx + 12, Y + 18, c.cz + 12, "air")                   # her cave, open to the strait
    c.ellipsoid(c.cx - 22, Y + 9, c.cz, 12, 11, 14, "air")
    for lz in (-10, 10):
        c.box(c.cx + 9, Y + 1, c.cz + lz, c.cx + 9, Y + 3, c.cz + lz, "bricks"); c.set(c.cx + 9, Y + 4, c.cz + lz, "glowstone")


def site_thrinacia(c):
    Y = c.p["y"]
    c.island(R=58, peak=70, plateau=26, Y=Y, wobble=0.08, amp=1.2)
    c.finish_terrain()
    c.clear(c.cx, c.cz, 19)
    for k in range(6):                                                                          # the altar of the sun
        a = k / 6 * 2 * math.pi
        x, z = int(c.cx + 14 + math.cos(a) * 5), int(c.cz - 18 + math.sin(a) * 5)
        c.box(x, Y + 1, z, x, Y + 6, z, "quartz_pillar"); c.set(x, Y + 7, z, "quartz")
    c.box(c.cx + 11, Y, c.cz - 21, c.cx + 17, Y, c.cz - 15, "smooth_quartz")
    c.scatter(14, "oak", (28, 14)); c.flowers(120, (4, 42))


def site_ithaca(c):
    Y = c.p["y"]
    c.island(R=46, peak=72, plateau=26, Y=Y, wobble=0.09)
    c.finish_terrain()
    c.clear(c.cx + 4, c.cz + 6, 7)
    x0, z0 = c.cx - 12, c.cz - 22                                                               # home: a white house with columns
    c.clear(x0 + 6, z0 + 5, 12)
    c.box(x0, Y - 3, z0, x0 + 12, Y, z0 + 10, "smooth_quartz")
    c.box(x0 + 1, Y + 1, z0 + 1, x0 + 11, Y + 5, z0 + 9, "quartz"); c.box(x0 + 2, Y + 1, z0 + 2, x0 + 10, Y + 5, z0 + 8, "air")
    c.box(x0 + 5, Y + 1, z0 + 1, x0 + 7, Y + 2, z0 + 1, "air")
    c.box(x0 - 1, Y + 6, z0 - 1, x0 + 13, Y + 6, z0 + 11, "smooth_quartz")
    for px in (x0, x0 + 4, x0 + 8, x0 + 12):
        for pz in (z0 - 2, z0 + 12):
            c.box(px, Y + 1, pz, px, Y + 5, pz, "quartz_pillar")
    c.box(x0 + 1, Y, z0 + 1, x0 + 11, Y, z0 + 9, "planks")
    c.scatter(24, "oak", (22, 20)); c.flowers(70, (6, 36))


BUILDERS = {"ogygia": site_ogygia, "troy": site_troy, "cyclops": site_cyclops, "telepylus": site_telepylus,
            "aeaea": site_aeaea, "hades": site_hades, "sirens": site_sirens, "strait": site_strait,
            "thrinacia": site_thrinacia, "ithaca": site_ithaca}


# ================================================================== writing the world
def bounds_of_region(margin=100):
    xs = [s["x"] - s["r"] - 14 for s in WP.SITES] + [s["x"] + s["r"] + 14 for s in WP.SITES]
    zs = [s["z"] - s["r"] - 14 for s in WP.SITES] + [s["z"] + s["r"] + 14 for s in WP.SITES]
    return (min(xs) - margin) // 16, (max(xs) + margin) // 16 + 1, (min(zs) - margin) // 16, (max(zs) + margin) // 16 + 1


def build_canvases(only=None):
    out = []
    for i, plan in enumerate(WP.SITES):
        if only and plan["id"] not in only:
            continue
        c = Canvas(plan, seed=100 + i)
        BUILDERS[plan["id"]](c)
        out.append(c)
    return out


def png_rgb(img):
    """Encode an (H, W, 3) uint8 array as a PNG."""
    import struct
    import zlib
    h, w, _ = img.shape
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def minimap(canvases, path, scale=2):
    """A top-down picture of the whole map (the highest solid block of every column), for checking the layout."""
    cx0, cx1, cz0, cz1 = bounds_of_region(40)
    W, D = (cx1 - cx0) * 16, (cz1 - cz0) * 16
    img = np.zeros((D, W, 3), np.uint8)
    img[:] = (np.array(MAP_COLORS["water"], float) * (1 - (WP.SEA - SEA_FLOOR - 1) * 0.011)).astype(np.uint8)    # the deep sea
    table = np.array([MAP_COLORS.get(n, (120, 120, 120)) for n in NAMES], float)
    for c in canvases:
        solid = (c.a != IDX["air"]) & (c.a != IDX["water"])
        ytop = NY - 1 - np.argmax(solid[:, ::-1, :], axis=1)
        has = solid.any(axis=1)
        idx = c.a[np.arange(c.W)[:, None], ytop, np.arange(c.D)[None, :]]
        shade = 0.72 + 0.28 * np.clip((ytop + Y0 - 60) / 40.0, 0, 1)
        col = (table[idx] * shade[..., None]).astype(np.uint8)
        depth = np.clip(WP.SEA - (ytop + Y0), 0, 30)
        deep = (np.array(MAP_COLORS["water"], float)[None, None, :] * (1 - depth[..., None] * 0.011)).astype(np.uint8)
        col = np.where((ytop + Y0 < WP.SEA)[..., None], deep, col)
        gx0, gz0 = c.x0 - cx0 * 16, c.z0 - cz0 * 16
        part = img[gz0:gz0 + c.D, gx0:gx0 + c.W]
        sub = np.transpose(col, (1, 0, 2)); m = has.T
        part[m] = sub[m]
    big = np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)
    with open(path, "wb") as f:
        f.write(png_rgb(big))


def write_level(path, canvases, log=print):
    import logging
    logging.disable(logging.CRITICAL)
    import amulet
    import amulet_nbt
    from amulet.api.block import Block
    from amulet.api.chunk import Chunk
    from amulet.api.selection import SelectionBox, SelectionGroup
    from amulet.level.formats.leveldb_world import LevelDBFormat

    if os.path.isdir(path):
        shutil.rmtree(path)
    fmt = LevelDBFormat(path)
    fmt.create_and_open("bedrock", (1, 21, 0), SelectionGroup([SelectionBox((-4000, Y0, -4000), (4000, 320, 4000))]), overwrite=True)
    fmt.close()
    level = amulet.load_level(path)
    dim = "minecraft:overworld"
    pal = level.block_palette
    def universal(k):
        ns, name, props = SPECIAL.get(k, ("universal_minecraft",) + BLOCKS[k])
        return Block(ns, name, {a: amulet_nbt.StringTag(b) for a, b in props.items()})
    bedrock = level.translation_manager.get_version("bedrock", (1, 21, 0))
    untranslated = [k for k in NAMES if bedrock.block.from_universal(universal(k))[0].namespace != "minecraft"]
    if untranslated:
        raise SystemExit(f"these blocks do not translate to Bedrock and would show up as dirt: {untranslated}")
    ids = np.array([pal.get_add_block(universal(k)) for k in NAMES], dtype=np.uint32)
    sea = np.full((16, NY, 16), IDX["air"], np.uint8)
    sea[:, 0, :] = IDX["bedrock"]
    sea[:, 1:SEA_FLOOR - Y0 + 1, :] = IDX["stone"]
    sea[:, SEA_FLOOR - Y0, :] = IDX["gravel"]
    sea[:, SEA_FLOOR - Y0 + 1:WATER_TOP - Y0 + 1, :] = IDX["water"]
    sea_ids = ids[sea]
    done = set()
    count = 0
    for c in canvases:
        for cx in range(c.x0 // 16, c.x1 // 16):
            for cz in range(c.z0 // 16, c.z1 // 16):
                ch = Chunk(cx, cz)
                ch.blocks[0:16, Y0:Y1, 0:16] = ids[c.a[cx * 16 - c.x0:cx * 16 - c.x0 + 16, :, cz * 16 - c.z0:cz * 16 - c.z0 + 16]]
                level.put_chunk(ch, dim)
                done.add((cx, cz)); count += 1
    cx0, cx1, cz0, cz1 = bounds_of_region()
    for cx in range(cx0, cx1):
        for cz in range(cz0, cz1):
            if (cx, cz) in done:
                continue
            ch = Chunk(cx, cz)
            ch.blocks[0:16, Y0:Y1, 0:16] = sea_ids
            level.put_chunk(ch, dim)
            count += 1
        level.save() if cx % 8 == 0 else None
    log(f"wrote {count} chunks")
    # level.dat: a flat survival world with commands, no natural mob spawns (the places keep their own creatures)
    rt = level.level_wrapper.root_tag.compound
    spawn = WP.MARKER
    T = amulet_nbt
    rt.update({
        "Generator": T.IntTag(2), "FlatWorldLayers": T.StringTag(json.dumps(FLAT_LAYERS, separators=(",", ":"))),
        "LevelName": T.StringTag("The Odyssey (2026)"), "GameType": T.IntTag(0), "Difficulty": T.IntTag(2),
        "commandsEnabled": T.ByteTag(1), "cheatsEnabled": T.ByteTag(1), "SpawnX": T.IntTag(spawn["x"]),
        "SpawnY": T.IntTag(spawn["y"] + 1), "SpawnZ": T.IntTag(spawn["z"] + 3), "spawnradius": T.IntTag(3),
        "domobspawning": T.ByteTag(0), "showcoordinates": T.ByteTag(1), "dodaylightcycle": T.ByteTag(1),
        "doweathercycle": T.ByteTag(1), "keepinventory": T.ByteTag(0), "MultiplayerGame": T.ByteTag(1),
        "LANBroadcast": T.ByteTag(1), "RandomSeed": T.LongTag(20260717), "Time": T.LongTag(0),
        "hasBeenLoadedInCreative": T.ByteTag(0), "educationFeaturesEnabled": T.ByteTag(0),
    })
    level.save()
    level.close()


def embed_packs(path, version):
    for pack, folder, name in (("BP", "behavior_packs", "Odyssey_Creatures_BP"), ("RP", "resource_packs", "Odyssey_Creatures_RP")):
        dst = os.path.join(path, folder, name)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(ROOT, pack), dst, ignore=shutil.ignore_patterns(".*"))
    manifests = {p: json.load(open(os.path.join(ROOT, p, "manifest.json"))) for p in ("BP", "RP")}
    for pack, fname in (("BP", "world_behavior_packs.json"), ("RP", "world_resource_packs.json")):
        h = manifests[pack]["header"]
        with open(os.path.join(path, fname), "w") as f:
            json.dump([{"pack_id": h["uuid"], "version": h["version"]}], f)
    with open(os.path.join(path, "levelname.txt"), "w") as f:
        f.write("The Odyssey (2026)")


def slice_png(c, path, axis, coord, scale=4, ylo=36, yhi=124):
    """A vertical cross-section of a place (axis 'z' = a west-east slice at z = coord), for checking caves and cliffs."""
    if axis == "z":
        sl = c.a[:, :, coord - c.z0]
    else:
        sl = c.a[coord - c.x0, :, :]
    sl = sl[:, ylo - Y0:yhi - Y0]
    table = np.array([MAP_COLORS.get(n, (120, 120, 120)) for n in NAMES], np.uint8)
    img = table[sl.T[::-1]]                                          # y up
    img = np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)
    with open(path, "wb") as f:
        f.write(png_rgb(img))


# free blocks above a creature's feet (the creature is this many blocks tall)
HEADROOM = {"studio:cyclops": 13, "studio:scylla": 10, "studio:trojan_horse": 12, "studio:laestrygonian": 5,
            "studio:laestrygonian_child": 3}


def verify_world(path, log=print):
    """Read the finished world back and check what the script relies on: the marker, solid ground and headroom at every
    place where a creature is spawned, and open water around the sirens' rocks. Returns a list of problems."""
    import logging
    logging.disable(logging.CRITICAL)
    import amulet

    level = amulet.load_level(path)
    dim = "minecraft:overworld"
    problems = []

    def block(x, y, z):
        ch = level.get_chunk(x // 16, z // 16, dim)
        return str(ch.get_block(x % 16, y, z % 16)).replace("universal_minecraft:", "").split("[")[0]
    m = WP.MARKER
    if block(m["x"], m["y"], m["z"]) != m["block"].replace("minecraft:", ""):
        problems.append(f"no {m['block']} at the marker position {m}")
    solid_not = {"air", "water", "leaves", "oak_leaves", "spruce_leaves", "short_grass", "dandelion", "poppy", "plant", "red_flower"}
    for s in WP.SITES:
        for typ, dx, dz in s["creatures"]:
            x, y, z = s["x"] + dx, s["y"], s["z"] + dz
            if block(x, y, z) in solid_not:
                problems.append(f"{s['id']}: {typ} would stand on {block(x, y, z)} at {(x, y, z)}")
            top = HEADROOM.get(typ, 3)
            blocked = [yy for yy in range(y + 1, y + 1 + top) if block(x, yy, z) not in ("air", "plant", "red_flower")]
            if blocked:
                problems.append(f"{s['id']}: {typ} at {(x, y, z)} has no room above (blocked at y={blocked[0]}: {block(x, blocked[0], z)})")
    # the sea connects the places: flood fill open water, 16 blocks at a time, from Ogygia and see what can be reached
    x0c, x1c, z0c, z1c = bounds_of_region(0)
    xs = list(range(x0c * 16 + 8, x1c * 16, 16))
    zs = list(range(z0c * 16 + 8, z1c * 16, 16))
    open_ = np.zeros((len(xs), len(zs)), bool)
    for i, x in enumerate(xs):
        for j, z in enumerate(zs):
            open_[i, j] = block(x, WP.SEA - 1, z) == "water" and all(block(x, WP.SEA + k, z) == "air" for k in (0, 2))
    home = WP.SITES[0]
    hi = min(range(len(xs)), key=lambda i: abs(xs[i] - home["x"] - 60))
    hj = min(range(len(zs)), key=lambda j: abs(zs[j] - home["z"]))
    reached = np.zeros_like(open_)
    stack = [(hi, hj)] if open_[hi, hj] else []
    while stack:
        i, j = stack.pop()
        if not (0 <= i < len(xs) and 0 <= j < len(zs)) or reached[i, j] or not open_[i, j]:
            continue
        reached[i, j] = True
        stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
    def can_sail_near(x, z, r):
        return any(reached[i, j] for i, X in enumerate(xs) for j, Z in enumerate(zs) if math.hypot(X - x, Z - z) <= r)
    for st in WP.SITES:
        if not can_sail_near(st["x"], st["z"], st["r"] + 30):
            problems.append(f"{st['id']} cannot be reached by boat")
    strait = next(st for st in WP.SITES if st["id"] == "strait")
    for dz in (-110, 0, 110):
        if not can_sail_near(strait["x"] + 35, strait["z"] + dz, 12):
            problems.append(f"the strait cannot be sailed at {dz:+d} from its middle")
    level.close()
    for pr in problems:
        log("  problem: " + pr)
    log(f"world check: {'OK' if not problems else str(len(problems)) + ' problem(s)'}")
    return problems


def package_world(path, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, files in os.walk(path):
            dirnames.sort()
            for fn in sorted(files):
                full = os.path.join(dirpath, fn)
                z.write(full, os.path.relpath(full, path).replace(os.sep, "/"))
                n += 1
    return n


def main(argv):
    import time
    value = {argv[argv.index("--minimap") + 1]} if "--minimap" in argv else set()
    only = [a for a in argv if not a.startswith("--") and a not in value]
    t0 = time.time()
    canvases = build_canvases(only or None)
    print(f"built {len(canvases)} places in {time.time() - t0:.1f}s")
    if "--minimap" in argv:
        out = argv[argv.index("--minimap") + 1]
        minimap(canvases, out)
        print("wrote", out)
        if "--no-world" in argv:
            return 0
    if "--no-world" in argv:
        return 0
    version = ".".join(map(str, json.load(open(os.path.join(ROOT, "BP", "manifest.json")))["header"]["version"]))
    work = os.path.join(ROOT, "dist", "world_build")
    write_level(work, canvases)
    embed_packs(work, version)
    if verify_world(work):
        return 1
    out = os.path.join(ROOT, "dist", f"The_Odyssey_v{version}.mcworld")
    n = package_world(work, out)
    print(f"wrote {os.path.relpath(out, ROOT)}: {n} files, {os.path.getsize(out) // 1024} KB in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
