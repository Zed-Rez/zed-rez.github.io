"""
Every classical feasibility test the parameter set passes.

A Moore graph of degree 57 would be a strongly regular graph with parameters
(n, k, lambda, mu) = (3250, 57, 0, 1).  The reason the problem is still open
after sixty-five years is that nothing in the standard toolkit says no: the
spectrum is integral, the Krein conditions hold, the absolute bound holds, the
ratio bound is an integer.  This module runs those tests, and validates each
formula on the two Moore graphs that do exist.
"""

from fractions import Fraction
from math import isqrt

import reduction


def srg_parameters(k):
    """(n, k, lambda, mu) of a Moore graph of degree k and diameter 2."""
    return (k * k + 1, k, 0, 1)


def srg_spectrum(n, k, lam, mu):
    """Eigenvalues and multiplicities of an srg, as exact rationals."""
    disc = (lam - mu) ** 2 + 4 * (k - mu)
    s = isqrt(disc)
    assert s * s == disc, "non-integral discriminant"
    r = Fraction(lam - mu + s, 2)
    t = Fraction(lam - mu - s, 2)
    assert r.denominator == 1 and t.denominator == 1
    r, t = int(r), int(t)
    # multiplicities
    num = 2 * k + (n - 1) * (lam - mu)
    f = Fraction(n - 1, 2) - Fraction(num, 2 * s)
    g = Fraction(n - 1, 2) + Fraction(num, 2 * s)
    assert f.denominator == 1 and g.denominator == 1, "non-integral multiplicities"
    return (k, 1), (r, int(f)), (t, int(g))


def krein(k, r, t):
    """The two Krein conditions for an srg with eigenvalues k > r > t."""
    c1 = (r + 1) * (k + r + 2 * r * t) <= (k + r) * (t + 1) ** 2
    c2 = (t + 1) * (k + t + 2 * r * t) <= (k + t) * (r + 1) ** 2
    return c1, c2


def absolute_bound(n, f, g):
    return n <= f * (f + 3) // 2 and n <= g * (g + 3) // 2


def ratio_bound(n, k, t):
    """Hoffman's bound on the independence number."""
    return Fraction(n * (-t), k - t)


def delsarte_clique_bound(k, t):
    return Fraction(k, -t) + 1


def count_5_cycles(g):
    """Brute-force count of 5-cycles, for validating the closed form."""
    verts = sorted(g, key=repr)
    idx = {v: i for i, v in enumerate(verts)}
    total = 0
    for a in verts:
        for b in g[a]:
            if idx[b] <= idx[a]:
                continue
            for c in g[b]:
                if c == a or idx[c] <= idx[a]:
                    continue
                for d in g[c]:
                    if d in (a, b) or idx[d] <= idx[a]:
                        continue
                    for e in g[d]:
                        if e in (a, b, c) or idx[e] <= idx[a]:
                            continue
                        if a in g[e]:
                            total += 1
    return total // 2          # each cycle traversed in two directions


def five_cycle_formula(n, k):
    """n * C(k,2) * (k-1) / 5 -- derived from girth 5 plus diameter 2."""
    return n * (k * (k - 1) // 2) * (k - 1) // 5


def report(k, graph=None):
    n, lam, mu = k * k + 1, 0, 1
    (ev0, m0), (r, f), (t, gm) = srg_spectrum(n, k, lam, mu)
    print("degree %d: strongly regular (%d, %d, %d, %d)" % (k, n, k, lam, mu))
    print("  spectrum        %d^%d, %d^%d, %d^%d" % (ev0, m0, r, f, t, gm))
    print("  integrality     PASS (eigenvalues and multiplicities are integers)")
    c1, c2 = krein(k, r, t)
    print("  Krein           %s, %s" % ("PASS" if c1 else "FAIL",
                                        "PASS" if c2 else "FAIL"))
    print("  absolute bound  %s" % ("PASS" if absolute_bound(n, f, gm) else "FAIL"))
    rb = ratio_bound(n, k, t)
    print("  ratio bound     independence number <= %s%s"
          % (rb, "  (an integer -- a tight coclique is not excluded)"
             if rb.denominator == 1 else ""))
    cb = delsarte_clique_bound(k, t)
    print("  clique bound    clique number <= %.4g  ->  <= %d "
          "(consistent with triangle-free)" % (float(cb), int(cb)))
    print("  edges           %d" % (n * k // 2))
    print("  5-cycles        %d (closed form)" % five_cycle_formula(n, k))
    if graph is not None:
        actual = count_5_cycles(graph)
        print("                  %d (counted in the actual graph) -- formula %s"
              % (actual, "VERIFIED" if actual == five_cycle_formula(n, k)
                 else "WRONG"))
        assert actual == five_cycle_formula(n, k)
    print()


if __name__ == "__main__":
    report(3, reduction.petersen())
    report(7, reduction.hoffman_singleton())
    report(57)
    print("Nothing in the classical toolkit rejects (3250, 57, 0, 1).  That is")
    print("why the question survives: it has to be settled by construction or")
    print("by an argument specific to this parameter set.")
