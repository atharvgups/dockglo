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

backup() {                                         # fresh backup JSON
  /usr/libexec/PlistBuddy -c 'Print persistent-apps' \
    ~/Library/Preferences/com.apple.dock.plist |
    sed -n 's/.*_CFURLString *= *"file:\/\/\(.*\.app\)".*/\1/p' |
    jq -R -s -c 'split("\n")[:-1]' > Dock.backup.json
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
  
  # ---------------------------------------------------------------------
  # ALWAYS create a brand-new backup so undo can fully restore the Dock.
  # ---------------------------------------------------------------------
  # always fresh backup so undo restores unopened pins
  backup_json="Dock.backup.json"
  /usr/libexec/PlistBuddy -c 'Print persistent-apps' \
    ~/Library/Preferences/com.apple.dock.plist |
    sed -n 's/.*_CFURLString *= *"file:\/\/\(.*\.app\)".*/\1/p' |
    jq -R -s -c 'split("\n")[:-1]' > "$backup_json"
  
  # Choose order file based on priority
  if   [ -f rainbow.order ];   then order_file=rainbow.order
  elif [ -f order.smart   ];   then order_file=order.smart
  else                              order_file=order.json;  fi
  
  seed_defaults
  [[ $changed -eq 1 ]] && snapshot
  dockutil --remove all
  changed=1
  dockutil --remove spacer &>/dev/null || true   # nuke rogue spacers
  i=0
  STYLE=${DG_STYLE:-score}           # DG_STYLE=rainbow to enable rainbow mode
  # Process each app/path from the order file or reorder.py
  if [ -f "$order_file" ]; then
    jq -r '.[]' "$order_file" | while read -r APP_PATH; do
      # For rainbow.order, we already have full paths
      if [[ -e "$APP_PATH" ]]; then
        APP="$APP_PATH"
      else
        # Try as bundle ID
        APP=$(mdfind "kMDItemCFBundleIdentifier == '$APP_PATH'" | head -1)
      fi
      
      [[ -z $APP ]] && continue

      echo "adding $APP"
      # If the app is already pinned remove it first
      dockutil --remove "$APP" &>/dev/null || true
      # add / move the app into the *apps* section, directly after Finder
      #   – --section apps keeps it left of the system divider
      #   – --after ensures Finder stays truly first
      if ! dockutil --add "$APP" \
               --section apps \
               --after "/System/Library/CoreServices/Finder.app" \
               --no-restart \
               --label "$(basename "$APP")" 2>/dev/null; then
        # Fallback: try adding with replacement
        dockutil --add "$APP" --section apps --replacing "$(basename "$APP" .app)" >/dev/null 2>&1 || true
      fi

      changed=1
    done
  else
    python reorder.py "$STYLE" | while read -r BID; do
      # Find the app, prefer standard locations over system volumes
      APP=$(mdfind "kMDItemCFBundleIdentifier == '$BID'" | grep -v "/System/Volumes/" | head -1)
      if [[ -z $APP ]]; then
        APP=$(mdfind "kMDItemCFBundleIdentifier == '$BID'" | head -1)
      fi
      
      [[ -z $APP ]] && continue
      
      # Check if the app actually exists before proceeding
      if [[ ! -e "$APP" ]]; then
          echo "Warning: App not found at path: $APP"
          continue
      fi

      echo "adding $APP"
      # If the app is already pinned remove it first
      dockutil --remove "$APP" &>/dev/null || true
      # add / move the app into the *apps* section, directly after Finder
      #   – --section apps keeps it left of the system divider
      #   – --after ensures Finder stays truly first
      if ! dockutil --add "$APP" \
               --section apps \
               --after "/System/Library/CoreServices/Finder.app" \
               --no-restart \
               --label "$(basename "$APP")" 2>/dev/null; then
        # Fallback: try adding with replacement
        dockutil --add "$APP" --section apps --replacing "$(basename "$APP" .app)" >/dev/null 2>&1 || true
      fi

      changed=1
    done
  fi
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

# -------- undo: reload the most-recent backup ---------- #
if [ "$1" = "undo" ]; then
  test -f Dock.backup.json || { echo "❗ no backup"; exit 1; }
  jq -r '.[]' Dock.backup.json > /tmp/dock.undo.list
  killall Dock; defaults delete com.apple.dock persistent-apps
  while read -r a; do defaults write com.apple.dock persistent-apps -array-add "{\"tile-data\":{\"file-data\":{\"_CFURLString\":\"file://$a\",\"_CFURLStringType\":0}}}"; done < /tmp/dock.undo.list
  killall Dock
  echo "↩️  Undo → $(date) complete."
  exit 0
fi

# take a fresh backup *before* doing anything else
backup

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
