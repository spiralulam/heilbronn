"""Strengthened MIP for the Heilbronn triangle problem (Section 3.4 of the paper).

Five boundary points, bilinear products w[i,j] = x[i]*y[j], and
partially fixed triangle orientations. Certifies optimality for n = 9
in about 15 minutes.
"""
from gurobipy import Model, GRB
from itertools import combinations, product
from collections import defaultdict

n = 7
points = list(range(n))
triangles = list(combinations(points, 3))

m = Model("Heilbronn")

# Known upper bounds (for tighter z bounds)
ub_known = {
    3: 0.5,
    4: 0.5,
    5: 0.5,
    6: 0.1924505571190438,
    7: 0.12501230057420779,
    8: 0.08385930745259085,
    9: 0.07237700373214552,
    10: 0.05488068669327922,
    11: 0.05488068669327922,
    12: 0.05488068669327922,
    13: 0.05488068669327922,
    14: 0.5,
}

# Five boundary points arranged counterclockwise:
# p0 left, p1 bottom, p2 right, p3 top, p4 left (above p0)
x = {}
y = {}
w = defaultdict(dict)

x[0] = 0
y[0] = m.addVar(lb=0, ub=1, name="y[0]")

x[1] = m.addVar(lb=0, ub=1, name="x[1]")
y[1] = 0

x[2] = 1
y[2] = m.addVar(lb=0, ub=1, name="y[2]")

if len(points) > 3:
    x[3] = m.addVar(lb=0, ub=1, name="x[3]")
    y[3] = 1
    m.addConstr(x[1] <= x[3])

if len(points) > 4:
    x[4] = 0
    y[4] = m.addVar(lb=0, ub=1, name="y[4]")
    m.addConstr(y[0] <= y[4])

if len(points) > 5:
    for i in points[5:]:
        x[i] = m.addVar(lb=0, ub=1, name=f"x[{i}]")
        y[i] = m.addVar(lb=0, ub=1, name=f"y[{i}]")
        m.addConstr(x[i - 1] <= x[i])

# Bilinear products
for (i, j) in product(points, points):
    w[i, j] = m.addVar(lb=0, ub=1, name=f"w[{i},{j}]")
    m.addConstr(w[i, j] == x[i] * y[j], name=f"wdef[{i},{j}]")

z = m.addVar(lb=0, ub=ub_known[n], name="z")

# Triangles with all vertices on the boundary have known orientation
triangles_pos = [t for t in triangles if t[2] <= 4]
triangles_neg = [t for t in triangles if (t[0] == 0 and t[1] == 4)]

A_sign = m.addVars(triangles, lb=-0.5, ub=0.5, name="A_sign")
b_sign = m.addVars(triangles, vtype=GRB.BINARY, name="b_sign")

for (i, j, k) in triangles:
    m.addConstr(
        A_sign[i, j, k] == 0.5 * (
            w[i, j] - w[i, k]
            - w[j, i] + w[j, k]
            + w[k, i] - w[k, j]
        ),
        name=f"Asig[{i},{j},{k}]",
    )

m.addConstrs(b_sign[t] == 1 for t in triangles_pos)
m.addConstrs(b_sign[t] == 0 for t in triangles_neg)
m.addConstrs((z <= (2 * b_sign[t] - 1) * A_sign[t] for t in triangles), name="min_area")
m.setObjective(z, sense=GRB.MAXIMIZE)

m.Params.TimeLimit = 10 * 24 * 3600
m.Params.MIPFocus = 2
m.Params.JSONSolDetail = 1

m.optimize()
m.write(f"incumbent_n={n}.json")
print(f"Best bound: {m.ObjBound}, Best objective: {m.ObjVal}")
