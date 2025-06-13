from openai import OpenAI
import subprocess, json, os, pathlib, textwrap
REPO = pathlib.Path(__file__).parent; ENV=dict(os.environ, LC_ALL="en_US.UTF-8")
SYSTEM="""You are DockGlo-Agent. Edit files & run shell cmds until pytest passes and Dock snapshot works.
Return JSON: {"edit":[{"path":"...","content":"..."}],"cmd":["..."],"msg":"..."}.
Stop when msg starts with DONE."""
thread=[{"role":"system","content":SYSTEM},{"role":"user","content":"First plan?"}]
client=OpenAI(timeout=30)
while True:
    res=client.chat.completions.create(model="gpt-4o-mini",messages=thread).choices[0].message
    plan=json.loads(res.content); thread.append({"role":"assistant","content":res.content})
    for e in plan.get("edit",[]): (REPO/e["path"]).write_text(e["content"])
    out=[]
    for c in plan.get("cmd",[]): out.append(f"$ {c}\n"+subprocess.run(c,shell=True,cwd=REPO,
        env=ENV,capture_output=True,text=True).stdout)
    test=subprocess.run("pytest -q",shell=True,cwd=REPO,env=ENV,
        capture_output=True,text=True); out.append("pytest:\n"+test.stdout+test.stderr)
    thread.append({"role":"user","content":textwrap.shorten(''.join(out),4000)})
    if plan.get("msg","").lower().startswith("done"): print("🎉 DONE"); break
