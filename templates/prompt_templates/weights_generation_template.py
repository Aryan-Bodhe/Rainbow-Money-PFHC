WEIGHT_GEN_SYS_MSG = """
You are a professional financial analyst with excellent personalization skills and a mathematically rigorous scoring engine.  
STRICTLY OUTPUT ONLY A JSON OBJECT—no markdown, no explanations, no private reasoning tokens, nothing else.
"""

WEIGHTS_GEN_USER_MSG = """
# DATA  
Here is the user's personal data (JSON):  
{personal_data}

## METRICS  
savings_income_ratio
investment_income_ratio
expense_income_ratio
debt_income_ratio
emergency_fund_ratio
liquidity_ratio
asset_liability_ratio
housing_income_ratio
health_insurance_adequacy
term_insurance_adequacy
net_worth_adequacy
retirement_adequacy

# TASK  
1. Assign each metric an integer “importance weight” ≥ 3. Tailor weights by the user's life stage (age, dependents).

# RESPONSE  
Return **only** a JSON object mapping metric names to integer weights, without the ```json tags, as for example:  

{{  
  "savings_income_ratio": 10,  
  "investment_income_ratio": 8,  
  …  
  "retirement_adequacy": 15  
}}

"""

DEFAULT_METRIC_WEIGHTS = {
    "savings_income_ratio": 10,
    "investment_income_ratio": 10,
    "expense_income_ratio": 10,
    "debt_income_ratio": 10,
    "emergency_fund_ratio": 8,
    "liquidity_ratio": 7,
    "asset_liability_ratio": 8,
    "housing_income_ratio": 7,
    "health_insurance_adequacy": 8,
    "term_insurance_adequacy": 7,
    "net_worth_adequacy": 7,
    "retirement_adequacy": 8,
}
