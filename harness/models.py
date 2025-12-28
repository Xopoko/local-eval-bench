from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass

MOCK_ANSWERS: dict[str, str] = {
    "t01_bigO_edges": (
        "Verdict: false.\n"
        "Proof sketch: Plug in n=1 to get 1^2 + 1 = 2 while 1.5 * 1^2 = 1.5, so the "
        "inequality fails at the edge case n=1. For C=1.5 we need n >= 2 so that n <= "
        "0.5 * n^2. Thus the smallest n0 is 2."
    ),
    "t02_polygon_angles": (
        "Verdict: false.\n"
        "Proof sketch: The formula (n - 2) * pi is for simple polygons with n >= 3. "
        "A 2-gon is excluded by the usual definition, so the n=2 case is not valid. "
        "Self-intersecting polygons also do not satisfy the same interior-angle sum. "
        "Therefore the claim is false."
    ),
    "t03_series_eps": (
        "Verdict: false.\n"
        "Proof sketch: For any n, sum_{k=n}^{2n} 1/k is bounded below by the integral "
        "from n to 2n of 1/x dx, which equals log 2. Hence the tail sum is >= log 2 "
        "for all n>=N, so it cannot be made smaller than an arbitrary eps."
    ),
    "t04_ineq_border": (
        "Verdict: false.\n"
        "Proof sketch: At the boundary x=0 we have x^2 = 0, which is not strictly less "
        "than x. At x=1 we have x^2 = x as well. The strict inequality only holds for "
        "0 < x < 1, so the stated claim on the closed interval fails at the boundary."
    ),
    "s01_compactness": (
        "Lemma: If K is compact and F is closed in K, then F is compact.\n"
        "Proof sketch: Let {U_i} be an open cover of F in the subspace "
        "topology, so each U_i = V_i intersect F with V_i open in X. "
        "Then {V_i} together with X \\ F covers K. By compactness of K "
        "there is a finite subcover, which restricts to a finite "
        "subcover of F."
    ),
    "s02_lipschitz": (
        "Lemma: If f is L-Lipschitz on (X, d), then f is uniformly continuous.\n"
        "Proof sketch: Given eps > 0, choose delta = eps / L. If d(x, y) < delta then "
        "|f(x) - f(y)| <= L * d(x, y) < eps. The delta depends only on eps, so the "
        "continuity is uniform."
    ),
    "s03_cntrex": (
        "Lemma: The functions f_n(x) = x^n on [0, 1] are continuous and converge "
        "pointwise to f(x) that equals 0 on [0, 1) and 1 at x=1, so the limit is "
        "discontinuous.\n"
        "Proof sketch: For each fixed x in [0, 1) we have x^n -> 0, while at x=1 the "
        "limit is 1. This defines a pointwise limit with a jump at 1."
    ),
    "s04_graph_lemma": (
        "Lemma: Every tree with n vertices has n-1 edges.\n"
        "Proof sketch: Use induction on n. For n=1 the statement is clear. A tree with "
        "n>1 has a leaf; removing it gives a tree with n-1 vertices and n-2 edges. "
        "Adding the leaf back adds one edge, yielding n-1 edges."
    ),
}


@dataclass
class ModelClient:
    cmd_template: str | None
    mock: bool = False

    def generate(self, prompt: str, model: str, task_type: str, task_id: str) -> str:
        if self.mock or not self.cmd_template:
            return self._mock_response(task_id, task_type, prompt)
        cmd = self.cmd_template.format(
            model=model,
            task_type=task_type,
            task_id=task_id,
        )
        args = shlex.split(cmd)
        result = subprocess.run(
            args,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(
                f"Model command failed (code {result.returncode}): {stderr}"
            )
        return result.stdout

    def _mock_response(self, task_id: str, task_type: str, prompt: str) -> str:
        if task_id in MOCK_ANSWERS:
            return MOCK_ANSWERS[task_id]
        if task_type == "py":
            return ""
        if task_type == "synth":
            return "Lemma: ...\nProof sketch: ..."
        return "Verdict: true.\nProof sketch: ..."


def default_model_client(mock: bool = False) -> ModelClient:
    cmd_template = os.environ.get("LOCAL_EVAL_MODEL_CMD")
    if not cmd_template:
        return ModelClient(cmd_template=None, mock=True)
    return ModelClient(cmd_template=cmd_template, mock=mock)


def arbiter_client() -> ModelClient:
    cmd_template = os.environ.get("LOCAL_EVAL_ARBITER_CMD")
    if not cmd_template:
        return ModelClient(cmd_template=None, mock=True)
    return ModelClient(cmd_template=cmd_template, mock=False)
