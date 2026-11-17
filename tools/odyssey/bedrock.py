"""Behaviour-pack and resource-pack JSON for every entity, item, recipe, spawn rule and sound."""

BOOL = {"type": "bool", "default": False, "client_sync": True}
NO_FALL = {"cause": "fall", "deals_damage": False}
INVULNERABLE = {"triggers": [{"cause": "all", "deals_damage": False}]}


def enum_prop(values):
    return {"type": "enum", "values": values, "default": values[0], "client_sync": True}


def int_prop(lo, hi):
    return {"type": "int", "range": [lo, hi], "default": lo, "client_sync": True}


def entity(identifier, props, comps, groups=None, events=None, spawnable=True):
    desc = {"identifier": identifier, "is_spawnable": spawnable, "is_summonable": True, "is_experimental": False}
    if props:
        desc["properties"] = props
    body = {"description": desc, "components": comps}
    if groups:
        body["component_groups"] = groups
    if events:
        body["events"] = events
    return {"format_version": "1.21.0", "minecraft:entity": body}


def target(prio, max_dist, families=("player",), must_see=True, extra=None):
    flt = {"any_of": [{"test": "is_family", "subject": "other", "value": f} for f in families]}
    if extra:
        flt = {"all_of": [flt] + extra}
    return {"priority": prio, "must_see": must_see, "reselect_targets": True, "scan_interval": 5,
            "entity_types": [{"filters": flt, "max_dist": max_dist}]}


def ai_wander(stroll=6, look=7, speed=0.9):
    return {"minecraft:behavior.random_stroll": {"priority": stroll, "speed_multiplier": speed},
            "minecraft:behavior.look_at_player": {"priority": look, "look_distance": 14, "probability": 0.5},
            "minecraft:behavior.random_look_around": {"priority": look + 1}}


def base(families, w, h, hp, sound_every=12):
    return {"minecraft:type_family": {"family": families + ["studio_odyssey", "mob"]},
            "minecraft:collision_box": {"width": w, "height": h},
            "minecraft:health": {"value": hp, "max": hp},
            "minecraft:physics": {},
            "minecraft:nameable": {},
            "minecraft:ambient_sound_interval": {"value": sound_every, "range": 10, "event_name": "ambient"}}


def walker(speed, water_ok=False):
    return {"minecraft:movement": {"value": speed}, "minecraft:movement.basic": {}, "minecraft:jump.static": {},
            "minecraft:navigation.walk": {"can_path_over_water": False, "avoid_water": not water_ok,
                                          "avoid_damage_blocks": True, "can_pass_doors": True}}


def static(npc_look=True):
    c = {"minecraft:movement": {"value": 0.0}, "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
         "minecraft:knockback_resistance": {"value": 1.0}}
    if npc_look:
        c["minecraft:behavior.look_at_player"] = {"priority": 7, "look_distance": 16, "probability": 0.8}
    return c


def interact(event, text, cooldown=1.0, extra_filters=None):
    flt = [{"test": "is_family", "subject": "other", "value": "player"}] + (extra_filters or [])
    return {"on_interact": {"filters": {"all_of": flt}, "event": event, "target": "self"},
            "cooldown": cooldown, "interact_text": text}


