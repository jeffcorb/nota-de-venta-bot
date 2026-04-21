"""Generación de Notas de Venta en PDF con diseño profesional."""

import io
import logging
from datetime import datetime

import requests
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Paragraph,
)

logger = logging.getLogger(__name__)

# ── Paleta de colores ──────────────────────────────────────────────────────────
C_PRIMARY = colors.HexColor("#1B4F72")   # Azul oscuro
C_ACCENT  = colors.HexColor("#2E86C1")   # Azul medio
C_STRIPE  = colors.HexColor("#D6EAF8")   # Azul muy claro (filas pares)
C_LIGHT   = colors.HexColor("#F2F3F4")   # Gris muy claro
C_BORDER  = colors.HexColor("#BDC3C7")   # Gris borde
C_TEXT    = colors.HexColor("#1C2833")   # Texto oscuro
C_WHITE   = colors.white
C_GRAY    = colors.HexColor("#7F8C8D")   # Gris texto secundario


def _styles() -> dict:
    base = getSampleStyleSheet()
    def ps(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        "biz_name": ps("biz_name", fontSize=20, textColor=C_PRIMARY,
                       fontName="Helvetica-Bold", alignment=TA_RIGHT,
                       spaceAfter=3),
        "biz_sub":  ps("biz_sub",  fontSize=11, textColor=C_TEXT,
                       fontName="Helvetica", alignment=TA_RIGHT,
                       spaceAfter=2),
        "banner_l": ps("banner_l", fontSize=15, textColor=C_WHITE,
                       fontName="Helvetica-Bold", alignment=TA_LEFT),
        "banner_r": ps("banner_r", fontSize=11, textColor=C_WHITE,
                       fontName="Helvetica", alignment=TA_RIGHT),
        "sec_hdr":  ps("sec_hdr",  fontSize=10, textColor=C_WHITE,
                       fontName="Helvetica-Bold", alignment=TA_LEFT),
        "label":    ps("label",    fontSize=9,  textColor=C_GRAY,
                       fontName="Helvetica"),
        "value":    ps("value",    fontSize=11, textColor=C_TEXT,
                       fontName="Helvetica"),
        "th":       ps("th",       fontSize=10, textColor=C_WHITE,
                       fontName="Helvetica-Bold", alignment=TA_CENTER),
        "td":       ps("td",       fontSize=10, textColor=C_TEXT,
                       fontName="Helvetica"),
        "td_c":     ps("td_c",     fontSize=10, textColor=C_TEXT,
                       fontName="Helvetica", alignment=TA_CENTER),
        "td_r":     ps("td_r",     fontSize=10, textColor=C_TEXT,
                       fontName="Helvetica", alignment=TA_RIGHT),
        "sub_l":    ps("sub_l",    fontSize=10, textColor=C_TEXT,
                       fontName="Helvetica-Bold", alignment=TA_RIGHT),
        "tot_l":    ps("tot_l",    fontSize=13, textColor=C_WHITE,
                       fontName="Helvetica-Bold", alignment=TA_RIGHT),
        "tot_v":    ps("tot_v",    fontSize=13, textColor=C_WHITE,
                       fontName="Helvetica-Bold", alignment=TA_RIGHT),
        "footer":   ps("footer",   fontSize=9,  textColor=C_GRAY,
                       fontName="Helvetica", alignment=TA_CENTER),
    }


