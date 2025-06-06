#!/usr/bin/env python3
"""Print optimal Dock order (one bundle-ID per line)."""
from core_logic import DockStats
for app in DockStats.load().suggest_order():
    print(app)