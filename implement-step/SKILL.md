---
name: implement-step
description: Execute the next implementation step of a task from .agent/ state — claim it, journal intent before coding, follow the design exactly, and exit in a clean state. Use when the user says "implement", "code it", "do step N", "continue implementation", or when next-task routes to a task at stage "implementing". Runs one step per session by default; the design doc and backlog are the only authority, not chat memory.
---

# Implement One Step

You are one of several disposable sessions executing a plan that lives on disk. Everything you know that isn't written down dies with this session — so write things down at the moments specified below, and change the plan only through recorded edits.

## State layout

Task folder: `.agent/tasks/<slug>/`. Read `.agent/index.md`, `04-backlog.md`, `05-journal.md`, `03-design.md`. This skill writes: code, `04-backlog.md` (status), `05-journal.md`, and — only for structural deviations — `03-design.md`. Backlog status values: `todo` | `in_progress (owner, since)` | `blocked (reason)` | `done`.

## Step 1 — Orient (in this order, nothing more)

0. If `.agent/scripts/agent_state.py` exists, run `python3 .agent/scripts/agent_state.py next` — it deterministically identifies the next eligible step, in-flight work, and stale sessions. Cross-check its answer with the reads below rather than replacing them.
1. `.agent/index.md` → active task and stage.
2. `04-backlog.md` → first step `in_progress` owned by this effort, else the next `todo` whose dependencies are all `done`.
3. `05-journal.md` tail (last ~10 entries) → what the previous session did, deviations, open blockers.
4. `03-design.md` → only the sections relevant to this step.
5. The files the step lists — and only those, plus whatever they force you to read. The design enumerated files precisely so you don't have to search.

If the chosen step is already `in_progress` with a recent timestamp from another owner, do not take it — surface it to the user (parallel sessions may be running).

## Step 2 — Claim with a write-ahead journal entry

Before touching any code:

1. Set the step's status: `in_progress (<owner>, since <ISO timestamp>)`.
2. Append to `05-journal.md`:

```markdown
## <ISO timestamp> — step N start: <title>
Intent: <files to touch, in what order, and the expected shape of the change>
Risks: <anything that might go wrong>
```

Why first: if this session dies mid-step, the next session reconstructs the exact position from this entry plus `git diff` — no guessing, no re-reading the whole codebase.

## Step 3 — Implement, with the deviation rules

Follow the design and the step's `what` exactly. When reality disagrees with the plan:

- **Small deviation** (contained within this step): make it, and record it in the journal entry for the step's completion.
- **Structural deviation** (invalidates a design claim or affects future steps): **stop coding.** Update `03-design.md` and every affected backlog step first, append a journal entry explaining what changed and why, then resume. The plan is mutable — but only through recorded edits, because future sessions read the plan, not this chat.

## Step 4 — Self-review before closing

Adversarial pass on your own diff: assume the code is of poor quality and tear it to shreds — naming, error handling, edge cases, readability (flag any ~10 lines without a comment where intent isn't obvious). Fix what you find. Then run the step's `done_when` checks and make them pass.

## Step 5 — Exit in one of exactly two states

**Done:**
1. Status → `done`; update the backlog's `Progress:` line. Run `python3 .agent/scripts/agent_state.py validate` and fix any errors it reports — never commit inconsistent state.
2. Journal entry: what changed, any small deviations, surprises worth knowing.
3. Update the index row's next action (next step, or "review" if this was the last).
4. Commit, message referencing task and step (e.g. `feat(<slug>): step 4 — token rotation`).

**Blocked:**
1. Status → `blocked (<reason>)`; nothing left half-applied — revert or stash uncommitted fragments.
2. Journal the blocker with enough detail that resolving it needs no archaeology.
3. Update the index row: flag `blocked`, next action = what would unblock it.

Never end silently mid-step — those are the only two legal exits.

Then stop. Recommend a fresh session for the next step: per-step context isolation is the point of this whole structure. If all steps are `done`, set the index stage to `reviewing` and point the user at the `review-work` skill.
