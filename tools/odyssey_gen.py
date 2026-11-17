#!/usr/bin/env python3
"""Odyssey creatures v2: HD (2 px per unit) cinematic textures, anatomical models,
Molang animations, behaviors, items, loot, spawn rules and sounds for studio:*."""
import json, math, os, struct, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = 2  # texture pixels per model unit (HD)

# =================================================================== noise
def hash2(ix, iy, seed):
    n = (int(ix) * 374761393 + int(iy) * 668265263 + int(seed) * 982451653) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, y, seed):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a, b = hash2(ix, iy, seed), hash2(ix + 1, iy, seed)
    c, d = hash2(ix, iy + 1, seed), hash2(ix + 1, iy + 1, seed)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


def fbm(x, y, seed, octaves=3):
    total, amp, freq, norm = 0.0, 0.5, 1.0, 0.0
    for i in range(octaves):
        total += vnoise(x * freq, y * freq, seed + i * 17) * amp
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm


# =================================================================== colour
def clamp8(v):
    return 0 if v < 0 else 255 if v > 255 else int(v)


def mix(a, b, t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def mul(c, k):
    if isinstance(k, tuple):
        return tuple(c[i] * k[i] for i in range(3))
    return tuple(x * k for x in c)


SIDES = ("north", "south", "east", "west")
FACE_LIGHT = {"up": 1.12, "north": 1.0, "east": 0.9, "west": 0.9, "south": 0.8, "down": 0.6}


class Ctx:
    __slots__ = ("face", "x", "y", "w", "h", "seed", "fo", "variant")


def lighting(c):
    l = FACE_LIGHT[c.face]
    if c.face in SIDES and c.h > 1:
        l *= 1.07 - 0.2 * (c.y / (c.h - 1))
    if c.w > 3 and c.h > 3 and (c.x == 0 or c.y == 0 or c.x == c.w - 1 or c.y == c.h - 1):
        l *= 0.88
    return l


def grade(rgb, l):
    """Cinematic grade: cool shadows, warm highlights, slight desaturation and contrast."""
    r, g, b = rgb[0] * l, rgb[1] * l, rgb[2] * l
    if l < 1:
        k = 1 - l
        r *= 1 - k * 0.22
        g *= 1 - k * 0.1
        b *= 1 + k * 0.08
    else:
        k = l - 1
        r *= 1 + k * 0.25
        g *= 1 + k * 0.12
        b *= 1 - k * 0.06
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    r, g, b = r + (lum - r) * 0.12, g + (lum - g) * 0.12, b + (lum - b) * 0.12
    return (clamp8((r - 128) * 1.06 + 128), clamp8((g - 128) * 1.06 + 128), clamp8((b - 128) * 1.06 + 128))


def _n(c, sx, sy, s=0, o=3):
    return fbm(c.x * sx + c.fo, c.y * sy + c.fo * 0.37, c.seed + s, o)


# =================================================================== materials
def flesh(base, dark=None, mottle=1.0, veins=None, pores=0.035, wrinkle=0.0, stain=None,
          tipdark=0, freckles=0.0, rings=0, ventral=None, nail=(78, 62, 50)):
    dk = dark or mul(base, 0.72)
    hi = mul(base, 1.1)

    def f(c):
        n = _n(c, 0.16, 0.16)
        col = mix(dk, hi, 0.5 + (n - 0.5) * 1.6 * mottle)
        b2 = _n(c, 0.06, 0.06, 7, 2)
        if b2 > 0.6:
            col = mix(col, mul(col, (0.9, 0.82, 0.8)), (b2 - 0.6) * 2.0)
        if veins is not None:
            vn = abs(_n(c, 0.11, 0.11, 3) - 0.5)
            if vn < 0.03:
                col = mix(col, veins, 0.5 * (1 - vn / 0.03))
        if pores and hash2(c.x, c.y, c.seed + 11) < pores:
            col = mul(col, 0.86)
        if freckles and hash2(c.x, c.y, c.seed + 13) < freckles:
            col = mix(col, (150, 92, 64), 0.45)
        if wrinkle and c.face in SIDES and math.sin(c.y * 1.7 + _n(c, 0.2, 0.2, 5) * 5) > 0.88:
            col = mul(col, 1 - wrinkle)
        if rings and c.face in SIDES:
            m = c.y % (rings * D)
            if m == 0:
                col = mul(col, 0.72)
            elif m == 1:
                col = mul(col, 1.1)
        if ventral is not None and c.face == "north" and abs(c.x - (c.w - 1) / 2) < c.w * 0.28:
            col = mix(col, ventral, 0.55)
        if stain is not None:
            t = 1.0 if c.face == "down" else 0.0 if c.face == "up" else c.y / max(1, c.h - 1)
            amt = max(0.0, (t - 0.25) / 0.75) * (0.75 + 0.25 * _n(c, 0.3, 0.3, 9))
            col = mix(col, stain, amt)
        if tipdark and (c.face == "down" or (c.face in SIDES and c.y >= c.h - tipdark * D)):
            col = mix(col, nail, 0.65)
        return col + (255,)
    return f


def hair(base, tips=0, streak=None):
    def f(c):
        if c.face in SIDES:
            k = 0.72 + 0.5 * hash2(c.x, 1, c.seed)
            col = mul(base, k * (0.85 + 0.3 * _n(c, 0.08, 0.35, 4, 2)))
            if streak is not None and hash2(c.x, 5, c.seed) > 0.8:
                col = mix(col, streak, 0.5)
            if tips and c.y >= c.h - tips * D:
                depth = (c.y - (c.h - tips * D) + 1) / (tips * D)
                if hash2(c.x, 9, c.seed) < depth * 0.9:
                    return (0, 0, 0, 0)
        else:
            n = _n(c, 0.3, 0.3, 4, 2)
            col = mul(base, 0.8 + 0.35 * n)
            if (c.x + int(n * 4)) % 3 == 0:
                col = mul(col, 0.82)
        return col + (255,)
    return f


def feather(base, tip, shaft=None, primary=False, tips=False):
    """Layered feather rows; `primary` = long flight feathers with ragged pointed tips.
    base/tip may be callables taking the paint variant (plumage palettes)."""
    def f(c):
        b = base(c.variant) if callable(base) else base
        t = tip(c.variant) if callable(tip) else tip
        sh = shaft or mix(b, (235, 225, 205), 0.5)
        if c.face not in SIDES:
            col = mul(b, 0.8 + 0.3 * _n(c, 0.25, 0.25, 2, 2))
            if (c.x + c.y) % 4 == 0:
                col = mul(col, 0.88)
            return col + (255,)
        if primary:
            fw = 4
            ci, lx = c.x // fw, c.x % fw
            col = mul(b, 0.85 + 0.25 * hash2(ci, 3, c.seed))
            if lx == 0:
                col = mul(col, 0.62)
            elif lx == 2:
                col = mix(col, sh, 0.45)
            td = c.h * 0.35
            if c.y > c.h - td:
                col = mix(col, t, (c.y - (c.h - td)) / td)
            if tips:
                tipline = c.h - 1 - int(hash2(ci, 4, c.seed) * 5)
                if lx in (0, 3):
                    tipline -= 2
                if c.y > tipline:
                    return (0, 0, 0, 0)
            return col + (255,)
        rh = 6
        r, ly = c.y // rh, c.y % rh
        off = (r % 2) * 3
        lx = (c.x + off) % 6
        col = mul(b, 0.88 + 0.22 * hash2((c.x + off) // 6, r, c.seed))
        if lx == 3:
            col = mix(col, sh, 0.35)
        elif lx == 0:
            col = mul(col, 0.7)
        if ly >= rh - 2:
            col = mix(col, t, 0.55 if ly == rh - 2 else 0.8)
        if ly == 0:
            col = mul(col, 0.85)
        if (lx + ly) % 2 == 0:
            col = mul(col, 0.95)
        return col + (255,)
    return f


def scale_mat(base, rim=None, hi=None):
    rm, hl = rim or mul(base, 0.62), hi or mul(base, 1.18)

    def f(c):
        r = c.y // 3
        lx, ly = (c.x + (r % 2) * 2) % 4, c.y % 3
        col = mul(base, 0.85 + 0.3 * _n(c, 0.15, 0.15, 6, 2))
        if ly == 2 or lx == 0:
            col = mix(col, rm, 0.7)
        elif ly == 0 and lx in (1, 2):
            col = mix(col, hl, 0.5)
        return col + (255,)
    return f


def cloth(base, folds=True, weave=True, tatter=0, grime=0.2, hem=None, knit=False):
    def f(c):
        col = mul(base, 0.88 + 0.22 * _n(c, 0.2, 0.2, 8, 2))
        if c.face in SIDES:
            if folds:
                col = mul(col, 0.92 + 0.1 * math.sin((c.x + _n(c, 0.05, 0.05, 2, 2) * 10) * 0.55))
            col = mul(col, 1 - grime * (c.y / max(1, c.h - 1)))
            if hem is not None and c.y >= c.h - 2:
                col = hem
            if tatter:
                cut = int(hash2(c.x // 2, 21, c.seed) * tatter * D)
                if c.y >= c.h - cut:
                    return (0, 0, 0, 0)
        if knit:
            k = (c.x % 4 in (1, 2)) ^ (c.y % 2 == 0)
            col = mul(col, 1.08 if k else 0.9)
        elif weave and (c.x + c.y) % 2 == 0:
            col = mul(col, 1.04)
        return col + (255,)
    return f


def metal(base, edge=None, rivets=True, bands=0, patina=None, scratches=True):
    eg = edge or mix(base, (255, 255, 255), 0.5)

    def f(c):
        col = mul(base, 0.86 + 0.28 * _n(c, 0.04, 0.9, 12, 2))
        if c.face in SIDES:
            col = mul(col, 1.12 - 0.3 * (c.y / max(1, c.h - 1)))
            if bands:
                bh = max(4, c.h // bands)
                m = c.y % bh
                if m == bh - 1:
                    col = mul(col, 0.55)
                elif m == 0:
                    col = mix(col, eg, 0.45)
                if rivets and m == bh // 2 and c.x % 6 == 3:
                    col = mix(col, eg, 0.8)
            elif rivets and (c.y == 2 or c.y == c.h - 3) and c.x % 6 == 3 and c.w > 6:
                col = mix(col, eg, 0.8)
        if c.x == 0 or c.y == 0:
            col = mix(col, eg, 0.35)
        if c.x == c.w - 1 or c.y == c.h - 1:
            col = mul(col, 0.7)
        if patina is not None:
            p = _n(c, 0.12, 0.12, 14, 3)
            if p > 0.62:
                col = mix(col, patina, min(1.0, (p - 0.62) * 3.5))
        if scratches and hash2(c.x - c.y, c.x // 4, c.seed + 15) < 0.015:
            col = mix(col, eg, 0.5)
        return col + (255,)
    return f


def mail(base):
    def f(c):
        ring = ((c.x % 3 == 1) and (c.y % 2 == 0)) or ((c.x % 3 == 0) and (c.y % 2 == 1))
        col = mul(base, 1.25 if ring else 0.62)
        if c.face in SIDES:
            col = mul(col, 1.08 - 0.25 * c.y / max(1, c.h - 1))
        return col + (255,)
    return f


def stone(base):
    def f(c):
        col = mul(base, 0.75 + 0.45 * _n(c, 0.12, 0.12, 20, 3))
        if abs(_n(c, 0.09, 0.09, 23, 2) - 0.5) < 0.02:
            col = mul(col, 0.5)
        if _n(c, 0.2, 0.2, 27, 2) > 0.72:
            col = mix(col, (96, 110, 70), 0.4)
        return col + (255,)
    return f


def wood(base, char=0.0):
    def f(c):
        g = math.sin(c.x * 1.3 + _n(c, 0.15, 0.04, 30, 2) * 9)
        col = mul(base, 0.86 + 0.14 * g)
        if hash2(c.x, c.y // 3, c.seed + 31) < 0.02:
            col = mul(col, 0.7)
        if char and c.face in SIDES:
            t = 1 - c.y / max(1, c.h - 1)
            if t > 1 - char:
                k = (t - (1 - char)) / char
                col = mix(col, (30, 22, 18), min(1.0, k * 1.4))
                if k > 0.7 and hash2(c.x, c.y, c.seed + 33) < 0.25:
                    return (255, 140, 40, 255, "E")
        return col + (255,)
    return f


def water(base, foam=(225, 238, 238), alpha=150, foam_amt=0.25):
    def f(c):
        n = _n(c, 0.08, 0.08, 40, 3)
        s = math.sin(c.x * 0.32 + c.y * 0.12 + n * 6)
        a = alpha + int(40 * n)
        if s > 1 - foam_amt * 2 and n > 0.45:
            return foam + (min(255, a + 70),)
        return mix(mul(base, 0.75), mul(base, 1.3), (s + 1) / 2) + (min(255, a),)
    return f


def bone_mat(base):
    def f(c):
        col = mul(base, 0.85 + 0.25 * _n(c, 0.2, 0.2, 50, 2))
        if c.face in SIDES and hash2(c.x // 2, c.y, c.seed + 51) < 0.06:
            col = mul(col, 0.85)
        return col + (255,)
    return f


def cavity(base=(48, 14, 16)):
    def f(c):
        col = mul(base, 0.6 + 0.6 * _n(c, 0.3, 0.3, 60, 2))
        if hash2(c.x, c.y, c.seed + 61) < 0.03:
            col = mix(col, (150, 70, 70), 0.5)
        return col + (255,)
    return f


def teeth(base=(226, 214, 180), point="down", gap=3):
    def f(c):
        lx, t = c.x % gap, c.x // gap
        col = mul(base, 0.85 + 0.25 * hash2(t, 2, c.seed))
        if c.face in ("north", "south"):
            if lx == gap - 1:
                return (0, 0, 0, 0)
            tipzone = c.y >= c.h // 2 if point == "down" else c.y < c.h - c.h // 2
            if tipzone and lx != (gap - 1) // 2:
                return (0, 0, 0, 0)
            root = (1 - c.y / max(1, c.h - 1)) if point == "down" else (c.y / max(1, c.h - 1))
            col = mix(col, (170, 150, 100), root * 0.35)
        return col + (255,)
    return f


def plant(base):
    def f(c):
        col = mul(base, 0.75 + 0.5 * _n(c, 0.3, 0.3, 70, 2))
        if c.x % 3 == 0:
            col = mul(col, 0.85)
        return col + (255,)
    return f


def frill(base):
    fl = flesh(base, veins=(110, 30, 40))

    def f(c):
        if c.face in SIDES and c.y < int(hash2(c.x // 2, 77, c.seed) * 4):
            return (0, 0, 0, 0)
        return fl(c)
    return f


def barnacle(base=(190, 186, 172)):
    def f(c):
        col = mul(base, 0.8 + 0.3 * _n(c, 0.4, 0.4, 80, 2))
        if c.face == "up" and abs(c.x - (c.w - 1) / 2) <= 0.6 and abs(c.y - (c.h - 1) / 2) <= 0.6:
            col = (40, 36, 34)
        return col + (255,)
    return f


# =================================================================== decals
def eye_decal(iris, sclera=(232, 220, 190), pupil=(12, 8, 8), bloodshot=True, blind_key=None, look=(0.0, 0.12)):
    def d(c, col):
        if c.face != "north":
            return col
        cx, cy = (c.w - 1) / 2, (c.h - 1) / 2
        nx, ny = (c.x - cx) / (c.w / 2), (c.y - cy) / (c.h / 2)
        r = math.sqrt(nx * nx + ny * ny)
        if r > 1.0:
            return mul(col[:3], 0.5) + (col[3],)
        if blind_key and c.variant.get(blind_key):
            n = fbm(c.x * 0.5, c.y * 0.5, c.seed + 90, 2)
            if r < 0.55:
                out = mix((22, 6, 6), (95, 14, 12), n)
            elif r < 0.85:
                out = mix((80, 30, 22), (140, 60, 40), n)
            else:
                out = mul(col[:3], 0.65)
            if ny > -0.2 and hash2(c.x, 3, c.seed + 91) < 0.35:
                out = mix(out, (125, 8, 8), 0.75)
            return out + (255,)
        out = mul(sclera, 1 - 0.3 * r * r)
        if bloodshot and r > 0.4 and abs(fbm(c.x * 0.45, c.y * 0.45, c.seed + 92, 2) - 0.5) < 0.05:
            out = mix(out, (175, 40, 38), 0.75)
        icx, icy = cx + look[0] * c.w * 0.5, cy + look[1] * c.h * 0.5
        ir = c.h * 0.38
        dp = math.hypot(c.x - icx, c.y - icy)
        if dp < ir:
            ang = math.atan2(c.y - icy, c.x - icx)
            out = mul(iris, 0.78 + 0.35 * hash2(int((ang + 3.2) * 6), 4, c.seed + 93))
            if dp > ir * 0.78:
                out = mul(out, 0.6)
            if dp < ir * 0.42:
                out = pupil
        if math.hypot(c.x - (icx - ir * 0.35), c.y - (icy - ir * 0.45)) < max(0.9, ir * 0.22):
            return (255, 250, 240, 255, "E")
        if c.y == 0:
            out = mul(out, 0.55)
        return out + (255,)
    return d


def side_eyes(color=(255, 176, 50), spots=((0.62, 0.3), (0.78, 0.22), (0.9, 0.36))):
    def d(c, col):
        if c.face not in ("east", "west"):
            return col
        for sx, sy in spots:
            ex = sx * (c.w - 1) if c.face == "east" else (1 - sx) * (c.w - 1)
            dd = math.hypot(c.x - ex, (c.y - sy * (c.h - 1)) * 1.3)
            if dd < 1.0:
                return color + (255, "E")
            if dd < 1.8:
                return mul(col[:3], 0.45) + (255,)
        return col
    return d


def ribs_decal(c, col):
    if c.face != "north":
        return col
    cx = (c.w - 1) / 2
    dx = (c.x - cx) / (c.w / 2)
    out = col[:3]
    for k in range(5):
        yk = c.h * 0.22 + k * c.h * 0.13 + dx * dx * c.h * 0.07
        dd = c.y - yk
        if 0.08 < abs(dx) < 0.92:
            if -0.6 < dd < 0.9:
                out = mul(out, 0.7)
            elif -2.2 < dd <= -0.6:
                out = mul(out, 1.09)
    if abs(c.x - cx) < 1.0 and c.y < c.h * 0.78:
        out = mul(out, 0.84)
    if c.y > c.h * 0.8:
        out = mul(out, 0.85)
    return out + (col[3],)


def face_cyclops(c, col):
    if c.face != "north":
        return col
    tx, ty = c.x / max(1, c.w - 1), c.y / max(1, c.h - 1)
    out = col[:3]
    if 0.22 < ty < 0.66 and 0.16 < tx < 0.84:
        out = mul(out, 0.58 + 0.35 * abs(tx - 0.5))
    if ty > 0.6 and (0.06 < tx < 0.2 or 0.8 < tx < 0.94):
        out = mul(out, 0.76)
    if 0.6 < ty < 0.68 and (0.18 < tx < 0.32 or 0.68 < tx < 0.82):
        out = mul(out, 1.14)
    if ty < 0.2 and int(c.y + math.sin(c.x * 0.5) * 1.3) % 3 == 0:
        out = mul(out, 0.84)
    if ty > 0.85:
        out = mul(out, 0.8)
    return out + (col[3],)


def nostrils(c, col):
    if c.face != "north":
        return col
    tx, ty = c.x / max(1, c.w - 1), c.y / max(1, c.h - 1)
    if ty > 0.62 and (0.15 < tx < 0.4 or 0.6 < tx < 0.85):
        return (30, 16, 14, 255)
    if tx < 0.12 or tx > 0.88:
        return mul(col[:3], 0.8) + (col[3],)
    return col


def face_human(iris, brow, lips, kohl=(40, 30, 32), black_eyes=False, mouth_open=0.0, age=0.0, veins=None):
    def d(c, col):
        if c.face != "north":
            return col
        tx, ty = (c.x + 0.5) / c.w, (c.y + 0.5) / c.h
        out = col[:3]
        if veins is not None and abs(fbm(c.x * 0.3, c.y * 0.3, c.seed + 5, 2) - 0.5) < 0.03:
            out = mix(out, veins, 0.4)
        if tx < 0.14 or tx > 0.86:
            out = mul(out, 0.86)
        for ex in (0.3, 0.7):
            dx = (tx - ex) / (0.16 if black_eyes else 0.13)
            dy = (ty - 0.47) / (0.085 if black_eyes else 0.06)
            r = math.hypot(dx, dy)
            if r < 1.0:
                if black_eyes:
                    if dx < -0.2 and dy < -0.1 and r < 0.55:
                        return (220, 230, 240, 255, "E")
                    return (8, 6, 8, 255)
                ir = math.hypot((tx - ex) / 0.065, (ty - 0.47) / 0.065)
                if ir < 1.0:
                    return (iris if ir > 0.45 else (15, 12, 12)) + (255,)
                return (225, 220, 205, 255)
            if r < 1.45 and (black_eyes or dy < -0.2 or (abs(dx) > 0.85 and dy < 0.4)):
                return mix(out, kohl, 0.55) + (255,)
            if not black_eyes and abs(ty - 0.34) < 0.035 and abs(tx - ex) < 0.15:
                return brow + (255,)
            if age and abs(ty - 0.56) < 0.02 and abs(tx - ex) < 0.11:
                out = mul(out, 1 - age)
        if abs(tx - 0.5) < 0.04 and 0.48 < ty < 0.64:
            out = mul(out, 0.9)
        if 0.52 < tx < 0.58 and 0.5 < ty < 0.66:
            out = mul(out, 0.84)
        if abs(ty - 0.68) < 0.025 and (0.42 < tx < 0.47 or 0.53 < tx < 0.58):
            out = mul(out, 0.7)
        if mouth_open:
            r = math.hypot((tx - 0.5) / 0.11, (ty - 0.81) / mouth_open)
            if r < 1.0:
                return ((40, 10, 14) if r < 0.75 else lips) + (255,)
        elif abs(ty - 0.8) < 0.035 and abs(tx - 0.5) < 0.13:
            return lips + (255,)
        return out + (255,)
    return d


def visor_decal(c, col):
    if c.face != "north":
        return col
    tx, ty = (c.x + 0.5) / c.w, (c.y + 0.5) / c.h
    if (0.36 < ty < 0.47 and 0.12 < tx < 0.88) or (0.45 < tx < 0.55 and 0.47 <= ty < 0.82):
        for ex in (0.32, 0.68):
            if abs(tx - ex) < 0.05 and 0.39 < ty < 0.45:
                return (200, 40, 20, 255, "E")
        return (10, 10, 12, 255)
    if ty < 0.36 and abs(tx - 0.5) < 0.04:
        return mul(col[:3], 1.3) + (255,)
    if 0.56 < ty < 0.86 and (0.18 < tx < 0.36 or 0.64 < tx < 0.82) and c.x % 3 == 1 and c.y % 3 == 1:
        return (14, 14, 16, 255)
    return col


def cuirass_decal(c, col):
    if c.face != "north":
        return col
    tx, ty = (c.x + 0.5) / c.w, (c.y + 0.5) / c.h
    out = col[:3]
    for cx0 in (0.29, 0.71):
        if abs(tx - cx0) < 0.21:
            yb = 0.36 - ((tx - cx0) / 0.21) ** 2 * 0.12
            if abs(ty - yb) < 0.025:
                out = mul(out, 0.5)
            elif 0 < yb - ty < 0.08:
                out = mul(out, 1.15)
    if 0.3 < tx < 0.7 and ty > 0.45:
        for yl in (0.52, 0.66, 0.8):
            if abs(ty - yl) < 0.018:
                out = mul(out, 0.6)
    if abs(tx - 0.5) < 0.02 and ty > 0.4:
        out = mul(out, 0.6)
    if (abs(tx - 0.16) < 0.04 or abs(tx - 0.84) < 0.04) and ty < 0.32:
        out = (160, 112, 56)
    return out + (col[3],)


def emblem_decal(c, col):
    if c.face not in ("east", "west"):
        return col
    tx, ty = (c.x + 0.5) / c.w, (c.y + 0.5) / c.h
    out = col[:3]
    if tx < 0.06 or tx > 0.94 or ty < 0.04 or ty > 0.96:
        return mix(out, (235, 200, 130), 0.5) + (255,)
    r = math.hypot((tx - 0.5) / 0.5, (ty - 0.5) / 0.5)
    if 0.78 < r < 0.84:
        out = mul(out, 0.55)
    ink = (26, 20, 18)
    if 0.46 < tx < 0.54 and 0.24 < ty < 0.8:
        out = ink
    if 0.34 < ty < 0.39 and 0.28 < tx < 0.72:
        out = ink
    for px in (0.3, 0.7):
        if abs(tx - px) < 0.04 and 0.2 < ty < 0.39:
            out = ink
    if 0.13 < ty < 0.22 and any(abs(tx - p) < 0.06 - (0.22 - ty) * 0.6 for p in (0.3, 0.5, 0.7)):
        out = ink
    return out + (255,)


def beads_decal(c, col):
    if c.face != "north":
        return col
    cx = (c.w - 1) / 2
    dx = (c.x - cx) / (c.w / 2)
    yb = 1.0 + (1 - dx * dx) * c.h * 0.3
    if abs(c.y - yb) < 0.8 and abs(dx) < 0.85:
        return [(220, 210, 190), (196, 130, 40), (130, 30, 30)][(c.x // 2) % 3] + (255,)
    tx, ty = (c.x + 0.5) / c.w, (c.y + 0.5) / c.h
    if 0.42 < tx < 0.58 and ty > 0.5 and ((c.y + c.x) % 4 == 0 or (c.y - c.x) % 4 == 0):
        return (60, 40, 25, 255)
    return col


def leaf_blade(c, col):
    if c.face not in ("north", "south"):
        return col
    ty = 1 - (c.y + 0.5) / c.h
    half = 0.5 * math.sin(math.pi * min(1.0, ty * 1.15)) ** 0.75
    dx = abs((c.x + 0.5) / c.w - 0.5)
    if dx > half:
        return (0, 0, 0, 0)
    if dx < 0.08:
        return mul(col[:3], 1.2) + (255,)
    if dx > half - 0.12:
        return mix(col[:3], (240, 240, 245), 0.5) + (255,)
    return col


def suckers(c, col):
    if c.face != "down":
        return col
    ly = c.y % 5
    if ly in (1, 2, 3) and abs(c.x - (c.w - 1) / 2) <= 1.2:
        return ((205, 170, 160) if ly != 2 else (120, 70, 70)) + (255,)
    return col


# =================================================================== model
class Model:
    def __init__(self, name, seed):
        self.name, self.seed = name, seed
        self.bones, self.index, self.paired, self.cubes = [], {}, set(), []
        self.tw = self.th = 0

    def bone(self, name, parent, pivot, rot=None):
        b = {"name": name, "pivot": [round(v, 3) for v in pivot]}
        if parent:
            b["parent"] = parent
        if rot and any(rot):
            b["rotation"] = [round(v, 3) for v in rot]
        b["cubes"] = []
        self.bones.append(b)
        self.index[name] = b
        return name

    def cube(self, bone, origin, size, mat, rot=None, pivot=None, decal=None):
        for s in size:
            assert s > 0 and abs(s * 2 - round(s * 2)) < 1e-6, (self.name, bone, size)
        cd = {"origin": [round(v, 3) for v in origin], "size": list(size)}
        if rot and any(rot):
            cd["pivot"] = [round(v, 3) for v in (pivot or (origin[0] + size[0] / 2, origin[1] + size[1] / 2,
                                                            origin[2] + size[2] / 2))]
            cd["rotation"] = [round(v, 3) for v in rot]
        self.index[bone]["cubes"].append(cd)
        self.cubes.append({"cd": cd, "mat": mat, "decal": decal or {}, "seed": self.seed * 1000 + len(self.cubes) * 37})

    @staticmethod
    def mo(origin, size):
        return (-origin[0] - size[0], origin[1], origin[2])

    @staticmethod
    def mr(rot):
        return None if rot is None else (rot[0], -rot[1], -rot[2])

    @staticmethod
    def mp(p):
        return None if p is None else (-p[0], p[1], p[2])

    def side(self, base, parent, pivot, origin, size, mat, rot=None, crot=None, decal=None):
        """Bone pair `base_r` (as given, -x side) and `base_l` (mirrored)."""
        for s in ("r", "l"):
            par = (f"{parent}_{s}" if parent in self.paired else parent) if parent else None
            pv, og, rt, cr = pivot, origin, rot, crot
            if s == "l":
                pv, og, rt, cr = self.mp(pivot), self.mo(origin, size), self.mr(rot), self.mr(crot)
            name = self.bone(f"{base}_{s}", par, pv, rt)
            self.cube(name, og, size, mat, rot=cr, decal=decal)
        self.paired.add(base)

    def side_cube(self, base, origin, size, mat, rot=None, pivot=None, decal=None):
        self.cube(f"{base}_r", origin, size, mat, rot=rot, pivot=pivot, decal=decal)
        self.cube(f"{base}_l", self.mo(origin, size), size, mat, rot=self.mr(rot), pivot=self.mp(pivot), decal=decal)

    def mcube(self, bone, origin, size, mat, rot=None, pivot=None, decal=None):
        self.cube(bone, origin, size, mat, rot=rot, pivot=pivot, decal=decal)
        self.cube(bone, self.mo(origin, size), size, mat, rot=self.mr(rot), pivot=self.mp(pivot), decal=decal)

    def pack(self):
        items = []
        for i, c in enumerate(self.cubes):
            w, h, d = c["cd"]["size"]
            items.append((d + h, 2 * (d + w), i))
        items.sort(key=lambda t: (-t[0], -t[1]))
        widest = max(t[1] for t in items)
        for W in (64, 128, 256, 512):
            if widest > W:
                continue
            x = y = row = 0
            pos = {}
            for hh, ww, i in items:
                if x + ww > W:
                    x, y, row = 0, y + row, 0
                pos[i] = (x, y)
                x += ww
                row = max(row, hh)
            H = y + row
            if H <= W:
                break
        hp = 16
        while hp < H:
            hp *= 2
        for i, (u, v) in pos.items():
            self.cubes[i]["cd"]["uv"] = [u, v]
        self.tw, self.th = W, hp

    def paint(self, variant=None):
        variant = variant or {}
        W, H = int(self.tw * D), int(self.th * D)
        img = [[(0, 0, 0, 0)] * W for _ in range(H)]
        ctx = Ctx()
        ctx.variant = variant
        for cb in self.cubes:
            w, h, d = cb["cd"]["size"]
            u, v = cb["cd"]["uv"]
            faces = (("east", u, v + d, d, h), ("north", u + d, v + d, w, h), ("west", u + d + w, v + d, d, h),
                     ("south", u + 2 * d + w, v + d, w, h), ("up", u + d, v, w, d), ("down", u + d + w, v, w, d))
            for fi, (face, fu, fv, fw, fh) in enumerate(faces):
                px0, py0 = int(round(fu * D)), int(round(fv * D))
                pw, ph = int(round(fw * D)), int(round(fh * D))
                ctx.face, ctx.w, ctx.h, ctx.seed, ctx.fo = face, pw, ph, cb["seed"], fi * 53.7
                mat = cb["mat"]
                dec = cb["decal"].get(face) or cb["decal"].get("*")
                for yy in range(ph):
                    row = img[py0 + yy]
                    ctx.y = yy
                    for xx in range(pw):
                        ctx.x = xx
                        px = mat(ctx)
                        if dec:
                            px = dec(ctx, px)
                        if len(px) > 4:
                            row[px0 + xx] = (clamp8(px[0]), clamp8(px[1]), clamp8(px[2]), px[3])
                        elif px[3] == 0:
                            row[px0 + xx] = (0, 0, 0, 0)
                        else:
                            r, g, b = grade(px[:3], lighting(ctx))
                            row[px0 + xx] = (r, g, b, clamp8(px[3]))
        return img

    def geometry(self, bounds_w, bounds_h, offset_y):
        return {"format_version": "1.12.0", "minecraft:geometry": [{
            "description": {"identifier": f"geometry.{self.name}", "texture_width": self.tw,
                            "texture_height": self.th, "visible_bounds_width": bounds_w,
                            "visible_bounds_height": bounds_h, "visible_bounds_offset": [0, offset_y, 0]},
            "bones": self.bones}]}


# =================================================================== creatures
def build_cyclops():
    """Polyphemus after Goya's 'Saturn Devouring His Son': gaunt, bald, hunched colossus,
    one huge bulging eye, gaping mouth, arms that drag near the ground."""
    m = Model("cyclops", 11)
    F = flesh((150, 132, 104), dark=(92, 76, 60), veins=(112, 86, 92), wrinkle=0.1)
    FD = flesh((118, 100, 80), dark=(70, 56, 44))
    FT = flesh((150, 132, 104), dark=(92, 76, 60), tipdark=1)
    WOOL = cloth((184, 172, 142), weave=False, tatter=3, grime=0.35)
    HAIR = hair((128, 122, 112), tips=3)
    BEARD = hair((104, 98, 90), tips=1)
    EYE = flesh((150, 132, 104))
    m.bone("root", None, (0, 0, 0))
    m.bone("hips", "root", (0, 26, 0))
    m.cube("hips", (-8, 24, -5), (16, 7, 10), F)
    m.cube("hips", (-8.5, 18, -5.5), (17, 8, 11), WOOL)
    m.bone("torso", "hips", (0, 30, 0), (25, 0, 0))
    m.cube("torso", (-9, 30, -6), (18, 16, 12), F, decal={"north": ribs_decal})
    m.cube("torso", (-11, 42, -6.5), (22, 6, 13), F)
    m.cube("torso", (-8, 46, -7), (16, 1.5, 2), FD)
    for k in range(4):
        m.cube("torso", (-1, 32 + 4 * k, 6), (2, 2, 1.5), FD)
    m.bone("neck", "torso", (0, 48, -1))
    m.cube("neck", (-3.5, 46.5, -4.5), (7, 6, 7), F)
    m.bone("head", "neck", (0, 52, -1), (-22, 0, 0))
    m.cube("head", (-7, 51, -8), (14, 13, 13), F, decal={"north": face_cyclops})
    m.cube("head", (-6, 64, -7), (12, 1.5, 11), F)
    m.cube("head", (-7.5, 59, -9.5), (15, 3, 3.5), FD)
    m.cube("head", (-4, 54.5, -9.6), (8, 5, 1.5), EYE,
           decal={"north": eye_decal((150, 108, 38), blind_key="blind")})
    m.cube("head", (-4.5, 58.5, -9.9), (9, 1, 1.5), FD)
    m.cube("head", (-2, 51.5, -10.5), (4, 3.5, 2.5), F, decal={"north": nostrils})
    m.mcube("head", (-8.5, 54, -3), (1.5, 4.5, 3), F)
    for (x, z, ln) in ((-7, 0, 12), (-6.5, 3, 14), (-5, 5.5, 10), (5.5, 1, 13), (6, 4, 11), (-2, 5.5, 9), (2.5, 5.5, 12)):
        m.cube("head", (x, 64 - ln, z), (1, ln, 1), HAIR)
    m.cube("head", (-4.5, 49.5, -8.6), (9, 1.5, 1), teeth((206, 190, 146), "down"))
    m.cube("head", (-5, 47, -8), (10, 4, 6), cavity())
    m.bone("jaw", "head", (0, 51, -2), (28, 0, 0))
    m.cube("jaw", (-5.5, 46, -9), (11, 5, 8), F)
    m.cube("jaw", (-4.5, 50.5, -8.7), (9, 1.5, 1), teeth((206, 190, 146), "up"))
    m.cube("jaw", (-5, 44.5, -8.5), (10, 2.5, 6), BEARD)
    m.side("arm", "torso", (-10.5, 44, 0), (-13.5, 28, -3), (6, 16, 6), F, rot=(-30, 0, 6))
    m.side("forearm", "arm", (-10.5, 28, 0), (-13, 13, -2.5), (5, 15, 5), F, rot=(-18, 0, -4))
    m.side("hand", "forearm", (-10.5, 13, 0), (-13, 8, -3), (5, 5, 6), FD)
    for i in range(4):
        m.side_cube("hand", (-13 + i * 1.25, 3, -2.5), (1, 5, 1), FT)
    m.side_cube("hand", (-8.5, 6, -3.5), (1, 3.5, 1), FT, rot=(0, 0, 25), pivot=(-8, 9.5, -3))
    m.side("thigh", "hips", (-5, 26, 0), (-8.5, 13, -3.5), (7, 13, 7), F, rot=(-24, 0, 4))
    m.side("shin", "thigh", (-5, 13, 0), (-8, 1, -3), (6, 12, 6), F, rot=(34, 0, -4))
    m.side_cube("shin", (-7, 10.5, -4.2), (4, 4, 1.5), FD)
    m.side("foot", "shin", (-5, 1, 0), (-9, -1.5, -9), (8, 3, 11), F, rot=(-10, 0, 0))
    for i in range(4):
        m.side_cube("foot", (-9 + i * 2, -1.5, -11), (1.5, 2, 2.5), FT)
    return m


SIREN_PALETTES = [
    {"body": (92, 70, 54), "tip": (40, 28, 22), "light": (196, 178, 150), "wing": (74, 56, 44)},    # dusk
    {"body": (82, 82, 86), "tip": (24, 24, 28), "light": (200, 198, 196), "wing": (58, 58, 62)},    # ash
    {"body": (52, 76, 80), "tip": (18, 30, 34), "light": (210, 208, 196), "wing": (40, 60, 66)},    # sea
]


def _pal(key):
    return lambda v: SIREN_PALETTES[v.get("plumage", 0)][key]


def build_siren():
    """Bird-bodied Siren (the film's sirens are birds): vulture frame, bare grey neck,
    gaunt human face with black eyes and a singing mouth, ragged wings, talons."""
    m = Model("siren", 23)
    BODY = feather(_pal("body"), _pal("tip"))
    LIGHT = feather(_pal("light"), _pal("body"))
    WING = feather(_pal("wing"), _pal("tip"))
    PRIM = feather(_pal("wing"), _pal("tip"), primary=True, tips=True)
    TAIL = feather(_pal("body"), _pal("tip"), primary=True, tips=True)
    SKIN = flesh((196, 188, 182), dark=(140, 128, 126), veins=(110, 120, 150), wrinkle=0.12)
    HAIR = hair((26, 24, 28), tips=4)
    LEG = scale_mat((150, 138, 104))
    CLAW = bone_mat((40, 34, 30))
    m.bone("root", None, (0, 0, 0))
    m.bone("body", "root", (0, 12, 0), (-6, 0, 0))
    m.cube("body", (-4.5, 8, -7), (9, 8, 15), BODY)
    m.cube("body", (-5, 11.5, -8.5), (10, 6, 4), LIGHT)
    m.cube("body", (-4, 7.5, -6), (8, 1.5, 11), LIGHT)
    m.bone("tail", "body", (0, 10.5, 7.5), (62, 0, 0))
    m.cube("tail", (-4.5, -1, 6.75), (9, 11.5, 1.5), TAIL)
    m.bone("neck", "body", (0, 15.5, -6.5), (20, 0, 0))
    m.cube("neck", (-1.5, 15, -8), (3, 7, 3), SKIN)
    m.bone("head", "neck", (0, 22, -6.5), (-14, 0, 0))
    m.cube("head", (-3.5, 22, -10), (7, 8, 7), SKIN,
           decal={"north": face_human((0, 0, 0), (0, 0, 0), (110, 100, 120), kohl=(60, 50, 60),
                                      black_eyes=True, mouth_open=0.11, veins=(120, 130, 160))})
    m.cube("head", (-4, 29, -10.5), (8, 2.5, 8), HAIR)
    m.cube("head", (-4, 17, -4), (8, 12, 3), HAIR)
    m.mcube("head", (-4, 22.5, -10.5), (1, 7, 6), HAIR)
    m.side("wing", "body", (-4.5, 15, -4), (-6, 3, -5), (1.5, 12, 11), WING, rot=(72, 0, 12))
    m.side("wingtip", "wing", (-5.25, 3, 0.5), (-6, -6, -4.5), (1, 9, 14), PRIM, rot=(4, 0, -4))
    m.side("leg", "body", (-2.5, 9, -1), (-4, 5, -3), (3, 5, 4), BODY, rot=(6, 0, 0))
    m.side("shank", "leg", (-2.5, 5, -1), (-3.25, 0, -1.75), (1.5, 5, 1.5), LEG)
    m.side("foot", "shank", (-2.5, 0.5, -1), (-3.75, 0, -4), (2.5, 1, 3.5), LEG)
    for i in range(3):
        m.side_cube("foot", (-3.75 + i * 0.85, 0, -5.5), (0.5, 1, 1.5), CLAW)
    m.side_cube("foot", (-2.75, 0, -0.5), (0.5, 1, 1.5), CLAW)
    return m


def build_circe():
    """Circe (Samantha Morton): earthy witch of Aeaea in rough-spun layers, long greying hair,
    bare forearms stained to the wrist from molding men into swine."""
    m = Model("circe", 37)
    SKIRT = cloth((116, 60, 40), tatter=2, grime=0.3)
    SKIRT_U = cloth((128, 70, 46), grime=0.15)
    DRESS = cloth((146, 116, 74))
    SHAWL = cloth((58, 70, 48), knit=True, folds=False, grime=0.1)
    SASH = cloth((70, 58, 40))
    SKIN = flesh((214, 186, 162), dark=(160, 128, 108), mottle=0.6, freckles=0.04)
    STAIN = flesh((214, 186, 162), dark=(160, 128, 108), mottle=0.6, stain=(96, 34, 28))
    HAIR = hair((104, 98, 92), streak=(170, 166, 160))
    HAIR_L = hair((104, 98, 92), tips=4, streak=(170, 166, 160))
    PLANT = plant((90, 110, 60))
    m.bone("root", None, (0, 0, 0))
    m.bone("body", "root", (0, 16, 0))
    m.bone("skirt", "body", (0, 16, 0))
    m.cube("skirt", (-6, 0, -5), (12, 10, 10), SKIRT)
    m.cube("skirt", (-5.5, 10, -4.5), (11, 6, 9), SKIRT_U)
    m.cube("body", (-5, 15.5, -3.5), (10, 2, 7), SASH)
    m.cube("body", (-4, 17, -2.5), (8, 9, 5), DRESS, decal={"north": beads_decal})
    m.cube("body", (-5, 22, -3), (10, 5, 6), SHAWL)
    m.cube("body", (3.5, 12.5, -5.5), (2, 4, 1.5), PLANT)
    m.mcube("body", (-3, 0, -6), (2.5, 1, 2.5), SKIN)
    m.bone("neck", "body", (0, 26, 0))
    m.cube("neck", (-1.5, 26, -1.5), (3, 2, 3), SKIN)
    m.bone("head", "neck", (0, 28, 0))
    m.cube("head", (-4, 28, -4), (8, 8, 8), SKIN,
           decal={"north": face_human((150, 168, 150), (70, 62, 58), (132, 58, 58), age=0.12)})
    m.cube("head", (-4.5, 35, -4.5), (9, 2, 9), HAIR)
    m.mcube("head", (-4.5, 27, -4.5), (1, 8.5, 7), HAIR_L)
    m.cube("head", (-4, 34, -4.6), (3, 1.5, 1), HAIR)
    m.cube("head", (1, 33.5, -4.6), (3, 2, 1), HAIR)
    m.bone("hair", "head", (0, 34, 3))
    m.cube("hair", (-4.5, 17, 1.5), (9, 18, 3), HAIR_L)
    m.side("arm", "body", (-5, 25, 0), (-6.5, 15, -1.5), (2.5, 10, 3), SKIN, rot=(0, 0, 6))
    m.side_cube("arm", (-7, 21, -2), (3.5, 4.5, 4), DRESS)
    m.side("forearm", "arm", (-5.25, 15, 0), (-6.5, 8, -1.5), (2.5, 7, 3), STAIN)
    m.side("hand", "forearm", (-5.25, 8, 0), (-6.75, 4.5, -2), (3, 3.5, 3.5), flesh((112, 52, 40), dark=(70, 26, 22)))
    return m


def build_scylla():
    """Scylla (del Toro-inspired): barnacled mass with eight tentacles and six serpentine
    necks ending in eyeless-snouted heads with rows of teeth and small burning side eyes."""
    m = Model("scylla", 53)
    HIDE = flesh((104, 104, 96), dark=(60, 62, 58), veins=(70, 50, 60))
    UNDER = flesh((170, 160, 146), dark=(130, 118, 104))
    NECK = flesh((138, 128, 118), dark=(88, 80, 74), rings=3, ventral=(186, 172, 150))
    HEAD = flesh((96, 90, 84), dark=(56, 52, 50), veins=(140, 120, 110))
    HEADD = flesh((70, 66, 62), dark=(40, 38, 36))
    TENT = flesh((120, 112, 104), dark=(72, 66, 62))
    UP_T, LOW_T = teeth((232, 222, 196), "down"), teeth((232, 222, 196), "up")
    m.bone("root", None, (0, 0, 0))
    m.bone("body", "root", (0, 8, 0))
    m.cube("body", (-11, 1, -9), (22, 12, 18), HIDE)
    m.cube("body", (-12.5, 3.5, -6), (25, 8, 12), HIDE)
    m.cube("body", (-7, 2.5, -11), (14, 9, 2.5), HIDE)
    m.cube("body", (-7, 2.5, 8.5), (14, 8, 3), HIDE)
    m.cube("body", (-8, 12.5, -7), (16, 5.5, 14), HIDE)
    m.cube("body", (-5, 17.5, -4.5), (10, 1.5, 8), HIDE)
    m.cube("body", (-9.5, 0, -7.5), (19, 2, 15), UNDER)
    for (x, y, z, s) in ((-9, 12.5, -6, 2), (7, 12.5, 4, 2.5), (-4, 17.5, 5, 1.5), (9.5, 6, -3, 2), (-10.5, 8, 3, 2),
                         (2, 17.5, -6, 1.5), (-6, 4, -9.5, 2), (5, 9, 8.5, 2), (-2, 17.5, 1, 1.5), (10, 3, 6, 1.5)):
        m.cube("body", (x, y, z), (s, 1.0 if s < 2 else 1.5, s), barnacle())
    for k in range(8):
        a = math.radians(22.5 + k * 45)
        dx, dz = math.sin(a), math.cos(a)
        bx, bz = round(dx * 10, 2), round(dz * 8.5, 2)
        theta = math.degrees(math.atan2(-dx, -dz))
        parent, L = "body", 6
        for s, (w, rx) in enumerate(((3, 14), (2.5, -14), (2, -20))):
            name = m.bone(f"tent_{k}_{s}", parent, (bx, 2.5, bz - L * s), (rx, theta, 0) if s == 0 else (rx, 0, 0))
            m.cube(name, (bx - w / 2, 2.5 - w / 2, bz - L * (s + 1)), (w, w, L), TENT, decal={"down": suckers})
            parent = name
    necks = [(-5, -4, 34, -26), (-1.5, -5.5, 40, -8), (2, -5.5, 38, 10), (5.5, -4, 32, 28),
             (-4, 2, 16, -36), (4, 2, 18, 34)]
    widths, L = (5, 4.5, 4, 3.5, 3), 6
    curves = ((0, -18, -12, 8, 12), (0, -10, -18, 12, 6))
    for i, (bx, bz, lean, side) in enumerate(necks):
        seg_rx = curves[i % 2]
        parent, y = "body", 18.5
        for s, w in enumerate(widths):
            rot = (lean, 0, side) if s == 0 else (seg_rx[s], 0, 0)
            name = m.bone(f"neck_{i}_{s}", parent, (bx, y, bz), rot)
            m.cube(name, (bx - w / 2, y, bz - w / 2), (w, L, w), NECK)
            parent, y = name, y + L
        top = y
        pitch = lean + sum(seg_rx)
        hb = m.bone(f"head_{i}", parent, (bx, top, bz), (-pitch + 10, 0, -side * 0.7))
        m.cube(hb, (bx - 3.5, top - 1, bz - 4), (7, 6, 8), HEAD, decal={"east": side_eyes(), "west": side_eyes()})
        m.cube(hb, (bx - 4, top + 4, bz - 3.5), (8, 1.5, 3.5), HEADD)
        m.cube(hb, (bx - 2.5, top, bz - 9.5), (5, 3.5, 5.5), HEAD)
        m.cube(hb, (bx - 2.5, top - 1.5, bz - 9.7), (5, 1.5, 1), UP_T)
        m.cube(hb, (bx - 2.5, top - 1.5, bz - 9), (5, 1.5, 6), cavity((90, 24, 32)))
        m.cube(hb, (bx - 4.5, top - 0.5, bz - 0.5), (1, 5, 3.5), frill((150, 64, 62)))
        m.cube(hb, (bx + 3.5, top - 0.5, bz - 0.5), (1, 5, 3.5), frill((150, 64, 62)))
        jb = m.bone(f"jaw_{i}", hb, (bx, top - 0.5, bz - 2.5), (32, 0, 0))
        m.cube(jb, (bx - 3, top - 2.5, bz - 10), (6, 2, 7.5), HEAD)
        m.cube(jb, (bx - 2.5, top - 0.5, bz - 9.9), (5, 1.5, 1), LOW_T)
    return m


RINGS = (44, 37, 30, 24, 18, 12, 7)


def build_charybdis():
    """Charybdis: a living whirlpool, concentric octagonal rings of churning water spiralling
    down to a dark throat, with wreck debris caught in the current."""
    m = Model("charybdis", 71)
    FOAM = water((70, 120, 130), alpha=200, foam_amt=0.45)
    WAT = water((30, 74, 92), alpha=165, foam_amt=0.2)
    DEEP = water((12, 30, 40), alpha=225, foam_amt=0.05)
    WOOD = wood((96, 72, 48))
    m.bone("root", None, (0, 0, 0))
    t = 3
    for k, r in enumerate(RINGS):
        y = -k * 4.5
        mat = FOAM if k < 2 else WAT if k < 4 else DEEP
        hh = 2.5
        for suffix, rest in (("a", 0), ("b", 45)):
            name = m.bone(f"ring{suffix}_{k}", "root", (0, y, 0), (0, rest + k * 11, 0))
            m.cube(name, (-r, y, -r), (2 * r, hh, t), mat)
            m.cube(name, (-r, y, r - t), (2 * r, hh, t), mat)
            m.cube(name, (-r, y, -r + t), (t, hh, 2 * r - 2 * t), mat)
            m.cube(name, (r - t, y, -r + t), (t, hh, 2 * r - 2 * t), mat)
    m.bone("core", "root", (0, -14, 0))
    m.cube("core", (-3, -36, -3), (6, 32, 6), DEEP)
    m.cube("ringa_1", (18, -3.5, -31), (7, 1, 2), WOOD, rot=(0, 25, 8))
    m.cube("ringb_3", (-16, -13, 4), (5, 1, 1.5), WOOD, rot=(0, -40, -10))
    m.cube("ringa_2", (-6, -8, 22), (6, 1.5, 1.5), WOOD, rot=(0, 70, 15))
    return m


def build_laestrygonian():
    """Laestrygonian giant: blackened plate with bronze trim (armour 'more sophisticated than
    anything Odysseus had seen'), closed T-visor helm with a horsehair crest, spear and tower shield."""
    m = Model("laestrygonian", 89)
    STEEL = metal((54, 56, 62), edge=(150, 152, 160))
    BANDS = metal((54, 56, 62), edge=(150, 152, 160), bands=4)
    BRONZE = metal((150, 104, 52), edge=(232, 190, 120), patina=(70, 112, 92), rivets=False)
    MAIL = mail((84, 86, 92))
    LEATHER = cloth((70, 50, 34), weave=False, grime=0.25)
    CREST = hair((24, 20, 20), tips=2)
    WOOD = wood((76, 56, 38))
    BLADE = metal((168, 170, 176), edge=(236, 236, 242), rivets=False, scratches=False)
    m.bone("root", None, (0, 0, 0))
    m.bone("hips", "root", (0, 24, 0))
    m.cube("hips", (-7.5, 22.5, -5.5), (15, 2.5, 11), BRONZE)
    m.cube("hips", (-7, 14, -5), (14, 8.5, 10), BANDS)
    m.bone("torso", "hips", (0, 25, 0))
    m.cube("torso", (-8, 25, -5), (16, 13, 10), STEEL, decal={"north": cuirass_decal})
    m.cube("torso", (-4.5, 37.5, -4.5), (9, 2.5, 9), STEEL)
    m.bone("head", "torso", (0, 40, 0))
    m.cube("head", (-4.5, 40, -5), (9, 10, 10), STEEL, decal={"north": visor_decal})
    m.cube("head", (-5, 44, -5.5), (10, 1, 11), BRONZE)
    m.cube("head", (-1, 50, -6), (2, 1.5, 12), BRONZE)
    m.cube("head", (-1, 51.5, -7), (2, 5, 14), CREST)
    m.mcube("head", (-5.5, 40, -5.5), (1, 6, 4.5), STEEL)
    m.side("arm", "torso", (-10, 36, 0), (-12.5, 26, -2.5), (5, 10, 5), MAIL, rot=(0, 0, 8))
    m.side_cube("arm", (-14, 33, -6), (6.5, 5, 12), BANDS, rot=(0, 0, -15), pivot=(-10.5, 35.5, 0))
    m.side("forearm", "arm", (-10, 26, 0), (-12.5, 15, -2.5), (5, 11, 5), STEEL)
    m.side_cube("forearm", (-13, 10.5, -3), (6, 4.5, 6), STEEL)
    m.bone("spear", "forearm_r", (-10, 13, 0))
    m.cube("spear", (-10.75, 0, -0.75), (1.5, 58, 1.5), WOOD)
    m.cube("spear", (-11, 56, -1), (2, 2, 2), BRONZE)
    m.cube("spear", (-11.5, 58, -0.5), (3, 10, 1), BLADE, decal={"north": leaf_blade, "south": leaf_blade})
    m.bone("shield", "forearm_l", (10, 20, 0))
    m.cube("shield", (12.5, 6, -8.5), (1.5, 26, 17), BRONZE, decal={"east": emblem_decal, "west": emblem_decal})
    m.cube("shield", (14, 17, -2), (1.5, 4, 4), BRONZE)
    m.side("thigh", "hips", (-4, 22, 0), (-7, 11.5, -3), (6, 11, 6), LEATHER)
    m.side("shin", "thigh", (-4, 11.5, 0), (-7, 1.5, -3), (6, 10, 6), STEEL)
    m.side("foot", "shin", (-4, 1.5, 0), (-7.5, 0, -6), (7, 2.5, 9), STEEL)
    return m


def build_boulder():
    m = Model("boulder", 97)
    S = stone((118, 112, 104))
    m.bone("rock", None, (0, 4, 0))
    m.cube("rock", (-4, 0, -4), (8, 8, 8), S, rot=(10, 20, 5), pivot=(0, 4, 0))
    m.cube("rock", (-3, 1, -5), (6, 6, 10), S, rot=(30, -15, 20), pivot=(0, 4, 0))
    m.cube("rock", (-5, 2, -3), (10, 5, 6), S, rot=(-20, 40, -10), pivot=(0, 4, 0))
    return m


# =================================================================== animations (Molang)
def A(bones, loop=True, length=None):
    a = {"loop": loop, "bones": bones}
    if length:
        a["animation_length"] = length
    return a


def rot(x=0, y=0, z=0):
    return {"rotation": [x, y, z]}


STRIDE = "q.modified_distance_moved*14"


def anims_cyclops():
    s = STRIDE
    return {
        "idle": A({"torso": rot("math.sin(q.life_time*70)*1.5"),
                   "head": rot("math.sin(q.life_time*45)*3", "math.sin(q.life_time*21)*10", "math.sin(q.life_time*33)*3"),
                   "jaw": rot("math.max(0, math.sin(q.life_time*55))*8"),
                   "arm_r": rot("math.sin(q.life_time*60)*2", 0, "math.sin(q.life_time*30)*2"),
                   "arm_l": rot("-math.sin(q.life_time*60)*2", 0, "-math.sin(q.life_time*30)*2")}),
        "walk": A({"thigh_r": rot(f"math.cos({s})*24"), "thigh_l": rot(f"-math.cos({s})*24"),
                   "shin_r": rot(f"math.max(0, math.sin({s}))*28"), "shin_l": rot(f"math.max(0, -math.sin({s}))*28"),
                   "arm_r": rot(f"-math.cos({s})*16"), "arm_l": rot(f"math.cos({s})*16"),
                   "torso": rot(0, f"math.cos({s})*5", f"math.cos({s})*4"),
                   "hips": {"position": [0, f"-math.abs(math.sin({s}))*1.5", 0]}}),
        "grab": A({"arm_r": rot(-75, 0, 10), "forearm_r": rot(-25), "jaw": rot(22), "head": rot(-8), "torso": rot(8)}),
        "throw": A({"arm_r": {"rotation": {"0.0": [0, 0, 0], "0.3": [-170, 0, 10], "0.45": [-60, 0, 0], "0.75": [0, 0, 0]}},
                    "torso": {"rotation": {"0.0": [0, 0, 0], "0.3": [-10, 0, 0], "0.45": [15, 0, 0], "0.75": [0, 0, 0]}}},
                   loop=False, length=0.75),
        "cry": A({"head": rot(-35, "math.sin(q.life_time*400)*6"), "jaw": rot(30),
                  "arm_r": rot(-120, 0, -25), "arm_l": rot(-120, 0, 25), "forearm_r": rot(-40), "forearm_l": rot(-40)}),
        "drunk": A({"torso": rot(0, 0, "math.sin(q.life_time*80)*9"),
                    "head": rot("10+math.sin(q.life_time*50)*6", 0, "math.sin(q.life_time*65)*14"),
                    "arm_r": rot(0, 0, "8+math.sin(q.life_time*60)*6"), "arm_l": rot(0, 0, "-8-math.sin(q.life_time*60)*6")}),
        "asleep": A({"root": {"rotation": [-90, 0, 0], "position": [0, 6, 0]},
                     "head": rot(0, 30, 0), "jaw": rot("math.max(0, math.sin(q.life_time*40))*14"),
                     "arm_r": rot(0, 0, 25), "arm_l": rot(0, 0, -25), "thigh_r": rot(10, 0, 8), "thigh_l": rot(10, 0, -8)}),
        "blind_search": A({"head": rot(0, "math.sin(q.life_time*120)*25", 0)}),
    }


ANIMATE_CYCLOPS = ["idle",
                   {"walk": "q.modified_move_speed > 0.05 && q.property('studio:state') != 'asleep'"},
                   {"grab": "q.property('studio:anim') == 'grab'"},
                   {"throw": "q.property('studio:anim') == 'throw'"},
                   {"cry": "q.property('studio:anim') == 'cry'"},
                   {"drunk": "q.property('studio:state') == 'drunk'"},
                   {"asleep": "q.property('studio:state') == 'asleep'"},
                   {"blind_search": "q.property('studio:blind')"}]


def anims_siren():
    flap = "q.life_time*480"
    return {
        "fly": A({"wing_r": rot(0, 0, f"25+(math.sin({flap})+1)*35"), "wing_l": rot(0, 0, f"-25-(math.sin({flap})+1)*35"),
                  "wingtip_r": rot(0, 0, f"math.sin({flap}-40)*20"), "wingtip_l": rot(0, 0, f"-math.sin({flap}-40)*20"),
                  "body": {"position": [0, f"math.sin({flap}+90)*1.0", 0]},
                  "tail": rot("math.sin(q.life_time*240)*6"),
                  "leg_r": rot("20+math.sin(q.life_time*200)*5"), "leg_l": rot("20+math.sin(q.life_time*200+60)*5"),
                  "head": rot("math.sin(q.life_time*60)*4", "math.sin(q.life_time*30)*12")}),
        "sing": A({"head": rot(-25, 0, "math.sin(q.life_time*150)*6"), "neck": rot(-10),
                   "body": rot(0, 0, "math.sin(q.life_time*900)*1.5")}),
    }


ANIMATE_SIREN = ["fly", {"sing": "q.property('studio:anim') == 'sing'"}]


def anims_circe():
    s = "q.modified_distance_moved*30"
    return {
        "idle": A({"hair": rot("math.sin(q.life_time*50)*3", 0, "math.sin(q.life_time*37)*2"),
                   "head": rot("math.sin(q.life_time*30)*3", "math.sin(q.life_time*18)*10"),
                   "arm_r": rot("math.sin(q.life_time*40)*2"), "arm_l": rot("-math.sin(q.life_time*40)*2"),
                   "skirt": rot(0, 0, "math.sin(q.life_time*45)*1")}),
        "walk": A({"arm_r": rot(f"math.cos({s})*18"), "arm_l": rot(f"-math.cos({s})*18"),
                   "skirt": rot(0, 0, f"math.cos({s})*3"), "body": {"position": [0, f"math.abs(math.sin({s}))*0.4", 0]}}),
        "mold": A({"arm_r": rot(-65, 10, 0), "arm_l": rot(-65, -10, 0),
                   "forearm_r": rot("-25+math.sin(q.life_time*720)*18"), "forearm_l": rot("-25-math.sin(q.life_time*720)*18"),
                   "hand_r": rot(0, 0, "math.sin(q.life_time*900)*20"), "hand_l": rot(0, 0, "-math.sin(q.life_time*900)*20"),
                   "head": rot(15), "hair": rot(-8)}),
        "yielded": A({"head": rot(8), "arm_r": rot(-12, 0, 6), "arm_l": rot(-12, 0, -6)}),
    }


ANIMATE_CIRCE = ["idle", {"walk": "q.modified_move_speed > 0.05"},
                 {"mold": "q.property('studio:anim') == 'mold'"}, {"yielded": "q.property('studio:yielded')"}]


def anims_scylla():
    idle, snatch, walk = {}, {}, {}
    for i in range(6):
        for s in range(5):
            idle[f"neck_{i}_{s}"] = rot(f"math.sin(q.life_time*70+{i * 61 + s * 37})*5", 0,
                                        f"math.cos(q.life_time*55+{i * 47 + s * 29})*4")
        idle[f"jaw_{i}"] = rot(f"math.max(0, math.sin(q.life_time*110+{i * 83}))*22")
        idle[f"head_{i}"] = rot(f"math.sin(q.life_time*90+{i * 50})*6", f"math.sin(q.life_time*40+{i * 70})*12")
        snatch[f"neck_{i}_0"] = rot(f"-30+math.sin(q.life_time*500+{i * 60})*8")
        snatch[f"jaw_{i}"] = rot(38)
    for k in range(8):
        for s in range(3):
            idle[f"tent_{k}_{s}"] = rot(f"math.sin(q.life_time*80+{k * 45 + s * 40})*9", f"math.cos(q.life_time*50+{k * 30})*4")
        walk[f"tent_{k}_0"] = rot(f"math.sin(q.modified_distance_moved*40+{k * 45})*18")
    idle["body"] = {"position": [0, "math.sin(q.life_time*40)*0.6", 0]}
    return {"idle": A(idle), "walk": A(walk), "snatch": A(snatch)}


ANIMATE_SCYLLA = ["idle", {"walk": "q.modified_move_speed > 0.05"}, {"snatch": "q.property('studio:anim') == 'snatch'"}]


def anims_charybdis():
    bones = {"core": rot(0, "q.life_time*360", 0)}
    for k in range(len(RINGS)):
        for sfx in ("a", "b"):
            bones[f"ring{sfx}_{k}"] = rot(0, f"q.life_time*{90 + k * 45}", 0)
    return {"swirl": A(bones)}


def anims_laestrygonian():
    s = "q.modified_distance_moved*16"
    return {
        "idle": A({"torso": rot("math.sin(q.life_time*60)*1.2"), "head": rot(0, "math.sin(q.life_time*20)*18"),
                   "shield": rot(0, 0, "math.sin(q.life_time*40)*1.5")}),
        "walk": A({"thigh_r": rot(f"math.cos({s})*26"), "thigh_l": rot(f"-math.cos({s})*26"),
                   "shin_r": rot(f"math.max(0, math.sin({s}))*30"), "shin_l": rot(f"math.max(0, -math.sin({s}))*30"),
                   "arm_r": rot(f"-math.cos({s})*10"), "arm_l": rot(f"math.cos({s})*10"),
                   "torso": rot(0, f"math.cos({s})*4"), "hips": {"position": [0, f"-math.abs(math.sin({s}))*1.2", 0]}}),
        "charge": A({"arm_r": rot(-80), "spear": rot(180), "torso": rot(15), "arm_l": rot(-50),
                     "thigh_r": rot(-25), "thigh_l": rot(15)}),
        "throw": A({"arm_r": {"rotation": {"0.0": [0, 0, 0], "0.3": [-165, 0, 0], "0.45": [-50, 0, 0], "0.75": [0, 0, 0]}}},
                   loop=False, length=0.75),
    }


ANIMATE_LAESTRYGONIAN = ["idle", {"walk": "q.modified_move_speed > 0.05"},
                         {"charge": "q.property('studio:anim') == 'charge'"},
                         {"throw": "q.property('studio:anim') == 'throw'"}]


def anims_boulder():
    return {"spin": A({"rock": rot("q.life_time*400", "q.life_time*250", 0)})}


# =================================================================== behaviors
def ai_basic(stroll=6, look=7):
    return {
        "minecraft:behavior.float": {"priority": 0},
        "minecraft:behavior.random_stroll": {"priority": stroll, "speed_multiplier": 0.9},
        "minecraft:behavior.look_at_player": {"priority": look, "look_distance": 14, "probability": 0.5},
        "minecraft:behavior.random_look_around": {"priority": look + 1},
    }


def target(prio, max_dist, families=("player",), must_see=True, extra=None):
    flt = {"any_of": [{"test": "is_family", "subject": "other", "value": f} for f in families]}
    if extra:
        flt = {"all_of": [flt] + extra}
    return {"priority": prio, "must_see": must_see, "reselect_targets": True, "scan_interval": 5,
            "entity_types": [{"filters": flt, "max_dist": max_dist}]}


def enum_prop(values, default=None):
    return {"type": "enum", "values": values, "default": default or values[0], "client_sync": True}


BOOL = {"type": "bool", "default": False, "client_sync": True}
NO_FALL = {"cause": "fall", "deals_damage": False}


def entity(identifier, props, comps, groups=None, events=None, spawnable=True):
    desc = {"identifier": identifier, "is_spawnable": spawnable, "is_summonable": True, "is_experimental": False}
    if props:
        desc["properties"] = props
    body = {"description": desc, "components": comps}
    if groups:
        body["component_groups"] = groups
    if events:
        body["events"] = events
    return {"format_version": "1.21.0", "minecraft:entity": body}


def common(families, w, h, hp, speed, loot=None, sound_every=10):
    c = {"minecraft:type_family": {"family": families + ["studio_odyssey", "mob"]},
         "minecraft:collision_box": {"width": w, "height": h},
         "minecraft:health": {"value": hp, "max": hp},
         "minecraft:movement": {"value": speed},
         "minecraft:physics": {},
         "minecraft:nameable": {},
         "minecraft:follow_range": {"value": 32, "max": 48},
         "minecraft:ambient_sound_interval": {"value": sound_every, "range": 10, "event_name": "ambient"}}
    if loot:
        c["minecraft:loot"] = {"table": f"loot_tables/entities/{loot}.json"}
    return c


def bp_cyclops():
    c = common(["cyclops", "giant", "monster"], 1.9, 3.8, 160, 0.21, "cyclops")
    c.update({
        "minecraft:movement.basic": {}, "minecraft:jump.static": {},
        "minecraft:navigation.walk": {"can_path_over_water": False, "avoid_water": True, "avoid_damage_blocks": True},
        "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
        "minecraft:knockback_resistance": {"value": 0.8},
        "minecraft:attack": {"damage": 9},
        "minecraft:damage_sensor": {"triggers": [NO_FALL]},
        "minecraft:interact": {"interactions": [{
            "on_interact": {"filters": {"all_of": [
                {"test": "is_family", "subject": "other", "value": "player"},
                {"test": "has_equipment", "subject": "other", "domain": "hand", "value": "studio:maronian_wine"},
                {"test": "enum_property", "subject": "self", "domain": "studio:state", "operator": "!=", "value": "asleep"}]},
                "event": "studio:drink_wine", "target": "self"},
            "use_item": True, "interact_text": "action.interact.studio.wine"}]},
    })
    ai = ai_basic()
    ai["minecraft:behavior.hurt_by_target"] = {"priority": 1}
    ai["minecraft:behavior.melee_attack"] = {"priority": 3, "speed_multiplier": 1.15, "track_target": True}
    groups = {
        "studio:awake_ai": ai,
        "studio:hunting": {"minecraft:behavior.nearest_attackable_target": target(2, 32)},
        "studio:blind_hunting": {"minecraft:behavior.nearest_attackable_target": target(
            2, 9, must_see=False, extra=[{"test": "is_sneaking", "subject": "other", "value": False}])},
        "studio:drunk": {"minecraft:movement": {"value": 0.09}},
        "studio:asleep": {"minecraft:movement": {"value": 0.0}},
    }
    events = {
        "minecraft:entity_spawned": {"add": {"component_groups": ["studio:awake_ai"]}},
        "studio:anger": {"add": {"component_groups": ["studio:hunting"]}},
        "studio:drink_wine": {"set_property": {"studio:state": "drunk"}, "add": {"component_groups": ["studio:drunk"]}},
        "studio:fall_asleep": {"set_property": {"studio:state": "asleep"},
                               "remove": {"component_groups": ["studio:awake_ai", "studio:hunting", "studio:blind_hunting", "studio:drunk"]},
                               "add": {"component_groups": ["studio:asleep"]}},
        "studio:wake": {"set_property": {"studio:state": "awake"},
                        "remove": {"component_groups": ["studio:asleep", "studio:drunk"]},
                        "add": {"component_groups": ["studio:awake_ai"]}},
        "studio:blinded": {"set_property": {"studio:blind": True, "studio:state": "awake"},
                           "remove": {"component_groups": ["studio:asleep", "studio:drunk", "studio:hunting"]},
                           "add": {"component_groups": ["studio:awake_ai", "studio:blind_hunting"]}},
    }
    props = {"studio:state": enum_prop(["awake", "drunk", "asleep"]), "studio:blind": BOOL,
             "studio:anim": enum_prop(["none", "grab", "throw", "cry"])}
    return entity("studio:cyclops", props, c, groups, events)


def bp_siren():
    c = common(["siren", "monster"], 0.8, 1.6, 36, 0.3, "siren", sound_every=6)
    c.update({
        "minecraft:flying_speed": {"value": 0.16},
        "minecraft:movement.hover": {}, "minecraft:can_fly": {},
        "minecraft:navigation.hover": {"can_path_over_water": True, "can_sink": False, "can_pass_doors": False,
                                       "can_path_from_air": True, "avoid_water": True, "avoid_damage_blocks": True},
        "minecraft:physics": {"has_gravity": False},
        "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
        "minecraft:damage_sensor": {"triggers": [NO_FALL]},
        "minecraft:attack": {"damage": 5},
        "minecraft:behavior.random_hover": {"priority": 7, "xz_dist": 10, "y_dist": 6, "y_offset": -1,
                                            "interval": 1, "hover_height": [2, 6]},
        "minecraft:behavior.look_at_player": {"priority": 8, "look_distance": 16},
        "minecraft:behavior.hurt_by_target": {"priority": 1},
        "minecraft:behavior.nearest_attackable_target": target(2, 20),
        "minecraft:behavior.melee_attack": {"priority": 3, "speed_multiplier": 1.4, "track_target": True},
    })
    events = {"minecraft:entity_spawned": {"randomize": [
        {"weight": 1, "set_property": {"studio:plumage": 0}},
        {"weight": 1, "set_property": {"studio:plumage": 1}},
        {"weight": 1, "set_property": {"studio:plumage": 2}}]}}
    props = {"studio:plumage": {"type": "int", "range": [0, 2], "default": 0, "client_sync": True},
             "studio:anim": enum_prop(["none", "sing"])}
    return entity("studio:siren", props, c, None, events)


def bp_circe():
    c = common(["circe", "goddess"], 0.7, 2.3, 80, 0.24, "circe", sound_every=14)
    c.update({
        "minecraft:movement.basic": {}, "minecraft:jump.static": {},
        "minecraft:navigation.walk": {"can_path_over_water": False, "avoid_water": True, "can_pass_doors": True,
                                      "can_open_doors": True},
        "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
        "minecraft:attack": {"damage": 4},
        "minecraft:damage_sensor": {"triggers": [NO_FALL]},
        "minecraft:interact": {"interactions": [
            {"on_interact": {"filters": {"all_of": [
                {"test": "is_family", "subject": "other", "value": "player"},
                {"test": "bool_property", "subject": "self", "domain": "studio:yielded", "value": False}]},
                "event": "studio:offer_feast", "target": "self"},
             "cooldown": 30, "interact_text": "action.interact.studio.feast"},
            {"on_interact": {"filters": {"all_of": [
                {"test": "is_family", "subject": "other", "value": "player"},
                {"test": "bool_property", "subject": "self", "domain": "studio:yielded", "value": True}]},
                "event": "studio:counsel", "target": "self"},
             "cooldown": 10, "interact_text": "action.interact.studio.counsel"}]},
    })
    ai = ai_basic()
    ai["minecraft:behavior.hurt_by_target"] = {"priority": 1}
    ai["minecraft:behavior.melee_attack"] = {"priority": 2, "speed_multiplier": 1.0, "track_target": True}
    groups = {
        "studio:witch_ai": ai,
        "studio:yielded": dict(ai_basic(), **{"minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": False}]}}),
    }
    events = {
        "minecraft:entity_spawned": {"add": {"component_groups": ["studio:witch_ai"]}},
        "studio:offer_feast": {"set_property": {"studio:anim": "none"}},
        "studio:counsel": {"set_property": {"studio:anim": "none"}},
        "studio:yield": {"set_property": {"studio:yielded": True},
                         "remove": {"component_groups": ["studio:witch_ai"]},
                         "add": {"component_groups": ["studio:yielded"]}},
    }
    props = {"studio:anim": enum_prop(["none", "mold"]), "studio:yielded": BOOL}
    return entity("studio:circe", props, c, groups, events)


def bp_scylla():
    c = common(["scylla", "monster", "aquatic"], 2.4, 3.0, 300, 0.18, "scylla", sound_every=8)
    c.update({
        "minecraft:underwater_movement": {"value": 0.12},
        "minecraft:movement.amphibious": {"max_turn": 5},
        "minecraft:navigation.generic": {"is_amphibious": True, "can_path_over_water": False, "can_swim": True,
                                         "can_walk": True, "can_breach": True, "can_sink": True, "avoid_damage_blocks": True},
        "minecraft:breathable": {"breathes_water": True, "breathes_air": True, "total_supply": 15, "suffocate_time": 0},
        "minecraft:jump.static": {},
        "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
        "minecraft:knockback_resistance": {"value": 1.0},
        "minecraft:damage_sensor": {"triggers": [NO_FALL, {"cause": "drowning", "deals_damage": False}]},
        "minecraft:attack": {"damage": 8},
        "minecraft:behavior.random_swim": {"priority": 7, "speed_multiplier": 1.0, "xz_dist": 10, "y_dist": 7},
        "minecraft:behavior.random_stroll": {"priority": 8, "speed_multiplier": 0.8},
        "minecraft:behavior.hurt_by_target": {"priority": 1},
        "minecraft:behavior.nearest_attackable_target": target(2, 28, ("player", "villager")),
        "minecraft:behavior.melee_attack": {"priority": 3, "speed_multiplier": 1.2, "track_target": True},
        "minecraft:behavior.look_at_player": {"priority": 9, "look_distance": 16},
    })
    return entity("studio:scylla", {"studio:anim": enum_prop(["none", "snatch"])}, c)


def bp_charybdis():
    c = {"minecraft:type_family": {"family": ["charybdis", "studio_odyssey", "inanimate"]},
         "minecraft:collision_box": {"width": 1.0, "height": 0.5},
         "minecraft:health": {"value": 1000, "max": 1000},
         "minecraft:physics": {"has_gravity": False, "has_collision": False},
         "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
         "minecraft:knockback_resistance": {"value": 1.0},
         "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": False}]},
         "minecraft:persistent": {},
         "minecraft:ambient_sound_interval": {"value": 3, "range": 2, "event_name": "ambient"}}
    return entity("studio:charybdis", None, c)


def bp_laestrygonian():
    c = common(["laestrygonian", "giant", "monster"], 1.4, 3.4, 110, 0.23, "laestrygonian")
    c.update({
        "minecraft:movement.basic": {}, "minecraft:jump.static": {},
        "minecraft:navigation.walk": {"can_path_over_water": False, "avoid_water": True, "avoid_damage_blocks": True},
        "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
        "minecraft:knockback_resistance": {"value": 0.7},
        "minecraft:attack": {"damage": 11},
        "minecraft:damage_sensor": {"triggers": [NO_FALL, {"cause": "projectile", "deals_damage": False}]},
        "minecraft:behavior.hurt_by_target": {"priority": 1},
        "minecraft:behavior.nearest_attackable_target": target(2, 32, ("player", "villager")),
        "minecraft:behavior.melee_attack": {"priority": 3, "speed_multiplier": 1.2, "track_target": True},
    })
    c.update(ai_basic())
    return entity("studio:laestrygonian", {"studio:anim": enum_prop(["none", "charge", "throw"])}, c)


def bp_boulder():
    c = {"minecraft:type_family": {"family": ["studio_boulder", "inanimate"]},
         "minecraft:collision_box": {"width": 0.6, "height": 0.6},
         "minecraft:health": {"value": 1, "max": 1},
         "minecraft:physics": {"has_gravity": False, "has_collision": False},
         "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
         "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": False}]}}
    return entity("studio:boulder", None, c, spawnable=False)


# =================================================================== client side
def client_entity(name, textures, rc, animations, animate, egg=None, material="entity_alphatest"):
    desc = {"identifier": f"studio:{name}", "materials": {"default": material}, "textures": textures,
            "geometry": {"default": f"geometry.{name}"}, "render_controllers": [rc],
            "animations": {k: f"animation.{name}.{k}" for k in animations}, "scripts": {"animate": animate}}
    if egg:
        desc["spawn_egg"] = {"base_color": egg[0], "overlay_color": egg[1]}
    return {"format_version": "1.10.0", "minecraft:client_entity": {"description": desc}}


RENDER_CONTROLLERS = {"format_version": "1.10.0", "render_controllers": {
    "controller.render.studio_cyclops": {
        "arrays": {"textures": {"Array.skins": ["Texture.default", "Texture.blinded"]}},
        "geometry": "Geometry.default", "materials": [{"*": "Material.default"}],
        "textures": ["Array.skins[query.property('studio:blind')]"]},
    "controller.render.studio_siren": {
        "arrays": {"textures": {"Array.skins": ["Texture.dusk", "Texture.ash", "Texture.sea"]}},
        "geometry": "Geometry.default", "materials": [{"*": "Material.default"}],
        "textures": ["Array.skins[query.property('studio:plumage')]"]},
}}

SOUNDS = {"entity_sounds": {"entities": {
    "studio:cyclops": {"volume": 1.0, "pitch": [0.5, 0.65], "events": {
        "ambient": "mob.ravager.ambient", "hurt": "mob.ravager.hurt", "death": "mob.ravager.death", "step": "mob.ravager.step"}},
    "studio:siren": {"volume": 1.0, "pitch": [0.55, 0.75], "events": {
        "ambient": "mob.allay.idle", "hurt": "mob.phantom.hurt", "death": "mob.phantom.death"}},
    "studio:circe": {"volume": 1.0, "pitch": [0.8, 0.95], "events": {
        "ambient": "mob.witch.ambient", "hurt": "mob.witch.hurt", "death": "mob.witch.death"}},
    "studio:scylla": {"volume": 1.2, "pitch": [0.45, 0.6], "events": {
        "ambient": "mob.hoglin.ambient", "hurt": "mob.hoglin.hurt", "death": "mob.ravager.death"}},
    "studio:charybdis": {"volume": 0.8, "pitch": [0.5, 0.7], "events": {"ambient": "bubble.downinside"}},
    "studio:laestrygonian": {"volume": 1.0, "pitch": [0.5, 0.6], "events": {
        "ambient": "mob.vindicator.idle", "hurt": "mob.irongolem.hit", "death": "mob.irongolem.death",
        "step": "mob.irongolem.walk"}},
}}}


# =================================================================== items
ITEM_ART = {
    "moly": ({"w": (235, 235, 225), "W": (255, 255, 250), "y": (230, 200, 60), "g": (70, 120, 50),
              "l": (100, 150, 60), "k": (25, 22, 25), "K": (70, 64, 70)}, [
        "................", "......w.w.......", ".....wWyWw......", "......wWw.......", ".....w.g.w......",
        ".......g........", ".......g.l......", "......lg.ll.....", ".....ll.g.......", "........g.......",
        ".......gg.......", "......kkk.......", ".....kKkkk......", "......kKk.k.....", ".....k..k..k....",
        "................"]),
    "beeswax": ({"o": (120, 80, 20), "Y": (240, 190, 60), "y": (215, 160, 40), "H": (252, 222, 124)}, [
        "................", "................", "................", ".....oooooo.....", "....oYYYYYYo....",
        "...oYyHyYyHyo...", "...oyHyYyHyYo...", "..oYyYHyYHyYyo..", "..oyHyYyHyYyHo..", "..oYyHyYyHyYyo..",
        "...oyYyHyYyHo...", "...ooyYyYyYoo...", ".....oooooo.....", "................", "................",
        "................"]),
    "maronian_wine": ({"O": (200, 110, 50), "k": (30, 20, 15), "r": (110, 20, 40)}, [
        "................", ".......rr.......", "......kOOk......", ".......OO.......", ".....kOOOOk.....",
        "....kOOOOOOk....", "....OkkkkkkO....", "...kOkOOOOkOk...", "...kOkOkkOkOk...", "...kOkkkkkkOk...",
        "....kOOOOOOk....", "....kOOkkOOk....", ".....kOOOOk.....", "......kOOk......", ".......kk.......",
        "................"]),
    "olive_stake": ({"E": (255, 150, 40), "e": (255, 220, 120), "c": (40, 30, 25), "w": (130, 100, 60),
                     "W": (175, 140, 90)}, [
        "..............Ee", ".............EEe", "............cEE.", "...........ccc..", "..........wcc...",
        ".........wwc....", "........wWw.....", ".......wWw......", "......wWw.......", ".....wWw........",
        "....wWw.........", "...wWw..........", "..wWw...........", ".wWw............", ".ww.............",
        "................"]),
    "circe_feast": ({"b": (190, 140, 70), "B": (220, 175, 100), "g": (80, 40, 90), "P": (130, 70, 140),
                     "s": (120, 70, 40), "S": (160, 100, 55), "t": (120, 60, 30), "T": (180, 95, 45)}, [
        "................", "................", ".....b...gg.....", "....bbb.gPgg....", "...bBBbbgPPg....",
        "....sssssssss...", "...sSsSSsSssSs..", "..tsSSssSSsSSst.", "..tTTTTTTTTTTTt.", "..ttTtTTtTTtTt..",
        "...tTTTTTTTTTt..", "....tTTTTTTTt...", ".....ttttttt....", "................", "................",
        "................"]),
}

ITEMS = {
    "moly": dict(cat="nature", stack=16, food=(1, 0.3), anim="eat", dur=1.2),
    "beeswax": dict(cat="items", stack=16, food=(0, 0.0), anim="eat", dur=1.0),
    "maronian_wine": dict(cat="items", stack=8, food=(2, 0.4), anim="drink", dur=1.6),
    "olive_stake": dict(cat="equipment", stack=1, weapon=7),
    "circe_feast": dict(cat="items", stack=4, food=(10, 1.2), anim="eat", dur=2.0),
}


def item_json(name, spec):
    comps = {"minecraft:icon": {"textures": {"default": f"studio_{name}"}}, "minecraft:display_name": {"value": f"item.studio:{name}.name"},
             "minecraft:max_stack_size": spec["stack"]}
    if "food" in spec:
        comps["minecraft:food"] = {"nutrition": spec["food"][0], "saturation_modifier": spec["food"][1],
                                   "can_always_eat": True}
        comps["minecraft:use_animation"] = spec["anim"]
        comps["minecraft:use_modifiers"] = {"use_duration": spec["dur"], "movement_modifier": 0.35}
    if "weapon" in spec:
        comps["minecraft:hand_equipped"] = True
        comps["minecraft:damage"] = {"value": spec["weapon"]}
    return {"format_version": "1.21.0", "minecraft:item": {
        "description": {"identifier": f"studio:{name}", "menu_category": {"category": spec["cat"]}},
        "components": comps}}


RECIPES = {
    "beeswax": {"format_version": "1.20.10", "minecraft:recipe_shapeless": {
        "description": {"identifier": "studio:beeswax"}, "tags": ["crafting_table"],
        "ingredients": [{"item": "minecraft:honeycomb"}], "result": {"item": "studio:beeswax", "count": 2}}},
    "moly": {"format_version": "1.20.10", "minecraft:recipe_shapeless": {
        "description": {"identifier": "studio:moly"}, "tags": ["crafting_table"],
        "ingredients": [{"item": "minecraft:lily_of_the_valley"}, {"item": "minecraft:ink_sac"}],
        "result": {"item": "studio:moly"}}},
    "maronian_wine": {"format_version": "1.20.10", "minecraft:recipe_shapeless": {
        "description": {"identifier": "studio:maronian_wine"}, "tags": ["crafting_table"],
        "ingredients": [{"item": "minecraft:sweet_berries"}, {"item": "minecraft:sweet_berries"},
                        {"item": "minecraft:glass_bottle"}],
        "result": {"item": "studio:maronian_wine"}}},
    "olive_stake": {"format_version": "1.20.10", "minecraft:recipe_shaped": {
        "description": {"identifier": "studio:olive_stake"}, "tags": ["crafting_table"],
        "pattern": ["F", "S", "S"], "key": {"F": {"item": "minecraft:flint"}, "S": {"item": "minecraft:stick"}},
        "result": {"item": "studio:olive_stake"}}},
}


def loot(entries):
    pools = []
    for name, lo, hi, chance in entries:
        pool = {"rolls": 1, "entries": [{"type": "item", "name": name, "weight": 1,
                                         "functions": [{"function": "set_count", "count": {"min": lo, "max": hi}}]}]}
        if chance < 1:
            pool["conditions"] = [{"condition": "random_chance", "chance": chance}]
        pools.append(pool)
    return {"pools": pools}


LOOT = {
    "cyclops": loot([("minecraft:mutton", 3, 6, 1), ("minecraft:white_wool", 1, 3, 1), ("minecraft:bone", 2, 5, 1)]),
    "siren": loot([("minecraft:feather", 2, 5, 1), ("minecraft:bone", 0, 2, 1), ("minecraft:amethyst_shard", 1, 1, 0.25)]),
    "circe": loot([("studio:moly", 1, 2, 1), ("minecraft:glass_bottle", 1, 2, 1)]),
    "scylla": loot([("minecraft:prismarine_shard", 3, 7, 1), ("minecraft:bone", 3, 6, 1),
                    ("minecraft:heart_of_the_sea", 1, 1, 0.1)]),
    "laestrygonian": loot([("minecraft:iron_ingot", 2, 5, 1), ("minecraft:copper_ingot", 1, 4, 1),
                           ("minecraft:shield", 1, 1, 0.15)]),
}


def spawn_rule(identifier, tag_filter, weight, herd, underwater=False):
    cond = {"minecraft:weight": {"default": weight}, "minecraft:herd": {"min_size": herd[0], "max_size": herd[1]},
            "minecraft:density_limit": {"surface": 2}, "minecraft:difficulty_filter": {"min": "easy", "max": "hard"},
            "minecraft:biome_filter": tag_filter}
    cond["minecraft:spawns_underwater" if underwater else "minecraft:spawns_on_surface"] = {}
    return {"format_version": "1.8.0", "minecraft:spawn_rules": {
        "description": {"identifier": identifier, "population_control": "monster"}, "conditions": [cond]}}


SPAWN_RULES = {
    "siren": spawn_rule("studio:siren", {"test": "has_biome_tag", "value": "beach"}, 6, (2, 3)),
    "cyclops": spawn_rule("studio:cyclops", {"test": "has_biome_tag", "value": "extreme_hills"}, 2, (1, 1)),
    "laestrygonian": spawn_rule("studio:laestrygonian", {"all_of": [
        {"test": "has_biome_tag", "value": "beach"}, {"test": "has_biome_tag", "value": "cold"}]}, 3, (2, 3)),
    "scylla": spawn_rule("studio:scylla", {"all_of": [
        {"test": "has_biome_tag", "value": "ocean"}, {"test": "has_biome_tag", "value": "deep"}]}, 1, (1, 1), underwater=True),
}

LANG = [
    ("entity.studio:cyclops.name", "Polyphemus the Cyclops"), ("entity.studio:siren.name", "Siren"),
    ("entity.studio:circe.name", "Circe"), ("entity.studio:scylla.name", "Scylla"),
    ("entity.studio:charybdis.name", "Charybdis"), ("entity.studio:laestrygonian.name", "Laestrygonian Giant"),
    ("entity.studio:boulder.name", "Hurled Boulder"),
    ("item.spawn_egg.entity.studio:cyclops.name", "Spawn Polyphemus"),
    ("item.spawn_egg.entity.studio:siren.name", "Spawn Siren"),
    ("item.spawn_egg.entity.studio:circe.name", "Spawn Circe"),
    ("item.spawn_egg.entity.studio:scylla.name", "Spawn Scylla"),
    ("item.spawn_egg.entity.studio:charybdis.name", "Spawn Charybdis"),
    ("item.spawn_egg.entity.studio:laestrygonian.name", "Spawn Laestrygonian Giant"),
    ("item.studio:moly.name", "Moly"), ("item.studio:beeswax.name", "Beeswax"),
    ("item.studio:maronian_wine.name", "Maronian Wine"), ("item.studio:olive_stake.name", "Olive-Wood Stake"),
    ("item.studio:circe_feast.name", "Circe's Feast"),
    ("action.interact.studio.wine", "Offer Wine"), ("action.interact.studio.feast", "Ask for Food"),
    ("action.interact.studio.counsel", "Ask for Counsel"),
]


# =================================================================== output
def png_bytes(rows):
    h, w = len(rows), len(rows[0])
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for px in row:
            raw += bytes(px)

    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def write_png(rel, rows):
    path = f"{ROOT}/{rel}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png_bytes(rows))


def write_json(rel, data):
    path = f"{ROOT}/{rel}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


CREATURES = {
    # name: (builder, bounds (w, h, offset_y), textures {key: variant}, render controller, anims, animate, egg, material)
    "cyclops": (build_cyclops, (4, 4.5, 2), {"default": {}, "blinded": {"blind": True}},
                "controller.render.studio_cyclops", anims_cyclops, ANIMATE_CYCLOPS, ("#8C7A5E", "#3B2A22"), "entity_alphatest"),
    "siren": (build_siren, (3, 2.5, 1.2), {"dusk": {"plumage": 0}, "ash": {"plumage": 1}, "sea": {"plumage": 2}},
              "controller.render.studio_siren", anims_siren, ANIMATE_SIREN, ("#5C4636", "#C4B296"), "entity_alphatest"),
    "circe": (build_circe, (2, 2.6, 1.3), {"default": {}}, "controller.render.default", anims_circe, ANIMATE_CIRCE,
              ("#743C28", "#3A4630"), "entity_alphatest"),
    "scylla": (build_scylla, (5, 4.5, 2), {"default": {}}, "controller.render.default", anims_scylla, ANIMATE_SCYLLA,
               ("#686860", "#962F3A"), "entity_alphatest"),
    "charybdis": (build_charybdis, (6, 3.5, -1), {"default": {}}, "controller.render.default", anims_charybdis, ["swirl"],
                  ("#1E4A5C", "#E1EEEE"), "entity_alphablend"),
    "laestrygonian": (build_laestrygonian, (3, 4.8, 2.2), {"default": {}}, "controller.render.default",
                      anims_laestrygonian, ANIMATE_LAESTRYGONIAN, ("#36383E", "#966834"), "entity_alphatest"),
    "boulder": (build_boulder, (1.5, 1.5, 0.5), {"default": {}}, "controller.render.default", anims_boulder, ["spin"],
                None, "entity_alphatest"),
}

BEHAVIORS = {"cyclops": bp_cyclops, "siren": bp_siren, "circe": bp_circe, "scylla": bp_scylla,
             "charybdis": bp_charybdis, "laestrygonian": bp_laestrygonian, "boulder": bp_boulder}


def main():
    for name, (build, bounds, textures, rc, anims, animate, egg, material) in CREATURES.items():
        m = build()
        m.pack()
        tex_paths = {}
        for key, variant in textures.items():
            fname = name if key == "default" else f"{name}_{key}" if key != "blinded" else f"{name}_blind"
            write_png(f"RP/textures/entity/{fname}.png", m.paint(variant))
            tex_paths[key] = f"textures/entity/{fname}"
        write_json(f"RP/models/entity/{name}.geo.json", m.geometry(*bounds))
        anim_defs = anims()
        write_json(f"RP/animations/{name}.animation.json", {
            "format_version": "1.10.0",
            "animations": {f"animation.{name}.{k}": v for k, v in anim_defs.items()}})
        write_json(f"RP/entity/{name}.entity.json", client_entity(name, tex_paths, rc, anim_defs, animate, egg, material))
        write_json(f"BP/entities/{name}.json", BEHAVIORS[name]())
        print(f"{name:14s} bones={len(m.bones):3d} cubes={len(m.cubes):3d} atlas={m.tw * D}x{m.th * D}px")

    write_json("RP/render_controllers/odyssey.render_controllers.json", RENDER_CONTROLLERS)
    write_json("RP/sounds.json", SOUNDS)
    tex_data = {}
    for name, (palette, rows) in ITEM_ART.items():
        img = [[(palette[ch] + (255,)) if ch != "." else (0, 0, 0, 0) for ch in row] for row in rows]
        write_png(f"RP/textures/items/{name}.png", img)
        tex_data[f"studio_{name}"] = {"textures": f"textures/items/{name}"}
    write_json("RP/textures/item_texture.json", {"resource_pack_name": "odyssey", "texture_name": "atlas.items",
                                                 "texture_data": tex_data})
    for name, spec in ITEMS.items():
        write_json(f"BP/items/{name}.json", item_json(name, spec))
    for name, data in RECIPES.items():
        write_json(f"BP/recipes/{name}.json", data)
    for name, data in LOOT.items():
        write_json(f"BP/loot_tables/entities/{name}.json", data)
    for name, data in SPAWN_RULES.items():
        write_json(f"BP/spawn_rules/{name}.json", data)
    for pack in ("BP", "RP"):
        path = f"{ROOT}/{pack}/texts/en_US.lang"
        keep = [l for l in open(path).read().splitlines() if "pixel_slime" in l]
        with open(path, "w") as f:
            f.write("\n".join(keep + [f"{k}={v}" for k, v in LANG]) + "\n")


if __name__ == "__main__":
    main()
