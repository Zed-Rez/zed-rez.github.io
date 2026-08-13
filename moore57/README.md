# The missing Moore graph of degree 57

An attempt to find it, an audit of how far the known constraints bind the
problem, and a measurement of how far short of brute force that leaves us.

Short answer: **there is no point at which brute force becomes possible.** The
reachable frontier is 20 of the 57 branches the graph needs. The gap between
the pruned search tree and the computational capacity of the observable
universe is roughly 10^5950 for the honest search, and still 10^65 for the
restricted search that everyone actually runs — and that restricted search is
now known to be a dead end anyway.

## The object

A Moore graph of degree 57 and diameter 2 is a strongly regular graph with
parameters (3250, 57, 0, 1): 57-regular, 3250 vertices, girth 5, 92,625 edges,
58,094,400 pentagons, spectrum 57¹ 7¹⁷²⁹ (−8)¹⁵²⁰. Degrees 2, 3 and 7 give the
pentagon, the Petersen graph and the Hoffman–Singleton graph. Degree 57 is the
only remaining case, open since Hoffman and Singleton in 1960.

`known_constraints.py` runs the classical feasibility tests. Every one passes:
integral spectrum, both Krein conditions, the absolute bound, a ratio bound of
exactly 400. Each formula is validated against Petersen and Hoffman–Singleton
first, including a brute-force pentagon count that confirms the closed form
n·C(k,2)·(k−1)/5.

## The reduction

Root the graph at a vertex. It has 57 neighbours, each with 56 further
children, giving 57 blocks of 56. Girth 5 forces the edges between any two
blocks to be a perfect matching σ_ij, and is *equivalent* to the condition that
every product around a 3-cycle or 4-cycle of blocks is a derangement. So the
graph is exactly an edge-labelling of K₅₇ by 1596 permutations of 56 points
(1540 after gauge-fixing), subject to 29,260 triangle and 1,185,030
quadrilateral constraints.

`reduction.py` implements this in both directions and checks it end to end:
Petersen and Hoffman–Singleton are decomposed into σ-tables, the tables satisfy
the derangement conditions, the tables rebuild into the original graphs, and
perturbing a single bijection breaks both the conditions and the graph.

A structure on t < 57 blocks is what the literature calls a *t-subgraph*.

## What the literature binds

*(Full texts were not reachable from this sandbox — outbound HTTPS to arXiv,
MDPI, ScienceDirect and Wikipedia is blocked by the egress proxy — so these
attributions come from search-result summaries and should be checked against
the originals.)*

| Result | Source |
| --- | --- |
| Not vertex-transitive | G. Higman |
| \|Aut\| ≤ 375 if odd, ≤ 110 if even | Mačaj & Širáň, *Search for properties of the missing Moore graph*, LAA 2010 |
| No involutions ⇒ \|Aut\| is odd ⇒ \|Aut\| ≤ 375 | Y. Ishida, *No involutions in the missing Moore graph*, arXiv:2606.29183 (Jun 2026) |
| Distance-regularity of induced subgraphs; a tight 400-coclique leaves a distance-regular graph on 2850 vertices, degree 49, diameter 3 | C. Dalfó, *A survey on the missing Moore graph*, LAA 569 (2019) 1–14 |
| Optimization approach converges "massively short" of the 92,625 edges | Smith & Montemanni, *The missing Moore graph as an optimization problem*, EURO J. Comput. Optim. 2023 |
| CP-SAT under a cyclic group extends the t-subgraph frontier from 15 to 20 | Smith & Montemanni, *Potential Subgraphs of the Missing Moore Graph*, Symmetry 16 (2024) 1563 |
| A construction using only a cyclic group of permutations is impossible | *The Moore Graph of Diameter 2 and Degree 57 via Cyclic Derangements*, Axioms 15 (2026) 332 |
| The 2020 claimed non-existence proof is not valid; the question is open | V. Faber, *Existence of a Moore graph of degree 57 is still open*, arXiv:2210.09577 |

## What was run here

### 1. The cyclic frontier, reproduced

`push_cyclic.py` grows a labelling one branch at a time with CP-SAT. It reaches
**t = 19** of 57 and stalls there across every restart (90 s per branch). The
literature frontier is 20.

`t19_cyclic.json` holds the certificate; `verify_frontier.py` checks it twice —
once arithmetically against the Z₅₆ conditions, and once by building the graph
it describes: 1084 vertices, girth 5, with 19 vertices already at their full
degree 57 and 1064 vertices at 19 of 57.

### 2. The cyclic ansatz cannot find Hoffman–Singleton

This is the load-bearing negative result. Requiring every σ_ij to lie in one
regular cyclic group collapses the problem to arithmetic in Z₅₆ — which is what
makes t = 20 reachable at all. But it is not a free assumption: if all σ_ij lie
in a common regular abelian group, acting by a generator on every block is an
automorphism of order k−1 fixing the root and all k of its neighbours.

`cyclic_search.py` searches that model exhaustively at the degrees where the
answer is known:

| degree | cyclic ansatz reaches | needs | verdict |
| --- | --- | --- | --- |
| 3 | t = 3 | 3 | finds the Petersen graph |
| 7 | t = 5 | 7 | **misses Hoffman–Singleton** |

