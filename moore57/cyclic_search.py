"""
The cyclic ansatz, and how far it binds the problem.

Following reduction.py, a Moore graph of degree k is an edge-labelling of K_k
by permutations sigma_ij of a (k-1)-set whose products around 3-cycles and
4-cycles are derangements.  The standard way to make that tractable is to
insist that every sigma_ij lie in one fixed cyclic group C of order k-1 acting
regularly on the block, i.e.

        sigma_ij = c^{a_ij},        a_ij in Z_{k-1},   a_ji = -a_ij.

An element of a regular cyclic group is a derangement iff it is not the
identity, so in this ansatz the whole problem collapses to arithmetic in
Z_{k-1}: find an antisymmetric labelling a of K_t with

        a_ij + a_jl + a_li          != 0   (all distinct i, j, l)
        a_ij + a_jl + a_lm + a_mi   != 0   (all distinct i, j, l, m)

and t = k is a Moore graph.  A partial solution with t < k is what the
literature calls a "t-subgraph": the first t branches of the rooted tree.

Gauge freedom: replacing a_ij by a_ij + b_j - b_i (relabel block i by c^{b_i})
preserves every constraint, so we may set a_0j = 0 for all j.

Note what the ansatz really assumes.  If all sigma_ij lie in a common regular
*abelian* group, then acting by c on every block is an automorphism of the
whole graph, of order k-1, fixing the root and all k of its neighbours.  So the
cyclic ansatz is not merely a convenience: it assumes the graph has an
automorphism of order k-1 with 1 + k fixed points.  This module measures the
cost of that assumption where the answer is known.
"""

import sys
from itertools import combinations


# --------------------------------------------------------------------------
# exhaustive incremental search over Z_m
# --------------------------------------------------------------------------

class CyclicSearch:
    """Exhaustive search for antisymmetric Z_m-labellings of K_t with no
    vanishing 3-sum or 4-sum, built up one vertex at a time."""

    def __init__(self, m, t):
        self.m = m
        self.t = t
        self.a = [[0] * t for _ in range(t)]   # a[i][j]
        self.nodes = 0

    def _set(self, i, j, val):
        self.a[i][j] = val % self.m
        self.a[j][i] = (-val) % self.m

    def _ok(self, r):
        """Check every constraint that involves vertex r, given that vertices
        0..r are all assigned."""
        a, m = self.a, self.m
        rng = range(r)
        for i, j in combinations(rng, 2):
            if (a[i][j] + a[j][r] + a[r][i]) % m == 0:
                return False
        for i, j, l in combinations(rng, 3):
            if (a[i][j] + a[j][l] + a[l][r] + a[r][i]) % m == 0:
                return False
            if (a[i][j] + a[j][r] + a[r][l] + a[l][i]) % m == 0:
                return False
            if (a[i][l] + a[l][j] + a[j][r] + a[r][i]) % m == 0:
                return False
        return True

    def _partial_ok(self, r, upto):
        """Constraints fully determined by the entries a[0..upto][r] chosen so
        far, used for pruning mid-vertex."""
        a, m = self.a, self.m
        rng = range(upto + 1)
        for i in rng:
            if i != upto and (a[i][upto] + a[upto][r] + a[r][i]) % m == 0:
                return False
        for i, j in combinations(rng, 2):
            if upto not in (i, j):
                continue
            for l in rng:
                if l in (i, j):
                    continue
                if (a[i][j] + a[j][l] + a[l][r] + a[r][i]) % m == 0:
                    return False
                if (a[i][j] + a[j][r] + a[r][l] + a[l][i]) % m == 0:
                    return False
                if (a[i][l] + a[l][j] + a[j][r] + a[r][i]) % m == 0:
                    return False
        return True

    def solve(self, r=2, best=None):
        """Assign vertices r, r+1, ..., t-1.  Vertices 0 and 1 need nothing:
        a[0][1] = 0 by the gauge.  Returns the labelling or None."""
        if r == self.t:
            return [row[:] for row in self.a]
        # choose a[1][r], ..., a[r-1][r];  a[0][r] = 0 by the gauge
        return self._assign(r, 1, best)

    def _assign(self, r, i, best):
        if i == r:
            if not self._ok(r):
                return None
            return self.solve(r + 1, best)
        for val in range(self.m):
            self.nodes += 1
            self._set(i, r, val)
            if self._partial_ok(r, i):
                got = self._assign(r, i + 1, best)
                if got is not None:
                    return got
        self._set(i, r, 0)
        return None


def max_t_exhaustive(m, tcap=40, verbose=True):
    """Largest t for which a cyclic t-subgraph over Z_m exists (exhaustive)."""
    best = 1
    for t in range(2, tcap + 1):
        s = CyclicSearch(m, t)
        sol = s.solve()
        if verbose:
            print("    m=%2d  t=%2d  %-8s (%d search nodes)"
                  % (m, t, "OK" if sol else "IMPOSSIBLE", s.nodes))
        if sol is None:
            return best, t
        best = t
    return best, None


