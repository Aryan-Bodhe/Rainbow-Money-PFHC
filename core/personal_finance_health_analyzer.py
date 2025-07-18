from models.UserProfile import UserProfile
from typing import Literal
from core.rule_based_analysis import assemble_report_data_rule_based
from core.llm_based_analysis import assemble_report_data_llm_based
from utils.logger import get_logger

async def personal_finance_health_analyzer(user_profile: UserProfile, mode: Literal['basic', 'advanced']):
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