#!/usr/bin/env python3
"""Write rainbow.order with Dock apps sorted by icon hue."""
from pathlib import Path, PurePath
import subprocess, tempfile, re, json, colorsys, sys
apps = json.loads(Path("Dock.backup.json").read_text())
apps = [a for a in apps if Path(a).exists()]
def hue(app_path):
    try:
        # Find the app icon
        import glob
        icon_patterns = [
            f"{app_path}/Contents/Resources/AppIcon.icns",
            f"{app_path}/Contents/Resources/*.icns"
        ]
        icon = None
        for pattern in icon_patterns:
            matches = glob.glob(pattern)
            if matches:
                icon = matches[0]
                break
        
        if not icon:
            return 999
            
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            subprocess.check_call(
                ["sips", "-s", "format", "png", icon, "--out", tmp.name],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            out = subprocess.check_output(
                ["sips","-g","pixelHex",tmp.name],
                text=True, timeout=2)
            hx = re.search(r'pixelHex:\s*0x([0-9A-Fa-f]{6})', out).group(1)
            r,g,b = (int(hx[i:i+2],16)/255 for i in (0,2,4))
            h,s,_ = colorsys.rgb_to_hsv(r,g,b)
            return 999 if s < .15 else h*360      # greys last
    except Exception:
        return 999          # greys to the far right
apps_sorted = sorted(apps, key=hue)
finder = [a for a in apps_sorted if PurePath(a).name == "Finder.app"]
Path("rainbow.order").write_text(json.dumps(finder + [a for a in apps_sorted if a not in finder]))
print("🌈  rainbow.order written – run './mac/reorder_and_apply.sh apply'")
