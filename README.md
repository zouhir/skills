# skills

Personal [Claude Code](https://claude.com/claude-code) skills, symlinked into `~/.claude/skills/` via GNU Stow.

Eight skills implement a full task lifecycle for AI agents — research → design → backlog → implement → review — with persistent, multi-session progress tracking. Based on the Elephant-Goldfish Model (context-rich sessions produce durable docs; fresh sessions verify and execute them), extended with an execution-state layer the original method lacks.

## Skills

| Skill | Role | Typical trigger |
|---|---|---|
| **[research-task](research-task/)** | Interrogation → problem spec + acceptance criteria | "new feature", "let's build X" |
| **[write-design](write-design/)** | Design doc + fresh-context gauntlet (comprehension / critic / readiness) | "write the design" |
| **[build-backlog](build-backlog/)** | Decompose design into session-sized steps | "break this down" |
| **[implement-step](implement-step/)** | Execute one step: claim, write-ahead journal, exact-plan, clean exit | "implement", routed from next-task |
| **[review-work](review-work/)** | Adversarial review vs. criteria + design, loop until nitpicks | "review this", "ready to merge?" |
| **[task-status](task-status/)** | Read-only report: done / in-flight / blocked / drift / what's left | "where are we?" |
| **[next-task](next-task/)** | Continuation dispatcher: orient from state, route by stage | "work on next task", "continue" |
| **[bootstrap-context](bootstrap-context/)** | Scoped README roll-up (monorepo-safe) + `.agent/` init | per subtree, on demand |

### Domain skills

Standalone reference skills, unrelated to the task lifecycle above.

| Skill | Role | Typical trigger |
|---|---|---|
| **[html-in-canvas](html-in-canvas/)** | Consult the local WICG HTML-in-Canvas spec, then build with `<canvas layoutsubtree>` / `drawElementImage` / `onpaint` — reads the spec every time since the API is new and undocumented | "render HTML in a canvas", "replace html2canvas", "DOM as a WebGL texture" |

## Shared state — the actual memory

Skills are stateless instructions; all persistence lives in one git-committed folder:

```
.agent/
  index.md                  # registry: stage + next action per task
  scripts/agent_state.py    # read-only validator/accessor (see below)
  tasks/<slug>/
    01-problem.md           # problem spec
    02-criteria.md          # acceptance criteria
    03-design.md            # technical plan, alternatives, file-by-file changes
    04-backlog.md           # steps: status, deps, files, done-criteria
    05-journal.md           # append-only: intents, deviations, blockers
    06-verification.md      # design gates + review rounds
```

`agent_state.py` (bundled in research-task and bootstrap-context, installed into `.agent/scripts/` on init) gives deterministic reads over the markdown: `validate` catches malformed statuses, dangling deps, and stage drift; `next` computes the next eligible step; `status` summarizes everything. Markdown stays the single source of truth — the script never writes.

The invariant the whole system defends: **a fresh session reading only this folder knows exactly what to do next, with zero chat history.** Commit `.agent/` — it's team state and institutional memory, not scratch.

## Lifecycle

```
research-task ──► write-design ──► build-backlog ──► implement-step ×N ──► review-work ──► done
   (spec+criteria)   (doc+gates)       (steps)          (one per fresh chat,     (fresh-context
                                                         parallel if disjoint)     critics)
        ▲
   next-task = entry point for any resumed session (routes by stage)
   task-status = read-only "where are we?" — safe anytime
   bootstrap-context = one-time brownfield onboarding
```

## Quickstart

1. Existing repo? Run `bootstrap-context` once. New repo? Skip it.
2. "Let's build \<feature\>" → `research-task` fires → answer its questions.
3. Fresh chat: "work on next task" → routed to `write-design`, then `build-backlog`, then step-by-step `implement-step` — one fresh chat per step, killable at any time for the price of a journal entry.
4. "Where are we?" in any chat → `task-status`.

## Make invocation deterministic

Skills auto-trigger by matching their `description` against your request — reliable, but probabilistic. Add this to a repo's `CLAUDE.md` to pin the entry points:

```markdown
## Task workflow
This repo tracks agent work in .agent/ (see .claude/skills/).
- On any continuation request ("continue", "next task", "resume",
  "keep going"), invoke the next-task skill before doing anything else.
- For any new non-trivial feature or task, invoke research-task first —
  do not jump to design or code.
- Never edit .agent/ files except through the workflow skills.
- Any change that adds/removes/repurposes files in a directory updates
  that directory's README.md file list (if READMEs exist).
```

## Design rules the skills enforce

- **Write-ahead journaling:** intent is journaled before code is touched, so a dead session is reconstructable from journal + `git diff`.
- **Two legal exits only:** every implementation session ends `done` (journaled, committed) or `blocked` (journaled, nothing half-applied). Anything not written down never happened.
- **Plan mutable only through recorded edits:** a deviation that affects future steps updates the design + backlog *now* — future sessions read the plan, not old chats.
- **Fresh-context verification:** design gates and reviews run in zero-context subagents, because the session that wrote something can't neutrally judge it.

## Install

Requires [stow](https://www.gnu.org/software/stow/) (`brew install stow`).

```sh
make link      # symlink every skill into ~/.claude/skills/
make unlink    # remove the symlinks
make relink    # unlink + link (useful after adding a new skill)
```

## Adding a new skill

1. Create a directory at the repo root with a `SKILL.md` inside. The directory name must match the `name:` in the skill's frontmatter.
2. Run `make relink`.
