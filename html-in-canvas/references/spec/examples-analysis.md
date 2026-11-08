---
title: Examples Analysis
order: 4
---

# Official Examples Analysis

All examples live at https://wicg.github.io/html-in-canvas/Examples/ (synced 2026-10-03, after the `content=drawable` / `drawable` update).

**Transitional markup:** every official demo currently writes `<canvas content="drawable" layoutsubtree>` with a comment: "content=drawable is the new API and layoutsubtree has been left" so they still work on older builds. The WebGL and WebGPU demos also `try` the new method names and fall back to the old ones.

## 1. Complex Text (complex-text.html)

**What it demonstrates:** Rotated rich text (emoji, RTL Persian, vertical Chinese, inline `<img>`/`<svg>`, a link) drawn with one call.

```html
<canvas id="canvas" content="drawable" layoutsubtree>
  <div id="draw_element" drawable style="width: 550px;">Hello from …</div>
</canvas>
```
```js
canvas.onpaint = () => {
  ctx.reset();
  ctx.rotate((15 * Math.PI) / 180);
  ctx.translate(80 * devicePixelRatio, -20 * devicePixelRatio);
  ctx.drawElementImage(draw_element, 0, 0);   // no transform write-back anymore
};
canvas.requestPaint();
```

**Insight:** The simplest case. Rotation goes through the CTM, and hit testing and link clicks follow it automatically.

---

## 2. Pie Chart (pie-chart.html)

**What it demonstrates:** An accessible pie chart. Labels are focusable `role="listitem"` drawables positioned radially.

```html
<canvas content="drawable" layoutsubtree class="pie" role="list" aria-label="Pie Chart">
  <div drawable class="label" role="listitem" tabindex="0" data-val="0.45" data-color="tomato">…</div>
  …
</canvas>
```
```js
canvas.onpaint = () => {
  ctx.reset();
  const radius = 0.95 * Math.min(canvas.width, canvas.height) / 2;
  ctx.translate(canvas.width / 2, canvas.height / 2);
  let angle = 0, focusedPath = null;
  for (const label of canvas.children) {
    const slice = Number(label.dataset.val) * Math.PI * 2;
    const path = new Path2D(); path.moveTo(0, 0); path.arc(0, 0, radius, angle, angle + slice); path.closePath();
    ctx.fill(path);
    if (document.activeElement === label) focusedPath = path;
    const mid = angle + slice / 2;
    const w = label.offsetWidth * devicePixelRatio, h = label.offsetHeight * devicePixelRatio; // CSS → grid px
    ctx.drawElementImage(label, Math.cos(mid) * radius * 0.6 - w / 2, Math.sin(mid) * radius * 0.6 - h / 2);
    angle += slice;
  }
  if (focusedPath) ctx.drawFocusIfNeeded(focusedPath, document.activeElement);
};
```

**Insight:** The accessibility showcase. Note the `offsetWidth * devicePixelRatio` conversion: draw coordinates are canvas grid pixels. The demo still uses `drawFocusIfNeeded` (but see the SKILL.md gotcha about Brave crashes on older builds).

---

## 3. Nested Sparkles (nested-sparkles.html), new

**What it demonstrates:** Nested drawables. A poem is one drawable, and one word inside it (`<span drawable id="sparkle">`) is a separate drawable with an animated sparkle effect drawn underneath it.

```html
<canvas id="canvas" content="drawable" layoutsubtree>
  <div drawable id="poem">… And so are <span id="sparkle" drawable>you</span>.</div>
</canvas>
```
```js
canvas.onpaint = () => {
  ctx.reset();
  ctx.translate(canvas.width / 3, canvas.height / 5);
  ctx.drawElementImage(poem, 0, 0);               // excludes #sparkle
  const rect = getInFlowRect(sparkle);            // grid coords, relative to closest drawable/canvas
  /* draw random white dots inside rect */
  ctx.drawElementImage(sparkle, rect.x, rect.y, rect.width, rect.height);
  canvas.requestPaint();                          // continuous animation
};

function getInFlowRect(element) {
  let rect = new DOMRect(element.offsetLeft, element.offsetTop, element.offsetWidth, element.offsetHeight);
  const ancestor = element.parentElement.closest('[drawable], canvas');
  if (ancestor.convertRectFromNode !== undefined) {           // GeometryUtils, where available
    rect = ancestor.convertRectFromNode(rect, element.offsetParent).getBounds();
  } else {
    for (let cur = element.offsetParent; cur !== ancestor; cur = cur.offsetParent) {
      rect.x += cur.offsetLeft; rect.y += cur.offsetTop;
    }
  }
  return new DOMRect(rect.x * devicePixelRatio, rect.y * devicePixelRatio,
                     rect.width * devicePixelRatio, rect.height * devicePixelRatio);
}
```

**Insight:** Drawing a parent leaves a hole where its nested drawables are. You put them back yourself, at their in-flow position or anywhere else, with effects in between. This replaced the old "text-input" form demo.

