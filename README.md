# vera plugin

`vera-plugin` bundles reusable skills for Claude Code and opencode.

## Install

### Claude Code plugin

Install from this repository's marketplace metadata, then invoke skills with the
`vera:` namespace.

### opencode one-line install (`skills.urls`)

Add the published skills index URL to your opencode config:

```json
{
  "skills": {
    "urls": [
      "https://raw.githubusercontent.com/golem-works-ai/vera-plugin/main/index.json"
    ]
  }
}
```

This index is generated from the canonical `skills/<name>/SKILL.md` tree and
published at the repository root (`index.json`).

## Verify

- Open `https://raw.githubusercontent.com/golem-works-ai/vera-plugin/main/index.json` and confirm it
  lists the bundled skills and `SKILL.md` URLs.
- Run opencode's skill listing/debug command and confirm skills from the index
  are available.
