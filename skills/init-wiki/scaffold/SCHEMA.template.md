# Wiki Schema — <REPO> (local instance)

> Universal conventions (page model, navigation, provenance, self-improving
> update, modification protocol, orient/lint) live in the canonical
> **`CONVENTIONS.md`**, refreshed by the `init-wiki` skill. **This file holds
> only what is specific to *this* wiki** — domain, tag taxonomy, hubs, and
> source paths — and is created once by `init-wiki` and never overwritten. Edit
> it freely; it is yours.

<!-- init-wiki: installed-conventions-version: 1 -->

## Domain

**<REPO> operations** — the agent's persistent knowledge base covering:

- **<primary subject>** — <one line>
- **<secondary subject>** — <one line>
- **Conventions** — <spec format, auth, gotchas specific to this repo>
- **User / people** — <who; note any lookalike identities to disambiguate>

This wiki is the agent's **warm-tier memory**: deeper than the small
always-loaded pointer file, but bounded by what the agent can hold on its
persistent volume. The pointer file holds 1-line pointers into this wiki.

## Hubs

The high-degree pages any task reliably lands on first (see Navigation model in
`CONVENTIONS.md`). Keep this to one hub per domain:

- `[[<project-hub>]]`
- `[[<person-hub>]]`
- `[[<org-or-topic-hub>]]`

## Source paths

How `sources:` frontmatter references resolve for this wiki (see Source
references in `CONVENTIONS.md`):

- **Local clone** (preferred): `<path-to-local-clone>/...`
- **Raw URL base** (when no clone): `https://raw.githubusercontent.com/<org>/<repo>/main/...`
- **`raw/`**: external articles/papers/transcripts only.

## Tag Taxonomy

<!--
  REQUIRED SECTION — do not remove or rename this heading. `wiki_lint.py` reads
  the tags from this exact `## Tag Taxonomy` section; if it is missing, tag
  validation SILENTLY NO-OPS (no error). Define every tag here BEFORE using it;
  a tag on a page that is not listed here is a lint error.
-->

Define tags here before using them. Every tag on a page must appear in this list.

### Meta (starter set — keep or adapt)
- `meta-question` — open question
- `meta-comparison` — side-by-side analysis
- `meta-summary` — synthesis / overview

### Roles & People
- `user` — <the primary user>
- `person` — other people in the user's network

<!-- Add repo-specific tag groups below (repos, conventions, infra, ops, topics). -->
