import os
import json
from pydantic import ValidationError
from rich.console import Console
import asyncio
import time

from models.UserProfile import UserProfile
from apis.llm_clients.OpenRouterLLM import OpenRouterLLM
from apis.llm_clients.TogetherLLM import TogetherLLM
from core.personal_finance_metrics_calculator import PersonalFinanceMetricsCalculator
from utils.pdf_generator import PDFGenerator
from config.config import ENABLE_TESTING, USER_PROFILE_DATA_PATH, REPORT_TEMPLATE_NAME
from core.benchmarking import get_benchmarks
from core.scoring_system import score_metrics
from utils.response_parsing import post_process_weights
from utils.data_validation import validate_report_response, is_valid_json


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


async def runTest():

    timeStart = time.perf_counter()
    os.system('clear')
    console = Console()

    print('--> Personal Finance Health Calculator.')
    try:
        raw_data = read_json_from_file(USER_PROFILE_DATA_PATH)
    except Exception as e:
        console.print(f"[red]Error reading user data:[/] {e}")
        return

    print('--> Setting User Data')
    user_profile = set_user_data(raw_data)

    print('--> Computing Financial Metrics')
    calc = PersonalFinanceMetricsCalculator()
    derived_metrics = calc.analyze_user_profile(user_profile)

    personal_data_json = user_profile.personal_data.model_dump_json(indent=2)
    derived_metrics_json = derived_metrics.model_dump_json(indent=2)

    benchmark_data = get_benchmarks(derived_metrics)

    print('----------------------------------------')

    print('\n--> Analyzing User Profile using LLMs.')

    llm_1 = TogetherLLM(llm_model='DeepSeek_R1_Distilled', temperature=0.5)
    # llm_1 = OpenRouterLLM(llm_model='DeepSeek_R1', temperature=1)
    llm_2 = TogetherLLM(llm_model='DeepSeek_R1_Distilled', temperature=1)
    # llm_2 = OpenRouterLLM(llm_model='Mistral_7B', temperature=0.5)


    # report_data = await llm_tg.generate_report_using_llm(personal_data_json, derived_metrics_json, json.dumps(benchmark_data))
    # console.print('[green]--> Received report data.[/]')
    # weight_data = await llm_tg.generate_weights_using_llm(personal_data_json)
    # console.print('[green]--> Received weight data.[/]')

    report_data, weight_data = await asyncio.gather(
        llm_1.generate_report_using_llm(personal_data_json, derived_metrics_json, json.dumps(benchmark_data)),
        llm_2.generate_weights_using_llm(personal_data_json),
    )
    
    report_data_content = report_data['response']
    report_gen_perf_data = report_data['perf_data']
    weight_data_content = post_process_weights(weight_data['response'])
    weight_gen_perf_data = weight_data['perf_data']

    # console.print_json(data=json.dumps(report_data_content), indent=2)
    # console.print_json(data=json.dumps(weight_data_content), indent=2)

    scores = score_metrics(derived_metrics, weight_data_content)

    valid, err = validate_report_response(report_data_content)

    if not valid:
        console.print('[red]Report Data validation failed. Aborting.[/]')
        print(err)
        if is_valid_json(report_data_content):
            console.print_json(report_data_content)
        else:
            console.print(report_data_content)
        return

    pdf_generator = PDFGenerator()
    analyzed_metrics_table = pdf_generator.get_metrics_summary_table_dict(
        derived_metrics.model_dump(), 
        weight_data_content, 
        benchmark_data,
        scores
    )
    context_data = pdf_generator.generate_context_data(report_data_content, analyzed_metrics_table)
    # console.print_json(data=context_data, indent=2)
    pdf_generator.j2_template_to_pdf(REPORT_TEMPLATE_NAME, context_data)


    # console.print("[bold green]Final weights:[/]")
    # console.print_json(data=weights['output'], indent=2)

    console.print("\n<--- [bold green] Report Generation Successful.[/] --->")
    print('-----------------------------------------------------------')

    if ENABLE_TESTING:
        console.print("\n[bold yellow]Weights Allocation LLM Performance Data:[/]")
        console.print_json(data=weight_gen_perf_data, indent=2)
        console.print("\n[bold yellow]Report Generation LLM Performance Data:[/]")
        console.print_json(data=report_gen_perf_data, indent=2)
    timeEnd = time.perf_counter()

    total_ex_time = round(timeEnd-timeStart, 2)
    if int(total_ex_time / 60) == 0:
        console.print(f"\n[bold green]Total Execution Runtime: {total_ex_time:0.2f} secs.")
    else:
        console.print(f"\n[bold green]Total Execution Runtime: {int(total_ex_time / 60)} min {total_ex_time % 60} secs.")

    print('-----------------------------------------------------------')


if __name__ == "__main__":
    asyncio.run(runTest())