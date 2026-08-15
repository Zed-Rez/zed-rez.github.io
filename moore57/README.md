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

### 20. The gauge turns the conjecture into a 1-factorization statement

Gauge-fix σ_0j = identity for *every* branch. In that gauge the involution
property becomes something far more concrete:

> every σ_ij with i,j ≥ 1 is a **fixed-point-free involution** of the 56 points,
> and for each fixed i the family { σ_ij : j ≠ i } is a **1-factorization of
> K₅₆**.

Verified on both graphs that exist: after gauging, all 15 of
Hoffman–Singleton's bijections have cycle type (2,2,2), and every row is a
1-factorization of K₆. Petersen likewise.

The row condition has no slack whatsoever: 55 matchings × 28 edges = 1540 =
C(56,2) exactly. And the space collapses:

| | per unknown | raw space (1540 unknowns) |
| --- | --- | --- |
| general model | 56! = 10⁷⁴·⁹ | 10¹¹⁵²⁷² |
| 1-factorization model | 55!! = 10³⁶·⁹ | 10⁵⁶⁸⁸⁶ |
| **reduction** | | **10⁵⁸³⁸⁶** |

**How hard does it prune, exactly?** At degree 7 the whole space is enumerable,
so this is measured rather than estimated (`involution_prune.py`):

| branches | valid structures | involutive | pruning |
| --- | --- | --- | --- |
| 3 | 265 | **15** | 17.7× |
| 4 | 101,040 | **120** | 842× |

The 15 is not a coincidence: it is 5!!, exactly the number of fixed-point-free
involutions of 6 points — precisely what the model predicts σ₁₂ must be.

And at degree 7 the filter is **sound**: Hoffman–Singleton is the unique Moore
graph of that degree and all its composites are involutions, so every partial
structure that extends to a complete graph is involutive. The filter discards
nothing that could have led to the graph — *at that degree*. Soundness at 57
remains the conjecture.

`factorization_search.py` implements this model with the full propagation it
allows: cells are fixed-point-free, avoid every edge their row already uses,
are pairwise distinct down each column, and satisfy every original
triangle/quadrilateral disequality. It **rebuilds Hoffman–Singleton**, and at
degree 57 it runs far past the previous involution encoding (which stalled at
4 branches).

### 20b. The conjecture in its most attackable form

Everything conditional here rests on one statement, and it is worth stating in
the form that mentions no bijections, no gauge and no coordinates
(`conjecture.py` checks all three forms):

> **Form C.** Let v be a vertex, u a neighbour of v, and a_x, a_y two distinct
> neighbours of u other than v. There are exactly k−1 five-cycles through the
> path a_x − u − a_y; each is a_x − w − z − a_y − u with w in branch i and z in
> branch j. Write φ_{x,y}(i) = j. Then **φ_{x,y} is an involution.**

In words: if you can get from a_x to a_y in two steps leaving by branch i and
arriving by branch j, you can also do it leaving by j and arriving by i. A
symmetry of the pentagon structure and nothing more.

| | Petersen | Hoffman–Singleton |
| --- | --- | --- |
| Form A (composites are involutions) | 6/6 | 210/210 |
| Form B (gauged bijections; rows are 1-factorizations) | yes | yes |
| Form C (φ_{x,y} is an involution) | 2/2 | 30/30 |

**Correction — these are not all equivalent.** I claimed they were, and that
was wrong. With the gauge, the triples containing branch 0 collapse to
"σ_ij is an involution", which is Form B; but a triple of three *non-zero*
branches is a product of three involutions, and that need not be an involution.
The true relations are

    A ⟹ B,  A ⟹ C,  B ⟺ C,  and **B does not imply A**.

Form A is strictly the strongest, and it is the one that matters. This is not a
pedantic point — it changes the results below.

### 20c. The three frontiers, and what "frontier" even means

| model | assumption | branches reached | can it complete? |
| --- | --- | --- | --- |
| cyclic (published) | all σ in one cyclic group | 20 (lit.), 19 (here) | **no** — provably cannot reach 57, and misses Hoffman–Singleton |
| general | none | 12 | unknown; the honest model |
| 1-factorization | the involution conjecture | 10 | unknown; strongest propagation |

The 1-factorization frontier being *lower* is the constraint doing its job, not
the search being worse. It rebuilds Hoffman–Singleton at degree 7 where the
cyclic model cannot, and it prunes by 842× at four branches.

The real point is what "frontier" means. If the conjecture holds at degree 57,
then the 19- and 20-branch cyclic structures are not partial Moore graphs in
any useful sense — they have 66 involutive composites out of 5814 and cannot
extend to anything. The published number is measuring how far a doomed model
can be pushed, not how much of the graph is known. Under the conjecture the
honest figure is 10 of 57, and it is 10 branches that could actually be part of
a Moore graph.

### 20d. Probabilistic search — and what it says about the state space

Dropping the guarantee entirely: simulated annealing over the σ-table, cost =
the number of fixed points summed over every triangle and quadrilateral
composite. Cost 0 is exactly a Moore graph. Two state spaces, same cost
function, same move budget (`anneal.py`, `anneal_fast.py`).

