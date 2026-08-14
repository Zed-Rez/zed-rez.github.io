"""
What is the true ceiling of the reduced reflection model, as a law in n?

The model is: a symmetric labelling f of K_t over Z_n, gauge-fixed by f_0j = 0,
with no vanishing 4-cycle sum f_pw - f_uw + f_qu - f_pq.  For the degree-57
problem n = 28, and every search plateaus at t = 14 while a first-moment count
promises about 21.

Rather than argue about the extrapolation, compute the answer exactly for small
n, where CP-SAT can prove INFEASIBLE, and read off the law.  If the pattern
extrapolates to roughly 14 at n = 28, then 14 is the model's ceiling and the
search was never the problem.
"""

import sys
from itertools import combinations

from ortools.sat.python import cp_model


def feasible(t, n, seconds=60.0, workers=4):
    model = cp_model.CpModel()
    f = {}
    for i, j in combinations(range(t), 2):
        if i == 0:
            v = model.NewConstant(0)                  # gauge
        else:
            v = model.NewIntVar(0, n - 1, "f%d_%d" % (i, j))
        f[(i, j)] = v
        f[(j, i)] = v
    for a, b, c, d in combinations(range(t), 4):
        for (p, q, u, w) in ((a, b, c, d), (a, b, d, c), (a, c, b, d)):
            s = model.NewIntVar(-2 * n, 2 * n, "")
            model.Add(s == f[(p, w)] - f[(u, w)] + f[(q, u)] - f[(p, q)])
            for mult in range(-2, 3):
                model.Add(s != mult * n)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    st = solver.Solve(model)
    return solver.StatusName(st)


def max_t(n, seconds, cap=30):
    t = 4
    last = 3
    while t <= cap:
        name = feasible(t, n, seconds=seconds)
        if name in ("OPTIMAL", "FEASIBLE"):
            last = t
            t += 1
        elif name == "INFEASIBLE":
            return last, True
        else:
            return last, False              # undecided
    return last, False


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    ns = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else \
        [2, 3, 4, 5, 6, 7, 8, 10, 12, 14]

    print("Exact ceiling of the reduced reflection model, by modulus\n")
    print("  %-6s %-10s %-10s %s" % ("n", "max t", "proved?", "t / n"))
    data = []
    for n in ns:
        best, proved = max_t(n, secs)
        print("  %-6d %-10d %-10s %.3f"
              % (n, best, "yes" if proved else "undecided", best / n),
              flush=True)
        if proved:
            data.append((n, best))

    if len(data) >= 3:
        print()
        print("  Proved points: %s" % data)
        # crude linear fit through the proved points
        xs = [n for n, _ in data]
        ys = [b for _, b in data]
        k = len(xs)
        mx = sum(xs) / k
        my = sum(ys) / k
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = sum((x - mx) ** 2 for x in xs)
        slope = num / den if den else 0
        icept = my - slope * mx
        print("  linear fit: max t ~ %.3f n + %.2f" % (slope, icept))
        print("  extrapolated to n = 28: max t ~ %.1f" % (slope * 28 + icept))
        print()
        print("  The searched frontier at n = 28 is 14.  Compare.")


if __name__ == "__main__":
    main()
