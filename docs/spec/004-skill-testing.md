# Skill Testing

## Goal

The `project-profile` skill is verified across its decision matrix with a
fixture-based behavior harness plus deterministic packaging and frontmatter
checks. Cost and non-determinism are controlled by separating model-dependent
tests from deterministic ones.

See [design §6](../superpowers/specs/2026-05-21-project-profile-skill-design.md).

## Done When

### Tier 1 — fixture behavior tests

- [ ] A harness runs the skill headless (`claude -p`, `--plugin-dir ./`) against fixture repos and asserts on resulting working-tree changes, run non-interactive <!-- slug: testing.tier1.harness -->
- [ ] An `empty/` fixture (LICENSE only) yields the language-independent core, `Stack: <fill-me-in>`, and a placeholder task runner <!-- slug: testing.tier1.empty -->
- [ ] A `python-clean/` fixture (pyproject + uv.lock + tests/) yields detection with no questions and proposed Python defaults <!-- slug: testing.tier1.python-clean -->
- [ ] A `typescript-clean/` fixture (package.json + pnpm-lock) documents pnpm rather than replacing it and proposes TypeScript defaults <!-- slug: testing.tier1.typescript-clean -->
- [ ] A `populated-satisfied/` fixture (all five artifacts present and consistent) produces no drift and zero writes <!-- slug: testing.tier1.populated-satisfied -->
- [ ] A `populated-drift/` fixture (profile claims pnpm but lockfile is npm; spec file missing) produces specific drift findings <!-- slug: testing.tier1.populated-drift -->
- [ ] An `unsupported-language/` fixture (Rust repo) yields the language-independent core only, tooling left as `<fill-me-in>`, with no clobbering <!-- slug: testing.tier1.unsupported-language -->

### Tier 2 — packaging validation

- [ ] `claude plugin validate .` passes in CI <!-- slug: testing.tier2.claude-validate -->
- [ ] `plugin.json` and `marketplace.json` parse and contain required fields <!-- slug: testing.tier2.manifests-parse -->
- [ ] `opencode debug skill` lists `project-profile` with the in-repo `opencode.json` <!-- slug: testing.tier2.opencode-discovers -->
- [ ] The skill loads as `vera:project-profile` via `--plugin-dir` <!-- slug: testing.tier2.namespaced-load -->

### Tier 3 — frontmatter lint

- [ ] `SKILL.md` frontmatter conforms to the name and description rules accepted by both Claude Code and opencode validators <!-- slug: testing.tier3.frontmatter-conforms -->

### Cadence and location

- [ ] The test harness lives in the `vera-plugin` repo and runs on its own CI <!-- slug: testing.cadence.in-repo -->
- [ ] Deterministic Tiers 2–3 run in CI on every PR; model-dependent Tier 1 runs behind a `just test-skill` target on demand or nightly <!-- slug: testing.cadence.split -->
- [ ] A manual interactive checklist enumerates the three behaviors without automated coverage: the one-at-a-time stack question, the gate question, and the "present as individual questions" affordance <!-- slug: testing.manual.interactive-checklist -->
