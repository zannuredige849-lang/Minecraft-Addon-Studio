"""Molang animations, animation controllers and sound cues for every entity.

Rotations use Bedrock's convention (checked against in-game screenshots): a positive x rotation tilts up-vectors
forward (-z) and swings down-vectors backward (+z), so *raising* an arm forward is a NEGATIVE x rotation, leaning
forward is positive. Animations add to a bone's rest rotation. Positive y turns a bone toward the creature's right,
positive z swings a hanging right limb outward (and a left limb inward).

One-shot moves (see moves.py) are entered through an animation controller state so each one restarts from frame 0
every time the script sets `studio:anim`; `scripts.animate` blends alone would never restart them. Sound cues are
attached to the animations ("sound_effects") and to controller states (footsteps on each foot strike), so sound is
placed on the same frame as the motion for every player, with no script involved.
"""
from .moves import MOVES

Z = (0, 0, 0)


# ------------------------------------------------------------------ building blocks
def A(bones, loop=True, length=None, sfx=None):
    a = {"loop": loop, "bones": bones}
    if length:
        a["animation_length"] = length
    if sfx:
        a["sound_effects"] = {f"{t:.2f}": {"effect": e} for t, e in sfx}
    return a


def rot(x=0, y=0, z=0):
    return {"rotation": [x, y, z]}


def keys(*frames):
    """Rotation keyframes: (time, [x, y, z]) pairs."""
    return {"rotation": {f"{t:.2f}": list(v) for t, v in frames}}


def pkeys(*frames):
    """Position keyframes: (time, [x, y, z]) pairs."""
    return {"position": {f"{t:.2f}": list(v) for t, v in frames}}


def _xyz(v):
    return (v, 0, 0) if isinstance(v, (int, float, str)) else v


def T(times, **table):
    """Rotation table: every bone gets one pose per listed time (a number means x only)."""
    out = {}
    for bone, vals in table.items():
        assert len(vals) == len(times), f"{bone}: {len(vals)} poses for {len(times)} times"
        out[bone] = keys(*zip(times, [_xyz(v) for v in vals]))
    return out


def PT(times, **table):
    out = {}
    for bone, vals in table.items():
        assert len(vals) == len(times), f"{bone}: {len(vals)} positions for {len(times)} times"
        out[bone] = pkeys(*zip(times, vals))
    return out


