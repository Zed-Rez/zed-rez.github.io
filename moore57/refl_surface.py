"""
Search the surface of 14-branch structures, not one point on it.

When the reflection growth stalled at 13, most 13 -> 14 extensions came back
INFEASIBLE and exactly one line survived: whether a structure extends is a
property of *that* structure, not of the level.  So the way to reach 15 is not
to hammer one 14-branch labelling but to generate many distinct ones and ask
each whether it extends.

Anneal-then-repair produces a fresh 14-branch structure in about two minutes,
so a surface of them is cheap.  Each is then handed to CP-SAT, which can prove
INFEASIBLE outright and move on rather than timing out.
"""

import json
import sys
import time

import formA_reflection as R
import formA_reflection_grow as G
import refl_anneal as A


def fresh_14(seed, anneal_secs=90.0, repair_secs=90.0, t=14):
    a = A.ReflAnneal(t, seed=seed)
    b1, _, _ = a.run_ils(time.time() + anneal_secs, seed=seed)
    if b1 != 0:
        b2, _ = A.focused_repair(a, time.time() + repair_secs, seed=seed)
        if b2 != 0:
            return None
    return a.to_g()


def main():
    t = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    samples = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    cp_secs = float(sys.argv[3]) if len(sys.argv) > 3 else 90.0
    seed0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    print("surface search: distinct %d-branch structures, each tested for "
          "extension\n" % t, flush=True)
    stats = {"INFEASIBLE": 0, "UNKNOWN": 0, "made": 0}
    for s in range(samples):
        g = fresh_14(seed0 + 313 * s, t=t)
        if g is None:
            print("  sample %d: could not build a %d-branch structure"
                  % (s, t), flush=True)
            continue
        stats["made"] += 1
        # verify the base before extending
        sig = R.to_sigma(t, g)
        ok, inv, tot, n, girth = R.audit(t, sig)
        assert ok and inv == tot and girth
        t0 = time.time()
        col, name, n_q = G.extend(g, t, seconds=cp_secs, seed=s * 17 + 1)
        el = time.time() - t0
        if col is None:
            stats[name] = stats.get(name, 0) + 1
            print("  sample %d: base verified (Form A %d/%d) -> extend %s "
                  "(%.0fs)" % (s, inv, tot, name, el), flush=True)
            continue
        g2 = dict(g)
        for i in range(t):
            g2[(i, t)] = col[i]
        sig2 = R.to_sigma(t + 1, g2)
        ok2, inv2, tot2, n2, girth2 = R.audit(t + 1, sig2)
        print("  sample %d: EXTENDED to t=%d -- Moore %s, Form A %d/%d, "
              "fragment %d vertices, girth>=5 %s"
              % (s, t + 1, ok2, inv2, tot2, n2, girth2), flush=True)
        assert ok2 and inv2 == tot2 and girth2
        json.dump({"t": t + 1, "m": 56,
                   "sigma": {"%d,%d" % k: list(v) for k, v in sig2.items()},
                   "labels": {"%d,%d" % k: v for k, v in g2.items()}},
                  open("formA_surface_t%d.json" % (t + 1), "w"))
        print("\n  reached t = %d" % (t + 1), flush=True)
        return

    print("\n  %d structures built; extensions: %d INFEASIBLE, %d undecided"
          % (stats["made"], stats.get("INFEASIBLE", 0),
             stats.get("UNKNOWN", 0)), flush=True)
    if stats.get("INFEASIBLE", 0) and not stats.get("UNKNOWN", 0):
        print("  Every structure sampled is a proved dead end at this level.",
              flush=True)


if __name__ == "__main__":
    main()
