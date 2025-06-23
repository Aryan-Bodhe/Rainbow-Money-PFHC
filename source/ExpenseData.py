# from dataclasses import dataclass
from pydantic import BaseModel

class ExpenseData(BaseModel):
    housing_cost: int
    utilities_and_bills: int
    groceries_and_essentials: int
    term_insurance_premium: int
    medical_insurance_premium: int
    discretionary_expense: int
