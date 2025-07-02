import json
import os
import time
from dotenv import load_dotenv
from typing_extensions import Literal
from colorama import Fore
import asyncio

from openai import OpenAI
from config.config import LLM_TEMP
from core.exceptions import LLMResponseFailedError, InvalidJsonFormatError
from utils.response_parsing import parse_llm_output
from templates.prompt_templates.weights_generation_template import WEIGHT_GEN_SYS_MSG, WEIGHTS_GEN_USER_MSG
from templates.prompt_templates.ReportGenerationTemplate import REPORT_GEN_SYS_MSG, REPORT_GEN_USER_MSG

load_dotenv()

class TogetherLLM:
    def __init__(
        self,
        llm_model: Literal['DeepSeek_R1_Distilled', 'Llama_3.3_Instruct_Turbo', 'LG_Exaone_3.5_Instruct'],
        temperature: float = LLM_TEMP,
    ):
        self.model_map = {
            'DeepSeek_R1_Distilled':'deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free',
            'Llama_3.3_Instruct_Turbo':'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free', # does not work
            'LG_Exaone_3.5_Instruct':'lgai/exaone-3-5-32b-instruct' # not free?
        }
        
        self.fallback_models = ['Llama_3.3_Instruct_Turbo', 'LG_Exaone_3.5_Instruct']

        self.provider_name = 'Together.ai'
        self.temperature = temperature
        self.model = self.model_map.get(llm_model)
        self.model_name = llm_model
        self.client = OpenAI(
            api_key=os.getenv('TOGETHER_API_KEY'),
            base_url='https://api.together.xyz/v1'
        )

    async def generate_report_part(self, system_msg: str, user_msg: str, advanced = Literal[True, False], **kwargs):
        """
            Requires personal_data, derived_metrics, benchmark_data
        """
        user_message = self.format_any_prompt_template(user_msg, **kwargs)
        return await self.get_model_response(system_msg, user_message, advanced)

    async def generate_report_using_llm(self, personal_data: str, derived_metrics: str, benchmark_data: str):
        user_message = self._format_report_gen_template(REPORT_GEN_USER_MSG, personal_data, derived_metrics, benchmark_data)
        return await self.get_model_response(REPORT_GEN_SYS_MSG, user_message)


    async def generate_weights_using_llm(self, personal_data: str, advanced = Literal[True, False]):
        user_message = self._format_scoring_template(WEIGHTS_GEN_USER_MSG, personal_data)
        return await self.get_model_response(WEIGHT_GEN_SYS_MSG, user_message, advanced)
        

    async def get_model_response(
        self,
        system_message: str,
        user_message: str,
        advanced: Literal[True, False] = True,
    ) -> dict:
        
        loop = asyncio.get_running_loop()

        fallback_models = self.fallback_models[:]
        if self.model_name in fallback_models:
            fallback_models.remove(self.model_name)

        retry = 0
        while retry < len(fallback_models):
            print(f"--> Attempting response with model: {self.model_name}.")
            try:
                response_time_start = time.perf_counter()
                
                if advanced:
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": system_message},
                                {"role": "user", "content": user_message}
                            ],
                            temperature=self.temperature or LLM_TEMP,
                            response_format='json'
                        )
                    )
                else:
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": system_message},
                                {"role": "user", "content": user_message}
                            ],
                            temperature=self.temperature or LLM_TEMP,
                        )
                    )

                response_time_end = time.perf_counter()

                output = response.choices[0].message.content

                # if not is_valid_json(output):
                #     raise InvalidJsonFormatError()

                output = parse_llm_output(output)

                token_data = {
                    'prompt_tokens':response.usage.prompt_tokens,
                    'response_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }

                perf_data = {
                    "total_response_time": round(response_time_end - response_time_start, 4),
                    "total_tokens": token_data
                }

                return {'response': output, 'perf_data': perf_data}
            
            except InvalidJsonFormatError:
                print(f"--> Malformed JSON output: {self.model_name}")
                # print(output)
                retry += 1
                continue
            
            except Exception as e:
                new_model = fallback_models[retry]
                print(Fore.RED+f"[ERROR] API Response failed for LLM '{self.model_name}'. Retrying using LLM '{new_model}'.")
                print(f"[REASON]"+Fore.RESET, e)
                print()
                retry += 1
                self._set_llm_model(new_model)

        raise LLMResponseFailedError(self.provider_name)


    def _format_report_gen_template(self, template: str, personal_data: str, derived_metrics: str, benchmark_data: str) -> str:
        try:
            return template.format(personal_data=personal_data, derived_metrics=derived_metrics, benchmark_data=benchmark_data)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")
        

    def format_any_prompt_template(self, template: str, **kwargs) -> str:
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")


    def _format_scoring_template(self, template: str, personal_data: str) -> str:
        try:
            return template.format(personal_data=personal_data)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")
        

    def _set_llm_model(
        self,
        model: Literal[
            'DeepSeek_R1_Distilled', 'Llama_3.3_Instruct_Turbo', 'LG_Exaone_3.5_Instruct'
        ] = 'LG_Exaone_3.5_Instruct'
    ):

        chosen = self.model_map.get(model)
        if not chosen:
            # fallback to default if somehow model not in map
            chosen = self.model_map['LG_Exaone_3.5_Instruct']
        self.model = chosen
        self.model_name = model
