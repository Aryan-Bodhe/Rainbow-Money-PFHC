from models.DerivedMetrics import PersonalFinanceMetrics, Metric
from models.BenchmarkData import BenchmarkData
from .user_segment_classifier import classify_income_bracket
from data.ideal_benchmark_data import IDEAL_RANGES


def get_benchmarks(pfm: PersonalFinanceMetrics) -> BenchmarkData:
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

    benchmark_data = BenchmarkData(**benchmarks)
    return benchmark_data


def analyse_metrics_against_benchmarks(pfm: PersonalFinanceMetrics):
    if pfm is None:
        raise ValueError("Metrics not Provided.")

    benchmarks = get_benchmarks(pfm).model_dump()  # dict[str, tuple[float, float]]

    low_relax_stage_1 = 0.85
    high_relax_stage_1 = 1.15
    low_relax_stage_2 = 0.7
    high_relax_stage_2 = 1.3

    for key, (bm_low, bm_high) in benchmarks.items():
        metric_obj = getattr(pfm, key, None)

        if not isinstance(metric_obj, Metric):
            continue  # Skip if not a Metric field

        user_val = metric_obj.value
        if user_val is None or user_val == 999:
            metric_obj.verdict = "error_computing_metric"
            continue

        if user_val < bm_low * low_relax_stage_2:
            verdict = "extremely_low"
        elif user_val < bm_low * low_relax_stage_1:
            verdict = "low"
        elif user_val < bm_low:
            verdict = "good"
        elif user_val < bm_high:
            verdict = "excellent"
        elif user_val < bm_high * high_relax_stage_1:
            verdict = "good"
        elif user_val < bm_high * high_relax_stage_2:
            verdict = "high"
        else:
            verdict = "extremely_high"

        metric_obj.verdict = verdict

