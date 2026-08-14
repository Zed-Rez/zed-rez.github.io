"""
Breakout: dynamic constraint weighting for the reduced reflection model.

Every method here converges on t = 15 and then sticks at a residual of 5 to 7
violated conditions out of ~4000.  That is the classic signature of a local
minimum that no amount of restarting escapes, and the classic remedy is not a
better move or a better schedule but a *changing objective*: give each condition
a weight, minimise the weighted violation count, and whenever the search is
stuck, add one to the weight of every currently violated condition.

The local minimum is then destroyed rather than escaped -- after enough bumps
the stuck configuration is no longer a minimum of the reweighted objective, and
the search moves on.  Weights also accumulate on the conditions that are
genuinely hard to satisfy, which steers later effort towards them.

Extension is not a route to 15: refl_surface.py proves seven independent 13- and
14-branch structures are dead ends, in seconds each.  A 15-branch structure has
to be found directly, which is what this does.
"""

import json
import random
import sys
import time
from itertools import combinations

import formA_reflection as R

MOD = 28


class Breakout:
    def __init__(self, t, seed=0):
        self.t = t
        self.rng = random.Random(seed)
        self.f = {}
        for i in range(t):
            for j in range(i + 1, t):
                v = 0 if i == 0 else self.rng.randrange(MOD)
                self.f[(i, j)] = v
        self.conds = []
        for a, b, c, d in combinations(range(t), 4):
            for cyc in ((a, b, c, d), (a, b, d, c), (a, c, b, d)):
                self.conds.append(cyc)
        self.w = [1] * len(self.conds)
        # conditions touching each pair
        self.touch = {(i, j): [] for i in range(t) for j in range(i + 1, t)}
        for idx, (p, q, u, v2) in enumerate(self.conds):
            for (x, y) in ((p, q), (q, u), (u, v2), (v2, p)):
                key = (x, y) if x < y else (y, x)
                self.touch[key].append(idx)
        self.free = [(i, j) for i in range(1, t) for j in range(i + 1, t)]

    def lab(self, i, j):
        return self.f[(i, j)] if i < j else self.f[(j, i)]

    def viol(self, idx):
        p, q, u, v = self.conds[idx]
        return (self.lab(p, v) - self.lab(u, v)
                + self.lab(q, u) - self.lab(p, q)) % MOD == 0

    def all_violated(self):
        return [i for i in range(len(self.conds)) if self.viol(i)]

    def weighted_local(self, key):
        return sum(self.w[i] for i in self.touch[key] if self.viol(i))

    def run(self, deadline, log=None):
        best = len(self.all_violated())
        best_f = dict(self.f)
        bumps = 0
        it = 0
        while time.time() < deadline:
            it += 1
            viol = self.all_violated()
            n = len(viol)
            if n == 0:
                return 0, it, bumps
            if n < best:
                best, best_f = n, dict(self.f)
                if log:
                    print("        %d violations (it %d, %d bumps)"
                          % (n, it, bumps), file=log, flush=True)
            # pick a violated condition, weighted, and try to repair it
            idx = viol[self.rng.randrange(len(viol))]
            p, q, u, v = self.conds[idx]
            cands = [(x, y) if x < y else (y, x)
                     for (x, y) in ((p, q), (q, u), (u, v), (v, p))]
            cands = [c for c in cands if c[0] != 0]
            if not cands:
                self.w[idx] += 1
                bumps += 1
                continue
            key = cands[self.rng.randrange(len(cands))]
            before = self.weighted_local(key)
            old = self.f[key]
            bestval, bestcost = old, before
            for val in range(MOD):
                if val == old:
                    continue
                self.f[key] = val
                c = self.weighted_local(key)
                if c < bestcost:
                    bestval, bestcost = val, c
            self.f[key] = bestval
            if bestcost >= before:
                # stuck: destroy the minimum by reweighting
                for i in self.all_violated():
                    self.w[i] += 1
                bumps += 1
        self.f = best_f
        return best, it, bumps

    def to_g(self):
        return {(i, j): (2 * self.f[(i, j)] + 1) % 56
                for i in range(self.t) for j in range(i + 1, self.t)}


def attempt(t, secs, seed, log=None):
    b = Breakout(t, seed=seed)
    best, it, bumps = b.run(time.time() + secs, log=log)
    if best != 0:
        return None, best, bumps
    g = b.to_g()
    sig = R.to_sigma(t, g)
    ok, inv, tot, n, girth = R.audit(t, sig)
    assert ok and inv == tot and girth, (ok, inv, tot, girth)
    json.dump({"t": t, "m": 56,
               "sigma": {"%d,%d" % k: list(v) for k, v in sig.items()},
               "labels": {"%d,%d" % k: v for k, v in g.items()}},
              open("formA_breakout_t%d.json" % t, "w"))
    return (inv, tot, n, girth), 0, bumps


def main():
    tstart = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 180.0
    tries = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    tmax = int(sys.argv[4]) if len(sys.argv) > 4 else 30

    print("breakout (dynamic constraint weighting) on the reflection model\n",
          flush=True)
    best_t = tstart - 1
    for t in range(tstart, tmax + 1):
        got = None
        for k in range(tries):
            res, resid, bumps = attempt(t, secs, seed=4242 + 91 * t + k)
            if res is not None:
                inv, tot, n, girth = res
                print("  t=%-3d SOLVED -- Form A %d/%d, fragment %d vertices, "
                      "girth>=5 %s (%d bumps)"
                      % (t, inv, tot, n, girth, bumps), flush=True)
                got = res
                break
            print("  t=%-3d try %d: %d violations left (%d bumps)"
                  % (t, k, resid, bumps), flush=True)
        if got is None:
            break
        best_t = t
    print("\nbreakout frontier: t = %d of 57" % best_t, flush=True)


if __name__ == "__main__":
    main()
