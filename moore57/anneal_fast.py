"""
Fast probabilistic search: the whole sigma-table as one numpy array.

anneal.py evaluates a move by looping over the affected conditions, which is
fine at degree 7 and hopeless at 57 (3025 composites per move).  Here the table
is a single (t, t, m) array, so every condition touching a pair (i, j) is
evaluated in a handful of batched numpy operations, independent of t.

For the pair (i, j) the conditions that involve it are

    triangles      (i, j, l)              for each other branch l
    quadrilaterals (i, j, l, m) and (i, j, m, l)    for each other pair {l, m}

(the third cyclic order of a 4-set, (i, l, j, m), does not use the edge (i, j)
and is therefore unaffected by the move).  Batched:

    a = S[i,j]                          shape (m,)
    b = S[j,L][:, a]                    shape (P, m)
    c = S[L,M][arange, b]               shape (P, m)
    d = S[M,i][arange, c]               shape (P, m)
    cost = count of d == identity

The state space is the conjecture's form B: every sigma_ij with i,j >= 1 is a
fixed-point-free involution, and a move rewires two edges of one matching.
anneal.py's validation shows why that matters -- in this space local search
solves degree 7 in a few hundred iterations, every time; in the space of
arbitrary permutations it never solves it at all.
"""

import json
import math
import random
import sys
import time

import numpy as np

import reduction


