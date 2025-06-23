# from dataclasses import dataclass, field
from typing_extensions import Optional
from pydantic import BaseModel
# @dataclass
class PersonalFinanceMetrics(BaseModel):
    total_monthly_income: Optional[float] = 0
    total_monthly_expense: Optional[float] = 0
    total_monthly_investments: Optional[float] = 0
    total_monthly_emi: Optional[float] = 0
    total_assets: Optional[float] = 0
    total_liabilities: Optional[float] = 0

    savings_income_ratio: Optional[float] = 0
    investment_income_ratio: Optional[float] = 0
    expense_income_ratio: Optional[float] = 0
    debt_income_ratio: Optional[float] = 0
    emergency_fund_ratio: Optional[float] = 0
    liquidity_ratio: Optional[float] = 0
    asset_liability_ratio: Optional[float] = 0
    housing_income_ratio: Optional[float] = 0

    health_insurance_adequacy: Optional[float] = 0
    term_insurance_adequacy: Optional[float] = 0
    net_worth_adequacy: Optional[float] = 0
    retirement_adequacy: Optional[float] = 0
    
    asset_class_distribution: Optional[dict] = None
