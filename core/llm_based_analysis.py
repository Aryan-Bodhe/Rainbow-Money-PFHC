import asyncio
import json
from config.config import GLOSSARY_PATH
from core.personal_finance_metrics_calculator import PersonalFinanceMetricsCalculator as PFMC
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

from templates.prompt_templates.areas_for_improvement_generation_template import AREAS_FOR_IMPROVEMENT_SYS_MSG, AREAS_FOR_IMPROVEMENT_USER_MSG
from templates.prompt_templates.commendable_areas_generation_template import COMMENDABLE_AREAS_SYS_MSG, COMMENDABLE_AREAS_USER_MSG
from templates.prompt_templates.profile_review_generation_template import PROFILE_REVIEW_SYS_MSG, PROFILE_REVIEW_USER_MSG, PROFILE_REVIEW_FALLBACK_TEXT
from templates.prompt_templates.summary_generation_template import SUMMARY_GENERATION_SYS_MSG, SUMMARY_GENERATION_USER_MSG, SUMMARY_GENERATION_FALLBACK_TEXT
from templates.prompt_templates.weights_generation_template import DEFAULT_METRIC_WEIGHTS

logger = get_logger()

def assign_weights(pfm: PersonalFinanceMetrics, weights: dict[str, int]) -> PersonalFinanceMetrics:
    for metric_name, weight in weights.items():
        metric_obj = getattr(pfm, metric_name, None)
        if isinstance(metric_obj, Metric):
            metric_obj.weight = weight
    return pfm

def get_glossary_data(glossary_data_path: str = GLOSSARY_PATH):
    with open(glossary_data_path, 'r') as file:
        data = json.load(file)
    return data


async def assemble_report_data_llm_based(user_profile: UserProfile) -> ReportData:
    try:
        derived_metrics = PFMC().compute_personal_finance_metrics(user_profile) ###
        logger.info('Derived metrics computation complete.')
    except Exception as e:
        logger.critical("Derived metrics computation failed. Aborting.")
        logger.exception(e)
        raise CriticalInternalFailure()

    # llm_heavy = TogetherLLM(llm_model='DeepSeek_R1_Distilled', temperature=0.5)
    llm_heavy = OpenAILLM(llm_model='GPT-o4-Reasoning-Mini')
    llm_light = TogetherLLM(llm_model='LG_Exaone_3.5_Instruct', temperature=1)

    user_profile_str = user_profile.model_dump_json()
    personal_data_str = user_profile.personal_data.model_dump_json()
    derived_metrics_str = derived_metrics.model_dump_json()

    weight_data: LLMResponse = None
    review_data: LLMResponse = None
    comm_data: LLMResponse = None
    improv_data: LLMResponse = None

    results = await asyncio.gather(
        llm_light.generate_weights_using_llm(personal_data_str),
        llm_light.generate_report_part(
            system_msg=PROFILE_REVIEW_SYS_MSG,
            user_msg=PROFILE_REVIEW_USER_MSG,
            user_profile=user_profile_str,
            
        ),
        llm_heavy.generate_report_part(
            system_msg=COMMENDABLE_AREAS_SYS_MSG,
            user_msg=COMMENDABLE_AREAS_USER_MSG,
            personal_data=personal_data_str,
            derived_metrics=derived_metrics_str
        ),
        llm_heavy.generate_report_part(
            system_msg=AREAS_FOR_IMPROVEMENT_SYS_MSG,
            user_msg=AREAS_FOR_IMPROVEMENT_USER_MSG,
            personal_data=personal_data_str,
            derived_metrics=derived_metrics_str
        ),
        return_exceptions=True
    )

    weight_data, review_data, comm_data, improv_data = results

    if isinstance(comm_data, Exception) or isinstance(improv_data, Exception):
        logger.critical('Failed to get valid LLM response for commendable points or improvement_points. Aborting.')
        raise CriticalInternalFailure()

    if isinstance(weight_data, Exception):
        logger.warning('Failed to get valid LLM response for weights generation. Defaulting to fallback.')
        weight_data = LLMResponse(content=DEFAULT_METRIC_WEIGHTS, metadata=None)

    if isinstance(review_data, Exception):
        logger.warning('Failed to get valid LLM response for profile_review. Defaulting to fallback.')
        review_data = LLMResponse(content=PROFILE_REVIEW_FALLBACK_TEXT, metadata=None)

    try:
        weights = post_process_weights(weight_data.content)
        logger.info('Weights post processed.')
    except Exception as e:
        logger.warning('Failed to post-process weights. Defaulting to fallback.')
        weights = DEFAULT_METRIC_WEIGHTS

    profile_review = review_data.content

    try:
        comm_points = [
            CommendablePoint(**item)
            for item in comm_data.content.get("commendable_areas", [])
        ]
        improv_points = [
            ImprovementPoint(**item)
            for item in improv_data.content.get("areas_for_improvement", [])
        ]
    except Exception as e:
        logger.critical('Failed to unpack commendable points or improvement points from LLM response. Aborting.')
        logger.exception(e)
        raise CriticalInternalFailure()

    try:
        derived_metrics = assign_weights(derived_metrics, weights)
        logger.info('Weights assigned successfully.')
    except Exception as e:
        logger.critical('Failed to assign weights to metrics. Aborting.')
        logger.exception(e)
        raise CriticalInternalFailure()

    try:
        summary_data = await llm_light.generate_report_part(
            system_msg=SUMMARY_GENERATION_SYS_MSG,
            user_msg=SUMMARY_GENERATION_USER_MSG,
            profile_review=profile_review,
            commendable_areas=comm_points,
            areas_for_improvement=improv_points
        )
        logger.info('Received summary data from LLM successfully.')
    except Exception as e:
        logger.warning('Failed to get valid LLM response for summary generation. Defaulting to fallback.')
        summary_data = LLMResponse(content=SUMMARY_GENERATION_FALLBACK_TEXT, metadata=None)
    
    try:
        glossary = get_glossary_data()
        logger.info('Glossary data loaded.')
    except Exception as e:
        logger.warning('Failed to load glossary data.')
        glossary = None

    metrics_table = None
    try:
        metrics_table = FAE().get_metrics_scoring_table(derived_metrics)
        logger.info('Metrics table loaded.')
    except Exception as e:
        logger.warning('Failed to load Metrics Scoring Table.')
    
    report_data = ReportData(
        profile_review=profile_review.get('profile_review'),
        commendable_areas=comm_points,
        areas_for_improvement=improv_points,
        summary=summary_data.content.get('summary'),
        glossary=glossary,
        metrics_scoring_table=metrics_table
    )

    return report_data 