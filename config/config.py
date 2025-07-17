LLM_TEMP = 0.1
ENABLE_TESTING = True
GENERATE_REPORT = False
RETRY_ATTEMPT_LIMIT = 3

PROFILE_1_PATH = 'data/sample_user_profile1.json'
PROFILE_2_PATH = 'data/sample_user_profile2.json'
PROFILE_3_PATH = 'data/sample_user_profile3.json'

VERY_POOR_PROFILE = 'data/test_data/very_poor_profile.json'
POOR_PROFILE = 'data/test_data/poor_profile.json'
AVERAGE_PROFILE = 'data/test_data/average_profile.json'
GOOD_PROFILE = 'data/test_data/good_profile.json'
VERY_GOOD_PROFILE = 'data/test_data/very_good_profile.json'

USER_PROFILE_DATA_PATH = VERY_POOR_PROFILE
METRICS_OUTPUT_PATH = 'temp/output_metrics.json'
REPORT_PATH = 'temp/personal_finance_health_report.pdf'
REPORT_STYLESHEET = 'templates/pdf_templates/pdf_formatting.css'
LLM_OUTPUT_PATH = 'temp/llm_output.md'
REPORT_TEMPLATE_NAME = 'report_template.j2'
REPORT_TEMPLATE_DIR = 'templates/pdf_templates/'
GLOSSARY_PATH = 'assets/glossary.json'
LOGGING_DIR = 'logs/'
LOGGING_LIMIT_DAYS = 1

ANNUAL_INFLATION_RATE = 0.05
RETIREMENT_CORPUS_GROWTH_RATE = 0.08
AVG_LIFE_EXPECTANCY = 75
RETIREMENT_EXPENSE_REDUCTION_RATE = 0
MEDICAL_COVER_FACTOR = 500000
TERM_COVER_FACTOR = 10

SCORING_BASE_VALUE = 0.1