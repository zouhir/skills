# skills

Personal [Claude Code](https://claude.com/claude-code) skills, symlinked into `~/.claude/skills/` via GNU Stow.

## Skills

| Skill | Role | Typical trigger |
|---|---|---|
| **[html-in-canvas](html-in-canvas/)** | Consult the local WICG HTML-in-Canvas spec, then build with `<canvas layoutsubtree>` / `drawElementImage` / `onpaint` — reads the spec every time since the API is new and undocumented | "render HTML in a canvas", "replace html2canvas", "DOM as a WebGL texture" |

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
