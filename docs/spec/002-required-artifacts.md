# Project Profile — Required Artifacts and Drift Checks

## Goal

The skill enforces the *existence* of five core artifacts. Format, filename, and
path are customizable; the chosen convention is recorded in `PROJECT_PROFILE.md`
and respected on later runs. Drift mode audits each artifact against actual repo
state.

## Done When

### Authority scope

- [ ] The skill's authority is exactly the five required artifacts; it stays silent on CI workflows, `README.md` content, `.gitignore`, and language manifests <!-- slug: artifacts.scope.five-only -->

### CLAUDE.md

- [ ] `CLAUDE.md` exists at the repo root and carries real agent guardrails rather than being empty or a stub <!-- slug: artifacts.claude-md.exists -->
- [ ] `CLAUDE.md` references the task-runner entrypoint and the spec-file and failure-log paths declared in `PROJECT_PROFILE.md`, and those paths resolve <!-- slug: artifacts.claude-md.references-resolve -->

### PROJECT_PROFILE.md

- [ ] `PROJECT_PROFILE.md` exists with a populated `Stack` section for supported stacks (Python/TypeScript); unsupported or unknown stacks may remain `<fill-me-in>` until confirmed <!-- slug: artifacts.profile.stack-populated -->
- [ ] `PROJECT_PROFILE.md` declares paths for the spec file, failure log, task runner, and test dirs, and each declared path resolves on disk <!-- slug: artifacts.profile.paths-resolve -->
- [ ] Each tool declared in `PROJECT_PROFILE.md` (package manager, linter, formatter, test framework) has corresponding repo signal <!-- slug: artifacts.profile.tools-have-signal -->

### Spec file

- [ ] A spec file exists at the declared path (default `docs/spec/README.md`) and contains at least one done-when criterion line, or the template marker for empty repos <!-- slug: artifacts.spec.exists -->
- [ ] When the format declared in `PROJECT_PROFILE.md` is slug-based, every criterion line carries a unique slug; a declared non-slug format skips the slug checks <!-- slug: artifacts.spec.slug-checks -->
- [ ] The spec file's format is never rewritten — a custom declared format is respected, not normalized to the default <!-- slug: artifacts.spec.format-not-enforced -->

### Failure log and guardrails

- [ ] The failure log and active-guardrails files both exist at their declared paths (default `docs/failures/README.md` + `docs/failures/RULES.md`) <!-- slug: artifacts.failures.exist -->
- [ ] The guardrails file has an active-guardrails section header (an empty section is acceptable) and `CLAUDE.md` references the guardrails-file path <!-- slug: artifacts.failures.section-and-reference -->

### Task runner

- [ ] A task runner exists at the declared path (default `justfile`, accepts `Makefile` or any declared path) <!-- slug: artifacts.task-runner.exists -->
- [ ] The task runner defines `precommit`, `lint`, `format`, and `test` targets <!-- slug: artifacts.task-runner.required-targets -->

### Drift output

- [ ] Drift findings each report the artifact, the claimed vs. actual state, and a proposed fix, surfaced in the single review block before any write <!-- slug: artifacts.drift.findings-format -->
