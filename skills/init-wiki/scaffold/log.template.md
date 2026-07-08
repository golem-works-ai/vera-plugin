# Wiki Log

> Chronological record of all wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: create, ingest, update, query, lint, archive, delete
> When this file exceeds 500 entries, rotate: rename to `log-YYYY.md`, start fresh.

## [<DATE>] create | Wiki initialized
- Installed by the `init-wiki` skill (canonical source: golem-works-ai/vera-plugin)
- Structure: CONVENTIONS.md (canonical), SCHEMA.md (local instance), index.md, log.md, entities/, concepts/, comparisons/, queries/, summaries/
- Wiki path: `$WIKI_PATH` (see CLAUDE.md); conventions-version: 1
- Next: fill in SCHEMA.md domain + tag taxonomy + hubs, then ingest first sources
