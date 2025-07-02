from core.exceptions import UserProfileNotProvidedError, InvalidFinanceParameterError
from config.config import ANNUAL_INFLATION_RATE, AVG_LIFE_EXPECTANCY, RETIREMENT_CORPUS_GROWTH_RATE, RETIREMENT_EXPENSE_REDUCTION_RATE
from models.UserProfile import UserProfile
from models.DerivedMetrics import PersonalFinanceMetrics
from .user_segment_classifier import classify_city_tier

class PersonalFinanceMetricsCalculator:
    def __init__(self):
        self.user_profile = None


    def analyze_user_profile(self, user_profile: UserProfile):
        self._set_user_profile(user_profile)
        metrics = PersonalFinanceMetrics()

        self.user_profile.years_to_retirement = self._compute_years_to_retirement()
        metrics.total_assets = self.user_profile.total_assets = self._compute_total_assets()
        metrics.total_liabilities = self.user_profile.total_liabilities = self._compute_total_liabilities()
        metrics.total_monthly_emi = self.user_profile.total_monthly_emi = self._compute_total_monthly_emi()
        metrics.total_monthly_expense = self.user_profile.total_monthly_expense = self._compute_total_monthly_expense()
        metrics.total_monthly_income = self.user_profile.total_monthly_income = self._compute_total_monthly_income()
        metrics.total_monthly_investments = self.user_profile.total_monthly_investments = self._compute_total_monthly_investments()
        metrics.target_retirement_corpus = self.user_profile.target_retirement_corpus = self._compute_target_retirement_corpus()
        metrics.city_tier = classify_city_tier(user_profile.personal_data.city)

        functions = [            
            # compute ratios
            self._compute_savings_income_ratio,
            self._compute_investment_income_ratio,
            self._compute_expense_income_ratio,
            self._compute_debt_income_ratio,
            self._compute_emergency_fund_ratio,
            self._compute_liquidity_ratio,
            self._compute_asset_liability_ratio,
            self._compute_housing_income_ratio,

            # compute adequacies
            self._compute_health_insurance_adequacy,
            self._compute_term_insurance_adequacy,
            self._compute_net_worth_adequacy,
            self._compute_retirement_adequacy,

            # compute distribution
            self._compute_asset_class_distribution,
        ]

        for func in functions:
            key = func.__name__.replace('_compute_', '')
            try:
                value = func(user_profile)
            except InvalidFinanceParameterError as e:
                print(e)
                value = 999
            if isinstance(value, float):
                value = round(value, 2)
            setattr(metrics, key, value)

        return metrics


    def _set_user_profile(self, user_profile: UserProfile):
        if user_profile is None:
            raise UserProfileNotProvidedError()
        self.user_profile = user_profile


    def _compute_years_to_retirement(self, user_profile: UserProfile = None):
        curr_age = self.user_profile.personal_data.age
        retirement_age = self.user_profile.personal_data.expected_retirement_age
        return retirement_age - curr_age


    def _compute_total_assets(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.asset_data.total_debt_investments + 
            self.user_profile.asset_data.total_equity_investments + 
            self.user_profile.asset_data.total_savings_balance + 
            self.user_profile.asset_data.total_retirement_investments + 
            self.user_profile.asset_data.total_real_estate_investments +
            self.user_profile.asset_data.total_emergency_fund
        )

        return total
    
    
    def _compute_total_liabilities(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.liability_data.outstanding_car_loan_balance + 
            self.user_profile.liability_data.outstanding_credit_card_balance + 
            self.user_profile.liability_data.outstanding_home_loan_balance +
            self.user_profile.liability_data.outstanding_personal_loan_balance + 
            self.user_profile.liability_data.outstanding_student_loan_balance
        )

        return total


    def _compute_total_monthly_emi(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.liability_data.car_loan_emi + 
            self.user_profile.liability_data.credit_card_emi + 
            self.user_profile.liability_data.home_loan_emi +
            self.user_profile.liability_data.personal_loan_emi + 
            self.user_profile.liability_data.student_loan_emi
        )

        return total


    def _compute_total_monthly_investments(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.asset_data.debt_sip + 
            self.user_profile.asset_data.equity_sip +
            self.user_profile.asset_data.retirement_sip
        )

        return total


    def _compute_total_monthly_income(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.income_data.business_income +
            self.user_profile.income_data.freelance_income +
            self.user_profile.income_data.investment_returns + 
            self.user_profile.income_data.rental_income + 
            self.user_profile.income_data.salaried_income
        )

        return total


    def _compute_total_monthly_expense(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.expense_data.discretionary_expense + 
            self.user_profile.expense_data.groceries_and_essentials +
            self.user_profile.expense_data.housing_cost +
            self.user_profile.expense_data.utilities_and_bills +
            self.user_profile.expense_data.medical_insurance_premium +
            self.user_profile.expense_data.term_insurance_premium
        )

        return total

