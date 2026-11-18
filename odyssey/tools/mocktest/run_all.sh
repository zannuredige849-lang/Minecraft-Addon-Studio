#!/bin/sh
# Copies the behavior pack scripts next to the mock modules and runs every scenario in its own process.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d)
cp -r "$HERE/../../world/behavior_packs/Odyssey_Creatures_BP/scripts" "$WORK/scripts"
mkdir -p "$WORK/node_modules" && cp -r "$HERE/mock/@minecraft" "$WORK/node_modules/"
cp "$HERE/run.mjs" "$WORK/"
echo '{"type":"module"}' > "$WORK/package.json"
cd "$WORK"
status=0
for s in solo duo four afk disconnect leave_lobby late guide; do
  SCRIPTS="$WORK/scripts" node run.mjs $s 2>&1 | grep -v "^\[odyssey\]" || status=1
done
rm -rf "$WORK"
exit $status
