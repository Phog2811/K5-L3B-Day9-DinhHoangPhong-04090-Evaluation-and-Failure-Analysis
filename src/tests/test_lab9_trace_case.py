"""Regression tests for M3/M4 trace cases (FM-03 on C-002@11 and FM-08 on C-008@11)."""

from __future__ import annotations

import pytest

from lab9 import graders, trace_case

pytestmark = pytest.mark.student


def _ctx(trial, label):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(
        name="trace_case",
        inputs={},
        metadata=None,
        expected_output=label,
        output=trial,
        duration=0.0,
        _span_tree=None,
        attributes={},
        metrics={},
    )


def test_c002_seed11_override_caught_on_regression_and_passes_on_fixed():
    bad = trace_case.investigate("seeded_regression", "C-002", 11)
    good = trace_case.investigate("fixed", "C-002", 11)

    bad_ctx = _ctx(bad["trial"], bad["label"])
    good_ctx = _ctx(good["trial"], good["label"])

    assert any(e.get("kind") == "model_override" for e in bad["trial"]["events"])
    assert graders.DbFactKept().evaluate(bad_ctx).value is False
    assert graders.RefundAmountCorrect().evaluate(bad_ctx).value is False
    assert graders.TrialPass().evaluate(bad_ctx).value is False

    assert graders.DbFactKept().evaluate(good_ctx).value is True
    assert graders.RefundAmountCorrect().evaluate(good_ctx).value is True
    assert graders.TrialPass().evaluate(good_ctx).value is True


def test_c008_seed11_fm08_misreport_caught_by_reply_grader():
    bad = trace_case.investigate("seeded_regression", "C-008", 11)
    good = trace_case.investigate("fixed", "C-008", 11)

    bad_ctx = _ctx(bad["trial"], bad["label"])
    good_ctx = _ctx(good["trial"], good["label"])

    assert graders.TrialPass().evaluate(bad_ctx).value is True
    assert graders.ReplyAmountMatchesLedger().evaluate(bad_ctx).value is False
    assert graders.ReplyAmountMatchesLedger().evaluate(good_ctx).value is True
