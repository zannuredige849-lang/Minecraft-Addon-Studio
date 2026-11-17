"""Molang animations for every entity, driven by actor properties set by the behaviour pack and script.

Stride constants are degrees per block walked (q.modified_distance_moved is in blocks): a full gait cycle should
cover roughly two steps of the creature's real leg length, so long legs get small constants.
"""


def A(bones, loop=True, length=None):
    a = {"loop": loop, "bones": bones}
    if length:
        a["animation_length"] = length
    return a


def rot(x=0, y=0, z=0):
    return {"rotation": [x, y, z]}


def keys(*frames):
    """frames: (time, [x, y, z]) pairs."""
    return {"rotation": {f"{t:.2f}": v for t, v in frames}}


def walk(k, leg=26, knee=30, arm=16, bob=0.4, roll=3, legs=("thigh", "shin"), arms="arm", chest="chest", hips="hips"):
    d = f"q.modified_distance_moved*{k}"
    th, sh = legs
    b = {
        f"{th}_r": rot(f"math.cos({d})*{leg}"), f"{th}_l": rot(f"-math.cos({d})*{leg}"),
        f"{sh}_r": rot(f"math.max(0, math.sin({d}))*{knee}"), f"{sh}_l": rot(f"math.max(0, -math.sin({d}))*{knee}"),
        hips: {"position": [0, f"-math.abs(math.sin({d}))*{bob}", 0]},
    }
    if arms:
        b[f"{arms}_r"] = rot(f"-math.cos({d})*{arm}")
        b[f"{arms}_l"] = rot(f"math.cos({d})*{arm}")
    if chest:
        b[chest] = rot(0, f"math.cos({d})*{roll}", 0)
    return A(b)


def human_idle(head_amp=10, breathe=1.2):
    return A({"chest": rot(f"math.sin(q.life_time*60)*{breathe}"),
              "head": rot("math.sin(q.life_time*28)*3", f"math.sin(q.life_time*17)*{head_amp}"),
              "arm_r": rot("math.sin(q.life_time*40)*2", 0, "math.sin(q.life_time*23)*1.5"),
              "arm_l": rot("-math.sin(q.life_time*40)*2", 0, "-math.sin(q.life_time*23)*1.5")})


RISE = A({"root": {"position": {"0.00": [0, -32, 0], "1.80": [0, 0, 0]}}}, loop=False, length=1.8)
SINK = A({"root": {"position": {"0.00": [0, 0, 0], "2.00": [0, -34, 0]}}}, loop=False, length=2.0)


def anims_cyclops():
    return {
        "idle": A({"chest": rot("math.sin(q.life_time*55)*1.5"),
                   "head": rot("math.sin(q.life_time*29)*3", "math.sin(q.life_time*37)*8+math.sin(q.life_time*113)*2"),
                   "jaw": rot("math.max(0, math.sin(q.life_time*45))*6"),
                   "arm_r": rot("math.sin(q.life_time*40)*2"), "arm_l": rot("-math.sin(q.life_time*40)*2"),
                   "hand_r": rot("math.sin(q.life_time*90)*3"), "hand_l": rot("-math.sin(q.life_time*90)*3")}),
        "walk": walk(83, leg=20, knee=25, arm=12, bob=0.6, roll=3),        # 6.5 blocks: ~4.3-block stride
        # solved so the wrist sits ~7 units in front of the mouth, where the script holds the victim
        "grab": A({"arm_r": rot(-32, -10, 12), "forearm_r": rot(-110), "hand_r": rot(45),
                   "jaw": rot("20+math.sin(q.anim_time*720)*12"), "head": rot(-15)}),
        "throw": A({"arm_r": keys((0, [0, 0, 0]), (0.35, [-170, 0, 15]), (0.55, [-50, 0, 0]), (0.9, [0, 0, 0])),
                    "chest": keys((0, [0, 0, 0]), (0.35, [-10, 0, 0]), (0.55, [12, 0, 0]), (0.9, [0, 0, 0]))},
                   loop=False, length=0.9),
        "cry": A({"head": rot(-40, "math.sin(q.life_time*500)*5", 0), "jaw": rot(32),
                  "arm_r": rot(-125, 0, -20), "arm_l": rot(-125, 0, 20), "forearm_r": rot(-50), "forearm_l": rot(-50)}),
        "asleep": A({"root": {"rotation": [0, 0, 90], "position": [0, 6.5, 0]},
                     "thigh_r": rot(-70), "thigh_l": rot(-70), "shin_r": rot(95), "shin_l": rot(95),
                     "arm_r": rot(-55), "arm_l": rot(-55), "head": rot(20),
                     "jaw": rot("math.max(0, math.sin(q.life_time*35))*10")}),
        "blind_search": A({"head": rot(0, "math.sin(q.life_time*90)*30", 0),
                           "arm_r": rot("-60+math.sin(q.life_time*120)*15", 0, 10),
                           "arm_l": rot("-60+math.sin(q.life_time*120+90)*15", 0, -10)}),
    }


