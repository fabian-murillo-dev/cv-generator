#!/usr/bin/env python3
"""
Generate a role-specific CV from the base CV and a role config.

Usage:
    python generate_cv.py <role_name>
    python generate_cv.py --list
    python generate_cv.py --cv-dir CVs/MyCV <role_name>

Examples:
    python generate_cv.py controls_engineer
    python generate_cv.py automation_engineer
    python generate_cv.py --list
    python generate_cv.py --cv-dir CVs/MyCV controls_engineer
"""

import sys
import re
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install it with: pip install pyyaml")
    sys.exit(1)

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


def get_paths(cv_dir: Path):
    return cv_dir / "cv_base.md", cv_dir / "roles", cv_dir / "output"


def list_roles(roles_dir: Path):
    roles = sorted(p.stem for p in roles_dir.glob("*.yaml"))
    if not roles:
        print(f"No role configs found in {roles_dir}")
        return
    print("Available roles:")
    for r in roles:
        config = yaml.safe_load((roles_dir / f"{r}.yaml").read_text())
        print(f"  {r:30s} -> {config.get('role', r)}")


def load_role(role_name: str, roles_dir: Path) -> dict:
    path = roles_dir / f"{role_name}.yaml"
    if not path.exists():
        print(f"Error: role config '{role_name}' not found at {path}")
        print("Use --list to see available roles.")
        sys.exit(1)
    return yaml.safe_load(path.read_text())


def parse_base_cv(text: str) -> dict:
    """Parse the base CV into sections, tracking tag comments."""
    sections = {}
    current_section = None
    current_content = []
    current_tags = set()

    for line in text.splitlines():
        # Detect section headers (## level)
        if line.startswith("## "):
            if current_section:
                sections[current_section] = {
                    "content": "\n".join(current_content),
                    "tags": current_tags,
                }
            current_section = line.lstrip("# ").strip()
            current_content = [line]
            current_tags = set()
            continue

        # Detect tag comments
        tag_match = re.match(r"<!--\s*tag:([\w,]+)\s*-->", line)
        if tag_match:
            current_tags.update(tag_match.group(1).split(","))

        current_content.append(line)

    if current_section:
        sections[current_section] = {
            "content": "\n".join(current_content),
            "tags": current_tags,
        }

    return sections


def filter_skills_section(section_text: str, include_tags: set) -> str:
    """Keep only skill groups whose tag is in include_tags."""
    lines = section_text.splitlines()
    result = []
    include_block = True

    for line in lines:
        tag_match = re.match(r"<!--\s*tag:([\w,]+)\s*-->", line)
        if tag_match:
            block_tags = set(tag_match.group(1).split(","))
            include_block = bool(block_tags & include_tags)
            if include_block:
                result.append(line)
            continue

        if line.startswith("## "):
            include_block = True
            result.append(line)
        elif include_block:
            result.append(line)

    return "\n".join(result)


def filter_experience_bullets(section_text: str, include_tags: set) -> str:
    """For experience, keep all jobs but reorder bullets matching tags to top."""
    # Experience is always fully included -- tags just influence emphasis
    return section_text


def build_cv(role_config: dict, base_cv: Path) -> str:
    base_text = base_cv.read_text()
    include_tags = set(role_config.get("include_tags", []))

    # Extract the header (everything before first ## section)
    header_match = re.match(r"(.*?)(?=^## )", base_text, re.DOTALL | re.MULTILINE)
    header = header_match.group(1) if header_match else ""

    # Replace the summary line in the header
    original_summary_match = re.search(
        r"(?<=## Professional Summary\n\n).*?(?=\n\n---)", base_text, re.DOTALL
    )

    sections = parse_base_cv(base_text)

    # Build the output
    parts = []

    # Header with swapped summary
    role_title = role_config["role"]
    new_header = re.sub(
        r"\*\*.+?\*\*",
        f"**{role_title}**",
        header,
        count=1,
    )
    parts.append(new_header.rstrip())

    # Professional Summary -- use role-specific one
    parts.append("## Professional Summary\n")
    parts.append(role_config["summary"].strip())
    parts.append("\n---\n")

    # Core Skills -- filtered by tags + extra skills
    if "Core Skills" in sections:
        filtered = filter_skills_section(sections["Core Skills"]["content"], include_tags)
        parts.append(filtered.rstrip())

        extra = role_config.get("extra_skills", [])
        if extra:
            parts.append("\n<!-- tag:role_specific -->")
            for skill in extra:
                parts.append(f"- {skill}")

        parts.append("\n\n---\n")

    # Experience -- always included in full
    if "Professional Experience" in sections:
        parts.append(sections["Professional Experience"]["content"].rstrip())
        parts.append("\n---\n")

    # Education, Certifications, Memberships, Languages -- pass through
    for section_name in ["Education", "Certifications", "Professional Memberships", "Languages"]:
        if section_name in sections:
            parts.append(sections[section_name]["content"].rstrip())
            parts.append("")

    # ATS keywords as hidden comment at the bottom
    ats = role_config.get("ats_keywords", [])
    if ats:
        parts.append(f"\n<!-- ATS Keywords: {', '.join(ats)} -->")

    output = "\n".join(parts)
    # Clean up extra blank lines
    output = re.sub(r"\n{3,}", "\n\n", output)
    return output


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    cv_dir, args = get_cv_dir(sys.argv[1:])
    base_cv, roles_dir, output_dir = get_paths(cv_dir)

    if not cv_dir.exists():
        print(f"Error: CV directory '{cv_dir}' does not exist")
        sys.exit(1)

    if not args:
        print(__doc__.strip())
        sys.exit(1)

    if args[0] == "--list":
        list_roles(roles_dir)
        return

    role_name = args[0]
    role_config = load_role(role_name, roles_dir)

    cv_text = build_cv(role_config, base_cv)

    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / f"cv_{role_name}.md"
    out_path.write_text(cv_text)

    print(f"Generated: {out_path}")
    print(f"Role:      {role_config['role']}")
    print(f"Tags:      {', '.join(role_config.get('include_tags', []))}")
    if role_config.get("ats_keywords"):
        print(f"ATS keys:  {len(role_config['ats_keywords'])} keywords embedded")


if __name__ == "__main__":
    main()
