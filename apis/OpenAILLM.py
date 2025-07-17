import os
import time
import asyncio
from dotenv import load_dotenv
from typing_extensions import Literal
from colorama import Fore

from openai import OpenAI

from config.config import LLM_TEMP
from .LLMResponse import LLMResponse
from core.exceptions import LLMResponseFailedError, InvalidJsonFormatError
from utils.response_parsing import parse_llm_output
from templates.prompt_templates.weights_generation_template import WEIGHT_GEN_SYS_MSG, WEIGHTS_GEN_USER_MSG
from templates.prompt_templates.ReportGenerationTemplate import REPORT_GEN_SYS_MSG, REPORT_GEN_USER_MSG

load_dotenv(override=True)

class OpenAILLM:
    def __init__(
        self,
        llm_model: Literal[
            'GPT-o4-Reasoning-Mini', 'GPT-4o-Mini', 'GPT-4.1-Mini', 'GPT-o3-Reasoning-Full', 'GPT-3.5-Turbo'
        ],
        temperature: float = LLM_TEMP,
    ):
        self.model_map = {
            'GPT-o4-Reasoning-Mini': 'o4-mini-2025-04-16',
            'GPT-4o-Mini': 'gpt-4o-mini-2024-07-18',
            'GPT-4.1-Mini': 'gpt-4.1-mini-2025-04-14',
            'GPT-o3-Reasoning-Full': 'o3-2025-04-16',
            'GPT-3.5-Turbo': 'gpt-3.5-turbo-0125'
        }
        self.provider_name     = 'OpenAI'
        self.fallback_models   = ['GPT-4.1-Mini', 'GPT-3.5-Turbo']
        self.reasoning_models  = ['GPT-o4-Reasoning-Mini', 'GPT-o3-Reasoning-Full']
        self.temperature       = temperature
        self.model_name        = llm_model
        self.model             = self.model_map[llm_model]
        self.client            = OpenAI() ## auto finds api key OPENAI_API_KEY

    async def _get_llm_response(
        self,
        system_message: str,
        user_message: str,
    ) -> LLMResponse:
        
        loop = asyncio.get_running_loop()
        time_start = time.perf_counter()

        response = await loop.run_in_executor(
            None,
            lambda: self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': user_message}
                ],
                temperature=self.temperature,
                response_format='json',
                timeout=180
            )
        )
        time_end = time.perf_counter()

        metadata = {
            'response_time': round(time_end - time_start, 2),
            'token_usage': {
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }

        output = parse_llm_output(response.choices[0].message.content)
        return LLMResponse(content=output, metadata=metadata)


    async def get_model_response(
        self,
        system_message: str,
        user_message: str,
        retry_limit: int = 1
    ) -> LLMResponse:
        
        fallback_models = self.fallback_models[:]
        if self.model_name in fallback_models:
            fallback_models.remove(self.model_name)

        retry = 0
        while retry < min(retry_limit, len(fallback_models)):
            print(f"--> Attempting response with model: {self.model_name}.")
            try:
                llm_response = await self._get_llm_response(system_message, user_message)
                return llm_response
            
            except InvalidJsonFormatError:
                print(f"--> Malformed JSON output: {self.model_name}")
                retry += 1
            
            except Exception as e:
                new_model = fallback_models[retry]
                print(Fore.RED+f"[ERROR] API Response failed for LLM '{self.model_name}'. Retrying using LLM '{new_model}'.")
                print(f"[REASON]"+Fore.RESET, e)
                print()
                retry += 1
                self._set_llm_model(new_model)

        raise LLMResponseFailedError(self.provider_name)


    def _set_llm_model(
        self,
        model: Literal[
            'GPT-o4-Reasoning-Mini', 'GPT-4o-Mini', 'GPT-4.1-Mini', 'GPT-o3-Reasoning-Full', 'GPT-3.5-Turbo'
        ] = 'LG_Exaone_3.5_Instruct'
    ):

        chosen = self.model_map.get(model)
        if not chosen:
            # fallback to default if somehow model not in map
            chosen = self.model_map['GPT-4o-Mini']
        self.model = chosen
        self.model_name = model


    async def generate_report_part(
        self, 
        system_msg: str, 
        user_msg: str,
        **kwargs
    ) -> LLMResponse:
        """
            Weight-gen: Requires personal_data
            Non-weight-gen: Requires personal_data, derived_metrics, benchmark_data 
        """
        user_message = self.format_any_prompt_template(user_msg, **kwargs)
        return await self.get_model_response(system_msg, user_message)


    async def generate_weights_using_llm(
        self, 
        personal_data: str, 
    ) -> LLMResponse:
        user_message = self.format_any_prompt_template(WEIGHT_GEN_SYS_MSG, personal_data=personal_data)
        return await self.get_model_response(WEIGHT_GEN_SYS_MSG, user_message)


    def format_any_prompt_template(self, template: str, **kwargs) -> str:
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")
        

    async def generate_report_using_llm(self, personal_data: str, derived_metrics: str, benchmark_data: str):
        """
            Generates complete report. Requires personal_data, derived_metrics, benchmark_data.
        """
        user_message = self._format_report_gen_template(REPORT_GEN_USER_MSG, personal_data, derived_metrics, benchmark_data)
        return await self.get_model_response(REPORT_GEN_SYS_MSG, user_message)


    def _format_report_gen_template(self, template: str, personal_data: str, derived_metrics: str, benchmark_data: str) -> str:
        try:
            return template.format(personal_data=personal_data, derived_metrics=derived_metrics, benchmark_data=benchmark_data)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")
        