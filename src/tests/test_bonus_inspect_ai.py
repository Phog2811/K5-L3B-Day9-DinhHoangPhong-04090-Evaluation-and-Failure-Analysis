"""Bonus (+5): verify Inspect AI ported scorers match pydantic-evals graders 100%.

Skipped automatically when inspect-ai is not installed (e.g. standard CI environment).
"""

from __future__ import annotations

import pytest

inspect_ai = pytest.importorskip("inspect_ai")

from pathlib import Path  # noqa: E402
from lab9.bonus_inspect import PORTED_METRICS, compare_shape  # noqa: E402
from lab9.eval import load_spec  # noqa: E402


@pytest.mark.parametrize("shape", ["fixed", "seeded_regression"])
def test_inspect_ai_graders_match_pydantic_evals(shape):
    spec = load_spec(Path("config/metric_spec.yaml"))
    res = compare_shape(shape, spec)
    assert res["mismatches"] == []
    for metric in PORTED_METRICS:
        assert res["summary"][metric]["delta"] == 0
