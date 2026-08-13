"""
The block/matching reduction for Moore graphs of diameter 2.

A Moore graph of degree k and diameter 2 has n = k^2 + 1 vertices, is k-regular
and has girth 5.  Conversely any k-regular graph on k^2 + 1 vertices with girth 5
is such a Moore graph, so "girth 5" is the whole of the condition.

Root the graph at a vertex v.  Then

    layer 0 : v
    layer 1 : u_1, ..., u_k          (the neighbours of v)
    layer 2 : k blocks B_1, ..., B_k of size k - 1, where B_i is the set of
              neighbours of u_i other than v.

Three facts follow immediately from girth 5, and together they are equivalent
to girth 5:

  (R1) layer 1 is independent and each block B_i is independent;
  (R2) every vertex of B_i has exactly one neighbour in every other block B_j,
       i.e. the edges between B_i and B_j form a perfect matching, described by
       a bijection sigma_ij : B_i -> B_j with sigma_ji = sigma_ij^{-1};
  (R3) no triangles and no 4-cycles among the blocks, which in terms of the
       bijections says that for all distinct i, j, l and all distinct
       i, j, l, m the compositions

           sigma_il^{-1} . sigma_jl . sigma_ij                (3-cycles)
           sigma_im^{-1} . sigma_lm . sigma_jl . sigma_ij     (4-cycles)

       are derangements (fixed-point free permutations) of B_i.

So the search for a Moore graph of degree k is exactly the search for an
edge-labelling of the complete graph K_k by permutations of a (k-1)-set such
that every closed walk on 3 or 4 distinct blocks multiplies out to a
derangement.  For k = 57 that is 1596 permutations of 56 points.

This module implements the reduction in both directions and checks it against
the two Moore graphs that are known to exist (Petersen, k = 3; Hoffman-
Singleton, k = 7).

Conventions
-----------
A permutation of {0, ..., m-1} is a tuple p with p[x] the image of x.
Composition ``compose(q, p)`` is "p then q", i.e. (q . p)(x) = q[p[x]].
"""

from itertools import permutations


# --------------------------------------------------------------------------
# permutation helpers
# --------------------------------------------------------------------------

def compose(q, p):
    """Return q . p, i.e. apply p first."""
    return tuple(q[x] for x in p)


def inverse(p):
    out = [0] * len(p)
    for x, y in enumerate(p):
        out[y] = x
    return tuple(out)


def is_derangement(p):
    return all(x != y for x, y in enumerate(p))


def identity(m):
    return tuple(range(m))


# --------------------------------------------------------------------------
# graph helpers  (graphs are dict: vertex -> set of vertices)
# --------------------------------------------------------------------------

def add_edge(g, a, b):
    g.setdefault(a, set()).add(b)
    g.setdefault(b, set()).add(a)


def girth_at_least_5(g):
    """True iff g has no 3-cycle and no 4-cycle."""
    for v in g:
        nbrs = g[v]
        for a in nbrs:
            if a in g and nbrs & g[a]:
                return False            # triangle
    # 4-cycle: some pair of vertices with two common neighbours
    for v in g:
        seen = set()
        for a in g[v]:
            for b in g[a]:
                if b == v:
                    continue
                if b in seen:
                    return False        # two paths of length 2 from v to b
                seen.add(b)
    return True


def is_moore(g, k):
    """Check g is a Moore graph of degree k and diameter 2."""
    if len(g) != k * k + 1:
        return False, "wrong order %d != %d" % (len(g), k * k + 1)
    for v in g:
        if len(g[v]) != k:
            return False, "vertex %r has degree %d" % (v, len(g[v]))
    if not girth_at_least_5(g):
        return False, "girth < 5"
    # girth >= 5 plus k-regular plus k^2+1 vertices forces diameter 2, but
    # check it anyway -- it is cheap and this is the property we care about.
    for v in g:
        reach = set(g[v]) | {v}
        for a in g[v]:
            reach |= g[a]
        if len(reach) != len(g):
            return False, "diameter > 2 from %r" % (v,)
    return True, "Moore graph of degree %d on %d vertices" % (k, len(g))


