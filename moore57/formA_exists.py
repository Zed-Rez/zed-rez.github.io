"""
Does a 5-branch Form A structure exist at degree 57?

This is the sharpest test available of my own conjecture, and it can go either
way.

If a Moore graph of degree 57 exists and satisfies Form A, then every one of
its 5-branch sub-structures satisfies Form A, so such structures certainly
exist.  Contrapositive: if no 5-branch Form A structure exists at degree 57,
Form A is FALSE for degree 57 and every conditional result in this project
built on it collapses.

The annealer finds 4-branch Form A structures easily and fails at 5.  That is
suggestive but proves nothing -- a search failing is not an absence.  CP-SAT
can settle it for a *given* 4-branch structure: extending by one branch under
the Form A constraints is a finite model, and INFEASIBLE is a proof that that
particular structure is a dead end.

Doing that for several independent 4-branch structures does not refute the
conjecture outright -- that needs all of them -- but a run of INFEASIBLEs would
be serious evidence against it, and a single SOLVED settles the existence
question the other way.
"""

import json
import sys
import time

import numpy as np

import formA_search
import involution_search
import reduction
from general_extend import Structure


def find_formA(t, seed, secs):
    a = formA_search.FormAAnneal(t, 56, seed=seed, model="involution")
    best, it, kicks = a.run_ils(time.time() + secs, t_lo=0.06, stall=25000,
                                kick=8, seed=seed)
    if best != 0:
        return None
    inv, tot = formA_search.check_formA(a)
    assert inv == tot, "annealer returned a non-Form-A structure"
    st = Structure(m=56)
    st.t = t
    st.sigma = {(i, j): [int(x) for x in a.S[i, j]]
                for i in range(t) for j in range(t) if i != j}
    ok, msg = st.verify()
    assert ok, msg
    return st


def main():
    samples = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    anneal_secs = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    cp_secs = float(sys.argv[3]) if len(sys.argv) > 3 else 600.0

    print("Does a 5-branch Form A structure exist at degree 57?\n", flush=True)
    results = []
    for s in range(samples):
        st = find_formA(4, seed=4000 + s, secs=anneal_secs)
        if st is None:
            print("  sample %d: could not even find a 4-branch Form A "
                  "structure" % s, flush=True)
            continue
        t0 = time.time()
        col, name, counts = involution_search.extend_involutive(
            st, seconds=cp_secs, workers=4, seed=s, impose=True)
        el = time.time() - t0
        results.append(name)
        print("  sample %d: 4-branch Form A structure -> extending: %s "
              "(%.0fs, %d diseq, %d involution conditions)"
              % (s, name, el, counts[0], counts[1]), flush=True)
        if col is not None:
            st.add_block(col)
            ok, msg = st.verify()
            g = reduction.build_graph(st.t, {(i, j): tuple(st.sigma[(i, j)])
                                             for i in range(st.t)
                                             for j in range(st.t) if i != j},
                                      m=56)
            print("    EXISTS: %s, fragment %d vertices, girth>=5 %s"
                  % (msg, len(g), reduction.girth_at_least_5(g)), flush=True)
            json.dump({"t": st.t, "m": 56,
                       "sigma": {"%d,%d" % k: list(v)
                                 for k, v in st.sigma.items()}},
                      open("formA_exists_t%d.json" % st.t, "w"))
            print("\n  Conclusion: 5-branch Form A structures DO exist at "
                  "degree 57.", flush=True)
            return

    n_inf = results.count("INFEASIBLE")
    print("\n  %d of %d samples proved INFEASIBLE, %d timed out."
          % (n_inf, len(results), results.count("UNKNOWN")), flush=True)
    if n_inf and n_inf == len(results):
        print("  Every 4-branch Form A structure tested is a dead end.  That is")
        print("  evidence against Form A at degree 57 -- not a refutation,")
        print("  which would need all such structures, but the conjecture is")
        print("  in trouble if this pattern holds.", flush=True)
    elif not results:
        print("  No conclusion.", flush=True)
    else:
        print("  No conclusion: the solver could not decide.", flush=True)


if __name__ == "__main__":
    main()
