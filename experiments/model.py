"""Model builders for the MPC revision experiments.

All formulations of the paper in one place, so that every run of the revision
comes from the same code:

  full      P*_Delta of the paper (Figure "final model"), with switches for the
            ablation study:
              signfix  fix the orientation binaries on T+ and T-
              order    order the points p6..pn by nondecreasing x
              wsub     product substitution w_ij = x_i y_j
              cap      upper bound z <= Delta_{n-1}
              freebin  binaries only for triangles whose sign is not fixed
                       (Remark 6 of the submitted version)
              strips   strip-capacity constraints (see strip_capacities)
              contacts contact conditions of Lemma 2(C) (see _add_contacts)
              nobound  no boundary pattern: no fixed coordinates and hence no sign
                       fixing; all points ordered by x (ablation of the edge fixings)
  baseline  P^0_Delta: no symmetry breaking, no substitution, z <= 1/2
  type2     two adjacent corners C=(1,1), D=(0,1), a further point L on the
            left edge and a point b on the bottom edge (case II of the revised
            boundary proposition, reached by an area-preserving shear)
  type3     three corners A=(0,0), C=(1,1), D=(0,1) (case III)

Point indices are 0-based in the code and 1-based in the paper.
"""
from itertools import combinations, product

import gurobipy as gp
from gurobipy import GRB

# Upper bounds Delta_{n-1} used by the cap z <= Delta_{n-1}.
# n-1 <= 8: proved optimal values (rounded up in the 13th digit).
# n-1 = 9: no proof exists. We use the solver-reported dual bound of the
# submitted n=9 run (0.054881757...), rounded up. The cap is never active at
# the optimum, because Delta_n is far below Delta_{n-1}.
CAP = {
    3: 0.5, 4: 0.5, 5: 0.5,
    6: 0.1924500897299,   # Delta_5 = sqrt(3)/9
    7: 0.1250000000001,   # Delta_6 = 1/8
    8: 0.0838590090076,   # Delta_7
    9: 0.0723764243185,   # Delta_8 = (sqrt(13)-1)/36
    10: 0.0548818,        # numerical upper bound for Delta_9
}

FULL_DEFAULTS = dict(signfix=True, order=True, wsub=True, cap=True, freebin=False,
                     strips=False, contacts=False, nobound=False)

# Proved values Delta_m (m <= 8), as upper bounds (rounded up), and the best
# known value of Delta_n as a lower bound H (rounded down). Used only by the
# strip-capacity constraints.
DELTA_UP = {3: 0.5, 4: 0.5, 5: 0.1924500897299, 6: 0.1250000000001,
            7: 0.0838590090076, 8: 0.0723764243185}
DELTA_LOW = {5: 0.1924500897298, 6: 0.125, 7: 0.0838590090075,
             8: 0.0723764243184, 9: 0.0548759991708}


def strip_capacities(n):
    """Pairs (t, m): at most m points of an optimal n-configuration lie in an
    open strip of height t along any edge of the square.

    Scaling a strip of height t to the unit square multiplies all areas by 1/t.
    If m+1 points lay in the strip with minimum area >= H, the scaled points would
    have minimum area >= H/t > Delta_{m+1}, which is impossible. So every strip of
    height t < H/Delta_{m+1} holds at most m points. The capacities of Monji,
    Modir and Kocuk (Table 1) are the special case t = 1/kappa. Valid for every
    configuration with value >= H, independent of labeling and symmetry breaking.
    Rigorous as long as m+1 <= 8 (proved values).
    """
    H = DELTA_LOW[n]
    caps = {}
    for m in range(2, n - 1):
        if m + 1 not in DELTA_UP:
            break
        t = H / DELTA_UP[m + 1] * (1 - 1e-7)
        if t < 1:
            caps[round(t, 12)] = min(m, caps.get(round(t, 12), m))
    return sorted(caps.items())


def _area_expr(i, j, k, x, y, w):
    """Twice the signed area of (p_i, p_j, p_k), as an expression."""
    if w is not None:
        return w[i, j] + w[j, k] + w[k, i] - w[i, k] - w[j, i] - w[k, j]
    return (x[i] * y[j] + x[j] * y[k] + x[k] * y[i]
            - x[i] * y[k] - x[j] * y[i] - x[k] * y[j])


def _var_or_const(m, val, name):
    return val if val is not None else m.addVar(lb=0, ub=1, name=name)


