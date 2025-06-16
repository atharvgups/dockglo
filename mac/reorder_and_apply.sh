#!/usr/bin/env bash
set -euo pipefail

CMD=${1:-apply}                           # apply | undo | list
SNAP_DIR="$HOME/.dockglo/snapshots"
mkdir -p "$SNAP_DIR"

snapshot() {                              # store only .app paths or bundle-IDs
  dockutil --list --section apps | awk -F'\t' '
    ($1 ~ /\.app$/) {print $1}            # full path to an .app bundle
    ($2 ~ /^[A-Za-z0-9_.-]+$/) {print $2} # or bundle-ID
  ' > "$SNAP_DIR/$(date +%s).txt"
}

seed_defaults() {                         # once: dump current Dock bundle-IDs
  python - <<PY
import json, subprocess, pathlib, os, re, sys
seed_file = pathlib.Path("defaults.json")
if seed_file.exists(): sys.exit(0)
lines = subprocess.check_output(["dockutil","--list","--section","apps"]).decode().splitlines()
bids  = []
for l in lines:
    parts = l.split("\t")
    if len(parts) > 1 and re.match(r'^[A-Za-z0-9_.-]+$', parts[1]):
        bids.append(parts[1])
json.dump({"pinned": bids}, open(seed_file,"w"), indent=2)
print("✨ defaults.json seeded with", len(bids), "bundle IDs")
PY
}

apply() {
  changed=0
  seed_defaults
  [[ $changed -eq 1 ]] && snapshot
  dockutil --remove all
  changed=1
  dockutil --remove spacer &>/dev/null || true   # nuke rogue spacers
  i=0
  python reorder.py | while read -r BID; do
    APP=$(mdfind "kMDItemCFBundleIdentifier == '$BID'" | head -1)
    [[ -z $APP ]] && continue

    # If the app is already pinned remove it first; if that still fails use --replacing
    dockutil --remove "$APP" &>/dev/null || dockutil --remove "$BID" &>/dev/null || true
    dockutil --add "$APP" --section apps --position $(( ++i )) 2>/tmp/dg_add_err \
      || dockutil --add "$APP" --section apps --replacing "$(basename "$APP" .app)" >/dev/null

    changed=1
  done
  echo "✨ Dock glowed!"
}

undo() {
  PREV=$(ls -t "$SNAP_DIR" | sed -n '2p')
  [[ -z $PREV ]] && { echo "Reached oldest snapshot"; exit 1; }

  dockutil --remove all
  dockutil --remove spacer &>/dev/null || true   # nuke rogue spacers
  i=0
  while read -r ITEM; do
      [[ $ITEM == *spacer* ]] && continue  # skip spacer lines
      if [[ -e $ITEM && $ITEM == *.app ]]; then          # real .app path
          APP="$ITEM"
      else                                               # treat ITEM as BID
          APP=$(mdfind "kMDItemCFBundleIdentifier == '$ITEM'" | head -1)
      fi
      [[ -z $APP ]] && continue
      dockutil --add "$APP" --section apps --position $(( ++i )) 2>/tmp/dockerr || dockutil --add "$BID" --section apps --position $i >/dev/null
  done < "$SNAP_DIR/$PREV"
  echo "↩️  Undo → $(date -r "$SNAP_DIR/$PREV") complete."
}

list() { ls -lt "$SNAP_DIR"; }

case "$CMD" in
  apply) apply ;;
  undo)  undo  ;;
  list)  list  ;;
  *) echo "Usage: $0 {apply|undo|list}" ;;
esac
