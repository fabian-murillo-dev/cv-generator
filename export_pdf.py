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

from generate_cv import SECTION_ALIASES

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

# Color palettes. Each person picks one in CVs/<Person>/style.yaml (`palette: forest`).
#   dark   - name and job/degree titles
#   accent - section headings, companies, links, bullets, header rule
#   text   - body text
#   muted  - dates, locations, contact separators
#   light  - thin rules under section headings
# Accents are kept dark enough (>= 7:1 on white) to survive greyscale printing.
PALETTES = {
    "classic": {    # navy blue - neutral default
        "dark": (13, 27, 42), "accent": (44, 82, 130), "text": (40, 40, 40),
        "muted": (110, 110, 110), "light": (203, 213, 224),
    },
    "executive": {  # graphite + deep navy - formal, conservative industries
        "dark": (22, 24, 29), "accent": (31, 52, 84), "text": (38, 38, 38),
        "muted": (105, 105, 110), "light": (200, 204, 210),
    },
    "forest": {     # deep forest green - environmental, climate, outdoors
        "dark": (18, 38, 31), "accent": (11, 79, 58), "text": (40, 40, 40),
        "muted": (105, 112, 108), "light": (196, 216, 206),
    },
    "ocean": {      # deep teal - fresh, modern, tech
        "dark": (12, 36, 48), "accent": (0, 92, 110), "text": (40, 40, 40),
        "muted": (104, 112, 116), "light": (190, 214, 220),
    },
    "tech": {       # slate + electric indigo - software, startups, developer roles
        "dark": (15, 23, 42), "accent": (67, 56, 202), "text": (30, 41, 59),
        "muted": (100, 116, 139), "light": (205, 208, 245),
    },
    "burgundy": {   # wine red - confident, finance/legal/hospitality
        "dark": (38, 20, 25), "accent": (118, 28, 46), "text": (40, 40, 40),
        "muted": (112, 104, 106), "light": (222, 200, 205),
    },
    "terracotta": { # burnt orange - warm, youthful, creative
        "dark": (45, 28, 20), "accent": (150, 62, 26), "text": (40, 40, 40),
        "muted": (112, 106, 102), "light": (230, 208, 196),
    },
}
DEFAULT_PALETTE = "classic"

COLOR_DARK = COLOR_ACCENT = COLOR_TEXT = COLOR_MUTED = COLOR_LIGHT = None


def apply_palette(cv_dir: Path) -> str:
    """Load the palette named in <cv_dir>/style.yaml (falls back to the default)."""
    global COLOR_DARK, COLOR_ACCENT, COLOR_TEXT, COLOR_MUTED, COLOR_LIGHT
    name = DEFAULT_PALETTE
    style_path = cv_dir / "style.yaml"
    if style_path.exists():
        name = (yaml.safe_load(style_path.read_text()) or {}).get("palette", DEFAULT_PALETTE)
    if name not in PALETTES:
        print(f"Warning: unknown palette '{name}', using '{DEFAULT_PALETTE}'. "
              f"Available: {', '.join(PALETTES)}")
        name = DEFAULT_PALETTE
    pal = PALETTES[name]
    COLOR_DARK, COLOR_ACCENT, COLOR_TEXT = pal["dark"], pal["accent"], pal["text"]
    COLOR_MUTED, COLOR_LIGHT = pal["muted"], pal["light"]
    return name


apply_palette(DEFAULT_CV_DIR)

MARGIN = 18
LINE_H = 4.4          # body line height (mm)
BODY_SIZE = 9.5
DATE_RE = re.compile(r"(19|20)\d{2}|Present|Presente|Actual", re.IGNORECASE)


class CVPDF(FPDF):
    def __init__(self):
        super().__init__(format="Letter")
        self.set_auto_page_break(auto=True, margin=MARGIN)
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.add_page()

    @property
    def content_width(self):
        return self.w - self.l_margin - self.r_margin

    def ensure_space(self, height):
        """Start a new page if `height` mm won't fit, so blocks aren't orphaned."""
        if self.get_y() + height > self.page_break_trigger:
            self.add_page()

    def rule(self, color, width, gap_after):
        self.set_draw_color(*color)
        self.set_line_width(width)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(gap_after)


def clean_markdown(text: str) -> str:
    """Remove tag comments and ATS keyword comments."""
    text = re.sub(r"^\s*<!--.*?-->\s*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*<!--\s*ATS Keywords:.*?-->\s*", "", text, flags=re.DOTALL)
    text = text.replace(" -- ", " - ")
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


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL_RE = re.compile(r"https?://\S+|www\.\S+")
PHONE_RE = re.compile(r"\+?\(?\+?\d[\d\s().-]{6,}\d")


