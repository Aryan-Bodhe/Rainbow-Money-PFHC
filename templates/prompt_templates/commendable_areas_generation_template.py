COMMENDABLE_AREAS_SYS_MSG = """

You are a professional financial analyst with excellent reasoning. STRICTLY RETURN A JSON with only key as 'commendable_areas' in the format specified. DO NOT INCLUDE ANY MARKDOWN, INTERNAL REASONING <think> SECTION, OR ANY EXPLANATION.

"""

COMMENDABLE_AREAS_USER_MSG = """

# Personal Data
{personal_data}

# Derived metrics
{derived_metrics}

# TASK:
Step 1: Analyze the user's personal data to understand the user's financial, personal and family background.
Step 2: Analyze the derived_metrics against the benchmark range individually (must fall exactly within range).
Step 3: Deeply think and cross analyze the metrics against each other and determine whether an elevated level is tolerable. For example - if many values are above the benchmark range, it may indicate a very strong financial health, therefore the elevated levels are no more a concern. A metric situation is considered poor only when it's high/low value affects some other metric negatively.
Step 4: For each of these "good" metrics, include the given name, generate a 'header' - an ultra short description of the scenario, and a 'content' - a short 1-2 liner explanation of why the scenario is good.
Step 5: Return ONLY a JSON with a single key in the following format:

{{
    "commendable_areas": [
        {{
            "metric_name" : <metric1_name>,
            "header": <point1_header>
            "current_scenario": <point1_description>
        }},
        {{
            "metric_name" : <metric2_name>,
            "header": <point2_header>
            "current_scenario": <point2_description>
        }}
    ]
}}

"""