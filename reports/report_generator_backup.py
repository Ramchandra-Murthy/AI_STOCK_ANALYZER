from pathlib import Path
from datetime import datetime
import math

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


class ReportGenerator:

    def __init__(self):
        self.styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            "ReportTitle",
            parent=self.styles["Heading1"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            spaceAfter=8,
        )

        self.subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=self.styles["BodyText"],
            alignment=TA_CENTER,
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            textColor=colors.grey,
            spaceAfter=10,
        )

        self.heading_style = ParagraphStyle(
            "SectionHeading",
            parent=self.styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.darkblue,
            spaceBefore=8,
            spaceAfter=8,
        )

        self.normal = ParagraphStyle(
            "ReportBody",
            parent=self.styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            alignment=TA_LEFT,
        )

        self.small = ParagraphStyle(
            "SmallText",
            parent=self.normal,
            fontSize=8,
            leading=10,
            textColor=colors.grey,
        )

    # ======================================================
    # FORMATTERS
    # ======================================================

    @staticmethod
    def _safe_float(value):
        try:
            number = float(value)

            if math.isnan(number) or math.isinf(number):
                return None

            return number

        except (TypeError, ValueError):
            return None

    def _format_number(self, value, decimals=2):
        number = self._safe_float(value)

        if number is None:
            return "N/A"

        return f"{number:,.{decimals}f}"

    def _format_price(self, value):
        number = self._safe_float(value)

        if number is None:
            return "N/A"

        return f"Rs. {number:,.2f}"

    def _format_percent(self, value):
        number = self._safe_float(value)

        if number is None:
            return "N/A"

        return f"{number * 100:.2f}%"

    def _format_market_cap(self, value):
        number = self._safe_float(value)

        if number is None:
            return "N/A"

        if number >= 1e12:
            return f"Rs. {number / 1e12:.2f} Lakh Cr"

        if number >= 1e7:
            return f"Rs. {number / 1e7:,.2f} Cr"

        if number >= 1e5:
            return f"Rs. {number / 1e5:,.2f} Lakh"

        return f"Rs. {number:,.0f}"

    # ======================================================
    # PDF HELPERS
    # ======================================================

    def _section_title(self, title):
        return Paragraph(
            title,
            self.heading_style,
        )

    def _bullet(self, text):
        return Paragraph(
            f"&#8226; {text}",
            self.normal,
        )

    def _table(self, rows):
        formatted_rows = []

        for row_index, row in enumerate(rows):
            formatted_row = []

            for cell in row:
                style = self.small if row_index == 0 else self.normal

                formatted_row.append(
                    Paragraph(
                        str(cell),
                        style,
                    )
                )

            formatted_rows.append(formatted_row)

        table = Table(
            formatted_rows,
            colWidths=[
                2.4 * inch,
                3.6 * inch,
            ],
            repeatRows=1,
            hAlign="LEFT",
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.darkblue,
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.lightgrey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 1),
                        (-1, -1),
                        colors.whitesmoke,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        return table

    # ======================================================
    # HEADER / FOOTER
    # ======================================================

    def _draw_header_footer(self, canvas, doc):
        canvas.saveState()

        width, height = A4

        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.darkblue)

        canvas.drawString(
            doc.leftMargin,
            height - 28,
            "AI STOCK ANALYZER PRO",
        )

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)

        canvas.drawRightString(
            width - doc.rightMargin,
            height - 28,
            "Equity Research Report",
        )

        canvas.setStrokeColor(colors.lightgrey)

        canvas.line(
            doc.leftMargin,
            height - 34,
            width - doc.rightMargin,
            height - 34,
        )

        canvas.line(
            doc.leftMargin,
            32,
            width - doc.rightMargin,
            32,
        )

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)

        canvas.drawString(
            doc.leftMargin,
            20,
            "AI Stock Analyzer Pro",
        )

        canvas.drawRightString(
            width - doc.rightMargin,
            20,
            f"Page {doc.page}",
        )

        canvas.restoreState()
