"""
Local search for the branch-extension problem.

Pass 7 showed that adding a branch is a colouring problem with no local
obstruction: 1008 cells, a 361-regular conflict graph, 56 values, every row a
permutation and every colour class a transversal.  CP-SAT returns UNKNOWN on
it, which is unsurprising -- dense equitable-colouring and quasigroup-completion
problems are classically much better served by local search than by systematic
search.

State      : one permutation p_i of the 56 values per row i = 1..t-1
             (row 0 is the identity, fixed by the gauge).
Cost       : number of violated constraints.
             Constraints touching row 0 become unary (a forbidden value for a
             cell); the rest are binary disequalities p_i[a] != p_j[b].
Move       : swap p_i[a] and p_i[b] -- this keeps every row a permutation, so
             the search never leaves the feasible region of the row structure
             and only has to fight the cross-row conflicts.

That move set is the reason this can work where CP-SAT stalls: the permutation
structure is maintained by construction rather than propagated.
"""

import json
import math
import random
import sys
import time

import general_extend
from general_extend import Structure


class Extension:
    def __init__(self, st):
        self.st = st
        self.t, self.m = st.t, st.m
        rows = range(1, self.t)
        self.rows = list(rows)
        self.ncell = (self.t - 1) * self.m

        # cell (i, x) -> flat index
        self.flat = {(i, x): (i - 1) * self.m + x
                     for i in rows for x in range(self.m)}

        self.unary = [set() for _ in range(self.ncell)]
        adj = [[] for _ in range(self.ncell)]
        for (i, a, j, b) in general_extend.build_disequalities(st):
            if i == 0 and j == 0:
                continue
            if i == 0:                      # p_0[a] = a is a constant
                self.unary[self.flat[(j, b)]].add(a)
            elif j == 0:
                self.unary[self.flat[(i, a)]].add(b)
            else:
                u, v = self.flat[(i, a)], self.flat[(j, b)]
                adj[u].append(v)
                adj[v].append(u)
        self.adj = [tuple(x) for x in adj]
        self.n_binary = sum(len(x) for x in adj) // 2
        self.n_unary = sum(len(u) for u in self.unary)

    # -- state helpers ------------------------------------------------------
    def random_state(self, rng):
        val = [0] * self.ncell
        for i in self.rows:
            perm = list(range(self.m))
            rng.shuffle(perm)
            for x in range(self.m):
                val[self.flat[(i, x)]] = perm[x]
        return val

    def cell_cost(self, val, c):
        v = val[c]
        cost = 1 if v in self.unary[c] else 0
        for d in self.adj[c]:
            if val[d] == v:
                cost += 1
        return cost

    def total_cost(self, val):
        tot = 0
        for c in range(self.ncell):
            v = val[c]
            if v in self.unary[c]:
                tot += 1
            for d in self.adj[c]:
                if val[d] == v:
                    tot += 1
        return tot // 1 - sum(
            1 for c in range(self.ncell) for d in self.adj[c]
            if val[d] == val[c]) // 2

    def cost(self, val):
        """Violations: unary + binary (each binary counted once)."""
        u = sum(1 for c in range(self.ncell) if val[c] in self.unary[c])
        b = 0
        for c in range(self.ncell):
            v = val[c]
            for d in self.adj[c]:
                if d > c and val[d] == v:
                    b += 1
        return u + b

    def swap_delta(self, val, c, d):
        """Change in cost from swapping the values of cells c and d
        (which must be in the same row)."""
        before = self.cell_cost(val, c) + self.cell_cost(val, d)
        # c and d are in the same row so they are never adjacent; no
        # double-counting correction is needed
        val[c], val[d] = val[d], val[c]
        after = self.cell_cost(val, c) + self.cell_cost(val, d)
        val[c], val[d] = val[d], val[c]
        return after - before

    # -- the search ---------------------------------------------------------
    def violated_cells(self, val):
        out = []
        for c in range(self.ncell):
            if self.cell_cost(val, c):
                out.append(c)
        return out

    def anneal(self, seconds=600.0, seed=0, t0=1.5, t1=0.01, report=None,
               targeted=True):
        """Simulated annealing over row-swaps.

        The move is biased towards cells that are actually in conflict: pick a
        violated cell, then a random partner in its own row.  For colouring
        problems that focus is worth far more than raw move throughput."""
        rng = random.Random(seed)
        val = self.random_state(rng)
        cur = self.cost(val)
        best, best_val = cur, val[:]
        start = time.time()
        it = 0
        m = self.m
        bad = self.violated_cells(val)
        refresh = 0
        while True:
            elapsed = time.time() - start
            if elapsed > seconds or best == 0:
                break
            frac = elapsed / seconds
            temp = t0 * (t1 / t0) ** frac
            for _ in range(2000):
                it += 1
                if targeted and bad:
                    c = bad[rng.randrange(len(bad))]
                    i = c // m + 1
                    b = rng.randrange(m)
                    d = self.flat[(i, b)]
                    if c == d:
                        continue
                else:
                    i = self.rows[rng.randrange(len(self.rows))]
                    a, b = rng.randrange(m), rng.randrange(m)
                    if a == b:
                        continue
                    c, d = self.flat[(i, a)], self.flat[(i, b)]
                delta = self.swap_delta(val, c, d)
                if delta <= 0 or rng.random() < math.exp(-delta / temp):
                    val[c], val[d] = val[d], val[c]
                    cur += delta
                    if cur < best:
                        best, best_val = cur, val[:]
                        if best == 0:
                            break
            refresh += 1
            if targeted and refresh % 3 == 0:
                bad = self.violated_cells(val)
            if report and it % 400000 < 2000:
                report(elapsed, cur, best)
        return best, best_val, it

    def to_columns(self, val):
        return {i: [val[self.flat[(i, x)]] for x in range(self.m)]
                for i in self.rows}


