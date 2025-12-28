"""Graders for local eval tasks."""

from . import grade_lean, grade_md, grade_py, grade_synth

__all__ = ["grade_md", "grade_py", "grade_synth", "grade_lean"]
