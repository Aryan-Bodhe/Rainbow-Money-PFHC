# from dataclasses import dataclass
from pydantic import BaseModel
# @dataclass
class InsuranceData(BaseModel):
    total_medical_cover: int
    total_term_cover: int
