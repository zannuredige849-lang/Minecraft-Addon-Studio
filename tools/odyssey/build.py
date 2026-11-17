"""Generate the whole Odyssey add-on: models, textures, animations, entities, items, spawn rules, sounds, lang.

Usage (from the repository root):  python3 -m tools.odyssey.build [--previews DIR]
Every model is grounded and checked; the build stops on floating parts or detached joints.
"""
import json
import math
import os
import sys

from . import anims as AN
from . import bedrock as BR
from . import fk
from .c_animals import build_cattle, build_sister
from .c_laestrygonian import GROUND_IGNORE as LAE_IGNORE, build as build_lae, build_child
from .c_misc import build_boulder, build_horse, HORSE_TARGET_BLOCKS
from .c_people import build_athena, build_calypso, build_circe, build_shade, build_siren, build_tiresias
from .c_polyphemus import TARGET_HEIGHT_BLOCKS as CYCLOPS_BLOCKS, build as build_cyclops
from .c_sea import build_charybdis, build_scylla
from .core import png_bytes

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _first(x):
    return x[0] if isinstance(x, tuple) else x


# name: builder, scale (float | ("height", blocks) | None), ground_ignore, ground, textures, rc, anims, animate,
#       egg, material, behaviour, spawn egg shown
SPECS = {
    "cyclops": dict(build=build_cyclops, scale=("height", CYCLOPS_BLOCKS), textures={"default": {}, "blinded": {"blind": True}},
                    rc="controller.render.studio_cyclops", anims=AN.anims_cyclops, animate=AN.ANIMATE_CYCLOPS,
                    egg=("#B0ACA4", "#5C5650"), bp=BR.bp_cyclops),
    "laestrygonian": dict(build=build_lae, scale=("height", 4.0), ignore=LAE_IGNORE, textures={"default": {}},
                          rc="controller.render.studio_laestrygonian", anims=AN.anims_laestrygonian,
                          animate=AN.ANIMATE_LAESTRYGONIAN, egg=("#B2B6BE", "#4A4E58"), bp=BR.bp_laestrygonian),
    "laestrygonian_child": dict(build=build_child, anims=AN.anims_child, animate=AN.ANIMATE_CHILD,
                                egg=("#60483A", "#B2B6BE"), bp=BR.bp_child),
    "circe": dict(build=build_circe, anims=AN.anims_circe, animate=AN.ANIMATE_CIRCE, egg=("#62584A", "#968F86"), bp=BR.bp_circe),
    "circe_sister": dict(build=build_sister, anims=AN.anims_sister, animate=["idle"], egg=None, bp=BR.bp_sister),
    "siren": dict(build=build_siren, anims=AN.anims_siren, animate=["idle"], egg=("#C8C8C6", "#24222A"),
                  material="entity_alphablend", bp=BR.bp_siren),
    "scylla": dict(build=build_scylla, scale=3.0, anims=AN.anims_scylla, animate=AN.ANIMATE_SCYLLA,
                   egg=("#70604E", "#8A5446"), bp=BR.bp_scylla),
    "charybdis": dict(build=build_charybdis, scale=3.0, ground=False, anims=AN.anims_charybdis, animate=["swirl"],
                      egg=("#1C4858", "#E2EEEE"), material="entity_alphablend", bp=BR.bp_charybdis),
    "shade": dict(build=build_shade, textures={"default": {}, "agamemnon": {"agamemnon": True}, "sinon": {"sinon": True}},
                  rc="controller.render.studio_shade", anims=AN.anims_shade, animate=AN.ANIMATE_SHADE,
                  egg=("#3A3634", "#8A6A44"), bp=BR.bp_shade),
    "tiresias": dict(build=build_tiresias, anims=AN.anims_tiresias, animate=AN.ANIMATE_TIRESIAS,
                     egg=("#3C3832", "#A8A49C"), bp=BR.bp_tiresias),
    "sun_cattle": dict(build=build_cattle, anims=AN.anims_cattle, animate=AN.ANIMATE_CATTLE, egg=("#D6BA8E", "#F0E6CC"),
                       bp=BR.bp_cattle),
    "calypso": dict(build=build_calypso, anims=AN.anims_simple_npc, animate=AN.ANIMATE_NPC, egg=("#E8E2D2", "#E0CC9E"),
                    bp=BR.bp_calypso),
    "athena": dict(build=build_athena, anims=AN.anims_athena, animate=AN.ANIMATE_ATHENA, egg=("#EEECE6", "#96684E"),
                   bp=BR.bp_athena),
    "trojan_horse": dict(build=build_horse, scale=("height", HORSE_TARGET_BLOCKS), anims=None, animate=None,
                         egg=("#96704A", "#5A4028"), bp=BR.bp_horse),
    "boulder": dict(build=build_boulder, ground=False, anims=AN.anims_boulder, animate=["spin"], egg=None, bp=BR.bp_boulder),
}

