from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from harness import core
from harness.models import arbiter_client, default_model_client
from harness.router import choose_route


def _pass_rate(
    results: list[dict[str, Any]],
    task_type: str | None = None,
    key: str = "pass_at_1",
) -> float | None:
    filtered = [r for r in results if task_type is None or r["task_type"] == task_type]
    if not filtered:
        return None
    values: list[float] = []
    for r in filtered:
        value = r.get(key)
        if isinstance(value, (int, float, bool)):
            values.append(float(value))
    if not values:
        return None
    return sum(values) / len(values)


def _avg_time_to_fix(results: list[dict[str, Any]]) -> float | None:
    values = [r["time_to_fix"] for r in results if r["time_to_fix"] not in (None, 0.0)]
    if not values:
        return None
    return sum(values) / len(values)


def _avg_py_coverage(results: list[dict[str, Any]]) -> float | None:
    cov_values = []
    for r in results:
        if r["task_type"] != "py":
            continue
        attempts = r["attempts"]
        if not attempts:
            continue
        details = attempts[-1]["details"]
        cov = details.get("coverage_percent")
        if cov is not None:
            cov_values.append(cov)
    if not cov_values:
        return None
    return sum(cov_values) / len(cov_values)


def _write_summary(
    report_dir: Path,
    run_meta: dict[str, Any],
    results: list[dict[str, Any]],
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = report_dir / "summary.md"

    lines = []
    lines.append("# Summary")
    lines.append("")
    lines.append(f"Run time: {run_meta['timestamp']}")
    lines.append(f"Model (logic): {run_meta['logic_model']}")
    lines.append(f"Model (code): {run_meta['code_model']}")
    lines.append("")

    overall = _pass_rate(results)
    overall_k = _pass_rate(results, key="pass_at_k")
    overall_rate = _pass_rate(results, key="pass_rate")
    md_rate = _pass_rate(results, "md")
    py_rate = _pass_rate(results, "py")
    synth_rate = _pass_rate(results, "synth")
    lean_rate = _pass_rate(results, "lean")
    md_k = _pass_rate(results, "md", key="pass_at_k")
    py_k = _pass_rate(results, "py", key="pass_at_k")
    synth_k = _pass_rate(results, "synth", key="pass_at_k")
    lean_k = _pass_rate(results, "lean", key="pass_at_k")
    md_rate_avg = _pass_rate(results, "md", key="pass_rate")
    py_rate_avg = _pass_rate(results, "py", key="pass_rate")
    synth_rate_avg = _pass_rate(results, "synth", key="pass_rate")
    lean_rate_avg = _pass_rate(results, "lean", key="pass_rate")
    ttf_avg = _avg_time_to_fix(results)
    cov_avg = _avg_py_coverage(results)
    k = run_meta.get("max_tries", 1)

    lines.append("## Metrics")
    lines.append("")
    lines.append(
        f"- pass@1 overall: {overall:.2f}"
        if overall is not None
        else "- pass@1 overall: n/a"
    )
    if overall_k is not None:
        lines.append(f"- pass@{k} overall: {overall_k:.2f}")
    if overall_rate is not None:
        lines.append(f"- avg pass rate overall: {overall_rate:.2f}")
    lines.append(
        f"- pass@1 md: {md_rate:.2f}"
        if md_rate is not None
        else "- pass@1 md: n/a"
    )
    if md_k is not None:
        lines.append(f"- pass@{k} md: {md_k:.2f}")
    if md_rate_avg is not None:
        lines.append(f"- avg pass rate md: {md_rate_avg:.2f}")
    lines.append(
        f"- pass@1 py: {py_rate:.2f}"
        if py_rate is not None
        else "- pass@1 py: n/a"
    )
    if py_k is not None:
        lines.append(f"- pass@{k} py: {py_k:.2f}")
    if py_rate_avg is not None:
        lines.append(f"- avg pass rate py: {py_rate_avg:.2f}")
    lines.append(
        f"- pass@1 synth: {synth_rate:.2f}"
        if synth_rate is not None
        else "- pass@1 synth: n/a"
    )
    if synth_k is not None:
        lines.append(f"- pass@{k} synth: {synth_k:.2f}")
    if synth_rate_avg is not None:
        lines.append(f"- avg pass rate synth: {synth_rate_avg:.2f}")
    if lean_rate is not None:
        lines.append(f"- pass@1 lean: {lean_rate:.2f}")
    if lean_k is not None:
        lines.append(f"- pass@{k} lean: {lean_k:.2f}")
    if lean_rate_avg is not None:
        lines.append(f"- avg pass rate lean: {lean_rate_avg:.2f}")
    if ttf_avg is not None:
        lines.append(f"- avg time-to-fix (sec): {ttf_avg:.2f}")
    else:
        lines.append("- avg time-to-fix (sec): n/a")
    if cov_avg is not None:
        lines.append(f"- avg py coverage (%): {cov_avg:.1f}")
    else:
        lines.append("- avg py coverage (%): n/a")

    lines.append("")
    lines.append("## Tasks")
    lines.append("")
    for r in results:
        status = "PASS" if r.get("pass_at_k") else "FAIL"
        lines.append(f"- {r['task_id']} ({r['task_type']}): {status}")

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_metrics(
    report_dir: Path,
    run_meta: dict[str, Any],
    results: list[dict[str, Any]],
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = report_dir / "metrics.json"

    metrics = {
        "run": run_meta,
        "results": results,
        "pass_at_1": {
            "overall": _pass_rate(results),
            "md": _pass_rate(results, "md"),
            "py": _pass_rate(results, "py"),
            "synth": _pass_rate(results, "synth"),
            "lean": _pass_rate(results, "lean"),
        },
        "pass_at_k": {
            "overall": _pass_rate(results, key="pass_at_k"),
            "md": _pass_rate(results, "md", key="pass_at_k"),
            "py": _pass_rate(results, "py", key="pass_at_k"),
            "synth": _pass_rate(results, "synth", key="pass_at_k"),
            "lean": _pass_rate(results, "lean", key="pass_at_k"),
        },
        "pass_rate": {
            "overall": _pass_rate(results, key="pass_rate"),
            "md": _pass_rate(results, "md", key="pass_rate"),
            "py": _pass_rate(results, "py", key="pass_rate"),
            "synth": _pass_rate(results, "synth", key="pass_rate"),
            "lean": _pass_rate(results, "lean", key="pass_rate"),
        },
        "time_to_fix_avg": _avg_time_to_fix(results),
        "py_coverage_avg": _avg_py_coverage(results),
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    csv_path = report_dir / "metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "task_id",
                "type",
                "model",
                "pass_at_1",
                "pass_at_k",
                "pass_rate",
                "time_to_fix",
            ]
        )
        for r in results:
            writer.writerow(
                [
                    r["task_id"],
                    r["task_type"],
                    r["model"],
                    r["pass_at_1"],
                    r.get("pass_at_k"),
                    r.get("pass_rate"),
                    r["time_to_fix"],
                ]
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-5.2")
    parser.add_argument("--codegen", default=None)
    parser.add_argument("--auto-route", action="store_true")
    parser.add_argument("--max-tries", type=int, default=5)
    parser.add_argument("--min-coverage", type=float, default=90.0)
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--task-types", default="md,py,synth,lean")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    tasks_root = repo_root / "tasks"

    tasks = core.list_tasks(tasks_root)
    task_types = [t.strip() for t in args.task_types.split(",") if t.strip()]
    allowed_types = set(task_types)
    order = ["md", "py", "synth", "lean"]
    tasks_all: list[core.Task] = []
    for task_type in order:
        if task_type in allowed_types:
            tasks_all.extend(tasks.get(task_type, []))
    if not tasks_all:
        raise SystemExit(f"No tasks found for types: {', '.join(task_types)}")
    if args.auto_route:
        route = choose_route(
            repo_root=repo_root,
            model=args.model,
            codegen=args.codegen or args.model,
            max_tries=1,
            min_coverage=args.min_coverage,
            mock=args.mock,
        )
        logic_model = route["logic_model"]
        code_model = route["code_model"]
    else:
        logic_model = args.model
        code_model = args.codegen or args.model

    model_client = default_model_client(mock=args.mock)
    arbiter = arbiter_client() if os.environ.get("LOCAL_EVAL_ARBITER_CMD") else None

    results: list[dict[str, Any]] = []
    report_dir = repo_root / args.reports_dir
    existing_ids: set[str] = set()
    metrics_path = report_dir / "metrics.json"
    if args.resume and metrics_path.exists():
        data = json.loads(metrics_path.read_text(encoding="utf-8"))
        existing_results = data.get("results", [])
        if isinstance(existing_results, list):
            results.extend(existing_results)
            existing_ids = {
                r.get("task_id") for r in existing_results if isinstance(r, dict)
            }

    run_meta = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "logic_model": logic_model,
        "code_model": code_model,
        "max_tries": args.max_tries,
        "min_coverage": args.min_coverage,
        "mock": args.mock,
        "task_types": task_types,
    }

    tasks_to_run = [t for t in tasks_all if t.task_id not in existing_ids]
    total = len(tasks_to_run)

    for idx, task in enumerate(tasks_to_run, start=1):
        model_name = code_model if task.task_type == "py" else logic_model
        message = (
            f"[{idx}/{total}] start {task.task_id} ({task.task_type}) "
            f"model={model_name}"
        )
        print(message, flush=True)
        task_start = time.time()
        try:
            result = core.evaluate_task(
                task,
                model_client,
                model_name,
                repo_root,
                max_tries=args.max_tries,
                min_coverage=args.min_coverage,
                arbiter=arbiter,
                continue_on_error=args.continue_on_error,
            )
        except Exception as exc:
            elapsed = time.time() - task_start
            print(
                f"[{idx}/{total}] error {task.task_id} ({task.task_type}) "
                f"after {elapsed:.1f}s: {type(exc).__name__}: {exc}",
                flush=True,
            )
            raise
        results.append(result)
        elapsed = time.time() - task_start
        status = "PASS" if result.get("pass_at_k") else "FAIL"
        model_error = None
        if result["attempts"]:
            model_error = result["attempts"][0].get("model_error")
        suffix = f" error={model_error}" if model_error else ""
        print(
            f"[{idx}/{total}] done {task.task_id} ({task.task_type}) "
            f"status={status} elapsed={elapsed:.1f}s{suffix}",
            flush=True,
        )
        _write_summary(report_dir, run_meta, results)
        _write_metrics(report_dir, run_meta, results)

    _write_summary(report_dir, run_meta, results)
    _write_metrics(report_dir, run_meta, results)


if __name__ == "__main__":
    main()
