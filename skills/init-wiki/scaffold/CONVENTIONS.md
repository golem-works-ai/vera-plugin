---
title: Agent Memory Wiki — Conventions
conventions-version: 1
canonical-source: golem-works-ai/vera-plugin skills/init-wiki/scaffold/CONVENTIONS.md
---

# Agent Memory Wiki — Conventions

> **This file is canonical and repo-agnostic. Do not hand-edit it in a consuming
> repo — it is overwritten verbatim on every `init-wiki` run.** Repo-specific
> content (domain, tag taxonomy, hub list, source paths) lives in the sibling
> `SCHEMA.md`, which `init-wiki` creates once and never touches again.

A Karpathy-style "warm tier" of agent memory: a navigable wiki of markdown pages
an agent grows over time, sitting between a small always-loaded pointer file
(cold pointers) and the underlying sources (repos, transcripts, articles). It is
distilled enough to answer a planning or debugging question in a few page-reads,
but always anchored back to a source so a claim can be verified rather than
trusted. The unique value is the content that has **no other home** — a decision
made in a standup, a pattern observed across many transcripts, a cross-repo
convention.

## Page model

Every page is YAML frontmatter + a markdown body. Filenames are
lowercase-hyphenated; a page's filename stem is its **slug** — the target of
every `[[wikilink]]`. Pages live under `entities/`, `concepts/`, `comparisons/`,
`queries/`, `summaries/`.

### Frontmatter (wiki pages)

```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [from taxonomy]
sources: [<source reference — see below>]
use-when: <routing-trigger — the situation that should land a reader here>
# Optional:
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
---
```

Mandatory fields: `title`, `created`, `updated`, `type`, `tags`, `sources`,
`use-when`. `type` is one of the five allowed values above. `tags` must be drawn
from the taxonomy declared in this wiki's `SCHEMA.md` — a tag not in the taxonomy
is an error, not a new tag. The linter (`wiki_lint.py`) errors on any missing or
malformed field.

