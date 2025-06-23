#!/usr/bin/env python3
import json, plistlib, os, pathlib, sys
plist = pathlib.Path.home()/'Library/Preferences/com.apple.dock.plist'
apps  = plistlib.load(plist.open('rb'))['persistent-apps']
paths = [t['tile-data']['file-data']['_CFURLString'].removeprefix('file://')
         for t in apps]
json.dump(paths, open('Dock.backup.json','w'))
print("📦  Dock.backup.json saved   (", len(paths), "pins )")
