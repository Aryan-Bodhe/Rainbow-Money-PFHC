from source.UserProfile import UserProfile
from exceptions import UserProfileNotProvidedError, InvalidFinanceParameterError
from source.Metrics import PersonalFinanceMetrics
from config import ANNUAL_INFLATION_RATE, AVG_LIFE_EXPECTANCY, RETIREMENT_CORPUS_GROWTH_RATE

class PersonalFinanceMetricsCalculator:
    def __init__(self):
        self.user_profile = None
        # self.total_monthly_income = None
        # self.total_monthly_expense = None
        # self.total_monthly_investments = None
        # self.total_monthly_emi = None
        # self.total_assets = None
        # self.total_liabilities = None


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
            value = func(user_profile)
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
            self.user_profile.asset_data.total_real_estate_investments
        )

        return total


    def _compute_total_insurance(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        total = (
            self.user_profile.insurance_data.total_medical_cover + 
            self.user_profile.insurance_data.total_term_cover
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
            self.user_profile.expense_data.term_insurance_premium + 
            self.user_profile.total_monthly_emi
        )

        return total

# --------------------------------------------------------------------------------------
            
    def _compute_savings_income_ratio(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        savings_ratio = 0
        savings = self.user_profile.total_monthly_income - self.user_profile.total_monthly_expense
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
        
        expense = self.user_profile.total_monthly_expense
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
        
        liquid = self.user_profile.asset_data.total_savings_balance + self.user_profile.asset_data.total_debt_investments
        expense = self.user_profile.total_monthly_expense

        try:
            efr = liquid / expense
            return efr
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Emergency Fund Ratio", "Expense")
        
    def _compute_liquidity_ratio(self, user_profile: UserProfile = None) -> float:
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        
        liquid = self.user_profile.asset_data.total_savings_balance + self.user_profile.asset_data.total_debt_investments
        emi = self.user_profile.total_monthly_emi 

        try:
            liquidity_ratio = liquid / emi
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
        
        net_worth = self.user_profile.total_assets - self.user_profile.total_liabilities
        annual_income = self.user_profile.total_monthly_income * 12

        try:
            nwa = net_worth / annual_income
            return nwa
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Net Worth Adequacy", "Income")
        

    def _compute_target_retirement_corpus(self, user_profile: UserProfile = None) -> float:
        # Extract inputs
        age_retire = self.user_profile.personal_data.expected_retirement_age
        years_after = AVG_LIFE_EXPECTANCY - age_retire

        # Current corpus and SIP
        C0 = self.user_profile.asset_data.total_retirement_investments
        annual_expense = self.user_profile.total_monthly_expense * 12

        # Rates
        r_nominal = RETIREMENT_CORPUS_GROWTH_RATE
        r_inflation = ANNUAL_INFLATION_RATE

        # 3) Required corpus at retirement to cover expenses for remaining years
        T = years_after
        if abs(r_nominal - r_inflation) < 1e-6:
            # Special case: equal rates
            required_corpus = annual_expense * T * (1 + r_inflation) ** (T - 1)
        else:
            required_corpus = annual_expense * ((1 + r_nominal) ** T - (1 + r_inflation) ** T) / (r_nominal - r_inflation)

        return required_corpus

    def _compute_retirement_adequacy(self, user_profile: UserProfile = None) -> float:
        # Load or set user profile
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        required_corpus = self.user_profile.target_retirement_corpus

        # Extract inputs
        age_now = self.user_profile.personal_data.age
        age_retire = self.user_profile.personal_data.expected_retirement_age
        years_to_retire = age_retire - age_now

        # Current corpus and SIP
        C0 = self.user_profile.asset_data.total_retirement_investments
        SIP_monthly = self.user_profile.asset_data.retirement_sip

        # Rates
        r_nominal = RETIREMENT_CORPUS_GROWTH_RATE
        r_inflation = ANNUAL_INFLATION_RATE

        # 1) Nominal projection to retirement
        months = years_to_retire * 12
        r_monthly = (1 + r_nominal) ** (1/12) - 1
        corpus_nominal = C0 * (1 + r_nominal) ** years_to_retire
        corpus_nominal += SIP_monthly * ((1 + r_monthly) ** months - 1) / r_monthly

        # 2) Deflate nominal corpus to real at retirement
        corpus_real = corpus_nominal / (1 + r_inflation) ** years_to_retire

        # print('Simulated Corpus :', corpus_real)

        # 4) Adequacy ratio
        try:
            ratio = corpus_real / required_corpus
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Retirement Adequacy", "Invalid rates leading to division by zero")

        return ratio
        
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
                name: value / total_assets
                for name, value in alloc.items()
            }
            return allocation
        except ZeroDivisionError:
            return InvalidFinanceParameterError("Asset Allocation", "Total Asset")

    def _simulate_retirement_corpus_growth(self, user_profile: UserProfile = None):
        ey = self.total_monthly_expense
