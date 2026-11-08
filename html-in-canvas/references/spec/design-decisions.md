---
title: Design Decisions
order: 3
---

# Design Decisions & Rationale

## Why `content="drawable"` instead of `layoutsubtree`?

The opt-in is now an enumerated attribute: `content="fallback"` (default) or `content="drawable"`. It names what the attribute controls (how canvas content is treated) and leaves room for more modes later. Without it, canvas descendants are classic fallback content. With it, they're laid out, take part in accessibility, and become hit-testable once their geometry is set. They stay invisible until drawn.

The dual role is unchanged: the drawn elements *are* the accessibility tree, so the two can't drift apart.

## Why a per-element `drawable` attribute (instead of "direct children only")?

The old API only let you draw direct children of the canvas. That forced authors to flatten their markup into an unrelated list of top-level elements, which broke semantics like `<figure>` → `<img>` + `<figcaption>`.

`drawable` fixes this:
- **Natural DOM structure.** Draw any descendant and keep semantic wrappers. Wrappers don't need `drawable` themselves.
- **Drawing flexibility.** Each drawable is captured independently, so it isn't constrained by its ancestors' stacking or clipping. Drawing an element captures its subtree *except* nested drawables, so nested parts can be drawn or animated separately (see the `nested-sparkles` demo).
- **Explicit intent.** The browser knows exactly which elements need snapshots.

`drawable` implies `isolation: isolate` and a containing block for descendants, so each drawable's rendering is self-contained.

## Why CSS transforms on source elements are ignored for drawing

Drawing starts at the border box *before* CSS transforms. The canvas CTM controls placement. Applying CSS transforms too would double-position the element. The drawn position is tracked separately as the element's **canvas element transform**, which is geometry state, not a CSS property.

## Why automatic geometry instead of returning a `DOMMatrix`?

Previously `drawElementImage` returned a `DOMMatrix` and authors had to write it back to `element.style.transform`. This had problems:
- It was easy to forget, which silently broke hit testing, selection, and a11y bounds.
- It overloaded the author-visible `transform` style, which conflicts with real CSS transforms and the transform-origin math.
- It said nothing about **layer order**, which hit testing needs (issue #94).

Now each drawable has internal geometry state (canvas transform, hit-test clip, position in the canvas's hit-test stack). In 2D, `drawElementImage` sets this automatically. Later draws go on top, matching the painter's order. `{ preserveElementGeometry: true }` opts out for custom cases.

3D contexts can't be automatic because the texture-to-screen mapping lives in the author's shaders. So `updateElementGeometry` is public, and WebGL/WebGPU callers pass a `canvasTransform`.

Geometry state doesn't affect rendering, so changing it never fires `paint`.

## Why batch OffscreenCanvas geometry updates?

Workers can't touch the DOM synchronously. Geometry updates from an `OffscreenCanvas` are queued, batched in a microtask, posted to the main thread, and applied atomically. Then `elementgeometryupdate` fires. Batching (like observer APIs) means no other task sees a half-applied set of updates. It also replaces the old pattern where the worker posted transforms back by hand.

## Why `texElementSubImage2D` (sub-image) rather than `texElementImage2D`?

Raised in issue #33 (greggman). `texImage2D` both allocates and uploads, so it can't target immutable `texStorage2D` textures, which are more efficient. The sub-image form only uploads: you allocate once (sized from `canvas.getElementImageDefaultSize(el)`), upload repeatedly, and can place the element at an `xoffset`/`yoffset` inside a larger atlas.

## Why `drawElementImageToTexture` with dictionaries (WebGPU)?

It was renamed from `copyElementImageToTexture` and reshaped into `GPUDrawElementImageSource` / `GPUDrawElementImageDestination` dictionaries, matching WebGPU conventions (`copyExternalImageToTexture`-style `source` / `texture` / `size`). "Draw" signals that it rasterizes a snapshot rather than copying existing texels.

## Why `paint` fires after Paint (Option C)

- **Option A (resize-observer timing, looping):** would need a synchronous Paint of drawables (expensive, hard in Gecko) or placeholder recording. Placeholders deadlock WebGL, because many GL calls like `getError()` force a flush.
- **Option B (after Paint, looping):** even more rendering steps per loop.
- **Option C (after Paint, once per frame), chosen:** the rendering update is locked in before `paint` runs, except for the canvas's own drawn content. DOM changes made in `paint` apply to the *next* update.

Events fire in reverse tree order (and child frames before parents), so inner drawables and nested canvases are up to date before outer ones draw them.

## Why `captureElementImage` for workers?

Workers have no DOM. A transferable `ElementImage` snapshot fits the `ImageBitmap` pattern. Workers pass it wherever an `Element` is accepted, and from a worker only `ElementImage` may be passed to `updateElementGeometry`.

## Why `getElementImageDefaultSize()` instead of `ElementImage.width/height`?

Sizing used to require capturing a snapshot (`captureElementImage(el).width`) even on the main thread, just to allocate a texture. In Oct 2026 the size moved to a canvas method, `getElementImageDefaultSize(Element or ElementImage)`, on both `HTMLCanvasElement` and `OffscreenCanvas`, and `ElementImage` was reduced to `close()`. You can now size directly from the element, and workers can still ask with an `ElementImage`. In the same change, `clip` was renamed `canvasClip` to match `canvasTransform`.

## Why not `foreignObject` or `html2canvas`?

`foreignObject` lives in SVG's rendering model, with no canvas CTM, WebGL, or WebGPU integration, and it isn't interactive. `html2canvas`-style libraries re-implement rendering in JS, so they're incomplete, slow, inaccurate, heavy, and static. HTML-in-Canvas uses the real engine and keeps interactivity.

## Privacy model (read-back-allowed rendering)

WebGL and WebGPU always allow pixel read-back, so anything drawn must already be observable by script. Both pixels and `paint` timing are covered. Cross-origin content, system colors/themes, spelling markers, visited links, pending autofill, subpixel AA, captions/video controls, and IME UI are excluded. Form-control appearance, caret blink rate, find-in-page markers, and `forced-colors` are considered already observable.

The captions/video-controls exclusion is being reconsidered (issue #165): authors may just switch to JS players that ignore user caption preferences.
