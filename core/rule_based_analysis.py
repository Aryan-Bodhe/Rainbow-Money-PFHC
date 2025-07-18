import asyncio
import json
from functools import lru_cache

from config.config import GLOSSARY_PATH
from core.exceptions import CriticalInternalFailure
from core.metrics_calculator import PersonalFinanceMetricsCalculator as PFMC
from core.financial_analysis_engine import FinancialAnalysisEngine
from models.UserProfile import UserProfile
from models.DerivedMetrics import Metric, PersonalFinanceMetrics
from models.ReportData import ReportData
from apis.TogetherLLM import TogetherLLM
from apis.LLMResponse import LLMResponse
from templates.prompt_templates.profile_review_generation_template import (
    PROFILE_REVIEW_SYS_MSG,
    PROFILE_REVIEW_FALLBACK_TEXT,
    PROFILE_REVIEW_USER_MSG
)
from templates.prompt_templates.summary_generation_template import (
    SUMMARY_GENERATION_SYS_MSG,
    SUMMARY_GENERATION_FALLBACK_TEXT,
    SUMMARY_GENERATION_USER_MSG
)
from templates.prompt_templates.weights_generation_template import DEFAULT_METRIC_WEIGHTS
from utils.response_parsing import post_process_weights
from utils.logger import get_logger
from utils.response_parsing import parse_llm_output

logger = get_logger()

def assign_weights(pfm: PersonalFinanceMetrics, weights: dict[str, int]) -> PersonalFinanceMetrics:
    """
    Apply integer weights to each Metric in a PersonalFinanceMetrics object.

    Iterates through the provided weights dict, finds matching Metric
    attributes on the pfm object, and sets their .weight accordingly.

    Args:
        pfm:            Instance of PersonalFinanceMetrics to update.
        weights:        Mapping from metric_name to integer weight.

    Returns:
        The same pfm object with updated Metric.weight values.
    """
    for metric_name, weight in weights.items():
        metric_obj = getattr(pfm, metric_name, None)
        if isinstance(metric_obj, Metric):
            metric_obj.weight = weight
    return pfm


@lru_cache(maxsize=1)
def get_glossary_data(glossary_data_path: str = GLOSSARY_PATH):
    """
    Load and cache glossary JSON data from disk.

    This function is memoized to avoid repeated file reads on every request.
    The first call will read and parse the file; subsequent calls return
    the cached dict.

    Args:
        glossary_data_path: Path to the JSON glossary file.

    Returns:
        Parsed JSON as a Python dict.
    """
    with open(glossary_data_path, 'r') as file:
        data = json.load(file)
    return data


async def assemble_report_data_rule_based(user_profile: UserProfile) -> ReportData:
    """
    Orchestrates generation of a complete financial report for the given user profile.

    Steps:
      1. Compute derived metrics via rule-based calculator.
      2. Generate metric weights via LLM (with fallback to defaults).
      3. Post-process and assign weights to metrics.
      4. Run the FinancialAnalysisEngine to produce commendable & improvement points.
      5. Generate profile review and summary via LLM (parallel, with fallbacks).
      6. Append glossary data and return a ReportData object.

    Args:
        user_profile:  Pydantic UserProfile model containing all user inputs.

    Returns:
        A fully populated ReportData instance.

    Raises:
        CriticalInternalFailure: If any non-recoverable step fails.
    """

    # 1. Derived metrics
    try:
        derived_metrics = PFMC().compute_personal_finance_metrics(user_profile)
        logger.info('Derived metrics computation complete.')
    except Exception as e:
        logger.critical("Derived metrics computation failed. Aborting.")
        logger.exception(e)
        raise CriticalInternalFailure()

    llm = TogetherLLM(llm_model='LG_Exaone_3.5_Instruct', temperature=1)

    user_profile_str = user_profile.model_dump_json()
    personal_data_str = user_profile.personal_data.model_dump_json()



    # 2. Weight generation
    try:
        weights_gen_response = await llm.generate_weights_using_llm(personal_data_str, advanced=True)
        weights_raw = weights_gen_response.content
        logger.info('Received LLM response for weights generation.')
    except Exception as e:
        logger.warning('Failed to get valid LLM response for weights generation. Defaulting to fallback.')
        weights_raw = DEFAULT_METRIC_WEIGHTS
    


    # 3. Post-process & assign weights
    try:
        weights = post_process_weights(weights_raw)
    except Exception as e:
        logger.warning('Failed to post-process weights. Defaulting to fallback.')
        weights = DEFAULT_METRIC_WEIGHTS



    # 4. Financial analysis
    try:
        derived_metrics = assign_weights(derived_metrics, weights)
        logger.info('Weights assigned successfully.')
    except Exception as e:
        logger.critical('Failed to assign weights to metrics. Aborting.')
        logger.exception(e)
        raise CriticalInternalFailure()



    # 5. LLM-based review & summary (in parallel)
    try:
        report_data = FinancialAnalysisEngine().analyse(user_profile, derived_metrics)
        logger.info('Financial Analysis Successful.')
    except Exception as e:
        logger.critical('Financial Analysis Engine failed. Aborting.')
        logger.exception(e)
        raise CriticalInternalFailure()

    review_data: LLMResponse = None
    summary_data: LLMResponse = None

    results = await asyncio.gather(
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
        ),
        return_exceptions=True
    )

    # Unpack results
    review_data, summary_data = results

    # Handle review result
    if isinstance(review_data, Exception):
        logger.warning('Failed to get valid LLM response for profile_review. Defaulting to fallback.')
        logger.exception(review_data)
        review_data = LLMResponse(content=PROFILE_REVIEW_FALLBACK_TEXT, metadata=None)


    # Handle summary result
    if isinstance(summary_data, Exception):
        logger.warning('Failed to get valid LLM response for summary generation. Defaulting to fallback.')
        logger.exception(summary_data)
        summary_data = LLMResponse(content=SUMMARY_GENERATION_FALLBACK_TEXT, metadata=None)


    report_data.profile_review = review_data.content.get('profile_review')
    report_data.summary = summary_data.content.get('summary')


    # 6. Append cached glossary and return
    report_data.glossary = get_glossary_data()
    logger.info('Appended glossary data to report.')

    return report_data
