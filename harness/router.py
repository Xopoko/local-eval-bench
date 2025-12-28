from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from harness import core
from harness.models import arbiter_client, default_model_client


def choose_route(
    repo_root: Path,
    model: str,
    codegen: str,
    max_tries: int = 1,
    min_coverage: float = 90.0,
    mock: bool = False,
) -> dict[str, Any]:
    tasks_root = repo_root / "tasks"
    tasks = core.list_tasks(tasks_root)

    if not tasks["py"] or not tasks["md"]:
        return {
            "code_model": model,
            "logic_model": model,
            "reason": "missing sample tasks",
        }

    sample_py = tasks["py"][0]
    sample_md = tasks["md"][0]

    model_client = default_model_client(mock=mock)
    arbiter = arbiter_client() if os.environ.get("LOCAL_EVAL_ARBITER_CMD") else None

    py_model = core.evaluate_task(
        sample_py,
        model_client,
        model,
        repo_root,
        max_tries=max_tries,
        min_coverage=min_coverage,
        arbiter=arbiter,
    )
    py_codegen = core.evaluate_task(
        sample_py,
        model_client,
        codegen,
        repo_root,
        max_tries=max_tries,
        min_coverage=min_coverage,
        arbiter=arbiter,
    )
    md_model = core.evaluate_task(
        sample_md,
        model_client,
        model,
        repo_root,
        max_tries=max_tries,
        min_coverage=min_coverage,
        arbiter=arbiter,
    )
    md_codegen = core.evaluate_task(
        sample_md,
        model_client,
        codegen,
        repo_root,
        max_tries=max_tries,
        min_coverage=min_coverage,
        arbiter=arbiter,
    )

    if py_codegen["pass_at_1"] > py_model["pass_at_1"] and md_codegen["pass_at_1"] < md_model["pass_at_1"]:
        return {
            "code_model": codegen,
            "logic_model": model,
            "reason": "codegen better on py, model better on md",
            "samples": {
                "py_model": py_model,
                "py_codegen": py_codegen,
                "md_model": md_model,
                "md_codegen": md_codegen,
            },
        }

    return {
        "code_model": model,
        "logic_model": model,
        "reason": "default to single model",
        "samples": {
            "py_model": py_model,
            "py_codegen": py_codegen,
            "md_model": md_model,
            "md_codegen": md_codegen,
        },
    }
