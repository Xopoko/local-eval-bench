from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _parse_rubric(task_text: str) -> dict[str, list[str]]:
    match = re.search(r"<!--\s*rubric:(.*?)-->", task_text, flags=re.S | re.I)
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


def _match_pattern(pattern: str, text: str) -> bool:
    if pattern.startswith("re:"):
        regex = pattern[3:].strip()
        return re.search(regex, text, flags=re.I | re.M) is not None
    if pattern.startswith("/") and pattern.endswith("/") and len(pattern) > 2:
        regex = pattern[1:-1]
        return re.search(regex, text, flags=re.I | re.M) is not None
    return pattern.lower() in text.lower()


def _arbiter_verdict(task_text: str, answer: str, arbiter: Any) -> bool:
    prompt = (
        "You are a strict grader. Output only PASS or FAIL.\n\n"
        "Task:\n"
        f"{task_text}\n\n"
        "Answer:\n"
        f"{answer}\n"
    )
    reply = arbiter.generate(prompt, model="arbiter", task_type="arbiter", task_id="md")
    reply_upper = reply.strip().upper()
    if "PASS" in reply_upper and "FAIL" not in reply_upper:
        return True
    if "FAIL" in reply_upper and "PASS" not in reply_upper:
        return False
    return False


def evaluate(
    task_path: Path,
    answer: str,
    arbiter: Any | None = None,
) -> dict[str, Any]:
    task_text = Path(task_path).read_text(encoding="utf-8")
    rubric = _parse_rubric(task_text)

    missing = [p for p in rubric["must"] if not _match_pattern(p, answer)]
    should_hits = sum(1 for p in rubric["should"] if _match_pattern(p, answer))
    length_ok = len(answer.strip()) >= 60

    heuristics_pass = not missing and length_ok
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
        "arbiter_pass": arbiter_pass,
    }
