"""
Grow and repair: add a branch at random, then let annealing fix everything.

The CP-SAT growth in factorization_search.py is greedy in a strong sense --
once branch r is placed it is never revised, so a bad early choice is a dead
end that only backtracking can undo, and backtracking at this size is
hopeless.  Cold annealing at a fixed t has the opposite problem: it throws away
everything already known.

This does both.  Start from a solved t-branch structure, append a branch with
random bijections, and anneal the *whole* table -- moves may touch any pair, so
the search can revise branch 3 in order to fit branch 15.  If it reaches cost 0
the structure is saved and the process repeats at t+1.

Everything is conditional on the involution conjecture when run in the
involution state space, and unconditional in the general one.
"""

import json
import sys
import time

import numpy as np

import anneal_fast
import reduction


def extend_state(a, seed):
    """A FastAnneal on t+1 branches whose first t branches copy `a`."""
    b = anneal_fast.FastAnneal(a.t + 1, a.m, seed=seed, model=a.model)
    b.S[:a.t, :a.t] = a.S
    return b


def save(a, path):
    json.dump({"t": a.t, "m": a.m,
               "sigma": {"%d,%d" % k: list(v) for k, v in a.to_sigma().items()}},
              open(path, "w"))


def verify(a):
    """Independent check: build the fragment and test girth 5."""
    g = reduction.build_graph(a.t, a.to_sigma(), m=a.m)
    n_expected = 1 + a.t + a.t * a.m
    return (len(g) == n_expected and reduction.girth_at_least_5(g)), len(g)


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "involution"
    per_branch = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
    tries = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    budget = float(sys.argv[4]) if len(sys.argv) > 4 else 12000.0
    seed0 = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    target = int(sys.argv[6]) if len(sys.argv) > 6 else 57

    print("grow-and-repair, %s state space, %.0fs per branch, %d tries each"
          % (model, per_branch, tries), flush=True)
    end = time.time() + budget

    a = anneal_fast.FastAnneal(3, 56, seed=seed0, model=model)
    best, _ = a.run(10_000_000, t0=2.0, t1=0.02,
                    deadline=min(time.time() + per_branch, end))
    if best != 0:
        print("  could not even solve t=3", flush=True)
        return
    print("  t=3 solved", flush=True)

    while a.t < target and time.time() < end:
        placed = False
        # Escalating budgets: a long budget makes the cooling schedule sluggish,
        # so an easy branch that would fall in seconds instead burns the whole
        # allowance.  Try short and cheap first, lengthen only on failure.
        budgets = []
        b = max(10.0, per_branch / 32.0)
        while b < per_branch:
            budgets.append(b)
            b *= 3
        budgets.append(per_branch)
        attempts = [(bud, k) for bud in budgets for k in range(tries)]
        for (bud, k) in attempts:
            if time.time() > end:
                break
            cand = extend_state(a, seed=seed0 + 7919 * a.t + 31 * k + int(bud))
            t0 = time.time()
            c0 = cand.total_cost()
            best, it = cand.run(10_000_000, t0=1.2, t1=0.01,
                                deadline=min(time.time() + bud, end))
            el = time.time() - t0
            if best == 0:
                ok, n = verify(cand)
                print("  t=%-3d solved (%.0fs budget, try %d, cost %d->0, "
                      "%d moves, %.0fs) -- fragment %d vertices, girth>=5: %s"
                      % (cand.t, bud, k, c0, it, el, n, ok), flush=True)
                assert ok, "annealer produced an invalid structure"
                a = cand
                save(a, "grow_%s_t%d.json" % (model, a.t))
                placed = True
                break
            else:
                print("  t=%-3d %.0fs try %d: cost %d -> %d (%d moves, %.0fs)"
                      % (cand.t, bud, k, c0, best, it, el), flush=True)
        if not placed:
            print("  stalled at t=%d" % a.t, flush=True)
            break

    print("grow-and-repair frontier: t = %d of 57" % a.t, flush=True)


if __name__ == "__main__":
    main()
