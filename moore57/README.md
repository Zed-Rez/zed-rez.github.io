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
(Section 17 gives quantitative evidence that it probably does *not* hold at 57,
so treat this conditional as unlikely to fire.)
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

## Third pass: the gauged model, and why the degree-7 construction does not generalize

### 10. In the gauge, every bijection is a perfect matching

Fixing σ_0j = id collapses the involution property into something far more
usable. The triple {0,i,j} gives τ = σ_j0·σ_ij·σ_0i = **σ_ij** — so every σ_ij
with i,j ≥ 1 is itself a fixed-point-free involution, a perfect matching on the
56 points. (Verified: 1/1 for Petersen, 15/15 for Hoffman–Singleton.)

The quadrilateral {0,i,j,l} collapses to σ_jl·σ_ij, and a product of two
fixed-point-free involutions is fixed-point-free exactly when the matchings
share no edge. Over the three cyclic orders this makes M_ij, M_jl and M_il
pairwise edge-disjoint, so **for each branch i the 55 matchings {M_ij} form a
1-factorization of K₅₆** — exactly, since 55 × 28 = 1540 = |E(K₅₆)|. And
M_ij = M_ji, so the object is a symmetric array of matchings whose every row is
a 1-factorization, with a dual structure on the point side.

`gauged_search.py` implements this. It is by far the best model found here:

| model | finds Hoffman–Singleton in |
| --- | --- |
| general search over S₆ | 81,381,110 nodes / 61 s |
| gauged matching model | **2 s, monolithically** (no growth, no backtracking) |

At degree 57 it is still hard — CP-SAT returns UNKNOWN at 8 branches — because
the involution property is such a strong constraint. So the next move was to
stop searching and construct.

### 11. The obvious algebraic construction fails, structurally

The natural candidate indexes both branches and points by Z₅₅ ∪ {∞} and uses
the standard round-robin 1-factorization on both sides (`construct.py`). Every
condition through the root holds by construction. Every other condition fails —
0 of 240 triangles fixed-point-free, and no twist s ↦ us+v repairs any of them.

The reason is clean. The round-robin factors act on Z₅₅ as reflections
a ↦ 2s−a, so a triangle composite is a ↦ 2(s₁−s₂+s₃) − a, whose fixed point is
a = s₁−s₂+s₃ — and 2 is invertible mod 55 because **55 is odd**, so the fixed
point always exists. Any 1-factorization built from reflections on an
odd-order group is disqualified outright. This is the same parity obstruction
that kills the reflection ansatz, showing up again.

### 12. Why the degree-7 construction cannot generalize

Hoffman–Singleton's gauged array has an exceptional property: its 15
branch-pairs map **bijectively onto all 15 perfect matchings of K₆**. That is
the classical Sylvester duads-and-synthemes configuration, the structure behind
the outer automorphism of S₆ — and it is why the degree-7 case has a rigid,
findable, unique solution.

The coincidence that makes it possible is C(m,2) = (m−1)!!, i.e. branch-pairs =
available matchings:

| m = k−1 | branch pairs | perfect matchings of K_m | equal? |
| --- | --- | --- | --- |
| 2 (degree 3) | 1 | 1 | **yes** |
| 4 | 6 | 3 | no |
| 6 (degree 7) | 15 | 15 | **yes** |
| 8 | 28 | 105 | no |
| 56 (degree 57) | 1,540 | 8.7 × 10³⁶ | no |

It holds at exactly m = 2 and m = 6 — precisely the two degrees where a Moore
graph exists.

Read this carefully, because it is easy to over-claim. It is **not** evidence
of non-existence: having more matchings available is more freedom, not less,
and naive counting would favour existence at 56. What it does explain is why no
construction generalizes. At degrees 3 and 7 the structure is pinned by an
exceptional coincidence that supplies the whole algebraic scaffold; at degree
57 there is no scaffold, and 1,540 matchings must be selected from 8.7 × 10³⁶
with nothing forcing the choice. If the graph exists, this says it is probably
not an algebraic object — consistent with its being non-vertex-transitive with
|Aut| ≤ 375 of odd order, which is exactly what an inherently non-algebraic
object looks like.

### 13. A proof, not a search: reflection constructions are impossible at 57

The gauged model turns the reflection family into a counting question, and the
counting settles it outright.

