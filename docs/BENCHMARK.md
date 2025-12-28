# Benchmark Specification

LocalEval Bench measures model performance on small, high-signal tasks with
lightweight automatic grading. It is designed for routing experiments and
rapid iteration, not as a formal math proof checker.

## Task families

- md: short logic checks with edge cases
- py: refactor plus tests (unified diff required)
- synth: lemma completion + proof sketch
- lean: Lean-style theorem + proof sketch (ASCII only)

## Scoring

Each task is sampled K times (default K=5):

- pass@1: success on the first sample
- pass@K: success on any of K samples
- avg pass rate: average success rate over K samples
- time-to-fix: time from first failure to first success

## Grading details

- md/synth/lean use rubric-based heuristics (must/should signals).
- py applies the patch, then runs pytest, coverage, and ruff.

## Limitations

- No ground-truth proofs are stored.
- Lean tasks are not compiled by default.
- Heuristic grading can accept weak or reject strong answers.

For best results, consider adding an LLM arbiter or a Lean checker.
