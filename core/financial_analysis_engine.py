import re
from string import capwords
from random import choice
from typing import List, Union

from core.user_segment_classifier import classify_income_bracket
from data.ideal_benchmark_data import IDEAL_RANGES
from models.DerivedMetrics import PersonalFinanceMetrics, Metric
from models.ReportData import CommendablePoint, ReviewPoint, ImprovementPoint, ReportData
from models.UserProfile import UserProfile
from config.config import MEDICAL_COVER_FACTOR, TERM_COVER_FACTOR, SCORING_BASE_VALUE
from core.exceptions import FeedbackGenerationFailedError
from templates.feedback_templates.areas_for_improvement_templates import AREAS_FOR_IMPROVEMENT
from templates.feedback_templates.commendable_areas_template import COMMENDABLE_AREAS
from templates.feedback_templates.review_areas_templates import REVIEW_AREAS
from templates.feedback_templates.header_templates import HEADER_TEMPLATES

class FinancialAnalysisEngine:
    def __init__(self):
        self.user_profile: UserProfile = None
        self.derived_metrics: PersonalFinanceMetrics = None
        self.good_labels = ['good', 'excellent']
        self.review_labels = ['high', 'extremely_high']
        self.bad_labels = ['extremely_low', 'low', 'high', 'extremely_high']
        self.metrics_analysed = []
        self.header_templates = HEADER_TEMPLATES
        self.assessment_fields = [
            'savings_income_ratio', 'investment_income_ratio', 'expense_income_ratio',
            'debt_income_ratio', 'emergency_fund_ratio', 'liquidity_ratio',
            'asset_liability_ratio', 'housing_income_ratio',
            'health_insurance_adequacy', 'term_insurance_adequacy',
            'net_worth_adequacy', 'retirement_adequacy'
        ]

    def analyse(self, user_profile: UserProfile, pfm: PersonalFinanceMetrics):
        pfm = self._get_benchmarks(pfm)
        pfm = self._generate_metric_verdicts(pfm)
        pfm = self._score_metrics(pfm)

        commendable_points, improvement_points, review_points = self._generate_feedbacks(user_profile, pfm)
        metrics_table = self.get_metrics_scoring_table(pfm)
        
        return ReportData(
            commendable_areas=commendable_points,
            areas_for_improvement=improvement_points,
            review_areas=review_points,
            metrics_scoring_table=metrics_table
        )

    def _get_benchmarks(self, pfm: PersonalFinanceMetrics) -> PersonalFinanceMetrics:
        """
        Returns a dict mapping each metric to its ideal (min, max) benchmark values based on the user's profile.
        """
        tier_key = f"Tier {pfm.city_tier}"
        bracket = classify_income_bracket(pfm.total_monthly_income)

        for metric, ideal in IDEAL_RANGES.items():
            if isinstance(ideal, dict):
                min_i, max_i = ideal[tier_key][bracket]
            else:
                min_i, max_i = ideal
            if hasattr(pfm, metric):
                met = getattr(pfm, metric)
                setattr(met, 'benchmark', (min_i, max_i))

        return pfm

    def _filter_metrics_by_names(self) -> tuple[list, list, list]:
        comm_metrics, impr_metrics, review_metrics = [], [], []
        # Only check your assessment fields
        assessment_fields = self.assessment_fields

        for name in assessment_fields:
            metric_obj = getattr(self.derived_metrics, name, None)
            if not isinstance(metric_obj, Metric) or not metric_obj.verdict:
                continue
            if metric_obj.verdict in self.good_labels:
                comm_metrics.append(name)
            if metric_obj.verdict in self.bad_labels:
                impr_metrics.append(name)
            if metric_obj.verdict in self.review_labels:
                review_metrics.append(name)

        return comm_metrics, impr_metrics, review_metrics

    def _generate_metric_verdicts(
        self,
        pfm: PersonalFinanceMetrics
    ) -> PersonalFinanceMetrics:
        if pfm is None:
            raise ValueError("Metrics not provided.")

        # Relaxation thresholds
        low_relax_stage_1 = 0.85
        high_relax_stage_1 = 1.15
        low_relax_stage_2 = 0.75
        high_relax_stage_2 = 1.25

        # Only these fields need assessment
        assessment_fields = self.assessment_fields

        for field in assessment_fields:
            metric_obj: Metric = getattr(pfm, field, None)
            if not isinstance(metric_obj, Metric):
                continue

            user_val = metric_obj.value
            bench = metric_obj.benchmark

            # Handle missing or sentinel values
            if user_val is None or user_val == 999:
                metric_obj.verdict = "error_computing_metric"
                continue

            if not bench or len(bench) != 2:
                metric_obj.verdict = "no_benchmark_provided"
                continue

            bm_low, bm_high = bench

            # Determine verdict
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

        return pfm

    def _generate_feedback_header(self, metric: Metric) -> str:
        mode = 'good' if metric.verdict in self.good_labels else 'bad'
        
        if metric.metric_name.endswith('ratio'):
            if mode == 'bad':
                if metric.verdict in ['extremely_low', 'low']:
                    tmpl = self.header_templates['ratio_headers'][mode]['low']
                else:
                    tmpl = self.header_templates['ratio_headers'][mode]['high']
            else:
                tmpl = self.header_templates['ratio_headers'][mode]
            
        elif metric.metric_name.endswith('adequacy'):
            tmpl = self.header_templates['adequacy_headers'][mode]
        else:
            tmpl = self.header_templates['asset_allocation_headers'][mode]
        tmp = choice(tmpl)    
        metric_name_readable = ' '.join(metric.metric_name.split(sep='_')).title()
        header = tmp.format(metric_name=metric_name_readable)
        return header
    
    def _generate_feedbacks(
        self,
        user_profile: UserProfile,
        derived_metrics: PersonalFinanceMetrics,
    ) -> tuple[List[CommendablePoint], List[ImprovementPoint], List[ReviewPoint]]:
        
        if not all([user_profile, derived_metrics]):
            raise FeedbackGenerationFailedError()
        self.user_profile = user_profile
        self.derived_metrics = derived_metrics

        # self.derived_metrics = self.generate_metric_verdicts(self.derived_metrics, self.benchmark_data)
        good_metrics, bad_metrics, review_metrics = self._filter_metrics_by_names()

        good_points: List[CommendablePoint] = self._generate_commendable_points(derived_metrics, good_metrics)
        review_points: List[ReviewPoint] = self._generate_review_points(derived_metrics, review_metrics) ## review must be called before bad points as non review points falls through
        bad_points: List[ImprovementPoint] = self._generate_improvement_points(derived_metrics, bad_metrics)

        return (good_points, bad_points, review_points)
    
    def _generate_review_points(
        self,
        derived_metrics: PersonalFinanceMetrics,
        review_metrics: List[str]
    ) -> List[ReviewPoint]:
        
        review_points = []

        for metric_name in review_metrics:
            metric_data = getattr(derived_metrics, metric_name)
            if self.metrics_analysed.count(metric_name):
                continue
            feedback = self._create_review_point(metric_data)
            if feedback is not None:
                review_points.append((metric_name, feedback))
                self.metrics_analysed.append(metric_name)

        sorted_review  = self._sort_points(review_points)
        review_points=[pt for _, pt in sorted_review]

        return review_points
    
    def _generate_improvement_points(
        self,
        derived_metrics: PersonalFinanceMetrics,
        bad_metrics: List[str]
    ) -> List[ImprovementPoint]:
        
        bad_points = []

        for metric_name in bad_metrics:
            metric_data = getattr(derived_metrics, metric_name)
            if self.metrics_analysed.count(metric_name):
                continue
            feedback = self._create_improvement_point(metric_data)
            if feedback is not None:
                bad_points.append((metric_name, feedback))
                self.metrics_analysed.append(metric_name)

        sorted_bad  = self._sort_points(bad_points)
        improvement_points=[pt for _, pt in sorted_bad]

        return improvement_points
    
    def _generate_commendable_points(
        self, 
        derived_metrics: PersonalFinanceMetrics,
        good_metrics: List[str]
    ) -> List[CommendablePoint]:
        
        good_points = []

        for metric_name in good_metrics:
            metric_data = getattr(derived_metrics, metric_name)
            if self.metrics_analysed.count(metric_name):
                continue
            feedback = self._create_commend_point(metric_data)
            if feedback is not None:
                good_points.append((metric_name, feedback))
                self.metrics_analysed.append(metric_name)

        sorted_good = self._sort_points(good_points)
        commendable_points=[pt for _, pt in sorted_good]

        return commendable_points
    
    def _create_review_point(self, metric: Metric) -> ReviewPoint:
        min_b, max_b = metric.benchmark
        formatted = self._get_formatted_review_point(metric, min_b, max_b)
        if formatted is None:
            return None

        return ReviewPoint(
            metric_name=metric.metric_name,
            header=self._generate_feedback_header(metric),
            current_scenario=formatted['current_scenario']
        )

    def _create_commend_point(self, metric: Metric) -> CommendablePoint:
        min_b, max_b = metric.benchmark
        formatted = self._get_formatted_commend_point(metric)
        
        return CommendablePoint(
            metric_name=metric.metric_name,
            header=self._generate_feedback_header(metric),
            current_scenario=formatted['current_scenario']
        )

    def _create_improvement_point(self, metric: Metric) -> ImprovementPoint:
        min_b, max_b = metric.benchmark

        gap_amt = self._compute_gap(metric, min_b, max_b)
        formatted = self._get_formatted_improvement_point(metric, gap_amt, min_b, max_b)

        return ImprovementPoint(
            metric_name=metric.metric_name,
            header=self._generate_feedback_header(metric),
            current_scenario=formatted.get('current_scenario'),
            actionable=formatted.get('actionable')
        )

    def _compute_gap(
        self, 
        metric: Metric, 
        min_b: float, 
        max_b: float
    ) -> float:
        
        base = {
            'income': self.derived_metrics.total_monthly_income,
            'expense': self.derived_metrics.total_monthly_expense + self.derived_metrics.total_monthly_emi,
            'corpus': self.derived_metrics.target_retirement_corpus,
            'assets': self.derived_metrics.total_assets,
            'liabilities': self.derived_metrics.total_liabilities,
            'total_medical_cover': self.user_profile.insurance_data.total_medical_cover,
            'total_term_cover': self.user_profile.insurance_data.total_term_cover,
            'family_size': self.user_profile.personal_data.no_of_dependents + 1
        }
        MIN_THRESH = 1000
        try:
            if metric.metric_name in {
                'savings_income_ratio','investment_income_ratio',
                'expense_income_ratio','housing_income_ratio'
            }:
                gap_vals = [
                    abs((min_b - metric.value)*base['income']), 
                    abs((max_b - metric.value)*base['income'])
                ]
            elif metric.metric_name in {'emergency_fund_ratio','liquidity_ratio'}:
                gap_vals = [
                    abs((min_b - metric.value)*base['expense']), 
                    abs((max_b - metric.value)*base['expense'])
                ]
            elif metric.metric_name == 'retirement_adequacy':
                years_left = self.user_profile.personal_data.expected_retirement_age - self.user_profile.personal_data.age
                monthly_factor = max(1, 12 * years_left)
                gap_vals = [
                    abs((min_b - metric.value)*base['corpus']) / monthly_factor, 
                    abs((max_b - metric.value)*base['corpus']) / monthly_factor
                ] 
            elif metric.metric_name == 'asset_liability_ratio':
                low_liab = base['assets']/ (min_b or 1)
                high_liab= base['assets']/ (max_b or 1)
                gap_vals = [
                    abs(base['liabilities'] - low_liab), 
                    abs(base['liabilities'] - high_liab)
                ]
            elif metric.metric_name == 'health_insurance_adequacy':
                gap_vals = [
                    abs(base['total_medical_cover'] - min_b * base['family_size'] * MEDICAL_COVER_FACTOR),
                    abs(base['total_medical_cover'] - max_b * base['family_size'] * MEDICAL_COVER_FACTOR)
                ]
            elif metric.metric_name == 'term_insurance_adequacy':
                gap_vals = [
                    abs(base['total_term_cover'] - min_b * 12 * base['income'] * TERM_COVER_FACTOR),
                    abs(base['total_term_cover'] - max_b * 12 * base['income'] * TERM_COVER_FACTOR)
                ]
                
            else:
                return MIN_THRESH
            return max(min(gap_vals), MIN_THRESH)
        except ZeroDivisionError:
            return MIN_THRESH
        
    def _get_formatted_review_point(self, metric: Metric, min_b: float, max_b: float):
        template = REVIEW_AREAS.get(metric.metric_name)
        if not template:
            return None
        
        template = template.get(metric.verdict)
        curr_scnr = template.get('current_scenario')
        places = re.findall(r'{(\w+)[^}]*}', curr_scnr)
        ctx = {
            'user_value': metric.value,
            'min_val': min_b,
            'max_val': max_b
        }

        filtered_ctx = {k: v for k, v in ctx.items() if k in places}

        return {
            'current_scenario': curr_scnr.format(**filtered_ctx)
        }

    def _get_formatted_commend_point(self, metric: Metric):
        template = COMMENDABLE_AREAS.get(metric.metric_name)
        if not template:
            return {
                'current_scenario': 'Metric values are well within ideal ranges. Great work!'
            }
        template = template.get(metric.verdict)
        curr_scnr = template.get('current_scenario')


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
        user_val = metric.value

        if metric.metric_name == 'health_insurance_adequacy':
            factor = (1 + self.user_profile.personal_data.no_of_dependents) * MEDICAL_COVER_FACTOR
            min_b = min_b * factor
            max_b = max_b * factor
            user_val = self.user_profile.insurance_data.total_medical_cover
        elif metric.metric_name == 'term_insurance_adequacy':
            inc_factor = (self.derived_metrics.total_monthly_income) * 12 * TERM_COVER_FACTOR
            min_b = min_b * inc_factor
            max_b = max_b * inc_factor
            user_val = self.user_profile.insurance_data.total_term_cover

        ctx = {
            'gap_amt': gap_amt,
            'min_val': min_b,
            'max_val': max_b
        }

        filtered_ctx = {k: v for k, v in ctx.items() if k in places}

        
        return {
            'current_scenario': curr_scnr.format(user_value=user_val),
            'actionable': action.format_map(filtered_ctx)
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

    def _score_metrics(
        self,
        metrics: PersonalFinanceMetrics,
    ) -> PersonalFinanceMetrics:

        pfm = metrics

        for metric_name in metrics.model_fields:
            if not (metric_name.endswith('ratio') or metric_name.endswith('adequacy')):
                continue
            benchmark = getattr(getattr(metrics, metric_name), 'benchmark')
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
        if ideal_min <= val <= ideal_max or val == 999:
            return max_score
        if ideal_max <= val:
            return 0.85 * max_score
        ratio = val / ideal_min if val < ideal_min else ideal_max / val
        return max_score * (SCORING_BASE_VALUE + (1 - SCORING_BASE_VALUE) * max(0.0, min(1.0, ratio))) ** 3

    def get_metrics_scoring_table(self, pfm: PersonalFinanceMetrics) -> list[dict]:
        """
        Returns a table of metrics with their weights, benchmarks, values, and scores.
        """
        scoring_table = []
        total_score = 0

        for metric_name in pfm.model_fields:
            if not (metric_name.endswith('ratio') or metric_name.endswith('adequacy')):
                continue

            metric: Metric = getattr(pfm, metric_name, None)
            if not isinstance(metric, Metric):
                continue
            
            total_score += metric.assigned_score
            capitalised_name = capwords(metric_name.replace('_', ' '))
            capitalised_verdict = capwords(metric.verdict.replace('_', ' '))
            scoring_table.append({
                "Metric": capitalised_name,
                "Weight Assigned": metric.weight,
                "Benchmark": metric.benchmark,
                "User Value": metric.value,
                "Verdict": capitalised_verdict,
                "Points Awarded": metric.assigned_score
            })
        
        # Append totals row
        scoring_table.append({
            "Metric": 'Total',
            "Weight Assigned": '',
            "Benchmark": '',
            "User Value": '',
            "Verdict": '',
            "Points Awarded": total_score
        })
        

        return scoring_table