**`use-when` is mandatory.** Phrase it as the routing *situation* ("planning a
change to X" / "when debugging Y"), not as a topic description ("about X"). One
canonical line per page, owned by the target.

### Source references

Wiki pages reference sources via the `sources:` field; sources are **referenced,
not duplicated**. Three conventions, in order of preference:

1. **Local clone path** (preferred when a local clone exists) — fast, no network,
   no duplication; machine-local.
2. **Canonical raw URL** (when no local clone exists) — always canonical, no
   duplication; requires network.
3. **`raw/` local copy** (only for external/non-canonical sources — web
   articles, papers, transcripts). Use `source_url` + `sha256` frontmatter on the
   raw copy for drift detection on re-ingest.

The concrete clone paths / URL bases for *this* wiki's sources are recorded in
`SCHEMA.md`.

### Page thresholds

- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to an existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions
- **Split a page** when it exceeds ~200 lines
- **Archive a page** when fully superseded — move to `_archive/`, remove from index

## Navigation model

The wiki is navigated the way a human plays the Wikipedia game: land on a page,
then make greedy local hops following the most promising link, without a global
view. This works when the link graph is dense and the local routing signal is
good. Three rules make that true:

- **Hubs.** A small number of high-degree hub pages (one per domain — a person, a
  project, a topic) that any task reliably lands on first and that fan out to
  everything prominent in that domain. Navigability is determined far more by hub
  quality than by average degree. *This wiki's hubs are listed in `SCHEMA.md`.*
- **`use-when` triggers, owned by the target.** Each page declares a single
  canonical `use-when:` — phrased as the situation that should route a reader
  here, not a topic description. A link block references the target's canonical
  trigger rather than restating it, so the trigger has exactly one source of
  truth and drift is mechanically detectable. Triggers encode routing value, not
  topical similarity — the link that *routes* toward an answer, not the link that
  merely shares a subject.
- **`similar-to` with contrast.** A "similar to" link must state the *difference*
  from the current page, never bare similarity, or it adds graph degree (and
  per-hop reading cost) without improving routing.

### Degree budget

High degree raises hit-rate but every outbound link is read by everyone passing
through the page, so degree is a cost as well as a benefit. Pages target a small
out-degree (≈7); the math is forgiving (7^3.2 ≈ 500 reachable pages in ~3 hops),
so density should be *good* edges, not *many* edges. `wiki_lint.py` warns above
12 outbound links per page by default.

## Provenance rule

Summaries are allowed and encouraged — distilling five transcripts into one
"X prefers Y" line is the whole value, and it saves context. The discipline is
that **every load-bearing claim must link to the source that grounds it.** A
summary that compresses *and* cites is safe; a free-floating asserted fact with
no pointer is the failure mode that produces confident, wrong memory.

## Self-improving update rule

The wiki improves from its own query traffic. After a search, the path taken is a
labeled signal: a long path is a graph defect with the fix attached. The update
step proposes the edge (or hub promotion) that would have shortened the path,
gated by two tests and bounded by the degree budget:

1. **Recurring, not one-off.** Only crystallize an edge for a route that recurs; a
   single random query must not add a vanity edge.
2. **Justifiable on the source page.** The edge is added only if a reader of the
   *source* page would independently find it relevant — because every visitor to
   that page pays to read it.
3. **Add-and-evict.** When a page exceeds its degree budget, adding the hot edge
   demotes the coldest one. The graph stays dense where traffic is and sparse
   where it isn't.

## Update policy

When new information conflicts with existing content:

1. **Check dates** — newer sources generally supersede older ones.
2. **If contradictory**, note both positions with dates and sources.
3. **Mark the contradiction** in frontmatter: `contradictions: [page-slug]`.
4. **Flag for user review** in the lint report.

## Modification protocol

Every agent modifying wiki files MUST use a git worktree to isolate changes from
`main`. This prevents two concurrent agents from stepping on each other's edits.
Read-only operations (survey, query, reading `index.md`, reading pages for
research) do NOT need a worktree — only agents that will **write** need the
isolation. Git operations run from the repo root, not from `$WIKI_PATH` (which
may be a symlink into the repo).

1. **Pre-commit on main** (capture pre-modification state):
   ```bash
   cd "$WIKI_PATH" && git add -A && git diff --cached --quiet ||
     git commit -m "pre-$(whoami) checkpoint $(date +%Y-%m-%d)"
   ```
2. **Create a worktree** (clean up any leftover from a prior failed run), and
   store `$WORKTREE` — ALL subsequent file ops, linting, and subagent prompts use
   it, NOT `$WIKI_PATH`:
   ```bash
   BRANCH="$(whoami)-$(date +%Y-%m-%d)"
   WORKTREE="/tmp/wiki-work-$(whoami)-$(date +%Y-%m-%d)"
   cd "$WIKI_PATH"
   git worktree remove "$WORKTREE" 2>/dev/null || true
   git branch -D "$BRANCH" 2>/dev/null || true
   git worktree add -b "$BRANCH" "$WORKTREE" main
   ```
3. **Do work inside the worktree** — read/edit at `$WORKTREE/...`, run
   `python3 <scripts-dir>/wiki_lint.py "$WORKTREE" --strict`, and pass
   `WIKI_ROOT=$WORKTREE` to any subagents so they operate on worktree files too.
4. **Commit in the worktree**:
   ```bash
   cd "$WORKTREE" && git add -A && git commit -m "$(whoami) $(date +%Y-%m-%d): <summary>"
   ```
5. **Merge back to main and clean up**:
   ```bash
   cd "$WIKI_PATH"
   git checkout main
   git merge --no-ff "$BRANCH" -m "merge $(whoami) $(date +%Y-%m-%d)"
   git branch -d "$BRANCH"
   git worktree remove "$WORKTREE"
   ```

**Cleanup on failure:** always attempt
`git worktree remove "$WORKTREE" 2>/dev/null; git branch -D "$BRANCH" 2>/dev/null; git checkout main`,
report the failure honestly (do not fabricate success), and note any leftover
worktree path with uncommitted changes.

## Orientation (session start)

At session start, orient by running the deterministic dump tool (not by reading
files manually):

```bash
python3 <scripts-dir>/wiki_orient.py                 # uses $WIKI_PATH
python3 <scripts-dir>/wiki_orient.py --log-entries 30
```

It prints `CONVENTIONS.md` (this file), then `SCHEMA.md`, then `index.md`, then
the last N `log.md` entries — deterministic and bounded (~2–5K tokens). This is
the **only wiki read** needed to know what exists and how it is organized. Do it
**once per session**, not every turn.

## Lint

```bash
python3 <scripts-dir>/wiki_lint.py "$WIKI_PATH" --strict
```

Must be 0 errors and 0 warnings. Checks: frontmatter + required fields (incl.
`use-when`), `type` set, tag taxonomy (read from `SCHEMA.md`), broken
`[[wikilinks]]`, orphan pages, out-degree budget. Exits 0 (with a skip notice)
when `$WIKI_PATH` is absent, so it is safe to wire into `just lint` on a checkout
with no wiki.
