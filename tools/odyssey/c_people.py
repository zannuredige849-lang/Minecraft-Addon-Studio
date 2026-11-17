"""Human-shaped characters of Nolan's The Odyssey (2026): Circe, the Sirens, Calypso, Athena, Tiresias and the
shades of the dead. Each is built on the shared anatomical body with film-described costume on top."""
from .core import Model
from .human import build_human, hood
from .materials import (skin, cloth, linen, fishnet, hair, leather, metal, human_face, crust, translucent,
                        switch, switch_decal, flat)
from .parts import strands


# ------------------------------------------------------------------ costume helpers
def gown(m, b, mat, flare=0.45, hem=0.12, tatter=0.0, folds=True, fold_mat=None, top="chest"):
    """Full-length garment: bodice, waist and an A-line skirt to the ankles (on the hips bone)."""
    hh = b.hh
    m.cbox("chest", (0, b.y_chest_lo + (b.y_sh - b.y_chest_lo) / 2 + 0.04 * hh, 0),
           (b.chest_w + 0.12 * hh, b.y_sh - b.y_chest_lo + 0.22 * hh, b.chest_d + 0.14 * hh), mat)
    m.cbox("waist", (0, (b.y_waist + b.y_chest_lo) / 2, 0),
           (b.waist_w + 0.14 * hh, b.y_chest_lo - b.y_waist + 0.12 * hh, b.chest_d + 0.12 * hh), mat)
    top_y = b.y_waist + 0.05 * hh
    mid_y = b.y_hip - 1.6 * hh
    m.cbox("hips", (0, (top_y + mid_y) / 2, 0.02 * hh), (b.hip_w + 0.16 * hh, top_y - mid_y, b.chest_d + 0.2 * hh), mat)
    lo_h = mid_y - hem
    m.cbox("hips", (0, mid_y - lo_h / 2 + 0.02, 0.02 * hh), (b.hip_w + flare * hh, lo_h + 0.05, b.chest_d + flare * hh * 0.9),
           mat if not tatter else _tattered(mat, tatter))
    if folds:
        fm = fold_mat or mat
        w, d = b.hip_w + flare * hh, b.chest_d + flare * hh * 0.9
        for i, fx in enumerate((-0.36, -0.12, 0.12, 0.36)):
            m.cbox("hips", (fx * w, mid_y - lo_h / 2 + 0.02, -d / 2 - 0.05 * hh), (0.12 * hh, lo_h, 0.1 * hh), fm)
        for fz in (-0.25, 0.25):
            m.mcbox("hips", (-w / 2 - 0.04 * hh, mid_y - lo_h / 2 + 0.02, fz * d), (0.1 * hh, lo_h, 0.12 * hh), fm)


def _tattered(mat, amount):
    def f(c):
        px = mat(c)
        from .core import SIDES, hash2
        if c.face in SIDES and c.v >= c.size[1] - hash2(int(c.u * 2), 33, c.seed) * amount:
            return (0, 0, 0, 0)
        return px
    return f


def sleeves(m, b, mat, to="elbow", wide=0.0):
    hh = b.hh
    m.scbox("arm", (-b.x_sh - 0.02 * hh, b.y_sh - 0.62 * hh, 0), (0.46 * hh + wide * hh, 1.3 * hh, 0.48 * hh + wide * hh), mat)
    if to == "wrist":
        m.scbox("forearm", (-b.x_sh, b.y_elbow - 0.55 * hh, 0), (0.42 * hh + wide * hh, 1.15 * hh, 0.44 * hh + wide * hh), mat)


