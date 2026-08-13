"""
Growing the structure with UNRESTRICTED permutations.

Everything published on the degree-57 t-subgraph frontier assumes the
bijections lie in one cyclic group.  cyclic_search.py shows that ansatz is a
dead end: it cannot even produce Hoffman-Singleton.  This module drops it.

The reason a general search looked hopeless is that the constraints are
conditions on *compositions* of unknown permutations.  But when a single new
block r is added to an existing structure on blocks 0..r-1, every constraint
becomes a binary disequality between two cells of the unknowns.  Write

        p_i := sigma_{i,r}        (the unknown, for i = 1..r-1)
        p_0 := identity           (the gauge)

Then the walk h -> i -> r -> h is a derangement iff

        sigma_{r,h}(sigma_{i,r}(sigma_{h,i}(x))) != x    for all x

and applying sigma_{h,r} to both sides turns it into

        p_i[ sigma_{h,i}(x) ]  !=  p_h[ x ]

where sigma_{h,i} is already known, so the index is a *constant*.  The same
happens for the three cyclic orders of each quadrilateral.  So adding a block
is exactly a list-colouring problem:

    variables : the (r-1) * 56 cells p_i[x],  domain {0..55}
    constraints: each row is a permutation (all-different), plus
                 C(r,2)*56 + 3*C(r,3)*56 binary disequalities between cells.

That is a shape CP-SAT is good at, and it is fully general -- no group
assumption anywhere.
"""

import json
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

M = 56                                   # block size for degree 57


# --------------------------------------------------------------------------
# permutation helpers on lists
# --------------------------------------------------------------------------

def inv(p):
    out = [0] * len(p)
    for x, y in enumerate(p):
        out[y] = x
    return out


class Structure:
    """A valid t-block structure: sigma[(i,j)] for all ordered pairs i != j."""

    def __init__(self, m=M):
        self.m = m
        self.t = 1
        self.sigma = {}

    @classmethod
    def from_cyclic(cls, labelling, m=M):
        s = cls(m)
        t = len(labelling)
        for i in range(t):
            for j in range(t):
                if i != j:
                    a = labelling[i][j] % m
                    s.sigma[(i, j)] = [(x + a) % m for x in range(m)]
        s.t = t
        return s

    def seed_two(self):
        """Blocks 0 and 1 joined by the identity (the gauge)."""
        idp = list(range(self.m))
        self.sigma[(0, 1)] = idp[:]
        self.sigma[(1, 0)] = idp[:]
        self.t = 2

    def add_block(self, column):
        """column[i] = sigma_{i,t} for i = 0..t-1."""
        t = self.t
        for i in range(t):
            self.sigma[(i, t)] = column[i][:]
            self.sigma[(t, i)] = inv(column[i])
        self.t = t + 1

    # -- verification ------------------------------------------------------
    def walk(self, seq):
        m = self.m
        cur = list(range(m))
        for a, b in zip(seq, seq[1:] + seq[:1]):
            s = self.sigma[(a, b)]
            cur = [s[cur[x]] for x in range(m)]
        return cur

    def verify(self):
        t = self.t
        for i, j in combinations(range(t), 2):
            if sorted(self.sigma[(i, j)]) != list(range(self.m)):
                return False, "sigma_%d%d is not a permutation" % (i, j)
            if any(self.sigma[(j, i)][self.sigma[(i, j)][x]] != x
                   for x in range(self.m)):
                return False, "sigma_%d%d is not the inverse of sigma_%d%d" % (j, i, i, j)
        for c in combinations(range(t), 3):
            i, j, l = c
            for seq in ((i, j, l),):
                w = self.walk(seq)
                if any(w[x] == x for x in range(self.m)):
                    return False, "triangle %s has a fixed point" % (seq,)
        for c in combinations(range(t), 4):
            i, j, l, r = c
            for seq in ((i, j, l, r), (i, j, r, l), (i, l, j, r)):
                w = self.walk(seq)
                if any(w[x] == x for x in range(self.m)):
                    return False, "quadrilateral %s has a fixed point" % (seq,)
        return True, "valid %d-block structure" % t


# --------------------------------------------------------------------------
# the extension model
# --------------------------------------------------------------------------

