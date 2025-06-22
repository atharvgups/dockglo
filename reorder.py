#!/usr/bin/env python3
"""Print optimal Dock order (one bundle-ID per line)."""
import sys
from core_logic import DockStats

# Get style parameter (default to None for score-based ordering)
style = sys.argv[1] if len(sys.argv) > 1 else None

for app in DockStats.load().suggest_order(style=style):
    print(app)
