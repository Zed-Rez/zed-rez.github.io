"""
anneal -> min-conflicts repair -> breakout, chained.

Each stage is good at a different part of the descent.  Annealing falls fast
from a random start but wastes moves once the residual is small; min-conflicts
aims every move at a live violation and finishes the easy tails; breakout
changes the objective itself, which is the only thing that helps when the
residual is a genuine local minimum.

Chaining them is strictly better than any one: annealing reaches the low
hundreds in seconds, repair takes that to single digits, and breakout works on
what remains with a weighted objective that the earlier stages cannot see.
"""

import json
import sys
import time

import breakout as B
import formA_reflection as R
import refl_anneal as A


def pipeline(t, a_s, r_s, b_s, seed):
    a = A.ReflAnneal(t, seed=seed)
    b1, _, _ = a.run_ils(time.time() + a_s, seed=seed)
    if b1:
        b2, _ = A.focused_repair(a, time.time() + r_s, seed=seed)
    else:
        b2 = 0
    if b2 == 0:
        return 0, a.to_g(), 0
    bo = B.Breakout(t, seed=seed)
    for (i, j) in bo.f:
        if i:
            bo.f[(i, j)] = int(a.F[i, j])
    best, it, bumps = bo.run(time.time() + b_s)
    return best, bo.to_g(), bumps


def main():
    t = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    a_s = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
    r_s = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
    b_s = float(sys.argv[4]) if len(sys.argv) > 4 else 300.0
    tries = int(sys.argv[5]) if len(sys.argv) > 5 else 12
    target = int(sys.argv[6]) if len(sys.argv) > 6 else 30

    print("pipeline anneal(%.0fs) -> repair(%.0fs) -> breakout(%.0fs)\n"
          % (a_s, r_s, b_s), flush=True)
    while t <= target:
        done = False
        for k in range(tries):
            best, g, bumps = pipeline(t, a_s, r_s, b_s, seed=1300 + 53 * t + k)
            if best == 0:
                sig = R.to_sigma(t, g)
                ok, inv, tot, n, girth = R.audit(t, sig)
                assert ok and inv == tot and girth
                print("  t=%-3d SOLVED -- Form A %d/%d, fragment %d vertices, "
                      "girth>=5 %s" % (t, inv, tot, n, girth), flush=True)
                json.dump({"t": t, "m": 56,
                           "sigma": {"%d,%d" % kk: list(v)
                                     for kk, v in sig.items()},
                           "labels": {"%d,%d" % kk: v for kk, v in g.items()}},
                          open("formA_pipeline_t%d.json" % t, "w"))
                done = True
                break
            print("  t=%-3d try %d: %d violations left (%d bumps)"
                  % (t, k, best, bumps), flush=True)
        if not done:
            print("  stalled at t=%d" % (t - 1), flush=True)
            break
        t += 1
    print("\npipeline frontier: t = %d of 57" % (t - 1), flush=True)


if __name__ == "__main__":
    main()