def build_disequalities(st):
    """All binary disequalities (i, a, j, b) meaning p_i[a] != p_j[b], for the
    extension of the structure ``st`` by one block."""
    t, sg = st.t, st.sigma
    out = []
    # triangles {h, i, r}
    for h, i in combinations(range(t), 2):
        s_hi = sg[(h, i)]
        for x in range(st.m):
            out.append((i, s_hi[x], h, x))
    # quadrilaterals {g, h, i, r}, three cyclic orders
    for g, h, i in combinations(range(t), 3):
        s_gh, s_hi = sg[(g, h)], sg[(h, i)]
        s_hg, s_gi = sg[(h, g)], sg[(g, i)]
        s_ih = sg[(i, h)]
        for x in range(st.m):
            out.append((i, s_hi[s_gh[x]], g, x))
            out.append((i, s_gi[s_hg[x]], h, x))
            out.append((h, s_ih[s_gi[x]], g, x))
    return out


def extend(st, seconds=120.0, workers=4, seed=0, log=False):
    """Try to add one block using arbitrary permutations.  Returns the new
    column (a list of t permutations) or None."""
    t, m = st.t, st.m
    model = cp_model.CpModel()

    # p[0] is the identity by the gauge; p[1..t-1] are unknown permutations
    p = {}
    for x in range(m):
        p[(0, x)] = model.NewConstant(x)
    for i in range(1, t):
        row = [model.NewIntVar(0, m - 1, "p%d_%d" % (i, x)) for x in range(m)]
        model.AddAllDifferent(row)
        for x in range(m):
            p[(i, x)] = row[x]

    n_con = 0
    for (i, a, j, b) in build_disequalities(st):
        if i == 0 and j == 0:
            assert a != b, "the existing structure is already inconsistent"
            continue
        if i == 0:
            model.Add(p[(j, b)] != a)
        elif j == 0:
            model.Add(p[(i, a)] != b)
        else:
            model.Add(p[(i, a)] != p[(j, b)])
        n_con += 1

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.randomize_search = True
    solver.parameters.log_search_progress = log
    status = solver.Solve(model)
    name = solver.StatusName(status)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        col = [[solver.Value(p[(i, x)]) for x in range(m)] for i in range(t)]
        return col, name, n_con
    return None, name, n_con


def grow(st, target=57, seconds=120.0, out=sys.stdout, save=None, workers=4,
         seed=0):
    while st.t < target:
        t0 = time.time()
        col, name, n_con = extend(st, seconds=seconds, workers=workers,
                                  seed=seed + st.t)
        el = time.time() - t0
        if col is None:
            print("  blocks %2d -> %2d : %s after %.0fs (%d disequalities)"
                  % (st.t, st.t + 1, name, el, n_con), file=out, flush=True)
            return st, name
        st.add_block(col)
        ok, msg = st.verify()
        print("  blocks %2d -> %2d : SOLVED in %.0fs (%d disequalities) -- %s"
              % (st.t - 1, st.t, el, n_con, msg), file=out, flush=True)
        if not ok:
            raise SystemExit("solver returned an invalid structure: " + msg)
        if save:
            json.dump({"t": st.t, "m": st.m,
                       "sigma": {"%d,%d" % k: v for k, v in st.sigma.items()}},
                      open(save, "w"))
    return st, "COMPLETE"


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "scratch"
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    if mode == "seeded":
        data = json.load(open("t19_cyclic.json"))
        st = Structure.from_cyclic(data["labelling"])
        ok, msg = st.verify()
        print("seed from the cyclic certificate: %s" % msg, flush=True)
        assert ok
        save = "general_frontier_seeded.json"
    else:
        st = Structure()
        st.seed_two()
        save = "general_frontier.json"

    print("growing with UNRESTRICTED permutations, %.0fs per block" % secs,
          flush=True)
    st, why = grow(st, seconds=secs, save=save, workers=workers, seed=seed)
    print("frontier: t = %d blocks of 57  (%s)" % (st.t, why), flush=True)
    ok, msg = st.verify()
    print("final check: %s" % msg, flush=True)


if __name__ == "__main__":
    main()