def _add_contacts(m, n, x, y, variant):
    """Contact conditions of Lemma 2(C), valid for every optimal configuration.

    The x-ranges of the points on the bottom and on the top edge intersect, and
    so do the y-ranges of the points on the left and on the right edge. With
    binaries on[e][i] = 1 only if point i lies on edge e, each range condition
    "min over A <= max over B" is modeled by selecting one point a of A and one
    point b of B (selection binaries) with coordinate(a) <= coordinate(b).
    Coordinates lie in [0, 1], so 1 is a valid big-M.
    For the full model, the condition min_bottom x <= max_top x already follows
    from x2 <= x4, so only the three remaining conditions are added.
    """
    pts = range(n)
    on = {}
    for e in ("b", "t", "l", "r"):
        on[e] = m.addVars(n, vtype=GRB.BINARY, name=f"on_{e}")
    for i in pts:
        m.addConstr(y[i] <= 1 - on["b"][i], name=f"onb[{i}]")
        m.addConstr(y[i] >= on["t"][i], name=f"ont[{i}]")
        m.addConstr(x[i] <= 1 - on["l"][i], name=f"onl[{i}]")
        m.addConstr(x[i] >= on["r"][i], name=f"onr[{i}]")
    if variant == "full":                      # known boundary points of the pattern
        for e, i in (("l", 0), ("b", 1), ("r", 2), ("t", 3), ("l", 4)):
            on[e][i].LB = 1

    def at_most(coord, low_edge, high_edge, tag):
        # some point on low_edge has coord <= coord of some point on high_edge
        s_lo = m.addVars(n, vtype=GRB.BINARY, name=f"sel_{tag}_lo")
        s_hi = m.addVars(n, vtype=GRB.BINARY, name=f"sel_{tag}_hi")
        m.addConstr(s_lo.sum() == 1, name=f"sel_{tag}_lo_one")
        m.addConstr(s_hi.sum() == 1, name=f"sel_{tag}_hi_one")
        for i in pts:
            m.addConstr(s_lo[i] <= on[low_edge][i])
            m.addConstr(s_hi[i] <= on[high_edge][i])
        for i in pts:
            for j in pts:
                if i != j:
                    m.addConstr(coord[i] - coord[j] <= 2 - s_lo[i] - s_hi[j], name=f"cmp_{tag}[{i},{j}]")

    at_most(x, "t", "b", "tb")                 # min_top x <= max_bottom x
    at_most(y, "l", "r", "lr")                 # min_left y <= max_right y
    at_most(y, "r", "l", "rl")                 # min_right y <= max_left y
    if variant != "full":
        at_most(x, "b", "t", "bt")


