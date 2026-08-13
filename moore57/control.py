"""
Control experiment: is the involution property real, or automatic at m = 6?

Every positive data point for the involution property comes from graphs with
m = k-1 equal to 2 or 6.  Those are tiny, and in tiny symmetric groups a lot of
statements are true by accident.  Before leaning on the property at m = 56 it
has to be checked that it is not simply forced by the size.

The question: for three *pairwise edge-disjoint* perfect matchings A, B, C of
an m-set (which is what M_ij, M_jl, M_li must be, since each pair shares an
index), how often is the composite C.B.A an involution?

  * If the answer is "always" at m = 6, then Hoffman-Singleton's 210/210 says
    nothing at all and the whole conjecture collapses to an artefact.
  * If the answer is "rarely", the 210/210 is a real signal.

The same statistic is then computed at larger even m by sampling, to see how
the base rate behaves as m grows towards 56.
"""

import random
import sys
from itertools import combinations


def matchings(m):
    """All perfect matchings of an m-set, as permutations (tuples)."""
    out = []

    def rec(rem, acc):
        if not rem:
            p = [0] * m
            for a, b in acc:
                p[a] = b
                p[b] = a
            out.append(tuple(p))
            return
        x = rem[0]
        for i in range(1, len(rem)):
            y = rem[i]
            rec([z for z in rem[1:] if z != y], acc + [(x, y)])

    rec(list(range(m)), [])
    return out


def random_matching(m, rng):
    pts = list(range(m))
    rng.shuffle(pts)
    p = [0] * m
    for i in range(0, m, 2):
        a, b = pts[i], pts[i + 1]
        p[a] = b
        p[b] = a
    return tuple(p)


def disjoint(p, q):
    return all(p[x] != q[x] for x in range(len(p)))


def compose(q, p):
    return tuple(q[x] for x in p)


def is_involution(p):
    return all(p[p[x]] == x for x in range(len(p)))


def is_fpf(p):
    return all(p[x] != x for x in range(len(p)))


def exhaustive(m):
    ms = matchings(m)
    tot = inv = fpf = 0
    for A in ms:
        for B in ms:
            if not disjoint(A, B):
                continue
            for C in ms:
                if not disjoint(C, A) or not disjoint(C, B):
                    continue
                tau = compose(C, compose(B, A))
                tot += 1
                if is_involution(tau):
                    inv += 1
                if is_fpf(tau):
                    fpf += 1
    return tot, inv, fpf, len(ms)


def sampled(m, trials, rng):
    tot = inv = fpf = 0
    while tot < trials:
        A = random_matching(m, rng)
        B = random_matching(m, rng)
        if not disjoint(A, B):
            continue
        C = random_matching(m, rng)
        if not disjoint(C, A) or not disjoint(C, B):
            continue
        tau = compose(C, compose(B, A))
        tot += 1
        if is_involution(tau):
            inv += 1
        if is_fpf(tau):
            fpf += 1
    return tot, inv, fpf


def main():
    print("Control: how often is the composite of three pairwise disjoint")
    print("perfect matchings an involution?\n")
    print("  %-6s %-12s %-22s %s"
          % ("m", "triples", "composite an involution", "composite f.p.f."))

    for m in (4, 6, 8):
        tot, inv, fpf, nm = exhaustive(m)
        print("  %-6d %-12d %-22s %s"
              % (m, tot, "%d  (%.4g%%)" % (inv, 100.0 * inv / tot),
                 "%d  (%.4g%%)" % (fpf, 100.0 * fpf / tot)))

    rng = random.Random(20260813)
    for m in (10, 12, 16, 24, 56):
        tot, inv, fpf = sampled(m, 200000, rng)
        print("  %-6d %-12s %-22s %s"
              % (m, "%d sampled" % tot,
                 "%d  (%.4g%%)" % (inv, 100.0 * inv / tot),
                 "%d  (%.4g%%)" % (fpf, 100.0 * fpf / tot)))

    print()
    print("At m = 6 the base rate is 25%, so Hoffman-Singleton's 210/210 is a")
    print("real signal, not an artefact of the group being small.  But the rate")
    print("collapses with m: nothing in 200,000 samples at m = 24 or m = 56.")
    print()
    severity()


def severity():
    """How much correlation would the property need in order to hold?"""
    from math import comb, lgamma, log, log10

    def involutions(m):
        a, b = 1, 1
        for n in range(2, m + 1):
            a, b = b, b + (n - 1) * a
        return b

    def fpf_involutions(m):
        r, n = 1, m - 1
        while n > 1:
            r *= n
            n -= 2
        return r

    print("How severe is the constraint?  A first-moment count for the gauged")
    print("model: C(m,2) matchings to choose, C(m,3) triangle conditions, each")
    print("asking a permutation of m points to be an involution.\n")
    print("  %-10s %-16s %-18s %s"
          % ("degree", "freedom", "cost of conditions", "expected count"))
    rows = {}
    for k in (7, 57):
        m = k - 1
        pairs, tri = comb(m, 2), comb(m, 3)
        free = pairs * log10(fpf_involutions(m))
        p = log10(involutions(m)) - lgamma(m + 1) / log(10)
        cost = tri * p
        rows[k] = free + cost
        print("  %-10d 10^%-13.0f 10^%-15.0f 10^%.0f"
              % (k, free, cost, free + cost))
    print()
    print("  degree  7 : short by %.0f orders of magnitude -- and the graph"
          % -rows[7])
    print("              exists, so correlation bridges that easily.")
    print("  degree 57 : short by %.0f orders of magnitude." % -rows[57])
    print()
    print("That is the honest reading, and it cuts against the conjecture.  The")
    print("first-moment method is unreliable here -- it is wrong at degree 7 by")
    print("construction.  But being wrong by 2 orders and being wrong by")
    print("900,000 are not the same kind of claim.  The most likely conclusion")
    print("is that a degree-57 Moore graph would NOT have the involution")
    print("property: it is a genuine feature of m = 2 and m = 6 whose cost")
    print("grows far faster than the available freedom.")
    print()
    print("Consequences if so:")
    print("  * the gauged matching model is searching for something that does")
    print("    not exist, which explains why it stalls at four branches;")
    print("  * the earlier claim that the published t = 20 frontier is")
    print("    'off-path' was conditional on this conjecture, and should be")
    print("    withdrawn to that extent;")
    print("  * the cyclic ansatz is still dead, but on the independent grounds")
    print("    proved earlier (no order-56 automorphism; the reflection bound).")


if __name__ == "__main__":
    main()
