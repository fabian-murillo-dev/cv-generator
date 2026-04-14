#!/usr/bin/env python3
"""
Export a generated CV markdown to a styled PDF.

Usage:
    python export_pdf.py <role_name>
    python export_pdf.py --all
    python export_pdf.py --cv-dir CVs/MyCV <role_name>

Examples:
    python export_pdf.py fluor_controls_engineer
    python export_pdf.py worley_automation_consultant
    python export_pdf.py --all
    python export_pdf.py --cv-dir CVs/MyCV fluor_controls_engineer
"""

import sys
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install it with: pip install pyyaml")
    sys.exit(1)

from fpdf import FPDF
from fpdf.enums import XPos, YPos

DEFAULT_CV_DIR = Path(__file__).parent / "CVs" / "Sample"


def get_cv_dir(args: list) -> tuple:
    """Extract --cv-dir from args, return (cv_dir, remaining_args)."""
    if "--cv-dir" in args:
        idx = args.index("--cv-dir")
        if idx + 1 >= len(args):
            print("Error: --cv-dir requires a path argument")
            sys.exit(1)
        cv_dir = Path(__file__).parent / args[idx + 1]
        remaining = args[:idx] + args[idx + 2:]
        return cv_dir, remaining
    return DEFAULT_CV_DIR, args

# Color palette
COLOR_DARK = (13, 27, 42)
COLOR_ACCENT = (44, 82, 130)
COLOR_TEXT = (26, 26, 26)
COLOR_LIGHT = (203, 213, 224)


class CVPDF(FPDF):
    def __init__(self):
        super().__init__(format="Letter")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 18, 20)
        self.add_page()

    def _set_font_safe(self, family, style="", size=10):
        self.set_font(family, style, size)

    def section_line(self):
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), self.w - 20, self.get_y())
        self.ln(4)

    def thin_line(self):
        self.set_draw_color(*COLOR_LIGHT)
        self.set_line_width(0.2)
        self.line(20, self.get_y(), self.w - 20, self.get_y())
        self.ln(3)


def clean_markdown(text: str) -> str:
    """Remove tag comments and ATS keyword comments."""
    text = re.sub(r"^\s*<!--.*?-->\s*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*<!--\s*ATS Keywords:.*?-->\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(---\s*\n\s*){2,}", "---\n\n", text)
    return text.strip()


def parse_clean_md(text: str) -> list:
    """Parse cleaned markdown into structured blocks."""
    blocks = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("# ") and not line.startswith("## "):
            blocks.append(("h1", line[2:].strip()))
        elif line.startswith("### "):
            blocks.append(("h3", line[4:].strip()))
        elif line.startswith("## "):
            blocks.append(("h2", line[3:].strip()))
        elif line.startswith("---"):
            blocks.append(("hr", ""))
        elif line.startswith("- "):
            blocks.append(("bullet", line[2:].strip()))
        elif line.startswith("**") and line.endswith("**"):
            blocks.append(("bold_line", line.strip("* ")))
        elif line.strip():
            blocks.append(("text", line.strip()))
        i += 1

    return blocks


def render_text_with_bold(pdf, text, size=10):
    """Render text that may contain **bold** segments."""
    pdf.set_font("Helvetica", "", size)
    pdf.set_text_color(*COLOR_TEXT)

    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font("Helvetica", "B", size)
            pdf.write(5, part[2:-2])
            pdf.set_font("Helvetica", "", size)
        else:
            pdf.write(5, part)
    pdf.ln(5)


