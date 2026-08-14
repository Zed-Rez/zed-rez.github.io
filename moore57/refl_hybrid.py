"""
Anneal, then repair: the best method found for the reflection model.

Annealing drives the cost down fast but sticks in the tail -- cost 3 to 6 out of
thousands of conditions -- because uniform pair selection wastes nearly every
move once only a handful of conditions are broken.  Min-conflicts repair aims
every move at a live violation, and finishes what annealing starts.

That combination closed t = 14, which CP-SAT growth reached only once out of
319 restarts, and it does it in about two minutes.
"""

import json
import sys
import time

import formA_reflection as R
import refl_anneal as A


def attempt(t, anneal_secs, repair_secs, seed):
    a = A.ReflAnneal(t, seed=seed)
    b1, _, _ = a.run_ils(time.time() + anneal_secs, seed=seed)
    if b1 == 0:
        b2 = 0
    else:
        b2, _ = A.focused_repair(a, time.time() + repair_secs, seed=seed)
    if b2 != 0:
        return None, b1, b2
    g = a.to_g()
    sig = R.to_sigma(t, g)
    ok, inv, tot, n, girth = R.audit(t, sig)
    assert ok and inv == tot and girth, (ok, inv, tot, girth)
    json.dump({"t": t, "m": 56,
               "sigma": {"%d,%d" % k: list(v) for k, v in sig.items()},
               "labels": {"%d,%d" % k: v for k, v in g.items()}},
              open("formA_hybrid_t%d.json" % t, "w"))
    return (inv, tot, n, girth), b1, b2


def main():
    tstart = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    base = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    tries = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    tmax = int(sys.argv[4]) if len(sys.argv) > 4 else 57
    budget = float(sys.argv[5]) if len(sys.argv) > 5 else 20000.0

    end = time.time() + budget
    print("anneal-then-repair on the reflection model, base budget %.0fs\n"
          % base, flush=True)
    best = tstart - 1
    for t in range(tstart, tmax + 1):
        got = None
        # escalate: cheap attempts first, longer ones only if they fail
        for mult in (1, 3, 9):
            if got is not None or time.time() > end:
                break
            for k in range(tries):
                if time.time() > end:
                    break
                res, b1, b2 = attempt(t, base * mult, base * mult * 0.6,
                                      seed=9000 + 137 * t + 11 * k + mult)
                if res is not None:
                    inv, tot, n, girth = res
                    print("  t=%-3d SOLVED (%.0fs budget) -- Form A %d/%d, "
                          "fragment %d vertices, girth>=5 %s"
                          % (t, base * mult, inv, tot, n, girth), flush=True)
                    got = res
                    break
                print("  t=%-3d %.0fs try %d: anneal %d -> repair %d"
                      % (t, base * mult, k, b1, b2), flush=True)
        if got is None:
            print("  stalled at t=%d" % best, flush=True)
            break
        best = t
    print("\nreflection frontier, anneal+repair: t = %d of 57" % best,
          flush=True)


if __name__ == "__main__":
    main()
