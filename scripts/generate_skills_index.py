#!/usr/bin/env python3
"""Generate a skills.urls index.json from bundled skills."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills-dir",
        default="skills",
        help="Directory containing <skill>/SKILL.md trees",
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Base URL where this repository is published",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path for generated index.json",
    )
    return parser.parse_args()


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def build_index(skills_dir: Path, base_url: str) -> dict[str, list[dict[str, str]]]:
    skills: list[dict[str, str]] = []

    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        skill_name = skill_md.parent.name
        relative_path = skill_md.as_posix()
        skills.append(
            {
                "name": skill_name,
                "path": relative_path,
                "url": f"{base_url}/{relative_path}",
            }
        )

    return {"skills": skills}


def main() -> int:
    args = parse_args()
    skills_dir = Path(args.skills_dir)
    base_url = normalize_base_url(args.base_url)
    output_path = Path(args.output)

    index = build_index(skills_dir=skills_dir, base_url=base_url)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
