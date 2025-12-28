-- Task l01_np_verifier
-- Use ASCII only: forall, exists. Output Lean code only (no Markdown fences).
-- Assume the following names exist:
--   Language : Type
--   NP : Set Language
--   verifier : Language -> String -> Prop
--   poly : (Nat -> Nat) -> Prop
--   cert_len : String -> Nat
--   inNP : Language -> Prop
-- (You may use NP instead of inNP.)

-- Write a lemma statement and a proof sketch in Lean style.
-- Goal: NP membership iff there exists a polynomially bounded certificate
-- verified in polynomial time.

-- Required format:
-- theorem/lemma ... : ... := by
--   -- proof sketch (tactics or comments)

/- rubric:
must: theorem
must: by
must: NP
must: exists
must: verifier
must: certificate
should: forall
should: polynomial
-/-
