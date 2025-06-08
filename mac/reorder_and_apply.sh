#!/usr/bin/env bash
set -euo pipefail
REPO="$HOME/dev/dockglo"
PY="$REPO/venv/bin/python"
RESOLVE="$REPO/mac/resolve_app.sh"
BACKUPS="$REPO/mac/backups"; mkdir -p "$BACKUPS"
POINTER="$BACKUPS/.current"          # stores filename of last applied backup
ts() { date +"%Y%m%d-%H%M%S"; }

backup() { "$REPO/mac/backup_dock.sh" >"$BACKUPS/$(ts).txt"; }

resolve_path() {
  local id="$1"; local path
  path=$(grep "|$id\$" "$1" | cut -d'|' -f1 || true)
  [[ -z $path ]] && path=$("$RESOLVE" "$id" || true)
  [[ $path == NOTFOUND || $path == SKIP ]] && path=""
  echo "$path"
}

apply() {
  pre="$BACKUPS/$(ts).txt"; backup      # snapshot BEFORE changes
  echo "$pre" >"$POINTER"

  ORDER="$("$PY" "$REPO/reorder.py")"
  dockutil --remove all >/dev/null
  for id in $ORDER; do
    path=$(resolve_path "$pre" "$id")
    [[ -z $path ]] && continue
    dockutil --add "$path" >/dev/null
  done
  killall Dock
  echo "✨ Dock glowed!"
}

undo() {
  [[ -f $POINTER ]] || { echo "No checkpoints to undo 😬"; exit 1; }
  cur=$(cat "$POINTER")
  all=($(ls -1t "$BACKUPS"/*.txt))
  prev=""
  for f in "${all[@]}"; do
    [[ $f == "$cur" ]] && break
    prev="$f"
  done
  [[ -z $prev ]] && { echo "Reached oldest snapshot"; exit 0; }
  echo "$prev" >"$POINTER"

  dockutil --remove all >/dev/null
  while IFS='|' read -r path _; do
    [[ -e $path ]] && dockutil --add "$path" >/dev/null
  done <"$prev"
  killall Dock
  echo "↩️  Dock restored to $(basename "$prev")"
}

list() { ls -1 "$BACKUPS" | sort; }

case "${1:-apply}" in
  apply) apply ;;
  undo)  undo  ;;
  list)  list  ;;
  *) echo "usage: $0 [apply|undo|list]" ;;
esac
