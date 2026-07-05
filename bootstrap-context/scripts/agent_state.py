#!/usr/bin/env python3
"""agent_state.py - read-only accessor & validator for .agent/ task state.

The markdown files are the single source of truth; this script only parses,
checks, and answers. It never writes.

Commands:
  validate   exit 0 if state is well-formed and consistent; else print errors
  next       print the next actionable step for the active task (or --task SLUG)
  status     compact summary of all tasks + drift warnings

Usage: python3 .agent/scripts/agent_state.py [--root PATH] {validate|next|status} [--task SLUG]
Stdlib only. Python 3.8+.
"""
import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGES = ["researching", "designing", "ready-for-backlog", "implementing", "reviewing", "done"]
STALE_HOURS = 24

STATUS_RE = re.compile(
    r"^(?:(todo)|(done)|in_progress\s*\(\s*([^,)]+?)\s*,\s*since\s+([^)]+?)\s*\)|blocked\s*\((.+)\))$"
)


def parse_ts(s):
    s = s.strip().replace("Z", "+00:00")
    for fmt in (None, "%Y-%m-%d"):
        try:
            dt = datetime.fromisoformat(s) if fmt is None else datetime.strptime(s, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def age_hours(ts):
    dt = parse_ts(ts)
    return None if dt is None else (datetime.now(timezone.utc) - dt).total_seconds() / 3600


class State:
    def __init__(self, root):
        self.root = Path(root)
        self.agent = self.root / ".agent"
        self.errors, self.warnings = [], []
        self.active, self.rows = None, []
        self.backlogs = {}  # slug -> list of step dicts
        self._load()

    def err(self, m):
        self.errors.append(m)

    def warn(self, m):
        self.warnings.append(m)

    # ---------- parsing ----------
    def _load(self):
        idx = self.agent / "index.md"
        if not idx.exists():
            self.err(f"missing {idx.relative_to(self.root)}")
            return
        for line in idx.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^Active:\s*(\S+)", line.strip())
            if m:
                self.active = None if m.group(1) in {"-", "—", "none"} else m.group(1)
            if line.strip().startswith("|") and "---" not in line:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 4 and cells[0] not in ("task", ""):
                    stage = cells[1]
                    blocked = "(blocked)" in stage
                    stage = stage.replace("(blocked)", "").strip()
                    self.rows.append(
                        dict(task=cells[0], stage=stage, blocked=blocked, next=cells[2], updated=cells[3])
                    )
        for r in self.rows:
            self.backlogs[r["task"]] = self._parse_backlog(r["task"])

    def _parse_backlog(self, slug):
        p = self.agent / "tasks" / slug / "04-backlog.md"
        if not p.exists():
            return None
        steps, cur = [], None
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^##\s+Step\s+(\d+)\s*:\s*(.+)$", line)
            if m:
                cur = dict(n=int(m.group(1)), title=m.group(2).strip(), status="", deps=[],
                           files="", done_when="", raw_status="")
                steps.append(cur)
                continue
            if cur is None:
                continue
            m = re.match(r"^-\s*(status|depends_on|files|what|done_when)\s*:\s*(.*)$", line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if key == "status":
                    cur["raw_status"] = val
                elif key == "depends_on":
                    cur["deps"] = [int(x) for x in re.findall(r"\d+", val)]
                else:
                    cur[key] = val
        for s in steps:
            m = STATUS_RE.match(s["raw_status"])
            if not m:
                self.err(f"{slug} step {s['n']}: unparseable status '{s['raw_status']}'")
                s["status"] = "?"
            else:
                s["status"] = "todo" if m.group(1) else "done" if m.group(2) else \
                              "in_progress" if m.group(3) else "blocked"
                s["owner"], s["since"], s["reason"] = m.group(3), m.group(4), m.group(5)
        return steps

    # ---------- validation ----------
    def validate(self):
        seen = set()
        for r in self.rows:
            slug, stage = r["task"], r["stage"]
            if slug in seen:
                self.err(f"duplicate index row for '{slug}'")
            seen.add(slug)
            if stage not in STAGES:
                self.err(f"{slug}: unknown stage '{stage}' (expected one of {', '.join(STAGES)})")
            tdir = self.agent / "tasks" / slug
            if not tdir.exists():
                self.err(f"{slug}: no folder at {tdir.relative_to(self.root)}")
                continue
            need = {"ready-for-backlog": ["03-design.md"],
                    "implementing": ["03-design.md", "04-backlog.md"],
                    "reviewing": ["03-design.md", "04-backlog.md"]}.get(stage, [])
            for f in need:
                if not (tdir / f).exists():
                    self.err(f"{slug}: stage '{stage}' but {f} is missing")
            if stage in ("designing", "ready-for-backlog", "implementing", "reviewing"):
                for f in ("01-problem.md", "02-criteria.md"):
                    if not (tdir / f).exists():
                        self.warn(f"{slug}: {f} missing at stage '{stage}'")
            self._validate_backlog(r)
        if self.active and self.active not in seen:
            self.err(f"index Active '{self.active}' has no row")
        for r in self.rows:
            if age_hours(r["updated"]) is None:
                self.warn(f"{r['task']}: index 'updated' value '{r['updated']}' not a date")

    def _validate_backlog(self, row):
        slug, steps = row["task"], self.backlogs.get(row["task"])
        if steps is None or not steps:
            return
        nums = [s["n"] for s in steps]
        if len(nums) != len(set(nums)):
            self.err(f"{slug}: duplicate step numbers in backlog")
        byn = {s["n"]: s for s in steps}
        for s in steps:
            for d in s["deps"]:
                if d not in byn:
                    self.err(f"{slug} step {s['n']}: depends_on {d} does not exist")
                elif s["status"] == "done" and byn[d]["status"] != "done":
                    self.err(f"{slug} step {s['n']} is done but dependency {d} is not")
            if not s.get("done_when"):
                self.warn(f"{slug} step {s['n']}: no done_when criteria")
            if s["status"] == "in_progress":
                h = age_hours(s.get("since") or "")
                if h is None:
                    self.warn(f"{slug} step {s['n']}: in_progress 'since' not parseable")
                elif h > STALE_HOURS:
                    self.warn(f"{slug} step {s['n']}: in_progress for {h:.0f}h "
                              f"(owner {s.get('owner')}) - likely dead session; "
                              f"reconstruct from journal intent + git diff")
        undone = [s for s in steps if s["status"] in ("todo", "in_progress", "blocked", "?")]
        if row["stage"] == "implementing" and not undone:
            self.warn(f"{slug}: all steps done but stage is 'implementing' - move to 'reviewing'")
        if row["stage"] in ("reviewing", "done") and undone:
            self.warn(f"{slug}: stage '{row['stage']}' but {len(undone)} step(s) not done")

    # ---------- queries ----------
    def next_step(self, slug):
        row = next((r for r in self.rows if r["task"] == slug), None)
        if row is None:
            return f"no task '{slug}' in index"
        out = [f"task: {slug}  stage: {row['stage']}" + ("  [BLOCKED]" if row["blocked"] else "")]
        if row["stage"] != "implementing":
            act = {"researching": "resume research-task (open questions in 01-problem.md)",
                   "designing": "resume write-design (see 06-verification.md for last gate)",
                   "ready-for-backlog": "run build-backlog",
                   "reviewing": "run review-work",
                   "done": "task complete"}.get(row["stage"], row["next"])
            out.append(f"next: {act}")
            return "\n".join(out)
        steps = self.backlogs.get(slug) or []
        byn = {s["n"]: s for s in steps}
        for s in steps:
            if s["status"] == "in_progress":
                h = age_hours(s.get("since") or "")
                stale = f" - STALE ({h:.0f}h), reconstruct from journal + git diff" if h and h > STALE_HOURS else ""
                out.append(f"in flight: step {s['n']} \"{s['title']}\" ({s.get('owner')}){stale}")
        for s in steps:
            if s["status"] == "blocked":
                out.append(f"blocked: step {s['n']} \"{s['title']}\" - {s.get('reason')}")
        cand = next((s for s in steps
                     if s["status"] == "todo" and all(byn[d]["status"] == "done" for d in s["deps"] if d in byn)), None)
        if cand:
            out.append(f"next: step {cand['n']} \"{cand['title']}\"")
            if cand.get("files"):
                out.append(f"files: {cand['files']}")
            if cand.get("done_when"):
                out.append(f"done_when: {cand['done_when']}")
        elif not any(s["status"] == "in_progress" for s in steps):
            out.append("next: no eligible todo steps - check blocked steps or move stage")
        return "\n".join(out)

    def status(self):
        out = []
        for r in self.rows:
            steps = self.backlogs.get(r["task"])
            prog = ""
            if steps:
                done = sum(1 for s in steps if s["status"] == "done")
                prog = f"  {done}/{len(steps)} steps"
                cur = next((s for s in steps if s["status"] == "in_progress"), None)
                if cur:
                    prog += f"  (step {cur['n']} in progress: {cur.get('owner')})"
            flag = " [BLOCKED]" if r["blocked"] else ""
            out.append(f"{r['task']:<28} {r['stage']:<18}{flag}{prog}  next: {r['next']}")
        active = f"active: {self.active}" if self.active else "active: -"
        return active + "\n" + "\n".join(out) if out else active + "\n(no tasks)"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["validate", "next", "status"])
    ap.add_argument("--task", help="task slug (default: the index's Active task)")
    ap.add_argument("--root", default=".", help="repo root containing .agent/ (default: cwd)")
    args = ap.parse_args()

    st = State(args.root)
    st.validate()

    if args.command == "validate":
        for e in st.errors:
            print(f"ERROR: {e}")
        for w in st.warnings:
            print(f"WARN:  {w}")
        print(f"{len(st.errors)} error(s), {len(st.warnings)} warning(s)")
        sys.exit(1 if st.errors else 0)

    if st.errors:
        print("state has errors - run 'validate' first:", file=sys.stderr)
        for e in st.errors:
            print(f"  ERROR: {e}", file=sys.stderr)

    if args.command == "next":
        slug = args.task or st.active
        if not slug:
            print("no active task in index and no --task given")
            sys.exit(1)
        print(st.next_step(slug))
    elif args.command == "status":
        print(st.status())
        for w in st.warnings:
            print(f"WARN:  {w}")


if __name__ == "__main__":
    main()
