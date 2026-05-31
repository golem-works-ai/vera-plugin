from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class _SpecMark:
    @staticmethod
    def spec(_slug: str):
        def decorate(func):
            return func

        return decorate


class _PytestStub:
    mark = _SpecMark()


pytest = _PytestStub()


class SkillsIndexTests(unittest.TestCase):
    @pytest.mark.spec("packaging.skills-urls.index-published")
    def test_generate_index_lists_skills_with_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            skills_dir = temp_path / "skills"
            (skills_dir / "zeta").mkdir(parents=True)
            (skills_dir / "alpha").mkdir(parents=True)
            (skills_dir / "zeta" / "SKILL.md").write_text("# zeta\n", encoding="utf-8")
            (skills_dir / "alpha" / "SKILL.md").write_text("# alpha\n", encoding="utf-8")

            output_path = temp_path / "index.json"
            subprocess.run(
                [
                    "python3",
                    "scripts/generate_skills_index.py",
                    "--skills-dir",
                    str(skills_dir),
                    "--base-url",
                    "https://example.com/vera-plugin/",
                    "--output",
                    str(output_path),
                ],
                check=True,
            )

            generated = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                generated,
                {
                    "skills": [
                        {
                            "name": "alpha",
                            "path": f"{skills_dir.as_posix()}/alpha/SKILL.md",
                            "url": f"https://example.com/vera-plugin/{skills_dir.as_posix()}/alpha/SKILL.md",
                        },
                        {
                            "name": "zeta",
                            "path": f"{skills_dir.as_posix()}/zeta/SKILL.md",
                            "url": f"https://example.com/vera-plugin/{skills_dir.as_posix()}/zeta/SKILL.md",
                        },
                    ]
                },
            )

    @pytest.mark.spec("packaging.skills-urls.readme")
    def test_readme_documents_skills_urls_config(self) -> None:
        readme = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("skills.urls", readme)
        self.assertIn(
            "https://raw.githubusercontent.com/golem-works-ai/vera-plugin/main/index.json",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
