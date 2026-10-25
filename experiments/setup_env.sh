#!/bin/bash
# Create the two Python environments for the experiments.
#   .venv-g13  Gurobi 13.0.3 (all blocks except F), SymPy, mpmath
#   .venv-g11  Gurobi 11.0.1 (block F only)
# gurobipy 11.0.1 has wheels only up to Python 3.12, so a Python 3.11 or 3.12
# interpreter is needed (Homebrew: brew install python@3.12).
set -e
cd "$(dirname "$0")"

PY=""
for cand in python3.12 python3.11; do
  if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then
  echo "Need python3.12 or python3.11 (brew install python@3.12)"; exit 1
fi
echo "Using $PY ($($PY --version))"

$PY -m venv .venv-g13
.venv-g13/bin/pip install --quiet --upgrade pip
.venv-g13/bin/pip install --quiet -r requirements.txt

$PY -m venv .venv-g11
.venv-g11/bin/pip install --quiet --upgrade pip
.venv-g11/bin/pip install --quiet gurobipy==11.0.1

echo "Checking licenses:"
.venv-g13/bin/python -c "import gurobipy as g; m=g.Model(); print('  Gurobi', g.gurobi.version(), 'license OK')"
.venv-g11/bin/python -c "import gurobipy as g; m=g.Model(); print('  Gurobi', g.gurobi.version(), 'license OK')" \
  || echo "  Gurobi 11.0.1: license not accepted -> block F will be skipped automatically"
