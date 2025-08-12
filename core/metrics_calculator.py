"""
Personal finance metrics calculator.

This module provides `PersonalFinanceMetricsCalculator`, a class that computes a
set of derived personal finance metrics from a `UserProfile` object. These
derived metrics include various ratios (savings/income, expense/income, debt/income,
liquidity, emergency fund, etc.), adequacy measures (health insurance, term insurance,
net worth, retirement adequacy) and auxiliary aggregates (total assets, total liabilities,
monthly income/expenses/investments, target retirement corpus, asset class distribution).

The calculator:
- Validates that a `UserProfile` is supplied.
- Aggregates totals from asset, liability, income and expense sections.
- Computes benchmark-ready Metric objects (value + benchmark) for downstream engines.
- Raises domain-specific exceptions when required inputs are missing or when invalid
  arithmetic conditions occur (e.g., division by zero is wrapped as `InvalidFinanceParameterError`).

Note
----
This module depends on:
- `IDEAL_RANGES` from `data.ideal_benchmark_data` for benchmark resolution.
- `classify_city_tier` and `classify_income_bracket` for segmenting users.
- Several configuration constants from `config.config`.
"""
from core.exceptions import UserProfileNotProvidedError, InvalidFinanceParameterError
from data.ideal_benchmark_data import IDEAL_RANGES
from models.UserProfile import UserProfile
from models.DerivedMetrics import PersonalFinanceMetrics, Metric
from .user_segment_classifier import classify_city_tier, classify_income_bracket
from utils.logger import get_logger
from config.config import (
    ANNUAL_INFLATION_RATE,
    AVG_LIFE_EXPECTANCY,
    RETIREMENT_CORPUS_GROWTH_RATE,
    RETIREMENT_EXPENSE_REDUCTION_RATE,
    MEDICAL_COVER_FACTOR,
    TERM_COVER_FACTOR,
)


