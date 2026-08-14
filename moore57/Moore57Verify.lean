/-
  A verified checker for Moore graphs of degree k and diameter 2.

  PURPOSE.  This is the verification half of the problem.  Nobody has a
  degree-57 Moore graph, but if a candidate is ever produced, its verification
  should not rest on a Python script.  This file gives

    * `MooreCheck n k adj : Bool`   -- an executable decision procedure, and
    * `MooreCheck_sound`            -- a proof that it returning `true` implies
                                       the graph really is a Moore graph.

  So verifying a candidate reduces to evaluating one Boolean on concrete data,
  which the kernel can do (via `decide` for small cases, `native_decide` for
  n = 3250).  The candidate itself is supplied as an adjacency table; the
  companion `checker.py` produces that table from a sigma-table and is the
  reference implementation this file mirrors line for line.

  STATUS.  NOT machine-checked.  This sandbox has no Lean toolchain and the
  egress proxy blocks elan, leanprover.github.io and GitHub, so nothing here
  has been through the kernel.  The `sorry`s are marked individually.  The
  executable part (`MooreCheck` and everything it calls) is mirrored exactly by
  `checker.py`, which IS tested here: it accepts the Petersen and
  Hoffman-Singleton graphs and rejects every perturbation of them.
-/

import Mathlib

namespace Moore57

/-- A graph on `n` vertices as an adjacency table: `adj[v]` lists the
neighbours of `v`.  Vertices are `Fin n`. -/
abbrev Adj (n : ℕ) := Array (Array (Fin n))

variable {n : ℕ}

/-- Membership test on a sorted-or-unsorted neighbour list. -/
def hasEdge (adj : Adj n) (u v : Fin n) : Bool :=
  match adj[u.val]? with
  | some l => l.contains v
  | none   => false

/-- Every vertex has exactly `k` neighbours. -/
def isRegular (adj : Adj n) (k : ℕ) : Bool :=
  adj.size == n && adj.all (fun l => l.size == k)

/-- The table is symmetric and loop-free: a genuine undirected simple graph. -/
def isSimpleSymmetric (adj : Adj n) : Bool :=
  (List.finRange n).all (fun u =>
    match adj[u.val]? with
    | some l => l.all (fun v => v != u && hasEdge adj v u) && l.toList.Nodup
    | none   => false)

/-- No triangles: no edge has an endpoint pair with a common neighbour. -/
def triangleFree (adj : Adj n) : Bool :=
  (List.finRange n).all (fun u =>
    match adj[u.val]? with
    | some l => l.all (fun v =>
        match adj[v.val]? with
        | some m => m.all (fun w => !hasEdge adj u w)
        | none   => false)
    | none   => false)

/-- No two distinct vertices have two common neighbours.  Together with
`triangleFree` this is exactly girth ≥ 5, and with regularity and the order it
is exactly the Moore condition. -/
def noTwoCommonNeighbours (adj : Adj n) : Bool :=
  (List.finRange n).all (fun u =>
    let seen : Array Bool := Array.replicate n false
    let step := (List.finRange n).foldl
      (fun (acc : Array Bool × Bool) _ => acc) (seen, true)
    -- count paths of length two from u; fail on any repeat
    let res := (match adj[u.val]? with
      | some l =>
        l.foldl (fun (acc : Array Bool × Bool) v =>
          match adj[v.val]? with
          | some m =>
            m.foldl (fun (acc : Array Bool × Bool) w =>
              if w == u then acc
              else if acc.1[w.val]! then (acc.1, false)
              else (acc.1.set! w.val true, acc.2)) acc
          | none => (acc.1, false)) (step.1, true)
      | none => (seen, false))
    res.2)

/-- The full check: order `k^2 + 1`, `k`-regular, simple, girth ≥ 5. -/
def MooreCheck (n k : ℕ) (adj : Adj n) : Bool :=
  n == k * k + 1 &&
  isRegular adj k &&
  isSimpleSymmetric adj &&
  triangleFree adj &&
  noTwoCommonNeighbours adj

/-- The mathematical property being certified, stated on `SimpleGraph`. -/
structure IsMoore (G : SimpleGraph (Fin n)) [DecidableRel G.Adj] (k : ℕ) : Prop where
  order : n = k * k + 1
  regular : ∀ v, G.degree v = k
  triangleFree : ∀ ⦃a b c⦄, G.Adj a b → G.Adj b c → G.Adj c a → False
  unique_common : ∀ ⦃a b⦄, a ≠ b → ¬ G.Adj a b → ∃! c, G.Adj a c ∧ G.Adj b c

/-- The graph read off an adjacency table. -/
def toGraph (adj : Adj n) (h : isSimpleSymmetric adj = true) :
    SimpleGraph (Fin n) where
  Adj u v := hasEdge adj u v = true
  symm := by
    intro u v huv
    -- symmetry is exactly what `isSimpleSymmetric` checks
    sorry
  loopless := by
    intro u huu
    -- `isSimpleSymmetric` rejects loops
    sorry

instance (adj : Adj n) (h : isSimpleSymmetric adj = true) :
    DecidableRel (toGraph adj h).Adj := by
  intro u v
  simpa [toGraph] using (inferInstance : Decidable (hasEdge adj u v = true))

/-- **Soundness.**  If the checker accepts, the graph really is a Moore graph
of degree `k` and diameter two.

Each conjunct of `MooreCheck` is the Boolean image of the corresponding clause
of `IsMoore`; the only real content is that `noTwoCommonNeighbours` gives
*exactly one* common neighbour for non-adjacent pairs, which follows from
counting: `k`-regularity plus girth 5 plus `n = k^2+1` forces every non-adjacent
pair to have at least one, and the check forbids two. -/
theorem MooreCheck_sound (n k : ℕ) (adj : Adj n)
    (hs : isSimpleSymmetric adj = true) (h : MooreCheck n k adj = true) :
    IsMoore (toGraph adj hs) k := by
  sorry

/-- Verifying a concrete candidate is then a single kernel computation.  For
n = 3250 this wants `native_decide`; for the small cases `decide` suffices.

    theorem petersen_is_moore :
        IsMoore (toGraph petersenAdj (by decide)) 3 :=
      MooreCheck_sound 10 3 petersenAdj (by decide) (by decide)

    theorem candidate_is_moore :
        IsMoore (toGraph candidateAdj (by native_decide)) 57 :=
      MooreCheck_sound 3250 57 candidateAdj (by native_decide) (by native_decide)

The second is the statement that would settle the problem.  No `candidateAdj`
exists to plug in -- that is the whole difficulty, and this file cannot supply
it.  What it does supply is that the final step would be machine-checked rather
than trusted. -/
def verificationRecipe : Unit := ()

end Moore57
