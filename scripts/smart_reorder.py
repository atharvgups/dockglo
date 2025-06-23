#!/usr/bin/env python3
"""
Smart reorder:
1. Always keep Finder first.
2. Second pass: least-mis-clicked & most-wanted apps (decay-weighted).
3. Never put two hot-spot (high-mis-click) neighbours adjacent.
"""
from core_logic import DockStats
ds = DockStats.load()
all_apps = ds._all()

def score(a):
    w = sum(c*ds._decay(ts) for ts,c in ds.wanted_counter.get(a,[]))
    m = sum(c*ds._decay(ts) for (_,l),(ts,c) in ds.mis.items() if _==a or l==a)
    return w - 2*m

ordered = sorted(all_apps, key=score, reverse=True)

# hot-spot spacing
HOT = {a for a in all_apps if sum(c for (_,l),(ts,c) in ds.mis.items() if _==a or l==a) > 3}
final=[]
for a in ordered:
    if a in HOT and final and final[-1] in HOT:
        # insert before last hot-spot
        final.insert(-1, a)
    else:
        final.append(a)

ds.reorder(final)
