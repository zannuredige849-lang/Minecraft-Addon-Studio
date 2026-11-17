"""The map of the journey: where each place of the film is, what lives there and what the air looks like.

One plan feeds both the world builder (terrain, structures, packs) and the script (`BP/scripts/data/sites.js`), so what
is built and what the script spawns always agree. Coordinates are blocks; y is the surface the creatures stand on.
The sea is at y = 62. A lodestone at MARKER tells the script it is running in the map and not in an ordinary world: only
then does it give the crew's supplies, show the place titles and keep the creatures of each place alive.
"""

SEA = 62
MARKER = {"x": 0, "y": 64, "z": 0, "block": "minecraft:lodestone"}

# kind: how the world builder shapes the place
SITES = [
    dict(id="ogygia", x=0, z=0, r=45, y=64, kind="island", fog=None,
         creatures=[("studio:calypso", 7, 5)]),
    dict(id="troy", x=-150, z=-260, r=40, y=64, kind="beach", fog=None,
         creatures=[("studio:trojan_horse", 0, 0)]),
    dict(id="cyclops", x=300, z=-150, r=75, y=66, kind="hills", fog="haze",
         creatures=[("studio:cyclops", 18, 0)]),
    dict(id="telepylus", x=560, z=60, r=60, y=64, kind="harbor", fog="telepylus",
         creatures=[("studio:laestrygonian", -12, -10), ("studio:laestrygonian", 16, 4), ("studio:laestrygonian", 4, -16),
                    ("studio:laestrygonian_child", 0, 0)]),
    dict(id="aeaea", x=520, z=360, r=50, y=64, kind="meadow", fog=None,
         creatures=[("studio:circe", 0, 4)]),
    dict(id="hades", x=260, z=520, r=50, y=64, kind="blacksand", fog="hades",
         creatures=[("minecraft:sheep", -6, 4), ("minecraft:sheep", -4, 6), ("minecraft:sheep", -7, 7)]),
    dict(id="sirens", x=-40, z=480, r=70, y=63, kind="rocks", fog="sirens",
         creatures=[("studio:siren", -14, -6), ("studio:siren", 9, 10), ("studio:siren", 18, -12)]),
    dict(id="strait", x=-300, z=380, r=80, y=64, kind="cliff", fog="strait",
         creatures=[("studio:scylla", 0, 0)]),
    dict(id="thrinacia", x=-480, z=130, r=60, y=64, kind="meadow", fog=None,
         creatures=[("studio:sun_cattle", dx, dz) for dx, dz in ((-8, 4), (-2, -9), (6, 6), (10, -4), (-12, -8), (2, 12))]),
    dict(id="ithaca", x=-420, z=-200, r=50, y=64, kind="island", fog=None,
         creatures=[("studio:athena", 4, 6)]),
]

# fog identifier -> (start, end, colour, underwater colour); applied per player while they are in a place
FOGS = {
    "haze": (10, 70, "#b8c0b8", "#2f5766"),
    "telepylus": (2, 28, "#a7aeb2", "#2b4f5b"),
    "hades": (1, 22, "#171515", "#101c20"),
    "sirens": (3, 38, "#c4ccd0", "#2f5a66"),
    "strait": (6, 56, "#8a9498", "#25444e"),
}

RESPAWN_TICKS = 12000      # a place's creature that was killed comes back after ten minutes
