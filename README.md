# CV Generator

Multi-version CV system that generates role-specific resumes from a single base CV. Write your full CV once with tagged sections, then produce tailored versions for different job applications — each with a custom summary, filtered skills, and ATS keywords.

## How It Works

1. **Base CV** (`cv_base.md`) — Your complete CV in Markdown. Skill groups and experience bullets are annotated with HTML comment tags (e.g. `<!-- tag:instrumentation -->`).
2. **Role configs** (`roles/*.yaml`) — One YAML file per job application, specifying which tags to include, a tailored summary, extra skills, and ATS keywords.
3. **Generate** — `generate_cv.py` assembles a tailored CV by filtering the base with the role config.
4. **Export** — `export_pdf.py` strips tag comments and renders a clean, styled PDF.

## Project Structure

```
generate_cv.py          # Reads base CV + role config, outputs tailored .md
export_pdf.py           # Converts output .md files to styled PDFs
CVs/
  ├── Sample/           # Example CV (tracked in git)
  │   ├── cv_base.md
  │   ├── roles/
  │   └── output/
  └── <PersonName>/     # Real CVs (gitignored)
      ├── cv_base.md    # Master CV with tagged sections
      ├── roles/        # .yaml configs (one per job application)
      └── output/       # Generated .md and .pdf files
```

Each folder under `CVs/` is a self-contained CV project. Only `CVs/Sample/` is tracked in git — all other person folders are gitignored.

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

Tag skill groups and experience bullets in `cv_base.md` with HTML comments. Tags are fully custom — you define whatever tags make sense for your CV. For example:

```markdown
## Core Skills

<!-- tag:frontend -->
- React, TypeScript, Next.js
- Responsive design and accessibility

<!-- tag:backend -->
- Node.js, Python, Go
- REST API and GraphQL design
```

Then reference those tags in a role config to include only the relevant groups:

```yaml
role: Full Stack Developer
summary: >
  Full Stack Developer with 5+ years of experience...
include_tags:
  - frontend
  - backend
extra_skills:
  - CI/CD pipelines
  - Cloud infrastructure (AWS)
ats_keywords:
  - full stack developer
  - React
  - Node.js
```

The `CVs/Sample/` folder contains a working example with its own set of tags — see it for a complete reference.

## Adding a New CV

1. Create a folder under `CVs/` (e.g. `CVs/JaneDoe/`) with `roles/` and `output/` subdirectories
2. Write your `cv_base.md` with tagged sections
3. Create a role config in `roles/` for each job application
4. Run `generate_cv.py` then `export_pdf.py`
