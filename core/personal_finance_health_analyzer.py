from models.UserProfile import UserProfile
from typing import Literal
from core.rule_based_analysis import assemble_report_data_rule_based
from core.llm_based_analysis import assemble_report_data_llm_based
from utils.logger import get_logger


async def personal_finance_health_analyzer(
    user_profile: UserProfile,
    mode: Literal['basic', 'advanced']
):
    """
    Analyzes a user's personal finance health and generates a report.

    This function serves as the main entry point for financial health analysis.
    It supports two modes:
      - "basic": Uses a static, rule-based analysis approach.
      - "advanced": Uses an LLM-based approach for deeper insights.

    Args:
        user_profile (UserProfile): A fully populated user profile containing financial and personal data.
        mode (Literal['basic', 'advanced']): The analysis mode to run.
            - 'basic'    → Rule-based static analysis.
            - 'advanced' → LLM-powered dynamic analysis.

    Returns:
        ReportData: A structured report containing:
            - Profile review
            - Commendable points
            - Areas for improvement
            - Summary
            - Glossary (if available)
            - Metrics scoring table (if available)

    Raises:
        CriticalInternalFailure: If essential computation or LLM calls fail in advanced mode.
    """
    logger = get_logger()
    report_data = None

    if mode == 'advanced':
        logger.info('Running LLM based advanced analytics.')
        report_data = await assemble_report_data_llm_based(user_profile)
        logger.info('Received LLM based report data.')
    else:
        logger.info('Running rule based static analytics.')
        report_data = await assemble_report_data_rule_based(user_profile)
        logger.info('Received rule based report data.')

    return report_data
