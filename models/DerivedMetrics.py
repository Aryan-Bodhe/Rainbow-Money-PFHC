from typing_extensions import Optional
from pydantic import BaseModel

class Metric(BaseModel):
    metric_name: Optional[str] = None
    value: Optional[float] = None
    verdict: Optional[str] = None
    weight: Optional[float] = None
    assigned_score: Optional[float] = None

class PersonalFinanceMetrics(BaseModel):
    # Need not be assessed separately
    city_tier: Optional[int] = None
    total_monthly_income: Optional[float] = None
    total_monthly_expense: Optional[float] = None
    total_monthly_investments: Optional[float] = None
    total_monthly_emi: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    target_retirement_corpus: Optional[float] = None
    asset_class_distribution: Optional[dict] = None

    # Assessment required
    savings_income_ratio: Optional[Metric] = None
    investment_income_ratio: Optional[Metric] = None
    expense_income_ratio: Optional[Metric] = None
    debt_income_ratio: Optional[Metric] = None
    emergency_fund_ratio: Optional[Metric] = None
    liquidity_ratio: Optional[Metric] = None
    asset_liability_ratio: Optional[Metric] = None
    housing_income_ratio: Optional[Metric] = None

    health_insurance_adequacy: Optional[Metric] = None
    term_insurance_adequacy: Optional[Metric] = None
    net_worth_adequacy: Optional[Metric] = None
    retirement_adequacy: Optional[Metric] = None
    