def _logo_image(url: str, max_w: float = 4.5 * cm, max_h: float = 3 * cm):
    """Descarga y devuelve un objeto Image de ReportLab, o None si falla."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        buf = io.BytesIO(resp.content)
        img = Image(buf)
        ratio = min(max_w / img.drawWidth, max_h / img.drawHeight)
        img.drawWidth  *= ratio
        img.drawHeight *= ratio
        return img
    except Exception as exc:
        logger.warning("No se pudo descargar el logo: %s", exc)
        return None


def generate_pdf(venta: dict, config: dict) -> bytes:
    """Genera el PDF y devuelve los bytes."""
    buffer  = io.BytesIO()
    page_w  = A4[0] - 3 * cm          # ancho útil
    numero  = venta.get("numero", 1)
    moneda  = config.get("moneda", "USD")
    fecha   = datetime.now().strftime("%d/%m/%Y")
    s       = _styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm,  bottomMargin=2 * cm,
        title=f"Nota de Venta #{numero:04d}",
        author=config.get("nombre", ""),
    )

    story = []

    # ── 1. Encabezado: logo + datos del negocio ─────────────────────────────
    logo = _logo_image(config["logo_url"]) if config.get("logo_url") else None
    logo_w = logo.drawWidth + 0.3 * cm if logo else 0

    biz_lines = [
        [Paragraph(config.get("nombre", "Mi Negocio"), s["biz_name"])],
        [Paragraph(config.get("telefono", ""),         s["biz_sub"])],
        [Paragraph(config.get("email", ""),            s["biz_sub"])],
    ]
    biz_tbl = Table(biz_lines, colWidths=[page_w - logo_w])
    biz_tbl.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 1), (0, 1),   12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    if logo:
        hdr_tbl = Table([[logo, biz_tbl]], colWidths=[logo_w, page_w - logo_w])
    else:
        hdr_tbl = Table([[biz_tbl]], colWidths=[page_w])

    hdr_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    story.append(hdr_tbl)
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=C_PRIMARY))
    story.append(Spacer(1, 0.3 * cm))

    # ── 2. Banner nota + fecha ──────────────────────────────────────────────
    banner = Table(
        [[Paragraph(f"NOTA DE VENTA  #{numero:04d}", s["banner_l"]),
          Paragraph(f"Fecha:  {fecha}", s["banner_r"])]],
        colWidths=[page_w * 0.6, page_w * 0.4],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_PRIMARY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.5 * cm))

    # ── 3. Datos del cliente ────────────────────────────────────────────────
    cli     = venta.get("cliente", {})
    col_w_c = page_w / 4

    cli_tbl = Table(
        [
            [Paragraph("DATOS DEL CLIENTE", s["sec_hdr"]), "", "", ""],
            [
                Paragraph("Nombre / Razón Social", s["label"]),
                Paragraph("N° Documento / RUC",    s["label"]),
                Paragraph("Dirección",             s["label"]),
                Paragraph("Forma de Pago",         s["label"]),
            ],
            [
                Paragraph(cli.get("nombre",    ""), s["value"]),
                Paragraph(cli.get("ruc",       ""), s["value"]),
                Paragraph(cli.get("direccion", ""), s["value"]),
                Paragraph(cli.get("pago",      ""), s["value"]),
            ],
        ],
        colWidths=[col_w_c] * 4,
    )
    cli_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_ACCENT),
        ("SPAN",          (0, 0), (-1, 0)),
        ("BACKGROUND",    (0, 1), (-1, -1), C_LIGHT),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID",     (0, 1), (-1, -1), 0.3, C_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(cli_tbl)
    story.append(Spacer(1, 0.5 * cm))

    # ── 4. Tabla de artículos ───────────────────────────────────────────────
    articulos = venta.get("articulos", [])
    w_n    = 1.0 * cm
    w_cant = 2.0 * cm
    w_pu   = 3.5 * cm
    w_tot  = 3.5 * cm
    w_desc = page_w - w_n - w_cant - w_pu - w_tot

    rows = [[
        Paragraph("#",            s["th"]),
        Paragraph("Descripción",  s["th"]),
        Paragraph("Cant.",        s["th"]),
        Paragraph("P. Unitario",  s["th"]),
        Paragraph("Total",        s["th"]),
    ]]

    for idx, art in enumerate(articulos):
        qty     = art.get("cantidad", 0)
        precio  = art.get("precio",   0)
        sub     = art.get("subtotal", 0)
        qty_str = str(int(qty)) if qty == int(qty) else f"{qty:.2f}"

        rows.append([
            Paragraph(str(idx + 1), s["td_c"]),
            Paragraph(art.get("nombre", ""), s["td"]),
            Paragraph(qty_str,               s["td_c"]),
            Paragraph(f"{moneda} {precio:.2f}", s["td_r"]),
            Paragraph(f"{moneda} {sub:.2f}",    s["td_r"]),
        ])

    total = sum(a.get("subtotal", 0) for a in articulos)

    # Fila subtotal
    rows.append([
        "", "", "",
        Paragraph("SUBTOTAL", s["sub_l"]),
        Paragraph(f"{moneda} {total:.2f}", s["td_r"]),
    ])
    # Fila total
    rows.append([
        Paragraph("", s["tot_l"]),
        "", "",
        Paragraph("TOTAL", s["tot_l"]),
        Paragraph(f"{moneda} {total:.2f}", s["tot_v"]),
    ])

    art_tbl = Table(rows, colWidths=[w_n, w_desc, w_cant, w_pu, w_tot])

    tbl_style = [
        # Encabezado
        ("BACKGROUND",    (0,  0), (-1,  0), C_PRIMARY),
        ("TOPPADDING",    (0,  0), (-1,  0), 8),
        ("BOTTOMPADDING", (0,  0), (-1,  0), 8),
        # Fila subtotal
        ("BACKGROUND",    (0, -2), (-1, -2), C_LIGHT),
        ("TOPPADDING",    (0, -2), (-1, -2), 5),
        ("BOTTOMPADDING", (0, -2), (-1, -2), 5),
        # Fila total
        ("BACKGROUND",    (0, -1), (-1, -1), C_PRIMARY),
        ("SPAN",          (0, -1), (2, -1)),
        ("TOPPADDING",    (0, -1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        # General
        ("LEFTPADDING",   (0,  0), (-1, -1), 8),
        ("RIGHTPADDING",  (0,  0), (-1, -1), 8),
        ("VALIGN",        (0,  0), (-1, -1), "MIDDLE"),
        ("BOX",           (0,  0), (-1, -1), 0.5, C_BORDER),
        ("LINEBELOW",     (0,  0), (-1, -3), 0.3, C_BORDER),
    ]

    for i in range(1, len(articulos) + 1):
        bg = C_STRIPE if i % 2 == 0 else C_WHITE
        tbl_style.append(("BACKGROUND", (0, i), (-1, i), bg))

    art_tbl.setStyle(TableStyle(tbl_style))
    story.append(art_tbl)
    story.append(Spacer(1, 0.5 * cm))

    # ── 5. Notas adicionales ────────────────────────────────────────────────
    notas = venta.get("notas", "")
    if notas:
        notes_tbl = Table(
            [
                [Paragraph("NOTAS", s["sec_hdr"])],
                [Paragraph(notas,   s["value"])],
            ],
            colWidths=[page_w],
        )
        notes_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), C_ACCENT),
            ("BACKGROUND",    (0, 1), (-1, -1), C_LIGHT),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
        ]))
        story.append(notes_tbl)
        story.append(Spacer(1, 0.5 * cm))

    # ── 6. Pie de página ────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} "
        f"— {config.get('nombre', '')}",
        s["footer"],
    ))

    doc.build(story)
    return buffer.getvalue()
