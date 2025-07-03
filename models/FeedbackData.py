from pydantic import BaseModel
from typing import List, Optional

class FeedbackPoint(BaseModel):
    header: str
    content: str 

class FeedbackData(BaseModel):
    commendable_points: Optional[List[FeedbackPoint]] = None
    improvement_points: Optional[List[FeedbackPoint]] = None
