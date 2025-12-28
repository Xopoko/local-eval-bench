from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ALLOWED_FILES = {"impl.py", "tests.py"}


def _find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return start


def _copy_repo_config(repo_root: Path, dest: Path) -> None:
    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        shutil.copy2(pyproject, dest / "pyproject.toml")


def _extract_patch_paths(patch_text: str) -> list[str]:
    paths: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            path = line[4:].strip().split("\t", 1)[0]
            if path == "/dev/null":
                continue
            if path.startswith("a/") or path.startswith("b/"):
                path = path[2:]
            paths.append(path)
    return paths


def _patch_is_safe(patch_text: str) -> tuple[bool, str]:
    if not patch_text.strip():
        return False, "empty patch"

    paths = _extract_patch_paths(patch_text)
    if not paths:
        return False, "no file paths found in patch"

    for path in paths:
        if path.startswith("/"):
            return False, f"absolute path in patch: {path}"
        if ".." in Path(path).parts:
            return False, f"parent path in patch: {path}"
        if Path(path).name not in ALLOWED_FILES:
            return False, f"patch touches disallowed file: {path}"

    return True, ""


def _apply_patch(task_dir: Path, patch_text: str) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write(patch_text)
        patch_path = tmp.name

    for strip in (0, 1):
        result = subprocess.run(
            ["patch", f"-p{strip}", "-i", patch_path, "-s"],
            cwd=task_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True, ""

    return False, result.stderr.strip() or result.stdout.strip()


def _parse_coverage(report_text: str) -> float | None:
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", report_text)
    if not match:
        return None
    return float(match.group(1))


def evaluate(
    task_dir: Path,
    patch_text: str,
    repo_root: Path | None = None,
    min_coverage: float = 90.0,
) -> dict[str, Any]:
    repo_root = _find_repo_root(task_dir) if repo_root is None else repo_root

    safe, reason = _patch_is_safe(patch_text)
    if not safe:
        return {
            "passed": False,
            "patch_applied": False,
            "patch_error": reason,
        }

    added = 0
    removed = 0
    for line in patch_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        task_copy = tmp_path / "task"
        shutil.copytree(task_dir, task_copy)
        _copy_repo_config(repo_root, task_copy)

        applied, error = _apply_patch(task_copy, patch_text)
        if not applied:
            return {
                "passed": False,
                "patch_applied": False,
                "patch_error": error,
                "edit_lines": added + removed,
            }

        cov_run = subprocess.run(
            ["python", "-m", "coverage", "run", "-m", "pytest", "-q", "--maxfail=1"],
            cwd=task_copy,
            capture_output=True,
            text=True,
            check=False,
        )
        tests_ok = cov_run.returncode == 0

        cov_report = subprocess.run(
            ["python", "-m", "coverage", "report", "-m"],
            cwd=task_copy,
            capture_output=True,
            text=True,
            check=False,
        )
        coverage_percent = _parse_coverage(cov_report.stdout)
        coverage_ok = coverage_percent is not None and coverage_percent >= min_coverage

        ruff_run = subprocess.run(
            ["python", "-m", "ruff", "check", "."],
            cwd=task_copy,
            capture_output=True,
            text=True,
            check=False,
        )
        ruff_ok = ruff_run.returncode == 0

    passed = tests_ok and coverage_ok and ruff_ok

    return {
        "passed": passed,
        "patch_applied": True,
        "patch_error": None,
        "tests_ok": tests_ok,
        "coverage_percent": coverage_percent,
        "coverage_ok": coverage_ok,
        "ruff_ok": ruff_ok,
        "pytest_output": cov_run.stdout.strip(),
        "pytest_error": cov_run.stderr.strip(),
        "ruff_output": ruff_run.stdout.strip(),
        "ruff_error": ruff_run.stderr.strip(),
        "edit_lines": added + removed,
    }
