"""
Anneal to the plateau, then hand the remainder to an exact solver.

Annealing stalls at t branches with a small residual cost -- 11 to 14 out of an
initial ~570 at t = 12, 9 out of ~920 at t = 14.  A residual that small is
usually concentrated: most branches are fine and one is carrying the
violations.

So: anneal, then for each branch ask what the cost would be if that branch were
deleted.  If some branch's removal leaves cost exactly 0, the remaining t-1
branches are a *verified* structure, and the question "does it extend?" can be
put to CP-SAT exactly, because freeing a single branch keeps the model in the
easy binary-disequality form.

Three outcomes, all informative:

  SOLVED      the frontier advances to t, with an exact certificate;
  INFEASIBLE  a hard fact -- this verified (t-1)-branch structure provably does
              not extend, so the annealer was not merely unlucky;
  UNKNOWN     the solver ran out of time and we learn nothing.

The INFEASIBLE case is the valuable one: it converts "my search got stuck" into
"this structure is a dead end", which is a statement about the problem rather
than about the searcher.
"""

import json
import sys
import time

import numpy as np

import anneal_fast
import factorization_search as F
import general_extend as G
import reduction


def drop_branch(a, r):
    """A FastAnneal state with branch r removed and later branches renumbered."""
    keep = [i for i in range(a.t) if i != r]
    b = anneal_fast.FastAnneal(a.t - 1, a.m, seed=0, model=a.model)
    for ni, oi in enumerate(keep):
        for nj, oj in enumerate(keep):
            b.S[ni, nj] = a.S[oi, oj]
    return b


def to_cp_structure(a, model):
    if model == "involution":
        st = F.FactStructure(a.m)
        st.t = a.t
        st.sigma = {(i, j): [int(x) for x in a.S[i, j]]
                    for i in range(1, a.t) for j in range(1, a.t) if i != j}
    else:
        st = G.Structure(m=a.m)
        st.t = a.t
        st.sigma = {(i, j): [int(x) for x in a.S[i, j]]
                    for i in range(a.t) for j in range(a.t) if i != j}
    return st


def main():
    t = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    model = sys.argv[2] if len(sys.argv) > 2 else "involution"
    anneal_secs = float(sys.argv[3]) if len(sys.argv) > 3 else 400.0
    cp_secs = float(sys.argv[4]) if len(sys.argv) > 4 else 900.0
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    seedfile = sys.argv[6] if len(sys.argv) > 6 else None

    print("hybrid: anneal t=%d (%s) for %.0fs, then exact-extend for %.0fs"
          % (t, model, anneal_secs, cp_secs), flush=True)

    a = anneal_fast.FastAnneal(t, 56, seed=seed, model=model)
    if seedfile:
        d = json.load(open(seedfile))
        for k, v in d["sigma"].items():
            i, j = (int(z) for z in k.split(","))
            if i < d["t"] and j < d["t"]:
                a.S[i, j] = np.array(v, dtype=np.int16)
        print("  seeded from %s (t=%d)" % (seedfile, d["t"]), flush=True)

    best, it = a.run(10_000_000, t0=1.2, t1=0.01,
                     deadline=time.time() + anneal_secs)
    print("  annealed to cost %d in %d moves" % (best, it), flush=True)

    if best == 0:
        print("  already a valid %d-branch structure" % t, flush=True)
        reduced, r = a, None
    else:
        # which single branch is carrying the violations?
        options = []
        for r in range(1, a.t):
            c = drop_branch(a, r).total_cost()
            options.append((c, r))
        options.sort()
        c, r = options[0]
        print("  dropping branch %d leaves cost %d (best of %d options; "
              "others %s)" % (r, c, len(options),
                              [x[0] for x in options[1:5]]), flush=True)
        if c != 0:
            print("  no single branch carries all the violations -- the "
                  "residual is spread out, so there is nothing exact to hand "
                  "over.", flush=True)
            return
        reduced = drop_branch(a, r)

    st = to_cp_structure(reduced, model)
    ok, msg = st.verify()
    print("  reduced structure: %s" % msg, flush=True)
    assert ok, msg

    print("  asking CP-SAT to extend it exactly (%.0fs)..." % cp_secs,
          flush=True)
    t0 = time.time()
    if model == "involution":
        col, name, n_con = F.extend(st, seconds=cp_secs, workers=4, seed=seed)
    else:
        col, name, n_con = G.extend(st, seconds=cp_secs, workers=4, seed=seed)
    el = time.time() - t0
    print("  -> %s in %.0fs (%d conditions)" % (name, el, n_con), flush=True)

    if col is not None:
        if model == "involution":
            st.add_block(col)
        else:
            st.add_block(col)
        good, msg2 = st.verify()
        g = reduction.build_graph(st.t, st.to_sigma() if model == "involution"
                                  else {(i, j): tuple(st.sigma[(i, j)])
                                        for i in range(st.t)
                                        for j in range(st.t) if i != j},
                                  m=56)
        print("  EXTENDED: %s, fragment %d vertices, girth>=5: %s"
              % (msg2, len(g), reduction.girth_at_least_5(g)), flush=True)
        json.dump({"t": st.t, "m": 56,
                   "sigma": {"%d,%d" % k: list(v) for k, v in st.sigma.items()}},
                  open("hybrid_%s_t%d.json" % (model, st.t), "w"))
    elif name == "INFEASIBLE":
        print("  HARD FACT: this verified %d-branch structure provably does "
              "not extend." % st.t, flush=True)
        json.dump({"t": st.t, "m": 56, "nonextendable": True,
                   "sigma": {"%d,%d" % k: list(v) for k, v in st.sigma.items()}},
                  open("nonextendable_%s_t%d.json" % (model, st.t), "w"))
    else:
        print("  no conclusion.", flush=True)


if __name__ == "__main__":
    main()
