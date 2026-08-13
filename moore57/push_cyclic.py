"""
Push the cyclic frontier for k = 57 as far as it will go.

Two strategies:
  * monolithic  -- hand the whole t-subgraph model to CP-SAT at once;
  * incremental -- grow a valid labelling one block at a time, solving only
                   the new column with CP-SAT, backtracking when a column has
                   no completion.

The literature frontier under this ansatz is t = 20 of the 57 needed.
"""

import random
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

M = 56


def verify(t, a):
    for i, j, l in combinations(range(t), 3):
        if (a[i][j] + a[j][l] + a[l][i]) % M == 0:
            return False
    for i, j, l, r in combinations(range(t), 4):
        for p, q, u, w in ((i, j, l, r), (i, j, r, l), (i, l, j, r)):
            if (a[p][q] + a[q][u] + a[u][w] + a[w][p]) % M == 0:
                return False
    return True


def extend_column(a, t, seconds=30.0, seed=0, workers=4):
    """Given a valid labelling on blocks 0..t-1, try to add block t.
    a is a (T x T) list of lists; entries for blocks < t are set."""
    model = cp_model.CpModel()
    x = {0: model.NewConstant(0)}                      # gauge: a[0][t] = 0
    for i in range(1, t):
        x[i] = model.NewIntVar(1, M - 1, "x%d" % i)    # a[i][t] != 0 forced
                                                       # by triangle {0,i,t}

    def forbid(exprs, lo, hi):
        s = model.NewIntVar(lo, hi, "")
        model.Add(s == sum(exprs))
        k = -(-lo // M)
        while k * M <= hi:
            model.Add(s != k * M)
            k += 1

    # triangles {h, i, t}:  a[h][i] + a[i][t] - a[h][t] != 0
    for h, i in combinations(range(t), 2):
        forbid([a[h][i], x[i], -x[h]], -2 * M, 2 * M)
    # quadrilaterals {g, h, i, t}: three cyclic orders, two edges touch t
    for g, h, i in combinations(range(t), 3):
        forbid([a[g][h], a[h][i], x[i], -x[g]], -3 * M, 3 * M)
        forbid([a[h][g], a[g][i], x[i], -x[h]], -3 * M, 3 * M)
        forbid([a[g][i], a[i][h], x[h], -x[g]], -3 * M, 3 * M)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.randomize_search = True
    st = solver.Solve(model)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return [solver.Value(x[i]) for i in range(t)], solver.StatusName(st)
    return None, solver.StatusName(st)


def incremental(target=57, seconds=30.0, restarts=200, log=sys.stdout):
    T = target
    best = 0
    best_a = None
    for attempt in range(restarts):
        a = [[0] * T for _ in range(T)]
        t = 2                       # blocks 0,1 with a[0][1] = 0 (gauge)
        stalled = False
        while t < T:
            col, st = extend_column(a, t, seconds=seconds, seed=attempt * 1000 + t)
            if col is None:
                print("  attempt %2d: block %2d has no extension (%s)"
                      % (attempt, t, st), file=log, flush=True)
                stalled = True
                break
            for i in range(t):
                a[i][t] = col[i] % M
                a[t][i] = (-col[i]) % M
            t += 1
        if t > best:
            best = t
            best_a = [row[:] for row in a]
            print("  attempt %2d: reached t = %d  (verified: %s)"
                  % (attempt, t, verify(t, a)), file=log, flush=True)
        if not stalled:
            print("  COMPLETE at t = %d" % t, file=log, flush=True)
            return t, a
    return best, best_a


def monolithic(t, seconds, workers=4):
    import cyclic_search
    t0 = time.time()
    name, sol, counts = cyclic_search.cpsat_t_subgraph(M, t, seconds=seconds,
                                                       workers=workers)
    return name, sol, time.time() - t0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "incremental"
    if mode == "incremental":
        secs = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
        tries = int(sys.argv[3]) if len(sys.argv) > 3 else 60
        print("incremental cyclic search, %.0fs per column, %d restarts"
              % (secs, tries), flush=True)
        best, a = incremental(seconds=secs, restarts=tries)
        print("BEST t =", best, flush=True)
        if a is not None:
            print("verified:", verify(best, a), flush=True)
            print("labelling:", [a[i][:best] for i in range(best)], flush=True)
    else:
        t = int(sys.argv[2])
        secs = float(sys.argv[3]) if len(sys.argv) > 3 else 600.0
        name, sol, el = monolithic(t, secs)
        print("monolithic t=%d: %s in %.0fs" % (t, name, el), flush=True)