Realise the non-root matchings as reflections in a fixed abelian group G of
order m = k−1, M_ij(x) = g_ij − x. Everything algebraic is then free: M_ij is
always an involution; it is fixed-point-free iff g_ij ∉ 2G; M_ij and M_il are
edge-disjoint iff g_ij ≠ g_il; triangle composites are reflections, hence
involutions.

So the construction needs, for each branch i, that the m−1 labels g_ij (j ≠ i)
be **distinct elements of G \ 2G**. Since |2G| = |G|/|G[2]|,

    |G \ 2G| = m − m/|G[2]| ≥ m − 1  ⟺  G[2] = G  ⟺  m is a power of two.

> **Theorem.** A reflection construction over an abelian group exists only when
> m = k−1 is a power of two.

| m | degree | usable labels (best group) | needed | verdict |
| --- | --- | --- | --- | --- |
| 2 | 3 | 1 (Z₂) | 1 | possible — it *is* the Petersen graph |
| 6 | 7 | 3 (Z₂×Z₃) | 5 | **impossible** |
| 56 | 57 | 49 (Z₂×Z₂×Z₂×Z₇) | 55 | **impossible — short by 6** |

`reflection_bound.py` enumerates every abelian group of each order and checks
that the counting verdict is exactly "m is a power of two". It cross-checks
against the solver in both decidable cases: `reflection.py` returns a Moore
graph at degree 3 and INFEASIBLE at degree 7. At degree 57 no search is needed
at all.

The argument generalizes past reflections, and this is the useful part: **any
ansatz must supply, per branch, 55 pairwise-disjoint fixed-point-free
involutions** — a full 1-factorization of K₅₆. Constructions that draw from a
smaller pool are dead on arrival. Translations by involutions in an abelian
group of order 56 supply at most 7; reflections supply at most 49. That single
criterion disposes of the natural algebraic families without any search, and it
is the rigorous core of why constructions never generalize past degree 7.

### 14. How far the involution property survives at degree 57

`feasibility.py` asks the decisive question directly. If the graph exists *and*
has the involution property, valid gauged structures exist for every t.

| branches | verdict | time |
| --- | --- | --- |
| 4 | **SAT** — verified, 229 vertices, girth 5 | 58 s |
| 5 | undecided (UNKNOWN) | 900 s |

No infeasibility was found, so the conjecture is not refuted; but nor is it
supported far. The model is brutally hard at m = 56: CP-SAT cannot decide five
branches in fifteen minutes, where it settles all seven branches of
Hoffman–Singleton in two seconds. That gap between m = 6 and m = 56 is itself
the honest measure of how much harder degree 57 is than anything solved.

### 15. What the involution property really says: a dihedral relation

Writing A = M_ij, B = M_jl, C = M_li (three fixed-point-free involutions), the
triangle condition (C·B·A)² = id is equivalent to C·B·A = A·B·C, and
multiplying on the left by A turns that into

    A (C·B) A = (C·B)^{-1}

> **M_ij conjugates M_li·M_jl to its inverse**: the group generated by the
> permutation M_li·M_jl and the involution M_ij is dihedral, with M_ij acting
> as a reflection.

`dihedral.py` verifies the equivalence of all three formulations and the
relation itself: 120/120 ordered triples on Hoffman–Singleton.

This also explains why no cheap counting obstruction exists at degree 57, and
that is worth knowing before anyone hunts for one. M_jl and M_li share the
index l, so they are edge-disjoint matchings; the union of two disjoint perfect
matchings is a union of even cycles, so the cycles of M_li·M_jl come in
equal-length pairs (verified 120/120). A fixed-point-free involution inverting
such a permutation always exists — pair the equal-length cycles. So **no single
triple is ever unsatisfiable**. Any obstruction at degree 57 must be global
across all C(56,3) = 27,720 triples simultaneously, which is exactly the
regime solvers are worst at, and exactly what the frontier data shows.

### 16. The frontier under the strong model

| model | assumption | frontier at degree 57 |
| --- | --- | --- |
| cyclic (published) | order-56 automorphism — provably absent | 19–20 branches, but off-path |
| general | none | 12 branches from scratch |
| gauged matching | involution property (conjectural at 57) | **4 branches** |

