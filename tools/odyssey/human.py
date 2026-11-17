"""Shared anatomical human body (head-height proportions) used by every human-shaped character."""
from .materials import skin as skin_mat


class Body:
    """Key measurements of a built body, for costume placement."""
    pass


def hood(m, b, mat, extra=0.18, length=1.0, back_drop=0.0):
    """Hood framing the face: crown, back and two side panels, open at the front."""
    hh, hc = b.hh, b.head_c
    t = extra * hh
    W, Hh, Dd = b.head_w + 2 * t, b.head_h + t, b.head_d + t
    top = hc[1] + b.head_h / 2 + t
    m.cbox("head", (0, top - t / 2, hc[2] + t / 2), (W, t, Dd), mat)
    back_h = Hh * length + back_drop
    m.cbox("head", (0, top - back_h / 2, hc[2] + b.head_d / 2 + t / 2), (W, back_h, t), mat)
    for sx in (-1, 1):
        m.cbox("head", (sx * (b.head_w / 2 + t / 2), top - Hh * length / 2, hc[2] + t * 0.5),
               (t, Hh * length, b.head_d + t * 0.2), mat)


def build_human(m, H, sex="f", heads=7.5, skin_color=(214, 188, 168), skin_kw=None, lips=None, face=None,
                nail=(200, 176, 160), legs=True, arms=True, feet="bare", stoop=0.0, build=1.0, bust=True,
                neck_len=1.0, skin_override=None):
    """Build the body on model m. Feet rest on y=0, the figure faces -z."""
    hh = H / heads
    b = Body()
    b.hh, b.H = hh, H
    f = sex == "f"
    kw = dict(skin_kw or {})
    skin = skin_override or skin_mat(skin_color, **kw)
    nailskin = skin_mat(skin_color, nail=nail, nail_len=0.3, **kw) if nail else skin
    lips = lips or skin

    # ---------------------------------------------------- vertical landmarks
    b.y_chin = H - hh
    b.y_sh = H - 1.33 * hh
    b.y_chest_lo = H - 2.55 * hh
    b.y_waist = H - 3.1 * hh
    b.y_hip = H - 3.75 * hh
    if heads < 7:      # child proportions: big head, short limbs
        b.y_sh = H - 1.25 * hh
        b.y_chest_lo = H - 2.05 * hh
        b.y_waist = H - 2.5 * hh
        b.y_hip = H - 2.95 * hh
    b.y_knee = b.y_hip * 0.52
    b.y_ankle = (0.28 if heads >= 7 else 0.32) * hh

    # ---------------------------------------------------- widths
    sh_half = (0.85 if f else 1.0) * hh * build
    b.x_sh = sh_half - 0.17 * hh
    b.x_hip = (0.34 if f else 0.31) * hh * build
    b.chest_w = (1.36 if f else 1.56) * hh * build
    b.waist_w = (1.04 if f else 1.2) * hh * build
    b.hip_w = (1.48 if f else 1.34) * hh * build
    b.chest_d = (0.58 if f else 0.64) * hh * build
    b.head_w, b.head_h, b.head_d = (0.68 if f else 0.72) * hh, 0.95 * hh, 0.82 * hh

    # ---------------------------------------------------- bones
    m.bone("root", None, (0, 0, 0))
    m.bone("hips", "root", (0, b.y_hip, 0))
    m.bone("waist", "hips", (0, b.y_waist, 0))
    m.bone("chest", "waist", (0, b.y_chest_lo, 0), (stoop, 0, 0))
    m.bone("neck", "chest", (0, b.y_chin - 0.3 * hh * neck_len, -0.03 * hh))
    m.bone("head", "neck", (0, b.y_chin, -0.03 * hh), (-stoop * 0.85, 0, 0))

    # torso
    m.cbox("hips", (0, (b.y_hip + b.y_waist) / 2 - 0.15 * hh, 0.02 * hh),
           (b.hip_w, b.y_waist - b.y_hip + 0.5 * hh, b.chest_d * 0.98), skin)
    m.cbox("waist", (0, (b.y_waist + b.y_chest_lo) / 2, 0),
           (b.waist_w, b.y_chest_lo - b.y_waist + 0.1 * hh, b.chest_d * 0.92), skin)
    ch = b.y_sh - b.y_chest_lo + 0.12 * hh
    m.cbox("chest", (0, b.y_chest_lo + ch / 2, 0), (b.chest_w, ch, b.chest_d), skin)
    m.cbox("chest", (0, b.y_sh + 0.02 * hh, 0.02 * hh), (b.chest_w * 0.82, 0.16 * hh, b.chest_d * 0.85), skin)
    if f and bust:
        m.mcbox("chest", (-0.27 * hh * build, b.y_sh - 0.72 * hh, -b.chest_d / 2 - 0.07 * hh), (0.4 * hh, 0.36 * hh, 0.2 * hh), skin)
    m.mcbox("chest", (-0.33 * hh, b.y_sh - 0.05 * hh, -b.chest_d / 2 + 0.02 * hh), (0.5 * hh, 0.09 * hh, 0.09 * hh), skin)
    m.cbox("neck", (0, b.y_chin - 0.08 * hh, -0.03 * hh), (0.36 * hh, 0.5 * hh * neck_len, 0.38 * hh), skin)

    # ---------------------------------------------------- head and face sculpt
    hc = (0, b.y_chin + b.head_h / 2 + 0.02 * hh, -0.03 * hh)
    b.head_c = hc
    fz = hc[2] - b.head_d / 2
    b.face_z = fz
    m.cbox("head", hc, (b.head_w, b.head_h, b.head_d), skin, decal={"north": face} if face else None)
    m.cbox("head", (0, hc[1] + b.head_h / 2 + 0.03 * hh, hc[2] + 0.02 * hh), (b.head_w * 0.86, 0.08 * hh, b.head_d * 0.86), skin)
    m.cbox("head", (0, hc[1] + 0.12 * hh, fz - 0.035 * hh), (b.head_w * 0.76, 0.07 * hh, 0.08 * hh), skin)       # brow
    m.cbox("head", (0, hc[1] - 0.02 * hh, fz - 0.05 * hh), (0.1 * hh, 0.26 * hh, 0.1 * hh), skin)               # nose bridge
    m.cbox("head", (0, hc[1] - 0.15 * hh, fz - 0.08 * hh), (0.17 * hh, 0.09 * hh, 0.11 * hh), skin)             # nose tip
    m.mcbox("head", (-0.2 * hh, hc[1] - 0.05 * hh, fz - 0.02 * hh), (0.15 * hh, 0.09 * hh, 0.06 * hh), skin)   # cheekbones
    m.cbox("head", (0, hc[1] - 0.27 * hh, fz - 0.03 * hh), (0.24 * hh, 0.05 * hh, 0.06 * hh), lips)            # upper lip
    m.cbox("head", (0, hc[1] - 0.32 * hh, fz - 0.035 * hh), (0.22 * hh, 0.06 * hh, 0.07 * hh), lips)           # lower lip
    m.cbox("head", (0, hc[1] - 0.42 * hh, fz - 0.03 * hh), (0.24 * hh, 0.09 * hh, 0.06 * hh), skin)            # chin
    m.mcbox("head", (-(b.head_w / 2 + 0.03 * hh), hc[1], hc[2] + 0.06 * hh), (0.07 * hh, 0.26 * hh, 0.16 * hh), skin)  # ears

    # ---------------------------------------------------- arms and hands
    ua, fa = 1.45 * hh, 1.25 * hh
    b.y_elbow, b.y_wrist = b.y_sh - ua, b.y_sh - ua - fa
    if arms:
        m.side("arm", "chest", (-b.x_sh, b.y_sh - 0.06 * hh, 0), (0, 0, 4))
        m.scbox("arm", (-b.x_sh, b.y_sh - 0.06 * hh - ua / 2 + 0.05 * hh, 0), (0.36 * hh * build, ua, 0.38 * hh * build), skin)
        m.scbox("arm", (-b.x_sh - 0.03 * hh, b.y_sh - 0.12 * hh, 0), (0.42 * hh * build, 0.36 * hh, 0.42 * hh * build), skin)
        m.side("forearm", "arm", (-b.x_sh, b.y_elbow, 0))
        m.scbox("forearm", (-b.x_sh, b.y_elbow - fa / 2 + 0.04 * hh, 0), (0.31 * hh * build, fa, 0.33 * hh * build), skin)
        m.scbox("forearm", (-b.x_sh, b.y_elbow - 0.02 * hh, 0.07 * hh), (0.26 * hh, 0.14 * hh, 0.22 * hh), skin)
        m.side("hand", "forearm", (-b.x_sh, b.y_wrist, 0))
        wx = -b.x_sh
        m.scbox("hand", (wx, b.y_wrist - 0.25 * hh, 0), (0.14 * hh, 0.5 * hh, 0.36 * hh), skin)
        for i, ln in enumerate((0.42, 0.47, 0.44, 0.36)):
            z = -0.13 * hh + i * 0.087 * hh
            L = ln * hh
            top = b.y_wrist - 0.5 * hh
            m.scbox("hand", (wx + 0.01 * hh, top - L * 0.28, z), (0.12 * hh, L * 0.56, 0.075 * hh), skin)
            m.scbox("hand", (wx + 0.02 * hh, top - L * 0.78, z), (0.11 * hh, L * 0.46, 0.07 * hh), nailskin,
                    rot=(0, 0, -8), pivot=(wx + 0.02 * hh, top - L * 0.56, z))
        m.scbox("hand", (wx + 0.05 * hh, b.y_wrist - 0.33 * hh, -0.2 * hh), (0.1 * hh, 0.3 * hh, 0.09 * hh), nailskin,
                rot=(-22, 0, -8), pivot=(wx + 0.05 * hh, b.y_wrist - 0.18 * hh, -0.17 * hh))

    # ---------------------------------------------------- legs and feet
    m.side("thigh", "hips", (-b.x_hip, b.y_hip, 0))
    m.side("shin", "thigh", (-b.x_hip, b.y_knee, 0))
    m.side("foot", "shin", (-b.x_hip, b.y_ankle, 0))
    if legs:
        th = b.y_hip - b.y_knee
        m.scbox("thigh", (-b.x_hip, b.y_hip - th / 2, 0), (0.52 * hh * build, th + 0.1 * hh, 0.55 * hh * build), skin)
        m.scbox("thigh", (-b.x_hip, b.y_knee + 0.06 * hh, -0.24 * hh * build), (0.32 * hh, 0.22 * hh, 0.12 * hh), skin)
        sh = b.y_knee - b.y_ankle
        m.scbox("shin", (-b.x_hip, b.y_knee - sh / 2, 0.02 * hh), (0.38 * hh * build, sh + 0.05 * hh, 0.4 * hh * build), skin)
        m.scbox("shin", (-b.x_hip, b.y_knee - sh * 0.33, 0.16 * hh * build), (0.3 * hh, sh * 0.4, 0.16 * hh), skin)
    fy = b.y_ankle
    if feet == "bare":
        m.scbox("foot", (-b.x_hip, fy / 2, -0.24 * hh), (0.34 * hh, fy, 0.86 * hh), skin)
        m.scbox("foot", (-b.x_hip, fy + 0.06 * hh, 0.0), (0.3 * hh, 0.14 * hh, 0.34 * hh), skin)
        for i in range(5):
            m.scbox("foot", (-b.x_hip - 0.12 * hh + i * 0.06 * hh, 0.05 * hh, -0.7 * hh), (0.06 * hh, 0.1 * hh, 0.1 * hh), nailskin)
    b.skin = skin
    return b