def build_pdf(blocks: list) -> CVPDF:
    pdf = CVPDF()
    effective_width = pdf.w - 40

    i = 0
    while i < len(blocks):
        btype, content = blocks[i]

        if btype == "h1":
            pdf.set_font("Helvetica", "B", 22)
            pdf.set_text_color(*COLOR_DARK)
            pdf.cell(effective_width, 10, content, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

        elif btype == "bold_line":
            # Check if this is the role title (right after h1) or a subheading
            if i > 0 and blocks[i - 1][0] == "h1":
                pdf.set_font("Helvetica", "", 12)
                pdf.set_text_color(*COLOR_ACCENT)
                pdf.cell(effective_width, 6, content, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(1)
            elif content.endswith(("Present", "2020", "2017", "2014", "2015", "2016", "2018", "2019", "2021", "2022", "2023", "2024", "2025", "2026")):
                # Company | Location | Date line
                pdf.set_font("Helvetica", "B", 9.5)
                pdf.set_text_color(*COLOR_TEXT)
                pdf.cell(effective_width, 5, content, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(1)
            else:
                # Skill category subheading
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*COLOR_DARK)
                pdf.cell(effective_width, 6, content, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(0.5)

        elif btype == "text":
            # Handle contact info line or paragraphs
            if "|" in content and "@" in content:
                clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", content)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*COLOR_TEXT)
                pdf.cell(effective_width, 5, clean, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(2)
            else:
                render_text_with_bold(pdf, content, 10)
                pdf.ln(1)

        elif btype == "h2":
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*COLOR_DARK)
            pdf.cell(effective_width, 7, content.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.section_line()

        elif btype == "h3":
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.cell(effective_width, 6, content, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        elif btype == "bullet":
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(*COLOR_TEXT)
            x = pdf.get_x()
            pdf.cell(5, 4.5, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.multi_cell(effective_width - 5, 4.5, content)
            pdf.ln(0.5)

        elif btype == "hr":
            pdf.thin_line()

        i += 1

    return pdf


def print_feedback(role_config: dict):
    """Print position feedback summary from the role config."""
    match = role_config.get("match")
    feedback = role_config.get("feedback")
    strong = role_config.get("strong_points", [])
    weak = role_config.get("weak_points", [])
    review = role_config.get("review_notes", [])
    reqs = role_config.get("requirements_analysis", [])
    recommendation = role_config.get("overall_recommendation")
    deal_breakers = role_config.get("deal_breakers", [])

    if not any([match, feedback, strong, weak, review, reqs, recommendation, deal_breakers]):
        return

    company = role_config.get("company", "Unknown")
    role = role_config.get("role", "Unknown")
    sep = "=" * 60

    print()
    print(sep)
    print(f"  POSITION FEEDBACK: {role} @ {company}")
    print(sep)

    if match is not None:
        match_str = str(match).rstrip("%")
        try:
            match_val = int(match_str)
            if match_val >= 75:
                indicator = "STRONG"
            elif match_val >= 50:
                indicator = "MODERATE"
            else:
                indicator = "WEAK"
        except ValueError:
            indicator = ""
        print(f"\n  Match:  {match_str}% — {indicator}" if indicator else f"\n  Match:  {match}")

    if recommendation:
        print(f"  Recommendation:  {recommendation}")

    if feedback:
        print(f"\n  Summary:\n    {feedback}")

    if deal_breakers:
        print(f"\n  {'!' * 3} DEAL BREAKERS {'!' * 3}")
        for db in deal_breakers:
            print(f"    !! {db}")

    if reqs:
        print(f"\n  Requirements Analysis:")
        status_icons = {"met": "[MET]    ", "partial": "[PARTIAL]", "unmet": "[UNMET]  "}
        for req in reqs:
            if isinstance(req, dict):
                status = status_icons.get(req.get("status", ""), "         ")
                name = req.get("requirement", "")
                detail = req.get("detail", "")
                print(f"    {status}  {name}")
                if detail:
                    print(f"               {detail}")
            else:
                print(f"    - {req}")

    if strong:
        print(f"\n  Strong Points ({len(strong)}):")
        for s in strong:
            print(f"    + {s}")

    if weak:
        print(f"\n  Weak Points ({len(weak)}):")
        for w in weak:
            print(f"    - {w}")

    if review:
        print(f"\n  Action Items:")
        for i, r in enumerate(review, 1):
            print(f"    {i}. {r}")

    print()
    print(sep)


def export_role(role_name: str, cv_dir: Path):
    output_dir = cv_dir / "output"
    roles_dir = cv_dir / "roles"

    # Try _clean version first, fall back to regular
    clean_path = output_dir / f"cv_{role_name}_clean.md"
    regular_path = output_dir / f"cv_{role_name}.md"

    if clean_path.exists():
        md_path = clean_path
    elif regular_path.exists():
        md_path = regular_path
    else:
        print(f"Error: no CV found for '{role_name}' in {output_dir}")
        return False

    raw = md_path.read_text()
    cleaned = clean_markdown(raw)
    blocks = parse_clean_md(cleaned)
    pdf = build_pdf(blocks)

    pdf_path = output_dir / f"cv_{role_name}.pdf"
    pdf.output(str(pdf_path))

    print(f"PDF exported: {pdf_path}")
    print(f"    Source:   {md_path.name}")
    print(f"    Size:     {pdf_path.stat().st_size / 1024:.0f} KB")

    # Print feedback from role config if available
    role_path = roles_dir / f"{role_name}.yaml"
    if role_path.exists():
        role_config = yaml.safe_load(role_path.read_text())
        print_feedback(role_config)

    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    cv_dir, args = get_cv_dir(sys.argv[1:])

    if not cv_dir.exists():
        print(f"Error: CV directory '{cv_dir}' does not exist")
        sys.exit(1)

    if not args:
        print(__doc__.strip())
        sys.exit(1)

    if args[0] == "--all":
        output_dir = cv_dir / "output"
        md_files = sorted(output_dir.glob("cv_*_clean.md"))
        if not md_files:
            md_files = sorted(output_dir.glob("cv_*.md"))
        if not md_files:
            print(f"No CV files found in {output_dir}")
            sys.exit(1)
        for f in md_files:
            name = f.stem.replace("cv_", "").replace("_clean", "")
            export_role(name, cv_dir)
            print()
        return

    export_role(args[0], cv_dir)


if __name__ == "__main__":
    main()
