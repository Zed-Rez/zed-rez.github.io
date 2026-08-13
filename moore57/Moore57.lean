/-
  The block decomposition of a Moore graph of diameter two.

  This is the structural fact the whole search rests on: rooted at any vertex,
  a Moore graph of degree k splits its second layer into k blocks of size
  k - 1, and the edges between any two distinct blocks form a *perfect
  matching*.  That matching is the bijection sigma_ij of `reduction.py`, and
  the search implemented there is the search for a consistent family of them.

  STATUS.  This file is NOT machine-checked.  The sandbox this was written in
  has no Lean toolchain and no network route to one (`elan`, `leanprover.github.io`
  and GitHub are all blocked by the egress proxy), so nothing here has been
  through the kernel.  Declarations that are fully proved below are proved in
  the ordinary Mathlib idiom and should compile with light editing; the three
  that are left as `sorry` are flagged individually and are counting arguments,
  not the structural core.

  Targets Lean 4 with Mathlib (`import Mathlib`).
-/

import Mathlib

namespace Moore

open Finset SimpleGraph

variable {V : Type*} [Fintype V] [DecidableEq V]
variable (G : SimpleGraph V) [DecidableRel G.Adj]

/-- A Moore graph of diameter two and degree `k`: regular, triangle-free, and
any two distinct non-adjacent vertices have exactly one common neighbour.

This is the "friendship at distance two" formulation.  It is equivalent to the
usual one (`k`-regular, `k^2+1` vertices, girth 5): triangle-freeness rules out
3-cycles, and uniqueness of the common neighbour rules out 4-cycles. -/
structure IsMoore (k : ℕ) : Prop where
  regular : ∀ v : V, G.degree v = k
  triangleFree : ∀ ⦃a b c : V⦄, G.Adj a b → G.Adj b c → G.Adj c a → False
  unique_common : ∀ ⦃a b : V⦄, a ≠ b → ¬ G.Adj a b →
    ∃! c : V, G.Adj a c ∧ G.Adj b c

variable {G} {k : ℕ}

/-- Adjacent vertices have no common neighbour (restatement of triangle-freeness). -/
theorem no_common_of_adj (h : IsMoore G k) {a b c : V}
    (hab : G.Adj a b) (hac : G.Adj a c) (hbc : G.Adj b c) : False :=
  h.triangleFree hab hbc (G.symm hac)

section Rooted

variable (v : V)

/-- The block below a neighbour `u` of the root: the other neighbours of `u`. -/
def block (u : V) : Finset V :=
  (G.neighborFinset u).erase v

@[simp] theorem mem_block {u x : V} :
    x ∈ block G v u ↔ x ≠ v ∧ G.Adj u x := by
  simp [block, and_comm]

/-- A block has `k - 1` elements. -/
theorem card_block (h : IsMoore G k) {u : V} (hu : G.Adj v u) :
    (block G v u).card = k - 1 := by
  have hv : v ∈ G.neighborFinset u := by
    simpa [mem_neighborFinset] using G.symm hu
  rw [block, card_erase_of_mem hv, card_neighborFinset_eq_degree, h.regular]

variable {v}

/-- No vertex of a block is adjacent to the root. -/
theorem not_adj_root_of_mem_block (h : IsMoore G k) {u x : V}
    (hu : G.Adj v u) (hx : x ∈ block G v u) : ¬ G.Adj v x := by
  rw [mem_block] at hx
  exact fun hvx => no_common_of_adj h hu hvx hx.2

