"""Laestrygonians as in Nolan's The Odyssey (2026).

Film still: smooth, rounded, polished silver plate; a domed helmet with a beak-like ridge down the face and a dark
Y-shaped face opening with a bright rim; one great dome pauldron per shoulder; a corpulent muscle cuirass with a
band across the belly; big flared forearm guards; bare hands; a skirt of large hanging plates.

Film references: giants about four metres high, "massive corpulence, broad and slightly arched shoulders";
"heavy flat armor with silver or iron elements, constituting helmets, breastplates, and articulated limb
protections" covering them head-to-toe, almost medieval in look; "clad in silver armor ... conceived as though
they were made entirely of metal"; "helmet shapes grew out of research into smaller creatures of the sea and
forest, then were enlarged to a hulking scale" (costume designer Ellen Mirojnick); weapons: straight iron swords
"the size of a ship's prow", a glaive that launches men into trees, one-handed all-metal maces that crush men
and ships, and a large curved blade. The child is adult-sized and wears "quilted Himalayan dress ... sharing the
armor-plated vocabulary of his larger adult counterparts".
"""
import math

from .core import Model
from .human import build_human, hood
from .materials import metal, mail, leather, quilted, human_face, skin, blade, helm_opening
from .parts import digit, chain_y

GROUND_IGNORE = ("sword", "glaive", "mace", "scimitar")
SILVER = (178, 182, 190)
SILVER_EDGE = (238, 240, 244)


