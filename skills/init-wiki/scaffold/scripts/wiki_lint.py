#!/usr/bin/env python3
"""Linter for the agent memory wiki (see ``docs/spec/agent-wiki.md``).

The wiki content is committed to this repo under ``wiki/``; on the deployment
``$WIKI_PATH`` (default ``/opt/data/wiki``) is a symlink to it. This linter is
the mechanical enforcement of the conventions the spec defines. It is pure
stdlib (no hermes import, no PyYAML) so it can run inside ``just lint`` /
pre-commit without the agent.

Checks (errors fail the run):

- frontmatter present and well-formed
- mandatory fields: ``title``, ``created``, ``updated``, ``type``, ``tags``,
  ``sources``, ``use-when``
- ``type`` in the allowed set; ``tags`` drawn from the ``SCHEMA.md`` taxonomy
- every ``[[wikilink]]`` resolves to an existing page slug

Warnings (do not fail unless ``--strict``):

- orphan pages (no inbound links)
- pages exceeding the out-degree budget

Path resolution (first that applies): a positional ``WIKI_PATH`` argument, then
``$WIKI_PATH``, then the ``wiki/`` committed alongside this script, then
``/opt/data/wiki``. On a checkout this lints the in-repo ``wiki/``; on the
deployed machine ``$WIKI_PATH`` points at the same files via symlink. When the
resolved path does not exist the linter prints a skip notice and exits 0, so
wiring it into ``just lint`` is safe on a checkout with no wiki.

Usage::

    python scripts/wiki_lint.py [WIKI_PATH] [--strict] [--json]
                                [--max-degree N] [--log-entries unused]
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_WIKI_PATH = "/opt/data/wiki"
# The wiki committed in this repo, a sibling of scripts/ (this file's parent).
IN_REPO_WIKI = Path(__file__).resolve().parent.parent / "wiki"
PAGE_DIRS = ("entities", "concepts", "comparisons", "queries", "summaries")
RESERVED = {"SCHEMA.md", "index.md", "log.md"}
ALLOWED_TYPES = {"entity", "concept", "comparison", "query", "summary"}
REQUIRED_FIELDS = ("title", "created", "updated", "type", "tags", "sources", "use-when")
DEFAULT_MAX_DEGREE = 12

_WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")
_TAXONOMY_TAG_RE = re.compile(r"^\s*[-*]\s+`([a-z0-9-]+)`")


@dataclass
class Finding:
    level: str  # "error" | "warn"
    page: str
    message: str


@dataclass
class Page:
    slug: str
    rel: str
    frontmatter: dict[str, object]
    outlinks: set[str] = field(default_factory=set)


def parse_frontmatter(text: str) -> dict[str, object] | None:
    """Parse a leading ``---`` YAML-ish frontmatter block.

    Returns a dict (scalars as ``str``, lists as ``list[str]``) or ``None`` when
    no well-formed block is present. Deliberately tiny: handles ``key: value``,
    inline ``key: [a, b]``, and block lists of ``- item`` lines — which is all
    the schema uses.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None

    fm: dict[str, object] = {}
    body = lines[1:end]
    i = 0
    while i < len(body):
        raw = body[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            fm[key] = items
        elif value:
            fm[key] = value
        else:
            # Block list: consume following indented "- item" lines.
            items = []
            while i < len(body) and body[i].lstrip().startswith("- "):
                items.append(body[i].lstrip()[2:].strip())
                i += 1
            fm[key] = items if items else ""
    return fm


def load_taxonomy(wiki: Path) -> set[str] | None:
    """Tags declared under ``## Tag Taxonomy`` in ``SCHEMA.md``, or ``None``."""
    schema = wiki / "SCHEMA.md"
    if not schema.exists():
        return None
    tags: set[str] = set()
    in_section = False
    for line in schema.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line.strip().lower() == "## tag taxonomy"
            continue
        if in_section:
            match = _TAXONOMY_TAG_RE.match(line)
            if match:
                tags.add(match.group(1))
    return tags or None


def load_pages(wiki: Path) -> list[Page]:
    pages: list[Page] = []
    for sub in PAGE_DIRS:
        directory = wiki / sub
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            if path.name in RESERVED:
                continue
            text = path.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            outlinks = {m.strip() for m in _WIKILINK_RE.findall(text)}
            pages.append(
                Page(
                    slug=path.stem,
                    rel=path.relative_to(wiki).as_posix(),
                    frontmatter=fm if fm is not None else {},
                    outlinks=outlinks,
                )
            )
            if fm is None:
                pages[-1].frontmatter = {"__no_frontmatter__": True}
    return pages


def lint(wiki: Path, max_degree: int = DEFAULT_MAX_DEGREE) -> list[Finding]:
    findings: list[Finding] = []
    pages = load_pages(wiki)
    slugs = {p.slug for p in pages}
    taxonomy = load_taxonomy(wiki)

    inbound: dict[str, int] = {p.slug: 0 for p in pages}
    for page in pages:
        for target in page.outlinks:
            if target in inbound and target != page.slug:
                inbound[target] += 1

    for page in pages:
        fm = page.frontmatter
        if fm.get("__no_frontmatter__"):
            findings.append(Finding("error", page.rel, "missing frontmatter block"))
            continue

        for field_name in REQUIRED_FIELDS:
            value = fm.get(field_name)
            if value is None or value == "" or value == []:
                findings.append(
                    Finding(
                        "error", page.rel, f"missing frontmatter field: {field_name}"
                    )
                )

        page_type = fm.get("type")
        if isinstance(page_type, str) and page_type not in ALLOWED_TYPES:
            findings.append(Finding("error", page.rel, f"invalid type: {page_type!r}"))

        tags = fm.get("tags")
        if taxonomy is not None and isinstance(tags, list):
            for tag in tags:
                if tag not in taxonomy:
                    findings.append(
                        Finding("error", page.rel, f"tag not in taxonomy: {tag!r}")
                    )

        for target in sorted(page.outlinks):
            if target not in slugs:
                findings.append(
                    Finding("error", page.rel, f"broken wikilink: [[{target}]]")
                )

        degree = len(page.outlinks)
        if degree > max_degree:
            findings.append(
                Finding(
                    "warn",
                    page.rel,
                    f"out-degree {degree} exceeds budget {max_degree}",
                )
            )

        if inbound.get(page.slug, 0) == 0:
            findings.append(Finding("warn", page.rel, "orphan page (no inbound links)"))

    return findings


def _render(findings: list[Finding], page_count: int) -> str:
    if not findings:
        return f"wiki lint: {page_count} pages, no findings."
    lines = [f"wiki lint: {page_count} pages, {len(findings)} findings:"]
    for f in findings:
        lines.append(f"  [{f.level}] {f.page}: {f.message}")
    return "\n".join(lines)


def _default_wiki_path() -> Path:
    """Resolve the wiki path when none is given on the command line.

    ``$WIKI_PATH`` wins (the deployment sets it to the ``/opt/data/wiki``
    symlink); otherwise prefer the ``wiki/`` committed in this repo so a plain
    checkout lints it; finally fall back to ``/opt/data/wiki``.
    """
    env = os.environ.get("WIKI_PATH")
    if env:
        return Path(env)
    if IN_REPO_WIKI.exists():
        return IN_REPO_WIKI
    return Path(DEFAULT_WIKI_PATH)


def main(argv: list[str] | None = None) -> int:
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    strict = "--strict" in argv
    as_json = "--json" in argv
    max_degree = DEFAULT_MAX_DEGREE
    if "--max-degree" in argv:
        idx = argv.index("--max-degree")
        max_degree = int(argv[idx + 1])
        del argv[idx : idx + 2]
    positional = [a for a in argv if not a.startswith("--")]
    wiki = Path(positional[0]) if positional else _default_wiki_path()

    if not wiki.exists():
        print(f"wiki lint: no wiki at {wiki} — skipping.")
        return 0

    findings = lint(wiki, max_degree=max_degree)
    page_count = len(load_pages(wiki))

    if as_json:
        print(
            json.dumps(
                [
                    {"level": f.level, "page": f.page, "message": f.message}
                    for f in findings
                ]
            )
        )
    else:
        print(_render(findings, page_count))

    errors = [f for f in findings if f.level == "error"]
    warns = [f for f in findings if f.level == "warn"]
    if errors or (strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
