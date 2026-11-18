"""Armor models + textures for the copper helm, copper cuirass and Aegis plate (attachables).
Helm: custom Corinthian helmet geometry (bone "head", follows the player's head) with a red crest.
Chest pieces: vanilla geometry.humanoid.armor.chestplate with a 64x32 armor-layer texture.
Usage: python3 paint_armor.py <RP dir>"""
import json, os, sys
from PIL import Image, ImageDraw
RP = sys.argv[1]; S = 4
C = dict(base=(194, 122, 69), hi=(232, 163, 104), lo=(138, 78, 42), dark=(90, 50, 28), red=(160, 36, 30), red_lo=(110, 24, 20),
         gold=(214, 168, 80), leather=(92, 62, 38))
def rect(d, x, y, w, h, col, s=S): d.rectangle([x * s, y * s, (x + w) * s - 1, (y + h) * s - 1], fill=col + (255,))
def metal(d, x, y, w, h, s=S, base=None, hi=None, lo=None):
    base = base or C["base"]; hi = hi or C["hi"]; lo = lo or C["lo"]
    rect(d, x, y, w, h, base, s)
    d.rectangle([x * s, y * s, (x + w) * s - 1, y * s + max(1, s // 2) - 1], fill=hi + (255,))       # top highlight
    d.rectangle([x * s, (y + h) * s - max(1, s // 2), (x + w) * s - 1, (y + h) * s - 1], fill=lo + (255,))  # lower rim
def box_faces(u, v, w, h, d):
    return {"up": (u + d, v, w, d), "down": (u + d + w, v, w, d), "east": (u, v + d, d, h), "north": (u + d, v + d, w, h),
            "west": (u + d + w, v + d, d, h), "south": (u + 2 * d + w, v + d, w, h)}

# ---------------- helm (64x64 UV, painted at 4x)
helm = Image.new("RGBA", (64 * S, 64 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(helm)
for f, (x, y, w, h) in box_faces(0, 0, 8, 8, 8).items():
    metal(d, x, y, w, h)
    if f in ("east", "west", "south"):
        rect(d, x, y + 6, w, 1, C["gold"])                       # embossed brow band
fx, fy, _, _ = box_faces(0, 0, 8, 8, 8)["north"]
metal(d, fx, fy, 8, 8)
rect(d, fx, fy + 2, 8, 1, C["gold"])                             # brow ridge
for (ex, ew) in ((1, 2.5), (4.5, 2.5)):                          # almond eye openings (transparent)
    d.rectangle([(fx + ex) * S, (fy + 3.2) * S, (fx + ex + ew) * S - 1, (fy + 4.4) * S - 1], fill=(0, 0, 0, 0))
d.rectangle([(fx + 3.5) * S, (fy + 3.2) * S, (fx + 4.5) * S - 1, (fy + 8) * S - 1], fill=(0, 0, 0, 0))   # vertical mouth slit
rect(d, fx + 3.5, fy + 4.4, 1, 1.4, C["hi"])                     # nose guard
for f, (x, y, w, h) in box_faces(0, 16, 1, 3, 12).items():       # crest
    rect(d, x, y, w, h, C["red"] if f != "down" else C["red_lo"])
    for i in range(int(w * S)):
        if i % 3 == 0: d.line([(x * S + i, y * S), (x * S + i, (y + h) * S - 1)], fill=C["red_lo"] + (255,))
for f, (x, y, w, h) in box_faces(28, 16, 2, 1, 12).items():      # crest holder
    metal(d, x, y, w, h)
os.makedirs(os.path.join(RP, "textures/models/armor"), exist_ok=True)
helm.save(os.path.join(RP, "textures/models/armor/copper_helm.png"))

# ---------------- chest pieces (standard 64x32 armor layer, painted at 4x)
def chest(path, style):
    im = Image.new("RGBA", (64 * S, 32 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for f, (x, y, w, h) in box_faces(16, 16, 8, 12, 4).items():   # body
        metal(d, x, y, w, h)
        if f == "north":
            if style == "cuirass":                                # muscle cuirass: pectorals + abdominal lines
                rect(d, x + 1, y + 2, 2.6, 2, C["hi"]); rect(d, x + 4.4, y + 2, 2.6, 2, C["hi"])
                rect(d, x + 3.8, y + 1, 0.4, 8, C["lo"])
                for yy in (5, 6.6, 8.2): rect(d, x + 2, y + yy, 4, 0.3, C["lo"])
            else:                                                 # Aegis plate: Gorgoneion medallion
                d.ellipse([(x + 2) * S, (y + 2) * S, (x + 6) * S - 1, (y + 6) * S - 1], fill=C["gold"] + (255,), outline=C["dark"] + (255,))
                rect(d, x + 3.2, y + 3.4, 0.6, 0.6, C["dark"]); rect(d, x + 4.2, y + 3.4, 0.6, 0.6, C["dark"])
                rect(d, x + 3.4, y + 4.8, 1.2, 0.4, C["dark"])
        if f in ("north", "south"):
            for i in range(8):                                    # leather pteruges hanging at the hem
                rect(d, x + i + 0.1, y + 10, 0.8, 2, C["leather"])
    for f, (x, y, w, h) in box_faces(40, 16, 4, 12, 4).items():   # arms: shoulder guard, bare below
        if f == "down": continue
        if f == "up": metal(d, x, y, w, h); continue
        metal(d, x, y, w, 3.5)
        rect(d, x, y + 3.5, w, 0.6, C["gold"] if style == "aegis" else C["lo"])
    im.save(os.path.join(RP, path))
chest("textures/models/armor/copper_cuirass.png", "cuirass")
chest("textures/models/armor/aegis_copper_plate.png", "aegis")

geo = {"format_version": "1.12.0", "minecraft:geometry": [{
    "description": {"identifier": "geometry.studio_corinthian_helm", "texture_width": 64, "texture_height": 64,
                    "visible_bounds_width": 2, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1.5, 0]},
    "bones": [
        {"name": "head", "pivot": [0, 24, 0], "cubes": [{"origin": [-4, 24, -4], "size": [8, 8, 8], "uv": [0, 0], "inflate": 1.0}]},
        {"name": "crest_holder", "parent": "head", "pivot": [0, 33, 0], "cubes": [{"origin": [-1, 33, -6], "size": [2, 1, 12], "uv": [28, 16]}]},
        {"name": "crest", "parent": "head", "pivot": [0, 34, 0], "cubes": [{"origin": [-0.5, 34, -6], "size": [1, 3, 12], "uv": [0, 16], "inflate": 0.2}]},
    ]}, {
    "description": {"identifier": "geometry.studio_copper_chest", "texture_width": 64, "texture_height": 32,
                    "visible_bounds_width": 2, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1.5, 0]},
    "bones": [
        {"name": "body", "pivot": [0, 24, 0], "cubes": [{"origin": [-4, 12, -2], "size": [8, 12, 4], "uv": [16, 16], "inflate": 1.01}]},
        {"name": "rightArm", "pivot": [-5, 22, 0], "cubes": [{"origin": [-8, 12, -2], "size": [4, 12, 4], "uv": [40, 16], "inflate": 1.0}]},
        {"name": "leftArm", "pivot": [5, 22, 0], "mirror": True, "cubes": [{"origin": [4, 12, -2], "size": [4, 12, 4], "uv": [40, 16], "inflate": 1.0}]},
    ]}]}
json.dump(geo, open(os.path.join(RP, "models/entity/studio_armor.geo.json"), "w"), indent=2)
print("armor done")