def long_hair(m, b, mat, length=2.2, front=True, crown=True, side_len=1.2, seed=1, count=7):
    """Crown, a back mass hanging `length` head-heights, and side strands framing the face."""
    hh, hc = b.hh, b.head_c
    top = hc[1] + b.head_h / 2
    if crown:
        m.cbox("head", (0, top + 0.06 * hh, hc[2] + 0.04 * hh), (b.head_w + 0.1 * hh, 0.14 * hh, b.head_d + 0.1 * hh), mat)
        m.cbox("head", (0, top - 0.12 * hh, hc[2] - b.head_d / 2 - 0.03 * hh), (b.head_w * 0.9, 0.22 * hh, 0.08 * hh), mat)
    back_h = length * hh
    m.cbox("head", (0, top - back_h / 2 + 0.05 * hh, hc[2] + b.head_d / 2 + 0.06 * hh), (b.head_w + 0.14 * hh, back_h, 0.14 * hh), mat)
    strands(m, "head", -b.head_w / 2 - 0.02 * hh, b.head_w / 2 + 0.02 * hh, top - 0.05 * hh, hc[2] + b.head_d / 2 + 0.17 * hh,
            (back_h * 0.75, back_h * 1.08), 0.12 * hh, 0.1 * hh, mat, count, seed=seed)
    if front:
        for sx in (-1, 1):
            strands(m, "head", sx * (b.head_w / 2 + 0.05 * hh) - 0.04 * hh, sx * (b.head_w / 2 + 0.05 * hh) + 0.04 * hh,
                    top - 0.02 * hh, hc[2] - b.head_d * 0.15, (side_len * hh * 0.8, side_len * hh), 0.08 * hh, b.head_d * 0.7,
                    mat, 2, seed=seed + (3 if sx > 0 else 0))


# ------------------------------------------------------------------ Circe
def build_circe():
    """An aged, plain-looking pagan witch living in a dilapidated house (Villains Wiki); Samantha Morton."""
    m = Model("circe", 37, D=4)
    face = human_face(iris=(128, 138, 118), brow=(108, 102, 96), lips=(156, 108, 102), eye_y=0.48, mouth_y=0.8, age=0.16)
    b = build_human(m, 27.2, sex="f", heads=7.2, skin_color=(212, 188, 170), skin_kw={"wrinkle": 0.08, "spots": 0.08},
                    face=face, nail=(186, 160, 140), legs=False, feet="bare", stoop=7, build=0.95)
    hh = b.hh
    DRESS = cloth((98, 88, 70), folds=0.12, grime=0.32, patch=(78, 70, 56), tatter=0.0)
    SKIRT = cloth((86, 78, 64), folds=0.14, grime=0.35, patch=(70, 62, 52))
    SHAWL = cloth((70, 62, 56), folds=0.08, weave=False, grime=0.15)
    APRON = cloth((120, 108, 86), folds=0.1, grime=0.4, patch=(96, 84, 66))
    HAIR = hair((150, 146, 140), tips=0.9, streak=(96, 92, 88))
    gown(m, b, DRESS, flare=0.5, tatter=0.5, fold_mat=SKIRT)
    m.cbox("hips", (0, b.y_hip - 0.6 * hh, -(b.chest_d + 0.45 * hh) / 2 - 0.06 * hh), (b.hip_w * 0.8, 2.1 * hh, 0.08 * hh), APRON)
    sleeves(m, b, DRESS, to="elbow")
    m.cbox("chest", (0, b.y_sh - 0.05 * hh, 0.02 * hh), (b.chest_w + 0.42 * hh, 0.42 * hh, b.chest_d + 0.4 * hh), SHAWL)
    m.mcbox("chest", (-0.38 * hh, b.y_sh - 0.62 * hh, -b.chest_d / 2 - 0.2 * hh), (0.42 * hh, 1.0 * hh, 0.1 * hh), SHAWL,
            rot=(0, 0, -16))
    m.cbox("chest", (0, b.y_sh - 0.65 * hh, b.chest_d / 2 + 0.18 * hh), (b.chest_w + 0.2 * hh, 1.1 * hh, 0.1 * hh), SHAWL)
    m.cbox("waist", (0, b.y_waist + 0.1 * hh, 0), (b.waist_w + 0.3 * hh, 0.14 * hh, b.chest_d + 0.3 * hh), leather((84, 66, 48)))
    m.cbox("waist", (0.42 * hh, b.y_waist - 0.25 * hh, -b.chest_d / 2 - 0.2 * hh), (0.3 * hh, 0.42 * hh, 0.16 * hh), leather((96, 74, 52)))
    long_hair(m, b, HAIR, length=2.4, side_len=1.5, seed=5, count=8)
    return m, b


