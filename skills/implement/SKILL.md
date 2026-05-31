# Implement - Development Workflow Orchestrator

This skill orchestrates the development workflow using sub-agents for each phase.
It stays lightweight while delegating context-heavy work to fresh sub-agents.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:test-driven-development` and
`superpowers:verification-before-completion` before using this skill.

## Lifecycle Boundary

**Stage:** Code lifecycle (TDD, test, review, verify) — post-claim, pre-push.

```
iterate (issue lifecycle) ──▶ implement (code lifecycle) ──▶ finalize-and-push
                                 ├── TDD agent
                                 ├── code-reviewer (self-review loop)
                                 └── verification-agent (fresh-eyes)
```

| Boundary | This Skill | Other Skill |
|----------|-----------|-------------|
| Before | Issue claimed, branch created | `iterate` handles claim + branch |
| After | Commits ready, NOT pushed | `iterate` invokes `finalize-and-push` for push + PR |
| Review type | Self-review (pre-push quality) | `address-review-feedback` handles human reviewer feedback (post-push) |
| Bug fixes | Spawns `bug-fix` for UI bugs found during verification | `bug-fix` can also be invoked standalone |

**Does NOT:** claim issues, push code, create PRs, or address human reviewer comments.

**Resource rule:** Do NOT run tests (`just precommit`, `just test-all`, or `uv run pytest`) or
`code-reviewer` sub-agents concurrently with each other. Each is resource-intensive;
serialize heavyweight operations. This prevents OOM kills on memory-constrained runners
(8 GB fly.io VMs).

## When to Use

- Called by `iterate` skill after claiming an issue
- Called directly when implementing a feature without a GitHub issue
- Called when you have clear acceptance criteria to implement

## Workflow Overview

```
implement (orchestrator, low context)
├── 1. Validate preconditions
├── 2. Spawn TDD agent → implements features (commits changes)
├── 2.5. Merge main (keep branch current)
├── 2.6. Lint & format gate → auto-fix → verify clean (before review)
├── 3. Code review loop → fix issues → re-review (loop until clean, max 2)
├── 4. Spawn ui-qa agent → tests UI (if applicable)
├── 5. Verification gate (quick checks)
├── 6. Spawn adversarial verifier → skeptical fresh-eyes check
└── 7. Return success/failure with details (does NOT push - caller handles that)
```

**Key principle:** The adversarial verifier (Step 6) is a FRESH agent with no implementation
context. Its job is to DISPROVE success claims, catching "works for me" blindness and
TODO/placeholder code that slipped through.

## Execution

### Step 1: Validate Preconditions

Before spawning any agents, verify:

```bash
# Ensure we're on a clean state
git status --porcelain
```

#### Scope Sanity Check

Before spawning any implementation agents, do a quick gut-check on the issue scope.
If the issue description makes the scope obviously absurd — hundreds of files to modify,
multi-month rewrites, entire system redesigns — refuse immediately:

> "This issue appears far too large to implement in a single job. Please break it into
> focused sub-issues of 50–100k tokens each."

This is NOT a thorough re-estimation. It's a fast sanity guard to catch issues that
slipped through without review-plan sizing. When in doubt, proceed — review-plan's
estimate is the authoritative sizing mechanism.

### Step 2: Spawn TDD Implementation Agent

Create a sub-agent with Opus (default) or Sonnet (if issue specifies) to do the actual implementation:

```
Task: Implement the following using TDD methodology.

## Requirements
<paste acceptance criteria from issue or user request>

## Instructions
1. Follow superpowers:test-driven-development methodology
2. For EACH acceptance criterion, follow RED-GREEN-REFACTOR:
   - RED: Write a failing test, verify it fails (MANDATORY)
   - GREEN: Write minimum code to pass, verify it passes
   - REFACTOR: Clean up while keeping tests green. **This includes merging
     duplicates:** if the code you touched has a near-twin elsewhere (copy-paste
     siblings), consolidate them into one implementation now. "Write minimum code
     to pass" governs *new behavior* — it is not permission to leave a known
     duplicate of code you are already editing in place. Copy drift is a top
     source of Vera bugs; merging a duplicate you are touching is in-scope best
     practice, not scope creep. If the plan names duplicates to merge, do it; if
     you discover one, merge it and report it in the handoff.
