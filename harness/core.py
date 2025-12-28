from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.graders import grade_lean, grade_md, grade_py, grade_synth


@dataclass
class Task:
    task_id: str
    task_type: str
    path: Path


def list_tasks(tasks_root: Path) -> dict[str, list[Task]]:
    md_tasks = [
        Task(task_id=p.stem, task_type="md", path=p)
        for p in sorted((tasks_root / "md").glob("*.md"))
    ]
    lean_tasks = [
        Task(task_id=p.stem, task_type="lean", path=p)
        for p in sorted((tasks_root / "lean").glob("*.lean"))
    ]
    synth_tasks = [
        Task(task_id=p.stem, task_type="synth", path=p)
        for p in sorted((tasks_root / "synth").glob("*.md"))
    ]
    py_tasks: list[Task] = []
    for p in sorted((tasks_root / "py").iterdir()):
        if not p.is_dir():
            continue
        if (p / "impl.py").exists() and (p / "tests.py").exists():
            py_tasks.append(Task(task_id=p.name, task_type="py", path=p))
    return {"md": md_tasks, "py": py_tasks, "synth": synth_tasks, "lean": lean_tasks}


def build_prompt(task: Task) -> str:
    if task.task_type in {"md", "synth", "lean"}:
        return task.path.read_text(encoding="utf-8")

    impl = (task.path / "impl.py").read_text(encoding="utf-8")
    tests = (task.path / "tests.py").read_text(encoding="utf-8")
    return (
        "You are asked to refactor code and add tests.\n"
        "- Preserve behavior unless explicitly stated.\n"
        "- Improve naming and decomposition.\n"
        "- Add or expand pytest tests.\n"
        "- Keep the API stable.\n\n"
        "Return a unified diff patch relative to the task folder.\n"
        "Only edit impl.py and tests.py.\n"
        "Output only the diff, no code fences or extra text.\n\n"
        "impl.py:\n"
        "```python\n"
        f"{impl}\n"
        "```\n\n"
        "tests.py:\n"
        "```python\n"
        f"{tests}\n"
        "```\n"
    )


def evaluate_task(
    task: Task,
    model_client: Any,
    model_name: str,
    repo_root: Path,
    max_tries: int = 1,
    min_coverage: float = 90.0,
    arbiter: Any | None = None,
    continue_on_error: bool = False,
) -> dict[str, Any]:
    attempts = []
    first_failure_time: float | None = None
    first_pass_time: float | None = None
    start_time = time.time()
    pass_count = 0

    for attempt in range(1, max_tries + 1):
        attempt_start = time.time()
        prompt = build_prompt(task)
        model_error = None
        try:
            output = model_client.generate(
                prompt, model_name, task.task_type, task.task_id
            )
        except Exception as exc:
            if not continue_on_error:
                raise
            model_error = f"{type(exc).__name__}: {exc}"
            output = ""
        if task.task_type == "py":
            grade = grade_py.evaluate(
                task.path,
                output,
                repo_root=repo_root,
                min_coverage=min_coverage,
            )
        elif task.task_type == "md":
            grade = grade_md.evaluate(task.path, output, arbiter=arbiter)
        elif task.task_type == "lean":
            grade = grade_lean.evaluate(task.path, output, arbiter=arbiter)
        else:
            grade = grade_synth.evaluate(task.path, output, arbiter=arbiter)

        attempt_end = time.time()
        if grade["passed"]:
            pass_count += 1
            if first_pass_time is None:
                first_pass_time = attempt_end
        elif first_failure_time is None:
            first_failure_time = attempt_end

        attempt_result = {
            "attempt": attempt,
            "passed": grade["passed"],
            "details": grade,
            "output_chars": len(output),
            "model_error": model_error,
            "elapsed_sec": attempt_end - attempt_start,
        }
        attempts.append(attempt_result)

    end_time = time.time()
    pass_at_1 = bool(attempts and attempts[0]["passed"])
    pass_at_k = pass_count > 0
    pass_rate = pass_count / max_tries if max_tries else 0.0
    time_to_fix = None
    if pass_at_1:
        time_to_fix = 0.0
    elif first_pass_time is not None and first_failure_time is not None:
        time_to_fix = first_pass_time - first_failure_time

    return {
        "task_id": task.task_id,
        "task_type": task.task_type,
        "model": model_name,
        "attempts": attempts,
        "pass_at_1": pass_at_1,
        "pass_at_k": pass_at_k,
        "pass_rate": pass_rate,
        "attempts_total": max_tries,
        "time_to_fix": time_to_fix,
        "elapsed_sec": end_time - start_time,
    }
