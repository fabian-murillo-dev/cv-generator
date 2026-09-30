# CV Generator

Multi-version CV system that generates role-specific resumes from a single base CV. Write your full CV once with tagged sections, then produce tailored versions for different job applications — each with a custom summary, filtered skills, ATS keywords, and a fit analysis against the job posting.

## Recommended: Use It with Claude Code

This project is designed to be driven by an AI assistant — specifically [Claude Code](https://claude.com/claude-code). The Python scripts only assemble and render the CV; the tailoring work (reading the job posting, writing the summary, choosing tags, estimating the match and analyzing fit) is done by the AI following the instructions in [`CLAUDE.md`](CLAUDE.md), which Claude Code loads automatically.

**Workflow with Claude Code:**

1. Install the dependencies (see [Setup](#setup)).
2. Open this folder in Claude Code (`cd cv-generator && claude`).
3. Say hi. Claude will ask who the CV is for:
   - **New person** — paste the base CV (or point to a file) and pick a color palette. Claude creates `CVs/<PersonName>/` with the tagged `cv_base.md` and `style.yaml`.
   - **Existing person** — Claude shows a summary of their `cv_base.md` to confirm.
4. Paste the job posting (or a job title) and tell Claude where you found it (LinkedIn, Indeed, company site...).
5. Claude generates the role config, runs both scripts, and shows you in the chat:
   - Match % and overall recommendation (Apply / Apply with reservations / Consider skipping)
   - Deal breakers, if any
   - Requirements analysis table (met / partial / unmet)
   - Strong and weak points, and numbered action items
   - Paths to the generated `.md` and `.pdf`

**Without an AI:** everything still works, but you have to write each role config in `roles/` by hand (see [Role Config](#role-config)). Only `role` and `summary` are strictly required; the analysis fields are optional.

## How It Works

1. **Base CV** (`cv_base.md`) — Your complete CV in Markdown. Skill groups and experience entries are annotated with HTML comment tags (e.g. `<!-- tag:instrumentation -->`).
2. **Role configs** (`roles/*.yaml`) — One YAML file per job application, specifying which tags to include, a tailored summary, extra skills, ATS keywords, and the fit analysis.
3. **Generate** — `generate_cv.py` assembles a tailored CV by filtering the base with the role config, and adds an entry to `positions.md`.
4. **Export** — `export_pdf.py` strips tag comments, renders a clean, styled PDF using the person's palette, and prints a feedback summary from the role config.

## Project Structure

```
CLAUDE.md               # Instructions for Claude Code (the AI workflow)
generate_cv.py          # Reads base CV + role config, outputs tailored .md
export_pdf.py           # Converts output .md files to styled PDFs
CVs/
  ├── Sample/           # Example CV (tracked in git)
  │   ├── cv_base.md
  │   ├── positions.md
  │   ├── roles/
  │   └── output/
  └── <PersonName>/     # Real CVs (gitignored)
      ├── cv_base.md    # Master CV with tagged sections
      ├── positions.md  # Auto-generated position tracker
      ├── style.yaml    # PDF color palette (optional)
      ├── roles/        # .yaml configs (one per job application)
      └── output/       # Generated .md and .pdf files
```

Each folder under `CVs/` is a self-contained CV project. Only `CVs/Sample/` is tracked in git — all other person folders are gitignored. The whole project is portable: zip it and send it, and all configuration travels with it.

## Setup

```bash
pip install pyyaml fpdf2
```

## Usage

```bash
# List available roles
python3 generate_cv.py --cv-dir CVs/MyCV --list

# Generate a tailored CV
python3 generate_cv.py --cv-dir CVs/MyCV <role_name>

# Export to PDF
python3 export_pdf.py --cv-dir CVs/MyCV <role_name>

# Export all generated CVs to PDF
python3 export_pdf.py --cv-dir CVs/MyCV --all
```

If `--cv-dir` is omitted, the scripts default to `CVs/Sample`.

## Tagging System

Tag skill groups, experience entries, and certifications in `cv_base.md` with HTML comments. Tags are fully custom — you define whatever tags make sense for your CV. For example:

```markdown
## Core Skills

<!-- tag:frontend -->
- React, TypeScript, Next.js
- Responsive design and accessibility

<!-- tag:backend -->
- Node.js, Python, Go
- REST API and GraphQL design
```

How tags are applied:

- **Skills and certifications** — only groups whose tag is in `include_tags` are kept.
- **Experience** — each job (`### ` heading) is kept if its *first* tag is in `include_tags`. Jobs without a tag are always kept.
- **Education, memberships, languages** — always included.

Section headings can be in English or Spanish (e.g. `Core Skills` / `Habilidades`, `Professional Experience` / `Experiencia Laboral`); the original heading is preserved in the output.

The `CVs/Sample/` folder contains a working example with its own set of tags — see it for a complete reference.

## Role Config

```yaml
role: Full Stack Developer                 # Title shown on the CV (required)
company: Acme Corp
description: Full stack role for internal tools team
match: 80%
source: LinkedIn
summary: >                                  # Role-specific summary (required)
  Full Stack Developer with 5+ years of experience...
include_tags:
  - frontend
  - backend
extra_skills:
  - CI/CD pipelines
  - Cloud infrastructure (AWS)
ats_keywords:                               # Embedded as a hidden HTML comment
  - full stack developer
  - React
  - Node.js

# Fit analysis (printed by export_pdf.py; generated by the AI in the Claude Code workflow)
feedback: >
  Strong match on the core stack; main gap is cloud experience.
overall_recommendation: "Apply - core stack matches, cloud gap is addressable"
deal_breakers: []
strong_points:
  - "5 years of React - maps directly to the frontend requirement"
weak_points:
  - "MODERATE: limited AWS experience - addressable with a certification"
review_notes:
  - "Highlight the internal dashboard project in the cover letter"
requirements_analysis:
  - requirement: "3+ years React"
    status: met          # met | partial | unmet
    detail: "5 years of production React"
```

See `CVs/Sample/roles/` for complete examples.

## PDF Design & Palettes

Every CV uses the same layout: job/degree title in bold with dates right-aligned, company in the accent color with location in grey, core skills in two balanced columns, and headings kept together with their first lines (never orphaned at the bottom of a page).

Colors come from `CVs/<PersonName>/style.yaml`:

```yaml
palette: forest
```

| Palette | Look | Good for |
|---------|------|----------|
| `classic` | Navy blue, neutral | Default when there's no `style.yaml` |
| `executive` | Graphite + deep navy | Formal/conservative industries |
| `forest` | Deep forest green | Environmental, climate, outdoors |
| `ocean` | Deep teal | Fresh, modern, tech |
| `tech` | Slate + electric indigo | Software, startups, developer roles |
| `burgundy` | Wine red | Finance, legal, hospitality |
| `terracotta` | Burnt orange | Warm, youthful, creative |

**Character set:** the PDF uses core Helvetica, which only supports Latin-1. Avoid em/en dashes (—, –), curly quotes and bullets (•) in `cv_base.md` and role configs; use `-` and straight quotes instead. Accented letters (á, é, ñ) are fine.

## Position Tracking

Every time `generate_cv.py` runs, it automatically adds an entry to `positions.md` in the person's CV folder. The tracker is a Markdown table with the following columns:

| Column | Description |
|--------|-------------|
| Date | When the CV was generated |
| Company | From the `company` field in the role YAML |
| Position | From the `role` field in the role YAML |
| Description | From the `description` field in the role YAML |
| Source | From the `source` field in the role YAML |
| CV Sent | Checkbox — mark `[x]` when the CV has been sent |
| Replied | Checkbox — mark `[x]` when the company replies |
| Interview | Checkbox — mark `[x]` when an interview is scheduled |
| CV | Link to the generated PDF |
| Match | From the `match` field in the role YAML |

Update the checkboxes manually (`[ ]` → `[x]`) as the application progresses. Duplicate entries for the same role are skipped automatically.

## Adding a New CV

**With Claude Code:** open the project and tell Claude the person's name — it handles the rest.

**Manually:**

1. Create a folder under `CVs/` (e.g. `CVs/JaneDoe/`) with `roles/` and `output/` subdirectories
2. Write your `cv_base.md` with tagged sections
3. Optionally add a `style.yaml` with your palette
4. Create a role config in `roles/` for each job application
5. Run `generate_cv.py` then `export_pdf.py`
