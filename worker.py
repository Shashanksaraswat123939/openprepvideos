# Renders every valid script in scripts/ that has no video in out/ yet, in manifest order. Keeps watching until all are done.
#   python worker.py            run until all videos exist (or --once to do one pass)
import json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
items = json.load(open("manifest.json", encoding="utf-8")); os.makedirs("logs", exist_ok=True)
if "--only" in sys.argv: items = [it for it in items if it["id"] == sys.argv[sys.argv.index("--only") + 1]]
SHARD, SHARDS = 0, 1
if "--shard" in sys.argv: SHARD, SHARDS = [int(v) for v in sys.argv[sys.argv.index("--shard") + 1].split("/")]
def log(m):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + m; print(line, flush=True); open(f"logs/worker{SHARD}.log" if SHARDS > 1 else "logs/worker.log", "a", encoding="utf-8").write(line + "\n")
def pass_once():
    did = 0
    for n, it in enumerate(items):
        if n % SHARDS != SHARD: continue
        i = it["id"]; sp = f"scripts/{i}.json"; mp = f"out/{i}.mp4"
        if os.path.exists(mp) or not os.path.exists(sp) or os.path.exists(f"scripts/{i}.errors.txt") and os.path.getmtime(f"scripts/{i}.errors.txt") > os.path.getmtime(sp): continue
        log(f"render {i}")
        r = subprocess.run([sys.executable, "render.py", sp], capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})
        if r.returncode == 0 and os.path.exists(mp): log(f"done {i}"); did += 1
        else:
            open(f"scripts/{i}.errors.txt", "w", encoding="utf-8").write((r.stdout + "\n" + r.stderr)[-4000:]); log(f"FAILED {i} (see scripts/{i}.errors.txt)")
    return did
if __name__ == "__main__":
    while True:
        pass_once(); left = [it["id"] for n, it in enumerate(items) if n % SHARDS == SHARD and not os.path.exists(f"out/{it['id']}.mp4")]
        if "--once" in sys.argv or not left: break
        have = [i for i in left if os.path.exists(f"scripts/{i}.json")]; log(f"{len(items) - len(left)} done, {len(have)} scripts waiting, {len(left) - len(have)} scripts not written yet"); time.sleep(60)
    log("worker finished")
