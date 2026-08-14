"""
What does the best method actually cost per branch, and where does that land 57?

The goal was a program that reaches the graph in feasible local compute.  The
complete search answered that with an exact count (bruteforce.py): no.  This
answers it for the *best* method found here, grow-and-repair annealing, using
its own measured timings rather than a model.

The grow logs record, for each branch, every attempt and its budget.  The cost
of placing branch t is the sum of the failed attempts plus the successful one.
Fitting the growth rate of that quantity and extrapolating to 57 gives the
honest projection for the method that actually works best.
"""

import math
import re
import sys


def parse(path):
    """-> {t: seconds spent placing branch t, solved: bool}"""
    spent = {}
    solved = set()
    for line in open(path):
        m = re.search(r"t=(\d+)\s+solved .*?(\d+)s\)", line)
        if m:
            t = int(m.group(1))
            spent[t] = spent.get(t, 0.0) + float(m.group(2))
            solved.add(t)
            continue
        m = re.search(r"t=(\d+)\s+[\d.]+s try \d+: cost \d+ -> \d+ "
                      r"\(\d+ moves, (\d+)s\)", line)
        if m:
            t = int(m.group(1))
            spent[t] = spent.get(t, 0.0) + float(m.group(2))
    return spent, solved


def fit_and_project(spent, solved, label, target=57):
    ts = sorted(t for t in spent if t in solved)
    if len(ts) < 3:
        print("  %s: not enough data" % label)
        return
    print("  %s" % label)
    print("     %-6s %-12s %s" % ("branch", "seconds", "ratio to previous"))
    prev = None
    for t in ts:
        r = ("%.1fx" % (spent[t] / prev)) if prev and prev > 0 else "-"
        print("     %-6d %-12.0f %s" % (t, spent[t], r))
        prev = spent[t]

    # geometric fit over the last few solved branches, where the trend is real
    tail = ts[-4:] if len(ts) >= 4 else ts
    xs = tail
    ys = [max(spent[t], 1.0) for t in tail]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(math.log(y) for y in ys) / n
    num = sum((x - mx) * (math.log(y) - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    slope = num / den if den else 0.0
    ratio = math.exp(slope)
    intercept = my - slope * mx
    print("     fitted growth: x%.2f per branch" % ratio)

    log10_total = 0.0
    for t in range(ts[-1] + 1, target + 1):
        log10_total = max(log10_total, (intercept + slope * t) / math.log(10))
    print("     projected cost of the LAST branch (t=%d): 10^%.0f seconds"
          % (target, (intercept + slope * target) / math.log(10)))
    yrs = (intercept + slope * target) / math.log(10) - math.log10(3.156e7)
    print("     that is 10^%.0f years on this machine" % yrs)
    if spent.get(max(spent), 0) and max(spent) not in solved:
        print("     (branch %d already consumed %.0fs without solving)"
              % (max(spent), spent[max(spent)]))
    print()


def main():
    logs = sys.argv[1:] or ["grow_inv.log", "grow_gen.log"]
    print("Measured cost per branch for grow-and-repair annealing\n")
    for path in logs:
        try:
            spent, solved = parse(path)
        except FileNotFoundError:
            continue
        fit_and_project(spent, solved,
                        "%s (frontier %d)" % (path, max(solved) if solved else 0))
    print("Read this next to bruteforce.py's exact accounting.  The complete")
    print("search cannot finish for counting reasons; the best heuristic")
    print("cannot finish for measured ones.  Neither is close, and they fail")
    print("for independent reasons.")


if __name__ == "__main__":
    main()
