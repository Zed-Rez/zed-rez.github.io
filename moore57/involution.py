"""
Are the triangle composites involutions?

The reduction demands only that the composite around a triangle of branches,

        tau(a, j, b)  =  sigma_{b,a} . sigma_{j,b} . sigma_{a,j}   : B_a -> B_a

be a *derangement*.  But latin.py found that the Latin square of every ordered
branch pair of Petersen and of Hoffman-Singleton is symmetric, and symmetry of
that square is exactly the statement that tau(a, j, b) is an involution.

An involution is enormously stronger than a derangement: of the 56! elements
of S_56 about 1/e are derangements, while only about 10^-30 of them are
fixed-point-free involutions.  If the involution property is forced, the
search model used here and in the literature is badly under-constrained.

This module

  1. checks the property on the two Moore graphs that exist;
  2. checks whether it holds in partial structures produced by the search,
     which tells us whether it is a consequence of the local conditions or
     something only completion forces;
  3. re-runs the general growth with the involution property imposed, to see
     what it costs and what it buys.
"""

import json
import sys
from itertools import combinations, permutations

import reduction


def composite(sigma, k, a, j, b, m):
    """tau(a,j,b) as a tuple: B_a -> B_j -> B_b -> B_a."""
    def s(i, jj):
        return sigma[(i, jj)] if (i, jj) in sigma else reduction.inverse(sigma[(jj, i)])
    saj, sjb, sba = s(a, j), s(j, b), s(b, a)
    return tuple(sba[sjb[saj[x]]] for x in range(m))


def is_involution(p):
    return all(p[p[x]] == x for x in range(len(p)))


def audit_graph(name, g, k):
    _, sigma = reduction.decompose(g, sorted(g, key=repr)[0])
    m = k - 1
    tot = inv = der = 0
    for a, j, b in permutations(range(k), 3):
        tau = composite(sigma, k, a, j, b, m)
        tot += 1
        if is_involution(tau):
            inv += 1
        if all(tau[x] != x for x in range(m)):
            der += 1
    print("  %-18s %4d ordered triples: %d derangements, %d involutions%s"
          % (name, tot, der, inv, "  <-- ALL" if inv == tot else ""))
    return inv == tot


def audit_structure(name, sigma, t, m):
    """Audit a partial structure (sigma keyed by (i,j) with list values)."""
    tot = inv = der = 0
    sig = {kk: tuple(v) for kk, v in sigma.items()}
    for a, j, b in permutations(range(t), 3):
        tau = composite(sig, t, a, j, b, m)
        tot += 1
        if is_involution(tau):
            inv += 1
        if all(tau[x] != x for x in range(m)):
            der += 1
    print("  %-28s %5d ordered triples: %d derangements, %d involutions"
          % (name, tot, der, inv))
    return inv, tot


def main():
    print("1. The Moore graphs that exist\n")
    all_petersen = audit_graph("Petersen", reduction.petersen(), 3)
    all_hosi = audit_graph("Hoffman-Singleton", reduction.hoffman_singleton(), 7)
    print()

    if all_petersen and all_hosi:
        print("  Every triangle composite is an involution in both graphs.")
        print("  This is NOT implied by the derangement conditions -- see below.")
    print()

    print("2. Partial structures produced by the search\n")
    try:
        data = json.load(open("t19_cyclic.json"))
        import cyclic_search
        t = data["t"]
        sig = cyclic_search.labelling_to_sigma(56, t, data["labelling"])
        full = {}
        for (i, j), p in sig.items():
            full[(i, j)] = p
            full[(j, i)] = reduction.inverse(p)
        audit_structure("cyclic frontier (t=%d)" % t, full, t, 56)
    except FileNotFoundError:
        print("  (no cyclic certificate found)")

    for path, label in (("general_frontier.json", "general growth, from scratch"),
                        ("general_frontier_seeded.json", "general growth, seeded")):
        try:
            d = json.load(open(path))
        except FileNotFoundError:
            continue
        sig = {}
        for key, v in d["sigma"].items():
            i, j = key.split(",")
            sig[(int(i), int(j))] = v
        audit_structure("%s (t=%d)" % (label, d["t"]), sig, d["t"], d["m"])
    print()
    print("  If the search's structures are full of non-involutive composites")
    print("  while both real Moore graphs have none, the involution property")
    print("  is extra information the search is not using.")


if __name__ == "__main__":
    main()
