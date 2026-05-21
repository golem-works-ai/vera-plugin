# Plugin Packaging and Distribution

## Goal

`vera-plugin` ships as a Claude Code plugin (marketplace install) and an
opencode skill bundle (documented install). A single canonical skill tree serves
both ecosystems within their verified discovery constraints.

## Done When

### Layout

- [ ] Skills live at the canonical path `skills/<name>/SKILL.md` at the repo root <!-- slug: packaging.layout.canonical-skills-dir -->
- [ ] `.claude-plugin/plugin.json` exists with `name` `vera`, a description, a version, and an author <!-- slug: packaging.layout.plugin-json -->
- [ ] `.claude-plugin/marketplace.json` exists, lists the `vera` plugin with `source: "."` (self-marketplace) <!-- slug: packaging.layout.marketplace-json -->
- [ ] `opencode.json` exists and configures opencode to discover the canonical skills directory for in-repo development <!-- slug: packaging.layout.opencode-json -->

### SKILL.md frontmatter

- [ ] The skill's `SKILL.md` frontmatter `name` and `description` conform to the rules accepted by both the Claude Code and opencode validators <!-- slug: packaging.frontmatter.conforms -->

### Claude Code install

- [ ] The plugin manifest validates as well-formed <!-- slug: packaging.claude.validate -->
- [ ] The repo is installable as a Claude Code plugin from its self-marketplace, after which the skill is invocable as `vera:project-profile` <!-- slug: packaging.claude.install-namespaced -->

### opencode install

- [ ] opencode discovers `project-profile` when run in the repo <!-- slug: packaging.opencode.debug-lists-skill -->
- [ ] The README documents the opencode end-user install path <!-- slug: packaging.opencode.readme-install -->

### Documentation

- [ ] The README explains what the plugin is and gives install instructions for both Claude Code and opencode <!-- slug: packaging.docs.readme -->

## Planned Refill Items

#### 🚧 Host a skills.urls index for one-line opencode install

- [ ] A generated `index.json` is published (e.g. via GitHub Pages) listing the bundled skills and their `SKILL.md` URLs <!-- slug: packaging.skills-urls.index-published -->
- [ ] The README documents the `skills.urls` config entry for opencode users <!-- slug: packaging.skills-urls.readme -->
