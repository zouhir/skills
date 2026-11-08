---
title: Open Questions
order: 5
---

# Open Questions & Issues

_Synced from [`WICG/html-in-canvas` issues](https://github.com/WICG/html-in-canvas/issues) on 2026-10-03._

## Resolved since the April 2026 snapshot

These are closed or superseded by the Aug–Sep 2026 API changes:
- **#94 Hit testing and layer ordering:** solved by the canvas hit-test stack in `updateElementGeometry` (`preserveHitTestOrder`). Draw order sets hit order automatically in 2D.
- **#33 texHTMLElement should be texSubImage2D-like:** now `texElementSubImage2D`, with no allocation.
- **#71 Interactive WebGL demo:** the WebGL demo is now an interactive flipping card that uses `updateElementGeometry`.
- **#48 `display: contents` root fails to draw:** superseded. Drawn elements need `drawable` and generated boxes, so put `drawable` on an element that has a box.
- **#96, #95 (`changedElements` shape / workers), #88 (`ElementImage` lifetime), #82 (fingerprinting), #47 (blend modes), #31 (animated media), #107 (CSS layout of renderables), #112 (site bug):** closed upstream. The current IDL keeps `changedElements` as a `FrozenArray<Element>`.

## Breaking-change announcements (pinned)

- **[#179](https://github.com/WICG/html-in-canvas/issues/179) `layoutsubtree` → `content=drawable`**
- **[#174](https://github.com/WICG/html-in-canvas/issues/174) `drawElementImageToTexture`, `texElementSubImage2D`, the `drawable` attribute, geometry updates.** This is the full migration guide. Old WebGL/WebGPU names work only during a migration period.

## Still open

### [#171: Allow on-demand paint records for offline rendering](https://github.com/WICG/html-in-canvas/issues/171)
For offline video export you want to change DOM state and get its snapshot *immediately* (a hypothetical `await drawable.recordPaint()`). Today you `requestPaint()` and await the next `paint`, which adds ~8–17 ms per frame at 60 Hz. **Implication:** frame-by-frame export is bound to the display's frame rate for now.

### [#170: Mark ancestors of drawn elements as on-screen](https://github.com/WICG/html-in-canvas/issues/170)
Non-drawable wrappers (e.g. `<figure>` around a drawn `<img>` + `<figcaption>`) are currently reported as off-screen to a11y. Proposal: treat ancestors of visible drawn elements as on-screen.

### [#165: Relax the restriction on video controls and captions](https://github.com/WICG/html-in-canvas/issues/165)
Captions and native video controls are excluded from drawing. Proposal: allow them without user customizations, since authors will otherwise switch to JS players that ignore caption preferences.

### [#151: Responsive canvas sizing](https://github.com/WICG/html-in-canvas/issues/151)
A canvas doesn't size to its drawable content. Today you need a ResizeObserver on the child to resize the canvas.

### [#148: Precise hit testing](https://github.com/WICG/html-in-canvas/issues/148)
Follow-up on the hit-test stack. A per-element projection matrix and reverse-draw-order testing cover common cases. Non-affine or occluded 3D cases may need more.

### [#146: Positioning elements by other corners (e.g. RTL)](https://github.com/WICG/html-in-canvas/issues/146)
`drawElementImage` positions by the top-left. Right- or bottom-anchoring needs manual math with the element's size. Requested for RTL-friendly APIs.

### [#131: Opt-in cross-origin frame pixel access](https://github.com/WICG/html-in-canvas/issues/131)
Something like `<iframe crossorigin>` that would let an embeddee opt in to being drawn. Not available today, so cross-origin frames render blank.

### [#126: Make `<canvas>` optional](https://github.com/WICG/html-in-canvas/issues/126)
Proposal to apply shaders to page HTML via CSS without wrapping it in a `<canvas>`.

### [#85: Add `removedElements` to the `paint` event](https://github.com/WICG/html-in-canvas/issues/85)
For granular redraw. Today you track removals yourself.

### [#81: Use case: DOM capture / screenshot library (snapdom)](https://github.com/WICG/html-in-canvas/issues/81)
html2canvas-style libraries evaluating `drawElementImage` as a backend.

### [#79: `backdrop-filter` using canvas content as the backdrop root](https://github.com/WICG/html-in-canvas/issues/79)
Not supported. `backdrop-filter` on a drawable doesn't see pixels already in the canvas.

### [#77: Surface when cross-origin content has been omitted](https://github.com/WICG/html-in-canvas/issues/77)
No exception or warning today. Omitted cross-origin content just doesn't paint. A DevTools Issues entry has been proposed.
