# Native teaching surfaces

For smooth bivariate surfaces, slices, or tangent planes, load `assets/draft.js` before `assets/surface3d.js`. Working example with overlays: `templates/partial-derivatives/viz/partial-derivatives.html` (its heat-rod model is not required elsewhere).

## Interface and responsibilities

```js
const {c, w, h, project, skippedTriangles} = Surface3D.draw(canvas, {
  f: (x, y) => MODEL.f(x, y, P),
  domain: {x: MODEL.domain.x, y: MODEL.domain.y, z: [-1.1, 1.1]},
  camera: {yaw: state.yaw, pitch: state.pitch}, // Degrees, not radians
  mesh: [60, 60], // Cells in each direction, not sample-point counts
  axisScale: [1, 1, 1],
  wire: true
});
// Draw explanatory overlays after the surface. They do not establish occlusion.
const points = Array.from({length:101}, (_, i) => {
  const x = MODEL.domain.x[0] + (MODEL.domain.x[1] - MODEL.domain.x[0]) * i / 100;
  return project(x, state.y0, MODEL.f(x, state.y0, P));
});
Draft.path(c, points, {color: Draft.colors().accent, width: 2.3});
```

`surface3d.js` owns fixed world bounds, orthographic projection, sampling, and face sorting. The page owns `state`, `update()`, dragging/keyboard/exact inputs, axis labels, and readings. `project(x,y,z)` returns screen coordinates and sorting depth; use Draft helpers for probes, tangent lines, or planes. Model formulas and numerical verification stay outside the renderer.

`axisScale` is display length per data unit. By default, scaling uses the bounding sphere of the whole fixed world box and does not refit with parameters or camera rotation. A fixed `viewSpan:[horizontalSpan,verticalSpan]` reproduces a chosen composition, but a small span may clip rotated geometry.

## Applicability

- For smooth, single-valued `z=f(x,y)` on finite domains. Triangles touching nonfinite or out-of-range z are skipped and counted in `skippedTriangles`; explain missing geometry instead of presenting a complete surface. Unsampled discontinuities go undetected; partition singular/discontinuous domains explicitly.
- Faces sort by mean depth. No per-pixel occlusion, intersecting transparency, lighting, hover picking, perspective camera, or volume rendering; overlays must not imply physical occlusion.
- Compute readings from the model; the mesh only approximates shape. Choose mesh density for the function's variation and compare refined meshes for undersampling; the default is not accurate for arbitrary functions.

- Overlays (slices, probes, vertical sections, tangent lines) use the interface above; a labeled vertical section is `Draft.poly(c, corners.map(p=>project(...p)), ...)`. Fix z bounds and mesh density per function.
