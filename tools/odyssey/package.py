"""Package BP/ and RP/ into one .mcaddon, the file you open on a phone or PC to import both packs into Minecraft.

    python3 -m tools.odyssey.package          # writes dist/Odyssey_Creatures_v<version>.mcaddon
"""
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKS = (("BP", "Odyssey_Creatures_BP"), ("RP", "Odyssey_Creatures_RP"))


def build(out=None):
    version = json.load(open(os.path.join(ROOT, "BP", "manifest.json")))["header"]["version"]
    out = out or os.path.join(ROOT, "dist", "Odyssey_Creatures_v{}.mcaddon".format(".".join(map(str, version))))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for pack, folder in PACKS:
            base = os.path.join(ROOT, pack)
            for dirpath, dirnames, files in os.walk(base):
                dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
                for f in sorted(files):
                    if f.startswith("."):
                        continue
                    full = os.path.join(dirpath, f)
                    z.write(full, folder + "/" + os.path.relpath(full, base).replace(os.sep, "/"))
                    count += 1
    # self-check: both manifests at the top of their folders and every JSON file parses
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        for _, folder in PACKS:
            assert folder + "/manifest.json" in names, f"{folder}/manifest.json missing"
        for n in names:
            if n.endswith(".json"):
                json.loads(z.read(n).decode("utf-8"))
    print(f"wrote {os.path.relpath(out, ROOT)}: {count} files, {os.path.getsize(out) // 1024} KB")
    return out


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
