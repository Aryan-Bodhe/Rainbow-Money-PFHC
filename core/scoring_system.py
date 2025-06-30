from data.ideal_benchmark_data import IDEAL_RANGES
from models.DerivedMetrics import PersonalFinanceMetrics
from .user_segment_classifier import classify_income_bracket


def score_metrics(
    pfm: PersonalFinanceMetrics,
    weights: dict[str, float]
) -> dict[str, float]:
    """
    Returns a dict mapping each *original* metric name from weights
    to its scored value, by normalizing the key for lookup in IDEAL_RANGES.
    """
    scores: dict[str, float] = {}
    tier_key = f"Tier {pfm.city_tier}"
    bracket = classify_income_bracket(pfm.total_monthly_income)

    for metric_label, w in weights.items():
        # 1) Normalize the label to snake_case to match IDEAL_RANGES & pfm attributes
        norm_key = (
            metric_label
            .strip()
            .lower()
            .replace('-', '_')
            .replace(' ', '_')
        )

        # 2) Find the ideal range
        ideal = IDEAL_RANGES.get(norm_key)
        if ideal is None:
            # no benchmark defined for this metric—skip or warn
            print(f"[WARN] Skipping unknown metric '{metric_label}'")
            continue

        # 3) Unpack min/max depending on whether tiered or flat
        if isinstance(ideal, dict):
            min_i, max_i = ideal[tier_key][bracket]
        else:
            min_i, max_i = ideal

        # 4) Get the user's value from pfm
        val = getattr(pfm, norm_key, None)

        # 5) Compute the score
        scores[metric_label] = _score_value(val, min_i, max_i, w)

    return scores


def _score_value(val: float, ideal_min: float, ideal_max: float, max_score: float) -> float:
    """
    - full max_score if val in [ideal_min, ideal_max]
    - if val < ideal_min: score scaled by (val / ideal_min) * 0.8 + 0.2
    - if val > ideal_max: score scaled by (ideal_max / val) * 0.8 + 0.2
    """
    if val is None or max_score == 0:
        return 0.0
    if ideal_min <= val <= ideal_max:
        return max_score
    ratio = val / ideal_min if val < ideal_min else ideal_max / val
    return max_score * (0.2 + 0.8 * max(0.0, min(1.0, ratio)))
