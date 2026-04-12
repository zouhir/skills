---
name: session-log
description: Track project tasks across Claude Code sessions. Use whenever the user says "next task", "continue", "where were we", "what's next", or asks you to start/resume implementation work on a project that has a TODO.md or PROGRESS.md file. Reads the task list and progress log to know exactly what to work on, then logs what was done after completing each task so the next session can pick up seamlessly.
---

# Session Log

A two-file convention for stateful, multi-session work:

- **`TODO.md`** — owned by the user. An ordered list of tasks as `- [ ]` checkboxes. You only ever check items off; you never reorder, rewrite, or invent new ones unless the user explicitly asks.
- **`PROGRESS.md`** — owned by you. Append-only log of completed tasks with context.

Both live at the repo root unless the user has placed them elsewhere (check `.claude/`, `docs/`, or root).

## When the user says "next task" (or equivalent)

Do this in order. Do not skip steps.

1. **Locate the files.** Look for `TODO.md` and `PROGRESS.md` at repo root first, then `.claude/`, then `docs/`. If `TODO.md` is missing, stop and ask the user where it is or whether to create one. If `PROGRESS.md` is missing, you'll create it on the first log write.

2. **Read `PROGRESS.md`** (if it exists) — specifically the last 1–3 entries. This tells you what was just done, what files were touched, and any blockers or notes the previous session left for you. If the last entry has a "Next up" line that names a specific task, that takes precedence over the TODO order — the previous session may have left you a hand-off.

3. **Read `TODO.md`** and find the first unchecked `- [ ]` item (or the one named in the hand-off). That is the task.

4. **State the task back to the user in one sentence** before starting work, so they can redirect if you picked wrong. Example: "Picking up: *Add rate limiting to the /login endpoint*. Starting now." Do not ask for confirmation — just state and proceed. The user will interrupt if it's wrong.

5. **Do the work.** Follow normal project conventions (CLAUDE.md, scoped context, etc.).

6. **When done, log it.** See the logging format below. Then check the box in `TODO.md`.

## Logging format

Append to `PROGRESS.md`. One entry per completed task. Use this exact structure so future sessions can parse it reliably:

```markdown
## YYYY-MM-DD HH:MM — <task title, copied from TODO.md>

**Done:** One or two sentences describing what was actually built/changed. Concrete, not aspirational.

**Files:** `path/one.ts`, `path/two.ts`, `path/three.md`

**Decisions:** Any non-obvious choice made during implementation that a future session would need to know. Skip this section if there were none — don't pad.

**Blockers:** Anything that's incomplete, broken, or waiting on the user. Skip if none.

**Next up:** If the work naturally leads to a specific follow-up that isn't already in TODO.md, name it here and tell the user to add it. If the next TODO item is the obvious continuation, just write "next TODO item".

---
```

Rules for entries:
- **Be concrete.** "Added JWT validation middleware in `auth/middleware.ts` that rejects expired tokens with 401" beats "improved auth".
- **No marketing language.** No "successfully", "robust", "comprehensive". Just what happened.
- **One entry per task**, not per file or per commit. If you did three small things for one TODO item, that's one entry.
- **Always include the timestamp** in the heading. Use the actual current date/time.
- **Append to the bottom** of the file, never the top. Chronological order, oldest first.

## Checking off TODO.md

After logging, edit `TODO.md` to change `- [ ]` to `- [x]` for the task you just finished. Do not delete the line. Do not reorder anything else. Do not touch other unchecked items.

## What you do NOT do

- Do not invent tasks. If `TODO.md` is empty or all checked, tell the user and ask what's next — don't guess.
- Do not reorder `TODO.md`. The user controls priority.
- Do not edit or rewrite past `PROGRESS.md` entries. It's an append-only log. If you made a mistake in a prior entry, add a correction in the new entry instead.
- Do not skip the logging step because the task was small. Every completed task gets an entry — that's the whole point.
- Do not write `PROGRESS.md` entries for work the user did manually or for partial/abandoned attempts. Only completed tasks from `TODO.md`.

## Bootstrapping a new project

If the user invokes this skill on a project with neither file, offer to create both:

- A `TODO.md` with a brief header explaining the format and one example unchecked item.
- A `PROGRESS.md` with just a header — no entries yet.

Then ask the user to fill in `TODO.md` before the first "next task" call.
