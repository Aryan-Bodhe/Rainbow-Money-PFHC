from pydantic import BaseModel
from typing import List, Optional

class CommendablePoint(BaseModel):
    header: str
    current_scenario: str 

class ImprovementPoint(BaseModel):
    header: str
    current_scenario: str
    actionable: str

class FeedbackData(BaseModel):
    commendable_points: Optional[List[CommendablePoint]] = None
    improvement_points: Optional[List[ImprovementPoint]] = None
