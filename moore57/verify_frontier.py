"""
Verify the frontier certificate two independent ways.

t19_cyclic.json holds a 19-branch structure for degree 57, found by
push_cyclic.py under the cyclic ansatz.  This checks it

  (a) arithmetically, against the Z_56 conditions, and
  (b) concretely, by building the 1 + 19 + 19*56 = 1084 vertex graph it
      describes and confirming that graph has girth 5 and the degrees a
      19-branch fragment of the missing Moore graph must have.
"""

import json

import cyclic_search
import push_cyclic
import reduction

M = 56


def main(path="t19_cyclic.json"):
    data = json.load(open(path))
    t, a = data["t"], data["labelling"]
    assert data["m"] == M

    print("certificate: %d of the 57 branches" % t)
    print("  Z_%d conditions (no vanishing 3-sum or 4-sum): %s"
          % (M, push_cyclic.verify(t, a)))
    assert push_cyclic.verify(t, a)

    sigma = cyclic_search.labelling_to_sigma(M, t, a)
    print("  derangement conditions on the sigma table:    %s"
          % reduction.sigma_conditions_hold(t, sigma, m=M))
    assert reduction.sigma_conditions_hold(t, sigma, m=M)

    g = reduction.build_graph(t, sigma, m=M)
    n = len(g)
    print("  built graph: %d vertices (expected %d)" % (n, 1 + t + t * M))
    assert n == 1 + t + t * M
    print("  girth >= 5:                                   %s"
          % reduction.girth_at_least_5(g))
    assert reduction.girth_at_least_5(g)

    deg_root = len(g["v"])
    deg_layer1 = {len(g[("u", i)]) for i in range(t)}
    deg_layer2 = {len(g[(i, x)]) for i in range(t) for x in range(M)}
    print("  root degree      %d   (57 in the complete graph)" % deg_root)
    print("  layer-1 degrees  %s   (57 -- these branches are already full)"
          % sorted(deg_layer1))
    print("  layer-2 degrees  %s   (57 in the complete graph)"
          % sorted(deg_layer2))
    assert deg_root == t
    assert deg_layer1 == {1 + M}
    assert deg_layer2 == {t}          # 1 parent + (t-1) cross-block edges
    print()
    print("  So: a girth-5 graph on %d vertices in which %d vertices already"
          % (n, t))
    print("  have their full degree 57, and the remaining %d layer-2 vertices"
          % (t * M))
    print("  have %d of 57.  Completing it means adding branches 20..57."
          % t)


if __name__ == "__main__":
    main()
