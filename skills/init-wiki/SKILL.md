---
name: init-wiki
description: Use when adding (or refreshing) an agent memory wiki in a repo — idempotently installs the canonical conventions + linter/orient scripts and, once, a local instance stub, without ever overriding local taxonomy, hubs, or content.
---

# init-wiki — Idempotent Agent Memory Wiki Installer

Adds a Karpathy-style agent memory wiki (see `scaffold/CONVENTIONS.md`) to a
repo, or refreshes an existing one to the current canonical conventions. Modeled
on the `init` skill's discipline: **idempotency by convention** (don't replace
what works), **verbatim canonical artifacts**, and **verify, don't assume**.

This skill makes real file changes directly (no GitHub-issue round-trip — a wiki
install is low-stakes and mechanical). Support a `--dry-run` that prints the plan
and writes nothing.

## The one invariant (this is the whole skill)

Every file the skill manages is exactly one of two kinds:

| Kind | Files | On every run |
| --- | --- | --- |
| **Canonical** (repo-agnostic) | `CONVENTIONS.md`, `scripts/wiki_lint.py`, `scripts/wiki_orient.py` | **Overwrite verbatim** from `scaffold/` |
| **Local** (repo-specific) | `SCHEMA.md`, `index.md`, `log.md`, and all wiki content (`entities/`, `concepts/`, …) | **Create if missing, then NEVER touch** |

That single rule *is* the "don't override local customizations" guarantee. The
local `SCHEMA.md` is where a repo declares its domain, **tag taxonomy**, hubs,
and source paths; the canonical `CONVENTIONS.md` holds the page model,
navigation rules, provenance rule, self-improving update rule, modification
protocol, and orient/lint rituals. `wiki_orient.py` prints `CONVENTIONS.md` then
`SCHEMA.md` at session start, so both reach the agent.

> **Hard constraint — taxonomy stays in `SCHEMA.md`.** `wiki_lint.py`'s
> `load_taxonomy()` reads tags from the `## Tag Taxonomy` section of `SCHEMA.md`
> specifically, and returns `None` (→ **silently skips all tag validation**) if
> that section is absent. Never move the taxonomy into `CONVENTIONS.md`, and
> verify after install that a bad tag is actually flagged (see Step 4).

## Inputs

- **Wiki location** — where the wiki lives in the repo (default `wiki/`), exposed
  to the running agent via `$WIKI_PATH` (on a deployment, typically a symlink to
  the in-repo `wiki/`).
- **Scripts location** — where the two scripts are installed (default
  `scripts/`).
- Read the repo's `CLAUDE.md` and task runner first to match existing
  conventions (idempotency by convention).

## Workflow

### Step 1 — Assess

Detect current state and classify. For each managed file decide: **bootstrap**
(no wiki yet), **refresh** (canonical file present but older/different), or
**preserve** (local file already exists).

- Is there a `wiki/` (or configured location)? → bootstrap vs. refresh.
- Version compare: the canonical version is `conventions-version:` in
  `scaffold/CONVENTIONS.md` frontmatter; the installed version is the
  `<!-- init-wiki: installed-conventions-version: N -->` marker in the local
  `SCHEMA.md`. Equal → canonical files are already current (still re-copy scripts
  verbatim — cheap and self-healing). Newer → a refresh; call it out.
- If `scripts/wiki_lint.py` / `wiki_orient.py` exist, they are canonical — plan
  to overwrite (do **not** treat them as local conventions to preserve).

Print the plan: what will be overwritten, what will be created, what is being
left untouched. On `--dry-run`, stop here.

### Step 2 — Install canonical artifacts (overwrite)

Copy **verbatim** from this skill's `scaffold/`:

- `scaffold/CONVENTIONS.md` → `<wiki>/CONVENTIONS.md`
- `scaffold/scripts/wiki_lint.py` → `<scripts>/wiki_lint.py`
- `scaffold/scripts/wiki_orient.py` → `<scripts>/wiki_orient.py`

Never hand-edit these into the repo — if a repo needs different behavior, the fix
goes upstream in `vera-plugin` and re-installs. That is what keeps every repo on
one source of truth.

### Step 3 — Create local instance (only if missing)

For each of `SCHEMA.md`, `index.md`, `log.md` and the page dirs (`entities/`,
`concepts/`, `comparisons/`, `queries/`, `summaries/`): **create from the
`*.template.md` stub only if absent.** If it already exists, leave it exactly as
is. Substitute `<REPO>` / `<DATE>` / `<org>` placeholders when creating.

Stamp the new `SCHEMA.md`'s `installed-conventions-version` marker to match the
canonical version from Step 1. (On a refresh where `SCHEMA.md` already exists,
update **only** that one marker line, nothing else — it is the version ratchet,
not content.)

### Step 4 — Wire + verify (verify, don't assume)

1. **Task runner** — ensure `just lint` (or the repo's equivalent) runs
   `python3 <scripts>/wiki_lint.py "$WIKI_PATH" --strict`. It exits 0 with a skip
   notice when `$WIKI_PATH` is absent, so it is safe on checkouts with no wiki.
2. **`CLAUDE.md`** — ensure a `$WIKI_PATH` note points at the wiki and the orient
   command, and links `CONVENTIONS.md` + `SCHEMA.md`. Follow the idempotency
   rule: if the repo already documents this, adapt to its wording, don't
   duplicate.
3. **Prove the linter works — the critical check.** Run it clean, then run it
   against a deliberately bad tag and assert it *errors*:
   ```bash
   python3 <scripts>/wiki_lint.py "$WIKI_PATH" --strict            # expect: 0 findings
   # inject a page with a tag not in SCHEMA.md's taxonomy → expect a non-zero exit
   ```
   A linter that exits 0 on a bad tag means the `## Tag Taxonomy` section is
   missing or misnamed and validation is silently no-opping — fix `SCHEMA.md`
   before finishing. Do not report success on a green run alone.
4. **Orient smoke test** — `python3 <scripts>/wiki_orient.py "$WIKI_PATH"` should
   print `CONVENTIONS.md`, then `SCHEMA.md`, then `index.md`, then the log tail.

### Step 5 — Report honestly

Summarize: files overwritten, files created, files left untouched, the
before/after conventions-version, and the linter verdict (including the bad-tag
assertion). Do not commit — leave changes staged for the human to review.

## Direction of truth

After this skill exists, **`vera-plugin/skills/init-wiki/scaffold/` is the
canonical home** of `CONVENTIONS.md` + the two scripts. Every repo — including
`vermes`, where these scripts originated — is a **consumer** that re-installs
from here; changes to conventions or scripts land in `vera-plugin` first, then
`init-wiki` propagates them. Do not fork the scripts per repo.

### Reconciling `vermes` (the origin repo)

`vermes` today has a single fat `wiki/SCHEMA.md` that fuses universal conventions
*and* its local taxonomy/hubs, plus `docs/spec/agent-wiki.md` as the spec of
record. Promoting `vermes` onto this skill is a **one-time migration**, not part
of a normal `init-wiki` run:

- Split its `SCHEMA.md`: universal sections become derived from
  `CONVENTIONS.md`; keep only Domain, `## Tag Taxonomy`, Hubs, and Source paths
  locally.
- Reframe `vermes/docs/spec/agent-wiki.md` so its conventions are stated as
  derived from the canonical `CONVENTIONS.md` (the spec keeps the vermes-specific
  linter `Done-when`).

Until that migration runs, `vermes` keeps working unchanged — `wiki_orient.py`
skips `CONVENTIONS.md` when it is absent.
