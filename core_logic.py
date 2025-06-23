class DockStats:
    """Track Dock clicks and suggest optimal ordering."""

    def __init__(self):
        from collections import Counter
        self.wanted_counter = Counter()
        self.landed_counter = Counter()
        self.misclick_counter = Counter()

    # ---------- scoring ----------
    def _decay(self, ts: float) -> float:
        """Half-life ≈ 8 days – recent clicks ≫ old clicks."""
        import time, math
        return 2.0 ** (-(time.time() - ts) / 86400 / 8)

    def beauty_score(self, app_id: str) -> float:
        """Recency-weighted beauty score."""
        wanted = self.wanted_counter.get(app_id, 0)
        mis = sum(c for (w, _), c in self.misclick_counter.items() if w == app_id)
        return wanted + mis * 2.0

    # ---------- colour helpers ----------
    def _h(self, app_id: str) -> str:
        """Get cached hex color for app icon."""
        # This would be implemented with actual hex color caching
        return ""
    
    def _icn(self, app_id: str) -> str:
        """Get path to app icon."""
        import pathlib, glob
        # Map common bundle IDs to actual app names
        app_map = {
            'com.apple.finder': 'Finder',
            'com.apple.Safari': 'Safari', 
            'com.apple.Terminal': 'Terminal',
            'com.apple.Mail': 'Mail',
            'com.microsoft.VSCode': 'Visual Studio Code',
            'com.google.Chrome': 'Google Chrome',
            'com.spotify.client': 'Spotify'
        }
        
        app_name = app_map.get(app_id, app_id.split('.')[-1])
        
        # Try different possible paths
        for path in [
            f"/Applications/{app_name}.app/Contents/Resources/AppIcon.icns",
            f"/System/Applications/{app_name}.app/Contents/Resources/AppIcon.icns", 
            f"/Applications/{app_name}.app/Contents/Resources/*.icns"
        ]:
            matches = glob.glob(path)
            if matches:
                return matches[0]
        
        return ""
    
    def _icon_hue(self, app_id: str) -> float:
        """
        Return the HSB hue (0-360) of an app icon.
        Grey / monochrome icons get 999 so they stay right.
        """
        import subprocess, re, colorsys, tempfile, os, sys
        icon = self._h(app_id)                # existing _h() = hex
        if icon:                              # fast path: hex → hue
            r,g,b = (int(icon[i:i+2],16)/255 for i in (0,2,4))
            return colorsys.rgb_to_hsv(r,g,b)[0]*360

        # Slow path: ask macOS sips for pixel sample
        try:
            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                # First convert to PNG
                subprocess.run(["sips","-s","format","png",self._icn(app_id),
                                "--out",tmp.name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # Then get pixel color - use simpler format
                out = subprocess.check_output(["sips","-g","pixelHex",tmp.name], stderr=subprocess.DEVNULL)
            # Parse simple format: pixelHex: RRGGBB
            match = re.search(r'pixelHex:\s*([0-9A-Fa-f]{6})', out.decode())
            if match:
                hexcol = match.group(1)
                r,g,b = (int(hexcol[i:i+2],16)/255 for i in (0,2,4))
                return colorsys.rgb_to_hsv(r,g,b)[0]*360
            return 999.0
        except Exception:
            return 999.0                      # grey / error

    def suggest_order(self, style: str | None = None):
        """Return list of bundle-ids sorted by score (default) or style == "rainbow"."""
        import json, pathlib
        all_apps = set(self.wanted_counter) | set(self.landed_counter)
        
        if style == "rainbow":
            return sorted(all_apps, key=lambda a: self._icon_hue(a))
        
        # ---------- order: everything the learner knows ----------
        # `all_apps` already includes every pinned & seen app, so
        # just return it – no baked-in defaults.
        return list(all_apps)

    # ---------- recording ----------
    def record(self, wanted: str, landed: str):
        self.wanted_counter[wanted] += 1
        self.landed_counter[landed] += 1
        if wanted != landed:
            self.misclick_counter[(wanted, landed)] += 1

    # ---------- loading ----------
    @classmethod
    def load(cls, filename="dock_stats.json"):
        """Load DockStats from JSON file."""
        import json
        from pathlib import Path
        
        instance = cls()
        stats_file = Path(filename)
        
        if stats_file.exists():
            data = json.loads(stats_file.read_text())
            
            # Load wanted counter
            if "wanted" in data:
                instance.wanted_counter.update(data["wanted"])
            
            # Load landed counter
            if "landed" in data:
                instance.landed_counter.update(data["landed"])
            
            # Load misclick counter (convert from "app1|app2" format to (app1, app2) tuples)
            if "mis" in data:
                for key, count in data["mis"].items():
                    if "|" in key:
                        wanted, landed = key.split("|", 1)
                        instance.misclick_counter[(wanted, landed)] = count
        
        # Add 'mis' as alias for misclick_counter for compatibility
        instance.mis = instance.misclick_counter
        return instance
    
    def _all(self):
        """Return all tracked app IDs."""
        return list(set(self.wanted_counter) | set(self.landed_counter))
    
    def reorder(self, order):
        """Reorder dock with given app order list."""
        # This would interface with macOS dock reordering
        # For now, just print the order
        print(f"Reordering dock: {order}")

