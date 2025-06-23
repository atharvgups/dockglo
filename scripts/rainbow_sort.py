#!/usr/bin/env python3
"""Re-orders the current Dock left→right by icon color (hue)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_logic import DockStats
ds = DockStats.load()
order = sorted(ds._all(), key = ds._icon_hue)   # rainbow
ds.reorder(order)
