"""
Incremental reflection growth with randomised restarts.

The first-moment estimate for the reduced model (g_ij = 2 f_ij + 1, f symmetric
over Z_28, no vanishing 4-cycle sum) puts the ceiling of this ansatz near
t = 20.  Deep backtracking only reached 14, so the shortfall is search rather
than structure -- which also means an INFEASIBLE at 15 is not what to expect.

The cyclic labelling had exactly this profile, and randomised restarts of the
incremental growth took it from 15 to 19.  This applies the same recipe to the
reflection labelling, where anything found is Form A compliant by construction
and so is on-path under the conjecture.
"""

import json
import sys
import time

import formA_reflection as R
import formA_reflection_grow as G


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else 3600.0
    target = int(sys.argv[3]) if len(sys.argv) > 3 else 57

    end = time.time() + budget
    best = 0
    attempt = 0
    while time.time() < end:
        attempt += 1
        g = {(0, 1): 1}
        t = 2
        while t < target and time.time() < end:
            col, name, nq = G.extend(g, t, seconds=secs,
                                     seed=attempt * 1000 + t)
            if col is None:
                break
            for i in range(t):
                g[(i, t)] = col[i]
            t += 1
        if t > best:
            best = t
            sig = R.to_sigma(t, g)
            ok, inv, tot, n, girth = R.audit(t, sig)
            print("  attempt %d: t=%d -- Moore %s, Form A %d/%d, fragment %d "
                  "vertices, girth>=5 %s"
                  % (attempt, t, ok, inv, tot, n, girth), flush=True)
            assert ok and inv == tot and girth
            json.dump({"t": t, "m": 56,
                       "sigma": {"%d,%d" % k: list(v) for k, v in sig.items()},
                       "labels": {"%d,%d" % k: v for k, v in g.items()}},
                      open("formA_best_t%d.json" % t, "w"))
        else:
            print("  attempt %d: t=%d" % (attempt, t), flush=True)
    print("best Form A structure by reflection restarts: t = %d of 57" % best,
          flush=True)


if __name__ == "__main__":
    main()