# --------------------------------------------------------------------------
# reduction:  sigma table  ->  graph
# --------------------------------------------------------------------------

def build_graph(k, sigma, m=None):
    """Build the rooted graph from the bijections.

    ``sigma`` is a dict mapping (i, j) with i != j, 0 <= i, j < k, to a
    permutation of range(m); only the entries with i < j need be given, the
    others are taken to be the inverses.

    ``k`` is the number of blocks and ``m`` the block size.  For a complete
    Moore graph of degree k these satisfy m = k - 1, which is the default;
    passing them separately builds a partial structure of k branches out of
    the m + 1 that a full graph would have.

    Vertices are 'v', ('u', i) and (i, x) for a block index i and a point x.
    """
    if m is None:
        m = k - 1
    g = {}
    g['v'] = set()
    for i in range(k):
        add_edge(g, 'v', ('u', i))
        for x in range(m):
            add_edge(g, ('u', i), (i, x))
    for i in range(k):
        for j in range(i + 1, k):
            p = sigma[(i, j)] if (i, j) in sigma else inverse(sigma[(j, i)])
            for x in range(m):
                add_edge(g, (i, x), (j, p[x]))
    return g


def sigma_conditions_hold(k, sigma, verbose=False, m=None):
    """Check the derangement conditions (R3) directly on the sigma table."""
    if m is None:
        m = k - 1

    def s(i, j):
        if (i, j) in sigma:
            return sigma[(i, j)]
        return inverse(sigma[(j, i)])

    for i in range(k):
        for j in range(k):
            if j == i:
                continue
            for l in range(k):
                if l in (i, j):
                    continue
                tri = compose(inverse(s(i, l)), compose(s(j, l), s(i, j)))
                if not is_derangement(tri):
                    if verbose:
                        print("triangle at", i, j, l)
                    return False
                for mm in range(k):
                    if mm in (i, j, l):
                        continue
                    quad = compose(inverse(s(i, mm)),
                                   compose(s(l, mm), compose(s(j, l), s(i, j))))
                    if not is_derangement(quad):
                        if verbose:
                            print("quadrilateral at", i, j, l, mm)
                        return False
    return True


# --------------------------------------------------------------------------
# reduction:  graph -> sigma table
# --------------------------------------------------------------------------

def decompose(g, root):
    """Extract (k, sigma) from a Moore graph rooted at ``root``."""
    us = sorted(g[root], key=repr)
    k = len(us)
    blocks = []
    for u in us:
        b = sorted(g[u] - {root}, key=repr)
        assert len(b) == k - 1, "block size %d" % len(b)
        blocks.append(b)
    index = {}
    for i, b in enumerate(blocks):
        for x, w in enumerate(b):
            index[w] = (i, x)

    sigma = {}
    for i in range(k):
        for j in range(k):
            if i == j:
                continue
            p = [None] * (k - 1)
            for x, w in enumerate(blocks[i]):
                hits = [index[z][1] for z in g[w] if z in index and index[z][0] == j]
                assert len(hits) == 1, "block %d -> %d from %r: %r" % (i, j, w, hits)
                p[x] = hits[0]
            sigma[(i, j)] = tuple(p)
    return k, sigma


# --------------------------------------------------------------------------
# automorphisms that fix the root and all of its neighbours
# --------------------------------------------------------------------------

def root_fixing_automorphisms(k, sigma, m=None):
    """All automorphisms fixing the root and every layer-1 vertex.

    Such an automorphism acts on block i by some permutation pi_i, and edge
    preservation says pi_j . sigma_ij = sigma_ij . pi_i for every i, j.  So
    pi_0 determines the rest via pi_j = sigma_0j . pi_0 . sigma_0j^{-1}, and
    the whole group is parametrised by the admissible pi_0.

    This is exactly the group the cyclic ansatz assumes to be non-trivial: if
    all the sigma_ij lie in one regular abelian group, its generator gives such
    an automorphism of order m.
    """
    if m is None:
        m = k - 1

    def s(i, j):
        return sigma[(i, j)] if (i, j) in sigma else inverse(sigma[(j, i)])

    out = []
    for p0 in permutations(range(m)):
        pis = [p0]
        for j in range(1, k):
            sj = s(0, j)
            pis.append(compose(compose(sj, p0), inverse(sj)))
        ok = True
        for i in range(k):
            for j in range(k):
                if i == j:
                    continue
                if compose(pis[j], s(i, j)) != compose(s(i, j), pis[i]):
                    ok = False
                    break
            if not ok:
                break
        if ok:
            out.append(tuple(pis))
    return out


