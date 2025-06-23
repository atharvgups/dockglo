#!/usr/bin/env python3
"""
Pure-aesthetic rainbow: read *current* persistent-apps from the Dock plist,
sort by icon hue (greyscale last), write rainbow.order (Finder kept first).
"""
from pathlib import Path
import plistlib, subprocess, re, colorsys, tempfile, os, json, sys
PLIST = Path.home() / "Library/Preferences/com.apple.dock.plist"

plist = plistlib.load(PLIST.open("rb"))
apps  = [t["tile-data"]["file-data"]["_CFURLString"].removeprefix("file://")
         for t in plist["persistent-apps"]]

def hue(icon):
    try:
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            subprocess.run(["sips","-s","format","png",icon,"--out",tmp.name],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=True)
            out = subprocess.check_output(["sips","-g","pixelHex",tmp.name],
                                          text=True)
        hx  = re.search(r"pixelHex:\s*#([0-9A-Fa-f]{6})", out).group(1)
        r,g,b = (int(hx[i:i+2],16)/255 for i in (0,2,4))
        h,s,_ = colorsys.rgb_to_hsv(r,g,b)
        return 999 if s < .15 else h*360
    except Exception:
        return 999

apps_sorted = sorted(apps, key=hue)
finder      = [a for a in apps_sorted if a.endswith("/Finder.app")]
rainbow     = finder + [a for a in apps_sorted if a not in finder]

Path("rainbow.order").write_text(json.dumps(rainbow))
print("🌈  rainbow.order written")
