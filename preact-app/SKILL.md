---
name: preact-app
description: Scaffold and build frontend web apps on the user's preact-starter setup — Preact + TypeScript + Vite + Tailwind CSS v4 + preact-iso routing + @preact/signals with a class-based AppModel store. Use when the user wants to start a new frontend app, SPA, dashboard, prototype or web UI (unless they name another framework), and when adding routes, components, stores or features to an app built from this starter (look for preact-iso, @preact/signals and src/store/index.tsx with AppModel).
---

The user's default frontend stack. Source of truth: github.com/zouhir/preact-starter (local checkout: `~/Projects/preact-starter`). A snapshot lives in `assets/template/`.

| Layer | Choice |
|---|---|
| UI | Preact (not React) + TypeScript (strict) |
| Build | Vite with `@preact/preset-vite`, `@tailwindcss/vite` |
| Styling | Tailwind CSS v4 utilities only (`@import "tailwindcss"` in `src/index.css`, no config file) |
| Routing | `preact-iso` (`LocationProvider`, `Router`, `Route`, `lazy`, `ErrorBoundary`) |
| State | `@preact/signals` in domain store classes composed into one `AppModel`, provided via context |

If the user asks for a different framework (React, Vue, Next, Svelte…), this skill does not apply.

## Starting a new app

1. Pick the target directory (ask only if the user gave no name or location; default to a sibling of the current project, e.g. `~/Projects/<name>`).
2. Run the scaffold script:
   ```bash
   <skill dir>/scripts/new-app.sh <target-dir> [--name <pkg-name>] [--title "<Page Title>"] [--no-install] [--no-git]
   ```
   It copies the template, renames the package (package.json + lockfile), sets `<title>` and the README heading, runs `npm install`, and `git init`s without committing. It refuses a non-empty target.
3. If `~/Projects/preact-starter` exists and has newer commits than the snapshot, prefer it: compare with `git -C ~/Projects/preact-starter log -1 --format=%h` against the snapshot commit below, and if they differ, mention it and offer to refresh the template (see "Refreshing the template").
4. Replace the placeholder Home content with the user's app, then build features following the conventions below.
5. Verify (see "Verify"). Don't commit unless asked.

## Conventions (apply in any app from this starter)

Read [references/patterns.md](references/patterns.md) before adding routes, stores or components — it has copy-ready recipes.

- **Preact JSX**: `class`, not `className`; `for`, not `htmlFor`. Hooks from `preact/hooks`, types (`ComponentChildren`, `JSX`) from `preact`. Signals from `@preact/signals`. Only reach for `preact/compat` when a React-only library demands it (tsconfig already aliases `react`/`react-dom`).
- **Layout**: `src/routes/<RouteName>/index.tsx` and `src/components/<ComponentName>/index.tsx`, PascalCase folders, **named exports** (no default exports). Create `src/components/` on first need.
- **Routing**: register every route in `src/app.tsx`. Keep the landing route eager; lazy-load all others with `lazy(() => import('./routes/X').then((m) => m.X))`. Keep `<Route default component={NotFound} />` last. Use plain `<a href>` for internal links (preact-iso intercepts them); `useLocation().route(path)` for programmatic navigation; `useRoute().params` for `:param` segments.
- **State**: app/shared state goes in domain store classes in `src/store/`, instantiated as `readonly` fields on `AppModel`. Pass a store only the other stores it depends on (constructor args), never the whole `AppModel`. Components read with `useStore()`. Keep ephemeral UI state (an open dropdown, an input draft) local with `useSignal`/`useState`. Derived values use `computed`; multi-signal writes use `batch`. Read `.value` in JSX so components subscribe.
- **Styling**: Tailwind utility classes only — no CSS modules, styled-components, or extra CSS files beyond `src/index.css` (theme tokens via `@theme` there). For polished UI blocks, the `tailwind-elements-select` / `tailwind-elements-build` skills apply; for visual direction, `frontend-design`.
- **TypeScript**: strict, `verbatimModuleSyntax` (use `import type` / inline `type` imports), `erasableSyntaxOnly` (no `enum`, no constructor parameter properties, no namespaces — declare class fields explicitly). Unused locals/params fail the build.
- **Dependencies**: keep it lean; check whether Preact/signals/preact-iso already covers it before adding a package.
- Keep the app's `llms.txt` and README in sync when you change structure or conventions.

## Verify

- `npm run build` (runs `tsc -b` then `vite build`) must pass — this is the type check.
- The template ships `.claude/launch.json` with a `dev` config (port 5173): use `preview_start {name: "dev"}` to open it in the browser pane, check console errors, click through the routes (including an unknown URL for the 404), and screenshot the result.

## Refreshing the template

The snapshot was taken from preact-starter commit `f0a6ca8`. To refresh it from the local checkout (tracked files only), after the user agrees:

```bash
rm -rf <skill dir>/assets/template && mkdir -p <skill dir>/assets/template && git -C ~/Projects/preact-starter archive HEAD | tar -x -C <skill dir>/assets/template
```

Then update the commit hash above and re-check that the conventions section still matches the starter's `llms.txt`.
