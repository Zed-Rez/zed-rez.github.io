"""
Is the involution property even satisfiable at degree 57?

If the Moore graph of degree 57 exists *and* has the involution property, then
its first t branches give a valid gauged matching structure for every
t <= 57.  So a proof of INFEASIBILITY at any small t would show:

    either the graph does not exist, or it does not have the involution
    property (which is verified at degrees 3 and 7).

Either branch of that disjunction is worth having: the second would refute the
conjecture and retire the model built on it, the first would be a genuine
non-existence result.  A run of SAT results at increasing t is evidence the
other way.

This runs the gauged model at small t with long budgets and reports a definite
SAT / UNSAT wherever CP-SAT can reach one.
"""

import json
import sys
import time

import gauged_search
import reduction


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 900.0
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    ts = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 \
        else [4, 5, 6, 7]
    m = 56

    print("gauged matching model at degree 57, decisive small-t feasibility")
    print("(SAT = the involution property survives at that many branches;")
    print(" UNSAT = it is refuted at degree 57)\n", flush=True)

    for t in ts:
        t0 = time.time()
        sol, name, (nd, ne) = gauged_search.build(t, m, seconds=secs,
                                                  workers=workers, seed=t)
        el = time.time() - t0
        verdict = {"OPTIMAL": "SAT", "FEASIBLE": "SAT",
                   "INFEASIBLE": "UNSAT"}.get(name, "undecided")
        print("t=%2d branches : %-9s (%s) in %6.0fs   [%d diseq, %d element]"
              % (t, verdict, name, el, nd, ne), flush=True)
        if sol is not None:
            sigma = gauged_search.to_sigma(t, m, sol)
            ok = reduction.sigma_conditions_hold(t, sigma, m=m)
            g = reduction.build_graph(t, sigma, m=m)
            print("               verified: derangement conditions %s, "
                  "%d vertices, girth>=5 %s"
                  % (ok, len(g), reduction.girth_at_least_5(g)), flush=True)
            if ok:
                json.dump({"k": 57, "t": t, "m": m,
                           "M": {"%d,%d" % kk: v for kk, v in sol.items()}},
                          open("gauged57_t%d.json" % t, "w"))
        if name == "INFEASIBLE":
            print("\n  REFUTED: no %d-branch structure at degree 57 has the"
                  % t, flush=True)
            print("  involution property.  Since Petersen and "
                  "Hoffman-Singleton do have it,", flush=True)
            print("  the property is not a theorem about Moore graphs in "
                  "general.", flush=True)
            return
    print("\n  No infeasibility found at these sizes.", flush=True)


if __name__ == "__main__":
    main()
