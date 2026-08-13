"""
An explicit algebraic candidate, and what breaks.

The gauged model (gauged_search.py) says the object is startlingly symmetric:
branches 1..56 and points 1..56, an assignment {i,j} |-> M_ij of a perfect
matching on the points to every pair of branches, symmetric, such that each
branch's 55 matchings form a 1-factorization of K_56.  Dually, each point pair
gives a perfect matching on the branches.

So the natural thing to try is the standard round-robin 1-factorization on both
sides.  Index both the 56 points and the 56 branches by Z_55 + {inf}.  The
round-robin colouring assigns to an edge the colour

        c({a,b}) = (a + b) / 2  (mod 55)          for a, b in Z_55
        c({inf, a}) = a

and the matching of colour s is

        F_s :  inf <-> s,   a <-> 2s - a   (a != s).

Setting M_ij = F_{c(i,j)} makes every structural condition through the root
true by construction.  What remains are the triangle and quadrilateral
conditions among non-root branches.  This module measures exactly how many of
those hold, for this construction and for twisted variants of it.
"""

import sys
from itertools import combinations

N = 55                      # Z_55 plus one point at infinity
M_POINTS = N + 1            # 56
INF = N                     # index of the point at infinity

HALF = pow(2, -1, N)        # inverse of 2 mod 55


def colour(a, b):
    """Round-robin colour of the edge {a, b} on Z_55 + {inf}."""
    if a == INF:
        return b
    if b == INF:
        return a
    return ((a + b) * HALF) % N


def factor(s):
    """The perfect matching of colour s, as a permutation of 0..55."""
    f = [0] * M_POINTS
    f[INF] = s
    f[s] = INF
    for a in range(N):
        if a != s:
            f[a] = (2 * s - a) % N
    return f


def build(twist=None):
    """M[(i,j)] for branches i, j in 0..55.  ``twist`` optionally remaps the
    colour before choosing the factor, giving a family of candidates."""
    fac = [factor(s) for s in range(N)]
    M = {}
    for i, j in combinations(range(M_POINTS), 2):
        s = colour(i, j)
        if twist is not None:
            s = twist(s)
        M[(i, j)] = fac[s]
        M[(j, i)] = fac[s]
    return M


def audit(M, branches=None, verbose=True):
    """Check the conditions the construction does not get for free."""
    if branches is None:
        branches = list(range(M_POINTS))
    m = M_POINTS

    # rows are 1-factorizations (should hold by construction)
    row_ok = 0
    row_tot = 0
    for i in branches:
        others = [j for j in branches if j != i]
        for j, l in combinations(others, 2):
            row_tot += 1
            if all(M[(i, j)][x] != M[(i, l)][x] for x in range(m)):
                row_ok += 1

    tri_fpf = tri_inv = tri_tot = 0
    for i, j, l in combinations(branches, 3):
        for a, b, c in ((i, j, l), (i, l, j)):
            tau = [M[(c, a)][M[(b, c)][M[(a, b)][x]]] for x in range(m)]
            tri_tot += 1
            if all(tau[x] != x for x in range(m)):
                tri_fpf += 1
            if all(tau[tau[x]] == x for x in range(m)):
                tri_inv += 1

    quad_fpf = quad_tot = 0
    for quad in combinations(branches, 4):
        a, b, c, d = quad
        for p, q, u, w in ((a, b, c, d), (a, b, d, c), (a, c, b, d)):
            comp = [M[(w, p)][M[(u, w)][M[(q, u)][M[(p, q)][x]]]]
                    for x in range(m)]
            quad_tot += 1
            if all(comp[x] != x for x in range(m)):
                quad_fpf += 1

    if verbose:
        print("    rows are 1-factorizations : %d/%d" % (row_ok, row_tot))
        print("    triangles fixed-point-free: %d/%d" % (tri_fpf, tri_tot))
        print("    triangles involutive      : %d/%d" % (tri_inv, tri_tot))
        print("    quadrilaterals f.p.f.     : %d/%d" % (quad_fpf, quad_tot))
    return (row_ok == row_tot and tri_fpf == tri_tot
            and tri_inv == tri_tot and quad_fpf == quad_tot)


def main():
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    branches = list(range(nb))
    print("round-robin construction, auditing the first %d branches" % nb)
    M = build()
    ok = audit(M, branches)
    print("  all conditions hold: %s\n" % ok)

    print("twisted variants s |-> u*s + v  (u a unit mod 55):")
    best = None
    for u in (1, 2, 3, 4, 6, 7, 8, 9, 12, 13):
        if u % 5 == 0 or u % 11 == 0:
            continue
        for v in range(0, 5):
            Mt = build(twist=lambda s, u=u, v=v: (u * s + v) % N)
            m = M_POINTS
            tri_bad = 0
            for i, j, l in combinations(branches, 3):
                for a, b, c in ((i, j, l), (i, l, j)):
                    tau = [Mt[(c, a)][Mt[(b, c)][Mt[(a, b)][x]]]
                           for x in range(m)]
                    if not all(tau[x] != x for x in range(m)):
                        tri_bad += 1
            if best is None or tri_bad < best[0]:
                best = (tri_bad, u, v)
    print("  fewest failing triangles over the variants tried: %d (u=%d, v=%d)"
          % best)


if __name__ == "__main__":
    main()