def build():
    m = Model("laestrygonian", 89, D=2)
    PL = metal(SILVER, edge=SILVER_EDGE, rivets=False, polish=0.3, scratches=False, brushed=False)    # smooth plate
    PLB = metal(SILVER, edge=SILVER_EDGE, bands=3, polish=0.2, brushed=False)
    PLD = metal((140, 144, 152), edge=(214, 216, 222), rivets=False, polish=0.2, brushed=False)
    BAND = metal((116, 120, 128), edge=(196, 200, 206), rivets=False, polish=0.1, brushed=False)
    MAIL = mail((82, 84, 90))
    STRAP = leather((62, 50, 40))
    HAND = skin((178, 140, 118), mottle=0.8)                                # the hands are bare
    IRON = metal((150, 152, 158), edge=(226, 228, 232), rivets=False, polish=0.5)
    BLADE = blade((156, 158, 164))
    GRIP = leather((70, 50, 34))

    m.bone("root", None, (0, 0, 0))
    # ------------------------------------------------------------ hips: belt and a skirt of great hanging plates
    m.bone("hips", "root", (0, 34, 0))
    m.cbox("hips", (0, 33.5, 0), (24, 5, 18), MAIL)
    m.cbox("hips", (0, 36.2, -0.5), (27, 2.5, 20.5), STRAP)
    m.cbox("hips", (0, 29.5, -10.6), (8, 11, 1.5), PL)                                   # front plate
    m.mcbox("hips", (-8.7, 30.0, -10.0), (8, 10, 1.5), PL, rot=(0, 8, 4))                # front tassets, flaring
    m.mcbox("hips", (-13.7, 30.0, -1.0), (1.5, 10, 10), PLD, rot=(0, 0, 6))              # side tassets
    m.cbox("hips", (0, 30.0, 10.4), (22, 10, 1.5), PLD)                                  # back plates
    # ------------------------------------------------------------ torso: a rounded, corpulent muscle cuirass
    m.bone("torso", "hips", (0, 36, 0), (8, 0, 0))
    TC = (0, 46, -0.5)
    m.cbox("torso", TC, (28, 14, 16), PL)
    m.cbox("torso", TC, (24, 19, 16), PL)
    m.cbox("torso", TC, (24, 14, 20), PL)
    m.mcbox("torso", (-5.75, 49.5, -10.9), (11, 6.5, 1.5), PL, rot=(0, 8, 0))            # pectoral plates
    m.cbox("torso", (0, 41.5, -11.0), (20, 8, 2), PL)                                    # round belly
    m.cbox("torso", (0, 45.6, -11.7), (22, 1.5, 1), BAND)                                # band across the belly
    m.cbox("torso", (0, 37.9, -11.4), (16, 1.5, 1), BAND)
    m.cbox("torso", (0, 53.6, -9.9), (14, 3, 1.5), PLD)                                  # collar edge
    m.cbox("torso", (0, 46, 10.6), (22, 15, 1.5), PL)                                    # back plate
    m.cbox("torso", (0, 56.0, 0), (20, 3, 14), PLD)
    m.cbox("torso", (0, 58.2, -1.5), (13, 2.5, 12), PL)                                  # gorget
    # ------------------------------------------------------------ head: smooth domed helm, beak ridge, Y opening
    m.bone("head", "torso", (0, 59, -2), (-8, 0, 0))
    HC = (0, 65, -3.0)
    m.cbox("head", HC, (12, 9, 10), PL)
    m.cbox("head", HC, (10, 12, 10), PL)
    m.cbox("head", (0, 64.5, -3.0), (10, 9, 13), PL, decal={"north": helm_opening()})
    m.cbox("head", (0, 71.3, -3.0), (1.5, 1.5, 11), PLD)                                 # ridge over the dome
    m.cbox("head", (0, 66.6, -10.0), (2.0, 4.5, 1.0), PL, rot=(-8, 0, 0))                # beak-like nasal
    m.cbox("head", (0, 58.6, -2.5), (13, 2, 12), PLD)                                    # rim on the gorget

    # ------------------------------------------------------------ arms: domed pauldrons, flared vambraces, bare hands
    m.side("arm", "torso", (-14, 53, 0), (-6, 0, 8))
    for size in ((11, 8, 12), (9, 10, 10), (9, 8, 14)):                                  # one great dome a shoulder
        m.scbox("arm", (-16.5, 55.0, 0), size, PL, rot=(0, 0, 16), pivot=(-14, 55, 0))
    m.scbox("arm", (-18.0, 49.8, 0), (9, 3, 12), PLD, rot=(0, 0, 22), pivot=(-14, 55, 0))
    m.scbox("arm", (-15.5, 45.5, 0), (7, 10, 7.5), PL)
    m.scbox("arm", (-13.5, 50, 0), (4, 4, 6), MAIL)
    m.side("forearm", "arm", (-15.5, 40.5, 0), (-14, 0, 0))
    m.scbox("forearm", (-15.5, 40.5, 1.0), (7.5, 4, 7), PLD)
    m.scbox("forearm", (-15.5, 34.5, 0), (7.5, 9, 7.5), PL)
    m.scbox("forearm", (-15.5, 29.8, 0), (9, 3, 9), PL)                                  # flared cuff
    m.side("hand", "forearm", (-15.5, 28.5, 0), (6, 0, 0))
    for side, s in (("r", 1), ("l", -1)):
        bone = f"hand_{side}"
        X = -15.5 * s
        m.cbox(bone, (X, 27.8, 0), (4, 2.5, 5), HAND)
        m.cbox(bone, (X, 24.5, 0), (4, 5, 6), HAND)
        for i in range(4):
            z = -2.2 + i * 1.45
            digit(m, bone, (X + 0.3 * s, 22.2, z), (1.75, 1.5, 1.25), (2.0, 1.25), (20, 30, 30), (HAND,), plane="x", s=s)
        digit(m, bone, (X + 1.6 * s, 25.5, -3.2), (2.0, 1.5), (1.5, 1.5), (40, 30), (HAND,), plane="z", s=1)

    # ------------------------------------------------------------ weapons (right hand, shown per variant)
    grip = (-15.5, 23.0, 0.0)
    m.bone("sword", "hand_r", grip, (-65, 0, 0))
    m.cbox("sword", (-15.5, 23.0, 0), (2.5, 7, 2.5), GRIP)
    m.cbox("sword", (-15.5, 27.2, 0), (3.5, 1.5, 3.5), IRON)
    m.cbox("sword", (-15.5, 18.5, 0), (3, 2, 13), IRON)
    m.cbox("sword", (-15.5, -3.5, 0), (1.5, 42, 5.5), BLADE)
    m.cbox("sword", (-15.5, -26, 0), (1.5, 3, 3.5), BLADE)
    m.bone("glaive", "hand_r", grip, (-8, 0, 0))
    m.cbox("glaive", (-15.5, 40, 0), (2.5, 76, 2.5), GRIP)
    m.cbox("glaive", (-15.5, 78.5, 0), (3.5, 3, 3.5), IRON)
    chain_y(m, "glaive", (-15.5, 80.0, -1.0), (3, 3, 3, 3, 3, 3, 3),
            [(1.5, 6.5), (1.5, 6.25), (1.5, 5.75), (1.5, 5), (1.5, 4.25), (1.5, 3.5), (1.5, 2.5)],
            (-6, -7, -8, -9, -9, -10, -11), [BLADE], up=True, overlap=1.0)
    m.cbox("glaive", (-15.5, 81.5, 2.6), (1.5, 2, 3.5), IRON, rot=(35, 0, 0))
    m.bone("mace", "hand_r", grip, (-26, 0, 0))
    m.cbox("mace", (-15.5, 16, 0), (2.5, 20, 2.5), IRON)
    m.cbox("mace", (-15.5, 25.5, 0), (3.5, 2, 3.5), IRON)
    m.cbox("mace", (-15.5, 3.5, 0), (6, 8, 6), IRON)
    for k in range(6):
        a = math.radians(k * 60)
        cx, cz = -15.5 + math.cos(a) * 3.6, math.sin(a) * 3.6
        m.cbox("mace", (cx, 3.5, cz), (3.5, 9, 1.5), IRON, rot=(0, -k * 60, 0) if k else None, pivot=(cx, 3.5, cz))
    m.cbox("mace", (-15.5, -1.2, 0), (2.5, 1.5, 2.5), IRON)
    m.bone("scimitar", "hand_r", grip, (-78, 0, 0))
    m.cbox("scimitar", (-15.5, 23.0, 0), (2.5, 7, 2.5), GRIP)
    m.cbox("scimitar", (-15.5, 18.6, 0), (3, 2, 9), IRON)
    chain_y(m, "scimitar", (-15.5, 17.6, 0.0), (5, 5, 5, 5, 5, 5, 5, 5, 4.5, 4),
            [(1.5, 6.5), (1.5, 6.5), (1.5, 6.25), (1.5, 6), (1.5, 5.75), (1.5, 5.25), (1.5, 4.75), (1.5, 4),
             (1.5, 3.25), (1.5, 2.25)],
            (0, 4, 4, 5, 5, 5, 6, 6, 7, 8), [BLADE], up=False, overlap=1.0)

    # ------------------------------------------------------------ legs: cuisses, poleyns, greaves, sabatons
    m.side("thigh", "hips", (-7, 34, 0), (0, 0, 2))
    m.scbox("thigh", (-7.5, 27, 0), (9.5, 13, 10), PL)
    m.scbox("thigh", (-8, 31, -5.6), (10, 6, 1.5), PLB, rot=(8, 0, 0))
    m.scbox("thigh", (-7.5, 20.5, -1), (8, 5, 9), PLD)
    m.scbox("thigh", (-11.9, 20.5, 0), (1, 6, 6), PL)
    m.scbox("thigh", (-7.5, 20.5, 3.6), (7, 4, 2), MAIL)
    m.side("shin", "thigh", (-7.5, 20, 0))
    m.scbox("shin", (-7.5, 11.5, 0.5), (8.5, 16, 9), PL)
    m.scbox("shin", (-7.5, 11.5, -4.3), (1.5, 15, 1), PLD)
    m.side("foot", "shin", (-7.5, 3.5, 0))
    m.scbox("foot", (-7.5, 2, -2.5), (8.5, 4, 13), PLB)
    for k in range(3):
        m.scbox("foot", (-7.5, 1.5 - k * 0.25, -10.5 - k * 2.2), (7.5 - k * 1.5, 3 - k * 0.5, 2.5), PL if k % 2 else PLD)
    m.scbox("foot", (-7.5, 2, 4.6), (5, 3, 2), PLD)
    return m


