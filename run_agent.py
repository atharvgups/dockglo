from openai import OpenAI
import subprocess, json, os, pathlib, textwrap

REPO = pathlib.Path(__file__).parent
ENV  = dict(os.environ, LC_ALL="en_US.UTF-8")
client = OpenAI()                         # needs OPENAI_API_KEY in env

SYSTEM = """You are DockGlo-Agent.
Edit files and run shell commands inside a git repo that beautifies the macOS Dock.
Goal: snapshot/undo works, Swift event-tap logs clicks, ingest updates stats, tests green.
Respond ONLY with JSON:
  { "edit":[{"path":"...","content":"..."}], "cmd":["..."], "msg":"..."}
After each loop you will receive command output + pytest results.
Stop when msg starts with DONE."""
thread=[{"role":"system","content":SYSTEM},
        {"role":"user","content":"Plan your first edits and commands."}]

while True:
    res = client.chat.completions.create(model="gpt-4o-mini",messages=thread).choices[0].message
    plan=json.loads(res.content)
    thread.append({"role":"assistant","content":res.content})

    # apply file edits
    for e in plan.get("edit",[]):
        (REPO/e["path"]).write_text(e["content"])
    # run commands
    out = []
    for c in plan.get("cmd",[]):
        proc=subprocess.run(c,shell=True,capture_output=True,text=True,cwd=REPO,env=ENV)
        out.append(f"$ {c}\n{proc.stdout}{proc.stderr}")
    # always run pytest
    proc=subprocess.run("pytest -q",shell=True,capture_output=True,text=True,cwd=REPO,env=ENV)
    out.append("pytest:\n"+proc.stdout+proc.stderr)

    # send results back
    thread.append({"role":"user","content":textwrap.dedent(f"""
    ### shell output
    {''.join(out)[:4000]}
    """)})

    if plan.get("msg","").lower().startswith("done"):
        print("🎉 Agent says DONE — exiting."); break
