"""
How many verified structures are dead ends?

Every search here stalls, and the usual reading is "the search is not good
enough".  There is a sharper possibility: that the space is full of valid
structures which simply cannot be extended, so that a searcher which reaches t
branches has probably already walked into a trap and no amount of effort at the
frontier will help.

That is measurable.  For a given t, generate valid t-branch structures at
random (annealing does this quickly at small t), and for each ask CP-SAT
exactly whether it extends.  Adding one branch to a fixed structure is a set of
binary disequalities, so at small t the solver terminates with a definite
answer rather than a timeout.

The output is the fraction of verified t-branch structures that are provably
dead ends.  If that fraction climbs steeply with t, the frontier is explained
by the object and not by the searcher, and no better search will move it.
"""

import sys
import time

import anneal_fast
import factorization_search as F
import general_extend as G


def random_valid(t, model, seed, budget):
    """A valid t-branch structure found by annealing, or None."""
    a = anneal_fast.FastAnneal(t, 56, seed=seed, model=model)
    best, _ = a.run(10_000_000, t0=1.2, t1=0.01,
                    deadline=time.time() + budget)
    if best != 0:
        return None
    if model == "involution":
        st = F.FactStructure(56)
        st.t = t
        st.sigma = {(i, j): [int(x) for x in a.S[i, j]]
                    for i in range(1, t) for j in range(1, t) if i != j}
    else:
        st = G.Structure(m=56)
        st.t = t
        st.sigma = {(i, j): [int(x) for x in a.S[i, j]]
                    for i in range(t) for j in range(t) if i != j}
    ok, msg = st.verify()
    assert ok, msg
    return st


def main():
    ts = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [5, 6, 7, 8]
    model = sys.argv[2] if len(sys.argv) > 2 else "involution"
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    cp_secs = float(sys.argv[4]) if len(sys.argv) > 4 else 60.0
    anneal_secs = float(sys.argv[5]) if len(sys.argv) > 5 else 60.0

    print("dead-end density, %s state space, %d samples per t, "
          "%.0fs exact budget each\n" % (model, n, cp_secs), flush=True)
    print("  %-4s %-8s %-10s %-12s %-8s" %
          ("t", "sampled", "extends", "DEAD END", "unknown"), flush=True)

    for t in ts:
        ext = dead = unk = got = 0
        for s in range(n):
            st = random_valid(t, model, seed=9000 + 137 * t + s,
                              budget=anneal_secs)
            if st is None:
                continue
            got += 1
            if model == "involution":
                col, name, _ = F.extend(st, seconds=cp_secs, workers=4, seed=s)
            else:
                col, name, _ = G.extend(st, seconds=cp_secs, workers=4, seed=s)
            if col is not None:
                ext += 1
            elif name == "INFEASIBLE":
                dead += 1
            else:
                unk += 1
        print("  %-4d %-8d %-10d %-12d %-8d" % (t, got, ext, dead, unk),
              flush=True)


if __name__ == "__main__":
    main()
