"""Release validation for the behaviour and resource packs.

Checks every JSON file parses, manifest UUIDs are unique, and the cross references Minecraft resolves at load time:
geometry ids, texture files and their HD size, animations and their bones, animate entries, render controllers and
the bones they hide, entity properties and enum values used in Molang, events the script triggers, items, recipes,
spawn rules, sounds and language keys.

    python3 -m tools.odyssey.validate
"""
import glob
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BP = os.path.join(ROOT, "BP")
RP = os.path.join(ROOT, "RP")
VANILLA_MATERIALS = {"entity", "entity_alphatest", "entity_alphablend", "entity_emissive", "entity_emissive_alpha",
                     "entity_nocull", "entity_change_color", "entity_alphatest_change_color", "entity_custom",
                     "entity_alphatest_one_sided", "entity_emissive_alpha_one_sided", "entity_loyalty_rope",
                     "slime", "slime_outer"}
VANILLA_RENDER_CONTROLLERS = {"controller.render.default"}

errors = []


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
    rcs = {name: {} for name in VANILLA_RENDER_CONTROLLERS}
    for path in glob.glob(os.path.join(RP, "render_controllers", "*.json")):
        rcs.update(data.get(path, {}).get("render_controllers", {}))

    bp_entities = {}
    for path in glob.glob(os.path.join(BP, "entities", "*.json")):
        ent = data.get(path, {}).get("minecraft:entity")
        if ent:
            bp_entities[ent["description"]["identifier"]] = ent

    rp_lang = open(os.path.join(RP, "texts", "en_US.lang"), encoding="utf-8").read()
    lang_keys = {ln.split("=", 1)[0].strip() for ln in rp_lang.splitlines() if "=" in ln and not ln.startswith("#")}

    # 3. client entities
    for path in sorted(glob.glob(os.path.join(RP, "entity", "*.entity.json"))):
        ce = data.get(path, {}).get("minecraft:client_entity", {}).get("description", {})
        ident = ce.get("identifier")
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
        for short, aname in ce.get("animations", {}).items():
            if aname.startswith("controller."):
                continue
            if aname not in anims:
                err(f"{where}: animation {aname} not defined")
                continue
            a, apath = anims[aname]
            for bone in a.get("bones", {}):
                if bone not in geo_bones:
                    err(f"{rel(apath)}: {aname} animates missing bone {bone}")
        scripts = ce.get("scripts", {})
        for entry in scripts.get("animate", []):
            name = entry if isinstance(entry, str) else next(iter(entry))
            if name not in ce.get("animations", {}):
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
        text = json.dumps(ce) + json.dumps([anims[a][0] for a in ce.get("animations", {}).values() if a in anims])
        for m in re.finditer(r"q(?:uery)?\.property\(\s*'([^']+)'\s*\)\s*(==|!=)?\s*('([^']*)')?", text):
            pname, value = m.group(1), m.group(4)
            if pname not in props:
                err(f"{where}: Molang reads undeclared property {pname}")
            elif value is not None and value not in props[pname].get("values", []):
                err(f"{where}: {pname} compared with unknown value '{value}'")
        if f"entity.{ident}.name" not in lang_keys:
            err(f"RP lang: missing entity.{ident}.name")
        if ce.get("spawn_egg") and bp_entities.get(ident, {}).get("description", {}).get("is_spawnable") \
                and f"item.spawn_egg.entity.{ident}.name" not in lang_keys:
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
            if key not in lang_keys:
                err(f"RP lang: missing {key}")

    # 5. the script: events it triggers and values it writes
    script = open(os.path.join(BP, "scripts", "main.js"), encoding="utf-8").read()
    every_event = set().union(*all_events.values())
    for ev_name in set(re.findall(r'trigger\([^,]+, "(studio:[^"]+)"\)', script)):
        if ev_name not in every_event:
            err(f"main.js triggers {ev_name}, which no entity defines")
    anim_values = set()
    for ent in bp_entities.values():
        anim_values.update(ent["description"].get("properties", {}).get("studio:anim", {}).get("values", []))
    for v in set(re.findall(r'(?:animate\([^,]+|setProp\([^,]+, "studio:anim"), "([a-z_]+)"', script)):
        if v not in anim_values:
            err(f"main.js sets studio:anim to '{v}', which no entity declares")
    for item in set(re.findall(r'ItemStack\("([^"]+)"', script)) | set(re.findall(r'=== "(studio:[a-z_]+)"', script)):
        name = item.split(":", 1)[1]
        if item.startswith("studio:") and item not in bp_entities and item not in every_event and not os.path.exists(os.path.join(BP, "items", f"{name}.json")):
            err(f"main.js references item {item}, which is not defined")
    for ident in set(re.findall(r'"(studio:[a-z_]+)"', script)) & {f"studio:{os.path.basename(p)[:-5]}" for p in
                                                                  glob.glob(os.path.join(RP, "entity", "*.json"))}:
        if ident not in bp_entities:
            err(f"main.js references entity {ident}, which has no behaviour file")
    for ident in set(re.findall(r'(?:spawnEntity|entitiesOf|near\([^)]*)\(?\s*"(studio:[a-z_]+)"', script)):
        if ident not in bp_entities:
            err(f"main.js spawns or queries unknown entity {ident}")

    # 6. items, item textures, recipes, spawn rules
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
        if f"item.{ident}" not in lang_keys and f"item.{ident}.name" not in lang_keys:
            err(f"RP lang: missing item.{ident}")
    for path in glob.glob(os.path.join(BP, "recipes", "*.json")):
        blob = json.dumps(data.get(path, {}))
        for ident in re.findall(r'"item": "(studio:[a-z_]+)"', blob):
            if ident not in items:
                err(f"{rel(path)}: unknown item {ident}")
    for path in glob.glob(os.path.join(BP, "spawn_rules", "*.json")):
        ident = data.get(path, {}).get("minecraft:spawn_rules", {}).get("description", {}).get("identifier")
        if ident not in bp_entities:
            err(f"{rel(path)}: spawn rule for unknown entity {ident}")

    # 7. sounds.json entity mappings
    sounds = data.get(os.path.join(RP, "sounds.json"), {})
    for ident in sounds.get("entity_sounds", {}).get("entities", {}):
        if ident not in bp_entities:
            err(f"sounds.json: sounds for unknown entity {ident}")

    # 8. script dependencies
    for mod in re.findall(r'from "(@minecraft/[a-z-]+)"', script):
        if not any(d.get("module_name") == mod for d in bp_man.get("dependencies", [])):
            err(f"main.js imports {mod} but the BP manifest does not depend on it")

    if errors:
        print(f"{len(errors)} problem(s):")
        for e in errors:
            print("  -", e)
        return 1
    print(f"OK: {len(bp_entities)} entities, {len(geos)} geometries, {len(anims)} animations, "
          f"{len(items)} items, {len(uuids)} unique manifest uuids")
    return 0


if __name__ == "__main__":
    sys.exit(main())
