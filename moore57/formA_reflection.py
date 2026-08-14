"""
Form A from reflections: a second, larger construction.

The abelian construction (formA_abelian.py) gets Form A because commuting
involutions satisfy sigma_ca sigma_bc sigma_ab = sigma_ab sigma_bc sigma_ca
trivially.  It caps at 5 branches.

Dihedral groups give the property a different way.  A product of an *odd*
number of reflections is again a reflection, and a reflection is an involution.
So if every sigma_ij is a reflection of Z_56,

        sigma_ij(x) = g_ij - x,        g_ij = g_ji,

then every triangle composite is a reflection and therefore an involution --
Form A holds automatically, with no commuting required.  This is the ansatz
reflection.py tested at full size (infeasible at degree 7, builds Petersen);
what was never run is the *partial* problem at degree 57, which is what matters
now.

The conditions reduce to arithmetic:

    triangle  x |-> c - x,  c = g_ab - g_bj + g_aj,  fixed-point-free iff c is
              odd -- satisfied outright by taking every g_ij odd;
    quadrilateral  x |-> x + d,  d = g_al - g_bl + g_jb - g_aj,
              fixed-point-free iff d != 0 mod 56.

So only the quadrilateral conditions remain, over 28 odd residues per pair.
"""

import json
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

import involution
import reduction

M = 56


def solve_partial(t, m=M, seconds=120.0, workers=4, seed=0):
    """Find an odd symmetric labelling of K_t over Z_m with no vanishing
    quadrilateral sum."""
    model = cp_model.CpModel()
    odd = [(o,) for o in range(1, m, 2)]
    g = {}
    for i, j in combinations(range(t), 2):
        if i == 0:
            v = model.NewConstant(1)                 # gauge
        else:
            v = model.NewIntVar(0, m - 1, "g%d_%d" % (i, j))
            model.AddAllowedAssignments([v], odd)
        g[(i, j)] = v
        g[(j, i)] = v

    n_q = 0
    for quad in combinations(range(t), 4):
        a, j, b, l = quad
        for (p, q, u, w) in ((a, j, b, l), (a, j, l, b), (a, b, j, l)):
            d = model.NewIntVar(-2 * m, 2 * m, "")
            model.Add(d == g[(p, w)] - g[(u, w)] + g[(q, u)] - g[(p, q)])
            for mult in range(-2, 3):
                model.Add(d != mult * m)
            n_q += 1

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    st = solver.Solve(model)
    name = solver.StatusName(st)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {(i, j): solver.Value(g[(i, j)])
                for i, j in combinations(range(t), 2)}, name, n_q
    return None, name, n_q


def to_sigma(t, g, m=M):
    sigma = {}
    for i, j in combinations(range(t), 2):
        val = g[(i, j)]
        p = tuple((val - x) % m for x in range(m))
        sigma[(i, j)] = p
        sigma[(j, i)] = p                            # reflections are involutions
    return sigma


def audit(t, sigma, m=M):
    from itertools import permutations
    ok_sig = reduction.sigma_conditions_hold(t, sigma, m=m)
    tot = inv = 0
    for x, y, z in permutations(range(t), 3):
        tau = involution.composite(sigma, t, x, y, z, m)
        tot += 1
        if involution.is_involution(tau) and all(tau[k] != k for k in range(m)):
            inv += 1
    g = reduction.build_graph(t, sigma, m=m)
    return ok_sig, inv, tot, len(g), reduction.girth_at_least_5(g)


def main():
    tmax = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0

    print("Form A from reflections at degree 57 (block size %d)\n" % M,
          flush=True)
    best = 0
    for t in range(3, tmax + 1):
        t0 = time.time()
        g, name, n_q = solve_partial(t, seconds=secs)
        el = time.time() - t0
        if g is None:
            print("  t=%-3d %s (%.0fs, %d quadrilateral conditions)"
                  % (t, name, el, n_q), flush=True)
            break
        sigma = to_sigma(t, g)
        ok_sig, inv, tot, n, girth = audit(t, sigma)
        print("  t=%-3d FOUND -- Moore conditions %s, Form A %d/%d, "
              "fragment %d vertices, girth>=5 %s (%.0fs)"
              % (t, ok_sig, inv, tot, n, girth, el), flush=True)
        assert ok_sig and inv == tot and girth
        best = t
        json.dump({"t": t, "m": M,
                   "sigma": {"%d,%d" % k: list(v) for k, v in sigma.items()}},
                  open("formA_reflection_t%d.json" % t, "w"))

    print("\n  Form A frontier from reflections: t = %d of 57" % best,
          flush=True)
    if best > 5:
        print("  That beats the abelian construction's 5 and the annealer's 4.")


if __name__ == "__main__":
    main()
