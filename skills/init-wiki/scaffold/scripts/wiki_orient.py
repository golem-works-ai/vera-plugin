#!/usr/bin/env python3
"""Deterministic orientation dump for the agent memory wiki.

Prints ``CONVENTIONS.md`` (when present), then ``SCHEMA.md``, then ``index.md``,
then a compact changelog tail of ``log.md`` (an entry begins with a ``## ``
heading). This is the once-per-session read the agent does to know what the wiki
contains and how it is organized, within a bounded token budget (see
``docs/spec/agent-wiki.md`` and the runbook).

The log tail is rendered as a changelog: the ``## [date] action | subject``
header line for the last N entries, with only the most recent few expanded to
their full bullets. A well-written header already carries the recency signal an
orienting agent needs ("what changed and why it matters"); the per-entry bullets
are detail the agent reads on demand from ``log.md``. Expanding all N entries
costs a few thousand tokens of mostly-stale detail every session, so we don't —
see "Writing a log entry" in ``CONVENTIONS.md`` for how to write for this.

``CONVENTIONS.md`` is the canonical (repo-agnostic) design shared across repos
via the ``init-wiki`` skill; ``SCHEMA.md`` is this wiki's local instance
(domain, tag taxonomy, hubs, sources). ``CONVENTIONS.md`` is optional so this
dump stays correct on a wiki that predates the split.

Pure stdlib; reads ``$WIKI_PATH`` (default ``/opt/data/wiki``) or an explicit
path argument.

Usage::

    python scripts/wiki_orient.py [WIKI_PATH] [--log-entries N] [--log-full M]
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_WIKI_PATH = "/opt/data/wiki"
DEFAULT_LOG_ENTRIES = 20
DEFAULT_LOG_FULL = 3


def tail_log_entries(log_text: str, n: int, full: int = DEFAULT_LOG_FULL) -> str:
    """Render the last ``n`` ``## ``-delimited log entries for orientation.

    Emits the header line (``## [date] action | subject``) for each of the last
    ``n`` entries as a compact changelog, expanding only the most recent
    ``full`` to their complete bullets. Entry order follows the file (append
    order), matching the old full-dump behavior. The ``# Wiki Log`` preamble is
    dropped — it is append-format boilerplate, not orientation content.
    """
    lines = log_text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("## ")]
    if not starts:
        return log_text.strip()
    kept = starts[-n:] if n < len(starts) else starts
    bounds = kept + [len(lines)]  # sentinel end; entry i = [bounds[i], bounds[i + 1])
    full = max(0, min(full, len(kept)))
    full_cutoff = len(kept) - full  # entries at index >= full_cutoff are expanded

    parts: list[str] = []
    if full_cutoff > 0:  # compact header-only block for the older entries
        parts.append("\n".join(lines[bounds[i]].strip() for i in range(full_cutoff)))
    for i in range(full_cutoff, len(kept)):  # full bullets for the most recent
        parts.append("\n".join(lines[bounds[i] : bounds[i + 1]]).strip())
    return "\n\n".join(p for p in parts if p).strip()


def orient(
    wiki: Path,
    log_entries: int = DEFAULT_LOG_ENTRIES,
    log_full: int = DEFAULT_LOG_FULL,
) -> str:
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
        tail = tail_log_entries(
            log_path.read_text(encoding="utf-8"), log_entries, full=log_full
        )
        sections.append(
            f"===== log.md (last {log_entries} entries: headers, "
            f"newest {log_full} in full) =====\n{tail}"
        )
    else:
        sections.append("===== log.md =====\n(missing)")

    return "\n\n".join(sections)


def main(argv: list[str] | None = None) -> int:
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    log_entries = DEFAULT_LOG_ENTRIES
    log_full = DEFAULT_LOG_FULL
    if "--log-entries" in argv:
        idx = argv.index("--log-entries")
        log_entries = int(argv[idx + 1])
        del argv[idx : idx + 2]
    if "--log-full" in argv:
        idx = argv.index("--log-full")
        log_full = int(argv[idx + 1])
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

    print(orient(wiki, log_entries=log_entries, log_full=log_full))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