class PersonalFinanceMetricsCalculator:
    """
    Calculate derived personal finance metrics from a user's profile.

    The class holds transient state while computing metrics:
    - `user_profile`: the input UserProfile instance
    - aggregated totals (assets, liabilities, income, expense, investments, emi)
    - computed target retirement corpus and years to retirement

    Typical usage
    -------------
    calc = PersonalFinanceMetricsCalculator()
    metrics = calc.compute_personal_finance_metrics(user_profile)

    The returned `metrics` is a `PersonalFinanceMetrics` object whose attributes
    are `Metric` instances with `.metric_name`, `.value`, and `.benchmark`.
    """

    def __init__(self):
        """
        Initialize an empty PersonalFinanceMetricsCalculator.

        No parameters. The instance is populated once `compute_personal_finance_metrics`
        is called with a valid `UserProfile`.
        """
        self.user_profile = None
        self.target_retirement_corpus = 0
        self.years_to_retirement = 0
        self.total_monthly_income = 0
        self.total_monthly_expense = 0
        self.total_monthly_investments = 0
        self.total_monthly_emi = 0
        self.total_assets = 0
        self.total_liabilities = 0

    def compute_personal_finance_metrics(self, user_profile: UserProfile):
        """
        Compute and return derived personal finance metrics for a user.

        This high-level method:
        - Validates and sets the user profile,
        - Computes aggregate totals (assets, liabilities, income, expenses, EMIs, investments),
        - Computes the retirement corpus target and city tier,
        - Computes a range of ratio and adequacy metrics and wraps each as a `Metric`.

        Parameters
        ----------
        user_profile : UserProfile
            Input user profile containing asset, liability, income, expense,
            insurance and personal information.

        Returns
        -------
        PersonalFinanceMetrics
            Container whose attributes are `Metric` objects (metric_name, value, benchmark).

        Raises
        ------
        UserProfileNotProvidedError
            If `user_profile` is None or not provided.
        """
        self._set_user_profile(user_profile)
        metrics = PersonalFinanceMetrics()

        self.years_to_retirement = self._compute_years_to_retirement()
        metrics.total_assets = self.total_assets = self._compute_total_assets()
        metrics.total_liabilities = self.total_liabilities = self._compute_total_liabilities()
        metrics.total_monthly_emi = self.total_monthly_emi = self._compute_total_monthly_emi()
        metrics.total_monthly_expense = self.total_monthly_expense = self._compute_total_monthly_expense()
        metrics.total_monthly_income = self.total_monthly_income = self._compute_total_monthly_income()
        metrics.total_monthly_investments = self.total_monthly_investments = self._compute_total_monthly_investments()
        metrics.target_retirement_corpus = self.target_retirement_corpus = self._compute_target_retirement_corpus()
        metrics.city_tier = classify_city_tier(user_profile.personal_data.city)
        metrics.asset_class_distribution = self._compute_asset_class_distribution()

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
        ]

        # computing exclusively ratios only
        for func in functions:
            key = func.__name__.replace("_compute_", "")

            try:
                value = func(user_profile)
            except InvalidFinanceParameterError as e:
                # print(e)
                get_logger().warning(e)
                value = 999

            value = round(value, 2)
            bm = self._get_benchmark_for_metric(key, metrics)
            metric_obj = Metric(metric_name=key, value=value, benchmark=bm)
            setattr(metrics, key, metric_obj)

        return metrics

    def _get_benchmark_for_metric(self, metric_name: str, pfm: PersonalFinanceMetrics) -> tuple:
        """
        Retrieve the benchmark (min, max) for a given metric.

        Benchmarks are resolved from `IDEAL_RANGES` using:
        - The user's city tier (`pfm.city_tier`) as "Tier X"
        - The income bracket classified by `classify_income_bracket`

        Parameters
        ----------
        metric_name : str
            The metric key/name to fetch a benchmark for (e.g. 'savings_income_ratio').
        pfm : PersonalFinanceMetrics
            Currently-building metrics object which provides `city_tier` and `total_monthly_income`.

        Returns
        -------
        tuple or None
            (min, max) benchmark tuple if available, otherwise None.

        Notes
        -----
        - If no entry exists in `IDEAL_RANGES` for `metric_name`, None is returned.
        """
        if not metric_name:
            return

        tier_key = f"Tier {pfm.city_tier}"
        bracket = classify_income_bracket(pfm.total_monthly_income)

        ideal = IDEAL_RANGES.get(metric_name)
        if ideal is None:
            return  # No benchmark defined

        if isinstance(ideal, dict):
            min_i, max_i = ideal.get(tier_key, {}).get(bracket, (None, None))
        else:
            min_i, max_i = ideal

        if min_i is not None and max_i is not None:
            return (min_i, max_i)
        return None

    def _set_user_profile(self, user_profile: UserProfile):
        """
        Set and validate the user profile for computations.

        Parameters
        ----------
        user_profile : UserProfile
            The input profile to be used for subsequent metric computations.

        Raises
        ------
        UserProfileNotProvidedError
            If `user_profile` is None.
        """
        if user_profile is None:
            raise UserProfileNotProvidedError()
        self.user_profile = user_profile

    def _compute_years_to_retirement(self, user_profile: UserProfile = None):
        """
        Compute years remaining until retirement.

        Parameters
        ----------
        user_profile : UserProfile, optional
            Optional user_profile parameter (method uses internal `self.user_profile`).

        Returns
        -------
        int
            Number of years left until expected retirement age.
        """
        curr_age = self.user_profile.personal_data.age
        retirement_age = self.user_profile.personal_data.expected_retirement_age
        return retirement_age - curr_age

    def _compute_total_assets(self, user_profile: UserProfile = None) -> float:
        """
        Sum and return total assets from the user profile.

        Parameters
        ----------
        user_profile : UserProfile, optional
            Optional user_profile parameter. If provided, the internal profile will be set.

        Returns
        -------
        float
            Total asset value aggregated from multiple fields.

        Raises
        ------
        UserProfileNotProvidedError
            If no profile is available to compute totals.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.asset_data.total_debt_investments
            + self.user_profile.asset_data.total_equity_investments
            + self.user_profile.asset_data.total_savings_balance
            + self.user_profile.asset_data.total_retirement_investments
            + self.user_profile.asset_data.total_real_estate_investments
            + self.user_profile.asset_data.total_emergency_fund
        )

        return total

    def _compute_total_liabilities(self, user_profile: UserProfile = None) -> float:
        """
        Sum and return total liabilities from the user profile.

        Parameters
        ----------
        user_profile : UserProfile, optional

        Returns
        -------
        float
            Total liabilities aggregated from multiple liability fields.

        Raises
        ------
        UserProfileNotProvidedError
            If no profile is available to compute totals.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.liability_data.outstanding_car_loan_balance
            + self.user_profile.liability_data.outstanding_credit_card_balance
            + self.user_profile.liability_data.outstanding_home_loan_balance
            + self.user_profile.liability_data.outstanding_personal_loan_balance
            + self.user_profile.liability_data.outstanding_student_loan_balance
        )

        return total

    def _compute_total_monthly_emi(self, user_profile: UserProfile = None) -> float:
        """
        Compute total monthly EMI payments.

        Parameters
        ----------
        user_profile : UserProfile, optional

        Returns
        -------
        float
            Sum of monthly EMIs across loan categories.

        Raises
        ------
        UserProfileNotProvidedError
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.liability_data.car_loan_emi
            + self.user_profile.liability_data.credit_card_emi
            + self.user_profile.liability_data.home_loan_emi
            + self.user_profile.liability_data.personal_loan_emi
            + self.user_profile.liability_data.student_loan_emi
        )

        return total

    def _compute_total_monthly_investments(self, user_profile: UserProfile = None) -> float:
        """
        Compute total monthly investments (SIPs and retirement SIPs).

        Parameters
        ----------
        user_profile : UserProfile, optional

        Returns
        -------
        float
            Sum of monthly investment-related cashflows.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.asset_data.debt_sip
            + self.user_profile.asset_data.equity_sip
            + self.user_profile.asset_data.retirement_sip
        )

        return total

    def _compute_total_monthly_income(self, user_profile: UserProfile = None) -> float:
        """
        Compute aggregate monthly income.

        Parameters
        ----------
        user_profile : UserProfile, optional

        Returns
        -------
        float
            Sum of salaried, business, freelance, rental and other income.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.income_data.business_income
            + self.user_profile.income_data.freelance_income
            + self.user_profile.income_data.other_sources
            + self.user_profile.income_data.rental_income
            + self.user_profile.income_data.salaried_income
        )

        return total

    def _compute_total_monthly_expense(self, user_profile: UserProfile = None) -> float:
        """
        Compute aggregate monthly expense (including insurance premiums).

        Parameters
        ----------
        user_profile : UserProfile, optional

        Returns
        -------
        float
            Sum of discretionary, groceries, housing, utilities and insurance premiums.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        total = (
            self.user_profile.expense_data.discretionary_expense
            + self.user_profile.expense_data.groceries_and_essentials
            + self.user_profile.expense_data.housing_cost
            + self.user_profile.expense_data.utilities_and_bills
            + self.user_profile.expense_data.medical_insurance_premium
            + self.user_profile.expense_data.term_insurance_premium
        )

        return total

    # --------------------------------------------------------------------------------------

    def _compute_savings_income_ratio(self, user_profile: UserProfile = None) -> float:
        """
        Compute the savings-to-income ratio.

        Formula
        -------
        savings = total_monthly_income - total_monthly_expense - total_monthly_emi
        ratio = savings / total_monthly_income

        Raises
        ------
        InvalidFinanceParameterError
            If total_monthly_income is zero (division by zero).
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        savings_ratio = 0
        savings = self.total_monthly_income - self.total_monthly_expense - self.total_monthly_emi
        income = self.total_monthly_income

        try:
            savings_ratio = savings / income
            return savings_ratio
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Savings-Income Ratio", "Income")

    def _compute_investment_income_ratio(self, user_profile: UserProfile = None) -> float:
        """
        Compute the investment (monthly investments) to income ratio.

        Raises
        ------
        InvalidFinanceParameterError
            If total_monthly_income is zero.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        investment = self.total_monthly_investments
        income = self.total_monthly_income

        try:
            investment_ratio = investment / income
            return investment_ratio
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Investment-Income Ratio", "Income")

    def _compute_expense_income_ratio(self, user_profile: UserProfile = None) -> float:
        """
        Compute expense (including EMIs) to income ratio.

        Raises
        ------
        InvalidFinanceParameterError
            If total_monthly_income is zero.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        expense = self.total_monthly_expense + self.total_monthly_emi
        income = self.total_monthly_income

        try:
            expense_ratio = expense / income
            return expense_ratio
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Expense-Income Ratio", "Income")

    def _compute_debt_income_ratio(self, user_profile: UserProfile = None) -> float:
        """
        Compute debt (EMIs) to income ratio.

        Raises
        ------
        InvalidFinanceParameterError
            If total_monthly_income is zero.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        debt = self.total_monthly_emi
        income = self.total_monthly_income

        try:
            dti = debt / income
            return dti
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Debt-Income Ratio", "Income")

    def _compute_emergency_fund_ratio(self, user_profile: UserProfile = None) -> float:
        """
        Compute the emergency fund adequacy ratio.

        Formula
        -------
        emergency_fund / (monthly_expense + monthly_emi)

        Raises
        ------
        InvalidFinanceParameterError
            If expense + EMI is zero.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        emergency = self.user_profile.asset_data.total_emergency_fund
        expense = self.total_monthly_expense + self.total_monthly_emi

        try:
            efr = emergency / expense
            return efr
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Emergency Fund Ratio", "Expense")

    def _compute_liquidity_ratio(self, user_profile: UserProfile = None) -> float:
        """
        Compute liquidity ratio as liquid assets divided by monthly obligations (expense + EMI).

        Raises
        ------
        InvalidFinanceParameterError
            If the denominator is zero.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        liquid = self.user_profile.asset_data.total_savings_balance
        expense = self.total_monthly_expense + self.total_monthly_emi

        try:
            liquidity_ratio = liquid / expense
            return liquidity_ratio
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Liquidity Ratio", "Total Monthly EMI")

    def _compute_asset_liability_ratio(self, user_profile: UserProfile = None) -> float:
        """
        Compute asset to liability ratio.

        Raises
        ------
        InvalidFinanceParameterError
            If total_liabilities is zero.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        assets = self.total_assets
        liabilities = self.total_liabilities

        try:
            alr = assets / liabilities
            return alr
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Total Assets", "Total Liabilities")

    def _compute_housing_income_ratio(self, user_profile: UserProfile = None) -> float:
        """
        Compute housing cost (rent + home loan EMI) to income ratio.

        Raises
        ------
        InvalidFinanceParameterError
            If total_monthly_income is zero.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        housing_cost = self.user_profile.expense_data.housing_cost + self.user_profile.liability_data.home_loan_emi
        income = self.total_monthly_income

        try:
            hir = housing_cost / income
            return hir
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Housing Cost", "Income")

    def _compute_health_insurance_adequacy(self, user_profile: UserProfile = None) -> float:
        """
        Compute health insurance adequacy as user coverage divided by recommended coverage per dependant.

        The recommended coverage is calculated using `MEDICAL_COVER_FACTOR` and family size.

        Raises
        ------
        InvalidFinanceParameterError
            If dependents calculation leads to zero divisor.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        health_cover = self.user_profile.insurance_data.total_medical_cover
        dep = (self.user_profile.personal_data.no_of_dependents + 1) * MEDICAL_COVER_FACTOR  # 5L pp benchmark

        try:
            hia = health_cover / dep
            return hia
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Health Insurance Adequacy", "No of Dependents")

    def _compute_term_insurance_adequacy(self, user_profile: UserProfile = None) -> float:
        """
        Compute term insurance adequacy as term cover divided by income-based threshold.

        Threshold = total_monthly_income * 12 * TERM_COVER_FACTOR.

        Raises
        ------
        InvalidFinanceParameterError
            If income-based threshold is zero.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        term_cover = self.user_profile.insurance_data.total_term_cover
        income = self.total_monthly_income * 12 * TERM_COVER_FACTOR  # threshold

        try:
            tia = term_cover / income
            return tia
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Term Insurance Adequacy", "Income")

    def _compute_net_worth_adequacy(self, user_profile: UserProfile = None) -> float:
        """
        Compute net worth adequacy relative to a required multiplier of annual income.

        Multiplier varies by age group.

        Raises
        ------
        InvalidFinanceParameterError
            If annual income is zero.
        """
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

        net_worth = self.total_assets - self.total_liabilities
        annual_income = (self.total_monthly_income * 12)
        required_net_worth = annual_income * multiplier

        try:
            nwa = net_worth / required_net_worth
            return nwa
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Net Worth Adequacy", "Income")

    def _compute_retirement_corpus_future_value(self, user_profile: UserProfile = None) -> float:
        """
        Estimate the future value of existing retirement investments and SIPs at retirement.

        Formula uses:
        - L: current lumpsum retirement investments
        - r_g: expected growth rate for retirement corpus (RETIREMENT_CORPUS_GROWTH_RATE)
        - sip: current monthly retirement SIP
        - r_i: inflation adjustment (ANNUAL_INFLATION_RATE)
        - T: years until retirement

        Returns
        -------
        float
            Projected future value of retirement investments (inflation-adjusted).

        Raises
        ------
        InvalidFinanceParameterError
            If a numerical error occurs (e.g., division by zero while computing series).
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        L = self.user_profile.asset_data.total_retirement_investments
        r_g = RETIREMENT_CORPUS_GROWTH_RATE
        r_i = ANNUAL_INFLATION_RATE
        curr_age = self.user_profile.personal_data.age
        retirement_age = self.user_profile.personal_data.expected_retirement_age
        sip = self.user_profile.asset_data.retirement_sip
        T = retirement_age - curr_age

        try:
            lumpsum_future = (L * (1 + r_g) ** T)
            sip_future = (sip * (1 + r_g / 12) * ((1 + r_g / 12) ** (12 * T) - 1) * 12 / r_g)
            final_value = (lumpsum_future + sip_future) * (1 + r_i) ** T
            return final_value
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("err", "err")

    def _compute_target_retirement_corpus(self, user_profile: UserProfile = None) -> dict:
        """
        Compute the target retirement corpus required at retirement to fund expected expenses.

        Steps
        -----
        - Project current monthly expense to retirement using inflation.
        - Apply a retirement expense reduction factor.
        - Convert post-retirement returns into a real return (adjusted for inflation).
        - Compute present value (annuity due / payout model) for retirement years.

        Parameters
        ----------
        user_profile : UserProfile, optional

        Returns
        -------
        int
            Rounded estimated target corpus required at retirement (monthly payout basis).

        Raises
        ------
        UserProfileNotProvidedError
            If user profile is missing.
        ValueError
            If present age >= retirement age, or retirement_age >= life_expectancy, or
            if expense_reduction_rate is out of expected bounds.
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)

        present_age = self.user_profile.personal_data.age
        retirement_age = self.user_profile.personal_data.expected_retirement_age
        current_expenses = self.total_monthly_expense + self.total_monthly_emi

        life_expectancy = AVG_LIFE_EXPECTANCY
        inflation = ANNUAL_INFLATION_RATE
        post_retirement_return = RETIREMENT_CORPUS_GROWTH_RATE
        expense_reduction_rate = RETIREMENT_EXPENSE_REDUCTION_RATE

        # Input validation
        if present_age >= retirement_age:
            raise ValueError("Retirement age must be greater than present age.")
        if retirement_age >= life_expectancy:
            raise ValueError("Life expectancy must be greater than retirement age.")
        if expense_reduction_rate < 0 or expense_reduction_rate > 50:
            raise ValueError("Expense reduction must be between 0% and 50%.")

        # Calculate future expenses at retirement (adjusted for inflation)
        years_to_retirement = retirement_age - present_age
        future_expenses = current_expenses * (1 + inflation) ** years_to_retirement

        # Apply expense reduction in retirement
        retirement_expenses = future_expenses * (1 - expense_reduction_rate)

        # Calculate real rate of return (adjusting post-retirement returns for inflation)
        real_return = ((1 + post_retirement_return) / (1 + inflation)) - 1

        # Calculate required retirement corpus (PV of annuity due)
        retirement_years = life_expectancy - retirement_age
        if abs(real_return) < 1e-6:  # Handle near-zero real return
            target_corpus = retirement_expenses * retirement_years * 12  # Monthly payouts
        else:
            target_corpus = retirement_expenses * (1 - (1 + real_return / 12) ** (-retirement_years * 12)) / (real_return / 12)

        return round(target_corpus)

    def _compute_retirement_adequacy(self, user_profile: UserProfile = None) -> float:
        """
        Compute retirement adequacy as the ratio of projected retirement investments' future value
        to the target retirement corpus.

        Returns
        -------
        float
            Ratio (projected_future_value / target_corpus).

        Raises
        ------
        InvalidFinanceParameterError
            If division by zero occurs while computing adequacy.
        """
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
        """
        Compute the proportional distribution of assets across major classes.

        Returns
        -------
        dict
            Mapping of asset class name -> proportion (rounded to 2 decimals).

        Raises
        ------
        InvalidFinanceParameterError
            If total assets is zero (cannot compute proportions).
        """
        if self.user_profile is None:
            if user_profile is None:
                raise UserProfileNotProvidedError()
            self._set_user_profile(user_profile=user_profile)
        total_assets = self.total_assets
        alloc = {
            "liquid": self.user_profile.asset_data.total_savings_balance,
            "equity": self.user_profile.asset_data.total_equity_investments,
            "debt": self.user_profile.asset_data.total_debt_investments,
            "retirement": self.user_profile.asset_data.total_retirement_investments,
            "real_estate": self.user_profile.asset_data.total_real_estate_investments,
        }

        try:
            allocation = {name: round(value / total_assets, 2) for name, value in alloc.items()}
            return allocation
        except ZeroDivisionError:
            raise InvalidFinanceParameterError("Asset Allocation", "Total Asset")
