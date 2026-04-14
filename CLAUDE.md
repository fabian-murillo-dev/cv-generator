# CV Generator

Multi-version CV system that generates role-specific resumes from a single base CV.

## On Conversation Start

When a new conversation begins in this project, first ask the user:
1. **Who is this CV for?** (person's name -- this determines the folder under `CVs/`)

Then check if the person's folder exists under `CVs/`:

- **Exact match** (folder exists with that name): Treat as an existing person.
- **Fuzzy match** (a folder exists with a similar name, e.g. user says "Diego" and `CVs/DiegoMurillo/` exists): Ask the user to confirm whether that's the same person before proceeding. If yes, treat as existing. If no, treat as new.
- **No match** (no folder matches): Treat as a new person.

Then follow the appropriate path:

- **New person**:
  1. Ask the user to provide the base CV content (paste it or point to a file).
  2. Create `CVs/<PersonName>/` with `roles/` and `output/` subdirectories. Save the base CV as `CVs/<PersonName>/cv_base.md`.
  3. Then ask **what position they are applying to** (job title or paste a job description).
- **Existing person**:
  1. Read their `cv_base.md` and show a brief summary (name, current title, key skills) so the user can confirm it's the right person before proceeding.
  2. Then ask **what position they are applying to** (job title or paste a job description).

Once the base CV is in place and a position is provided:
- Generate a role `.yaml` config in `CVs/<PersonName>/roles/` based on the job position provided, including:
  - `match`: Your estimated match percentage between the candidate's profile and the job requirements
  - `company`: Company name (extracted from the job posting)
  - `description`: A very short description of the position
  - `source`: Where the job posting was found (e.g., LinkedIn, Indeed, Craigslist, company website). Always ask the user. If the job description hints at a platform, confirm with the user rather than assuming.
  - `role`, `summary`, `include_tags`, `extra_skills`, `ats_keywords`: As described in "How It Works" below
- Run `generate_cv.py --cv-dir CVs/<PersonName> <role_name>` to produce the tailored CV (this also adds an entry to `positions.md`).
- Run `export_pdf.py --cv-dir CVs/<PersonName> <role_name>` to produce the PDF.

## Project Structure

```
generate_cv.py          # Reads base CV + role config, outputs tailored .md
export_pdf.py           # Converts output .md files to styled PDFs
CVs/                    # One folder per person
  ├── Sample/           # Example CV (tracked in git)
  │   ├── cv_base.md
  │   ├── positions.md
  │   ├── roles/
  │   └── output/
  └── <PersonName>/     # Real CVs (gitignored)
      ├── cv_base.md    # Person's master CV with tagged sections
      ├── positions.md  # Auto-generated tracker for all applied positions
      ├── roles/        # Generated .yaml configs (one per job position)
      └── output/       # Generated CVs (.md and .pdf)
```

Each folder under `CVs/` is a self-contained CV project per person, with its own `cv_base.md`, `roles/`, and `output/`. Only `CVs/Sample/` is tracked in git -- all other person folders are gitignored.

## How It Works

1. `cv_base.md` contains the full CV. Skill groups and experience bullets are annotated with HTML comment tags like `<!-- tag:control_systems -->`.
2. When a job position is provided, a `.yaml` role config is generated in `roles/` containing:
   - `company`: Company name (used for position tracking)
   - `description`: Short description of the position (used for position tracking)
   - `match`: Estimated match percentage between the candidate and the position
   - `source`: Where the job posting was found (e.g., LinkedIn, Indeed, company website)
   - `role`: Title to display on the CV
   - `summary`: Role-specific professional summary
   - `include_tags`: Which skill groups from the base to include
   - `extra_skills`: Additional skills not in the base (role-specific)
   - `ats_keywords`: Keywords embedded as an HTML comment for ATS parsing
3. `generate_cv.py` assembles a tailored CV by filtering the base with the role config and adds an entry to `positions.md`.
4. `export_pdf.py` strips tag comments and renders to a clean PDF.

The `roles/` and `output/` folders start empty. Role configs are generated based on provided job positions, then used to produce tailored CVs.

## Usage

```bash
# Using the default CV directory (CVs/Sample)
python3 generate_cv.py --list
python3 generate_cv.py <role_name>
python3 export_pdf.py <role_name>
python3 export_pdf.py --all

# Using a custom CV directory
python3 generate_cv.py --cv-dir CVs/MyCV --list
python3 generate_cv.py --cv-dir CVs/MyCV <role_name>
python3 export_pdf.py --cv-dir CVs/MyCV <role_name>
```

## Adding a New CV

1. Create a new folder under `CVs/` (e.g. `CVs/MyCV/`)
2. Add your `cv_base.md` inside it
3. Generate role configs from job positions, then run the scripts

## Dependencies

```bash
pip install pyyaml fpdf2
```

## Available Tags in cv_base.md

Tags are fully custom per person -- each `cv_base.md` defines its own set. Read the person's `cv_base.md` to discover their available tags before generating a role config.

The `CVs/Sample/cv_base.md` uses these tags as an example:
- `instrumentation` -- process instrumentation design, P&IDs, instrument index, loop diagrams, hook-ups
- `control_systems` -- DCS, PLC, SCADA, SIS, HMI
- `calibration` -- calibration, HART/Fieldbus, smart transmitters
- `project_management` -- project execution, vendor evaluation, FAT/SAT, commissioning, documentation
- `software` -- SPI/INtools, AutoCAD, MATLAB, SAP PM
- `safety_compliance` -- functional safety, HAZOP, LOPA, SIL, IEC 61511

## Position Tracking

Each person's folder contains a `positions.md` file that tracks all generated CVs. It is auto-created and appended by `generate_cv.py`. Columns:
- **Date** -- when the CV was generated
- **Company** -- from the `company` field in the role YAML
- **Position** -- from the `role` field in the role YAML
- **Description** -- from the `description` field in the role YAML
- **Source** -- where the job posting was found (from the `source` field in the role YAML)
- **CV Sent / Replied / Interview** -- checkboxes, updated manually (`[ ]` → `[x]`)
- **CV** -- link to the generated PDF
- **Match** -- from the `match` field in the role YAML