def _sum(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + b
    return f"({a})+({b})"


def M(*parts):
    """Merge bone tables. A bone's rotation (or position) can come from several tables: they must share their key
    times, and the values add up (an arm raised by one table and spread by another does both)."""
    out = {}
    for p in parts:
        for bone, chans in p.items():
            have = out.setdefault(bone, {})
            for name, ch in chans.items():
                if name not in have:
                    have[name] = ch
                    continue
                old = have[name]
                assert isinstance(old, dict) and isinstance(ch, dict) and set(old) == set(ch), \
                    f"{bone}.{name}: tables with different key times cannot be merged"
                have[name] = {t: [_sum(a, b) for a, b in zip(old[t], ch[t])] for t in old}
    return out


def walk(k, leg=26, knee=30, arm=16, bob=0.4, roll=3, legs=("thigh", "shin"), arms="arm", chest="chest", hips="hips",
         feet=0.9):
    """Distance-driven gait (k = degrees of phase per block walked). `feet` counter-rotates the foot against thigh
    and knee so soles stay level (0 = off)."""
    d = f"q.modified_distance_moved*{k}"
    th, sh = legs
    b = {
        f"{th}_r": rot(f"math.cos({d})*{leg}"), f"{th}_l": rot(f"-math.cos({d})*{leg}"),
        f"{sh}_r": rot(f"math.max(0, math.sin({d}))*{knee}"), f"{sh}_l": rot(f"math.max(0, -math.sin({d}))*{knee}"),
        hips: {"position": [0, f"-math.abs(math.sin({d}))*{bob}", 0]},
    }
    if feet:
        b["foot_r"] = rot(f"-({feet})*(math.cos({d})*{leg}+math.max(0, math.sin({d}))*{knee})")
        b["foot_l"] = rot(f"-({feet})*(-math.cos({d})*{leg}+math.max(0, -math.sin({d}))*{knee})")
    if arms:
        b[f"{arms}_r"] = rot(f"-math.cos({d})*{arm}")
        b[f"{arms}_l"] = rot(f"math.cos({d})*{arm}")
    if chest:
        b[chest] = rot(0, f"math.cos({d})*{roll}", 0)
    return A(b)


def human_idle(head_amp=10, breathe=1.2):
    """Standing and alive: slow breathing, a shifting of weight, the head turning to look, arms swaying a little."""
    return A({"chest": rot(f"math.sin(q.life_time*60)*{breathe}*1.8", "math.sin(q.life_time*21)*2.5", "math.sin(q.life_time*33)*1.3"),
              "head": rot("math.sin(q.life_time*28)*4", f"math.sin(q.life_time*17)*{head_amp}*1.3+math.sin(q.life_time*43)*2"),
              "arm_r": rot("math.sin(q.life_time*40)*4.5", 0, "3+math.sin(q.life_time*23)*3"),
              "arm_l": rot("-math.sin(q.life_time*40)*4.5", 0, "-3-math.sin(q.life_time*23)*3"),
              "hips": {"position": ["math.sin(q.life_time*33)*0.14", "math.sin(q.life_time*60)*0.08", 0]}})


def stand_legs(times, thigh, shin, foot=None):
    """Both legs with the same pose (one value per time); the feet default to staying level."""
    out = {}
    for s in ("r", "l"):
        out[f"thigh_{s}"] = keys(*zip(times, [(v, 0, 0) for v in thigh]))
        out[f"shin_{s}"] = keys(*zip(times, [(v, 0, 0) for v in shin]))
        f = foot if foot is not None else [-0.9 * (a + b) for a, b in zip(thigh, shin)]
        out[f"foot_{s}"] = keys(*zip(times, [(v, 0, 0) for v in f]))
    return out


def both(times, bone, vals):
    """The same x rotation on the _r and _l bones."""
    return {f"{bone}_{s}": keys(*zip(times, [(v, 0, 0) for v in vals])) for s in ("r", "l")}


def spread(times, bone, vals):
    """Outward z swing on both limbs (right +, left -)."""
    return {f"{bone}_r": keys(*zip(times, [(0, 0, v) for v in vals])),
            f"{bone}_l": keys(*zip(times, [(0, 0, -v) for v in vals]))}


RISE = A({"root": {"position": {"0.00": [0, -32, 0], "1.80": [0, 0, 0]}}}, loop=False, length=1.8,
         sfx=[(0.05, "rise")])
SINK = A({"root": {"position": {"0.00": [0, 0, 0], "2.00": [0, -34, 0]}}}, loop=False, length=2.0, sfx=[(0.05, "sink")])


# ------------------------------------------------------------------ Polyphemus
def anims_cyclops():
    mv = MOVES["cyclops"]
    out = {
        "idle": A({"chest": rot("math.sin(q.life_time*55)*1.5"),
                   "head": rot("math.sin(q.life_time*29)*3", "math.sin(q.life_time*37)*8+math.sin(q.life_time*113)*2"),
                   "jaw": rot("math.max(0, math.sin(q.life_time*45))*6"),
                   "arm_r": rot("math.sin(q.life_time*40)*2"), "arm_l": rot("-math.sin(q.life_time*40)*2"),
                   "hand_r": rot("math.sin(q.life_time*90)*3"), "hand_l": rot("-math.sin(q.life_time*90)*3")}),
        "walk": walk(49, leg=20, knee=25, arm=12, bob=0.6, roll=3),          # 11 blocks: a ~7-block stride
        # asleep on his side, snoring every 3.2 s
        "asleep": A({"root": {"rotation": [0, 0, 90], "position": [0, 6.5, 0]},
                     "thigh_r": rot(-70), "thigh_l": rot(-70), "shin_r": rot(95), "shin_l": rot(95),
                     "arm_r": rot(-55), "arm_l": rot(-55), "head": rot(20),
                     "jaw": rot("math.max(0, math.sin(q.anim_time*112))*10")}, length=3.2, sfx=[(0.0, "snore")]),
        # blind: feeling ahead with both hands, sniffing
        "blind_search": A({"head": rot(0, "math.sin(q.life_time*90)*30", 0),
                           "arm_r": rot("-60+math.sin(q.life_time*120)*15", 0, 10),
                           "arm_l": rot("-60+math.sin(q.life_time*120+90)*15", 0, -10)}, length=2.6,
                          sfx=[(0.2, "sniff")]),
        # wading through the sea: arms out for balance
        "wade": A({"arm_r": rot(0, 0, "34+math.sin(q.life_time*110)*6"), "arm_l": rot(0, 0, "-34-math.sin(q.life_time*110)*6"),
                   "chest": rot("math.sin(q.life_time*80)*2")}),
    }
    # --- devour: reach down, scoop a man up, lift him to the mouth, bite twice, toss him away
    d = mv["devour"]
    t = [0, d["grab"], 1.5, d["bite"][0], d["bite"][1], d["release"], d["length"]]
    jt = [0, 1.4, 1.75, d["bite"][0], 2.12, d["bite"][1], 2.62, d["release"], d["length"]]
    out["devour"] = A(M(
        T(t, belly=[0, 6, 0, 0, 0, 4, 0], chest=[0, 14, -2, -6, 2, 10, 0], neck=[0, 5, -6, -10, -4, 4, 0],
          head=[0, 12, -22, -30, -26, 0, 0],
          arm_r=[0, 8, (-25, -20, 20), (-25, -20, 20), (-25, -20, 20), (-30, 20, 30), 0],    # elbow out, palm at the lips
          forearm_r=[0, -20, -140, -140, -140, -30, 0], hand_r=[0, 25, 55, 55, 55, 10, 0],
          arm_l=[0, -10, -22, -26, -26, -10, 0]),
        PT(t, hips=[Z, (0, -5, 0), (0, -2, 0), (0, -2, 0), (0, -2, 0), (0, -4, 0), Z]),
        T(jt, jaw=[0, 0, 34, 0, 30, 0, 28, 6, 0]),
        stand_legs(t, [0, -20, -4, -4, -4, -14, 0], [0, 35, 6, 6, 6, 20, 0])),
        loop=False, length=d["length"],
        sfx=[(0.35, "devour_grab"), (d["bite"][0] - 0.05, "bite"), (d["bite"][1] - 0.05, "bite"), (2.7, "gulp")])
    # --- kick: lean back, swing the right leg through a man standing beside him
    k = mv["kick"]
    t = [0, 0.5, k["hit"], 1.0, k["length"]]
    out["kick"] = A(M(
        T(t, chest=[0, -14, -4, 0, 0], head=[0, -10, 2, 0, 0], arm_r=[0, 20, 30, 10, 0], arm_l=[0, -35, -60, -40, 0],
          thigh_r=[0, 30, -85, -60, 0], shin_r=[0, 55, 0, 10, 0], foot_r=[0, -20, -25, -15, 0],
          thigh_l=[0, -8, -8, -8, 0], shin_l=[0, 12, 12, 12, 0], foot_l=[0, -3, -3, -3, 0]),
        PT(t, hips=[Z, (0, -2, 0), Z, Z, Z])),
        loop=False, length=k["length"], sfx=[(0.45, "kick_whoosh"), (k["hit"], "kick_hit")])
    # --- stomp: lift a foot, arms out for balance, slam it down
    s = mv["stomp"]
    t = [0, 0.6, s["hit"], 1.1, s["length"]]
    out["stomp"] = A(M(
        T(t, chest=[0, -14, 12, 6, 0], head=[0, -8, 10, 5, 0], arm_r=[0, -20, -5, -5, 0], arm_l=[0, -20, -5, -5, 0],
          thigh_r=[0, -70, -8, -8, 0], shin_r=[0, 80, 4, 4, 0], foot_r=[0, -10, 5, 5, 0],
          thigh_l=[0, 6, 6, 6, 0], shin_l=[0, -6, -6, -6, 0], foot_l=[0, 0, 0, 0, 0]),
        spread(t, "arm", [0, 45, 10, 10, 0]),
        PT(t, hips=[Z, (0, 1, 0), (0, -3, 0), (0, -2, 0), Z])),
        loop=False, length=s["length"], sfx=[(s["hit"] - 0.04, "stomp_boom"), (s["hit"] + 0.12, "debris")])
    # --- throw: stoop for the rock, hoist it overhead with both hands, hurl it
    h = mv["throw"]
    t = [0, h["pick"], 0.85, h["release"], 1.5, h["length"]]
    out["throw"] = A(M(
        T(t, chest=[0, 22, -4, -22, 34, 0], head=[0, 10, -14, -14, 8, 0], forearm_r=[0, -20, -30, -30, -10, 0],
          forearm_l=[0, -20, -30, -30, -10, 0]),
        both(t, "arm", [0, -30, -160, -170, -40, 0]),
        PT(t, hips=[Z, (0, -5, 0), (0, -1, 0), (0, -1, 0), (0, -3, 0), Z]),
        stand_legs(t, [0, -22, -6, -6, -14, 0], [0, 38, 8, 8, 24, 0])),
        loop=False, length=h["length"], sfx=[(0.3, "rock_lift"), (h["release"] - 0.02, "throw_grunt")])
    # --- cry to Poseidon: head thrown back, arms raised, the whole body shaking
    c = mv["cry"]
    t = [0, 0.6, 4.4, c["length"]]
    sh = "math.sin(q.anim_time*900)"
    out["cry"] = A(M(
        T(t, head=[0, (f"-45+{sh}*3", 0, 0), (f"-45+{sh}*3", 0, 0), 0], jaw=[0, 35, 35, 0],
          chest=[0, (f"-10+{sh}*2", 0, 0), (f"-10+{sh}*2", 0, 0), 0],
          forearm_r=[0, -35, -35, 0], forearm_l=[0, -35, -35, 0]),
        both(t, "arm", [0, -140, -140, 0]), spread(t, "arm", [0, 25, 25, 0]),
        stand_legs(t, [0, -10, -10, 0], [0, 18, 18, 0])),
        loop=False, length=c["length"], sfx=[(0.1, "cry_voice"), (3.9, "sob")])
    # --- tend the flock: bend down and stroke a sheep, humming
    e = mv["tend"]
    t = [0, 0.9, e["stroke"], 2.2, 2.8, e["length"]]
    out["tend"] = A(M(
        T(t, chest=[0, 16, 18, 16, 8, 0], head=[0, 8, 10, 8, 2, 0], arm_r=[0, -12, -10, -14, -4, 0],
          forearm_r=[0, -25, "-25+math.sin(q.anim_time*400)*12", "-25+math.sin(q.anim_time*400)*12", -8, 0],
          hand_r=[0, 10, "10+math.sin(q.anim_time*520)*10", "10+math.sin(q.anim_time*520)*10", 0, 0]),
        PT(t, hips=[Z, (0, -4, 0), (0, -4, 0), (0, -4, 0), (0, -1, 0), Z]),
        stand_legs(t, [0, -14, -14, -14, -4, 0], [0, 24, 24, 24, 6, 0])),
        loop=False, length=e["length"], sfx=[(0.4, "hum")])
    # --- wake: roll up from his side, stretch and yawn
    w = mv["wake"]
    t = [0, 1.0, 1.4, w["length"]]
    out["wake"] = A(M(
        {"root": {**keys((0, [0, 0, 90]), (1.0, [0, 0, 0]), (w["length"], [0, 0, 0])),
                  **pkeys((0, [0, 6.5, 0]), (1.0, [0, 0, 0]), (w["length"], [0, 0, 0]))}},
        T(t, head=[20, 10, -30, 0], jaw=[0, 0, 40, 0], arm_r=[-55, -30, -150, 0], arm_l=[-55, -30, -150, 0]),
        stand_legs(t, [-70, -10, -10, 0], [95, 20, 20, 0], foot=[0, 0, 0, 0])),
        loop=False, length=w["length"], sfx=[(0.1, "wake_groan")])
    return out


ANIMATE_CYCLOPS = ["idle",
                   {"walk": "q.modified_move_speed > 0.02 && q.property('studio:state') != 'asleep'"},
                   {"wade": "q.is_in_water"},
                   {"asleep": "q.property('studio:state') == 'asleep'"},
                   {"blind_search": "q.property('studio:blind') && q.property('studio:state') != 'asleep'"}]


# ------------------------------------------------------------------ Laestrygonians
def anims_laestrygonian():
    mv = MOVES["laestrygonian"]
    out = {
        "idle": A({"torso": rot("math.sin(q.life_time*50)*1.2"), "head": rot(0, "math.sin(q.life_time*18)*15"),
                   "arm_l": rot("math.sin(q.life_time*35)*2")}),
        "walk": walk(90, leg=24, knee=28, arm=10, bob=1.0, roll=4, chest="torso"),
    }
    # --- slash (sword): torso wound right, then swept left through everything in front
    s = mv["slash"]
    t = [0, 0.45, s["hit"], 0.8, s["length"]]
    out["slash"] = A(M(
        {"torso": keys(*zip(t, [Z, (4, 55, 0), (10, -50, 0), (8, -45, 0), Z]))},
        {"head": keys(*zip(t, [Z, (0, -30, 0), (0, 30, 0), (0, 26, 0), Z]))},
        {"arm_r": keys(*zip(t, [Z, (-42, 0, 40), (-46, 0, -5), (-40, 0, -5), Z]))},
        T(t, arm_l=[0, -10, -20, -15, 0], thigh_r=[0, 10, -12, -10, 0], thigh_l=[0, -10, 12, 10, 0])),
        loop=False, length=s["length"], sfx=[(0.5, "slash_whoosh"), (s["hit"] + 0.02, "blade_ring")])
    # --- impale (glaive): draw the pole back, thrust it out, heave the man overhead and fling him
    i = mv["impale"]
    t = [0, 0.35, i["hit"], 0.8, i["fling"], 1.3, i["length"]]
    out["impale"] = A(M(
        {"torso": keys(*zip(t, [Z, (-4, 28, 0), (12, -8, 0), (6, -8, 0), (8, -8, 0), (12, 0, 0), Z]))},
        T(t, arm_r=[0, -10, -35, -75, -45, -30, 0], glaive=[0, -22, 150, 70, 150, 90, 0],
          thigh_l=[0, 8, -14, -14, -10, -4, 0], thigh_r=[0, -6, 10, 10, 6, 2, 0])),
        loop=False, length=i["length"], sfx=[(0.5, "thrust"), (i["hit"] + 0.02, "stab"), (i["fling"] - 0.02, "fling")])
    # --- crush (mace): both arms overhead, slam it into the ground
    c = mv["crush"]
    t = [0, 0.7, c["hit"], 1.2, c["length"]]
    out["crush"] = A(M(
        T(t, torso=[0, -24, 30, 22, 0], head=[0, 10, -12, -8, 0], forearm_r=[0, -25, -8, -8, 0], mace=[0, 20, -10, -10, 0],
          thigh_r=[0, 8, -20, -16, 0], thigh_l=[0, 8, -20, -16, 0], shin_r=[0, -4, 18, 14, 0], shin_l=[0, -4, 18, 14, 0]),
        both(t, "arm", [0, -150, -62, -58, 0]), spread(t, "arm", [0, 8, 4, 4, 0]),
        PT(t, hips=[Z, (0, 1, 0), (0, -3, 0), (0, -2, 0), Z])),
        loop=False, length=c["length"], sfx=[(c["hit"] - 0.04, "mace_slam"), (c["hit"] + 0.07, "debris")])
    # --- cleave (curved blade): two sweeping cuts, right to left and back
    v = mv["cleave"]
    t = [0, 0.3, v["hit"][0], 0.7, v["hit"][1], 1.3, v["length"]]
    out["cleave"] = A(M(
        {"torso": keys(*zip(t, [Z, (2, 65, 0), (8, -75, 0), (6, -75, 0), (8, 65, 0), (4, 40, 0), Z]))},
        {"head": keys(*zip(t, [Z, (0, -35, 0), (0, 40, 0), (0, 40, 0), (0, -35, 0), (0, -20, 0), Z]))},
        {"arm_r": keys(*zip(t, [Z, (-40, 0, 35), (-48, 0, -8), (-44, 0, -8), (-48, 0, 35), (-30, 0, 10), Z]))},
        T(t, thigh_r=[0, 8, -10, -10, 8, 4, 0], thigh_l=[0, -8, 10, 10, -8, -4, 0])),
        loop=False, length=v["length"], sfx=[(0.36, "cleave_whoosh"), (0.86, "cleave_whoosh")])
    # --- smash: raise the weapon high on the right and chop down through a ship
    m = mv["smash"]
    t = [0, 0.5, m["hit"], 1.2, m["length"]]
    out["smash"] = A(M(
        {"torso": keys(*zip(t, [Z, (-14, 25, 0), (26, -18, 0), (20, -14, 0), Z]))},
        {"arm_r": keys(*zip(t, [Z, (-135, 0, 25), (-34, 0, -8), (-32, 0, -8), Z]))},
        T(t, arm_l=[0, -40, -50, -40, 0], thigh_r=[0, 6, -18, -14, 0], thigh_l=[0, 6, -18, -14, 0],
          shin_r=[0, 0, 14, 10, 0], shin_l=[0, 0, 14, 10, 0])),
        loop=False, length=m["length"], sfx=[(m["hit"] - 0.06, "boat_smash")])
    return out


ANIMATE_LAESTRYGONIAN = ["idle", {"walk": "q.modified_move_speed > 0.02"}]


# ------------------------------------------------------------------ the armoured child
def anims_child():
    mv = MOVES["laestrygonian_child"]
    lt = [0, 0.3, 1.5, mv["laugh"]["length"]]
    st = [0, 0.3, 1.7, mv["scream"]["length"]]
    shake = "math.sin(q.anim_time*900)"
    return {
        "idle": human_idle(14), "walk": walk(220, leg=34, knee=40, arm=26, bob=0.5),
        # doubled over, shoulders shaking
        "laugh": A(M(T(lt, head=[0, (f"-12+{shake}*4", 0, 0), (f"-12+{shake}*4", 0, 0), 0],
                       chest=[0, (f"{shake}*3", 0, 0), (f"{shake}*3", 0, 0), 0],
                       forearm_r=[0, -60, -60, 0], forearm_l=[0, -60, -60, 0]),
                     both(lt, "arm", [0, -40, -40, 0])),
                   loop=False, length=mv["laugh"]["length"], sfx=[(0.1, "laugh")]),
        # head back, arms flung out, screaming for the giants
        "scream": A(M(T(st, head=[0, -28, -28, 0], chest=[0, -6, -6, 0]),
                      both(st, "arm", [0, -30, -30, 0]), spread(st, "arm", [0, 35, 35, 0])),
                    loop=False, length=mv["scream"]["length"], sfx=[(0.1, "scream")]),
    }


ANIMATE_CHILD = ["idle", {"walk": "q.modified_move_speed > 0.02"}]


# ------------------------------------------------------------------ Circe and her sister
def anims_circe():
    mv = MOVES["circe"]
    sv, sc, mo, co = mv["serve"], mv["scream"], mv["mold"], mv["counsel"]
    t1 = [0, 0.6, sv["give"], 1.9, sv["length"]]
    t2 = [0, 0.3, 1.5, sc["length"]]
    t4 = [0, 0.6, 1.2, 2.0, co["length"]]
    return {
        # a floor-length gown: short steps keep the feet under the hem
        "idle": human_idle(8), "walk": walk(200, leg=9, knee=10, arm=12, bob=0.3),
        "yielded": A({"head": rot(10), "arm_r": rot(-10, 0, 6), "arm_l": rot(-10, 0, -6)}),
        # ladling stew: turns, offers a bowl in outstretched hands
        "serve": A(M({"waist": keys(*zip(t1, [Z, (0, 18, 0), (0, 18, 0), (0, 6, 0), Z]))},
                     T(t1, arm_r=[0, -62, -66, -30, 0], arm_l=[0, -40, -48, -20, 0], forearm_r=[0, -40, -46, -14, 0],
                       forearm_l=[0, -50, -56, -20, 0], head=[0, 12, 14, 4, 0])),
                   loop=False, length=sv["length"], sfx=[(0.7, "ladle")]),
        # the sensible thing to do when armoured strangers demand food: scream
        "scream": A(M(T(t2, head=[0, -14, -14, 0], chest=[0, -8, -8, 0],
                        arm_r=[0, -118, -118, 0], arm_l=[0, -118, -118, 0], forearm_r=[0, -125, -125, 0],
                        forearm_l=[0, -125, -125, 0])),
                    loop=False, length=sc["length"], sfx=[(0.1, "scream")]),
        # working men's flesh like clay
        "mold": A({"arm_r": rot(-65, 10, 0), "arm_l": rot(-65, -10, 0),
                   "forearm_r": rot("-25+math.sin(q.anim_time*720)*18"), "forearm_l": rot("-25-math.sin(q.anim_time*720)*18"),
                   "hand_r": rot(0, 0, "math.sin(q.anim_time*900)*20"), "hand_l": rot(0, 0, "-math.sin(q.anim_time*900)*20"),
                   "head": rot(18)}, loop=False, length=mo["length"], sfx=[(0.0, "squelch")]),
        # pointing the way to Hades
        "counsel": A(M({"arm_r": keys(*zip(t4, [Z, (-80, 0, 12), (-84, 0, 12), (-84, 0, 12), Z]))},
                       {"head": keys(*zip(t4, [Z, (0, -20, 0), (0, -26, 0), (0, -20, 0), Z]))},
                       T(t4, arm_l=[0, -30, -34, -30, 0], forearm_l=[0, -70, -80, -70, 0])),
                     loop=False, length=co["length"], sfx=[(0.3, "murmur")]),
    }


ANIMATE_CIRCE = ["idle", {"walk": "q.modified_move_speed > 0.02"}, {"yielded": "q.property('studio:yielded')"}]


def anims_sister():
    f = MOVES["circe_sister"]["flap"]["length"]
    return {"idle": A({"head": rot("math.sin(q.life_time*200)*6", "math.sin(q.life_time*90)*35"),
                       "tail": rot("math.sin(q.life_time*160)*8")}),
            # struggling in a man's hand
            "flap": A({"wing_r": rot(0, 0, "30+math.sin(q.anim_time*2200)*50"),
                       "wing_l": rot(0, 0, "-30-math.sin(q.anim_time*2200)*50"),
                       "body": rot("math.sin(q.anim_time*1100)*12", "math.sin(q.anim_time*700)*15"),
                       "head": rot("math.sin(q.anim_time*1800)*14"), "tail": rot("math.sin(q.anim_time*1100)*20")},
                      loop=False, length=f, sfx=[(0.05, "screech")])}


# ------------------------------------------------------------------ the Sirens (mermaids on the rocks)
def anims_siren():
    mv = MOVES["siren"]
    sg, bk, dr = mv["sing"], mv["beckon"], mv["drag"]
    base = {"chest": rot("math.sin(q.life_time*30)*2", 0, "math.sin(q.life_time*24)*3"),
            "head": rot("math.sin(q.life_time*20)*4", "math.sin(q.life_time*14)*12"),
            "arm_r": rot("math.sin(q.life_time*40)*10"), "forearm_r": rot("math.sin(q.life_time*40+50)*14")}
    for n in range(5):
        base[f"tail_{n}"] = rot(0, f"math.sin(q.life_time*45-{n * 35})*{3 + n * 2}", 0)
    base["tail_4"] = rot("math.sin(q.life_time*60)*12", "math.sin(q.life_time*45-140)*11", 0)
    # singing: head thrown back, arm lifted, the whole body swaying with the song
    t = [0, 0.8, sg["length"] - 0.8, sg["length"]]
    hd, ch = "-24+math.sin(q.anim_time*60)*4", "-8+math.sin(q.anim_time*45)*3"
    sing = M(T(t, head=[0, (hd, 0, 0), (hd, 0, 0), 0], chest=[0, (ch, 0, 0), (ch, 0, 0), 0], arm_l=[0, -48, -48, 0],
               forearm_l=[0, "-20+math.sin(q.anim_time*90)*8", "-20+math.sin(q.anim_time*90)*8", 0]),
             {f"tail_{n}": keys(*zip(t, [Z, (0, f"math.sin(q.anim_time*70-{n * 40})*{8 + n * 3}", 0),
                                         (0, f"math.sin(q.anim_time*70-{n * 40})*{8 + n * 3}", 0), Z]))
              for n in range(5)})
    # beckoning with a curling hand
    t = [0, 0.5, 1.7, bk["length"]]
    fo, ha = "-30+math.sin(q.anim_time*520)*26", "math.sin(q.anim_time*520+40)*30"
    beckon = T(t, arm_l=[0, -72, -72, 0], head=[0, -8, -8, 0], forearm_l=[0, (fo, 0, 0), (fo, 0, 0), 0],
               hand_l=[0, (ha, 0, 0), (ha, 0, 0), 0])
    # lunging to seize a man, hauling him under
    t = [0, dr["grab"], 1.0, dr["length"]]
    drag = M(T(t, waist=[0, 28, -14, 0], head=[0, 10, -6, 0], arm_l=[0, -88, -22, 0], arm_r=[0, -84, -26, 0],
               forearm_l=[0, -10, -50, 0], forearm_r=[0, -10, -50, 0]),
             {f"tail_{n}": keys(*zip(t, [Z, (0, f"math.sin(q.anim_time*180-{n * 30})*{14 + n * 4}", 0),
                                         (0, f"math.sin(q.anim_time*180-{n * 30})*{14 + n * 4}", 0), Z]))
              for n in range(5)})
    return {"idle": A(base),
            "sing": A(sing, loop=False, length=sg["length"]),
            "beckon": A(beckon, loop=False, length=bk["length"], sfx=[(0.3, "beckon_breath")]),
            "drag": A(drag, loop=False, length=dr["length"], sfx=[(0.1, "drag_hiss"), (1.0, "splash")])}


ANIMATE_SIREN = ["idle"]


# ------------------------------------------------------------------ people: Calypso, Athena, Tiresias, the shades
def anims_calypso():
    mv = MOVES["calypso"]
    of, em = mv["offer"], mv["embrace"]
    t1 = [0, 0.7, of["give"], 1.9, of["length"]]
    t2 = [0, 0.8, em["hug"], 2.0, em["length"]]
    return {"idle": human_idle(10), "walk": walk(200, leg=24, knee=26, arm=14, bob=0.3),
            # holding out a lotus flower
            "offer": A(M(T(t1, arm_r=[0, -66, -70, -30, 0], forearm_r=[0, -34, -40, -10, 0], hand_r=[0, 10, 14, 0, 0],
                           head=[0, 6, 8, 2, 0], chest=[0, 4, 6, 2, 0])),
                       loop=False, length=of["length"], sfx=[(0.6, "lotus_chime")]),
            # an embrace: arms open, then folded around a man
            "embrace": A(M(T(t2, arm_r=[0, -72, -84, -30, 0], arm_l=[0, -72, -84, -30, 0], forearm_r=[0, -20, -80, -20, 0],
                             forearm_l=[0, -20, -80, -20, 0], chest=[0, 6, 10, 4, 0]),
                           {"head": keys(*zip(t2, [Z, (4, 0, 0), (6, 18, 0), (2, 8, 0), Z]))},
                           spread(t2, "arm", [0, 30, 8, 14, 0])),
                         loop=False, length=em["length"], sfx=[(em["hug"] - 0.1, "sigh")])}


def anims_athena():
    mv = MOVES["athena"]
    bl, ap, va = mv["bless"], mv["appear"], mv["vanish"]
    tb = [0, 0.6, 1.6, bl["length"]]
    ta = [0, 0.8, ap["length"]]
    tv = [0, 0.8, va["length"]]
    return {"idle": human_idle(10), "walk": walk(200, leg=9, knee=10, arm=14, bob=0.3),     # floor-length gown
            "bless": A(M(T(tb, arm_r=[0, -112, -112, 0], forearm_r=[0, -20, -20, 0], head=[0, 8, 8, 0],
                           chest=[0, 4, 4, 0])),
                       loop=False, length=bl["length"], sfx=[(0.3, "chime")]),
            # a vision: arms rise from her sides as she materialises
            "appear": A(M(T(ta, head=[-10, 0, 0], chest=[-4, 0, 0]), spread(ta, "arm", [60, 22, 6])),
                        loop=False, length=ap["length"], sfx=[(0.0, "shimmer")]),
            "vanish": A(M(T(tv, head=[0, -14, -22], chest=[0, -6, -8]), spread(tv, "arm", [6, 40, 62])),
                        loop=False, length=va["length"], sfx=[(0.1, "shimmer")])}


def anims_tiresias():
    mv = MOVES["tiresias"]
    sp = mv["speak"]["length"]
    t = [0, 0.6, 2.8, sp]
    arm = ("-52+math.sin(q.anim_time*80)*12", 0, 10)
    hd = "math.sin(q.anim_time*120)*5"
    return {"idle": A({"chest": rot("math.sin(q.life_time*30)*1.5"),
                       "head": rot("math.sin(q.life_time*22)*4", "math.sin(q.life_time*11)*14")}),
            "rise": RISE, "sink": SINK,
            # prophesying: one arm raised, the head shaking with each word
            "speak": A(M({"arm_r": keys((0, Z), (0.6, arm), (2.8, arm), (sp, Z))},
                         T(t, head=[0, (hd, 0, 0), (hd, 0, 0), 0])),
                       loop=False, length=sp, sfx=[(0.2, "voice")])}


def anims_shade():
    mv = MOVES["shade"]
    gr = mv["grasp"]
    ts = [0, 0.6, 2.4, mv["speak_sinon"]["length"]]
    tg = [0, gr["hit"], 1.2, gr["length"]]
    hd = "12+math.sin(q.anim_time*70)*3"
    return {"idle": A({"chest": rot("6+math.sin(q.life_time*40)*2", 0, "math.sin(q.life_time*23)*3"),
                       "head": rot("math.sin(q.life_time*31)*5", "math.sin(q.life_time*19)*10"),
                       "arm_r": rot("-8+math.sin(q.life_time*35)*4"), "arm_l": rot("-8-math.sin(q.life_time*35)*4")}),
            "walk": walk(190, leg=26, knee=28, arm=10, bob=0.4),
            "rise": RISE, "sink": SINK,
            # Sinon: a hand pressed to his chest, reproaching
            "speak_sinon": A(M(T(ts, arm_r=[0, -62, -62, 0], forearm_r=[0, -105, -105, 0], head=[0, (hd, 0, 0), (hd, 0, 0), 0])),
                             loop=False, length=mv["speak_sinon"]["length"], sfx=[(0.2, "voice")]),
            # Agamemnon: an accusing arm thrust out, head high
            "speak_agamemnon": A(M(T(ts, head=[0, -12, -12, 0], chest=[0, -6, -6, 0]),
                                   {"arm_r": keys(*zip(ts, [Z, (-82, 0, -8), (-82, 0, -8), Z]))}),
                                 loop=False, length=mv["speak_agamemnon"]["length"], sfx=[(0.2, "voice")]),
            # the crew: both arms reaching for the living, wanting them to join their shame
            "grasp": A(M(T(tg, arm_r=[0, -96, -90, 0], arm_l=[0, -96, -90, 0], chest=[0, 16, 10, 0], head=[0, 10, 6, 0])),
                       loop=False, length=gr["length"], sfx=[(0.3, "grasp_moan")])}


ANIMATE_SHADE = ["idle", {"walk": "q.modified_move_speed > 0.02"}]
ANIMATE_TIRESIAS = ["idle"]
ANIMATE_NPC = ["idle", {"walk": "q.modified_move_speed > 0.02"}]


# ------------------------------------------------------------------ Scylla: six heads, five phases of attack
def anims_scylla(necks=6, segs=8):
    mv = MOVES["scylla"]
    idle = {}
    for i in range(necks):
        for s in range(segs):
            idle[f"neck_{i}_{s}"] = rot(f"math.sin(q.life_time*60+{i * 61 + s * 37})*4", 0, f"math.cos(q.life_time*45+{i * 47 + s * 29})*3")
        idle[f"jaw_{i}"] = rot(f"math.max(0, math.sin(q.life_time*90+{i * 83}))*18")
        idle[f"head_{i}"] = rot(f"math.sin(q.life_time*70+{i * 50})*6", f"math.sin(q.life_time*35+{i * 70})*10")
    out = {"idle": A(idle, length=6.0, sfx=[(0.0, "hiss")])}

    def per_head(fn):
        bones = {}
        for i in range(necks):
            side = (i - (necks - 1) / 2) / ((necks - 1) / 2)       # -1 (left) .. +1 (right)
            for bone, frames in fn(i, side).items():
                bones[bone] = keys(*frames)
        return bones

    # lunge: every neck stretches out toward the deck
    ln = mv["lunge"]["length"]

    def lunge(i, side):
        p = i * 0.04
        return {f"neck_{i}_0": [(0, Z), (0.45 + p, (42, 14 * side, 0)), (0.9, (32, 10 * side, 0)), (ln, (22, 8 * side, 0))],
                f"neck_{i}_3": [(0, Z), (0.45 + p, (-12, 0, 0)), (ln, (-6, 0, 0))],
                f"head_{i}": [(0, Z), (0.45 + p, (30, 0, 0)), (ln, (18, 0, 0))],
                f"jaw_{i}": [(0, Z), (0.4 + p, (42, 0, 0)), (ln, (14, 0, 0))]}
    out["lunge"] = A(per_head(lunge), loop=False, length=ln, sfx=[(0.15, "roar")])

    # snatch: each head dives and bites its man in turn
    sn = mv["snatch"]

    def snatch(i, side):
        b = sn["bite"] + i * 0.06
        return {f"neck_{i}_0": [(0, (22, 8 * side, 0)), (b - 0.2, (58, 16 * side, 0)), (b + 0.4, (34, 8 * side, 0)),
                                (sn["length"], (18, 4 * side, 0))],
                f"neck_{i}_3": [(0, (-6, 0, 0)), (b - 0.2, (-4, 0, 0)), (sn["length"], (8, 0, 0))],
                f"head_{i}": [(0, (18, 0, 0)), (b - 0.2, (42, 0, 0)), (b + 0.4, (28, 0, 0)), (sn["length"], (14, 0, 0))],
                f"jaw_{i}": [(0, (14, 0, 0)), (b - 0.25, (46, 0, 0)), (b, (0, 0, 0)), (sn["length"], (4, 0, 0))]}
    out["snatch"] = A(per_head(snatch), loop=False, length=sn["length"],
                      sfx=[(sn["bite"] + 0.06 * i, "bite") for i in range(necks)])

    # devour: heads haul their victims up toward the cave and chew
    dv = mv["devour"]

    def devour(i, side):
        n_t = dv["length"]
        chew = f"math.max(0, math.sin(q.anim_time*520+{i * 70}))*22"
        return {f"neck_{i}_0": [(0, (18, 4 * side, 0)), (0.7, (-12, 6 * side, 0)), (n_t - 0.5, (-14, 6 * side, 0)), (n_t, (14, 4 * side, 0))],
                f"neck_{i}_3": [(0, (8, 0, 0)), (0.7, (22, 0, 0)), (n_t - 0.5, (22, 0, 0)), (n_t, (4, 0, 0))],
                f"head_{i}": [(0, (14, 0, 0)), (0.7, (-6, 0, 0)), (n_t - 0.5, (-6, 0, 0)), (n_t, (10, 0, 0))],
                f"jaw_{i}": [(0, (4, 0, 0)), (0.5, (8, 0, 0)), (1.0, (chew, 0, 0)), (n_t - 0.5, (chew, 0, 0)), (n_t, (6, 0, 0))]}
    out["devour"] = A(per_head(devour), loop=False, length=dv["length"], sfx=[(b, "chew") for b in dv["bite"]])

    # rend: the heads swing across and tear a ship apart
    rd = mv["rend"]

    def rend(i, side):
        t_hit = rd["hit"] + 0.05 * abs(side)
        return {f"neck_{i}_0": [(0, Z), (0.35, (-10, 0, 0)), (t_hit, (72, -34 * side, 0)), (1.2, (60, 30 * side, 0)), (rd["length"], (14, 0, 0))],
                f"neck_{i}_4": [(0, Z), (t_hit, (24, 0, 0)), (rd["length"], (2, 0, 0))],
                f"head_{i}": [(0, Z), (t_hit, (40, 0, 0)), (1.2, (36, 20 * side, 0)), (rd["length"], (8, 0, 0))],
                f"jaw_{i}": [(0, Z), (t_hit - 0.1, (40, 0, 0)), (1.2, (10, 0, 0)), (rd["length"], (4, 0, 0))]}
    out["rend"] = A(per_head(rend), loop=False, length=rd["length"], sfx=[(rd["hit"] - 0.05, "rend")])

    # recoil: back into the cave, hissing
    rc = mv["recoil"]

    def recoil(i, side):
        return {f"neck_{i}_0": [(0, (14, 0, 0)), (0.4, (-26, 4 * side, 0)), (rc["length"], Z)],
                f"neck_{i}_3": [(0, (4, 0, 0)), (0.4, (14, 0, 0)), (rc["length"], Z)],
                f"head_{i}": [(0, (10, 0, 0)), (0.4, (-10, 0, 0)), (rc["length"], Z)],
                f"jaw_{i}": [(0, (6, 0, 0)), (0.3, (34, 0, 0)), (rc["length"], Z)]}
    out["recoil"] = A(per_head(recoil), loop=False, length=rc["length"], sfx=[(0.1, "hiss")])
    return out


ANIMATE_SCYLLA = ["idle"]


# ------------------------------------------------------------------ Charybdis
def anims_charybdis(rings=7):
    mv = MOVES["charybdis"]
    b = {"core": rot(0, "q.life_time*240", 0), "spiral": rot(0, "q.life_time*90", 0)}
    sg = {"core": rot(0, "q.anim_time*720", 0), "spiral": rot(0, "q.anim_time*270", 0),
          "root": {"position": [0, "math.sin(q.anim_time*40)*1.5", 0]}}
    g = mv["gulp"]
    t = [0, g["gulp"], 1.0, g["length"]]
    # the funnel stretches downward as one piece: neighbouring layers never sink more than half a unit apart
    gulp = {"core": pkeys(*zip(t, [Z, (0, -5, 0), (0, -2, 0), Z])), "spiral": pkeys(*zip(t, [Z, (0, -4.2, 0), (0, -1.7, 0), Z]))}
    for k in range(rings):
        for s_ in ("a", "b"):
            b[f"ring{s_}_{k}"] = rot(0, f"q.life_time*{60 + k * 30}", 0)
            sg[f"ring{s_}_{k}"] = rot(0, f"q.anim_time*{180 + k * 90}", 0)
            gulp[f"ring{s_}_{k}"] = pkeys(*zip(t, [Z, (0, -(4.0 - k * 0.45), 0), (0, -(1.6 - k * 0.18), 0), Z]))
    return {"swirl": A(b, length=4.0, sfx=[(0.0, "roar")]),
            "surge": A(sg, loop=False, length=mv["surge"]["length"], sfx=[(0.0, "surge")]),
            "gulp": A(gulp, loop=False, length=g["length"], sfx=[(0.1, "gulp")])}


ANIMATE_CHARYBDIS = ["swirl"]


# ------------------------------------------------------------------ cattle of Apollo
def anims_cattle():
    mv = MOVES["sun_cattle"]
    d = "q.modified_distance_moved*240"
    gz, lw = mv["graze"]["length"], mv["low"]["length"]
    tg = [0, 0.7, 2.6, gz]
    tl = [0, 0.5, 1.2, lw]
    return {"idle": A({"head": rot("math.max(0, math.sin(q.life_time*12))*30", "math.sin(q.life_time*9)*10"),
                       "tail": rot(0, 0, "math.sin(q.life_time*140)*14")}),
            "walk": A({"leg_fl": rot(f"math.cos({d})*25"), "leg_hr": rot(f"math.cos({d})*25"),
                       "leg_fr": rot(f"-math.cos({d})*25"), "leg_hl": rot(f"-math.cos({d})*25")}),
            # head down to the grass, chewing
            "graze": A(M(T(tg, head=[0, 44, ("44+math.sin(q.anim_time*420)*5", 0, 0), 0], leg_fl=[0, -8, -8, 0],
                           leg_fr=[0, -8, -8, 0]),
                         {"tail": keys(*zip(tg, [Z, (0, 0, 8), (0, 0, -8), Z]))}),
                       loop=False, length=gz, sfx=[(0.8, "chew")]),
            # head up, lowing
            "low": A(M(T(tl, head=[0, -42, -42, 0]), {"tail": keys(*zip(tl, [Z, (0, 0, 12), (0, 0, -12), Z]))}),
                     loop=False, length=lw, sfx=[(0.3, "low")])}


ANIMATE_CATTLE = ["idle", {"walk": "q.modified_move_speed > 0.02"}]


# ------------------------------------------------------------------ the Trojan Horse
def anims_horse():
    mv = MOVES["trojan_horse"]
    h, s = mv["hatch"], mv["sally"]
    th = [0, 0.4, h["open"], 1.5, h["length"]]
    ts = [0, 0.5, s["eject"], 2.2, s["length"]]
    shudder = {"body": rot("math.sin(q.anim_time*1500)*1.6", 0, "math.sin(q.anim_time*1100)*1.6")}
    return {"rear": A({"body": rot("math.sin(q.life_time*30)*0.8", 0, "math.cos(q.life_time*22)*0.5"),
                       "head": rot("math.sin(q.life_time*40)*2")}, length=4.0, sfx=[(1.8, "creak")]),
            # the belly hatch swings down
            "hatch": A(T(th, hatch=[0, 82, 82, 82, 0]), loop=False, length=h["length"], sfx=[(0.35, "hatch_open")]),
            # the Greeks pour out: the whole horse shudders, then the hatch drops
            "sally": A(M(T(ts, hatch=[0, 0, 88, 88, 0]), shudder), loop=False, length=s["length"],
                       sfx=[(0.0, "shudder"), (0.55, "hatch_open")])}


ANIMATE_HORSE = ["rear"]


# ------------------------------------------------------------------ boulder
def anims_boulder():
    return {"spin": A({"rock": rot("q.life_time*400", "q.life_time*250", 0)})}


# ------------------------------------------------------------------ animation controllers
def moves_controller(entity, base):
    """One controller per entity. `default` plays the continuous animations; each move has its own state, so the
    animation restarts from 0 whenever the script sets `studio:anim` to it. Moves may chain directly into each other."""
    names = list(MOVES.get(entity, {}))
    prop = "q.property('studio:anim')"
    states = {"default": {"animations": list(base), "blend_transition": 0.15,
                          "transitions": [{m: f"{prop} == '{m}'"} for m in names]}}
    for m in names:
        states[m] = {"animations": [m], "blend_transition": 0.1,
                     "transitions": [{o: f"{prop} == '{o}'"} for o in names if o != m] + [{"default": f"{prop} == 'none'"}]}
    return {"format_version": "1.10.0", "animation_controllers": {f"controller.animation.{entity}.moves": {
        "initial_state": "default", "states": states}}}


def steps_controller(entity, k, effect="step"):
    """Footstep sounds on every foot strike: the sign of sin(phase) flips exactly when the gait's legs are
    furthest apart, so the state change (and its sound) lands on the heel strike of the walk animation."""
    d = f"q.modified_distance_moved*{k}"
    moving = "q.modified_move_speed > 0.02"
    return {"format_version": "1.10.0", "animation_controllers": {f"controller.animation.{entity}.steps": {
        "initial_state": "still", "states": {
            "still": {"transitions": [{"a": f"{moving} && math.sin({d}) >= 0"}, {"b": f"{moving} && math.sin({d}) < 0"}]},
            "a": {"sound_effects": [{"effect": effect}],
                  "transitions": [{"still": f"!({moving})"}, {"b": f"math.sin({d}) < 0"}]},
            "b": {"sound_effects": [{"effect": effect}],
                  "transitions": [{"still": f"!({moving})"}, {"a": f"math.sin({d}) >= 0"}]}}}}}
