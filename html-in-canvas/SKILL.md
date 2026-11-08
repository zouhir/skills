---
name: html-in-canvas
description: Use the WICG HTML-in-Canvas browser API (`<canvas content="drawable">`, the `drawable` attribute, `drawElementImage`, `onpaint`, `requestPaint`, `updateElementGeometry`, `captureElementImage`, `texElementSubImage2D`, `drawElementImageToTexture`; formerly `layoutsubtree`, `texElementImage2D`, `copyElementImageToTexture`) to paint real, accessible DOM into a canvas. Trigger when the user asks to render HTML inside a canvas, replace `html2canvas`, use DOM as a WebGL/WebGPU texture, capture an HTML element to an image/PNG, migrate old `layoutsubtree` code, or otherwise mentions "HTML in canvas", `drawElementImage`, `drawable`, or `layoutsubtree`.
---

# HTML-in-Canvas

A dev-trial Chromium API (Chrome Canary, behind flags) that lets `<canvas>` paint real DOM descendants. The browser handles layout, text shaping, accessibility, focus, and hit testing. The canvas draws snapshots of the elements as pixels, which compose with all existing 2D / WebGL / WebGPU operations.

**The API had breaking changes in Aug–Sep 2026.** Most code, blog posts, and training data use the *old* shape (`layoutsubtree`, `DOMMatrix` return value, `texElementImage2D`, `copyElementImageToTexture`). **The authoritative source is the bundled spec, not your memory.** Read it first, every time.

## STEP 0: Read the spec before writing any code (every time)

Before you write, edit, or review any HTML-in-Canvas code, read the relevant spec files. They ship inside this skill, relative to `SKILL.md`:

```
references/spec/
├── overview.md          # 5 primitives, paint timing, a11y, privacy, old→new migration table
├── api-reference.md     # exact IDL, all overloads, geometry API, WebGL/WebGPU, patterns
├── design-decisions.md  # why: drawable attr, auto geometry, sub-image upload, Option C
├── examples-analysis.md # the 5 official demos broken down into copyable patterns
├── browser-support.md   # flags, old-vs-new API generations, feature detection
└── open-questions.md    # open upstream issues; check before relying on edge behavior
```

