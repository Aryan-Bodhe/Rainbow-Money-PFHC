from pydantic import BaseModel

class AssetData(BaseModel):
    equity_sip: int
    debt_sip: int
    retirement_sip: int
    total_savings_balance: int
    total_emergency_fund: int
    total_equity_investments: int
    total_debt_investments: int
    total_retirement_investments: int
    total_real_estate_investments: int
