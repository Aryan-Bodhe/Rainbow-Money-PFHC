import os
import time
import asyncio
from dotenv import load_dotenv
from typing_extensions import Literal

from openai import OpenAI

from apis.LLMResponse import LLMResponse
from config.config import LLM_TEMP
from utils.logger import get_logger
from core.exceptions import LLMResponseFailedError, InvalidJsonFormatError
from utils.response_parsing import parse_llm_output
from templates.prompt_templates.weights_generation_template import WEIGHT_GEN_SYS_MSG, WEIGHTS_GEN_USER_MSG
from templates.prompt_templates.ReportGenerationTemplate import REPORT_GEN_SYS_MSG, REPORT_GEN_USER_MSG

load_dotenv(override=True)
logger = get_logger()

class TogetherLLM:
    def __init__(
        self,
        llm_model: Literal['DeepSeek_R1_Distilled', 'Llama_3.3_Instruct_Turbo', 'LG_Exaone_3.5_Instruct'],
        temperature: float = LLM_TEMP,
    ):
        # Platform-specific mappings remain unchanged
        self.model_map = {
            'DeepSeek_R1_Distilled': 'deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free',
            'Llama_3.3_Instruct_Turbo': 'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free',
            'LG_Exaone_3.5_Instruct': 'lgai/exaone-3-5-32b-instruct'
        }
        self.fallback_models = ['Llama_3.3_Instruct_Turbo', 'LG_Exaone_3.5_Instruct']
        self.models_support_json = ['DeepSeek_R1_Distilled']
        self.provider_name = 'Together.ai'
        self.temperature = temperature
        self.model_name = llm_model
        self.model = self.model_map[llm_model]
        self.client = OpenAI(
            api_key=os.getenv('TOGETHER_API_KEY'),
            base_url='https://api.together.xyz/v1'
        )

    async def _get_llm_response(self, system_message: str, user_message: str, advanced: Literal[True, False] = False) -> LLMResponse:
        """
        Calls the Chat Completions endpoint, measures performance, parses JSON output.
        """
        start = time.perf_counter()
        # Use asyncio.to_thread for cleaner thread offload
        if advanced:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                response_format='json',
                timeout=180
            )
        else:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                timeout=120
            )
        duration = round(time.perf_counter() - start, 4)

        # Extract raw content
        raw_output = response.choices[0].message.content
        parsed = parse_llm_output(raw_output)

        metadata = {
            'response_time': duration,
            'token_usage': {
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
        return LLMResponse(content=parsed, metadata=metadata)

    async def get_model_response(
        self,
        system_message: str,
        user_message: str,
        retry_limit: int = 1,
        advanced: Literal[True, False] = False
    ) -> LLMResponse:
        """
        Attempts to get a response, retries on failure with fallback models.
        """
        fallback_models = [m for m in self.fallback_models if m != self.model_name]
        attempts = 0

        while attempts <= retry_limit and attempts <= len(fallback_models):
            logger.info(f'Attempting response with model: {self.model_name}.')
            try:
                if self.model_name not in self.models_support_json:
                    advanced = False
                return await self._get_llm_response(system_message, user_message, advanced)

            except Exception as e:
                # On JSON errors or other exceptions, switch model and retry
                if attempts < len(fallback_models):
                    new_model = fallback_models[attempts]
                    logger.error(f"{self.provider_name} API Response failed for LLM '{self.model_name}'. Retrying using LLM '{new_model}'.")
                    logger.exception(e)
                    self._set_llm_model(new_model)
                    attempts += 1
                    continue
                break

        raise LLMResponseFailedError(self.provider_name)

    async def generate_report_part(self, system_msg: str, user_msg: str, advanced: Literal[True, False] = False, **kwargs) -> LLMResponse:
        """Generates a report segment given a prompt template and kwargs."""
        user_message = self.format_any_prompt_template(user_msg, **kwargs)
        return await self.get_model_response(system_msg, user_message, advanced=advanced)

    async def generate_weights_using_llm(self, personal_data: str, advanced: Literal[True, False] = False) -> LLMResponse:
        """Generates weight suggestions based on personal data."""
        user_message = self.format_any_prompt_template(WEIGHTS_GEN_USER_MSG, personal_data=personal_data)
        return await self.get_model_response(WEIGHT_GEN_SYS_MSG, user_message, advanced)

    async def generate_report_using_llm(
        self,
        personal_data: str,
        derived_metrics: str,
        benchmark_data: str
    ) -> LLMResponse:
        """Generates a full report based on provided data."""
        user_message = self._format_report_gen_template(
            REPORT_GEN_USER_MSG,
            personal_data,
            derived_metrics,
            benchmark_data
        )
        return await self.get_model_response(REPORT_GEN_SYS_MSG, user_message)

    def format_any_prompt_template(self, template: str, **kwargs) -> str:
        """Safely formats a prompt template with provided kwargs."""
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

    def _set_llm_model(
        self,
        model: Literal['DeepSeek_R1_Distilled', 'Llama_3.3_Instruct_Turbo', 'LG_Exaone_3.5_Instruct']
    ):
        """Updates the client to use a different model."""
        chosen = self.model_map.get(model, self.model_map[self.fallback_models[0]])
        self.model_name = model
        self.model = chosen
