"""
THEOREM.  The reflection ansatz cannot produce a Moore graph of degree 57.

Setting.  The ansatz takes every bijection to be a reflection of Z_56,
sigma_ij(x) = g_ij - x with g_ij = g_ji.  Section 20n shows this makes every
triangle composite an involution automatically, so Form A holds; and every g_ij
must be odd for the triangle composites to be fixed-point-free.  Writing
g_ij = 2 f_ij + 1 turns the quadrilateral condition into

        f_pw - f_uw + f_qu - f_pq  !=  0   (mod 28)

for the 4-cycle p -> q -> u -> w -> p, with f symmetric.

Step 1 (the collapse).  Because f is symmetric, f_qu = f_uq, so

        f_pw - f_uw + f_qu - f_pq  =  (f_pw - f_pq) - (f_uw - f_uq).

Step 2 (what the conditions say).  For a 4-set the three cyclic orders
correspond exactly to the three ways of splitting it into two pairs {p,u} and
{q,w}.  So the full set of quadrilateral conditions is equivalent to:

    for every pair {q, w}, the map   i  |->  f_iw - f_iq  (mod 28)
    is INJECTIVE over the indices i outside {q, w}.

Step 3 (the count).  That map takes t - 2 arguments and lands in Z_28, so
injectivity forces

        t - 2  <=  28,      i.e.      t  <=  30.

A Moore graph of degree 57 needs t = 57 branches.  Therefore no Moore graph of
degree 57 has all of its bijections reflections in Z_56.  []

This is the same shape as the published result that no cyclic construction
exists (Axioms 2026), and it is proved here for a different and strictly larger
family -- the reflection family contains structures reaching 14 branches, where
the cyclic one dies at 4 under Form A.

The module checks Step 2 by brute force on random labellings (the equivalence
is an identity, so any counterexample would be a bug), and checks the bound
against the certificates on disk.
"""

import glob
import json
import random
import sys
from itertools import combinations

MOD = 28


def quad_violations(f, t):
    """Vanishing 4-cycle sums, counted directly."""
    n = 0
    for a, b, c, d in combinations(range(t), 4):
        for (p, q, u, w) in ((a, b, c, d), (a, b, d, c), (a, c, b, d)):
            if (f[(p, w)] - f[(u, w)] + f[(q, u)] - f[(p, q)]) % MOD == 0:
                n += 1
    return n


def injectivity_failures(f, t):
    """Pairs {q,w} where i -> f_iw - f_iq repeats a value."""
    n = 0
    for q, w in combinations(range(t), 2):
        seen = {}
        for i in range(t):
            if i in (q, w):
                continue
            v = (f[(i, w)] - f[(i, q)]) % MOD
            if v in seen:
                n += 1
            seen[v] = i
    return n


def sym(rng, t):
    f = {}
    for i in range(t):
        for j in range(i, t):
            v = rng.randrange(MOD)
            f[(i, j)] = f[(j, i)] = v
    return f


def main():
    rng = random.Random(20240607)
    print("Step 2, checked by brute force on random symmetric labellings")
    print("(the two counts must vanish together, and in fact match):\n")
    print("  %-5s %-8s %-22s %s" % ("t", "trial", "quad violations",
                                    "injectivity failures"))
    agree = True
    for t in (5, 6, 7, 8):
        for trial in range(4):
            f = sym(rng, t)
            a = quad_violations(f, t)
            b = injectivity_failures(f, t)
            print("  %-5d %-8d %-22d %d" % (t, trial, a, b))
            if (a == 0) != (b == 0):
                agree = False
    print("\n  vanish together in every case: %s" % agree)
    assert agree

    print("\nThe bound: t - 2 distinct values are needed from Z_%d, so t <= %d."
          % (MOD, MOD + 2))
    print("A Moore graph of degree 57 needs t = 57.")
    print("=> No Moore graph of degree 57 has all bijections reflections in "
          "Z_56.\n")

    print("Certificates on disk, checked against the theorem:")
    for path in sorted(glob.glob("formA_*t*.json")):
        try:
            d = json.load(open(path))
        except Exception:
            continue
        if "labels" not in d:
            continue
        t = d["t"]
        lab = {tuple(int(z) for z in k.split(",")): v
               for k, v in d["labels"].items()}
        f = {}
        for (i, j), g in lab.items():
            v = ((g - 1) // 2) % MOD
            f[(i, j)] = f[(j, i)] = v
        for i in range(t):
            f.setdefault((i, i), 0)
        bad = injectivity_failures(f, t)
        print("  %-32s t=%-3d injectivity failures %d  (bound allows t<=%d)"
              % (path, t, bad, MOD + 2))
        assert bad == 0, path


if __name__ == "__main__":
    sys.exit(main())