# ------------------------------------------------------------------ Siren
def build_siren():
    """'Ordinary human silhouettes, distant and haze-shrouded in mist' (Villains Wiki). Rendered half-transparent."""
    m = Model("siren", 23, D=4)
    A = 196
    face = human_face(iris=(40, 40, 46), brow=(56, 54, 58), lips=(146, 116, 120), eye_y=0.5, mouth_y=0.8, mouth_open=0.06)
    skin_t = translucent(skin((206, 202, 200), mottle=0.5), A)
    b = build_human(m, 28.0, sex="f", heads=7.6, skin_color=(206, 202, 200), skin_override=skin_t, face=face,
                    nail=None, legs=False, feet="bare", build=0.88)
    hh = b.hh
    SHIFT = translucent(linen((200, 200, 198), bleach=0.05), A)
    FOLD = translucent(linen((176, 176, 176), bleach=0.0), A)
    HAIR = translucent(hair((36, 34, 38), tips=1.0), A)
    gown(m, b, SHIFT, flare=0.38, tatter=0.0, fold_mat=FOLD)
    long_hair(m, b, HAIR, length=3.0, side_len=2.0, seed=9, count=8)
    return m, b


# ------------------------------------------------------------------ Calypso
def build_calypso():
    """Charlize Theron's Calypso: 'a raw something that was woven, found, or washed up that she could just put on,
    rip, and tie', a fishnet outer-dress layer and sun-bleached linen (costume designer Ellen Mirojnick)."""
    m = Model("calypso", 61, D=4)
    face = human_face(iris=(112, 132, 150), brow=(170, 146, 110), lips=(178, 114, 110), eye_y=0.49, mouth_y=0.8)
    b = build_human(m, 28.6, sex="f", heads=7.6, skin_color=(224, 194, 170), skin_kw={"freckles": 0.03},
                    face=face, nail=(226, 200, 186), legs=True, feet="bare", build=0.93)
    hh = b.hh
    LIN = linen((232, 226, 210), bleach=0.2)
    LIN_T = linen((228, 222, 206), bleach=0.2, tatter=1.2)
    NET = fishnet((112, 94, 72), cell=0.7, thick=0.14)
    ROPE = leather((150, 124, 86))
    HAIR = hair((224, 204, 158), tips=1.0, streak=(246, 232, 196))
    # wrap dress tied at one shoulder, ripped short hem
    m.cbox("chest", (0, b.y_chest_lo + (b.y_sh - b.y_chest_lo) / 2, 0),
           (b.chest_w + 0.1 * hh, b.y_sh - b.y_chest_lo + 0.05 * hh, b.chest_d + 0.12 * hh), LIN)
    m.cbox("chest", (-0.42 * hh, b.y_sh + 0.12 * hh, -0.02 * hh), (0.26 * hh, 0.3 * hh, b.chest_d + 0.16 * hh), LIN, rot=(0, 0, 12))
    m.cbox("chest", (-0.5 * hh, b.y_sh + 0.3 * hh, -b.chest_d / 2 - 0.1 * hh), (0.18 * hh, 0.18 * hh, 0.18 * hh), ROPE)
    m.cbox("waist", (0, (b.y_waist + b.y_chest_lo) / 2, 0), (b.waist_w + 0.12 * hh, b.y_chest_lo - b.y_waist + 0.1 * hh, b.chest_d + 0.1 * hh), LIN)
    m.cbox("hips", (0, b.y_hip - 0.45 * hh, 0.02 * hh), (b.hip_w + 0.28 * hh, (b.y_waist - b.y_hip) + 1.3 * hh, b.chest_d + 0.3 * hh), LIN_T)
    m.cbox("waist", (0, b.y_waist + 0.05 * hh, 0), (b.waist_w + 0.24 * hh, 0.1 * hh, b.chest_d + 0.24 * hh), ROPE)
    m.cbox("waist", (0.3 * hh, b.y_waist - 0.3 * hh, -b.chest_d / 2 - 0.16 * hh), (0.08 * hh, 0.6 * hh, 0.08 * hh), ROPE)
    # fishnet outer layer
    m.cbox("chest", (0, b.y_chest_lo + (b.y_sh - b.y_chest_lo) / 2 - 0.1 * hh, 0),
           (b.chest_w + 0.24 * hh, b.y_sh - b.y_chest_lo, b.chest_d + 0.26 * hh), NET, tag="net")
    m.cbox("hips", (0, b.y_hip - 0.35 * hh, 0.02 * hh), (b.hip_w + 0.4 * hh, (b.y_waist - b.y_hip) + 1.5 * hh, b.chest_d + 0.42 * hh), NET, tag="net")
    long_hair(m, b, HAIR, length=2.6, side_len=1.7, seed=13, count=8)
    return m, b


