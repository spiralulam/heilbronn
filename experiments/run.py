"""Work through the run plan, one Gurobi run at a time.

  python run.py                 all blocks A..G in plan order
  python run.py --blocks A,B    only these blocks
  python run.py --smoke         every block once at n=5 (n=7 for F), 60 s limit,
                                results go to smoke/ instead of out/
  python run.py --list          show what is done and what is pending

Finished runs (out/results/<id>.json with "finished": true) are skipped, so the
batch can be interrupted and restarted at any time. Each run is a separate
process, so a crash or license problem in one run does not stop the batch.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from plan import RUNS

HERE = Path(__file__).resolve().parent
ENVS = {"g13": HERE / ".venv-g13" / "bin" / "python",
        "g11": HERE / ".venv-g11" / "bin" / "python"}


def done(out, rid):
    f = out / "results" / f"{rid}.json"
    try:
        return json.loads(f.read_text()).get("finished", False)
    except (OSError, ValueError):
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", default="A,B,C,D,E,F,G")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    blocks = set(a.blocks.split(","))
    runs = [r for r in RUNS if r["block"] in blocks]
    out = HERE / ("smoke" if a.smoke else "out")
    if a.smoke:
        seen, smoke = set(), []
        for r in runs:
            key = (r["block"], r["variant"], json.dumps(r["opts"], sort_keys=True), r["warmstart"])
            if key in seen:
                continue
            seen.add(key)
            s = dict(r, n=7 if r["block"] in "EF" else 5, seed=0, timelimit=60)
            s["id"] = "smoke_" + r["id"].rsplit("_n", 1)[0] + f"_n{s['n']}"
            smoke.append(s)
        runs = smoke

    if a.list:
        for r in runs:
            print(("done    " if done(out, r["id"]) else "pending ") + r["id"])
        return

    for r in runs:
        if done(out, r["id"]):
            continue
        py = ENVS[r["env"]]
        if not py.exists():
            print(f"[{r['id']}] SKIPPED: environment {r['env']} missing ({py})", flush=True)
            continue
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} start {r['id']}", flush=True)
        slack = 3600 if r.get("timelimit") else None
        try:
            subprocess.run([str(py), str(HERE / "run_one.py"), json.dumps(r), str(out)],
                           cwd=HERE, check=False,
                           timeout=(r["timelimit"] + slack) if slack else None)
        except subprocess.TimeoutExpired:
            print(f"[{r['id']}] killed after timeout", flush=True)


if __name__ == "__main__":
    sys.exit(main())
