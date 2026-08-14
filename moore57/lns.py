"""
Large-neighbourhood search: revise an OLD branch, not just the new one.

Both search styles used so far share a blind spot.  The CP-SAT growth in
factorization_search.py never touches a branch once placed.  grow_anneal.py can
in principle move any pair, but in practice the annealer settles the early
branches and then only jiggles the frontier.  So when branch t will not fit,
neither can say "branch 4 was the mistake".

LNS says exactly that.  Hold every branch but one fixed, delete that one, and
re-solve it exactly with CP-SAT while forbidding the column it had before.  The
key point is that freeing a *single* branch keeps the model in the easy form:
every constraint that involves branch r involves only bijections in column r,
so the whole thing stays a set of binary disequalities plus the
involution/matching structure -- no products of two unknowns, no element
constraints.

The loop is: try to add a branch; if that fails, revise a random existing
branch and try again.  That is the move the greedy searches cannot make.
"""

import json
import random
import sys
import time

import factorization_search as F
import reduction


def drop_branch(st, r):
    """A structure with branch r removed and the later branches renumbered."""
    new = F.FactStructure(st.m)
    old = [i for i in range(st.t) if i != r]
    pos = {o: n for n, o in enumerate(old)}
    new.t = st.t - 1
    for i in old:
        for j in old:
            if i == j or i == 0 or j == 0:
                continue
            new.sigma[(pos[i], pos[j])] = st.sigma[(i, j)][:]
    return new


def column_of(st, r):
    """The column [sigma_{i,r}] as extend() would return it."""
    return {i: st.sigma[(i, r)][:] for i in range(1, st.t) if i != r}


def load(path):
    d = json.load(open(path))
    st = F.FactStructure(d["m"])
    st.t = d["t"]
    st.sigma = {tuple(int(z) for z in k.split(",")): v
                for k, v in d["sigma"].items()
                if not k.startswith("0,") and ",0" not in k}
    return st


def verify_fragment(st):
    g = reduction.build_graph(st.t, st.to_sigma(), m=st.m)
    return reduction.girth_at_least_5(g), len(g)


def main():
    path = sys.argv[1]
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    budget = float(sys.argv[4]) if len(sys.argv) > 4 else 12000.0
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0

    rng = random.Random(seed)
    st = load(path)
    ok, msg = st.verify()
    print("loaded %s -> %s" % (path, msg), flush=True)
    assert ok
    end = time.time() + budget
    best_t = st.t

    for rnd in range(rounds):
        if time.time() > end:
            break
        # 1. try to add a branch
        col, name, n_con = F.extend(st, seconds=seconds, workers=4,
                                    seed=rng.randrange(10 ** 6))
        if col is not None:
            st.add_block(col)
            good, msg = st.verify()
            assert good, msg
            g_ok, n = verify_fragment(st)
            print("  round %2d: GREW to t=%d -- %s, fragment %d vertices, "
                  "girth>=5: %s" % (rnd, st.t, msg, n, g_ok), flush=True)
            assert g_ok
            best_t = max(best_t, st.t)
            json.dump({"t": st.t, "m": st.m,
                       "sigma": {"%d,%d" % k: v for k, v in st.sigma.items()}},
                      open("lns_t%d.json" % st.t, "w"))
            continue

        # 2. it would not grow -- revise an existing branch and try again
        r = rng.randrange(1, st.t)
        old_col = column_of(st, r)
        reduced = drop_branch(st, r)
        banned = [{i: old_col[o] for i, o in
                   enumerate([o for o in range(1, st.t) if o != r], start=1)}]
        new_col, name2, _ = F.extend(reduced, seconds=seconds, workers=4,
                                     seed=rng.randrange(10 ** 6),
                                     banned=banned)
        if new_col is None:
            print("  round %2d: add %s; revising branch %d also %s"
                  % (rnd, name, r, name2), flush=True)
            continue
        reduced.add_block(new_col)
        good, msg = reduced.verify()
        assert good, msg
        st = reduced
        print("  round %2d: add %s; revised branch %d (now %s)"
              % (rnd, name, r, msg), flush=True)

    print("LNS frontier: t = %d of 57" % best_t, flush=True)


if __name__ == "__main__":
    main()
