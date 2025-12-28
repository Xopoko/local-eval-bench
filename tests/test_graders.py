from harness.graders import grade_lean, grade_md


def test_grade_md_pass(tmp_path):
    task = tmp_path / "t.md"
    task.write_text(
        """
# Task

Do something.

<!-- rubric:
must: Verdict:
must: Proof sketch:
must: n=1
should: edge case
-->
""".strip(),
        encoding="utf-8",
    )
    answer = (
        "Verdict: true.\n"
        "Proof sketch: Check n=1 as an edge case; the claim holds in the base case "
        "and the argument extends by a standard bound."
    )
    result = grade_md.evaluate(task, answer)
    assert result["passed"] is True


def test_grade_md_missing_must(tmp_path):
    task = tmp_path / "t.md"
    task.write_text(
        """
# Task

<!-- rubric:
must: Verdict:
must: Proof sketch:
-->
""".strip(),
        encoding="utf-8",
    )
    answer = "Verdict: true."
    result = grade_md.evaluate(task, answer)
    assert result["passed"] is False
    assert "Proof sketch:" in result["missing"]


def test_grade_lean_pass(tmp_path):
    task = tmp_path / "t.lean"
    task.write_text(
        """
-- Task
/- rubric:
must: theorem
must: by
must: NP
must: exists
-/-
""".strip(),
        encoding="utf-8",
    )
    answer = (
        "theorem np_witness : NP -> exists y, True := by\n"
        "  -- proof sketch: unfold NP, pick a witness y, and apply the verifier.\n"
        "  admit"
    )
    result = grade_lean.evaluate(task, answer)
    assert result["passed"] is True
