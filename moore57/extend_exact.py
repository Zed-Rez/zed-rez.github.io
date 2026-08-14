"""
Does a verified structure extend?  Ask exactly.

The annealer produces cost-0 structures: 11 branches in the involution space,
13 in the general space, each verified by rebuilding the graph fragment.  The
question that matters is not "can my search go further" but "does *this*
structure extend at all".  CP-SAT can answer that exactly, because adding one
branch to a fixed structure is a set of binary disequalities.

  SOLVED      the frontier advances, with an exact certificate
  INFEASIBLE  a hard fact: this verified structure is a dead end, and every
              move spent trying to extend it was wasted
  UNKNOWN     the solver ran out of time

The INFEASIBLE outcome is what turns "the search stalled" into a statement
about the object rather than about the searcher.  If verified structures at
11 branches routinely fail to extend, that is a real obstruction; if they
extend easily and the annealer simply could not find the extension, that is a
statement about the annealer.
"""

import json
import sys
import time

import factorization_search as F
import general_extend as G
import reduction


def load(path, model):
    d = json.load(open(path))
    t, m = d["t"], d["m"]
    raw = {}
    for k, v in d["sigma"].items():
        i, j = (int(z) for z in k.split(","))
        raw[(i, j)] = v
    if model == "involution":
        st = F.FactStructure(m)
        st.t = t
        st.sigma = {(i, j): raw[(i, j)] for i in range(1, t)
                    for j in range(1, t) if i != j}
    else:
        st = G.Structure(m=m)
        st.t = t
        st.sigma = {(i, j): raw[(i, j)] for i in range(t)
                    for j in range(t) if i != j}
    return st


def main():
    path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "involution"
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 900.0
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    st = load(path, model)
    ok, msg = st.verify()
    print("%s -> %s" % (path, msg), flush=True)
    assert ok, msg

    t0 = time.time()
    if model == "involution":
        col, name, n_con = F.extend(st, seconds=secs, workers=4, seed=seed)
    else:
        col, name, n_con = G.extend(st, seconds=secs, workers=4, seed=seed)
    el = time.time() - t0
    print("  exact extension: %s in %.0fs (%d conditions)"
          % (name, el, n_con), flush=True)

    if col is not None:
        st.add_block(col)
        good, msg2 = st.verify()
        assert good, msg2
        sig = (st.to_sigma() if model == "involution"
               else {(i, j): tuple(st.sigma[(i, j)])
                     for i in range(st.t) for j in range(st.t) if i != j})
        g = reduction.build_graph(st.t, sig, m=st.m)
        print("  EXTENDED to t=%d: %s, fragment %d vertices, girth>=5: %s"
              % (st.t, msg2, len(g), reduction.girth_at_least_5(g)), flush=True)
        json.dump({"t": st.t, "m": st.m,
                   "sigma": {"%d,%d" % k: list(v) for k, v in st.sigma.items()}},
                  open("exact_%s_t%d.json" % (model, st.t), "w"))
    elif name == "INFEASIBLE":
        print("  HARD FACT: this verified %d-branch structure provably does "
              "NOT extend to %d." % (st.t, st.t + 1), flush=True)
    else:
        print("  no conclusion (solver timed out).", flush=True)


if __name__ == "__main__":
    main()
