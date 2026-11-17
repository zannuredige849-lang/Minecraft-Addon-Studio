"""Generate the whole Odyssey add-on: models, textures, animations, animation controllers, entities, items, spawn
rules, sounds, text and the data tables the script imports.

Usage (from the repository root):  python3 -m tools.odyssey.build [--previews DIR] [--no-sound] [names...]
Every model is grounded and checked; the build stops on floating parts or detached joints.
"""
import json
import math
import os
import sys

from . import anims as AN
from . import bedrock as BR
from . import fk
from . import lang as LG
from . import paths
from . import world_plan as WP
from .c_animals import build_cattle, build_sister
from .c_laestrygonian import GROUND_IGNORE as LAE_IGNORE, build as build_lae, build_child
from .c_misc import build_boulder, build_horse, HORSE_TARGET_BLOCKS
from .c_people import build_athena, build_calypso, build_circe, build_shade, build_siren, build_tiresias
from .c_polyphemus import TARGET_HEIGHT_BLOCKS as CYCLOPS_BLOCKS, build as build_cyclops
from .c_sea import build_charybdis, build_scylla
from .core import png_bytes
from .moves import MOVES, ticks

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _first(x):
    return x[0] if isinstance(x, tuple) else x


# name: builder, scale (float | ("height", blocks) | None), ground_ignore, textures, render controller, animations,
#       base animations (the controller's default state), gait constant for footsteps (None = silent), spawn egg colours
SPECS = {
    "cyclops": dict(build=build_cyclops, scale=("height", CYCLOPS_BLOCKS), textures={"default": {}, "blinded": {"blind": True}},
                    rc="controller.render.studio_cyclops", anims=AN.anims_cyclops, animate=AN.ANIMATE_CYCLOPS, steps=49,
                    egg=("#B0ACA4", "#5C5650"), bp=BR.bp_cyclops),
    "laestrygonian": dict(build=build_lae, scale=("height", 4.0), ignore=LAE_IGNORE, textures={"default": {}},
                          rc="controller.render.studio_laestrygonian", anims=AN.anims_laestrygonian,
                          animate=AN.ANIMATE_LAESTRYGONIAN, steps=90, egg=("#B2B6BE", "#4A4E58"), bp=BR.bp_laestrygonian),
    "laestrygonian_child": dict(build=build_child, anims=AN.anims_child, animate=AN.ANIMATE_CHILD, steps=220,
                                egg=("#60483A", "#B2B6BE"), bp=BR.bp_child),
    "circe": dict(build=build_circe, anims=AN.anims_circe, animate=AN.ANIMATE_CIRCE, steps=200,
                  egg=("#62584A", "#968F86"), bp=BR.bp_circe),
    "circe_sister": dict(build=build_sister, anims=AN.anims_sister, animate=["idle"], egg=None, bp=BR.bp_sister),
    "siren": dict(build=build_siren, anims=AN.anims_siren, animate=AN.ANIMATE_SIREN, egg=("#C8CCD0", "#3E5254"),
                  bp=BR.bp_siren),
    "scylla": dict(build=build_scylla, scale=3.0, anims=AN.anims_scylla, animate=AN.ANIMATE_SCYLLA,
                   egg=("#70604E", "#8A5446"), bp=BR.bp_scylla),
    "charybdis": dict(build=build_charybdis, scale=3.0, ground=False, anims=AN.anims_charybdis,
                      animate=AN.ANIMATE_CHARYBDIS, egg=("#1C4858", "#E2EEEE"), material="entity_alphablend",
                      bp=BR.bp_charybdis),
    "shade": dict(build=build_shade, textures={"default": {}, "agamemnon": {"agamemnon": True}, "sinon": {"sinon": True}},
                  rc="controller.render.studio_shade", anims=AN.anims_shade, animate=AN.ANIMATE_SHADE,
                  egg=("#3A3634", "#8A6A44"), bp=BR.bp_shade),
    "tiresias": dict(build=build_tiresias, anims=AN.anims_tiresias, animate=AN.ANIMATE_TIRESIAS,
                     egg=("#3C3832", "#A8A49C"), bp=BR.bp_tiresias),
    "sun_cattle": dict(build=build_cattle, anims=AN.anims_cattle, animate=AN.ANIMATE_CATTLE, steps=240,
                       egg=("#D6BA8E", "#F0E6CC"), bp=BR.bp_cattle),
    "calypso": dict(build=build_calypso, anims=AN.anims_calypso, animate=AN.ANIMATE_NPC, steps=200,
                    egg=("#E8E2D2", "#E0CC9E"), bp=BR.bp_calypso),
    "athena": dict(build=build_athena, anims=AN.anims_athena, animate=AN.ANIMATE_NPC, steps=200,
                   egg=("#EEECE6", "#96684E"), bp=BR.bp_athena),
    "trojan_horse": dict(build=build_horse, scale=("height", HORSE_TARGET_BLOCKS), anims=AN.anims_horse,
                         animate=AN.ANIMATE_HORSE, egg=("#96704A", "#5A4028"), bp=BR.bp_horse),
    "boulder": dict(build=build_boulder, ground=False, anims=AN.anims_boulder, animate=["spin"], egg=None,
                    bp=BR.bp_boulder),
}

