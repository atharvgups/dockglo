#!/usr/bin/env python3
"""Re-orders the current Dock left→right by icon color (hue)."""
from core_logic import DockStats
ds = DockStats.load()
order = sorted(ds._all(), key = ds._icon_hue)   # rainbow
ds.reorder(order)
