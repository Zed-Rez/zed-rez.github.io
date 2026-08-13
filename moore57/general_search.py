"""
The general (non-cyclic) block search, and exact counts where it is possible.

This drops the cyclic ansatz entirely: sigma_ij ranges over all of S_{k-1}.
It is the honest search -- it can find every Moore graph of degree k, and for
k = 7 it does find Hoffman-Singleton, which the cyclic ansatz cannot (see
cyclic_search.py).

The search adds one block at a time.  With the gauge sigma_0j = identity, the
unknowns are sigma_ij for 1 <= i < j <= k-1, and adding block r costs r-1 new
permutations.  Immediately after choosing sigma_ir the newly determined
constraints are

    triangles      {h, i, r},  h < i                        ->  i    of them
    quadrilaterals {g, h, i, r},  g < h < i, 3 cyclic orders ->  3*C(i,2)

so the search is heavily pruned from the top.

Exact counts of valid t-block structures come out of the same DFS, and those
are the numbers that let us calibrate every heuristic in firstmoment.py.
"""

import sys
from itertools import combinations, permutations

from reduction import compose, inverse, is_derangement, identity


class GeneralSearch:
    """Permutations are handled as indices into a precomputed table: for
    m = 6 the full 720 x 720 composition table fits easily and turns every
    constraint check into a chain of list lookups."""

    def __init__(self, k, count_all=False, node_cap=None, depth_limit=None):
        self.k = k
        self.m = k - 1
        self.depth_limit = depth_limit if depth_limit is not None else k
        self.perms = list(permutations(range(self.m)))
        self.idx = {p: i for i, p in enumerate(self.perms)}
        self.ID = self.idx[identity(self.m)]
        self.COMP = [[self.idx[compose(p, q)] for q in self.perms]
                     for p in self.perms]
        self.INV = [self.idx[inverse(p)] for p in self.perms]
        self.DER = [is_derangement(p) for p in self.perms]
        self.derangements = [i for i, p in enumerate(self.perms)
                             if is_derangement(p)]
        self.count_all = count_all
        self.node_cap = node_cap
        self.nodes = 0
        self.solutions = 0
        self.level_counts = [0] * (k + 1)   # valid t-block structures
        self.s = {}                          # (i, j) -> permutation index
        self.first = None
        self.capped = False

    # -- table access -------------------------------------------------------
    def put(self, i, j, p):
        self.s[(i, j)] = p
        self.s[(j, i)] = self.INV[p]

    def drop(self, i, j):
        self.s.pop((i, j), None)
        self.s.pop((j, i), None)

    def walk(self, seq):
        """Composite permutation index around the closed walk seq."""
        s, C = self.s, self.COMP
        cur = self.ID
        for a, b in zip(seq, seq[1:] + seq[:1]):
            cur = C[s[(a, b)]][cur]
        return cur

    # -- constraint check ---------------------------------------------------
    def newly_ok(self, i, r):
        """Check the constraints that become determined when sigma_ir is set."""
        s, C, D = self.s, self.COMP, self.DER
        ir = s[(i, r)]
        for h in range(i):
            # walk h -> i -> r -> h
            if not D[C[s[(r, h)]][C[ir][s[(h, i)]]]]:
                return False
        for g, h in combinations(range(i), 2):
            gh, hg = s[(g, h)], s[(h, g)]
            gi, hi = s[(g, i)], s[(h, i)]
            rg, rh = s[(r, g)], s[(r, h)]
            # g -> h -> i -> r -> g
            if not D[C[rg][C[ir][C[hi][gh]]]]:
                return False
            # h -> g -> i -> r -> h
            if not D[C[rh][C[ir][C[gi][hg]]]]:
                return False
            # g -> i -> h -> r -> g   (uses sigma_hr, already set since h < i)
            if not D[C[rg][C[s[(h, r)]][C[s[(i, h)]][gi]]]]:
                return False
        return True

    # -- search -------------------------------------------------------------
    def run(self):
        for j in range(self.k):
            if j:
                self.put(0, j, self.ID)
        self.level_counts[2] += 1          # blocks 0,1 alone are always valid
        self._block(2)
        return self

    def _block(self, r):
        if r >= self.k:
            self.solutions += 1
            if self.first is None:
                self.first = dict(self.s)
            return not self.count_all
        if r >= self.depth_limit:
            return False        # counting only: do not descend past the limit
        return self._col(r, 1)

    def _col(self, r, i):
        if i == r:
            self.level_counts[r + 1] += 1
            if self.first is None and r + 1 == self.k:
                pass
            return self._block(r + 1)
        # sigma_{0,r} is the identity by the gauge, so the triangle {0,i,r}
        # forces sigma_ir itself to be a derangement -- start from that pool.
        pool = self.derangements if i >= 1 else self.perms
        for p in pool:
            self.nodes += 1
            if self.node_cap and self.nodes > self.node_cap:
                self.capped = True
                return True
            self.put(i, r, p)
            if self.newly_ok(i, r):
                if self._col(r, i + 1):
                    return True
        self.drop(i, r)
        return False


def report(k, count_all=False, node_cap=None, depth_limit=None):
    import reduction
    import time
    import firstmoment
    t0 = time.time()
    s = GeneralSearch(k, count_all=count_all, node_cap=node_cap,
                      depth_limit=depth_limit)
    s.run()
    el = time.time() - t0
    print("degree k = %d   (%d blocks of %d points; |S_%d| = %d, %d derangements)"
          % (k, k, k - 1, k - 1, len(s.perms), len(s.derangements)))
    print("  search nodes: %d%s   (%.1fs)"
          % (s.nodes, "  (CAPPED)" if s.capped else "", el))
    if count_all:
        logB, logq = firstmoment.model_params(k, cyclic=False)
        print("    %-6s %-16s %-16s %s"
              % ("blocks", "exact count", "first-moment", "ratio exact/pred"))
        for t in range(3, k + 1):
            if not s.level_counts[t]:
                continue
            pred = 10.0 ** firstmoment.cumulative_log10(k, t, cyclic=False)
            print("    t=%-4d %-16d %-16.4g %.4g"
                  % (t, s.level_counts[t], pred,
                     s.level_counts[t] / pred if pred else float("inf")))
        print("  complete solutions: %d" % s.solutions)
    if s.first is not None:
        sigma = {ij: s.perms[p] for ij, p in s.first.items()}
        g = reduction.build_graph(k, sigma)
        ok, msg = reduction.is_moore(g, k)
        print("  first solution rebuilds to: %s" % msg)
        assert ok
    else:
        print("  no complete solution found")
    return s


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "3"):
        report(3, count_all=True)
        print()
    if which in ("all", "7"):
        print("--- first complete solution (does the general search find "
              "Hoffman-Singleton?) ---")
        report(7, count_all=False)
        print()
        print("--- exact counts of valid t-block structures, t <= %s ---"
              % (sys.argv[2] if len(sys.argv) > 2 else "5"))
        report(7, count_all=True,
               depth_limit=int(sys.argv[2]) if len(sys.argv) > 2 else 5)
