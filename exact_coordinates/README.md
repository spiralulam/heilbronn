# Exact Coordinates

Derives exact symbolic coordinates for the Heilbronn configurations
(n = 5, …, 9) from the numerical Gurobi solutions in `solver_solutions_square/`.
The configurations are proven optimal for n ≤ 8. For n = 9 they are optimal
within solver tolerances, without a rigorous proof.

## Requirements

- Python 3.11+, SymPy 1.14+

## Usage

```bash
python exact_coordinates.py       # all cases
python exact_coordinates.py 7     # single case
```
