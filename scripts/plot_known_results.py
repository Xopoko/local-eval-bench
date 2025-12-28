#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

DATA = [
    {
        "model": "openai/gpt-5.1-codex-max",
        "pass_at_1": 0.33,
        "pass_at_5": 1.00,
        "avg_pass_rate": 0.50,
    },
    {
        "model": "anthropic/claude-opus-4.5",
        "pass_at_1": 0.83,
        "pass_at_5": 0.83,
        "avg_pass_rate": 0.80,
    },
    {
        "model": "anthropic/claude-sonnet-4",
        "pass_at_1": 0.67,
        "pass_at_5": 0.83,
        "avg_pass_rate": 0.73,
    },
    {
        "model": "openai/gpt-5.1-codex-mini",
        "pass_at_1": 0.33,
        "pass_at_5": 0.50,
        "avg_pass_rate": 0.20,
    },
    {
        "model": "openai/gpt-5.2",
        "pass_at_1": 0.33,
        "pass_at_5": 0.33,
        "avg_pass_rate": 0.30,
    },
    {
        "model": "openai/gpt-5-mini",
        "pass_at_1": 0.00,
        "pass_at_5": 0.00,
        "avg_pass_rate": 0.00,
    },
    {
        "model": "openai/gpt-5-nano",
        "pass_at_1": 0.00,
        "pass_at_5": 0.00,
        "avg_pass_rate": 0.00,
    },
]


def main() -> None:
    models = [row["model"] for row in DATA]
    pass_at_1 = [row["pass_at_1"] for row in DATA]
    pass_at_5 = [row["pass_at_5"] for row in DATA]

    height = 0.35
    y = list(range(len(models)))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh([i + height / 2 for i in y], pass_at_5, height=height, label="pass@5")
    ax.barh([i - height / 2 for i in y], pass_at_1, height=height, label="pass@1")

    ax.set_xlim(0, 1)
    ax.set_xlabel("Score")
    ax.set_title("Lean-only benchmark (6 tasks, K=5)")
    ax.set_yticks(y)
    ax.set_yticklabels(models)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="lower right")

    for idx, value in enumerate(pass_at_5):
        ax.text(min(value + 0.02, 0.98), idx + height / 2, f"{value:.2f}", va="center")

    out_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "assets"
        / "lean_known_results.png"
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)


if __name__ == "__main__":
    main()
