# from dataclasses import dataclass
from pydantic import BaseModel
# @dataclass
class LiabilityData(BaseModel):
    credit_card_emi: int
    personal_loan_emi: int
    car_loan_emi: int
    student_loan_emi: int
    home_loan_emi: int
    outstanding_credit_card_balance: int
    outstanding_personal_loan_balance: int
    outstanding_car_loan_balance: int
    outstanding_student_loan_balance: int
    outstanding_home_loan_balance: int
