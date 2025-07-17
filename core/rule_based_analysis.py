import asyncio
import json

from config.config import GLOSSARY_PATH
from core.personal_finance_metrics_calculator import PersonalFinanceMetricsCalculator as PFMC
from core.financial_analysis_engine import FinancialAnalysisEngine
from models.UserProfile import UserProfile
from models.DerivedMetrics import Metric, PersonalFinanceMetrics
from apis.TogetherLLM import TogetherLLM
from templates.prompt_templates.profile_review_generation_template import PROFILE_REVIEW_SYS_MSG, PROFILE_REVIEW_USER_MSG
from templates.prompt_templates.summary_generation_template import SUMMARY_GENERATION_SYS_MSG, SUMMARY_GENERATION_USER_MSG
from utils.response_parsing import post_process_weights
from utils.logger import get_logger

def assign_weights(pfm: PersonalFinanceMetrics, weights: dict[str, int]) -> PersonalFinanceMetrics:
    for metric_name, weight in weights.items():
        metric_obj = getattr(pfm, metric_name, None)
        if isinstance(metric_obj, Metric):
            metric_obj.weight = weight
    return pfm

def get_glossary_data(glossary_data_path: str = GLOSSARY_PATH):
    try:
        with open(glossary_data_path, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(e)
        raise

async def assemble_report_data_rule_based(user_profile: UserProfile):
    logger = get_logger()

    try:
        derived_metrics = PFMC().compute_personal_finance_metrics(user_profile)
        logger.info('Derived metrics computation complete.')
    except Exception as e:
        logger.exception(e)
        raise

    llm = TogetherLLM(llm_model='LG_Exaone_3.5_Instruct', temperature=1)

    user_profile_str = user_profile.model_dump_json()
    personal_data_str = user_profile.personal_data.model_dump_json()

    try:
        weights_gen_response = await llm.generate_weights_using_llm(personal_data_str, advanced=True)
        logger.info('Received weights from LLM successfully.')
    except Exception as e:
        logger.exception(e)
        raise
    
    try:
        weights = post_process_weights(weights_gen_response.content)
    except Exception as e:
        logger.exception(e)
        raise

    weights_gen_metadata = weights_gen_response.metadata

    try:
        derived_metrics = assign_weights(derived_metrics, weights)
        logger.info('Weights assigned successfully.')
    except Exception as e:
        logger.exception(e)
        raise

    try:
        report_data = FinancialAnalysisEngine().analyse(user_profile, derived_metrics)
        logger.info('Financial Analysis Successful.')
    except Exception as e:
        logger.exception(e)
        raise

    try:
        review_data, summary_data = await asyncio.gather(
            llm.generate_report_part(
                PROFILE_REVIEW_SYS_MSG, 
                PROFILE_REVIEW_USER_MSG, 
                advanced=False,
                user_profile=user_profile_str
            ),
            llm.generate_report_part(
                SUMMARY_GENERATION_SYS_MSG, 
                SUMMARY_GENERATION_USER_MSG,
                advanced=False,
                profile_review='',
                commendable_areas=json.dumps([area.model_dump() for area in report_data.commendable_areas]),
                areas_for_improvement=json.dumps([area.model_dump() for area in report_data.areas_for_improvement]),
            )   
        )
        logger.info('Received review, summary from LLM successfully.')
    except Exception as e:
        logger.exception(e)
        raise

    report_data.profile_review = review_data.content.get('profile_review')
    report_data.summary = summary_data.content.get('summary')
    report_data.glossary = get_glossary_data()
    logger.info('Appended glossary data to report.')

    return report_data
