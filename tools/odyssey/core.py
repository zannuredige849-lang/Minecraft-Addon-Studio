"""Core: noise, colour grading, the box-UV Model with HD texel density, atlas packing and PNG output."""
import math
import struct
import zlib


# ------------------------------------------------------------------ noise
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


# ------------------------------------------------------------------ colour
def clamp8(v):
    return 0 if v < 0 else 255 if v > 255 else int(v)


def mix(a, b, t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def mul(c, k):
    if isinstance(k, tuple):
        return (c[0] * k[0], c[1] * k[1], c[2] * k[2])
    return (c[0] * k, c[1] * k, c[2] * k)


SIDES = ("north", "south", "east", "west")
FACE_LIGHT = {"up": 1.12, "north": 1.0, "east": 0.9, "west": 0.9, "south": 0.82, "down": 0.62}


class Ctx:
    """Per-texel paint context. x,y are pixel coords inside the face; u,v are the same in model units."""
    __slots__ = ("face", "x", "y", "w", "h", "seed", "fo", "variant", "D", "size")

    @property
    def u(self):
        return self.x / self.D

    @property
    def v(self):
        return self.y / self.D


def lighting(c):
    l = FACE_LIGHT[c.face]
    if c.face in SIDES and c.h > 1:
        l *= 1.07 - 0.2 * (c.y / (c.h - 1))
    if c.w > 3 and c.h > 3 and (c.x == 0 or c.y == 0 or c.x == c.w - 1 or c.y == c.h - 1):
        l *= 0.88
    return l


def grade(rgb, l):
    """Film grade: cool shadows, warm highlights, slight desaturation and contrast."""
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


# ------------------------------------------------------------------ model
class Model:
    """Bedrock geometry builder. Units are model pixels (16 per block before client scale).
    D = texture pixels per unit; every cube size must be a multiple of 1/D."""

    def __init__(self, name, seed, D=2):
        self.name, self.seed, self.D = name, seed, D
        self.bones, self.index, self.paired, self.cubes = [], {}, set(), []
        self.tw = self.th = 0
        self.locators = {}

    # ---------------------------------------------------------- bones and cubes
    def bone(self, name, parent, pivot, rot=None):
        assert name not in self.index, f"duplicate bone {name}"
        if parent:
            assert parent in self.index, f"{name}: unknown parent {parent}"
        b = {"name": name, "pivot": [float(v) for v in pivot]}
        if parent:
            b["parent"] = parent
        if rot and any(rot):
            b["rotation"] = [float(v) for v in rot]
        b["cubes"] = []
        self.bones.append(b)
        self.index[name] = b
        return name

    def snap(self, v):
        return round(v * self.D) / self.D

    def cube(self, bone, origin, size, mat, rot=None, pivot=None, decal=None, inflate=None, tag=None):
        size = tuple(max(1.0 / self.D, self.snap(s)) for s in size)
        cd = {"origin": [round(v, 4) for v in origin], "size": list(size)}
        if rot and any(rot):
            p = pivot or (origin[0] + size[0] / 2, origin[1] + size[1] / 2, origin[2] + size[2] / 2)
            cd["pivot"] = [round(v, 4) for v in p]
            cd["rotation"] = [round(v, 4) for v in rot]
        if inflate:
            cd["inflate"] = inflate
        self.index[bone]["cubes"].append(cd)
        self.cubes.append({"cd": cd, "mat": mat, "decal": decal or {}, "bone": bone, "tag": tag,
                           "seed": self.seed * 1000 + len(self.cubes) * 37})
        return cd

    def cbox(self, bone, center, size, mat, rot=None, pivot=None, **kw):
        """Box given by its centre."""
        size = tuple(max(1.0 / self.D, self.snap(s)) for s in size)
        o = (center[0] - size[0] / 2, center[1] - size[1] / 2, center[2] - size[2] / 2)
        return self.cube(bone, o, size, mat, rot=rot, pivot=pivot or (center if rot else None), **kw)

    @staticmethod
    def mo(origin, size):
        return (-origin[0] - size[0], origin[1], origin[2])

    @staticmethod
    def mr(rot):
        return None if rot is None else (rot[0], -rot[1], -rot[2])

    @staticmethod
    def mp(p):
        return None if p is None else (-p[0], p[1], p[2])

    def side(self, base, parent, pivot, rot=None):
        """Bone pair base_r (as given, on -x) and base_l (mirrored)."""
        for s in ("r", "l"):
            par = (f"{parent}_{s}" if parent in self.paired else parent) if parent else None
            if s == "r":
                self.bone(f"{base}_r", par, pivot, rot)
            else:
                self.bone(f"{base}_l", par, self.mp(pivot), self.mr(rot))
        self.paired.add(base)

    def scbox(self, base, center, size, mat, rot=None, pivot=None, **kw):
        """Centred box on base_r plus its mirror on base_l."""
        self.cbox(f"{base}_r", center, size, mat, rot=rot, pivot=pivot, **kw)
        c2 = (-center[0], center[1], center[2])
        self.cbox(f"{base}_l", c2, size, mat, rot=self.mr(rot), pivot=self.mp(pivot), **kw)

    def mcbox(self, bone, center, size, mat, rot=None, pivot=None, **kw):
        """Centred box and its mirror across x=0 on the same bone."""
        self.cbox(bone, center, size, mat, rot=rot, pivot=pivot, **kw)
        self.cbox(bone, (-center[0], center[1], center[2]), size, mat, rot=self.mr(rot), pivot=self.mp(pivot), **kw)

    def locator(self, bone, name, pos):
        self.index[bone].setdefault("locators", {})[name] = [round(v, 3) for v in pos]

    # ---------------------------------------------------------- transforms
    def shift(self, dx=0.0, dy=0.0, dz=0.0):
        for b in self.bones:
            b["pivot"] = [b["pivot"][0] + dx, b["pivot"][1] + dy, b["pivot"][2] + dz]
            for cd in b["cubes"]:
                cd["origin"] = [round(cd["origin"][0] + dx, 4), round(cd["origin"][1] + dy, 4), round(cd["origin"][2] + dz, 4)]
                if "pivot" in cd:
                    cd["pivot"] = [round(cd["pivot"][0] + dx, 4), round(cd["pivot"][1] + dy, 4), round(cd["pivot"][2] + dz, 4)]
            for k, v in b.get("locators", {}).items():
                b["locators"][k] = [v[0] + dx, v[1] + dy, v[2] + dz]

    # ---------------------------------------------------------- atlas
    def pack(self):
        items = []
        for i, c in enumerate(self.cubes):
            w, h, d = c["cd"]["size"]
            items.append((d + h, 2 * (d + w), i))
        items.sort(key=lambda t: (-t[0], -t[1]))
        widest = max(t[1] for t in items)
        g = 1.0 / self.D
        for W in (32, 64, 128, 256, 512, 1024):
            if widest > W:
                continue
            x = y = row = 0.0
            pos = {}
            for hh, ww, i in items:
                if x + ww > W:
                    x, y, row = 0.0, y + row, 0.0
                pos[i] = (x, y)
                x += ww + g          # one texel gap against bleeding
                row = max(row, hh + g)
            H = y + row
            if H <= W:
                break
        hp = 16
        while hp < H:
            hp *= 2
        for i, (u, v) in pos.items():
            self.cubes[i]["cd"]["uv"] = [round(u, 4), round(v, 4)]
        self.tw, self.th = W, hp

    def paint(self, variant=None):
        variant = variant or {}
        D = self.D
        W, H = int(self.tw * D), int(self.th * D)
        img = [[(0, 0, 0, 0)] * W for _ in range(H)]
        ctx = Ctx()
        ctx.variant, ctx.D = variant, D
        for cb in self.cubes:
            w, h, d = cb["cd"]["size"]
            u, v = cb["cd"]["uv"]
            ctx.size = (w, h, d)
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
                        if len(px) > 4:          # emissive / pre-lit texel
                            row[px0 + xx] = (clamp8(px[0]), clamp8(px[1]), clamp8(px[2]), clamp8(px[3]))
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


# ------------------------------------------------------------------ PNG
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