Read `overview.md` + `api-reference.md` at minimum. Add the others as the task needs them (3D → examples-analysis; "why doesn't X work" → open-questions + design-decisions; migrating old code → overview's migration table + browser-support).

**Staying current:** this is a snapshot of the WICG explainer as of **2026-10-03** (upstream `20d5f08`). The upstream source is https://github.com/WICG/html-in-canvas (`README.md` + `Examples/`). Breaking changes are announced as pinned issues there. If you have network access and the task depends on exact details, check for commits after that date. If upstream has diverged, tell the user, and offer to refresh `references/spec/`. Never *require* that check. The bundled copy is enough to answer.

If the spec and the quick reference below ever disagree, the spec wins. Flag the discrepancy to the user.

## When to use vs. not

Reach for HTML-in-Canvas when the canvas needs:
- Real text (bidi, shaping, ruby, vertical CJK, emoji) instead of `ctx.fillText`
- Real form controls, contenteditable, focus, or screen-reader semantics in canvas-rendered scenes
- A native replacement for `html2canvas` / DOM-to-image
- HTML as a WebGL/WebGPU texture (3D scenes, shader effects, media export)

Do **not** suggest it for production code that must work today in Firefox/Safari or in Chrome stable without flags. It's dev-trial only. Always pair an example with browser-support guidance.

## Browser support

- Chrome Canary: enable **both** `chrome://flags/#canvas-draw-element` **and** `chrome://flags/#enable-experimental-web-platform-features`, then relaunch. Chrome blocks click-through to `chrome://` URLs, so tell users to copy and paste them.
- Brave Stable 1.89 / Chromium 147 (`brave://flags/#canvas-draw-element`) has only the **old** API.
- Firefox / Safari: not implemented, no announced timeline.

Confirm against `browser-support.md`, which changes often.

## Quick reference (current API; verify against the spec)

- **`<canvas content="drawable">`** opts descendants into layout. Replaces `layoutsubtree`. The canvas blockifies its immediate children. Descendants are in the a11y tree (without geometry until set) and **not hit-testable until their geometry is set**.
- **`drawable` attribute** is **required on every element you draw**, including direct children. It implies `isolation: isolate` and a containing block. **Nestable:** drawing a drawable captures its subtree *minus* nested drawables, which you draw separately.
- **`ctx.drawElementImage(el, …)`** uses `drawImage`-style overloads `(dx,dy)`, `(dx,dy,dw,dh)`, `(sx,sy,sw,sh,dx,dy)`, `(sx,sy,sw,sh,dx,dy,dw,dh)`, each with an optional trailing `{ preserveElementGeometry }`.
  - **Returns `undefined`.** In 2D it **automatically** syncs hit testing, a11y bounds, and `getBoundingClientRect` to the drawn position, and puts the element on top of the hit-test stack. Do not write `style.transform`.
  - Draws the last snapshot from the border box, *before* CSS transforms. The canvas CTM applies. Coordinates are **canvas grid px** (CSS px × `devicePixelRatio` with a DPR-sized canvas). A source rect can add outsets for ink overflow.
  - Throws if the element isn't `drawable`, before the first snapshot, or if the element is inside a nested `<canvas>`.
- **`paint` event** (`CanvasPaintEvent`, `event.changedElements`) fires after Paint each rendering update when a snapshot changed. **Draw calls land this frame. DOM mutations land next frame.** Fires in reverse tree order (descendants first). Geometry/CSS-transform changes don't trigger it.
- **`canvas.requestPaint()`** forces one `paint` next frame. Use it for the initial paint, continuous animation, and after mutations made inside `onpaint`.
- **`canvas.updateElementGeometry(el, { canvasTransform?, clip?, preserveHitTestOrder? })`** sets geometry manually. **Required for WebGL/WebGPU.** `canvasTransform` maps the border box → canvas **CSS** coordinates. `clip` limits the hit region. Also `clearElementGeometry(el)` and `getElementTransform(el)` (now one argument).
- **`canvas.captureElementImage(el)`** returns a transferable `ElementImage` (`width`/`height` are `double`s in canvas grid units, plus `close()`). Use it for workers + `OffscreenCanvas`, and to size textures. Worker geometry updates are batched to the main thread, which then fires `canvas.onelementgeometryupdate` (`event.elements`).
- **WebGL:** `gl.texElementSubImage2D(target, level, xoffset, yoffset, el, config?)`. It **doesn't allocate**, so call `texImage2D(..., null)` first, sized from `captureElementImage`. Use `TEXTURE_MIN_FILTER = LINEAR`.
- **WebGPU:** `device.queue.drawElementImageToTexture({ source: el, sourceX?, … }, { texture, size? })`.

## Required boilerplate (2D)

```html
<canvas id="canvas" content="drawable" layoutsubtree>  <!-- layoutsubtree: only for old builds -->
  <div id="content" drawable>Real, accessible HTML</div>
</canvas>
```

```js
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const content = document.getElementById('content');

canvas.onpaint = () => {
  ctx.reset();                                  // deterministic state each frame
  ctx.drawElementImage(content, 0, 0);          // geometry syncs automatically
};

new ResizeObserver(([entry]) => {
  canvas.width  = entry.devicePixelContentBoxSize[0].inlineSize;
  canvas.height = entry.devicePixelContentBoxSize[0].blockSize;
}).observe(canvas, { box: 'device-pixel-content-box' });

canvas.requestPaint();                          // first paint
```

For animation, call `canvas.requestPaint()` at the end of `onpaint` (or from rAF). The rendering pipeline has to run to refresh the snapshots `drawElementImage` reads, so rAF alone isn't enough.

## Supporting old builds (only if the user needs it)

Default to the **current** API. If the user is on Brave/Chromium 147-era builds, or asks for compatibility, do what the official demos do: set both `content="drawable"` and `layoutsubtree`, put `drawable` on drawn elements (harmless on old builds), and branch on feature detection:

```js
const NEW_API = 'updateElementGeometry' in HTMLCanvasElement.prototype;

const r = ctx.drawElementImage(el, x, y);
if (!NEW_API && r) el.style.transform = r.toString();      // old: manual sync
```

For WebGL/WebGPU, `try` the new method and fall back to `texElementImage2D(target, level, ifmt, fmt, type, el)` / `copyElementImageToTexture(...)` (see `examples-analysis.md` for exact fallbacks). The old names will be removed after the migration period, so say so.

## DPR / canvas sizing

Upstream (README, all demos) sizes the canvas grid to **device pixels** via `ResizeObserver` with `box: 'device-pixel-content-box'`, and expresses draw coordinates in grid pixels (`el.offsetWidth * devicePixelRatio`, etc.). Follow that by default.

Field testing on old (Chromium 147-era) builds sometimes showed DPR-scaled bitmaps breaking the children's layout (wrong wrapping or flex sizing on Retina), where sizing 1:1 with CSS px held up better. If HiDPI layout looks wrong, try 1:1 and tell the user the trade-off (softer text). This hasn't been re-verified on the new API.

## Critical gotchas (some learned the hard way, not in the spec)

1. **Forgot `drawable`?** Every drawn element needs it. Missing it **throws** on new builds. A nested drawable won't appear when you draw its parent. Draw it yourself (see `nested-sparkles` in `examples-analysis.md`).

2. **Don't hand-write `style.transform` on the new API.** Geometry is automatic in 2D. Writing a CSS transform as well double-offsets hit testing. If you need custom hit geometry, draw with `{ preserveElementGeometry: true }` and call `updateElementGeometry`.

3. **WebGL/WebGPU need explicit `updateElementGeometry` every paint.** Without it, drawn elements are not hit-testable, have no a11y geometry, and focus/clicks go nowhere. Project the textured quad to canvas CSS px and build a `DOMMatrix` (see the WebGL card in `examples-analysis.md`). Set `inert` on drawables that aren't currently visible (e.g. a card's back face).