**At degree 7, where the answer exists, the two spaces behave completely
differently:**

| state space | move | degree-7 result |
| --- | --- | --- |
| arbitrary permutations | compose with a transposition | **0 of 6 restarts** solve, 300k iterations each |
| fixed-point-free involutions | rewire two edges of the matching | **6 of 6 restarts** solve, in 190–840 iterations |

Initial cost is ~120–135 and it goes to 0 almost immediately in the involution
space, and never in the permutation space. Each solve rebuilds
Hoffman–Singleton.

This is independent evidence for the conjecture that has nothing to do with the
earlier arguments: the involution structure is not merely a filter that happens
to be true of the known graphs — it is the space in which the problem is
*searchable at all*. In the unrestricted space the landscape is hopeless even
when a solution is known to exist a few hundred moves away.

**A methodological note worth recording.** The first sweep reported failure at
8 branches. The bug was that the cooling schedule was indexed by iteration
count while the run was cut off by a wall-clock deadline, so the temperature
never left its starting value and the "annealer" was a hot random walk. Driving
the schedule by elapsed time instead turned "best cost 62" into solved-to-zero
at 8 and 10 branches. Worth stating because a plateau is exactly what a broken
schedule and a genuine obstruction look like from the outside.

**Grow and repair.** Cold annealing at a fixed t throws away everything already
known; the CP-SAT growth never revises a branch once placed. `grow_anneal.py`
does both: append a branch with random bijections, then anneal the *whole*
table, so the search may revise branch 3 in order to fit branch 12. Budgets
escalate (28 s, 84 s, 252 s, …) because a long budget makes the cooling
schedule sluggish and burns the allowance on branches that would fall in
seconds.

Probabilistic frontiers at degree 57, every certificate verified independently
by building the graph fragment and confirming girth 5:

| state space | branches at cost 0 | fragment | next branch |
| --- | --- | --- | --- |
| fixed-point-free involutions (Form **B** only) | **11** | 628 vertices, girth 5 | t=12 reached cost 26 of ~530 |
| arbitrary permutations | **13** | 742 vertices, girth 5 | t=14 reached cost 48 of ~930 |

**What the correction costs.** The "involution state space" imposes Form B, not
Form A. `locality.py` audits every certificate in the repository and the
11-branch one has only **270 of 990** triangle composites involutive — it
satisfies B and violates A. Since any sub-structure of a Moore graph inherits
Form A (its composites are composites of the whole graph), a structure
violating A cannot extend to a Moore graph *if A holds*. So my own best
certificates are off-path under my own conjecture — exactly the criticism I
levelled at the published cyclic frontier, now applying to me.

The search that imposed the full Form A is `involution_search.py`, and it
stalled at 4–5 branches. That, not 11, is the honest frontier under the
conjecture. Verified against Hoffman–Singleton: its first t branches satisfy
Form A exactly, for every t from 3 to 7.

Annealing beats the exact solver on this problem: CP-SAT growth reached 10 and
12 branches on the same models where annealing reaches 11 and 13.

**Large-neighbourhood search** (`lns.py`) adds the one move neither method has —
revising an *old* branch. Freeing a single branch keeps the model in the easy
form (every condition involving branch r involves only column-r bijections, so
it stays binary disequalities with no products of unknowns), so an old branch
can be deleted and re-solved exactly while forbidding the column it had. It
works, but at 11 branches both the add and the revise time out in CP-SAT where
annealing succeeds — on this problem the exact solver is the weaker tool, and
that is worth knowing before anyone invests in a bigger CP model.

The general space gets further only because at small t it is far less
constrained — a weaker structure, not a better result. And the honest baseline
is that the 19-branch cyclic certificate is itself a valid general structure,
so probabilistic search from scratch has not beaten what construction already
gives.

The general-space number is higher only because at small t that model is far
less constrained — it is a weaker structure, not a better result. And note the
19-branch cyclic certificate is itself a valid general structure, so the
unconditional general frontier is ≥ 19 by construction.

### 20e. Seven methods, compared honestly

Everything tried on this problem, with what it actually achieved:

| method | degree-7 check | degree-57 reach | note |
| --- | --- | --- | --- |
| complete DFS (guaranteed) | finds HoSi, 765,621 nodes | 12 branches in 242 s | correct, never finishes |
| cyclic ansatz + CP-SAT | **misses HoSi** (5 of 7) | 19–20 branches | provably cannot complete |
| reflection ansatz | **infeasible at 7** | — | dead on arrival |
| CP-SAT growth, general | — | 12 branches | never revises a branch |
| CP-SAT growth, 1-factorization | rebuilds HoSi | 10 branches | strongest propagation |
| LNS (delete + re-solve a branch) | — | no gain | both add and revise time out at 11 |
| **annealing, grow-and-repair** | 6/6 in involution space, **0/6** in permutation space | **11 involution / 13 general** | best method here |
| parallel tempering | 4/4 | 58 at t=12 vs annealing's 26 | loses even when tuned |

