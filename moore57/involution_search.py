"""
Search with the involution property imposed.

involution.py finds that in both Moore graphs that exist, every triangle
composite

        tau(a, j, b) = sigma_{b,a} . sigma_{j,b} . sigma_{a,j}

is a fixed-point-free *involution*, not merely a derangement -- and that
structures produced by the ordinary search satisfy this essentially never
(0 of 1320 triples in a 12-branch structure; 66 of 5814 in the published-style
cyclic frontier).  So it is real information that the standard model throws
away.

For an unordered triple of branches all six orderings give composites that are
conjugate or inverse to one another, so there is exactly one condition per
unordered triple.  Written without inverses of the composite it is

        sigma_{b,a} . sigma_{r,b} . sigma_{a,r}  =  sigma_{r,a} . sigma_{b,r} . sigma_{a,b}

which, with p_i := sigma_{i,r} for the new branch r, reads pointwise

        sigma_ba[ pinv_b[ p_a[x] ] ]  =  pinv_a[ p_b[ sigma_ab[x] ] ]

-- a chain of table lookups, encodable with element constraints.

STATUS: the involution property is verified for degrees 3 and 7 and is a
conjecture for degree 57.  A search that imposes it is therefore a conditional
search: complete solutions it finds are genuine Moore graphs (the derangement
conditions are still enforced in full), but failure to find one would only rule
out Moore graphs *with* the property.  This module also validates the model by
recovering Hoffman-Singleton at degree 7.
"""

import json
import sys
import time
from itertools import combinations

from ortools.sat.python import cp_model

import general_extend
import reduction
from general_extend import Structure, build_disequalities


def elem(model, arr, idx, lo, hi, name=""):
    """A new variable equal to arr[idx], where arr may hold ints or vars."""
    out = model.NewIntVar(lo, hi, name)
    model.AddElement(idx, arr, out)
    return out


def extend_involutive(st, seconds=120.0, workers=4, seed=0, log=False,
                      impose=True, banned=()):
    """Add one branch, enforcing the derangement conditions and (optionally)
    the involution property.  ``banned`` lists columns that must not be
    returned again, so the caller can enumerate distinct children."""
    t, m = st.t, st.m
    model = cp_model.CpModel()

    p, pinv = {}, {}
    for i in range(t):
        if i == 0:                                   # gauge: sigma_0r = id
            p[0] = [model.NewConstant(x) for x in range(m)]
            pinv[0] = [model.NewConstant(x) for x in range(m)]
            continue
        p[i] = [model.NewIntVar(0, m - 1, "p%d_%d" % (i, x)) for x in range(m)]
        pinv[i] = [model.NewIntVar(0, m - 1, "q%d_%d" % (i, x)) for x in range(m)]
        model.AddInverse(p[i], pinv[i])

    # --- derangement conditions: binary disequalities on cells --------------
    n_dis = 0
    for (i, a, j, b) in build_disequalities(st):
        if i == 0 and j == 0:
            continue
        model.Add(p[i][a] != p[j][b])
        n_dis += 1

    # --- involution conditions: one per unordered pair {a,b} ----------------
    #
    # D = sigma_ab^{-1} . p_b^{-1} . p_a  acts on B_a, and D(x) = y is just
    #     p_a[x] == p_b[ sigma_ab[y] ]
    # so "D is an involution" becomes a biconditional between two equalities of
    # variables at *constant* indices -- no element constraints needed.  (The
    # x = y case says D has no fixed point, which the derangement
    # disequalities above already enforce.)
    n_inv = 0
    if impose:
        # Pairs involving the gauge branch 0 collapse: with p_0 the identity,
        # the condition is exactly that h_b = p_b . sigma_0b is an involution,
        # which CP-SAT propagates natively.
        for b in range(1, t):
            s_0b = st.sigma[(0, b)]
            h = [p[b][s_0b[x]] for x in range(m)]
            model.AddInverse(h, h)
            n_inv += 1
        for a, b in combinations(range(1, t), 2):
            s_ab = st.sigma[(a, b)]
            for x, y in combinations(range(m), 2):
                e1 = model.NewBoolVar("")
                model.Add(p[a][x] == p[b][s_ab[y]]).OnlyEnforceIf(e1)
                model.Add(p[a][x] != p[b][s_ab[y]]).OnlyEnforceIf(e1.Not())
                e2 = model.NewBoolVar("")
                model.Add(p[a][y] == p[b][s_ab[x]]).OnlyEnforceIf(e2)
                model.Add(p[a][y] != p[b][s_ab[x]]).OnlyEnforceIf(e2.Not())
                model.Add(e1 == e2)
                n_inv += 1

    # --- exclude columns already tried at this node ------------------------
    for col in banned:
        lits = []
        for i in range(1, t):
            for x in range(m):
                bvar = model.NewBoolVar("")
                model.Add(p[i][x] != col[i][x]).OnlyEnforceIf(bvar)
                model.Add(p[i][x] == col[i][x]).OnlyEnforceIf(bvar.Not())
                lits.append(bvar)
        model.AddBoolOr(lits)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.randomize_search = True
    solver.parameters.log_search_progress = log
    status = solver.Solve(model)
    name = solver.StatusName(status)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        col = [[solver.Value(p[i][x]) for x in range(m)] for i in range(t)]
        return col, name, (n_dis, n_inv)
    return None, name, (n_dis, n_inv)