def order_of_permutation(p):
    n, seen, orders = len(p), set(), []
    for x in range(n):
        if x in seen:
            continue
        c, y = 0, x
        while y not in seen:
            seen.add(y)
            y = p[y]
            c += 1
        orders.append(c)
    from math import gcd
    out = 1
    for o in orders:
        out = out * o // gcd(out, o)
    return out


# --------------------------------------------------------------------------
# the two known Moore graphs
# --------------------------------------------------------------------------

def petersen():
    g = {}
    for i in range(5):
        add_edge(g, ('o', i), ('o', (i + 1) % 5))
        add_edge(g, ('i', i), ('i', (i + 2) % 5))
        add_edge(g, ('o', i), ('i', i))
    return g


def hoffman_singleton():
    """Robertson's construction: 5 pentagons P_h, 5 pentagrams Q_i, and vertex
    j of P_h joined to vertex (h*i + j) mod 5 of Q_i."""
    g = {}
    for h in range(5):
        for j in range(5):
            add_edge(g, ('P', h, j), ('P', h, (j + 1) % 5))
            add_edge(g, ('Q', h, j), ('Q', h, (j + 2) % 5))
    for h in range(5):
        for i in range(5):
            for j in range(5):
                add_edge(g, ('P', h, j), ('Q', i, (h * i + j) % 5))
    return g


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

def main():
    for name, g, k in (("Petersen", petersen(), 3),
                       ("Hoffman-Singleton", hoffman_singleton(), 7)):
        ok, msg = is_moore(g, k)
        print("%-18s %s" % (name, msg))
        assert ok, msg

        root = sorted(g, key=repr)[0]
        kk, sigma = decompose(g, root)
        assert kk == k
        print("%-18s decomposed into %d blocks of %d; "
              "derangement conditions hold: %s"
              % ("", k, k - 1, sigma_conditions_hold(k, sigma)))
        assert sigma_conditions_hold(k, sigma)

        g2 = build_graph(k, sigma)
        ok2, msg2 = is_moore(g2, k)
        print("%-18s rebuilt from the sigma table: %s" % ("", msg2))
        assert ok2, msg2
        print()

    # the group the cyclic ansatz needs to exist
    print("Automorphisms fixing the root and every one of its neighbours")
    print("(the cyclic ansatz needs one of order k-1):")
    for name, g, k in (("Petersen", petersen(), 3),
                       ("Hoffman-Singleton", hoffman_singleton(), 7)):
        _, sigma = decompose(g, sorted(g, key=repr)[0])
        auts = root_fixing_automorphisms(k, sigma)
        orders = sorted({order_of_permutation(a[0]) for a in auts})
        print("  %-18s group order %d, element orders %s -> ansatz %s"
              % (name, len(auts), orders,
                 "can work" if (k - 1) in orders else "is EMPTY"))
    print()

    # sanity check in the other direction: perturbing one bijection must break it
    k = 7
    _, sigma = decompose(hoffman_singleton(), ('P', 0, 0))
    bad = dict(sigma)
    p = list(bad[(0, 1)])
    p[0], p[1] = p[1], p[0]
    bad[(0, 1)] = tuple(p)
    bad[(1, 0)] = inverse(bad[(0, 1)])
    print("perturbed Hoffman-Singleton table still valid:",
          sigma_conditions_hold(k, bad),
          "/ still a Moore graph:", is_moore(build_graph(k, bad), k)[0])


if __name__ == "__main__":
    main()
