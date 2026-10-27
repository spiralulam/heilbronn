"""Exact count of the labeled copies of the known optimal configurations that
are feasible for the final model P*_Delta (Table "copies" of the paper).

Procedure, in exact arithmetic (SymPy, coordinates in Q(sqrt 3), Q(sqrt 13),
Q(sqrt 65), Q(f) with f a root of 19f^3-27f^2+11f-1, or Q(z) with z the real
root of 12z^3-27z^2+20z-4):
  1. Apply each of the 8 symmetries g of the square to the optimal
     configuration P.
  2. For every ordered choice of five distinct points (p1,...,p5) of g(P),
     check the fixed coordinates x1=x5=0, y2=0, x3=1, y4=1 and the
     inequalities y1<=y5, x2<=x4.
  3. Label the remaining points p6,...,pn by nondecreasing x. If several
     points share an x-coordinate, every order among them is admissible.
  4. Check the sign fixings: all triangles (i,j,k) with k<=5 positively
     oriented, all triangles (1,5,k) nonpositively oriented.
  5. Count the distinct labeled configurations (tuples of points) that pass.
     Different symmetries can produce the same labeled tuple if P itself is
     symmetric, so tuples are deduplicated.
"""
import sys
from itertools import combinations, permutations, groupby
import sympy as sp

sys.path.insert(0, '.')
from verify_exact import configs, f7, z10, cub10   # exact coordinates of Section 6

def num(e):
    return sp.sympify(e).subs({sp.Symbol('f'): f7, sp.Symbol('z'): z10})

def simp(e):
    e = sp.sympify(e)
    if e.has(sp.Symbol('f')):
        return sp.rem(sp.expand(e), 19*sp.Symbol('f')**3 - 27*sp.Symbol('f')**2 + 11*sp.Symbol('f') - 1, sp.Symbol('f'))
    if e.has(sp.Symbol('z')):
        return sp.rem(sp.expand(e), cub10, sp.Symbol('z'))
    return sp.nsimplify(sp.radsimp(sp.expand(e)))

def is_zero(e):
    return simp(e) == 0

def sign(e):
    if is_zero(e):
        return 0
    return 1 if num(e).evalf(50) > 0 else -1

D4 = {
    'identity':              lambda x, y: (x, y),
    'rotation 90':           lambda x, y: (1 - y, x),
    'rotation 180':          lambda x, y: (1 - x, 1 - y),
    'rotation 270':          lambda x, y: (y, 1 - x),
    'reflection x=1/2':      lambda x, y: (1 - x, y),
    'reflection y=1/2':      lambda x, y: (x, 1 - y),
    'reflection diagonal':   lambda x, y: (y, x),
    'reflection antidiag.':  lambda x, y: (1 - y, 1 - x),
}

def sa(a, b, c):
    return ((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])) / 2

def le(a, b):            # a <= b exactly
    return sign(b - a) >= 0

def count(n):
    P = [(sp.sympify(x), sp.sympify(y)) for x, y in configs[n]]
    found, per_g = set(), {}
    for gname, g in D4.items():
        Q = [tuple(simp(c) for c in g(*p)) for p in P]
        hits = 0
        for first5 in permutations(range(len(Q)), 5):
            B = [Q[i] for i in first5]
            if not (is_zero(B[0][0]) and is_zero(B[1][1]) and is_zero(B[2][0] - 1)
                    and is_zero(B[3][1] - 1) and is_zero(B[4][0])):
                continue
            if not (le(B[0][1], B[4][1]) and le(B[1][0], B[3][0])):
                continue
            rest = sorted((Q[i] for i in range(len(Q)) if i not in first5), key=lambda p: num(p[0]).evalf(50))
            # all orders consistent with nondecreasing x (permute ties)
            groups = [list(gr) for _, gr in groupby(rest, key=lambda p: simp(p[0]))]
            orders = [[]]
            for gr in groups:
                orders = [o + list(pm) for o in orders for pm in permutations(gr)]
            for o in orders:
                L = B + o
                ok = all(sign(sa(L[i], L[j], L[k])) > 0 for (i, j, k) in combinations(range(5), 3)) and \
                     all(sign(sa(L[0], L[4], L[k])) <= 0 for k in range(5, len(L)))
                if ok:
                    key = tuple(L)
                    if key not in found:
                        found.add(key)
                        hits += 1
        per_g[gname] = hits
    return found, per_g

if __name__ == "__main__":
    for n in (5, 7, 8, 9, 10):
        found, per_g = count(n)
        print(f"n={n}: {len(found)} feasible labeled copies")
        for gname, h in per_g.items():
            if h:
                print(f"    {gname:22s} {h} new")
        if n == 7:
            for L in sorted(found, key=lambda L: [float(num(c)) for p in L for c in p]):
                print("     ", [(round(float(num(x)), 4), round(float(num(y)), 4)) for x, y in L])
