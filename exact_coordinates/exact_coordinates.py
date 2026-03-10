"""Exact algebraic coordinates for optimal Heilbronn configurations, n = 5..9.

Reads the certified numerical solutions produced by the Gurobi MIP model,
identifies critical triangles, solves the resulting equal-area system
symbolically, and verifies the result.
"""

import json, sys
import sympy as sp
from itertools import combinations
from pathlib import Path

SOLUTION_DIR = Path(__file__).parent / "certified_optimal_points_square"


# ── shared helpers ──────────────────────────────────────────────────────────

def load_solution(n):
    """Parse certified-solution JSON.  Returns (coords_dict, z)."""
    with open(SOLUTION_DIR / f"certified_solution_n={n}.json") as f:
        data = json.load(f)
    v = {r["VarName"]: r["X"] for r in data["Vars"]}
    # The MIP model fixes: p0 left (x0=0), p1 bottom (y1=0),
    # p2 right (x2=1), p3 top (y3=1), p4 left (x4=0, y4>=y0).
    pts = {
        0: (0.0, v["y[0]"]),
        1: (v["x[1]"], 0.0),
        2: (1.0, v["y[2]"]),
        3: (v["x[3]"], 1.0),
        4: (0.0, v["y[4]"]),
    }
    for i in range(5, n):
        pts[i] = (v[f"x[{i}]"], v[f"y[{i}]"])
    return pts, v["z"]


def signed_area(pts, i, j, k):
    """Signed triangle area (half the shoelace determinant)."""
    xi, yi = pts[i]; xj, yj = pts[j]; xk, yk = pts[k]
    return sp.Rational(1, 2) * (xi*(yj - yk) + xj*(yk - yi) + xk*(yi - yj))


def num_area(pts, i, j, k):
    """Unsigned numerical triangle area."""
    xi, yi = pts[i]; xj, yj = pts[j]; xk, yk = pts[k]
    return abs(0.5 * (xi*(yj - yk) + xj*(yk - yi) + xk*(yi - yj)))


def critical_triangles(pts, n, tol=1e-3):
    """Triangles within relative tol of the minimum area."""
    all_tri = list(combinations(range(n), 3))
    areas = [(t, num_area(pts, *t)) for t in all_tri]
    areas.sort(key=lambda x: x[1])
    z = areas[0][1]
    return [t for t, a in areas if abs(a - z) / z < tol]


def oriented_area(sym_pts, num_pts, tri):
    """Symbolic area of tri, sign-matched to the numerical orientation."""
    sa = signed_area(sym_pts, *tri)
    i, j, k = tri
    ns = 0.5 * (num_pts[i][0]*(num_pts[j][1] - num_pts[k][1])
              + num_pts[j][0]*(num_pts[k][1] - num_pts[i][1])
              + num_pts[k][0]*(num_pts[i][1] - num_pts[j][1]))
    return sa if ns > 0 else -sa


def equal_area_eqs(sym_pts, num_pts, crits):
    """area(crits[0]) = area(crits[i]) for i >= 1."""
    areas = [oriented_area(sym_pts, num_pts, t) for t in crits]
    return [sp.Eq(areas[0], a) for a in areas[1:]]


def verify(pts, n, min_area):
    """Check every C(n,3) triangle area >= min_area.  Returns True/False."""
    z = float(sp.Abs(sp.N(min_area, 30)))
    for tri in combinations(range(n), 3):
        a = float(sp.Abs(sp.N(signed_area(pts, *tri), 30)))
        if a < z - 1e-10:
            print(f"  VIOLATION: {tri}, area = {a:.15f} < {z:.15f}")
            return False
    return True


def make_exact(pts, n, sol):
    """Substitute solution into symbolic coordinate dict."""
    return {i: tuple(sp.simplify(sp.S(co).subs(sol)) for co in pts[i])
            for i in range(n)}


def print_result(pts, n, min_area):
    z = float(sp.Abs(sp.N(min_area, 30)))
    ncrit = sum(1 for t in combinations(range(n), 3)
                if abs(float(sp.Abs(sp.N(signed_area(pts, *t), 30))) - z)
                < 1e-10)
    ntri = n * (n - 1) * (n - 2) // 6
    print(f"\n{'='*60}")
    print(f"  n = {n}")
    print(f"{'='*60}")
    print(f"\n  Exact coordinates:\n")
    for i in range(n):
        x, y = pts[i]
        xf = float(sp.re(sp.N(x, 20)))
        yf = float(sp.re(sp.N(y, 20)))
        print(f"    p{i} = ({x}, {y})")
        print(f"         ~ ({xf:.10f}, {yf:.10f})")
    print(f"\n  Minimum area = {min_area}")
    print(f"              ~ {z:.15f}")
    if verify(pts, n, min_area):
        print(f"  Verified: {ntri} triangles, {ncrit} critical  [OK]\n")
    else:
        print(f"  VERIFICATION FAILED\n")