3. **Spec slug coverage (MANDATORY):** If an acceptance criterion corresponds to a
   `Done-when` item in `docs/spec/` that carries a `<!-- slug: topic.section.criterion -->`
   annotation, the test for that criterion MUST have a matching
   `@pytest.mark.spec("topic.section.criterion")` marker. List slugs with:
   ```bash
   grep -rh 'slug:' docs/spec/ | grep -oP '(?<=slug: )[\w.-]+' | sort -u
   ```
   A test without its slug marker does not count as covering the criterion.
4. Run `just precommit` after all criteria are implemented
   **Do NOT run background Bash tasks or sub-agents concurrently with `just precommit`.**
   The command fans out 5 parallel test tiers, each spawning N pytest workers. Wait
   for precommit to exit before starting any other process.
5. If precommit fails, fix issues and re-run

## Context
- Working directory: <pwd>
- Baseline coverage: <X>%
- Related files: <list key files if known>

## Handoff
When complete, provide:
- List of files changed
- Tests added (count and names)
- Final coverage percentage
- Any concerns or edge cases discovered
- Whether UI files were modified (templates/, static/, router.py)
- **RED phase evidence for each criterion**: Exact test output showing failure before implementation
- **GREEN phase evidence for each criterion**: Exact test output showing pass after implementation
- **Structured `tdd_events` list** — one entry per phase commit, used by the orchestrator
  to persist `JobLog` rows via `vera.lifecycle.tdd_stages.record_tdd_event`. The
  parent `implement` flow writes one row per event before returning so that
  `tests/integration/test_tdd_ordering.py` can verify ordering and the Tier 3
  acceptance test can read the trail from staging job logs (issue #2379):
  ```json
  {
    "tdd_events": [
      {"phase": "red",   "criterion_slug": "topic.section.criterion", "commit_sha": "<sha>"},
      {"phase": "green", "criterion_slug": "topic.section.criterion", "commit_sha": "<sha>"}
    ]
  }
  ```
  Every spec-tagged criterion in the handoff MUST have a matching `red` event;
  green-only criteria indicate skipped TDD and will be flagged as PARTIAL.

**CRITICAL**: If you cannot provide RED/GREEN evidence for a criterion, that criterion is INCOMPLETE.
Following superpowers:verification-before-completion, claims require proof.
```

**Wait for TDD agent to complete.**

If TDD agent:
- **Succeeds**: Continue to Step 3
- **Fails with fixable issues**: Spawn a new TDD agent with the failure context
- **Fails with blocking issues**: Return failure to caller with details

### Step 2.5: Merge Main

Keep the branch current with main before linting and review:

```bash
git fetch origin main
if ! git merge origin/main --no-edit; then
  echo "Merge produced conflicts — resolving before continuing."
  # Resolve every path in `git ls-files -u | awk '{print $4}' | sort -u`
  # via Read/Edit, then `git add <file>` each. When `git ls-files -u` is empty:
  git commit --no-edit
fi
```

Do NOT push the merge commit separately — the caller (`finalize-and-push`) batches it
with the implementation commits so only one CI cycle runs. If conflicts cannot be
resolved, return PARTIAL with details.

### Step 2.6: Lint & Format Gate (Before Review)

**Before dispatching the code reviewer, run a single auto-format + lint pass to catch
trivially fixable issues locally.** This prevents the reviewer from spending tokens on
formatting errors. Encouraging multiple retries here masks real lint errors with cosmetic
fixes, so the budget is deliberately tight: **one auto-fix pass, then verify.**

Run the unconditional pre-pass — auto-fix, then auto-commit *any* resulting diff, then
verify:

```bash
uvx ruff check --fix . || true
uvx ruff format src/ tests/
git add -u
if ! git diff --cached --quiet; then
  git commit -m "style: auto-format with ruff"
fi
just lint 2>&1 | tail -40   # must now pass cleanly
```

**If `just lint` still exits non-zero after this single auto-fix pass:**

- Return **PARTIAL** with the lint output.
- Do NOT retry the auto-fix loop.
- Do NOT dispatch code-reviewer — a reviewer running against code that fails `just lint`
  wastes tokens on mechanical feedback CI will catch anyway.

**Only proceed to Step 3 when `just lint` passes cleanly on the first verify.**

### Step 3: Code Review Loop (max 2 iterations)

Dispatch code-reviewer subagent (see `code-reviewer` skill for canonical interface) to
review the changes. **Repeat until clean or 2 iterations, whichever comes first.**

```
iteration = 0
while iteration < 2:
    dispatch code-reviewer with git diff range
    if no Critical or Important issues:
        break  # review is clean
    fix Critical issues immediately
    fix Important issues
    commit fixes
    iteration += 1
if iteration == 2 and still has Important issues:
    return PARTIAL
```

For each iteration, dispatch the reviewer with:

```
Task: Review the code changes from the previous implementation.

## Instructions
1. Run `git diff <BASE_SHA>..<HEAD_SHA>` to see all changes
2. Check for:
   - DRY violations (repeated code that should be abstracted), including a
     near-duplicate of code this diff touched that was left un-merged — flag it
     and name the consolidation target
   - Missing or inadequate tests
   - Security issues (injection, XSS, etc.)
   - Code that doesn't match the codebase style
   - Over-engineering or unnecessary complexity
3. Report findings with severity (Critical / Important / Minor)

## Previous Review Context (if iteration > 1)
<list issues fixed from previous iteration>
Confirm these are resolved and check for any new issues introduced.
```

**After fixing review issues:**
- Run `just precommit` to verify fixes don't break anything (no concurrent background tasks)
- Commit the fixes in a separate commit
- Re-dispatch the reviewer with updated HEAD SHA
- Minor/nice-to-have issues: fix if trivial, otherwise note and proceed

**Wait for clean review before proceeding to Step 4.**

### Step 4: UI Verification (Conditional)

Check if UI files were modified:

```bash
git diff --name-only $(git merge-base HEAD main)..HEAD | grep -E "(templates/|static/|router\.py)"
```

**If UI files were modified**, spawn ui-qa agent (breaker mode):

```
Task: Test the UI changes using the ui-qa skill (breaker mode).

## Instructions
1. Read the ui-qa skill: .claude/skills/ui-qa/SKILL.md
2. Use breaker mode
3. Focus on testing the functionality described in:
   <paste acceptance criteria>
4. Report bugs with severity and reproduction steps

## Context
- UI files changed: <list>
- Expected functionality: <summary>
```

**Handle ui-qa results:**

| Severity                                   | Action                              |
| ------------------------------------------ | ----------------------------------- |
| Critical/High (basic functionality broken) | Spawn bug-fix agent, then re-verify |
| Medium (edge cases)                        | Spawn bug-fix agent, then re-verify |
| Low (cosmetic)                             | Note in report, proceed             |

### Step 5: Template-Route Contract Verification

If templates were modified, verify all HTMX endpoints have handlers:

```bash
# Find all HTMX endpoints in changed templates
for template in $(git diff --name-only $(git merge-base HEAD main)..HEAD | grep "\.html$"); do
    echo "=== Checking $template ==="
    grep -oE 'hx-(get|post|put|delete|patch)="[^"]*"' "$template" 2>/dev/null | while read line; do
        path=$(echo "$line" | sed 's/.*="\([^"]*\)".*/\1/' | sed 's/{{[^}]*}}/__PARAM__/g')
        method=$(echo "$line" | grep -oE 'hx-[a-z]+' | sed 's/hx-//' | tr '[:lower:]' '[:upper:]')
        echo "  $method $path"
    done
done
```

For each endpoint pattern, search for a matching route handler. If missing:
- **File a bug** with the missing endpoint details
- **Return failure** - cannot proceed with unimplemented endpoints

### Step 5.5: Verification Gate (Before SUCCESS)

**Before returning SUCCESS, you MUST verify the TDD agent's claims:**

1. **Check for red flags in diff**: `git diff HEAD~1 | grep -E "(DEPRECATED|TODO|FIXME|removed|disabled)"`
2. **Verify RED/GREEN evidence was provided** for each acceptance criterion
3. **Spot-check at least ONE criterion manually** through the actual interface
4. **Spec slug coverage check**: any Done-when criterion touched by this issue that has
   a slug annotation in `docs/spec/` must have a `@pytest.mark.spec("slug")` test marker.
   Run locally:
   ```bash
   grep -rh 'slug:' docs/spec/ | grep -oP '(?<=slug: )[\w.-]+' | sort -u > "${TMPDIR:-/tmp}/all_slugs.txt"
   grep -rhE '^[[:space:]]*@pytest\.mark\.spec\(' tests/ | grep -oP "(?<=spec\()['\"][^'\"]+['\"]" | tr -d "\"'" | sort -u > "${TMPDIR:-/tmp}/tested_slugs.txt"
   comm -23 "${TMPDIR:-/tmp}/all_slugs.txt" "${TMPDIR:-/tmp}/tested_slugs.txt" > "${TMPDIR:-/tmp}/untested_slugs.txt"
   ```
   Any slug relevant to this issue that appears in `${TMPDIR:-/tmp}/untested_slugs.txt` is a red
   flag — status is PARTIAL until the missing marker is added.

If ANY of these checks fail, status is PARTIAL, not SUCCESS.

**You cannot delegate verification integrity to sub-agents.**

**Note:** A git hook may BLOCK commits that introduce TODO/FIXME/placeholder comments in source files. If you hit this hook:
1. The work is incomplete - status is PARTIAL
2. Either complete the work or file a GitHub issue for the TODO
3. Replace the TODO comment with `# See issue #NNN`

### Step 5.6: Spawn Adversarial Verification Agent

**After TDD and review complete, spawn a FRESH agent specifically for verification.**

Why a fresh agent?
- No sunk-cost bias from implementation work
- Fresh context to be skeptical of claims
- Catches "works for me" blindness
- Enforces the "trust but verify" principle

Spawn a Sonnet agent that uses the `verification-agent` skill:

```
Task: Verify implementation using the verification-agent skill.

Read the skill: .claude/skills/verification-agent/SKILL.md

## Acceptance Criteria to Verify
<paste acceptance criteria from issue>

## Files Changed
<list from TDD agent report>

Follow the verification-agent skill methodology and return a Verification Report.
```

**Handle verification agent results:**

| Result                              | Action                                                      |
| ----------------------------------- | ----------------------------------------------------------- |
| All criteria verified with evidence | Proceed to Step 7 with SUCCESS                              |
| Any criterion failed                | Return PARTIAL, spawn bug-fix agent if fixable              |
| Red flags found (TODO/stubs)        | Return PARTIAL, document what needs completion in the issue |

**If verification agent finds issues the TDD agent missed:**
1. Do NOT try to fix in this cycle (context is limited)
2. Document findings clearly in the existing issue
3. Return PARTIAL with specific remediation steps
4. The next iteration will spawn fresh agents to fix

### Step 7: Return Results

**IMPORTANT:** This skill commits changes but does NOT push. The caller (iterate) handles pushing.

Return a structured report to the caller:

```markdown
## Implementation Complete

### Summary
- Acceptance criteria: X/Y implemented
- Tests added: N
- Coverage: X% (was Y%)
- UI verified: Yes/No/N/A
- Commits created: N (NOT pushed - caller handles that)

### Files Changed
- file1.py
- file2.html

### Issues Found
- [Severity] Description (fixed/filed as #NNN)

### Blockers
- None / List any unresolved issues

### Status
SUCCESS / PARTIAL / FAILED
```

## `--in-multi-agent` mode

When invoked with `--in-multi-agent` — the generic flag every
multi-agent harness (e.g. `/multi-review`, the benchmark `franken`
engine) passes to skills it wraps — you are running inside an outer
review loop. Adjust behavior so internal review defers to the outer
orchestrator:

1. Run the normal preconditions, TDD agent, merge-main, and lint-gate
   phases (everything up to and including the lint gate). The actual
   implementation still happens.
2. **Skip the internal `code-reviewer` Agent dispatch and the
   adversarial verification-agent spawn.** The outer `/multi-review`
   loop owns review. (References stable phase names rather than
   numeric step IDs — those drift.)
3. Keep UI verification and the template-route contract check — those
   produce signal the outer reviewers cannot get on their own.
4. Skip the normal return-wrap. Instead, print the implementation
   summary plus a draft artifact suitable for review: a unified-diff
   summary of the commits made, the test evidence, and the changed
   files list. Then print exactly one line of the form
   `MULTI_REVIEW_OUTPUT: branch:<branch-name>` so the `/multi-review`
   orchestrator knows where the work lives.
5. **Append both markers at the end of the output** using
   `.claude/skills/multi-review/scope-templates.md`. `/implement`
   **always uses Template B (service spec / implementation)** — the
   artifact is code, not a guidance document. Pick `complexity`
   honestly: `low` for one-file fixes, `medium` for typical features,
   `high` for cross-cutting changes — and DO NOT leave the literal
   `<low|medium|high>` placeholder in the marker.

The markers must survive verbatim through any revision rounds the
orchestrator runs.

## Status Definitions

| Status  | Meaning                                                   | When to Use                                                                 |
| ------- | --------------------------------------------------------- | --------------------------------------------------------------------------- |
| SUCCESS | All acceptance criteria implemented, tested, and verified | Every criterion has implementation, tests, AND manual verification evidence |
| PARTIAL | Some progress made but not all criteria complete          | Any criterion lacks implementation, tests, OR verification evidence         |
| FAILED  | Unable to make meaningful progress                        | Blocking issues prevent implementation                                      |

**PARTIAL is the honest path.** Common PARTIAL scenarios:
- Implemented 4 of 5 criteria
- Tests pass but manual verification blocked
- TDD agent reported success but verification gate failed
- Context exhaustion before completing all criteria

**It is never acceptable to report SUCCESS with incomplete work.**

## Handling Failures

### TDD Agent Context Exhaustion

If TDD agent runs out of context mid-implementation:

1. Get handoff notes from the agent
2. Spawn a new TDD agent with:
   - Original requirements
   - **Completed criteria** (list only, NOT implementation details)
   - Remaining tasks
   - Current test status
   - **DO NOT pass implementation code** - the new agent should read files fresh

### Bug-Fix Loop Limit

If ui-qa keeps finding bugs after 3 bug-fix cycles:

1. Stop the loop
2. File remaining bugs as issues
3. Return PARTIAL status with details

### Unrecoverable Failures

If any sub-agent fails in a way that can't be retried:

1. Document the failure
2. Return FAILED status
3. Include all context for human review

## Integration with iterate

**Division of responsibilities:**
- **implement**: Commits changes, returns structured report
- **iterate**: Invokes `finalize-and-push` (quality gates, docs, push, PR), then handles labels

When called from `iterate`:

```python
# iterate skill pseudo-code
issue = find_and_claim_next_issue()
branch = create_branch(f"vera/{issue.number}-{brief_desc}")
result = invoke_skill("implement", issue.acceptance_criteria)
# implement returns report with status (SUCCESS/PARTIAL/FAILED)
# implement has committed changes but NOT pushed

if result.status == "SUCCESS":
    invoke_skill("finalize-and-push")  # iterate Step 6: precommit, docs, push, PR
    post_comment(issue, result.report)  # iterate posts the report
    mark_needs_testing(issue)  # iterate updates labels
    # Issue stays OPEN - project-manager verifies PR and merges
elif result.status == "PARTIAL":
    post_comment(issue, result.report)
    mark_needs_work(issue)
    release_claim(issue)
else:  # FAILED
    post_comment(issue, result.report)
    mark_question(issue)
    release_claim(issue)
```

## Standalone Usage

Can be invoked directly:

```
/implement

Add a dark mode toggle to the settings page.

Acceptance criteria:
- Toggle switch in settings UI
- Persists preference to user profile
- Applies theme immediately without reload
- Works with existing color variables
```

The skill will orchestrate TDD → Review → UI-breaker automatically.