class FastAnneal:
    def __init__(self, t, m, seed=0, model="involution"):
        self.t, self.m = t, m
        self.model = model
        self.rng = random.Random(seed)
        self.ident = np.arange(m, dtype=np.int16)
        self.S = np.zeros((t, t, m), dtype=np.int16)
        for i in range(t):
            for j in range(t):
                self.S[i, j] = self.ident
        for i in range(1, t):
            for j in range(i + 1, t):
                p = (self._rand_fpf() if self.model == "involution"
                     else self._rand_perm())
                self._put(i, j, p)
        # index pattern for the other-branch pairs (same shape for every i,j)
        n = t - 2
        if n >= 2:
            iu = np.triu_indices(n, 1)
            self.iu0, self.iu1 = iu[0], iu[1]
            self.ar = np.arange(len(self.iu0))[:, None]
        else:
            self.iu0 = self.iu1 = np.array([], dtype=int)
            self.ar = np.zeros((0, 1), dtype=int)
        self.arL = np.arange(t - 2)[:, None]

    def _rand_fpf(self):
        pts = list(range(self.m))
        self.rng.shuffle(pts)
        p = np.empty(self.m, dtype=np.int16)
        for a, b in zip(pts[0::2], pts[1::2]):
            p[a], p[b] = b, a
        return p

    def _rand_perm(self):
        pts = list(range(self.m))
        self.rng.shuffle(pts)
        return np.array(pts, dtype=np.int16)

    def _put(self, i, j, p):
        self.S[i, j] = p
        inv = np.empty(self.m, dtype=np.int16)
        inv[p] = self.ident
        self.S[j, i] = inv

    # -- cost --------------------------------------------------------------
    def local_cost(self, i, j, others):
        S, ident = self.S, self.ident
        a = S[i, j]
        # triangles (i, j, l)
        b = S[j, others][:, a]                       # (L, m)
        c = S[others, i][self.arL, b]                # (L, m)
        cost = int(np.count_nonzero(c == ident))
        if len(self.iu0):
            L = others[self.iu0]
            M = others[self.iu1]
            # order (i, j, L, M)
            b2 = S[j, L][:, a]
            c2 = S[L, M][self.ar, b2]
            d2 = S[M, i][self.ar, c2]
            cost += int(np.count_nonzero(d2 == ident))
            # order (i, j, M, L)
            b3 = S[j, M][:, a]
            c3 = S[M, L][self.ar, b3]
            d3 = S[L, i][self.ar, c3]
            cost += int(np.count_nonzero(d3 == ident))
        return cost

    def total_cost(self):
        """Sum over all conditions; each pair-local block counts the triangles
        once per pair (3 pairs per triangle) and the quads once per pair for
        two of its four edges, so divide accordingly."""
        tri = quad = 0
        t = self.t
        S, ident = self.S, self.ident
        from itertools import combinations
        for a, b, c in combinations(range(t), 3):
            comp = S[c, a][S[b, c][S[a, b]]]
            tri += int(np.count_nonzero(comp == ident))
        for a, b, c, d in combinations(range(t), 4):
            for (p, q, u, w) in ((a, b, c, d), (a, b, d, c), (a, c, b, d)):
                comp = S[w, p][S[u, w][S[q, u][S[p, q]]]]
                quad += int(np.count_nonzero(comp == ident))
        return tri + quad

    # -- moves -------------------------------------------------------------
    def propose(self, i, j):
        p = self.S[i, j]
        new = p.copy()
        m = self.m
        if self.model != "involution":
            # a transposition keeps it a permutation
            a = self.rng.randrange(m)
            b = self.rng.randrange(m)
            while b == a:
                b = self.rng.randrange(m)
            new[a], new[b] = p[b], p[a]
            return new
        a = self.rng.randrange(m)
        b = self.rng.randrange(m)
        while b == a or p[a] == b:
            b = self.rng.randrange(m)
        a2, b2 = int(p[a]), int(p[b])
        new[a], new[b] = b, a
        new[a2], new[b2] = b2, a2
        return new

    def run(self, iters, t0=2.0, t1=0.02, deadline=None, report_every=None,
            log=sys.stdout, focus=0.0, refresh=20000):
        """``focus`` is the probability of picking the pair to move in
        proportion to how much unsatisfied cost it currently carries, rather
        than uniformly (a WalkSAT-style focused walk).  The per-pair costs go
        stale as neighbouring pairs change, so they are recomputed every
        ``refresh`` moves."""
        t = self.t
        others_cache = {}
        cost = self.total_cost()
        best = cost
        start = time.time()
        pairs = [(i, j) for i in range(1, t) for j in range(i + 1, t)]
        npairs = len(pairs)

        def others_for(i, j):
            o = others_cache.get((i, j))
            if o is None:
                o = np.array([l for l in range(t) if l not in (i, j)])
                others_cache[(i, j)] = o
            return o

        pc = np.zeros(npairs, dtype=np.float64)
        if focus > 0:
            for idx, (i, j) in enumerate(pairs):
                pc[idx] = self.local_cost(i, j, others_for(i, j))
        # When a wall-clock deadline is given, drive the cooling schedule by
        # elapsed time rather than by iteration count -- otherwise a deadline
        # that cuts the run short leaves the temperature still near t0 and the
        # walk never anneals at all.
        span = (deadline - start) if deadline else None
        frac = 0.0
        for it in range(iters):
            if (it & 255) == 0:
                now = time.time()
                if deadline:
                    if now > deadline:
                        return best, it
                    frac = min((now - start) / max(span, 1e-9), 1.0)
                else:
                    frac = it / max(iters - 1, 1)
            if focus > 0 and (it % refresh) == 0 and it:
                for idx, (a_, b_) in enumerate(pairs):
                    pc[idx] = self.local_cost(a_, b_, others_for(a_, b_))
            if focus > 0 and self.rng.random() < focus and pc.sum() > 0:
                idx = int(np.searchsorted(np.cumsum(pc),
                                          self.rng.random() * pc.sum()))
                idx = min(idx, npairs - 1)
            else:
                idx = self.rng.randrange(npairs)
            i, j = pairs[idx]
            others = others_for(i, j)
            before = self.local_cost(i, j, others)
            old = self.S[i, j].copy()
            old_inv = self.S[j, i].copy()
            self._put(i, j, self.propose(i, j))
            after = self.local_cost(i, j, others)
            delta = after - before
            temp = t0 * (t1 / t0) ** frac
            if delta <= 0 or self.rng.random() < math.exp(-delta / max(temp, 1e-9)):
                cost += delta
                if focus > 0:
                    pc[idx] = after
                if cost < best:
                    best = cost
                if cost == 0:
                    return 0, it
            else:
                self.S[i, j] = old
                self.S[j, i] = old_inv
                if focus > 0:
                    pc[idx] = before
            if report_every and it and it % report_every == 0:
                print("      iter %d: cost %d (best %d, %.0f moves/s)"
                      % (it, cost, best, it / max(time.time() - start, 1e-9)),
                      file=log, flush=True)
        return best, iters

    def to_sigma(self):
        return {(i, j): tuple(int(x) for x in self.S[i, j])
                for i in range(self.t) for j in range(self.t) if i != j}


