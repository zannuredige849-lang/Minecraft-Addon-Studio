"""Scylla and Charybdis as in Nolan's The Odyssey (2026).

Scylla: "a massive body anchored in the cliff, with six long and bumped serpentine necks finished by bestial heads
structured like articulated arms, with very small eyes and powerful jaws capable of catching several men
simultaneously. Her skin is rough brown, a mixture of rock, scales and marine flesh ... The heads move
independently" (Villains Wiki); a "rock monster" (Moria review); she never leaves her rock.

Charybdis: "a gigantic living whirlpool ... like a huge abysmal mouth with swirling waters ... a living throat that
sucks everything in its path" (Villains Wiki).
"""
import math

from .core import Model
from .materials import rock_flesh, cavity, teeth, flat, water, wood

NECKS = 6
NECK_SEGS = 8


def build_scylla():
    m = Model("scylla", 53, D=2)
    ROCK = rock_flesh(rock=(116, 104, 88), scale=(98, 76, 58), flesh=(128, 84, 70))
    BODY = rock_flesh(rock=(110, 100, 86), scale=(92, 72, 56), flesh=(120, 80, 66))
    NECK = rock_flesh(rock=(104, 86, 70), scale=(108, 82, 60), flesh=(140, 92, 76))
    HEAD = rock_flesh(rock=(96, 82, 68), scale=(104, 78, 58), flesh=(136, 88, 74))
    CAVE = cavity((14, 10, 10))
    UPT, LOT = teeth((226, 214, 184), "down", gap=1.0), teeth((222, 210, 180), "up", gap=1.0)
    EYE = flat((22, 16, 12))

    m.bone("root", None, (0, 0, 0))
    m.bone("body", "root", (0, 0, 0))
    m.cbox("body", (0, 4, 4), (46, 8, 30), BODY)
    m.cbox("body", (0, 18, 6), (40, 22, 24), BODY)
    m.cbox("body", (-10, 30, 5), (18, 10, 18), ROCK, rot=(0, 15, 8))
    m.cbox("body", (12, 28, 6), (16, 12, 16), ROCK, rot=(0, -20, -6))
    m.cbox("body", (0, 34, 9), (22, 8, 14), BODY, rot=(6, 0, 0))
    m.cbox("body", (-22, 13, 5), (10, 20, 20), ROCK, rot=(0, 0, 6))
    m.cbox("body", (22, 12, 6), (10, 18, 20), ROCK, rot=(0, 0, -8))
    m.cbox("body", (0, 20, -6.0), (20, 15, 1), CAVE)
    m.cbox("body", (0, 27.5, -6.5), (22, 2, 2), ROCK)
    m.cbox("body", (-11, 19, -6.5), (2, 16, 2), ROCK)
    m.cbox("body", (11, 19, -6.5), (2, 16, 2), ROCK)

    bases = [(-6.5, 23.5), (-4, 25.5), (-1.3, 22.5), (1.3, 25.5), (4, 22.5), (6.5, 24.5)]
    spread = (-34, -20, -7, 7, 20, 34)
    curves = ((52, -9, -11, -10, -8, -6, -4, -3), (60, -10, -12, -12, -9, -7, -4, -2), (46, -8, -9, -8, -7, -5, -3, -2))
    L = 5.0
    for i, (bx, by) in enumerate(bases):
        bz = -4.0
        cv = curves[i % 3]
        parent = "body"
        y = by
        for s in range(NECK_SEGS):
            w = 4.5 - s * 0.25
            rot = (cv[0], 0, spread[i]) if s == 0 else (cv[s], 0, 0)
            name = m.bone(f"neck_{i}_{s}", parent, (bx, y, bz), rot)
            m.cbox(name, (bx, y + L / 2, bz), (w, L + 0.5, w), NECK)
            m.cbox(name, (bx, y + L * 0.55, bz + w / 2 + 0.3), (w * 0.55, L * 0.5, 1.0), NECK)        # dorsal bump
            if s % 2 == 0:
                m.cbox(name, (bx + w / 2 + 0.25, y + L * 0.4, bz), (1.0, L * 0.4, w * 0.5), NECK)      # side bump
            parent, y = name, y + L
        top = y
        pitch = sum(cv)
        hb = m.bone(f"head_{i}", parent, (bx, top, bz), (-pitch + 16, 0, -spread[i] * 0.55))
        # an elongated head built like an arm: hinged cranium, snout and jaw
        m.cbox(hb, (bx, top + 1.5, bz - 1.5), (5, 4.5, 6), HEAD)
        m.cbox(hb, (bx, top + 3.9, bz - 0.5), (3.5, 1.0, 5), HEAD)
        m.cbox(hb, (bx, top + 0.9, bz - 7.0), (4, 3.5, 6), HEAD, rot=(8, 0, 0), pivot=(bx, top + 1.5, bz - 4.5))
        m.cbox(hb, (bx, top + 2.4, bz - 7.0), (2.5, 1.0, 4), HEAD, rot=(8, 0, 0), pivot=(bx, top + 1.5, bz - 4.5))
        m.cbox(hb, (bx, top - 0.85, bz - 9.6), (3.5, 1.25, 0.5), UPT, rot=(8, 0, 0), pivot=(bx, top + 1.5, bz - 4.5))
        for sx in (-1, 1):
            m.cbox(hb, (bx + sx * 1.85, top - 0.85, bz - 7.0), (0.5, 1.25, 5.0), UPT, rot=(8, 0, 0), pivot=(bx, top + 1.5, bz - 4.5))
            m.cbox(hb, (bx + sx * 2.55, top + 2.4, bz - 3.6), (0.5, 0.5, 0.5), EYE)
        jb = m.bone(f"jaw_{i}", hb, (bx, top - 0.3, bz - 2.0), (24, 0, 0))
        m.cbox(jb, (bx, top - 1.0, bz - 6.0), (4.5, 1.5, 8.5), HEAD)
        m.cbox(jb, (bx, top + 0.05, bz - 9.9), (3.5, 1.0, 0.5), LOT)
        for sx in (-1, 1):
            m.cbox(jb, (bx + sx * 1.9, top + 0.05, bz - 6.5), (0.5, 1.0, 6.0), LOT)
    return m