# ------------------------------------------------------------------ Athena
def build_athena():
    """Zendaya's Athena: a 'hooded, artfully draped white linen robe' (Mirojnick)."""
    m = Model("athena", 67, D=4)
    face = human_face(iris=(70, 46, 30), brow=(36, 26, 22), lips=(124, 74, 66), eye_y=0.49, mouth_y=0.8)
    b = build_human(m, 28.4, sex="f", heads=7.6, skin_color=(150, 104, 78), face=face, nail=(186, 150, 130),
                    legs=False, feet="sandal", build=0.92)
    hh = b.hh
    ROBE = linen((238, 236, 230), bleach=0.05)
    DRAPE = linen((226, 224, 216), bleach=0.0)
    HAIR = hair((30, 24, 22), curly=True)
    SAND = leather((120, 86, 56))
    gown(m, b, ROBE, flare=0.42, fold_mat=DRAPE)
    m.cbox("chest", (0, b.y_sh - 0.85 * hh, -b.chest_d / 2 - 0.12 * hh), (0.32 * hh, 2.2 * hh, 0.08 * hh), DRAPE, rot=(0, 0, 28))
    m.cbox("chest", (0, b.y_sh - 0.85 * hh, b.chest_d / 2 + 0.12 * hh), (0.32 * hh, 2.2 * hh, 0.08 * hh), DRAPE, rot=(0, 0, 28))
    sleeves(m, b, ROBE, to="wrist", wide=0.14)
    m.cbox("head", (0, b.head_c[1] + 0.32 * hh, b.face_z + 0.04 * hh), (b.head_w * 0.92, 0.2 * hh, 0.1 * hh), HAIR)
    m.mcbox("head", (-b.head_w / 2 + 0.06 * hh, b.head_c[1] + 0.05 * hh, b.face_z + 0.1 * hh), (0.12 * hh, 0.5 * hh, 0.14 * hh), HAIR)
    hood(m, b, ROBE, extra=0.2, length=1.25, back_drop=0.6 * hh)
    m.cbox("chest", (0, b.y_sh + 0.08 * hh, 0.04 * hh), (b.chest_w + 0.3 * hh, 0.3 * hh, b.chest_d + 0.32 * hh), ROBE)
    for side, sx in (("r", 1), ("l", -1)):
        X = -b.x_hip * sx
        m.cbox(f"foot_{side}", (X, 0.05 * hh, -0.24 * hh), (0.36 * hh, 0.1 * hh, 0.9 * hh), SAND)
        m.cbox(f"foot_{side}", (X, 0.17 * hh, -0.24 * hh), (0.3 * hh, 0.16 * hh, 0.78 * hh), skin((150, 104, 78)))
        for zz in (-0.5, -0.1):
            m.cbox(f"foot_{side}", (X, 0.2 * hh, zz * hh), (0.38 * hh, 0.07 * hh, 0.08 * hh), SAND)
    return m, b


# ------------------------------------------------------------------ Tiresias
def build_tiresias():
    """The blind prophet who 'appears from underneath the sand' of Hades (James Remar)."""
    m = Model("tiresias", 71, D=4)
    SAND = (34, 32, 31)
    face = human_face(blind=True, brow=(150, 146, 140), lips=(120, 100, 96), eye_y=0.48, mouth_y=0.8, age=0.2,
                      beard=(150, 146, 138), beard_from=0.66, sand=SAND)
    b = build_human(m, 29.0, sex="m", heads=7.4, skin_color=(150, 144, 136), skin_kw={"wrinkle": 0.12},
                    skin_override=crust(skin((150, 144, 136), wrinkle=0.12), SAND, 0.5), face=face,
                    nail=None, legs=False, feet="bare", stoop=14, build=0.9)
    hh = b.hh
    ROBE = crust(cloth((70, 64, 58), folds=0.12, grime=0.3, tatter=0.0), SAND, 0.6)
    HAIR = crust(hair((168, 164, 156), tips=1.0), SAND, 0.35)
    gown(m, b, ROBE, flare=0.5, tatter=0.8)
    sleeves(m, b, ROBE, to="wrist", wide=0.1)
    long_hair(m, b, HAIR, length=1.9, side_len=1.3, seed=21, count=6)
    hc = b.head_c
    strands(m, "head", -0.22 * hh, 0.22 * hh, hc[1] - 0.3 * hh, b.face_z - 0.06 * hh, (0.9 * hh, 1.5 * hh), 0.1 * hh, 0.1 * hh,
            HAIR, 5, seed=4)
    m.cbox("head", (0, hc[1] - 0.45 * hh, b.face_z - 0.05 * hh), (0.5 * hh, 0.35 * hh, 0.12 * hh), HAIR)
    return m, b


