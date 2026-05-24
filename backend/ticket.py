import os
import json
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame

from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# ── Paths ─────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent
ROOT_DIR    = BASE_DIR.parent
TICKETS_DIR = ROOT_DIR / "tickets"
TICKETS_DIR.mkdir(exist_ok=True)

load_dotenv(dotenv_path=ROOT_DIR / ".env")
load_dotenv(find_dotenv(usecwd=False))

# ── Groq client ───────────────────────────────────────────────────
_groq_client: OpenAI | None = None

def _groq() -> OpenAI:
    global _groq_client
    if _groq_client is None:
        _groq_client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY") or os.getenv("API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
    return _groq_client


# ── Colour palette ────────────────────────────────────────────────
NAVY        = colors.HexColor("#0F1F3D")
ACCENT      = colors.HexColor("#2F7BE8")
ACCENT_DARK = colors.HexColor("#1A5CB8")
LIGHT       = colors.HexColor("#EBF3FD")
LIGHTER     = colors.HexColor("#F5F9FF")
SUCCESS     = colors.HexColor("#1A9E5C")
SUCCESS_BG  = colors.HexColor("#EAFAF1")
DANGER      = colors.HexColor("#C0392B")
DANGER_BG   = colors.HexColor("#FDECEA")
TEXT        = colors.HexColor("#1A1A2E")
MUTED       = colors.HexColor("#6B7A99")
RULE        = colors.HexColor("#D0DFF5")
WHITE       = colors.white
GOLD        = colors.HexColor("#E67E22")   # tier 2 accent

PAGE_W, PAGE_H = A4
MARGIN_L = 1.8 * cm
MARGIN_R = 1.8 * cm
MARGIN_T = 3.2 * cm  
MARGIN_B = 1.8 * cm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

HEADER_H  = 82        # pts — canvas header band height
STRIPE_H  = 5         # pts — accent stripe under header
BAR_W     = 4         # pts — left accent bar width
BAR_X     = 20        # pts — left accent bar x position


