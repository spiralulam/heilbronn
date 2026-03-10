# Heilbronn's Triangle Problem

Code and data for the paper

> N. Sudermann-Merx, *From Computational Certification to Exact Coordinates: Heilbronn's Triangle Problem on the Unit Square*, 2026.

<p align="center">
  <img src="figures/fig_n=9.png" alt="Optimal configuration for n = 9" width="350"/>
</p>

## Contents

- **optimization_models/** — Gurobi MIP formulations (baseline and strengthened)
- **best-known-configurations/** — Point configurations for n = 3, …, 16 as JSON
- **exact_coordinates/** — Exact symbolic coordinates for n = 5, …, 9 (SymPy)
- **figures/** — Configuration plots

## Requirements

- Python ≥ 3.9
- [Gurobi](https://www.gurobi.com/) ≥ 11.0 (for the MIP models)
- [SymPy](https://www.sympy.org/) ≥ 1.14 (for the exact coordinates)

## Usage

```bash
python optimization_models/heilbronn_final.py
python exact_coordinates/exact_coordinates.py 7
```

## Citation

```bibtex
@article{SudermannMerx2026Heilbronn,
  author  = {Sudermann-Merx, Nathan},
  title   = {From Computational Certification to Exact Coordinates:
             {Heilbronn}'s Triangle Problem on the Unit Square},
  year    = {2026},
}
```

## License

MIT
