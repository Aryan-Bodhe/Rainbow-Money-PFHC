# Personal Finance Health Calculator

## Inputs
1. Personal Data
    - Age
    - Gender
    - City Tier (input city name, then classify)
    - Marital Status
    - No of dependents
    - Expected Retirement Age
    - Risk Profile (Dropdown)

2. Income Data (Monthly)
    - Salaried Income
    - Business Income
    - Freelance Income
    - Investment Returns 
    - Rental Income

3. Expense Data (Monthly)
    - Groceries & Essentials
    - Bills and Utilities
    - Health Cover Premium
    - Term Cover Premium
    - Discretionary Expense

4. Assets Data (Monthly, unless specified)
    - Liquid Funds = A/C Balance (Total)
    - Equity Investment Held (Total)
    - Equity Investment Recurring
    - Debt Investment Held (Total)
    - Debt Investment Recurring
    - Retirement Funds Held (Total)
    - Retirement Funds Recurring 
    - Tax Saver Funds (Annual)
    - Real Estate Investment (Total)

5. Liabilities Data (Monthly, unless specified)
    - Credit Card Outstanding Debt (Total)
    - Credit Card EMI 
    - Personal Loan Outstanding Debt (Total)
    - Personal Loan EMI
    - Car Loan Outstanding Debt (Total)
    - Car Loan EMI
    - Student Loan Outstanding Debt (Total)
    - Student Loan EMI
    - Home Loan Outstanding Debt (Total)
    - Home Loan EMI

6. Taxation Data
    - Property Tax
    - Income Tax
    - Availed Deductions (need to be filled section wise na so as to actually tell where)

---

## Computed Metrics

**Prerequisites**

- **TotalMonthlyIncome** = Salaried Income + Business Income + Freelance Income + Investment Returns + Rental Income
- **TotalMonthlyExpenses** = Groceries & Essentials + Bills and Utilities + Health Cover Premium + Term Cover Premium + Discretionary Expense
- **TotalMonthlyEMI** = Credit Card EMI + Personal Loan EMI + Car Loan EMI + Student Loan EMI + Home Loan EMI
- **TotalAssets** = Liquid Funds + Equity Investment Held + Debt Investment Held + Retirement Funds Held + Real Estate Investment
- **TotalLiabilities** = Credit Card Outstanding Debt + Personal Loan Outstanding Debt + Car Loan Outstanding Debt + Student Loan Outstanding Debt + Home Loan Outstanding Debt
- **YearsToRetirement** = Expected Retirement Age – Age

---

1. Metric Name: **Savings Ratio**

   - Required fields: [`TotalMonthlyIncome`, `TotalMonthlyExpenses`]
   - Formula: (TotalMonthlyIncome – TotalMonthlyExpenses) / TotalMonthlyIncome × 100

2. Metric Name: **Investment‑Savings Ratio**

   - Required fields: [`TotalAssets`, `TotalMonthlyIncome`, `TotalMonthlyExpenses`]
   - Formula: TotalAssets / (TotalMonthlyIncome – TotalMonthlyExpenses)

3. Metric Name: **Debt-Income Ratio**

   - Required fields: [`TotalMonthlyEMI`, `TotalMonthlyIncome`]
   - Formula: TotalMonthlyEMI / TotalMonthlyIncome

4. Metric Name: **Emergency Fund Ratio**

   - Required fields: [`Liquid Funds`, `TotalMonthlyExpenses`]
   - Formula: Liquid Funds / TotalMonthlyExpenses

5. Metric Name: **Liquidity Ratio**

   - Required fields: [`Liquid Funds`, `TotalMonthlyEMI`]
   - Formula: Liquid Funds / TotalMonthlyEMI

6. Metric Name: **Asset‑Liability Ratio**

   - Required fields: [`TotalAssets`, `TotalLiabilities`]
   - Formula: TotalAssets / TotalLiabilities

7. Metric Name: **Health Insurance Adequacy**

   - Required fields: [`Health Cover Premium`, `TotalMonthlyIncome`]
   - Formula: (Health Cover Premium × 12) / (TotalMonthlyIncome × 12)

8. Metric Name: **Term Insurance Adequacy**

   - Required fields: [`Term Cover Premium`, `TotalMonthlyIncome`]
   - Formula: (Term Cover Premium × 12) / (TotalMonthlyIncome × 12)

9. Metric Name: **Asset Distribution**

   - Required fields: [`Liquid Funds`, `Equity Investment Held`, `Debt Investment Held`, `Retirement Funds Held`, `Real Estate Investment`, `TotalAssets`]
   - Formula:

     - Liquid share = Liquid Funds / TotalAssets
     - Equity share = Equity Investment Held / TotalAssets
     - Debt share = Debt Investment Held / TotalAssets
     - Retirement share = Retirement Funds Held / TotalAssets
     - Real estate share = Real Estate Investment / TotalAssets

10. Metric Name: **Housing‑Income Ratio**

    - Required fields: [`Home Loan EMI`, `TotalMonthlyIncome`]
    - Formula: Home Loan EMI / TotalMonthlyIncome

11. Metric Name: **Expense‑Income Ratio**

    - Required fields: [`TotalMonthlyExpenses`, `TotalMonthlyIncome`]
    - Formula: TotalMonthlyExpenses / TotalMonthlyIncome