# Where a carried body, a thrown rock or a weapon point is during a move: bone and an offset from its pivot (model
# units). Sampled from the animation itself, so the script holds a victim exactly where the animation shows it.
_SCYLLA_MOUTH = {f"head{i}": [(f"head_{i}", (0, -1.5, -6))] for i in range(6)}
POINTS = {
    "cyclops": {
        "devour": {"hand": [("hand_r", (0, -5.5, -1.4))], "mouth": [("jaw", (0, -1.2, -3.2))]},
        "throw": {"hand": [("hand_r", (0, -4, -1)), ("hand_l", (0, -4, -1))]},
    },
    "laestrygonian": {"impale": {"point": [("glaive", (0, 55, 0))]}},
    "scylla": {"snatch": _SCYLLA_MOUTH, "devour": _SCYLLA_MOUTH},
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
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_png(rel, rows):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png_bytes(rows))


def write_text(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


from .molang import pose  # noqa: E402  (re-exported: the previews and pose checks import it from here)


def cue_names(anim_defs):
    """Every sound cue (short name) the animations of an entity fire."""
    out = set()
    for a in anim_defs.values():
        out.update(v["effect"] for v in a.get("sound_effects", {}).values())
    return out


def _controllers_json(name, sp):
    """moves + steps controllers of an entity: (file content or None, controller short names)."""
    ctrls = {}
    if name in MOVES:
        ctrls.update(AN.moves_controller(name, sp["animate"])["animation_controllers"])
    if sp.get("steps"):
        ctrls.update(AN.steps_controller(name, sp["steps"])["animation_controllers"])
    if not ctrls:
        return None, ()
    return {"format_version": "1.10.0", "animation_controllers": ctrls}, tuple(k.rsplit(".", 1)[1] for k in ctrls)


# ------------------------------------------------------------------ main
def build_all(preview_dir=None, only=None, sound=True):
    report = {}
    errors = []
    sounds_needed = {}                    # entity -> set of short names (animation cues, steps, engine events)
    move_data, path_data, size_data = {}, {}, {}
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
        anim_defs = sp["anims"]()
        write_json(f"RP/animations/{name}.animation.json", {
            "format_version": "1.10.0", "animations": {f"animation.{name}.{k}": v for k, v in anim_defs.items()}})
        ctrl_doc, ctrl_names = _controllers_json(name, sp)
        ctrl_path = f"RP/animation_controllers/{name}.animation_controller.json"
        if ctrl_doc:
            write_json(ctrl_path, ctrl_doc)
        elif os.path.exists(os.path.join(ROOT, ctrl_path)):
            os.remove(os.path.join(ROOT, ctrl_path))
        shorts = cue_names(anim_defs)
        if sp.get("steps"):
            shorts.add("step")
        for k, v in (BR.SOUND_EVENTS.get(name) or {}).items():
            sounds_needed.setdefault(name, set()).add(v)
        sounds_needed.setdefault(name, set()).update(shorts)
        write_json(f"RP/entity/{name}.entity.json", BR.client_entity(
            name, tex_paths, sp.get("rc", "controller.render.default"), list(anim_defs), sp.get("animate"),
            sp.get("egg"), sp.get("material", "entity_alphatest"), scale, controllers=ctrl_names,
            sound_shorts=shorts))
        write_json(f"BP/entities/{name}.json", sp["bp"]())
        for move, points in POINTS.get(name, {}).items():
            path_data[f"{name}.{move}"] = paths.sample(m, anim_defs, move, points, MOVES[name][move]["length"], s)
        if name in MOVES:
            move_data[name] = ticks(name)
        height_blocks = (mx[1] - max(0.0, mn[1])) * s / 16
        size_data[name] = round(height_blocks, 2)
        report[name] = dict(bones=len(m.bones), cubes=len(m.cubes), atlas=f"{int(m.tw * m.D)}x{int(m.th * m.D)}",
                            height=round(height_blocks, 2), scale=scale, zfix=len(zf))
        if preview_dir:
            os.makedirs(preview_dir, exist_ok=True)
            with open(os.path.join(preview_dir, f"{name}.geo.json"), "w") as f:
                json.dump(m.geometry(bw, bh, boff), f)
            with open(os.path.join(preview_dir, f"{name}.anims.json"), "w") as f:
                json.dump(anim_defs, f)

    if only:
        return report, errors
    write_json("RP/render_controllers/studio.render_controllers.json", BR.RENDER_CONTROLLERS)
    write_json("RP/sounds.json", BR.entity_sounds())
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
    languages = ["en_US", "ru_RU"]
    for pack in ("BP", "RP"):
        write_json(f"{pack}/texts/languages.json", languages)
        for language in languages:
            write_text(f"{pack}/texts/{language}.lang", "\n".join(f"{k}={v}" for k, v in LG.texts(language)) + "\n")
    # data the script imports: every move in ticks, and the sampled carry paths (blocks: [forward, up, right],
    # one sample every 2 ticks from tick 0)
    js = ["// Generated by tools/odyssey/build.py - do not edit.",
          "// MOVES: every move of every creature in game ticks (len = total length). The client plays the same animation",
          "// and its sound cues from the same numbers. PATHS: where a hand, mouth or weapon point is during a move,",
          "// relative to the creature's feet in blocks as [forward, up, right], one sample every 2 ticks.",
          "export const MOVES = " + json.dumps(move_data, indent=1) + ";",
          "export const PATHS = " + json.dumps(path_data, separators=(",", ":")) + ";",
          "export const HEIGHT = " + json.dumps(size_data) + ";", ""]
    write_text("BP/scripts/data/moves.js", "\n".join(js))
    sites = {"MARKER": WP.MARKER, "SITES": [dict(id=x["id"], x=x["x"], z=x["z"], r=x["r"], y=x["y"], fog=x["fog"],
                                                 creatures=[list(c) for c in x["creatures"]]) for x in WP.SITES],
             "FOGS": {k: k for k in WP.FOGS}, "RESPAWN_TICKS": WP.RESPAWN_TICKS}
    write_text("BP/scripts/data/sites.js", "// Generated by tools/odyssey/build.py from world_plan.py - do not edit.\n" + "\n".join(
        f"export const {k} = {json.dumps(v)};" for k, v in sites.items()) + "\n")
    for fid, (start, end, color, water) in WP.FOGS.items():
        write_json(f"RP/fogs/odyssey_{fid}.json", {"format_version": "1.16.100", "minecraft:fog_settings": {
            "description": {"identifier": f"odyssey:{fid}"},
            "distance": {"air": {"fog_start": start, "fog_end": end, "fog_color": color, "render_distance_type": "fixed"},
                         "water": {"fog_start": 0, "fog_end": 14, "fog_color": water, "render_distance_type": "fixed"}}}})
    if sound:
        from . import sfx
        for ent, shorts in sorted(sounds_needed.items()):
            for sh in sorted(shorts):
                if f"{ent}.{sh}" not in sfx.RECIPES:
                    errors.append(f"sound odyssey.{ent}.{sh} (used by the animations) has no recipe in sfx.py")
        sfx.write_all(ROOT)
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
    rep, errs = build_all(prev, only, sound="--no-sound" not in sys.argv)
    for n, r in rep.items():
        print(f"{n:20s} bones={r['bones']:3d} cubes={r['cubes']:4d} atlas={r['atlas']:>9s} height={r['height']:6.2f} blocks"
              f" scale={r['scale']} zfix={r['zfix']}")
    if errs:
        print("\nERRORS:")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print("\nall models passed checks")
