"""
A rigorous impossibility proof for reflection constructions.

In the gauged matching model (gauged_search.py) the non-root bijections are
perfect matchings M_ij on the m = k-1 points, and the quadrilaterals through
the root force, for each branch i, the m-1 matchings {M_ij : j != i} to be
pairwise edge-disjoint.

Suppose we try to realise them as reflections in a fixed abelian group G of
order m:

        M_ij(x) = g_ij - x .

Then everything algebraic falls out for free:

  * M_ij is an involution, always;
  * M_ij is fixed-point-free  <=>  g_ij - x != x for all x  <=>  g_ij not in 2G;
  * M_ij and M_il are edge-disjoint  <=>  g_ij != g_il;
  * triangle composites are reflections (hence involutions), fixed-point-free
    under the same "not in 2G" condition, which for all-odd labels is automatic.

So the construction needs, for each branch i, that the m-1 labels g_ij for
j != i be **distinct elements of G \ 2G**.  That is a pure counting condition:

        |G \ 2G|  >=  m - 1 .

Now |2G| = |G| / |G[2]| where G[2] is the 2-torsion subgroup, so

        |G \ 2G| = m - m/|G[2]|  >=  m - 1   <=>   m/|G[2]| <= 1
                                            <=>   G[2] = G
                                            <=>   G is elementary abelian of
                                                  exponent 2, so m is a power of 2.

THEOREM.  A reflection construction over an abelian group exists only when
m = k - 1 is a power of two.

  m = 2  (degree 3)   : possible, and it is the Petersen graph.
  m = 6  (degree 7)   : impossible -- 6 is not a power of two.
  m = 56 (degree 57)  : impossible -- 56 is not a power of two.

This matches the solver exactly: reflection.py returns a Moore graph at degree
3 and INFEASIBLE at degree 7.  It is a proof rather than a search result, and
it disposes of the whole reflection family at degree 57 in one line -- the best
available abelian group of order 56 supplies only 49 usable labels where 55 are
needed.
"""

from itertools import product


def abelian_groups_of_order(n):
    """All abelian groups of order n, as tuples of invariant prime-power
    factors (the multiset of cyclic factor orders in a primary decomposition)."""
    def factor(n):
        f, d = {}, 2
        while d * d <= n:
            while n % d == 0:
                f[d] = f.get(d, 0) + 1
                n //= d
            d += 1
        if n > 1:
            f[n] = f.get(n, 0) + 1
        return f

    def partitions(k):
        if k == 0:
            yield ()
            return
        for first in range(k, 0, -1):
            for rest in partitions(k - first):
                if not rest or rest[0] <= first:
                    yield (first,) + rest

    f = factor(n)
    per_prime = []
    for p, e in sorted(f.items()):
        per_prime.append([tuple(p ** a for a in part) for part in partitions(e)])
    for combo in product(*per_prime):
        parts = []
        for c in combo:
            parts.extend(c)
        yield tuple(sorted(parts))


def two_torsion_order(parts):
    """|G[2]| for G = product of cyclic groups of the given orders."""
    out = 1
    for q in parts:
        if q % 2 == 0:
            out *= 2
    return out


def usable_labels(m, parts):
    """|G \\ 2G| = m - m/|G[2]|."""
    return m - m // two_torsion_order(parts)


def report(m, degree):
    need = m - 1
    print("m = %d  (degree %d):  each branch needs %d distinct labels in G \\ 2G"
          % (m, degree, need))
    best = 0
    for parts in abelian_groups_of_order(m):
        have = usable_labels(m, parts)
        best = max(best, have)
        name = " x ".join("Z_%d" % q for q in parts)
        print("    %-28s |G\\2G| = %-4d %s"
              % (name, have, "OK" if have >= need else "short by %d" % (need - have)))
    verdict = "POSSIBLE" if best >= need else "IMPOSSIBLE"
    print("    -> reflection construction %s (best group supplies %d of %d)\n"
          % (verdict, best, need))
    return best >= need


def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0


def main():
    print(__doc__.split("THEOREM.")[0].strip()[:0] or "", end="")
    print("Reflection constructions: a counting impossibility\n")
    for degree in (3, 7, 57):
        m = degree - 1
        ok = report(m, degree)
        assert ok == is_power_of_two(m), \
            "the counting verdict must agree with 'm is a power of two'"

    print("The verdict is exactly 'm is a power of two' in every case, which is")
    print("the theorem: G \\ 2G has m - m/|G[2]| elements, and that reaches the")
    print("required m - 1 only when G[2] = G.\n")

    print("Cross-check against the solver (reflection.py):")
    print("  degree 3  : counting says POSSIBLE     -- solver returns a Moore graph")
    print("  degree 7  : counting says IMPOSSIBLE   -- solver returns INFEASIBLE")
    print("  degree 57 : counting says IMPOSSIBLE   -- no search needed")


if __name__ == "__main__":
    main()
