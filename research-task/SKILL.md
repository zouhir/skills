---
name: research-task
description: Start any new task, feature, or piece of non-trivial work with a structured interrogation before designing or coding. Use whenever the user wants to begin something new — "new feature", "new task", "let's build X", "I want to add Y", "research this problem" — even if they never say "research". Produces a problem spec (01-problem.md) and acceptance criteria (02-criteria.md) in a per-task folder under .agent/tasks/ and registers the task in .agent/index.md. Do not jump straight to design or code for non-trivial work; run this first.
---

# Research a Task

The quality of everything downstream — design, backlog, code — is gated by the quality of the problem description. Your job in this skill is to **interrogate, not to answer**. You are the questioner; the user holds the domain judgment.

## State layout (shared by all workflow skills)

```
.agent/
  index.md                  # task registry: one row per task (stage, next action)
  tasks/<slug>/
    01-problem.md           # problem spec          ← this skill writes
    02-criteria.md          # acceptance criteria   ← this skill writes
    03-design.md            # design doc            (write-design)
    04-backlog.md           # implementation steps  (build-backlog)
    05-journal.md           # append-only log       (all skills append)
    06-verification.md      # gate/review results   (write-design, review-work)
```

Stages: `researching → designing → ready-for-backlog → implementing → reviewing → done` (any stage may carry a `blocked` flag).

## Step 0 — Register the task

1. Derive a short kebab-case slug from the task name.
2. Create `.agent/tasks/<slug>/` and an empty `05-journal.md`.
3. Create `.agent/index.md` if missing, then add a row:

```markdown
# Task Index
Active: <slug>

| task   | stage       | next action            | updated    |
|--------|-------------|------------------------|------------|
| <slug> | researching | complete interrogation | YYYY-MM-DD |
```

4. Append a journal entry: `## <ISO timestamp> — task created`.
5. Ensure `.agent/scripts/agent_state.py` exists — if missing, copy it from this skill's `scripts/agent_state.py`. It's the read-only validator/accessor (`validate` / `next` / `status`) the other workflow skills use for deterministic state checks; committing it keeps those checks available to every future session.

## Step 1 — The interrogation (no code, no solutions)

Do not propose solutions, architectures, or code in this phase — premature solutions narrow the problem before it is understood. Instead:

- Ask clarifying questions in small batches (3–5 at a time), then wait.
- Challenge assumptions rather than accepting statements at face value. Probe the edges: scale, users, failure modes, security/privacy, constraints, deadlines, and especially **non-goals**.
- When the user states something that contradicts the codebase or earlier answers, say so and ask which is true.
- Continue until the user says "done" or your questions have degraded into nitpicks.

Sycophancy check: if you notice yourself agreeing and praising ("great point!"), stop — you are most helpful when you challenge the user's thinking and force them to examine the edges of the problem, not when you agree.

## Step 2 — Write the problem spec

Write `01-problem.md` from the interrogation. Keep it plain-English; a reader with no context should understand what is being attempted and why.

```markdown
# Problem: <title>

## What and why
<3–8 sentences: the business/user problem, who it affects, why now>

## Context
<relevant facts about the current system, links to files/docs>

## Constraints
<hard limits: perf, compat, security, deadline>

## Non-goals
<explicitly out of scope — these prevent future scope drift>

## Open questions
<anything unresolved, with owner>
```

## Step 3 — The acceptance-criteria interview

Switch roles: you are now a skeptical acceptance tester. The work will eventually be judged by someone who never saw this conversation, so the criteria must stand alone. Interview the user again, focused only on: *how will we know the outcome is correct and complete?*

Push for criteria that are **verifiable** — a command to run, an observable behavior, a measurable threshold. "Works well" is not a criterion; "p95 latency under 200ms on the /search endpoint" is.

Write `02-criteria.md`:

```markdown
# Acceptance criteria: <title>

1. <criterion — verifiable, with the check to perform>
2. ...

## Evidence required
<what artifacts prove the criteria: test output, screenshots, benchmark numbers>
```

## Step 4 — Close out

1. Update the index row: stage `designing`, next action "write design doc".
2. Append a journal entry summarizing what was decided and what remains open.
3. Tell the user the next step is the `write-design` skill — and that it can run in a fresh session, since everything needed is now on disk.
