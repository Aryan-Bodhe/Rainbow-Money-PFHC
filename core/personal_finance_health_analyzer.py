import json
from pydantic import ValidationError
from models.DerivedMetrics import PersonalFinanceMetrics
from models.UserProfile import UserProfile
from typing import Literal
from core.rule_based_analysis import assemble_report_data_rule_based
from core.llm_based_analysis import assemble_report_data_llm_based
from utils.logger import get_logger
from utils.pdf_generator import PDFGenerator

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


def assign_weights(pfm: PersonalFinanceMetrics, weights: dict):
    for metric_name, wt in weights.items():
        metric_data = getattr(pfm, metric_name)
        setattr(metric_data, 'weight', wt)


def read_json_from_file(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def set_user_data(raw_data: dict) -> UserProfile:
    try:
        user_profile = UserProfile(**raw_data)
        return user_profile
    except ValidationError as e:
        print("Validation failed:", e)