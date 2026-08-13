"""
A decisive, cheap test for whether a structure can be extended at all.

Adding branch t to a valid t-branch structure means choosing the cells
p_i[x] = sigma_{i,t}(x) for i = 1..t-1, x = 0..55, subject to

  * each row i is a permutation of the 56 values, and
  * a large set of binary disequalities p_i[a] != p_g[b] coming from the
    triangles and quadrilaterals through the new branch (general_extend.py).

Read that as a colouring problem on the (t-1) x 56 grid of cells, where the
"colour" of a cell is its value.  Because every row is a permutation, each
value occurs exactly once per row, so **every colour class is a transversal**:
one cell from each row.  And the disequalities say a colour class must be an
*independent set* of the conflict graph.

So an extension exists only if the 56(t-1) cells partition into 56 independent
transversals.  A far cheaper necessary condition is that **at least one**
independent transversal exists -- a CSP with only t-1 variables of domain 56
rather than 56(t-1).

If no independent transversal exists, the structure provably admits no
extension, whatever the solver does with the full model.  That converts an
UNKNOWN into a theorem about that structure.
"""

import json
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

import cyclic_search
import general_extend
from general_extend import Structure


def conflict_pairs(st):
    """Set of conflicting cell pairs ((i,a),(g,b)) for the extension of st."""
    con = set()
    for (i, a, j, b) in general_extend.build_disequalities(st):
        if i == j:
            continue
        key = ((i, a), (j, b)) if (i, a) <= (j, b) else ((j, b), (i, a))
        con.add(key)
    return con


def independent_transversal(st, seconds=300.0, workers=4, count=False):
    """Is there one cell per row, pairwise non-conflicting?"""
    t = st.t
    m = st.m
    con = conflict_pairs(st)

    # bucket conflicts by row pair for a compact model
    by_rows = {}
    for (i, a), (g, b) in con:
        if i == 0 or g == 0:
            continue                       # row 0 is the fixed identity
        by_rows.setdefault((i, g) if i < g else (g, i), set()).add(
            (a, b) if i < g else (b, a))

    model = cp_model.CpModel()
    pick = {i: model.NewIntVar(0, m - 1, "r%d" % i) for i in range(1, t)}
    n_forbidden = 0
    for (i, g), pairs in by_rows.items():
        allowed = [(a, b) for a in range(m) for b in range(m)
                   if (a, b) not in pairs]
        model.AddAllowedAssignments([pick[i], pick[g]], allowed)
        n_forbidden += len(pairs)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    st_code = solver.Solve(model)
    name = solver.StatusName(st_code)
    sol = None
    if st_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sol = {i: solver.Value(pick[i]) for i in range(1, t)}
    return name, sol, len(con), n_forbidden


def disjoint_transversals(st, k, seconds=300.0, workers=4):
    """Are there k pairwise-disjoint independent transversals?

    The full extension is exactly the case k = 56 (every cell coloured).  Any
    k for which this is INFEASIBLE proves the structure cannot be extended.
    """
    t, m = st.t, st.m
    con = conflict_pairs(st)
    by_rows = {}
    for (i, a), (g, b) in con:
        if i == 0 or g == 0:
            continue
        key = (i, g) if i < g else (g, i)
        by_rows.setdefault(key, set()).add((a, b) if i < g else (b, a))

    model = cp_model.CpModel()
    a = {(i, c): model.NewIntVar(0, m - 1, "a%d_%d" % (i, c))
         for i in range(1, t) for c in range(k)}
    for i in range(1, t):
        model.AddAllDifferent([a[(i, c)] for c in range(k)])
    # symmetry breaking: the classes are interchangeable, so order row 1
    for c in range(k - 1):
        model.Add(a[(1, c)] < a[(1, c + 1)])

    for (i, g), pairs in by_rows.items():
        allowed = [(p, q) for p in range(m) for q in range(m)
                   if (p, q) not in pairs]
        for c in range(k):
            model.AddAllowedAssignments([a[(i, c)], a[(g, c)]], allowed)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    code = solver.Solve(model)
    return solver.StatusName(code)


def load_cyclic_t19():
    d = json.load(open("t19_cyclic.json"))
    return Structure.from_cyclic(d["labelling"])


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "t19"
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0

    if which == "t19":
        st = load_cyclic_t19()
        label = "the verified 19-branch cyclic structure"
    else:
        d = json.load(open(which))
        st = Structure(m=d["m"])
        st.t = d["t"]
        for key, v in d["sigma"].items():
            i, j = (int(q) for q in key.split(","))
            st.sigma[(i, j)] = v
        label = which

    ok, msg = st.verify()
    print("%s: %s" % (label, msg), flush=True)
    assert ok

    print("\nextension to branch %d:" % st.t, flush=True)
    t0 = time.time()
    name, sol, n_con, n_forb = independent_transversal(st, seconds=secs)
    el = time.time() - t0
    print("  conflict graph: %d conflicting cell pairs over %d cells"
          % (n_con, (st.t - 1) * st.m), flush=True)
    print("  independent transversal: %-11s in %.0fs" % (name, el), flush=True)

    if name == "INFEASIBLE":
        print("\n  PROVEN: this structure admits NO extension.", flush=True)
        print("  A colour class of any valid extension would have to be an", flush=True)
        print("  independent transversal, and none exists.  So the %d-branch"
              % st.t, flush=True)
        print("  structure is a dead end -- not a solver timeout, a theorem.",
              flush=True)
    elif sol is not None and len(sys.argv) > 3 and sys.argv[3] == "sweep":
        print("\n  escalating: k pairwise-disjoint independent transversals")
        print("  (k = 56 is the full extension; any INFEASIBLE k is a proof)",
              flush=True)
        for k in (2, 4, 8, 16, 32, 56):
            t0 = time.time()
            name_k = disjoint_transversals(st, k, seconds=secs)
            print("    k=%-3d %-12s in %5.0fs" % (k, name_k, time.time() - t0),
                  flush=True)
            if name_k == "INFEASIBLE":
                print("\n  PROVEN: no %d disjoint independent transversals "
                      "exist, so the" % k, flush=True)
                print("  %d-branch structure admits NO extension, cyclic or "
                      "otherwise." % st.t, flush=True)
                return
        print("\n  No infeasibility found at these k.", flush=True)
    elif sol is not None:
        # verify the witness by hand
        con = conflict_pairs(st)
        bad = 0
        for i, g in combinations(range(1, st.t), 2):
            a, b = sol[i], sol[g]
            key = ((i, a), (g, b)) if (i, a) <= (g, b) else ((g, b), (i, a))
            if key in con:
                bad += 1
        print("  witness verified: %d conflicting pairs among the chosen cells"
              % bad, flush=True)
        assert bad == 0
        print("\n  A transversal exists, so this cheap test does not rule the",
              flush=True)
        print("  extension out.  It remains necessary-but-not-sufficient: all",
              flush=True)
        print("  56 colour classes must exist simultaneously and partition the",
              flush=True)
        print("  cells.", flush=True)


if __name__ == "__main__":
    main()
