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
        ordered = seed + [a for a in all_apps if a not in seed]
        return ordered

    # ---------- recording ----------
    def record(self, wanted: str, landed: str):
        self.wanted_counter[wanted] += 1
        self.landed_counter[landed] += 1
        if wanted != landed:
            self.misclick_counter[(wanted, landed)] += 1
PY
"""Core logic for DockBeautifier."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import List, Tuple

