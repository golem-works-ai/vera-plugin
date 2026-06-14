# Project Profile — Core Behavior

## Goal

`vera:project-profile` establishes and maintains an opinionated minimum baseline
on a System B customer repo. It is idempotent, picks its mode from repo state,
asks the user only what it must, and lets the user decide how changes land.

## Done When

### Modes

- [ ] The skill runs from a single entry point and selects its mode automatically from repo state <!-- slug: project-profile.mode.auto-select -->
- [ ] Generate mode triggers when no `PROJECT_PROFILE.md` exists <!-- slug: project-profile.mode.generate-trigger -->
- [ ] Drift mode triggers when `PROJECT_PROFILE.md` already exists <!-- slug: project-profile.mode.drift-trigger -->

### Detection

- [ ] The skill detects the repo's stack, tooling, and which required artifacts already exist from available repo signal <!-- slug: project-profile.detect.explore -->
- [x] The skill treats missing or genuinely ambiguous language signal as blocking unknowns, while defaulting non-blocking values from repo signal <!-- slug: project-profile.detect.blocking-unknowns -->

### Question flow

- [x] In an interactive session, the skill asks only blocking unknowns and asks them one question at a time <!-- slug: project-profile.questions.minimal-one-at-a-time -->
- [x] The stack question offers only Python and TypeScript as supported options (with "Other" as an unsupported-language escape hatch) <!-- slug: project-profile.questions.python-typescript-only -->
- [x] Choosing the "Other" stack escape hatch routes to the language-independent core with tooling left as `<fill-me-in>` <!-- slug: project-profile.questions.other-escape-hatch -->

### Stack handling

- [ ] With a known supported stack, the skill proposes its opinionated default tooling for that stack <!-- slug: project-profile.stack.opinionated-defaults -->
- [ ] An existing repo in an unsupported language is not clobbered; the skill scaffolds only the language-independent core and leaves tooling as `<fill-me-in>` <!-- slug: project-profile.stack.unsupported-not-clobbered -->

### Interactivity detection

- [ ] An explicit invocation flag forces non-interactive mode (signal B) <!-- slug: project-profile.interactivity.explicit-flag -->
- [ ] With no flag, the skill infers interactivity from trigger context — automated/GitHub trigger is non-interactive, human invocation is interactive (signal C) <!-- slug: project-profile.interactivity.trigger-fallback -->
- [ ] The unrelated `--in-multi-agent` token is treated as a no-op, not as the interactivity signal <!-- slug: project-profile.interactivity.ignore-multi-agent -->

### Review and git gates

- [ ] Interactive generate mode presents a single review block (detected vs. defaulted values, files to create/modify, and already-satisfied artifacts) before any write <!-- slug: project-profile.gate.review-block -->
- [ ] The gate question offers three outcomes: leave as working-tree changes, commit on the current branch, or open a PR <!-- slug: project-profile.gate.three-outcomes -->
- [ ] The end-of-summary message offers to re-present the review as individual questions on request <!-- slug: project-profile.gate.offer-questions -->

### Non-interactive behavior

- [ ] Non-interactive runs make reasonable choices and open a PR with no prompts <!-- slug: project-profile.noninteractive.pr -->
- [ ] The non-interactive PR body lists every changed file and flags `<fill-me-in>` placeholders prominently as the review surface <!-- slug: project-profile.noninteractive.pr-body-flags -->
- [ ] A non-interactive empty repo (no language signal) emits only the language-independent core plus a placeholder task runner <!-- slug: project-profile.noninteractive.empty-core -->

### Idempotency

- [ ] Re-running on a satisfied repo writes nothing and opens no PR, in both modes <!-- slug: project-profile.idempotency.no-writes -->
- [ ] Drift mode that finds no drift prints a "no drift" message and exits without prompting or writing <!-- slug: project-profile.idempotency.no-drift-exit -->
- [ ] An artifact in a non-default location or format declared in `PROJECT_PROFILE.md` is respected, never relocated or reformatted <!-- slug: project-profile.idempotency.preserve-convention -->
