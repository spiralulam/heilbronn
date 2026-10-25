# Computational study (Section 4 of the paper)

Every computational number in the revised paper comes from this folder: one
machine (Apple MacBook Pro, M5 Pro, 15-core CPU, 48 GB), one solver version
(Gurobi 13.0.3, plus 11.0.1 for block F), one script. `tables.py` writes the
LaTeX tables of Section 4.

## Run plan (`plan.py`, 69 runs, about 3 days)

| Block | Runs | Purpose |
|---|---|---|
| A | final model, n=5..9, 5 seeds, 12 h limit | main results, performance variability |
| B | models for boundary types II and III, n=5..9, 4 h | completeness of the case split |
| C | baseline model, n=5..7, 4 h | effect of all enhancements together |
| D | ablation for n=7..9, 4 h: without boundary pattern, sign fixing, interior order, product substitution, cap z <= Delta_{n-1}; fixed signs without binaries; with strip capacities; with the contact conditions of Lemma 2(C) | contribution of each component |
| E | warm start from the best-known solution, n=7..9, 4 h | effect of a known incumbent |
| F | final model under Gurobi 11.0.1, n=7..9, 4 h | solver-version effect in the comparison with Monji et al. |
| G | final model, n=10, 48 h | outlook |
| post | `post.py`: exact verification, copies of the optimum, distinct areas, LICQ, running time of the symbolic step | Sections 3, 5, 6, 7 |

## Running it

```bash
./setup_env.sh          # .venv-g13 (Gurobi 13.0.3) and .venv-g11 (Gurobi 11.0.1), Python 3.12
./run.sh --smoke        # every block once at n=5, results in smoke/
./run.sh                # the batch, log in batch.log; a restart skips finished runs
./run.sh --list         # progress
.venv-g13/bin/python post.py
.venv-g13/bin/python tables.py
```

A Gurobi license is required. Before publishing logs, remove the license
lines with `python3 redact_logs.py out/logs/*.log batch.log`.

## Files

- `model.py`: the MINLP models (final model, baseline, types II and III, ablation options)
- `plan.py`, `run.py`, `run_one.py`, `run.sh`: run plan and driver
- `known_optima.py`: best-known configurations labeled for the final model (warm start)
- `post.py`, `tables.py`, `placeholders.py`: post-processing, tables, summary of the numbers
- `out/`: results, solutions and (redacted) Gurobi logs of the runs reported in the paper
