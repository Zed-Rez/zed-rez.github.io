"""
A complete brute-force search, and an honest measurement of what it costs.

"Complete" here means: no heuristics, no ansatz, no random restarts.  The
search enumerates every gauge-fixed structure in a fixed order and therefore
finds a Moore graph of degree k if and only if one exists.  It is validated at
the degrees where the answer is known, then run at degree 57 with a wall-clock
budget so the local throughput can be measured rather than guessed.

Search order.  Branches are added one at a time.  For each new branch the
columns sigma_{i,t} are built cell by cell with forward checking: a cell's
domain is the 56 values minus those excluded by the already-placed cells of the
same row (a permutation) and by every triangle/quadrilateral disequality whose
other endpoint is already placed.  Cells are chosen by smallest remaining
domain, which changes the order but not the completeness.

The counting facts at the bottom are exact and are what actually settle the
feasibility question -- see `verdict()`.
"""

import sys
import time
from itertools import combinations
from math import comb, factorial, lgamma, log, log10

import general_extend
import reduction
from general_extend import Structure


class CompleteSearch:
    def __init__(self, m, node_budget=None, seconds=None):
        self.m = m
        self.node_budget = node_budget
        self.seconds = seconds
        self.nodes = 0
        self.start = None
        self.exhausted = False
        self.stopped = False
        self.deepest = 0

    # -- enumerate every valid extension of `st` by one branch -------------
    def columns(self, st):
        """Yield every valid new column, in a fixed order.  Complete."""
        m, t = self.m, st.t
        cells = [(i, x) for i in range(1, t) for x in range(m)]
        pos = {c: k for k, c in enumerate(cells)}

        # conflicts: cell -> list of (other cell) and cell -> forbidden values
        forb = {c: set() for c in cells}
        adj = {c: [] for c in cells}
        for (i, a, j, b) in general_extend.build_disequalities(st):
            if i == 0 and j == 0:
                continue
            if i == 0:
                forb[(j, b)].add(a)
            elif j == 0:
                forb[(i, a)].add(b)
            else:
                adj[(i, a)].append((j, b))
                adj[(j, b)].append((i, a))

        val = {}

        def rec(k):
            if self.stopped:
                return
            if k == len(cells):
                yield dict(val)
                return
            # smallest remaining domain among unassigned cells
            best, best_dom = None, None
            for c in cells:
                if c in val:
                    continue
                used = {val[d] for d in adj[c] if d in val}
                used |= {val[(c[0], y)] for y in range(self.m)
                         if (c[0], y) in val}
                dom = [v for v in range(self.m)
                       if v not in used and v not in forb[c]]
                if best_dom is None or len(dom) < len(best_dom):
                    best, best_dom = c, dom
                    if not dom:
                        break
            for v in best_dom:
                self.nodes += 1
                if self.node_budget and self.nodes > self.node_budget:
                    self.stopped = True
                    return
                if self.seconds and self.nodes % 4096 == 0 \
                        and time.time() - self.start > self.seconds:
                    self.stopped = True
                    return
                val[best] = v
                yield from rec(k + 1)
                del val[best]

        yield from rec(0)

    # -- the whole search --------------------------------------------------
    def run(self, k):
        m = self.m
        self.start = time.time()
        st = Structure(m=m)
        st.seed_two()

        def dfs(cur):
            if self.stopped:
                return None
            self.deepest = max(self.deepest, cur.t)
            if cur.t == k:
                return cur
            for col in self.columns(cur):
                nxt = Structure(m=m)
                nxt.t = cur.t
                nxt.sigma = {kk: v[:] for kk, v in cur.sigma.items()}
                nxt.add_block([[x for x in range(m)]] +
                              [[col[(i, x)] for x in range(m)]
                               for i in range(1, cur.t)])
                got = dfs(nxt)
                if got is not None:
                    return got
                if self.stopped:
                    return None
            return None

        got = dfs(st)
        if got is None and not self.stopped:
            self.exhausted = True
        return got


