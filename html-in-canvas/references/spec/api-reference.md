---
title: API Reference
order: 2
---

# HTML-in-Canvas API Reference

_Synced from the [`WICG/html-in-canvas` README](https://github.com/WICG/html-in-canvas/blob/main/README.md) IDL as of 2026-11-07 (upstream commit `5d9d970`), and checked against the Chromium M157 IDL (the first version with this on by default). They match._

## IDL Definitions

### HTMLCanvasElement Extensions

```idl
dictionary UpdateElementGeometryOptions {
  // If true and the element is already in the canvas's hit testing stack, do
  // nothing. In all other cases, place the element at the top of the stack.
  boolean preserveHitTestOrder = false;

  // The element's canvas clip used for hit testing, in the coordinate space of
  // `canvasTransform`. If omitted, the existing clip is preserved.
  // (Renamed from `clip` in Oct 2026.)
  DOMRectInit canvasClip;

  // Maps the element's border box, before CSS transforms, to the canvas.
  // If omitted, the existing canvas transform is preserved.
  DOMMatrixInit canvasTransform;
};

dictionary ElementImageDefaultSize {
  double width;
  double height;
};

partial interface HTMLCanvasElement {
  [CEReactions, Reflect, ReflectOnly=("fallback", "drawable"),
      ReflectMissing="fallback", ReflectInvalid="fallback"]
      attribute DOMString content;

  attribute EventHandler onpaint;

  void requestPaint();

  ElementImage captureElementImage(Element element);

  // Manual geometry updates (primarily for WebGL/WebGPU).
  void updateElementGeometry(
      (Element or ElementImage) element,
      optional UpdateElementGeometryOptions options = {});
  void clearElementGeometry((Element or ElementImage) element);

  // The element's current canvas transform (border box, before CSS
  // transforms → canvas coordinates), or identity if none has been set.
  [NewObject] DOMMatrix getElementTransform(Element element);

  // Fired when geometry updates that came from an OffscreenCanvas are applied.
  attribute EventHandler onelementgeometryupdate;

  // The default size of the element in canvas grid coordinates.
  ElementImageDefaultSize getElementImageDefaultSize(
      (Element or ElementImage) element);
};
```

| Member | Description |
|--------|-------------|
| `content` | Enumerated attribute: `"fallback"` (default; descendants are fallback content) or `"drawable"` (descendants are laid out). Replaces the old boolean `layoutsubtree`. |
| `onpaint` | Handler for the `paint` event (a `CanvasPaintEvent`). |
| `requestPaint()` | Fire `paint` once at the next rendering opportunity even if nothing changed. Analogous to `requestAnimationFrame()`. |
| `captureElementImage(element)` | Returns the most recent snapshot of a `drawable` element as a transferable `ElementImage`. |
| `getElementImageDefaultSize(element)` | Returns `{ width, height }` (`double`, canvas grid coordinates): the size `drawElementImage` uses when `dw`/`dh` are omitted. Use it to size textures. Accepts an `Element` or `ElementImage`. Replaces the removed `ElementImage.width/height`. |
| `updateElementGeometry(element, options)` | Sets the element's canvas transform (`canvasTransform`), hit-test clip (`canvasClip`), and hit-test order. Required for WebGL/WebGPU; automatic for 2D. |
| `clearElementGeometry(element)` | Clears the state set by `updateElementGeometry`. |
| `getElementTransform(element)` | Reads back the current canvas transform. **Signature changed:** it no longer takes a `drawTransform` argument. |
| `onelementgeometryupdate` | Fires on the `<canvas>` after batched OffscreenCanvas geometry updates are applied. |

### The `drawable` attribute (on descendants)

Not an IDL member of canvas. It's a plain attribute on any descendant of `<canvas content="drawable">`:

- **Required** on every element passed to `drawElementImage` / `texElementSubImage2D` / `drawElementImageToTexture`, including direct children. Drawing an element without it **throws**.
- Implies `isolation: isolate` and makes the element a containing block for all descendants.
- Can be nested. A *drawable subtree* is a drawable element plus its descendants, **excluding** nested `drawable` descendants and their subtrees. So drawing a parent doesn't draw its nested drawables; you draw those separately.

### OffscreenCanvas Extensions

```idl
partial interface OffscreenCanvas {
  // From a worker, only ElementImage may be passed. Updates are batched via a
  // microtask and posted to the main thread; main-thread updates are batched
  // the same way. When applied, `elementgeometryupdate` fires on the
  // associated HTMLCanvasElement.
  void updateElementGeometry(
      (Element or ElementImage) element,
      optional UpdateElementGeometryOptions options = {});
  void clearElementGeometry((Element or ElementImage) element);

  // The default size of the element in canvas grid coordinates.
  ElementImageDefaultSize getElementImageDefaultSize(
      (Element or ElementImage) element);
};
```

### CanvasDrawElementImage Mixin

Included by `CanvasRenderingContext2D` and `OffscreenCanvasRenderingContext2D`.

```idl
dictionary DrawElementImageOptions {
  // If true, don't automatically update the element's geometry.
  // If false, automatically call updateElementGeometry with a canvasTransform
  // mapping the element's border box to the drawn position.
  boolean preserveElementGeometry = false;
};

interface mixin CanvasDrawElementImage {
  void drawElementImage((Element or ElementImage) element,
      unrestricted double dx, unrestricted double dy,
      optional DrawElementImageOptions options = {});

  void drawElementImage((Element or ElementImage) element,
      unrestricted double dx, unrestricted double dy,
      unrestricted double dwidth, unrestricted double dheight,
      optional DrawElementImageOptions options = {});

  void drawElementImage((Element or ElementImage) element,
      unrestricted double sx, unrestricted double sy,
      unrestricted double swidth, unrestricted double sheight,
      unrestricted double dx, unrestricted double dy,
      optional DrawElementImageOptions options = {});

  void drawElementImage((Element or ElementImage) element,
      unrestricted double sx, unrestricted double sy,
      unrestricted double swidth, unrestricted double sheight,
      unrestricted double dx, unrestricted double dy,
      unrestricted double dwidth, unrestricted double dheight,
      optional DrawElementImageOptions options = {});
};
```

| Signature | Description |
|-----------|-------------|
| `(element, dx, dy, opts?)` | Draw at (dx, dy) at the element's default size (`canvas.getElementImageDefaultSize(element)`) |
| `(element, dx, dy, dw, dh, opts?)` | Draw at (dx, dy) scaled to dw × dh |
| `(element, sx, sy, sw, sh, dx, dy, opts?)` | Draw source rect at (dx, dy) |
| `(element, sx, sy, sw, sh, dx, dy, dw, dh, opts?)` | Draw source rect scaled into dest rect |

**Return value: `undefined`.** ⚠️ Breaking change: it used to return a `DOMMatrix` that you assigned to `element.style.transform`. Now geometry is synced automatically (see below).

**Semantics:**
- Draws the **last snapshot** of the element and its drawable subtree.
- Rendering starts at the element's **border box, before CSS transforms**. CSS transforms on the element are not used for drawing. The canvas CTM is applied.
- All coordinates are **canvas grid** coordinates. With a DPR-sized grid, multiply CSS-pixel offsets/sizes by `devicePixelRatio` (the pie-chart demo does `label.offsetWidth * devicePixelRatio`).
- The **source rect** can clip, or use *outsets* to include ink overflow (shadows, outlines) beyond the border box.
- **Throws** if the element doesn't have `drawable`, if no snapshot has been recorded yet, or if the element has another `<canvas>` ancestor (nested canvases).
- By default (2D only), automatically calls `updateElementGeometry` so hit testing, accessibility bounds, and `getBoundingClientRect()` follow the drawn position, and pushes the element to the top of the hit-test stack. Pass `{ preserveElementGeometry: true }` to opt out.

### WebGL Extension

```idl
dictionary WebGLCopyElementImageConfig {
  GLfloat sx;
  GLfloat sy;
  GLfloat swidth;
  GLfloat sheight;
  GLsizei width;
  GLsizei height;
};

partial interface WebGLRenderingContext {
  void texElementSubImage2D(
      GLenum target, GLint level,
      GLint xoffset, GLint yoffset,
      (Element or ElementImage) element,
      optional WebGLCopyElementImageConfig config = {});
};
```

⚠️ Replaces `texElementImage2D`. Like `texSubImage2D`, it **does not allocate storage**. You must allocate first (`texImage2D(..., null)` or `texStorage2D`), sized to `config.width/height` or the element's default size (`canvas.getElementImageDefaultSize(el)`, rounded up). Re-allocate only when the element grows.

```js
const { width, height } = canvas.getElementImageDefaultSize(element);
gl.bindTexture(gl.TEXTURE_2D, tex);
gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8,
              Math.ceil(width), Math.ceil(height), 0,
              gl.RGBA, gl.UNSIGNED_BYTE, null);           // allocate once / on growth
gl.texElementSubImage2D(gl.TEXTURE_2D, 0, 0, 0, element); // every paint
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); // LINEAR, not mipmaps, for text
```

### WebGPU Extension

```idl
// GPUImageCopyTextureTagged extends GPUTexelCopyTextureInfo, which has a
// required `GPUTexture texture` member.
dictionary GPUDrawElementImageDestination : GPUImageCopyTextureTagged {
  GPUExtent3D size;
};

dictionary GPUDrawElementImageSource {
  required (Element or ElementImage) source;
  float sourceX;
  float sourceY;
  float sourceWidth;
  float sourceHeight;
};

partial interface GPUQueue {
  void drawElementImageToTexture(
      GPUDrawElementImageSource source,
      GPUDrawElementImageDestination destination);
};
```

⚠️ Replaces `copyElementImageToTexture`.

```js
device.queue.drawElementImageToTexture(
  { source: element },                                  // optional sourceX/Y/Width/Height
  { texture: gpuTexture, size: { width: w, height: h } });
```

### CanvasPaintEvent

```idl
[Exposed=Window]
interface CanvasPaintEvent : Event {
  constructor(DOMString type, optional CanvasPaintEventInit eventInitDict);
  [SameObject] readonly attribute FrozenArray<Element> changedElements;
};

dictionary CanvasPaintEventInit : EventInit {
  sequence<Element> changedElements = [];
};
```

Renamed from `PaintEvent`. `changedElements` lists the canvas's `drawable` descendants whose snapshot changed.

### ElementImage

```idl
[Exposed=(Window,Worker), Transferable]
interface ElementImage {
  undefined close();
};
```

⚠️ Breaking change (Oct 2026): `ElementImage` no longer has `width` / `height`. Pass the element or the `ElementImage` to `canvas.getElementImageDefaultSize()` (or `offscreenCanvas.getElementImageDefaultSize()` in a worker) instead. The result is a `double` in **canvas grid coordinates**, so use `Math.ceil` when sizing textures.

### ElementGeometryUpdateEvent

```idl
[Exposed=Window]
interface ElementGeometryUpdateEvent : Event {
  constructor(DOMString type,
              optional ElementGeometryUpdateEventInit eventInitDict = {});
  [SameObject] readonly attribute FrozenArray<Element> elements;
};

dictionary ElementGeometryUpdateEventInit : EventInit {
  sequence<Element> elements = [];
};
```

Elements that no longer exist when the event fires are left out of `elements`.

## Common Patterns

### Basic 2D Canvas

```html
<canvas id="canvas" style="width: 400px; height: 200px;" content="drawable">
  <form drawable id="form">
    <label for="name">name:</label>
    <input id="name">
  </form>
</canvas>
<script>
  const ctx = canvas.getContext('2d');
  canvas.onpaint = () => {
    ctx.reset();
    ctx.drawElementImage(form, 100, 0); // geometry/hit testing sync automatically
  };
  new ResizeObserver((entries) => {
    canvas.width = entries[0].devicePixelContentBoxSize[0].inlineSize;
    canvas.height = entries[0].devicePixelContentBoxSize[0].blockSize;
  }).observe(canvas, { box: 'device-pixel-content-box' });
</script>
```

### Nested drawables

```html
<canvas id="canvas" content="drawable">
  <div drawable id="poem">
    Roses are red … And so are <span drawable id="sparkle">you</span>.
  </div>
</canvas>
<script>
  canvas.onpaint = () => {
    ctx.reset();
    ctx.drawElementImage(poem, 0, 0);       // does NOT include #sparkle
    const r = rectInCanvasGrid(sparkle);    // offsetLeft/Top walk up to closest('[drawable], canvas'), × dpr
    ctx.drawElementImage(sparkle, r.x, r.y, r.width, r.height);
  };
</script>
```

The nested element is skipped when its drawable ancestor is drawn. Put it back at its in-flow position yourself (or anywhere else). The `nested-sparkles` demo uses `GeometryUtils.convertRectFromNode` when it's available and falls back to summing `offsetLeft/offsetTop`.

### Manual geometry (custom 2D hit region)

```js
ctx.drawElementImage(el, x, y, { preserveElementGeometry: true });
canvas.updateElementGeometry(el, {
  canvasTransform: myTransform,                 // border box → canvas
  canvasClip: new DOMRect(0, 0, visibleW, visibleH),  // only part of it was drawn
});
```

Under a rotated or skewed `canvasTransform`, Chrome 157 hit-tests against the clip's axis-aligned bounding box rather than the transformed rectangle (issue #186). Don't rely on precise clipped hit regions for rotated elements.

### OffscreenCanvas with Worker

```js
// Main thread
const offscreen = canvas.transferControlToOffscreen();
worker.postMessage({ canvas: offscreen }, [offscreen]);

canvas.onpaint = () => {
  const img = canvas.captureElementImage(form);
  worker.postMessage({ form: img }, [img]);
};
canvas.onelementgeometryupdate = (e) => {
  // e.elements now have updated canvas transforms
  // (e.g. form.getBoundingClientRect() reflects the worker's draw offset).
};

// Worker
self.onmessage = (e) => {
  if (e.data.canvas) ctx = e.data.canvas.getContext('2d');
  if (e.data.form) {
    ctx.reset();
    ctx.drawElementImage(e.data.form, 100, 0); // auto geometry → batched → main thread
  }
};
```

No manual transform round-trip anymore. The worker's draw call queues the geometry update, and the main thread applies it and fires `elementgeometryupdate`.

### WebGL texture + geometry

```js
canvas.onpaint = () => {
  if (!allocated) { /* texImage2D(..., null) sized from getElementImageDefaultSize */ allocated = true; }
  gl.texElementSubImage2D(gl.TEXTURE_2D, 0, 0, 0, element);
  drawScene();
  canvas.updateElementGeometry(element, { canvasTransform: elementToCanvasCss });
};
```

### WebGPU texture + geometry

```js
canvas.onpaint = () => {
  device.queue.drawElementImageToTexture(
    { source: element }, { texture, size: { width, height } });
  canvas.updateElementGeometry(element, { canvasTransform: elementToCanvasCss });
};
```

For 3D, `canvasTransform` maps the element's border box into the canvas's **CSS** coordinate space. The WebGL demo projects the quad's corners through its model-view-projection matrix, converts GL clip space (−1…1) to canvas CSS pixels, and builds a scale+translate `DOMMatrix`.

### Device Pixel Ratio Handling

Size the canvas grid to device pixels:

```js
new ResizeObserver(([entry]) => {
  canvas.width = entry.devicePixelContentBoxSize[0].inlineSize;
  canvas.height = entry.devicePixelContentBoxSize[0].blockSize;
}).observe(canvas, { box: 'device-pixel-content-box' });
```

Then express `drawElementImage` coordinates in grid pixels (CSS px × `devicePixelRatio`). For OffscreenCanvas, where you can't set the size directly on the element, the upstream example posts `contentRect.width * devicePixelRatio` to the worker and calls `canvas.requestPaint()`.
