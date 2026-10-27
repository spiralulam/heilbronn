"""Exact verification of the configurations in Section 5 (MPC revision).

For n = 5..9 the coordinates of Tables 4-8 are entered symbolically, and for
n = 10 the configuration of Comellas and Yebra (Appendix B), which is optimal
within solver tolerances (Section 4.7). For every
one of the C(n,3) triangles the signed area is computed in exact arithmetic
over the relevant number field, the minimum is identified exactly, and the
number of triangles attaining it and the number of distinct areas are counted.
Feasibility (all coordinates in [0,1]) is also checked exactly.
"""
import time
from itertools import combinations
import sympy as sp

s3, s13, s65 = sp.sqrt(3), sp.sqrt(13), sp.sqrt(65)
R = sp.Rational
f = sp.symbols('f')
cub = 19*f**3 - 27*f**2 + 11*f - 1
f7 = sp.CRootOf(cub, 1)            # middle real root, approx 0.5839
z = sp.symbols('z')
cub10 = 12*z**3 - 27*z**2 + 20*z - 4    # minimal polynomial of z = 3/4 - c/12 - 1/(12c), c^3 = 63+8 sqrt(62)
z10 = sp.CRootOf(cub10, 0)         # its only real root, approx 0.3156
x10, y10 = z/2, 1 - 3*z + 2*z**2

configs = {
 5: [(0, R(1,3)), (s3/3, 0), (1, 1 - s3/3), (R(2,3), 1), (0, 1)],
 6: [(0, 0), (R(1,2), 0), (1, R(1,2)), (R(1,2), 1), (0, R(1,2)), (1, 1)],   # c = 0
 6.1: [(0, R(1,8)), (R(1,2), 0), (1, R(3,8)), (R(1,2), 1), (0, R(5,8)), (1, R(7,8))],  # c = 1/8
 7: [(0, 19*f**2-16*f+3), (19*f**2-27*f+10, 0), (1, (-19*f**2+10*f+1)/2), (1, 1), (0, 1),
     (-19*f**2+8*f+2, 57*f**2-41*f+5), (19*f**2-27*f+10, f)],
 8: [(0, 0), (R(1,6)+s13/6, 0), (1, R(7,18)-s13/18), (1, 1), (0, R(11,18)+s13/18),
     (R(5,6)-s13/6, 1), (R(5,6)-s13/6, R(7,9)-s13/9), (R(1,6)+s13/6, R(2,9)+s13/9)],
 9: [(0, 1-s65/10), (R(3,8)-s65/40, 0), (1, R(9,16)-3*s65/80), (R(3,8)-s65/40, 1),
     (0, R(5,8)+s65/40), (R(1,4)+s65/20, R(3,4)-s65/20), (R(7,16)+3*s65/80, 0),
     (s65/10, 1), (1, R(5,8)+s65/40)],
 10: [(x10, 0), (1-y10, 0), (0, x10), (1, y10), (1-z, z), (z, 1-z), (0, 1-y10), (1, 1-x10),
      (y10, 1), (1-x10, 1)],
}
claimed = {5: s3/9, 6: R(1,8), 6.1: R(1,8), 7: f - R(1,2), 8: (s13-1)/36, 9: (9*s65-55)/320, 10: R(5,8)*z**2 - z**3/2}

# n = 7 and n = 10 live in cubic fields Q(f) and Q(z): reduce polynomials modulo
# the minimal polynomial, so equality is decided exactly
cubic = {7: (f, cub, f7), 10: (z, cub10, z10)}

if __name__ == "__main__":
    for n, P in configs.items():
        t0 = time.time()
        if n in cubic:
            v, mp, root = cubic[n]
            red = lambda e, v=v, mp=mp: sp.rem(sp.expand(e), mp, v)
        else:
            red = lambda e: sp.nsimplify(sp.radsimp(sp.expand(e)))
        areas = []
        for (i, j, k) in combinations(range(len(P)), 3):
            (xi, yi), (xj, yj), (xk, yk) = P[i], P[j], P[k]
            a = red(((xj-xi)*(yk-yi) - (yj-yi)*(xk-xi))/2)
            areas.append(a)
        num = lambda e: (sp.sympify(e).subs(v, root) if n in cubic else sp.sympify(e)).evalf(40)
        absA = [a if num(a) > 0 else -a for a in areas]
        target = red(claimed[n])
        zero = [a for a in absA if sp.simplify(red(a - target)) == 0]
        below = [a for a in absA if num(a) < num(target) and sp.simplify(red(a - target)) != 0]
        # distinct areas (exact)
        distinct = []
        for a in absA:
            if not any(sp.simplify(red(a - b)) == 0 for b in distinct):
                distinct.append(a)
        coords_ok = all(0 <= num(c) <= 1 for p in P for c in p)
        print(f"n={n}: triangles={len(areas)} exact_min_ties={len(zero)} strictly_below={len(below)} "
              f"distinct_areas={len(distinct)} coords_in_square={coords_ok} "
              f"value={num(target):.15f} time={time.time()-t0:.2f}s", flush=True)