The group theory says the same thing, and `reduction.py` computes it directly.
An automorphism fixing the root and every layer-1 vertex acts on block i by
some π_i with π_j σ_ij = σ_ij π_i, so the whole group is the set of admissible
π₀ — computable by inspection of the σ-table:

| degree | root-fixing automorphism group | element orders | ansatz |
| --- | --- | --- | --- |
| 3 | order 2 | 1, 2 | can work (needs order 2) |
| 7 | **trivial** | 1 | **empty** (needs order 6) |

So at degree 7 the ansatz has nothing to find, which is why the exhaustive
search stalls two branches short. At degree 57 the assumed automorphism has
order 56 — even — which the no-involutions theorem now forbids outright,
independently of the Axioms 2026 result.

So t = 20 is not the frontier of the problem. It is the frontier of a method
that provably cannot reach 57, and that would have missed the last Moore graph
anyone actually found.

### 3. Where the structure runs out, and why that is not evidence

`firstmoment.py` computes the expected number of ways to add each branch. The
per-branch factor crosses 1 at a definite point, and that crossover tracks the
empirical frontier closely:

| model | predicted max t | actual |
| --- | --- | --- |
| k=3, cyclic and general | 3 | 3 |
| k=7, cyclic | 5 | 5 (exact) |
| k=7, general | 5 | **7 — prediction too low** |
| k=57, cyclic | 22 | 19 here, 20 in the literature |
| k=57, general | 20 | unknown |

Exact counts back this up at k=7: 265 valid 3-block structures (the estimate
gives 265 exactly) and 101,040 valid 4-block structures (estimate 341,500).

The k=7 general row is the point. The same estimator that says the degree-57
graph should die at 20 branches — and that puts the expected number of complete
structures at 10^−412088 — says Hoffman–Singleton should die at 5 branches, and
Hoffman–Singleton exists. The constraints are positively correlated, and the
first-moment method is therefore falsely pessimistic. **A search stalling near
the crossover is not evidence of non-existence**: at degree 7 that identical
signal would have been wrong.

### 4. The cost of brute force

Measured at degree 7: 81,381,110 search nodes, 61 seconds, to the first
Hoffman–Singleton. Projecting the same tree-size model to degree 57:

| search | widest level | structures there | tree size |
| --- | --- | --- | --- |
| k=7, general (measured) | t=5 | 10⁶ | 10⁷·⁹ nodes |
| k=57, cyclic ansatz | t=22 | 10¹⁸³ | 10¹⁸⁵ nodes |
| k=57, general | t=20 | 10⁵⁹⁹² | 10⁶⁰⁶⁷ nodes |

Lloyd's bound on the total computation available in the observable universe is
about 10¹²⁰ operations. The general search exceeds that by ~5947 orders of
magnitude. Even the cyclic-restricted search — the dead-end one — exceeds it by
65.

Symmetry does not rescue this. The most any automorphism assumption can buy is
the order of the assumed group; that group now has odd order and order at most
375, worth a factor of 10²·⁶. And the assumption is not safe: a trivial
automorphism group is consistent with everything known, and Higman already
ruled out the symmetric case that would have helped most.

## Conclusion

The question was where the constraints bind hard enough to hand the rest to
brute force. They do not, and not by a small margin: the binding constraints
buy a couple of orders of magnitude against a shortfall of thousands. Nor is
the shortfall an artefact of a bad search formulation — the reduction used here
is exact and is the same one the published searches use.

Two things follow that are worth acting on:

1. **The t = 20 frontier should not be read as evidence against existence.**
   It is the ceiling of an ansatz that misses Hoffman–Singleton, and it sits
   exactly where a first-moment estimate that is demonstrably wrong at degree 7
   says it should sit.
2. **The leverage is structural, not computational.** The involutions result is
   the right shape: a trace–rank identity that closes a case without searching.
   The other tractable-looking target is Dalfó's tight-coclique residual — a
   distance-regular graph on 2850 vertices of degree 49 and diameter 3 — which
   is a strictly smaller object than the graph itself.

## Files

| file | what it does |
| --- | --- |
| `reduction.py` | the block/bijection reduction, both directions, validated on Petersen and Hoffman–Singleton |
| `known_constraints.py` | classical feasibility tests, formulas validated on the known Moore graphs |
| `cyclic_search.py` | the cyclic ansatz; exhaustive at small degree, CP-SAT at 57 |
| `push_cyclic.py` | incremental CP-SAT growth of the degree-57 frontier |
| `general_search.py` | the unrestricted search over S₅₆-valued labellings; exact counts at degree 7 |
| `run_k7.py` | driver for the degree-7 exact counts and brute-force cost |
| `firstmoment.py` | expected-count model, calibration table, brute-force budget |
| `verify_frontier.py` | independent verification of the t = 19 certificate |
| `t19_cyclic.json` | the certificate itself |

Run order: `python3 reduction.py`, `known_constraints.py`, `firstmoment.py`,
`verify_frontier.py` are all fast. `cyclic_search.py [seconds]` and
`run_k7.py` take minutes; `push_cyclic.py incremental 90 25` takes hours.

Requires `ortools` and Python 3.11+.
