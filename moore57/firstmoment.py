"""
How big is the search, and where does the structure run out?

Both search models of this project are "add one block at a time".  Adding
block r to a valid r-block structure introduces

    r - 1  new bijections            (sigma_ir for i = 1..r-1; sigma_0r = id
                                      by the gauge)
    C(r,2) + 3*C(r,3)  new constraints, each demanding that some composite
                       be a derangement.

Treating the composites as uniformly random permutations gives a first-moment
estimate for the number of valid t-block structures,

    E[N_t] = prod_{r=2}^{t-1}  B^{r-1} * q^{C(r,2) + 3 C(r,3)}

with B = 56! and q = D_56/56! ~ 1/e for the general model, and B = 56,
q = 55/56 for the cyclic model.  The per-step factor crosses 1 at a definite
r*: above it, structures are expected to die out.

The point of this file is not the estimate -- it is the calibration.  The same
formula is applied to k = 3 and k = 7, where the exact counts are known from
general_search.py and cyclic_search.py, so we can see exactly how far the
heuristic is from the truth before trusting anything it says about k = 57.
"""

import math
from math import comb, lgamma, log, log10


def n_derangements(m):
    d = [1, 0]
    for i in range(2, m + 1):
        d.append((i - 1) * (d[-1] + d[-2]))
    return d[m]


def log_factorial(m):
    return lgamma(m + 1)


def model_params(k, cyclic):
    m = k - 1
    if cyclic:
        return log(m), log((m - 1) / m)          # log B, log q
    return log_factorial(m), log(n_derangements(m)) - log_factorial(m)


def step_log(r, logB, logq):
    """log of the expected number of ways to add block r."""
    return (r - 1) * logB + (comb(r, 2) + 3 * comb(r, 3)) * logq


def crossover(k, cyclic):
    """Predicted largest reachable t, in blocks.

    step_log(r) is the expected number of ways to add block index r, i.e. to
    go from r blocks to r+1.  The last r for which that is >= 1 predicts a
    largest structure of r+1 blocks."""
    logB, logq = model_params(k, cyclic)
    r = 2
    while step_log(r, logB, logq) >= 0:
        r += 1
        if r > 10000:
            break
    return min(r, k)          # (r-1) + 1 blocks


def cumulative_log10(k, t, cyclic):
    logB, logq = model_params(k, cyclic)
    return sum(step_log(r, logB, logq) for r in range(2, t)) / log(10)


def table(k):
    m = k - 1
    print("=" * 74)
    print("degree k = %d :  %d blocks of %d,  %d bijections to choose "
          "(%d after gauge)" % (k, k, m, comb(k, 2), comb(k - 1, 2)))
    print("  target: t = %d blocks" % k)
    for cyclic in (False, True):
        name = "cyclic  (sigma in Z_%d)" % m if cyclic else "general (sigma in S_%d)" % m
        logB, logq = model_params(k, cyclic)
        rstar = crossover(k, cyclic)
        space = comb(k - 1, 2) * logB / log(10)
        print("  %-26s search space 10^%-10.1f  per-step crossover r* = %d"
              % (name, space, rstar))
        # a few explicit expected-extension counts
        pts = sorted(set([3, 5, rstar - 1, rstar, rstar + 1, rstar + 2,
                          min(k, rstar + 5), k]))
        cells = []
        for r in pts:
            if 2 <= r <= k:
                cells.append("r=%d: 10^%.1f" % (r, step_log(r, logB, logq) / log(10)))
        print("      expected ways to add block r:  " + ",  ".join(cells))
        print("      expected number of complete (t=%d) structures: 10^%.0f"
              % (k, cumulative_log10(k, k, cyclic)))
    print()