Two details worth keeping from the tempering attempt. The swap acceptance rate
is the diagnostic: at 0.95 the ladder is so dense that neighbouring replicas
are indistinguishable and the method is worthless (best energy 428); retuned to
a colder, wider ladder with rate 0.43 it improves sevenfold to 58. It still
loses to a single well-scheduled annealing trajectory, because R replicas split
the move budget R ways and this landscape rewards one long descent more than
many short ones.

Focused, WalkSAT-style move selection — picking the pair to move in proportion
to the unsatisfied cost it carries — was also tried and is within noise (mean
51 against 53 on equal budgets). So the difficulty is not where the moves are
aimed, and not the cooling schedule. It is the hard tail: at 12 branches the
cost falls from ~570 to 14 and then resists, which is the familiar behaviour of
a constraint problem near its satisfiability threshold.

### 20f. Is the search stuck because of the searcher, or the object?

Two experiments aimed at that question rather than at the frontier.

**Where the residual sits.** When annealing plateaus at 12 branches with cost
~11–30, is the leftover concentrated in one bad branch or spread out?
`hybrid.py` deletes each branch in turn and recomputes. Best single deletion
leaves cost 14, not 0 — the runners-up are 16, 17, 19, 19. **The residual is
spread across branches, not carried by one.** So there is no small exact
sub-problem to hand to a solver, which is why the anneal-then-solve hybrid does
not fire, and why LNS on a single branch cannot help either.

**How many valid structures are dead ends?** `deadends.py` samples valid
t-branch structures at random and asks CP-SAT exactly whether each extends —
at small t the solver terminates with a definite answer rather than a timeout.

| branches | sampled | extend | **provably dead ends** | unknown |
| --- | --- | --- | --- | --- |
| 4 | 6 | 6 | **0** | 0 |
| 5 | 6 | 6 | **0** | 0 |
| 6 | 6 | 6 | **0** | 0 |
| 7 | 6 | 6 | **0** | 0 |

Not one dead end up to 7 branches. So the space is *not* trap-rich early: a
searcher that reaches 7 branches has not already doomed itself, and the
stalling at 11–14 is not explained by early mistakes. What is left is the plain
growth of constraint density — the number of conditions grows like C(t,3) +
3·C(t,4) while the freedom per branch grows only linearly.

And a direct exact question, asked of the verified 11-branch structure: does it
extend? CP-SAT returned UNKNOWN after 480 s on 30,800 conditions. No
conclusion — the honest answer, and the reason the "is it the searcher or the
object" question stays open at the frontier even though it is settled below it.

### 20g. The measured cost curve, and where it puts 57

`bruteforce.py` answered the feasibility question for the *complete* search by
exact counting. `scaling.py` answers it for the *best* method found here —
grow-and-repair annealing — using its own recorded timings rather than a model.
The cost of placing branch t is every failed attempt plus the successful one:

| branch | involution space | general space |
| --- | --- | --- |
| 8 | 10 s | 10 s |
| 9 | 13 s | 11 s |
| 10 | 21 s | 13 s |
| 11 | **638 s** | 23 s |
| 12 | 4048 s, unsolved | 126 s |
| 13 | — | **705 s** |
| 14 | — | 4048 s, unsolved |

Fitted tail growth: **×3.65 per branch** (involution), **×3.93** (general).
Projecting to the final branch:

> the last branch alone would cost 10²⁸–10²⁹ seconds — **about 10²¹ years** on
> this machine.

So the two approaches fail for genuinely independent reasons: the complete
search cannot finish for *counting* reasons (≥10¹⁴⁸ isomorphism classes at four
branches, a 10¹³⁵ shortfall against a century of compute), and the best
heuristic cannot finish for *measured* ones (a ~4× cost multiplier per branch,
with 45 branches still to place). Neither is within astronomical distance.

### 20h. What the dead-end measurement means

Extending `deadends.py` upward, over 34 sampled valid structures:

| branches | sampled | extend | **dead ends** | undecided |
| --- | --- | --- | --- | --- |
| 4–7 | 24 | 24 | **0** | 0 |
| 8 | 4 | 4 | **0** | 0 |
| 9 | 4 | 3 | **0** | 1 |
| 10 | 4 | 0 | 0 | **4** |

Not one provable dead end anywhere the exact solver could decide, and at 10
branches it can no longer decide at all.

That is worth stating carefully, because it cuts against the prevailing read.
The published optimization work converges "massively short" and takes that as
evidence of non-existence. But up to 9 branches, valid structures essentially
always extend — the object is not obstructing. What changes with t is the cost
of *finding* the extension, which the table above shows growing about fourfold
per branch. **The barrier here is measured to be computational, not
structural** — over the range where the two can be told apart at all.

### 20i. Seeding row 1 with an explicit 1-factorization — another symmetric dead end

Under the conjecture the gauge makes row 1 of the σ-table *literally* a
1-factorization of K₅₆, so it need not be searched for: write one down. The
round-robin ("circle") factorization is the obvious candidate, and at degree 7
pinning it costs nothing at all, because K₆ has a **unique** 1-factorization up
to isomorphism. That makes the degree-7 run a clean test rather than a lucky
guess — and it passes, 6 of 6 restarts (`seeded_factorization.py`).

