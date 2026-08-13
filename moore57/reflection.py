"""
The reflection ansatz.

The published searches take every bijection to be a translation of Z_{k-1},

        sigma_ij(x) = x + a_ij .

Then the triangle composite is a translation too, and a translation is an
involution only if it is by exactly (k-1)/2 -- which forces every triangle sum
to that value and then breaks the quadrilateral conditions.  That is the whole
reason the cyclic ansatz dies, and it is why it cannot produce
Hoffman-Singleton, whose triangle composites are all involutions.

Take reflections instead:

        sigma_ij(x) = g_ij - x ,        g_ij = g_ji in Z_{k-1}.

Composing two reflections gives a translation and composing three gives a
reflection, so

    triangle  a->j->b->a :   x  |->  c - x,   c = g_ab - g_bj + g_aj
    quadrilateral a->j->b->l->a : x |-> x + d,
                             d = g_al - g_bl + g_jb - g_aj

A reflection x |-> c - x is fixed-point-free exactly when c is odd (2x = c has
no solution mod an even modulus), and it is *always* an involution.  So:

  * every triangle composite is automatically an involution -- the property
    both known Moore graphs have and the cyclic ansatz cannot have;
  * the triangle conditions reduce to a parity condition, which is satisfied
    outright by taking every g_ij odd;
  * only the quadrilateral conditions remain, as d != 0 mod (k-1).

That is a search over 28 values per pair instead of 56! per pair, with the
triangle constraints free.  This module tests it where the answer is known
(k = 7 must yield Hoffman-Singleton) and then runs it at k = 57.
"""

import json
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

import reduction


def solve(k, seconds=300.0, workers=4, seed=0, log=False, gauge=True):
    """Find a symmetric odd labelling g of K_k over Z_{k-1} with no vanishing
    quadrilateral sum."""
    m = k - 1
    assert m % 2 == 0, "k - 1 must be even for the parity argument"
    model = cp_model.CpModel()

    odd = list(range(1, m, 2))
    g = {}
    for i, j in combinations(range(k), 2):
        if gauge and i == 0:
            v = model.NewConstant(1)          # gauge: g_0j = 1
        else:
            v = model.NewIntVar(0, m - 1, "g%d_%d" % (i, j))
            model.AddAllowedAssignments([v], [(o,) for o in odd])
        g[(i, j)] = v
        g[(j, i)] = v                         # symmetric

    n_q = 0
    for quad in combinations(range(k), 4):
        a, j, b, l = quad
        for cyc in ((a, j, b, l), (a, j, l, b), (a, b, j, l)):
            p, q, u, w = cyc
            # d = g_pw - g_uw + g_qu - g_pq   (cycle p->q->u->w->p)
            d = model.NewIntVar(-2 * m, 2 * m, "")
            model.Add(d == g[(p, w)] - g[(u, w)] + g[(q, u)] - g[(p, q)])
            for mult in range(-2, 3):
                model.Add(d != mult * m)
            n_q += 1

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = log
    st = solver.Solve(model)
    name = solver.StatusName(st)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        out = {(i, j): solver.Value(g[(i, j)])
               for i, j in combinations(range(k), 2)}
        return out, name, n_q
    return None, name, n_q


def to_sigma(k, g):
    m = k - 1
    sigma = {}
    for i, j in combinations(range(k), 2):
        val = g[(i, j)]
        sigma[(i, j)] = tuple((val - x) % m for x in range(m))
    return sigma


def check(k, g):
    """Verify by building the graph and testing it directly."""
    sigma = to_sigma(k, g)
    ok_sig = reduction.sigma_conditions_hold(k, sigma)
    graph = reduction.build_graph(k, sigma)
    ok, msg = reduction.is_moore(graph, k)
    return ok_sig, ok, msg, graph


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "7"
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    k = int(which)
    print("reflection ansatz at degree %d (blocks of %d, %d unknowns, "
          "%d values each)"
          % (k, k - 1, len(list(combinations(range(k), 2))), (k - 1) // 2),
          flush=True)
    t0 = time.time()
    g, name, n_q = solve(k, seconds=secs, workers=workers, seed=seed)
    el = time.time() - t0
    print("  %s in %.0fs  (%d quadrilateral constraints; triangles are free)"
          % (name, el, n_q), flush=True)
    if g is None:
        return
    ok_sig, ok, msg, graph = check(k, g)
    print("  derangement conditions hold: %s" % ok_sig, flush=True)
    print("  rebuilt graph: %s" % msg, flush=True)
    json.dump({"k": k, "g": {"%d,%d" % kk: v for kk, v in g.items()}},
              open("reflection_k%d.json" % k, "w"))
    if ok:
        print("\n  *** A MOORE GRAPH OF DEGREE %d ***" % k, flush=True)


if __name__ == "__main__":
    main()
