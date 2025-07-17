from pydantic import BaseModel
from typing import List, Optional, Any

class LLMResponse(BaseModel):
    content: dict
    metadata: dict[str, Any]
