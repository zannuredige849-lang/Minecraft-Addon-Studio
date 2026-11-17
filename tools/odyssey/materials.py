"""Procedural materials and decals. A material maps a paint context to (r, g, b, a) or (r, g, b, a, 'E')
for pre-lit texels. Patterns use model units (c.u, c.v) so their density does not depend on texel density."""
import math

from .core import SIDES, fbm, hash2, mix, mul


def _n(c, sx, sy, s=0, o=3):
    return fbm(c.u * sx + c.fo, c.v * sy + c.fo * 0.37, c.seed + s, o)


def _vert(c):
    """0 at the top of a side face, 1 at the bottom (up=0, down=1)."""
    if c.face == "up":
        return 0.0
    if c.face == "down":
        return 1.0
    return c.y / max(1, c.h - 1)


# ================================================================== organic
def skin(base, dark=None, mottle=1.0, veins=None, pores=0.03, wrinkle=0.0, stain=None, freckles=0.0,
         nail=None, nail_len=0.0, spots=0.0):
    dk = dark or mul(base, 0.74)
    hi = mul(base, 1.08)

    def f(c):
        n = _n(c, 0.9, 0.9)
        col = mix(dk, hi, 0.5 + (n - 0.5) * 1.5 * mottle)
        b2 = _n(c, 0.35, 0.35, 7, 2)
        if b2 > 0.62:
            col = mix(col, mul(col, (0.92, 0.84, 0.82)), (b2 - 0.62) * 2.0)
        if veins is not None:
            vn = abs(_n(c, 0.6, 0.6, 3) - 0.5)
            if vn < 0.028:
                col = mix(col, veins, 0.45 * (1 - vn / 0.028))
        if pores and hash2(c.x, c.y, c.seed + 11) < pores:
            col = mul(col, 0.88)
        if freckles and hash2(c.x, c.y, c.seed + 13) < freckles:
            col = mix(col, (150, 96, 70), 0.4)
        if spots and _n(c, 1.6, 1.6, 17, 2) > 1 - spots:
            col = mix(col, mul(col, 0.8), 0.6)
        if wrinkle and c.face in SIDES and math.sin(c.v * 9 + _n(c, 1.2, 1.2, 5) * 5) > 0.9:
            col = mul(col, 1 - wrinkle)
        if stain is not None:
            amt = max(0.0, (_vert(c) - 0.25) / 0.75) * (0.75 + 0.25 * _n(c, 1.5, 1.5, 9))
            col = mix(col, stain, amt)
        if nail is not None and nail_len and (c.face == "down" or (c.face in SIDES and c.v >= c.size[1] - nail_len)):
            col = nail
        return col + (255,)
    return f


def elephant(base, crease=None, mottle=1.0, spots=0.0):
    """Thick, deeply creased grey skin (Polyphemus)."""
    cr = crease or mul(base, 0.52)

    def f(c):
        n = _n(c, 0.45, 0.45)
        col = mix(mul(base, 0.86), mul(base, 1.07), 0.5 + (n - 0.5) * 1.3 * mottle)
        # irregular crease network: warped, broken lines whose strength varies across the hide
        warp = _n(c, 0.5, 0.5, 21, 3) * 9
        strength = 0.35 + 0.65 * _n(c, 0.3, 0.3, 24, 2)
        w1 = math.sin(c.v * 1.7 + warp + c.u * 0.45)
        if w1 > 0.955:
            col = mix(col, cr, 0.55 * strength)
        elif w1 > 0.86:
            col = mix(col, cr, 0.18 * strength)
        elif 0.55 < w1 < 0.7:
            col = mul(col, 1.0 + 0.05 * strength)
        w2 = math.sin((c.u * 1.3 - c.v * 0.9) * 1.6 + _n(c, 0.7, 0.7, 23, 2) * 8)
        if w2 > 0.975:
            col = mix(col, cr, 0.3 * strength)
        if hash2(c.x, c.y, c.seed + 29) < 0.03:
            col = mul(col, 0.9)
        if spots and _n(c, 0.5, 0.5, 31, 2) > 1 - spots:
            col = mix(col, (120, 108, 100), 0.35)
        return col + (255,)
    return f


