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


def analyse_benchmarks(pfm: PersonalFinanceMetrics) -> dict:
    if pfm is None:
        raise ValueError('Metrics not Provided.')
    benchmarks = get_benchmarks(pfm)
    metrics = pfm.model_dump()
    analysis = {}

    low_relax_stage_1 = 0.85
    high_relax_stage_1 = 1.15

    low_relax_stage_2 = 0.7
    high_relax_stage_2 = 1.3
    
    for key, value in benchmarks.items():
        bm_low = value[0]
        bm_high = value[1]
        user_val = metrics[key]

        if user_val == 999:
            analysis[key] = 'error_computing_metric'
            continue

        if not isinstance(user_val, float):
            analysis[key] = 'invalid_metric_value'
            continue

        if user_val < bm_low * low_relax_stage_2:
            analysis[key] = 'urgent_attention_needed: too low'
        elif user_val < bm_low * low_relax_stage_1 :
            analysis[key] = 'improvement_needed: low'
        elif user_val < bm_low:
            analysis[key] = 'good'
        elif user_val < bm_high:
            analysis[key] = 'excellent'
        elif user_val <  bm_high * high_relax_stage_1:
            analysis[key] = 'good'
        elif user_val < bm_high * high_relax_stage_2:
            analysis[key] = 'improvement_needed: high'
        else:
            analysis[key] = 'urgent_attention_needed: too high'

    return analysis
