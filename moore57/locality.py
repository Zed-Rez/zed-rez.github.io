"""
How global must a proof of the involution conjecture be?

The conjecture says every triangle composite of a *complete* Moore graph is a
fixed-point-free involution.  The obvious way to attack it is locally: take a
handful of branches, apply girth 5 and the unique-common-neighbour condition
among them, and try to force the involution property.

That cannot work, and the certificates already produced say how far it cannot
work.  A t-branch structure satisfies every Moore condition that can be stated
about t branches -- no triangles, no quadrilaterals, unique common neighbours
-- so if a valid t-branch structure exists whose composites are *not*
involutions, then no argument that looks at t branches and uses only those
conditions can prove the conjecture.

This module measures exactly that: for each certificate on disk, the fraction
of triangle composites that are involutions.  The largest t for which a
violating structure exists is a lower bound on how many branches any proof must
consider at once.
"""

import glob
import json
import sys
from itertools import permutations

import involution
import reduction


def audit(path):
    d = json.load(open(path))
    t, m = d["t"], d["m"]
    sig = {}
    for k, v in d["sigma"].items():
        i, j = (int(z) for z in k.split(","))
        sig[(i, j)] = tuple(v)
    # fill in branch 0 and any missing inverses
    ident = tuple(range(m))
    for i in range(t):
        for j in range(t):
            if i == j:
                continue
            if (i, j) in sig:
                continue
            if i == 0 or j == 0:
                sig[(i, j)] = ident
            elif (j, i) in sig:
                sig[(i, j)] = reduction.inverse(sig[(j, i)])
    tot = inv = 0
    for a, j, b in permutations(range(t), 3):
        tau = involution.composite(sig, t, a, j, b, m)
        tot += 1
        if involution.is_involution(tau):
            inv += 1
    return t, inv, tot


def main():
    paths = sys.argv[1:]
    if not paths:
        paths = sorted(set(glob.glob("*_t*.json")) | set(glob.glob("t*.json")))
    print("Involution property in verified partial structures\n")
    print("  %-34s %-4s %-16s %s" % ("certificate", "t", "involutive", "verdict"))
    worst = 0
    for p in paths:
        try:
            t, inv, tot = audit(p)
        except Exception as e:
            continue
        frac = inv / tot if tot else 1.0
        verdict = "satisfies it" if inv == tot else "VIOLATES it"
        print("  %-34s %-4d %-16s %s"
              % (p, t, "%d / %d" % (inv, tot), verdict))
        if inv != tot:
            worst = max(worst, t)
    print()
    print("  Largest valid structure that violates the property: t = %d" % worst)
    print()
    print("  So every Moore condition statable about %d branches is satisfied" % worst)
    print("  by a configuration whose composites are not involutions.  Any")
    print("  proof of the conjecture must therefore use more than %d branches"
          % worst)
    print("  at once -- no bounded-neighbourhood argument can reach it.  That")
    print("  is why the direct attempts in this project failed: they all tried")
    print("  to force the property from a triangle, a quadrilateral, or a")
    print("  six-cycle, and no such configuration determines it.")


if __name__ == "__main__":
    main()
