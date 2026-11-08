#!/usr/bin/env bash
# Scaffold a new Preact app from the bundled starter template.
#
# Usage: new-app.sh <target-dir> [--name <package-name>] [--title "<Page Title>"] [--no-install] [--no-git]
#
# - <target-dir> must not exist, or must be empty.
# - --name defaults to the target directory's basename (lowercased, npm-safe).
# - --title defaults to the name in Title Case; sets <title> and the README heading.
# - Runs npm install and git init (no commit) unless disabled; skips git init inside an existing repo.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$SKILL_DIR/assets/template"

usage() { sed -n '2,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 1; }

TARGET="" NAME="" TITLE="" INSTALL=1 GIT=1
while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="${2:?--name needs a value}"; shift 2 ;;
    --title) TITLE="${2:?--title needs a value}"; shift 2 ;;
    --no-install) INSTALL=0; shift ;;
    --no-git) GIT=0; shift ;;
    -h|--help) usage ;;
    -*) echo "Unknown option: $1" >&2; usage ;;
    *) [ -z "$TARGET" ] || { echo "Only one target dir allowed" >&2; usage; }; TARGET="$1"; shift ;;
  esac
done
[ -n "$TARGET" ] || usage

if [ -e "$TARGET" ] && [ -n "$(ls -A "$TARGET" 2>/dev/null)" ]; then
  echo "Refusing to scaffold: $TARGET exists and is not empty" >&2
  exit 1
fi

[ -n "$NAME" ] || NAME="$(basename "$TARGET")"
NAME="$(printf '%s' "$NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^[-._]+//; s/-+$//')"
[ -n "$NAME" ] || { echo "Could not derive a valid package name; pass --name" >&2; exit 1; }
[ -n "$TITLE" ] || TITLE="$(printf '%s' "$NAME" | sed -E 's/[-_.]+/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1')"

mkdir -p "$TARGET"
cp -R "$TEMPLATE/." "$TARGET/"
cd "$TARGET"

# Rename package (package.json + lockfile root entries), page title and README heading.
APP_NAME="$NAME" APP_TITLE="$TITLE" node - <<'JS'
const fs = require('fs')
const { APP_NAME: name, APP_TITLE: title } = process.env
const edit = (file, fn) => fs.writeFileSync(file, fn(fs.readFileSync(file, 'utf8')))

edit('package.json', (s) => JSON.stringify({ ...JSON.parse(s), name }, null, 2) + '\n')
edit('package-lock.json', (s) => {
  const lock = JSON.parse(s)
  lock.name = name
  if (lock.packages?.['']) lock.packages[''].name = name
  return JSON.stringify(lock, null, 2) + '\n'
})
const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
edit('index.html', (s) => s.replace(/<title>.*<\/title>/, `<title>${esc(title)}</title>`))
edit('README.md', (s) => s.replace(/^# .*$/m, `# ${title}`))
JS

if [ "$INSTALL" = 1 ]; then
  npm install --no-audit --no-fund
fi

if [ "$GIT" = 1 ] && ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git init -q  # no commit: leave that to the user
fi

echo "Created $NAME in $(pwd)"
