"""
LLM-backed report assembler for personal finance analysis.

This module wires together metric calculation, lightweight/heavy LLM calls, and
the financial analysis engine to produce a final `ReportData` object suitable
for API responses or downstream presentation layers.

Primary responsibilities
- Compute derived personal finance metrics from a `UserProfile`.
- Request metric weights, profile review, commendable areas, and areas-for-improvement
  from LLMs (uses both lightweight and heavy LLM clients in parallel).
- Post-process and assign weights, build model objects from LLM responses,
  generate a summary via LLM, and assemble the final `ReportData`.
- Load glossary data for inclusion in the report.

Errors & fallbacks
- If metrics computation or critical unpacking fails, raises `CriticalInternalFailure`.
- If LLM calls fail, uses sensible fallbacks for weights, profile review and summary,
  while logging warnings/errors.
- Network-level API errors from OpenAI are surfaced (e.g., `APIConnectionError`).

Dependencies
- `PFMC` (PersonalFinanceMetricsCalculator) to compute derived metrics.
- LLM wrappers: `OpenAILLM` and `TogetherLLM` for content generation.
- `FinancialAnalysisEngine` (FAE) for generating scoring table.
- Templates and default payloads for the LLM prompts in `templates.prompt_templates.*`.
- `GLOSSARY_PATH` location for glossary JSON.
"""
import asyncio
import json
from openai import APIConnectionError

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

from templates.prompt_templates.areas_for_improvement_generation_template import (
    AREAS_FOR_IMPROVEMENT_SYS_MSG,
    AREAS_FOR_IMPROVEMENT_USER_MSG,
)
from templates.prompt_templates.commendable_areas_generation_template import (
    COMMENDABLE_AREAS_SYS_MSG,
    COMMENDABLE_AREAS_USER_MSG,
)
from templates.prompt_templates.profile_review_generation_template import (
    PROFILE_REVIEW_SYS_MSG,
    PROFILE_REVIEW_USER_MSG,
    PROFILE_REVIEW_FALLBACK_TEXT,
)
from templates.prompt_templates.summary_generation_template import (
    SUMMARY_GENERATION_SYS_MSG,
    SUMMARY_GENERATION_USER_MSG,
    SUMMARY_GENERATION_FALLBACK_TEXT,
)
from templates.prompt_templates.weights_generation_template import DEFAULT_METRIC_WEIGHTS

logger = get_logger()


def assign_weights(pfm: PersonalFinanceMetrics, weights: dict[str, int]) -> PersonalFinanceMetrics:
    """
    Assign numeric weights to Metric objects contained in `pfm`.

    This function mutates the provided `pfm` by setting the `.weight` attribute
    on any `Metric` instances whose names appear in the `weights` mapping.

    Parameters
    ----------
    pfm : PersonalFinanceMetrics
        Container of metric attributes (each expected to be a `Metric` instance).
    weights : dict[str, int]
        Mapping of metric attribute name -> integer weight to assign.

    Returns
    -------
    PersonalFinanceMetrics
        The same `pfm` instance with updated `.weight` attributes where applicable.

    Notes
    -----
    - Metrics not present on `pfm` are ignored.
    - No validation of weight ranges is performed here; upstream callers should
      ensure the weights are sensible.
    """
    for metric_name, weight in weights.items():
        metric_obj = getattr(pfm, metric_name, None)
        if isinstance(metric_obj, Metric):
            metric_obj.weight = weight
    return pfm


def get_glossary_data(glossary_data_path: str = GLOSSARY_PATH):
    """
    Load glossary JSON from disk.

    Parameters
    ----------
    glossary_data_path : str, optional
        Filesystem path to the glossary JSON file. Defaults to `GLOSSARY_PATH`.

    Returns
    -------
    dict
        Parsed JSON content (dictionary) loaded from the file.

    Raises
    ------
    FileNotFoundError
        If the glossary file does not exist.
    json.JSONDecodeError
        If the file contains invalid JSON.

    Notes
    -----
    - Callers should handle exceptions; this function intentionally surfaces IO
      and parsing errors so the caller can decide on fallback behavior.
    """
    with open(glossary_data_path, "r") as file:
        data = json.load(file)
    return data