def build_child():
    """The armoured Laestrygonian child: adult-human sized, quilted padded dress with plate pieces."""
    m = Model("laestrygonian_child", 91, D=4)
    Q = quilted((96, 74, 56), stitch=(54, 40, 30))
    Q2 = quilted((112, 88, 64), stitch=(60, 46, 34))
    PL = metal(SILVER, edge=SILVER_EDGE, polish=0.3)
    PLB = metal(SILVER, edge=SILVER_EDGE, bands=3, polish=0.2)
    BOOT = leather((66, 50, 38))
    face = human_face(iris=(70, 60, 50), brow=(80, 66, 56), lips=(170, 100, 96), eye_y=0.5, mouth_y=0.8, mouth_open=0.09)
    b = build_human(m, 28.8, sex="m", heads=5.5, skin_color=(220, 190, 166), skin_kw={"freckles": 0.02},
                    face=face, legs=True, feet="boots", build=1.15, bust=False, neck_len=0.8)
    hh = b.hh
    # quilted coat (chuba-like), long, wrapped, belted
    m.cbox("chest", (0, b.y_chest_lo + (b.y_sh - b.y_chest_lo) / 2 + 0.05 * hh, 0),
           (b.chest_w + 0.25 * hh, b.y_sh - b.y_chest_lo + 0.3 * hh, b.chest_d + 0.25 * hh), Q)
    m.cbox("waist", (0, (b.y_waist + b.y_chest_lo) / 2, 0), (b.waist_w + 0.35 * hh, b.y_chest_lo - b.y_waist + 0.1 * hh,
                                                            b.chest_d + 0.3 * hh), Q)
    m.cbox("waist", (0, b.y_waist + 0.05 * hh, 0), (b.waist_w + 0.45 * hh, 0.22 * hh, b.chest_d + 0.4 * hh), leather((150, 112, 54)))
    m.cbox("hips", (0, b.y_hip - 0.1 * hh, 0), (b.hip_w + 0.45 * hh, (b.y_waist - b.y_hip) + 0.55 * hh, b.chest_d + 0.45 * hh), Q2)
    m.scbox("thigh", (-b.x_hip, b.y_hip - 0.75 * hh, 0), (0.75 * hh, 1.5 * hh, 0.85 * hh), Q2)
    m.scbox("shin", (-b.x_hip, b.y_knee - 0.35 * hh, 0.0), (0.55 * hh, 0.6 * hh, 0.6 * hh), Q)
    m.scbox("foot", (-b.x_hip, b.y_ankle * 0.55, -0.12 * hh), (0.5 * hh, b.y_ankle * 1.1, 0.95 * hh), BOOT)
    m.scbox("foot", (-b.x_hip, b.y_ankle + 0.3 * hh, 0.0), (0.48 * hh, 0.6 * hh, 0.5 * hh), BOOT)
    # wide quilted sleeves
    m.scbox("arm", (-b.x_sh - 0.02 * hh, b.y_sh - 0.62 * hh, 0), (0.62 * hh, 1.25 * hh, 0.64 * hh), Q)
    m.scbox("forearm", (-b.x_sh, b.y_elbow - 0.5 * hh, 0), (0.6 * hh, 1.0 * hh, 0.62 * hh), Q2)
    # plate pieces in the adults' vocabulary
    for k in range(3):
        m.scbox("arm", (-b.x_sh - 0.12 * hh, b.y_sh + 0.08 * hh - k * 0.22 * hh, 0), (0.75 * hh - k * 0.06 * hh, 0.22 * hh,
                                                                                    0.8 * hh), PLB if k % 2 else PL,
                rot=(0, 0, 22 - k * 8), pivot=(-b.x_sh, b.y_sh, 0))
    for k in range(3):
        m.cbox("chest", (0, b.y_sh - 0.3 * hh - k * 0.24 * hh, -b.chest_d / 2 - 0.16 * hh - k * 0.02 * hh),
               (0.95 * hh - k * 0.1 * hh, 0.26 * hh, 0.14 * hh), PLB if k % 2 else PL)
    # quilted hood with a segmented crest like the giants' helms
    hc = b.head_c
    hood(m, b, Q, extra=0.14, length=0.95)
    for k in range(4):
        m.cbox("head", (0, hc[1] + b.head_h * 0.55 - abs(k - 1.5) * 0.06 * hh, hc[2] - 0.35 * hh + k * 0.25 * hh),
               (0.35 * hh, 0.16 * hh, 0.26 * hh), PLB if k % 2 else PL)
    return m
