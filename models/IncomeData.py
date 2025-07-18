from pydantic import BaseModel

class IncomeData(BaseModel):
    salaried_income: int
    business_income: int
    freelance_income: int
    other_sources: int
    rental_income: int
