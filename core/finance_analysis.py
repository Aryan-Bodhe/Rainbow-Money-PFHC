from ..models.BenchmarkData import BenchmarkData
from ..models.DerivedMetrics import PersonalFinanceMetrics, Metric
from ..models.FeedbackData import FeedbackData, CommendablePoint, ImprovementPoint
from ..models.UserProfile import UserProfile
from .exceptions import FeedbackGenerationFailedError
from ..templates.feedback_templates.areas_for_improvement_templates import AREAS_FOR_IMPROVEMENT
from ..templates.feedback_templates.commendable_areas_template import COMMENDABLE_AREAS
from ..templates.feedback_templates.header_templates import HEADER_TEMPLATES
from random import choice
from typing_extensions import Literal

class FinancialAnalysisEngine:
    def __init__(self):
        self.user_profile: UserProfile = None
        self.derived_metrics: PersonalFinanceMetrics = None
        self.benchmark_data: BenchmarkData = None
        self.good_labels = ['good', 'excellent']
        self.bad_labels = ['extremely_low', 'extremely_high', 'low', 'high']
        self.header_templates = HEADER_TEMPLATES

    def filter_metrics_by_names(self):
        comm_metrics = []
        impr_metrics = []

        for key in self.derived_metrics.model_fields:
            value = getattr(self.derived_metrics, key)
            if isinstance(value, Metric):
                if value.verdict in self.good_labels: 
                    comm_metrics.append(key)
                elif value.verdict in self.bad_labels:
                    impr_metrics.append(key)

        return comm_metrics, impr_metrics


    def analyse_asset_allocation(self):
        raise NotImplementedError()


    def generate_feedback_header(
        self, metric_name: str, metric_data: Metric
    ) -> str | None:
        """Pick a randomized header template based on metric type and verdict."""
        mode = 'good' if metric_data.verdict in self.good_labels else 'bad'
        if metric_name == 'asset_allocation':
            return self.analyse_asset_allocation()

        if metric_name.endswith('ratio'):
            tmpl = self.header_templates['ratio_headers'][mode]
        elif metric_name.endswith('adequacy'):
            tmpl = self.header_templates['adequacy_headers'][mode]
        else:
            tmpl = self.header_templates.get('asset_allocation_headers', {}).get(mode)

        return choice(tmpl) if tmpl else None


    def generate_feedbacks(
        self, 
        user_profile: UserProfile, 
        derived_metrics: PersonalFinanceMetrics, 
        benchmark_data: BenchmarkData
    ):
        if user_profile is None or derived_metrics is None or benchmark_data is None:
            raise FeedbackGenerationFailedError()
        
        self.user_profile = user_profile
        self.derived_metrics = derived_metrics
        self.benchmark_data = benchmark_data
        good_feedbacks = bad_feedbacks = []
        good_metrics, bad_metrics = self.filter_metrics_by_names()

        # Get feedbacks for the good metrics
        for metric_name in good_metrics:
            metric_data = getattr(derived_metrics, metric_name)
            feedback = self.generate_feedback_for_metric(metric_name, metric_data)
            good_feedbacks.append(feedback)

        # Get feedbacks for the bad metrics
        for metric_name in bad_metrics:
            metric_data = getattr(derived_metrics, metric_name)
            feedback = self.generate_feedback_for_metric(metric_name, metric_data)
            bad_feedbacks.append(feedback)
        
        feedback_data = FeedbackData()
        feedback_data.commendable_points = good_feedbacks
        feedback_data.improvement_points = bad_feedbacks

        return feedback_data


    def generate_feedback_for_metric(
        self, 
        metric_name: str, 
        metric_data: Metric, 
        user_profile: UserProfile, 
        metric_benchmark: tuple[float, float]
    ) -> CommendablePoint | ImprovementPoint:
        if metric_data is None:
            return None

        feedback_header = self.generate_feedback_header(metric_name, metric_data)
        feedback_point = None
        if metric_data.verdict in self.good_labels:
            commend = self.generate_commend_point()
            feedback_point = CommendablePoint(feedback_header, commend.get('current_scenario'))
        elif metric_data.verdict in self.bad_labels:
            remedy = self.generate_remedy(user_profile, metric_name, metric_benchmark, metric_data)
            feedback_point = ImprovementPoint(feedback_header, remedy.get('current_scenario'), remedy.get('actionable'))

        return feedback_point

    def format_remedy_feedback(
        self,
        raw_template: dict[str, str],
        user_value: float,
        gap_amt: float,
        min_val: float,
        max_val: float
    ) -> dict[str, str]:
        try:
            # Format current_scenario using only user_value
            scenario = raw_template['current_scenario'].format(user_value=user_value)

            # Prepare context for actionable
            context = {
                'user_value': user_value,
                'gap_amt': gap_amt,
                'lower_bound': min_val,
                'upper_bound': max_val
            }

            # Format actionable — only pass values that exist in the string
            actionable_template = raw_template['actionable']
            if '{gap_amt' not in actionable_template:
                context.pop('gap_amt')
            if '{lower_bound' not in actionable_template:
                context.pop('lower_bound')
            if '{upper_bound' not in actionable_template:
                context.pop('upper_bound')

            actionable = actionable_template.format(**context)

            return {
                "current_scenario": scenario,
                "actionable": actionable
            }

        except Exception as e:
            print(f"Error formatting remedy template: {e}")
            return {
                "current_scenario": "Unable to generate feedback.",
                "actionable": "Please check the metric configuration."
            }
    

    # def compute_remedial_amount(
    #     self,
    #     user_profile: UserProfile,
    #     metric_name: str,
    #     metric_benchmark: tuple[float, float],
    #     user_val: float,
    # ) -> float:
    #     """
    #     Returns the absolute rupee gap (positive number) needed to move user_val
    #     into the ideal [lower_bound, upper_bound] range for the given metric.
    #     """
    #     lower_bound, upper_bound = metric_benchmark

    #     income_based = {
    #         'savings_income_ratio',
    #         'investment_income_ratio',
    #         'expense_income_ratio',
    #         'housing_income_ratio'
    #     }
    #     expense_based = {
    #         'emergency_fund_ratio',
    #         'liquidity_ratio'
    #     }

    #     if metric_name in income_based:
    #         income = user_profile.total_monthly_income
    #         # gaps (in ₹) for hitting lower or upper target ratios
    #         gap_low  = abs((lower_bound - user_val) * income)
    #         gap_high = abs((upper_bound - user_val) * income)
    #         return min(gap_low, gap_high)

    #     if metric_name in expense_based:
    #         # use total outflows (expense + emi)
    #         total_expense = user_profile.total_monthly_expense + user_profile.total_monthly_emi
    #         gap_low  = abs((lower_bound - user_val) * total_expense)
    #         gap_high = abs((upper_bound - user_val) * total_expense)
    #         return min(gap_low, gap_high)

    #     if metric_name == 'retirement_adequacy':
    #         # user_val is fraction of target corpus
    #         trc = user_profile.target_retirement_corpus
    #         gap_low  = abs((lower_bound - user_val) * trc)
    #         gap_high = abs((upper_bound - user_val) * trc)
    #         return min(gap_low, gap_high)

    #     if metric_name == 'asset_liability_ratio':
    #         # desired liabilities to hit target ratio
    #         assets = user_profile.total_assets
    #         target_liab_low  = assets / lower_bound
    #         target_liab_high = assets / upper_bound
    #         current_liab = user_profile.total_liabilities
    #         gap_low  = abs(current_liab - target_liab_low)
    #         gap_high = abs(current_liab - target_liab_high)
    #         return min(gap_low, gap_high)

    #     raise ValueError(f"Unsupported metric for remedial calculation: {metric_name!r}")
        

    def compute_remedial_amount(
        self,
        user_profile: UserProfile,
        metric_name: str,
        metric_benchmark: tuple[float, float],
        user_val: float,
        verdict: Literal['extremely_low', 'low', 'high', 'extremely_high']
    ) -> float:
        """
        Returns the absolute rupee gap (positive number) needed to move user_val
        into the ideal [lower_bound, upper_bound] range for the given metric.
        Enforces a minimum threshold of ₹1,000.
        """
        lower_bound, upper_bound = metric_benchmark
        MIN_THRESHOLD = 1000  # ₹1,000 floor to avoid noisy advice

        income_based = {
            'savings_income_ratio',
            'investment_income_ratio',
            'expense_income_ratio',
            'housing_income_ratio'
        }
        expense_based = {
            'emergency_fund_ratio',
            'liquidity_ratio'
        }

        if metric_name in income_based:
            income = user_profile.total_monthly_income
            gap_low  = abs((lower_bound - user_val) * income)
            gap_high = abs((upper_bound - user_val) * income)
            return max(min(gap_low, gap_high), MIN_THRESHOLD)

        if metric_name in expense_based:
            total_expense = user_profile.total_monthly_expense + user_profile.total_monthly_emi
            gap_low  = abs((lower_bound - user_val) * total_expense)
            gap_high = abs((upper_bound - user_val) * total_expense)
            return max(min(gap_low, gap_high), MIN_THRESHOLD)

        if metric_name == 'retirement_adequacy':
            trc = user_profile.target_retirement_corpus
            gap_low  = abs((lower_bound - user_val) * trc)
            gap_high = abs((upper_bound - user_val) * trc)
            return max(min(gap_low, gap_high), MIN_THRESHOLD)

        if metric_name == 'asset_liability_ratio':
            assets = user_profile.total_assets
            target_liab_low  = assets / lower_bound
            target_liab_high = assets / upper_bound
            current_liab = user_profile.total_liabilities
            gap_low  = abs(current_liab - target_liab_low)
            gap_high = abs(current_liab - target_liab_high)
            return max(min(gap_low, gap_high), MIN_THRESHOLD)

        raise ValueError(f"Unsupported metric for remedial calculation: {metric_name!r}")


    def generate_remedy(
        self,
        user_profile: UserProfile,
        metric_name: str,
        metric_benchmark: tuple[float, float],
        metric_data: Metric
    ) -> dict[str, str]:
        """
        Returns the filled-in improvement feedback for `metric_name` based on
        its `metric_data.verdict` (must be one of self.bad_labels).
        """
        label = metric_data.verdict
        if label not in self.bad_labels:
            raise ValueError(f"Cannot generate remedy for verdict {label!r}")

        # Unpack bounds and current value
        min_val, max_val = metric_benchmark
        user_val = metric_data.value

        # Compute the gap (amount to increase or decrease)
        gap_amt = self.compute_remedial_amount(
            user_profile=user_profile,
            metric_name=metric_name,
            metric_benchmark=metric_benchmark,
            user_val=user_val
        )

        # Fetch the raw template
        try:
            raw_tpl = AREAS_FOR_IMPROVEMENT[metric_name][label]
        except KeyError:
            raise ValueError(f"No improvement template for {metric_name!r} with verdict {label!r}")

        # Format with all four possible placeholders
        return self.format_remedy_feedback(
            raw_tpl,
            user_value=user_val,
            gap_amt=gap_amt,
            min_val=min_val,
            max_val=max_val
        )
    

    def generate_commend_point(self) -> dict[str, str]:
        raise NotImplementedError()