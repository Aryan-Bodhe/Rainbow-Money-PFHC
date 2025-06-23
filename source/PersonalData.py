# from dataclasses import dataclass
from pydantic import BaseModel
from typing_extensions import Literal

class PersonalData(BaseModel):
    age: int
    gender: Literal['Male', 'Female']
    city: str
    risk_profile: Literal['Conservative', 'Moderate', 'Aggressive']
    expected_retirement_age: int
    marital_status: Literal['Married', 'Unmarried']
    no_of_dependents: int