# ── n = 5 ──────────────────────────────────────────────────────────────────

def solve_n5():
    """
    H_5 = sqrt(3)/9.  4 critical triangles.

    Boundary: p0 left, p1 bottom, p2 right, p3 top, p4 left.
    From numerics: y4 = 1, so p4 sits at the top-left corner.
    Free: a = y0, b = x1, c = y2, d = x3  (4 unknowns).
    Three equal-area equations, leaving d free.
    z(d) = d sqrt(1 - d) / 2, maximised at d = 2/3.
    """
    num_pts, _ = load_solution(5)
    crits = critical_triangles(num_pts, 5)

    a, b, c, d = sp.symbols('a b c d', positive=True)
    pts = {0: (0, a), 1: (b, 0), 2: (1, c), 3: (d, 1), 4: (0, 1)}

    eqs = equal_area_eqs(pts, num_pts, crits)
    sol = sp.solve(eqs, [a, b, c, d], dict=True)[0]  # parametric in d

    # z(d) = d sqrt(1-d) / 2, maximised at d = 2/3
    d_val = sp.Rational(2, 3)
    full = {v: sp.simplify(sol[v].subs(d, d_val)) for v in sol}
    full[d] = d_val

    exact = make_exact(pts, 5, full)
    min_area = sp.simplify(oriented_area(pts, num_pts, crits[0]).subs(full))

    print_result(exact, 5, min_area)
    return exact, min_area


# ── n = 6 ──────────────────────────────────────────────────────────────────

def solve_n6():
    """
    H_6 = 1/8.  6 critical triangles.

    Boundary: p0 left, p1 bottom, p2 right, p3 top, p4 left, p5 right.
    From numerics: x1 ~ x3 (both ~ 0.5), x5 = 1.
    Free: a = y0, b = x1 = x3, c = y2, d = y4, e = y5  (5 unknowns).
    Five equal-area equations, but the system has rank deficiency:
      z = b(1-b)/2, maximised at b = 1/2 giving z = 1/8.
      c (= y2) is a family parameter: z does not depend on it.

    We present the parametric family.  For the numerical representative
    used in verification, c is taken from the Gurobi solution.
    """
    num_pts, _ = load_solution(6)
    crits = critical_triangles(num_pts, 6)

    a, b, c, d, e = sp.symbols('a b c d e', positive=True)
    pts = {0: (0, a), 1: (b, 0), 2: (1, c), 3: (b, 1),
           4: (0, d), 5: (1, e)}

    eqs = equal_area_eqs(pts, num_pts, crits)
    sol = sp.solve(eqs, [a, b, c, d, e], dict=True)[0]

    # z = b(1-b)/2, max at b = 1/2.  c is free.
    b_val = sp.Rational(1, 2)

    # Show the parametric family
    param = {v: sp.simplify(sol[v].subs(b, b_val))
             for v in sol if v not in (b, c)}
    print(f"\n  Parametric family (b = 1/2, c free):")
    for v in [a, d, e]:
        if v in param:
            print(f"    {v} = {param[v]}")

    # For verification, use c from the numerical solution
    c_val = sp.nsimplify(num_pts[2][1], rational=True, tolerance=1e-4)
    full = {v: sp.simplify(param[v].subs(c, c_val))
            for v in param}
    full[b] = b_val
    full[c] = c_val

    exact = make_exact(pts, 6, full)
    min_area = sp.Rational(1, 8)

    print_result(exact, 6, min_area)
    return exact, min_area


# ── n = 7 ──────────────────────────────────────────────────────────────────

