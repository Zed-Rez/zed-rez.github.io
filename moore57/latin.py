"""
A Moore graph of degree k contains a Latin square of order k - 1.

Root the graph and take two of the branches, B_0 and B_1, as coordinates.
For a vertex x_r in B_0 and y_c in B_1 define

    L(r, c) = 0                     if x_r and y_c are adjacent
    L(r, c) = j                     otherwise, where B_j is the block holding
                                    the unique common neighbour of x_r and y_c

The common neighbour cannot be the root (the root has no layer-2 neighbours),
cannot be in layer 1 (u_0 meets only B_0, u_1 only B_1), and cannot be in B_0
or B_1 (blocks are independent), so j ranges over 2..k-1 and L uses exactly
(k-2) + 1 = k - 1 symbols.

L is Latin.  In a row: x_r has exactly one neighbour in B_1, giving one cell
with symbol 0; and for each j it has exactly one neighbour z in B_j, and z has
exactly one neighbour in B_1, giving exactly one cell with symbol j.  Columns
are symmetric.

So existence of the degree-57 Moore graph implies a Latin square of order 56
carrying a great deal of extra structure -- and, read the other way, the whole
graph is 57 branches whose pairwise interaction is governed by such squares.
This module extracts L and checks it on the Moore graphs that exist.
"""

import sys
from itertools import combinations

import reduction


def latin_from_pair(k, sigma, a, b, m=None):
    """The square for the ordered branch pair (a, b), with rows indexed by
    B_a and columns by B_b, and the index sets identified through sigma_ab so
    that adjacency lands on the diagonal."""
    if m is None:
        m = k - 1

    def s(i, j):
        return sigma[(i, j)] if (i, j) in sigma else reduction.inverse(sigma[(j, i)])

    sab = s(a, b)
    L = [[None] * m for _ in range(m)]
    for r in range(m):
        for cc in range(m):
            c = sab[cc]                     # identify column index through sigma_ab
            if sab[r] == c:
                L[r][cc] = -1               # sentinel: adjacent, not a block index
                continue
            hits = [j for j in range(k) if j not in (a, b)
                    and s(a, j)[r] == s(b, j)[c]]
            if len(hits) != 1:
                return None
            L[r][cc] = hits[0]
    return L


def is_symmetric(L):
    n = len(L)
    return all(L[i][j] == L[j][i] for i in range(n) for j in range(n))


def constant_diagonal(L):
    return len({L[i][i] for i in range(len(L))}) == 1


def latin_from_sigma(k, sigma, m=None):
    """Extract L from a sigma-table, working entirely with the bijections.

    Cell (r, c) of block pair (0, 1):
      * symbol 0 if sigma_01(r) = c;
      * otherwise the unique j >= 2 with sigma_0j(r) and sigma_1j(c) equal --
        i.e. x_r and y_c have their common neighbour in block j.
    """
    if m is None:
        m = k - 1

    def s(i, j):
        return sigma[(i, j)] if (i, j) in sigma else reduction.inverse(sigma[(j, i)])

    s01 = s(0, 1)
    L = [[None] * m for _ in range(m)]
    for r in range(m):
        for c in range(m):
            if s01[r] == c:
                L[r][c] = 0
                continue
            hits = [j for j in range(2, k) if s(0, j)[r] == s(1, j)[c]]
            if len(hits) != 1:
                return None, "cell (%d,%d) has %d common neighbours" % (r, c, len(hits))
            L[r][c] = hits[0]
    return L, "ok"


def is_latin(L):
    n = len(L)
    syms = set()
    for row in L:
        syms |= set(row)
    if len(syms) != n:
        return False, "uses %d symbols, needs %d" % (len(syms), n)
    for i, row in enumerate(L):
        if len(set(row)) != n:
            return False, "row %d repeats a symbol" % i
    for j in range(n):
        col = [L[i][j] for i in range(n)]
        if len(set(col)) != n:
            return False, "column %d repeats a symbol" % j
    return True, "Latin square of order %d" % n


def intercalates(L):
    """Number of 2x2 subsquares (intercalates).  A useful fingerprint: the
    cyclic square of order n has many, and squares with none are rare."""
    n = len(L)
    total = 0
    for r1, r2 in combinations(range(n), 2):
        for c1, c2 in combinations(range(n), 2):
            if L[r1][c1] == L[r2][c2] and L[r1][c2] == L[r2][c1]:
                total += 1
    return total


def show(L):
    return "\n".join("      " + " ".join("%2d" % x for x in row) for row in L)


def report(name, g, k):
    print("%s (degree %d, blocks of %d)" % (name, k, k - 1))
    _, sigma = reduction.decompose(g, sorted(g, key=reduction.repr_key)[0]
                                   if hasattr(reduction, "repr_key")
                                   else sorted(g, key=repr)[0])
    L, msg = latin_from_sigma(k, sigma)
    if L is None:
        print("  extraction FAILED: %s" % msg)
        return None
    ok, what = is_latin(L)
    print("  %s -- %s" % (what, "VERIFIED" if ok else "NOT LATIN"))
    assert ok, what
    print("  intercalates (2x2 subsquares): %d" % intercalates(L))
    if k <= 8:
        print(show(L))
    print()
    return L


def main():
    print("The Latin square hidden in a Moore graph\n")
    report("Petersen", reduction.petersen(), 3)
    report("Hoffman-Singleton", reduction.hoffman_singleton(), 7)

    print("Every ordered pair of branches, not just the one we looked at.")
    print("Indices are identified through sigma_ab, so adjacency sits on the")
    print("diagonal by construction -- the question is whether the square is")
    print("Latin (claimed above) and whether it is symmetric.  A symmetric")
    print("Latin square with constant diagonal is a 1-factorization of K_{k-1}.\n")
    for name, g, k in (("Petersen", reduction.petersen(), 3),
                       ("Hoffman-Singleton", reduction.hoffman_singleton(), 7)):
        _, sigma = reduction.decompose(g, sorted(g, key=repr)[0])
        tot = lat = sym = 0
        for a in range(k):
            for b in range(k):
                if a == b:
                    continue
                L = latin_from_pair(k, sigma, a, b)
                tot += 1
                if L is None:
                    continue
                if is_latin(L)[0]:
                    lat += 1
                if is_symmetric(L):
                    sym += 1
        print("  %-18s %d ordered pairs: %d Latin, %d symmetric"
              % (name, tot, lat, sym))
    print()

    print("Consequence for degree 57: any such graph yields a Latin square of")
    print("order 56 for every ordered pair of its 57 branches -- 3192 squares,")
    print("mutually constrained.  Note the constraint is real but not by itself")
    print("prohibitive: Latin squares of order 56 are plentiful.  What it rules")
    print("out is any construction whose branch pairs fail to be Latin, and it")
    print("is the same structure that makes the degree-7 case work, so it")
    print("cannot be used to argue non-existence on its own.")


if __name__ == "__main__":
    main()