RINGS = (44, 38, 32, 26, 20, 14, 9)


def build_charybdis():
    m = Model("charybdis", 71, D=1)
    FOAM = water((70, 120, 130), alpha=205, foam_amt=0.45)
    WAT = water((28, 72, 90), alpha=170, foam_amt=0.2)
    DEEP = water((10, 26, 36), alpha=230, foam_amt=0.04)
    WOOD = wood((96, 72, 48))
    m.bone("root", None, (0, 0, 0))
    t = 3
    for k, r in enumerate(RINGS):
        y = -k * 4.5
        mat = FOAM if k < 2 else WAT if k < 4 else DEEP
        hh = 3
        for suffix, rest in (("a", 0), ("b", 45)):
            name = m.bone(f"ring{suffix}_{k}", "root", (0, y, 0), (0, rest + k * 11, 0))
            m.cube(name, (-r, y, -r), (2 * r, hh, t), mat)
            m.cube(name, (-r, y, r - t), (2 * r, hh, t), mat)
            m.cube(name, (-r, y, -r + t), (t, hh, 2 * r - 2 * t), mat)
            m.cube(name, (r - t, y, -r + t), (t, hh, 2 * r - 2 * t), mat)
    m.bone("spiral", "root", (0, 0, 0))
    for k in range(14):
        a = k * 50
        r = 40 - k * 2.5
        y = -k * 2.3
        x, z = math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r
        m.cube("spiral", (x - 1, y, z - 7), (2, 1, 14), FOAM if k < 5 else WAT, rot=(0, -a, 12), pivot=(x, y, z))
    m.bone("core", "root", (0, -14, 0))
    m.cube("core", (-4, -38, -4), (8, 34, 8), DEEP)
    m.cube("ringa_1", (18, -3.5, -33), (7, 1, 2), WOOD, rot=(0, 25, 8))
    m.cube("ringb_3", (-16, -13, 4), (5, 1, 2), WOOD, rot=(0, -40, -10))
    m.cube("ringa_2", (-6, -8, 26), (6, 2, 2), WOOD, rot=(0, 70, 15))
    return m
