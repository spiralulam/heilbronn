"""Baseline MIQCP for the Heilbronn triangle problem (no symmetry breaking)."""

from gurobipy import Model, GRB
from itertools import combinations


n = 7
points = list(range(n))
triangles = list(combinations(points, 3))
m = Model("Heilbronn")

x = {i: m.addVar(lb=0, ub=1, name=f"x[{i}]") for i in points}
y = {i: m.addVar(lb=0, ub=1, name=f"y[{i}]") for i in points}

z = m.addVar(lb=0, ub=0.5, name="z")
A_sign = m.addVars(triangles, lb=-0.5, ub=0.5, name="A_sign")
b_sign = m.addVars(triangles, vtype=GRB.BINARY, name="b_sign")

for (i, j, k) in triangles:
    m.addConstr(
        A_sign[i, j, k] == 0.5 * (
            x[i] * y[j] - x[i] * y[k]
            + x[j] * y[k] - x[j] * y[i]
            + x[k] * y[i] - x[k] * y[j]
        ),
        name=f"Asig[{i},{j},{k}]",
    )

m.addConstrs((z <= (2 * b_sign[t] - 1) * A_sign[t] for t in triangles), name="min_area")
m.setObjective(z, sense=GRB.MAXIMIZE)

m.Params.TimeLimit = 48 * 3600
m.Params.JSONSolDetail = 1

m.optimize()
m.write(f"incumbent_vanilla_n={n}.json")
print(f"Best bound: {m.ObjBound}, Best objective: {m.ObjVal}")
