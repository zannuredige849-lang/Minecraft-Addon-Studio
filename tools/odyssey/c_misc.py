"""The Trojan Horse and the boulder Polyphemus hurls at the ship.

Trojan Horse: production designer Ruth De Jong's 36 ft (11 m) model, "a more sophisticated-looking horse", shown
rearing (several viewers remarked on the rearing pose). Greek soldiers hid inside it.
"""
from .core import Model
from .materials import planks, wood, metal, stone

HORSE_TARGET_BLOCKS = 11.0


def build_horse():
    m = Model("trojan_horse", 97, D=2)
    P = planks((150, 112, 70), seam=(70, 50, 32))
    PD = planks((124, 90, 56), seam=(60, 42, 28))
    BEAM = wood((96, 68, 42), grain=0.2)
    IRON = metal((70, 70, 76), edge=(140, 140, 146), rivets=False)
    m.bone("root", None, (0, 0, 0))
    m.cbox("root", (0, 1.5, 2), (20, 3, 34), PD)
    for zz in (-12, 0, 12):
        m.cbox("root", (0, 3.25, 2 + zz), (21, 0.5, 2), BEAM)
    # hind legs standing on the platform
    for sx in (-1, 1):
        x = sx * 4.0
        m.cbox("root", (x, 6.5, 10.5), (3.0, 7, 3.5), PD)
        m.cbox("root", (x, 3.75, 9.5), (3.5, 1.5, 4), IRON)
        m.cbox("root", (x, 13.5, 11.0), (3.5, 8.5, 4.5), P, rot=(14, 0, 0))
        m.cbox("root", (x, 17.0, 9.5), (4.5, 4, 6), P)
    # the body rears up from the hips
    m.bone("body", "root", (0, 17, 9), (-34, 0, 0))
    m.cbox("body", (0, 20, -2), (12, 12, 26), P)
    m.cbox("body", (0, 21, 10), (11, 11, 4), PD)
    m.bone("hatch", "body", (0, 14.2, 5))                              # the belly hatch, hinged at its rear edge
    m.cbox("hatch", (0, 14.2, -2), (8, 0.5, 14), BEAM)
    m.cbox("hatch", (0, 13.7, -8.5), (2, 0.5, 1.5), IRON)               # its handle
    for zz in (-10, -2, 6):
        m.cbox("body", (0, 20, zz), (12.5, 12.5, 1.0), BEAM)
    m.mcbox("body", (-4.5, 17.5, 9.5), (4, 9, 7), P)                   # haunches
    # neck, mane and head
    m.bone("neck", "body", (0, 24, -13), (-30, 0, 0))
    m.cbox("neck", (0, 30, -14), (6, 14, 7), P)
    for k in range(5):
        m.cbox("neck", (0, 25.5 + k * 2.6, -10.3), (2, 2.4, 1.5), BEAM)
    m.bone("head", "neck", (0, 36, -14), (60, 0, 0))
    m.cbox("head", (0, 38.5, -15.5), (5, 5, 6), P)
    m.cbox("head", (0, 38.0, -21), (4, 4, 6), PD)
    m.mcbox("head", (-1.7, 42.2, -14.5), (1.25, 2.5, 1.25), P)
    m.mcbox("head", (-2.55, 38.8, -18.0), (0.5, 1.0, 1.0), IRON)
    # raised forelegs
    for side, sx in (("r", -1), ("l", 1)):
        m.bone(f"fore_{side}", "body", (sx * 4.0, 18, -12), (-60, 0, 0))
        m.cbox(f"fore_{side}", (sx * 4.0, 13.5, -12), (3.0, 9, 3.5), P)
        m.bone(f"forelow_{side}", f"fore_{side}", (sx * 4.0, 9.0, -12), (95, 0, 0))
        m.cbox(f"forelow_{side}", (sx * 4.0, 5.0, -12), (2.5, 8, 3.0), PD)
        m.cbox(f"forelow_{side}", (sx * 4.0, 0.6, -12.2), (3.0, 1.5, 3.5), IRON)
    m.bone("tail", "body", (0, 21, 12.5), (40, 0, 0))
    m.cbox("tail", (0, 15, 13.5), (2.5, 12, 2.5), PD)
    return m


def build_boulder():
    m = Model("boulder", 101, D=2)
    S = stone((118, 112, 104))
    m.bone("rock", None, (0, 4, 0))
    m.cube("rock", (-4, 0, -4), (8, 8, 8), S, rot=(10, 20, 5), pivot=(0, 4, 0))
    m.cube("rock", (-3, 1, -5), (6, 6, 10), S, rot=(30, -15, 20), pivot=(0, 4, 0))
    m.cube("rock", (-5, 2, -3), (10, 5, 6), S, rot=(-20, 40, -10), pivot=(0, 4, 0))
    return m
