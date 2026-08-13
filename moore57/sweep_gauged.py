"""Push the gauged matching model at degree 57 as far as it will build."""
import sys
import time

import gauged_search
import reduction

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 600.0
workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
ts = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else \
    [8, 10, 12, 14, 16, 18, 20, 22, 25]

m = 56
best = 0
for t in ts:
    t0 = time.time()
    try:
        sol, name, (nd, ne) = gauged_search.build(t, m, seconds=secs,
                                                  workers=workers, seed=t)
    except Exception as exc:                       # model too large to build
        print("t=%2d : model build failed (%s)" % (t, exc), flush=True)
        break
    el = time.time() - t0
    print("t=%2d : %-12s in %6.0fs  (%d diseq, %d element)"
          % (t, name, el, nd, ne), flush=True)
    if sol is None:
        if name == "INFEASIBLE":
            print("      INFEASIBLE -- no %d-branch structure has the "
                  "involution property at degree 57." % t, flush=True)
            print("      That would refute the involution conjecture at 57.",
                  flush=True)
            break
        continue
    sigma = gauged_search.to_sigma(t, m, sol)
    ok = reduction.sigma_conditions_hold(t, sigma, m=m)
    g = reduction.build_graph(t, sigma, m=m)
    print("      verified: derangement conditions %s, %d vertices, girth>=5 %s"
          % (ok, len(g), reduction.girth_at_least_5(g)), flush=True)
    if ok:
        best = max(best, t)
        import json
        json.dump({"k": 57, "t": t, "m": m,
                   "M": {"%d,%d" % kk: v for kk, v in sol.items()}},
                  open("gauged_frontier.json", "w"))
print("best verified: t = %d of 57" % best, flush=True)
