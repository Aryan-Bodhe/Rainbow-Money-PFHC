import os
import json
from dotenv import load_dotenv
from typing_extensions import Literal, Generator, Union
from openai import OpenAI

from config import LLM_TEMP
from exceptions import InvalidJsonFormatError
from apis.PromptTemplate import PROMPT_TEMPLATE

load_dotenv()

'''
meta-llama/llama-3.3-8b-instruct:free
mistralai/mistral-7b-instruct:free
opengvlab/internvl3-14b:free
nousresearch/deephermes-3-llama-3-8b-preview:free
qwen/qwen3-30b-a3b:free
microsoft/phi-4-reasoning-plus:free
deepseek/deepseek-r1-0528-qwen3-8b:free
mistralai/mistral-small-3.2-24b-instruct:free
deepseek/deepseek-chat-v3-0324:free
nvidia/llama-3.3-nemotron-super-49b-v1:free
'''

class OpenRouterLLM:
    def __init__(
        self, 
        llm_model: Literal['Mistral_7B', 'Mistral_Small', 'Llama_3.3', 'DeepSeek_R1', 'Qwen_A3B', 'InternVL3', 'Nous_DeepHermes', 'Microsoft_Phi4', 'DeepSeek_V3', 'Nvidia_Nemotron'] = 'Mistral_7B', 
        temperature: float = None, 
        custom_api_key: str = None
    ):
        self.model_map = {
            'DeepSeek_R1':      'deepseek/deepseek-r1-0528-qwen3-8b:free',
            'InternVL3':        'opengvlab/internvl3-14b:free',
            'DeepSeek_V3':      'deepseek/deepseek-chat-v3-0324:free',
            'Llama_3.3':        'meta-llama/llama-3.3-8b-instruct:free',
            'Microsoft_Phi4':   'microsoft/phi-4-reasoning-plus:free',
            'Mistral_7B':       'mistralai/mistral-7b-instruct:free',
            'Mistral_Small':    'mistralai/mistral-small-3.2-24b-instruct:free',
            'Nous_DeepHermes':  'nousresearch/deephermes-3-llama-3-8b-preview:free',
            'Nvidia_Nemotron':  'nvidia/llama-3.3-nemotron-super-49b-v1:free',
            'Qwen_A3B':         'qwen/qwen3-30b-a3b:free',
        }
        self.openrouter_api_key = custom_api_key or os.getenv("OPENROUTER_API_KEY")
        self.temperature = temperature
        self.model = self.model_map.get(llm_model) or self.model_map['Mistral_7B']
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.openrouter_api_key
        )


    def format_prompt(self, template: str, user_profile: str, derived_metrics: str) -> str:
        try:
            return template.format(user_profile=user_profile, derived_metrics=derived_metrics)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt template: {e}")
        

    def _is_valid_json(self, json_str: str) -> bool:
        try:
            json.loads(json_str)
            return True
        except Exception:
            return False
        

    def get_model_response(
        self,
        user_profile: str,
        derived_metrics: str,
        streaming: bool = False,
        enable_testing: bool = False
    ) -> Union[str, Generator[Union[str, dict], None, None]]:
        if self.model is None:
            self.set_llm_model('Mistral_7B')

        if not self._is_valid_json(user_profile):
            raise InvalidJsonFormatError('user_profile')
        
        if not self._is_valid_json(derived_metrics):
            raise InvalidJsonFormatError('derived_metrics')

        # ----------- Add multi-model fallback logic --------------------

        prompt_text = self.format_prompt(PROMPT_TEMPLATE, user_profile, derived_metrics)
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt_text}],
            stream=streaming,
            temperature=self.temperature or LLM_TEMP,
        )

        if not streaming:
            # Sync path: return complete content
            return stream.choices[0].message.content

        # Streaming path: return a generator
        def _stream_gen():
            if enable_testing:
                import time
                ttft_start = time.perf_counter()
                trt_start = ttft_start
                tokens_rec = 0

            for chunk in stream:
                delta = chunk.choices[0].delta
                token = getattr(delta, "content", None)
                if not token:
                    continue

                # Testing hook: capture first‐token time
                if enable_testing:
                    tokens_rec += 1
                    if tokens_rec == 1:
                        ttft_end = time.perf_counter()

                yield token

            # After streaming finishes, yield perf summary if requested
            if enable_testing:
                trt_end = time.perf_counter()
                yield {
                    "_perf": {
                        "time_to_first_token": ttft_end - ttft_start,
                        "total_response_time": trt_end - trt_start,
                        "total_tokens": tokens_rec
                    }
                }

        return _stream_gen()


    def set_llm_model(
        self,
        model: Literal[
            'Mistral_7B', 'Mistral_Small', 'Llama_3.3', 'DeepSeek_R1',
            'Qwen_A3B', 'InternVL3', 'Nous_DeepHermes', 'Microsoft_Phi4',
            'DeepSeek_V3', 'Nvidia_Nemotron'
        ] = 'Mistral_7B'
    ):

        chosen = self.model_map.get(model)
        if not chosen:
            # fallback to default if somehow model not in map
            chosen = self.model_map['Mistral_7B']
        self.model = chosen
