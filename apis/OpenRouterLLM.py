import os
import time
import asyncio
from dotenv import load_dotenv
from typing_extensions import Literal

from openai import OpenAI

from apis.LLMResponse import LLMResponse
from config.config import LLM_TEMP
from core.exceptions import LLMResponseFailedError, InvalidJsonFormatError
from utils.response_parsing import parse_llm_output
from utils.logger import get_logger
from templates.prompt_templates.weights_generation_template import WEIGHT_GEN_SYS_MSG, WEIGHTS_GEN_USER_MSG
from templates.prompt_templates.ReportGenerationTemplate import REPORT_GEN_SYS_MSG, REPORT_GEN_USER_MSG

load_dotenv(override=True)
logger = get_logger()

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
        # platform-specific mappings unchanged
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

        self.temperature      = temperature
        self.model_name       = llm_model
        self.model            = self.model_map[llm_model]
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.client           = OpenAI(
            api_key=self.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    async def _get_llm_response(self, system_message: str, user_message: str) -> LLMResponse:
        """
        Calls Chat Completions, measures perf, parses and validates JSON.
        """
        start = time.perf_counter()
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user",   "content": user_message}
            ],
            temperature=self.temperature,
            response_format='json',
            timeout=180
        )
        duration = round(time.perf_counter() - start, 4)

        raw = response.choices[0].message.content
        parsed = parse_llm_output(raw)

        metadata = {
            "response_time": duration,
            "token_data": {
                "prompt_tokens":     response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens":      response.usage.total_tokens
            }
        }
        return LLMResponse(content=parsed, metadata=metadata)

    async def get_model_response(
        self,
        system_message: str,
        user_message: str,
        retry_limit: int = 1
    ) -> LLMResponse:
        """
        Core async call with fallback and retry logic.
        """
        fallback = [m for m in self.fallback_models if m != self.model_name]
        attempts = 0

        while attempts <= retry_limit and attempts <= len(fallback):
            logger.info(f"{self.provider_name} attempting response with model: {self.model_name}")
            try:
                return await self._get_llm_response(system_message, user_message)

            except (InvalidJsonFormatError, Exception) as e:
                if attempts < len(fallback):
                    new_model = fallback[attempts]
                    logger.error(f"{self.provider_name} API Response failed for LLM '{self.model_name}'. Retrying using LLM '{new_model}'.")
                    self._set_llm_model(new_model)
                    attempts += 1
                    continue
                break

        raise LLMResponseFailedError(self.provider_name)

    async def generate_report_part(
        self,
        system_msg: str,
        user_msg: str,
        **kwargs
    ) -> LLMResponse:
        """Generates a report segment using prompt template and kwargs."""
        user_message = self.format_any_prompt_template(user_msg, **kwargs)
        return await self.get_model_response(system_msg, user_message)

    async def generate_weights_using_llm(self, personal_data: str) -> LLMResponse:
        """Generates weight suggestions based on personal data."""
        user_message = self.format_any_prompt_template(WEIGHTS_GEN_USER_MSG, personal_data=personal_data)
        return await self.get_model_response(WEIGHT_GEN_SYS_MSG, user_message)

    async def generate_report_using_llm(
        self,
        personal_data: str,
        derived_metrics: str,
        benchmark_data: str
    ) -> LLMResponse:
        """Generates full report from provided data."""
        user_message = self._format_report_gen_template(
            REPORT_GEN_USER_MSG,
            personal_data,
            derived_metrics,
            benchmark_data
        )
        return await self.get_model_response(REPORT_GEN_SYS_MSG, user_message)

    def format_any_prompt_template(self, template: str, **kwargs) -> str:
        """Safely formats any prompt template with kwargs."""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")

    def _format_report_gen_template(
        self,
        template: str,
        personal_data: str,
        derived_metrics: str,
        benchmark_data: str
    ) -> str:
        """Formats the report generation template."""
        try:
            return template.format(
                personal_data=personal_data,
                derived_metrics=derived_metrics,
                benchmark_data=benchmark_data
            )
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")

    def _format_scoring_template(self, template: str, personal_data: str) -> str:
        """Formats the weights generation template."""
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
        """Updates model to a fallback identifier."""
        chosen = self.model_map.get(model, self.model_map[self.fallback_models[0]])
        self.model_name = model
        self.model      = chosen
