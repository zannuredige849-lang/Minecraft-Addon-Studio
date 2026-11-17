"""Release validation for the behaviour and resource packs.

Checks every JSON file parses, manifest UUIDs are unique, and the cross references Minecraft resolves at load time:
geometry ids, texture files and their HD size, animations and their bones, animation controllers and the states they
move between, every sound cue and every sound id down to the .ogg file, render controllers and the bones they hide,
entity properties and enum values used in Molang, moves (animation, controller state, enum value and script data all
agree), the events and sounds the script uses, translate keys in every language, items, recipes, spawn rules, fogs and
the places of the map.

    python3 -m tools.odyssey.validate
"""
import glob
import json
import os
import re
import struct
import sys

from .moves import MOVES, enum_values, ticks

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BP = os.path.join(ROOT, "BP")
RP = os.path.join(ROOT, "RP")
VANILLA_MATERIALS = {"entity", "entity_alphatest", "entity_alphablend", "entity_emissive", "entity_emissive_alpha",
                     "entity_nocull", "entity_change_color", "entity_alphatest_change_color", "entity_custom",
                     "entity_alphatest_one_sided", "entity_emissive_alpha_one_sided", "entity_loyalty_rope",
                     "slime", "slime_outer"}
VANILLA_RENDER_CONTROLLERS = {"controller.render.default"}
VANILLA_ENTITIES = {"minecraft:sheep", "minecraft:pig"}
LANGUAGES = ("en_US", "ru_RU")

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    return struct.unpack(">II", head[16:24])


def rel(p):
    return os.path.relpath(p, ROOT)


def read_lang(pack, language):
    path = os.path.join(pack, "texts", f"{language}.lang")
    if not os.path.exists(path):
        err(f"{rel(path)} is missing")
        return {}
    out = {}
    for ln in open(path, encoding="utf-8").read().splitlines():
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            out[k.strip()] = v
    return out


def js_exports(text):
    names = set(re.findall(r"export\s+(?:function|class)\s+(\w+)", text))
    for m in re.finditer(r"export\s+(?:const|let|var)\s+([^;]+);", text):
        names.update(re.findall(r"(?:^|,)\s*([A-Za-z_$][\w$]*)\s*=", m.group(1)))
    return names


