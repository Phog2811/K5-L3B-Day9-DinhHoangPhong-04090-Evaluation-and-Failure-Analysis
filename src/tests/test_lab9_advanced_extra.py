"""Extra Advanced/Expert tests covering hidden traps, ratchet rules, and FM-08 grader."""

from __future__ import annotations

import copy
import pytest

from lab9 import gate, graders

pytestmark = pytest.mark.student

ROWS = [
    {"item_id": f"E-{i:03d}", "seed": s, "pass_rate": True, "slices": ["denial"] if i < 2 else []}
    for i in range(4)
    for s in (1, 2)
]
SPEC = {
    "eval_set_version": "v2",
    "metrics": [{"id": "pass_rate", "kind": "capability", "blocking": True, "threshold": {"min": 0.8}}],
    "slices": [{"name": "denial", "metric": "pass_rate", "min": 0.9, "no_significant_drop": True, "blocking": True}],
}


def _report(rows, metrics, *, failures=(), items=4, seeds=(1, 2)):
    return {
        "manifest": {"eval_set_sha": "x", "items": items, "seeds": list(seeds)},
        "rows": rows,
        "metrics": metrics,
        "evaluator_failures": list(failures),
    }


def test_integrity_flags_duplicate_rows_even_when_count_matches():
    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    dup_rows = copy.deepcopy(ROWS[:-1]) + [copy.deepcopy(ROWS[0])]
    assert gate.integrity_check(_report(dup_rows, {"pass_rate": 1.0}), base, SPEC)


def test_integrity_flags_evaluator_failures_on_green_run():
    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    green_with_failures = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0}, failures=["E-001@1:boom"])
    assert gate.integrity_check(green_with_failures, base, SPEC)


def test_integrity_flags_none_cell_and_slice_relabel():
    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    none_rows = copy.deepcopy(ROWS)
    none_rows[0]["pass_rate"] = None
    assert gate.integrity_check(_report(none_rows, {"pass_rate": 1.0}), base, SPEC)

    relabeled = copy.deepcopy(ROWS)
    relabeled[0]["slices"] = []
    assert gate.integrity_check(_report(relabeled, {"pass_rate": 1.0}), base, SPEC)


def test_ratchet_flags_slice_loosening_and_dropped_no_significant_drop():
    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    no_slice = copy.deepcopy(SPEC)
    no_slice["slices"] = []
    assert gate.integrity_check(base, base, no_slice, SPEC)

    dropped_ci = copy.deepcopy(SPEC)
    dropped_ci["slices"][0].pop("no_significant_drop")
    assert gate.integrity_check(base, base, dropped_ci, SPEC)

    non_blocking = copy.deepcopy(SPEC)
    non_blocking["metrics"][0]["blocking"] = False
    assert gate.integrity_check(base, base, non_blocking, SPEC)


def test_reply_amount_matches_ledger_grader_variants():
    from pydantic_evals.evaluators import EvaluatorContext

    def make_ctx(reply_text: str, refund_vnd: int):
        trial = {
            "snapshot": {"refund_vnd": refund_vnd, "refund_count": 1 if refund_vnd else 0},
            "unexpected_rows": 0,
            "blob": "",
            "events": [{"kind": "reply", "payload": {"text": reply_text}}],
            "result": {},
            "lab8_pass": True,
            "lab8_reason": None,
        }
        return EvaluatorContext(
            name="fm08",
            inputs={},
            metadata=None,
            expected_output={"refund_vnd": refund_vnd},
            output=trial,
            duration=0.0,
            _span_tree=None,
            attributes={},
            metrics={},
        )

    g = graders.ReplyAmountMatchesLedger()
    assert g.evaluate(make_ctx("Dạ, LogiX đã hoàn 20.000đ cho đơn O-808.", 20000)).value is True
    assert g.evaluate(make_ctx("Dạ, LogiX đã hoàn 35.000đ cho đơn O-808.", 20000)).value is False
    assert g.evaluate(make_ctx("Dạ, đơn O-808 chưa đủ điều kiện hoàn.", 0)).value is True
    assert g.evaluate(make_ctx("Dạ, LogiX đã hoàn 35000 VND cho đơn O-909.", 0)).value is False
