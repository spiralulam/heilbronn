"""Best-known configurations, labeled so that they are feasible for P*_Delta.

Used for the warm-start runs (block E). Coordinates come from
../best-known-configurations (full-precision doubles). A labeling is found
by trying all elements of D4 and all assignments of the five boundary roles,
exactly as in ../verification/check_symmetric_feasible.py.
"""
import json
from itertools import combinations, permutations
from pathlib import Path

CANON = Path(__file__).resolve().parents[1] / "best-known-configurations"
TOL = 1e-12

D4 = [lambda x, y: (x, y), lambda x, y: (1 - y, x), lambda x, y: (1 - x, 1 - y),
      lambda x, y: (y, 1 - x), lambda x, y: (1 - x, y), lambda x, y: (x, 1 - y),
      lambda x, y: (y, x), lambda x, y: (1 - y, 1 - x)]


def load(n):
    d = json.load(open(CANON / f"config_n{n:02d}.json"))
    return [(float(p[0]), float(p[1])) for p in d["points"]]


def _sa(a, b, c):
    return 0.5 * ((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))


def _feasible_full(L):
    n = len(L)
    if not (abs(L[0][0]) < TOL and abs(L[1][1]) < TOL and abs(L[2][0] - 1) < TOL
            and abs(L[3][1] - 1) < TOL and abs(L[4][0]) < TOL):
        return False
    if L[1][0] > L[3][0] + TOL or L[0][1] > L[4][1] + TOL:
        return False
    if any(L[i][0] > L[i + 1][0] + TOL for i in range(5, n - 1)):
        return False
    for (i, j, k) in combinations(range(n), 3):
        a = _sa(L[i], L[j], L[k])
        if k <= 4 and a < -TOL:
            return False
        if i == 0 and j == 4 and a > TOL:
            return False
    return True


def labeled_for_full(n):
    """One labeling of the best-known n-point configuration feasible for P*."""
    P = load(n)
    for g in D4:
        Q = [g(*q) for q in P]
        for first5 in permutations(range(n), 5):
            B = [Q[i] for i in first5]
            rest = sorted(Q[i] for i in range(n) if i not in first5)
            L = B + rest
            if _feasible_full(L):
                # snap boundary coordinates to the exact fixed values
                L[0] = (0.0, L[0][1]); L[1] = (L[1][0], 0.0); L[2] = (1.0, L[2][1])
                L[3] = (L[3][0], 1.0); L[4] = (0.0, L[4][1])
                return L
    raise RuntimeError(f"no feasible labeling found for n={n}")


if __name__ == "__main__":
    for n in range(5, 11):
        print(n, labeled_for_full(n))