def check_scripts(bp_man, bp_entities, every_event, sound_ids, lang_keys, items):
    """Static checks over every module of the script."""
    files = sorted(glob.glob(os.path.join(BP, "scripts", "**", "*.js"), recursive=True))
    code = {f: open(f, encoding="utf-8").read() for f in files}
    code_files = [f for f in files if os.sep + "data" + os.sep not in f]
    exports = {f: js_exports(t) for f, t in code.items()}
    entry = os.path.join(BP, "scripts", "main.js")
    if entry not in code:
        err("BP/scripts/main.js is missing")
        return
    all_moves = {m for ms in MOVES.values() for m in ms}
    for f in code_files:
        text, where = code[f], rel(f)
        # imports resolve, and every imported name is exported
        for m in re.finditer(r"import\s*\{([^}]*)\}\s*from\s*\"(\.[^\"]+)\"", text):
            target = os.path.normpath(os.path.join(os.path.dirname(f), m.group(2)))
            if target not in code:
                err(f"{where}: imports {m.group(2)}, which does not exist")
                continue
            for n in [x.strip().split(" as ")[0].strip() for x in m.group(1).replace("\n", " ").split(",") if x.strip()]:
                if n not in exports[target]:
                    err(f"{where}: imports {n} from {m.group(2)}, which does not export it")
        for m in re.finditer(r"import \* as \w+ from \"(\.[^\"]+)\"", text):
            if os.path.normpath(os.path.join(os.path.dirname(f), m.group(1))) not in code:
                err(f"{where}: imports {m.group(1)}, which does not exist")
        for mod in re.findall(r'from "(@minecraft/[a-z-]+)"', text):
            if not any(d.get("module_name") == mod for d in bp_man.get("dependencies", [])):
                err(f"{where} imports {mod} but the BP manifest does not depend on it")
        # events it triggers exist on some entity
        for ev_name in set(re.findall(r'trigger\([^,()]+, "(studio:[^"]+)"\)', text)):
            if ev_name not in every_event:
                err(f"{where} triggers {ev_name}, which no entity defines")
        # moves it performs exist
        for mv in set(re.findall(r'perform\([^,()]+, "([a-z_]+)"', text)):
            if mv not in all_moves:
                err(f"{where} performs move '{mv}', which no creature has")
        for mv in set(re.findall(r'setProp\([^,()]+, "studio:anim", "([a-z_]+)"', text)):
            if mv != "none" and mv not in all_moves:
                err(f"{where} sets studio:anim to '{mv}', which no creature has")
        # sound ids and translate keys
        for s in set(re.findall(r'"(odyssey\.[a-z_]+\.[a-z_]+)"', text)):
            if s in lang_keys.get("en_US", {}) or s.startswith("odyssey.site."):
                continue
            if s not in sound_ids:
                err(f"{where}: '{s}' is neither a sound nor a translate key")
        for k in set(re.findall(r'"(odyssey\.[a-z_]+(?:\.[a-z_]+)+)"', text)):
            if k in sound_ids:
                continue
            for language in LANGUAGES:
                if k not in lang_keys[language] and not k.startswith("odyssey.site."):
                    err(f"{where}: translate key {k} is missing from {language}")
        # items, entities
        for item in set(re.findall(r'ItemStack\("([^"]+)"', text)):
            if item.startswith("studio:") and item not in items:
                err(f"{where}: ItemStack of undefined item {item}")
        for ident in set(re.findall(r'spawnEntity\(\s*"(studio:[a-z_]+)"', text)) \
                | set(re.findall(r'near\([^;]*?,\s*"(studio:[a-z_]+)"\s*\)', text)) \
                | set(re.findall(r'\btype: "(studio:[a-z_]+)"', text)):
            if ident not in bp_entities:
                err(f"{where}: spawns or queries unknown entity {ident}")
    # every export-level constant the entry file uses comes from an existing module
    sites = code.get(os.path.join(BP, "scripts", "data", "sites.js"), "")
    for s in re.findall(r"\"id\": \"([a-z]+)\"", sites):
        for k in (f"odyssey.site.{s}", f"odyssey.site.{s}.sub"):
            for language in LANGUAGES:
                if k not in lang_keys[language]:
                    err(f"place '{s}': translate key {k} is missing from {language}")
    # the generated move table is the one moves.py describes
    mjs = code.get(os.path.join(BP, "scripts", "data", "moves.js"), "")
    mm = re.search(r"export const MOVES = (\{.*?\n\});", mjs, re.S)
    if not mm:
        err("data/moves.js has no MOVES table: run python3 -m tools.odyssey.build")
    else:
        table = json.loads(mm.group(1))
        for ent in MOVES:
            if table.get(ent) != ticks(ent):
                err(f"data/moves.js is out of date for {ent}: run python3 -m tools.odyssey.build")
    return code


