class DockStats:
    """Track Dock clicks and suggest optimal ordering."""

    def __init__(self):
        from collections import Counter
        self.wanted_counter = Counter()
        self.landed_counter = Counter()
        self.misclick_counter = Counter()

    # ---------- scoring ----------
    def beauty_score(self, app_id: str) -> float:
        wanted = self.wanted_counter.get(app_id, 0)
        mis = sum(c for (w, _), c in self.misclick_counter.items() if w == app_id)
        return wanted + mis * 2.0

    def suggest_order(self):
        import json, pathlib
        all_apps = set(self.wanted_counter) | set(self.landed_counter)
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

