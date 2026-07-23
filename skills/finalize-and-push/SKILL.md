# Finalize and Push

One-stop checklist for wrapping up work: quality gates, knowledge capture, documentation,
and PR creation. Works for both human-invoked and autonomous agent workflows.

**Announce at start:** "Using finalize-and-push to wrap up this work."

## Checklist

Steps 1–4 are independent and should run **in parallel** (e.g., via concurrent Agent
tool calls or parallel tool invocations). Steps 5–10 are sequential and run after
Steps 1–4 complete. Create a TodoWrite entry for each step.

### Steps 1–4: Run in Parallel

These four steps have no dependencies on each other. Launch them concurrently to
save time, then wait for all to finish before proceeding to Step 5.

#### Step 1: Memorizer Reflection

Review the work done this session. Ask yourself:

- Did I discover debugging insights or pitfalls not in CLAUDE.md or skills?
- Did I find conventions or patterns worth preserving?
- Did I make architectural decisions a future agent should know about?

If yes: search memorizer first (no duplicates), then store or update entries.
If nothing worth remembering: skip. This is a judgment call, not a mechanical step.

#### Step 2: AGENT-NOTE Audit

```bash
git diff main...HEAD --name-only
```

For each changed file, ask: *"Would an agent reading only this file make the wrong choice?"*

- If yes: add `AGENT-NOTE:` comments (self-contained, <=3 lines, "Use X not Y" style per CLAUDE.md).
- If no non-obvious decisions exist: skip.

#### Step 3: Targeted Docs Update

Diff-driven — only update what the changes affect:

1. Check `git diff main...HEAD` for user-facing changes
2. Update `README.md` and any relevant documentation files: remove `🚧` for completed features, add missing features
3. Update affected `README.md` sections if commands/structure changed
4. Follow documentation skill formatting: user perspective, `**Done when:**` criteria, no implementation details

If nothing user-facing changed, skip.

#### Step 4: Leftover Work

Scan for incomplete work:

```bash
# New TODOs in the diff
git diff main...HEAD | grep '^\+.*\(TODO\|FIXME\|HACK\|XXX\)' || true
```

Also check: unfinished acceptance criteria from the claimed issue, known incomplete work.

**Mode detection:**
- **Interactive** (human invoked `/finalize-and-push`): flag and suggest — list leftovers,
  recommend creating issues, don't block the push.
- **Autonomous** (called from iterate/implement): prefer completing the work. Only create
  issues as a last resort for genuinely out-of-scope items.

### Steps 5–9: Run Sequentially (after Steps 1–4 complete)

### Step 5: Quality Gate

#### 5a. Post-merge sanity (skip if no merge commit on this branch)

