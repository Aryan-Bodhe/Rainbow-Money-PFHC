import json
import os
import time
from dotenv import load_dotenv
from typing_extensions import Literal, Generator, Union, Tuple
from colorama import Fore
import asyncio

from openai import OpenAI
from config import LLM_TEMP
from exceptions import InvalidJsonFormatError ,LLMResponseFailedError
from apis.prompts.PromptTemplate import PROMPT_TEMPLATE
from apis.prompts.ScoringPromptTemplate import SCORING_PROMPT_TEMPLATE
from apis.prompts.RescorePromptTemplate import RESCORE_TEMPLATE

load_dotenv()

class TogetherLLM:
    def __init__(
        self,
        llm_model: Literal['Llama_3.3_Instruct_Turbo', 'DeepSeek_R1_Dis_Llama', 'Llama_3.3_Instruct', 'LG_Exaone_3.5_Instruct'],
        temperature: float = LLM_TEMP,
    ):
        self.model_map = {
            'Llama_3.3_Instruct_Turbo':'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free',
            'DeepSeek_R1_Dis_Llama':'deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free',
            'Llama_3.3_Instruct':'nim/meta/llama-3.3-70b-instruct',
            'LG_Exaone_3.5_Instruct':'lgai/exaone-3-5-32b-instruct'
        }
        
        self.fallback_models = ['Llama_3.3_Instruct', 'Llama_3.3_Instruct_Turbo', 'LG_Exaone_3.5_Instruct']

        self.provider_name = 'Together.ai'
        self.temperature = temperature
        self.model = self.model_map.get(llm_model)
        self.model_name = llm_model
        self.client = OpenAI(
            api_key=os.getenv('TOGETHER_API_KEY'),
            base_url='https://api.together.xyz/v1'
        )


    async def generate_weights_using_llm(self, personal_data: str):
        prompt_text = self._format_scoring_template(SCORING_PROMPT_TEMPLATE, personal_data, '')
        return await self.get_model_response(prompt_text)
        

    async def get_model_response(
        self,
        prompt_text: str,
    ) -> dict:
        
        loop = asyncio.get_running_loop()

        fallback_models = self.fallback_models[:]
        if self.model in fallback_models:
            fallback_models.remove(self.model_name)

        retry = 0
        while retry < len(fallback_models):
            try:
                response_time_start = time.perf_counter()

                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt_text}],
                        temperature=self.temperature or LLM_TEMP,
                    )
                )

                response_time_end = time.perf_counter()

                output = response.choices[0].message.content
                output = self._parse_llm_output(output)
                output = self._post_process_weights(output)
                token_data = {
                    'prompt_tokens':response.usage.prompt_tokens,
                    'response_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }

                perf_data = {
                    "total_response_time": round(response_time_end - response_time_start, 4),
                    "total_tokens": token_data
                }

                return {'output': output, 'perf_data': perf_data}
            
            except Exception as e:
                new_model = fallback_models[retry]
                print(Fore.RED+f"[ERROR] API Response failed for LLM '{self.model_name}'. Retrying using LLM '{new_model}'.")
                print(f"[REASON]"+Fore.RESET, e)
                print()
                retry += 1
                self._set_llm_model(new_model)

        raise LLMResponseFailedError(self.provider_name)


    def _post_process_weights(self, raw_weights: dict):
        if sum(raw_weights.values()) == 100:
            return raw_weights
        
        # 1) Clip & normalize
        clipped = {k: max(0, v) for k, v in raw_weights.items()}
        total   = sum(clipped.values()) or 1
        scaled  = {k: v/total*100 for k, v in clipped.items()}
        # 2) Floor + compute remainders
        floors   = {k: int(v) for k, v in scaled.items()}
        remainders = {k: scaled[k] - floors[k] for k in scaled}
        shortfall  = 100 - sum(floors.values())
        # 3) Distribute remaining points
        for k in sorted(remainders, key=remainders.get, reverse=True)[:shortfall]:
            floors[k] += 1
        return floors
    
    def _parse_llm_output(self, json_str: str) -> dict:
        # 2) Strip any triple-backticks or think tags
        clean = json_str
        if clean.startswith('```'):
            clean = clean.replace('```json', '').replace('```', '')

        # strip think section if exists
        if clean.startswith('<think>'):
            clean = clean.split('</think>')[1]
            first_brace = clean.find('{')
            if first_brace != -1:
                clean = clean[first_brace:]

        # 3) Parse to dict
        try:
            weights = json.loads(clean)
            return weights
        except json.JSONDecodeError:
            raise InvalidJsonFormatError(var='weights')


    def _format_scoring_template(self, template: str, personal_data: str, derived_metrics:str):
        try:
            return template.format(personal_data=personal_data, derived_metrics=derived_metrics)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")
        

    def _is_valid_json(self, json_str: str) -> bool:
        try:
            json.loads(json_str)
            return True
        except Exception:
            return False


    def _set_llm_model(
        self,
        model: Literal[
            'Llama_3.3_Instruct_Turbo', 'DeepSeek_R1_Dis_Llama', 'Llama_3.3_Instruct', 'LG_Exaone_3.5_Instruct'
        ] = 'LG_Exaone_3.5_Instruct'
    ):

        chosen = self.model_map.get(model)
        if not chosen:
            # fallback to default if somehow model not in map
            chosen = self.model_map['LG_Exaone_3.5_Instruct']
        self.model = chosen
