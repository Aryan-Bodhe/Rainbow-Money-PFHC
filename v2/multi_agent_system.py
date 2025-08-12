# ---------------------------------------------------------------- #

DATA_ANALYST = """
You are a detail-oriented financial data analyst. Your job is to extract and interpret key financial metrics from a client's profile. Focus purely on numbers, ratios, and facts. Avoid opinions or advice.
Output a structured list of metrics and their interpretations. Use INR and indian numbering system.
"""

RISK_AUDITOR = """
You are a conservative financial risk auditor. Your role is to identify vulnerabilities, blind spots, and risky dependencies in a user's financial situation. Assume the user might have overlooked risks.
Base your analysis entirely on the previous analyst’s metrics. Challenge assumptions and highlight risks clearly.
Always quantify your analysis by stating the numbers/ratios/external standard data you use. Aim for an accurate numbers-heavy statistical response. Use INR and indian numbering system.
"""

FINANCIAL_STRATEGIST = """
You are a senior financial planner. Use the user's financial metrics and identified risks to propose strategic financial actions. Your recommendations should be realistic, balanced, and tailored. Prioritize the most important 3–5 actions. Use short titles and supporting justifications.
Always quantify your analysis by stating the numbers/ratios/external standard data you use. Aim for an accurate numbers-heavy statistical response. Use INR and indian numbering system.
"""

COMMUNICATOR = """
You are a warm, engaging financial communicator. Use inputs from a data analyst, risk auditor, and financial strategist to generate a user-facing narrative review of the person’s financial profile. The tone should be clear, respectful, and encouraging—like a real human advisor would talk.
Always quantify your analysis by stating the numbers/ratios/external standard data, etc you use. Aim for an accurate numbers-heavy statistical response. Use INR and indian numbering system.
"""

PRODUCT_RECOMMENDER = """
You are a financial product recommender for Indian users. Based on the provided financial profile, suggest relevant financial products that can improve the user's financial health, ensure better protection, or optimize investments.

Only recommend products that are suitable for the user’s age, income, and risk profile. For each recommendation, give:
- Product Type (e.g., Term Insurance, PPF, Equity Mutual Fund)
- Why it's relevant
- Expected benefits
- Any caveats or prerequisites

Only name if the product is top-tier and well-trusted in indian market or dont name. Always quantify your analysis by stating the numbers/ratios/external standard data, etc you use. Aim for an accurate numbers-heavy statistical response. Use INR and indian numbering system.
"""

SCENARIO_SIMULATOR = """
You are a scenario simulator for personal finance planning. Given a user's financial summary and assumptions about a hypothetical future event, explain the likely financial consequences and suggest actions to mitigate risks.

Simulate the impact of the given scenario, and explain:
- How key financial metrics will change (savings, investments, liabilities)
- Whether the user is resilient to this scenario
- Suggested adjustments to stay secure

Always quantify your analysis by stating the numbers/ratios/external standard data, etc you use. Aim for an accurate numbers-heavy statistical response. Use INR and indian numbering system.
"""

BEHAVIOURAL_COACH = """
You are a behavioral finance coach. Based on the user's financial behavior and profile, offer gentle, constructive suggestions to help them develop better money habits.

Focus on:
- Spending discipline
- Building consistent saving/investing habits
- Tackling procrastination or emotional spending
- Encouraging financial mindfulness

Avoid technical jargon. Be empathetic and personalized. Always quantify your analysis by stating the numbers/ratios/external standard data, etc you use. Aim for an accurate numbers-heavy statistical response. Use INR and indian numbering system.
"""

# ---------------------------------------------------------------- #

PLANNER = """
You are a smart task planner for a financial review agentic-ai system. 
Given a user's profile summary, decide which specialist agents to invoke:

Agents available:
- Data Analyst
- Risk Auditor
- Financial Strategist
- Communicator
- Product Recommender
- Scenario Simulator
- Behavioral Coach

Only include agents relevant to the current profile in order of execution. First agent should be Data analyst and last agent must be Communicator. Return a python list, with a short justification string post it to explain why each of these agents were selected in that order. NO MARKDOWN or any other text. Limit to maximum of 5 agents only.

"""

import asyncio
import json
import re
from typing import Literal
from openai import OpenAI
import os

from config.config import GLOSSARY_PATH
from core.metrics_calculator import PersonalFinanceMetricsCalculator as PFMC
from core.exceptions import CriticalInternalFailure
from models.DerivedMetrics import Metric, PersonalFinanceMetrics
from models.UserProfile import UserProfile
from models.ReportData import CommendablePoint, ImprovementPoint, ReportData
from apis.OpenAILLM import OpenAILLM
from apis.TogetherLLM import TogetherLLM
from apis.LLMResponse import LLMResponse
from utils.response_parsing import post_process_weights
from utils.logger import get_logger
from core.financial_analysis_engine import FinancialAnalysisEngine as FAE

logger = get_logger()

client = OpenAI(
    api_key=os.getenv('TOGETHER_API_KEY'),
    base_url='https://api.together.xyz/v1'
)


from markdown import markdown
from weasyprint import HTML
from config.config import REPORT_STYLESHEET

