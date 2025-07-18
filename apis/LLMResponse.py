from pydantic import BaseModel
from typing import List, Optional, Any

class LLMResponse(BaseModel):
    content: Any
    metadata: Any
