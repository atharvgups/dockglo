"""Core logic for DockBeautifier."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import List, Tuple

class DockStats:
    def __init__(self) -> None:
        self.wanted: Counter[str] = Counter()
        self.landed: Counter[str] = Counter()
        self.mis: Counter[Tuple[str, str]] = Counter()

    # ---------- data collection ---------- #
    def record(self, wanted: str, landed: str) -> None:
        self.wanted[wanted] += 1
        self.landed[landed] += 1
        if wanted != landed:
            self.mis[(wanted, landed)] += 1

    # ---------- scoring ---------- #
    def _score(self, app: str) -> float:
        return self.wanted[app] + 2 * sum(n for (w, _), n in self.mis.items() if w == app) \
               - 0.5 * sum(n for (_, l), n in self.mis.items() if l == app)

    def suggest_order(self) -> List[str]:
        apps = set(self.wanted) | set(self.landed)
        return sorted(apps, key=lambda a: (-self._score(a), a))

    # ---------- disk ---------- #
    def save(self, path: str = "dock_stats.json") -> None:
        Path(path).write_text(json.dumps({
            "wanted": self.wanted,
            "landed": self.landed,
            "mis": {f"{w}|{l}": n for (w, l), n in self.mis.items()},
        }, indent=2))

    @classmethod
    def load(cls, path: str = "dock_stats.json") -> "DockStats":
        ds = cls()
        if not Path(path).exists():
            return ds
        data = json.loads(Path(path).read_text())
        ds.wanted.update(data["wanted"])
        ds.landed.update(data["landed"])
        for k, n in data["mis"].items():
            w, l = k.split("|")
            ds.mis[(w, l)] = n
        return ds