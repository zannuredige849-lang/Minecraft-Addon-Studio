// The Odyssey (2026) — World Sites & Island Coordinates
export const MARKER = {"x": 0, "y": 64, "z": 0, "block": "minecraft:lodestone"};
export const SITES = [
  {"id": "ogygia",    "x": 0,    "z": 0,    "r": 45, "y": 64, "fog": null,        "creatures": [["studio:calypso", 7, 5]]},
  {"id": "troy",      "x": -150, "z": -260, "r": 45, "y": 64, "fog": null,        "creatures": [["studio:trojan_horse", 0, 0]]},
  {"id": "sparta",    "x": -260, "z": -90,  "r": 45, "y": 64, "fog": null,        "creatures": [["studio:athena", 0, 3]]},
  {"id": "cyclops",   "x": 300,  "z": -150, "r": 75, "y": 66, "fog": "haze",      "creatures": [["studio:cyclops", 18, 0]]},
  {"id": "telepylus", "x": 560,  "z": 60,   "r": 60, "y": 64, "fog": "telepylus", "creatures": [["studio:laestrygonian", -12, -10], ["studio:laestrygonian", 16, 4], ["studio:laestrygonian", 4, -16], ["studio:laestrygonian_child", 0, 0]]},
  {"id": "aeaea",     "x": 520,  "z": 360,  "r": 50, "y": 64, "fog": null,        "creatures": [["studio:circe", 0, 4]]},
  {"id": "hades",     "x": 260,  "z": 520,  "r": 50, "y": 64, "fog": "hades",     "creatures": [["minecraft:sheep", -6, 4], ["minecraft:sheep", -4, 6], ["minecraft:sheep", -7, 7]]},
  {"id": "sirens",    "x": -40,  "z": 480,  "r": 70, "y": 63, "fog": "sirens",    "creatures": [["studio:siren", -14, -6], ["studio:siren", 9, 10], ["studio:siren", 18, -12]]},
  {"id": "strait",    "x": -300, "z": 380,  "r": 80, "y": 64, "fog": "strait",    "creatures": [["studio:scylla", 0, 0]]},
  {"id": "thrinacia", "x": -480, "z": 130,  "r": 60, "y": 64, "fog": null,        "creatures": [["studio:sun_cattle", -8, 4], ["studio:sun_cattle", -2, -9], ["studio:sun_cattle", 6, 6], ["studio:sun_cattle", 10, -4], ["studio:sun_cattle", -12, -8], ["studio:sun_cattle", 2, 12]]},
  {"id": "ithaca",    "x": -420, "z": -200, "r": 55, "y": 64, "fog": null,        "creatures": [["studio:athena", 4, 6]]}
];
export const FOGS = {"haze": "haze", "telepylus": "telepylus", "hades": "hades", "sirens": "sirens", "strait": "strait"};
export const RESPAWN_TICKS = 12000;