# --------------------------------------------------------------------------
# CP-SAT model for the sizes where exhaustive search is hopeless
# --------------------------------------------------------------------------

def cpsat_t_subgraph(m, t, seconds=60.0, workers=4, log=False, hint=None):
    """Try to find a cyclic t-subgraph over Z_m with CP-SAT.
    Returns (status_name, labelling or None)."""
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    a = {}
    for i in range(t):
        for j in range(i + 1, t):
            if i == 0:
                v = model.NewConstant(0)          # gauge
            else:
                v = model.NewIntVar(1, m - 1, "a_%d_%d" % (i, j))
            a[(i, j)] = v
            a[(j, i)] = None                      # filled below

    def lin(i, j):
        """a_ij as a linear expression (a_ji = -a_ij)."""
        return a[(i, j)] if i < j else -a[(j, i)]

    def forbid_zero_mod(exprs, lo, hi):
        s = model.NewIntVar(lo, hi, "")
        model.Add(s == sum(exprs))
        k = lo // m
        while k * m <= hi:
            if lo <= k * m <= hi:
                model.Add(s != k * m)
            k += 1

    n3 = n4 = 0
    for i, j, l in combinations(range(t), 3):
        forbid_zero_mod([lin(i, j), lin(j, l), lin(l, i)], -3 * m, 3 * m)
        n3 += 1
    for i, j, l, r in combinations(range(t), 4):
        for cyc in ((i, j, l, r), (i, j, r, l), (i, l, j, r)):
            p, q, u, w = cyc
            forbid_zero_mod([lin(p, q), lin(q, u), lin(u, w), lin(w, p)],
                            -4 * m, 4 * m)
            n4 += 1

    # symmetry breaking: the gauge is already fixed; a global unit multiplier
    # u in Z_m^* still acts, so we may bound the first free label.
    if t >= 3:
        model.Add(a[(1, 2)] <= m // 2)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.log_search_progress = log
    if hint:
        for (i, j), val in hint.items():
            if i < j and i != 0:
                model.AddHint(a[(i, j)], val)
    status = solver.Solve(model)
    name = solver.StatusName(status)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        out = {}
        for i in range(t):
            for j in range(i + 1, t):
                out[(i, j)] = solver.Value(a[(i, j)])
        return name, out, (n3, n4)
    return name, None, (n3, n4)


# --------------------------------------------------------------------------
# turning a cyclic labelling back into a graph, to check it end to end
# --------------------------------------------------------------------------

def labelling_to_sigma(m, t, a):
    """Convert a Z_m labelling into a sigma table over the regular cyclic
    group, as consumed by reduction.build_graph."""
    sigma = {}
    for i in range(t):
        for j in range(i + 1, t):
            val = a[i][j] if isinstance(a, list) else a[(i, j)]
            sigma[(i, j)] = tuple((x + val) % m for x in range(m))
    return sigma


def main():
    import reduction

    print("Calibration: does the cyclic ansatz find the Moore graphs that "
          "actually exist?\n")

    for k in (3, 7):
        m = k - 1
        print("  degree k=%d  (blocks of size %d, group Z_%d), need t=%d:"
              % (k, m, m, k))
        best, failed_at = max_t_exhaustive(m, tcap=k + 1)
        verdict = ("FINDS IT" if best >= k else
                   "MISSES IT -- stalls at t=%d of %d" % (best, k))
        print("    -> cyclic ansatz %s\n" % verdict)

        if best >= k:
            s = CyclicSearch(m, k)
            sol = s.solve()
            sigma = labelling_to_sigma(m, k, sol)
            g = reduction.build_graph(k, sigma)
            print("    reconstructed graph:", reduction.is_moore(g, k)[1], "\n")

    print("Now degree 57 (blocks of size 56, group Z_56), need t=57.")
    print("Exhaustive search is hopeless here; using CP-SAT.\n")
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    for t in (10, 15, 18, 20, 21, 22):
        name, sol, (n3, n4) = cpsat_t_subgraph(56, t, seconds=secs)
        print("    t=%2d  %-14s  (%d triangle + %d quadrilateral constraints)"
              % (t, name, n3, n4))
        if sol is not None:
            aa = [[0] * t for _ in range(t)]
            for (i, j), v in sol.items():
                aa[i][j], aa[j][i] = v, (-v) % 56
            sigma = labelling_to_sigma(56, t, aa)
            assert verify_partial(56, t, aa), "solver returned an invalid labelling"


def verify_partial(m, t, a):
    for i, j, l in combinations(range(t), 3):
        if (a[i][j] + a[j][l] + a[l][i]) % m == 0:
            return False
    for i, j, l, r in combinations(range(t), 4):
        for p, q, u, w in ((i, j, l, r), (i, j, r, l), (i, l, j, r)):
            if (a[p][q] + a[q][u] + a[u][w] + a[w][p]) % m == 0:
                return False
    return True


if __name__ == "__main__":
    main()