def copy_structure(st):
    new = Structure(m=st.m)
    new.t = st.t
    new.sigma = {k: v[:] for k, v in st.sigma.items()}
    return new


def grow_backtracking(st, target, seconds=120.0, impose=True, fanout=4,
                      out=sys.stdout, save=None, workers=4, seed=0,
                      deadline=None):
    """Depth-first growth with backtracking: at each branch level try up to
    ``fanout`` distinct columns before giving up and backing out."""
    best = [st.t, copy_structure(st)]

    def dfs(cur, depth):
        if cur.t >= target:
            return cur
        if deadline and time.time() > deadline:
            return None
        banned = []
        for child in range(fanout):
            col, name, (nd, ni) = extend_involutive(
                cur, seconds=seconds, workers=workers,
                seed=seed + 1000 * depth + child, impose=impose, banned=banned)
            if col is None:
                if child == 0:
                    print("  %2d -> %2d : %s (%d diseq, %d inv)"
                          % (cur.t, cur.t + 1, name, nd, ni), file=out, flush=True)
                return None if name == "INFEASIBLE" and child == 0 else None
            banned.append(col)
            nxt = copy_structure(cur)
            nxt.add_block(col)
            ok, msg = nxt.verify()
            if not ok:
                raise SystemExit("invalid structure: " + msg)
            if nxt.t > best[0]:
                best[0], best[1] = nxt.t, copy_structure(nxt)
                print("  %2d -> %2d : SOLVED (%d diseq, %d inv) -- new best"
                      % (cur.t, nxt.t, nd, ni), file=out, flush=True)
                if save:
                    json.dump({"t": nxt.t, "m": nxt.m,
                               "sigma": {"%d,%d" % k: v
                                         for k, v in nxt.sigma.items()}},
                              open(save, "w"))
            got = dfs(nxt, depth + 1)
            if got is not None:
                return got
            if deadline and time.time() > deadline:
                return None
        return None

    got = dfs(st, 0)
    return (got, "COMPLETE") if got is not None else (best[1], "exhausted/timeout")


def grow(st, target, seconds=120.0, impose=True, out=sys.stdout, save=None,
         workers=4, seed=0):
    while st.t < target:
        t0 = time.time()
        col, name, (nd, ni) = extend_involutive(st, seconds=seconds,
                                                workers=workers,
                                                seed=seed + st.t, impose=impose)
        el = time.time() - t0
        if col is None:
            print("  branches %2d -> %2d : %s after %.0fs (%d diseq, %d inv)"
                  % (st.t, st.t + 1, name, el, nd, ni), file=out, flush=True)
            return st, name
        st.add_block(col)
        ok, msg = st.verify()
        print("  branches %2d -> %2d : SOLVED in %.0fs (%d diseq, %d inv) -- %s"
              % (st.t - 1, st.t, el, nd, ni, msg), file=out, flush=True)
        if not ok:
            raise SystemExit("invalid structure: " + msg)
        if save:
            json.dump({"t": st.t, "m": st.m,
                       "sigma": {"%d,%d" % k: v for k, v in st.sigma.items()}},
                      open(save, "w"))
    return st, "COMPLETE"


def check_involutions(st):
    """Fraction of triangle composites that are involutions."""
    import involution
    sig = {k: tuple(v) for k, v in st.sigma.items()}
    tot = inv = 0
    from itertools import permutations as perms
    for a, j, b in perms(range(st.t), 3):
        tau = involution.composite(sig, st.t, a, j, b, st.m)
        tot += 1
        if involution.is_involution(tau):
            inv += 1
    return inv, tot


def validate_degree7(seconds=60.0):
    """The model must recover Hoffman-Singleton."""
    print("Validation at degree 7 (blocks of 6, need 7 branches):", flush=True)
    st = Structure(m=6)
    st.seed_two()
    st, why = grow_backtracking(st, target=7, seconds=seconds, impose=True,
                                fanout=6)
    print("  result: t = %d (%s)" % (st.t, why), flush=True)
    if st.t == 7:
        sigma = {k: tuple(v) for k, v in st.sigma.items()}
        g = reduction.build_graph(7, sigma, m=6)
        ok, msg = reduction.is_moore(g, 7)
        print("  rebuilt: %s" % msg, flush=True)
        inv, tot = check_involutions(st)
        print("  involutive composites: %d/%d" % (inv, tot), flush=True)
        return ok
    return False


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "validate"
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    if mode == "validate":
        ok = validate_degree7(seconds=secs)
        print("\nmodel %s" % ("VALIDATED -- it finds the graph that exists"
                              if ok else "FAILED validation"))
        return

    print("Degree 57 with the involution property imposed, %.0fs per branch"
          % secs, flush=True)
    st = Structure(m=56)
    st.seed_two()
    st, why = grow(st, target=57, seconds=secs, impose=True,
                   save="involution_frontier.json", workers=workers, seed=seed)
    print("frontier: t = %d of 57 (%s)" % (st.t, why), flush=True)
    inv, tot = check_involutions(st)
    print("involutive composites: %d/%d" % (inv, tot), flush=True)


if __name__ == "__main__":
    main()