def solve_n7():
    """
    H_7 is a root of a cubic.  8 critical triangles.

    Boundary: p0 left, p1 bottom, p2 right, p3 right, p4 left.
    From numerics: x3 = 1, y3 = 1, y4 = 1 (corners), x1 ~ x6.
    Free: a = y0, b = x1 = x6, c = y2, d = x5, e = y5, f = y6
          (6 unknowns).
    Seven equal-area equations in six unknowns.
    Groebner basis (lex order) yields a univariate cubic in f:
        19 f^3 - 27 f^2 + 11 f - 1 = 0.
    The correct root is represented via CRootOf; the remaining variables
    are recovered by back-substitution through the basis.
    """
    num_pts, _ = load_solution(7)
    n = 7
    crits = critical_triangles(num_pts, n)

    a, b, c, d, e, f = sp.symbols('a b c d e f', positive=True)
    pts = {0: (0, a), 1: (b, 0), 2: (1, c), 3: (1, 1), 4: (0, 1),
           5: (d, e), 6: (b, f)}
    syms = [a, b, c, d, e, f]

    eqs = equal_area_eqs(pts, num_pts, crits)
    polys = [eq.lhs - eq.rhs for eq in eqs]

    # Groebner basis, lex order
    G = list(sp.groebner(polys, syms, order='lex'))

    # Find the univariate polynomial (in f, the last variable)
    univar = None
    for g in reversed(G):
        if g.free_symbols & set(syms) == {f}:
            univar = sp.Poly(g, f)
            break
    assert univar is not None, "no univariate polynomial found"
    print(f"  Univariate: {univar.as_expr()} = 0  (degree {univar.degree()})")

    # Numerical targets for branch selection
    num_target = {a: num_pts[0][1], b: num_pts[1][0], c: num_pts[2][1],
                  d: num_pts[5][0], e: num_pts[5][1], f: num_pts[6][1]}

    # Pick the CRootOf closest to the numerical f
    best_root, best_err = None, float("inf")
    for idx in range(univar.degree()):
        cr = sp.CRootOf(univar, idx)
        err = abs(float(cr.evalf()) - num_target[f])
        if err < best_err:
            best_root, best_err = cr, err

    sol = {f: best_root}

    # Back-substitute through the remaining basis elements
    for g in G:
        unknown = (g.free_symbols & set(syms)) - sol.keys()
        if len(unknown) != 1:
            continue
        var = unknown.pop()
        roots = sp.solve(g.subs(sol), var)
        if roots:
            sol[var] = min(roots,
                          key=lambda r: abs(complex(r.evalf())
                                            - num_target[var]))

    assert len(sol) == len(syms), f"incomplete: solved {list(sol)}"

    exact = make_exact(pts, n, sol)
    min_area = sp.simplify(oriented_area(pts, num_pts, crits[0]).subs(sol))

    print_result(exact, n, min_area)
    return exact, min_area


# ── n = 8 ──────────────────────────────────────────────────────────────────

def solve_n8():
    """
    H_8 = (sqrt(13) - 1) / 36.  12 critical triangles.

    Boundary: p0 left, p1 bottom, p2 right, p3 top, p4 left, p5 top.
    From numerics: y0 = 0, x3 = 1, y3 = 1, y5 = 1, x1 ~ x7, x5 ~ x6.
    Free: a = x1 = x7, b = y2, c = y4, d = x5 = x6, e = y6, f = y7
          (6 unknowns).
    Eleven equal-area equations in six unknowns (overdetermined).
    sp.solve finds a unique closed-form solution in Q(sqrt(13)).
    """
    num_pts, _ = load_solution(8)
    n = 8
    crits = critical_triangles(num_pts, n)

    a, b, c, d, e, f = sp.symbols('a b c d e f', positive=True)
    pts = {0: (0, 0), 1: (a, 0), 2: (1, b), 3: (1, 1),
           4: (0, c), 5: (d, 1), 6: (d, e), 7: (a, f)}
    syms = [a, b, c, d, e, f]

    eqs = equal_area_eqs(pts, num_pts, crits)
    solutions = sp.solve(eqs, syms, dict=True, cubics=False)

    # Select branch closest to numerical coordinates
    best_sol, best_dist = None, float("inf")
    for sol in solutions:
        try:
            dist = sum(
                (float(sp.re(sp.N(sp.S(pts[i][0]).subs(sol), 20)))
                 - num_pts[i][0])**2
              + (float(sp.re(sp.N(sp.S(pts[i][1]).subs(sol), 20)))
                 - num_pts[i][1])**2
                for i in range(n))
        except Exception:
            continue
        if dist < best_dist:
            best_dist, best_sol = dist, sol
    assert best_sol is not None and best_dist < 0.01, \
        f"no valid branch (best dist = {best_dist})"

    exact = make_exact(pts, n, best_sol)
    min_area = sp.simplify(
        oriented_area(pts, num_pts, crits[0]).subs(best_sol))

    print_result(exact, n, min_area)
    return exact, min_area


