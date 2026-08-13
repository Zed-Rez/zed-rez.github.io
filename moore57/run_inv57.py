"""Driver: degree-57 growth with the involution property imposed."""
import sys
import time

import involution_search
from general_extend import Structure

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0
fanout = int(sys.argv[2]) if len(sys.argv) > 2 else 3
workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 21
budget = float(sys.argv[5]) if len(sys.argv) > 5 else 20000.0

st = Structure(m=56)
st.seed_two()
st, why = involution_search.grow_backtracking(
    st, target=57, seconds=secs, impose=True, fanout=fanout, workers=workers,
    seed=seed, save="involution_frontier.json",
    deadline=time.time() + budget)
print("frontier: t = %d of 57 (%s)" % (st.t, why), flush=True)
print("involutive composites: %d/%d" % involution_search.check_involutions(st),
      flush=True)
