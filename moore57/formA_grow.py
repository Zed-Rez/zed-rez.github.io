"""Seed the Form A annealer from the abelian construction and push upward."""
import json, sys, time
import numpy as np
import formA_abelian, formA_search, reduction, involution
from itertools import permutations

n0 = int(sys.argv[1]) if len(sys.argv) > 1 else 4      # abelian K_n seed
per_try = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
tries = int(sys.argv[3]) if len(sys.argv) > 3 else 4
target = int(sys.argv[4]) if len(sys.argv) > 4 else 12

a_col = formA_abelian.search(n0)
t0, sigma = formA_abelian.build_sigma(n0, a_col, 56)
print("seed: abelian Form A structure with t=%d branches" % t0, flush=True)

cur = formA_search.FormAAnneal(t0, 56, seed=0, model="involution")
for (i, j), p in sigma.items():
    cur.S[i, j] = np.array(p, dtype=np.int16)
assert cur.total_cost() == 0, "seed is not cost 0"

while cur.t < target:
    placed = False
    for k in range(tries):
        nxt = formA_search.FormAAnneal(cur.t + 1, 56, seed=k, model="involution")
        nxt.S[:cur.t, :cur.t] = cur.S
        c0 = nxt.total_cost()
        st = time.time()
        best, it, kicks = nxt.run_ils(time.time() + per_try, t_lo=0.06,
                                      stall=40000, kick=10, seed=k)
        el = time.time() - st
        if best == 0:
            inv, tot = formA_search.check_formA(nxt)
            g = reduction.build_graph(nxt.t, nxt.to_sigma(), m=56)
            gok = reduction.girth_at_least_5(g)
            print("  t=%-2d SOLVED (try %d, %d->0, %d moves, %.0fs) -- Form A %d/%d, "
                  "fragment %d vertices, girth>=5 %s"
                  % (nxt.t, k, c0, it, el, inv, tot, len(g), gok), flush=True)
            assert inv == tot and gok
            json.dump({"t": nxt.t, "m": 56,
                       "sigma": {"%d,%d" % kk: list(v) for kk, v in nxt.to_sigma().items()}},
                      open("formA_grow_t%d.json" % nxt.t, "w"))
            cur = nxt; placed = True; break
        else:
            print("  t=%-2d try %d: %d -> %d (%.0fs)" % (nxt.t, k, c0, best, el), flush=True)
    if not placed:
        print("  stalled at t=%d" % cur.t, flush=True)
        break
print("Form A frontier: t = %d of 57" % cur.t, flush=True)
