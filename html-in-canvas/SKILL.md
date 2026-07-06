---
name: html-in-canvas
description: Use the WICG HTML-in-Canvas browser API (`<canvas layoutsubtree>`, `drawElementImage`, `onpaint`, `requestPaint`, `captureElementImage`, `texElementImage2D`, `copyElementImageToTexture`) to paint real, accessible DOM into a canvas. Trigger when the user asks to render HTML inside a canvas, replace `html2canvas`, use DOM as a WebGL/WebGPU texture, capture an HTML element to an image/PNG, or otherwise mentions "HTML in canvas", `drawElementImage`, or `layoutsubtree`.
---

# HTML-in-Canvas

A dev-trial Chromium API (Chrome Canary + Brave Stable on Chromium 147+) that lets `<canvas>` paint its own real DOM children. The browser handles layout, text shaping, accessibility, focus, and hit-testing for the children; the canvas draws their cached paint records as pixels — composable with all existing 2D / WebGL / WebGPU operations.

This API is new and there is very little public documentation. **The authoritative source is the bundled spec, not your training data.** Do not rely on memory for signatures, behaviors, or timing — read the spec first, every time.

## STEP 0 — Read the spec before writing any code (do this every time)

Before writing, editing, or reviewing any HTML-in-Canvas code, read the relevant spec files. They are the source of truth. They ship inside this skill, so this step works on any machine — no external checkout required.

**Source — bundled with this skill, relative to `SKILL.md`:**

```
references/spec/
├── overview.md          # the 3 primitives + helper, synchronization, privacy, paint timing
├── api-reference.md     # exact IDL, all drawElementImage overloads, ElementImage, PaintEvent
├── design-decisions.md  # why the API is shaped this way (transforms ignored, Option C, etc.)
├── examples-analysis.md # the 5 official demos broken down into copyable patterns
├── browser-support.md   # flags, versions, what's not implemented
└── open-questions.md    # unresolved spec issues — check before relying on edge behavior
```

Read `overview.md` + `api-reference.md` at minimum. Add the others as the task warrants (3D → examples-analysis, "why doesn't X work" → open-questions + design-decisions).

**Staying current:** this spec is a snapshot. The upstream source is the `html-in-canvas-dot-dev` repo (`spec/` directory); if a local checkout exists at `~/Projects/html-in-canvas-dot-dev/spec/`, you may cross-check it for newer content and, if it has diverged, refresh `references/spec/` from it and tell the user. But never *require* that path — the bundled copy is always sufficient to answer.

Match your answer to what the spec actually says. If the spec and the quick reference below ever disagree, the spec wins — and flag the discrepancy to the user.

## When to use vs. not

Reach for HTML-in-Canvas when the canvas needs:
- Real text (bidi, shaping, ruby, vertical CJK, emoji) instead of `ctx.fillText`
- Real form controls, contenteditable, focus, or screen-reader semantics inside canvas-rendered scenes
- A native one-call replacement for `html2canvas` / DOM-to-image
- HTML used as a WebGL/WebGPU texture (3D scenes, shader post-processing, media export)

Do **not** suggest it for production code that must work today in Firefox/Safari, or in Chrome stable without the flag — it is dev-trial only. Always pair an example with browser-support guidance.

## Browser support

- Chrome Canary, flag `chrome://flags/#canvas-draw-element` ("Enable the new drawElement API for Canvas") → relaunch.
- Brave Stable ≥ 1.89.132 (Chromium 147+), flag `brave://flags/#canvas-draw-element`.
- Firefox / Safari: not implemented; no announced timeline.
- Chrome blocks click-through to `chrome://` URLs — tell users to copy-paste the flag URL.

Confirm exact versions/flags against `browser-support.md` — this moves.

## Quick reference (verify against the spec before relying on it)

The three primitives + one helper:

- **`layoutsubtree`** — boolean HTML attribute on `<canvas>`. Direct children participate in layout, hit-testing, and a11y; they stay visually invisible until drawn. Each child gets paint containment, becomes a containing block, and forms a stacking context.
- **`ctx.drawElementImage(element, ...)`** — draws a direct child into the canvas. Overloads mirror `drawImage()`:
  - `(element, dx, dy)`
  - `(element, dx, dy, dw, dh)`
  - `(element, sx, sy, sw, sh, dx, dy)`
  - `(element, sx, sy, sw, sh, dx, dy, dw, dh)`

  Returns a `DOMMatrix`. Assign it back: `element.style.transform = matrix.toString()` so DOM hit-testing, focus, and text selection line up with the painted pixels. Canvas CTM is applied; **CSS transforms on the element are ignored for drawing** (they'd double up). Element must be a direct child with generated boxes (no `display:none`).
- **`paint` event (`canvas.onpaint` / `addEventListener('paint', …)`)** — fires when child rendering changes. Has `changedElements: FrozenArray<Element>`. Fires just after the browser's own Paint step. **Canvas draw commands in the handler land this frame; DOM mutations you make in the handler apply on the *next* frame.** Changing a child's CSS transform does NOT trigger paint.
- **`canvas.requestPaint()`** — schedule a `paint` for the next frame (like `requestAnimationFrame`). Required to drive animation and required after offscreen DOM mutations so the browser regenerates cached paint records.
- **`canvas.captureElementImage(element)`** — returns a transferable `ElementImage` snapshot for `postMessage` to a worker / `OffscreenCanvas`. `ElementImage` has `width`, `height`, `close()`.
- **`canvas.getElementTransform(element, drawTransform)`** — returns the `DOMMatrix` to sync DOM hit-testing with a 3D (WebGL/WebGPU) draw transform.
- **WebGL:** `gl.texElementImage2D(target, level, internalformat, format, type, element)` — mirrors `texImage2D`. Use `TEXTURE_MIN_FILTER = LINEAR` (not mipmaps) for readable text.
- **WebGPU:** `device.queue.copyElementImageToTexture(source, destination)` — `source` may be an `Element` or `ElementImage`.

Full IDL and every overload's exact semantics are in `api-reference.md`. Read it rather than trusting this summary for anything subtle.

## Required boilerplate

```html
<canvas id="canvas" layoutsubtree>
  <div id="content">Real, accessible HTML</div>
</canvas>
```

```js
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const content = document.getElementById('content');

canvas.onpaint = () => {
  ctx.reset();                                   // deterministic transform state each frame
  const transform = ctx.drawElementImage(content, 0, 0);
  if (transform) content.style.transform = transform.toString(); // sync hit-testing
};

canvas.requestPaint?.();                          // trigger the first paint
```

For animation, call `canvas.requestPaint()` each frame (inside `requestAnimationFrame` if you're pacing to the display) — the browser's paint pipeline must run to refresh the children's cached paint records that `drawElementImage` reads from. Don't rely on rAF alone.

## DPR / canvas sizing — CHECK THE SPEC, it is nuanced

`api-reference.md` and `examples-analysis.md` size the canvas grid to **device pixels** via a `ResizeObserver` with `box: 'device-pixel-content-box'`:

```js
new ResizeObserver(([entry]) => {
  canvas.width  = entry.devicePixelContentBoxSize[0].inlineSize;
  canvas.height = entry.devicePixelContentBoxSize[0].blockSize;
}).observe(canvas, { box: 'device-pixel-content-box' });
```

Field-testing on some builds showed the opposite failure mode (DPR-scaling the bitmap breaks the children's layout viewport → wrong text wrapping/flex sizing on Retina), where sizing 1:1 with CSS pixels was more robust. **This is genuinely build-dependent right now.** Read the current `api-reference.md` "Device Pixel Ratio Handling" section, follow it as the default, and if layout looks wrong on HiDPI, try the 1:1 approach and tell the user about the trade-off (slightly softer text).

## Critical gotchas (learned the hard way — not all are in the spec)

1. **`drawElementImage` requires the source `<canvas layoutsubtree>` to actually be painted by the browser.** `display:none`, `visibility:hidden`, `opacity:0`, `left:-9999px`, and `clip-path: inset(50%)` all make Chrome skip painting → no cached paint record → `drawElementImage` throws "No cached paint record for element" or silently draws blank. To hide a staging canvas while keeping it paintable, wrap it in a `1×1` `overflow:hidden` container at a real on-screen position and let the canvas overflow it.

2. **DOM mutations inside `onpaint` apply on the *next* paint.** If you mutate text/layout in the handler, call `canvas.requestPaint()` immediately after so the new content shows.

3. **Always sync the returned `DOMMatrix` back to `element.style.transform`** when the drawn position differs from the laid-out position, or hit-testing/selection/focus land on the original DOM position, not the visible pixels. (Purely decorative multi-copy draws can skip this — say so if you do.)

4. **`ctx.drawFocusIfNeeded` crashes Brave Stable's renderer** ("Aw, Snap!" / `STATUS_ACCESS_VIOLATION`, ~0.5–1s after first paint, no console output) on `layoutsubtree` canvases — even though the official pie-chart demo uses it. Hand-draw focus rings instead: retrace the path and stroke it when `el === (root.activeElement ?? document.activeElement)`.

5. **Three.js + `<canvas layoutsubtree>` directly as a `CanvasTexture` source stalls at the first frame** — its upload pipeline doesn't see the layoutsubtree repaint as a content change. Workaround: `drawImage` the staging canvas into a plain intermediate `<canvas>` each frame, use *that* as the texture source, and set `tex.needsUpdate = true`.

6. **`createImageBitmap(layoutsubtreeCanvas)` can crash the Chrome Canary renderer.** Route through `canvas.toBlob()` → `createImageBitmap(blob)` for a transferable bitmap (slight overhead, safe) if `captureElementImage` isn't available in the user's build.

7. **Cross-version naming drift.** Some Canary builds expose `ctx.drawElement` instead of/alongside `ctx.drawElementImage`, and `requestPaint` may be absent. Feature-detect and optional-call:
   ```js
   const drawElementInto = ctx.drawElementImage?.bind(ctx) ?? ctx.drawElement?.bind(ctx);
   canvas.requestPaint?.();
   ```

8. **Privacy / tainted-canvas.** Anything drawn via `drawElementImage` must be same-origin-equivalent. Cross-origin iframes/images, `:visited` styling, system-theme colors, spellcheck markers, autofill previews are excluded by spec (see `overview.md` / `design-decisions.md`). Don't promise they'll render.

9. **`inert` on 3D-mapped HTML.** When HTML is a texture on a 3D surface, set `inert` on the source element so its on-screen DOM hit-box doesn't intercept clicks meant for the 3D scene. For interactive 3D HTML you must raycast and re-dispatch events yourself.

## Self-check before reporting done

- [ ] I read the bundled spec (`references/spec/`) for this task, not just memory.
- [ ] Canvas has `layoutsubtree`; drawn elements are *direct* children of it.
- [ ] An `onpaint` (or `addEventListener('paint', …)`) handler exists.
- [ ] Animation / state changes call `canvas.requestPaint?.()`.
- [ ] Canvas grid sizing follows the current spec's DPR guidance (and I flagged the HiDPI trade-off if relevant).
- [ ] Returned `DOMMatrix` is applied to the source element's `style.transform` (or I justified skipping it).
- [ ] No `drawFocusIfNeeded` on `layoutsubtree` canvases.
- [ ] Staging canvases are visually painted (not `display:none` etc.).
- [ ] Optional-chained `requestPaint?.()` and feature-detected `drawElementImage`/`drawElement`.
- [ ] I told the user this is dev-trial Chromium-only and which flag to enable.

## References in this skill

- `references/spec/` — the six spec files, bundled with this skill. This is the source of truth and works on any machine; read it directly. It's a snapshot of the upstream `html-in-canvas-dot-dev` `spec/` directory — see "Staying current" under STEP 0 for how to refresh it if a newer local checkout is available.

When editing demos inside a local `html-in-canvas-dot-dev` checkout itself, also follow that repo's `CLAUDE.md` (dual standalone/shadow-root authoring, `npm run check`, Playwright per changed demo).