# ── Canvas page decorator ─────────────────────────────────────────
def _make_page_decorator(ticket_id: str, timestamp: str, tier: str, outcome: str):
    """Returns a canvas callback that draws the header and left bar on every page."""

    def decorate(c: rl_canvas.Canvas, doc):
        c.saveState()

        # ── Header background ─────────────────────────────────────
        c.setFillColor(NAVY)
        c.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)

        # ── Right accent block (darker blue strip on far right) ───
        c.setFillColor(ACCENT_DARK)
        c.rect(PAGE_W - 140, PAGE_H - HEADER_H, 140, HEADER_H, fill=1, stroke=0)

        # ── Diagonal separator between navy and accent block ──────
        # (simple right-angled triangle for a slanted edge effect)
        from reportlab.graphics.shapes import Polygon
        # Draw a triangle that creates a slant: apex at (PAGE_W-160, PAGE_H),
        # base at (PAGE_W-140, PAGE_H) and (PAGE_W-140, PAGE_H-HEADER_H)
        c.setFillColor(NAVY)
        path = c.beginPath()
        path.moveTo(PAGE_W - 165, PAGE_H)
        path.lineTo(PAGE_W - 140, PAGE_H)
        path.lineTo(PAGE_W - 140, PAGE_H - HEADER_H)
        path.lineTo(PAGE_W - 168, PAGE_H - HEADER_H)
        path.close()
        c.drawPath(path, fill=1, stroke=0)

        # ── Accent stripe under header ────────────────────────────
        c.setFillColor(ACCENT)
        c.rect(0, PAGE_H - HEADER_H - STRIPE_H, PAGE_W, STRIPE_H, fill=1, stroke=0)

        # ── Header: left — "IT HELPDESK" title ───────────────────
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(MARGIN_L, PAGE_H - 36, "IT SUPPORT TICKET")

        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#8BAFD8"))
        c.drawString(MARGIN_L, PAGE_H - 54, "SUPPORT  TICKET")

        # Thin separator line
        c.setStrokeColor(colors.HexColor("#2E4A6E"))
        c.setLineWidth(0.5)
        c.line(MARGIN_L, PAGE_H - 62, PAGE_W - 160, PAGE_H - 62)

        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#5C7FA8"))
        c.drawString(MARGIN_L, PAGE_H - 74, "Automated Voice Bot System")

        # ── Header: right — ticket ID + timestamp ────────────────
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.HexColor("#A8CCF0"))
        c.drawCentredString(PAGE_W - 70, PAGE_H - 28, ticket_id)

        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#6B99CC"))
        c.drawCentredString(PAGE_W - 70, PAGE_H - 42, timestamp)

        # Tier badge in header right block
        tier_label = f"TIER {tier}"
        tier_color = GOLD if tier == "2" else colors.HexColor("#4CAF8A")
        c.setFillColor(tier_color)
        badge_w, badge_h = 52, 16
        badge_x = PAGE_W - 70 - badge_w / 2
        badge_y = PAGE_H - 70
        c.roundRect(badge_x, badge_y, badge_w, badge_h, 3, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(badge_x + badge_w / 2, badge_y + 5, tier_label)

        # ── Left accent bar (body area only) ─────────────────────
        c.setFillColor(ACCENT)
        bar_top    = PAGE_H - HEADER_H - STRIPE_H - 4
        bar_bottom = MARGIN_B + 10
        c.rect(BAR_X, bar_bottom, BAR_W, bar_top - bar_bottom, fill=1, stroke=0)

        # ── Footer ────────────────────────────────────────────────
        c.setStrokeColor(RULE)
        c.setLineWidth(0.6)
        c.line(MARGIN_L, MARGIN_B + 4, PAGE_W - MARGIN_R, MARGIN_B + 4)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(MUTED)
        c.drawString(MARGIN_L, MARGIN_B - 4,
                     f"Generated by IT Helpdesk Voice Bot  •  {timestamp}")
        c.drawRightString(PAGE_W - MARGIN_R, MARGIN_B - 4, ticket_id)

        c.restoreState()

    return decorate


# ── Styles ────────────────────────────────────────────────────────
def _styles():
    return {
        "section_label": ParagraphStyle(
            "section_label",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=ACCENT, spaceBefore=16, spaceAfter=6,
            letterSpacing=1.2,
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=10, fontName="Helvetica",
            textColor=TEXT, leading=15, spaceAfter=4,
        ),
        "muted": ParagraphStyle(
            "muted",
            fontSize=9, fontName="Helvetica",
            textColor=MUTED, leading=13,
        ),
        "chip_label": ParagraphStyle(
            "chip_label",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=MUTED, alignment=TA_CENTER,
        ),
        "chip_value": ParagraphStyle(
            "chip_value",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=TEXT, alignment=TA_CENTER, spaceAfter=0,
        ),
        "step_num": ParagraphStyle(
            "step_num",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER,
        ),
        "step_text": ParagraphStyle(
            "step_text",
            fontSize=10, fontName="Helvetica",
            textColor=TEXT, leading=14,
        ),
        "outcome_ok": ParagraphStyle(
            "outcome_ok",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=SUCCESS, spaceAfter=4,
        ),
        "outcome_esc": ParagraphStyle(
            "outcome_esc",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=DANGER, spaceAfter=4,
        ),
        "outcome_sub": ParagraphStyle(
            "outcome_sub",
            fontSize=9, fontName="Helvetica",
            textColor=MUTED, leading=13,
        ),
        "diff_orig": ParagraphStyle(
            "diff_orig",
            fontSize=9.5, fontName="Helvetica",
            textColor=DANGER,
        ),
        "diff_corr": ParagraphStyle(
            "diff_corr",
            fontSize=9.5, fontName="Helvetica-Bold",
            textColor=SUCCESS,
        ),
        "diff_src": ParagraphStyle(
            "diff_src",
            fontSize=8, fontName="Helvetica",
            textColor=MUTED,
        ),
    }


# ── Section header helper ─────────────────────────────────────────
def _section(label: str, S: dict) -> list:
    """Returns [HRFlowable, Paragraph] for a section heading."""
    return [
        HRFlowable(width=CONTENT_W, thickness=0.8, color=RULE, spaceAfter=0),
        Paragraph(label.upper(), S["section_label"]),
    ]


# ── Info chip row ─────────────────────────────────────────────────
def _chips(items: list[tuple], S: dict) -> Table:
    """
    Renders a horizontal row of info chips.
    items = [(label, value), ...]
    """
    n = len(items)
    chip_w = CONTENT_W / n

    header_row = [Paragraph(label, S["chip_label"]) for label, _ in items]
    value_row  = [Paragraph(str(value), S["chip_value"]) for _, value in items]

    t = Table([header_row, value_row], colWidths=[chip_w] * n)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHTER),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEAFTER",     (0, 0), (-2, -1), 0.8, RULE),
        ("BOX",           (0, 0), (-1, -1), 0.8, RULE),
    ]))
    return t


