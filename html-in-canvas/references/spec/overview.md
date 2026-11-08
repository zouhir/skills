---
title: Spec Overview
order: 1
---

# HTML-in-Canvas Spec Overview

**Source:** https://github.com/WICG/html-in-canvas (synced 2026-11-07, upstream `5d9d970`; cross-checked against Chromium M157 IDL)  
**Status:** Living explainer, continuously updated. HTML spec PR [whatwg/html#11588](https://github.com/whatwg/html/pull/11588) is open. **Enabled by default in Chrome 157+** (stable 2026-11-03), with no flags. Not in Firefox or Safari. See `browser-support.md`.  
**Authors:** Philip Rogers, Stephen Chenney (Igalia), Chris Harrelson, Philip Jägenstedt, Stefan Zager, Khushal Sagar, Vladimir Levin, Fernando Serboncini

> **API changed in Aug–Sep 2026.** `layoutsubtree` → `content="drawable"`. A `drawable` attribute is now required on drawn elements. `drawElementImage` returns `undefined` and syncs geometry automatically. WebGL/WebGPU methods were renamed. `PaintEvent` → `CanvasPaintEvent`. **Oct 2026:** `ElementImage.width/height` were removed in favor of `canvas.getElementImageDefaultSize(el)`, and the geometry option `clip` was renamed `canvasClip`. See "Migrating from the old API" below.

## Problem

There is no web API to render complex HTML layouts into a `<canvas>`. As a result, canvas-based content suffers in accessibility, internationalization, performance, and quality.

## Use Cases

1. **Styled, laid-out content in canvas**: chart legends/axes, rich text boxes in creative tools, in-game menus
2. **Accessibility**: no more hand-syncing an auxiliary DOM subtree with canvas draw calls
3. **Composing HTML with effects**: general WebGL shaders on HTML, beyond CSS filters/blend modes
4. **HTML in 3D**: rich 2D content on surfaces in a 3D scene
5. **Media export**: HTML content to images or video

## Solution: Five Primitives

### 1. The canvas `content` attribute

`content="fallback"` (default) treats canvas descendants as fallback content. `content="drawable"` opts descendants into layout.

```html
<canvas content="drawable">
  <div drawable id="label">Laid out, but invisible until drawn</div>
</canvas>
```

- The canvas **blockifies** its immediate children, and they're laid out with static positioning.
- Descendants are in the accessibility tree like regular DOM (and respect `aria-hidden`, `inert`, etc.). Until their geometry is set, they're exposed **without geometry**.
- Descendants are **not hit-testable** until their geometry is set (automatically by a 2D draw, or explicitly with `updateElementGeometry`).

### 2. The `drawable` attribute

Required on any descendant you want to draw (including direct children). It implies `isolation: isolate` and makes the element a containing block for all its descendants. Drawables **can be nested**. A *drawable subtree* is a drawable element and its descendants, excluding nested drawables and their subtrees, so each nested drawable is drawn in its own call.

### 3. The `paint` event

- A snapshot of every `drawable` element's rendering (its drawable subtree) is recorded on each rendering update. `paint` fires whenever a snapshot would be drawn differently.
- Fires just **after intersection observer steps** in update-the-rendering (after the browser's Paint step; see "Option C" in `design-decisions.md`).
- `event.changedElements` lists the changed `drawable` descendants (`CanvasPaintEvent`).
- **Canvas draw commands in the handler appear in this rendering update. DOM changes in the handler appear in the *next* one.**
- Ordering: fires in **reverse document order** (child frames before parents) and **reverse tree order** within a document, so descendants paint before ancestors (inner canvases before outer ones).
- Implementations may fire spuriously but should avoid it.
- `canvas.requestPaint()` forces one `paint` at the next rendering opportunity, like `requestAnimationFrame()`. Call it each frame for continuous animation.

### 4. Drawing: `drawElementImage` / `texElementSubImage2D` / `drawElementImageToTexture`

```js
ctx.drawElementImage(element, dx, dy);
ctx.drawElementImage(element, dx, dy, dw, dh);
ctx.drawElementImage(element, sx, sy, sw, sh, dx, dy);
ctx.drawElementImage(element, sx, sy, sw, sh, dx, dy, dw, dh);
// each accepts an optional trailing { preserveElementGeometry: boolean }
```

- Draws the **last snapshot** of a `drawable` element and its drawable subtree.
- Rendering starts at the **border box, before CSS transforms**. The canvas CTM applies.
- Source rect params can clip, or add outsets to include ink overflow. Dest params position and scale.
- **Throws** for elements without `drawable`, before the first snapshot, or for elements with another canvas ancestor.
- Returns `undefined`.

WebGL: `gl.texElementSubImage2D(target, level, xoffset, yoffset, element, config?)` (needs pre-allocated storage, sized from `getElementImageDefaultSize`).  
WebGPU: `queue.drawElementImageToTexture({ source, sourceX?, … }, { texture, size? })`.  
Workers: `canvas.captureElementImage(el)` → transferable `ElementImage` → draw on an `OffscreenCanvas`.  
Sizing: `canvas.getElementImageDefaultSize(el)` (also on `OffscreenCanvas`, and also accepts an `ElementImage`) returns `{ width, height }` in canvas grid coordinates. That's the size used when `drawElementImage` gets no `dw`/`dh`.

### 5. Synchronizing DOM and drawing: `updateElementGeometry`

Each drawable element has three pieces of geometry state, used for hit testing, accessibility bounds, and DOM geometry APIs. None of them affect rendering, so changing them never triggers `paint`:

- **Canvas element transform** (`canvasTransform`, a `DOMMatrix`): maps the border box, before CSS transforms, to its drawn location in the canvas. Setting it also gives the element geometry in the accessibility tree.
- **Canvas element clip** (`canvasClip`, a `DOMRect` in the transform's coordinate space; called `clip` before Oct 2026): limits the hit-test region when only part of the element is drawn. Under a rotated or skewed `canvasTransform`, Chrome 157 hit-tests against the clip's axis-aligned bounding box (issue #186).
- **Hit-test order**: the canvas keeps an ordered stack of drawable descendants. Each update puts the element on top unless you pass `preserveHitTestOrder: true` and it's already in the stack. Hit testing goes straight from the canvas to each descendant, skipping intervening clips and transforms.

`clearElementGeometry(el)` resets it. `getElementTransform(el)` reads the transform back (identity if unset).

**2D contexts:** `drawElementImage` calls `updateElementGeometry` automatically with the drawn transform. Opt out with `{ preserveElementGeometry: true }`.  
**WebGL/WebGPU:** you must call `canvas.updateElementGeometry(el, { canvasTransform })` yourself, because the texture-to-screen mapping isn't visible to the canvas API.  
**OffscreenCanvas / workers:** updates are queued, batched in a microtask, posted to the main thread, and applied atomically. Then `elementgeometryupdate` fires on the `<canvas>` with the updated `elements`.

## Basic Example

```html
<canvas style="width: 400px; height: 200px;" content="drawable">
  <form drawable>
    <label for="name">name:</label>
    <input id="name">
  </form>
</canvas>
<script>
  const canvas = document.querySelector('canvas');
  const form = document.querySelector('canvas form');
  const ctx = canvas.getContext('2d');

  canvas.onpaint = () => {
    ctx.reset();
    ctx.drawElementImage(form, 100, 0);
  };

  new ResizeObserver((entries) => {
    canvas.width = entries[0].devicePixelContentBoxSize[0].inlineSize;
    canvas.height = entries[0].devicePixelContentBoxSize[0].blockSize;
  }).observe(canvas, { box: 'device-pixel-content-box' });
</script>
```

## Accessibility

- `content="drawable"` descendants are in the a11y tree like regular DOM.
- If a drawable's geometry hasn't been set (automatically or explicitly), it and its drawable subtree are reported **without geometry**, so assistive tech can filter them, but semantics are kept.
- Content you're not drawing (hidden views, stale content) is still in the a11y tree. Remove it from the DOM or hide it with `aria-hidden="true"` / `inert`.
- Focus rings and carets **are** rendered by `drawElementImage` (and the WebGL/WebGPU equivalents).
- Wrapping elements don't need `drawable` to keep their semantics:

```html
<canvas id="canvas" content="drawable">
  <figure>
    <img drawable id="image" src="…" alt="image alt text" />
    <figcaption drawable id="caption">A caption</figcaption>
  </figure>
</canvas>
<script>
  canvas.onpaint = () => {
    const ctx = canvas.getContext('2d');
    ctx.reset();
    ctx.drawElementImage(image, 0, 0);     // auto geometry → a11y bounds
    ctx.drawElementImage(caption, 0, 200);
  };
</script>
```

## Read-back-allowed rendering (privacy)

Drawn snapshots, and the `paint` event itself (invalidation timing), must not reveal anything author code couldn't already observe. This is what makes pixel read-back safe.

**Excluded (not painted / not invalidated):**
- Cross-origin data in embedded content (`<iframe>`, `<img>`), `url()` references (`background-image`, `clip-path`), cross-origin-tainted `<canvas>`, and SVG references (`<use>`, `<pattern>`, `<feImage>`). Same-origin iframes paint, but cross-origin content inside them doesn't.
- System colors, themes, preferences
- Spelling and grammar markers
- Visited link information
- Pending autofill information
- Subpixel text anti-aliasing
- **Captions and video controls**
- **IME pop-ups and distinctive IME text formatting**

**Not considered sensitive:** find-in-page and text-fragment markers, scrollbar and form-control appearance, caret blink rate, `forced-colors`.

## Migrating from the old API

| Old (≤ mid-2026, Chromium ~147 era) | New |
|---|---|
| `<canvas layoutsubtree>` | `<canvas content="drawable">` |
| any direct child drawable | add `drawable` to every drawn element. Nesting is allowed. |
| `const t = ctx.drawElementImage(el, x, y); el.style.transform = t.toString();` | `ctx.drawElementImage(el, x, y);` (auto-synced, returns `undefined`) |
| `canvas.getElementTransform(el, drawTransform)` + set `style.transform` (3D) | `canvas.updateElementGeometry(el, { canvasTransform })` |
| `gl.texElementImage2D(target, level, ifmt, fmt, type, el)` | allocate with `texImage2D(..., null)`, then `gl.texElementSubImage2D(target, level, 0, 0, el)` |
| `queue.copyElementImageToTexture(el, { texture })` | `queue.drawElementImageToTexture({ source: el }, { texture, size })` |
| `PaintEvent` | `CanvasPaintEvent` |
| `ElementImage.width/height` | removed. Use `canvas.getElementImageDefaultSize(el)` → `{ width, height }` (`double`, canvas grid coordinates) |
| `updateElementGeometry(el, { clip })` | `updateElementGeometry(el, { canvasClip })` |
| worker posts transform back, main thread sets `style.transform` | automatic, plus `canvas.onelementgeometryupdate` |

The migration period is over. Chrome 157, the first version with this on by default, has **none** of the old names, and ignores `layoutsubtree`. Official demos still write both `content="drawable"` and `layoutsubtree` and keep `try/catch` fallbacks for pre-157 builds. Don't copy that into new code unless the user needs those builds.

## Future considerations

- **Auto-updating canvas:** `drawElementImage` would record a placeholder that's replayed on threaded scroll/animation updates without blocking on script. This would allow effects that stay in sync with native scrolling. Viable for 2D, and maybe WebGPU.
