"""
Grow the reflection labelling one branch at a time.

formA_reflection.py hands the whole K_t model to CP-SAT at once and stalls at
13 branches.  The cyclic labelling had exactly the same shape and the same
problem, and incremental growth -- fix what is already placed, solve only for
the new column -- took it from 15 to 19.  This does the same here.

Adding branch r to branches 0..r-1 means choosing the odd labels g_ir.  The
triangle conditions stay free (odd - odd + odd is odd), so only the
quadrilaterals matter, and every one of them that involves r is linear in the
new labels:

    cycle p -> q -> u -> w -> p  contributes  g_pw - g_uw + g_qu - g_pq != 0

Anything Form A compliant that this finds is a genuine partial Moore structure
under the conjecture -- unlike the certificates from the general and
1-factorization searches, which violate Form A and so cannot extend to a Moore
graph if it holds.
"""

import json
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

import formA_reflection as R
import reduction

M = 56


def extend(g, t, seconds=120.0, workers=4, seed=0, m=M, banned=()):
    """Choose odd g_ir for i < t, given the labels among 0..t-1."""
    model = cp_model.CpModel()
    odd = [(o,) for o in range(1, m, 2)]
    x = {}
    for i in range(t):
        if i == 0:
            x[0] = model.NewConstant(1)                 # gauge
        else:
            v = model.NewIntVar(0, m - 1, "x%d" % i)
            model.AddAllowedAssignments([v], odd)
            x[i] = v

    def lab(i, j):
        """label of the pair (i, j), where j may be the new branch t."""
        if i == t:
            return x[j]
        if j == t:
            return x[i]
        return g[(min(i, j), max(i, j))]

    n_q = 0
    for a, b, c in combinations(range(t), 3):
        for (p, q, u, w) in ((a, b, c, t), (a, b, t, c), (a, c, b, t)):
            d = model.NewIntVar(-2 * m, 2 * m, "")
            model.Add(d == lab(p, w) - lab(u, w) + lab(q, u) - lab(p, q))
            for mult in range(-2, 3):
                model.Add(d != mult * m)
            n_q += 1

    for col in banned:
        lits = []
        for i in range(1, t):
            b = model.NewBoolVar("")
            model.Add(x[i] != col[i]).OnlyEnforceIf(b)
            model.Add(x[i] == col[i]).OnlyEnforceIf(b.Not())
            lits.append(b)
        model.AddBoolOr(lits)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.randomize_search = True
    st = solver.Solve(model)
    name = solver.StatusName(st)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {i: solver.Value(x[i]) for i in range(t)}, name, n_q
    return None, name, n_q


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 57
    tries = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    seed0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    print("growing the reflection labelling with backtracking, %.0fs per "
          "branch, fanout %d\n" % (secs, tries), flush=True)
    best = [2]
    deadline = time.time() + float(sys.argv[5]) if len(sys.argv) > 5 else None

    def dfs(g, t, depth):
        """Place branch t; on failure back out and let the caller retry."""
        if t >= target:
            return g, t
        if deadline and time.time() > deadline:
            return None
        banned = []
        for k in range(tries):
            col, name, n_q = extend(g, t, seconds=secs,
                                    seed=seed0 + 31 * t + 7 * k,
                                    banned=banned)
            if col is None:
                if k == 0:
                    print("  %2d -> %2d : %s (%d conditions)"
                          % (t, t + 1, name, n_q), flush=True)
                return None
            banned.append(col)
            g2 = dict(g)
            for i in range(t):
                g2[(i, t)] = col[i]
            if t + 1 > best[0]:
                best[0] = t + 1
                sig = R.to_sigma(t + 1, g2)
                ok, inv, tot, n, girth = R.audit(t + 1, sig)
                print("  t=%-3d verified -- Moore %s, Form A %d/%d, fragment "
                      "%d vertices, girth>=5 %s"
                      % (t + 1, ok, inv, tot, n, girth), flush=True)
                assert ok and inv == tot and girth
                json.dump({"t": t + 1, "m": M,
                           "sigma": {"%d,%d" % kk: list(v)
                                     for kk, v in sig.items()},
                           "labels": {"%d,%d" % kk: v for kk, v in g2.items()}},
                          open("formA_grown_t%d.json" % (t + 1), "w"))
            got = dfs(g2, t + 1, depth + 1)
            if got is not None:
                return got
        return None

    dfs({(0, 1): 1}, 2, 0)
    t = best[0]

    print("\nForm A frontier by incremental reflection growth: t = %d of 57"
          % t, flush=True)


if __name__ == "__main__":
    main()