# ── n = 9 ──────────────────────────────────────────────────────────────────

def solve_n9():
    """
    H_9 = (9 sqrt(65) - 55) / 320.  11 critical triangles.

    Boundary: p0 left, p1 bottom, p2 right, p3 top, p4 left.
    From numerics: y6 = 0, y7 = 1, x8 = 1, x1 ~ x3, y4 ~ y8.
    Free: a = y0, b = x1 = x3, c = y2, d = y4 = y8, e = x5, f = y5,
          g = x6, h = x7  (8 unknowns).
    Ten equal-area equations in eight unknowns.

    All coordinates lie in Q(sqrt(65)).  This is discovered by nsimplify
    of the numerical minimum area.  We nsimplify each coordinate with the
    extension sqrt(65), then verify the equal-area equations symbolically.
    A few coordinates require refinement (re-solving a subsystem) because
    nsimplify can land on nearby but inexact Q(sqrt(65)) values.
    """
    num_pts, z_val = load_solution(9)
    n = 9
    crits = critical_triangles(num_pts, n)

    a, b, c, d, e, f, g, h = sp.symbols('a b c d e f g h', positive=True)
    pts = {0: (0, a), 1: (b, 0), 2: (1, c), 3: (b, 1),
           4: (0, d), 5: (e, f), 6: (g, 0), 7: (h, 1), 8: (1, d)}
    syms = [a, b, c, d, e, f, g, h]
    num_vals = {a: num_pts[0][1], b: num_pts[1][0], c: num_pts[2][1],
                d: num_pts[4][1], e: num_pts[5][0], f: num_pts[5][1],
                g: num_pts[6][0], h: num_pts[7][0]}

    # All coordinates lie in Q(sqrt(65))
    ext = [sp.sqrt(65)]
    sol = {}
    for s in syms:
        expr = sp.nsimplify(num_vals[s], ext, tolerance=1e-5)
        sol[s] = expr
        err = abs(float(expr.evalf()) - num_vals[s])
        print(f"    {s} = {expr}  (err = {err:.2e})")

    # Check equal-area equations; refine if any fail
    eqs = equal_area_eqs(pts, num_pts, crits)
    fails = [eq for eq in eqs
             if sp.simplify(eq.lhs.subs(sol) - eq.rhs.subs(sol)) != 0]

    if fails:
        print(f"  {len(fails)} equations fail -- refining ...")
        for pair in combinations(syms, 2):
            fix = {s: sol[s] for s in syms if s not in pair}
            reduced = []
            for eq in eqs:
                eq_sub = sp.Eq(eq.lhs.subs(fix), eq.rhs.subs(fix))
                if eq_sub != True and eq_sub is not True:
                    reduced.append(eq_sub)
            if len(reduced) < 2:
                continue
            try:
                candidates = sp.solve(reduced[:4], list(pair), dict=True)
            except Exception:
                continue
            for cand in candidates:
                test = dict(sol)
                test.update(cand)
                # Check all clean algebraic
                if not all(v.is_number for v in cand.values()):
                    continue
                dist = sum(
                    (float(sp.N(sp.S(pts[i][0]).subs(test), 20))
                     - num_pts[i][0])**2
                  + (float(sp.N(sp.S(pts[i][1]).subs(test), 20))
                     - num_pts[i][1])**2
                    for i in range(n))
                if dist < 1e-2:
                    sol = test
                    print(f"  Refined {list(pair)}: dist = {dist:.2e}")
                    break
            fails = [eq for eq in eqs
                     if sp.simplify(eq.lhs.subs(sol) - eq.rhs.subs(sol))
                     != 0]
            if not fails:
                break

    exact = make_exact(pts, n, sol)
    min_area = sp.simplify(oriented_area(pts, num_pts, crits[0]).subs(sol))

    print_result(exact, n, min_area)
    return exact, min_area


# ── CLI ────────────────────────────────────────────────────────────────────

SOLVERS = {5: solve_n5, 6: solve_n6, 7: solve_n7, 8: solve_n8, 9: solve_n9}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    ns = [int(args[0])] if args else [5, 6, 7, 8, 9]
    for nn in ns:
        SOLVERS[nn]()
