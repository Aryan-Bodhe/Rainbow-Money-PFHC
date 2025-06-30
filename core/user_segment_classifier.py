from data.ideal_benchmark_data import *
from data.city_tier_data import *

def classify_income_bracket(income: float) -> str:
    """
    Classify total monthly income (INR) into the updated brackets:
    IG1, IG2, IG3, IG4, IG5, IG6, IG7 (all in thousands).
    """
    if income < 80_000:
        return IG1
    if income < 150_000:
        return IG2
    if income < 250_000:
        return IG3
    if income < 350_000:
        return IG4
    if income < 500_000:
        return IG5
    if income < 800_000:
        return IG6
    return IG7


def classify_city_tier(city_name: str) -> int:
    """
    Classify an Indian city into Tier 1, 2, or 3.
    Returns:
        1 for Tier 1 cities
        2 for Tier 2 cities
        3 for all other cities (Tier 3)
    """
    name = city_name.strip().lower()
    if name in TIER1_CITIES:
        return 1
    if name in TIER2_CITIES:
        return 2
    return 3
