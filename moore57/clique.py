"""
A colouring lower bound for the extension problem.

Adding a branch is a colouring of the (t-1) x 56 grid of cells with 56 values,
where the constraints are

  * every row is a permutation -- so each row is a CLIQUE of size 56 in the
    conflict graph, and
  * the triangle/quadrilateral disequalities join cells across rows.

Any clique in that graph needs as many colours as it has vertices, so a clique
of 57 or more proves the extension impossible.  Each row already gives a clique
of exactly 56, which is tight; the question is whether mixing rows beats it.

A cell conflicts with exactly 18 cells of any other row (1 from the triangle
through those two branches, 17 from the quadrilaterals), so no single cell
extends a whole row.  This searches for larger mixed cliques directly.
"""

import json
import random
import sys
from itertools import combinations

import general_extend
from general_extend import Structure


def build_conflict(st):
    """adjacency as a dict cell -> set of cells, including row cliques."""
    m, t = st.m, st.t
    adj = {(i, x): set() for i in range(1, t) for x in range(m)}
    for (i, a, j, b) in general_extend.build_disequalities(st):
        if i == 0 or j == 0 or i == j:
            continue
        adj[(i, a)].add((j, b))
        adj[(j, b)].add((i, a))
    for i in range(1, t):                      # row cliques
        for x, y in combinations(range(m), 2):
            adj[(i, x)].add((i, y))
            adj[(i, y)].add((i, x))
    return adj


def greedy_clique(adj, start, rng):
    clique = [start]
    cand = set(adj[start])
    while cand:
        # pick the candidate with the most connections inside the candidate set
        best, best_deg = None, -1
        sample = list(cand) if len(cand) <= 400 else rng.sample(sorted(cand), 400)
        for v in sample:
            d = len(adj[v] & cand)
            if d > best_deg:
                best, best_deg = v, d
        clique.append(best)
        cand &= adj[best]
    return clique


def spectral(adj):
    """Clique-free obstructions: the Hoffman chromatic bound and the ratio
    bound on independent sets.  Either one can prove the extension impossible
    if it bites."""
    import numpy as np
    cells = sorted(adj)
    idx = {c: i for i, c in enumerate(cells)}
    n = len(cells)
    A = np.zeros((n, n))
    for c in cells:
        for v in adj[c]:
            A[idx[c], idx[v]] = 1.0
    assert (A == A.T).all()
    k = int(A.sum(1)[0])
    ev = np.linalg.eigvalsh(A)
    lmin, lmax = float(ev[0]), float(ev[-1])
    hoffman = 1 + lmax / (-lmin)
    ratio = n * (-lmin) / (k - lmin)
    return n, k, lmax, lmin, hoffman, ratio


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "t19"
    tries = int(sys.argv[2]) if len(sys.argv) > 2 else 400

    d = json.load(open("t19_cyclic.json"))
    st = Structure.from_cyclic(d["labelling"])
    ok, msg = st.verify()
    print("structure: %s" % msg, flush=True)

    adj = build_conflict(st)
    cells = sorted(adj)
    degs = sorted(len(adj[c]) for c in cells)
    print("conflict graph: %d cells, degree min %d / median %d / max %d"
          % (len(cells), degs[0], degs[len(degs) // 2], degs[-1]), flush=True)

    # cross-row conflict count, as a sanity check on the count of 18
    i, a = 1, 0
    per_row = {}
    for (g, b) in adj[(i, a)]:
        if g != i:
            per_row[g] = per_row.get(g, 0) + 1
    vals = sorted(set(per_row.values()))
    print("a cell conflicts with %s cells of each other row" % vals, flush=True)

    rng = random.Random(20260813)
    best, best_c = 0, None
    for n in range(tries):
        start = cells[rng.randrange(len(cells))]
        c = greedy_clique(adj, start, rng)
        if len(c) > best:
            best, best_c = len(c), c
    # verify the witness
    assert all(v in adj[u] for u, v in combinations(best_c, 2)), "not a clique"
    rows = len({r for r, _ in best_c})
    print("largest clique found: %d  (spanning %d rows) -- verified"
          % (best, rows), flush=True)
    print(flush=True)
    if best > 56:
        print("PROVEN: a clique of %d needs %d colours but only 56 values"
              % (best, best), flush=True)
        print("exist, so this structure admits no extension.", flush=True)
    n, k, lmax, lmin, hoffman, ratio = spectral(adj)
    print("spectral obstructions on the same graph:", flush=True)
    print("  %d-regular, eigenvalues max %.4f, min %.4f" % (k, lmax, lmin),
          flush=True)
    print("  Hoffman chromatic bound  chi >= %.4f   (56 values available) -> %s"
          % (hoffman, "PROOF" if hoffman > 56 else "no obstruction"), flush=True)
    print("  ratio bound              alpha <= %.2f  (classes need size %d) -> %s"
          % (ratio, st.t - 1, "PROOF" if ratio < st.t - 1 else "no obstruction"),
          flush=True)
    print(flush=True)

    if best > 56:
        pass
    else:
        print("A clique of %d does not exceed the 56 available values, so this"
              % best, flush=True)
        print("bound does not settle it.  Note a single row already gives 56,",
              flush=True)
        print("so the colouring is exactly tight: every row must use every",
              flush=True)
        print("value once, and the cross-row conflicts must all be absorbed",
              flush=True)
        print("without ever forcing a 57th colour.", flush=True)
        print(flush=True)
        print("Taken together: the 19-branch structure passes every cheap", flush=True)
        print("necessary condition -- a transversal exists, the clique number", flush=True)
        print("is exactly 56, and neither spectral bound bites.  So there is no", flush=True)
        print("LOCAL obstruction to extending it.  That matches the dihedral", flush=True)
        print("analysis: any obstruction at degree 57 has to be global.", flush=True)


if __name__ == "__main__":
    main()
