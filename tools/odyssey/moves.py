"""Single source of truth for every creature move: its length and key moments, in seconds.

anims.py builds the keyframes from these numbers, bedrock.py turns the names into the `studio:anim` enum values,
and build.py exports them (as ticks, with the sampled hand / mouth paths) to BP/scripts/data/moves.js. Animation,
sound cue and script effect therefore always land on the same frame.

A move is a one-shot: the script sets `studio:anim` to its name, the client animation controller enters that move's
state (restarting the animation from 0), and the script clears the property when the move is over.
"""

MOVES = {
    "cyclops": {
        # reach down, scoop a man up, lift him to the mouth, two bites, toss him aside
        "devour": dict(length=3.2, grab=0.6, bite=(1.9, 2.35), release=2.95),
        # a sideways kick: "kicked Elpenor who died on the spot"
        "kick": dict(length=1.5, hit=0.62),
        # raise a foot and bring it down on whatever is underfoot
        "stomp": dict(length=1.7, hit=0.72),
        # pick up a rock, raise it overhead, hurl it at the ship
        "throw": dict(length=2.1, pick=0.55, release=1.3),
        # blinded: the cry to Poseidon
        "cry": dict(length=5.0),
        # the gentle shepherd stroking his flock
        "tend": dict(length=3.4, stroke=1.5),
        # sit up out of sleep
        "wake": dict(length=2.4),
    },
    "laestrygonian": {
        "slash": dict(length=1.2, hit=0.62),                 # sword: a wide horizontal sweep
        "impale": dict(length=1.6, hit=0.56, fling=1.1),     # glaive: stab, lift, fling into the trees
        "crush": dict(length=1.8, hit=0.88),                 # mace: overhead slam, shockwave
        "cleave": dict(length=1.6, hit=(0.45, 0.95)),        # curved blade: a double sweep
        "smash": dict(length=1.8, hit=0.88),                 # any weapon: chop a ship to pieces
    },
    "laestrygonian_child": {
        "laugh": dict(length=1.8),
        "scream": dict(length=2.0),
    },
    "circe": {
        "serve": dict(length=2.4, give=1.3),
        "scream": dict(length=1.8),
        "mold": dict(length=2.4, finish=2.2),
        "counsel": dict(length=2.8),
    },
    "circe_sister": {
        "flap": dict(length=1.4),
    },
    "siren": {
        "sing": dict(length=8.6),
        "beckon": dict(length=2.2),
        "drag": dict(length=1.8, grab=0.6),
    },
    "scylla": {
        "lunge": dict(length=1.2),
        "snatch": dict(length=1.4, bite=0.5),
        "devour": dict(length=2.6, bite=(0.5, 1.2, 1.9)),
        "rend": dict(length=1.9, hit=0.7),
        "recoil": dict(length=1.3),
    },
    "charybdis": {
        "surge": dict(length=6.0),
        "gulp": dict(length=1.6, gulp=0.45),
    },
    "tiresias": {
        "rise": dict(length=1.8),
        "speak": dict(length=3.4),
        "sink": dict(length=2.0),
    },
    "shade": {
        "rise": dict(length=1.8),
        "sink": dict(length=2.0),
        "speak_sinon": dict(length=3.0),
        "speak_agamemnon": dict(length=3.0),
        "grasp": dict(length=1.8, hit=0.8),
    },
    "calypso": {
        "offer": dict(length=2.4, give=1.2),
        "embrace": dict(length=2.8, hug=1.1),
    },
    "athena": {
        "bless": dict(length=2.4, give=1.0),
        "appear": dict(length=1.6),
        "vanish": dict(length=1.6),
    },
    "sun_cattle": {
        "graze": dict(length=3.4),
        "low": dict(length=1.8),
    },
    "trojan_horse": {
        "hatch": dict(length=2.0, open=1.0),
        "sally": dict(length=2.8, eject=1.1),
    },
}


def enum_values(entity):
    """Values of the `studio:anim` property for an entity."""
    return ["none"] + list(MOVES.get(entity, {}))


def ticks(entity):
    """The moves of an entity with every time converted to game ticks (20 per second)."""
    out = {}
    for name, spec in MOVES.get(entity, {}).items():
        d = {}
        for k, v in spec.items():
            key = "len" if k == "length" else k
            d[key] = [round(x * 20) for x in v] if isinstance(v, tuple) else round(v * 20)
        out[name] = d
    return out
