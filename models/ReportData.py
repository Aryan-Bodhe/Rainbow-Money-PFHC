from pydantic import BaseModel
from typing import List, Optional
from .DerivedMetrics import PersonalFinanceMetrics

class CommendablePoint(BaseModel):
    metric_name: Optional[str] = None
    header: Optional[str] = None
    current_scenario: Optional[str] = None

class ImprovementPoint(BaseModel):
    metric_name: Optional[str] = None
    header: Optional[str] = None
    current_scenario: Optional[str] = None
    actionable: Optional[str] = None

class ReportData(BaseModel):
    profile_review: Optional[str] = None
    commendable_areas: Optional[List[CommendablePoint]] = None
    areas_for_improvement: Optional[List[ImprovementPoint]] = None
    summary: Optional[str] = None

    glossary: Optional[dict] = None
    metrics_scoring_table: Optional[list[dict]] = None
