# Adding Tasks

## Markdown logic (md)

- Add a file in `tasks/md/`.
- Include a rubric block:

```text
<!-- rubric:
must: Verdict:
must: Proof sketch:
should: edge case
-->
```

The grader checks that all `must` patterns appear (case-insensitive).

## Synthesis (synth)

- Add a file in `tasks/synth/`.
- Use the same rubric format.
- Output is expected to be 1-2 paragraphs.

## Lean (lean)

- Add a file in `tasks/lean/`.
- Use ASCII only and a rubric block:

```text
/- rubric:
must: theorem
must: by
should: forall
-/-
```

Lean is currently graded by rubrics only.

## Python refactors (py)

- Create a folder under `tasks/py/<task_id>/`.
- Include `impl.py` and `tests.py`.
- The model must output a unified diff that edits only those files.
