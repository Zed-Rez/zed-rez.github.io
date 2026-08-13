"""
The gauged matching model.

Fixing the gauge sigma_0j = identity collapses the involution property into
something far more usable.  With that gauge:

  * triple {0, i, j}:   tau = sigma_j0 . sigma_ij . sigma_0i = sigma_ij,
    so **every sigma_ij (i, j >= 1) is itself a fixed-point-free involution** --
    a perfect matching on the 56 points.  (Verified: 1/1 for Petersen, 15/15
    for Hoffman-Singleton.)

  * quadrilateral {0, i, j, l}: the composite collapses to sigma_jl . sigma_ij,
    and the product of two fixed-point-free involutions is fixed-point-free
    exactly when the two matchings share no edge.  Running over the three
    cyclic orders makes M_ij, M_jl and M_il pairwise edge-disjoint.

    Hence for each fixed branch i, the 55 matchings {M_ij : j != i} are
    pairwise edge-disjoint -- a **1-factorization of K_56** (55 matchings x 28
    edges = 1540 = |E(K_56)|, so it is exact).

  * M_ij = M_ji, so the whole object is a symmetric array of matchings whose
    every row is a 1-factorization.

What remains are the conditions not touching the root: for i, j, l >= 1 the
triangle composite sigma_li . sigma_jl . sigma_ij must be a fixed-point-free
involution (hence itself a matching), and the quadrilaterals among four
non-root branches must be fixed-point-free.

This is a much tighter model than permutations-in-S_56: the variables are
perfect matchings, most constraints are plain disequalities, and the
1-factorization structure is explicit.  Validated here by recovering
Hoffman-Singleton.

NOTE: this model assumes the involution property, which is verified at degrees
3 and 7 and conjectural at 57 (see README).  Solutions it finds are genuine
Moore graphs -- the derangement conditions are all enforced and the result is
rebuilt and checked as a graph -- but infeasibility only rules out Moore graphs
*with* the property.
"""

import json
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

import reduction


def build(t, m, seconds=300.0, workers=4, seed=0, log=False, impose_inv=True):
    """t branches (0..t-1) of block size m, in the gauge sigma_0j = id."""
    model = cp_model.CpModel()

    # --- the matchings M_ij for 1 <= i < j <= t-1 --------------------------
    M = {}
    for i, j in combinations(range(1, t), 2):
        row = [model.NewIntVar(0, m - 1, "M%d_%d_%d" % (i, j, x))
               for x in range(m)]
        model.AddInverse(row, row)                 # involution
        for x in range(m):
            model.Add(row[x] != x)                 # fixed-point-free
        M[(i, j)] = row
        M[(j, i)] = row                            # symmetric

    def sig(a, b):
        """sigma_ab as a list of vars/consts (identity when a or b is 0)."""
        if a == 0 or b == 0:
            return None                            # identity
        return M[(a, b)]

    n_dis = n_el = 0

    # --- edge-disjointness: quadrilaterals through the root -----------------
    for i in range(1, t):
        for j, l in combinations([q for q in range(1, t) if q != i], 2):
            for x in range(m):
                model.Add(M[(i, j)][x] != M[(i, l)][x])
                n_dis += 1

    # --- conditions among non-root branches --------------------------------
    def elem(arr, idx):
        out = model.NewIntVar(0, m - 1, "")
        model.AddElement(idx, arr, out)
        return out

    for i, j, l in combinations(range(1, t), 3):
        # triangle i -> j -> l -> i : tau = sigma_li . sigma_jl . sigma_ij
        for perm in ((i, j, l), (i, l, j)):
            a, b, c = perm
            tau = []
            for x in range(m):
                y = M[(a, b)][x]
                z = elem(M[(b, c)], y)
                w = elem(M[(c, a)], z)
                n_el += 2
                tau.append(w)
            for x in range(m):
                model.Add(tau[x] != x)             # fixed-point-free
            if impose_inv:
                model.AddInverse(tau, tau)         # and an involution

    for quad in combinations(range(1, t), 4):
        a, b, c, d = quad
        for cyc in ((a, b, c, d), (a, b, d, c), (a, c, b, d)):
            p, q, u, w = cyc
            for x in range(m):
                y = M[(p, q)][x]
                z = elem(M[(q, u)], y)
                zz = elem(M[(u, w)], z)
                ww = elem(M[(w, p)], zz)
                n_el += 3
                model.Add(ww != x)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = log
    st = solver.Solve(model)
    name = solver.StatusName(st)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        out = {}
        for i, j in combinations(range(1, t), 2):
            out[(i, j)] = [solver.Value(v) for v in M[(i, j)]]
        return out, name, (n_dis, n_el)
    return None, name, (n_dis, n_el)


def to_sigma(t, m, sol):
    sigma = {}
    ident = tuple(range(m))
    for j in range(1, t):
        sigma[(0, j)] = ident
    for (i, j), v in sol.items():
        sigma[(i, j)] = tuple(v)
    return sigma


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    t = int(sys.argv[2]) if len(sys.argv) > 2 else k
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 300.0
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    m = k - 1

    print("gauged matching model: degree %d (blocks of %d), %d branches"
          % (k, m, t), flush=True)
    print("  unknowns: %d perfect matchings on %d points"
          % (len(list(combinations(range(1, t), 2))), m), flush=True)
    t0 = time.time()
    sol, name, (nd, ne) = build(t, m, seconds=secs, workers=workers, seed=seed)
    el = time.time() - t0
    print("  %s in %.0fs  (%d disequalities, %d element constraints)"
          % (name, el, nd, ne), flush=True)
    if sol is None:
        return

    sigma = to_sigma(t, m, sol)
    ok_sig = reduction.sigma_conditions_hold(t, sigma, m=m)
    print("  derangement conditions on the sigma table: %s" % ok_sig, flush=True)
    json.dump({"k": k, "t": t, "m": m,
               "M": {"%d,%d" % kk: v for kk, v in sol.items()}},
              open("gauged_k%d_t%d.json" % (k, t), "w"))
    if t == k:
        g = reduction.build_graph(k, sigma, m=m)
        ok, msg = reduction.is_moore(g, k)
        print("  rebuilt graph: %s" % msg, flush=True)
        if ok:
            print("\n  *** A MOORE GRAPH OF DEGREE %d ***" % k, flush=True)
    else:
        g = reduction.build_graph(t, sigma, m=m)
        print("  partial structure: %d vertices, girth >= 5: %s"
              % (len(g), reduction.girth_at_least_5(g)), flush=True)


if __name__ == "__main__":
    main()