# ================================================================== entities
def bp_cyclops():
    c = base(["cyclops", "giant", "monster"], 1.8, 6.4, 600, 9)
    c.update({
        "minecraft:movement": {"value": 0.26}, "minecraft:movement.basic": {}, "minecraft:jump.static": {},
        "minecraft:navigation.generic": {"is_amphibious": True, "can_path_over_water": False, "can_swim": False,
                                         "can_walk": True, "can_sink": True, "avoid_water": False,
                                         "avoid_damage_blocks": True, "can_breach": False},
        "minecraft:breathable": {"total_supply": 300, "suffocate_time": 0, "breathes_water": True, "breathes_air": True},
        "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
        "minecraft:knockback_resistance": {"value": 1.0},
        "minecraft:attack": {"damage": 16},
        "minecraft:damage_sensor": {"triggers": [NO_FALL, {"cause": "drowning", "deals_damage": False}]},
        "minecraft:follow_range": {"value": 48, "max": 64},
        "minecraft:persistent": {},
    })
    awake = ai_wander(6, 7)
    awake["minecraft:behavior.hurt_by_target"] = {"priority": 1}
    awake["minecraft:behavior.melee_attack"] = {"priority": 3, "speed_multiplier": 1.1, "track_target": True}
    groups = {
        "studio:awake_ai": awake,
        "studio:hunting": {"minecraft:behavior.nearest_attackable_target": target(2, 40)},
        # Blind: he hunts by touch and hearing; men hidden in his flock (tagged by the script) are passed over
        "studio:blind_hunting": {"minecraft:behavior.nearest_attackable_target": target(
            2, 24, must_see=False, extra=[{"test": "has_tag", "subject": "other", "operator": "!=", "value": "studio:in_flock"}])},
        "studio:asleep": {"minecraft:movement": {"value": 0.0}},
    }
    events = {
        "minecraft:entity_spawned": {"add": {"component_groups": ["studio:awake_ai", "studio:hunting"]}},
        "studio:hunt": {"add": {"component_groups": ["studio:hunting"]}},
        "studio:fall_asleep": {"set_property": {"studio:state": "asleep"},
                               "remove": {"component_groups": ["studio:awake_ai", "studio:hunting", "studio:blind_hunting"]},
                               "add": {"component_groups": ["studio:asleep"]}},
        "studio:wake": {"set_property": {"studio:state": "awake"}, "remove": {"component_groups": ["studio:asleep"]},
                        "add": {"component_groups": ["studio:awake_ai"]}},
        "studio:blinded": {"set_property": {"studio:blind": True, "studio:state": "awake"},
                           "remove": {"component_groups": ["studio:asleep", "studio:hunting"]},
                           "add": {"component_groups": ["studio:awake_ai", "studio:blind_hunting"]}},
    }
    props = {"studio:state": enum_prop(["awake", "asleep"]), "studio:blind": BOOL,
             "studio:anim": enum_prop(["none", "grab", "throw", "cry"])}
    return entity("studio:cyclops", props, c, groups, events)


WEAPONS = (("sword", 14), ("glaive", 12), ("mace", 18), ("scimitar", 20))


def bp_laestrygonian():
    c = base(["laestrygonian", "giant", "monster"], 1.8, 4.0, 140, 14)
    c.update(walker(0.27, water_ok=True))
    c.update({
        "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
        "minecraft:knockback_resistance": {"value": 0.9},
        # armour 'of a level of sophistication Odysseus has never seen': blades barely bite, an arrow still kills
        "minecraft:damage_sensor": {"triggers": [NO_FALL, {"cause": "entity_attack", "deals_damage": True, "damage_multiplier": 0.5}]},
        "minecraft:follow_range": {"value": 40, "max": 48},
        "minecraft:attack": {"damage": 14},
    })
    calm = ai_wander(6, 7)
    calm["minecraft:behavior.hurt_by_target"] = {"priority": 1, "alert_same_type": True}
    calm["minecraft:behavior.melee_attack"] = {"priority": 3, "speed_multiplier": 1.15, "track_target": True}
    groups = {"studio:calm": calm,
              "studio:alarmed": {"minecraft:behavior.nearest_attackable_target": target(2, 40, ("player", "villager"), must_see=False)}}
    for i, (w, dmg) in enumerate(WEAPONS):
        groups[f"studio:w_{w}"] = {"minecraft:attack": {"damage": dmg}}
    rnd = []
    for i, ((w, _), weight) in enumerate(zip(WEAPONS, (4, 3, 3, 1))):
        rnd.append({"weight": weight, "set_property": {"studio:weapon": i}, "add": {"component_groups": [f"studio:w_{w}"]}})
    events = {"minecraft:entity_spawned": {"sequence": [{"add": {"component_groups": ["studio:calm"]}}, {"randomize": rnd}]},
              "studio:alarm": {"add": {"component_groups": ["studio:alarmed"]}}}
    props = {"studio:weapon": int_prop(0, 3), "studio:anim": enum_prop(["none", "swing", "smash"])}
    return entity("studio:laestrygonian", props, c, groups, events)