Both monolithic (`feasibility.py`) and incremental (`gauged_extend.py`) growth
stall at the same place: 4 branches solve in under a minute, 5 is UNKNOWN after
600–900 s, never INFEASIBLE. The stronger the model, the shorter the reach —
which is what one expects when the constraints are real and the solver, not the
mathematics, is the binding limit.

### 17. Testing my own conjecture, and finding against it

Every positive data point for the involution property comes from m = 2 and
m = 6. Those are small, so `control.py` asks the obvious control question: for
three *pairwise edge-disjoint* perfect matchings — which is what M_ij, M_jl,
M_li must be — how often is the composite an involution by chance?

| m | triples | composite is an involution |
| --- | --- | --- |
| 4 | 6 | 100% |
| 6 | 480 | **25%** |
| 8 | 197,820 | 26.1% |
| 10 | 200,000 sampled | 0.86% |
| 16 | 200,000 sampled | 0.0065% |
| 24 | 200,000 sampled | **0** |
| 56 | 200,000 sampled | **0** |

So the property is *real* at m = 6 — a 25% base rate means Hoffman–Singleton's
210/210 is a genuine signal, not an artefact of a small group. But the rate
collapses as m grows, and analytically the per-triple probability is
I(56)/56! ≈ 10⁻³⁵.

A first-moment count for the gauged model then reads:

| degree | freedom | cost of conditions | expected count |
| --- | --- | --- | --- |
| 7 | 10¹⁸ | 10⁻²⁰ | 10⁻² |
| 57 | 10⁵⁶⁸⁸⁶ | 10⁻⁹⁷¹⁷⁵⁷ | **10⁻⁹¹⁴⁸⁷¹** |

At degree 7 the property is short by 2 orders of magnitude, and the graph
exists, so correlation bridges it easily. At degree 57 it is short by 914,871.

**This cuts against my own conjecture, and I am reporting it as such.** The
first-moment method is unreliable — I demonstrated that earlier, where it is
wrong at degree 7 by construction. But being wrong by 2 orders and being wrong
by 900,000 are not the same kind of claim. The likeliest reading is that a
degree-57 Moore graph would **not** have the involution property: it is a
genuine feature of m = 2 and m = 6 whose cost outruns the available freedom
long before m = 56.

If that is right:

- the gauged matching model is searching for something that does not exist,
  which is a better explanation of its four-branch ceiling than solver weakness;
- the earlier claim that the published t = 20 frontier is "off-path" was
  conditional on the conjecture and should be withdrawn to that extent;
- the cyclic ansatz remains dead, but on the independent grounds proved in
  sections 2, 7 and 13 — no order-56 automorphism, and the reflection bound.

The residue that survives regardless: the exact reduction, the general
colouring-CSP search model, the reflection impossibility theorem, the S₆
generation result, the duads/synthemes explanation of degree 7, and the
calibration showing that a stalled search is not evidence of non-existence.

### 18. Branch extension as a colouring problem, and the absence of local obstructions

Adding a branch to a t-branch structure is exactly a colouring problem. The
unknowns are the (t−1) × 56 cells p_i[x] = σ_{i,t}(x); each row must be a
permutation, so **each row is a clique of size 56** and **each colour class is
a transversal** — one cell per row. The triangle and quadrilateral conditions
are binary disequalities joining cells across rows.

For the verified 19-branch structure the conflict graph is **1008 cells,
361-regular** (55 within-row, plus exactly 18 per each of the 17 other rows: one
from the triangle through those two branches and 17 from quadrilaterals).
Extending it means partitioning those 1008 cells into 56 independent
transversals of size 18.

That reformulation makes several cheap necessary conditions available, and it
is worth knowing that **all of them pass**:

| test | result | settles it? |
| --- | --- | --- |
| an independent transversal exists | yes, witness verified | no |
| clique number vs. 56 available values | exactly **56** (a single row) | no — tight |
| Hoffman chromatic bound | χ ≥ 19.77 | no |
| ratio bound on independent sets | α ≤ 51, classes need 18 | no |
| 2 or 4 disjoint transversals | UNKNOWN at 300 s each | no |

So the 19-branch structure has **no local obstruction** to being extended: it
is not a dead end that cheap mathematics can expose. The clique bound being
*exactly* 56 is the striking part — the colouring is a perfect fit, with every
row forced to use every value once and all cross-row conflicts absorbed without
ever forcing a 57th colour.

