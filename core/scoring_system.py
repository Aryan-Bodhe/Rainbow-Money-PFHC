from data.ideal_benchmark_data import IDEAL_RANGES
from models.DerivedMetrics import PersonalFinanceMetrics, Metric
from .user_segment_classifier import classify_income_bracket


def score_metrics(
    pfm: PersonalFinanceMetrics,
    weights: dict[str, float]
) -> dict[str, float]:
    """
    Scores each personal finance metric based on ideal benchmark ranges and user-specific context.

    This function:
    1. Iterates over provided metric weights.
    2. Finds the matching benchmark range from `IDEAL_RANGES`, adjusted for:
       - User's city tier (e.g., Tier 1, Tier 2, Tier 3).
       - User's income bracket.
    3. Computes a score for each metric relative to the ideal range.
    4. Updates the `assigned_score` field in each `Metric` object in `pfm`.
    5. Returns a flat dictionary mapping metric labels to computed scores.

    Args:
        pfm (PersonalFinanceMetrics):
            An object holding computed financial metrics for the user.
        weights (dict[str, float]):
            Mapping of metric labels to their maximum score weights.

    Returns:
        dict[str, float]: A dictionary mapping metric labels (as given in `weights`) to their computed scores.

    Notes:
        - Unknown metrics in `weights` are skipped with a warning.
        - Missing benchmark data for a metric will also result in skipping that metric.
        - Some metrics are treated as "lower is better" when scoring.

    Example:
        >>> score_metrics(pfm, {"expense_income_ratio": 10, "savings_rate": 15})
        {"expense_income_ratio": 8.5, "savings_rate": 12.0}
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
    Computes the score for a single metric based on its value relative to the benchmark range.

    The score is scaled between 0 and `max_score` depending on how close
    the metric value is to the ideal range:
      - If the value is within the ideal range, full points (`max_score`) are awarded.
      - If outside the range, a proportional score is computed.
      - For certain metrics (e.g., expense-income ratio, debt-income ratio),
        lower values are considered better.

    Args:
        metric (Metric): The metric object containing `value` and `metric_name`.
        ideal_min (float): Lower bound of the ideal range for this metric.
        ideal_max (float): Upper bound of the ideal range for this metric.
        max_score (float): Maximum score that can be awarded for this metric.

    Returns:
        float: Computed score between 0.0 and `max_score`.
    """
    lower_better_metrics = ['expense_income_ratio', 'debt_income_ratio', 'housing_income_ratio']
    val = metric.value

    if val is None or max_score == 0:
        return 0.0

    if val == 999:  # Special placeholder value
        if metric.metric_name in lower_better_metrics:
            return 0.0
        else:
            return max_score

    if ideal_min <= val <= ideal_max:
        return max_score

    ratio = val / ideal_min if val < ideal_min else ideal_max / val
    return max_score * (0.2 + 0.8 * max(0.0, min(1.0, ratio)))
