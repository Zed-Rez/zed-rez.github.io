"""
Grow-and-repair for the reflection model.

refl_hybrid.py restarts from scratch at every t, which throws away a verified
structure each time.  Everywhere else in this project grow-and-repair beat cold
restarts by a wide margin, and there is no reason this model should differ:
load the t-branch labelling, append a branch with random labels, then anneal and
repair the *whole* table so earlier branches can still be revised.
"""

import json
import sys
import time

import numpy as np

import formA_reflection as R
import refl_anneal as A

MOD = A.MOD


def load_labels(path):
    d = json.load(open(path))
    t = d["t"]
    lab = {}
    for k, v in d["labels"].items():
        i, j = (int(z) for z in k.split(","))
        lab[(min(i, j), max(i, j))] = v
    return t, lab


def state_from(t, lab, extra_seed):
    """A ReflAnneal on t+1 branches whose first t branches copy `lab`."""
    a = A.ReflAnneal(t + 1, seed=extra_seed)
    for (i, j), g in lab.items():
        f = ((g - 1) // 2) % MOD
        a.F[i, j] = a.F[j, i] = f
    # branch 0 stays gauge-fixed at zero
    for j in range(1, t + 1):
        a.F[0, j] = a.F[j, 0] = 0
    return a


def save(a, t):
    g = a.to_g()
    sig = R.to_sigma(t, g)
    ok, inv, tot, n, girth = R.audit(t, sig)
    assert ok and inv == tot and girth, (ok, inv, tot, girth)
    json.dump({"t": t, "m": 56,
               "sigma": {"%d,%d" % k: list(v) for k, v in sig.items()},
               "labels": {"%d,%d" % k: v for k, v in g.items()}},
              open("formA_growhybrid_t%d.json" % t, "w"))
    return inv, tot, n, girth


def main():
    path = sys.argv[1]
    base = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
    tries = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    target = int(sys.argv[4]) if len(sys.argv) > 4 else 57
    budget = float(sys.argv[5]) if len(sys.argv) > 5 else 20000.0

    t, lab = load_labels(path)
    print("seed: %s with t=%d branches" % (path, t), flush=True)
    end = time.time() + budget

    while t < target and time.time() < end:
        placed = False
        for mult in (1, 3, 9):
            if placed or time.time() > end:
                break
            for k in range(tries):
                if time.time() > end:
                    break
                a = state_from(t, lab, extra_seed=5000 + 97 * t + 7 * k + mult)
                c0 = a.total_cost()
                t0 = time.time()
                b1, _, _ = a.run_ils(time.time() + base * mult,
                                     seed=97 * t + k + mult)
                b2 = b1
                if b1 != 0:
                    b2, _ = A.focused_repair(
                        a, time.time() + base * mult * 0.8, seed=k + mult)
                el = time.time() - t0
                if b2 == 0:
                    inv, tot, n, girth = save(a, t + 1)
                    print("  t=%-3d SOLVED (%.0fs budget, cost %d -> 0, %.0fs) "
                          "-- Form A %d/%d, fragment %d vertices, girth>=5 %s"
                          % (t + 1, base * mult, c0, el, inv, tot, n, girth),
                          flush=True)
                    lab = a.to_g()
                    t += 1
                    placed = True
                    break
                print("  t=%-3d %.0fs try %d: %d -> anneal %d -> repair %d "
                      "(%.0fs)" % (t + 1, base * mult, k, c0, b1, b2, el),
                      flush=True)
        if not placed:
            print("  stalled at t=%d" % t, flush=True)
            break

    print("\nreflection frontier, grow + anneal + repair: t = %d of 57" % t,
          flush=True)


if __name__ == "__main__":
    main()
