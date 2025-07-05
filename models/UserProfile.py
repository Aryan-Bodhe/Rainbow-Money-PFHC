from typing_extensions import Optional
from pydantic import BaseModel

from .PersonalData import PersonalData
from .IncomeData import IncomeData
from .ExpenseData import ExpenseData
from .AssetData import AssetData
from .LiabilityData import LiabilityData
from .InsuranceData import InsuranceData

# @dataclass
class UserProfile(BaseModel):
    personal_data: PersonalData
    income_data: IncomeData
    expense_data: ExpenseData
    asset_data: AssetData
    liability_data: LiabilityData
    insurance_data: InsuranceData
    
