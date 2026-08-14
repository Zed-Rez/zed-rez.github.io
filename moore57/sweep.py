"""Probabilistic frontier: the largest t for which local search reaches cost 0."""
import sys
import time

import anneal_fast as A
import reduction

ts = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [10, 12, 14, 16, 18, 20]
per_t = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
restarts = int(sys.argv[3]) if len(sys.argv) > 3 else 6
model = sys.argv[4] if len(sys.argv) > 4 else "involution"
tag = sys.argv[5] if len(sys.argv) > 5 else model

print("Probabilistic frontier at degree 57 (%s state space)" % model)
print("%.0fs and up to %d restarts per t\n" % (per_t, restarts), flush=True)

best_solved = 0
for t in ts:
    deadline = time.time() + per_t
    solved = 0
    best = None
    tried = 0
    for s in range(restarts):
        if time.time() > deadline:
            break
        a = A.FastAnneal(t, 56, seed=100 * t + s, model=model)
        c0 = a.total_cost()
        b, it = a.run(10_000_000, t0=2.0, t1=0.02, deadline=deadline)
        tried += 1
        if best is None or b < best:
            best = b
        if b == 0:
            solved += 1
            import json
            json.dump({"t": t, "m": 56,
                       "sigma": {"%d,%d" % k: list(v)
                                 for k, v in a.to_sigma().items()}},
                      open("anneal_%s_t%d.json" % (tag, t), "w"))
            break
    status = "SOLVED" if solved else "best cost %d" % best
    print("  t=%-3d %-16s (%d restarts, initial cost ~%d)"
          % (t, status, tried, c0), flush=True)
    if solved:
        best_solved = t
    else:
        break

print("\nprobabilistic frontier: t = %d of 57" % best_solved, flush=True)
