---
name: build-backlog
description: Decompose an approved design doc into session-sized implementation steps in the task's 04-backlog.md under .agent/tasks/. Use when a task reaches stage "ready-for-backlog" in .agent/index.md, or the user says "build the backlog", "break this down", "plan the steps", "split this into tasks". Each step must be completable by a single fresh agent session, with explicit files, dependencies, and done-criteria — this is what enables one-chat-per-subtask execution.
---

# Build the Backlog

Each step you write here will be executed by a **fresh agent with no memory** of this conversation. A step that is too big dies mid-context and leaves a mess; a step that is vague forces the executor to guess. Size and specify accordingly.

## State layout

Task folder: `.agent/tasks/<slug>/` — read `03-design.md` (must have passed its gates; check `06-verification.md`). This skill writes `04-backlog.md` and updates `.agent/index.md`. Stages: `researching → designing → ready-for-backlog → implementing → reviewing → done`.

## Sizing rules

- One coherent change per step — describable in 2–4 lines.
- Roughly ≤5 files touched. More than that, split it.
- If you cannot state a step's done-criteria in two verifiable lines, the step is not understood yet — go back to the design.
- Prefer steps that leave the system working (tests green) at their boundary, so any step is a safe stopping point.

## Coverage and dependency rules

- **Coverage:** every file listed in design §4 (Detailed implementation) must appear in at least one step. Check this explicitly before finishing — an uncovered file is a silent gap.
- **Dependencies:** make them explicit per step. Steps with no shared files and no dependency edge may run in parallel sessions; note that where true.

## 04-backlog.md format

```markdown
# Backlog: <title>
Design: 03-design.md (as of YYYY-MM-DD)
Progress: 0/N done

## Step 1: <imperative title>
- status: todo
- depends_on: —
- files: src/auth/middleware.ts, src/auth/middleware.test.ts
- what: <2–4 lines; reference the design section it implements>
- done_when: <verifiable criteria; include the command to run if any>

## Step 2: ...
```

Status values (used by all skills): `todo` | `in_progress (owner, since <ISO timestamp>)` | `blocked (reason)` | `done`.

## Close out

1. Walk the user through the steps and dependency order; adjust on feedback.
2. Run `python3 .agent/scripts/agent_state.py validate` — it catches malformed statuses, dangling dependencies, and stage/backlog mismatches deterministically. Fix any errors before proceeding (if the script is missing, verify the same points by reading the files).
3. Update the index row: stage `implementing`, next action "step 1: <title>".
4. Append a journal entry to `05-journal.md`: step count, expected parallelism, any sequencing risks.
5. Tell the user each step can now run via "work on next task" in a fresh session (`next-task` → `implement-step`).
