"""Linear independence constraint qualification at optimal and best-known
configurations (Section 7.1).

Local problem: maximize z over (x_1..x_n, y_1..y_n, z) subject to
z - s_t A_t(x,y) <= 0 for all triangles t (s_t = current orientation) and the
box constraints. Active constraints: critical triangles and coordinates on the
boundary. LICQ holds iff their gradients are linearly independent.

n = 5, 6, 7, 9: exact rank by Gaussian elimination in the number field
(Q(sqrt 3), Q, Q(f), Q(sqrt 65)). For n = 6 the member c = 1/8 of the family.
n = 13, 15: numerical with the coordinates of ../best-known-configurations
(no exact coordinates known); smallest singular value at 50 digits.
"""
import json
import time
from itertools import combinations
from pathlib import Path
import sympy as sp
from mpmath import mp, mpf, matrix, svd

from verify_exact import configs, f7

F = sp.Symbol('f')
CUB = 19*F**3 - 27*F**2 + 11*F - 1


def gradients(P, num, is_zero):
    n = len(P)
    nv = 2*n + 1                                    # x_0..x_{n-1}, y_0..y_{n-1}, z
    tri = list(combinations(range(n), 3))
    def sarea(i, j, k):
        (xi, yi), (xj, yj), (xk, yk) = P[i], P[j], P[k]
        return ((xj-xi)*(yk-yi) - (yj-yi)*(xk-xi)) / 2
    areas = {t: sarea(*t) for t in tri}
    amin = min(abs(num(a)) for a in areas.values())
    rows, n_crit, n_box = [], 0, 0
    for (i, j, k), a in areas.items():
        if is_zero(abs(num(a)) - amin, a):
            n_crit += 1
            sgn = 1 if num(a) > 0 else -1
            (xi, yi), (xj, yj), (xk, yk) = P[i], P[j], P[k]
            # gradient of 2*A = (xj-xi)(yk-yi) - (yj-yi)(xk-xi)
            g = [0]*nv
            g[i] += (-(yk-yi) + (yj-yi)) / 2;  g[n+i] += (-(xj-xi) + (xk-xi)) / 2
            g[j] += (yk-yi) / 2;               g[n+j] += -(xk-xi) / 2
            g[k] += -(yj-yi) / 2;              g[n+k] += (xj-xi) / 2
            row = [-sgn*v for v in g]; row[2*n] = 1
            rows.append(row)
    for i, (x, y) in enumerate(P):
        for c, idx in ((x, i), (y, n+i)):
            for bound in (0, 1):
                if is_zero(num(c) - bound, c - bound):
                    row = [0]*nv; row[idx] = 1; rows.append(row); n_box += 1
    return rows, n_crit, n_box, nv


class NF:
    """Exact arithmetic in Q(alpha) = Q[t]/(minpoly), elements as rational coefficient lists."""
    def __init__(self, minpoly, t):
        self.t = t
        self.mp = sp.Poly(minpoly, t, domain=sp.QQ)
    def el(self, expr):
        return sp.Poly(sp.rem(sp.expand(expr), self.mp.as_expr(), self.t), self.t, domain=sp.QQ)
    def mul(self, a, b):
        return (a*b).rem(self.mp)
    def inv(self, a):
        return sp.Poly(sp.invert(a.as_expr(), self.mp.as_expr(), self.t), self.t, domain=sp.QQ)


def rank_nf(rows, K):
    """Exact rank by Gaussian elimination over the number field K."""
    M = [[K.el(e) for e in row] for row in rows]
    r, ncols = 0, len(M[0])
    for c in range(ncols):
        piv = next((i for i in range(r, len(M)) if not M[i][c].is_zero), None)
        if piv is None:
            continue
        M[r], M[piv] = M[piv], M[r]
        inv = K.inv(M[r][c])
        M[r] = [K.mul(v, inv) for v in M[r]]
        for i in range(len(M)):
            if i != r and not M[i][c].is_zero:
                fac = M[i][c]
                M[i] = [(M[i][j] - K.mul(fac, M[r][j])).rem(K.mp) for j in range(ncols)]
        r += 1
    return r


def exact(n):
    t = sp.Symbol('t')
    if n in (5, 6.1):
        P = [(sp.sympify(a), sp.sympify(b)) for a, b in configs[n]]
        num = lambda e: float(sp.sympify(e).evalf(40))
        K = NF(t**2 - 3, t)
        to_t = lambda e: sp.sympify(e).subs(sp.sqrt(3), t)
    elif n == 7:
        P = [(sp.sympify(a), sp.sympify(b)) for a, b in configs[n]]
        num = lambda e: float(sp.sympify(e).subs(F, f7).evalf(40))
        K = NF(CUB.subs(F, t), t)
        to_t = lambda e: sp.sympify(e).subs(F, t)
    else:
        P = [(sp.sympify(a), sp.sympify(b)) for a, b in configs[n]]
        num = lambda e: float(sp.sympify(e).evalf(40))
        K = NF(t**2 - 65, t)
        to_t = lambda e: sp.sympify(e).subs(sp.sqrt(65), t)
    is_zero = lambda numdiff, expr: abs(numdiff) < 1e-12
    rows, nc, nb, nv = gradients(P, num, is_zero)
    t0 = time.time()
    rk = rank_nf([[to_t(e) for e in row] for row in rows], K)
    return nc, nb, nv, len(rows), rk, time.time() - t0


def numeric(n):
    mp.dps = 50
    configs = Path(__file__).resolve().parents[1] / "best-known-configurations"
    pts = json.load(open(configs / f"config_n{n:02d}.json"))["points"]
    P = [(mpf(repr(a)), mpf(repr(b))) for a, b in pts]
    num = lambda e: e
    is_zero = lambda numdiff, expr: abs(numdiff) < mpf('1e-12')
    rows, nc, nb, nv = gradients(P, num, is_zero)
    A = matrix(rows)
    U, S, V = svd(A)
    svals = sorted(S[i] for i in range(min(A.rows, A.cols)))
    return nc, nb, nv, A.rows, svals


if __name__ == "__main__":
    for n in (5, 6.1, 7, 9):
        nc, nb, nv, m, rk, dt = exact(n)
        verdict = "LICQ holds" if rk == m else "LICQ fails"
        print(f"n={n}: {nc} critical + {nb} box = {m} active, {nv} variables, exact rank {rk}: {verdict} ({dt:.1f}s)", flush=True)
    for n in (13, 15):
        nc, nb, nv, rows, sv = numeric(n)
        print(f"n={n}: {nc} critical + {nb} box = {rows} active, {nv} variables: "
              f"smallest singular values {[mp.nstr(v, 6) for v in sv[:3]]}, largest {mp.nstr(sv[-1], 6)}", flush=True)