OBSOLETE = [
    "BP/items/maronian_wine.json", "BP/items/moly.json", "BP/items/olive_stake.json", "BP/items/circe_feast.json",
    "BP/recipes/maronian_wine.json", "BP/recipes/moly.json", "BP/recipes/olive_stake.json",
    "RP/textures/items/maronian_wine.png", "RP/textures/items/moly.png", "RP/textures/items/olive_stake.png",
    "RP/textures/items/circe_feast.png", "RP/textures/entity/siren_dusk.png", "RP/textures/entity/siren_ash.png",
    "RP/textures/entity/siren_sea.png", "RP/textures/entity/cyclops_blind.png", "BP/spawn_rules/cyclops.json",
    "BP/spawn_rules/scylla.json", "BP/loot_tables/entities/cyclops.json", "BP/loot_tables/entities/siren.json",
    "BP/loot_tables/entities/circe.json", "BP/loot_tables/entities/scylla.json", "BP/loot_tables/entities/laestrygonian.json",
    "RP/render_controllers/odyssey.render_controllers.json",
]


def write_json(rel, data):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def write_png(rel, rows):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png_bytes(rows))


# ------------------------------------------------------------------ Molang preview evaluator
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


# ------------------------------------------------------------------ main
def build_all(preview_dir=None, only=None):
    report = {}
    errors = []
    for name, sp in SPECS.items():
        if only and name not in only:
            continue
        m = _first(sp["build"]())
        if sp.get("ground", True):
            fk.ground(m, ignore=sp.get("ignore", ()))
        floating = fk.connectivity(m, ignore_tags=("net",))
        gaps = fk.joint_gaps(m, tol=2.0)
        if floating:
            errors.append(f"{name}: {len(floating)} floating part group(s): {floating[0][:2]}")
        if gaps:
            errors.append(f"{name}: detached joints {gaps}")
        zf = fk.zfight(m)
        skip = fk.descendants(m, sp.get("ignore", ()))
        boxes = [b for b in fk.world_boxes(m) if b[1] not in skip]
        mn = tuple(min(b[2][i] for b in boxes) for i in range(3))
        mx = tuple(max(b[3][i] for b in boxes) for i in range(3))
        scale = sp.get("scale")
        if isinstance(scale, tuple):
            scale = round(scale[1] * 16 / (mx[1] - max(0.0, mn[1])), 4)
        s = scale or 1.0
        all_mn, all_mx = fk.extents(m)
        bw = round(max(all_mx[0] - all_mn[0], all_mx[2] - all_mn[2]) * s / 16 + 1.0, 2)
        bh = round((all_mx[1] - all_mn[1]) * s / 16 + 1.0, 2)
        boff = round((all_mx[1] + all_mn[1]) / 2 * s / 16, 2)
        m.pack()
        if fk.uv_overlaps(m):
            errors.append(f"{name}: UV overlaps")
        tex_paths = {}
        for key, variant in sp.get("textures", {"default": {}}).items():
            img = m.paint(variant)
            clear = fk.transparent_faces(m, img, allowed_tags=("net",))
            if clear:
                errors.append(f"{name}/{key}: fully transparent faces {clear[:4]}")
            fname = name if key == "default" else f"{name}_{key}"
            write_png(f"RP/textures/entity/{fname}.png", img)
            tex_paths[key] = f"textures/entity/{fname}"
        write_json(f"RP/models/entity/{name}.geo.json", m.geometry(bw, bh, boff))
        anim_defs = sp["anims"]() if sp.get("anims") else {}
        if anim_defs:
            write_json(f"RP/animations/{name}.animation.json", {
                "format_version": "1.10.0", "animations": {f"animation.{name}.{k}": v for k, v in anim_defs.items()}})
        write_json(f"RP/entity/{name}.entity.json", BR.client_entity(
            name, tex_paths, sp.get("rc", "controller.render.default"), list(anim_defs), sp.get("animate"),
            sp.get("egg"), sp.get("material", "entity_alphatest"), scale))
        write_json(f"BP/entities/{name}.json", sp["bp"]())
        height_blocks = (mx[1] - max(0.0, mn[1])) * s / 16
        report[name] = dict(bones=len(m.bones), cubes=len(m.cubes), atlas=f"{int(m.tw * m.D)}x{int(m.th * m.D)}",
                            height=round(height_blocks, 2), scale=scale, zfix=len(zf))
        if preview_dir:
            os.makedirs(preview_dir, exist_ok=True)
            with open(os.path.join(preview_dir, f"{name}.geo.json"), "w") as f:
                json.dump(m.geometry(bw, bh, boff), f)
            with open(os.path.join(preview_dir, f"{name}.anims.json"), "w") as f:
                json.dump(anim_defs, f)
        if not anim_defs:
            p = os.path.join(ROOT, f"RP/animations/{name}.animation.json")
            if os.path.exists(p):
                os.remove(p)

    if only:
        return report, errors
    write_json("RP/render_controllers/studio.render_controllers.json", BR.RENDER_CONTROLLERS)
    write_json("RP/sounds.json", BR.SOUNDS)
    tex = {}
    for name, (pal, rows) in BR.ITEM_ART.items():
        write_png(f"RP/textures/items/{name}.png", [[(pal[ch] + (255,)) if ch != "." else (0, 0, 0, 0) for ch in r] for r in rows])
        tex[f"studio_{name}"] = {"textures": f"textures/items/{name}"}
    write_json("RP/textures/item_texture.json", {"resource_pack_name": "odyssey", "texture_name": "atlas.items", "texture_data": tex})
    for name, spec in BR.ITEMS.items():
        write_json(f"BP/items/{name}.json", BR.item_json(name, spec))
    for name, data in BR.RECIPES.items():
        write_json(f"BP/recipes/{name}.json", data)
    for name, data in BR.SPAWN_RULES.items():
        write_json(f"BP/spawn_rules/{name}.json", data)
    for pack in ("BP", "RP"):
        path = os.path.join(ROOT, pack, "texts", "en_US.lang")
        keep = [l for l in open(path).read().splitlines() if "pixel_slime" in l]
        with open(path, "w") as f:
            f.write("\n".join(keep + [f"{k}={v}" for k, v in BR.LANG]) + "\n")
    for rel in OBSOLETE:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            os.remove(p)
    lt = os.path.join(ROOT, "BP/loot_tables/entities")
    if os.path.isdir(lt) and not os.listdir(lt):
        os.rmdir(lt)
        if not os.listdir(os.path.dirname(lt)):
            os.rmdir(os.path.dirname(lt))
    return report, errors


if __name__ == "__main__":
    prev = None
    if "--previews" in sys.argv:
        prev = sys.argv[sys.argv.index("--previews") + 1]
    only = [a for a in sys.argv[1:] if not a.startswith("--") and a != prev] or None
    rep, errs = build_all(prev, only)
    for n, r in rep.items():
        print(f"{n:20s} bones={r['bones']:3d} cubes={r['cubes']:4d} atlas={r['atlas']:>9s} height={r['height']:6.2f} blocks"
              f" scale={r['scale']} zfix={r['zfix']}")
    if errs:
        print("\nERRORS:")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print("\nall models passed checks")