At degree 57 it does not help. Pinned row 1 reaches cost 30 and 37 at 250 s
against 26 and 28 for the unpinned baseline on the same budget: slightly worse,
not better.

My first explanation was that the round-robin factorization is highly
symmetric while the degree-57 graph is known *not* to be vertex-transitive
(|Aut| ≤ 375, odd), so pinning a symmetric object into an asymmetric one
repeats the cyclic ansatz's mistake. That explanation makes a prediction, so I
tested it: pin row 1 to a *randomised* 1-factorization instead, generated by
walking the standard alternating-cycle Markov chain away from the round-robin
one.

**The prediction failed.** The randomised factorization did worse, not better —
cost 37 against the round-robin's 29 on the same budget. (Single seed each, so
this is weak evidence for any ordering between them, but it is squarely against
the direction my explanation predicted.)

So the symmetry story is wrong here, and I am striking it. What the two runs
agree on is that *pinning at all* costs something: both pinned variants are
worse than the unpinned baseline. The plausible reading now is simply that
removing 55 unknowns from the move set removes freedom the annealer was using —
row 1 is not a free parameter to be guessed but part of what has to be
co-optimised with everything else.

### 20j. Iterated local search — the one algorithmic change that helped

Plain annealing gets one shot at its schedule: if it lands in a basin at cost
11 it stays there. Iterated local search keeps the best state seen, and when no
improvement has appeared for a while it *restores* that state and kicks it with
a handful of unconditional random moves, then descends again. That is the
standard remedy for a small stubborn residual, and it is the only algorithmic
change tried here that produced a consistent gain:

| seed | plain annealing | ILS |
| --- | --- | --- |
| 11 | 46 | **40** (2 kicks) |
| 12 | 44 | **32** (3 kicks) |

Same 120 s budget, same state space, t = 12. Worth contrasting with everything
else attempted at the search level: focused move selection was within noise,
parallel tempering lost even when tuned, pinning row 1 hurt. ILS is the one
that moved.

It does not change the picture — the measured ×3.65 per branch is what governs
the projection to 57, and a constant-factor improvement in cost per attempt
does not touch it. It is recorded because it is the one thing that did work.

### 20k. Searching for Form A directly

With the correction in hand, the right search is for Form A itself.
`formA_search.py` puts it in the annealer's cost — fixed points of every
triangle composite, plus its involution defects, plus the quadrilateral fixed
points — and searches the fixed-point-free-involution space with ILS. Cost 0 is
a Moore fragment that is Form A compliant.

Validated at degree 7: **4 of 6 restarts** reach cost 0, each verified as a
genuine Moore graph with all 210 composites involutive.

At degree 57 the honest Form A frontier is **4 branches** (verified, 229-vertex
girth-5 fragment). Five branches did not fall: best cost 80 from an initial
~244. That matches the old CP-based Form A search, which stalled in the same
place with completely different machinery.

That gap is itself the interesting thing. At degree 7, Form A is *easy* — it
falls in seconds and the complete graph satisfies it. At degree 57 it is hard
at five branches out of fifty-seven. Which raises the sharpest test of the
conjecture available:

> If no 5-branch Form A structure exists at degree 57, then Form A is **false**
> for degree 57 — because a Moore graph satisfying it would contain such
> structures — and every conditional result here collapses.

`formA_exists.py` puts that to CP-SAT: extending a given 4-branch Form A
structure is a finite model, and INFEASIBLE is a proof that that structure is a
dead end. So far the solver times out rather than deciding (2 samples, 130 s
each; longer runs in progress). No conclusion yet, in either direction — and I
would rather leave it open than read a timeout as evidence.

### 20l. An unconditional 14-branch structure

The general-space push closed t = 14 after 2063 s and 6.0 M moves, from cost
918 to 0. Verified independently: valid 14-block structure, 799-vertex fragment
(exactly 1 + 14 + 14·56), girth 5.

It carries **0 of 2184** involutive composites, so under Form A it is off-path
— but it assumes nothing, and as an unconditional object it is the largest
from-scratch search result here. The 19-branch cyclic certificate is still
larger and also unconditional, so this is not a record; it is a
differently-built structure of comparable size.

### 20m. Form A has a clean algebraic form, and a constructive answer

Each σ is an involution, so τ⁻¹ = σ_ab σ_bc σ_ca while τ = σ_ca σ_bc σ_ab.
Hence Form A's triple condition is exactly

> **σ_ca σ_bc σ_ab = σ_ab σ_bc σ_ca**

which is automatic when the bijections **commute**. Commuting fixed-point-free
involutions generate an elementary abelian 2-group acting freely, and a free
action on 56 points needs |E| | 56, so E = (Z₂)³ is the largest available
(56 = 8 × 7, seven orbits).

With the gauge, everything collapses to arithmetic in (Z₂)³ on the non-zero
branches — a_ij ≠ 0, a_ij ⊕ a_jk ≠ 0 (a proper edge colouring), a_ij ⊕ a_jk ⊕
a_ki ≠ 0, and a_ij ⊕ a_jk ⊕ a_kl ⊕ a_li ≠ 0 — with the triple condition free
because the group is abelian. That is a tiny exact search (`formA_abelian.py`),
and it produces:

