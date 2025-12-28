from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from harness.graders.grade_md import _arbiter_verdict, _match_pattern, _parse_rubric


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def evaluate(
    task_path: Path,
    answer: str,
    arbiter: Any | None = None,
) -> dict[str, Any]:
    task_text = Path(task_path).read_text(encoding="utf-8")
    rubric = _parse_rubric(task_text)

    missing = [p for p in rubric["must"] if not _match_pattern(p, answer)]
    should_hits = sum(1 for p in rubric["should"] if _match_pattern(p, answer))

    words = _word_count(answer)
    paragraphs = [p for p in answer.split("\n\n") if p.strip()]
    paragraphs_ok = 1 <= len(paragraphs) <= 2
    length_ok = 40 <= words <= 220

    heuristics_pass = not missing and length_ok and paragraphs_ok
    arbiter_pass = None
    if arbiter is not None and getattr(arbiter, "cmd_template", None):
        arbiter_pass = _arbiter_verdict(task_text, answer, arbiter)

    passed = (
        heuristics_pass
        if arbiter_pass is None
        else (heuristics_pass and arbiter_pass)
    )

    return {
        "passed": passed,
        "missing": missing,
        "should_hits": should_hits,
        "length_ok": length_ok,
        "paragraphs_ok": paragraphs_ok,
        "word_count": words,
        "arbiter_pass": arbiter_pass,
    }
