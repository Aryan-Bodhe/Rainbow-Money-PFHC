from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from markdown import markdown

from core.exceptions import NoMarkdownFileToConvertToPDFError
from config.config import REPORT_PATH, REPORT_STYLESHEET, REPORT_TEMPLATE_DIR

class PDFGenerator:
    def __init__(self, template: str = REPORT_TEMPLATE_DIR):
        # Jinja2 env for rendering markdown templates
        self.env = Environment(
            loader=FileSystemLoader(template),
            autoescape=select_autoescape(disabled_extensions=('md',))
        )

    def render_template_to_markdown(self, template_name: str, context: dict) -> str:
        """
        Render a Jinja2 markdown template with the provided context
        and return the resulting markdown string.
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def markdown_to_pdf(
        self,
        input_md_file: str = None,
        input_md_str: str = None,
        output_pdf: str = REPORT_PATH,
        css_path: str = REPORT_STYLESHEET
    ):
        """
        Convert a Markdown file or string to PDF.
        """
        if input_md_str is None:
            if input_md_file is None:
                raise NoMarkdownFileToConvertToPDFError()
            with open(input_md_file, 'r', encoding='utf-8') as f:
                md = f.read()
        else:
            md = input_md_str

        html = markdown(md, extensions=["fenced_code", "tables"])
        if css_path:
            HTML(string=html).write_pdf(output_pdf, stylesheets=[css_path])
        else:
            HTML(string=html).write_pdf(output_pdf)

    def j2_template_to_pdf(
        self,
        template_name: str,
        context: dict,
        output_pdf: str = REPORT_PATH,
        css_path: str = REPORT_STYLESHEET
    ):
        """
        One-step: render a Jinja2 markdown template and convert it to PDF.
        """
        md_content = self.render_template_to_markdown(template_name, context)
        self.markdown_to_pdf(input_md_str=md_content, output_pdf=output_pdf, css_path=css_path)

    
    def generate_context_data(self, report_data: dict, analyzed_metrics_table: dict):
        report_data['appendix'] = analyzed_metrics_table
        return report_data


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
        weight_sum = 0
        pts_sum = 0
        for metric, weight in weights.items():
            norm_key = (
                metric.strip()
                    .lower()
                    .replace('-', '_')
                    .replace(' ', '_')
            )
            user_val = round(metrics.get(norm_key, None), 2)
            weight_sum += weight
            bm = benchmarks.get(norm_key)
            if bm is None:
                bench_str = "N/A"
            else:
                min_v, max_v = bm
                bench_str = f"< {max_v}" if min_v == 0 else f"{min_v} - {max_v}"

            pts = int(scores.get(metric, 0))
            pts_sum += pts

            table.append({
                "metric": metric.replace("_", " ").title(),
                "weight": weight,
                "benchmark": bench_str,
                "user_value": user_val,
                "points_awarded": pts
            })

        table.append({
            "metric": "Total",
            "weight": '',
            "benchmark": '',
            "user_value": '',
            "points_awarded": pts_sum
        })

        return table