# ── Steps table ───────────────────────────────────────────────────
def _steps_table(steps: list[str], S: dict) -> Table:
    rows = []
    for i, step in enumerate(steps):
        bg = LIGHTER if i % 2 == 0 else WHITE
        rows.append([
            Paragraph(str(i + 1), S["step_num"]),
            Paragraph(step, S["step_text"]),
        ])

    t = Table(rows, colWidths=[22, CONTENT_W - 22])
    style = [
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (0, -1),  0),
        ("LEFTPADDING",   (1, 0), (1, -1),  10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 0.8, RULE),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.5, RULE),
    ]
    # Alternating row backgrounds
    for i in range(len(rows)):
        bg = LIGHTER if i % 2 == 0 else WHITE
        style.append(("BACKGROUND", (1, i), (1, i), bg))
    # Step-number column always navy
    style.append(("BACKGROUND", (0, 0), (0, -1), NAVY))

    t.setStyle(TableStyle(style))
    return t


# ── Outcome card ──────────────────────────────────────────────────
def _outcome_card(outcome: str, tier: str, S: dict) -> Table:
    if outcome == "close":
        icon, heading = "✓", "Issue Resolved"
        text_style, bg = S["outcome_ok"], SUCCESS_BG
        border_color   = SUCCESS
        sub_text = "The user confirmed the issue was resolved. No further action required."
    elif tier == "2":
        icon, heading = "⚠", "Escalated to Tier 2 — Specialist Required"
        text_style, bg = S["outcome_esc"], DANGER_BG
        border_color   = DANGER
        sub_text = "Issue involves critical infrastructure, a security incident, or multiple affected users. Assigned to Tier 2 specialist team."
    else:
        icon, heading = "⚠", "Escalated to Human Agent"
        text_style, bg = S["outcome_esc"], DANGER_BG
        border_color   = DANGER
        sub_text = "Issue could not be resolved automatically after all troubleshooting steps. Transferred to a Tier 1 human agent for further assistance."

    content = [
        Paragraph(f"{icon}  {heading}", text_style),
        Spacer(1, 4),
        Paragraph(sub_text, S["outcome_sub"]),
    ]

    # Accent border on left: Table with a 4pt colored column
    inner = Table([[c] for c in content], colWidths=[CONTENT_W - 8])
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))

    outer = Table([[None, inner]], colWidths=[8, CONTENT_W - 8])
    outer.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), border_color),
        ("BACKGROUND",    (1, 0), (1, -1), bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("BOX",           (0, 0), (-1, -1), 0.8, border_color),
    ]))
    return outer


# ── LLM helpers ───────────────────────────────────────────────────
def _generate_summary(session: dict) -> str:
    """2-3 sentence professional case summary."""
    steps      = session.get("steps_taken", [])
    intent     = session.get("intent", "unknown")
    outcome    = session.get("outcome", "unknown")
    transcript = session.get("corrected_transcript", session.get("raw_transcript", ""))
    steps_block = "\n".join(f"- {s}" for s in steps) if steps else "None recorded."

    prompt = (
        f"Write a 2-3 sentence professional IT helpdesk ticket summary.\n\n"
        f"Issue category: {intent}\n"
        f"User report: {transcript}\n"
        f"Bot steps attempted:\n{steps_block}\n"
        f"Outcome: {outcome}\n\n"
        "Cover: what the problem was, what was tried, and how it ended. "
        "Be factual. No bullet points."
    )
    try:
        res = _groq().chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=200, temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Ticket] Summary error: {e}")
        return "Summary unavailable."


def _extract_steps(messages: list[str]) -> list[str]:
    """
    Distil verbose bot troubleshoot messages → clean 1-line action summaries.
    e.g. "Let's try restarting your VPN client — disconnect, reopen..."
      →  "Restart the VPN client"
    """
    if not messages:
        return []

    numbered = "\n".join(f"{i}. {m}" for i, m in enumerate(messages, 1))
    prompt = (
        "Below are IT helpdesk bot responses. Each contains a troubleshooting instruction.\n\n"
        f"{numbered}\n\n"
        "For each response, extract ONLY the core technical action as a short, clear line "
        "(e.g. 'Restart the VPN client', 'Run ipconfig /flushdns in elevated Command Prompt', "
        "'Reinstall the VPN client from the company portal').\n"
        "Do NOT include questions, filler phrases, or follow-up text.\n"
        "Return JSON: {\"steps\": [\"action 1\", \"action 2\", ...]}"
    )
    try:
        res = _groq().chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=300, temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Extract concise IT action steps. Return JSON with a 'steps' array."},
                {"role": "user",   "content": prompt}
            ]
        )
        data = json.loads(res.choices[0].message.content)
        extracted = data.get("steps") or next(
            (v for v in data.values() if isinstance(v, list)), []
        )
        return [str(s) for s in extracted] if extracted else messages
    except Exception as e:
        print(f"[Ticket] Step extraction error: {e}")
        return messages   # fallback: show raw messages