def validate():
    print("Validation at degree 7 (t=7, m=6)", flush=True)
    wins = 0
    for seed in range(6):
        a = FastAnneal(7, 6, seed=seed)
        best, it = a.run(200000, t0=1.5, t1=0.02)
        if best == 0:
            g = reduction.build_graph(7, a.to_sigma(), m=6)
            ok, msg = reduction.is_moore(g, 7)
            assert ok, msg
            wins += 1
    print("  solved %d of 6 restarts" % wins, flush=True)
    return wins == 6


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        ok = validate()
        print("fast model %s" % ("VALIDATED" if ok else "FAILED"))
        return

    t = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 200000
    restarts = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    budget = float(sys.argv[4]) if len(sys.argv) > 4 else 1800.0
    seed0 = int(sys.argv[5]) if len(sys.argv) > 5 else 0

    print("Degree 57, t=%d branches, involution state space" % t, flush=True)
    deadline = time.time() + budget
    best_overall = None
    for s in range(restarts):
        if time.time() > deadline:
            break
        a = FastAnneal(t, 56, seed=seed0 + s)
        c0 = a.total_cost()
        t0 = time.time()
        best, it = a.run(iters, t0=2.0, t1=0.02, deadline=deadline)
        el = time.time() - t0
        print("  restart %d: %d -> %d  (%d iters, %.0fs, %.0f moves/s)"
              % (s, c0, best, it, el, it / max(el, 1e-9)), flush=True)
        if best_overall is None or best < best_overall:
            best_overall = best
        if best == 0:
            print("  *** COST 0 at t=%d ***" % t, flush=True)
            json.dump({"t": t, "m": 56,
                       "sigma": {"%d,%d" % k: list(v)
                                 for k, v in a.to_sigma().items()}},
                      open("anneal_t%d.json" % t, "w"))
            break
    print("best cost at t=%d: %s" % (t, best_overall), flush=True)


if __name__ == "__main__":
    main()


def run_ils(self, deadline, t_lo=0.06, stall=60000, kick=10, seed=0,
            log=None):
    """Iterated local search: descend at a low fixed temperature, and when no
    improvement has appeared for `stall` moves, restore the best state seen and
    kick it with `kick` unconditional random moves.

    Plain annealing has one shot at the schedule; if it lands in a basin at
    cost 11 it stays there.  ILS keeps the best state and repeatedly relaunches
    from a perturbed copy of it, which is the standard remedy when the residual
    is small and stubborn.
    """
    import math
    import random
    rng = random.Random(seed)
    t = self.t
    pairs = [(i, j) for i in range(1, t) for j in range(i + 1, t)]
    others = {(i, j): np.array([l for l in range(t) if l not in (i, j)])
              for (i, j) in pairs}
    cost = self.total_cost()
    best = cost
    best_S = self.S.copy()
    since = 0
    kicks = 0
    it = 0
    while time.time() < deadline:
        it += 1
        i, j = pairs[rng.randrange(len(pairs))]
        o = others[(i, j)]
        before = self.local_cost(i, j, o)
        old = self.S[i, j].copy()
        old_inv = self.S[j, i].copy()
        self._put(i, j, self.propose(i, j))
        after = self.local_cost(i, j, o)
        d = after - before
        if d <= 0 or rng.random() < math.exp(-d / t_lo):
            cost += d
            if cost < best:
                best = cost
                best_S = self.S.copy()
                since = 0
                if cost == 0:
                    return 0, it, kicks
            else:
                since += 1
        else:
            self.S[i, j] = old
            self.S[j, i] = old_inv
            since += 1
        if since > stall:
            self.S = best_S.copy()
            for _ in range(kick):
                a, b = pairs[rng.randrange(len(pairs))]
                self._put(a, b, self.propose(a, b))
            cost = self.total_cost()
            since = 0
            kicks += 1
            if log:
                print("        kick %d (cost now %d, best %d)"
                      % (kicks, cost, best), file=log, flush=True)
    return best, it, kicks


FastAnneal.run_ils = run_ils
