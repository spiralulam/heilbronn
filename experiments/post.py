"""Block H: everything that needs no MINLP solver, run after the batch.

  1. Exact verification of the configurations of Section 5
     (all C(n,3) areas in exact arithmetic), ../verification/verify_exact.py
  2. Exact count of the copies of each optimum feasible for P*,
     ../verification/count_copies.py (exact arithmetic)
  3. Critical and distinct triangle areas for n = 5..16, ../verification/distinct_areas.py
  4. Runtime of the symbolic Step 2, fed with the NEW Gurobi solutions of
     block A (seed 0) and block G (n=10), using ../exact_coordinates/exact_coordinates.py.
     The hand-written ansaetze expect the labeled copies in
     ../exact_coordinates/solver_solutions_square, so each new solution is first mapped onto that copy by a
     symmetry of the square and a relabeling. If no copy matches (n=6, whose
     optima form a family), Step 2 runs on the reference copy instead.

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
from itertools import permutations
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parent / "verification"
PIPELINE = HERE.parent / "exact_coordinates" / "exact_coordinates.py"
OUT = HERE / "out" / "post"
REFERENCE = HERE.parent / "exact_coordinates" / "solver_solutions_square"
MATCH_TOL = 1e-4

D4 = [lambda x, y: (x, y), lambda x, y: (1 - y, x), lambda x, y: (1 - x, 1 - y),
      lambda x, y: (y, 1 - x), lambda x, y: (1 - x, y), lambda x, y: (x, 1 - y),
      lambda x, y: (y, x), lambda x, y: (1 - y, 1 - x)]
FIXED = {"x[0]": 0.0, "y[1]": 0.0, "x[2]": 1.0, "y[3]": 1.0, "x[4]": 0.0}


def run_script(name):
    t0 = time.time()
    p = subprocess.run([sys.executable, name], cwd=CODE, capture_output=True, text=True)
    (OUT / f"{Path(name).stem}.txt").write_text(p.stdout + p.stderr)
    print(f"{name}: {time.time() - t0:.1f}s, exit {p.returncode}")


def points(path, n):
    v = {r["VarName"]: r["X"] for r in json.loads(path.read_text())["Vars"]}
    v.update(FIXED)
    return [(v[f"x[{i}]"], v[f"y[{i}]"]) for i in range(n)], v["z"]


def map_to_reference(new, ref):
    """Symmetry g and labeling that map the new points onto the reference ones.

    Returns (mapped points in the labels of ref, max distance) or None."""
    n = len(ref)
    for g in D4:
        img = [g(*p) for p in new]
        lab, used = [], set()
        for q in ref:     # nearest unused image point for every reference label
            j = min((j for j in range(n) if j not in used),
                    key=lambda j: (img[j][0] - q[0]) ** 2 + (img[j][1] - q[1]) ** 2)
            used.add(j)
            lab.append(j)
        mapped = [img[j] for j in lab]
        dist = max(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for a, b in zip(mapped, ref))
        if dist < MATCH_TOL:
            return mapped, dist
    return None


def write_solution(path, pts, z):
    vars_ = [dict(VarName=f"{c}[{i}]", X=p[k]) for i, p in enumerate(pts)
             for k, c in enumerate("xy") if f"{c}[{i}]" not in FIXED]
    path.write_text(json.dumps(dict(Vars=vars_ + [dict(VarName="z", X=z)])))


def symbolic_times():
    sol_dir = OUT / "solutions_for_pipeline"
    sol_dir.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("exact_coordinates", PIPELINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SOLUTION_DIR = sol_dir
    times = {}
    for n in range(5, 11):
        src = HERE / "out" / "solutions" / (f"A_full_n{n}_s0.json" if n < 10 else "G_full_n10_s0.json")
        if not src.exists():
            times[n] = "missing solution"
            continue
        ref_file = REFERENCE / f"solution_n={n}.json"
        new, z = points(src, n)
        ref, _ = points(ref_file, n)
        hit = map_to_reference(new, ref)
        dst = sol_dir / f"solution_n={n}.json"
        if hit:
            write_solution(dst, hit[0], z)
            source = f"new seed-0 solution, mapped onto the reference copy (max distance {hit[1]:.1e})"
        else:
            shutil.copy(ref_file, dst)
            source = "reference solution (no copy of the new solution matches it)"
        buf = io.StringIO()
        t0 = time.time()
        try:
            with redirect_stdout(buf):
                mod.SOLVERS[n]()
            times[n] = dict(seconds=time.time() - t0, ok=True, source=source)
        except Exception as e:      # the ansatz may not match a different symmetric copy
            times[n] = dict(seconds=time.time() - t0, ok=False, error=repr(e), source=source)
        (OUT / f"symbolic_n{n}.txt").write_text(buf.getvalue())
        print(f"symbolic n={n}: {times[n]}")
    (OUT / "symbolic_times.json").write_text(json.dumps(times, indent=1))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for s in ("verify_exact.py", "count_copies.py", "distinct_areas.py", "licq_check.py"):
        run_script(s)
    symbolic_times()
