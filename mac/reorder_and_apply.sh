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
  STYLE=${DG_STYLE:-score}           # DG_STYLE=rainbow to enable rainbow mode
  python reorder.py "$STYLE" | while read -r BID; do
    APP=$(mdfind "kMDItemCFBundleIdentifier == '$BID'" | head -1)
    [[ -z $APP ]] && continue

    # If the app is already pinned remove it first; if that still fails use --replacing
    dockutil --remove "$APP" &>/dev/null || dockutil --remove "$BID" &>/dev/null || true
    # add / move the app into the *apps* section, directly after Finder
    #   – --section apps keeps it left of the system divider
    #   – --after ensures Finder stays truly first
    dockutil --add "$APP" \
             --section apps \
             --after "/System/Library/CoreServices/Finder.app" \
             --no-restart \
             --label "$(basename "$APP")" 2>/dev/null \
      || dockutil --add "$APP" --section apps --replacing "$(basename "$APP" .app)" >/dev/null

    changed=1
  done
  # sweep others apps (duplicates) but keep folders/stacks
  dockutil --list --section others | awk -F"\t" '{if($1 ~ /\.app$/)print $1}' | while read -r D; do
    dockutil --remove "$D" --section others &>/dev/null; done

  # ---- fold hourly usage into dock_stats.json --------------------------------
  if [[ -f usage_log.jsonl ]]; then
      python - <<'PY'
import json, pathlib, collections, sys, datetime, dateutil.parser
stats = pathlib.Path("dock_stats.json"); log = pathlib.Path("usage_log.jsonl")
ds = {"wanted_counter":{}, "landed_counter":{}, "misclick_counter":{}}
if stats.exists(): ds = json.loads(stats.read_text())
wanted = collections.Counter(ds.get("wanted_counter", {}))
now = datetime.datetime.utcnow()
for line in log.read_text().splitlines():
    rec = json.loads(line); ts = dateutil.parser.isoparse(rec["time"])
    if (now-ts).days < 7: wanted[rec["bid"]] += 1
ds["wanted_counter"] = dict(wanted)
stats.write_text(json.dumps(ds, indent=2))
PY
  fi
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
