from pydantic import BaseModel
from typing import List, Optional

class CommendablePoint(BaseModel):
    metric_name: Optional[str] = None
    header: Optional[str] = None
    current_scenario: Optional[str] = None

class ImprovementPoint(BaseModel):
    metric_name: Optional[str] = None
    header: Optional[str] = None
    current_scenario: Optional[str] = None
    actionable: Optional[str] = None

class FeedbackData(BaseModel):
    commendable_points: Optional[List[CommendablePoint]] = None
    improvement_points: Optional[List[ImprovementPoint]] = None
