#!/usr/bin/env python3
"""
Every run:
  * Ask macOS which app is front-most.
  * Append {"time": "...", "bid": "..."} to usage_log.jsonl
"""
import json, subprocess, datetime, pathlib
out = subprocess.check_output(
    ["osascript", "-e", 'tell application "System Events" to get bundle identifier of first application process whose frontmost is true']
).decode().strip()
entry = {"time": datetime.datetime.utcnow().isoformat(), "bid": out}
path = pathlib.Path("usage_log.jsonl")
path.write_text((path.read_text() if path.exists() else "") + json.dumps(entry)+"\n")
