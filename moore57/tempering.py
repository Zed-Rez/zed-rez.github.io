"""
Parallel tempering (replica exchange).

Plain annealing keeps getting stuck: at 12 branches it falls to cost ~50 in
80 s and then crawls to ~26 over 250 s, which is the signature of a rugged
landscape with deep local minima rather than of a hard cooling schedule.
Focused (WalkSAT-style) move selection barely helped -- 51 against 53 on the
same budget -- so the problem is not where the moves are aimed.

Replica exchange is the standard remedy.  Run R copies of the system at a
geometric ladder of temperatures.  Each copy does Metropolis moves at its own
fixed temperature; periodically adjacent copies attempt to swap configurations
with probability

    min(1, exp((1/T_i - 1/T_j) * (E_i - E_j)))

The hot copies wander freely and feed fresh basins downward; the cold copies
refine.  Unlike annealing there is no schedule to get wrong, and a copy that
falls into a bad minimum is rescued by a swap instead of being stuck with it.
"""

import json
import math
import sys
import time

import numpy as np

import anneal_fast
import reduction


class Tempering:
    def __init__(self, t, m, model="involution", replicas=8, tmin=0.05,
                 tmax=2.0, seed=0):
        self.t, self.m, self.model = t, m, model
        self.R = replicas
        self.temps = [tmin * (tmax / tmin) ** (i / max(replicas - 1, 1))
                      for i in range(replicas)]
        self.reps = [anneal_fast.FastAnneal(t, m, seed=seed * 1000 + i,
                                            model=model)
                     for i in range(replicas)]
        self.energy = [r.total_cost() for r in self.reps]
        self.others = {}
        for i in range(1, t):
            for j in range(i + 1, t):
                self.others[(i, j)] = np.array(
                    [l for l in range(t) if l not in (i, j)])
        self.pairs = [(i, j) for i in range(1, t) for j in range(i + 1, t)]
        self.swaps = 0
        self.attempts = 0

    def _sweep(self, k, n_moves):
        """n_moves Metropolis moves on replica k at its own temperature."""
        rep = self.reps[k]
        temp = self.temps[k]
        rng = rep.rng
        e = self.energy[k]
        for _ in range(n_moves):
            i, j = self.pairs[rng.randrange(len(self.pairs))]
            o = self.others[(i, j)]
            before = rep.local_cost(i, j, o)
            old = rep.S[i, j].copy()
            old_inv = rep.S[j, i].copy()
            rep._put(i, j, rep.propose(i, j))
            after = rep.local_cost(i, j, o)
            d = after - before
            if d <= 0 or rng.random() < math.exp(-d / temp):
                e += d
                if e == 0:
                    self.energy[k] = 0
                    return 0
            else:
                rep.S[i, j] = old
                rep.S[j, i] = old_inv
        self.energy[k] = e
        return e

    def run(self, deadline, moves_per_sweep=400, log=sys.stdout, quiet=False):
        best = min(self.energy)
        best_k = int(np.argmin(self.energy))
        rounds = 0
        start = time.time()
        while time.time() < deadline:
            rounds += 1
            for k in range(self.R):
                e = self._sweep(k, moves_per_sweep)
                if e < best:
                    best, best_k = e, k
                if e == 0:
                    return 0, self.reps[k], rounds
            # adjacent swaps
            for k in range(self.R - 1):
                self.attempts += 1
                b = (1.0 / self.temps[k] - 1.0 / self.temps[k + 1])
                de = self.energy[k] - self.energy[k + 1]
                if de <= 0 or self.reps[0].rng.random() < math.exp(-b * de):
                    self.reps[k], self.reps[k + 1] = self.reps[k + 1], self.reps[k]
                    self.energy[k], self.energy[k + 1] = \
                        self.energy[k + 1], self.energy[k]
                    self.swaps += 1
            if not quiet and rounds % 25 == 0:
                print("      round %d: energies %s (best %d, swap rate %.2f, "
                      "%.0fs)" % (rounds, [int(x) for x in self.energy], best,
                                  self.swaps / max(self.attempts, 1),
                                  time.time() - start), file=log, flush=True)
        return best, self.reps[best_k], rounds


def validate():
    print("Validation at degree 7", flush=True)
    wins = 0
    for seed in range(4):
        pt = Tempering(7, 6, replicas=6, tmin=0.05, tmax=1.5, seed=seed)
        best, rep, rounds = pt.run(time.time() + 30, moves_per_sweep=200,
                                   quiet=True)
        if best == 0:
            g = reduction.build_graph(7, rep.to_sigma(), m=6)
            ok, msg = reduction.is_moore(g, 7)
            assert ok, msg
            wins += 1
    print("  solved %d of 4" % wins, flush=True)
    return wins


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        validate()
        return
    t = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
    model = sys.argv[3] if len(sys.argv) > 3 else "involution"
    replicas = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0

    print("parallel tempering: t=%d, %s, %d replicas, %.0fs"
          % (t, model, replicas, secs), flush=True)
    pt = Tempering(t, 56, model=model, replicas=replicas, seed=seed)
    print("  temperatures %s" % ["%.3f" % x for x in pt.temps], flush=True)
    best, rep, rounds = pt.run(time.time() + secs)
    print("  best energy %d after %d rounds (swap rate %.2f)"
          % (best, rounds, pt.swaps / max(pt.attempts, 1)), flush=True)
    if best == 0:
        g = reduction.build_graph(t, rep.to_sigma(), m=56)
        ok = reduction.girth_at_least_5(g)
        print("  *** COST 0 at t=%d -- fragment %d vertices, girth>=5: %s ***"
              % (t, len(g), ok), flush=True)
        json.dump({"t": t, "m": 56,
                   "sigma": {"%d,%d" % k: list(v)
                             for k, v in rep.to_sigma().items()}},
                  open("pt_%s_t%d.json" % (model, t), "w"))


if __name__ == "__main__":
    main()
