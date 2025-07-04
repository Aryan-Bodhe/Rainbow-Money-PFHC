## Personal Finance Metrics Computation

### 1. Years to Retirement

```
years_to_retirement = expected_retirement_age − current_age
```

* **current\_age**: `user_profile.personal_data.age`
* **expected\_retirement\_age**: `user_profile.personal_data.expected_retirement_age`

---

### 2. Total Assets

```
total_assets =
    asset_data.total_debt_investments
  + asset_data.total_equity_investments
  + asset_data.total_savings_balance
  + asset_data.total_retirement_investments
  + asset_data.total_real_estate_investments
  + asset_data.total_emergency_fund
```

---

### 3. Total Liabilities

```
total_liabilities =
    liability_data.outstanding_car_loan_balance
  + liability_data.outstanding_credit_card_balance
  + liability_data.outstanding_home_loan_balance
  + liability_data.outstanding_personal_loan_balance
  + liability_data.outstanding_student_loan_balance
```

---

### 4. Total Monthly EMI

```
total_monthly_emi =
    liability_data.car_loan_emi
  + liability_data.credit_card_emi
  + liability_data.home_loan_emi
  + liability_data.personal_loan_emi
  + liability_data.student_loan_emi
```

---

### 5. Total Monthly Investments

```
total_monthly_investments =
    asset_data.debt_sip
  + asset_data.equity_sip
  + asset_data.retirement_sip
```

---

### 6. Total Monthly Income

```
total_monthly_income =
    income_data.business_income
  + income_data.freelance_income
  + income_data.investment_returns
  + income_data.rental_income
  + income_data.salaried_income
```

---

### 7. Total Monthly Expense

```
total_monthly_expense =
    expense_data.discretionary_expense
  + expense_data.groceries_and_essentials
  + expense_data.housing_cost
  + expense_data.utilities_and_bills
  + expense_data.medical_insurance_premium
  + expense_data.term_insurance_premium
```

---

### 8. Target Retirement Corpus

```
# Inputs
present_age = personal_data.age
retirement_age = personal_data.expected_retirement_age
current_expenses = total_monthly_expense + total_monthly_emi

years_to_retirement = retirement_age − present_age
future_expenses = current_expenses × (1 + inflation_rate) ** years_to_retirement
retirement_expenses = future_expenses × (1 − expense_reduction_rate)

real_return = ((1 + post_retirement_return) / (1 + inflation_rate)) − 1
retirement_years = life_expectancy − retirement_age

if real_return ≈ 0:
    target_corpus = retirement_expenses × retirement_years × 12
else:
    target_corpus =
      retirement_expenses ×
      (1 − (1 + real_return/12)^(−retirement_years×12))
      ÷ (real_return/12)
```

---

### 9. Savings‑Income Ratio

```
savings_income_ratio =
  (total_monthly_income
   − total_monthly_expense
   − total_monthly_emi)
  ÷ total_monthly_income
```

---

### 10. Investment‑Income Ratio

```
investment_income_ratio =
  total_monthly_investments
  ÷ total_monthly_income
```

---

### 11. Expense‑Income Ratio

```
expense_income_ratio =
  (total_monthly_expense + total_monthly_emi)
  ÷ total_monthly_income
```

---

### 12. Debt‑Income Ratio

```
debt_income_ratio =
  total_monthly_emi
  ÷ total_monthly_income
```

---

### 13. Emergency Fund Ratio

```
emergency_fund_ratio =
  asset_data.total_emergency_fund
  ÷ (total_monthly_expense + total_monthly_emi)
```

---

### 14. Liquidity Ratio

```
liquidity_ratio =
  asset_data.total_savings_balance
  ÷ (total_monthly_expense + total_monthly_emi)
```

---

### 15. Asset‑Liability Ratio

```
asset_liability_ratio =
  total_assets
  ÷ total_liabilities
```

---

### 16. Housing‑Income Ratio

```
housing_income_ratio =
  (expense_data.housing_cost + liability_data.home_loan_emi)
  ÷ total_monthly_income
```

---

### 17. Health Insurance Adequacy

```
health_insurance_adequacy =
  insurance_data.total_medical_cover
  ÷ ((no_of_dependents + 1) × 500_000)
```

* Benchmark: ₹ 500 000 per person

---

### 18. Term Insurance Adequacy

```
term_insurance_adequacy =
  insurance_data.total_term_cover
  ÷ (total_monthly_income × 12 × 15)
```

* Assumes 15 × annual income cover

---

### 19. Net Worth Adequacy

```
multiplier = {
  age < 30: 1,
  age < 40: 2,
  age < 50: 4,
  age < 60: 6,
  else: 8
}

net_worth = total_assets − total_liabilities
annual_income = total_monthly_income × 12
required_net_worth = annual_income × multiplier

net_worth_adequacy =
  net_worth
  ÷ required_net_worth
```

---

### 20. Retirement Adequacy

```
retirement_corpus_future_value =
  L × (1 + r_g)^T
  + sip × (1 + r_g/12) × ((1 + r_g/12)^(12T) − 1) × 12/r_g

retirement_adequacy =
  retirement_corpus_future_value
  ÷ target_retirement_corpus
```

* **L** = current retirement investments
* **r\_g** = RETIREMENT\_CORPUS\_GROWTH\_RATE
* **T** = years to retirement
* **sip** = monthly retirement SIP

---

### 21. Asset Class Distribution

```python
allocation = {
  "liquid": asset_data.total_savings_balance,
  "equity": asset_data.total_equity_investments,
  "debt": asset_data.total_debt_investments,
  "retirement": asset_data.total_retirement_investments,
  "real_estate": asset_data.total_real_estate_investments
}

asset_class_distribution = {
  name: round(value ÷ total_assets, 2)
  for name, value in allocation.items()
}
```

> All ratios in code are rounded to two decimals, and divisions guard against `ZeroDivisionError` by raising `InvalidFinanceParameterError`.

---