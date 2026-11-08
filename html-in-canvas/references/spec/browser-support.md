---
title: Browser Support
order: 6
---

# Browser Support

_Synced from the [`WICG/html-in-canvas` README](https://github.com/WICG/html-in-canvas/blob/main/README.md) on 2026-10-03._

## Status

This is a living explainer that's continuously updated as feedback comes in. The APIs are implemented behind flags in Chromium.

## Developer Trial (Chrome Canary)

Enable **both** flags, then relaunch:

1. `chrome://flags/#canvas-draw-element`
2. `chrome://flags/#enable-experimental-web-platform-features`

(The second flag became a requirement in the Sept 2026 dev-trial update. Earlier docs only listed the first.)

Chrome blocks click-through to `chrome://` URLs, so copy and paste them.

Upstream wants feedback on: what content works and what fails (and which failures matter most), and how the feature interacts with accessibility.

- API feedback: https://github.com/WICG/html-in-canvas/issues/new
- Chromium implementation bugs: https://issues.chromium.org/issues/new?component=1456440&template=0

## API generations in the wild

| Build era | Canvas opt-in | Drawn elements | `drawElementImage` returns | WebGL | WebGPU |
|---|---|---|---|---|---|
| Old (e.g. Chromium 147, Brave 1.89) | `layoutsubtree` | direct children only | `DOMMatrix` (write to `style.transform`) | `texElementImage2D` | `copyElementImageToTexture` |
| Current Canary (≥ Sept 2026) | `content="drawable"` | `drawable` attr, nestable | `undefined` (auto geometry) | `texElementSubImage2D` | `drawElementImageToTexture` |

The old WebGL/WebGPU names still work "during a migration period" and will be removed. Feature-detect:

```js
const isNewApi = 'updateElementGeometry' in HTMLCanvasElement.prototype;
```

and mark up for both generations, as the official demos do:

```html
<canvas content="drawable" layoutsubtree>
  <div drawable id="el">…</div>
</canvas>
```

## Other browsers

- **Brave:** Stable ≥ 1.89.132 (Chromium 147) exposes the **old** API behind `brave://flags/#canvas-draw-element`. Newer Brave builds pick up the new API once their Chromium base includes it. Check the flag page and feature-detect.
- **Edge / other Chromium forks:** follow their Chromium milestone. Same flags.
- **Firefox:** no implementation announced.
- **Safari / WebKit:** no implementation announced.

## Live demos

https://wicg.github.io/html-in-canvas/Examples/ (complex-text, pie-chart, nested-sparkles, webGL, webgpu-jelly-slider)
