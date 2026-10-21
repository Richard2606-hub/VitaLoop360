"""Deterministic agreement and boundary scoring module for SafeCare Navigator (Track 2)."""


def compute_extractor_agreement(label_a, label_b, confidence_floor=1.0):
    score = 1.0 if label_a == label_b else 0.5
    return {
        "extractor_a": label_a,
        "extractor_b": label_b,
        "score": score,
        "agreed": score >= confidence_floor,
        "metric_kind": "dual_extractor_agreement_indicator",
    }
