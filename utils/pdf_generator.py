import json
from typing import List

from weasyprint import HTML
from markdown import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from models.ReportData import ReportData, PersonalFinanceMetrics
from config.config import REPORT_PATH, REPORT_STYLESHEET, REPORT_TEMPLATE_DIR
from core.exceptions import InvalidJsonFormatError

GLOSSARY_PATH = 'assets/glossary.json'

class PDFGenerator:
    def __init__(self, template_dir: str = REPORT_TEMPLATE_DIR):
        # Jinja2 env for rendering templates
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(disabled_extensions=('j2',))
        )

    def render_template(self, template_name: str, context: dict) -> str:
        """
        Render a Jinja2 template (markdown or HTML) with the provided context.
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def markdown_to_pdf(
        self,
        markdown_str: str,
        output_pdf: str = REPORT_PATH,
        css_path: str = REPORT_STYLESHEET
    ):
        """
        Convert a Markdown string to PDF.
        """
        html = markdown(markdown_str, extensions=["fenced_code", "tables"])
        if css_path:
            HTML(string=html).write_pdf(output_pdf, stylesheets=[css_path])
        else:
            HTML(string=html).write_pdf(output_pdf)

    def html_to_pdf(
        self,
        html_str: str,
        output_pdf: str = REPORT_PATH,
        css_path: str = REPORT_STYLESHEET
    ):
        """
        Convert raw HTML string to PDF.
        """
        if css_path:
            HTML(string=html_str).write_pdf(output_pdf, stylesheets=[css_path])
        else:
            HTML(string=html_str).write_pdf(output_pdf)

    def generate_pdf(
        self,
        report_data: ReportData,
        template_name: str = 'report_template.j2',
        output_pdf: str = REPORT_PATH,
        css_path: str = REPORT_STYLESHEET
    ):
        """
        Generate a PDF report from ReportData using a Jinja2 template.
        """
        # Build context from ReportData
        context = {
            'profile_review': report_data.profile_review,
            'commendable_areas': report_data.commendable_areas or [],
            'areas_for_improvement': report_data.areas_for_improvement or [],
            'summary': report_data.summary
        }

        # Add glossary and metrics scoring table
        context['glossary'] = self._get_glossary_data()
        context['metrics_scoring_table'] = self._build_metrics_table(
            report_data.metrics_scoring_table
        )

        # Render template
        rendered = self.render_template(template_name, context)

        # Convert to PDF based on template extension
        if template_name.endswith(('.md', '.markdown')):
            self.markdown_to_pdf(rendered, output_pdf=output_pdf, css_path=css_path)
        else:
            self.html_to_pdf(rendered, output_pdf=output_pdf, css_path=css_path)

    def _get_glossary_data(self, glossary_data_path: str = GLOSSARY_PATH) -> dict:
        with open(glossary_data_path, 'r') as file:
            return json.load(file)

    def _build_metrics_table(
        self,
        pfm: PersonalFinanceMetrics
    ) -> List[dict]:
        """
        Build a list of dicts for each metric, suitable for a Jinja2 table.
        Only uses assessment-required fields from PersonalFinanceMetrics.
        Fields: metric, weight, benchmark, user_value, points_awarded.
        Benchmarks where min == 0 are rendered as "< max", otherwise "min - max".
        """
        # Define assessment-required metric names
        field_names = [
            'savings_income_ratio', 'investment_income_ratio', 'expense_income_ratio',
            'debt_income_ratio', 'emergency_fund_ratio', 'liquidity_ratio',
            'asset_liability_ratio', 'housing_income_ratio',
            'health_insurance_adequacy', 'term_insurance_adequacy',
            'net_worth_adequacy', 'retirement_adequacy'
        ]

        table = []
        pts_sum = 0

        for name in field_names:
            metric_obj = getattr(pfm, name, None)
            if metric_obj is None:
                continue

            # Extract values
            user_val = getattr(metric_obj, 'value', None)
            weight = getattr(metric_obj, 'weight', None)
            bench = getattr(metric_obj, 'benchmark', None)
            pts = getattr(metric_obj, 'assigned_score', None)

            # Format fields
            metric_label = name.replace('_', ' ').title()
            user_val_str = f"{round(user_val, 2)}" if user_val is not None else 'N/A'
            weight_str = f"{weight}" if weight is not None else 'N/A'

            if bench:
                min_v, max_v = bench
                bench_str = f"< {max_v}" if min_v == 0 else f"{min_v} - {max_v}"
            else:
                bench_str = 'N/A'

            pts_val = int(pts) if pts is not None else 0
            pts_sum += pts_val

            table.append({
                'metric': metric_label,
                'weight': weight_str,
                'benchmark': bench_str,
                'user_value': user_val_str,
                'points_awarded': pts_val
            })

        # Append totals row
        table.append({
            'metric': 'Total',
            'weight': '',
            'benchmark': '',
            'user_value': '',
            'points_awarded': pts_sum
        })

        return table
