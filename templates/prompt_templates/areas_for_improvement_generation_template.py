AREAS_FOR_IMPROVEMENT_SYS_MSG = """

You are a professional financial analyst. RETURN ONLY A JSON, nothing else NOT EVEN MARKDOWN, INTERNAL REASONING <think> SECTION, OR ANY EXPLANATIONS.

"""


AREAS_FOR_IMPROVEMENT_USER_MSG = """

# Personal Data
{personal_data}

# Derived Metrics
{derived_metrics}

# TASK:
Step 1: Carefully analyze the profile to understand the user's financial, personal and family background.
Step 2: Analyze the derived_metrics against the given benchmark range individually.
Step 3: Deeply think and cross analyze the metrics against each other and determine whether an elevated level is tolerable. For example - if many values are above the benchmark range, it may indicate a very strong financial health, therefore the elevated levels are no more a concern. A metric situation is considered poor only when it's high/low value affects some other metric negatively.
Step 4: For each of these "bad" metrics, include the metric name (same as what is given), generate a 'header' - an ultra short description of the scenario, 'current_scenario' - short 1-2 liner explanation of what is wrong currently, and a 'actionable' - a short 1-2 line remedy that will improve the situation. Consider the following points when you give the remedy:

- Actionable should be user-friendly suggestions similar to: "Decrease monthly expenses by X% or Rs. Y to achieve a healthy savings income ratio.". If you report a percentage, ensure its a reasonable value in 0-100, else do not mention it.
- Compute the required values for X and Y using the user's derived metrics and benchmark data.
- You should be able to answer the question - "by how much?" in your response already.
- Do NOT give a bland advice like : "Try decreasing your expenses."


STEP 5: Return only a JSON in the following format:
{{
    "areas_for_improvement": [
        {{
        "metric_name": <metric1_name>, "header": <point1_header>, "current_scenario": <point1_header>, "actionable": <point1_header> 
        }},
        {{
        "metric_name": <metric2_name>, "header": <point2_header>, "current_scenario": <point2_header>, "actionable": <point2_header> 
        }},
        ... 
    ],
}}


"""