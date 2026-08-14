"""
Probabilistic search: simulated annealing / min-conflicts over the sigma-table.

No guarantee, no completeness -- just a randomized walk that tries to drive the
number of violated conditions to zero.  Two state spaces:

  general    sigma_ij is any permutation of the 56 points; a move composes one
             of them with a transposition.
  involution sigma_ij is a fixed-point-free involution (the conjecture's form
             B); a move rewires two edges of one matching, which keeps it a
             perfect matching.  The state space is 10^36.9 per unknown instead
             of 10^74.9, and the move set is closed on it.

COST.  The number of fixed points summed over every triangle composite and
every quadrilateral composite.  Cost 0 is exactly a Moore graph.  Branch 0 is
gauge-fixed to the identity and never moved.

Row edge-disjointness does not need a separate penalty: if sigma_ij(x) =
sigma_ij'(x) then the corresponding vertex and the point of B_0 they both point
at have two common neighbours, which is precisely a quadrilateral violation and
is already counted.

Validated at degree 7, where cost 0 must be reachable because
Hoffman-Singleton exists.
"""

import math
import random
import sys
import time
from itertools import combinations

import numpy as np

import reduction


class Anneal:
    def __init__(self, k, t=None, model="involution", seed=0, m=None):
        self.k = k
        self.m = m if m is not None else k - 1
        self.t = t if t is not None else k
        self.model = model
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        self.ident = np.arange(self.m, dtype=np.int16)
        self.s = {}
        self._init_state()

    # -- state -------------------------------------------------------------
    def _random_fpf_involution(self):
        pts = list(range(self.m))
        self.rng.shuffle(pts)
        p = np.empty(self.m, dtype=np.int16)
        for a, b in zip(pts[0::2], pts[1::2]):
            p[a], p[b] = b, a
        return p

    def _random_perm(self):
        p = np.array(self.np_rng.permutation(self.m), dtype=np.int16)
        return p

    def _init_state(self):
        for j in range(self.t):
            if j:
                self._put(0, j, self.ident.copy())
        for i, j in combinations(range(1, self.t), 2):
            p = (self._random_fpf_involution() if self.model == "involution"
                 else self._random_perm())
            self._put(i, j, p)

    def _put(self, i, j, p):
        self.s[(i, j)] = p
        inv = np.empty(self.m, dtype=np.int16)
        inv[p] = self.ident
        self.s[(j, i)] = inv

    # -- cost --------------------------------------------------------------
    def _fixed(self, arr):
        return int(np.count_nonzero(arr == self.ident))

    def tri(self, a, b, c):
        s = self.s
        return self._fixed(s[(c, a)][s[(b, c)][s[(a, b)]]])

    def quad(self, a, b, c, d):
        s = self.s
        return self._fixed(s[(d, a)][s[(c, d)][s[(b, c)][s[(a, b)]]]])

    def total_cost(self):
        c = 0
        for a, b, d in combinations(range(self.t), 3):
            c += self.tri(a, b, d)
        for a, b, d, e in combinations(range(self.t), 4):
            c += self.quad(a, b, d, e)
            c += self.quad(a, b, e, d)
            c += self.quad(a, d, b, e)
        return c

    def local_cost(self, i, j):
        """Cost of every condition that involves the pair (i, j)."""
        c = 0
        others = [l for l in range(self.t) if l not in (i, j)]
        for l in others:
            c += self.tri(i, j, l)
        for l, mm in combinations(others, 2):
            # the two cyclic orders whose 4-cycle uses the edge (i, j)
            c += self.quad(i, j, l, mm)
            c += self.quad(i, j, mm, l)
        return c

    # -- moves -------------------------------------------------------------
    def propose(self):
        i, j = self.rng.sample(range(1, self.t), 2)
        if i > j:
            i, j = j, i
        p = self.s[(i, j)]
        new = p.copy()
        if self.model == "involution":
            a = self.rng.randrange(self.m)
            b = self.rng.randrange(self.m)
            while b == a or p[a] == b:
                b = self.rng.randrange(self.m)
            a2, b2 = int(p[a]), int(p[b])
            new[a], new[b] = b, a
            new[a2], new[b2] = b2, a2
        else:
            a = self.rng.randrange(self.m)
            b = self.rng.randrange(self.m)
            while b == a:
                b = self.rng.randrange(self.m)
            new[a], new[b] = p[b], p[a]
        return i, j, new

    def run(self, iters=200000, t0=2.0, t1=0.01, report=None, deadline=None):
        cost = self.total_cost()
        best = cost
        start = time.time()
        for it in range(iters):
            if deadline and it % 512 == 0 and time.time() > deadline:
                break
            temp = t0 * (t1 / t0) ** (it / max(iters - 1, 1))
            i, j, new = self.propose()
            before = self.local_cost(i, j)
            old = self.s[(i, j)]
            old_inv = self.s[(j, i)]
            self._put(i, j, new)
            after = self.local_cost(i, j)
            delta = after - before
            if delta <= 0 or self.rng.random() < math.exp(-delta / max(temp, 1e-9)):
                cost += delta
                if cost < best:
                    best = cost
                    if report and best <= report:
                        print("      cost %d at iter %d (%.0fs)"
                              % (best, it, time.time() - start), flush=True)
                if cost == 0:
                    return 0, it
            else:
                self.s[(i, j)] = old
                self.s[(j, i)] = old_inv
        return best, iters

    # -- output ------------------------------------------------------------
    def to_sigma(self):
        return {(i, j): tuple(int(x) for x in self.s[(i, j)])
                for i in range(self.t) for j in range(self.t) if i != j}


