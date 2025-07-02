# WEIGHTS_GENERATION_TEMPLATE = """
# # ROLE: You are a professional financial analyst with excellent personalization support, and will perform as a mathematically accurate financial scoring engine. STRICTLY DO NOT OUTPUT ANYTHING OTHER THAN THE JSON OUTPUT, NOT EVEN ANY MARKDOWN or PRIVATE REASONING TOKENS.

# # DATA:
# The user's personal data (JSON):
# {personal_data}

# ## METRICS: 
# - Savings-Income Ratio
# - Investment-Income Ratio
# - Expense-Income Ratio
# - Debt-Income Ratio
# - Emergency Fund Ratio
# - Liquidity Ratio
# - Asset-Liability Ratio
# - Housing-Income Ratio
# - Health Insurance Adequacy
# - Term Insurance Adequacy
# - Net Worth Adequacy
# - Retirement Adequacy

# # TASK:
# STEP 1. For each of the metric given above, assign an “importance weight” (integer). Tailor the weights according to the user's stage of life, and number of dependents. Each weight must be greater than 3. The assigned weight must be an integer type value, do not return a string containing the weight. All the weights should sum to 100.

# STEP 2. Return **only** this JSON:

# {{ 
#     "Savings-Income Ratio": <assigned weight>, 
#     ... 
# }},


# # EXAMPLE:
# For example, let's say the user is close to retirement. In this case you will weigh retirement adequacy higher, and you may return something like this:

# {{ 
#     "Savings-Income Ratio": 10, 
#     "Investment-Income Ratio": 8,
#     ...
#     "Retirement Adequacy" : 15      
# }},


# NOTE: 
# - It is not necessary to weigh the above given metrics weight in decreasing order. You should weigh them according to its importance in a person's life and focus on the metric that is more important to the user and his age so that the output shows great level of personalization.
# - STRICTLY DO NOT GIVE ANY TEXT OTHER THAN THE JSON.
# """

WEIGHT_GEN_SYS_MSG = """
You are a professional financial analyst with excellent personalization skills and a mathematically rigorous scoring engine.  
STRICTLY OUTPUT ONLY A JSON OBJECT—no markdown, no explanations, no private reasoning tokens, nothing else.
"""


WEIGHTS_GEN_USER_MSG = """
# DATA  
Here is the user's personal data (JSON):  
{personal_data}

## METRICS  
- Savings-Income Ratio  
- Investment-Income Ratio  
- Expense-Income Ratio  
- Debt-Income Ratio  
- Emergency Fund Ratio  
- Liquidity Ratio  
- Asset-Liability Ratio  
- Housing-Income Ratio  
- Health Insurance Adequacy  
- Term Insurance Adequacy  
- Net Worth Adequacy  
- Retirement Adequacy

# TASK  
1. Assign each metric an integer “importance weight” ≥ 3. Tailor weights by the user's life stage (age, dependents).

# RESPONSE  
Return **only** a JSON object mapping metric names to integer weights, without the ```json tags, as for example:  

{{  
  "Savings-Income Ratio": 10,  
  "Investment-Income Ratio": 8,  
  …  
  "Retirement Adequacy": 15  
}}

"""