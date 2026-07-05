---
name: bootstrap-context
description: Make an existing codebase agent-ready by generating README context files and initializing the .agent/ state folder. Default mode is scoped — bootstrap only the subtrees relevant to upcoming work — which is what makes this viable on large monorepos; whole-tree roll-up is the optional thorough mode for small and medium repos. Use when adopting the task workflow on a brownfield repo — "onboard this codebase", "bootstrap context", "make this repo agent-ready", "generate READMEs". Not needed for greenfield projects, where design docs provide coverage from day one.
---

# Bootstrap Context for an Existing Codebase

Feeding an agent a whole source tree chokes its context and invites hallucination. A hierarchy of READMEs is compressed, layered context: a fresh session reads a handful of small files and understands the system's shape — because docs are orders of magnitude smaller than the code they describe.

Context is only worth generating where work will happen. Default to **scoped mode**; offer whole-tree only when the repo is small enough that the difference doesn't matter (roughly: a tree you could README in an afternoon).

## Scoped mode (default — monorepo-safe)

**1. Determine the working set.** Ask the user which area the upcoming work lives in, or derive it from the active task if one exists (the design doc and backlog enumerate files — their parent directories are the working set). Typically this is one service, package, or module subtree, not the repo.

**2. Draw the shallow map.** At the repo root, create (or update) a `README.md` that lists only the top-level directories with a one-line purpose each — no recursion. This "map of maps" is cheap even on a huge monorepo and gives every future session global orientation: what exists and where, without detail.

**3. Bootstrap the subtree.** Within the working set only, run the leaf-to-root process below. Stop at the subtree's root — do not roll up beyond it.

**4. Expand lazily.** When a later task touches an unbootstrapped area, run this skill again scoped to that area. Coverage grows where work actually happens; untouched corners of the monorepo never cost anything.

## The leaf-to-root process (used by both modes)

**Leaf READMEs (fan out).** For each leaf directory in scope — skipping vendored/generated dirs (`node_modules`, `dist`, `.git`, build output) — write a `README.md` that (a) explains the directory's purpose in 2–4 sentences and (b) enumerates each file with a one-line description. When subagents are available, fan out one per directory batch; the work is independent.

**Human verification checkpoint.** Leaf summaries inferred from code alone will be meaningfully wrong — expect something like half to need correction, because code carries no "why". Batch the generated READMEs and ask the user (or the engineer who owns each area) to spend 5–10 minutes per directory fixing them. Do not skip this: errors verified in at the leaves get amplified at every roll-up level above.

**Roll up, level by level.** Moving one level up at a time until the scope's root: read all child `README.md` files plus the code files in the current directory only, then write this directory's `README.md` in the same format (purpose + per-entry one-liners, where entries are files and subdirectories). Children's READMEs substitute for reading their code — that substitution is the compression.

## Whole-tree mode

Same process, scope = entire repo, rolled up to the root. Only sensible when the tree is small; on a monorepo, recommend scoped mode instead and say why.

## Initialize .agent/

Create the state folder used by the workflow skills:

```
.agent/
  index.md      # start with an empty registry:
                #   # Task Index
                #   Active: —
                #   | task | stage | next action | updated |
  tasks/        # empty; research-task populates it
  scripts/      # copy agent_state.py here from this skill's scripts/ dir
```

`agent_state.py` is the read-only validator/accessor (`validate` / `next` / `status`) the workflow skills use for deterministic state checks. Suggest committing `.agent/` and the READMEs — they are shared team state, not scratch.

## Lifespan and maintenance

- The READMEs are scaffolding: needed until design docs reference (and lightly explain) every code file in the areas you work on. At full design-doc coverage they're optional — keep or delete.
- One-line freshness rule worth adding to the repo's CLAUDE.md: any change that adds/removes/repurposes files in a directory updates that directory's README file list.
- Bonus: the hierarchy doubles as an onboarding pack — a new engineer (or a fresh agent) reads the map plus their subtree's README chain instead of shadowing someone for two weeks.
