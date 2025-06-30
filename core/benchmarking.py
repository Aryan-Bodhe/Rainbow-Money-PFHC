from models.DerivedMetrics import PersonalFinanceMetrics
from .user_segment_classifier import classify_income_bracket
from data.ideal_benchmark_data import IDEAL_RANGES


def get_benchmarks(pfm: PersonalFinanceMetrics) -> dict[str, tuple[float, float]]:
    """
    Returns a dict mapping each metric to its ideal (min, max) benchmark values based on the user's profile.
    """
    benchmarks: dict[str, tuple[float, float]] = {}
    tier_key = f"Tier {pfm.city_tier}"
    bracket = classify_income_bracket(pfm.total_monthly_income)

    for metric, ideal in IDEAL_RANGES.items():
        if isinstance(ideal, dict):
            min_i, max_i = ideal[tier_key][bracket]
        else:
            min_i, max_i = ideal
        benchmarks[metric] = (min_i, max_i)
    return benchmarks

