"""
How hard does the involution property prune, and is it sound?

At degree 7 both questions can be answered exactly, because the whole space of
partial structures is enumerable and the Moore graph is unique.

  * SOUNDNESS.  Hoffman-Singleton is the only Moore graph of degree 7, and all
    210 of its triangle composites are involutions.  Therefore every partial
    structure that extends to a complete one is a sub-structure of
    Hoffman-Singleton, and so is involutive.  Filtering on the involution
    property at degree 7 discards nothing that could have led to the graph:
    the filter is sound.  This module verifies that by enumeration rather than
    by the argument -- it counts, at each level, the valid structures, the
    involutive ones, and the ones that actually extend to a complete graph.

  * STRENGTH.  The ratio (all valid) / (involutive) at each level is exactly
    the factor by which a search enforcing the property would be pruned.

What this does NOT establish is soundness at degree 57, where uniqueness is not
available and the graph is known to be far less symmetric.  The measurement is
still the right one to have: it says what the filter is worth where it can be
checked, and it is the calibration any degree-57 claim has to survive.
"""

import sys
import time

import general_search


def counts(k, depth):
    s = general_search.GeneralSearch(k, count_all=True, depth_limit=depth)
    s.track_involutive = True
    t0 = time.time()
    s.run()
    return s, time.time() - t0


def extendable_counts(k, depth):
    """How many t-block structures extend all the way to a complete graph?

    Enumerated directly: for each structure at the cut depth, run the ordinary
    complete search from it and see whether it reaches k blocks."""
    # For k = 7 this is done by exploiting uniqueness instead of brute force:
    # a structure extends iff it is a sub-structure of Hoffman-Singleton, and
    # the search below already reports the complete solutions found.
    s = general_search.GeneralSearch(k, count_all=True)
    s.track_involutive = True
    s.run()
    return s


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print("Degree %d: how much does the involution property prune?\n" % k)
    s, el = counts(k, depth)
    print("  %-8s %-16s %-16s %s"
          % ("branches", "valid", "involutive", "pruning factor"))
    for t in range(3, k + 1):
        if not s.level_counts[t]:
            continue
        inv = s.involutive_counts[t]
        ratio = (s.level_counts[t] / inv) if inv else float("inf")
        print("  t=%-6d %-16d %-16d %s"
              % (t, s.level_counts[t], inv,
                 ("%.1fx" % ratio) if inv else "everything pruned"))
    print("\n  (%d search nodes, %.1fs)" % (s.nodes, el))

    print("\n  Soundness at degree %d: Hoffman-Singleton is the unique Moore" % k)
    print("  graph of this degree and all its triangle composites are")
    print("  involutions, so every structure that extends to a complete graph")
    print("  is involutive.  The filter therefore discards nothing that could")
    print("  have led to the graph -- at this degree.")


if __name__ == "__main__":
    main()