def main():
    # 1. every JSON parses
    data = {}
    for pack in (BP, RP):
        for path in sorted(glob.glob(os.path.join(pack, "**", "*.json"), recursive=True)):
            try:
                data[path] = load(path)
            except Exception as e:  # noqa: BLE001 - report any parse failure
                err(f"{rel(path)}: invalid JSON ({e})")
    print(f"parsed {len(data)} JSON files")

    # 2. manifest UUIDs unique
    uuids = {}
    for m in (os.path.join(BP, "manifest.json"), os.path.join(RP, "manifest.json")):
        man = data.get(m, {})
        for u in [man.get("header", {}).get("uuid")] + [mod.get("uuid") for mod in man.get("modules", [])]:
            if u in uuids:
                err(f"duplicate manifest uuid {u} ({rel(m)} and {uuids[u]})")
            uuids[u] = rel(m)
    bp_man, rp_man = data.get(os.path.join(BP, "manifest.json"), {}), data.get(os.path.join(RP, "manifest.json"), {})
    deps = {d.get("uuid") for d in bp_man.get("dependencies", []) if "uuid" in d}
    if rp_man.get("header", {}).get("uuid") not in deps:
        err("BP manifest does not depend on the RP header uuid")
    if bp_man.get("header", {}).get("version") != rp_man.get("header", {}).get("version"):
        err("BP and RP versions differ")

    # geometry bones and texture sizes
    geos = {}
    for path in glob.glob(os.path.join(RP, "models", "entity", "*.geo.json")):
        for g in data.get(path, {}).get("minecraft:geometry", []):
            d = g["description"]
            geos[d["identifier"]] = (d, {b["name"]: b for b in g.get("bones", [])}, path)
    anims = {}
    for path in glob.glob(os.path.join(RP, "animations", "*.json")):
        for name, a in data.get(path, {}).get("animations", {}).items():
            anims[name] = (a, path)
    controllers = {}
    for path in glob.glob(os.path.join(RP, "animation_controllers", "*.json")):
        for name, c in data.get(path, {}).get("animation_controllers", {}).items():
            controllers[name] = (c, path)
    rcs = {name: {} for name in VANILLA_RENDER_CONTROLLERS}
    for path in glob.glob(os.path.join(RP, "render_controllers", "*.json")):
        rcs.update(data.get(path, {}).get("render_controllers", {}))

    bp_entities = {}
    for path in glob.glob(os.path.join(BP, "entities", "*.json")):
        ent = data.get(path, {}).get("minecraft:entity")
        if ent:
            bp_entities[ent["description"]["identifier"]] = ent

    lang = {}
    for language in LANGUAGES:
        rp, bp = read_lang(RP, language), read_lang(BP, language)
        if rp != bp:
            err(f"{language}.lang differs between the packs")
        lang[language] = rp
    if set(lang["en_US"]) != set(lang["ru_RU"]):
        err("en_US and ru_RU have different keys: " + ", ".join(sorted(set(lang["en_US"]) ^ set(lang["ru_RU"]))[:6]))
    for pack in (BP, RP):
        listed = data.get(os.path.join(pack, "texts", "languages.json"))
        if listed != list(LANGUAGES):
            err(f"{rel(pack)}/texts/languages.json should list {list(LANGUAGES)}")
    lang_keys = lang
    en = lang["en_US"]

    # sounds: definitions, files
    sdefs = data.get(os.path.join(RP, "sounds", "sound_definitions.json"), {}).get("sound_definitions", {})
    used_files = set()
    for sid, sd in sdefs.items():
        for s in sd.get("sounds", []):
            f = os.path.join(RP, s["name"] + ".ogg")
            used_files.add(os.path.normpath(f))
            if not os.path.exists(f):
                err(f"sound {sid}: {s['name']}.ogg is missing")
            elif open(f, "rb").read(4) != b"OggS":
                err(f"sound {sid}: {s['name']}.ogg is not an Ogg file")
        if sd.get("max_distance", 0) <= sd.get("min_distance", 0):
            err(f"sound {sid}: max_distance must exceed min_distance")
    for f in glob.glob(os.path.join(RP, "sounds", "**", "*.ogg"), recursive=True):
        if os.path.normpath(f) not in used_files:
            err(f"{rel(f)} is not used by any sound definition")

    # 3. client entities
    cue_used = {}
    for path in sorted(glob.glob(os.path.join(RP, "entity", "*.entity.json"))):
        ce = data.get(path, {}).get("minecraft:client_entity", {}).get("description", {})
        ident = ce.get("identifier")
        short_id = (ident or "").replace("studio:", "")
        where = rel(path)
        if ident not in bp_entities:
            err(f"{where}: no behaviour entity {ident}")
        for mat in ce.get("materials", {}).values():
            if mat not in VANILLA_MATERIALS:
                err(f"{where}: unknown material {mat}")
        geo_bones = {}
        for key, gid in ce.get("geometry", {}).items():
            if gid not in geos:
                err(f"{where}: geometry {gid} not found")
                continue
            d, bones, gpath = geos[gid]
            geo_bones.update(bones)
            for tkey, tex in ce.get("textures", {}).items():
                png = os.path.join(RP, tex + ".png")
                if not os.path.exists(png):
                    err(f"{where}: texture {tex}.png missing")
                    continue
                w, h = png_size(png)
                tw, th = d["texture_width"], d["texture_height"]
                if w % tw or h % th or w // tw != h // th:
                    err(f"{where}: {tex}.png is {w}x{h}, not a whole multiple of {tw}x{th}")
        eanims = ce.get("animations", {})
        cue_map = ce.get("sound_effects", {})
        for sh, sid in cue_map.items():
            if sid not in sdefs:
                err(f"{where}: sound effect {sh} -> {sid}, which is not defined")
        cues = set()
        for short, aname in eanims.items():
            if aname.startswith("controller."):
                if aname not in controllers:
                    err(f"{where}: animation controller {aname} not defined")
                continue
            if aname not in anims:
                err(f"{where}: animation {aname} not defined")
                continue
            a, apath = anims[aname]
            for bone in a.get("bones", {}):
                if bone not in geo_bones:
                    err(f"{rel(apath)}: {aname} animates missing bone {bone}")
            length = a.get("animation_length")
            for t, v in a.get("sound_effects", {}).items():
                cues.add(v["effect"])
                if length and float(t) > length + 1e-6:
                    err(f"{aname}: sound cue {v['effect']} at {t}s is past the end of the animation ({length}s)")
        # controllers: states, transitions, animations, cues
        for short, aname in eanims.items():
            if not aname.startswith("controller.") or aname not in controllers:
                continue
            c, cpath = controllers[aname]
            states = c.get("states", {})
            if c.get("initial_state") not in states:
                err(f"{aname}: initial state missing")
            for sname, st in states.items():
                for entry in st.get("animations", []):
                    n = entry if isinstance(entry, str) else next(iter(entry))
                    if n not in eanims:
                        err(f"{aname}: state {sname} plays {n}, which {ident} does not declare")
                for tr in st.get("transitions", []):
                    if next(iter(tr)) not in states:
                        err(f"{aname}: state {sname} moves to unknown state {next(iter(tr))}")
                for se in st.get("sound_effects", []):
                    cues.add(se["effect"])
        for cue in cues:
            if cue not in cue_map:
                err(f"{where}: sound cue '{cue}' has no entry in sound_effects")
        cue_used[ident] = cues
        for sh in cue_map:
            if sh not in cues:
                err(f"{where}: sound effect '{sh}' is declared but never used")
        scripts = ce.get("scripts", {})
        for entry in scripts.get("animate", []):
            name = entry if isinstance(entry, str) else next(iter(entry))
            if name not in eanims:
                err(f"{where}: animate entry {name} has no animation")
        for rc in ce.get("render_controllers", []):
            name = rc if isinstance(rc, str) else next(iter(rc))
            if name not in rcs:
                err(f"{where}: render controller {name} not defined")
                continue
            ctl = rcs[name]
            for entry in ctl.get("part_visibility", []):
                for bone in entry:
                    if bone != "*" and bone not in geo_bones:
                        err(f"{name}: part_visibility names missing bone {bone} for {ident}")
            for arr in ctl.get("arrays", {}).get("textures", {}).values():
                for t in arr:
                    if t.split(".", 1)[1] not in ce.get("textures", {}):
                        err(f"{name}: {t} is not a texture of {ident}")
        # Molang properties must be declared, and compared enum values must exist
        props = bp_entities.get(ident, {}).get("description", {}).get("properties", {})
        text = json.dumps(ce) + json.dumps([anims[a][0] for a in eanims.values() if a in anims]) \
            + json.dumps([controllers[a][0] for a in eanims.values() if a in controllers])
        for m in re.finditer(r"q(?:uery)?\.property\(\s*'([^']+)'\s*\)\s*(==|!=)?\s*('([^']*)')?", text):
            pname, value = m.group(1), m.group(4)
            if pname not in props:
                err(f"{where}: Molang reads undeclared property {pname}")
            elif value is not None and value not in props[pname].get("values", []):
                err(f"{where}: {pname} compared with unknown value '{value}'")
        # moves: the enum, the animations, the controller states and the table all describe the same moves
        moves = MOVES.get(short_id, {})
        enum = props.get("studio:anim", {}).get("values")
        if moves or enum:
            if enum != enum_values(short_id):
                err(f"{ident}: studio:anim values {enum} differ from the moves {enum_values(short_id)}")
        for mv, spec in moves.items():
            a = anims.get(f"animation.{short_id}.{mv}")
            if not a:
                err(f"{ident}: move {mv} has no animation")
                continue
            if abs(a[0].get("animation_length", 0) - spec["length"]) > 1e-6 or a[0].get("loop"):
                err(f"{ident}: animation of move {mv} is not a one-shot of {spec['length']}s")
            ctrl = controllers.get(f"controller.animation.{short_id}.moves")
            if not ctrl or mv not in ctrl[0]["states"]:
                err(f"{ident}: no controller state for move {mv}")
            elif ctrl[0]["states"][mv]["animations"] != [mv]:
                err(f"{ident}: controller state {mv} should play only {mv}")
        if f"entity.{ident}.name" not in en:
            err(f"RP lang: missing entity.{ident}.name")
        if ce.get("spawn_egg") and bp_entities.get(ident, {}).get("description", {}).get("is_spawnable") \
                and f"item.spawn_egg.entity.{ident}.name" not in en:
            err(f"RP lang: missing item.spawn_egg.entity.{ident}.name")

    # 4. behaviour entities: events and interactions
    all_events = {}
    for ident, ent in bp_entities.items():
        all_events[ident] = set(ent.get("events", {}))
        groups = set(ent.get("component_groups", {}))
        props = ent["description"].get("properties", {})
        for ev_name, ev in ent.get("events", {}).items():
            blob = json.dumps(ev)
            for g in re.findall(r'"component_groups": \[([^\]]*)\]', blob):
                for name in re.findall(r'"([^"]+)"', g):
                    if name not in groups:
                        err(f"{ident}: event {ev_name} uses unknown group {name}")
            for m in re.finditer(r'"set_property": \{([^}]*)\}', blob):
                for k, v in re.findall(r'"([^"]+)": ("[^"]*"|true|false|-?\d+)', m.group(1)):
                    if k not in props:
                        err(f"{ident}: event {ev_name} sets undeclared property {k}")
                    elif props[k]["type"] == "enum" and v.strip('"') not in props[k]["values"]:
                        err(f"{ident}: event {ev_name} sets {k} to unknown value {v}")
        blob = json.dumps(ent.get("components", {})) + json.dumps(ent.get("component_groups", {}))
        for ev_name in re.findall(r'"event": "([^"]+)"', blob):
            if ev_name not in all_events[ident]:
                err(f"{ident}: interaction triggers undefined event {ev_name}")
        for key in re.findall(r'"interact_text": "([^"]+)"', blob):
            if key not in en:
                err(f"RP lang: missing {key}")

    # 5. items (needed by the script checks)
    item_tex = data.get(os.path.join(RP, "textures", "item_texture.json"), {}).get("texture_data", {})
    items = set()
    for path in glob.glob(os.path.join(BP, "items", "*.json")):
        it = data.get(path, {}).get("minecraft:item", {})
        ident = it.get("description", {}).get("identifier")
        items.add(ident)
        icon = it.get("components", {}).get("minecraft:icon")
        key = icon.get("textures", {}).get("default") if isinstance(icon, dict) else icon
        if not isinstance(icon, dict):
            err(f"{rel(path)}: minecraft:icon should use the object form")
        if key not in item_tex:
            err(f"{rel(path)}: icon {key} not in item_texture.json")
        else:
            tex = item_tex[key]["textures"]
            if not os.path.exists(os.path.join(RP, tex + ".png")):
                err(f"item_texture.json: {tex}.png missing")
        if f"item.{ident}.name" not in en:
            err(f"RP lang: missing item.{ident}.name")
    for path in glob.glob(os.path.join(BP, "recipes", "*.json")):
        blob = json.dumps(data.get(path, {}))
        for ident in re.findall(r'"item": "(studio:[a-z_]+)"', blob):
            if ident not in items:
                err(f"{rel(path)}: unknown item {ident}")
    for path in glob.glob(os.path.join(BP, "spawn_rules", "*.json")):
        ident = data.get(path, {}).get("minecraft:spawn_rules", {}).get("description", {}).get("identifier")
        if ident not in bp_entities:
            err(f"{rel(path)}: spawn rule for unknown entity {ident}")

    # 6. sounds.json entity mappings
    sounds = data.get(os.path.join(RP, "sounds.json"), {})
    for ident, spec in sounds.get("entity_sounds", {}).get("entities", {}).items():
        if ident not in bp_entities:
            err(f"sounds.json: sounds for unknown entity {ident}")
        for ev, sid in spec.get("events", {}).items():
            sid = sid if isinstance(sid, str) else sid.get("sound")
            if sid.startswith("odyssey.") and sid not in sdefs:
                err(f"sounds.json: {ident} {ev} -> {sid}, which is not defined")

    # 7. the script
    every_event = set().union(*all_events.values())
    code = check_scripts(bp_man, bp_entities, every_event, set(sdefs), lang_keys, items)

    # 8. fogs and the places of the map
    fogs = {}
    for path in glob.glob(os.path.join(RP, "fogs", "*.json")):
        d = data.get(path, {}).get("minecraft:fog_settings", {})
        fogs[d.get("description", {}).get("identifier")] = d
    sites_js = (code or {}).get(os.path.join(BP, "scripts", "data", "sites.js"), "")
    for fid in re.findall(r"\"fog\": \"([a-z]+)\"", sites_js):
        if f"odyssey:{fid}" not in fogs:
            err(f"a place uses fog {fid}, which has no file in RP/fogs")
    for ident in set(re.findall(r'\["((?:studio|minecraft):[a-z_]+)", -?\d+, -?\d+\]', sites_js)):
        if ident not in bp_entities and ident not in VANILLA_ENTITIES:
            err(f"a place spawns {ident}, which is not defined")

    if errors:
        print(f"{len(errors)} problem(s):")
        for e in errors:
            print("  -", e)
        return 1
    n_cues = sum(len(c) for c in cue_used.values())
    print(f"OK: {len(bp_entities)} entities, {len(geos)} geometries, {len(anims)} animations, {len(controllers)} controllers, "
          f"{n_cues} sound cues, {len(sdefs)} sounds, {len(items)} items, {len(uuids)} unique manifest uuids")
    return 0


if __name__ == "__main__":
    sys.exit(main())