def calibration():
    print("=" * 74)
    print("CALIBRATION -- prediction vs exact truth, at the degrees where a")
    print("Moore graph is known to exist")
    print("=" * 74)
    rows = [
        # k, cyclic, exact largest t reached, source
        (3, False, 3, "general search finds Petersen"),
        (3, True,  3, "cyclic search finds Petersen"),
        (7, False, 7, "general search finds Hoffman-Singleton"),
        (7, True,  5, "cyclic search stalls -- MISSES Hoffman-Singleton"),
    ]
    print("%-8s %-9s %-12s %-10s  %s" % ("degree", "model", "predicted max",
                                         "actual", "note"))
    for k, cyc, actual, note in rows:
        pred = crossover(k, cyc)
        print("%-8d %-9s t<=%-9d t=%-8d  %s%s"
              % (k, "cyclic" if cyc else "general", pred, actual, note,
                 "" if pred >= actual else "   <-- PREDICTION TOO LOW"))
    print()
    print("Read the k=7 general row carefully: the first-moment crossover says")
    print("the structure should die at t=%d blocks, and the Hoffman-Singleton"
          % crossover(7, False))
    print("graph nevertheless reaches t=7.  The estimate is wrong in the direction of")
    print("false pessimism, because the constraints are positively correlated.")
    print("So a search stalling near the crossover is NOT evidence of")
    print("non-existence -- at k=7 that same evidence would have been wrong.")
    print()


def peak_and_tree(k, cyclic):
    """Peak log10 of the number of valid t-block structures, and the resulting
    estimate of the size of the exhaustive search tree.

    The tree is dominated by the widest level: each valid t-block structure is
    extended by trying every one of B candidates for the next bijection, so
    nodes ~ max_t N_t * B.  Calibration at k = 7 (below) shows this
    overestimates the measured tree by about one order of magnitude."""
    logB, _ = model_params(k, cyclic)
    best_t, best = max(((t, cumulative_log10(k, t, cyclic))
                        for t in range(3, k + 1)), key=lambda z: z[1])
    return best_t, best, best + logB / log(10)


def brute_force_budget():
    print("=" * 74)
    print("WHAT WOULD A BRUTE-FORCE SEARCH COST?")
    print("=" * 74)
    m, k = 56, 57
    free = comb(k - 1, 2)
    raw = free * log_factorial(m) / log(10)
    print("  bijections to determine (after gauge)      %d, each from "
          "56! = 10^%.1f" % (free, log_factorial(m) / log(10)))
    print("  raw space                                  10^%.0f" % raw)
    print("  derangement constraints                    %d triangles + "
          "%d quadrilaterals = %d"
          % (comb(k, 3), 3 * comb(k, 4), comb(k, 3) + 3 * comb(k, 4)))
    print()
    print("  Raw space is the wrong measure -- pruning is what matters.  The")
    print("  size of the *pruned* tree is set by its widest level:")
    print()
    print("    %-22s %-14s %-16s %s"
          % ("search", "widest level", "structures there", "tree size (nodes)"))
    for kk, cyc, label in ((7, False, "k=7   general"),
                           (57, True, "k=57  cyclic ansatz"),
                           (57, False, "k=57  general")):
        t, n, tree = peak_and_tree(kk, cyc)
        print("    %-22s t = %-10d 10^%-13.0f 10^%.0f" % (label, t, n, tree))
    print()
    print("    measured, k=7 general: 81,381,110 = 10^7.9 nodes to the first")
    print("    solution (61 s).  The estimate above says 10^9.1, so it runs")
    print("    about one order of magnitude high.  Treat the k=57 rows the "
          "same way.")
    print()
    print("  For scale: a machine visiting 10^18 nodes per second for the age")
    print("  of the universe covers 10^%.0f nodes.  Lloyd's bound on the total"
          % log10(1e18 * 4.4e17))
    print("  computation available in the observable universe is about 10^120.")
    print("  Even the cyclic-restricted exhaustive search exceeds that bound by")
    print("  %d orders of magnitude; the general search exceeds it by %d."
          % (round(peak_and_tree(57, True)[2] - 120),
             round(peak_and_tree(57, False)[2] - 120)))
    print()
    print("  Symmetry does not rescue it.  The most any automorphism assumption")
    print("  can buy is the order of the assumed group, and that group is now")
    print("  known to have odd order (Ishida 2026) and order at most 375")
    print("  (Macaj-Siran 2010): a factor of 10^2.6.  The assumption is not even")
    print("  safe -- a trivial automorphism group is consistent with all of it.")
    print()
    print("  The honest measure of reach is the largest t-block structure anyone")
    print("  can build: t = 20 of 57.  Brute force would have to survive every")
    print("  block from there to 57.")
    print()


if __name__ == "__main__":
    for k in (3, 7, 57):
        table(k)
    calibration()
    brute_force_budget()
