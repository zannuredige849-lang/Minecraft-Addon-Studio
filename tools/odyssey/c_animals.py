"""Animals of Nolan's The Odyssey (2026): Circe's sister (whom Circe transformed into a bird) and the sacred cattle
of the sun god on Thrinacia."""
import math

from .core import Model
from .materials import feather, flat, hide, horn, skin, cloth, hair, nostrils
from .parts import chain_y


def build_sister():
    """Circe's sister, transformed into a bird. The film does not name the species; a small dark bird."""
    m = Model("circe_sister", 79, D=4)
    BODY = feather((54, 48, 44), (30, 26, 24))
    WING = feather((46, 40, 36), (24, 20, 18))
    BEAK = flat((50, 46, 42))
    LEG = flat((60, 54, 50))
    m.bone("root", None, (0, 0, 0))
    m.bone("body", "root", (0, 2.6, 0), (-12, 0, 0))
    m.cbox("body", (0, 3.0, 0.3), (2.5, 2.5, 4.25), BODY)
    m.cbox("body", (0, 2.6, -1.4), (2.25, 1.75, 1.25), feather((70, 62, 56), (40, 36, 32)))
    m.bone("head", "body", (0, 4.0, -1.6), (12, 0, 0))
    m.cbox("head", (0, 4.75, -2.1), (2, 2, 2), BODY)
    m.cbox("head", (0, 4.6, -3.55), (0.75, 0.75, 1.25), BEAK)
    m.mcbox("head", (-0.95, 5.0, -2.6), (0.25, 0.5, 0.5), flat((14, 12, 12)))
    m.side("wing", "body", (-1.25, 3.8, -1.0))
    m.scbox("wing", (-1.4, 3.0, 0.6), (0.5, 2.0, 4.0), WING)
    m.bone("tail", "body", (0, 2.6, 2.4), (-14, 0, 0))
    m.cbox("tail", (0, 2.5, 3.9), (1.75, 0.5, 3.0), WING)
    m.side("leg", "body", (-0.6, 1.9, 0.3))
    m.scbox("leg", (-0.6, 1.0, 0.3), (0.25, 1.75, 0.25), LEG)
    m.scbox("leg", (-0.6, 0.12, -0.2), (0.5, 0.25, 1.25), LEG)
    return m


def build_cattle():
    """The sun god's cattle on Thrinacia. The film's breed is not described; a large ancient long-horned bovine."""
    m = Model("sun_cattle", 83, D=4)
    COAT = hide((214, 186, 142), belly=(236, 222, 192))
    DARK = hide((176, 148, 108), belly=(214, 196, 160))
    MUZ = skin((132, 110, 100), mottle=0.4)
    HOOF = flat((48, 42, 38))
    HORN = horn((224, 214, 186), (62, 54, 46))
    m.bone("root", None, (0, 0, 0))
    m.bone("body", "root", (0, 15, 0))
    m.cbox("body", (0, 19.5, 0), (12, 11, 22), COAT)
    m.cbox("body", (0, 21.5, -8.5), (12.5, 12, 6), COAT)
    m.cbox("body", (0, 26.0, -7.0), (8, 2.5, 7), DARK)                 # shoulder hump
    m.cbox("body", (0, 18.5, 10.0), (11, 10, 3), COAT)
    m.cbox("body", (0, 14.6, -9.8), (3, 5, 3), COAT)                   # dewlap
    m.bone("head", "body", (0, 22.5, -11), (22, 0, 0))
    m.cbox("head", (0, 22.0, -15.0), (6.5, 7, 7.5), COAT)
    m.cbox("head", (0, 20.0, -19.25), (5.0, 4.0, 3.0), MUZ, decal={"north": nostrils()})
    m.cbox("head", (0, 25.6, -14.0), (7.5, 1.5, 3), DARK)
    m.mcbox("head", (-3.4, 23.2, -17.3), (0.25, 0.75, 0.75), flat((18, 14, 12)))
    m.mcbox("head", (-4.4, 24.0, -12.8), (2.5, 1.0, 1.5), COAT, rot=(0, 0, -20))
    for sx in (-1, 1):
        x0 = sx * 3.6
        base = (x0, 25.0, -14.2)
        a = 0.0
        x, y = base[0], base[1]
        segs = ((3.5, 1.75, 62), (3.5, 1.5, -24), (3.5, 1.25, -26), (3.0, 1.0, -22))
        for k, (L, w, ang) in enumerate(segs):
            a += ang
            r = math.radians(a)
            dx, dy = sx * math.sin(r), math.cos(r)
            drawn = L + (0.75 if k < len(segs) - 1 else 0.0)        # overlap closes the gap on the outside of a bend
            m.cube("head", (x - w / 2, y, base[2] - w / 2), (w, drawn, w), HORN, rot=(0, 0, sx * a), pivot=(x, y, base[2]))
            x, y = x + dx * L, y + dy * L
    for leg, (x, z) in (("fl", (-3.6, -8.0)), ("fr", (3.6, -8.0)), ("hl", (-3.6, 8.0)), ("hr", (3.6, 8.0))):
        m.bone(f"leg_{leg}", "body", (x, 15.5, z))
        m.cbox(f"leg_{leg}", (x, 12.0, z), (3.0, 8.0, 3.5), COAT)
        m.cbox(f"leg_{leg}", (x, 4.5, z), (2.25, 8.0, 2.5), DARK)
        m.cbox(f"leg_{leg}", (x, 0.6, z - 0.2), (2.75, 1.25, 3.0), HOOF)
    m.bone("tail", "body", (0, 23, 11.5), (12, 0, 0))
    m.cbox("tail", (0, 17.5, 12.0), (1.0, 11, 1.0), COAT)
    m.cbox("tail", (0, 11.0, 12.0), (1.75, 3, 1.75), hair((120, 96, 70), tips=1.0))
    return m
