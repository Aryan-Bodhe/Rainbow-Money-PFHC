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
from config.config import ENABLE_TESTING, REPORT_TEMPLATE_NAME, GENERATE_REPORT
from core.benchmarking import get_benchmarks, analyse_benchmarks
from core.scoring_system import score_metrics
from utils.response_parsing import post_process_weights
from utils.data_validation import validate_report_response, is_valid_json

from templates.prompt_templates.areas_for_improvement_generation_template import AREAS_FOR_IMPROVEMENT_SYS_MSG, AREAS_FOR_IMPROVEMENT_USER_MSG
from templates.prompt_templates.commendable_areas_generation_template import COMMENDABLE_AREAS_SYS_MSG, COMMENDABLE_AREAS_USER_MSG
from templates.prompt_templates.profile_review_generation_template import PROFILE_REVIEW_SYS_MSG, PROFILE_REVIEW_USER_MSG
from templates.prompt_templates.summary_generation_template import SUMMARY_GENERATION_SYS_MSG, SUMMARY_GENERATION_USER_MSG

from config.config import (
    VERY_POOR_PROFILE,
    POOR_PROFILE,
    AVERAGE_PROFILE,
    GOOD_PROFILE,
    VERY_GOOD_PROFILE
)

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


async def runLLMTest(user_profile_path: str):

    timeStart = time.perf_counter()
    os.system('clear')
    console = Console()

    print('--> Personal Finance Health Calculator.')
    try:
        raw_data = read_json_from_file(user_profile_path)
    except Exception as e:
        console.print(f"[red]Error reading user data:[/] {e}")
        return

    print('--> Setting User Data')
    user_profile = set_user_data(raw_data)

    print('--> Computing Financial Metrics')
    calc = PersonalFinanceMetricsCalculator()
    derived_metrics = calc.analyze_user_profile(user_profile)

    # user_profile_json = user_profile
    personal_data_json = user_profile.personal_data.model_dump_json(indent=2)
    derived_metrics_json = derived_metrics.model_dump_json(indent=2)

    benchmark_data = get_benchmarks(derived_metrics)
    benchmark_data_json = json.dumps(benchmark_data)

    benchmark_analysis = analyse_benchmarks(derived_metrics)

    print('----------------------------------------')

    prefix = user_profile_path.replace('data/test_data', '').replace('_profile.json', '')

    # console.print_json(data=raw_data, indent=2)
    with open(f'temp/test_data_results/{prefix}_user_data.json', 'w') as f:
        json.dump(raw_data, indent=2, fp=f)

    # print('----------------------------------------')
    # console.print_json(data=json.loads(derived_metrics_json), indent=2)
    with open(f'temp/test_data_results/{prefix}_derived_metrics.json', 'w') as f:
        json.dump(json.loads(derived_metrics_json), indent=2, fp=f)

    # print('----------------------------------------')

    # console.print_json(data=benchmark_data, indent=2)
    with open(f'temp/test_data_results/{prefix}_benchmark_data.json', 'w') as f:
        json.dump(benchmark_data, indent=2, fp=f)

    with open(f'temp/test_data_results/{prefix}_benchmark_analysis.json', 'w') as f:
        json.dump(benchmark_analysis, indent=2, fp=f)





    ## BROKEN DUE TO STRUCTURAL CHANGES
    if GENERATE_REPORT:
        print('\n--> Analyzing User Profile using LLMs.')

        llm_report = TogetherLLM(llm_model='DeepSeek_R1_Distilled', temperature=0.5)
        # llm_1 = OpenRouterLLM(llm_model='DeepSeek_R1', temperature=1)
        llm_weights = TogetherLLM(llm_model='DeepSeek_R1_Distilled', temperature=1)
        # llm_2 = OpenRouterLLM(llm_model='Mistral_7B', temperature=0.5)
        # llm_summary = OpenRouterLLM(llm_model='Mistral_7B', temperature=0.0)
        llm_summary = TogetherLLM(llm_model='LG_Exaone_3.5_Instruct', temperature=0)


        report_data_content = {}

        perf_data = {
            "weights_generation":"",
            "profile_review_generation":"",
            "commendable_areas_generation":"",
            "areas_for_improvement_generation":"",
            "summary_generation":""
        }
        

        weight_data, sec1, sec2, sec3 = await asyncio.gather(
            llm_weights.generate_weights_using_llm(
                personal_data_json,
                advanced=True
            ),
            llm_report.generate_report_part(
                PROFILE_REVIEW_SYS_MSG, 
                PROFILE_REVIEW_USER_MSG, 
                advanced=True,
                personal_data=personal_data_json, 
                derived_metrics=derived_metrics_json, 
                benchmark_data=benchmark_data_json
            ),
            llm_report.generate_report_part(
                COMMENDABLE_AREAS_SYS_MSG, 
                COMMENDABLE_AREAS_USER_MSG, 
                advanced=True,
                personal_data=personal_data_json, 
                derived_metrics=derived_metrics_json, 
                benchmark_data=benchmark_data_json
            ),
            llm_report.generate_report_part(
                AREAS_FOR_IMPROVEMENT_SYS_MSG, 
                AREAS_FOR_IMPROVEMENT_USER_MSG, 
                advanced=True,
                personal_data=personal_data_json, 
                derived_metrics=derived_metrics_json, 
                benchmark_data=benchmark_data_json
            )        
        )

        weight_data_content = post_process_weights(weight_data['response'])
        report_data_content.update(sec1['response'])
        report_data_content.update(sec2['response'])
        report_data_content.update(sec3['response'])

        console.print('[green]--> Generating Summary. [/]')

        summary_data = await llm_summary.generate_report_part(
            SUMMARY_GENERATION_SYS_MSG, 
            SUMMARY_GENERATION_USER_MSG,
            advanced=False,
            overall_profile_review=report_data_content['overall_profile_review'],
            commendable_areas=report_data_content['commendable_areas'],
            areas_for_improvement=report_data_content['areas_for_improvement']
        )
        
        report_data_content.update(summary_data['response'])

        perf_data["weights_generation"] = weight_data['perf_data']
        perf_data['profile_review_generation'] = sec1['perf_data']
        perf_data['commendable_areas_generation'] = sec2['perf_data']
        perf_data['areas_for_improvement_generation'] = sec3['perf_data']
        perf_data['summary_generation'] = summary_data['perf_data']


        console.print('[green]--> Scoring Metrics. [/]')
        scores = score_metrics(derived_metrics, weight_data_content)


        console.print('[green]--> Validating response. [/]')
        valid, err = validate_report_response(report_data_content)


        if not valid:
            console.print('[red]Report Data validation failed. Aborting.[/]')
            print(err)
            if is_valid_json(report_data_content):
                console.print_json(report_data_content)
            else:
                # console.print(report_data_content)
                pass
            return


        pdf_generator = PDFGenerator()
        analyzed_metrics_table = pdf_generator.get_metrics_summary_table_dict(
            derived_metrics.model_dump(), 
            weight_data_content, 
            benchmark_data,
            scores
        )

        context_data = pdf_generator.generate_context_data(report_data_content, analyzed_metrics_table)
        
        pdf_generator.j2_template_to_pdf(REPORT_TEMPLATE_NAME, context_data)


        # console.print("[bold green]Final weights:[/]")
        # console.print_json(data=weights['output'], indent=2)

        console.print("\n<--- [bold green] Report Generation Successful.[/] --->")
        print('-----------------------------------------------------------')

        # if ENABLE_TESTING:
        #     for key, value in perf_data.items():
        #         console.print(f"\n[bold yellow]LLM Performace Data for : {key}.[/]")
        #         console.print_json(data=value, indent=2)

        # console.print(f"\n[bold yellow]Total Performance: {key}.[/]")

        timeEnd = time.perf_counter()

        # total_ex_time = round(timeEnd-timeStart, 2)
        # if int(total_ex_time / 60) == 0:
        #     console.print(f"\n[bold green]Total Execution Runtime: {total_ex_time:0.2f} secs.")
        # else:
        #     console.print(f"\n[bold green]Total Execution Runtime: {int(total_ex_time / 60)} min {total_ex_time % 60:0.2f} secs.")

            
        # TOTAL EXECUTION PERFORMANCE
        total_prompt = 0
        total_response = 0
        total = 0

        for section in perf_data.values():
            if isinstance(section, dict) and "total_tokens" in section:
                tokens = section["total_tokens"]
                total_prompt += tokens.get("prompt_tokens", 0)
                total_response += tokens.get("response_tokens", 0)
                total += tokens.get("total_tokens", 0)

        perf_data["complete_report_generation"] = {
            "total_prompt_tokens": total_prompt,
            "total_response_tokens": total_response,
            "total_tokens": total
        }

        if ENABLE_TESTING:
            for key, value in perf_data.items():
                console.print(f"\n[bold yellow]LLM Performace Data for : {key}.[/]")
                console.print_json(data=value, indent=2)

        total_ex_time = round(timeEnd-timeStart, 2)
        if int(total_ex_time / 60) == 0:
            console.print(f"\n[bold green]Total Execution Runtime: {total_ex_time:0.2f} secs.")
        else:
            console.print(f"\n[bold green]Total Execution Runtime: {int(total_ex_time / 60)} min {total_ex_time % 60:0.2f} secs.")


        print('-----------------------------------------------------------')


async def runLLMTestCollection():
    tests = [
        VERY_POOR_PROFILE,
        POOR_PROFILE,
        AVERAGE_PROFILE,
        GOOD_PROFILE,
        VERY_GOOD_PROFILE
    ]

    for test in tests:
        await runLLMTest(user_profile_path=test)
        print('Analysis completed')


if __name__ == "__main__":
    # asyncio.run(runTestCollection())
    pass