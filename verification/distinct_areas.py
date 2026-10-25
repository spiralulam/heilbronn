"""Critical-triangle counts and numbers of distinct triangle areas for the
best-known square configurations n = 5..16 (../best-known-configurations,
double precision). Areas are grouped with tolerance 1e-12."""
import json
from itertools import combinations
from mpmath import mp, mpf
mp.dps = 40
CONFIGS = "../best-known-configurations"
for n in range(5, 17):
    d = json.load(open(f"{CONFIGS}/config_n{n:02d}.json"))
    P = [(mpf(repr(p[0])), mpf(repr(p[1]))) for p in d['points']]
    A = sorted(abs(((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]))/2) for a, b, c in combinations(P, 3))
    tol = mpf('1e-12')
    crit = sum(1 for a in A if a - A[0] < tol)
    distinct = 1 + sum(1 for u, v in zip(A, A[1:]) if v - u > tol)
    print(n, "crit", crit, "distinct", distinct, "of", len(A), "min", mp.nstr(A[0], 12), d['source'])