def validate(model, trials=8, iters=400000):
    """At degree 7 a perfect solution exists; the search must find it."""
    print("  model=%-11s degree 7, t=7" % model, flush=True)
    wins = 0
    for seed in range(trials):
        a = Anneal(7, t=7, model=model, seed=seed)
        best, it = a.run(iters=iters, t0=1.5, t1=0.02)
        if best == 0:
            g = reduction.build_graph(7, a.to_sigma(), m=6)
            ok, msg = reduction.is_moore(g, 7)
            assert ok, msg
            wins += 1
    print("    solved %d of %d restarts -- %s" % (wins, trials,
          "WORKS" if wins else "never reached cost 0"), flush=True)
    return wins


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if what == "validate":
        print("Validation: probabilistic search on the graph that exists\n")
        w1 = validate("involution")
        w2 = validate("general")
        print("\n  involution model %s, general model %s"
              % ("works" if w1 else "fails", "works" if w2 else "fails"))
        return

    t = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    model = sys.argv[3] if len(sys.argv) > 3 else "involution"
    iters = int(sys.argv[4]) if len(sys.argv) > 4 else 300000
    restarts = int(sys.argv[5]) if len(sys.argv) > 5 else 5
    budget = float(sys.argv[6]) if len(sys.argv) > 6 else 3600.0

    print("Degree 57, t=%d branches, model=%s, %d iters x %d restarts"
          % (t, model, iters, restarts), flush=True)
    deadline = time.time() + budget
    overall = None
    for seed in range(restarts):
        if time.time() > deadline:
            break
        a = Anneal(57, t=t, model=model, seed=seed, m=56)
        c0 = a.total_cost()
        t0 = time.time()
        best, it = a.run(iters=iters, t0=2.0, t1=0.01, deadline=deadline)
        el = time.time() - t0
        print("  restart %d: start cost %d -> best %d  (%d iters, %.0fs, "
              "%.0f moves/s)" % (seed, c0, best, it, el, it / max(el, 1e-9)),
              flush=True)
        if overall is None or best < overall:
            overall = best
        if best == 0:
            print("  *** COST 0 -- a %d-branch structure ***" % t, flush=True)
            import json
            json.dump({"t": t, "m": 56,
                       "sigma": {"%d,%d" % kk: list(v)
                                 for kk, v in a.to_sigma().items()}},
                      open("anneal_t%d.json" % t, "w"))
            break
    print("best cost over all restarts: %s" % overall, flush=True)


if __name__ == "__main__":
    main()
