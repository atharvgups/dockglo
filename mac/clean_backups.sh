#!/usr/bin/env bash
set -e
dir="$HOME/dev/dockglo/mac/backups"
[ -d "$dir" ] || exit 0
find "$dir" -type f -name '*.txt' -print0 | sort -z | head -z -n -20 | xargs -0 rm -f --