async def assemble_report_data_llm_based(user_profile: UserProfile) -> ReportData:
    """
    Assemble a `ReportData` object by combining computed metrics and LLM-generated content.

    Workflow
    --------
    1. Compute derived personal finance metrics from the `user_profile` via `PFMC`.
    2. Launch multiple LLM requests concurrently:
       - Metric weights (light LLM)
       - Profile review (light LLM)
       - Commendable areas (heavy LLM)
       - Areas for improvement (heavy LLM)
    3. Apply fallbacks if LLM responses fail or return exceptions.
    4. Post-process weights and assign them to metrics.
    5. Convert LLM responses into `CommendablePoint` and `ImprovementPoint` model lists.
    6. Request a short summary from an LLM using the generated parts.
    7. Load glossary and scoring table, and assemble final `ReportData`.

    Parameters
    ----------
    user_profile : UserProfile
        The user's profile data required to compute derived metrics and to
        contextualize LLM prompts.

    Returns
    -------
    ReportData
        Fully assembled report data including:
        - profile_review (str),
        - commendable_areas (list[CommendablePoint]),
        - areas_for_improvement (list[ImprovementPoint]),
        - summary (str),
        - glossary (dict or None),
        - metrics_scoring_table (list[dict] or None)

    Raises
    ------
    CriticalInternalFailure
        If computing derived metrics fails or if required unpacking of LLM responses
        into model objects fails.
    APIConnectionError
        If a low-level API connection/transport error is returned directly from an LLM
        call for critical sections (these are propagated to the caller).
    """
    try:
        derived_metrics = PFMC().compute_personal_finance_metrics(user_profile)
        logger.info("Derived metrics computation complete.")
    except Exception as e:
        logger.critical("Derived metrics computation failed. Aborting.")
        logger.exception(e)
        raise CriticalInternalFailure()

    # Choose LLM clients (lightweight for cheaper ops, heavy for textual quality)
    # llm_heavy = TogetherLLM(llm_model='DeepSeek_R1_Distilled', temperature=0.5)
    llm_heavy = OpenAILLM(llm_model="GPT-o4-Reasoning-Mini")
    llm_light = TogetherLLM(llm_model="LG_Exaone_3.5_Instruct", temperature=1)

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
            derived_metrics=derived_metrics_str,
        ),
        llm_heavy.generate_report_part(
            system_msg=AREAS_FOR_IMPROVEMENT_SYS_MSG,
            user_msg=AREAS_FOR_IMPROVEMENT_USER_MSG,
            personal_data=personal_data_str,
            derived_metrics=derived_metrics_str,
        ),
        return_exceptions=True,
    )

    weight_data, review_data, comm_data, improv_data = results
    logger.info(comm_data)
    logger.info(improv_data)

    # Surface transport-level API errors for critical content
    if isinstance(comm_data, APIConnectionError):
        raise comm_data

    if isinstance(improv_data, APIConnectionError):
        raise improv_data

    # If textual generation failed for content-critical parts, abort
    if isinstance(comm_data, Exception) or isinstance(improv_data, Exception):
        logger.critical(
            "Failed to get valid LLM response for commendable points or improvement_points. Aborting."
        )
        raise CriticalInternalFailure()

    # We can degrade gracefully for weights and profile review
    if isinstance(weight_data, Exception):
        logger.warning("Failed to get valid LLM response for weights generation. Defaulting to fallback.")
        weight_data = LLMResponse(content=DEFAULT_METRIC_WEIGHTS, metadata=None)

    if isinstance(review_data, Exception):
        logger.warning("Failed to get valid LLM response for profile_review. Defaulting to fallback.")
        review_data = LLMResponse(content=PROFILE_REVIEW_FALLBACK_TEXT, metadata=None)

    try:
        weights = post_process_weights(weight_data.content)
        logger.info("Weights post processed.")
    except Exception as e:
        logger.warning("Failed to post-process weights. Defaulting to fallback.")
        weights = DEFAULT_METRIC_WEIGHTS

    profile_review = review_data.content

    try:
        comm_points = [
            CommendablePoint(**item) for item in comm_data.content.get("commendable_areas", [])
        ]
        improv_points = [
            ImprovementPoint(**item) for item in improv_data.content.get("areas_for_improvement", [])
        ]
    except Exception as e:
        logger.critical("Failed to unpack commendable points or improvement points from LLM response. Aborting.")
        logger.exception(e)
        raise CriticalInternalFailure()

    try:
        derived_metrics = assign_weights(derived_metrics, weights)
        logger.info("Weights assigned successfully.")
    except Exception as e:
        logger.critical("Failed to assign weights to metrics. Aborting.")
        logger.exception(e)
        raise CriticalInternalFailure()

    try:
        summary_data = await llm_light.generate_report_part(
            system_msg=SUMMARY_GENERATION_SYS_MSG,
            user_msg=SUMMARY_GENERATION_USER_MSG,
            profile_review=profile_review,
            commendable_areas=comm_points,
            areas_for_improvement=improv_points,
        )
        logger.info("Received summary data from LLM successfully.")
    except Exception as e:
        logger.warning("Failed to get valid LLM response for summary generation. Defaulting to fallback.")
        summary_data = LLMResponse(content=SUMMARY_GENERATION_FALLBACK_TEXT, metadata=None)

    try:
        glossary = get_glossary_data()
        logger.info("Glossary data loaded.")
    except Exception as e:
        logger.warning("Failed to load glossary data.")
        glossary = None

    metrics_table = None
    try:
        metrics_table = FAE().get_metrics_scoring_table(derived_metrics)
        logger.info("Metrics table loaded.")
    except Exception as e:
        logger.warning("Failed to load Metrics Scoring Table.")

    report_data = ReportData(
        profile_review=profile_review.get("profile_review"),
        commendable_areas=comm_points,
        areas_for_improvement=improv_points,
        summary=summary_data.content.get("summary"),
        glossary=glossary,
        metrics_scoring_table=metrics_table,
    )

    return report_data
