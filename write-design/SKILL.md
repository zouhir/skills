---
name: write-design
description: Produce and battle-test a design document for a task whose problem spec already exists (stage "designing" in .agent/index.md). Use when the user says "write the design", "design doc", "let's design this", "propose an implementation", or when continuing any task at the designing stage. Covers the design debate, the doc itself (03-design.md), and the goldfish gauntlet — fresh-context comprehension, critic, and readiness tests run as subagents. No production code is written in this skill.
---

# Write and Battle-Test the Design

The design doc is the durable source of truth: coding sessions are disposable, the doc is not. Any future zero-context session must be able to implement from this document alone. That standard — not elegance — is what you are writing toward.

## State layout

Task folder: `.agent/tasks/<slug>/` — read `01-problem.md`, `02-criteria.md`, `05-journal.md` (tail). This skill writes `03-design.md` and `06-verification.md`. Stages: `researching → designing → ready-for-backlog → implementing → reviewing → done`.

## Step 1 — Load context, then prove it

Read the problem spec, criteria, and any code/docs they reference. Then tell the user, in your own words, how the relevant part of the system currently works. Let them correct you **now** — a misunderstanding at minute one becomes a terrible design at minute ten. When corrected, read the file that proves the correction rather than taking it on faith.

## Step 2 — Propose the first draft yourself

Propose the initial technical approach — prose and block diagrams, short pseudocode at most, no real code. Do not ask the user to propose first: your draft is a test of whether you understood the system, and reacting to *their* draft would let their blind spots survive unexamined.

Then debate. Expect the first draft to be at least partly wrong. Answer "why did you choose that?" questions, challenge the user's counter-proposals, and update as the argument settles. Do not rush this; hours spent here are cheaper than days spent un-writing bad code.

## Step 3 — Write 03-design.md, section by section

Never one-shot the document. Write each section separately, in this order:

```markdown
# Design: <title>

## 1. Problem
<3–5 plain-English sentences; a casual reader understands the goal>

## 2. Technical plan
<jargon-light prose describing the major components and how they fit;
 block diagram if helpful>

## 3. Alternatives considered
<every approach debated and rejected, with why — these are guardrails
 against re-litigating decisions and against future hallucinations>

## 4. Detailed implementation
<the longest section: every file to be created or changed, what changes,
 and the rationale. A file not listed here does not get touched.>
```

Section 4 is what keeps implementation sessions on rails later — be exhaustive.

## Step 4 — The goldfish gauntlet

A doc is only proven complete when a **zero-context** reader can act on it. Run each gate as a fresh subagent (Task tool) that receives *only* the doc path and repo access — no conversation history. That absence of context is the entire point.

**Gate 1 — Comprehension.** Prompt the subagent: "Read `.agent/tasks/<slug>/03-design.md` and the files it references. Explain what it is trying to accomplish and how the current system works as it relates to this change." If its explanation has gaps or errors, the doc is missing context. Fix the doc, rerun. Do not skip this loop.

**Gate 2 — Critic.** Fresh subagent: "Assume the role of an expert technical reviewer. Read this design doc, the files it references, `02-criteria.md`, and `06-verification.md`. Do not re-raise anything listed in the doc's Alternatives section or already adjudicated in the verification log — those are settled. Classify every finding as exactly one of: **CRITICAL** — the design fails a specific acceptance criterion (name it) or cannot be implemented as written; **MAJOR** — an implementer would have to guess something the doc should state; **MINOR** — an improvement or preference. Findings without a classification and a concrete consequence don't count."

Then **adjudicate** — this is your judgment call, not the critic's: for each CRITICAL/MAJOR, either fix the doc, or reject it with a written rationale added to the doc's Alternatives section (so the next fresh critic sees it and cannot re-raise it). MINORs: batch-apply the worthwhile ones once, log the rest. Expect only a fraction of findings to deserve fixes — a critic that produces findings is doing its job; a doc that absorbs every finding is not converging, it's churning.

**Gate 3 — Readiness.** Fresh subagent: "You are an engineer experienced with this codebase. Read this doc and the files it references. Does it contain absolutely everything you need to implement this correctly on the first pass? List every missing piece of information." Answer its questions **in the doc**, not in chat.

### Convergence rules (all gates)

A fresh critic can generate findings forever — zero findings is not a reachable state, so it is not the stop condition. A gate **passes** when a round produces **no new CRITICAL or MAJOR findings** (new = not already fixed or rejected-with-rationale). Budget: **3 rounds per gate**. If a gate hasn't passed by round 3, stop looping and escalate: present the open findings and your recommendation to the human, and let them decide. The budget isn't a concession — it forces the judgment call back to a person instead of laundering it through repetition.

Record every round — including adjudications — in `06-verification.md`. Rejections recorded here (and mirrored in the doc's Alternatives) are what stop the next fresh critic from re-litigating:

```markdown
# Verification log: <title>

## <date> — design gate 1 (comprehension), round 1
Result: FAIL — didn't understand auth flow; added §2 diagram + auth.ts reference
## <date> — design gate 1, round 2
Result: PASS
## <date> — design gate 2 (critic), round 1
Findings: 2 CRITICAL, 4 MAJOR, 5 MINOR
Adjudication: fixed C1,C2,M1,M3; rejected M2 (conflicts with criterion 4 — rationale
in Alternatives); rejected M4 (out of scope, see Non-goals); 2 MINORs applied
## <date> — design gate 2, round 2
Findings: 0 CRITICAL, 0 new MAJOR → PASS
```

## Step 5 — Human sign-off and close out

Ask the user (or their reviewer) to approve the doc. Then update the index row: stage `ready-for-backlog`, next action "build backlog", and append a journal entry noting major decisions and which gate rounds it took. Point the user to the `build-backlog` skill — fine to run in a fresh session.