4. **`texElementSubImage2D` needs pre-allocated storage.** Allocate once with `texImage2D(..., null)` from `Math.ceil(captureElementImage(el).width/height)`, and re-allocate when the element grows. Otherwise you get GL errors or blank textures.

5. **The source canvas must actually be painted by the browser.** `display:none`, `visibility:hidden`, `opacity:0`, `left:-9999px`, and `clip-path: inset(50%)` can make Chrome skip painting. Then there's no snapshot, and `drawElementImage` throws or draws blank. To hide a staging canvas but keep it painted, wrap it in a `1×1` `overflow:hidden` container at a real on-screen position and let it overflow. (Seen on old builds. Still a sensible default.)

6. **DOM mutations inside `onpaint` apply on the *next* paint.** Call `canvas.requestPaint()` after mutating.

7. **Undrawn descendants still count for a11y.** Hidden views and stale content under `content="drawable"` are in the a11y tree. Remove them or use `aria-hidden` / `inert`.

8. **`ctx.drawFocusIfNeeded` crashed Brave Stable 1.89's renderer** ("Aw, Snap!" `STATUS_ACCESS_VIOLATION`, ~0.5–1s after first paint) on `layoutsubtree` canvases, even though the pie-chart demo uses it. Focus rings now render as part of `drawElementImage` per the spec. Prefer that, or hand-draw a ring, on older builds.

9. **Three.js `CanvasTexture` with a drawable canvas as its source stalled at the first frame** (old builds). Workaround: `drawImage` it into a plain intermediate canvas each frame and set `tex.needsUpdate = true`. Or use the experimental three.js `HTMLTexture` (mrdoob/three.js PR #31233).

10. **`createImageBitmap(drawableCanvas)` could crash Canary's renderer** (old builds). Prefer `captureElementImage`, or `toBlob()` → `createImageBitmap(blob)`.

11. **Privacy exclusions:** cross-origin iframes/images/`url()`/SVG refs, system colors, spelling markers, `:visited`, autofill previews, subpixel AA, **captions and video controls**, and **IME UI** don't paint. Same-origin iframes paint. Don't promise the excluded content will render. Nothing warns you when it's omitted (issue #77).

12. **Offline/video export is frame-rate bound.** You must `requestPaint()` and await `paint` per frame. There's no synchronous snapshot yet (issue #171).

## Self-check before reporting done

- [ ] I read the bundled spec (`references/spec/`) for this task, not just memory.
- [ ] Canvas has `content="drawable"` (plus `layoutsubtree` only if old builds matter).
- [ ] Every drawn element has `drawable`. Nested drawables are drawn separately.
- [ ] An `onpaint` handler exists, and `requestPaint?.()` triggers the first paint and any animation.
- [ ] 2D: no manual `style.transform` sync (or it's gated behind old-API detection).
- [ ] WebGL/WebGPU: storage pre-allocated, the new method names are used, and `updateElementGeometry` is called with a correct `canvasTransform`. Off-screen faces are `inert`.
- [ ] Draw coordinates are in canvas grid px and the canvas is DPR-sized (or I flagged the HiDPI trade-off).
- [ ] Undrawn descendants are removed or hidden from a11y.
- [ ] I told the user it's dev-trial Chromium-only, which **two** flags to enable, and that older builds use a different API shape.

## References in this skill

- `references/spec/`: six spec files synced from `WICG/html-in-canvas` on 2026-10-03. This is the source of truth and works on any machine.

When editing demos inside a local `html-in-canvas-dot-dev` checkout, also follow that repo's `CLAUDE.md`. Note: that site's own `spec/` directory was last synced 2026-04-14 and predates the API change.
