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
        import pathlib
        icon_path = pathlib.Path(f"/Applications/{app_id.split('.')[-1]}.app/Contents/Resources/AppIcon.icns")
        return str(icon_path)
    
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
                subprocess.run(["sips","-s","format","png",self._icn(app_id),
                                "--out",tmp.name], check=True, stdout=subprocess.DEVNULL)
                out = subprocess.check_output(["sips","-g","pixelHex","--format","json",tmp.name])
            hx = re.search(r'"pixelHex" : "(..)(..)(..)', out.decode()).group(1,2,3)
            r,g,b = (int(x,16)/255 for x in hx)
            return colorsys.rgb_to_hsv(r,g,b)[0]*360
        except Exception:
            return 999.0                      # grey / error

    def suggest_order(self, style: str | None = None):
        """Return list of bundle-ids sorted by score (default) or style == "rainbow"."""
        import json, pathlib
        all_apps = set(self.wanted_counter) | set(self.landed_counter)
        
        if style == "rainbow":
            return sorted(all_apps, key=lambda a: self._icon_hue(a))
        
        # Default behavior - use beauty score with seed apps
        seed = []
        f = pathlib.Path("defaults.json")
        if f.exists():
            seed = json.loads(f.read_text()).get("pinned", [])
        # Sort remaining apps by beauty score (descending - higher scores first)
        remaining_apps = [a for a in all_apps if a not in seed]
        remaining_apps.sort(key=self.beauty_score, reverse=True)
        ordered = seed + remaining_apps
        return ordered

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

