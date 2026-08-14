"""
Reference implementation of the Moore-graph checker.

This mirrors `Moore57Verify.lean` clause for clause.  The Lean file cannot be
compiled in this sandbox, so this is the executable version that IS tested: it
must accept the Moore graphs that exist and reject everything else, including
graphs that are wrong in only one edge.

The checker takes an adjacency table -- a list of neighbour lists -- and
returns True only when the graph is a Moore graph of degree k and diameter 2:

    order                 n = k^2 + 1
    isRegular             every vertex has exactly k neighbours
    isSimpleSymmetric     no loops, no repeats, and the table is symmetric
    triangleFree          no edge closes a triangle
    noTwoCommonNeighbours no pair of vertices has two common neighbours

The last two together are girth >= 5, and with regularity and the order they
are exactly the Moore condition.  Nothing here assumes the graph came from the
sigma-table construction, so it is an independent check on any candidate.
"""

import sys

import reduction


# --------------------------------------------------------------------------
# the checker, mirroring the Lean definitions
# --------------------------------------------------------------------------

def is_regular(adj, n, k):
    return len(adj) == n and all(len(l) == k for l in adj)


def is_simple_symmetric(adj, n):
    for u in range(n):
        l = adj[u]
        if len(set(l)) != len(l):
            return False
        for v in l:
            if v == u or not (0 <= v < n):
                return False
            if u not in adj[v]:
                return False
    return True


def triangle_free(adj, n):
    for u in range(n):
        nb = set(adj[u])
        for v in adj[u]:
            for w in adj[v]:
                if w in nb:
                    return False
    return True


def no_two_common_neighbours(adj, n):
    for u in range(n):
        seen = bytearray(n)
        for v in adj[u]:
            for w in adj[v]:
                if w == u:
                    continue
                if seen[w]:
                    return False
                seen[w] = 1
    return True


def moore_check(adj, n, k):
    return (n == k * k + 1
            and is_regular(adj, n, k)
            and is_simple_symmetric(adj, n)
            and triangle_free(adj, n)
            and no_two_common_neighbours(adj, n))


# --------------------------------------------------------------------------
# turning the project's graph objects into adjacency tables
# --------------------------------------------------------------------------

def to_table(g):
    verts = sorted(g, key=repr)
    idx = {v: i for i, v in enumerate(verts)}
    return [sorted(idx[w] for w in g[v]) for v in verts]


def table_from_sigma(k, sigma, m=None):
    return to_table(reduction.build_graph(k, sigma, m=m))


# --------------------------------------------------------------------------
# tests
# --------------------------------------------------------------------------

def perturbations(adj, n, limit=200):
    """Graphs that differ from adj in one edge swap -- all must be rejected."""
    import random
    rng = random.Random(7)
    out = []
    for _ in range(limit):
        t = [list(l) for l in adj]
        u = rng.randrange(n)
        if not t[u]:
            continue
        v = t[u][rng.randrange(len(t[u]))]
        w = rng.randrange(n)
        if w == u or w in t[u]:
            continue
        t[u].remove(v)
        t[v].remove(u)
        t[u].append(w)
        t[w].append(u)
        out.append(t)
    return out


def main():
    print("Verified-checker reference implementation\n")
    ok = True

    for name, g, k in (("Petersen", reduction.petersen(), 3),
                       ("Hoffman-Singleton", reduction.hoffman_singleton(), 7)):
        adj = to_table(g)
        n = len(adj)
        good = moore_check(adj, n, k)
        print("  %-18s n=%-5d k=%-3d accepted: %s" % (name, n, k, good))
        ok &= good

        # wrong degree claimed
        print("    rejects a wrong degree claim      : %s"
              % (not moore_check(adj, n, k + 1)))
        ok &= not moore_check(adj, n, k + 1)

        # one-edge perturbations must all be rejected
        bad = perturbations(adj, n)
        rejected = sum(1 for t in bad if not moore_check(t, n, k))
        print("    rejects %d one-edge perturbations : %s"
              % (len(bad), rejected == len(bad)))
        ok &= rejected == len(bad)

    # a graph of the right order and degree but the wrong structure:
    # the complete bipartite-ish circulant on 10 vertices, degree 3
    circ = [[(i + 1) % 10, (i - 1) % 10, (i + 5) % 10] for i in range(10)]
    print("\n  circulant C10(1,5), n=10 k=3 accepted: %s  (must be False --"
          " it has 4-cycles)" % moore_check(circ, 10, 3))
    ok &= not moore_check(circ, 10, 3)

    # the checker applied to a partial structure must fail on degree
    sigma = {(i, j): tuple(range(56)) for i in range(2) for j in range(2) if i != j}
    print("  a 2-branch degree-57 fragment accepted: %s  (must be False)"
          % moore_check(table_from_sigma(2, sigma, m=56), 1 + 2 + 112, 57))

    print("\n  all checker tests passed: %s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
