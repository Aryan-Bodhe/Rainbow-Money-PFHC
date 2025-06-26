# from dataclasses import dataclass, field
from typing_extensions import Optional
from pydantic import BaseModel

from source.PersonalData import PersonalData
from source.IncomeData import IncomeData
from source.ExpenseData import ExpenseData
from source.AssetData import AssetData
from source.LiabilityData import LiabilityData
from source.InsuranceData import InsuranceData
from source.Metrics import PersonalFinanceMetrics

# @dataclass
class UserProfile(BaseModel):
    personal_data: PersonalData
    income_data: IncomeData
    expense_data: ExpenseData
    asset_data: AssetData
    liability_data: LiabilityData
    insurance_data: InsuranceData

    target_retirement_corpus: Optional[float] = None
    years_to_retirement: Optional[int] = None
    total_monthly_income: Optional[float] = 0
    total_monthly_expense: Optional[float] = 0
    total_monthly_investments: Optional[float] = 0
    total_monthly_emi: Optional[float] = 0
    total_assets: Optional[float] = 0
    total_liabilities: Optional[float] = 0
    
