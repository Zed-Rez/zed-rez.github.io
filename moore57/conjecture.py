"""
The involution conjecture, in three equivalent forms.

Everything conditional in this project rests on one statement.  It is verified
at degrees 3 and 7 and open at 57.  Stating it three ways is useful because the
third form mentions no bijections, no gauge and no coordinates at all -- it is
purely about how the 5-cycles of a Moore graph sit around a path of length two,
and it is the form worth trying to prove.

FORM A (composites).  For any three branches a, j, b of the rooted
decomposition, the triangle composite

        tau(a,j,b) = sigma_{b,a} . sigma_{j,b} . sigma_{a,j}

is a fixed-point-free involution, not merely a derangement.

FORM B (1-factorizations).  After gauge-fixing sigma_{0j} = identity, every
sigma_ij with i,j >= 1 is a fixed-point-free involution of the 56 points, and
for each fixed i the family { sigma_ij : j != i } is a 1-factorization of K_56.

FORM C (five-cycles).  Let v be a vertex, u a neighbour of v, and a_x, a_y two
distinct neighbours of u other than v.  There are exactly k-1 five-cycles
through the path a_x - u - a_y; each is

        a_x - w - z - a_y - u - a_x

with w in some branch i and z in some branch j.  Write phi_{x,y}(i) = j.  Then
phi_{x,y} is an involution on the branch set.

Form C says: if you can get from a_x to a_y in two steps leaving by branch i
and arriving by branch j, then you can also do it leaving by branch j and
arriving by branch i.  A symmetry of the pentagon structure, nothing more.

This module checks all three forms on the Moore graphs that exist.
"""

import sys
from itertools import combinations, permutations

import reduction


def form_A(g, k):
    """Every triangle composite is a fixed-point-free involution."""
    m = k - 1
    _, sig = reduction.decompose(g, sorted(g, key=repr)[0])

    def s(i, j):
        return sig[(i, j)] if (i, j) in sig else reduction.inverse(sig[(j, i)])

    tot = ok = 0
    for a, j, b in permutations(range(k), 3):
        tau = reduction.compose(s(b, a), reduction.compose(s(j, b), s(a, j)))
        tot += 1
        if all(tau[tau[x]] == x for x in range(m)) and \
           all(tau[x] != x for x in range(m)):
            ok += 1
    return ok, tot


def form_B(g, k):
    """After gauging, all bijections are fixed-point-free involutions and every
    row is a 1-factorization."""
    from collections import Counter
    m = k - 1
    idp = tuple(range(m))
    _, sig = reduction.decompose(g, sorted(g, key=repr)[0])

    def s(i, j):
        if i == j:
            return idp
        return sig[(i, j)] if (i, j) in sig else reduction.inverse(sig[(j, i)])

    G = {}
    for i in range(k):
        for j in range(k):
            if i != j:
                G[(i, j)] = reduction.compose(
                    reduction.inverse(s(0, j)),
                    reduction.compose(s(i, j), s(0, i)))
    assert all(G[(0, j)] == idp for j in range(1, k)), "gauge failed"

    all_inv = all(
        all(G[(i, j)][G[(i, j)][x]] == x and G[(i, j)][x] != x for x in range(m))
        for i, j in combinations(range(1, k), 2))

    rows_ok = True
    for i in range(1, k):
        cov = Counter()
        for j in range(1, k):
            if j == i:
                continue
            p = G[(i, j)]
            for x in range(m):
                if x < p[x]:
                    cov[(x, p[x])] += 1
        if set(cov.values()) != {1} or len(cov) != m * (m - 1) // 2:
            rows_ok = False
    return all_inv, rows_ok


def form_C(g, k):
    """phi_{x,y} is an involution on the branch set, for every ordered pair."""
    m = k - 1
    root = sorted(g, key=repr)[0]
    us = sorted(g[root], key=repr)
    blocks = [sorted(g[u] - {root}, key=repr) for u in us]
    which = {w: bi for bi, b in enumerate(blocks) for w in b}
    A = blocks[0]

    tot = ok = 0
    for xi in range(m):
        for yi in range(m):
            if xi == yi:
                continue
            ax, ay = A[xi], A[yi]
            phi = {}
            for w in g[ax]:
                if w == us[0]:
                    continue
                zs = [z for z in g[w] if z in g[ay] and z != us[0]]
                assert len(zs) == 1, "expected a unique common neighbour"
                phi[which[w]] = which[zs[0]]
            tot += 1
            if all(phi[phi[i]] == i for i in phi):
                ok += 1
    return ok, tot


def main():
    print("The involution conjecture, checked where a Moore graph exists\n")
    for name, g, k in (("Petersen", reduction.petersen(), 3),
                       ("Hoffman-Singleton", reduction.hoffman_singleton(), 7)):
        a_ok, a_tot = form_A(g, k)
        b_inv, b_rows = form_B(g, k)
        c_ok, c_tot = form_C(g, k)
        print("%s (degree %d)" % (name, k))
        print("  Form A  triangle composites that are f.p.f. involutions: "
              "%d / %d" % (a_ok, a_tot))
        print("  Form B  gauged bijections all f.p.f. involutions: %s;  "
              "every row a 1-factorization: %s" % (b_inv, b_rows))
        print("  Form C  phi_{x,y} an involution: %d / %d ordered pairs"
              % (c_ok, c_tot))
        assert a_ok == a_tot and b_inv and b_rows and c_ok == c_tot
        print()

    print("All three forms hold at every degree where a Moore graph exists.")
    print("At degree 57 all three are open, and they stand or fall together.")
    print()
    print("Why it matters: Form A is false in essentially every partial")
    print("structure a search produces (0 of 1320 triples in a 12-branch")
    print("structure), so it is real information no published search uses; and")
    print("it implies the 2026 theorem that no cyclic construction exists.")
    print()
    print("Why to doubt it: the only two graphs it can be checked on are")
    print("vertex-transitive and rank 3, and the degree-57 graph is neither.")


if __name__ == "__main__":
    sys.exit(main())