ANIMATE_CYCLOPS = ["idle",
                   {"walk": "q.modified_move_speed > 0.02 && q.property('studio:state') != 'asleep'"},
                   {"grab": "q.property('studio:anim') == 'grab'"},
                   {"throw": "q.property('studio:anim') == 'throw'"},
                   {"cry": "q.property('studio:anim') == 'cry'"},
                   {"asleep": "q.property('studio:state') == 'asleep'"},
                   {"blind_search": "q.property('studio:blind') && q.property('studio:state') != 'asleep'"}]


def anims_laestrygonian():
    return {
        "idle": A({"torso": rot("math.sin(q.life_time*50)*1.2"), "head": rot(0, "math.sin(q.life_time*18)*15"),
                   "arm_l": rot("math.sin(q.life_time*35)*2")}),
        "walk": walk(90, leg=24, knee=28, arm=10, bob=1.0, roll=4, chest="torso"),
        "swing": A({"arm_r": keys((0, [0, 0, 0]), (0.35, [-150, 0, 20]), (0.55, [-20, 0, -10]), (0.8, [0, 0, 0])),
                    "torso": keys((0, [0, 0, 0]), (0.35, [-8, 15, 0]), (0.55, [12, -15, 0]), (0.8, [0, 0, 0]))},
                   loop=False, length=0.8),
        "smash": A({"arm_r": keys((0, [0, 0, 0]), (0.4, [-160, 0, 10]), (0.6, [-30, 0, 0]), (1.0, [0, 0, 0])),
                    "arm_l": keys((0, [0, 0, 0]), (0.4, [-160, 0, -10]), (0.6, [-30, 0, 0]), (1.0, [0, 0, 0])),
                    "torso": keys((0, [0, 0, 0]), (0.4, [-12, 0, 0]), (0.6, [20, 0, 0]), (1.0, [0, 0, 0]))},
                   loop=False, length=1.0),
    }


ANIMATE_LAESTRYGONIAN = ["idle", {"walk": "q.modified_move_speed > 0.02"},
                         {"swing": "q.property('studio:anim') == 'swing'"},
                         {"smash": "q.property('studio:anim') == 'smash'"}]


def anims_child():
    return {"idle": human_idle(14), "walk": walk(220, leg=34, knee=40, arm=26, bob=0.5),
            "laugh": A({"chest": rot("math.sin(q.life_time*900)*3"), "head": rot("-10+math.sin(q.life_time*900)*4")}),
            "scream": A({"head": rot(-28), "arm_r": rot(-30, 0, 35), "arm_l": rot(-30, 0, -35)})}


ANIMATE_CHILD = ["idle", {"walk": "q.modified_move_speed > 0.02"},
                 {"laugh": "q.property('studio:anim') == 'laugh'"}, {"scream": "q.property('studio:anim') == 'scream'"}]


def anims_circe():
    # a floor-length gown: short steps keep the feet under the hem
    return {"idle": human_idle(8), "walk": walk(200, leg=9, knee=10, arm=12, bob=0.3),
            "mold": A({"arm_r": rot(-65, 10, 0), "arm_l": rot(-65, -10, 0),
                       "forearm_r": rot("-25+math.sin(q.life_time*720)*18"), "forearm_l": rot("-25-math.sin(q.life_time*720)*18"),
                       "hand_r": rot(0, 0, "math.sin(q.life_time*900)*20"), "hand_l": rot(0, 0, "-math.sin(q.life_time*900)*20"),
                       "head": rot(18)}),
            "yielded": A({"head": rot(10), "arm_r": rot(-10, 0, 6), "arm_l": rot(-10, 0, -6)})}


ANIMATE_CIRCE = ["idle", {"walk": "q.modified_move_speed > 0.02"},
                 {"mold": "q.property('studio:anim') == 'mold'"}, {"yielded": "q.property('studio:yielded')"}]


def anims_siren():
    """A mermaid reclining on the rocks: she sways as she sings, beckons with one hand, and her tail swishes."""
    b = {"chest": rot("math.sin(q.life_time*30)*2", 0, "math.sin(q.life_time*24)*3"),
         "head": rot("math.sin(q.life_time*20)*4", "math.sin(q.life_time*14)*12"),
         "arm_r": rot("math.sin(q.life_time*40)*10"), "forearm_r": rot("math.sin(q.life_time*40+50)*14")}
    for i in range(5):
        b[f"tail_{i}"] = rot(0, f"math.sin(q.life_time*45-{i * 35})*{3 + i * 2}", 0)
    b["tail_4"] = rot("math.sin(q.life_time*60)*12", "math.sin(q.life_time*45-140)*11", 0)
    return {"idle": A(b)}


def anims_simple_npc():
    return {"idle": human_idle(10), "walk": walk(200, leg=24, knee=26, arm=14, bob=0.3)}


ANIMATE_NPC = ["idle", {"walk": "q.modified_move_speed > 0.02"}]


def anims_athena():
    a = anims_simple_npc()
    a["walk"] = walk(200, leg=9, knee=10, arm=14, bob=0.3)          # floor-length gown: short steps
    a["bless"] = A({"arm_r": rot(-110, 0, 10), "forearm_r": rot(-20), "head": rot(8)})
    return a


