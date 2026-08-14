"""
Anneal the reduced reflection model.

Every g_ij is odd, so writing g_ij = 2 f_ij + 1 turns the quadrilateral sum into
2 (f_pw - f_uw + f_qu - f_pq); the reflection ansatz is therefore exactly

    a symmetric labelling f of K_t over Z_28 with no vanishing 4-cycle sum,

with the triangle conditions free and the gauge f_ij -> f_ij - s_i - s_j.

That state space is tiny next to the permutation models -- one of 28 values per
pair instead of one of 56! -- and annealing beat CP-SAT everywhere else in this
project, while here CP-SAT is what has been used throughout.  Cost is the number
of vanishing 4-cycle sums; cost 0 is a Form A compliant structure.

The first-moment estimate puts the ceiling of this model near t = 20, and
CP-SAT growth stalls at 13-14, so there is room for a better search to matter.
"""

import json
import math
import random
import sys
import time

import numpy as np

import formA_reflection as R

MOD = 28


class ReflAnneal:
    def __init__(self, t, seed=0):
        self.t = t
        self.rng = random.Random(seed)
        self.F = np.zeros((t, t), dtype=np.int64)
        for i in range(1, t):
            for j in range(i + 1, t):
                v = self.rng.randrange(MOD)
                self.F[i, j] = self.F[j, i] = v
        # gauge: f_0j = 0 for all j (row/col 0 stay zero)
        n = t - 2
        if n >= 2:
            iu = np.triu_indices(n, 1)
            self.iu0, self.iu1 = iu[0], iu[1]
        else:
            self.iu0 = self.iu1 = np.array([], dtype=int)
        self.pairs = [(i, j) for i in range(1, t) for j in range(i + 1, t)]
        self.others = {}
        for (i, j) in self.pairs:
            self.others[(i, j)] = np.array(
                [l for l in range(t) if l not in (i, j)])

    def local_cost(self, i, j):
        """Vanishing 4-cycle sums that use the edge (i, j)."""
        if not len(self.iu0):
            return 0
        F = self.F
        o = self.others[(i, j)]
        L = o[self.iu0]
        M = o[self.iu1]
        fij = F[i, j]
        d1 = (F[i, M] - F[L, M] + F[j, L] - fij) % MOD
        d2 = (F[i, L] - F[M, L] + F[j, M] - fij) % MOD
        return int(np.count_nonzero(d1 == 0) + np.count_nonzero(d2 == 0))

    def total_cost(self):
        from itertools import combinations
        F = self.F
        tot = 0
        for a, b, c, d in combinations(range(self.t), 4):
            for (p, q, u, w) in ((a, b, c, d), (a, b, d, c), (a, c, b, d)):
                if (F[p, w] - F[u, w] + F[q, u] - F[p, q]) % MOD == 0:
                    tot += 1
        return tot

    def run_ils(self, deadline, t_lo=0.35, stall=20000, kick=6, seed=0):
        rng = random.Random(seed)
        cost = self.total_cost()
        best = cost
        bestF = self.F.copy()
        since = 0
        it = 0
        kicks = 0
        while time.time() < deadline:
            it += 1
            i, j = self.pairs[rng.randrange(len(self.pairs))]
            old = int(self.F[i, j])
            before = self.local_cost(i, j)
            new = rng.randrange(MOD)
            while new == old:
                new = rng.randrange(MOD)
            self.F[i, j] = self.F[j, i] = new
            after = self.local_cost(i, j)
            d = after - before
            if d <= 0 or rng.random() < math.exp(-d / t_lo):
                cost += d
                if cost < best:
                    best, bestF, since = cost, self.F.copy(), 0
                    if cost == 0:
                        return 0, it, kicks
                else:
                    since += 1
            else:
                self.F[i, j] = self.F[j, i] = old
                since += 1
            if since > stall:
                self.F = bestF.copy()
                for _ in range(kick):
                    a, b = self.pairs[rng.randrange(len(self.pairs))]
                    v = rng.randrange(MOD)
                    self.F[a, b] = self.F[b, a] = v
                cost = self.total_cost()
                since = 0
                kicks += 1
        return best, it, kicks

    def to_g(self):
        return {(i, j): (2 * int(self.F[i, j]) + 1) % 56
                for i in range(self.t) for j in range(i + 1, self.t)}


