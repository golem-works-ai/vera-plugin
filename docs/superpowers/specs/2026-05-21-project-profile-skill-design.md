# Design: `project-profile` skill + vera-plugin packaging

**Date:** 2026-05-21
**Repo:** `golem-works-ai/vera-plugin` (public)
**Status:** Approved design, pending implementation plan

## Summary

`vera-plugin` is a public repository distributed as a **Claude Code plugin** and
(via documented manual/config install) an **opencode** skill bundle. It hosts
end-user-facing Vera skills — not internal Vera bootstrap skills. This document
designs the first skill, `project-profile`, and the plugin packaging that ships
it.

`project-profile` ensures a System B customer repo has the opinionated minimum
scaffolding Vera needs to operate effectively without the project becoming
unwieldy (duplicate code, weak tests, accumulating tech debt). It is
idempotent: safe to run repeatedly. It enforces the *existence* of a small set
of artifacts while letting the user customize their format, paths, and names.

> **System scope:** All skills in `vera-plugin` target **System B** (customer
> repos the deployed Vera app operates on), not the `jasonsurratt/vera`
> bootstrap repo. This is distinct from the internal `init` skill under
> `.claude/skills/`, which is System A only.

## Goals

- Establish/maintain an opinionated baseline on a customer repo.
- Be idempotent — a second run on a satisfied repo writes nothing.
- Let the user change aspects of the project interactively.
- Work both interactively (human in Claude Code/opencode) and
  non-interactively (automated invocation → PR for later review).
- Ship cleanly to Claude Code (marketplace install) and opencode (documented
  install).

## Non-Goals

- Model/LLM routing decisions (out of scope for this design).
- Layered/opt-in module selection — deferred. v1 ships one bundle (the required
  core). The design leaves room to layer later.
- CI workflow scaffolding, README/.gitignore/language-manifest enforcement —
  these stay the repo owner's choice; the skill is silent on them.
- A hosted `skills.urls` index for opencode — deferred to a fast-follow.

---

## 1. Purpose and Modes

**Skill name:** `project-profile` (surfaces as `vera:project-profile` once the
plugin is installed — Claude Code namespaces plugin skills by plugin name).

**Required core artifacts** (existence required; format/path customizable, with
the chosen convention recorded in `PROJECT_PROFILE.md` and respected on
subsequent runs):

1. `CLAUDE.md` — agent guardrails.
2. `PROJECT_PROFILE.md` — stack + conventions summary; **source of truth for
   where the other four artifacts live**.
3. A spec file (default `docs/spec/README.md`, checkbox format).
4. A failure log + active guardrails (default `docs/failures/README.md` +
   `docs/failures/RULES.md`). **Required** — it keeps failure rate and cost
   down.
5. A task runner with `precommit`, `lint`, `format`, `test` targets (default
   `justfile`, accepts `Makefile` or any path declared in
   `PROJECT_PROFILE.md`).

**Two modes, chosen automatically from repo state. One entry point.**

- **Generate mode** — triggers when no `PROJECT_PROFILE.md` exists. Detects
  available signal, asks the user only the blocking unknowns (interactive),
  then presents a single review block of proposed files.
- **Drift mode** — triggers when `PROJECT_PROFILE.md` exists. Audits the five
  required artifacts against actual repo state and proposes targeted fixes.
  **If no drift is found, exits cleanly ("no drift") — no prompts, no
  writes.**

**Supported stacks:** Python and TypeScript only. These are the only options
offered when asking the user. Other languages are not offered, but an existing
non-Python/TS repo is **not clobbered** — the skill scaffolds the
language-independent core and leaves tooling/task-runner specifics as
`<fill-me-in>` (no opinionated default to apply).

---

## 2. Required Artifacts and Drift Checks

The skill's authority is exactly these five artifacts. Existence is required;
the specific path/filename/format is captured in `PROJECT_PROFILE.md` as the
canonical convention and respected on subsequent runs.