12. Metric Name: **Net Worth Adequacy**

    - Required fields: [`TotalAssets`, `TotalLiabilities`, `TotalMonthlyIncome`]
    - Formula: (TotalAssets – TotalLiabilities) / (TotalMonthlyIncome × 12)

13. Metric Name: **Tax Efficiency**

    - Required fields: [`Income Tax`, `TotalMonthlyIncome`]
    - Formula: 1 – (Income Tax / (TotalMonthlyIncome × 12))

14. Metric Name: **Retirement Adequacy**

    - Required fields: [`Retirement Funds Held`, `YearsToRetirement`, `TotalMonthlyIncome`]
    - Formula: Retirement Funds Held / (YearsToRetirement × TotalMonthlyIncome × 12)


- Unused input fields : [`Gender`, `Marital Status`, `Risk Profile`, `Equity Investment Recurring`, `Debt Investment Recurring`, `Retirement Funds Recurring`, `Tax Saver Funds`, `No of Dependents`, `Property Tax`, `Availed Deductions`]

---

## Analysis Questions

1. Question: Is the user’s Expense‑Income Ratio ≤ 0.35?
   Fields: [`Expense‑Income Ratio`]
   Actionable: If > 0.35 → recommend reducing non‑essential spending categories

2. Question: Is the user’s recurring investment rate ≥ 0.10?
   Fields: [`Equity Investment Recurring`, `Debt Investment Recurring`, `Retirement Funds Recurring`, `TotalMonthlyIncome`]
   Actionable: If < 0.10 → recommend setting up or increasing automated SIPs

3. Question: Is the user’s Total Monthly Savings ≥ 15% of income?
   Fields: [`Savings%`]
   Actionable: If < 15% → recommend automating a higher savings transfer or payroll deduction

4. Question: Is the user’s Liquidity Ratio ≥ 1?
   Fields: [`Liquidity Ratio`]
   Actionable: If < 1 → recommend boosting liquid buffer or reducing EMI commitments

5. Question: Is the user’s Asset‑Liability Ratio ≥ 1.5?
   Fields: [`Asset‑Liability Ratio`]
   Actionable: If < 1.5 → recommend accelerating debt repayment or growing asset allocations

6. Question: Is the user’s Housing‑Income Ratio ≤ 0.30?
   Fields: [`Housing‑Income Ratio`]
   Actionable: If > 0.30 → recommend refinancing home loan or exploring rental income options

7. Question: Is the user’s DTI ≤ 0.30?
   Fields: [`DTI`]
   Actionable: If > 0.30 → recommend debt restructuring, tenor extension, or prioritizing high‑interest debt paydown

8. Question: Is the user’s EFR ≥ 3?
   Fields: [`EFR`]
   Actionable: If < 3 → recommend building emergency fund via small, regular transfers

9. Question: Is the user’s Savings% ≥ tier‑adjusted target?
   Fields: [`Savings%`, `City Tier`]
   Actionable: If below target → recommend increasing automated savings (higher SIP or payroll deduction)

10. Question: Does any expense category exceed 30% of TotalMonthlyExpenses?
    Fields: [`Groceries & Essentials`, `Bills and Utilities`, `Discretionary Expense`, `TotalMonthlyExpenses`]
    Actionable: If yes → recommend capping that category to a fixed monthly budget

11. Question: Is the user’s Health Insurance Adequacy ≥ 0.05 (5% of income)?
    Fields: [`Health Insurance Adequacy`]
    Actionable: If < 0.05 → recommend increasing health cover sum‑insured or adding riders

12. Question: Is the user’s Term Insurance Adequacy ≥ 0.05 (5% of income)?
    Fields: [`Term Insurance Adequacy`]
    Actionable: If < 0.05 → recommend increasing term cover or extending coverage term

13. Question: Is the user’s Retirement Adequacy ≥ 1?
    Fields: [`Retirement Adequacy`]
    Actionable: If < 1 → recommend boosting retirement contributions or shifting to higher‑growth funds

14. Question: Is the user’s Tax Efficiency ≥ 0.75?
    Fields: [`Tax Efficiency`]
    Actionable: If < 0.75 → recommend utilizing unused deductions under Sections 80C/80D/80E

15. Question: Is the user’s Investment‑Savings Ratio ≤ 5?
    Fields: [`Investment‑Savings Ratio`]
    Actionable: If > 5 → recommend prioritizing savings buildup before new investments

16. Question: Is the user’s Asset Distribution aligned with their Risk Profile?
    Fields: [`Asset Distribution`, `Risk Profile`]
    Actionable: If misaligned → recommend rebalancing toward target allocation bands

17. Question: Is the user’s Net Worth Adequacy ≥ 1?
    Fields: [`Net Worth Adequacy`]
    Actionable: If < 1 → recommend strategies to grow net worth (debt reduction or asset accumulation)

18. Question: After all EMIs and expenses, is there surplus cash available?
    Fields: [`TotalMonthlyIncome`, `TotalMonthlyExpenses`, `TotalMonthlyEMI`]
    Actionable: If surplus > 0 → recommend allocating to highest‑interest debt or equity SIPs


---


## Prompt Template
{
  "inputs": {...},
  "rules": [
    {
      "question": "Is the EMI burden below 30% of gross income?",
      "formula": "(Total_EMIs / Gross_Income) <= 0.3",
      "explanation_if_false": "High EMI burden; consider reducing loan obligations."
    },
    ...
  ]
}
