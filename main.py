import os
import json
from pydantic import ValidationError
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from source.FinanceAnalyzer import PersonalFinanceMetricsCalculator
from source.UserProfile import UserProfile
from apis.OpenRouterLLM import OpenRouterLLM
from apis.PDFGenerator import PDFGenerator
from config import METRICS_OUTPUT_PATH, ENABLE_TESTING, USER_PROFILE_DATA_PATH


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


def runtest():
    os.system('clear')
    print('Personal Finance Health Calculator is online.')
    try:
        raw_data = read_json_from_file(USER_PROFILE_DATA_PATH)
    except Exception as e:
        print(e)
        exit(0)

    print('Setting User Data')
    user_profile = set_user_data(raw_data)

    print('Computing Financial Metrics')
    calc = PersonalFinanceMetricsCalculator()
    user_derived_metrics = calc.analyze_user_profile(user_profile)

    # print(f'\nUser Derived Metrics:')
    # print(user_derived_metrics)

    user_profile_json = user_profile.model_dump_json(indent=2)
    user_derived_metrics_json = user_derived_metrics.model_dump_json(indent=2)

    print(f'Saving Computed Metrics to dumpfile. Location: {METRICS_OUTPUT_PATH}')
    with open(METRICS_OUTPUT_PATH, 'w') as f:
        f.write(user_derived_metrics_json)


    # ___________________________________________________________ #

    print('\n Analyzing User Profile using AI support.')

    llm = OpenRouterLLM(llm_model='DeepSeek_R1', temperature=0.2)
    stream = llm.get_model_response(user_profile_json, user_derived_metrics_json, streaming=True, enable_testing=ENABLE_TESTING)
    console = Console()
    buffer = ""
    perf_data = None

    print('---------------------------------------------------------')
    # Use Live to continuously update the rendered Markdown
    with Live(console=console, refresh_per_second=10) as live:
        for piece in stream:
            if isinstance(piece, str):
                buffer += piece
                # Update the live display with the latest Markdown buffer
                live.update(Markdown(buffer))
            elif isinstance(piece, dict) and "_perf" in piece:
                perf_data = piece["_perf"]

            
    # If you enabled testing, final piece is perf-data dict
    if ENABLE_TESTING and perf_data:
        console.print("\n[bold yellow]LLM Performance Data:[/]")
        console.print_json(data=json.dumps(perf_data), indent=2)


    print('Generating Report PDF.')
    pdf_gen = PDFGenerator()
    pdf_gen.markdown_to_pdf(input_md_str=buffer)
    print('Analysis Complete.')


if __name__ == "__main__":
    runtest()