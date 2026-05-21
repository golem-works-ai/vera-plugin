# Spec System

Specs use GitHub checkbox states and stable slug annotations. Each done-when
item maps to implementation and test coverage.

## Checkbox States

- `[ ]` Not started
- `[#123]` In progress and linked to issue 123
- `[x]` Complete

## Slug Annotation

Each done-when item includes a stable slug comment in `area.section.criterion`
form:

```markdown
- [ ] The skill exits without writing when no drift is found <!-- slug: project-profile.drift.no-op -->
```

Slugs must be globally unique within `docs/spec/`. Reference them in tests so
spec coverage can be tracked.

## Pull Request Requirement

If a pull request modifies files under `docs/spec/`, include at least one
relevant slug citation in a dedicated `## Spec Slug Citations` section in the PR
description so automation can verify spec traceability.

```markdown
## Spec Slug Citations
- project-profile.drift.no-op
```

## Done Criteria

A checked item should map to implementation and test coverage. Do not mark an
item complete until both exist.

## Planned Refill Items

Concrete spec files may include planned backlog items to seed implementation
issues. Use this heading format for each planned item:

```markdown
#### 🚧 Add a hosted skills.urls index for opencode
```

Add acceptance criteria as unchecked checklist entries with slug comments under
the heading. Once work starts, add a linked issue reference on the checklist
item (`[#123]`) or in the heading text.