# ------------------------------------------------------------------ Shades of the dead
def build_shade():
    """Odysseus' fallen soldiers rising from the black sand of Hades. Variants share the model:
    crew (crested helmet), Agamemnon (glossy black armour and towering horse-hair plume) and Sinon (young, bare-headed)."""
    m = Model("shade", 73, D=4)
    SAND = (34, 32, 31)
    dead_face = human_face(dead=True, brow=(70, 64, 58), lips=(110, 96, 92), eye_y=0.48, mouth_y=0.8,
                           beard=(54, 48, 44), beard_from=0.64, sand=SAND)
    young_face = human_face(dead=True, brow=(80, 70, 60), lips=(118, 100, 96), eye_y=0.48, mouth_y=0.8, sand=SAND)
    face = switch_decal("sinon", dead_face, young_face)
    SKIN = crust(skin((128, 122, 114)), SAND, 0.55)
    b = build_human(m, 29.6, sex="m", heads=7.5, skin_color=(128, 122, 114), skin_override=SKIN, face=face, nail=None,
                    legs=True, feet="sandal", build=1.0)
    hh = b.hh
    BRONZE = crust(metal((118, 90, 56), edge=(196, 160, 100), patina=(70, 96, 80), rivets=False), SAND, 0.6)
    BLACK = crust(metal((26, 26, 30), edge=(196, 198, 206), rivets=False, polish=0.6), SAND, 0.35)
    ARM = switch("agamemnon", BRONZE, BLACK)
    LINEN = crust(cloth((150, 134, 104), folds=0.1, grime=0.4), SAND, 0.6)
    STRIP = crust(leather((96, 72, 50)), SAND, 0.5)
    CREST = crust(hair((112, 40, 34), tips=0.4), SAND, 0.45)
    PLUME = hair((20, 18, 18), tips=0.8)
    CLOAK = crust(cloth((84, 40, 34), folds=0.12, tatter=1.6, grime=0.3), SAND, 0.6)
    # cuirass and shoulder guards
    m.cbox("chest", (0, b.y_chest_lo + (b.y_sh - b.y_chest_lo) / 2, 0),
           (b.chest_w + 0.16 * hh, b.y_sh - b.y_chest_lo + 0.2 * hh, b.chest_d + 0.2 * hh), ARM)
    m.cbox("waist", (0, (b.y_waist + b.y_chest_lo) / 2, 0), (b.waist_w + 0.2 * hh, b.y_chest_lo - b.y_waist + 0.1 * hh,
                                                            b.chest_d + 0.18 * hh), ARM)
    m.scbox("arm", (-b.x_sh - 0.06 * hh, b.y_sh - 0.1 * hh, 0), (0.55 * hh, 0.22 * hh, 0.6 * hh), LINEN, rot=(0, 0, 18))
    # war skirt of hanging strips (pteruges)
    m.cbox("hips", (0, b.y_waist - 0.25 * hh, 0), (b.hip_w + 0.14 * hh, 0.5 * hh, b.chest_d + 0.18 * hh), LINEN)
    n = 7
    w = (b.hip_w + 0.2 * hh) / n
    for i in range(n):
        x = -(b.hip_w + 0.2 * hh) / 2 + w * (i + 0.5)
        m.cbox("hips", (x, b.y_waist - 1.0 * hh, -b.chest_d / 2 - 0.12 * hh), (w * 0.86, 1.0 * hh, 0.08 * hh), STRIP)
        m.cbox("hips", (x, b.y_waist - 1.0 * hh, b.chest_d / 2 + 0.12 * hh), (w * 0.86, 1.0 * hh, 0.08 * hh), STRIP)
    m.mcbox("hips", (-(b.hip_w + 0.2 * hh) / 2 - 0.04 * hh, b.y_waist - 1.0 * hh, 0), (0.08 * hh, 1.0 * hh, b.chest_d + 0.16 * hh), STRIP)
    # greaves and sandals
    sh = b.y_knee - b.y_ankle
    m.scbox("shin", (-b.x_hip, b.y_knee - sh * 0.45, -0.04 * hh), (0.46 * hh, sh * 0.8, 0.48 * hh), ARM)
    for side, sx in (("r", 1), ("l", -1)):
        X = -b.x_hip * sx
        m.cbox(f"foot_{side}", (X, 0.05 * hh, -0.24 * hh), (0.38 * hh, 0.1 * hh, 0.92 * hh), STRIP)
        m.cbox(f"foot_{side}", (X, 0.18 * hh, -0.24 * hh), (0.32 * hh, 0.18 * hh, 0.8 * hh), SKIN)
        m.cbox(f"foot_{side}", (X, 0.3 * hh, -0.05 * hh), (0.4 * hh, 0.08 * hh, 0.36 * hh), STRIP)
    # tattered cloak at the back
    m.cbox("chest", (0, b.y_sh - 1.5 * hh, b.chest_d / 2 + 0.2 * hh), (b.chest_w + 0.1 * hh, 3.1 * hh, 0.1 * hh), CLOAK)
    # sword at the left hip
    m.cbox("hips", (b.hip_w / 2 + 0.16 * hh, b.y_waist - 1.0 * hh, 0.1 * hh), (0.14 * hh, 1.6 * hh, 0.3 * hh), STRIP,
           rot=(14, 0, 0))
    # helmet (Corinthian type, as worn by Odysseus' men in the film), crest and Agamemnon's plume
    hc, hw, hd = b.head_c, b.head_w, b.head_d
    m.bone("helmet", "head", (0, hc[1], hc[2]))
    top = hc[1] + b.head_h / 2
    m.cbox("helmet", (0, top + 0.05 * hh, hc[2]), (hw + 0.16 * hh, 0.26 * hh, hd + 0.16 * hh), ARM)
    m.cbox("helmet", (0, hc[1] + 0.05 * hh, hc[2] + hd / 2 + 0.06 * hh), (hw + 0.16 * hh, b.head_h + 0.1 * hh, 0.12 * hh), ARM)
    m.mcbox("helmet", (-hw / 2 - 0.06 * hh, hc[1] + 0.05 * hh, hc[2]), (0.12 * hh, b.head_h + 0.1 * hh, hd + 0.14 * hh), ARM)
    m.mcbox("helmet", (-hw * 0.3, hc[1] - 0.18 * hh, b.face_z - 0.06 * hh), (hw * 0.32, 0.55 * hh, 0.1 * hh), ARM)
    m.cbox("helmet", (0, hc[1] + 0.3 * hh, b.face_z - 0.06 * hh), (hw + 0.1 * hh, 0.22 * hh, 0.1 * hh), ARM)
    m.cbox("helmet", (0, hc[1] + 0.02 * hh, b.face_z - 0.08 * hh), (0.1 * hh, 0.36 * hh, 0.08 * hh), ARM)
    m.bone("crest", "helmet", (0, top + 0.2 * hh, hc[2]))
    m.cbox("crest", (0, top + 0.28 * hh, hc[2] + 0.1 * hh), (0.14 * hh, 0.18 * hh, hd + 0.3 * hh), ARM)
    m.cbox("crest", (0, top + 0.6 * hh, hc[2] + 0.15 * hh), (0.16 * hh, 0.5 * hh, hd + 0.5 * hh), CREST)
    m.cbox("crest", (0, top + 0.25 * hh, hc[2] + hd / 2 + 0.3 * hh), (0.16 * hh, 0.7 * hh, 0.2 * hh), CREST)
    m.bone("plume", "helmet", (0, top + 0.2 * hh, hc[2]))
    m.cbox("plume", (0, top + 0.3 * hh, hc[2]), (0.2 * hh, 0.25 * hh, 0.3 * hh), BLACK)
    m.cbox("plume", (0, top + 1.1 * hh, hc[2]), (0.24 * hh, 1.5 * hh, 0.34 * hh), PLUME)
    m.cbox("plume", (0, top + 1.2 * hh, hc[2] + 0.5 * hh), (0.2 * hh, 0.3 * hh, 0.8 * hh), PLUME, rot=(-30, 0, 0))
    m.cbox("plume", (0, top + 0.3 * hh, hc[2] + hd / 2 + 0.4 * hh), (0.22 * hh, 2.2 * hh, 0.26 * hh), PLUME, rot=(12, 0, 0))
    return m, b