def nails(base=(158, 148, 118), crack=(66, 56, 46), broken=True):
    def f(c):
        col = mul(base, 0.85 + 0.25 * _n(c, 3, 3, 40, 2))
        if hash2(c.x // 2, c.y, c.seed + 41) < 0.1:
            col = mix(col, crack, 0.6)
        if broken and c.face in SIDES and c.h >= 3:
            cut = int(hash2(c.x, 7, c.seed) * (c.h // 3 + 1))
            if c.y >= c.h - cut:
                return (0, 0, 0, 0)
        return col + (255,)
    return f


def hair(base, tips=0.0, streak=None, curly=False):
    def f(c):
        if curly:
            cell = 0.75
            cu, cv = (c.u % cell) / cell - 0.5, (c.v % cell) / cell - 0.5
            r = math.hypot(cu, cv)
            col = mul(base, 0.75 + 0.5 * (0.5 - abs(r - 0.32)) * 1.6)
            if hash2(int(c.u / cell), int(c.v / cell), c.seed) > 0.7:
                col = mul(col, 0.85)
            return col + (255,)
        if c.face in SIDES:
            k = 0.72 + 0.5 * hash2(c.x, 1, c.seed)
            col = mul(base, k * (0.85 + 0.3 * _n(c, 0.4, 1.6, 4, 2)))
            if streak is not None and hash2(c.x, 5, c.seed) > 0.78:
                col = mix(col, streak, 0.55)
            t = min(tips, c.size[1] * 0.4)
            if t and c.v >= c.size[1] - t:
                depth = (c.v - (c.size[1] - t)) / t
                if hash2(c.x, 9, c.seed) < depth * 0.9:
                    return (0, 0, 0, 0)
        else:
            n = _n(c, 1.5, 1.5, 4, 2)
            col = mul(base, 0.8 + 0.35 * n)
            if (c.x + int(n * 4)) % 3 == 0:
                col = mul(col, 0.82)
            if streak is not None and hash2(c.x, c.y // 3, c.seed + 6) > 0.85:
                col = mix(col, streak, 0.5)
        return col + (255,)
    return f


def feather(base, tip, shaft=None):
    def f(c):
        sh = shaft or mix(base, (235, 225, 205), 0.4)
        if c.face not in SIDES:
            col = mul(base, 0.8 + 0.3 * _n(c, 1.2, 1.2, 2, 2))
            return col + (255,)
        rh = max(2, int(0.75 * c.D))
        r, ly = c.y // rh, c.y % rh
        off = (r % 2) * rh // 2
        fw = max(2, rh)
        lx = (c.x + off) % fw
        col = mul(base, 0.88 + 0.22 * hash2((c.x + off) // fw, r, c.seed))
        if lx == fw // 2:
            col = mix(col, sh, 0.35)
        elif lx == 0:
            col = mul(col, 0.72)
        if ly >= rh - 1:
            col = mix(col, tip, 0.65)
        return col + (255,)
    return f


def hide(base, belly=None, streak=0.12):
    """Short-haired animal coat."""
    bl = belly or mix(base, (245, 240, 228), 0.5)

    def f(c):
        col = mul(base, 0.88 + 0.22 * _n(c, 0.6, 0.6, 50, 2))
        col = mul(col, 1 - streak + 2 * streak * hash2(c.x, c.y // 3, c.seed + 51))
        if c.face == "down":
            col = mix(col, bl, 0.7)
        elif c.face in SIDES and _vert(c) > 0.72:
            col = mix(col, bl, (_vert(c) - 0.72) * 2.2)
        return col + (255,)
    return f


def horn(base=(222, 212, 182), tip=(58, 50, 44)):
    def f(c):
        t = c.v / max(c.size[1], 1e-6) if c.face in SIDES else (1.0 if c.face == "down" else 0.0)
        col = mix(base, tip, max(0.0, t - 0.55) * 2.2)
        if int(c.v * 2.0) % 2 == 0:
            col = mul(col, 0.94)
        return mul(col, 0.92 + 0.12 * _n(c, 2, 2, 52, 2)) + (255,)
    return f


# ================================================================== cloth
def cloth(base, folds=0.1, weave=True, tatter=0.0, grime=0.2, hem=None, patch=None):
    def f(c):
        col = mul(base, 0.9 + 0.2 * _n(c, 1.0, 1.0, 8, 2))
        if c.face in SIDES:
            if folds:
                col = mul(col, 1 - folds + folds * 2 * (0.5 + 0.5 * math.sin((c.u + _n(c, 0.3, 0.3, 2, 2) * 5) * 2.2)))
            col = mul(col, 1 - grime * _vert(c))
            if hem is not None and c.v >= c.size[1] - 0.5:
                col = hem
            if tatter:
                cut = hash2(int(c.u * 2), 21, c.seed) * tatter
                if c.v >= c.size[1] - cut:
                    return (0, 0, 0, 0)
        if patch is not None and _n(c, 0.45, 0.45, 19, 2) > 0.7:
            col = mix(col, patch, 0.6)
        if weave and (c.x + c.y) % 2 == 0:
            col = mul(col, 1.04)
        return col + (255,)
    return f


def linen(base, bleach=0.12, tatter=0.0):
    """Sun-bleached linen: fine weave, uneven fading."""
    def f(c):
        col = mul(base, 0.92 + 0.12 * _n(c, 0.8, 0.8, 60, 2))
        col = mix(col, (250, 248, 240), bleach * _n(c, 0.3, 0.3, 61, 2))
        if (c.x % 2) ^ (c.y % 2):
            col = mul(col, 0.97)
        if c.face in SIDES:
            col = mul(col, 0.94 + 0.08 * math.sin(c.u * 3.0 + _n(c, 0.5, 0.5, 62, 2) * 4))
            if tatter:
                cut = hash2(int(c.u * 2), 23, c.seed) * tatter
                if c.v >= c.size[1] - cut:
                    return (0, 0, 0, 0)
        return col + (255,)
    return f


def fishnet(base, cell=0.75, thick=0.12):
    """Open net: transparent except the knotted cords."""
    def f(c):
        a = (c.u + c.v) % cell
        b = (c.u - c.v) % cell
        on = a < thick or b < thick
        if not on:
            return (0, 0, 0, 0)
        col = mul(base, 0.85 + 0.25 * hash2(c.x, c.y, c.seed))
        if a < thick and b < thick:
            col = mul(col, 0.7)
        return col + (255,)
    return f


def quilted(base, stitch=None, channel=0.75):
    """Padded, quilted garment (Laestrygonian child)."""
    st = stitch or mul(base, 0.55)

    def f(c):
        ph = (c.v % channel) / channel
        col = mul(base, 0.8 + 0.32 * math.sin(math.pi * ph))
        if ph < 0.08:
            col = mix(col, st, 0.8)
        if (int(c.u * 2) % 2 == 0) and ph < 0.15:
            col = mul(col, 0.9)
        col = mul(col, 0.92 + 0.12 * _n(c, 1, 1, 70, 2))
        return col + (255,)
    return f


def leather(base):
    def f(c):
        col = mul(base, 0.85 + 0.25 * _n(c, 1.5, 1.5, 80, 3))
        if hash2(c.x, c.y, c.seed + 81) < 0.04:
            col = mul(col, 0.8)
        return col + (255,)
    return f


# ================================================================== metal and stone
def metal(base, edge=None, rivets=True, bands=0, patina=None, scratches=True, polish=0.0, engrave=False):
    eg = edge or mix(base, (255, 255, 255), 0.5)

    def f(c):
        col = mul(base, 0.86 + 0.28 * _n(c, 0.2, 4.0, 12, 2))
        if c.face in SIDES:
            t = _vert(c)
            col = mul(col, 1.12 - 0.3 * t)
            if polish:
                band = math.exp(-((t - 0.22) ** 2) / 0.012)
                col = mix(col, eg, polish * band)
            if bands:
                bh = max(4, c.h // bands)
                m = c.y % bh
                if m == bh - 1:
                    col = mul(col, 0.52)
                elif m == 0:
                    col = mix(col, eg, 0.45)
                if rivets and m == bh // 2 and c.x % max(4, int(1.5 * c.D)) == 2:
                    col = mix(col, eg, 0.85)
            elif rivets and (c.y == 1 or c.y == c.h - 2) and c.x % max(4, int(1.5 * c.D)) == 2 and c.w > 6:
                col = mix(col, eg, 0.85)
            if engrave and (c.y == 2 or c.y == c.h - 3 or c.x == 2 or c.x == c.w - 3) and c.w > 8 and c.h > 8:
                col = mul(col, 0.7)
        if c.x == 0 or c.y == 0:
            col = mix(col, eg, 0.35)
        if c.x == c.w - 1 or c.y == c.h - 1:
            col = mul(col, 0.66)
        if patina is not None:
            p = _n(c, 0.6, 0.6, 14, 3)
            if p > 0.62:
                col = mix(col, patina, min(1.0, (p - 0.62) * 3.5))
        if scratches and hash2(c.x - c.y, c.x // 4, c.seed + 15) < 0.015:
            col = mix(col, eg, 0.5)
        return col + (255,)
    return f


def blade(base, edge=(236, 238, 242), fuller=True):
    """Forged blade metal with no per-cube bevel or gradient, so chained segments read as one blade: a lengthwise
    sheen on the flats, a bright honed bevel along both long edges and a dark fuller down the middle."""
    def f(c):
        along = c.v if c.face in ("east", "west") else c.u
        col = mul(base, 0.9 + 0.16 * fbm(along * 0.08 + c.fo, c.u * 0.6, c.seed + 70, 2))
        if c.face in ("east", "west") and c.w > 2:
            t = (c.x + 0.5) / c.w
            if t < 0.16 or t > 0.84:
                col = mix(col, edge, 0.55)
            elif fuller and 0.42 < t < 0.58 and c.w > 6:
                col = mul(col, 0.72)
        if hash2(c.x * 3 + c.y, c.y // 3, c.seed + 71) < 0.01:
            col = mix(col, edge, 0.4)
        return col + (255,)
    return f


def mail(base):
    def f(c):
        ring = ((c.x % 3 == 1) and (c.y % 2 == 0)) or ((c.x % 3 == 0) and (c.y % 2 == 1))
        col = mul(base, 1.25 if ring else 0.6)
        if c.face in SIDES:
            col = mul(col, 1.08 - 0.25 * _vert(c))
        return col + (255,)
    return f


def stone(base):
    def f(c):
        col = mul(base, 0.75 + 0.45 * _n(c, 0.6, 0.6, 20, 3))
        if abs(_n(c, 0.45, 0.45, 23, 2) - 0.5) < 0.02:
            col = mul(col, 0.5)
        if _n(c, 1.0, 1.0, 27, 2) > 0.74:
            col = mix(col, (96, 110, 70), 0.35)
        return col + (255,)
    return f


def rock_flesh(rock=(112, 100, 84), scale=(96, 74, 56), flesh=(132, 84, 70)):
    """Scylla: rock, scales and wet marine flesh blended so she melts into the cliff."""
    def f(c):
        n = _n(c, 0.25, 0.25, 90, 3)
        if n < 0.42:
            col = mul(rock, 0.75 + 0.45 * _n(c, 0.8, 0.8, 91, 3))
            if abs(_n(c, 0.5, 0.5, 92, 2) - 0.5) < 0.025:
                col = mul(col, 0.55)
        elif n < 0.62:
            rr = int(c.v * 1.6)
            lx, ly = (c.u * 1.6 + (rr % 2) * 0.5) % 1.0, (c.v * 1.6) % 1.0
            col = mul(scale, 0.85 + 0.3 * _n(c, 1, 1, 93, 2))
            if ly > 0.78 or lx < 0.12:
                col = mul(col, 0.62)
            elif ly < 0.25:
                col = mul(col, 1.15)
        else:
            col = mul(flesh, 0.85 + 0.3 * _n(c, 1.2, 1.2, 94, 2))
            if hash2(c.x, c.y, c.seed + 95) < 0.05:          # wet glints
                return mix(col, (225, 205, 195), 0.55) + (255,)
        return col + (255,)
    return f


def wood(base, grain=0.14, char=0.0):
    def f(c):
        g = math.sin(c.u * 6.5 + _n(c, 0.7, 0.2, 30, 2) * 9)
        col = mul(base, 1 - grain + grain * g)
        if hash2(c.x, c.y // 3, c.seed + 31) < 0.02:
            col = mul(col, 0.7)
        if char and c.face in SIDES:
            t = 1 - _vert(c)
            if t > 1 - char:
                k = (t - (1 - char)) / char
                col = mix(col, (30, 22, 18), min(1.0, k * 1.4))
                if k > 0.65 and hash2(c.x, c.y, c.seed + 33) < 0.3:
                    return (255, 140, 40, 255, "E")
        return col + (255,)
    return f


def planks(base, seam=None, plank=1.5, bolts=True):
    """Hewn planks with dark seams and iron bolts (Trojan Horse)."""
    sm = seam or mul(base, 0.45)

    def f(c):
        row = int(c.v / plank)
        col = mul(base, 0.86 + 0.24 * hash2(row, 3, c.seed))
        col = mul(col, 0.9 + 0.12 * math.sin(c.u * 4 + row * 1.7 + _n(c, 0.6, 0.15, 34, 2) * 6))
        if (c.v % plank) < 1.0 / c.D:
            col = mix(col, sm, 0.85)
        joint = (c.u + row * 2.7) % 6.0
        if joint < 1.0 / c.D:
            col = mix(col, sm, 0.7)
        if bolts and abs((c.u + row * 2.7) % 3.0 - 1.5) < 0.2 and abs((c.v % plank) - plank / 2) < 0.2:
            col = (70, 70, 76)
        return col + (255,)
    return f


def water(base, foam=(226, 238, 238), alpha=150, foam_amt=0.25):
    def f(c):
        n = _n(c, 0.4, 0.4, 40, 3)
        s = math.sin(c.u * 1.6 + c.v * 0.6 + n * 6)
        a = alpha + int(40 * n)
        if s > 1 - foam_amt * 2 and n > 0.45:
            return foam + (min(255, a + 70),)
        return mix(mul(base, 0.75), mul(base, 1.3), (s + 1) / 2) + (min(255, a),)
    return f


def bone_mat(base):
    def f(c):
        col = mul(base, 0.85 + 0.25 * _n(c, 1, 1, 50, 2))
        if c.face in SIDES and hash2(c.x // 2, c.y, c.seed + 51) < 0.06:
            col = mul(col, 0.85)
        return col + (255,)
    return f


def cavity(base=(44, 14, 16)):
    def f(c):
        col = mul(base, 0.6 + 0.6 * _n(c, 1.5, 1.5, 60, 2))
        if hash2(c.x, c.y, c.seed + 61) < 0.03:
            col = mix(col, (150, 70, 70), 0.5)
        return col + (255,)
    return f


def teeth(base=(220, 206, 168), point="down", gap=0.75, rot=(150, 120, 80)):
    def f(c):
        g = max(2, int(gap * c.D))
        lx, t = c.x % g, c.x // g
        col = mul(base, 0.82 + 0.28 * hash2(t, 2, c.seed))
        if hash2(t, 9, c.seed) < 0.2:
            col = mix(col, rot, 0.6)
        if c.face in ("north", "south"):
            if lx == g - 1:
                return (0, 0, 0, 0)
            tip = c.y >= c.h // 2 if point == "down" else c.y < c.h - c.h // 2
            if tip and lx not in ((g - 1) // 2, (g - 2) // 2):
                return (0, 0, 0, 0)
        return col + (255,)
    return f


def flat(color, alpha=255):
    def f(c):
        return mul(color, 0.92 + 0.12 * _n(c, 1, 1, 99, 2)) + (alpha,)
    return f


def crust(inner, sand=(36, 34, 33), amount=0.55, grains=(72, 68, 64)):
    """Black-sand and mud crust over any material (the risen dead of Hades)."""
    def f(c):
        px = inner(c)
        if px[3] == 0:
            return px
        n = _n(c, 0.55, 0.55, 110, 3)
        k = max(0.0, min(1.0, (n - (1 - amount)) * 2.5 + 0.25 * _vert(c)))
        col = mix(px[:3], sand, k)
        if hash2(c.x, c.y, c.seed + 111) < 0.05 * (0.3 + k):
            col = mix(col, grains, 0.55)
        return col + px[3:]
    return f


def translucent(inner, alpha=190):
    def f(c):
        px = inner(c)
        if px[3] == 0:
            return px
        return px[:3] + (min(px[3], alpha),) + px[4:]
    return f


# ================================================================== decals
def human_face(iris=(92, 74, 56), brow=(60, 48, 40), lips=(150, 84, 80), kohl=None, eye_y=0.5, eye_sep=0.21,
               mouth_y=0.8, mouth_open=0.0, blind=False, dead=False, age=0.0, beard=None, beard_from=0.62,
               lashes=None, cheek=None, sand=None):
    """Painted face for the north face of a head cube (the sculpted cubes add the relief)."""
    def d(c, col):
        if c.face != "north":
            return col
        tx, ty = (c.x + 0.5) / c.w, (c.y + 0.5) / c.h
        out = col[:3]
        if cheek is not None and 0.55 < ty < 0.75 and (abs(tx - 0.27) < 0.1 or abs(tx - 0.73) < 0.1):
            out = mix(out, cheek, 0.25)
        if tx < 0.12 or tx > 0.88:
            out = mul(out, 0.88)
        for ex in (0.5 - eye_sep, 0.5 + eye_sep):
            dx, dy = (tx - ex) / 0.13, (ty - eye_y) / 0.07
            r = math.hypot(dx, dy)
            if r < 1.0:
                if blind:
                    return mix((214, 212, 204), (170, 168, 160), r) + (255,)
                if dead:
                    return mix((178, 176, 166), (120, 118, 110), r * 0.8) + (255,)
                ir = math.hypot((tx - ex) / 0.06, (ty - eye_y) / 0.07)
                if ir < 1.0:
                    return (iris if ir > 0.48 else (14, 10, 10)) + (255,)
                return (224, 218, 204, 255)
            if kohl is not None and 1.0 <= r < 1.45 and dy < 0.2:
                return mix(out, kohl, 0.6) + (255,)
            if lashes is not None and 1.0 <= r < 1.25 and dy < -0.3:
                return lashes + (255,)
            if abs(ty - (eye_y - 0.13)) < 0.035 and abs(tx - ex) < 0.15:
                return brow + (255,)
            if age and abs(ty - (eye_y + 0.1)) < 0.02 and abs(tx - ex) < 0.11:
                out = mul(out, 1 - age)
            if age and abs(ty - (eye_y + 0.02)) < 0.02 and 0.13 < abs(tx - ex) < 0.2:
                out = mul(out, 1 - age * 0.8)
        if abs(tx - 0.5) < 0.04 and eye_y < ty < mouth_y - 0.14:
            out = mul(out, 0.92)
        if age and 0.28 < abs(tx - 0.5) < 0.32 and mouth_y - 0.14 < ty < mouth_y + 0.05:
            out = mul(out, 1 - age)
        if beard is not None and ty > beard_from:
            m = hash2(c.x, c.y, c.seed + 7)
            if not (abs(ty - mouth_y) < 0.04 and abs(tx - 0.5) < 0.12):
                out = mix(out, beard, 0.85 if m > 0.25 else 0.5)
        if mouth_open:
            r = math.hypot((tx - 0.5) / 0.12, (ty - mouth_y) / mouth_open)
            if r < 1.0:
                return ((34, 10, 12) if r < 0.72 else lips) + (255,)
        elif abs(ty - mouth_y) < 0.035 and abs(tx - 0.5) < 0.13:
            return lips + (255,)
        if sand is not None and fbm(c.x * 0.5, c.y * 0.5, c.seed + 9, 2) > 0.62:
            out = mix(out, sand, 0.7)
        return out + (255,)
    return d


def slit_eye(iris=(122, 96, 58), sclera=(206, 196, 160), blind_key="blind"):
    """One eye seen through a tall, narrow slit of lids: a pointed almond of bloodshot white around a round dark
    iris. Charred and bloody once blinded."""
    def d(c, col):
        if c.face != "north":
            return col
        cx, cy = (c.w - 1) / 2, (c.h - 1) / 2
        nx, ny = (c.x - cx) / (c.w / 2), (c.y - cy) / (c.h / 2)
        if abs(nx) > (1 - min(1.0, abs(ny)) ** 2) ** 0.6 or abs(ny) > 0.96:
            return mul(col[:3], 0.42) + (255,)                                  # the slit's shadowed rim
        if c.variant.get(blind_key):
            n = fbm(c.x * 0.4, c.y * 0.4, c.seed + 90, 2)
            out = mix((22, 6, 6), (104, 16, 12), n) if abs(ny) < 0.6 else mix((84, 30, 24), (140, 54, 38), n)
            return out + (255,)
        ux, uy = (c.x - cx) / c.D, (c.y - cy) / c.D                           # model units from the centre
        rr = math.hypot(ux, uy * 1.05)
        out = mul(sclera, 1 - 0.3 * min(1.0, abs(ny)) ** 2)
        if abs(fbm(c.x * 0.6, c.y * 0.6, c.seed + 92, 2) - 0.5) < 0.045:
            out = mix(out, (160, 44, 38), 0.7)                                  # veins
        if rr < 0.6:
            out = mul(iris, 0.75 + 0.35 * hash2(c.x, c.y, c.seed + 93))
            if rr > 0.47:
                out = mul(out, 0.62)
            if rr < 0.27:
                out = (12, 9, 9)
        if -0.36 < ny < -0.18 and -0.45 < nx < -0.05:
            out = mix(out, (250, 246, 236), 0.8)                                # wet highlight
        return out + (255,)
    return d


def edge_shade(edge, amount=0.4, reach=0.6):
    """Darken one edge of a north face (a lid's inner rim, a recess). edge: top/bottom/left/right; reach is the
    fraction of the face that fades."""
    def d(c, col):
        if c.face != "north":
            return col
        t = {"top": (c.y + 0.5) / c.h, "bottom": 1 - (c.y + 0.5) / c.h,
             "left": (c.x + 0.5) / c.w, "right": 1 - (c.x + 0.5) / c.w}[edge]
        if t >= reach:
            return col
        k = 1 - amount * (1 - t / reach) ** 1.5
        return mul(col[:3], k) + tuple(col[3:])
    return d


def nostrils(color=(34, 26, 24), y=0.45, sep=0.26, r=(0.11, 0.16)):
    """Two dark nostrils on a muzzle's front face, with a moist dark line between them."""
    def d(c, col):
        if c.face != "north":
            return col
        tx, ty = (c.x + 0.5) / c.w, (c.y + 0.5) / c.h
        for cx in (0.5 - sep, 0.5 + sep):
            if ((tx - cx) / r[0]) ** 2 + ((ty - y) / r[1]) ** 2 < 1:
                return color + tuple(col[3:])
        if abs(tx - 0.5) < 0.04 and ty > y + 0.15:
            return mix(col[:3], color, 0.5) + tuple(col[3:])
        return col
    return d


def tint(k):
    """Uniformly darken (k<1) or lighten (k>1) a face's paint: recesses and hollows."""
    def d(c, col):
        return mul(col[:3], k) + tuple(col[3:])
    return d


def socket_shade(eye, face_center, face_size, tilt, inner=None, radii=(1.2, 2.0), depth=0.3):
    """Darken a north face around a sunken eye socket. eye/face_center are model coordinates; tilt is the eye's
    z rotation in degrees. `inner` is another decal applied after the shading."""
    s, k = math.sin(math.radians(tilt)), math.cos(math.radians(tilt))

    def d(c, col):
        if c.face == "north":
            x = face_center[0] - face_size[0] / 2 + (c.x + 0.5) / c.D
            y = face_center[1] + face_size[1] / 2 - (c.y + 0.5) / c.D
            dx, dy = x - eye[0], y - eye[1]
            a, b = dx * s + dy * k, dx * k - dy * s
            r = math.hypot(b / radii[0], a / radii[1])
            if r < 1.6:
                t = max(0.0, (r - 0.55) / 1.05)
                col = mul(col[:3], 1 - depth * (1 - t * t * (3 - 2 * t))) + tuple(col[3:])
        return inner(c, col) if inner else col
    return d


def blood_below(blind_key="blind", x0=0.35, x1=0.65, top=0.15):
    """Blood running down a face plane once Polyphemus is blinded."""
    def d(c, col):
        if c.face != "north" or not c.variant.get(blind_key):
            return col
        tx, ty = (c.x + 0.5) / c.w, (c.y + 0.5) / c.h
        if x0 < tx < x1 and ty > top and hash2(c.x, 3, c.seed + 5) < 0.45 - (ty - top) * 0.3:
            return mix(col[:3], (110, 8, 8), 0.8) + (255,)
        return col
    return d


def slits(color=(10, 10, 12), rows=((0.38, 0.46),), x0=0.12, x1=0.88, vent=True):
    """Dark sight slits and breathing holes on a visor plate."""
    def d(c, col):
        if c.face != "north":
            return col
        tx, ty = (c.x + 0.5) / c.w, (c.y + 0.5) / c.h
        for a, b in rows:
            if a < ty < b and x0 < tx < x1:
                return color + (255,)
        if vent and 0.6 < ty < 0.88 and (0.2 < tx < 0.4 or 0.6 < tx < 0.8) and c.x % 3 == 1 and c.y % 3 == 1:
            return color + (255,)
        return col
    return d


def with_sand(dec, sand=(36, 34, 33)):
    """Apply the Hades crust on top of a decal result."""
    def d(c, col):
        out = dec(c, col)
        if out[3] == 0 or len(out) > 4:
            return out
        if fbm(c.x * 0.35, c.y * 0.35, c.seed + 9, 2) > 0.64:
            return mix(out[:3], sand, 0.75) + (255,)
        return out
    return d


def switch(key, normal, alt):
    """Pick a material per texture variant (e.g. Agamemnon's black armour on the shade model)."""
    def f(c):
        return (alt if c.variant.get(key) else normal)(c)
    return f


def switch_decal(key, normal, alt):
    def d(c, col):
        fn = alt if c.variant.get(key) else normal
        return fn(c, col) if fn else col
    return d