**1. `CLAUDE.md` (root).**
- Exists, non-trivial (>10 non-blank lines).
- Mentions the task-runner entrypoint (e.g. `just precommit`).
- Links to the spec file and failure-log paths declared in
  `PROJECT_PROFILE.md`.
- Drift = missing, empty, or referenced paths don't resolve.

**2. `PROJECT_PROFILE.md` (root).**
- Exists; `Stack` section populated (no `<fill-me-in>`).
- Declares paths for spec file, failure log, task runner, test dirs.
- Each declared path resolves on disk.
- Each declared tool (package manager, linter, formatter, test framework) has
  corresponding repo signal (lockfile, config, dependency).
- Drift = a profile claim the repo state contradicts.

**3. Spec file** (default `docs/spec/README.md`, overridable).
- Exists at the declared path.
- Contains ≥1 done-when criterion line (or the template marker for empty
  repos).
- If the chosen format uses slugs, every criterion line has one; slugs unique.
- Drift = missing, empty, or duplicate-slug. **Format is not enforced** — a
  custom format declared in the profile is respected, not rewritten.

**4. Failure log + guardrails** (default `docs/failures/README.md` +
`docs/failures/RULES.md`, overridable).
- Both exist at declared paths.
- `RULES.md` has an active-guardrails section header (empty is fine).
- `CLAUDE.md` references the rules-file path.
- Drift = either file missing, or `CLAUDE.md` doesn't reference `RULES.md`.

**5. Task runner** (default `justfile`, accepts `Makefile` or declared path).
- Exists at the declared path.
- Defines `precommit`, `lint`, `format`, `test` (target-name form depends on
  tool).
- Drift = file missing or a required target absent.

**Not enforced (intentionally):** CI workflow, `README.md` content,
`.gitignore`, language manifest. The skill stays silent on them.

**Drift mode output:** a list of findings, each with artifact, claimed vs.
actual, and a proposed fix — surfaced in the single review block (§4) before
any write.

---

## 3. Detection and Question Flow

**Step 1 — Detect.** Explore the repo (no hardcoded checklist): lockfiles,
language manifests, lint/format/typecheck configs, test dirs, existing task
runner, and the five required artifacts (present/absent + their conventions if
present).

**Step 2 — Classify blocking unknowns.** Only *blocking unknowns* become
questions — something that can't be reasonably defaulted and blocks progress:
- **Language/stack** when there's zero signal (the LICENSE-only case).
- Genuinely ambiguous signal (e.g. both `package.json` and `pyproject.toml`
  with no clear primary).

Everything else is a detected value or a sensible default shown in the review
block where the user can override it.

**Step 3 — Ask (interactive only), one question at a time.** Use a structured
question (e.g. `AskUserQuestion`). Stack options are **Python** and
**TypeScript** only (plus the implicit "Other" affordance). Keep to the minimum
needed to unblock — typically one question.

**Step 4 — Resolve defaults.** With the stack known, fill required-core
specifics from opinionated defaults (Python → uv/ruff/mypy/pytest/just; TS →
npm, detect pnpm/yarn / eslint / prettier / tsc --noEmit / vitest). These are
*proposals*, shown in the review block.

**Interactivity detection (B + C):**
- **B (primary):** an explicit signal from the invocation (a flag the
  caller/harness passes for non-interactive runs).
- **C (fallback):** when no flag is passed, infer from trigger context — GitHub
  event/automated → non-interactive; human-typed invocation → interactive.
- The unrelated `--in-multi-agent` soft flag is *not* this signal; treat
  unknown tokens as no-ops.

---

## 4. Review and Git Gates

**Generate mode, interactive.** After detection + minimal questions, print
**one review block**:
- Detected state (language, package manager, lint/format/typecheck, test
  framework, task runner) — each line marked *detected* vs. *defaulted*.
- Files to create/modify, each with proposed content (or a diff for
  modifications).
- Required artifacts already satisfied (listed, no action).

Then ask the **gate question** (one question, three answers):
> "What would you like to do?" → (1) leave as working-tree changes · (2) commit
> on current branch · (3) new branch + push + open PR.

