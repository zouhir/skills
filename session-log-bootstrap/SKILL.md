---
name: session-log-bootstrap
description: Set up TODO.md and PROGRESS.md for a project from scratch by interviewing the user and inspecting the codebase. Use when the user says "set up session log", "bootstrap the task list", "initialize session-log", "populate TODO from PRD", "help me plan tasks for this project", or invokes session-log on a project that has neither file yet. Reads any existing PRDs, architecture docs, README, and CLAUDE.md to propose a starting task list, then refines it through a short interview before writing the files.
---

# Session Log Bootstrap

One-time setup helper. Populates `TODO.md` (and creates an empty `PROGRESS.md`) for a project that doesn't have them yet, or augments an existing `TODO.md` with tasks derived from PRDs.

## When to run

- New project with no `TODO.md` / `PROGRESS.md`.
- Existing project, but the user just wrote a new PRD and wants tasks generated from it.
- User explicitly asks to "plan tasks" or "break down" a feature/document.

## The flow

Do these in order. Be brisk — the user wants a working task list, not a discovery workshop.

### 1. Inventory what already exists

Before asking the user anything, look at what the project tells you:

- Read `CLAUDE.md` (root and any nested ones) if present.
- Read `README.md` if present.
- Glob for likely PRD/architecture docs: `docs/**/*.md`, `docs/prd/**/*.md`, `docs/specs/**/*.md`, `docs/adr/**/*.md`, `*.md` at root. Read the ones that look like product or architecture docs (skip changelogs, license, contributing).
- Note the stack (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.) so proposed tasks use the right language/framework.
- Check if `TODO.md` already exists. If it does, you're augmenting, not replacing — read its current contents and treat existing items as fixed.

Summarize what you found in 3–5 bullets to the user before going further. Example: "I see a Go Web Service + Postgres project with a PRD for the auth flow at `docs/prd/auth.md`, no existing TODO.md, and a CLAUDE.md mentioning you use Firebase Auth. Going to plan tasks against the auth PRD — sound right?"

### 2. Short interview (only what you actually need)

Ask at most **three** questions, and only the ones the inventory didn't already answer. Skip any question whose answer is obvious from the docs. Candidates, in priority order:

- **Scope:** "Are we planning the whole project, or just <specific PRD/feature>?"
- **Starting point:** "Is the codebase empty, partially built, or already running? Any areas I should treat as done?"
- **Granularity:** "Do you want tasks sized for ~1 hour of work each, or larger half-day chunks?" (Default to ~1 hour if they don't care.)

Do NOT ask about: tech stack (read it), conventions (read CLAUDE.md), priorities for individual tasks (you'll propose an order and let them edit). Asking these wastes their time.

### 3. Draft the task list

Based on the docs + interview, draft an ordered list of tasks. Rules:

- **Each task is a single, verifiable outcome.** "Add `/login` endpoint that accepts email+password and returns a JWT" — not "implement auth".
- **Order by dependency, then priority.** Foundations first (schema, scaffolding), then features that depend on them, then polish.
- **Aim for the granularity the user specified.** If a task feels bigger than that, split it.
- **Don't pad.** No "set up the project" if the project is already set up. No "write tests" as a separate generic task — fold testing into each feature task or add specific test tasks for specific things.
- **Mark uncertainty.** If you're guessing at a task because the PRD is vague, prefix it with `(?)` so the user knows to review it. Example: `- [ ] (?) Add password reset flow — PRD doesn't specify the email provider`.

Show the draft to the user **in the chat first**, not by writing the file. They'll want to edit, reorder, or cut things before it lands on disk.

### 4. Refine, then write

After the user gives feedback (or says "looks good"):

- Write `TODO.md` using the template structure: brief header, then the task list.
- Create `PROGRESS.md` with just the header and an empty entries section. No fake first entry.
- Tell the user the files are written and that they can now say "next task" to start.

If `TODO.md` already existed, **append** new tasks to the end rather than rewriting the file. Never reorder or delete existing items during bootstrap — that's the user's call.

## What you do NOT do

- Do not write `TODO.md` without showing the draft first. The interview is cheap; a wrong file the user has to clean up is expensive.
- Do not invent features that aren't in the PRDs or that the user didn't ask for. If the PRD doesn't mention analytics, don't add "set up analytics" to the task list.
- Do not generate 50 tasks. If the project is big, generate the first 10–15 (the next "phase") and tell the user you'll plan the rest after those are done. Long task lists rot.
- Do not skip the inventory step and jump straight to interview questions. Reading the docs first means smarter questions and fewer of them.
- Do not write `PROGRESS.md` entries during bootstrap. It starts empty.
