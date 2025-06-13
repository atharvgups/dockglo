#!/usr/bin/env bash
set -euo pipefail

CMD=${1:-apply}                   # apply | undo
SNAP_DIR="$HOME/.dockglo/snapshots"
mkdir -p "$SNAP_DIR"

snap() {                          # create snapshot unless unchanged
  NOW="$SNAP_DIR/$(date +%s).json"
  dockutil --list > "$NOW"
  LATEST=$(ls -t "$SNAP_DIR" | head -1)
  [[ -f $SNAP_DIR/$LATEST ]] && diff -q "$SNAP_DIR/$LATEST" "$NOW" && rm "$NOW"
}

apply() {
  snap
  dockutil --remove all           # clear dock
  i=0
  python reorder.py | while read -r BUNDLE; do
    APP=$(mdfind "kMDItemCFBundleIdentifier == '$BUNDLE'" | head -1)
    [[ -z $APP ]] && continue
    dockutil --add "$APP" --section apps --position $(( ++i ))
  done
  echo "✨ Dock glowed!"
}

undo() {
  PREV=$(ls -t "$SNAP_DIR" | sed -n '2p')
  [[ -z $PREV ]] && { echo "Reached oldest snapshot"; exit 1; }
  dockutil --remove all
  i=0
  awk -F'\t' '{print $1}' "$SNAP_DIR/$PREV" | while read -r APP; do
    dockutil --add "$APP" --section apps --position $(( ++i ))
  done
  rm "$(ls -t "$SNAP_DIR" | head -1 | sed "s|^|$SNAP_DIR/|")"   # drop newest
  echo "↩️  Undo → $(date -r "$PREV") complete."
}

case "$CMD" in
  apply) apply ;;
  undo)  undo ;;
  *) echo "Usage: $0 {apply|undo}" ;;
esac
