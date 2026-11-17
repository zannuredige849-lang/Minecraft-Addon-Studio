"""Polyphemus as in Nolan's The Odyssey (2026).

Film references: a 60 ft (18 m) practical puppet; "slim and horrific monster without clothing, a pale gray
elephantine skin and massive hands with broken nails. His face has an asymmetrical nose and his eye is in
a vertical slit" (Villains Wiki); "His single eye hangs crooked above a horribly twisted nose and mouth, both
set askew across his face. He is not the muscular brute of popular imagination but a misshapen, gangly
creature" (MPA review); design after Goya's 'Saturn Devouring His Son'; bald. Film stills show a gaunt, wrinkled,
old-looking body (not a skeleton) and one wide-open round eye with an amber iris, set off to one side of the face.

The model is built at base size and scaled up on the client; in game he stands 11 blocks tall.
"""
from .core import Model
from .materials import elephant, nails, teeth, cavity, round_eye, blood_below, socket_shade, edge_shade, tint
from .parts import digit, forward_digit

TARGET_HEIGHT_BLOCKS = 11.0


def build():
    m = Model("cyclops", 11, D=4)
    SK = elephant((164, 156, 144), crease=(86, 80, 72))
    SKD = elephant((142, 135, 124), crease=(76, 70, 64))
    NAIL = nails((160, 150, 118), (64, 54, 44), broken=True)
    TOOTH = teeth((190, 172, 128), "down", gap=0.5)
    LTOOTH = teeth((180, 162, 120), "up", gap=0.5)
    MOUTH = cavity((40, 14, 14))

    m.bone("root", None, (0, 0, 0))
    # ------------------------------------------------------------ pelvis
    m.bone("hips", "root", (0, 22, 0))
    m.cbox("hips", (0, 22.4, 0.2), (7, 3.5, 4.5), SK)
    m.mcbox("hips", (-3.1, 23.6, -0.4), (1.5, 1.25, 3), SKD)
    m.cbox("hips", (0, 21.4, 1.9), (6, 2.5, 1.5), SK)
    # ------------------------------------------------------------ belly and ribcage (Goya hunch)
    m.bone("belly", "hips", (0, 24, 0), (8, 0, 0))
    m.cbox("belly", (0, 26, 0.3), (5.5, 4.5, 3.5), SK)
    m.cbox("belly", (0, 25.2, -1.55), (4.5, 2.5, 0.5), SK)
    for k in range(3):
        m.cbox("belly", (0, 24.6 + k * 1.4, 2.15), (1, 0.75, 0.75), SKD)
    m.bone("chest", "belly", (0, 28, 0), (14, 0, 0))
    m.cbox("chest", (0, 31.6, 0.2), (7, 7.5, 4.5), SK)
    for k in range(3):                                                     # faint ribs under slack old skin
        y = 29.2 + k * 1.3
        m.mcbox("chest", (-2.0, y, -2.1), (2.5, 0.5, 0.5), SK, rot=(0, 0, -12 + k * 3))
    m.cbox("chest", (0, 31.2, -2.45), (0.75, 5, 0.5), SKD)
    for k in range(5):
        m.cbox("chest", (0, 28.6 + k * 1.5, 2.6), (1, 0.75, 0.75), SKD)
    m.mcbox("chest", (-2.1, 33.6, 2.55), (2.5, 3, 0.5), SK, rot=(0, 0, 12))
    m.mcbox("chest", (-2.1, 35.0, -1.9), (3.5, 0.5, 0.75), SK, rot=(0, 0, -8))
    m.cbox("chest", (0, 35.4, 0.1), (8.5, 1.5, 3.75), SK)
    m.mcbox("chest", (-2.2, 36.1, 0.6), (3, 1, 2.5), SK, rot=(0, 0, -14))
    # ------------------------------------------------------------ neck
    m.bone("neck", "chest", (0, 36.4, -0.4), (-6, 0, 0))
    m.cbox("neck", (0, 38, -0.5), (2.5, 3.5, 2.5), SK)
    m.mcbox("neck", (-0.85, 37.8, -1.65), (0.5, 3.25, 0.5), SKD, rot=(14, 0, 8))
    m.cbox("neck", (0, 37.6, -1.85), (0.75, 0.75, 0.5), SK)
    # ------------------------------------------------------------ head: bald, misshapen, everything askew
    # The cranium is three crossed boxes, so every edge is chamfered and the silhouette reads round, not cubic.
    m.bone("head", "neck", (0, 39.6, -0.6), (-14, 0, 0))
    HC = (0, 43.6, -0.2)
    eye_c = (0.65, 43.3, -3.75)
    m.cbox("head", HC, (6.5, 5.0, 5.0), SK, decal={"north": tint(0.8)})                          # x-extended: hollow cheeks
    m.cbox("head", (0, 43.6, -0.2), (4.5, 7.0, 5.0), SK)                                         # y-extended
    m.cbox("head", HC, (4.5, 5.0, 7.0), SK, decal={"north": socket_shade(eye_c, HC, (4.5, 5.0), 14,
                                                                        blood_below("blind", 0.55, 0.75, 0.78),
                                                                        radii=(1.7, 1.8), depth=0.38)})
    m.cbox("head", (0.3, 47.35, 0.1), (3.5, 0.5, 4.0), SK)                                       # crown
    m.cbox("head", (-2.55, 45.4, 1.1), (2.0, 2.25, 3.0), SK)                                     # lumpy skull
    m.cbox("head", (0.4, 44.7, 3.55), (3.5, 3.5, 0.75), SK)                                      # occiput
    m.cbox("head", (0.2, 40.2, -3.2), (4.5, 1.75, 1.0), SK,                                      # upper jaw
           decal={"north": blood_below("blind", 0.5, 0.7, 0.0)})
    # one wide-open round eye, amber iris, set crooked to one side under a wrinkled brow
    m.cbox("head", eye_c, (2.0, 2.0, 0.25), SK, rot=(0, 0, 8), pivot=eye_c, decal={"north": round_eye()})
    m.cbox("head", (0.65, 44.5, -3.95), (2.5, 0.5, 0.5), SK, rot=(0, 0, 8), pivot=eye_c,        # upper lid
           decal={"north": edge_shade("bottom", 0.5, 0.9)})
    m.cbox("head", (0.65, 42.1, -3.9), (2.25, 0.5, 0.4), SK, rot=(0, 0, 8), pivot=eye_c,        # lower lid
           decal={"north": edge_shade("top", 0.45, 0.9)})
    for lx, edge in ((-0.5, "right"), (1.8, "left")):                                            # corners
        m.cbox("head", (lx, 43.3, -3.85), (0.25, 1.75, 0.25), SK, rot=(0, 0, 8), pivot=eye_c,
               decal={"north": edge_shade(edge, 0.45, 1.0)})
    m.cbox("head", (0.4, 45.35, -4.0), (4.25, 0.75, 0.75), SK, rot=(0, 0, 6))                    # brow ridge
    m.cbox("head", (-0.5, 40.9, -4.15), (1, 2.25, 1), SK, rot=(0, 12, -16))                      # twisted nose
    m.cbox("head", (-0.95, 39.95, -4.25), (1.5, 1, 1.25), SK, rot=(0, 8, -22))
    m.cbox("head", (-2.4, 41.5, -3.25), (1.25, 1.0, 1.0), SK)                                    # cheekbones
    m.cbox("head", (2.5, 41.2, -3.2), (1.25, 1.0, 1.0), SK)
    mouth_p = (0.35, 39.0, -3.55)
    m.cbox("head", (0.35, 39.55, -3.85), (3.5, 0.5, 0.75), SKD, rot=(0, 0, 9), pivot=mouth_p)     # upper lip
    m.cbox("head", mouth_p, (3.25, 0.75, 0.5), MOUTH, rot=(0, 0, 9), pivot=mouth_p)
    for i, h in enumerate((0.5, 0.75, 0.5, 0.75, 0.5, 0.75)):
        m.cbox("head", (-1.05 + i * 0.55 + 0.35, 39.05 + 0.25 - h / 2, -3.8), (0.5, h, 0.25), TOOTH, rot=(0, 0, 9), pivot=mouth_p)
    for sx, y0, k in ((-1, 42.5, 1.0), (1, 42.9, 0.8)):                                           # ears, uneven
        m.cbox("head", (sx * 3.45, y0 + 0.4 * k, 0.6), (0.5, 1.75 * k, 1.5 * k), SK, rot=(0, -sx * 18, 0),
               decal={"east" if sx > 0 else "west": tint(0.8)})
        m.cbox("head", (sx * 3.4, y0 - 0.9 * k, 0.4), (0.5, 0.75 * k, 0.75 * k), SK, rot=(0, -sx * 12, 0))
    m.bone("jaw", "head", (0, 40, -0.4), (10, 0, 5))
    m.cbox("jaw", (0.25, 38.9, -1.0), (5, 1.5, 4.75), SK)
    m.cbox("jaw", (0.65, 38.7, -3.6), (2.5, 1.25, 0.75), SK, rot=(0, 0, 10))
    m.cbox("jaw", (0.4, 39.45, -3.75), (3.25, 0.5, 0.5), SKD, rot=(0, 0, 9))
    for i, h in enumerate((0.5, 0.75, 0.5, 0.5, 0.75)):
        m.cbox("jaw", (-0.8 + i * 0.55 + 0.4, 39.75 + h / 2 - 0.1, -3.65), (0.5, h, 0.25), LTOOTH, rot=(0, 0, 9), pivot=(0.4, 39.45, -3.75))

    # ------------------------------------------------------------ gangly arms, massive hands, broken nails
    m.side("arm", "chest", (-4.3, 35.2, 0.2), (-24, 0, 7))
    m.scbox("arm", (-4.5, 35, 0.2), (2, 2.25, 2.25), SK)
    m.scbox("arm", (-4.3, 29.6, 0.2), (1.75, 10.5, 1.75), SK)
    m.scbox("arm", (-4.3, 31, -0.65), (1.25, 4, 0.75), SK)
    m.scbox("arm", (-4.3, 24.4, 0.95), (1.5, 1.5, 1), SKD)
    m.side("forearm", "arm", (-4.3, 24.3, 0.2), (-28, 0, -4))
    m.scbox("forearm", (-4.3, 18.8, 0.2), (1.5, 11, 1.5), SK)
    m.scbox("forearm", (-4.3, 19, 0.95), (0.5, 9.5, 0.5), SKD)
    m.scbox("forearm", (-4.3, 13.5, 0.2), (1.75, 0.75, 1.75), SKD)
    m.side("hand", "forearm", (-4.3, 13.2, 0.2), (8, 0, 0))
    for side, s in (("r", 1), ("l", -1)):
        bone = f"hand_{side}"
        X = -4.4 * s
        m.cbox(bone, (X, 10.6, 0.0), (1.5, 5, 4), SK)
        for i in range(4):
            z = -1.5 + i * 1.0
            m.cbox(bone, (X, 8.3, z), (1.5, 0.75, 1), SKD)
            L = (3.4, 3.8, 3.6, 2.8)[i]
            digit(m, bone, (X - 0.1 * s, 8.0, z), (L * 0.42, L * 0.33, L * 0.25), (1.0, 0.75),
                  (8, 10, 12), (SK, SK, SKD), plane="x", s=s, nail=NAIL, nail_size=(0.75, 0.75, 0.75))
        digit(m, bone, (X + 0.45 * s, 11.6, -2.0), (1.75, 1.5), (0.75, 1.0), (40, 18), (SK, SKD), plane="z", s=1,
              nail=NAIL, nail_size=(0.75, 0.75, 0.75))

    # ------------------------------------------------------------ long knobbly legs in a crouch
    m.side("thigh", "hips", (-2.2, 21.6, 0.2), (-26, 0, 3))
    m.scbox("thigh", (-2.2, 16, 0.2), (2.25, 11.5, 2.25), SK)
    m.scbox("thigh", (-2.2, 17, -0.85), (1.75, 5, 0.5), SK)
    m.scbox("thigh", (-2.2, 10.3, 0.2), (2.25, 1.75, 2.25), SKD)
    m.scbox("thigh", (-2.2, 10.5, -1.0), (1.5, 1.5, 0.5), SK)
    m.side("shin", "thigh", (-2.2, 10.2, 0.2), (42, 0, -3))
    m.scbox("shin", (-2.2, 5.2, 0.35), (1.75, 10, 1.75), SK)
    m.scbox("shin", (-2.2, 6.6, 1.25), (1.25, 4, 0.75), SK)
    m.scbox("shin", (-2.2, 5.4, -0.55), (0.5, 9, 0.5), SKD)
    m.scbox("shin", (-3.05, 0.9, 0.35), (0.5, 0.75, 0.75), SKD)
    m.scbox("shin", (-1.35, 0.9, 0.35), (0.5, 0.75, 0.75), SKD)
    m.side("foot", "shin", (-2.2, 0.6, 0.35), (-16, 0, 0))
    for side, s in (("r", 1), ("l", -1)):
        bone = f"foot_{side}"
        X = -2.2 * s
        m.cbox(bone, (X, 0.45, -1.4), (2.25, 0.9, 4.25), SK)
        m.cbox(bone, (X, 0.55, 0.95), (1.5, 1.1, 1.25), SKD)
        m.cbox(bone, (X, 1.05, -0.6), (1.75, 0.5, 2), SK)
        for i, (dx, L, w) in enumerate(((0.75, 1.25, 0.75), (0.25, 1.0, 0.5), (-0.2, 0.9, 0.5), (-0.6, 0.8, 0.5), (-0.95, 0.7, 0.5))):
            forward_digit(m, bone, (X + dx * s, 0.35, -3.5), (L * 0.6, L * 0.4), (w, 0.6), (6, 14), (SK, SKD), nail=NAIL)
    return m


def scale_for(height_units):
    return round(TARGET_HEIGHT_BLOCKS * 16 / height_units, 4)