ANIMATE_ATHENA = ANIMATE_NPC + [{"bless": "q.property('studio:anim') == 'bless'"}]


def anims_tiresias():
    return {"idle": A({"chest": rot("math.sin(q.life_time*30)*1.5"), "head": rot("math.sin(q.life_time*22)*4", "math.sin(q.life_time*11)*14")}),
            "rise": RISE, "sink": SINK,
            "speak": A({"arm_r": rot("-50+math.sin(q.life_time*80)*12", 0, 10), "head": rot("math.sin(q.life_time*120)*5")})}


ANIMATE_TIRESIAS = ["idle", {"rise": "q.property('studio:anim') == 'rise'"}, {"sink": "q.property('studio:anim') == 'sink'"},
                    {"speak": "q.property('studio:anim') == 'speak'"}]


def anims_shade():
    return {"idle": A({"chest": rot("6+math.sin(q.life_time*40)*2", 0, "math.sin(q.life_time*23)*3"),
                       "head": rot("math.sin(q.life_time*31)*5", "math.sin(q.life_time*19)*10"),
                       "arm_r": rot("-8+math.sin(q.life_time*35)*4"), "arm_l": rot("-8-math.sin(q.life_time*35)*4")}),
            "walk": walk(190, leg=26, knee=28, arm=10, bob=0.4),
            "rise": RISE, "sink": SINK,
            "grab": A({"arm_r": rot(-85, 0, 8), "arm_l": rot(-85, 0, -8), "head": rot(10)})}


ANIMATE_SHADE = ["idle", {"walk": "q.modified_move_speed > 0.02"},
                 {"rise": "q.property('studio:anim') == 'rise'"}, {"sink": "q.property('studio:anim') == 'sink'"},
                 {"grab": "q.property('studio:anim') == 'grab'"}]


def anims_scylla(necks=6, segs=8):
    idle, snatch = {}, {}
    for i in range(necks):
        for s in range(segs):
            idle[f"neck_{i}_{s}"] = rot(f"math.sin(q.life_time*60+{i * 61 + s * 37})*4", 0, f"math.cos(q.life_time*45+{i * 47 + s * 29})*3")
        idle[f"jaw_{i}"] = rot(f"math.max(0, math.sin(q.life_time*90+{i * 83}))*18")
        idle[f"head_{i}"] = rot(f"math.sin(q.life_time*70+{i * 50})*6", f"math.sin(q.life_time*35+{i * 70})*10")
        # 4.5 s, the script's snatch: lunge out at the deck, bite, then lift the victims high toward the cave
        t0 = 0.3 + i * 0.04
        snatch[f"neck_{i}_0"] = keys((0, [0, 0, 0]), (t0, [38, 0, 0]), (t0 + 0.9, [-12, 0, 0]), (4.5, [-12, 0, 0]))
        snatch[f"neck_{i}_3"] = keys((0, [0, 0, 0]), (t0, [-10, 0, 0]), (t0 + 0.9, [16, 0, 0]), (4.5, [16, 0, 0]))
        snatch[f"head_{i}"] = keys((0, [0, 0, 0]), (t0, [28, 0, 0]), (t0 + 0.9, [10, 0, 0]), (4.5, [10, 0, 0]))
        snatch[f"jaw_{i}"] = keys((0, [0, 0, 0]), (t0 - 0.1, [45, 0, 0]), (t0 + 0.1, [6, 0, 0]), (4.5, [6, 0, 0]))
    return {"idle": A(idle), "snatch": A(snatch, loop=False, length=4.5)}


ANIMATE_SCYLLA = ["idle", {"snatch": "q.property('studio:anim') == 'snatch'"}]


def anims_charybdis(rings=7):
    b = {"core": rot(0, "q.life_time*240", 0), "spiral": rot(0, "q.life_time*90", 0)}
    for k in range(rings):
        for sfx in ("a", "b"):
            b[f"ring{sfx}_{k}"] = rot(0, f"q.life_time*{60 + k * 30}", 0)
    return {"swirl": A(b)}


def anims_sister():
    return {"idle": A({"head": rot("math.sin(q.life_time*200)*6", "math.sin(q.life_time*90)*35"),
                       "tail": rot("math.sin(q.life_time*160)*8")})}


def anims_cattle():
    d = "q.modified_distance_moved*240"
    return {"idle": A({"head": rot("math.max(0, math.sin(q.life_time*12))*30", "math.sin(q.life_time*9)*10"),
                       "tail": rot(0, 0, "math.sin(q.life_time*140)*14")}),
            "walk": A({"leg_fl": rot(f"math.cos({d})*25"), "leg_hr": rot(f"math.cos({d})*25"),
                       "leg_fr": rot(f"-math.cos({d})*25"), "leg_hl": rot(f"-math.cos({d})*25")})}


ANIMATE_CATTLE = ["idle", {"walk": "q.modified_move_speed > 0.02"}]


def anims_boulder():
    return {"spin": A({"rock": rot("q.life_time*400", "q.life_time*250", 0)})}
