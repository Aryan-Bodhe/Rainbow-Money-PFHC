import asyncio
import json
from config.config import GLOSSARY_PATH
from core.personal_finance_metrics_calculator import PersonalFinanceMetricsCalculator
from models.DerivedMetrics import Metric, PersonalFinanceMetrics
from models.UserProfile import UserProfile
from models.ReportData import CommendablePoint, ImprovementPoint, ReportData
from apis.OpenAILLM import OpenAILLM
from apis.TogetherLLM import TogetherLLM
from utils.response_parsing import post_process_weights
from utils.logger import get_logger
from core.financial_analysis_engine import FinancialAnalysisEngine as FAE

from templates.prompt_templates.areas_for_improvement_generation_template import AREAS_FOR_IMPROVEMENT_SYS_MSG, AREAS_FOR_IMPROVEMENT_USER_MSG
from templates.prompt_templates.commendable_areas_generation_template import COMMENDABLE_AREAS_SYS_MSG, COMMENDABLE_AREAS_USER_MSG
from templates.prompt_templates.profile_review_generation_template import PROFILE_REVIEW_SYS_MSG, PROFILE_REVIEW_USER_MSG
from templates.prompt_templates.summary_generation_template import SUMMARY_GENERATION_SYS_MSG, SUMMARY_GENERATION_USER_MSG

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

async def assemble_report_data_llm_based(user_profile: UserProfile) -> ReportData:

    logger = get_logger()
    try:
        derived_metrics = PersonalFinanceMetricsCalculator().compute_personal_finance_metrics(user_profile)
        logger.info('Derived metrics computation complete.')
    except Exception as e:
        logger.exception(e)
        raise

    llm_heavy = TogetherLLM(llm_model='DeepSeek_R1_Distilled', temperature=0.5)
    llm_light = TogetherLLM(llm_model='LG_Exaone_3.5_Instruct', temperature=1)

    user_profile_str = user_profile.model_dump_json()
    personal_data_str = user_profile.personal_data.model_dump_json()
    derived_metrics_str = derived_metrics.model_dump_json()   

    try:
        weight_data, review_data, comm_data, improv_data = await asyncio.gather(
            llm_light.generate_weights_using_llm(personal_data_str),
            llm_heavy.generate_report_part(
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
            )
        )
        logger.info('Received weights, review, commendable areas, improvement areas from LLM successfully.')
    except Exception as e:
        logger.exception(e)
        raise

    try:
        weights = post_process_weights(weight_data.content)
        logger.info('Weights post processed.')
    except Exception as e:
        logger.exception(e)
        raise

    profile_review = review_data.content

    comm_points = [
        CommendablePoint(**item)
        for item in comm_data.content.get("commendable_areas", [])
    ]
    improv_points = [
        ImprovementPoint(**item)
        for item in improv_data.content.get("areas_for_improvement", [])
    ]

    try:
        derived_metrics = assign_weights(derived_metrics, weights)
        logger.info('Weights assigned successfully.')
    except Exception as e:
        logger.exception(e)
        raise

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
        logger.exception(e)
        raise
    
    summary = summary_data.content

    glossary = get_glossary_data()
    metrics_table = None
    try:
        metrics_table = FAE().get_metrics_scoring_table(derived_metrics)
        logger.info('Appended glossary data to report.')
    except Exception as e:
        logger.warning('Failed to generate Metrics Scoring Table.')
        # logger.exception(e)
    
    report_data = ReportData(
        profile_review=profile_review.get('profile_review'),
        commendable_areas=comm_points,
        areas_for_improvement=improv_points,
        summary=summary.get('summary'),
        glossary=glossary,
        metrics_scoring_table=metrics_table
    )

    return report_data 