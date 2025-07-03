from typing_extensions import Optional
from pydantic import BaseModel

class Metric(BaseModel):
    value: Optional[float] = None
    verdict: Optional[str] = None
    assigned_score: Optional[float] = None

class PersonalFinanceMetrics(BaseModel):
    # Need not be assessed separately
    city_tier: Optional[int] = None
    total_monthly_income: Optional[float] = 0
    total_monthly_expense: Optional[float] = 0
    total_monthly_investments: Optional[float] = 0
    total_monthly_emi: Optional[float] = 0
    total_assets: Optional[float] = 0
    total_liabilities: Optional[float] = 0
    asset_class_distribution: Optional[dict] = None

    # Assessment required
    savings_income_ratio: Optional[Metric] = 0
    investment_income_ratio: Optional[Metric] = 0
    expense_income_ratio: Optional[Metric] = 0
    debt_income_ratio: Optional[Metric] = 0
    emergency_fund_ratio: Optional[Metric] = 0
    liquidity_ratio: Optional[Metric] = 0
    asset_liability_ratio: Optional[Metric] = 0
    housing_income_ratio: Optional[Metric] = 0

    health_insurance_adequacy: Optional[Metric] = 0
    term_insurance_adequacy: Optional[Metric] = 0
    net_worth_adequacy: Optional[Metric] = 0
    target_retirement_corpus: Optional[Metric] = None
    retirement_adequacy: Optional[Metric] = 0
    
