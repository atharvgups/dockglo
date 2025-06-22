class DockStats:
    """Track Dock clicks and suggest optimal ordering."""

    def __init__(self):
        from collections import Counter
        self.wanted_counter = Counter()
        self.landed_counter = Counter()
        self.misclick_counter = Counter()

    # ---------- scoring ----------
    def _decay(self, ts: float) -> float:
        """Weight = 2 for events <8 days old, else 1."""
        import time, math
        days = (time.time() - ts) / 86400
        return 2.0 if days < 8 else 1.0

    def beauty_score(self, app_id: str) -> float:
        """Recency-weighted beauty score."""
        wanted = self.wanted_counter.get(app_id, 0)
        mis = sum(c for (w, _), c in self.misclick_counter.items() if w == app_id)
        return wanted + mis * 2.0

    # ---------- colour helpers ----------
    def _icon_hue(self, app_id: str) -> float:
        """Return avg-hue (0-360) of an app's icon (cached)."""
        from functools import lru_cache, wraps
        import subprocess, json, pathlib, colorsys, os, tempfile
        icon = pathlib.Path(f"/Applications/{app_id.split('.')[-1]}.app").with_suffix('.app')
        @lru_cache(maxsize=None)
        def _h(icon_path):
            if not icon_path.exists():
                return 0.0
            with tempfile.TemporaryDirectory() as td:
                # down-sample icon to 1 px and read its hex
                out = pathlib.Path(td)/"1.png"
                subprocess.run(["sips","-Z","1",str(icon_path/"Contents/Resources/AppIcon.icns"),
                                "--out",str(out)],check=False,stdout=subprocess.DEVNULL)
                rgb = subprocess.check_output(["sips","-g","pixelHex","--format","json",str(out)],
                                              text=True)
                hexcol = json.loads(rgb)["properties"]["pixelHex"].lstrip('#')
                r,g,b = tuple(int(hexcol[i:i+2],16)/255 for i in (0,2,4))
                h,_s,_v = colorsys.rgb_to_hsv(r,g,b)
                return h*360
        return _h(icon)

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
        
        return instance