def try_t(t, secs, seed):
    a = ReflAnneal(t, seed=seed)
    best, it, kicks = a.run_ils(time.time() + secs, seed=seed)
    if best != 0:
        return None, best
    g = a.to_g()
    sig = R.to_sigma(t, g)
    ok, inv, tot, n, girth = R.audit(t, sig)
    assert ok and inv == tot and girth, (ok, inv, tot, girth)
    json.dump({"t": t, "m": 56,
               "sigma": {"%d,%d" % k: list(v) for k, v in sig.items()},
               "labels": {"%d,%d" % k: v for k, v in g.items()}},
              open("formA_anneal_t%d.json" % t, "w"))
    return (inv, tot, n, girth), 0


def main():
    tstart = int(sys.argv[1]) if len(sys.argv) > 1 else 13
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    tries = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    tmax = int(sys.argv[4]) if len(sys.argv) > 4 else 57

    print("annealing the reduced reflection model (symmetric f over Z_%d)\n"
          % MOD, flush=True)
    best = 0
    for t in range(tstart, tmax + 1):
        got = None
        for k in range(tries):
            res, cost = try_t(t, secs, seed=1000 * t + k)
            if res is not None:
                inv, tot, n, girth = res
                print("  t=%-3d SOLVED -- Form A %d/%d, fragment %d vertices, "
                      "girth>=5 %s" % (t, inv, tot, n, girth), flush=True)
                got = res
                break
            else:
                print("  t=%-3d try %d: best cost %d" % (t, k, cost), flush=True)
        if got is None:
            break
        best = t
    print("\nreflection frontier by annealing: t = %d of 57" % best, flush=True)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# focused repair (min-conflicts)
# ---------------------------------------------------------------------------

def violations(a):
    """All vanishing 4-cycle sums, as (p, q, u, w) tuples."""
    from itertools import combinations
    F = a.F
    out = []
    for x, y, z, w0 in combinations(range(a.t), 4):
        for (p, q, u, w) in ((x, y, z, w0), (x, y, w0, z), (x, z, y, w0)):
            if (F[p, w] - F[u, w] + F[q, u] - F[p, q]) % MOD == 0:
                out.append((p, q, u, w))
    return out


def focused_repair(a, deadline, seed=0, t_lo=0.25, rescan=400):
    """Min-conflicts: repeatedly pick a violated 4-cycle and change one of its
    four edges.  Uniform pair selection wastes almost every move once only a
    handful of conditions are broken; this aims every move at a live one."""
    rng = random.Random(seed)
    cost = a.total_cost()
    best = cost
    bestF = a.F.copy()
    it = 0
    viol = violations(a)
    while time.time() < deadline:
        it += 1
        if not viol or it % rescan == 0:
            viol = violations(a)
            cost = len(viol)
            if cost < best:
                best, bestF = cost, a.F.copy()
            if cost == 0:
                return 0, it
        if not viol:
            return 0, it
        p, q, u, w = viol[rng.randrange(len(viol))]
        edges = [(p, q), (q, u), (u, w), (w, p)]
        i, j = edges[rng.randrange(4)]
        if i == 0 or j == 0:                       # gauge-fixed, cannot move
            continue
        i, j = (i, j) if i < j else (j, i)
        old = int(a.F[i, j])
        before = a.local_cost(i, j)
        new = rng.randrange(MOD)
        while new == old:
            new = rng.randrange(MOD)
        a.F[i, j] = a.F[j, i] = new
        after = a.local_cost(i, j)
        d = after - before
        if d <= 0 or rng.random() < math.exp(-d / t_lo):
            cost += d
            if cost < best:
                best, bestF = cost, a.F.copy()
                if cost == 0:
                    return 0, it
            viol = violations(a) if d else viol
        else:
            a.F[i, j] = a.F[j, i] = old
    a.F = bestF
    return best, it