| branches | Moore conditions | Form A | fragment |
| --- | --- | --- | --- |
| 3 | ✓ | 6/6 | 172 vertices, girth 5 |
| 4 | ✓ | 24/24 | 229 vertices, girth 5 |
| **5** | ✓ | **60/60** | 286 vertices, girth 5 |
| 6 | none exists in this construction | | |

**This settles the question the exact solver kept timing out on.** Five-branch
Form A structures *do* exist at degree 57, explicitly. So Form A is **not**
refuted there, and the annealer's stall at 4 was the searcher, not the object —
the opposite of what the timeout might have tempted me to conclude.

Two limits, stated plainly. The construction caps at 5 branches, well short of
the n−1 ≤ 7 ceiling that proper edge colouring alone would impose — the
triangle and quadrilateral conditions bite first. And seeding the Form A
annealer with the verified 5-branch structure did not reach 6 (cost 183–200
from ~360, three tries). So the Form A frontier is **5 of 57**, now
constructive rather than search-limited.

### 20n. Form A from reflections — the best conditional result here

Commuting is sufficient for σ_ca σ_bc σ_ab = σ_ab σ_bc σ_ca but not necessary.
In a **dihedral** group a product of an odd number of reflections is again a
reflection, and a reflection is an involution — so taking every bijection to be
a reflection of Z₅₆,

    σ_ij(x) = g_ij − x,   g_ij = g_ji,

makes every triangle composite a reflection and Form A holds **automatically**,
with no commuting required. The conditions collapse to arithmetic: the triangle
composite is x ↦ c − x with c = g_ab − g_bj + g_aj, fixed-point-free exactly
when c is odd — satisfied outright by taking every g_ij odd — and the
quadrilateral composite is the translation x ↦ x + d, fixed-point-free when
d ≠ 0. So only the quadrilateral conditions remain, over 28 odd residues per
pair.

This is the same ansatz `reflection.py` tested at *full* size, where it is
infeasible at degree 7. What was never run is the *partial* problem at degree
57, and that is a different question entirely:

| branches | Moore conditions | Form A | fragment |
| --- | --- | --- | --- |
| 5 | ✓ | 60/60 | 286 vertices, girth 5 |
| 9 | ✓ | 504/504 | 514 vertices, girth 5 |
| 11 | ✓ | 990/990 | 628 vertices, girth 5 |
| **13** | ✓ | **1716/1716** | 742 vertices, girth 5 |

Every one verified independently — derangement conditions on the σ-table, all
composites fixed-point-free involutions, and the graph fragment rebuilt and
checked for girth 5.

**13 of 57 branches, fully Form A compliant.** That beats the abelian
construction's 5 and the annealer's 4, and unlike the 11- and 14-branch
certificates from the general and 1-factorization searches, this one is not
off-path under the conjecture — it satisfies Form A exactly. It is the best
conditional structure in this project.

**Incremental growth with backtracking reaches 14.** Handing the whole K_t
model to CP-SAT stalls at 13; growing branch by branch and backtracking on
failure — the same move that took the cyclic labelling from 15 to 19 — gets one
further. The 14-branch certificate verifies completely:

| check | result |
| --- | --- |
| derangement conditions on the σ-table | ✓ |
| Form A (all composites f.p.f. involutions) | **2184 / 2184** |
| fragment | 799 vertices = 1 + 14 + 14·56, girth 5 |
| degrees | 14 and 57 — the 14 layer-1 vertices are already at full degree |

**14 of 57 branches, fully Form A compliant and independently verified.** This
is the best conditional structure in the project: unlike the 11-branch
1-factorization certificate and the 14-branch general one, which carry 270/990
and 0/2184 involutive composites respectively, this one is on-path under the
conjecture.

Three honest caveats. Most 13→14 extensions are proved INFEASIBLE — only one
line survived — and 14→15 came back INFEASIBLE on that line too, so the ansatz
is close to its ceiling. The reflection family is an ansatz, and the *same*
ansatz is provably infeasible at full size for degree 7, so it will not reach
57. And the degree-7 calibration is sobering in the other direction: there
reflections reach 5 of the 7 branches needed (71%), while at degree 57 they
reach 14 of 57 (25%).

### 20o. Reducing the reflection ansatz, and a better search for it

Every g_ij is odd, so write g_ij = 2f_ij + 1. The quadrilateral sum becomes
exactly 2(f_pw − f_uw + f_qu − f_pq), so the whole reflection ansatz is

> a **symmetric labelling f of K_t over Z₂₈** with no vanishing 4-cycle sum,

with the triangle conditions free and the gauge f_ij → f_ij − s_i − s_j (so the
"cut" labellings are the trivial ones). A first-moment count on that model puts
its ceiling near **t = 21**:

| branches | free labels | conditions | log₁₀ E[count] |
| --- | --- | --- | --- |
| 18 | 136 | 9,180 | +51.8 |
| 20 | 171 | 14,535 | +17.9 |
| 21 | 190 | 17,955 | −8.6 |

So CP-SAT growth stalling at 13–14 is a *search* limit, not the model's
ceiling — which also means an INFEASIBLE at 15 was never what to expect, and I
stopped a run that was chasing one.

