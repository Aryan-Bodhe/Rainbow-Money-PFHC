from pydantic import BaseModel
from typing import Optional, Tuple

class BenchmarkData(BaseModel):
    savings_income_ratio: Optional[Tuple[float, float]] = None
    investment_income_ratio: Optional[Tuple[float, float]] = None
    expense_income_ratio: Optional[Tuple[float, float]] = None
    debt_income_ratio: Optional[Tuple[float, float]] = None
    housing_income_ratio: Optional[Tuple[float, float]] = None
    emergency_fund_ratio: Optional[Tuple[float, float]] = None
    liquidity_ratio: Optional[Tuple[float, float]] = None
    asset_liability_ratio: Optional[Tuple[float, float]] = None
    health_insurance_adequacy: Optional[Tuple[float, float]] = None
    term_insurance_adequacy: Optional[Tuple[float, float]] = None
    net_worth_adequacy: Optional[Tuple[float, float]] = None
    retirement_adequacy: Optional[Tuple[float, float]] = None
