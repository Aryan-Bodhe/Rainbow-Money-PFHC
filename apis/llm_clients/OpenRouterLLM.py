import os
import time
import asyncio
from dotenv import load_dotenv
from typing_extensions import Literal
from colorama import Fore

from openai import OpenAI

from config.config import LLM_TEMP
from core.exceptions import LLMResponseFailedError, InvalidJsonFormatError
from utils.response_parsing import parse_llm_output
from templates.prompt_templates.weights_generation_template import WEIGHT_GEN_SYS_MSG, WEIGHTS_GEN_USER_MSG
from templates.prompt_templates.ReportGenerationTemplate import REPORT_GEN_SYS_MSG, REPORT_GEN_USER_MSG

load_dotenv()

class OpenRouterLLM:
    def __init__(
        self,
        llm_model: Literal[
            'Mistral_7B', 'Mistral_Small', 'Llama_3.2', 'DeepSeek_R1',
            'Qwen_A3B', 'InternVL3', 'Nous_DeepHermes', 'Microsoft_Phi4',
            'DeepSeek_V3', 'Nvidia_Nemotron', 'DeepSeek_R1_Qwen'
        ],
        temperature: float = LLM_TEMP,
    ):
        # map your friendly names → OpenRouter model identifiers
        self.model_map = {
            'DeepSeek_R1':      'deepseek/deepseek-r1-0528:free',
            'DeepSeek_V3':      'deepseek/deepseek-chat-v3-0324:free',
            'Microsoft_Phi4':   'microsoft/phi-4-reasoning-plus:free',
            'Qwen_A3B':         'qwen/qwq-32b:free',
            'InternVL3':        'opengvlab/internvl3-14b:free',
            'Llama_3.2':        'meta-llama/llama-3.2-3b-instruct:free',
            'Mistral_7B':       'mistralai/mistral-7b-instruct:free',
            'Mistral_Small':    'mistralai/mistral-small-3.2-24b-instruct:free',
            'Nous_DeepHermes':  'nousresearch/deephermes-3-llama-3-8b-preview:free',
            'Nvidia_Nemotron':  'nvidia/llama-3.3-nemotron-super-49b-v1:free',
            'DeepSeek_R1_Qwen': 'deepseek/deepseek-r1-0528-qwen3-8b:free'
        }
        self.provider_name   = 'OpenRouter'
        self.fallback_models = ['Qwen_A3B', 'Llama_3.2', 'Mistral_7B']

        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.temperature       = temperature
        self.model_name        = llm_model
        self.model             = self.model_map[llm_model]
        self.client            = OpenAI(
            api_key=self.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    async def generate_report_part(
        self,
        system_msg: str,
        user_msg: str,
        **kwargs
    ) -> dict:
        """
        A single section of the report (e.g. profile review, commendables, etc.).
        """
        user_message = self.format_any_prompt_template(user_msg, **kwargs)
        return await self.get_model_response(system_msg, user_message)

    async def generate_report_using_llm(
        self,
        personal_data: str,
        derived_metrics: str,
        benchmark_data: str
    ) -> dict:
        """
        One-shot full-report generation.
        """
        user_message = self._format_report_gen_template(
            REPORT_GEN_USER_MSG,
            personal_data,
            derived_metrics,
            benchmark_data
        )
        return await self.get_model_response(REPORT_GEN_SYS_MSG, user_message)

    async def generate_weights_using_llm(
        self,
        personal_data: str
    ) -> dict:
        """
        Ask the model to assign weights.
        """
        user_message = self._format_scoring_template(
            WEIGHTS_GEN_USER_MSG,
            personal_data
        )
        return await self.get_model_response(WEIGHT_GEN_SYS_MSG, user_message)

    async def get_model_response(
        self,
        system_message: str,
        user_message: str
    ) -> dict:
        """
        Core async call with fallback. Sends [system, user] messages and expects JSON.
        """
        fallback = [m for m in self.fallback_models if m != self.model_name]
        loop = asyncio.get_running_loop()
        retries = 0

        while retries < len(fallback) + 1:
            print(f"--> Attempting response with model {self.model_name}")
            try:
                t_start = time.perf_counter()

                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user",   "content": user_message}
                        ],
                        temperature=self.temperature or LLM_TEMP,
                        response_format='json'
                    )
                )

                t_end = time.perf_counter()
                raw = response.choices[0].message.content

                # parse + validate JSON
                parsed = parse_llm_output(raw)

                usage = response.usage
                perf_data = {
                    "total_response_time": round(t_end - t_start, 4),
                    "token_data": {
                        "prompt_tokens":     usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens":      usage.total_tokens
                    }
                }

                return {"response": parsed, "perf_data": perf_data}

            except InvalidJsonFormatError:
                print(f"--> Malformed JSON output from {self.model_name}, retrying...")
                retries += 1
                continue

            except Exception as e:
                print(Fore.RED + f"[ERROR] '{self.model_name}' failed." + Fore.RESET)
                print(f"Reason: {e}\n")
                if retries >= len(fallback):
                    break
                # switch to next fallback
                new_model = fallback[retries]
                self._set_llm_model(new_model)
                retries += 1

        raise LLMResponseFailedError(self.provider_name)

    def _format_report_gen_template(
        self,
        template: str,
        personal_data: str,
        derived_metrics: str,
        benchmark_data: str
    ) -> str:
        try:
            return template.format(
                personal_data=personal_data,
                derived_metrics=derived_metrics,
                benchmark_data=benchmark_data
            )
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")

    def format_any_prompt_template(
        self,
        template: str,
        **kwargs
    ) -> str:
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")

    def _format_scoring_template(
        self,
        template: str,
        personal_data: str
    ) -> str:
        try:
            return template.format(personal_data=personal_data)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")

    def _set_llm_model(
        self,
        model: Literal[
            'Mistral_7B', 'Mistral_Small', 'Llama_3.2', 'DeepSeek_R1',
            'Qwen_A3B', 'InternVL3', 'Nous_DeepHermes', 'Microsoft_Phi4',
            'DeepSeek_V3', 'Nvidia_Nemotron', 'DeepSeek_R1_Qwen'
        ]
    ):
        """
        Update both human-readable and actual model identifier.
        """
        self.model_name = model
        self.model      = self.model_map.get(model, self.model_map['Mistral_7B'])