# --------------------------------------------------------------------------------------
            
    def _compute_savings_income_ratio(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        savings_ratio = 0
        savings = self.user_profile.total_monthly_income - self.user_profile.total_monthly_expense - self.user_profile.total_monthly_emi
        income = self.user_profile.total_monthly_income

        try:
            savings_ratio = savings / income
            return savings_ratio
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Savings-Income Ratio", "Income")
        

        
    def _compute_investment_income_ratio(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        investment = self.user_profile.total_monthly_investments
        income = self.user_profile.total_monthly_income

        try:
            investment_ratio = investment / income
            return investment_ratio
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Investment-Income Ratio", "Income")
        

    def _compute_expense_income_ratio(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        expense = self.user_profile.total_monthly_expense + self.user_profile.total_monthly_emi
        income = self.user_profile.total_monthly_income

        try:
            expense_ratio = expense / income
            return expense_ratio
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Expense-Income Ratio", "Income")
        
            
    def _compute_debt_income_ratio(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        debt = self.user_profile.total_monthly_emi
        income = self.user_profile.total_monthly_income

        try:
            dti = debt / income
            return dti
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Debt-Income Ratio", "Income")
        

    def _compute_emergency_fund_ratio(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        emergency = self.user_profile.asset_data.total_emergency_fund
        expense = (
            self.user_profile.total_monthly_expense + 
            self.user_profile.total_monthly_emi
        )

        try:
            efr = emergency / expense
            return efr
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Emergency Fund Ratio", "Expense")
        

    def _compute_liquidity_ratio(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        liquid = (
            self.user_profile.asset_data.total_savings_balance
        )
        expense = (
            self.user_profile.total_monthly_expense  +
            self.user_profile.total_monthly_emi
        )

        try:
            liquidity_ratio = liquid / expense
            return liquidity_ratio
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Liquidity Ratio", "Total Monthly EMI")
        

    def _compute_asset_liability_ratio(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        assets = self.user_profile.total_assets
        liabilities = self.user_profile.total_liabilities

        try:
            alr = assets / liabilities
            return alr
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Total Assets", "Total Liabilities")
        

    def _compute_housing_income_ratio(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        housing_cost = self.user_profile.expense_data.housing_cost + self.user_profile.liability_data.home_loan_emi
        income = self.user_profile.total_monthly_income

        try:
            hir = housing_cost / income
            return hir
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Housing Cost", "Income")
        

    def _compute_health_insurance_adequacy(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        health_cover = self.user_profile.insurance_data.total_medical_cover
        dep = (self.user_profile.personal_data.no_of_dependents + 1) * 500000 # 5L pp benchmark

        try:
            hia = health_cover / dep 
            return hia
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Health Insurance Adequacy", "No of Dependents")
        

    def _compute_term_insurance_adequacy(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        term_cover = self.user_profile.insurance_data.total_term_cover
        income = self.user_profile.total_monthly_income * 12 * 15    # threshold 15

        try:
            tia = term_cover / income
            return tia
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Term Insurance Adequacy", "Income")
        

    def _compute_net_worth_adequacy(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        age = self.user_profile.personal_data.age
        multiplier = 1

        if age < 30:
            multiplier = 1
        elif age < 40:
            multiplier = 2
        elif age < 50:
            multiplier = 4
        elif age < 60:
            multiplier = 6
        else:
            multiplier = 8

        net_worth = self.user_profile.total_assets - self.user_profile.total_liabilities
        annual_income = (self.user_profile.total_monthly_income * 12)
        required_net_worth = annual_income * multiplier

        try:
            nwa = net_worth / required_net_worth
            return nwa
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Net Worth Adequacy", "Income")
        

    def _compute_retirement_corpus_future_value(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        L = self.user_profile.asset_data.total_retirement_investments
        r_g = RETIREMENT_CORPUS_GROWTH_RATE
        curr_age = self.user_profile.personal_data.age
        retirement_age = self.user_profile.personal_data.expected_retirement_age
        sip = self.user_profile.asset_data.retirement_sip
        T = retirement_age - curr_age

        try:
            lumpsum_future = (L * (1 + r_g) ** T) 
            sip_future = (sip * (1 + r_g / 12) * ((1 + r_g / 12) ** (12 * T) - 1) * 12 / r_g)
            return lumpsum_future + sip_future
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("err", "err")


    def _compute_target_retirement_corpus(self, user_profile: UserProfile = None) -> dict:
       
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        present_age = self.user_profile.personal_data.age
        retirement_age = self.user_profile.personal_data.expected_retirement_age
        current_expenses = self.user_profile.total_monthly_expense + self.user_profile.total_monthly_emi

        life_expectancy = AVG_LIFE_EXPECTANCY
        inflation = ANNUAL_INFLATION_RATE * 100
        post_retirement_return = RETIREMENT_CORPUS_GROWTH_RATE * 100
        expense_reduction = RETIREMENT_EXPENSE_REDUCTION_RATE


        # Input validation
        if present_age >= retirement_age:
            raise ValueError("Retirement age must be greater than present age.")
        if retirement_age >= life_expectancy:
            raise ValueError("Life expectancy must be greater than retirement age.")
        if expense_reduction < 0 or expense_reduction > 50:
            raise ValueError("Expense reduction must be between 0% and 50%.")

        # Calculate future expenses at retirement (adjusted for inflation)
        years_to_retirement = retirement_age - present_age
        future_expenses = current_expenses * (1 + inflation / 100) ** years_to_retirement

        # Apply expense reduction in retirement
        retirement_expenses = future_expenses * (1 - expense_reduction / 100)

        # Calculate real rate of return (adjusting post-retirement returns for inflation)
        real_return = ((1 + post_retirement_return / 100) / (1 + inflation / 100)) - 1

        # Calculate required retirement corpus (PV of annuity due)
        retirement_years = life_expectancy - retirement_age
        if abs(real_return) < 1e-6:  # Handle near-zero real return
            target_corpus = retirement_expenses * retirement_years * 12  # Monthly payouts
        else:
            target_corpus = retirement_expenses * (1 - (1 + real_return / 12) ** (-retirement_years * 12)) / (real_return / 12)

        return round(target_corpus)


    def _compute_retirement_adequacy(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        retirement_inv_fut_val = self._compute_retirement_corpus_future_value()
        target_retirement_corpus = self._compute_target_retirement_corpus()

        try:
            retadq = retirement_inv_fut_val / target_retirement_corpus
            return retadq
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Err", "Err")


    def _compute_asset_class_distribution(self, user_profile: UserProfile = None) -> dict:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        total_assets = self.user_profile.total_assets
        alloc = {
            "liquid": self.user_profile.asset_data.total_savings_balance,
            "equity": self.user_profile.asset_data.total_equity_investments,
            "debt": self.user_profile.asset_data.total_debt_investments,
            "retirement": self.user_profile.asset_data.total_retirement_investments,
            "real_estate": self.user_profile.asset_data.total_real_estate_investments
        }

        try:
            allocation = {
                name: round(value / total_assets, 2)
                for name, value in alloc.items()
            }
            return allocation
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Asset Allocation", "Total Asset")