**A much better search.** The reduced state space is one of 28 values per pair
rather than one of 56!, and annealing has beaten CP-SAT everywhere else here.
Annealing solves t = 13 in seconds and drives t = 14 to cost 3–6 — then sticks,
because once only a handful of conditions are broken, uniform pair selection
wastes nearly every move. Min-conflicts repair fixes exactly that: pick a
*violated* 4-cycle and change one of its four edges.

| method | t = 14 |
| --- | --- |
| CP-SAT incremental growth, 319 randomised restarts | reached it once |
| CP-SAT growth with backtracking | reached it once, ~8 min |
| **anneal + min-conflicts repair** | **reached it in ~2 min, repeatably** |

The t = 14 certificate is verified as before: Form A 2184/2184, 799-vertex
fragment, girth 5. At t = 15 the hybrid reaches cost 5–7 and has not closed it.

### 20p. Is the first-moment ceiling of t = 21 trustworthy? Partly.

The estimate assumes the conditions are independent. That is testable by
sampling: draw random gauge-fixed labellings and measure what fraction survive
all conditions, against the predicted (27/28)^(#conditions).

| branches | conditions | predicted | measured | measured / predicted |
| --- | --- | --- | --- | --- |
| 5 | 15 | 5.80e−1 | 5.67e−1 | 0.98 |
| 6 | 45 | 1.95e−1 | 1.75e−1 | 0.90 |
| 7 | 105 | 2.20e−2 | 1.58e−2 | 0.72 |
| 8 | 210 | 4.82e−4 | 1.80e−4 | 0.37 |
| 9 | 378 | 1.07e−6 | ~2.5e−6 | (1 hit in 400k — noise) |

So the estimator is accurate to within a factor of about three over the range
where sampling can see anything, and it errs *optimistically* — there are fewer
labellings than independence predicts, so the true ceiling is **at most** 21.
Past t = 8 the survival probability is too small to sample and the estimate is
untested.

That leaves the gap between the searched 14 and the estimated 21 genuinely
ambiguous, and I would rather say so than pick the flattering reading. What can
be said: every method tried plateaus in the same place. Cold anneal+repair, the
same seeded from the verified 14-branch certificate (initial cost only 33, still
ending at 6), CP-SAT growth, CP-SAT with backtracking, and 319 randomised
restarts all stop at 14 with a residual of 5–7 conditions at t = 15. A barrier
that survives five unrelated methods and both starting points is more likely to
be the object than the searcher — but the sampling above cannot confirm that,
and the estimate says otherwise.

### 20q. The ceiling law, computed exactly at small moduli

Instead of arguing about the extrapolation, compute the model's ceiling exactly
where CP-SAT can prove INFEASIBLE (`refl_law.py`). The model is a symmetric
Z_n labelling of K_t with no vanishing 4-cycle sum; degree 57 is n = 28.

| n | max t | proved | t / n |
| --- | --- | --- | --- |
| 2 | 3 | yes | 1.50 |
| 4 | 5 | yes | 1.25 |
| 6 | 6 | yes | 1.00 |
| 8 | ≥7 | undecided | 0.88 |
| 10 | ≥9 | undecided | 0.90 |
| 12 | ≥9 | undecided | 0.75 |

(Prime moduli behave differently — 3→5, 7→9 — so the even column is the
relevant one, 28 being even.)

**This corrects the reading I leaned toward last turn.** I had suggested that a
barrier surviving five methods was more likely the object than the searcher. The
even-modulus ratio sits around 0.75–0.9 and does not collapse, which
extrapolates to roughly **21–25 at n = 28** — in agreement with the first-moment
estimate and *against* my guess. On this evidence t = 14 is a search limit after
all, and the plateau across methods reflects that they share a weakness (all are
local in the same way) rather than a wall in the object.

Note the entries at n ≥ 8 are lower bounds, so the ratio could be higher still;
none of them is a proved ceiling. The honest conclusion is that the model very
probably admits structures well past 14 and none of the searches here find them.

### 20r. The small-n solutions have no algebraic structure

If the solutions CP-SAT finds at small moduli had a pattern, it could be
written down directly at n = 28 and the search skipped. They do not. Extracting
solutions at (t,n) = (9,12), (9,10) and (6,6) and testing:

| structure | present? |
| --- | --- |
| circulant (f depends only on i − j) | no |
| rank-1 bilinear (f_ij = x_i·x_j mod n) | no |

That is a useful negative, and it explains the pattern across this whole
section. Every *construction* tried caps early — commuting involutions at 5,
multiplicative/bilinear forms at 7 (since B(a,b) ≠ 0 for all differences forces
at most one vertex per residue class mod 7) — while *search* reaches 14. The
solutions that exist are generic, so there is no shortcut to write down, and
progress has to come from better search rather than better algebra.

### 20s. The CRT split: a good observation, a bad encoding

Z₂₈ = Z₄ × Z₇, so a 4-cycle sum vanishes mod 28 exactly when it vanishes mod 4
**and** mod 7. Splitting each label into (a_ij, b_ij) makes every condition a
disjunction, NOT(sum₄ = 0 AND sum₇ = 0), which is the shape SAT solvers like.

As an encoding it is a clear loss: t = 13 came back UNKNOWN at 150 s where the
direct encoding solves it in 32 s. The `AddModuloEquality` constraints cost more
than the disjunction saves.

As an observation it is worth keeping, because `refl_law.py` proves the ceilings
of the two components separately: **5 for modulus 4, 9 for modulus 7**. So
neither component alone can reach past 9, and every structure beyond that —
including the verified 14-branch one — must *mix*, satisfying some 4-cycles via
the mod-4 component and others via mod-7. That is precisely the freedom the
single-modulus constructions lack, and it explains why they cap at 5 and 7 while
search over the full Z₂₈ reaches 14.

### 20t. The reflection family is narrow: solutions exist at each level but rarely chain

Whether a structure extends is a property of *that* structure, so the way to
probe a level is to build many distinct structures there and ask each
(`refl_surface.py`). Anneal-then-repair produces a fresh one in about two
minutes, and CP-SAT decides extension in seconds rather than timing out:

| level | structures built (all verified Form A) | extension to next level |
| --- | --- | --- |
| 13 → 14 | 4 | **4 of 4 proved INFEASIBLE** (6–11 s each) |
| 14 → 15 | 1 | **INFEASIBLE** (5 s) |

And yet 14-branch structures certainly exist — several are in this repository,
verified at Form A 2184/2184. So they are not reached by extending a 13-branch
one; they have to be found *directly at level 14*, which is exactly what
anneal-then-repair does and what growth cannot.

That reframes every frontier number here. **The reflection family is narrow:
it has solutions at each level, but a randomly chosen solution is almost
certainly a dead end.** Compare the general permutation model, where the same
question gave 0 dead ends in 34 sampled structures up to 9 branches — there
valid structures nearly always extend. The two models could hardly behave more
differently, and the ansatz's narrowness is why growth-based methods stall while
direct search at a level keeps working.

It also settles a tension in the previous two sections honestly. The
even-modulus ratio suggested t ≈ 21 was reachable, and I leaned on that to call
14 a search limit. These INFEASIBLE proofs are much stronger evidence than that
extrapolation, which rested on undecided lower bounds at n ≥ 8. The right
statement is that reaching 15 requires finding a 15-branch structure directly,
and that the ceiling of this ansatz is still unproved in either direction.

### 20u. Breakout, and chaining the three searches

Every method converges on t = 15 and sticks at 5–7 violated conditions out of
~4000. That is a local minimum, and the standard remedy is neither a better
move nor a better schedule but a *changing objective*: weight each condition,
minimise the weighted violation count, and whenever the search is stuck add one
to the weight of every currently violated condition. The minimum is destroyed
rather than escaped.

Breakout alone (`breakout.py`) reaches residual **2** at t = 14 in 120 s —
better than annealing's 3–6 on the same budget — but does not close it, while
anneal+repair does in about the same time. So the three methods are good at
different parts of the descent:

| stage | strength |
| --- | --- |
| annealing | falls from hundreds to tens in seconds; wastes moves when the residual is small |
| min-conflicts repair | aims every move at a live violation; clears easy tails |
| breakout | changes the objective; the only one that attacks a true local minimum |

`pipeline.py` chains them, which is strictly better than any alone. It is
running at t = 15 now.

Note what this section is *not*. Chaining local searches is engineering, and the
frontier it moves is the frontier of an ansatz that is provably infeasible at
full size for degree 7. None of it bears on whether the Moore graph exists.

### 20v. A theorem: the reflection ansatz cannot reach degree 57

Not a search limit — a proof. In the reduced model every g_ij is odd, and
writing g_ij = 2f_ij + 1 makes the quadrilateral condition

    f_pw − f_uw + f_qu − f_pq ≠ 0  (mod 28),  f symmetric.

**Step 1 — the collapse.** Since f is symmetric, f_qu = f_uq, so

    f_pw − f_uw + f_qu − f_pq = (f_pw − f_pq) − (f_uw − f_uq).

**Step 2 — what the conditions say.** For a 4-set, the three cyclic orders
correspond exactly to the three ways of splitting it into two pairs {p,u} and
{q,w}. So the whole family of quadrilateral conditions is equivalent to:

> for every pair {q,w}, the map i ↦ f_iw − f_iq (mod 28) is **injective** over
> the indices i outside {q,w}.

**Step 3 — the count.** That map has t−2 arguments and lands in Z₂₈, so
injectivity forces t − 2 ≤ 28, i.e.

> **t ≤ 30.**

A Moore graph of degree 57 needs t = 57. **Therefore no Moore graph of degree
57 has all of its bijections reflections in Z₅₆.** ∎

`reflection_bound.py` checks Step 2 by brute force on random labellings (it is
an identity, so a counterexample would mean a bug) — the two violation counts
vanish together in every case — and confirms that all 16 reflection
certificates on disk have exactly zero injectivity failures.

This is the same shape as the published theorem that no cyclic construction
exists (Axioms 2026), proved here for a different and strictly larger family:
the reflection family reaches 14 branches under Form A where the cyclic family
dies at 4.

It also settles the status of everything in §20n–20u. That work was pushing the
frontier of an ansatz which is *provably* capped at 30 — so the effort spent
chasing t = 15 was, in the end, exploring a family that could never have
finished. Worth knowing before spending more on it, and exactly the kind of
thing worth proving early rather than late.

### 21. Verification: a checker, so a candidate would not rest on a script

`Moore57Verify.lean` is the verification half. It defines an executable
`MooreCheck n k adj : Bool` on an adjacency table together with
`MooreCheck_sound`, the statement that its returning `true` implies the graph
really is a Moore graph. Verifying a candidate then reduces to evaluating one
Boolean on concrete data — `decide` for the small cases, `native_decide` for
n = 3250:

```lean
theorem candidate_is_moore :
    IsMoore (toGraph candidateAdj (by native_decide)) 57 :=
  MooreCheck_sound 3250 57 candidateAdj (by native_decide) (by native_decide)
```

That is the statement which would settle the problem. There is no
`candidateAdj` to plug in — that is the whole difficulty — but the final step
would be machine-checked rather than trusted.

The Lean file is **not machine-checked** (no toolchain, egress blocked), so
`checker.py` is the executable mirror, clause for clause, and it *is* tested:
it accepts Petersen and Hoffman–Singleton, rejects a wrong degree claim,
rejects all 266 one-edge perturbations of both, and rejects the circulant
C₁₀(1,5) which has the right order and degree but 4-cycles.

### 22. A guaranteed brute force: written, validated, measured, and impossible

`bruteforce.py` is a complete search — no heuristics, no ansatz, no restarts.
It enumerates gauge-fixed structures in a fixed order with forward checking and
smallest-remaining-domain cell selection, so it finds a Moore graph of degree k
**if and only if one exists**.

Validated where the answer is known:

| degree | result |
| --- | --- |
| 3 | Petersen found in **2 nodes** |
| 7 | Hoffman–Singleton found in **765,621 nodes / 17.4 s** |

(That is 106× better than the naive complete search of section 4, which needed
81,381,110 nodes.)

Run at degree 57 on this machine: 705,124 nodes in 242 s — **2,919 nodes/s**,
reaching 12 of 57 branches, not exhausted.

Now the accounting, and the first number is **exact, not estimated**. With the
gauge σ_0j = id, a 3-branch structure is precisely a derangement of the 56
points, so the count on just 3 of the 57 branches is

    N₃ = D₅₆ = 261,561,763,155,337,832,293,801,371,240,394,297,250,999,460,530,798,866,171,481,991,351,183,803,665 ≈ 10⁷⁴·⁴

Isomorph rejection does help at 3 branches — the classes are just cycle types,
a few thousand — and then it stops helping. At 4 branches the count is ~D₅₆³ =
10²²³ against residual symmetry of at most 56! = 10⁷⁴·⁹, so the number of
*isomorphism classes* is at least 10¹⁴⁸.

| quantity | value |
| --- | --- |
| classes to cover at **4** of 57 branches | ≥ 10¹⁴⁸ |
| a year of this machine | 10¹¹ nodes |
| a century of this machine | 10¹³ nodes |
| **shortfall at four branches** | **10¹³⁵** |

> **A guaranteed brute force in local compute time does not exist for this
> problem.** The obstacle is not the implementation. Four branches out of
> fifty-seven already exceed any physically available budget by 135 orders of
> magnitude, and that is computed from an exact count with isomorph rejection
> already credited.

The program is correct and will find the graph if one exists. It will not
finish.

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
| `Moore57Verify.lean` | Lean verified-checker harness for a candidate (not machine-checked) |
| `checker.py` | tested reference implementation the Lean checker mirrors |
| `bruteforce.py` | complete guaranteed search, validated and measured |
| `factorization_search.py` | the 1-factorization model; validated, and the best search here |
| `involution_prune.py` | exact measurement of how hard the conjecture prunes |
| `conjecture.py` | the conjecture in three equivalent forms, checked |
| `anneal.py` | simulated annealing over both state spaces; degree-7 validation |
| `anneal_fast.py` | the same with the table as one numpy array, batched cost |
| `sweep.py` | probabilistic frontier sweep over t |
| `grow_anneal.py` | grow-and-repair with escalating budgets — the best search here |
| `lns.py` | large-neighbourhood search: delete and re-solve an old branch |
| `tempering.py` | parallel tempering / replica exchange |
| `hybrid.py` | anneal to the plateau, then hand the remainder to an exact solver |
| `extend_exact.py` | asks CP-SAT exactly whether a verified structure extends |
| `deadends.py` | dead-end density: fraction of valid structures that cannot extend |
| `scaling.py` | measured cost per branch, fitted and projected to 57 |
| `seeded_factorization.py` | pin row 1 to the round-robin 1-factorization |
| `push_frontier.py` | long single-branch push from a verified structure |

Run order: `python3 reduction.py`, `known_constraints.py`, `firstmoment.py`,
`verify_frontier.py` are all fast. `cyclic_search.py [seconds]` and
`run_k7.py` take minutes; `push_cyclic.py incremental 90 25` takes hours.

Requires `ortools` and Python 3.11+.