def markdown_to_pdf(
    markdown_str: str,
    step: int,
    css_path: str = REPORT_STYLESHEET
):
    """
    Convert a Markdown string to PDF.
    """
    html = f"""
        <html>
        <head>
        <meta charset="utf-8">
        </head>
        <body>
        {markdown(markdown_str, extensions=["fenced_code", "tables"])}
        </body>
        </html>
    """
    output_pdf = f'step_{step}.pdf'
    if css_path:
        HTML(string=html).write_pdf(output_pdf, stylesheets=[css_path])
    else:
        HTML(string=html).write_pdf(output_pdf)


async def get_model_response(
    llm_model: Literal['DeepSeek_R1_Distilled', 'Llama_3.3_Instruct_Turbo', 'LG_Exaone_3.5_Instruct'],
    system_msg: str,
    user_msg: str,
):
    model_map = {
        'DeepSeek_R1_Distilled': 'deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free',
        'Llama_3.3_Instruct_Turbo': 'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free',
        'LG_Exaone_3.5_Instruct': 'lgai/exaone-3-5-32b-instruct'
    }
    temperature = 1
    model = model_map[llm_model]
    
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        temperature=temperature,
        timeout=100
    )

    return response.choices[0].message.content


async def solve():
    user_data = None

    with open('data/test_data/average_profile.json') as f:
        user_data = json.load(f)
        user_profile = UserProfile(**user_data.get('data'))

    try:
        derived_metrics = PFMC().compute_personal_finance_metrics(user_profile) ###
        logger.info('Derived metrics computation complete.')
    except Exception as e:
        logger.critical("Derived metrics computation failed. Aborting.")
        logger.exception(e)
        raise CriticalInternalFailure()

    # llm_heavy = TogetherLLM(llm_model='DeepSeek_R1_Distilled', temperature=0.5)
    # llm_heavy = OpenAILLM(llm_model='GPT-o4-Reasoning-Mini')
    # llm_light = TogetherLLM(llm_model='LG_Exaone_3.5_Instruct', temperature=3)

    derived_metrics_str = derived_metrics.model_dump_json()

    logger.info('First LLM call.')
    output1 = await get_model_response('LG_Exaone_3.5_Instruct', DATA_ANALYST, derived_metrics_str)
    resp1 = output1
    # print(resp1)
    with open('o1.txt', 'w') as f:
        f.write(resp1)
    if resp1 is None:
        exit()

    logger.info('Second LLM call.')
    output2 = await get_model_response('LG_Exaone_3.5_Instruct', RISK_AUDITOR, resp1)
    resp2 = output2
    # print(resp2)
    with open('o2.txt', 'w') as f:
        f.write(resp2)
    if resp2 is None:
        exit()

    logger.info('Third LLM call.')
    output3 = await get_model_response('LG_Exaone_3.5_Instruct', FINANCIAL_STRATEGIST, resp2)
    resp3 = output3
    # print(resp3)
    with open('o3.txt', 'w') as f:
        f.write(resp3)
    if resp3 is None:
        exit()
    
    logger.info('Fourth LLM call.')
    output4 = await get_model_response('LG_Exaone_3.5_Instruct', COMMUNICATOR, resp3)
    resp4 = output4
    if resp4 is None:
        exit()
    with open('o4.txt', 'w') as f:
        f.write(resp4)
    # print(resp4)
    logger.info('Complete.')

mapping = {
    'Data Analyst' : DATA_ANALYST,
    'Risk Auditor' : RISK_AUDITOR,
    'Financial Strategist' : FINANCIAL_STRATEGIST,
    'Communicator' : COMMUNICATOR,
    'Product Recommender' : PRODUCT_RECOMMENDER,
    'Scenario Simulator' : SCENARIO_SIMULATOR,
    'Behavioral Coach' : BEHAVIOURAL_COACH
}

async def solve2():
    user_data = None

    with open('data/test_data/average_profile.json') as f:
        user_data = json.load(f)
        user_profile = UserProfile(**user_data.get('data'))

    try:
        derived_metrics = PFMC().compute_personal_finance_metrics(user_profile) ###
        logger.info('Derived metrics computation complete.')
    except Exception as e:
        logger.critical("Derived metrics computation failed. Aborting.")
        logger.exception(e)
        raise CriticalInternalFailure()
    
    derived_metrics_str = derived_metrics.model_dump_json()


    agents_to_invoke_resp = await get_model_response(llm_model='LG_Exaone_3.5_Instruct', system_msg=PLANNER, user_msg=derived_metrics_str)
    with open('step_0.txt', 'w') as f:
        f.write(agents_to_invoke_resp)

    import ast
    match = re.search(r"\[.*?\]", agents_to_invoke_resp)
    agents_to_invoke = ast.literal_eval(match.group())
    logger.info(agents_to_invoke)

    if not isinstance(agents_to_invoke, list):
        logger.error('Agents list type error')
        logger.error(agents_to_invoke)
        exit()

    prev_output = derived_metrics_str
    step = 1
    for agent in agents_to_invoke:
        if step > 5:
            logger.error('Too many unpaid agents working.')
            exit()
        AG = mapping.get(agent)
        output = await get_model_response('LG_Exaone_3.5_Instruct', system_msg=AG, user_msg=prev_output)
        try:
            markdown_to_pdf(output, step)
            logger.info(f'PDF generated for step {step}.')
        except Exception as e:
            logger.warning(f'Step {step} pdf generation failed.')
            logger.exception(e)
        finally:
            with open(f'step_{step}.txt', 'w') as f:
                f.write(output)
        prev_output = output
        logger.info(f'Step {step} completed with agent {agent}')
        step += 1




if __name__ == '__main__':
    asyncio.run(solve2())

# Current 
