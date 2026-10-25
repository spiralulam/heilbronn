"""Check whether symmetric images of the n=7 optimum are feasible for P*_Delta
(Referee 2, comment 2a). Applies all 8 elements of D4 to the exact optimum,
tries every labeling compatible with the boundary pattern of Table 1, and
reports those satisfying all constraints of P*: fixed coordinates, x2<=x4,
y1<=y5, x6<=...<=xn, and the sign fixing on T+ and T-."""
import json
from itertools import combinations, permutations
from mpmath import mp, mpf
mp.dps = 40
TOL = mpf('1e-20')
def load(n):
    d = json.load(open(f"../best-known-configurations/config_n{n:02d}.json"))
    return [(mpf(p[0]), mpf(p[1])) for p in d['points']]
D4 = [lambda x, y: (x, y), lambda x, y: (1-y, x), lambda x, y: (1-x, 1-y), lambda x, y: (y, 1-x),
      lambda x, y: (1-x, y), lambda x, y: (x, 1-y), lambda x, y: (y, x), lambda x, y: (1-y, 1-x)]
def sA(a, b, c): return ((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]))/2
def feasible(L):
    n = len(L); eq = lambda u, v: abs(u-v) < TOL
    p = L
    if not (eq(p[0][0], 0) and eq(p[1][1], 0) and eq(p[2][0], 1) and eq(p[3][1], 1) and eq(p[4][0], 0)): return False
    if p[1][0] > p[3][0] + TOL or p[0][1] > p[4][1] + TOL: return False
    if any(p[i][0] > p[i+1][0] + TOL for i in range(5, n-1)): return False
    for (i, j, k) in combinations(range(n), 3):
        a = sA(p[i], p[j], p[k])
        if k <= 4 and a < -TOL: return False
        if i == 0 and j == 4 and a > TOL: return False
    return True
for n in (5, 7, 8, 9):
    P = load(n); found = set()
    for gi, g in enumerate(D4):
        Q = [g(*q) for q in P]
        for first5 in permutations(range(n), 5):
            B = [Q[i] for i in first5]
            if not (abs(B[0][0]) < TOL and abs(B[1][1]) < TOL and abs(B[2][0]-1) < TOL and abs(B[3][1]-1) < TOL and abs(B[4][0]) < TOL):
                continue
            rest = sorted([Q[i] for i in range(n) if i not in first5])
            # all orderings of the interior points consistent with nondecreasing x
            for perm in permutations(rest):
                L = B + list(perm)
                if feasible(L):
                    found.add(tuple((mp.nstr(a, 10), mp.nstr(b, 10)) for a, b in L))
    print(f"n={n}: {len(found)} distinct labeled solutions of the optimum are feasible for P*")
    for s in sorted(found): print("   ", s)
