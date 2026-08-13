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

## Second pass: dropping the cyclic assumption, and a new constraint

### 5. The general search is tractable after all

Adding *one* branch to an existing structure turns every constraint into a
**binary disequality between two cells** of the unknowns. With p_i := σ_{i,r},
the triangle h→i→r→h condition is just

    p_i[ σ_hi(x) ]  ≠  p_h[ x ]

because σ_hi is already known, so the index is a constant. Same for all three
cyclic orders of each quadrilateral. So adding a branch is a list-colouring
problem — (r−1)·56 cells, 56 colours, all-different rows — with no group
assumption anywhere (`general_extend.py`).

From scratch this reaches 12 branches in about a minute. It also re-verifies
the 19-branch certificate. This is the honest search model; the published one
is a special case of it.

### 6. The involution property

In **both** Moore graphs that exist, every triangle composite

    τ(a,j,b) = σ_ba · σ_jb · σ_aj

is not merely a derangement — it is a **fixed-point-free involution**. All 6 of
them in Petersen, all 210 in Hoffman–Singleton, every one of cycle type
(2,2,2). Equivalently: the Latin square of every ordered branch pair is
symmetric (verified, 42/42 pairs), equivalently each pair of branches sees the
other k−2 as a **1-factorization of K₅₆**.

This is not implied by the conditions the search enforces:

| structure | involutive composites |
| --- | --- |
| Petersen | 6 / 6 |
| Hoffman–Singleton | 210 / 210 |
| cyclic frontier, t=19 | 66 / 5814 |
| general growth, t=12 | **0 / 1320** |

Two things make it credible rather than a coincidence:

- **It independently implies the published cyclic-impossibility theorem.** In
  the cyclic model τ is a translation, and a translation is an involution only
  if it is by exactly 28 — which forces *every* triangle sum to 28, and then
  the quadrilateral (0,i,j,k) sums to 56 ≡ 0, violating its condition. So
  involutions ⇒ the cyclic ansatz dies at t=4. That is exactly the Axioms 2026
  result, recovered here as a corollary of a property found from
  Hoffman–Singleton.
- **It explains why the ansatz misses Hoffman–Singleton** — the same mechanism,
  at degree 7.

**If the property holds at degree 57, every published t-subgraph is off-path.**
The t=20 frontier structures have 66 involutive composites out of 5814; they
cannot be extended to the graph no matter how much compute is thrown at them.
That is a much sharper claim than "the ansatz is a dead end".

Status: **verified at degrees 3 and 7, conjectural at 57.** I did not prove it.
A proof would be the most valuable single thing here.

**The caveat that cuts against it**, stated plainly because it matters: the
entire evidence base is two graphs that are vertex-transitive and rank 3, with
automorphism groups of order 120 and 252000. The degree-57 graph is known *not*
to be vertex-transitive (Higman) and to have |Aut| ≤ 375 of odd order. A
property that holds in the two most symmetric cases imaginable is exactly the
kind of property that can be an artefact of symmetry rather than a theorem
about Moore graphs. I tried and failed to prove it from the local axioms
(triangle-free plus a unique common neighbour for non-adjacent pairs); the
natural attempts get to a 6-cycle and stop.

What holds the other way is that the property implies a theorem about degree 57
specifically — the cyclic-impossibility result — which was proved without any
symmetry assumption. That is consistency, not proof.

### 7. Why no group ansatz can work

Hoffman–Singleton's bijections generate the **full symmetric group S₆** (order
720), across eight distinct cycle types. Nothing about the individual σ_ij is
structured; what is rigid is the composites. So confining the σ_ij to a small
group is structurally misdirected. Two ansätze tested to destruction:

| ansatz | σ_ij | composite is | degree 3 | degree 7 |
| --- | --- | --- | --- | --- |
| cyclic (published) | x + a_ij | translation | finds Petersen | stalls at 5 of 7 |
| reflection | g_ij − x | **always an involution** | finds Petersen | **INFEASIBLE** |

The reflection ansatz (`reflection.py`) is interesting because it gets the
involution property for free, makes all triangle conditions collapse to a
parity condition solved by taking every g_ij odd, and leaves only the
quadrilateral conditions — a search over 28 values per pair instead of 56!.
It builds the Petersen graph. At degree 7 it is infeasible, and since Z₆ is
the only abelian group of order 6, no abelian reflection ansatz can produce
Hoffman–Singleton either.

### 8. A validated involution-constrained search

`involution_search.py` imposes the property. The condition has a cheap form —
D(x)=y is just `p_a[x] == p_b[σ_ab[y]]`, so "D is an involution" is a
biconditional between two equalities at constant indices, and for pairs
involving the gauge branch it collapses to a native `AddInverse`. With
backtracking, the model **recovers Hoffman–Singleton** (210/210 involutive),
which validates it.

At degree 57 it currently stalls at 4 branches: the constraint is strong enough
that blind CP-SAT search struggles. The natural next step is to stop searching
blind and *seed* from an explicit 1-factorization of K₅₆, which is what the
property says the structure must be.

### 9. Lean

`Moore57.lean` formalizes the block decomposition: the definition of a Moore
graph in the "friendship at distance two" form, the block sizes, independence
of blocks, and the matching lemma (every vertex of one block has exactly one
neighbour in every other block) — the fact the whole reduction rests on. The
order and spectrum computations are stated and left as `sorry`.

It is **not machine-checked**: this sandbox has no Lean toolchain and no
network route to one (elan, leanprover.github.io and GitHub are all blocked by
the egress proxy), so it has not been through the kernel.

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

And the second pass adds a third, which is the most actionable thing here:

3. **Prove or refute the involution property at degree 57.** It is verified at
   every degree where a Moore graph exists, it is not implied by the conditions
   every published search enforces, and it independently re-derives a 2026
   theorem. If it is a theorem, the entire published search frontier is
   off-path and should be replaced by a 1-factorization-seeded search; if it is
   false at 57, that itself is a strong structural asymmetry between degree 57
   and the degrees that work.

### What I did not get

I did not find the graph, and nothing here suggests it is within reach. The
frontier moved from "20 branches under an ansatz that cannot work" to "12
branches under an honest model, 19 verified, plus a constraint that says the
20-branch structures were never on a path to a solution". That is progress on
the *design*, not on the *construction*.

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
| `general_extend.py` | the general (non-cyclic) search: adding a branch as a colouring CSP |
| `latin.py` | the Latin square of each branch pair, and its symmetry |
| `involution.py` | the involution audit across known graphs and search structures |
| `involution_search.py` | search with the involution property imposed; validated at degree 7 |
| `run_inv57.py` | driver for the degree-57 involution-constrained growth |
| `reflection.py` | the reflection ansatz x -> g - x |
| `Moore57.lean` | Lean formalization of the block decomposition (not machine-checked) |

Run order: `python3 reduction.py`, `known_constraints.py`, `firstmoment.py`,
`verify_frontier.py` are all fast. `cyclic_search.py [seconds]` and
`run_k7.py` take minutes; `push_cyclic.py incremental 90 25` takes hours.

Requires `ortools` and Python 3.11+.
