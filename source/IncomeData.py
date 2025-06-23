# from dataclasses import dataclass
from pydantic import BaseModel
# @dataclass
class IncomeData(BaseModel):
    salaried_income: int
    business_income: int
    freelance_income: int
    investment_returns: int
    rental_income: int