def render_contact_line(pdf, line):
    """Render a contact line, making emails/URLs/phones clickable."""
    line = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r"\1|||LINK|||\2|||END|||", line)

    parts = line.split(" | ") if " | " in line else [line]
    for i, part in enumerate(parts):
        if i > 0:
            pdf.write(5, "  |  ")

        # Markdown link expansion
        md_link_match = re.match(r"(.*?)\|\|\|LINK\|\|\|(.*?)\|\|\|END\|\|\|(.*)", part)
        if md_link_match:
            label, url, after = md_link_match.group(1), md_link_match.group(2), md_link_match.group(3)
            pdf.set_text_color(*COLOR_ACCENT)
            pdf.write(5, label, link=url)
            pdf.set_text_color(*COLOR_MUTED)
            if after:
                pdf.write(5, after)
            continue

        email_match = EMAIL_RE.search(part)
        url_match = URL_RE.search(part)
        phone_match = PHONE_RE.search(part) if not email_match and not url_match else None

        if email_match:
            before = part[:email_match.start()]
            after = part[email_match.end():]
            email = email_match.group()
            if before:
                pdf.write(5, before)
            pdf.set_text_color(*COLOR_ACCENT)
            pdf.write(5, email, link=f"mailto:{email}")
            pdf.set_text_color(*COLOR_MUTED)
            if after:
                pdf.write(5, after)
        elif url_match:
            before = part[:url_match.start()]
            after = part[url_match.end():]
            url = url_match.group()
            href = url if url.startswith("http") else f"https://{url}"
            if before:
                pdf.write(5, before)
            pdf.set_text_color(*COLOR_ACCENT)
            pdf.write(5, url, link=href)
            pdf.set_text_color(*COLOR_MUTED)
            if after:
                pdf.write(5, after)
        elif phone_match:
            before = part[:phone_match.start()]
            after = part[phone_match.end():]
            phone = phone_match.group()
            tel = re.sub(r"[^\d+]", "", phone)
            if before:
                pdf.write(5, before)
            pdf.set_text_color(*COLOR_ACCENT)
            pdf.write(5, phone, link=f"tel:{tel}")
            pdf.set_text_color(*COLOR_MUTED)
            if after:
                pdf.write(5, after)
        else:
            pdf.write(5, part)
    pdf.ln(5)


def render_text_with_bold(pdf, text, size=BODY_SIZE):
    """Render text that may contain **bold** segments."""
    pdf.set_font("Helvetica", "", size)
    pdf.set_text_color(*COLOR_TEXT)

    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font("Helvetica", "B", size)
            pdf.write(LINE_H, part[2:-2])
            pdf.set_font("Helvetica", "", size)
        else:
            pdf.write(LINE_H, part)
    pdf.ln(LINE_H)


def split_org_line(content: str):
    """Split '**Org** | Location | Dates' into (org, location, dates)."""
    parts = [p.strip().strip("*").strip() for p in content.split("|")]
    dates = ""
    if len(parts) > 1 and DATE_RE.search(parts[-1]):
        dates = parts.pop()
    org = parts[0] if parts else ""
    location = ", ".join(parts[1:])
    return org, location, dates.replace("--", "-")


def is_org_line(content: str) -> bool:
    return content.startswith("**") and "|" in content


def bullet_height(pdf, text, width, size):
    pdf.set_font("Helvetica", "", size)
    lines = pdf.multi_cell(width, LINE_H, text, dry_run=True, output="LINES")
    return len(lines) * LINE_H + 0.8


