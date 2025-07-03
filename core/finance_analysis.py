from ..models.BenchmarkData import BenchmarkData
from ..models.DerivedMetrics import PersonalFinanceMetrics, Metric
from ..models.FeedbackData import FeedbackData, FeedbackPoint
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

    def generate_feedback_for_metric(self, metric_name: str, metric_data: Metric):
        if metric_data is None:
            return None
        
        unformatted_feedback = None

        if metric_data.verdict in self.good_labels:
            unformatted_feedback = COMMENDABLE_AREAS.get(metric_name).get(metric_data.verdict)
        elif metric_data.verdict in self.bad_labels:
            unformatted_feedback = AREAS_FOR_IMPROVEMENT.get(metric_name).get(metric_data.verdict)

        if unformatted_feedback is not None:
            remedy_value = self.compute_remedial_amounts()
            formatted_feedback = self.format_suggestion(user_value=metric_data.value, remedy_value=remedy_value)
            header = self.generate_feedback_header(metric_name, metric_data)
            feedback_point = FeedbackPoint(header=header, content=formatted_feedback)

        return feedback_point
    
    def analyse_asset_allocation(self):
        pass

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


    def compute_remedial_amounts(self):
        return 0 # NOT IMPLEMENTED

    def format_feedback(self, feedback:str, user_value: float, remedy_value: float):
        feedback.format(user_val=user_value, remedy_val=remedy_value)
        return feedback