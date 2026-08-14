"""
The 1-factorization model.

Gauge-fix sigma_0j = identity for every branch j.  Then, *unconditionally*, the
Latin property of each branch pair holds; and *if* the involution property
holds, the square of every pair is symmetric, which in this gauge says exactly:

    every sigma_ij with i, j >= 1 is a fixed-point-free involution of the 56
    points, and for each fixed i the family { sigma_ij : j != i } is a
    1-factorization of K_56.

Both statements are verified for Petersen and Hoffman-Singleton (see
`gauge_check()` below): after gauging, every one of Hoffman-Singleton's 15
bijections has cycle type (2,2,2), and each of its rows is a 1-factorization
of K_6.

This is a large reduction.  Each unknown drops from |S_56| = 56! ~ 10^74.9 to
the fixed-point-free involutions, 55!! ~ 10^36.9, and the row condition makes
the branches of a row an exact cover of the 1540 edges of K_56 by 55 perfect
matchings of 28 edges each -- 55 * 28 = 1540 exactly, so there is no slack at
all.

Adding branch t then has very strong propagation:

  * cell (i,x) cannot take value x                     (fixed-point-free)
  * cell (i,x) cannot take any value already used by row i    (disjointness)
  * for fixed x, the values p_i[x] are all different      (row t disjointness)
  * p_i is an involution                                  (AddInverse(p,p))
  * plus every triangle/quadrilateral disequality of the original model

CONDITIONAL.  This model is sound only if the involution property is a theorem
at degree 57.  It is verified at degrees 3 and 7 and conjectural at 57; the
caveat in README.md applies in full.  What is unconditional is that the model
contains both Moore graphs that exist, which `validate()` checks by
reconstructing Hoffman-Singleton from scratch inside it.
"""

import json
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

import reduction


class FactStructure:
    """Branches 0..t-1 with sigma_0j = id; sigma[(i,j)] for i,j >= 1."""

    def __init__(self, m):
        self.m = m
        self.t = 1
        self.sigma = {}

    def full(self, i, j):
        if i == j:
            return list(range(self.m))
        if i == 0 or j == 0:
            return list(range(self.m))          # gauge
        return self.sigma[(i, j)]

    def add_block(self, cols):
        """cols[i] = sigma_{i,t} for i = 1..t-1 (sigma_{0,t} is the gauge)."""
        t = self.t
        for i in range(1, t):
            self.sigma[(i, t)] = cols[i][:]
            self.sigma[(t, i)] = cols[i][:]     # involution: its own inverse
        self.t = t + 1

    def verify(self):
        m, t = self.m, self.t
        for i in range(1, t):
            for j in range(1, t):
                if i == j:
                    continue
                p = self.sigma[(i, j)]
                if sorted(p) != list(range(m)):
                    return False, "sigma_%d%d not a permutation" % (i, j)
                if any(p[p[x]] != x for x in range(m)):
                    return False, "sigma_%d%d not an involution" % (i, j)
                if any(p[x] == x for x in range(m)):
                    return False, "sigma_%d%d has a fixed point" % (i, j)
            # row disjointness
            seen = set()
            for j in range(1, t):
                if j == i:
                    continue
                p = self.sigma[(i, j)]
                for x in range(m):
                    if x >= p[x]:
                        continue                 # count each edge once
                    e = (x, p[x])
                    if e in seen:
                        return False, "row %d reuses edge %s" % (i, e)
                    seen.add(e)
        # the original derangement conditions, on all branches including 0
        for c in combinations(range(t), 3):
            i, j, l = c
            w = self._walk((i, j, l))
            if any(w[x] == x for x in range(m)):
                return False, "triangle %s" % (c,)
        for c in combinations(range(t), 4):
            i, j, l, r = c
            for seq in ((i, j, l, r), (i, j, r, l), (i, l, j, r)):
                w = self._walk(seq)
                if any(w[x] == x for x in range(m)):
                    return False, "quadrilateral %s" % (seq,)
        return True, "valid %d-branch 1-factorization structure" % t

    def _walk(self, seq):
        cur = list(range(self.m))
        for a, b in zip(seq, seq[1:] + seq[:1]):
            s = self.full(a, b)
            cur = [s[cur[x]] for x in range(self.m)]
        return cur

    def to_sigma(self):
        out = {}
        for i in range(self.t):
            for j in range(self.t):
                if i != j:
                    out[(i, j)] = tuple(self.full(i, j))
        return out


# --------------------------------------------------------------------------
# extension
# --------------------------------------------------------------------------

def extend(st, seconds=120.0, workers=4, seed=0, banned=()):
    m, t = st.m, st.t
    model = cp_model.CpModel()

    p = {}
    for i in range(1, t):
        row = [model.NewIntVar(0, m - 1, "p%d_%d" % (i, x)) for x in range(m)]
        model.AddInverse(row, row)                       # involution
        for x in range(m):
            model.Add(row[x] != x)                       # fixed-point-free
        # row i disjointness: the new matching avoids edges row i already uses
        for x in range(m):
            for j in range(1, t):
                if j == i:
                    continue
                model.Add(row[x] != st.sigma[(i, j)][x])
        p[i] = row

    # row t disjointness: for each x the values p_i[x] are pairwise different
    for x in range(m):
        if t > 2:
            model.AddAllDifferent([p[i][x] for i in range(1, t)])

    # The original derangement conditions, generated by exactly the same code
    # the (validated) general model uses: each is p_i[a] != p_j[b], with
    # branch 0's map being the identity.
    import general_extend
    shim = general_extend.Structure(m=m)
    shim.t = t
    shim.sigma = {(i, j): list(st.full(i, j))
                  for i in range(t) for j in range(t) if i != j}

    n_con = 0
    for (i, a, j, b) in general_extend.build_disequalities(shim):
        if i == 0 and j == 0:
            assert a != b, "the existing structure is already inconsistent"
            continue
        if i == 0:
            model.Add(p[j][b] != a)
        elif j == 0:
            model.Add(p[i][a] != b)
        else:
            model.Add(p[i][a] != p[j][b])
        n_con += 1

    for col in banned:
        lits = []
        for i in range(1, t):
            for x in range(m):
                bv = model.NewBoolVar("")
                model.Add(p[i][x] != col[i][x]).OnlyEnforceIf(bv)
                model.Add(p[i][x] == col[i][x]).OnlyEnforceIf(bv.Not())
                lits.append(bv)
        model.AddBoolOr(lits)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.randomize_search = True
    st_code = solver.Solve(model)
    name = solver.StatusName(st_code)
    if st_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {i: [solver.Value(p[i][x]) for x in range(m)]
                for i in range(1, t)}, name, n_con
    return None, name, n_con