At the end of the summary, add:
> "I presented this as a summary — if you'd prefer to review these as
> individual questions instead, say so and I'll walk through them one at a
> time."

**Drift mode, interactive.** Same shape; the review block is the list of drift
findings (claimed vs. actual + proposed fix). **No drift → print "No drift" and
exit. No gate question, no writes.**

**Non-interactive (either mode).** No review block, no gate question. Make
reasonable choices, write files on branch `vera/project-profile`, commit grouped
by concern, push, open a PR. The PR body **is** the review surface: it lists
every file and flags any `<fill-me-in>` placeholders (e.g. unknown stack)
prominently. Non-interactive drift mode that finds nothing exits without a PR.

Empty-repo non-interactive (LICENSE-only, no language signal) → emit only the
language-independent core (`CLAUDE.md`, `PROJECT_PROFILE.md` with `Stack:
<fill-me-in>`, spec file, failure log, placeholder `justfile` whose `precommit`
echoes a TODO), then open the PR. Visible TODOs are the human's review surface.

**Commit grouping** (skip empty groups):
1. `chore(project-profile): agent guardrails (CLAUDE.md, PROJECT_PROFILE.md)`
2. `chore(project-profile): spec scaffold`
3. `chore(project-profile): failure log + guardrails`
4. `chore(project-profile): task runner`

**Idempotency guarantee.** Re-running on a satisfied repo writes nothing and
opens no PR, in both modes. Convention preservation: an artifact in a
non-default location/format declared in `PROJECT_PROFILE.md` is respected,
never relocated or reformatted.

---

## 5. Plugin Packaging (Claude Code + opencode)

All claims below were verified empirically against installed tooling (Claude
Code 2.1.138, opencode 1.14.46, latest opencode 1.15.6) plus official docs and
source.

**Verified constraints:**
- **Claude Code plugin loader discovers skills *only* at `skills/<name>/SKILL.md`
  at the plugin root** — confirmed via debug log (`.claude/skills/` inside a
  plugin is ignored by the plugin mechanism; it only works as *project* skills
  by cwd).
- **opencode never scans a bare top-level `skills/`.** It scans
  `.opencode/{skill,skills}/`, `.claude/skills/`, `.agents/skills/` (project,
  walked up to worktree root, plus home-dir equivalents), the opt-in
  `skills.paths` config array, and `skills.urls` (HTTP `index.json`).
- **opencode `plugin` array is JS-module-only** (`PluginSource = "file" |
  "npm"`). Git URLs are not supported and a JS plugin has **no hook to register
  skills** (`Hooks` interface has no `skill` member; the `config` hook is
  notify-only). Verified on both 1.14.46 and 1.15.6. (Refutes the claim that a
  `git+`-spec plugin entry mounts bundled SKILL.md files — tested against
  `anthropics/skills`: zero skills discovered.)

