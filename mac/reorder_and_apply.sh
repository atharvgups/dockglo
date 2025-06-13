#!/usr/bin/env bash
set -euo pipefail

CMD=${1:-apply}                           # apply | undo | list
SNAP_DIR="$HOME/.dockglo/snapshots"
mkdir -p "$SNAP_DIR"

snapshot() {                              # always create a checkpoint
  dockutil --list > "$SNAP_DIR/$(date +%s).txt"
}

apply() {
  snapshot                                # 1️⃣  save current Dock
  dockutil --remove all

  i=0
  python reorder.py | while read -r BID; do
    APP=$(mdfind "kMDItemCFBundleIdentifier == '$BID'" | head -1)
    [[ -z $APP ]] && continue             # skip if not installed
    dockutil --add "$APP" --section apps --position $(( ++i )) >/dev/null
  done
  echo "✨ Dock glowed!"
}

undo() {
  # newest file = last apply; second-newest = checkpoint we want
  PREV=$(ls -t "$SNAP_DIR" | sed -n '2p')
  [[ -z $PREV ]] && { echo "Reached oldest snapshot"; exit 1; }

  dockutil --remove all
  i=0
  awk -F'\t' '{print $1}' "$SNAP_DIR/$PREV" | while read -r APP; do
    dockutil --add "$APP" --section apps --position $(( ++i )) >/dev/null
  done
  echo "↩️  Undo → $(date -r "$SNAP_DIR/$PREV") complete."
}

list() { ls -lt "$SNAP_DIR"; }

case "$CMD" in
  apply) apply ;;
  undo)  undo  ;;
  list)  list  ;;
  *) echo "Usage: $0 {apply|undo|list}" ;;
esac
