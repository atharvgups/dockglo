#!/usr/bin/env python3
"""Generate fake Dock click-stream for dev use."""
import random
from core_logic import DockStats

APPS = [
    "com.apple.Safari", "com.apple.finder", "com.apple.Mail",
    "com.microsoft.VSCode", "com.spotify.client",
    "com.google.Chrome", "com.apple.Terminal"
]

def main() -> None:
    random.seed(42)
    stats = DockStats()
    for _ in range(1_000):
        wanted = random.choices(APPS, weights=[20,15,12,18,10,16,9])[0]
        landed = wanted if random.random() < 0.85 else random.choice([a for a in APPS if a != wanted])
        stats.record(wanted, landed)
    stats.save()
    print("Suggested order:", stats.suggest_order())

if __name__ == "__main__":
    main()