def build(n, variant="full", **opts):
    """Return (model, handles). handles holds x, y, z, A, b, w and metadata."""
    o = dict(FULL_DEFAULTS)
    o.update(opts)
    if variant == "baseline":
        o.update(signfix=False, order=False, wsub=False, cap=False, freebin=False)

    m = gp.Model(f"heilbronn_{variant}_n{n}")
    pts = range(n)
    triangles = list(combinations(pts, 3))

    # ---- coordinates with the fixings of each variant ----------------------
    fixed = {}            # i -> (x or None, y or None); None = free variable
    pos_tri, neg_tri = [], []
    first_free = 0        # index of the first point that is ordered by x
    if variant == "full" and o["nobound"]:
        pass                                   # all coordinates free, all points ordered by x
    elif variant == "full":
        fixed = {0: (0, None), 1: (None, 0), 2: (1, None), 3: (None, 1), 4: (0, None)}
        first_free = 5
        pos_tri = [t for t in triangles if t[2] <= 4]
        neg_tri = [t for t in triangles if t[0] == 0 and t[1] == 4]
    elif variant == "type2":
        # p0 = L on the left edge, p1 = b on the bottom edge, p2 = C, p3 = D.
        # Counterclockwise order L, b, C, D.
        fixed = {0: (0, None), 1: (None, 0), 2: (1, 1), 3: (0, 1)}
        first_free = 4
        pos_tri = [t for t in triangles if t[2] <= 3]                    # boundary points, ccw
        pos_tri += [t for t in triangles if t[0] == 2 and t[1] == 3]     # (C, D, k): area (1-y_k)/2
        neg_tri = [t for t in triangles if t[0] == 0 and t[1] == 3]      # (L, D, k): -(1-y_L) x_k / 2
    elif variant == "type3":
        # p0 = A, p1 = C, p2 = D. Counterclockwise order A, C, D.
        fixed = {0: (0, 0), 1: (1, 1), 2: (0, 1)}
        first_free = 3
        pos_tri = [(0, 1, 2)]
        pos_tri += [t for t in triangles if t[0] == 1 and t[1] == 2]     # (C, D, k): (1-y_k)/2
        neg_tri = [t for t in triangles if t[0] == 0 and t[1] == 2]      # (A, D, k): -x_k/2
    elif variant != "baseline":
        raise ValueError(variant)

    x, y = {}, {}
    for i in pts:
        fx, fy = fixed.get(i, (None, None))
        x[i] = _var_or_const(m, fx, f"x[{i}]")
        y[i] = _var_or_const(m, fy, f"y[{i}]")

    if variant == "full" and not o["nobound"]:
        m.addConstr(x[1] <= x[3], name="refl_x2_le_x4")
        m.addConstr(y[0] <= y[4], name="left_y1_le_y5")
    if o["order"] and variant != "baseline":
        for i in range(first_free, n - 1):
            m.addConstr(x[i] <= x[i + 1], name=f"order[{i}]")

    # ---- product substitution ---------------------------------------------
    w = None
    if o["wsub"]:
        w = {}
        for i, j in product(pts, pts):
            w[i, j] = m.addVar(lb=0, ub=1, name=f"w[{i},{j}]")
            m.addConstr(w[i, j] == x[i] * y[j], name=f"wdef[{i},{j}]")

    # ---- areas, signs, objective -------------------------------------------
    ub = CAP[n] if o["cap"] else 0.5
    z = m.addVar(lb=0, ub=ub, name="z")
    A = m.addVars(triangles, lb=-0.5, ub=0.5, name="A_sign")
    for (i, j, k) in triangles:
        m.addConstr(A[i, j, k] == 0.5 * _area_expr(i, j, k, x, y, w), name=f"Asig[{i},{j},{k}]")

    known = {}
    if o["signfix"]:
        known.update({t: 1 for t in pos_tri})
        known.update({t: 0 for t in neg_tri})

    b = {}
    if o["freebin"]:
        free = [t for t in triangles if t not in known]
        bv = m.addVars(free, vtype=GRB.BINARY, name="b_sign")
        b.update(bv)
        for t in triangles:
            if t in known:
                m.addConstr(z <= (A[t] if known[t] == 1 else -A[t]), name=f"min_area{t}")
            else:
                m.addConstr(z <= (2 * b[t] - 1) * A[t], name=f"min_area{t}")
    else:
        bv = m.addVars(triangles, vtype=GRB.BINARY, name="b_sign")
        b.update(bv)
        for t, val in known.items():
            m.addConstr(b[t] == val, name=f"signfix{t}")
        m.addConstrs((z <= (2 * b[t] - 1) * A[t] for t in triangles), name="min_area")

    # ---- strip capacities ----------------------------------------------------
    if o["strips"]:
        # u = 1 allows the point inside the open strip, u = 0 forces it outside.
        for (t, cap_m) in strip_capacities(n):
            for side in ("bottom", "top", "left", "right"):
                u = m.addVars(n, vtype=GRB.BINARY, name=f"strip_{side}_{t:.6f}")
                for i in pts:
                    c = y[i] if side in ("bottom", "top") else x[i]
                    if side in ("bottom", "left"):
                        m.addConstr(c >= t * (1 - u[i]), name=f"strip_{side}_{t:.6f}[{i}]")
                    else:
                        m.addConstr(c <= 1 - t * (1 - u[i]), name=f"strip_{side}_{t:.6f}[{i}]")
                m.addConstr(u.sum() <= cap_m, name=f"strip_card_{side}_{t:.6f}")

    if o["contacts"]:
        _add_contacts(m, n, x, y, variant)

    m.setObjective(z, GRB.MAXIMIZE)
    handles = dict(x=x, y=y, z=z, A=A, b=b, w=w, triangles=triangles, variant=variant,
                   options=o, n_fixed_signs=len(known))
    return m, handles


def set_start(m, h, pts):
    """MIP start from a labeled configuration pts[i] = (x_i, y_i)."""
    x, y, w, A, b, z = h["x"], h["y"], h["w"], h["A"], h["b"], h["z"]
    for i, (px, py) in enumerate(pts):
        if isinstance(x[i], gp.Var):
            x[i].Start = px
        if isinstance(y[i], gp.Var):
            y[i].Start = py
    if w is not None:
        for (i, j), v in w.items():
            v.Start = pts[i][0] * pts[j][1]
    zmin = 1.0
    for (i, j, k) in h["triangles"]:
        (xi, yi), (xj, yj), (xk, yk) = pts[i], pts[j], pts[k]
        a = 0.5 * (xi * yj + xj * yk + xk * yi - xi * yk - xj * yi - xk * yj)
        A[i, j, k].Start = a
        if (i, j, k) in b:
            b[i, j, k].Start = 1 if a >= 0 else 0
        zmin = min(zmin, abs(a))
    z.Start = zmin
