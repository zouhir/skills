---
name: next-task
description: Continuation dispatcher — determines where work stands from .agent/ state and routes to the correct lifecycle skill. Use whenever the user says "work on next task", "continue", "resume", "keep going", "pick up where we left off", "what should we do next", or opens a session in a repo containing .agent/ with a continuation intent. This is the default entry point for resumed work; prefer it over guessing from chat history, which fresh sessions don't have.
---

# Next Task (Dispatcher)

"Continue" does not always mean "write code" — the right next action depends on the stage where work last stopped. Your job: orient from three small files, route to the right skill, then follow that skill fully. Never reconstruct state by reading source code when the state files can tell you directly.

## Step 1 — Orient (three reads, ~1 minute)

0. If `.agent/scripts/agent_state.py` exists, run `python3 .agent/scripts/agent_state.py status` then `... next` — deterministic orientation in two commands. Still skim the journal tail yourself; the script reads structure, not narrative.
1. `.agent/index.md` → the `Active:` task and its stage.
2. That task's `04-backlog.md` (if it exists) → step statuses.
3. That task's `05-journal.md` tail → what the last session did or intended.

If `.agent/` doesn't exist: offer `research-task` (starting new work) or `bootstrap-context` (adopting an existing codebase). If multiple tasks are active or the `Active:` pointer is ambiguous, ask the user which — one question, then proceed.

## Step 2 — Route by stage

| Stage in index | Route to | Notes |
|---|---|---|
| researching | `research-task` | resume the interrogation from 01-problem.md's open questions |
| designing | `write-design` | resume at the doc section or gate recorded in 06-verification.md |
| ready-for-backlog | `build-backlog` | |
| implementing | `implement-step` | at the exact step (see below) |
| reviewing | `review-work` | |
| blocked (flag) | — | surface the journaled blocker to the user; do not guess around it |
| done (all tasks) | — | report it; offer the next task in the index or `research-task` |

## Step 3 — The mid-step death case

If the backlog shows a step `in_progress` with a stale owner (dead session):

1. Read that step's start entry in the journal — it recorded intent: files, order, expected shape.
2. Run `git diff` (and `git status`) to see how far the change actually got.
3. Reconcile: either continue from where it stopped, or revert the fragment and restart the step cleanly. Tell the user which you chose and why before proceeding.

This works because `implement-step` journals intent *before* coding — trust that entry over inference from raw code.

If the step is `in_progress` with a **recent** timestamp, another session may be live. Don't steal it; pick the next unblocked parallel-safe step or ask the user.

## Step 4 — Execute

Invoke the routed skill and follow it completely. You are a dispatcher, not a bypass — the discipline (write-ahead journaling, deviation rules, exit states) lives in the target skills.