def copy_of(st):
    new = FactStructure(st.m)
    new.t = st.t
    new.sigma = {k: v[:] for k, v in st.sigma.items()}
    return new


def grow(st, target, seconds=120.0, fanout=3, out=sys.stdout, save=None,
         workers=4, seed=0, deadline=None):
    best = [st.t, copy_of(st)]

    def dfs(cur, depth):
        if cur.t >= target:
            return cur
        if deadline and time.time() > deadline:
            return None
        banned = []
        for child in range(fanout):
            col, name, n_con = extend(cur, seconds=seconds, workers=workers,
                                      seed=seed + 1000 * depth + child,
                                      banned=banned)
            if col is None:
                if child == 0:
                    print("  %2d -> %2d : %s (%d conditions)"
                          % (cur.t, cur.t + 1, name, n_con), file=out, flush=True)
                return None
            banned.append(col)
            nxt = copy_of(cur)
            nxt.add_block(col)
            ok, msg = nxt.verify()
            if not ok:
                raise SystemExit("solver returned an invalid structure: " + msg)
            if nxt.t > best[0]:
                best[0], best[1] = nxt.t, copy_of(nxt)
                print("  %2d -> %2d : SOLVED -- %s" % (cur.t, nxt.t, msg),
                      file=out, flush=True)
                if save:
                    json.dump({"t": nxt.t, "m": nxt.m,
                               "sigma": {"%d,%d" % k: v
                                         for k, v in nxt.sigma.items()}},
                              open(save, "w"))
            got = dfs(nxt, depth + 1)
            if got is not None:
                return got
            if deadline and time.time() > deadline:
                return None
        return None

    got = dfs(st, 0)
    return (got, "COMPLETE") if got is not None else (best[1], "stalled")


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def gauge_check():
    """Confirm the model's premise on the graphs that exist."""
    from collections import Counter
    print("Premise check -- gauge sigma_0j = id, then look at sigma_ij, i,j>=1\n")
    for name, g, k in (("Petersen", reduction.petersen(), 3),
                       ("Hoffman-Singleton", reduction.hoffman_singleton(), 7)):
        m = k - 1
        idp = tuple(range(m))
        _, sig = reduction.decompose(g, sorted(g, key=repr)[0])

        def s(i, j):
            if i == j:
                return idp
            return sig[(i, j)] if (i, j) in sig else reduction.inverse(sig[(j, i)])

        G = {}
        for i in range(k):
            for j in range(k):
                if i != j:
                    G[(i, j)] = reduction.compose(
                        reduction.inverse(s(0, j)),
                        reduction.compose(s(i, j), s(0, i)))
        allinv = all(all(G[(i, j)][G[(i, j)][x]] == x and G[(i, j)][x] != x
                         for x in range(m))
                     for i, j in combinations(range(1, k), 2))
        ok1f = True
        for i in range(1, k):
            cov = Counter()
            for j in range(1, k):
                if j == i:
                    continue
                pp = G[(i, j)]
                for x in range(m):
                    if x < pp[x]:
                        cov[(x, pp[x])] += 1
            if set(cov.values()) != {1} or len(cov) != m * (m - 1) // 2:
                ok1f = False
        print("  %-18s all fixed-point-free involutions: %s;  every row a "
              "1-factorization of K_%d: %s" % (name, allinv, m, ok1f))
    print()


def validate(seconds=60.0):
    print("Validation -- rebuild Hoffman-Singleton inside the model\n")
    st = FactStructure(m=6)
    st.t = 2                                   # branches 0 and 1
    st, why = grow(st, target=7, seconds=seconds, fanout=6)
    print("  reached t = %d (%s)" % (st.t, why))
    if st.t == 7:
        g = reduction.build_graph(7, st.to_sigma(), m=6)
        ok, msg = reduction.is_moore(g, 7)
        print("  rebuilt: %s" % msg)
        return ok
    return False


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "validate"
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    budget = float(sys.argv[5]) if len(sys.argv) > 5 else 12000.0

    gauge_check()
    if mode == "validate":
        ok = validate(seconds=secs)
        print("\nmodel %s" % ("VALIDATED" if ok else "FAILED"))
        return
    st = FactStructure(m=56)
    st.t = 2
    print("Degree 57 in the 1-factorization model, %.0fs per branch\n" % secs,
          flush=True)
    st, why = grow(st, target=57, seconds=secs, fanout=3, workers=workers,
                   seed=seed, save="factorization_frontier.json",
                   deadline=time.time() + budget)
    print("frontier: t = %d of 57 (%s)" % (st.t, why), flush=True)


if __name__ == "__main__":
    main()
