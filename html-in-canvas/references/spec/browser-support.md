---
title: Browser Support
order: 6
---

# Browser Support

_Checked against Chromium source (`chrome/VERSION` 159 trunk and the M157 release branch `branch-heads/8103`), chromestatus, and the [`WICG/html-in-canvas` README](https://github.com/WICG/html-in-canvas/blob/main/README.md) on 2026-11-07._

## Status

- **Chrome 157+ (stable 2026-11-03): enabled by default.** No flags. Chromium flipped the `CanvasDrawElement` runtime feature to `status: "stable"` in commit `e6d4a6c87` (2026-10-09, after an approved Intent to Ship; [crbug 500967896](https://crbug.com/500967896), [chromestatus 5172548013916160](https://chromestatus.com/feature/5172548013916160)).
- **Spec:** still a WICG explainer. The HTML spec PR [whatwg/html#11588](https://github.com/whatwg/html/pull/11588) is open, so details can still change.
- Upstream removed the "Developer Trial Information" section from the README on 2026-10-30 (`5d9d970`), and closed the two pinned breaking-change announcements (#174, #179) on 2026-11-05. The migration period is over.

## Timeline

| Chrome | What shipped |
|---|---|
| M138 | Developer trial begins (behind `chrome://flags/#canvas-draw-element`). Old API shape. |
| M148–M150 | Origin trial (`HTMLInCanvas`). Old API shape. |
| ~M154–M156 (Canary/Dev, Aug–Oct 2026) | Transitional: the new API shape landed piecemeal behind **both** `#canvas-draw-element` and `#enable-experimental-web-platform-features`, with old names kept as fallbacks. |
| M157 (2026-11-03) | Enabled by default. **Only the new shape.** `layoutsubtree`, the `DOMMatrix` return value, `getElementTransform(el, drawTransform)`, `texElementImage2D`, `copyElementImageToTexture`, and `ElementImage.width/height` are all gone. |

## Verified API surface in Chrome 157

Read from the M157 branch IDL. It matches the explainer at `5d9d970`:

- `HTMLCanvasElement`: `content` (`"fallback"` | `"drawable"`), `onpaint`, `onelementgeometryupdate`, `requestPaint()`, `getElementImageDefaultSize()`, `getElementTransform()`, `captureElementImage()`, `updateElementGeometry()`, `clearElementGeometry()`
- `OffscreenCanvas`: `getElementImageDefaultSize()`, `updateElementGeometry()`, `clearElementGeometry()`
- `CanvasRenderingContext2D` / `OffscreenCanvasRenderingContext2D`: the four `drawElementImage` overloads
- `UpdateElementGeometryOptions`: `preserveHitTestOrder`, `canvasClip`, `canvasTransform`
- `ElementImage`: `close()` only
- WebGL: `texElementSubImage2D`. WebGPU: `GPUQueue.drawElementImageToTexture`
- `CanvasPaintEvent.changedElements`, `ElementGeometryUpdateEvent.elements`

## API generations in the wild

| Build | Canvas opt-in | Drawn elements | `drawElementImage` returns | Texture sizing | WebGL | WebGPU |
|---|---|---|---|---|---|---|
| Old (≤ ~M153 behind flags, and the M148–150 origin trial; e.g. Chromium 147, Brave 1.89) | `layoutsubtree` | direct children only | `DOMMatrix` (write to `style.transform`) | `ElementImage.width/height` | `texElementImage2D` | `copyElementImageToTexture` |
| Transitional (~M154–M156 behind flags) | `content="drawable"` | `drawable` attr, nestable | `undefined` (auto geometry) | `ElementImage.width/height` | `texElementSubImage2D` | `drawElementImageToTexture` |
| **Chrome 157+ (current)** | `content="drawable"` | `drawable` attr, nestable | `undefined` (auto geometry) | `getElementImageDefaultSize(el)` | `texElementSubImage2D` | `drawElementImageToTexture` |

Feature-detect:

```js
const supported = 'drawElementImage' in CanvasRenderingContext2D.prototype;
const isCurrentApi = 'getElementImageDefaultSize' in HTMLCanvasElement.prototype; // Chrome 157+ shape
```

The official demos still write `<canvas content="drawable" layoutsubtree>` and keep `try/catch` fallbacks to the old names. Chrome 157 ignores `layoutsubtree`. Only add it, or the fallbacks, if the user explicitly needs pre-157 builds.

## Other browsers

- **Edge / Opera / other Chromium forks:** follow their Chromium milestone. On by default once they're on Chromium 157.
- **Brave:** same, once its Chromium base reaches 157. Older Brave (e.g. 1.89 on Chromium 147) has only the old API behind `brave://flags/#canvas-draw-element`.
- **Firefox:** not implemented. Position request [mozilla/standards-positions#1076](https://github.com/mozilla/standards-positions/issues/1076) is open, with no position yet.
- **Safari / WebKit:** not implemented. Position request [WebKit/standards-positions#630](https://github.com/WebKit/standards-positions/issues/630) is open, with no position yet.

Production code must feature-detect and keep a non-canvas fallback (plain DOM) for Firefox, Safari, and older Chromium.

## Feedback

- API feedback: https://github.com/WICG/html-in-canvas/issues/new
- Chromium implementation bugs: https://issues.chromium.org/issues/new?component=1456440&template=0

## Live demos

https://wicg.github.io/html-in-canvas/Examples/ (complex-text, pie-chart, nested-sparkles, webGL, webgpu-jelly-slider)
