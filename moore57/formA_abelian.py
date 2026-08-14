"""
A constructive route to Form A: commuting involutions.

Form A asks that every triangle composite tau(a,b,c) = sigma_ca sigma_bc
sigma_ab be a fixed-point-free involution.  Since each sigma is an involution,
tau^{-1} = sigma_ab sigma_bc sigma_ca, so

        tau is an involution  <==>  sigma_ca sigma_bc sigma_ab
                                  = sigma_ab sigma_bc sigma_ca

which is automatic if the bijections *commute*.  Commuting fixed-point-free
involutions generate an elementary abelian 2-group acting freely, so take
E = (Z_2)^3 of order 8 acting freely on the 56 points (56 = 8 x 7, seven
orbits) and let every sigma_ij be a non-identity element of E.

In that setting an element is fixed-point-free exactly when it is non-zero, so
with the gauge sigma_0j = identity the whole of Form A plus the Moore
conditions becomes arithmetic in (Z_2)^3 on the non-zero branches 1..n:

    a_ij != 0                                  every sigma is f.p.f.
    a_ij xor a_jk != 0                         quadrilateral through branch 0
                                               (equivalently: a proper edge
                                               colouring of K_n)
    a_ij xor a_jk xor a_ki != 0                triangle
    a_ij xor a_jk xor a_kl xor a_li != 0       quadrilateral

with the triangle condition CBA = ABC free because the group is abelian.

That is a tiny search, and it settles constructively whether Form A structures
exist at degree 57 beyond the 4 branches the annealer manages -- a question the
exact solver has so far only timed out on.  Note the ceiling built in: a proper
edge colouring of K_n with 7 colours needs n - 1 <= 7, so this construction
cannot pass n = 8, i.e. t = 9 branches.  It is a lower bound, not a route to 57.
"""

import sys
from itertools import combinations

COLOURS = list(range(1, 8))          # non-zero elements of (Z_2)^3


def search(n, want_all=False):
    """Colour the edges of K_n from (Z_2)^3 \\ {0} satisfying all conditions."""
    a = [[0] * n for _ in range(n)]
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    sols = []

    def ok(i, j):
        # proper edge colouring at both endpoints
        for k in range(n):
            if k in (i, j):
                continue
            if a[i][k] and a[i][k] == a[i][j]:
                return False
            if a[j][k] and a[j][k] == a[i][j]:
                return False
        # triangles
        for k in range(n):
            if k in (i, j) or not (a[i][k] and a[j][k]):
                continue
            if a[i][j] ^ a[j][k] ^ a[k][i] == 0:
                return False
        # quadrilaterals: 4-cycles through the edge (i, j)
        for k in range(n):
            if k in (i, j):
                continue
            for l in range(n):
                if l in (i, j, k):
                    continue
                if not (a[j][k] and a[k][l] and a[l][i]):
                    continue
                if a[i][j] ^ a[j][k] ^ a[k][l] ^ a[l][i] == 0:
                    return False
        return True

    def rec(e):
        if e == len(edges):
            sols.append([row[:] for row in a])
            return not want_all
        i, j = edges[e]
        for c in COLOURS:
            a[i][j] = a[j][i] = c
            if ok(i, j) and rec(e + 1):
                return True
            a[i][j] = a[j][i] = 0
        return False

    found = rec(0)
    return sols[0] if sols else None


def build_sigma(n, a, m=56):
    """Turn the colouring into an explicit sigma-table on m points.

    (Z_2)^3 acts freely on m = 8 * (m/8) points: write a point as
    (block, offset) with offset in (Z_2)^3, and let g act by xor on the offset.
    """
    assert m % 8 == 0
    nb = m // 8
    def act(g):
        p = [0] * m
        for b in range(nb):
            for off in range(8):
                p[b * 8 + off] = b * 8 + (off ^ g)
        return tuple(p)
    ident = tuple(range(m))
    sigma = {}
    t = n + 1
    for j in range(1, t):
        sigma[(0, j)] = ident
        sigma[(j, 0)] = ident
    for i in range(1, t):
        for j in range(1, t):
            if i != j:
                sigma[(i, j)] = act(a[i - 1][j - 1])
    return t, sigma


def main():
    import reduction
    import involution
    from itertools import permutations

    nmax = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    m = int(sys.argv[2]) if len(sys.argv) > 2 else 56

    print("Commuting-involution construction for Form A at degree 57")
    print("(E = (Z_2)^3 acting freely on %d points)\n" % m, flush=True)

    best = 0
    for n in range(2, nmax + 1):
        a = search(n)
        t = n + 1
        if a is None:
            print("  n=%-2d (t=%2d branches): none" % (n, t), flush=True)
            break
        t, sigma = build_sigma(n, a, m)
        # independent verification: Moore conditions and Form A
        ok_sig = reduction.sigma_conditions_hold(t, sigma, m=m)
        tot = inv = 0
        for x, y, z in permutations(range(t), 3):
            tau = involution.composite(sigma, t, x, y, z, m)
            tot += 1
            if involution.is_involution(tau) and all(tau[k] != k for k in range(m)):
                inv += 1
        g = reduction.build_graph(t, sigma, m=m)
        girth = reduction.girth_at_least_5(g)
        print("  n=%-2d (t=%2d branches): FOUND -- Moore conditions %s, "
              "Form A %d/%d, fragment %d vertices, girth>=5 %s"
              % (n, t, ok_sig, inv, tot, len(g), girth), flush=True)
        assert ok_sig and inv == tot and girth
        best = t

    print()
    print("  Largest Form A structure from this construction: t = %d branches."
          % best)
    if best >= 5:
        print()
        print("  That answers the existence question the exact solver could")
        print("  not decide: 5-branch Form A structures DO exist at degree 57,")
        print("  so Form A is not refuted there, and the annealer's stall at 4")
        print("  was the searcher rather than the object.")


if __name__ == "__main__":
    main()
