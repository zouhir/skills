---
name: task-status
description: Read-only progress report over .agent/ state — what's done, in flight, blocked, drifting from plan, and what's left. Use when the user asks "where are we", "status", "what's left", "what's missing", "progress report", or to orient at the start of a session without acting. Safe to run at any time; it never mutates state, only flags problems for the workflow skills to repair.
---

# Task Status

Answer "where are we?" from disk alone, and be trustworthy precisely because you change nothing. When state disagrees with itself, report the disagreement — repairing it belongs to `next-task` and `implement-step`.

## What to read

0. If `.agent/scripts/agent_state.py` exists, run `python3 .agent/scripts/agent_state.py validate` and `... status` first — its errors and warnings are your drift flags, mechanically derived. The manual heuristics below cover what the script can't see.
1. `.agent/index.md` — the registry.
2. For each non-done task: `04-backlog.md` and the tail of `05-journal.md`.
3. Optionally `git log --oneline` since the last journal timestamp, to catch work that happened outside the workflow.

## Report format

```markdown
# Status — <date>

## <slug> — implementing (4/9 done)
- current: step 5 "token rotation" — in_progress (zouhir, 2h ago)
- blocked: none
- next: step 5 finish → steps 6,7 can run in parallel
- risk: <anything from journal tail worth surfacing>

## What's left (all tasks)
<one line per remaining step/stage across tasks>

## Drift flags
<see below — empty if clean>
```

## Drift checks (cheap heuristics, run all)

- Index row disagrees with the backlog (stage says `implementing`, backlog has no `in_progress`/remaining `todo`, or vice versa).
- A step marked `done` whose listed files don't exist or don't contain the described change (spot-check, don't deep-audit).
- An `in_progress` step older than ~24h — likely a dead session; recommend `next-task` to reconstruct from the journal's intent entry + `git diff`.
- Journal entries newer than the index's `updated` date — the index is stale.
- Commits in `git log` with no corresponding journal entry — work happened off-process.
- Backlog header references a design date older than `03-design.md`'s last modification — steps may predate a design change.

Flag each with a one-line recommended repair, but do not perform it.

## Tone

Compact and factual. This report is the first thing a returning human (or agent) reads — its job is orientation in under a minute, not narrative.
