"""
CRT encoding of the reduced reflection model.

Z_28 = Z_4 x Z_7, so a 4-cycle sum vanishes mod 28 exactly when it vanishes
mod 4 *and* mod 7.  Splitting each label f_ij into (a_ij, b_ij) over Z_4 x Z_7
turns every condition from "this sum avoids 0, 28, -28" over a wide integer
range into a plain disjunction

        NOT( sum_4 = 0  AND  sum_7 = 0 )

which is the shape CP-SAT reasons about well.  It also exposes what the two
components can do separately: refl_law.py proves the ceiling is 5 for modulus 4
and 9 for modulus 7, so neither component alone reaches past 9 -- every
structure beyond that has to mix, satisfying some 4-cycles mod 4 and others
mod 7.  That is exactly the freedom the single-modulus constructions lacked and
why they capped early.
"""

import json
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

import formA_reflection as R


def solve(t, seconds=300.0, workers=4, seed=0, log=False):
    model = cp_model.CpModel()
    a, b = {}, {}
    for i, j in combinations(range(t), 2):
        if i == 0:
            av = model.NewConstant(0)
            bv = model.NewConstant(0)
        else:
            av = model.NewIntVar(0, 3, "a%d_%d" % (i, j))
            bv = model.NewIntVar(0, 6, "b%d_%d" % (i, j))
        a[(i, j)] = a[(j, i)] = av
        b[(i, j)] = b[(j, i)] = bv

    n_c = 0
    for w, x, y, z in combinations(range(t), 4):
        for (p, q, u, v) in ((w, x, y, z), (w, x, z, y), (w, y, x, z)):
            # shift by a multiple of both 4 and 7 to keep sums non-negative
            s4 = model.NewIntVar(0, 24, "")
            model.Add(s4 == a[(p, v)] - a[(u, v)] + a[(q, u)] - a[(p, q)] + 12)
            r4 = model.NewIntVar(0, 3, "")
            model.AddModuloEquality(r4, s4, 4)
            z4 = model.NewBoolVar("")
            model.Add(r4 == 0).OnlyEnforceIf(z4)
            model.Add(r4 != 0).OnlyEnforceIf(z4.Not())

            s7 = model.NewIntVar(0, 42, "")
            model.Add(s7 == b[(p, v)] - b[(u, v)] + b[(q, u)] - b[(p, q)] + 21)
            r7 = model.NewIntVar(0, 6, "")
            model.AddModuloEquality(r7, s7, 7)
            z7 = model.NewBoolVar("")
            model.Add(r7 == 0).OnlyEnforceIf(z7)
            model.Add(r7 != 0).OnlyEnforceIf(z7.Not())

            model.AddBoolOr([z4.Not(), z7.Not()])
            n_c += 1

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = log
    st = solver.Solve(model)
    name = solver.StatusName(st)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        g = {}
        for i, j in combinations(range(t), 2):
            av, bv = solver.Value(a[(i, j)]), solver.Value(b[(i, j)])
            # CRT lift: f = the unique value mod 28 with f=av mod 4, bv mod 7
            f = next(x for x in range(28) if x % 4 == av % 4 and x % 7 == bv % 7)
            g[(i, j)] = (2 * f + 1) % 56
        return g, name, n_c
    return None, name, n_c


def main():
    ts = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [14, 15, 16]
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0

    print("CRT-encoded reflection model (Z_4 x Z_7)\n", flush=True)
    for t in ts:
        t0 = time.time()
        g, name, n_c = solve(t, seconds=secs, seed=t)
        el = time.time() - t0
        if g is None:
            print("  t=%-3d %s (%.0fs, %d conditions)" % (t, name, el, n_c),
                  flush=True)
            break
        sig = R.to_sigma(t, g)
        ok, inv, tot, n, girth = R.audit(t, sig)
        print("  t=%-3d FOUND -- Moore %s, Form A %d/%d, fragment %d vertices, "
              "girth>=5 %s (%.0fs)" % (t, ok, inv, tot, n, girth, el),
              flush=True)
        assert ok and inv == tot and girth
        json.dump({"t": t, "m": 56,
                   "sigma": {"%d,%d" % k: list(v) for k, v in sig.items()},
                   "labels": {"%d,%d" % k: v for k, v in g.items()}},
                  open("formA_crt_t%d.json" % t, "w"))


if __name__ == "__main__":
    main()
