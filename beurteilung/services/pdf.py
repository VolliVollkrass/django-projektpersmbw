from django.template.loader import render_to_string
from weasyprint import HTML

def generate_evaluation_pdf_bytes(evaluation) -> bytes:
    """
    Returns PDF as bytes for storage or sending via email.
    """
    html_string = render_to_string(
        "beurteilung/evaluation_pdf.html",
        {
            "evaluation": evaluation,
            "signature_valid": evaluation.verify_signature(),
        }
    )

    html = HTML(string=html_string)
    pdf_bytes = html.write_pdf()  # ⚡ direkt als bytes
    return pdf_bytes