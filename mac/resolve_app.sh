#!/usr/bin/env bash
id="$1"
case "$id" in
  com.apple.finder)        echo "SKIP"; exit ;;
  com.microsoft.VSCode)    echo "/Applications/Visual Studio Code.app"; exit ;;
  com.google.Chrome)       echo "/Applications/Google Chrome.app"; exit ;;
  com.apple.Mail)          echo "/System/Applications/Mail.app"; exit ;;
  com.spotify.client)      echo "/Applications/Spotify.app"; exit ;;
  com.apple.Terminal)      echo "/System/Applications/Utilities/Terminal.app"; exit ;;
esac
path=$(/usr/bin/mdfind "kMDItemCFBundleIdentifier == '$id'" | head -n1)
[[ -z "$path" ]] && { echo "NOTFOUND"; exit 1; }
echo "$path"
