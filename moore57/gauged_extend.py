"""
Incremental growth of the gauged matching structure at degree 57.

feasibility.py solves the gauged model monolithically and gets four branches;
five is undecided in fifteen minutes.  Growing one branch at a time is a much
smaller problem: adding branch t to a valid t-branch structure introduces only
t-1 new matchings, and every condition not involving t is already satisfied.

New unknowns:  M_it  for i = 1..t-1  (perfect matchings on the 56 points).
New conditions:
  * each M_it is a fixed-point-free involution;
  * row disjointness at branch i: M_it disjoint from every existing M_ij;
  * row disjointness at branch t: the M_it are pairwise disjoint;
  * triangles {i,j,t}: M_it . M_jt . M_ij  fixed-point-free and involutive
    (note M_ti = M_it, since the matchings are symmetric);
  * quadrilaterals {i,j,l,t}: fixed-point-free.

As in involution_search.py, this assumes the involution property, which is
verified at degrees 3 and 7 and conjectural at 57.  Anything it produces is
checked as an actual graph before being believed.
"""

import json
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

import reduction

M_SIZE = 56


class Gauged:
    """A gauged structure on branches 0..t-1: M[(i,j)] for 1 <= i < j <= t-1,
    with sigma_0j the identity."""

    def __init__(self, m=M_SIZE):
        self.m = m
        self.t = 2                      # branches 0 and 1, nothing to choose
        self.M = {}

    @classmethod
    def load(cls, path, m=M_SIZE):
        d = json.load(open(path))
        s = cls(m=d.get("m", m))
        s.t = d["t"]
        for key, v in d["M"].items():
            i, j = (int(q) for q in key.split(","))
            s.M[(i, j)] = v
            s.M[(j, i)] = v
        return s

    def save(self, path):
        json.dump({"k": 57, "t": self.t, "m": self.m,
                   "M": {"%d,%d" % (i, j): self.M[(i, j)]
                         for i, j in combinations(range(1, self.t), 2)}},
                  open(path, "w"))

    def to_sigma(self):
        ident = tuple(range(self.m))
        sigma = {(0, j): ident for j in range(1, self.t)}
        for i, j in combinations(range(1, self.t), 2):
            sigma[(i, j)] = tuple(self.M[(i, j)])
        return sigma

    def verify(self):
        sigma = self.to_sigma()
        return reduction.sigma_conditions_hold(self.t, sigma, m=self.m)

    def add(self, cols):
        """cols[i] = M_it for i = 1..t-1."""
        t = self.t
        for i in range(1, t):
            self.M[(i, t)] = cols[i][:]
            self.M[(t, i)] = cols[i][:]
        self.t = t + 1


def extend(st, seconds=600.0, workers=4, seed=0, log=False, banned=()):
    t, m = st.t, st.m
    model = cp_model.CpModel()

    new = {}
    for i in range(1, t):
        row = [model.NewIntVar(0, m - 1, "N%d_%d" % (i, x)) for x in range(m)]
        model.AddInverse(row, row)                 # involution
        for x in range(m):
            model.Add(row[x] != x)                 # fixed-point-free
        new[i] = row

    n_dis = n_el = 0

    # row disjointness at each existing branch i, against its existing matchings
    for i in range(1, t):
        for j in range(1, t):
            if j == i:
                continue
            ex = st.M[(i, j)]
            for x in range(m):
                model.Add(new[i][x] != ex[x])
                n_dis += 1
    # row disjointness at the new branch t
    for i, j in combinations(range(1, t), 2):
        for x in range(m):
            model.Add(new[i][x] != new[j][x])
            n_dis += 1

    def elem(arr, idx):
        out = model.NewIntVar(0, m - 1, "")
        model.AddElement(idx, arr, out)
        return out

    # triangles {i, j, t}: M_it . M_jt . M_ij   (both orientations)
    for i, j in combinations(range(1, t), 2):
        for a, b in ((i, j), (j, i)):
            base = st.M[(a, b)]
            tau = []
            for x in range(m):
                y = base[x]                        # constant index
                z = elem(new[b], y)                # M_bt[y]
                w = elem(new[a], z)                # M_at[z]
                n_el += 2
                tau.append(w)
            for x in range(m):
                model.Add(tau[x] != x)
            model.AddInverse(tau, tau)

    # quadrilaterals {i, j, l, t}
    for i, j, l in combinations(range(1, t), 3):
        for p, q, u in ((i, j, l), (i, l, j), (j, i, l)):
            # cycle p -> q -> u -> t -> p  : M_pt . M_ut . M_qu . M_pq
            for x in range(m):
                y = st.M[(p, q)][x]
                z = st.M[(q, u)][y]                # both constant
                zz = elem(new[u], z)
                ww = elem(new[p], zz)
                n_el += 2
                model.Add(ww != x)

    for col in banned:
        lits = []
        for i in range(1, t):
            for x in range(m):
                bv = model.NewBoolVar("")
                model.Add(new[i][x] != col[i][x]).OnlyEnforceIf(bv)
                model.Add(new[i][x] == col[i][x]).OnlyEnforceIf(bv.Not())
                lits.append(bv)
        model.AddBoolOr(lits)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.randomize_search = True
    solver.parameters.log_search_progress = log
    status = solver.Solve(model)
    name = solver.StatusName(status)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        cols = {i: [solver.Value(v) for v in new[i]] for i in range(1, t)}
        return cols, name, (n_dis, n_el)
    return None, name, (n_dis, n_el)


def main():
    seed_path = sys.argv[1] if len(sys.argv) > 1 else "gauged57_t4.json"
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 600.0
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    target = int(sys.argv[4]) if len(sys.argv) > 4 else 57

    st = Gauged.load(seed_path)
    print("seed: %d branches, valid: %s" % (st.t, st.verify()), flush=True)

    while st.t < target:
        t0 = time.time()
        cols, name, (nd, ne) = extend(st, seconds=secs, workers=workers,
                                      seed=st.t * 17)
        el = time.time() - t0
        if cols is None:
            print("  %2d -> %2d : %-11s in %5.0fs  (%d diseq, %d element)"
                  % (st.t, st.t + 1, name, el, nd, ne), flush=True)
            if name == "INFEASIBLE":
                print("     this structure admits no extension; a restart or"
                      " backtrack is needed", flush=True)
            break
        st.add(cols)
        ok = st.verify()
        print("  %2d -> %2d : SOLVED in %5.0fs  (%d diseq, %d element) -- "
              "derangement conditions %s" % (st.t - 1, st.t, el, nd, ne, ok),
              flush=True)
        if not ok:
            raise SystemExit("solver returned an invalid structure")
        st.save("gauged57_t%d.json" % st.t)

    sigma = st.to_sigma()
    g = reduction.build_graph(st.t, sigma, m=st.m)
    print("frontier: %d of 57 branches, %d vertices, girth>=5 %s"
          % (st.t, len(g), reduction.girth_at_least_5(g)), flush=True)
    if st.t == 57:
        ok, msg = reduction.is_moore(g, 57)
        print("rebuilt: %s" % msg, flush=True)
        if ok:
            print("\n  *** A MOORE GRAPH OF DEGREE 57 ***", flush=True)


if __name__ == "__main__":
    main()