def load(path):
    if path == "t19":
        d = json.load(open("t19_cyclic.json"))
        return Structure.from_cyclic(d["labelling"])
    d = json.load(open(path))
    st = Structure(m=d["m"])
    st.t = d["t"]
    for key, v in d["sigma"].items():
        i, j = (int(q) for q in key.split(","))
        st.sigma[(i, j)] = v
    return st


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "t19"
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 600.0
    restarts = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    target = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    st = load(src)
    ok, msg = st.verify()
    print("structure: %s" % msg, flush=True)
    assert ok

    while True:
        ext = Extension(st)
        print("\nextending to branch %d: %d cells, %d binary + %d unary "
              "constraints" % (st.t, ext.ncell, ext.n_binary, ext.n_unary),
              flush=True)
        solved = False
        for r in range(restarts):
            def rep(el, cur, best, r=r):
                print("    run %d  %5.0fs  current %6d  best %6d"
                      % (r, el, cur, best), flush=True)
            t0 = time.time()
            best, val, it = ext.anneal(seconds=secs, seed=1000 * st.t + r,
                                       report=rep)
            print("  run %d: best cost %d after %d moves (%.0fs)"
                  % (r, best, it, time.time() - t0), flush=True)
            if best == 0:
                cols = ext.to_columns(val)
                cols[0] = list(range(ext.m))       # the gauge
                st.add_block([cols[i] for i in range(st.t)])
                good, msg = st.verify()
                print("  EXTENDED to %d branches -- verified: %s"
                      % (st.t, good), flush=True)
                assert good, msg
                st_path = "anneal_t%d.json" % st.t
                json.dump({"t": st.t, "m": st.m,
                           "sigma": {"%d,%d" % k: v
                                     for k, v in st.sigma.items()}},
                          open(st_path, "w"))
                solved = True
                break
        if not solved:
            print("\nfrontier: %d branches (no extension found)" % st.t,
                  flush=True)
            return
        if target and st.t >= target:
            print("\nreached %d branches" % st.t, flush=True)
            return


if __name__ == "__main__":
    main()
