#!/usr/bin/env python3
from pathlib import Path, PurePath
import json, collections, rich, sys

log = Path("usage_log.jsonl")
if not log.exists():
    print("🔍  No usage_log.jsonl yet – click some Dock icons then re-run.")
    sys.exit(0)

want = collections.Counter(); land = collections.Counter()
for line in log.read_text().splitlines():
    ev = json.loads(line);  want[PurePath(ev["wanted"]).name]+=1; land[PurePath(ev["landed"]).name]+=1

t = rich.table.Table(title="DockGlo click stats", show_lines=True)
t.add_column("App"); t.add_column("Wanted", justify="right"); t.add_column("Landed", justify="right")
for app,w in want.most_common(): t.add_row(app,str(w),str(land[app]))
rich.print(t)