# ── PDF builder ───────────────────────────────────────────────────
def _build_pdf(ticket: dict, summary: str, steps: list[str], path: Path):
    S = _styles()

    # Custom doc template to apply page decorator
    class StyledDoc(BaseDocTemplate):
        def __init__(self, filename, **kwargs):
            super().__init__(filename, **kwargs)
            frame = Frame(
                MARGIN_L, MARGIN_B,
                CONTENT_W, PAGE_H - MARGIN_T - MARGIN_B,
                id="body", leftPadding=0, rightPadding=0,
                topPadding=0, bottomPadding=0,
            )
            decorator = _make_page_decorator(
                ticket["ticket_id"],
                ticket["timestamp"],
                ticket.get("tier", "1"),
                ticket.get("outcome", "close"),
            )
            self.addPageTemplates([
                PageTemplate(id="main", frames=[frame], onPage=decorator)
            ])

    doc = StyledDoc(
        str(path),
        pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T,  bottomMargin=MARGIN_B,
    )

    story = []

    # ── Info chips: Caller | Category | Tier | Outcome ────────────
    outcome_label = "Resolved" if ticket.get("outcome") == "close" else "Escalated"
    story.append(_chips([
        ("Caller",   ticket.get("caller_id", "Unknown")),
        ("Category", ticket.get("intent", "—").capitalize()),
        ("Tier",     ticket.get("tier", "1")),
        ("Outcome",  outcome_label),
    ], S))
    story.append(Spacer(1, 0.4 * cm))

    # ── Case summary ──────────────────────────────────────────────
    story.extend(_section("Case Summary", S))
    # Summary in a lightly tinted left-bordered card
    summary_inner = Table(
        [[Paragraph(summary, S["body"])]],
        colWidths=[CONTENT_W - 8]
    )
    summary_inner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    summary_card = Table([[None, summary_inner]], colWidths=[4, CONTENT_W - 4])
    summary_card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), ACCENT),
        ("BACKGROUND",    (1, 0), (1, -1), LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    story.append(summary_card)

    # ── Steps attempted ───────────────────────────────────────────
    story.extend(_section("Steps Attempted", S))
    if steps:
        story.append(_steps_table(steps, S))
    else:
        story.append(Paragraph("No troubleshooting steps were recorded.", S["muted"]))

    # ── Outcome ───────────────────────────────────────────────────
    story.extend(_section("Outcome", S))
    story.append(_outcome_card(
        ticket.get("outcome", "close"),
        ticket.get("tier", "1"),
        S
    ))

    doc.build(story)


# ── Public entrypoint ─────────────────────────────────────────────
def generate_ticket(session: dict) -> dict:
    ticket_id = f"TKT-{datetime.now():%Y%m%d-%H%M%S}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ticket = {
        "ticket_id":            ticket_id,
        "timestamp":            timestamp,
        "caller_id":            session.get("caller_id", "Unknown"),
        "tier":                 session.get("tier", "1"),
        "intent":               session.get("intent", "other"),
        "raw_transcript":       session.get("raw_transcript", ""),
        "corrected_transcript": session.get("corrected_transcript", ""),
        "asr_corrections":      session.get("corrections", []),
        "steps_attempted":      session.get("steps_taken", []),
        "outcome":              session.get("outcome", "unknown"),
        "escalation_reason":    session.get("escalation_reason", ""),
    }

    # LLM calls
    summary = _generate_summary(session)
    steps   = _extract_steps(session.get("steps_taken", []))
    ticket["summary"] = summary

    # Render PDF
    pdf_path = TICKETS_DIR / f"{ticket_id}.pdf"
    try:
        _build_pdf(ticket, summary, steps, pdf_path)
        ticket["pdf_path"] = str(pdf_path)
        print(f"[Ticket] PDF saved → {pdf_path}")
    except Exception as e:
        print(f"[Ticket] PDF export failed: {e}")
        ticket["pdf_path"] = None

    return ticket
