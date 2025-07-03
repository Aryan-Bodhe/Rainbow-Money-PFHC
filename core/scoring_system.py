from data.ideal_benchmark_data import IDEAL_RANGES
from models.DerivedMetrics import PersonalFinanceMetrics, Metric
from .user_segment_classifier import classify_income_bracket


def score_metrics(
    pfm: PersonalFinanceMetrics,
    weights: dict[str, float]
) -> dict[str, float]:
    """
    Updates the assigned_score field inside each Metric in pfm,
    and also returns a flat {metric_label: score} dictionary for external use.
    """
    scores: dict[str, float] = {}
    tier_key = f"Tier {pfm.city_tier}"
    bracket = classify_income_bracket(pfm.total_monthly_income)

    for metric_label, w in weights.items():
        # 1. Normalize label to match attribute name
        norm_key = (
            metric_label
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        # 2. Find benchmark
        ideal = IDEAL_RANGES.get(norm_key)
        if ideal is None:
            print(f"[WARN] Skipping unknown metric '{metric_label}'")
            continue

        # 3. Unpack min/max benchmark
        if isinstance(ideal, dict):
            min_i, max_i = ideal[tier_key][bracket]
        else:
            min_i, max_i = ideal

        # 4. Get metric object
        metric_obj = getattr(pfm, norm_key, None)
        if not isinstance(metric_obj, Metric):
            print(f"[WARN] Metric '{norm_key}' not found or invalid.")
            continue

        # 5. Compute score and assign
        score = _score_value(metric_obj, min_i, max_i, w)
        metric_obj.assigned_score = score
        scores[metric_label] = score

    return scores


def _score_value(metric: Metric, ideal_min: float, ideal_max: float, max_score: float) -> float:
    """
    Compute score for a metric based on its value vs benchmark range.
    """
    val = metric.value
    if val is None or max_score == 0:
        return 0.0
    if ideal_min <= val <= ideal_max:
        return max_score
    ratio = val / ideal_min if val < ideal_min else ideal_max / val
    return max_score * (0.2 + 0.8 * max(0.0, min(1.0, ratio)))
