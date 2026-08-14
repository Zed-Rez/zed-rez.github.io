"""
Load a verified structure and spend a long budget adding one more branch.

The measured cost curve (scaling.py) says each branch costs about four times
the last, and that branch 12 in the involution space had consumed 4048 s
without falling.  So the only honest way to advance the frontier is to spend
roughly that much again, several times over, on a single branch.  This does
exactly that and nothing else.
"""

import json
import sys
import time

import numpy as np

import anneal_fast
import factorization_search as F
import general_extend as G
import reduction


def load_into(path, model):
    d = json.load(open(path))
    t, m = d["t"], d["m"]
    a = anneal_fast.FastAnneal(t + 1, m, seed=0, model=model)
    for k, v in d["sigma"].items():
        i, j = (int(z) for z in k.split(","))
        if i < t and j < t:
            a.S[i, j] = np.array(v, dtype=np.int16)
    return a, t


def check(a, model):
    if model == "involution":
        st = F.FactStructure(a.m)
        st.t = a.t
        st.sigma = {(i, j): [int(x) for x in a.S[i, j]]
                    for i in range(1, a.t) for j in range(1, a.t) if i != j}
    else:
        st = G.Structure(m=a.m)
        st.t = a.t
        st.sigma = {(i, j): [int(x) for x in a.S[i, j]]
                    for i in range(a.t) for j in range(a.t) if i != j}
    return st.verify()


USE_ILS = True


def main():
    path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "involution"
    per_try = float(sys.argv[3]) if len(sys.argv) > 3 else 3600.0
    tries = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    seed0 = int(sys.argv[5]) if len(sys.argv) > 5 else 0

    print("pushing %s (%s), %.0fs x %d tries" % (path, model, per_try, tries),
          flush=True)
    best_ever = None
    for k in range(tries):
        a, t = load_into(path, model)
        # randomise only the new branch
        for i in range(1, t):
            p = (a._rand_fpf() if model == "involution" else a._rand_perm())
            a._put(i, t, p)
        a.rng.seed(seed0 + 977 * k)
        c0 = a.total_cost()
        t0 = time.time()
        if USE_ILS:
            best, it, kicks = a.run_ils(time.time() + per_try, t_lo=0.06,
                                        stall=40000, kick=10,
                                        seed=seed0 + 977 * k)
        else:
            best, it = a.run(10_000_000, t0=1.2, t1=0.008,
                             deadline=time.time() + per_try)
            kicks = 0
        el = time.time() - t0
        if best_ever is None or best < best_ever:
            best_ever = best
        print("  try %d: %d -> %d  (%d moves, %d kicks, %.0fs)"
              % (k, c0, best, it, kicks, el), flush=True)
        if best == 0:
            ok, msg = check(a, model)
            g = reduction.build_graph(a.t, a.to_sigma(), m=a.m)
            gok = reduction.girth_at_least_5(g)
            print("  *** SOLVED t=%d: %s, fragment %d vertices, girth>=5: %s"
                  % (a.t, msg, len(g), gok), flush=True)
            assert ok and gok
            json.dump({"t": a.t, "m": a.m,
                       "sigma": {"%d,%d" % kk: list(v)
                                 for kk, v in a.to_sigma().items()}},
                      open("push_%s_t%d.json" % (model, a.t), "w"))
            return
    print("  not solved; best cost %d" % best_ever, flush=True)


if __name__ == "__main__":
    main()
