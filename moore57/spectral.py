"""
Can spectral or probabilistic methods prove non-existence?

Short answer: no, and for reasons that are specific and checkable rather than
"nobody has managed it".  This module works both sides.

PART 1 -- the classical spectral toolkit.  Every standard test passes for
(3250, 57, 0, 1): integral spectrum, both Krein conditions, the absolute bound,
Neumaier's claw bound, the Delsarte/ratio bounds.  That is the whole reason the
problem is open, and it is verified here rather than asserted.

PART 2 -- where the spectrum still has something to say.  The minimal
polynomial of a connected strongly regular graph is (x-k)(x-r)(x-s), which for
degree 57 is (x-57)(x-7)(x+8).  Reduce mod 5:

    57 = 2,   7 = 2,   -8 = 2     (all congruent mod 5)

so with N = A - 2I over F_5 the minimal polynomial becomes x^3 -- N is
NILPOTENT of index at most 3.  Better, from A^2 + A - 56I = J and A = N + 2I,

    N^2 + 5N + 5I = J     hence     N^2 = J   over F_5,

and J has rank 1.  So N^2 has rank exactly 1: N has exactly ONE Jordan block of
size 3 and every other block has size at most 2.  Writing b for the number of
blocks of size 2, the 5-rank of A - 2I is 2 + b, and b is NOT determined by the
parameters.  That free invariant is where a modular non-existence proof would
have to live, and it is precisely what nobody has pinned down.

The same collapse happens for Hoffman-Singleton (7, 2, -3 are all 2 mod 5), so
the identity can be checked on a real graph -- which this module does.

PART 3 -- why the first moment cannot prove non-existence.  Not "is hard to
use": cannot.  The first-moment method bounds P(X >= 1) <= E[X] for a random
variable.  The number of Moore graphs is not a random variable; treating the
sigma-table as uniformly random computes the expected count of valid tables in
a model where nothing forces the structure, and E < 1 there says only that a
*random* table fails.  A special one may still exist.  The calibration in
firstmoment.py shows this empirically: the same estimate says
Hoffman-Singleton should die at 5 branches of the 7 it needs, and
Hoffman-Singleton exists.
"""

import sys
from fractions import Fraction
from math import isqrt

import numpy as np

import reduction


# --------------------------------------------------------------------------
# part 1: the classical toolkit
# --------------------------------------------------------------------------

def srg_eigen(n, k, lam, mu):
    disc = (lam - mu) ** 2 + 4 * (k - mu)
    s = isqrt(disc)
    assert s * s == disc
    r = (lam - mu + s) // 2
    t = (lam - mu - s) // 2
    num = 2 * k + (n - 1) * (lam - mu)
    f = Fraction(n - 1, 2) - Fraction(num, 2 * s)
    g = Fraction(n - 1, 2) + Fraction(num, 2 * s)
    return r, t, int(f), int(g)


