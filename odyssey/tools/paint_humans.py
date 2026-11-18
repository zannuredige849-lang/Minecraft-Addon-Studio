"""Paints clean, UV-correct textures for every humanoid that uses geometry.ship_crew.

The geometry declares a 64x64 UV space with quarter-unit UVs, so textures are painted at 8x
(512x512) and every cube face is filled with a shaded material swatch. No random per-pixel noise:
cloth gets soft vertical folds, metal gets a highlight band, skin gets a gentle top-light.
Usage: python3 paint_humans.py <RP dir>
"""
import json, sys, os
from PIL import Image, ImageDraw

RP = sys.argv[1]
S = 8  # pixels per UV unit
geo = json.load(open(os.path.join(RP, "models/entity/ship_crew.geo.json")))["minecraft:geometry"][0]
BONES = {b["name"]: b for b in geo["bones"]}

def hexc(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def shade(c, k): return tuple(max(0, min(255, int(v * k))) for v in c)

FACE_LIGHT = {"up": 1.12, "north": 1.0, "south": 0.86, "east": 0.93, "west": 0.93, "down": 0.7}

def faces_of(cube):
    u, v = cube["uv"]; w, h, d = cube["size"]
    return {"up": (u + d, v, w, d), "down": (u + d + w, v, w, d), "north": (u + d, v + d, w, h),
            "south": (u + 2 * d + w, v + d, w, h), "east": (u, v + d, d, h), "west": (u + d + w, v + d, d, h)}

def fill_face(img, rect, base, face, style):
    u, v, w, h = rect
    x0, y0 = round(u * S), round(v * S); x1, y1 = max(x0 + 1, round((u + w) * S)), max(y0 + 1, round((v + h) * S))
    px = img.load(); base = shade(base, FACE_LIGHT[face])
    W, H = x1 - x0, y1 - y0
    for y in range(y0, y1):
        for x in range(x0, x1):
            tx = (x - x0 + 0.5) / W; ty = (y - y0 + 0.5) / H
            k = 1.0
            if style == "cloth":       # soft folds
                k *= 0.94 + 0.06 * abs(((tx * 3.0) % 1.0) - 0.5) * 2
                k *= 1.04 - 0.10 * ty
            elif style == "metal":     # polished copper: highlight band + darker rim
                k *= 0.86 + 0.30 * max(0.0, 1 - abs(tx - 0.35) * 3.2)
                k *= 1.05 - 0.12 * ty
            elif style == "skin":
                k *= 1.03 - 0.08 * ty
            elif style == "leather":
                k *= 0.95 + 0.05 * (1 - ty)
            if x in (x0, x1 - 1) or y in (y0, y1 - 1):
                k *= 0.82 if W > 3 and H > 3 else 0.95
            px[x, y] = shade(base, k) + (255,)

def paint_face(img, cube, pal):
    """Eyes, brows, beard and mouth on the head's front (north) face."""
    u, v, w, h = faces_of(cube)["north"]
    d = ImageDraw.Draw(img)
    X = lambda t: round((u + w * t) * S); Y = lambda t: round((v + h * t) * S)
    hair = pal["hair"]
    d.rectangle([X(0), Y(0), X(1) - 1, Y(0.18)], fill=hair + (255,))            # fringe
    for ex in (0.22, 0.60):
        d.rectangle([X(ex), Y(0.36), X(ex + 0.18) - 1, Y(0.46)], fill=(245, 240, 230, 255))   # eye white
        d.rectangle([X(ex + 0.06), Y(0.36), X(ex + 0.13) - 1, Y(0.46)], fill=pal["eye"] + (255,))
        d.rectangle([X(ex - 0.02), Y(0.29), X(ex + 0.20) - 1, Y(0.33)], fill=shade(hair, 0.8) + (255,))  # brow
    if pal.get("beard"):
        b = pal["beard"]
        d.rectangle([X(0), Y(0.58), X(0.12) - 1, Y(1) - 1], fill=b + (255,))
        d.rectangle([X(0.88), Y(0.58), X(1) - 1, Y(1) - 1], fill=b + (255,))
        d.rectangle([X(0.12), Y(0.72), X(0.88) - 1, Y(1) - 1], fill=b + (255,))
        d.rectangle([X(0.34), Y(0.64), X(0.66) - 1, Y(0.69)], fill=shade(b, 0.9) + (255,))  # moustache
    d.rectangle([X(0.36), Y(0.76) if not pal.get("beard") else Y(0.70), X(0.64) - 1, (Y(0.80) if not pal.get("beard") else Y(0.73))],
                fill=(120, 60, 50, 255))

# material of every cube, by bone name and cube index
def material(bone, i, pal):
    m = {
        "hips": ["tunic", "belt"] + ["pteruges"] * 14 + ["tunic", "tunic", "scabbard"],
        "waist": ["belt", "tunic"],
        "chest": ["torso", "trim", "trim", "trim", "torso_outer", "cloak"],
        "neck": ["skin"],
        "head": ["skin", "hair", "hair", "skin", "skin", "hair", "hair", "skin", "skin", "skin", "hair", "hair"],
        "arm_r": ["skin", "shoulder", "shoulder"], "arm_l": ["skin", "shoulder", "shoulder"],
        "forearm_r": ["skin", "bracer"], "forearm_l": ["skin", "bracer"],
        "thigh_r": ["skin", "tunic"], "thigh_l": ["skin", "tunic"],
        "shin_r": ["skin", "sandal", "greave"], "shin_l": ["skin", "sandal", "greave"],
        "foot_r": ["sandal", "skin", "sandal"], "foot_l": ["sandal", "skin", "sandal"],
    }.get(bone)
    if bone.startswith("hand"):
        return "skin"
    return m[i] if m and i < len(m) else "tunic"

STYLE = {"skin": "skin", "hair": "leather", "tunic": "cloth", "torso": "cloth", "torso_outer": "cloth", "cloak": "cloth",
         "trim": "metal", "belt": "leather", "pteruges": "leather", "scabbard": "leather", "shoulder": "metal",
         "bracer": "leather", "greave": "metal", "sandal": "leather"}

def paint(pal, out):
    img = Image.new("RGBA", (64 * S, 64 * S), (0, 0, 0, 0))
    for bname, b in BONES.items():
        for i, c in enumerate(b.get("cubes", [])):
            mat = material(bname, i, pal)
            col = pal.get(mat) or pal["tunic"]
            if col is None:
                continue
            for face, rect in faces_of(c).items():
                fill_face(img, rect, col, face, STYLE.get(mat, "cloth"))
            if bname == "head" and i == 0:
                paint_face(img, c, pal)
                for face in ("south", "east", "west", "up"):   # hair over crown and back of head
                    u, v, w, h = faces_of(c)[face]
                    if face != "up":
                        h = h * (0.95 if face == "south" else 0.45)
                    fill_face(img, (u, v, w, h), pal["hair"], face, "leather")
    img.save(out)

H = hexc
PALETTES = {
    # The ship's crew: plain sailors in undyed chiton with a red sash (keeps the old spawn-egg colours).
    "ship_crew": dict(skin=H("c99a74"), hair=H("3b2a1e"), beard=H("3b2a1e"), eye=H("3a2c22"), tunic=H("d8cdb6"), torso=H("d8cdb6"),
                      torso_outer=H("a63a2c"), trim=H("b06a3c"), cloak=H("8a3328"), belt=H("6b4a2e"), pteruges=H("7a5634"),
                      scabbard=H("5a3d26"), shoulder=H("d8cdb6"), bracer=H("6b4a2e"), greave=H("c99a74"), sandal=H("6b4a2e")),
    # Telemachus: young, beardless prince of Ithaca in a blue-grey chiton and travelling cloak (interpretation).
    "telemachus": dict(skin=H("d2a47c"), hair=H("4a3022"), beard=None, eye=H("4a3a2a"), tunic=H("6f7f8f"), torso=H("6f7f8f"),
                       torso_outer=H("56677a"), trim=H("c08a50"), cloak=H("3f4a5c"), belt=H("5c3f28"), pteruges=H("5c3f28"),
                       scabbard=H("4a321f"), shoulder=H("56677a"), bracer=H("5c3f28"), greave=H("d2a47c"), sandal=H("5c3f28")),
    # Odysseus (portrait / NPC stand-in): copper muscle cuirass, red cloak, grey-streaked beard.
    "odysseus": dict(skin=H("b88560"), hair=H("4d4038"), beard=H("6b6058"), eye=H("3a3028"), tunic=H("9a3a2c"), torso=H("c27a45"),
                     torso_outer=H("b8703e"), trim=H("e0a060"), cloak=H("8e2a22"), belt=H("4a3220"), pteruges=H("5a3a22"),
                     scabbard=H("3e2a1a"), shoulder=H("c27a45"), bracer=H("4a3220"), greave=H("c27a45"), sandal=H("4a3220")),
    # Mentor: older friend of the house, undyed wool and a staff-bearer's grey cloak.
    "mentor": dict(skin=H("b8906c"), hair=H("a8a29a"), beard=H("bcb6ae"), eye=H("3a3028"), tunic=H("bfb29a"), torso=H("bfb29a"),
                   torso_outer=H("8f8676"), trim=H("8a6a48"), cloak=H("6e6a62"), belt=H("5a4430"), pteruges=H("5a4430"),
                   scabbard=H("5a4430"), shoulder=H("8f8676"), bracer=H("5a4430"), greave=H("b8906c"), sandal=H("5a4430")),
    # Eumaeus: the swineherd; rough brown wool and a hide wrap.
    "eumaeus": dict(skin=H("a8774f"), hair=H("2e2420"), beard=H("38302a"), eye=H("2e2420"), tunic=H("7a6248"), torso=H("7a6248"),
                    torso_outer=H("8c6d4a"), trim=H("5a4430"), cloak=H("5e4a36"), belt=H("3e2e20"), pteruges=H("6a5038"),
                    scabbard=H("3e2e20"), shoulder=H("8c6d4a"), bracer=H("3e2e20"), greave=H("a8774f"), sandal=H("3e2e20")),
    # Travel guides (variants 0-2): a coastal scout, a fisherman, a shepherd.
    "guide_scout": dict(skin=H("c08e66"), hair=H("2a2420"), beard=H("2a2420"), eye=H("2a2420"), tunic=H("8a7c5c"), torso=H("8a7c5c"),
                        torso_outer=H("6c6248"), trim=H("a07040"), cloak=H("556048"), belt=H("4a3826"), pteruges=H("4a3826"),
                        scabbard=H("4a3826"), shoulder=H("6c6248"), bracer=H("4a3826"), greave=H("c08e66"), sandal=H("4a3826")),
    "guide_fisher": dict(skin=H("b07a52"), hair=H("3a2e26"), beard=H("4a3c30"), eye=H("2a2420"), tunic=H("c9bfa8"), torso=H("c9bfa8"),
                         torso_outer=H("4d6a78"), trim=H("8a6a48"), cloak=H("4d6a78"), belt=H("6a5038"), pteruges=H("c9bfa8"),
                         scabbard=H("6a5038"), shoulder=H("c9bfa8"), bracer=H("b07a52"), greave=H("b07a52"), sandal=H("6a5038")),
    "guide_shepherd": dict(skin=H("c49470"), hair=H("6a5a48"), beard=H("7a6a58"), eye=H("2a2420"), tunic=H("d6ceb8"), torso=H("d6ceb8"),
                           torso_outer=H("e8e2d2"), trim=H("8a6a48"), cloak=H("a89c84"), belt=H("6a5038"), pteruges=H("d6ceb8"),
                           scabbard=H("6a5038"), shoulder=H("e8e2d2"), bracer=H("6a5038"), greave=H("c49470"), sandal=H("6a5038")),
}

if __name__ == "__main__":
    os.makedirs(os.path.join(RP, "textures/entity/people"), exist_ok=True)
    for name, pal in PALETTES.items():
        out = os.path.join(RP, "textures/entity", "ship_crew.png" if name == "ship_crew" else f"people/{name}.png")
        paint(pal, out)
        print("painted", out)
