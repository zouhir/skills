---
name: review-work
description: Adversarial review of completed work against its acceptance criteria and design, using fresh-context critics looped until only nitpicks remain. Use when a task reaches stage "reviewing" in .agent/index.md, when the user says "review this", "is this ready to merge", "tear this apart", or before shipping any task tracked in .agent/. Records every round in 06-verification.md and gates the task's transition to done.
---

# Review the Work

The session that wrote the code cannot review it neutrally — it shares the same blind spots that produced the bugs. Reviews therefore run in fresh contexts: spawn subagents (Task tool) that receive only file paths, or run this skill itself in a new session that did no implementation.

## State layout

Task folder: `.agent/tasks/<slug>/` — read `02-criteria.md`, `03-design.md`, `04-backlog.md`, and the diff (`git diff <base>...` or the files listed in the design). This skill writes `06-verification.md`, `05-journal.md`, and updates `.agent/index.md`.

## The three passes

**Pass 1 — Criteria audit.** For every criterion in `02-criteria.md`: pass or fail, with concrete evidence (command output, observed behavior, file/line). A criterion without evidence is a fail. This is the contract the work was commissioned against — it outranks taste.

**Pass 2 — Mean code review.** Fresh-context critic with this stance: "I have a strong intuition that this code is of poor quality. Tear it to shreds: correctness, edge cases, error handling, security, performance, and readability — flag any long stretch of non-obvious code without a comment." The pessimistic framing matters; a neutral reviewer rubber-stamps.

**Pass 3 — Design conformance.** Compare the implementation against `03-design.md` §4 and the backlog's per-step `what`. Files changed that the design never mentions, or design claims the code contradicts, are findings — each one either gets fixed in code or recorded in the design (see implement-step's deviation rules). Undocumented drift is how docs rot into fiction.

## Classify, adjudicate, loop — bounded

Require the critic to classify every finding, anchored to the artifacts, and to skip anything already adjudicated in `06-verification.md`: **MUST-FIX** — violates an acceptance criterion (name it) or is a correctness/security defect; **SHOULD-FIX** — a maintainer or implementer would be misled without it; **NITPICK** — preference. A finding with no named criterion or concrete consequence is a NITPICK by definition.

Then adjudicate yourself: fix MUST-FIX and worthwhile SHOULD-FIX items (fixes follow implement-step discipline: journal entries, recorded deviations); reject the rest **with a written rationale in the verification log** so the next fresh critic cannot re-raise them. A fresh critic will always find *something* — absorbing every finding is churn, not convergence.

Stop condition: a round produces **no new MUST-FIX or SHOULD-FIX findings**. Budget: **3 rounds**. If round 3 still surfaces new must-fixes, stop looping — that signals a design-level problem or genuinely unstable code; escalate to the human with the open findings and your read on the root cause.

Record every round, including rejections:

```markdown
## <date> — review round 2
Criteria: 7/8 pass (criterion 5: no benchmark evidence yet)
Findings: 1 MUST-FIX (unhandled 401 path), 2 SHOULD-FIX, 3 NITPICK
Adjudication: fixed 401 path in middleware.ts; rejected S2 (duplicate of
Alternatives §3 decision); S1 deferred to backlog as new step
```

## Close out

1. Summarize for the user: criteria results, rounds taken, residual nitpicks. Ask for human sign-off — a human, not this skill, owns the ship decision.
2. On sign-off: index row → stage `done`, next action "—"; journal entry closing the task.
3. If sign-off is refused, journal why and route back to `implement-step` (new backlog steps) or `write-design` (structural rework).
