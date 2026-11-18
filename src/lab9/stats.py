"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
import math

import numpy as np
from scipy import stats as sp_stats

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def _norm(label: str) -> str:
    return str(label).strip().upper()


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError(f"length mismatch: human={len(human)}, judge={len(judge)}")
    tp = fp = fn = tn = 0
    for h, j in zip(human, judge):
        h_pos = _norm(h) == POS
        j_pos = _norm(j) == POS
        if h_pos and j_pos:
            tp += 1
        elif not h_pos and j_pos:
            fp += 1
        elif h_pos and not j_pos:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    cm = confusion(human, judge)
    p = cm["tp"] / (cm["tp"] + cm["fp"]) if (cm["tp"] + cm["fp"]) else 0.0
    r = cm["tp"] / (cm["tp"] + cm["fn"]) if (cm["tp"] + cm["fn"]) else 0.0
    return p, r


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = cm["tp"] + cm["fp"] + cm["fn"] + cm["tn"]
    if n == 0:
        raise ValueError("cannot compute kappa on empty input")
    p_o = (cm["tp"] + cm["tn"]) / n
    h_pos = cm["tp"] + cm["fn"]
    j_pos = cm["tp"] + cm["fp"]
    h_neg = cm["tn"] + cm["fp"]
    j_neg = cm["tn"] + cm["fn"]
    p_e = ((h_pos * j_pos) + (h_neg * j_neg)) / (n * n)
    if p_e >= 1.0 - 1e-12:
        raise ValueError("kappa is undefined when expected agreement p_e == 1")
    return (p_o - p_e) / (1.0 - p_e)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    denom = sensitivity + specificity - 1.0
    if abs(denom) <= 1e-12 or denom < 0:
        return float(min(1.0, max(0.0, observed_rate)))
    raw = (observed_rate + specificity - 1.0) / denom
    return float(min(1.0, max(0.0, raw)))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    if len(a_arr) != len(b_arr):
        raise ValueError(f"length mismatch: a={len(a_arr)}, b={len(b_arr)}")
    if len(a_arr) == 0 or np.array_equal(a_arr, b_arr):
        return (0.0, 0.0, 0.0)
    diff = float(np.mean(a_arr) - np.mean(b_arr))
    res = sp_stats.bootstrap(
        (a_arr, b_arr),
        statistic=lambda x, y, axis=-1: np.mean(x, axis=axis) - np.mean(y, axis=axis),
        paired=True,
        n_resamples=n_resamples,
        method="percentile",
        confidence_level=confidence,
        rng=np.random.default_rng(rng),
    )
    return (diff, float(res.confidence_interval.low), float(res.confidence_interval.high))


def _validate_nck(n: int, c: int, k: int) -> None:
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (n, c, k)):
        raise ValueError("n, c, k must be integers")
    if n < 1 or k < 1 or k > n or c < 0 or c > n:
        raise ValueError(f"invalid (n={n}, c={c}, k={k}): require 1 <= k <= n and 0 <= c <= n")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    _validate_nck(n, c, k)
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    _validate_nck(n, c, k)
    return math.comb(c, k) / math.comb(n, k)
