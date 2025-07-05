from models.BenchmarkData import BenchmarkData
from models.DerivedMetrics import PersonalFinanceMetrics, Metric
from models.FeedbackData import FeedbackData, CommendablePoint, ImprovementPoint
from models.UserProfile import UserProfile
from core.exceptions import FeedbackGenerationFailedError
from templates.feedback_templates.areas_for_improvement_templates import AREAS_FOR_IMPROVEMENT
from templates.feedback_templates.commendable_areas_template import COMMENDABLE_AREAS
from templates.feedback_templates.header_templates import HEADER_TEMPLATES
from random import choice
from typing import Union
from data.ideal_benchmark_data import IDEAL_RANGES
from .user_segment_classifier import classify_income_bracket, classify_city_tier
import json
import re
from config.config import MEDICAL_COVER_FACTOR, TERM_COVER_FACTOR

class FinancialAnalysisEngine:
    def __init__(self):
        self.user_profile: UserProfile = None
        self.derived_metrics: PersonalFinanceMetrics = None
        self.benchmark_data: BenchmarkData = None
        self.good_labels = ['good', 'excellent']
        self.bad_labels = ['extremely_low', 'extremely_high', 'low', 'high']
        self.header_templates = HEADER_TEMPLATES

    def analyse(self, user_profile: UserProfile, pfm: PersonalFinanceMetrics, benchmark_data: BenchmarkData):
        judged_metrics = self.generate_metric_verdicts(pfm, benchmark_data)
        with open('temp1.json', 'w') as f:
            json.dump(judged_metrics.model_dump(), f, indent=2)

        scored_metrics = self.score_metrics(judged_metrics, benchmark_data)
        with open('temp2.json', 'w') as f:
            json.dump(scored_metrics.model_dump(), f, indent=2)

        feedback_data = self.generate_feedbacks(user_profile, scored_metrics, benchmark_data)
        return feedback_data

    def filter_metrics_by_names(self):
        comm_metrics, impr_metrics = [], []
        for name, metric in self.derived_metrics.model_dump().items():
            if isinstance(metric, dict) and 'verdict' in metric:
                if metric['verdict'] in self.good_labels:
                    comm_metrics.append(name)
                elif metric['verdict'] in self.bad_labels:
                    impr_metrics.append(name)
        return comm_metrics, impr_metrics

    def generate_metric_verdicts(self, pfm: PersonalFinanceMetrics, benchmark_data: BenchmarkData):
        if pfm is None:
            raise ValueError("Metrics not Provided.")

        benchmarks = benchmark_data.model_dump()
        metrics = pfm.model_copy(deep=True)

        low_relax_stage_1 = 0.85
        high_relax_stage_1 = 1.15
        low_relax_stage_2 = 0.7
        high_relax_stage_2 = 1.3

        for key, (bm_low, bm_high) in benchmarks.items():
            metric_obj = getattr(metrics, key, None)

            if not isinstance(metric_obj, Metric):
                continue  # Skip if not a Metric field

            user_val = metric_obj.value
            if user_val is None or user_val == 999:
                metric_obj.verdict = "error_computing_metric"
                continue

            if user_val < bm_low * low_relax_stage_2:
                verdict = "extremely_low"
            elif user_val < bm_low * low_relax_stage_1:
                verdict = "low"
            elif user_val < bm_low:
                verdict = "good"
            elif user_val < bm_high:
                verdict = "excellent"
            elif user_val < bm_high * high_relax_stage_1:
                verdict = "good"
            elif user_val < bm_high * high_relax_stage_2:
                verdict = "high"
            else:
                verdict = "extremely_high"

            metric_obj.verdict = verdict
        
        return metrics

    def analyse_asset_allocation(self) -> str:
        return 'assets_analysed'

    def _generate_feedback_header(self, metric: Metric) -> str:
        mode = 'good' if metric.verdict in self.good_labels else 'bad'
        if metric.metric_name == 'asset_allocation':
            return self.analyse_asset_allocation()
        if metric.metric_name.endswith('ratio'):
            tmpl = self.header_templates['ratio_headers'][mode]
        elif metric.metric_name.endswith('adequacy'):
            tmpl = self.header_templates['adequacy_headers'][mode]
        else:
            tmpl = self.header_templates['asset_allocation_headers'][mode]
        tmp = choice(tmpl)    
        metric_name_readable = ' '.join(metric.metric_name.split(sep='_')).title()
        header = tmp.format(metric_name=metric_name_readable)
        # print(header)
        return header
    
    def generate_feedbacks(
        self,
        user_profile: UserProfile,
        derived_metrics: PersonalFinanceMetrics,
        benchmark_data: BenchmarkData
    ) -> FeedbackData:
        
        if not all([user_profile, derived_metrics, benchmark_data]):
            raise FeedbackGenerationFailedError()
        self.user_profile = user_profile
        self.derived_metrics = derived_metrics
        self.benchmark_data = benchmark_data

        # self.derived_metrics = self.generate_metric_verdicts(self.derived_metrics, self.benchmark_data)
        good_metrics, bad_metrics = self.filter_metrics_by_names()

        good_points = []
        bad_points = []

        for metric_name in good_metrics:
            metric_data = getattr(derived_metrics, metric_name)
            feedback = self._create_commend_point(metric_data)
            good_points.append((metric_name, feedback))

        for metric_name in bad_metrics:
            metric_data = getattr(derived_metrics, metric_name)
            feedback = self._create_improvement_point(metric_data)
            bad_points.append((metric_name, feedback))
        
        # print(good_points)
        # print(bad_points)

        sorted_good = self._sort_points(good_points)
        sorted_bad  = self._sort_points(bad_points)

        return FeedbackData(
            commendable_points=[pt for _, pt in sorted_good],
            improvement_points=[pt for _, pt in sorted_bad]
        )

    def _create_commend_point(self, metric: Metric) -> CommendablePoint:
        # metric: Metric = getattr(self.derived_metrics, metric_name)
        min_b, max_b = getattr(self.benchmark_data, metric.metric_name)
        formatted = self._get_formatted_commend_point(metric, min_b, max_b)
        # print(formatted)
        return CommendablePoint(
            metric_name=metric.metric_name,
            header=self._generate_feedback_header(metric),
            current_scenario=formatted['current_scenario']
        )

    def _create_improvement_point(self, metric: Metric) -> ImprovementPoint:
        # metric = getattr(self.derived_metrics, metric.metric_name)
        min_b, max_b = getattr(self.benchmark_data, metric.metric_name)

        gap_amt = self._compute_gap(metric, min_b, max_b)
        formatted = self._get_formatted_improvement_point(metric, gap_amt, min_b, max_b)
        # formatted = self._format_feedback(template, metric.value, min_b, max_b, gap)
        return ImprovementPoint(
            metric_name=metric.metric_name,
            header=self._generate_feedback_header(metric),
            current_scenario=formatted.get('current_scenario'),
            actionable=formatted.get('actionable')
        )

    def _compute_gap(
        self, metric: Metric, min_b: float, max_b: float
    ) -> float:
        base = {
            'income': self.derived_metrics.total_monthly_income,
            'expense': self.derived_metrics.total_monthly_expense + self.derived_metrics.total_monthly_emi,
            'corpus': self.derived_metrics.target_retirement_corpus,
            'assets': self.derived_metrics.total_assets,
            'liabilities': self.derived_metrics.total_liabilities,
            'total_medical_cover': self.user_profile.insurance_data.total_medical_cover,
            'total_term_cover': self.user_profile.insurance_data.total_term_cover
        }
        MIN_THRESH = 1000
        try:
            if metric.metric_name in {
                'savings_income_ratio','investment_income_ratio',
                'expense_income_ratio','housing_income_ratio'
            }:
                gap_vals = [abs((min_b - metric.value)*base['income']), abs((max_b - metric.value)*base['income'])]
            elif metric.metric_name in {'emergency_fund_ratio','liquidity_ratio'}:
                gap_vals = [abs((min_b - metric.value)*base['expense']), abs((max_b - metric.value)*base['expense'])]
            elif metric.metric_name == 'retirement_adequacy':
                years_left = self.user_profile.personal_data.expected_retirement_age - self.user_profile.personal_data.age
                monthly_factor = max(1, 12 * years_left)
                gap_vals = [abs((min_b - metric.value)*base['corpus']) / monthly_factor, abs((max_b - metric.value)*base['corpus']) / monthly_factor] 
            elif metric.metric_name == 'asset_liability_ratio':
                low_liab = base['assets']/ (min_b or 1)
                high_liab= base['assets']/ (max_b or 1)
                gap_vals = [abs(base['liabilities'] - low_liab), abs(base['liabilities'] - high_liab)]
            elif metric.metric_name == 'health_insurance_adequacy':
                gap_vals = [abs(1 - metric.value) * MEDICAL_COVER_FACTOR]
            elif metric.metric_name == 'term_insurance_adequacy':
                gap_vals = [abs(1 - metric.value) * TERM_COVER_FACTOR]
                
            else:
                return MIN_THRESH
            return max(min(gap_vals), MIN_THRESH)
        except ZeroDivisionError:
            return MIN_THRESH

    def _get_formatted_commend_point(self, metric: Metric, min_b: float, max_b: float):
        template = COMMENDABLE_AREAS.get(metric.metric_name)
        if not template:
            return {
                'current_scenario': 'Metric values are well within ideal ranges. Great work!'
            }
        template = template.get(metric.verdict)
        # print(template)
        curr_scnr = template.get('current_scenario')
        # print(curr_scnr)

        return {
            'current_scenario': curr_scnr.format(user_value=metric.value)
        }

    def _get_formatted_improvement_point(self, metric: Metric, gap_amt: float, min_b: float, max_b: float):
        template = AREAS_FOR_IMPROVEMENT.get(metric.metric_name)

        if not template:
            template = {
                "current_scenario": "Metric value is far from ideal. Optimize for a healthier financial future.",
            }

        template = template.get(metric.verdict)

        curr_scnr = template.get('current_scenario')
        action = template.get('actionable')
        places = re.findall(r'{(\w+)[^}]*}', action)
        ctx = {
            'gap_amt': gap_amt,
            'min_val': min_b,
            'max_val': max_b
        }

        filtered_ctx = {k: v for k, v in ctx.items() if k in places}

        
        return {
            'current_scenario': curr_scnr.format(user_value=metric.value),
            'actionable': action.format_map(filtered_ctx)
        }

    def _format_feedback(
        self,
        tpl: dict[str, str],
        value: float,
        min_b: float,
        max_b: float,
        gap: float = None
    ) -> dict[str, str]:
        ctx = {'user_value': value, 'benchmark_min': min_b, 'benchmark_max': max_b}
        if gap is not None and '{gap_amt' in tpl.get('actionable', ''):
            ctx['gap_amt'] = gap
        try:
            current = tpl['current_scenario'].format(user_value=value)
            actionable_template = tpl.get('actionable', '')
            actionable = actionable_template.format(
                **{k: v for k, v in ctx.items() if f'{{{k}' in actionable_template}
            )
            return {'current_scenario': current, 'actionable': actionable}
        except Exception:
            return {
                'current_scenario': 'Unable to generate feedback.',
                'actionable': 'Please check configuration.'
            }

    def _sort_points(
        self, 
        named_points: list[tuple[str, Union[CommendablePoint, ImprovementPoint]]]
    ) -> list[tuple[str, Union[CommendablePoint, ImprovementPoint]]]:
        age = self.user_profile.personal_data.age
        if age < 30:
            priority = ['emergency_fund_ratio','expense_income_ratio','savings_income_ratio',
                        'debt_income_ratio','liquidity_ratio','investment_income_ratio']
        elif age < 45:
            priority = ['emergency_fund_ratio','health_insurance_adequacy','term_insurance_adequacy',
                        'savings_income_ratio','retirement_adequacy']
        elif age < 60:
            priority = ['retirement_adequacy','net_worth_adequacy','asset_liability_ratio',
                        'liquidity_ratio']
        else:
            priority = ['liquidity_ratio','asset_liability_ratio','emergency_fund_ratio']
        order = {m:i for i,m in enumerate(priority)}
        return sorted(named_points, key=lambda x: order.get(x[0], len(order)))

    def score_metrics(
        self,
        metrics: PersonalFinanceMetrics,
        benchmark_data: BenchmarkData,
    ) -> PersonalFinanceMetrics:

        pfm = metrics.model_copy(deep=True)
        # tier_key = f"Tier {pfm.city_tier}"
        # bracket = classify_income_bracket(pfm.total_monthly_income)

        for metric_name in metrics.model_fields:
            if not metric_name.endswith('ratio') or metric_name.endswith('adequacy'):
                continue
            benchmark = getattr(benchmark_data, metric_name)
            if benchmark is None:
                print(f"[WARNING] Skipping unknown metric for scoring '{metric_name}'")
                continue
            
            min_i, max_i = benchmark

            metric_obj = getattr(pfm, metric_name, None)
            if not isinstance(metric_obj, Metric):
                print(f"[WARN] Metric '{metric_name}' not found or invalid.")
                continue
            metric_data = getattr(pfm, metric_name)
            score = self._score_value(metric_obj, min_i, max_i, getattr(metric_data, 'weight'))
            metric_obj.assigned_score = round(score)
        
        return pfm

    def _score_value(self, metric: Metric, ideal_min: float, ideal_max: float, max_score: float) -> float:
        """
        Compute score for a metric based on its value vs benchmark range.
        """
        val = metric.value
        if val is None or max_score == 0:
            return 0.0
        if ideal_min <= val <= ideal_max:
            return max_score
        ratio = val / ideal_min if val < ideal_min else ideal_max / val
        return max_score * (0.2 + 0.8 * max(0.0, min(1.0, ratio)))
