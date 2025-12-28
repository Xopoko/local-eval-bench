from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from harness.graders.grade_md import _arbiter_verdict, _match_pattern


def _parse_rubric(task_text: str) -> dict[str, list[str]]:
    match = re.search(r"/-\s*rubric:(.*?)-/", task_text, flags=re.S | re.I)
    if not match:
        return {"must": [], "should": []}
    block = match.group(1)
    must: list[str] = []
    should: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("must:"):
            must.append(line.split(":", 1)[1].strip())
        elif line.lower().startswith("should:"):
            should.append(line.split(":", 1)[1].strip())
    return {"must": must, "should": should}


def evaluate(task_path: Path, answer: str, arbiter: Any | None = None) -> dict[str, Any]:
    task_text = Path(task_path).read_text(encoding="utf-8")
    rubric = _parse_rubric(task_text)

    missing = [p for p in rubric["must"] if not _match_pattern(p, answer)]
    should_hits = sum(1 for p in rubric["should"] if _match_pattern(p, answer))

    length_ok = len(answer.strip()) >= 80
    fence_ok = "```" not in answer

    heuristics_pass = not missing and length_ok and fence_ok
    arbiter_pass = None
    if arbiter is not None and getattr(arbiter, "cmd_template", None):
        arbiter_pass = _arbiter_verdict(task_text, answer, arbiter)

    passed = heuristics_pass if arbiter_pass is None else (heuristics_pass and arbiter_pass)

    return {
        "passed": passed,
        "missing": missing,
        "should_hits": should_hits,
        "length_ok": length_ok,
        "fence_ok": fence_ok,
        "arbiter_pass": arbiter_pass,
    }