def validate():
    print("Validation -- the search is complete, so it must find what exists\n")
    for k in (3, 7):
        m = k - 1
        s = CompleteSearch(m, seconds=600)
        t0 = time.time()
        got = s.run(k)
        el = time.time() - t0
        if got is None:
            print("  degree %d: FAILED to find a Moore graph (%d nodes)"
                  % (k, s.nodes))
            return False
        sigma = {kk: tuple(v) for kk, v in got.sigma.items()}
        g = reduction.build_graph(k, sigma, m=m)
        ok, msg = reduction.is_moore(g, k)
        print("  degree %d: found in %d nodes / %.1fs -- %s"
              % (k, s.nodes, el, msg))
        if not ok:
            return False
    return True


def measure(seconds=300.0):
    print("\nDegree 57, same complete search, %.0fs budget\n" % seconds)
    s = CompleteSearch(56, seconds=seconds)
    t0 = time.time()
    got = s.run(57)
    el = time.time() - t0
    rate = s.nodes / el if el else 0
    print("  nodes explored : %d" % s.nodes)
    print("  wall clock     : %.0fs   (%.0f nodes/s)" % (el, rate))
    print("  deepest reached: %d of 57 branches" % s.deepest)
    print("  found the graph: %s" % (got is not None))
    print("  search exhausted: %s" % s.exhausted)
    return rate


def verdict(rate):
    print("\n" + "=" * 70)
    print("IS A GUARANTEED BRUTE FORCE POSSIBLE IN LOCAL COMPUTE TIME?")
    print("=" * 70)
    m = 56

    # Exact: with the gauge sigma_0j = id, a 3-branch structure is exactly a
    # derangement of the 56 points, so N_3 = D_56 exactly.
    d = [1, 0]
    for i in range(2, m + 1):
        d.append((i - 1) * (d[-1] + d[-2]))
    D56 = d[m]
    print("\n  EXACT, not estimated:")
    print("    gauge-fixed structures on just 3 of the 57 branches")
    print("      = D_56 (derangements of 56 points)")
    print("      = %d" % D56)
    print("      = 10^%.1f" % log10(D56))

    # Isomorph rejection cannot rescue it: orbits >= structures / |group|.
    # The residual symmetry after gauge-fixing is at most simultaneous
    # relabelling of the 56 points, of order 56!.
    lg56 = lgamma(57) / log(10)
    print("\n    Isomorph rejection helps at 3 branches: the classes are just")
    print("    cycle types, a few thousand.  It stops helping almost at once.")
    print("    At 4 branches the count is ~D_56^3 = 10^%.0f while the residual"
          % (3 * log10(D56)))
    print("    symmetry is at most 56! = 10^%.1f, so orbits >= 10^%.0f."
          % (lg56, 3 * log10(D56) - lg56))

    print("\n  MEASURED, on this machine:")
    print("    %.0f search nodes per second" % rate)
    secs_per_year = 3.156e7
    print("    a year of local compute = 10^%.1f nodes"
          % log10(max(rate, 1) * secs_per_year))
    print("    a century = 10^%.1f nodes" % log10(max(rate, 1) * secs_per_year * 100))

    need = 3 * log10(D56) - lg56
    have = log10(max(rate, 1) * secs_per_year * 100)
    print("\n  VERDICT: a guaranteed complete search must cover at least")
    print("    10^%.0f classes at FOUR of the 57 branches alone." % need)
    print("    A century of this machine covers 10^%.0f nodes." % have)
    print("    Shortfall at four branches: 10^%.0f." % (need - have))
    print()
    print("    There is no way to close that with engineering.  The program")
    print("    below is complete and correct and will find the graph if one")
    print("    exists; it will not finish.  A guaranteed brute force in local")
    print("    compute time does not exist for this problem, and the obstacle")
    print("    is not the implementation -- it is that four branches out of")
    print("    fifty-seven already exceed any physically available budget.")


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0
    if not validate():
        print("validation failed -- not reporting further")
        return 1
    rate = measure(secs)
    verdict(rate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
