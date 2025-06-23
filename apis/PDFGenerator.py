from markdown import markdown
from weasyprint import HTML
from config import REPORT_PATH, REPORT_STYLESHEET, LLM_OUTPUT_PATH
from exceptions import NoMarkdownFileToConvertToPDFError

class PDFGenerator:

    def markdown_to_pdf(self, input_md_file: str = None, input_md_str: str = None, output_pdf: str = REPORT_PATH, css_path: str = REPORT_STYLESHEET):
        if input_md_str is None:
            if input_md_file is None:
                raise NoMarkdownFileToConvertToPDFError()
            with open(input_md_file) as f:
                md = f.read()
        else:
            md = input_md_str 
        html = markdown(md, extensions=["fenced_code", "tables"])
        if css_path:
            HTML(string=html).write_pdf(output_pdf, stylesheets=[css_path])
        else:
            HTML(string=html).write_pdf(output_pdf)

# Usage
# md_to_pdf_weasy("Prompt.md", "report.pdf", css_path="./markdown_pdf_style.css")
