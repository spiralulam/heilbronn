"""Block H: everything that needs no MINLP solver, run after the batch.

  1. Exact verification of the configurations of Section 5
     (all C(n,3) areas in exact arithmetic), ../verification/verify_exact.py
  2. Exact count of the copies of each optimum feasible for P*,
     ../verification/count_copies.py (exact arithmetic)
  3. Critical and distinct triangle areas for n = 5..16, ../verification/distinct_areas.py
  4. Runtime of the symbolic Step 2, fed with the NEW Gurobi solutions of
     block A (seed 0), using ../exact_coordinates/exact_coordinates.py

Output: out/post/*.txt and out/post/symbolic_times.json
"""
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parent / "verification"
PIPELINE = HERE.parent / "exact_coordinates" / "exact_coordinates.py"
OUT = HERE / "out" / "post"


def run_script(name):
    t0 = time.time()
    p = subprocess.run([sys.executable, name], cwd=CODE, capture_output=True, text=True)
    (OUT / f"{Path(name).stem}.txt").write_text(p.stdout + p.stderr)
    print(f"{name}: {time.time() - t0:.1f}s, exit {p.returncode}")


def symbolic_times():
    sol_dir = OUT / "solutions_for_pipeline"
    sol_dir.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("exact_coordinates", PIPELINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SOLUTION_DIR = sol_dir
    times = {}
    for n in range(5, 10):
        src = HERE / "out" / "solutions" / f"A_full_n{n}_s0.json"
        if not src.exists():
            times[n] = "missing solution"
            continue
        shutil.copy(src, sol_dir / f"solution_n={n}.json")
        buf = io.StringIO()
        t0 = time.time()
        try:
            with redirect_stdout(buf):
                mod.SOLVERS[n]()
            times[n] = dict(seconds=time.time() - t0, ok=True)
        except Exception as e:      # the ansatz may not match a different symmetric copy
            times[n] = dict(seconds=time.time() - t0, ok=False, error=repr(e))
        (OUT / f"symbolic_n{n}.txt").write_text(buf.getvalue())
        print(f"symbolic n={n}: {times[n]}")
    (OUT / "symbolic_times.json").write_text(json.dumps(times, indent=1))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for s in ("verify_exact.py", "count_copies.py", "distinct_areas.py", "licq_check.py"):
        run_script(s)
    symbolic_times()
