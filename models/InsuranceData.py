from pydantic import BaseModel

class InsuranceData(BaseModel):
    total_medical_cover: int
    total_term_cover: int
