from openai import OpenAI
import subprocess, json, os, pathlib, textwrap, time, sys

REPO = pathlib.Path(__file__).parent
ENV  = dict(os.environ, LC_ALL="en_US.UTF-8")
client = OpenAI(timeout=30)

SYSTEM = """You are DockGlo-Agent.
Edit repo files and run shell commands until:
 • DockGloTap compiles,
 • pytest passes,
 • mac/reorder_and_apply.sh apply succeeds without "?" icons.
Return only JSON:
{"edit":[{"path":"file","content":"full file"}],
 "cmd":["bash ...","pytest -q"],
 "msg":"description"}
Stop when msg starts with DONE.
"""

thread = [
    {"role":"system","content": SYSTEM},
    {"role":"user","content":
       "First task: compile DockGloTap.swift, run pytest, then echo DONE."
    }
]

def run(cmd):
    p = subprocess.run(cmd, shell=True, cwd=REPO, env=ENV,
                       capture_output=True, text=True)
    return f"$ {cmd}\n{p.stdout}{p.stderr}"

while True:
    print("⏳ OpenAI call…", flush=True)
    reply = client.chat.completions.create(
        model="gpt-4o-mini", messages=thread).choices[0].message
    plan = json.loads(reply.content)
    thread.append({"role":"assistant","content": reply.content})

    # apply edits
    for e in plan.get("edit", []):
        (REPO/e["path"]).write_text(e["content"])
    # run commands & collect output
    out = []
    for c in plan.get("cmd", []):
        out.append(run(c))
    out.append(run("pytest -q"))

    # feed back
    thread.append({"role":"user","content":
        textwrap.shorten('\n'.join(out), 4000)})

    if plan.get("msg","").lower().startswith("done"):
        print("🎉 DONE – agent finished.")
        sys.exit(0)
