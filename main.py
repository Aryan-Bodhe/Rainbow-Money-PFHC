import os
import json
from pydantic import ValidationError
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
import re
import asyncio

from source.FinanceAnalyzer import PersonalFinanceMetricsCalculator
from source.UserProfile import UserProfile
from apis.OpenRouterLLM import OpenRouterLLM
from apis.PDFGenerator import PDFGenerator
from apis.TogetherLLM import TogetherLLM
from config import METRICS_OUTPUT_PATH, ENABLE_TESTING, USER_PROFILE_DATA_PATH, ENABLE_STREAMING, SHOW_REASONING, RETRY_ATTEMPT_LIMIT


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


def _is_valid_json(json_str: str) -> bool:
    try:
        json.loads(json_str)
        return True
    except Exception:
        return False


async def runTest():
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
    user_derived_metrics = calc.analyze_user_profile(user_profile)

    personal_data_json = user_profile.personal_data.model_dump_json(indent=2)

    print('\n--> Analyzing User Profile using LLMs.')

    llm = TogetherLLM(llm_model='DeepSeek_R1_Dis_Llama', temperature=0.5)

    # 1) First, a sync call to get plain JSON string + perf
    response = await llm.generate_weights_using_llm(personal_data_json)


    print('\n--------------------------------------------------------\n')

    # print(response)

    console.print("[bold green]Final weights:[/]")
    console.print_json(data=response['output'], indent=2)
    if ENABLE_TESTING:
        console.print("\n[bold yellow]LLM Performance Data:[/]")
        console.print_json(data=response['perf_data'], indent=2)


def runOpenRouterTest():
    os.system('clear')
    print('--> Personal Finance Health Calculator.')
    try:
        raw_data = read_json_from_file(USER_PROFILE_DATA_PATH)
    except Exception as e:
        print(e)
        exit(0)

    print('--> Setting User Data')
    user_profile = set_user_data(raw_data)

    print('--> Computing Financial Metrics')
    calc = PersonalFinanceMetricsCalculator()
    user_derived_metrics = calc.analyze_user_profile(user_profile)

    # print(f'\nUser Derived Metrics:')
    # print(user_derived_metrics)

    user_profile_json = user_profile.personal_data.model_dump_json(indent=2)
    user_derived_metrics_json = user_derived_metrics.model_dump_json(indent=2)

    console = Console()
    # console.print_json(user_profile_json, indent=2)
    # console.print_json(user_derived_metrics_json, indent=2)

    # print(f'--> Saving Computed Metrics to {METRICS_OUTPUT_PATH}.')
    # with open(METRICS_OUTPUT_PATH, 'w') as f:
    #     f.write(user_derived_metrics_json)

    
    # ___________________________________________________________ #

    print('\n--> Analyzing User Profile using LLMs.')

    llm = OpenRouterLLM(llm_model='InternVL3', temperature=0.1)

    stream, _perf = llm.get_model_response(user_profile_json, user_derived_metrics_json, streaming=ENABLE_STREAMING, enable_testing=ENABLE_TESTING)
    print('--> User Profile Analysis Complete.')
    console = Console()
    buffer = ""
    perf_data = None

    print('---------------------------------------------------------')
    # Use Live to continuously update the rendered Markdown
    if ENABLE_STREAMING:
        with Live(console=console, refresh_per_second=10) as live:
            for piece in stream:
                # if piece is None:
                #     continue
                if isinstance(piece, str):
                    buffer += piece
                    # Update the live display with the latest Markdown buffer
                    live.update(Markdown(buffer))
                elif isinstance(piece, dict) and "_perf" in piece:
                    perf_data = piece["_perf"]
    else:
        if stream.startswith('```json') and stream.endswith('```'):
            stream = stream.replace('```json', '').replace('```', '')
        if _is_valid_json(json_str=(stream)):
            console.print_json(data=json.loads(stream))
            # print(stream)
        else:
            print(stream)
        
        

            
    # If you enabled testing, final piece is perf-data dict
    if ENABLE_TESTING and (perf_data or _perf):
        console.print("\n[bold yellow]LLM Performance Data:[/]")
        if ENABLE_STREAMING:
            console.print_json(data=(perf_data), indent=2)
        else:
            console.print_json(data=(_perf), indent=2)


    # print('--> Generating Report PDF.')
    # pdf_gen = PDFGenerator()
    # pdf_gen.markdown_to_pdf(input_md_str=buffer)
    # print('--> Analysis Complete.')


if __name__ == "__main__":
    asyncio.run(runTest())