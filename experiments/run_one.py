"""Run a single experiment and write results/<id>.json, logs/<id>.log and
solutions/<id>.json (Gurobi's JSON solution format).

Usage: python run_one.py '<json spec>' <outdir>
The spec is one entry of plan.py.
"""
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

import gurobipy as gp

import model as M


def machine_info():
    info = dict(platform=platform.platform(), python=platform.python_version(),
                cpu_count=os.cpu_count())
    if sys.platform == "darwin":
        def sysctl(key):
            try:
                return subprocess.run(["sysctl", "-n", key], capture_output=True,
                                      text=True).stdout.strip()
            except OSError:
                return None
        info.update(cpu=sysctl("machdep.cpu.brand_string"),
                    perf_cores=sysctl("hw.perflevel0.physicalcpu"),
                    eff_cores=sysctl("hw.perflevel1.physicalcpu"),
                    mem_bytes=sysctl("hw.memsize"))
    return info


def main():
    spec = json.loads(sys.argv[1])
    out = Path(sys.argv[2])
    for d in ("results", "logs", "solutions"):
        (out / d).mkdir(parents=True, exist_ok=True)
    rid = spec["id"]
    logfile = out / "logs" / f"{rid}.log"
    if logfile.exists():
        logfile.unlink()

    t0 = time.time()
    m, h = M.build(spec["n"], spec["variant"], **spec.get("opts", {}))
    build_time = time.time() - t0

    m.Params.LogFile = str(logfile)
    m.Params.MIPFocus = 2                 # as in the paper
    m.Params.Seed = spec.get("seed", 0)
    m.Params.JSONSolDetail = 1
    if spec.get("timelimit"):
        m.Params.TimeLimit = spec["timelimit"]
    if spec.get("threads"):
        m.Params.Threads = spec["threads"]

    if spec.get("warmstart"):
        from known_optima import labeled_for_full
        m.update()
        M.set_start(m, h, labeled_for_full(spec["n"]))

    m.optimize()

    res = dict(spec=spec, finished=True, build_time=build_time,
               status=m.Status, runtime=m.Runtime, work=getattr(m, "Work", None),
               objval=m.ObjVal if m.SolCount else None, objbound=m.ObjBound,
               mipgap=m.MIPGap if m.SolCount else None, nodecount=m.NodeCount,
               solcount=m.SolCount, n_fixed_signs=h["n_fixed_signs"],
               numvars=m.NumVars, numbinvars=m.NumBinVars, numconstrs=m.NumConstrs,
               numqconstrs=m.NumQConstrs, gurobi_version=".".join(map(str, gp.gurobi.version())),
               params={p: m.getParamInfo(p)[2] for p in
                       ("MIPGap", "MIPGapAbs", "FeasibilityTol", "IntFeasTol", "OptimalityTol",
                        "Threads", "MIPFocus", "Seed", "TimeLimit", "NonConvex")},
               machine=machine_info())
    if m.SolCount:
        res["constr_vio"] = m.ConstrVio
        res["points"] = [(h["x"][i].X if isinstance(h["x"][i], gp.Var) else h["x"][i],
                          h["y"][i].X if isinstance(h["y"][i], gp.Var) else h["y"][i])
                         for i in range(spec["n"])]
        m.write(str(out / "solutions" / f"{rid}.json"))
    # effective thread count as reported in the log
    try:
        mt = re.search(r"using up to (\d+) threads", logfile.read_text())
        res["threads_used"] = int(mt.group(1)) if mt else None
    except OSError:
        res["threads_used"] = None
    (out / "results" / f"{rid}.json").write_text(json.dumps(res, indent=1))
    print(f"[{rid}] status={m.Status} runtime={m.Runtime:.1f}s obj={res['objval']} bound={m.ObjBound}")


if __name__ == "__main__":
    main()
