"""
Search for Form A directly.

The correction in conjecture.py matters here.  The 1-factorization machinery
imposes Form B, which is strictly weaker, and its certificates violate Form A --
so they cannot extend to a Moore graph if A holds.  The only earlier search
that imposed the real thing was involution_search.py, which used a slow CP
encoding and stalled at 4-5 branches.

This puts Form A into the fast annealer instead, as part of the cost:

    cost = fixed points of every triangle composite          (derangement)
         + non-involution defects of every triangle composite (Form A)
         + fixed points of every quadrilateral composite      (derangement)

Cost 0 is a structure that is both a valid Moore fragment and Form A
compliant.  The state space is still fixed-point-free involutions, which is
Form B and therefore implied by A, so nothing is lost by restricting to it.

Validated at degree 7, where Hoffman-Singleton satisfies Form A exactly, so
cost 0 must be reachable.
"""

import json
import math
import sys
import time

import numpy as np

import anneal_fast
import reduction


class FormAAnneal(anneal_fast.FastAnneal):

    def _defect(self, C):
        """For a batch of composites C (shape (n, m)): fixed points plus
        involution defects."""
        n = C.shape[0]
        ar = np.arange(n)[:, None]
        fixed = np.count_nonzero(C == self.ident)
        CC = C[ar, C]
        noninv = np.count_nonzero(CC != self.ident)
        return int(fixed) + int(noninv)

    def local_cost(self, i, j, others):
        S = self.S
        a = S[i, j]
        # triangle composites (i, j, l) as maps on B_i
        b = S[j, others][:, a]
        C = S[others, i][self.arL, b]
        cost = self._defect(C)
        if len(self.iu0):
            L = others[self.iu0]
            M = others[self.iu1]
            b2 = S[j, L][:, a]
            c2 = S[L, M][self.ar, b2]
            d2 = S[M, i][self.ar, c2]
            cost += int(np.count_nonzero(d2 == self.ident))
            b3 = S[j, M][:, a]
            c3 = S[M, L][self.ar, b3]
            d3 = S[L, i][self.ar, c3]
            cost += int(np.count_nonzero(d3 == self.ident))
        return cost

    def total_cost(self):
        from itertools import combinations
        S, ident = self.S, self.ident
        tot = 0
        t = self.t
        for a, b, c in combinations(range(t), 3):
            comp = S[c, a][S[b, c][S[a, b]]]
            tot += int(np.count_nonzero(comp == ident))
            tot += int(np.count_nonzero(comp[comp] != ident))
        for a, b, c, d in combinations(range(t), 4):
            for (p, q, u, w) in ((a, b, c, d), (a, b, d, c), (a, c, b, d)):
                comp = S[w, p][S[u, w][S[q, u][S[p, q]]]]
                tot += int(np.count_nonzero(comp == ident))
        return tot


def check_formA(a):
    """Independent audit: are all triangle composites f.p.f. involutions?"""
    import involution
    sig = {(i, j): tuple(int(x) for x in a.S[i, j])
           for i in range(a.t) for j in range(a.t) if i != j}
    from itertools import permutations
    tot = inv = 0
    for x, y, z in permutations(range(a.t), 3):
        tau = involution.composite(sig, a.t, x, y, z, a.m)
        tot += 1
        if involution.is_involution(tau) and all(tau[k] != k for k in range(a.m)):
            inv += 1
    return inv, tot


def validate(secs=30.0):
    print("Validation at degree 7 -- Hoffman-Singleton satisfies Form A, so")
    print("cost 0 must be reachable.\n", flush=True)
    wins = 0
    for seed in range(6):
        a = FormAAnneal(7, 6, seed=seed, model="involution")
        best, it, kicks = a.run_ils(time.time() + secs, t_lo=0.06,
                                    stall=20000, kick=8, seed=seed)
        if best == 0:
            g = reduction.build_graph(7, a.to_sigma(), m=6)
            ok, msg = reduction.is_moore(g, 7)
            inv, tot = check_formA(a)
            assert ok and inv == tot, (msg, inv, tot)
            wins += 1
    print("  solved %d of 6 restarts (each verified as a Moore graph with all "
          "composites involutive)" % wins, flush=True)
    return wins


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        validate()
        return
    t = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
    tries = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    seed0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    print("Form A search at degree 57, t=%d, %.0fs x %d tries"
          % (t, secs, tries), flush=True)
    best_ever = None
    for k in range(tries):
        a = FormAAnneal(t, 56, seed=seed0 + k, model="involution")
        c0 = a.total_cost()
        t0 = time.time()
        best, it, kicks = a.run_ils(time.time() + secs, t_lo=0.06,
                                    stall=40000, kick=10, seed=seed0 + k)
        print("  try %d: %d -> %d (%d moves, %d kicks, %.0fs)"
              % (k, c0, best, it, kicks, time.time() - t0), flush=True)
        if best_ever is None or best < best_ever:
            best_ever = best
        if best == 0:
            inv, tot = check_formA(a)
            g = reduction.build_graph(t, a.to_sigma(), m=56)
            print("  *** COST 0 at t=%d: Form A %d/%d, fragment %d vertices, "
                  "girth>=5: %s" % (t, inv, tot, len(g),
                                    reduction.girth_at_least_5(g)), flush=True)
            json.dump({"t": t, "m": 56,
                       "sigma": {"%d,%d" % kk: list(v)
                                 for kk, v in a.to_sigma().items()}},
                      open("formA_t%d.json" % t, "w"))
            return
    print("  best cost %s" % best_ever, flush=True)


if __name__ == "__main__":
    main()