---

## 4. WebGL Card (webGL.html), rewritten

**What it demonstrates:** An **interactive** 3D card that flips. The front has a language picker (`#choice`, checkboxes/radios), and the back shows a message in English, Spanish, Hindi, or Korean.

**Key techniques:**
- Every drawable child has `drawable`. The message divs start `inert`, and `setInert()` toggles `inert` on whichever face isn't visible, so only the visible face is focusable and clickable.
- Textures start empty (`createEmptyTexture`). `onpaint` updates a texture only when its element is in `event.changedElements` (or the language changed).
- **Texture upload (new API):**
  ```js
  const img = gl.canvas.captureElementImage(element);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, img.width, img.height, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
  gl.texElementSubImage2D(gl.TEXTURE_2D, 0, 0, 0, element);
  ```
  with `try/catch` fallbacks to `texElementImage2D(target, level, ifmt, fmt, type, el)` and an even older `texElementImage2D(target, ifmt, el)`.
- `TEXTURE_MIN_FILTER = LINEAR`, `CLAMP_TO_EDGE`.
- **Geometry sync:** after drawing, it projects the quad's top-left and bottom-right through the model-to-screen matrix, maps GL clip space (−1…1) to canvas CSS px, and builds a `DOMMatrix` (`a`/`d` = scale from the 400px element, `e`/`f` = offset):
  ```js
  if (canvas.updateElementGeometry !== undefined)
    canvas.updateElementGeometry(visible_elmt, { canvasTransform: canvas_transform });
  else
    visible_elmt.style.transform = canvas_transform.toString();   // old builds
  ```
- `onpaint` calls `canvas.requestPaint()` to loop. The ResizeObserver records both `devicePixelContentBoxSize` (grid) and `contentBoxSize` (CSS size, used for the geometry math).

**Insight:** This resolves the old issue #71 ("replace webGL demo with one that is interactive"). The pattern for interactive 3D HTML is: draw to a texture, then `updateElementGeometry` with the projected screen rect, then `inert` the faces you can't see. You no longer need to raycast and re-dispatch events for planar, affine-projected surfaces.

A separate experimental three.js integration lives at https://github.com/mrdoob/three.js/pull/31233 (`htmltexture` branch).

---

## 5. WebGPU Jelly Slider (webgpu-jelly-slider/)

**What it demonstrates:** A real `<input type="range">` drives a TypeGPU ray-marched jelly. The value `<div>` is uploaded as a GPU texture.

```html
<canvas content="drawable" layoutsubtree>
  <input drawable id="slider" type="range" min="0" max="100" step="1" value="100" />
  <div drawable id="value" inert="true"></div>
</canvas>
```
```ts
canvas.onpaint = () => {
  try {
    root.device.queue.drawElementImageToTexture(
      { source: valueElement },
      { texture: valueRawTexture, size: { width, height } });
  } catch {
    // old: copyElementImageToTexture({source}, {destination:{texture}, width, height})
    // older: copyElementImageToTexture(el, width, height, {texture})
  }
  const t = new DOMMatrix().translate(x, y);           // hard-coded for now (TODO in source)
  if (canvas.updateElementGeometry !== undefined) {
    canvas.updateElementGeometry(valueElement,  { canvasTransform: t });
    canvas.updateElementGeometry(sliderElement, { canvasTransform: t });
  } else {
    sliderElement.style.transform = valueElement.style.transform = `translate(${x}px, ${y}px)`;
  }
};
canvas.requestPaint();
```

**Insight:** It mixes a native accessible control with GPU rendering. `requestPaint()` is called on slider input. It respects `prefers-reduced-motion` and `prefers-contrast`.

---

## Pattern Summary

| Example | Context | Draw API | Geometry sync | Interactive |
|---------|---------|----------|---------------|-------------|
| Complex Text | 2D | `drawElementImage` | automatic | links |
| Pie Chart | 2D | `drawElementImage` | automatic | focus/tab |
| Nested Sparkles | 2D | `drawElementImage` ×2 (nested) | automatic | n/a (animated) |
| WebGL Card | WebGL2 | `texElementSubImage2D` | `updateElementGeometry` | yes (form, flip) |
| Jelly Slider | WebGPU | `drawElementImageToTexture` | `updateElementGeometry` | yes (range input) |

## Common Boilerplate (2D)

```js
const ctx = canvas.getContext('2d');

canvas.onpaint = () => {
  ctx.reset();
  // ... ctx.drawElementImage(drawableEl, x, y) in canvas grid px ...
};

canvas.requestPaint(); // initial paint

new ResizeObserver(([entry]) => {
  canvas.width = entry.devicePixelContentBoxSize[0].inlineSize;
  canvas.height = entry.devicePixelContentBoxSize[0].blockSize;
}).observe(canvas, { box: 'device-pixel-content-box' });
```
