from pathlib import Path
import unicodedata
from uuid import uuid4

from fpdf import FPDF

from app.schemas import Panel

ROOT = Path(__file__).resolve().parents[2]
EXPORTS_DIR = ROOT / "static" / "exports"
PANELS_DIR = ROOT / "static" / "panels"


def _pdf_text(value: str) -> str:
    """Convert generated Unicode text to characters supported by core PDF fonts."""
    # NFKD preserves readable Latin text (for example, é -> e) and drops emoji,
    # smart punctuation, and other glyphs unavailable in FPDF's built-in fonts.
    substitutions = str.maketrans({
        "‘": "'", "’": "'", "‚": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "…": "...", "•": "-",
    })
    return unicodedata.normalize("NFKD", value.translate(substitutions)).encode("ascii", "replace").decode("ascii")


def save_pdf(title: str, panels: list[Panel]) -> str:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for panel in panels:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        # Built-in Helvetica is not a Unicode font; normalize text before passing it to FPDF.
        heading = f"{title} - Panel {panel.number}: {panel.title}"
        pdf.multi_cell(0, 12, _pdf_text(heading))
        if panel.image_url:
            image_path = PANELS_DIR / Path(panel.image_url).name
            if image_path.exists():
                pdf.image(str(image_path), x=15, y=pdf.get_y() + 4, w=180, h=105)
                pdf.ln(110)
        pdf.set_font("Helvetica", "I", 12)
        pdf.multi_cell(0, 8, _pdf_text(panel.scene_description))
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(0, 8, _pdf_text(panel.narration))
        if panel.dialogue:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 8, _pdf_text(panel.dialogue))
    filename = f"comic-{uuid4().hex[:12]}.pdf"
    pdf.output(str(EXPORTS_DIR / filename))
    return filename
