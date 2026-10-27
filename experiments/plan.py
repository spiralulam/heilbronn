"""The complete run plan of the MPC revision.

Blocks (see README.md):
  A  full model P*, n=5..9, 5 seeds              main results and variability
  B  case II and III models, n=5..10             validity of the case split (n=10: 24 h, run last)
  C  baseline P^0, n=5..7 (n=7: 1 h)             replaces the 45-minute remark
  D  ablation, one ingredient off, n=7..9        Referee 2, 3(b) and minor 1
  E  warm start from the best-known solution     Referee 2, 3(d)
  F  full model under Gurobi 11.0.1, n=7..9      solver-version effect (Monji et al.)
  G  full model, n=10, 24 h                      Referee 2, 3(c)
Order matters: the long n=10 run comes last.
"""
H1 = 3600
H4 = 4 * 3600
H12 = 12 * 3600
H24 = 24 * 3600

RUNS = []


def add(block, variant, n, seed=0, timelimit=None, env="g13", warmstart=False, **opts):
    tag = "_".join(f"{k}{int(v)}" for k, v in sorted(opts.items()))
    rid = f"{block}_{variant}{('_' + tag) if tag else ''}{'_ws' if warmstart else ''}_n{n}_s{seed}"
    RUNS.append(dict(id=rid, block=block, variant=variant, n=n, seed=seed,
                     timelimit=timelimit, env=env, warmstart=warmstart, opts=opts))


for n in range(5, 10):                      # A
    for s in range(5):
        add("A", "full", n, seed=s, timelimit=H12)
for n in range(5, 10):                      # B
    add("B", "type2", n, timelimit=H4)
    add("B", "type3", n, timelimit=H4)
for n in range(5, 8):                       # C
    add("C", "baseline", n, timelimit=H1 if n == 7 else H4)
for n in range(7, 10):                      # D
    add("D", "full", n, timelimit=H4, signfix=False)
    add("D", "full", n, timelimit=H4, order=False)
    add("D", "full", n, timelimit=H4, wsub=False)
    add("D", "full", n, timelimit=H4, cap=False)
    add("D", "full", n, timelimit=H4, freebin=True)
    add("D", "full", n, timelimit=H4, strips=True)
    add("D", "full", n, timelimit=H4, contacts=True)
    add("D", "full", n, timelimit=H4, nobound=True)
for n in range(7, 10):                      # E
    add("E", "full", n, timelimit=H4, warmstart=True)
for n in range(7, 10):                      # F
    add("F", "full", n, timelimit=H4, env="g11")
add("G", "full", 10, timelimit=H24)         # G
for v in ("type2", "type3"):                # B for n=10, added after the batch:
    add("B", v, 10, timelimit=H24)          # the G bound covers only type I

if __name__ == "__main__":
    from collections import Counter
    print(len(RUNS), "runs", dict(Counter(r["block"] for r in RUNS)))
    for r in RUNS:
        print(r["id"])
