#!/usr/bin/env bash
dockutil --list | while read -r line; do
  path="${line%% *}"
  [[ -e "$path" ]] || continue
  id=$(/usr/bin/mdls -name kMDItemCFBundleIdentifier -raw "$path" 2>/dev/null)
  echo "$path|$id"
done
