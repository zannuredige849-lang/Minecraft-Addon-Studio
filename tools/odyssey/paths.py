"""Sample where a creature's hands, weapon tip or mouth are during a move.

The script holds victims on these paths (a man carried to Polyphemus's mouth, a body on the glaive's point, a sailor
in a Scylla head) so what is shown by the animation and what the server does are the same motion. Positions are
relative to the creature's feet, in blocks, as [forward, up, right] (right = the creature's right).
"""
from . import fk
from .molang import pose as molang_pose


def _fk_pose(pz):
    return {b: tuple(v["rotation"]) + tuple(v["position"]) for b, v in pz.items()}


def sample(model, anims, anim, points, length, scale, step=0.1):
    """points: {label: [(bone, model_offset), ...]} (several entries are averaged). Returns {label: [[f, u, r], ...]}."""
    out = {label: [] for label in points}
    n = int(round(length / step)) + 1
    for i in range(n):
        t = min(length, i * step)
        q = {"life_time": t, "anim_time": t, "modified_distance_moved": 0.0, "modified_move_speed": 0.0}
        pz = molang_pose(anims, [anim], q, t)
        T = fk.world_transforms(model.bones, _fk_pose(pz))
        for label, parts in points.items():
            acc = [0.0, 0.0, 0.0]
            for bone, off in parts:
                R, t0 = T[bone]
                v = fk._mv(R, (-off[0], off[1], off[2]))
                for k in range(3):
                    acc[k] += t0[k] + v[k]
            w = [a / len(parts) for a in acc]
            out[label].append([round(-w[2] * scale / 16, 2), round(w[1] * scale / 16, 2), round(w[0] * scale / 16, 2)])
    return out
