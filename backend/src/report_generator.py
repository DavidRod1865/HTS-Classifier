"""
PDF report generator - produce a printable HTS classification report from batch results.

Uses fpdf2 (pure Python, no system dependencies) to generate a clean, professional PDF
that small businesses can print or share with customs brokers.
"""

import io
from datetime import datetime
from fpdf import FPDF


class HTSReport(FPDF):
    """Custom FPDF subclass with header/footer for the classification report."""

    def __init__(self, invoice_filename=""):
        super().__init__()
        self.invoice_filename = invoice_filename
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "HTS Classification Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        date_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        self.cell(0, 5, f"Generated: {date_str}", align="C", new_x="LMARGIN", new_y="NEXT")
        if self.invoice_filename:
            self.cell(0, 5, f"Source: {self.invoice_filename}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 4, "Disclaimer: Classifications are for reference only.", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 4, "Verify with a licensed customs broker before filing.", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 4, f"Page {self.page_no()}/{{nb}}", align="C")


def generate_report(items, invoice_filename=""):
    """
    Generate a PDF classification report.

    Args:
        items: list of { commodity, quantity, unit_price, line_number, classification }
        invoice_filename: original PDF filename for the header

    Returns:
        bytes - the PDF file content
    """
    pdf = HTSReport(invoice_filename)
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── Summary section ──────────────────────────────────────────────
    total = len(items)
    classified = sum(1 for i in items if i.get("classification", {}).get("type") == "result")
    needs_review = total - classified

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)

    summary_data = [
        ("Total Items", str(total)),
        ("Classified", str(classified)),
        ("Needs Review", str(needs_review)),
    ]
    for label, value in summary_data:
        pdf.cell(40, 6, f"{label}:", new_x="RIGHT")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 6, value, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

    pdf.ln(5)

    # ── Classification table ─────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Classification Results", new_x="LMARGIN", new_y="NEXT")

    # Table header
    col_widths = [8, 62, 30, 28, 22, 40]  # #, Description, HTS Code, Duty, Conf, Status
    headers = ["#", "Commodity", "HTS Code", "Duty Rate", "Conf.", "Status"]

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(240, 240, 240)
    for i, (header, w) in enumerate(zip(headers, col_widths)):
        pdf.cell(w, 7, header, border=1, fill=True,
                 new_x="RIGHT" if i < len(headers) - 1 else "LMARGIN",
                 new_y="TOP" if i < len(headers) - 1 else "NEXT")

    # Table rows
    pdf.set_font("Helvetica", "", 8)
    for item in items:
        classification = item.get("classification", {})
        results = classification.get("results", [])
        top_result = results[0] if results else {}
        is_classified = classification.get("type") == "result"

        row_data = [
            str(item.get("line_number", "")),
            _truncate(item.get("commodity", ""), 45),
            top_result.get("hts_code", "N/A"),
            _truncate(top_result.get("effective_duty", "N/A"), 18),
            f"{top_result.get('confidence_score', 0)}%" if top_result else "-",
            "Classified" if is_classified else "Needs Review",
        ]

        # Color the status cell
        for i, (val, w) in enumerate(zip(row_data, col_widths)):
            if i == len(row_data) - 1:  # Status column
                if is_classified:
                    pdf.set_text_color(0, 128, 0)
                else:
                    pdf.set_text_color(200, 120, 0)

            pdf.cell(w, 6, val, border=1,
                     new_x="RIGHT" if i < len(row_data) - 1 else "LMARGIN",
                     new_y="TOP" if i < len(row_data) - 1 else "NEXT")

            if i == len(row_data) - 1:
                pdf.set_text_color(0, 0, 0)

    pdf.ln(8)

    # ── Detailed breakdowns ──────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Detailed Results", new_x="LMARGIN", new_y="NEXT")

    for item in items:
        classification = item.get("classification", {})
        results = classification.get("results", [])
        is_classified = classification.get("type") == "result"

        pdf.set_font("Helvetica", "B", 9)
        prefix = "Review" if not is_classified else "Item"
        pdf.cell(0, 6, f"{prefix} #{item.get('line_number', '?')}: {_truncate(item.get('commodity', ''), 70)}",
                 new_x="LMARGIN", new_y="NEXT")

        if item.get("quantity"):
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 5, f"  Quantity: {item['quantity']}", new_x="LMARGIN", new_y="NEXT")

        analysis = classification.get("analysis")
        if analysis:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 4, _safe(f"  Analysis: {analysis}"))
            pdf.set_text_color(0, 0, 0)

        for j, result in enumerate(results[:3]):
            rank = "Best Match" if j == 0 else f"Alternative {j}"
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 5,
                     f"  {rank}: {result.get('hts_code', 'N/A')} - "
                     f"{_truncate(result.get('description', ''), 60)} "
                     f"(Duty: {result.get('effective_duty', 'N/A')}, "
                     f"Confidence: {result.get('confidence_score', 0)}%)",
                     new_x="LMARGIN", new_y="NEXT")

        pdf.ln(3)

    # Write to bytes
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def _truncate(text, max_len):
    """Truncate text with ellipsis if it exceeds max_len."""
    text = _safe(str(text).strip())
    if len(text) > max_len:
        return text[:max_len - 1] + "..."
    return text


def _safe(text):
    """Replace non-latin-1 characters so fpdf2 Helvetica doesn't choke."""
    return text.encode("latin-1", errors="replace").decode("latin-1")