This is the same conclusion the dihedral analysis reached from the algebraic
side: no single triple, and no local test, is ever unsatisfiable. Any
obstruction at degree 57 has to be global — which is precisely the kind a
solver cannot find and a counting argument cannot see.

### 19. Local search: the assumption-free frontier moves to 14

Pass 7 established that branch extension is a dense equitable-colouring
problem. CP-SAT is a poor fit for those; local search is the standard tool, and
it had not been tried.

`anneal.py` keeps one permutation per row (so the row structure is maintained
by construction, never propagated) and moves by swapping two values within a
row, biased towards cells currently in conflict. It runs at ~56,000 moves/s.

**Validated first**: it extends Hoffman–Singleton's 6-branch structure to 7 in
9,086 moves, and the result rebuilds as a genuine Moore graph of degree 7.

Applied to the assumption-free search, it advances the frontier:

| step | result |
| --- | --- |
| 12 → 13 branches | solved, verified (15.6M moves, 128 s) |
| 13 → 14 branches | solved, verified (13.3M moves, 127 s) |
| 14 → 15 branches | plateaus at cost 7–12 of 56,784 constraints |

`hybrid.py` then hands the near-solution to CP-SAT as a hint, and separately
runs large-neighbourhood repair with the conflict-free rows frozen. Both return
UNKNOWN at 300 s. So **14 branches** is the honest, assumption-free frontier
reached here — up from 12.

### 20. The cyclic frontier structures are empirically hostile to extension

The same annealer, run on the verified 19-branch *cyclic* structure, behaves
completely differently:

| structure | best cost after annealing | relative residual |
| --- | --- | --- |
| general, 14 branches | 7 of 56,784 | 0.012% |
| cyclic, 19 branches | **581** of 154,224 (44.3M moves, 900 s) | 0.377% |

General structures are driven to exactly zero, repeatedly. The cyclic structure
cannot be moved below 581 violations by 44 million moves. That is a 30-fold
difference in relative residual, and more tellingly a qualitative one: one kind
of structure completes, the other never approaches completion.

This matters because it is **independent of the involution conjecture** that
section 17 undermined. The earlier claim that the published t = 20 frontier is
"off-path" rested on that conjecture and was withdrawn. This is separate
evidence for the same conclusion, resting only on measurement: the cyclic
structures are not merely restricted, they are empirically hostile to being
extended at all, even when the cyclic assumption is dropped and arbitrary
permutations are allowed.

It remains evidence, not proof — local search failing is not impossibility, and
the two instances differ in size. But it is the strongest signal available that
climbing to 20 branches under the cyclic ansatz is not progress towards the
graph.

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

3. **The involution property is probably false at degree 57** — see section 17.
   It is verified at every degree where a Moore graph exists and is not implied
   by the conditions any published search enforces, but its cost grows far
   faster than the available freedom, and a control experiment puts the
   shortfall at 2 orders of magnitude at degree 7 against 914,871 at degree 57.
   That asymmetry is itself a structural difference between 57 and the degrees
   that work, and it is the sharpest thing this project produced.

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
| `gauged_search.py` | the gauged matching model: sigma_ij are perfect matchings, rows are 1-factorizations |
| `sweep_gauged.py` | pushing the gauged model upward at degree 57 |
| `construct.py` | the round-robin algebraic candidate and why it fails |
| `reflection_bound.py` | the counting proof that reflection constructions need m a power of two |
| `feasibility.py` | decisive small-t feasibility of the involution property at degree 57 |
| `gauged_extend.py` | incremental growth of the gauged structure at degree 57 |
| `dihedral.py` | the involution property restated as a dihedral relation |
| `control.py` | control experiment on the involution base rate, and its severity |
| `transversal.py` | branch extension as a transversal-colouring problem |
| `clique.py` | clique and spectral obstructions on the conflict graph |
| `anneal.py` | local search for branch extension (row-swap simulated annealing) |
| `hybrid.py` | annealing to get close, CP-SAT plus LNS to close the gap |
| `Moore57.lean` | Lean formalization of the block decomposition (not machine-checked) |

Run order: `python3 reduction.py`, `known_constraints.py`, `firstmoment.py`,
`verify_frontier.py` are all fast. `cyclic_search.py [seconds]` and
`run_k7.py` take minutes; `push_cyclic.py incremental 90 25` takes hours.

Requires `ortools` and Python 3.11+.
