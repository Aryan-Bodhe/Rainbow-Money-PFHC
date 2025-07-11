from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
import json
from markdown import markdown

from core.exceptions import NoMarkdownFileToConvertToPDFError
from config.config import REPORT_PATH, REPORT_STYLESHEET, REPORT_TEMPLATE_DIR
from models.FeedbackData import FeedbackData
from models.DerivedMetrics import PersonalFinanceMetrics, Metric
from models.BenchmarkData import BenchmarkData

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
        pfm: PersonalFinanceMetrics,
        benchmark_data: BenchmarkData,
        feedback_data: FeedbackData,
        review_data: str,
        summary_data: str,
        template_name: str = 'report_template.j2',
        output_pdf: str = REPORT_PATH,
        css_path: str = REPORT_STYLESHEET
    ):
        """
        Generate a PDF report from FeedbackData using a Jinja2 template.

        :param feedback_data: Pydantic FeedbackData object
        :param appendix_table: List of dicts for appendix (e.g., metrics summary)
        :param template_name: Filename of the Jinja2 template (e.g., 'report_template.j2')
        :param output_pdf: Path where PDF will be saved
        :param css_path: CSS stylesheet path for PDF styling
        """
        # Build base context
        context = {
            'overall_profile_review': review_data,
            'commendable_areas': feedback_data.commendable_points or [],
            'areas_for_improvement': feedback_data.improvement_points or [],
            'summary': summary_data
        }
        # Add glossary and appendix data
        context = self.generate_context_data(context, pfm, benchmark_data)

        # Render the template (could be markdown or HTML)
        rendered = self.render_template(template_name, context)

        # Decide conversion path by template extension
        if template_name.endswith('.md') or template_name.endswith('.markdown'):
            self.markdown_to_pdf(rendered, output_pdf=output_pdf, css_path=css_path)
        else:
            # assume template outputs HTML
            self.html_to_pdf(rendered, output_pdf=output_pdf, css_path=css_path)

    def generate_context_data(self, report_data: dict, pfm: PersonalFinanceMetrics, benchmark_data: BenchmarkData) -> dict:
        report_data['glossary'] = self.get_glossary_data()
        report_data['appendix'] = self.generate_appendix_table(pfm, benchmark_data)

        return report_data

    def get_glossary_data(self, glossary_data_path: str = GLOSSARY_PATH) -> dict:
        with open(glossary_data_path, 'r') as file:
            glossary_data = json.load(file)
        return glossary_data
    
    def generate_appendix_table(self, pfm: PersonalFinanceMetrics, benchmark_data: BenchmarkData):
        """
        Extract four dictionaries needed for summary:
         - metrics: metric_name -> value
         - weights: metric_name -> weight
         - benchmarks: metric_name -> (min, max)
         - scores: metric_name -> assigned_score

        :param metric_data: PersonalFinanceMetrics instance
        :param benchmark_data: BenchmarkData instance
        :return: (metrics, weights, benchmarks, scores)
        """
        # list of metric field names to include
        field_names = [
            'savings_income_ratio', 'investment_income_ratio', 'expense_income_ratio',
            'debt_income_ratio', 'emergency_fund_ratio', 'liquidity_ratio',
            'asset_liability_ratio', 'housing_income_ratio', 'health_insurance_adequacy',
            'term_insurance_adequacy', 'net_worth_adequacy', 'retirement_adequacy'
        ]
        metrics = {}
        weights = {}
        benchmarks = {}
        scores = {}

        for name in field_names:
            metric_obj: Metric = getattr(pfm, name, None)
            bench = getattr(benchmark_data, name, None)
            if metric_obj is None:
                print('err')
                continue
            # extract values
            if metric_obj.value is not None:
                metrics[name] = metric_obj.value
            if metric_obj.weight is not None:
                weights[name] = metric_obj.weight
            if bench is not None:
                benchmarks[name] = bench
            if metric_obj.assigned_score is not None:
                scores[name] = metric_obj.assigned_score

        output = self.get_metrics_summary_table_dict(metrics, weights, benchmarks, scores)
        # print(output)
        return output



    def get_metrics_summary_table_dict(
        self,
        metrics: dict[str, float],
        weights: dict[str, float],
        benchmarks: dict[str, tuple[float, float]],
        scores: dict[str, float]
    ) -> list[dict[str, str]]:
        """
        Build a list of dicts for each metric, suitable for a Jinja2 table.
        Fields: metric, weight, benchmark, user_value, points_awarded.
        Benchmarks where min == 0 are rendered as "< max", otherwise "min - max".
        """
        table = []
        pts_sum = 0
        for metric_label, weight in weights.items():
            norm_key = (
                metric_label.strip()
                    .lower()
                    .replace('-', '_')
                    .replace(' ', '_')
            )
            user_val = round(metrics.get(norm_key, 0), 2)
            bm = benchmarks.get(norm_key)
            if bm is None:
                bench_str = "N/A"
            else:
                min_v, max_v = bm
                bench_str = f"< {max_v}" if min_v == 0 else f"{min_v} - {max_v}"

            pts = int(scores.get(norm_key, 0))
            pts_sum += pts

            table.append({
                "metric": metric_label.replace("_", " ").title(),
                "weight": weight,
                "benchmark": bench_str,
                "user_value": user_val,
                "points_awarded": pts
            })

        # Append totals row
        table.append({
            "metric": "Total",
            "weight": '',
            "benchmark": '',
            "user_value": '',
            "points_awarded": pts_sum
        })

        # print(table)

        return table
