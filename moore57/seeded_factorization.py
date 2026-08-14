"""
Seed row 1 with an explicit 1-factorization instead of searching for one.

Under the conjecture (form B) the gauge makes every row of the sigma-table a
1-factorization of K_56: for each i, the family { sigma_ij : j != i } is 55
perfect matchings partitioning the 1540 edges.  So row 1 is not something to
discover -- it is a 1-factorization, and one can simply be written down.

The round-robin ("circle") 1-factorization of K_2n is the standard one: fix
point 2n-1, arrange the rest in a circle, and rotate.  Fixing row 1 to it costs
nothing at degree 7, because K_6 has a *unique* 1-factorization up to
isomorphism -- so the degree-7 run below is a clean test of the idea rather
than a lucky guess.  At degree 57 it is a genuine assumption: K_56 has
astronomically many non-isomorphic 1-factorizations and this picks one.

Fixing row 1 removes 55 of the 1540 unknowns outright and constrains the rest
through every triangle and quadrilateral that touches branch 1.
"""

import json
import sys
import time

import numpy as np

import anneal_fast
import reduction


def round_robin(m):
    """The circle 1-factorization of K_m (m even): m-1 perfect matchings,
    returned as fixed-point-free involutions on {0..m-1}."""
    assert m % 2 == 0
    fixed = m - 1
    others = list(range(m - 1))
    factors = []
    for r in range(m - 1):
        rot = others[r:] + others[:r]
        p = np.empty(m, dtype=np.int16)
        a = rot[0]
        p[fixed], p[a] = a, fixed
        for k in range(1, m // 2):
            u, v = rot[k], rot[m - 1 - k]
            p[u], p[v] = v, u
        factors.append(p)
    return factors


def check_factorization(factors, m):
    seen = {}
    for idx, p in enumerate(factors):
        assert all(p[p[x]] == x and p[x] != x for x in range(m)), "not fpf inv"
        for x in range(m):
            if x < p[x]:
                e = (x, int(p[x]))
                assert e not in seen, "edge %s reused" % (e,)
                seen[e] = idx
    return len(seen) == m * (m - 1) // 2


class SeededAnneal(anneal_fast.FastAnneal):
    """FastAnneal with row 1 pinned to a 1-factorization and never moved."""

    def pin_row1(self, factors):
        for j in range(2, self.t):
            self._put(1, j, factors[j - 2].copy())
        self.frozen = {(1, j) for j in range(2, self.t)}


def run(t, m, secs, seed, report=True):
    factors = round_robin(m)
    assert check_factorization(factors, m), "bad 1-factorization"
    a = SeededAnneal(t, m, seed=seed, model="involution")
    a.pin_row1(factors)
    # restrict the move set: never propose on a pinned pair
    pairs = [(i, j) for i in range(1, t) for j in range(i + 1, t)
             if not (i == 1)]
    a._restricted_pairs = pairs
    best, it = a.run_restricted(pairs, secs, seed)
    return a, best, it


def _run_restricted(self, pairs, secs, seed):
    """Metropolis over a restricted pair set, time-based cooling."""
    import math
    import random
    rng = random.Random(seed)
    others = {(i, j): np.array([l for l in range(self.t) if l not in (i, j)])
              for (i, j) in pairs}
    cost = self.total_cost()
    best = cost
    start = time.time()
    end = start + secs
    it = 0
    while True:
        it += 1
        if (it & 255) == 0:
            now = time.time()
            if now > end:
                break
            frac = (now - start) / secs
        else:
            frac = 0.0 if it < 256 else frac
        i, j = pairs[rng.randrange(len(pairs))]
        o = others[(i, j)]
        before = self.local_cost(i, j, o)
        old = self.S[i, j].copy()
        old_inv = self.S[j, i].copy()
        self._put(i, j, self.propose(i, j))
        after = self.local_cost(i, j, o)
        d = after - before
        temp = 1.2 * (0.01 / 1.2) ** frac
        if d <= 0 or rng.random() < math.exp(-d / max(temp, 1e-9)):
            cost += d
            if cost < best:
                best = cost
            if cost == 0:
                return 0, it
        else:
            self.S[i, j] = old
            self.S[j, i] = old_inv
    return best, it


SeededAnneal.run_restricted = _run_restricted


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        print("Degree 7: K_6 has a unique 1-factorization up to isomorphism,")
        print("so pinning row 1 to the round-robin one costs nothing.\n")
        wins = 0
        for s in range(6):
            a, best, it = run(7, 6, 20.0, seed=s)
            if best == 0:
                g = reduction.build_graph(7, a.to_sigma(), m=6)
                ok, msg = reduction.is_moore(g, 7)
                assert ok, msg
                wins += 1
        print("  solved %d of 6 restarts -- %s" % (wins, "WORKS" if wins else "fails"))
        return

    t = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
    tries = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    print("row-1-seeded search at t=%d, %.0fs x %d tries" % (t, secs, tries),
          flush=True)
    for s in range(tries):
        a, best, it = run(t, 56, secs, seed=s)
        print("  try %d: best cost %d (%d moves)" % (s, best, it), flush=True)
        if best == 0:
            g = reduction.build_graph(t, a.to_sigma(), m=56)
            print("  *** COST 0 at t=%d -- fragment %d vertices, girth>=5: %s"
                  % (t, len(g), reduction.girth_at_least_5(g)), flush=True)
            json.dump({"t": t, "m": 56,
                       "sigma": {"%d,%d" % k: list(v)
                                 for k, v in a.to_sigma().items()}},
                      open("seeded_t%d.json" % t, "w"))
            break


if __name__ == "__main__":
    main()
