# Exact Coordinates

Derives exact symbolic coordinates for the Heilbronn configurations
(n = 5, …, 10) from the numerical Gurobi solutions in `solver_solutions_square/`.
These are the seed-0 solutions of the revision runs (`../experiments/out/solutions/`),
mapped by a symmetry of the square and a relabeling onto the copy the hand-written
ansatz expects (n = 6: the solution of the first submission, since the optima form a family;
n = 10: the solution of the n = 10 run, `G_full_n10_s0.json`).
The configurations are proven optimal for n ≤ 8. For n = 9 and n = 10 they are optimal
within solver tolerances, without a rigorous proof. For n = 10, Step 2 adds a stationarity
condition, since the equal-area system alone leaves a one-parameter family (see `solve_n10`).

## Requirements

- Python 3.11+, SymPy 1.14+

## Usage

```bash
python exact_coordinates.py       # all cases
python exact_coordinates.py 7     # single case
```
