# skills

Personal [Claude Code](https://claude.com/claude-code) skills, symlinked into `~/.claude/skills/` via GNU Stow.

## Skills

- **[session-log](session-log/)** — Track project tasks across sessions using `TODO.md` + `PROGRESS.md`. Triggered by "next task", "continue", "where were we".
- **[session-log-bootstrap](session-log-bootstrap/)** — One-time setup helper: interviews the user and inspects the codebase to populate `TODO.md` for a new project.

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