def bp_child():
    c = base(["laestrygonian_child", "laestrygonian"], 0.6, 1.9, 30, 20)
    c.update(walker(0.3))
    c.update({"minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True}})
    c.update(ai_wander(6, 5))
    groups = {"studio:fleeing": {"minecraft:behavior.avoid_mob_type": {"priority": 1, "entity_types": [
        {"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 24, "walk_speed_multiplier": 1.4,
         "sprint_speed_multiplier": 1.6}]}}}
    events = {"studio:flee": {"add": {"component_groups": ["studio:fleeing"]}}}
    return entity("studio:laestrygonian_child", {"studio:anim": enum_prop(["none", "laugh", "scream"])}, c, groups, events)


def bp_circe():
    c = base(["circe", "witch_goddess"], 0.6, 1.75, 40, 30)
    c.update(walker(0.2))
    c.update({"minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True}, "minecraft:persistent": {}})
    c.update(ai_wander(6, 5, 0.6))
    c["minecraft:interact"] = {"interactions": [
        interact("studio:offer_stew", "action.interact.studio.stew", 5,
                 [{"test": "bool_property", "subject": "self", "domain": "studio:yielded", "value": False}]),
        interact("studio:counsel", "action.interact.studio.counsel", 5,
                 [{"test": "bool_property", "subject": "self", "domain": "studio:yielded", "value": True}])]}
    events = {"studio:offer_stew": {"set_property": {"studio:anim": "none"}},
              "studio:counsel": {"set_property": {"studio:anim": "none"}},
              "studio:yield": {"set_property": {"studio:yielded": True, "studio:anim": "none"}}}
    return entity("studio:circe", {"studio:anim": enum_prop(["none", "mold"]), "studio:yielded": BOOL}, c, None, events)


def bp_sister():
    c = base(["circe_sister", "bird"], 0.4, 0.5, 6, 18)
    c.update({"minecraft:physics": {"has_gravity": False, "has_collision": False},
              "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
              "minecraft:damage_sensor": INVULNERABLE, "minecraft:persistent": {},
              "minecraft:interact": {"interactions": [interact("studio:seized", "action.interact.studio.seize", 2)]}})
    groups = {"studio:seized": {"minecraft:persistent": {}}}
    return entity("studio:circe_sister", None, c, groups, {"studio:seized": {"add": {"component_groups": ["studio:seized"]}}},
                  spawnable=False)


def bp_siren():
    # a mermaid lying on the sea rocks: she does not move from them, breathes in water and air, cannot be harmed
    c = base(["siren", "mermaid"], 1.0, 1.2, 100, 999)
    c.update(static())
    c.update({"minecraft:damage_sensor": INVULNERABLE,
              "minecraft:breathable": {"total_supply": 300, "suffocate_time": 0, "breathes_water": True, "breathes_air": True}})
    return entity("studio:siren", None, c)


def bp_scylla():
    c = base(["scylla", "monster"], 5.0, 8.0, 1000, 8)
    c.update(static(npc_look=False))
    c.update({"minecraft:damage_sensor": INVULNERABLE, "minecraft:persistent": {}})
    return entity("studio:scylla", {"studio:anim": enum_prop(["none", "snatch"])}, c)


def bp_charybdis():
    c = {"minecraft:type_family": {"family": ["charybdis", "studio_odyssey", "inanimate"]},
         "minecraft:collision_box": {"width": 1.0, "height": 0.5},
         "minecraft:health": {"value": 1000, "max": 1000},
         "minecraft:physics": {"has_gravity": False, "has_collision": False},
         "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
         "minecraft:knockback_resistance": {"value": 1.0},
         "minecraft:damage_sensor": INVULNERABLE, "minecraft:persistent": {},
         "minecraft:ambient_sound_interval": {"value": 3, "range": 2, "event_name": "ambient"}}
    return entity("studio:charybdis", None, c)


def bp_shade():
    c = base(["shade", "undead", "monster"], 0.6, 1.9, 24, 8)
    c.update(walker(0.27))
    c.update({"minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True}, "minecraft:attack": {"damage": 4},
              "minecraft:damage_sensor": {"triggers": [NO_FALL]}})
    hostile = ai_wander(6, 7)
    hostile["minecraft:behavior.nearest_attackable_target"] = target(2, 32, must_see=False)
    hostile["minecraft:behavior.melee_attack"] = {"priority": 3, "speed_multiplier": 1.2, "track_target": True}
    groups = {"studio:hostile": hostile,
              "studio:speaker": {"minecraft:behavior.look_at_player": {"priority": 2, "look_distance": 24, "probability": 1.0},
                                 "minecraft:movement": {"value": 0.0}},
              "studio:rising": {"minecraft:movement": {"value": 0.0}}}
    events = {"minecraft:entity_spawned": {"add": {"component_groups": ["studio:hostile"]}},
              "studio:as_crew": {"set_property": {"studio:variant": 0}},
              "studio:as_agamemnon": {"set_property": {"studio:variant": 1}, "remove": {"component_groups": ["studio:hostile"]},
                                      "add": {"component_groups": ["studio:speaker"]}},
              "studio:as_sinon": {"set_property": {"studio:variant": 2}, "remove": {"component_groups": ["studio:hostile"]},
                                  "add": {"component_groups": ["studio:speaker"]}},
              "studio:rise": {"add": {"component_groups": ["studio:rising"]}},
              "studio:risen": {"remove": {"component_groups": ["studio:rising"]}}}
    props = {"studio:variant": int_prop(0, 2), "studio:anim": enum_prop(["none", "rise", "sink", "grab"])}
    return entity("studio:shade", props, c, groups, events)


def bp_tiresias():
    c = base(["tiresias", "shade"], 0.6, 1.9, 100, 999)
    c.update(static())
    c.update({"minecraft:damage_sensor": INVULNERABLE})
    return entity("studio:tiresias", {"studio:anim": enum_prop(["none", "rise", "sink", "speak"])}, c)


def bp_cattle():
    c = base(["sun_cattle", "cattle"], 1.2, 1.7, 20, 14)
    c.update(walker(0.2))
    c.update({"minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
              "minecraft:behavior.float": {"priority": 0},
              "minecraft:behavior.panic": {"priority": 1, "speed_multiplier": 1.4}})
    c.update(ai_wander(6, 7, 0.8))
    return entity("studio:sun_cattle", None, c)


def bp_calypso():
    c = base(["calypso", "nymph"], 0.6, 1.85, 40, 999)
    c.update(walker(0.18))
    c.update(ai_wander(6, 5, 0.5))
    c.update({"minecraft:persistent": {}, "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
              "minecraft:interact": {"interactions": [interact("studio:offer_lotus", "action.interact.studio.lotus", 5)]}})
    groups = {"studio:visited": {"minecraft:persistent": {}}}
    return entity("studio:calypso", None, c, groups, {"studio:offer_lotus": {"add": {"component_groups": ["studio:visited"]}}})


def bp_athena():
    c = base(["athena", "goddess"], 0.6, 1.85, 100, 999)
    c.update(walker(0.18))
    c.update(ai_wander(6, 5, 0.5))
    c.update({"minecraft:persistent": {}, "minecraft:damage_sensor": INVULNERABLE,
              "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
              "minecraft:interact": {"interactions": [interact("studio:bless", "action.interact.studio.athena", 5)]}})
    return entity("studio:athena", {"studio:anim": enum_prop(["none", "bless"])}, c, None,
                  {"studio:bless": {"set_property": {"studio:anim": "bless"}}})


def bp_horse():
    seats = [{"position": [x, y, z]} for (x, y, z) in
             ((-0.5, 4.4, -0.6), (0.5, 4.4, -0.6), (-0.5, 4.9, 0.5), (0.5, 4.9, 0.5), (-0.5, 5.4, 1.5), (0.5, 5.4, 1.5))]
    c = {"minecraft:type_family": {"family": ["trojan_horse", "studio_odyssey", "inanimate"]},
         "minecraft:collision_box": {"width": 3.0, "height": 4.0},
         "minecraft:health": {"value": 1000, "max": 1000},
         "minecraft:physics": {},
         "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
         "minecraft:knockback_resistance": {"value": 1.0},
         "minecraft:damage_sensor": INVULNERABLE, "minecraft:persistent": {},
         "minecraft:rideable": {"seat_count": 6, "family_types": ["player"], "interact_text": "action.interact.studio.hide",
                                "pull_in_entities": False, "seats": seats}}
    return entity("studio:trojan_horse", None, c)


def bp_boulder():
    c = {"minecraft:type_family": {"family": ["studio_boulder", "inanimate"]},
         "minecraft:collision_box": {"width": 0.8, "height": 0.8},
         "minecraft:health": {"value": 1, "max": 1},
         "minecraft:physics": {"has_gravity": False, "has_collision": False},
         "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
         "minecraft:damage_sensor": INVULNERABLE}
    return entity("studio:boulder", None, c, spawnable=False)


# ================================================================== client side
RENDER_CONTROLLERS = {"format_version": "1.10.0", "render_controllers": {
    "controller.render.studio_cyclops": {
        "arrays": {"textures": {"Array.skins": ["Texture.default", "Texture.blinded"]}},
        "geometry": "Geometry.default", "materials": [{"*": "Material.default"}],
        "textures": ["Array.skins[query.property('studio:blind')]"]},
    "controller.render.studio_laestrygonian": {
        "geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"],
        "part_visibility": [{"*": True},
                            {"sword": "query.property('studio:weapon') == 0"},
                            {"glaive": "query.property('studio:weapon') == 1"},
                            {"mace": "query.property('studio:weapon') == 2"},
                            {"scimitar": "query.property('studio:weapon') == 3"}]},
    "controller.render.studio_shade": {
        "arrays": {"textures": {"Array.skins": ["Texture.default", "Texture.agamemnon", "Texture.sinon"]}},
        "geometry": "Geometry.default", "materials": [{"*": "Material.default"}],
        "textures": ["Array.skins[query.property('studio:variant')]"],
        "part_visibility": [{"*": True},
                            {"helmet": "query.property('studio:variant') != 2"},
                            {"crest": "query.property('studio:variant') == 0"},
                            {"plume": "query.property('studio:variant') == 1"}]},
}}


def client_entity(name, textures, rc, anim_names, animate, egg=None, material="entity_alphatest", scale=None):
    desc = {"identifier": f"studio:{name}", "materials": {"default": material}, "textures": textures,
            "geometry": {"default": f"geometry.{name}"}, "render_controllers": [rc],
            "animations": {k: f"animation.{name}.{k}" for k in anim_names}}
    scripts = {}
    if animate:
        scripts["animate"] = animate
    if scale:
        scripts["scale"] = str(scale)
    if scripts:
        desc["scripts"] = scripts
    if egg:
        desc["spawn_egg"] = {"base_color": egg[0], "overlay_color": egg[1]}
    return {"format_version": "1.10.0", "minecraft:client_entity": {"description": desc}}


SOUNDS = {"entity_sounds": {"entities": {
    "studio:cyclops": {"volume": 1.6, "pitch": [0.35, 0.45], "events": {
        "ambient": "mob.ravager.ambient", "hurt": "mob.ravager.hurt", "death": "mob.ravager.death", "step": "mob.ravager.step"}},
    "studio:laestrygonian": {"volume": 1.0, "pitch": [0.55, 0.65], "events": {
        "hurt": "mob.irongolem.hit", "death": "mob.irongolem.death", "step": "mob.irongolem.walk"}},
    "studio:laestrygonian_child": {"volume": 1.0, "pitch": [1.1, 1.3], "events": {"hurt": "mob.villager.hurt"}},
    "studio:circe": {"volume": 1.0, "pitch": [0.85, 0.95], "events": {"hurt": "mob.witch.hurt", "death": "mob.witch.death"}},
    "studio:circe_sister": {"volume": 0.8, "pitch": [0.8, 0.9], "events": {"ambient": "mob.parrot.idle"}},
    "studio:scylla": {"volume": 1.4, "pitch": [0.35, 0.45], "events": {"ambient": "mob.hoglin.ambient"}},
    "studio:charybdis": {"volume": 0.9, "pitch": [0.5, 0.7], "events": {"ambient": "bubble.downinside"}},
    "studio:shade": {"volume": 1.0, "pitch": [0.55, 0.7], "events": {
        "ambient": "mob.zombie.say", "hurt": "mob.zombie.hurt", "death": "mob.zombie.death"}},
    "studio:sun_cattle": {"volume": 1.0, "pitch": [0.75, 0.85], "events": {
        "ambient": "mob.cow.say", "hurt": "mob.cow.hurt", "death": "mob.cow.hurt", "step": "mob.cow.step"}},
}}}


# ================================================================== items
ITEMS = {
    "beeswax": dict(cat="items", stack=16, food=(0, 0.0), anim="eat", dur=1.0),
    "burning_stake": dict(cat="equipment", stack=1, weapon=6),
    "circe_stew": dict(cat="items", stack=1, food=(8, 0.9), anim="eat", dur=1.6),
    "lotus_flower": dict(cat="nature", stack=8, food=(1, 0.2), anim="eat", dur=1.2),
}


def item_json(name, spec):
    comps = {"minecraft:icon": {"textures": {"default": f"studio_{name}"}},
             "minecraft:display_name": {"value": f"item.studio:{name}.name"},
             "minecraft:max_stack_size": spec["stack"]}
    if "food" in spec:
        comps["minecraft:food"] = {"nutrition": spec["food"][0], "saturation_modifier": spec["food"][1], "can_always_eat": True}
        comps["minecraft:use_animation"] = spec["anim"]
        comps["minecraft:use_modifiers"] = {"use_duration": spec["dur"], "movement_modifier": 0.35}
    if "weapon" in spec:
        comps["minecraft:hand_equipped"] = True
        comps["minecraft:damage"] = {"value": spec["weapon"]}
    return {"format_version": "1.21.0", "minecraft:item": {
        "description": {"identifier": f"studio:{name}", "menu_category": {"category": spec["cat"]}}, "components": comps}}


RECIPES = {
    "beeswax": {"format_version": "1.20.10", "minecraft:recipe_shapeless": {
        "description": {"identifier": "studio:beeswax"}, "tags": ["crafting_table"],
        "ingredients": [{"item": "minecraft:honeycomb"}], "result": {"item": "studio:beeswax", "count": 2}}},
    "burning_stake": {"format_version": "1.20.10", "minecraft:recipe_shaped": {
        "description": {"identifier": "studio:burning_stake"}, "tags": ["crafting_table"],
        "pattern": ["F", "L", "C"], "key": {"F": {"item": "minecraft:flint"}, "L": {"item": "minecraft:oak_log"},
                                           "C": {"item": "minecraft:coal"}},
        "result": {"item": "studio:burning_stake"}}},
}


def spawn_rule(identifier, tag_filter, weight, herd, density=2, control="monster"):
    cond = {"minecraft:spawns_on_surface": {}, "minecraft:weight": {"default": weight},
            "minecraft:herd": {"min_size": herd[0], "max_size": herd[1]},
            "minecraft:density_limit": {"surface": density}, "minecraft:biome_filter": tag_filter}
    if control == "monster":
        cond["minecraft:difficulty_filter"] = {"min": "easy", "max": "hard"}
    return {"format_version": "1.8.0", "minecraft:spawn_rules": {
        "description": {"identifier": identifier, "population_control": control}, "conditions": [cond]}}


SPAWN_RULES = {
    # Telepylus was filmed in Scotland's Culbin pine forest: giants in coniferous forest, with their child
    "laestrygonian": spawn_rule("studio:laestrygonian", {"test": "has_biome_tag", "value": "taiga"}, 2, (2, 3)),
    "laestrygonian_child": spawn_rule("studio:laestrygonian_child", {"test": "has_biome_tag", "value": "taiga"}, 1, (1, 1), 1),
    # the Sirens on their rocks by the sea
    "siren": spawn_rule("studio:siren", {"all_of": [{"test": "has_biome_tag", "value": "beach"},
                                                     {"test": "has_biome_tag", "value": "stone"}]}, 4, (2, 3), 3),
    # the sun god's herd grazing on Thrinacia
    "sun_cattle": spawn_rule("studio:sun_cattle", {"test": "has_biome_tag", "value": "plains"}, 2, (3, 4), 4, "animal"),
}

LANG = [
    ("entity.studio:cyclops.name", "Polyphemus"), ("entity.studio:laestrygonian.name", "Laestrygonian"),
    ("entity.studio:laestrygonian_child.name", "Laestrygonian Child"), ("entity.studio:circe.name", "Circe"),
    ("entity.studio:circe_sister.name", "Circe's Sister"), ("entity.studio:siren.name", "Siren"),
    ("entity.studio:scylla.name", "Scylla"), ("entity.studio:charybdis.name", "Charybdis"),
    ("entity.studio:shade.name", "Shade"), ("entity.studio:tiresias.name", "Tiresias"),
    ("entity.studio:sun_cattle.name", "Cattle of Apollo"), ("entity.studio:calypso.name", "Calypso"),
    ("entity.studio:athena.name", "Athena"), ("entity.studio:trojan_horse.name", "Trojan Horse"),
    ("entity.studio:boulder.name", "Boulder"),
    ("item.spawn_egg.entity.studio:cyclops.name", "Spawn Polyphemus"),
    ("item.spawn_egg.entity.studio:laestrygonian.name", "Spawn Laestrygonian"),
    ("item.spawn_egg.entity.studio:laestrygonian_child.name", "Spawn Laestrygonian Child"),
    ("item.spawn_egg.entity.studio:circe.name", "Spawn Circe"),
    ("item.spawn_egg.entity.studio:siren.name", "Spawn Siren"),
    ("item.spawn_egg.entity.studio:scylla.name", "Spawn Scylla"),
    ("item.spawn_egg.entity.studio:charybdis.name", "Spawn Charybdis"),
    ("item.spawn_egg.entity.studio:shade.name", "Spawn Shade"),
    ("item.spawn_egg.entity.studio:tiresias.name", "Spawn Tiresias"),
    ("item.spawn_egg.entity.studio:sun_cattle.name", "Spawn Cattle of Apollo"),
    ("item.spawn_egg.entity.studio:calypso.name", "Spawn Calypso"),
    ("item.spawn_egg.entity.studio:athena.name", "Spawn Athena"),
    ("item.spawn_egg.entity.studio:trojan_horse.name", "Spawn Trojan Horse"),
    ("item.studio:beeswax.name", "Wax"), ("item.studio:burning_stake.name", "Burning Stake"),
    ("item.studio:circe_stew.name", "Circe's Stew"), ("item.studio:lotus_flower.name", "Lotus Flower"),
    ("action.interact.studio.stew", "Beg for Food"), ("action.interact.studio.counsel", "Ask the Way Home"),
    ("action.interact.studio.seize", "Seize Her Sister"), ("action.interact.studio.lotus", "Accept a Lotus"),
    ("action.interact.studio.athena", "Speak with Athena"), ("action.interact.studio.hide", "Hide Inside"),
]

ITEM_ART = {
    "beeswax": ({"o": (120, 80, 20), "Y": (240, 190, 60), "y": (215, 160, 40), "H": (252, 222, 124)}, [
        "................", "................", "................", ".....oooooo.....", "....oYYYYYYo....",
        "...oYyHyYyHyo...", "...oyHyYyHyYo...", "..oYyYHyYHyYyo..", "..oyHyYyHyYyHo..", "..oYyHyYyHyYyo..",
        "...oyYyHyYyHo...", "...ooyYyYyYoo...", ".....oooooo.....", "................", "................",
        "................"]),
    "burning_stake": ({"E": (255, 150, 40), "e": (255, 220, 120), "c": (40, 30, 25), "w": (122, 92, 56),
                       "W": (164, 128, 82)}, [
        "............eEe.", "...........EEEe.", "..........cEEE..", ".........cccE...", "........wccc....",
        ".......wWwc.....", "......wWww......", ".....wWww.......", "....wWww........", "...wWww.........",
        "..wWww..........", ".wWww...........", ".www............", "ww..............", "................",
        "................"]),
    "circe_stew": ({"s": (96, 70, 44), "S": (128, 96, 58), "g": (88, 104, 50), "t": (108, 76, 46), "T": (150, 108, 64),
                    "m": (150, 90, 70)}, [
        "................", "................", "................", "................", ".....m...g......",
        "....sssssssss...", "...sSsmSsSgsSs..", "..tsSSssSSsSSst.", "..tTTTTTTTTTTTt.", "..ttTtTTtTTtTt..",
        "...tTTTTTTTTTt..", "....tTTTTTTTt...", ".....ttttttt....", "................", "................",
        "................"]),
    "lotus_flower": ({"w": (246, 236, 236), "p": (232, 170, 190), "P": (212, 130, 160), "y": (238, 206, 90),
                      "g": (78, 120, 64), "G": (110, 150, 80)}, [
        "................", "......w..w......", ".....wpwwpw.....", "....wpPwwPpw....", "...wpPpyyPpPw...",
        "....wPpyypPw....", ".....wppppw.....", ".......gg.......", "......Gg........", ".......g........",
        ".......g..GG....", "....GGGgGGG.....", "...GGG.g........", ".......g........", "................",
        "................"]),
}
