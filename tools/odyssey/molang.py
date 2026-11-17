"""A tiny Molang evaluator for the subset the animations use: sin/cos in degrees, max/min/abs, q.* variables."""
import math


def _molang(expr, q):
    if isinstance(expr, (int, float)):
        return float(expr)
    e = expr.replace("math.", "M_").replace("query.", "Q_").replace("q.", "Q_")
    env = {"M_sin": lambda d: math.sin(math.radians(d)), "M_cos": lambda d: math.cos(math.radians(d)),
           "M_max": max, "M_min": min, "M_abs": abs}
    env.update({f"Q_{k}": v for k, v in q.items()})
    return float(eval(e, {"__builtins__": {}}, env))


def _channel(ch, t, q):
    if isinstance(ch, list):
        return [_molang(v, q) for v in ch]
    frames = sorted((float(k), v) for k, v in ch.items())
    if t <= frames[0][0]:
        return [_molang(v, q) for v in frames[0][1]]
    for (t0, v0), (t1, v1) in zip(frames, frames[1:]):
        if t0 <= t <= t1:
            k = (t - t0) / (t1 - t0) if t1 > t0 else 0
            return [_molang(a, q) + (_molang(b, q) - _molang(a, q)) * k for a, b in zip(v0, v1)]
    return [_molang(v, q) for v in frames[-1][1]]


def pose(anim_defs, names, q, t=0.0):
    """Sum the named animations into a renderer pose {bone: {rotation, position}}."""
    out = {}
    for n in names:
        for bone, chans in anim_defs[n]["bones"].items():
            p = out.setdefault(bone, {"rotation": [0, 0, 0], "position": [0, 0, 0]})
            if "rotation" in chans:
                p["rotation"] = [a + b for a, b in zip(p["rotation"], _channel(chans["rotation"], t, q))]
            if "position" in chans:
                p["position"] = [a + b for a, b in zip(p["position"], _channel(chans["position"], t, q))]
    return out