/-- A vertex of a block is not itself a neighbour of the root. -/
theorem ne_of_mem_block_of_adj_root (h : IsMoore G k) {u u' x : V}
    (hu : G.Adj v u) (hu' : G.Adj v u') (hx : x ∈ block G v u) : x ≠ u' := by
  rintro rfl
  exact not_adj_root_of_mem_block h hu hx hu'

/-- A vertex of one block is not adjacent to any *other* neighbour of the root.
If it were, that neighbour and `u` would share the two common neighbours `v`
and `x`. -/
theorem not_adj_other_root_nbr (h : IsMoore G k) {u u' x : V}
    (hu : G.Adj v u) (hu' : G.Adj v u') (hne : u' ≠ u)
    (hx : x ∈ block G v u) : ¬ G.Adj x u' := by
  intro hxu'
  rw [mem_block] at hx
  -- `u` and `u'` are distinct and non-adjacent, so they have a unique common
  -- neighbour; but both `v` and `x` are common neighbours.
  have hnadj : ¬ G.Adj u u' := fun huu' => h.triangleFree hu huu' (G.symm hu')
  obtain ⟨c, _, hc⟩ := h.unique_common (Ne.symm hne) hnadj
  have h1 : v = c := hc v ⟨G.symm hu, G.symm hu'⟩
  have h2 : x = c := hc x ⟨hx.2, G.symm hxu'⟩
  exact hx.1 (h1 ▸ h2)

/-- Blocks are independent sets: two vertices of a block, together with `u`,
would form a triangle. -/
theorem block_indep (h : IsMoore G k) {u x y : V}
    (hx : x ∈ block G v u) (hy : y ∈ block G v u) : ¬ G.Adj x y := by
  rw [mem_block] at hx hy
  exact fun hxy => no_common_of_adj h hx.2 hy.2 hxy

/-- **The matching lemma.**  Every vertex of one block has exactly one
neighbour in every other block.

Proof: `x` and `u'` are distinct and non-adjacent, so they have a unique common
neighbour `c`.  Any common neighbour lies in `N(u') = {v} ∪ block u'`, and `v`
is not adjacent to `x`, so `c` lies in `block u'`. -/
theorem exists_unique_nbr_in_block (h : IsMoore G k) {u u' x : V}
    (hu : G.Adj v u) (hu' : G.Adj v u') (hne : u' ≠ u)
    (hx : x ∈ block G v u) :
    ∃! y : V, y ∈ block G v u' ∧ G.Adj x y := by
  have hxu' : ¬ G.Adj x u' := not_adj_other_root_nbr h hu hu' hne hx
  have hxne : x ≠ u' := ne_of_mem_block_of_adj_root h hu hu' hx
  obtain ⟨c, ⟨hxc, hu'c⟩, huniq⟩ := h.unique_common hxne hxu'
  refine ⟨c, ⟨?_, hxc⟩, ?_⟩
  · -- `c ∈ block u'`: it is a neighbour of `u'` and it is not `v`
    rw [mem_block]
    refine ⟨?_, hu'c⟩
    rintro rfl
    exact not_adj_root_of_mem_block h hu hx (G.symm hxc)
  · rintro y ⟨hy, hxy⟩
    exact huniq y ⟨hxy, (mem_block.mp hy).2.symm⟩

/-- Consequently the edges between two distinct blocks form a perfect matching:
the relation `G.Adj` restricted to `block u × block u'` is a bijection.  This
is the bijection called `sigma_ij` in the accompanying Python code, and the
object the search enumerates. -/
theorem matching_between_blocks (h : IsMoore G k) {u u' : V}
    (hu : G.Adj v u) (hu' : G.Adj v u') (hne : u' ≠ u) :
    ∀ x ∈ block G v u, ∃! y, y ∈ block G v u' ∧ G.Adj x y :=
  fun _ hx => exists_unique_nbr_in_block h hu hu' hne hx

end Rooted

/-!
### The counting facts

These are the standard order and spectrum computations.  They are stated here
for completeness and are the parts of this file that have not been proved.
-/

/-- A Moore graph of degree `k` and diameter two has `k^2 + 1` vertices.

Counting argument: fix `v`; the `k` neighbours contribute `k`, each of the `k`
blocks contributes `k - 1`, the blocks are disjoint (a vertex in two blocks
would give two common neighbours to a pair of root-neighbours), and every
vertex is the root, a neighbour, or in a block (diameter two). -/
theorem card_eq_of_isMoore (h : IsMoore G k) [Nonempty V] :
    Fintype.card V = k ^ 2 + 1 := by
  sorry

/-- The Moore bound admits only degrees 2, 3, 7 and 57 in diameter two.

This is the Hoffman–Singleton integrality argument: the adjacency matrix
satisfies `A^2 + A - (k-1)I = J`, whose non-principal eigenvalues are the roots
of `x^2 + x - (k-1) = 0`, and integrality of the multiplicities forces
`k ∈ {2, 3, 7, 57}`. -/
theorem degree_mem_of_isMoore (h : IsMoore G k) [Nonempty V] :
    k ∈ ({2, 3, 7, 57} : Finset ℕ) := by
  sorry

/-- Degree 57 is the open case: no construction and no non-existence proof.
Stated as a definition rather than an axiom -- this is the conjecture, not a
theorem, and nothing downstream may depend on it. -/
def MooreGraph57Exists : Prop :=
  ∃ (V : Type) (_ : Fintype V) (_ : DecidableEq V) (G : SimpleGraph V)
    (_ : DecidableRel G.Adj), IsMoore G 57

end Moore