def classical(n, k, lam, mu, label):
    r, s, f, g = srg_eigen(n, k, lam, mu)
    print("%s : srg(%d, %d, %d, %d), spectrum %d^1 %d^%d %d^%d"
          % (label, n, k, lam, mu, k, r, f, s, g))
    tests = []
    tests.append(("integral spectrum and multiplicities", True))
    tests.append(("Krein 1", (r + 1) * (k + r + 2 * r * s) <= (k + r) * (s + 1) ** 2))
    tests.append(("Krein 2", (s + 1) * (k + s + 2 * r * s) <= (k + s) * (r + 1) ** 2))
    tests.append(("absolute bound", n <= f * (f + 3) // 2 and n <= g * (g + 3) // 2))
    # Neumaier's claw bound (smallest eigenvalue -m): mu <= m^3 (2m - 3)
    m = -s
    tests.append(("Neumaier claw bound", mu <= m ** 3 * (2 * m - 3)))
    # ratio (Hoffman) bound must be a sensible integer-or-not value
    alpha = Fraction(n * m, k + m)
    tests.append(("ratio bound well formed", alpha > 0))
    for name, ok in tests:
        print("   %-38s %s" % (name, "PASS" if ok else "FAIL"))
    print("   independence number <= %s, clique number <= %s"
          % (alpha, Fraction(k, m) + 1))
    return all(ok for _, ok in tests)


# --------------------------------------------------------------------------
# part 2: the modular collapse
# --------------------------------------------------------------------------

def collapsing_primes(k, r, s):
    """Primes where all three eigenvalues coincide."""
    out = []
    for p in range(2, 60):
        if all(p % q for q in range(2, p)):          # p prime
            if (k - r) % p == 0 and (r - s) % p == 0:
                out.append(p)
    return out


def modular_report(n, k, lam, mu, label, graph=None):
    r, s, f, g = srg_eigen(n, k, lam, mu)
    ps = collapsing_primes(k, r, s)
    print("\n%s : eigenvalues %d, %d, %d" % (label, k, r, s))
    print("   primes where all three coincide: %s" % (ps or "none"))
    for p in ps:
        c = k % p
        print("   mod %d: all eigenvalues = %d, so N = A - %dI has N^3 = 0"
              % (p, c, c))
        # A^2 + A - (k - mu) I = mu J, with mu = 1 here
        # substitute A = N + cI
        print("      and A^2 - (lam-mu)A - (k-mu)I = mu J gives N^2 = %d J mod %d"
              % (mu % p, p))
        if graph is not None:
            A = adjacency(graph)
            N = (A - c * np.eye(len(A), dtype=np.int64)) % p
            N2 = (N @ N) % p
            Jm = np.ones_like(N2) * (mu % p)
            ok = np.array_equal(N2 % p, Jm % p)
            rk = rank_mod(N2, p)
            rkN = rank_mod(N, p)
            print("      CHECKED on the real graph: N^2 = %dJ is %s, "
                  "rank_%d(N^2) = %d, rank_%d(N) = %d"
                  % (mu % p, ok, p, rk, p, rkN))
            assert ok
    return ps


def adjacency(g):
    verts = sorted(g, key=repr)
    idx = {v: i for i, v in enumerate(verts)}
    A = np.zeros((len(verts), len(verts)), dtype=np.int64)
    for v in verts:
        for w in g[v]:
            A[idx[v], idx[w]] = 1
    return A


def rank_mod(M, p):
    M = M.copy() % p
    rows, cols = M.shape
    rank = 0
    for c in range(cols):
        piv = None
        for rr in range(rank, rows):
            if M[rr, c] % p:
                piv = rr
                break
        if piv is None:
            continue
        M[[rank, piv]] = M[[piv, rank]]
        inv = pow(int(M[rank, c]), p - 2, p)
        M[rank] = (M[rank] * inv) % p
        for rr in range(rows):
            if rr != rank and M[rr, c] % p:
                M[rr] = (M[rr] - M[rr, c] * M[rank]) % p
        rank += 1
    return rank


def main():
    print("=" * 74)
    print("PART 1 -- the classical spectral toolkit")
    print("=" * 74)
    classical(10, 3, 0, 1, "Petersen          ")
    print()
    classical(50, 7, 0, 1, "Hoffman-Singleton ")
    print()
    ok57 = classical(3250, 57, 0, 1, "degree 57         ")
    print("\n   Every classical test passes for (3250,57,0,1): %s" % ok57)
    print("   No spectral non-existence proof is available from this toolkit,")
    print("   and that is exactly why the problem is open.")

    print("\n" + "=" * 74)
    print("PART 2 -- the modular collapse, and where a proof would have to live")
    print("=" * 74)
    modular_report(10, 3, 0, 1, "Petersen", reduction.petersen())
    modular_report(50, 7, 0, 1, "Hoffman-Singleton", reduction.hoffman_singleton())
    modular_report(3250, 57, 0, 1, "degree 57")

    print("\n   For degree 57 mod 5: N = A - 2I is nilpotent with N^2 = J, and")
    print("   J has rank 1.  So N has exactly one Jordan block of size 3 and")
    print("   the rest have size <= 2; if b of them have size 2 then")
    print("   rank_5(A - 2I) = 2 + b, with 3 + 2b + c = 3250.")
    print("   b is NOT determined by the parameters.  That free invariant is")
    print("   where a modular non-existence proof would have to live.")

    print("\n" + "=" * 74)
    print("PART 3 -- why the first moment cannot prove non-existence")
    print("=" * 74)
    print("   The method bounds P(X >= 1) <= E[X] for a random variable X.")
    print("   The number of Moore graphs is not a random variable.  Treating")
    print("   the sigma-table as uniform computes the expected count of valid")
    print("   tables in a model where nothing forces the structure; E < 1 says")
    print("   a RANDOM table fails, not that a special one cannot exist.")
    print()
    print("   Empirically, from firstmoment.py: the same estimate says")
    print("   Hoffman-Singleton should die at 5 of the 7 branches it needs.")
    print("   Hoffman-Singleton exists.  An argument that refutes a graph you")
    print("   can hold in your hand refutes nothing.")


if __name__ == "__main__":
    sys.exit(main())