**Decision:** Canonical skill tree at `skills/<name>/SKILL.md` (the one path
Claude Code's plugin loader actually loads). Bridge opencode via committed
config for in-repo dev and document the end-user install. The in-repo bridge
only matters for running tools *inside* this repo; end users consume the skill
in *their own* repos.

**Layout:**
```
vera-plugin/
├── .claude-plugin/
│   ├── plugin.json          # name: "vera", description, version, author
│   └── marketplace.json     # self-marketplace; plugins[].source = "."
├── skills/
│   └── project-profile/
│       └── SKILL.md         # canonical — Claude Code plugin reads here
├── opencode.json            # { "skills": { "paths": ["./skills"] } } — dev only
├── docs/
│   └── superpowers/specs/   # design docs (this file)
├── README.md                # install instructions for both tools
└── LICENSE
```

`plugin.json`:
```json
{
  "name": "vera",
  "description": "Vera project automation skills for Claude Code and opencode",
  "version": "0.1.0",
  "author": { "name": "Jason R. Surratt" }
}
```

`marketplace.json`:
```json
{
  "name": "vera-plugin",
  "description": "Vera project automation skills",
  "owner": { "name": "Jason R. Surratt" },
  "plugins": [
    {
      "name": "vera",
      "description": "Vera skills for Claude Code and opencode",
      "source": "."
    }
  ]
}
```

**Install UX:**
- **Claude Code:** `/plugin marketplace add golem-works-ai/vera-plugin` then
  `/plugin install vera`. Skill surfaces as `vera:project-profile`.
- **opencode (manual):** clone the repo and add `skills/` to global opencode
  config (`skills.paths`) or copy `skills/project-profile/` into
  `~/.config/opencode/skills/` (or `~/.claude/skills/`). Documented in README.
- **opencode (in-repo dev):** the committed `opencode.json` makes
  `opencode debug skill` find `project-profile` when run from the repo root
  (relative `skills.paths` resolve against cwd — run-from-root caveat).

**Caveats / risk:**
- `opencode.json` `skills.paths` relative path resolves against cwd, not the
  config file — breaks if opencode is launched from a subdirectory. Acceptable:
  it's a dev-only convenience.
- The symlink alternative (`.claude/skills -> ../skills`) is cwd-robust (via
  opencode's up-walk) but carries Windows/checkout risk. Not chosen; revisit
  only if the config approach proves insufficient.

**Fast-follow (deferred):** host a generated `index.json` (e.g. GitHub Pages)
so opencode users can install via `skills.urls` — the closest opencode gets to
Claude Code's marketplace polish. Additive; does not block v0.1.

---

## 6. Testing the Skill

Skills are markdown instruction files, not code; "testing" means verifying the
skill produces correct artifacts across the designed scenarios.

**Tier 1 — Fixture-based behavior tests (core).** A harness runs the skill
headless (`claude -p`, `--plugin-dir ./`) against fixture repos, then asserts on
resulting working-tree changes. Run non-interactive (no prompts). Fixtures:
- `empty/` — LICENSE only → language-independent core + `Stack: <fill-me-in>` +
  placeholder justfile.
- `python-clean/` — pyproject + uv.lock + tests/ → detection, no questions,
  Python defaults proposed.
- `typescript-clean/` — package.json + pnpm-lock → pnpm documented (not
  replaced), TS defaults.
- `populated-satisfied/` — all five artifacts present and consistent → **no
  drift, zero writes** (idempotency guarantee).
- `populated-drift/` — profile claims pnpm but lockfile is npm; spec file
  missing → specific drift findings.
- `unsupported-language/` — a Rust repo → language-independent core only,
  tooling left as fill-me-in, no clobbering.

Assertions: which files created/modified, presence of required sections, and
that satisfied repos stay untouched.

**Tier 2 — Packaging validation (deterministic).**
- `claude plugin validate .` passes.
- `plugin.json` / `marketplace.json` parse with required fields.
- `opencode debug skill` (with in-repo `opencode.json`) lists `project-profile`.
- The skill loads as `vera:project-profile` via `--plugin-dir`.

**Tier 3 — Frontmatter/lint.** `SKILL.md` frontmatter conforms (name
lowercase-alphanumeric-hyphens matching the dir; description within length
limits) — satisfies both Claude Code and opencode validators.

**Deliberately skipped (YAGNI):** mocking the LLM; snapshotting exact generated
prose (assert structure/required sections instead); automated interactive-mode
tests (cover non-interactive in CI; verify interactive manually).

**Cadence & location:**
- Harness lives in the `vera-plugin` repo (self-contained, own CI).
- **Option (c):** deterministic Tiers 2–3 run in CI on every PR; model-dependent
  Tier 1 fixtures run behind a `just test-skill` target on demand / nightly, to
  control token cost and non-determinism.

---

## Open Items for the Implementation Plan

- Exact wording/structure of the generated `CLAUDE.md`, `PROJECT_PROFILE.md`,
  spec template, and failure-registry files for the v1 bundle.
- The precise non-interactive flag name/contract (interactivity detection B).
- Fixture repo contents and the assertion harness implementation.
- README content for both install paths.
