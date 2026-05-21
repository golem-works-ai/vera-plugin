# Plugin Packaging and Distribution

## Goal

`vera-plugin` ships as a Claude Code plugin (marketplace install) and an
opencode skill bundle (documented install). A single canonical skill tree serves
both ecosystems within their verified discovery constraints.

See [design §5](../superpowers/specs/2026-05-21-project-profile-skill-design.md).

## Done When

### Layout

- [ ] Skills live at the canonical path `skills/<name>/SKILL.md` at the repo root <!-- slug: packaging.layout.canonical-skills-dir -->
- [ ] `.claude-plugin/plugin.json` exists with `name` `vera`, a description, a version, and an author <!-- slug: packaging.layout.plugin-json -->
- [ ] `.claude-plugin/marketplace.json` exists, lists the `vera` plugin with `source: "."` (self-marketplace) <!-- slug: packaging.layout.marketplace-json -->
- [ ] `opencode.json` exists with `skills.paths` set to `["./skills"]` for in-repo opencode development <!-- slug: packaging.layout.opencode-json -->

### SKILL.md frontmatter

- [ ] The skill's `SKILL.md` frontmatter `name` is lowercase alphanumeric with single hyphens, 1–64 chars, and matches its directory name <!-- slug: packaging.frontmatter.name-rules -->
- [ ] The skill's `SKILL.md` frontmatter `description` is within the length limits accepted by both Claude Code and opencode validators <!-- slug: packaging.frontmatter.description-limits -->

### Claude Code install

- [ ] `claude plugin validate .` passes <!-- slug: packaging.claude.validate -->
- [ ] After `/plugin marketplace add golem-works-ai/vera-plugin` and `/plugin install vera`, the skill is invocable as `vera:project-profile` <!-- slug: packaging.claude.install-namespaced -->

### opencode install

- [ ] Running `opencode debug skill` from the repo root (with the committed `opencode.json`) lists `project-profile` <!-- slug: packaging.opencode.debug-lists-skill -->
- [ ] The README documents the opencode end-user install: clone and add `skills/` to global opencode config, or copy `skills/project-profile/` into a discovered global path <!-- slug: packaging.opencode.readme-install -->

### Documentation

- [ ] The README explains what the plugin is and gives install instructions for both Claude Code and opencode <!-- slug: packaging.docs.readme -->

## Planned Refill Items

#### 🚧 Host a skills.urls index for one-line opencode install

- [ ] A generated `index.json` is published (e.g. via GitHub Pages) listing the bundled skills and their `SKILL.md` URLs <!-- slug: packaging.skills-urls.index-published -->
- [ ] The README documents the `skills.urls` config entry for opencode users <!-- slug: packaging.skills-urls.readme -->
