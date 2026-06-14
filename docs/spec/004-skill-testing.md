# Skill Testing

## Goal

The `project-profile` skill is verified across its decision matrix with a
fixture-based behavior harness plus deterministic packaging and frontmatter
checks. Cost and non-determinism are controlled by separating model-dependent
tests from deterministic ones.

## Done When

### Tier 1 — fixture behavior tests

- [ ] A harness runs the skill non-interactively against fixture repos and asserts on the resulting working-tree changes <!-- slug: testing.tier1.harness -->
- [ ] An `empty/` fixture (LICENSE only) yields the language-independent core, `Stack: <fill-me-in>`, and a placeholder task runner <!-- slug: testing.tier1.empty -->
- [#15] An `ambiguous-signal/` fixture (conflicting Python and TypeScript repo signal) is treated as a blocking unknown, and the blocking stack prompt limits supported choices to Python or TypeScript (with an Other escape hatch) while non-blocking values still default from repo signal <!-- slug: testing.tier1.blocking-unknowns -->
- [ ] A `python-clean/` fixture (pyproject + uv.lock + tests/) yields detection with no questions and proposes Python defaults (`uv` + `ruff` + `pytest`) <!-- slug: testing.tier1.python-clean -->
- [ ] A `typescript-clean/` fixture (package.json + pnpm-lock) documents pnpm rather than replacing it and proposes TypeScript defaults (`pnpm` + `eslint` + `prettier` + `vitest`) <!-- slug: testing.tier1.typescript-clean -->
- [ ] A `populated-satisfied/` fixture (all five artifacts present and consistent) produces no drift and zero writes <!-- slug: testing.tier1.populated-satisfied -->
- [ ] A `populated-drift/` fixture (profile claims pnpm but lockfile is npm; spec file missing) produces specific drift findings <!-- slug: testing.tier1.populated-drift -->
- [ ] An `unsupported-language/` fixture (Rust repo) yields the language-independent core only (equivalent to choosing Other in stack selection), tooling left as `<fill-me-in>`, with no clobbering <!-- slug: testing.tier1.unsupported-language -->

### Tier 2 — packaging validation

- [ ] The Claude Code plugin manifest validates as well-formed <!-- slug: testing.tier2.claude-validate -->
- [ ] `plugin.json` and `marketplace.json` parse and contain their required fields <!-- slug: testing.tier2.manifests-parse -->
- [ ] opencode discovers `project-profile` when run in the repo <!-- slug: testing.tier2.opencode-discovers -->
- [ ] The skill loads under the `vera:project-profile` namespace as a plugin <!-- slug: testing.tier2.namespaced-load -->

### Tier 3 — frontmatter lint

- [ ] `SKILL.md` frontmatter conforms to the name and description rules accepted by both Claude Code and opencode validators <!-- slug: testing.tier3.frontmatter-conforms -->

### Cadence and location

- [ ] The test harness lives in the `vera-plugin` repo and runs on its own CI <!-- slug: testing.cadence.in-repo -->
- [ ] Deterministic Tiers 2–3 run in CI on every PR; model-dependent Tier 1 runs on demand or nightly to control token cost and non-determinism <!-- slug: testing.cadence.split -->
- [#16] A manual interactive checklist verifies that only blocking unknowns are asked and each prompt asks exactly one unknown at a time <!-- slug: testing.manual.interactive-checklist -->
- [ ] The manual interactive checklist also covers the gate question and the "present as individual questions" affordance <!-- slug: testing.manual.gate-and-represent -->
