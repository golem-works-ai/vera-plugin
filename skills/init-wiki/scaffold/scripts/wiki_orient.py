#!/usr/bin/env python3
"""Deterministic orientation dump for the agent memory wiki.

Prints ``CONVENTIONS.md`` (when present), then ``SCHEMA.md``, then ``index.md``,
then the last N entries of ``log.md`` (an entry begins with a ``## `` heading).
This is the once-per-session read the agent does to know what the wiki contains
and how it is organized, within a bounded token budget (see
``docs/spec/agent-wiki.md`` and the runbook).

``CONVENTIONS.md`` is the canonical (repo-agnostic) design shared across repos
via the ``init-wiki`` skill; ``SCHEMA.md`` is this wiki's local instance
(domain, tag taxonomy, hubs, sources). ``CONVENTIONS.md`` is optional so this
dump stays correct on a wiki that predates the split.

Pure stdlib; reads ``$WIKI_PATH`` (default ``/opt/data/wiki``) or an explicit
path argument.

Usage::

    python scripts/wiki_orient.py [WIKI_PATH] [--log-entries N]
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_WIKI_PATH = "/opt/data/wiki"
DEFAULT_LOG_ENTRIES = 20


def tail_log_entries(log_text: str, n: int) -> str:
    """Return the last ``n`` ``## ``-delimited entries of the log, in order."""
    lines = log_text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("## ")]
    if not starts:
        return log_text.strip()
    preamble_end = starts[0]
    keep_from = starts[-n] if n < len(starts) else preamble_end
    header = "\n".join(lines[:preamble_end]).strip()
    body = "\n".join(lines[keep_from:]).strip()
    return f"{header}\n\n{body}".strip() if header else body


def orient(wiki: Path, log_entries: int = DEFAULT_LOG_ENTRIES) -> str:
    sections: list[str] = []

    # CONVENTIONS.md is the canonical, repo-agnostic design (shared via the
    # init-wiki skill). It is optional: skip silently when absent so this dump
    # stays correct on a wiki that predates the CONVENTIONS/SCHEMA split.
    conventions = wiki / "CONVENTIONS.md"
    if conventions.exists():
        sections.append(
            f"===== CONVENTIONS.md =====\n{conventions.read_text(encoding='utf-8').strip()}"
        )

    for name in ("SCHEMA.md", "index.md"):
        path = wiki / name
        if path.exists():
            sections.append(
                f"===== {name} =====\n{path.read_text(encoding='utf-8').strip()}"
            )
        else:
            sections.append(f"===== {name} =====\n(missing)")

    log_path = wiki / "log.md"
    if log_path.exists():
        tail = tail_log_entries(log_path.read_text(encoding="utf-8"), log_entries)
        sections.append(f"===== log.md (last {log_entries} entries) =====\n{tail}")
    else:
        sections.append("===== log.md =====\n(missing)")

    return "\n\n".join(sections)


def main(argv: list[str] | None = None) -> int:
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    log_entries = DEFAULT_LOG_ENTRIES
    if "--log-entries" in argv:
        idx = argv.index("--log-entries")
        log_entries = int(argv[idx + 1])
        del argv[idx : idx + 2]
    positional = [a for a in argv if not a.startswith("--")]
    wiki = (
        Path(positional[0])
        if positional
        else Path(os.environ.get("WIKI_PATH", DEFAULT_WIKI_PATH))
    )

    if not wiki.exists():
        print(f"wiki orient: no wiki at {wiki} — skipping.")
        return 0

    print(orient(wiki, log_entries=log_entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