If `git log HEAD --merges -1 --since=1.day` returns a commit, run:
<!-- Editor note: this check is Layer 1 defense for failure class `merge-conflict-loses-feature`
     (docs/failures/SUMMARY.md:101, #2104/#2108). The heavyweight semantic check is in
     address-review-feedback Step 0.1. Do not soften "Stop. Do not push." -->

```bash
BASE=$(git merge-base origin/main HEAD)
FILES=$(git diff --name-only "$BASE" HEAD)
git diff --shortstat origin/main HEAD -- $FILES
```

0/0 means your branch contributes nothing vs main — the merge dropped your fix.
**Stop. Do not push.** See address-review-feedback Step 0.1 for the heavier
semantic check, and #2104 for the failure class `merge-conflict-loses-feature`.

#### 5b. Precommit

```bash
mkdir -p tmp && just precommit 2>&1 | tee tmp/precommit.log | tail -20
```

Do NOT run any background Bash tasks, sub-agents, or other test processes
concurrently with this step. `just precommit` fans out 5 parallel test tiers,
each spawning N pytest workers auto-calibrated from the machine's RAM.

**Hard gate** — if it fails, stop and fix. No proceeding with red tests or lint errors.
This runs after Steps 1–4 so that any changes from memorizer reflection, AGENT-NOTEs,
spec/docs updates, or leftover work fixes are validated before committing.

#### 5c. Record pre-commit and test-suite evidence in the implement callback

When this skill is running inside an **implement callback** (i.e., the agent
will POST to `/internal/jobs/callback` after pushing), the callback body's
`outcome` block must include a freeform `summary`, plus a `pre_commit` block
and a `test_suite` block. The `pre_commit` / `test_suite` blocks are derived
from the single Step 5b `just precommit` run:


```json
{
  "job_id": "...",
  "token": "...",
  "status": "completed",
  "outcome": {
    "status": "completed",
    "summary": "implemented the feature; just precommit green; pushed PR",
    "pre_commit": {
      "ran": true,
      "passed": true,
      "log_tail": "<tail of tmp/precommit.log>"
    },

    "test_suite": {
      "passed": true,
      "command": "just precommit",
      "summary": "<tail summary line from tmp/precommit.log>"
    }
  }
}
```

The top-level `outcome.summary` is **required** -- it is a one-line,
human-readable description of what happened, rendered verbatim into the PR
status comment. Never omit it; an outcome missing `summary` is rejected as a
failure (issue #3087).

`just precommit` is the canonical "full test suite" command — it runs
lint + format + type check + tests. It is the single source of truth for
both subdicts:

- **`pre_commit`** — set `ran` to `true` (you ran it), `passed` to whether
  `just precommit` exited 0, and `log_tail` to a plain-string tail of
  `tmp/precommit.log`. **`pre_commit.passed` is the server-side routing gate**
  (`_write_pre_commit_log` in hooks/implement.py, satisfying spec slug
  `ticket-lifecycle.tdd-implementation.pre-commit-hooks-run-pass-implementation`):
  if it is missing or false, the server routes the job to `_handle_implement_failure`
  and reports "agent did not run pre-commit" — no PR is created. You MUST emit
  `passed`, not just `ran` and `log_tail`.
- **`test_suite`** — capture the final summary line of `tmp/precommit.log` as
  `summary` (server truncates to ~500 chars). Satisfies spec slug
  `ticket-lifecycle.tdd-implementation.full-test-suite-runs-passes-pr-created`.
  Under strict enforcement (`VERA_IMPLEMENT_REQUIRE_TEST_SUITE=true`, #2930/#2381)
  a missing or false `test_suite` also blocks PR creation: the `vera:in-qa`
  label is not applied and the credit reservation is released.


### Step 6: Commit

Stage **all** changes — both your work from Steps 1-4 and any files reformatted by
`just precommit` in Step 5. Linter/formatter changes are part of the PR and should not
be discarded or left uncommitted.

```bash
git add -A
```

Use `commit-assistant` skill for message formatting.

If nothing changed in Steps 2-5 (including no linter reformats), skip.

### Step 7: Issue Tracking

Ensure there is an open GitHub issue tracking this work before creating a PR.

```bash
# Check for an existing in-progress issue linked to this branch/work
gh issue list --label "in-progress" --state open --json number,title | head -20
```

If no issue exists for this work, create one now with the `in-progress` label.
Always pass `--repo "$REPO"` — without it, `gh` defaults to the cwd remote
(jasonsurratt/vera) and silently mis-targets customer issues (incident #1042):

```bash
gh issue create --repo "$REPO" \
  --title "<concise description of the work>" \
  --label "in-progress" \
  --body "Tracking issue for: <brief summary of what was done>"
```

If an issue already exists (was claimed before starting), skip creation.

### Step 9: Push + PR Creation

**Never push directly to main/master.** If on a protected branch, create a feature branch first.

```bash
# Check if PR already exists
existing_pr=$(gh pr list --head "$(git branch --show-current)" --json number --jq '.[0].number // empty')
```

**If PR exists:** push only.

```bash
git push
```

**Duplicate-PR guard (issue #2915).** If the job payload carried an
`existing_pr` (a retry against a pre-existing Vera PR) AND the push to the
canonical branch is rejected — non-fast-forward, "unrelated history", or any
other rejection — **do NOT fall through to `gh pr create`**. Opening a second
PR for the same issue is forbidden. Instead emit a failed/needs_input outcome
to `${TMPDIR:-/tmp}/vera_outcome.json` and stop:

```bash
EXISTING_PR="<existing_pr from job payload; empty if absent>"
if ! git push 2>push.err; then
  if [ -n "$EXISTING_PR" ]; then
    cat > "${TMPDIR:-/tmp}/vera_outcome.json" <<EOF
{"status": "needs_input", "question": "Could not push to the canonical branch for PR #${EXISTING_PR}: local history is unrelated to the existing branch. A maintainer must rebase or reset the branch. Not opening a second PR — see #${EXISTING_PR}."}
EOF
    echo "::error::push to canonical branch rejected; existing PR #${EXISTING_PR} — stopping (no duplicate PR)"
    exit 1
  fi
  cat push.err
  exit 1
fi
```

**If no PR:** push and create.

**These two lines are spec-required and must appear verbatim in the PR body: `Closes #<issue-number>` (not `Fixes #`) and the trailing footer `🤖 Generated with <model> <model version>`.** These satisfy spec slugs `github-app.pr-creation.pr-body-references-originating-issue-closes-n` and `ticket-lifecycle.comment-formatting-rules.comment-includes-standard-footer`. Do not drop or reword them.

```bash
git push -u origin "$(git branch --show-current)"

# Always pass --repo "$REPO" — see Step 7 note on incident #1042.
gh pr create --repo "$REPO" --title "<concise title>" --body "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2>

## Test Plan
- [ ] <verification step>

Closes #<issue-number>

---
🤖 Generated with <model> <model version>
EOF
)"
```

**After PR creation (or if PR already exists), assign it to the issue's assignee:**

```bash
# If working on an issue, copy its assignee to the PR
ISSUE_NUMBER=<linked-issue-number>
PR_NUMBER=<pr-number>
ASSIGNEE=$(gh issue view "$ISSUE_NUMBER" --json assignees --jq '.assignees[0].login // empty')
if [ -n "$ASSIGNEE" ]; then
  gh pr edit "$PR_NUMBER" --add-assignee "$ASSIGNEE"
fi
```

This ensures the correct OAuth token is used by downstream CI workflows (review, address-feedback).

Report the PR URL when done.

### Step 10: Return to Main (VSCode only)

If running inside VSCode (check `$TERM_PROGRAM` or `$VSCODE_CWD`):

```bash
git checkout main && git pull
```

This keeps the IDE's branch indicator clean after the feature branch is pushed. Skip in headless/terminal-only environments.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping precommit because "it passed earlier" | Run it fresh in Step 5 — Steps 1-4 may have changed files |
| Memorizer spam | Search before storing; skip if nothing novel |
| AGENT-NOTEs for obvious things | Only add when an agent would make the wrong choice |
| Full docs sync when only backend changed | Targeted updates only — check the diff |
| Creating issues for work you could just finish | Complete the work first; issues are last resort |
| Discarding linter changes from precommit | Commit all files modified by `just precommit` — they belong in the PR |
| Force-pushing without asking | Never force-push; always confirm with user first |
| Committing/pushing on main | Always create a feature branch first — use the branch guard check |
| Staying on feature branch after PR (VSCode) | Run Step 10 to return to main so the IDE branch indicator stays clean |
