"""Collect the numbers for the red \\tbd{} placeholders of the paper and the letter.

Reads out/results/*.json, out/solutions/*.json and out/post/ (written by run.py
and post.py) and prints, for every placeholder, the value and where it goes.
Nothing is written into the paper: the author checks the values first.

    .venv-g13/bin/python placeholders.py            # report
    .venv-g13/bin/python placeholders.py --out FILE # also write it as Markdown
"""
import argparse
import json
import statistics as st
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE / "out" / "results"
POST = HERE / "out" / "post"


def load_results():
    rows = {}
    for f in sorted(RES.glob("*.json")):
        r = json.loads(f.read_text())
        if r.get("finished"):
            rows[r["spec"]["id"]] = r
    return rows


def pick(rows, **kw):
    return [r for r in rows.values() if all(r["spec"].get(k) == v for k, v in kw.items())]


def solved(r):
    return r["status"] == 2


def fmt_time(r):
    t = r["runtime"]
    return f"{t:.1f} s" + ("" if solved(r) else f" (status {r['status']}, limit reached)")


def margins(points):
    """Critical-area spread, gap to the next area, and boundary deviation of a numerical solution."""
    A = sorted(abs(((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / 2)
               for a, b, c in combinations(points, 3))
    amin = A[0]
    crit = [a for a in A if a - amin < 1e-5]
    nxt = A[len(crit)] if len(crit) < len(A) else None
    dev = max(min(abs(c), abs(1 - c)) for p in points for c in p if min(abs(c), abs(1 - c)) < 1e-3)
    return dict(n_crit=len(crit), crit_spread=crit[-1] - amin, next_gap=(nxt - amin) if nxt else None,
                rel_gap=((nxt - amin) / amin) if nxt else None, max_boundary_dev=dev)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--root", help="alternative output folder (default: out/)")
    a = ap.parse_args()
    global RES, POST
    if a.root:
        RES, POST = Path(a.root) / "results", Path(a.root) / "post"
    rows = load_results()
    L = []
    say = L.append
    say(f"# Placeholder values ({len(rows)} finished runs)\n")

    # main results
    say("## Main results (block A, 5 seeds)\n")
    for n in range(5, 10):
        rs = pick(rows, block="A", n=n)
        if not rs:
            say(f"- n={n}: no results yet")
            continue
        ts = [r["runtime"] for r in rs]
        say(f"- n={n}: median {st.median(ts):.1f} s, range {min(ts):.1f}-{max(ts):.1f} s, "
            f"all optimal: {all(map(solved, rs))}, best objective {max(r['objval'] or 0 for r in rs):.8f}")
    a9 = pick(rows, block="A", n=9)
    if a9:
        say(f"\n**Abstract, 1.4, 1.6 ('X minutes' for n=9):** median {st.median(r['runtime'] for r in a9) / 60:.1f} minutes")
    a8 = pick(rows, block="A", n=8, seed=0)
    if a8:
        say(f"**4.1 (objective reported for n=8, exact 0.07237642):** {a8[0]['objval']:.8f}")
    a7 = pick(rows, block="A", n=7, seed=0)
    if a7:
        say(f"**5.2 (Gurobi time for n=7):** {fmt_time(a7[0])}")
    thr = sorted({r.get("threads_used") for r in rows.values() if r.get("threads_used")})
    say(f"**4.1 (threads used):** {thr}")

    # remark in 5.1 and the deviation in 5.2
    say("\n## Remark in 5.1 (margins of the numerical solutions, seed 0)\n")
    for n in range(5, 10):
        rs = pick(rows, block="A", n=n, seed=0)
        if rs and rs[0].get("points"):
            m = margins(rs[0]["points"])
            say(f"- n={n}: {m['n_crit']} critical, spread of critical areas {m['crit_spread']:.1e}, "
                f"gap to next area {m['next_gap']:.3g} ({100 * m['rel_gap']:.1f} %), "
                f"max boundary deviation {m['max_boundary_dev']:.1e}")
    say("Check: gap >> 1e-6 (tolerance) and boundary deviation < 1e-6, as the remark claims. "
        "For n=7 the spread of the critical areas fills the '5e-7' placeholder in 5.2.")

    # types II and III
    say("\n## Types II and III (block B)\n")
    for n in range(5, 10):
        cells = []
        for v in ("type2", "type3"):
            rs = pick(rows, block="B", n=n, variant=v)
            cells.append(f"{v}: bound {rs[0]['objbound']:.8f}, {fmt_time(rs[0])}" if rs else f"{v}: -")
        ref = pick(rows, block="A", n=n, seed=0)
        refv = f"type I value {ref[0]['objval']:.8f}" if ref else ""
        say(f"- n={n}: " + " | ".join(cells) + (f" | {refv}" if refv else ""))

    # baseline
    say("\n## Baseline (block C, 3.1)\n")
    for n in (5, 6, 7):
        rs = pick(rows, block="C", n=n)
        say(f"- n={n}: {fmt_time(rs[0])}, gap {rs[0]['mipgap']}" if rs else f"- n={n}: -")

    # ablation, warm start, Gurobi 11
    say("\n## Ablation (D), warm start (E), Gurobi 11.0.1 (F), seed 0, times in s\n")
    variants = [("full (A)", dict(block="A", variant="full", seed=0), {})] + [
        (k, dict(block="D", variant="full"), {k: v}) for k, v in
        (("nobound", True), ("signfix", False), ("order", False), ("wsub", False), ("cap", False),
         ("freebin", True), ("strips", True), ("contacts", True))] + [
        ("warm start (E)", dict(block="E"), {}), ("Gurobi 11.0.1 (F)", dict(block="F"), {})]
    for name, kw, opts in variants:
        cells = []
        for n in (7, 8, 9):
            rs = [r for r in pick(rows, n=n, **kw) if r["spec"]["opts"] == opts]
            cells.append(fmt_time(rs[0]) if rs else "-")
        say(f"- {name}: " + " | ".join(cells))
    say("Rule: the 'contacts' variant goes into the paper ONLY IF it is faster than full (A).")

    # effort comparison
    b9 = [pick(rows, block="B", n=9, variant=v) for v in ("type2", "type3")]
    a9s0 = pick(rows, block="A", n=9, seed=0)
    if a9s0 and all(b9):
        tot = a9s0[0]["runtime"] + sum(x[0]["runtime"] for x in b9)
        say(f"\n**4.6, Table effort (this paper, Gurobi 13.0.3, I + II + III, seed 0):** {tot:.0f} s")
    f9 = pick(rows, block="F", n=9)
    if f9:
        say(f"**4.6, Table effort (this paper, Gurobi 11.0.1, type I only):** {fmt_time(f9[0])}")

    # n = 10
    g = pick(rows, block="G")
    if g:
        r = g[0]
        gap = (r["objbound"] - r["objval"]) / r["objval"] if r["objval"] else None
        say(f"\n**4.7 / outlook (n=10, 48 h):** {fmt_time(r)}, objective {r['objval']}, bound {r['objbound']}, "
            f"relative gap {gap:.2%}" if gap is not None else "")

    # post-processing
    say("\n## Post-processing (post.py)\n")
    sym = POST / "symbolic_times.json"
    if sym.exists():
        t = json.loads(sym.read_text())
        say(f"- Step 2 (5.1): {json.dumps(t)}")
    ver = POST / "verify_exact.txt"
    if ver.exists():
        tot = sum(float(l.split("time=")[1].rstrip("s\n")) for l in ver.read_text().splitlines() if "time=" in l)
        say(f"- exact verification, total (Section 6): {tot:.1f} s")

    text = "\n".join(L)
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n")


if __name__ == "__main__":
    main()
