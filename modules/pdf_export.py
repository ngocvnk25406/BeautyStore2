"""
pdf_export.py - Xuất hóa đơn điện tử dạng PDF
Yêu cầu: pip install reportlab
"""
import os
from pathlib import Path
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

BASE_DIR = Path(__file__).resolve().parent.parent
EXPORT_DIR = BASE_DIR / "exports"


def _ensure_export_dir():
    EXPORT_DIR.mkdir(exist_ok=True)


def export_invoice_pdf(order: dict, customer: dict = None, products_map: dict = None) -> str:
    """
    Xuất hóa đơn PDF cho đơn hàng.
    Trả về đường dẫn file PDF hoặc raise RuntimeError nếu thiếu reportlab.
    """
    if not REPORTLAB_OK:
        raise RuntimeError(
            "Thư viện reportlab chưa được cài đặt.\n"
            "Vui lòng chạy: pip install reportlab"
        )

    _ensure_export_dir()
    order_id = order.get("order_id", "UNKNOWN")
    filename = EXPORT_DIR / f"HoaDon_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    pink = colors.HexColor("#ee609c")
    purple = colors.HexColor("#b565a7")

    title_style = ParagraphStyle(
        "title",
        parent=styles["Title"],
        fontSize=20,
        textColor=pink,
        spaceAfter=4,
        alignment=1,
    )
    sub_style = ParagraphStyle(
        "sub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        alignment=1,
    )
    normal = ParagraphStyle("norm", parent=styles["Normal"], fontSize=10, spaceAfter=2)
    bold_normal = ParagraphStyle("bold_norm", parent=normal, fontName="Helvetica-Bold")

    story = []

    # Header
    story.append(Paragraph("🧴 GLOWUP BEAUTY STORE", title_style))
    story.append(Paragraph("Cửa hàng Mỹ phẩm & Tư vấn Skincare", sub_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=pink))
    story.append(Spacer(1, 0.3 * cm))

    # Tiêu đề hóa đơn
    story.append(Paragraph(f"<b>HÓA ĐƠN BÁN HÀNG</b>", bold_normal))
    story.append(Paragraph(f"Mã đơn hàng: <b>{order_id}</b>", normal))
    story.append(Paragraph(f"Ngày: <b>{order.get('datetime', '')}</b>", normal))

    # Thông tin khách hàng
    if customer:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("<b>THÔNG TIN KHÁCH HÀNG</b>", bold_normal))
        story.append(Paragraph(f"Họ tên: {customer.get('name', 'Khách lẻ')}", normal))
        story.append(Paragraph(f"SĐT: {customer.get('phone', '')}", normal))
        story.append(Paragraph(f"Hạng thành viên: {customer.get('rank', 'Đồng')}", normal))
    else:
        story.append(Paragraph("Khách hàng: Khách lẻ", normal))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("<b>CHI TIẾT SẢN PHẨM</b>", bold_normal))
    story.append(Spacer(1, 0.2 * cm))

    # Bảng sản phẩm
    headers = ["STT", "Sản phẩm", "Đơn giá", "SL", "Thành tiền"]
    data = [headers]
    items = order.get("items", [])
    for i, item in enumerate(items, 1):
        pid = item.get("product_id", "")
        name = item.get("name", pid)
        if products_map and pid in products_map:
            name = products_map[pid].get("name", name)
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        subtotal = price * qty
        data.append([
            str(i),
            name[:45],
            f"{price:,.0f}d",
            str(qty),
            f"{subtotal:,.0f}d",
        ])

    col_widths = [1 * cm, 8 * cm, 3 * cm, 1.5 * cm, 3 * cm]
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), pink),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff0f5")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.4 * cm))

    # Tổng tiền
    subtotal = order.get("subtotal", order.get("total", 0))
    discount = order.get("discount", 0)
    total = order.get("total", 0)
    discount_rate = order.get("discount_rate", 0)

    summary_data = [
        ["Tạm tính:", f"{subtotal:,.0f}d"],
        [f"Giảm giá ({int(discount_rate*100)}%):", f"-{discount:,.0f}d"],
        ["TỔNG THANH TOÁN:", f"{total:,.0f}d"],
    ]
    sum_table = Table(summary_data, colWidths=[10 * cm, 5 * cm])
    sum_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 2), (-1, 2), 12),
        ("TEXTCOLOR", (0, 2), (-1, 2), pink),
        ("LINEABOVE", (0, 2), (-1, 2), 1, pink),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sum_table)

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<i>Cảm ơn bạn đã mua hàng tại GLOWUP BEAUTY STORE! 💖</i>",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=9,
                       textColor=colors.grey, alignment=1)
    ))

    doc.build(story)
    return str(filename)