def draw_bullet(pdf, text, x, width, size=BODY_SIZE):
    """A small filled dot marker + left-aligned wrapped text."""
    indent = 4
    y = pdf.get_y()
    pdf.set_fill_color(*COLOR_ACCENT)
    r = 0.55
    pdf.ellipse(x + 1.2 - r, y + LINE_H / 2 - r, 2 * r, 2 * r, style="F")
    pdf.set_xy(x + indent, y)
    pdf.set_font("Helvetica", "", size)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.multi_cell(width - indent, LINE_H, text, align="L",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(0.8)


def render_skills_grid(pdf, items):
    """Skills as two balanced newspaper-style columns (left fills first)."""
    gap = 8
    col_w = (pdf.content_width - gap) / 2
    size = 9.2
    heights = [bullet_height(pdf, t, col_w - 4, size) for t in items]

    # Split where the left column first reaches half the total height
    total, running, split = sum(heights), 0, len(items)
    for k, h in enumerate(heights):
        if running + h / 2 > total / 2:
            split = k
            break
        running += h
    split = max(split, (len(items) + 1) // 2 if len(items) < 4 else 1)
    columns = [(items[:split], heights[:split]), (items[split:], heights[split:])]
    col_height = max(sum(hs) for _, hs in columns)

    if col_height > pdf.page_break_trigger - pdf.t_margin:
        # Too long for one page: fall back to a single column
        for text in items:
            pdf.ensure_space(bullet_height(pdf, text, pdf.content_width - 4, size))
            draw_bullet(pdf, text, pdf.l_margin, pdf.content_width, size)
        return

    pdf.ensure_space(col_height)
    top = pdf.get_y()
    for col, (col_items, _) in enumerate(columns):
        pdf.set_y(top)
        for text in col_items:
            draw_bullet(pdf, text, pdf.l_margin + col * (col_w + gap), col_w, size)
    pdf.set_y(top + col_height)


def render_entry_header(pdf, title, org_line, first_bullet):
    """Job/degree header: bold title with right-aligned dates, then org in accent + location."""
    org, location, dates = split_org_line(org_line) if org_line else ("", "", "")
    w = pdf.content_width

    needed = 6 + (5 if org_line else 0)
    if first_bullet:
        needed += bullet_height(pdf, first_bullet, w - 4, BODY_SIZE)
    pdf.ensure_space(needed + 2)
    pdf.ln(2.2)

    pdf.set_font("Helvetica", "B", 9)
    date_w = pdf.get_string_width(dates) + 1 if dates else 0
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(w - date_w, 5.5, title, new_x=XPos.RIGHT, new_y=YPos.TOP)
    if dates:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*COLOR_MUTED)
        pdf.cell(date_w, 5.5, dates, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    else:
        pdf.ln(5.5)

    if org_line:
        pdf.set_font("Helvetica", "B", 9.8)
        pdf.set_text_color(*COLOR_ACCENT)
        pdf.write(5, org)
        if location:
            pdf.set_font("Helvetica", "", 9.3)
            pdf.set_text_color(*COLOR_MUTED)
            pdf.write(5, f"   {location}")
        pdf.ln(5)
    pdf.ln(0.8)


def render_section_heading(pdf, title, next_block_height):
    pdf.ensure_space(12 + next_block_height)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*COLOR_ACCENT)
    pdf.set_char_spacing(1.2)
    pdf.cell(pdf.content_width, 6, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_char_spacing(0)
    pdf.ln(0.5)
    pdf.rule(COLOR_LIGHT, 0.35, 2.5)


def build_pdf(blocks: list) -> CVPDF:
    pdf = CVPDF()
    w = pdf.content_width
    skill_names = {n.lower() for n in SECTION_ALIASES["skills"]}
    section = ""

    i = 0
    while i < len(blocks):
        btype, content = blocks[i]
        nxt = blocks[i + 1] if i + 1 < len(blocks) else (None, "")

        if btype == "h1":
            pdf.set_font("Helvetica", "B", 22)
            pdf.set_text_color(*COLOR_DARK)
            pdf.cell(w, 10, content, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        elif btype == "bold_line" and i > 0 and blocks[i - 1][0] == "h1":
            # Role title under the name
            pdf.set_font("Helvetica", "", 12.5)
            pdf.set_text_color(*COLOR_ACCENT)
            pdf.cell(w, 6.5, content, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1.5)

        elif btype == "text" and "|" in content and ("@" in content or "](http" in content):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*COLOR_MUTED)
            render_contact_line(pdf, content)
            # Close the header with an accent rule after the last contact line
            n_type, n_content = nxt
            if not (n_type == "text" and "|" in n_content):
                pdf.ln(1.5)
                pdf.rule(COLOR_ACCENT, 0.6, 1)

        elif btype == "h2":
            section = content.lower()
            # Keep the heading with the start of its content
            if nxt[0] == "h3":
                follow = 22
            elif nxt[0] == "text":
                follow = 14
            else:
                follow = 10
            render_section_heading(pdf, content, follow)

        elif btype == "h3":
            org_line = nxt[1] if nxt[0] in ("bold_line", "text") and is_org_line(nxt[1]) else ""
            j = i + (2 if org_line else 1)
            first_bullet = blocks[j][1] if j < len(blocks) and blocks[j][0] == "bullet" else ""
            render_entry_header(pdf, content, org_line, first_bullet)
            if org_line:
                i += 1

        elif btype == "bold_line":
            # Standalone bold line (e.g. a skill category subheading)
            pdf.ensure_space(12)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*COLOR_DARK)
            pdf.cell(w, 6, content, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        elif btype == "bullet":
            if section in skill_names:
                items = []
                while i < len(blocks) and blocks[i][0] == "bullet":
                    items.append(blocks[i][1])
                    i += 1
                render_skills_grid(pdf, items)
                continue
            pdf.ensure_space(bullet_height(pdf, content, w - 4, BODY_SIZE))
            draw_bullet(pdf, content, pdf.l_margin, w)

        elif btype == "text":
            pdf.set_font("Helvetica", "", BODY_SIZE)
            pdf.set_text_color(*COLOR_TEXT)
            if "**" in content:
                render_text_with_bold(pdf, content)
            else:
                pdf.multi_cell(w, LINE_H + 0.3, content, align="J",
                               new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

        # "hr" blocks are skipped: section headings carry their own rule

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

    palette = apply_palette(cv_dir)
    raw = md_path.read_text()
    cleaned = clean_markdown(raw)
    blocks = parse_clean_md(cleaned)
    pdf = build_pdf(blocks)

    pdf_path = output_dir / f"cv_{role_name}.pdf"
    pdf.output(str(pdf_path))

    print(f"PDF exported: {pdf_path}")
    print(f"    Source:   {md_path.name}")
    print(f"    Palette:  {palette}")
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
