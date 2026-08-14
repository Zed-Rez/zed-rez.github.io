"""
Annealing + CP-SAT: local search to get close, exact search to close the gap.

anneal.py drives the extension cost down quickly but plateaus a handful of
violations short (typically 8 of ~154,000 constraints).  CP-SAT alone returns
UNKNOWN from a cold start.  Together they work: anneal to a near-solution, then
hand that state to CP-SAT as a hint so it only has to repair the residue.

Also supports large-neighbourhood repair: freeze the rows that are not in
conflict and let the solver re-derive the rest.
"""

import json
import sys
import time

from ortools.sat.python import cp_model

import anneal
import general_extend
from anneal import Extension
from general_extend import Structure


def repair(st, val, ext, seconds=600.0, workers=4, free_rows=None, seed=0):
    """CP-SAT on the extension, hinted (or partly fixed) by an annealed state."""
    t, m = st.t, st.m
    model = cp_model.CpModel()
    p = {}
    for x in range(m):
        p[(0, x)] = model.NewConstant(x)
    rows = {}
    for i in range(1, t):
        row = [model.NewIntVar(0, m - 1, "p%d_%d" % (i, x)) for x in range(m)]
        model.AddAllDifferent(row)
        rows[i] = row
        for x in range(m):
            p[(i, x)] = row[x]

    for (i, a, j, b) in general_extend.build_disequalities(st):
        if i == 0 and j == 0:
            continue
        model.Add(p[(i, a)] != p[(j, b)])

    for i in range(1, t):
        for x in range(m):
            v = val[ext.flat[(i, x)]]
            if free_rows is not None and i in free_rows:
                model.AddHint(rows[i][x], v)
            elif free_rows is not None:
                model.Add(rows[i][x] == v)        # frozen
            else:
                model.AddHint(rows[i][x], v)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    code = solver.Solve(model)
    name = solver.StatusName(code)
    if code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return name, [[solver.Value(p[(i, x)]) for x in range(m)]
                      for i in range(t)]
    return name, None


def grow(st, target, anneal_secs=240.0, repair_secs=300.0, restarts=3,
         workers=4):
    while st.t < target:
        ext = Extension(st)
        print("\nbranch %d -> %d : %d cells, %d binary constraints"
              % (st.t, st.t + 1, ext.ncell, ext.n_binary), flush=True)
        done = False
        for r in range(restarts):
            best, val, it = ext.anneal(seconds=anneal_secs, seed=7 * st.t + r)
            print("  anneal run %d: cost %d" % (r, best), flush=True)
            if best == 0:
                cols = ext.to_columns(val)
                cols[0] = list(range(ext.m))
                st.add_block([cols[i] for i in range(st.t)])
                done = True
                break
            # hand the near-solution to CP-SAT
            t0 = time.time()
            name, full = repair(st, val, ext, seconds=repair_secs,
                                workers=workers, seed=r)
            print("    repair: %-11s in %.0fs" % (name, time.time() - t0),
                  flush=True)
            if full is not None:
                st.add_block(full)
                done = True
                break
            # large-neighbourhood: free only the rows carrying violations
            bad = ext.violated_cells(val)
            free = sorted({c // ext.m + 1 for c in bad})
            if 0 < len(free) < st.t - 1:
                t0 = time.time()
                name, full = repair(st, val, ext, seconds=repair_secs,
                                    workers=workers, free_rows=set(free),
                                    seed=r)
                print("    LNS (%d rows free): %-11s in %.0fs"
                      % (len(free), name, time.time() - t0), flush=True)
                if full is not None:
                    st.add_block(full)
                    done = True
                    break
        if not done:
            print("\nfrontier: %d branches" % st.t, flush=True)
            return st
        ok, msg = st.verify()
        print("  EXTENDED to %d branches -- verified: %s" % (st.t, ok),
              flush=True)
        assert ok, msg
        json.dump({"t": st.t, "m": st.m,
                   "sigma": {"%d,%d" % k: v for k, v in st.sigma.items()}},
                  open("hybrid_t%d.json" % st.t, "w"))
    return st


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "anneal_t14.json"
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    asec = float(sys.argv[3]) if len(sys.argv) > 3 else 240.0
    rsec = float(sys.argv[4]) if len(sys.argv) > 4 else 300.0

    st = anneal.load(src)
    ok, msg = st.verify()
    print("seed: %s" % msg, flush=True)
    assert ok
    st = grow(st, target, anneal_secs=asec, repair_secs=rsec)
    print("\nfinal: %d of 57 branches" % st.t, flush=True)


if __name__ == "__main__":
    main()
