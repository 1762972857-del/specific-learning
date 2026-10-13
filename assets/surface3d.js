/* Optional teaching surfaces on Canvas 2D. Load after draft.js.
   Orthographic projection + average-depth triangle sorting, not a solid 3D engine.
   Page state, controls, labels and teaching overlays stay with the topic. */
(() => {
  'use strict';

  /**
   * Draw z=f(x,y) inside fixed domain {x:[a,b], y:[c,d], z:[e,f]}.
   * camera uses degrees; axisScale changes display units (label unequal units NTS).
   * viewSpan optionally fixes the horizontal/vertical display spans. By default a
   * rotation-independent bounding sphere fits the world box in the canvas.
   * Returns {c,w,h,project,triangles,skippedTriangles}; project returns [px,py,depth]
   * for topic-owned overlays. Invalid/out-of-z-range samples leave holes, never
   * bridge undefined values or flatten peaks onto the range boundary.
   */
  function draw(canvas, {f, domain, camera = {}, mesh = [28, 22],
    axisScale = [1, 1, 1], viewSpan, wire = true} = {}) {
    const D = window.Draft;
    if (!D) throw new Error('surface3d.js requires draft.js');
    const ranges = ['x', 'y', 'z'].map(key => domain?.[key]);
    if (typeof f !== 'function' || ranges.some(r => !Array.isArray(r) || r.length !== 2 || !r.every(Number.isFinite) || r[0] >= r[1])) {
      throw new Error('Surface3D: supply f and finite increasing x/y/z ranges');
    }
    if (!Array.isArray(mesh) || mesh.length !== 2 || !mesh.every(n => Number.isInteger(n) && n > 0) ||
      !Array.isArray(axisScale) || axisScale.length !== 3 || !axisScale.every(n => Number.isFinite(n) && n > 0)) {
      throw new Error('Surface3D: mesh needs two positive integers; axisScale needs three positive numbers');
    }
    const yaw = camera.yaw ?? -55, pitch = camera.pitch ?? 28;
    if (![yaw, pitch].every(Number.isFinite)) throw new Error('Surface3D: camera angles must be finite');
    const diameter = Math.hypot(...ranges.map((r, i) => (r[1] - r[0]) * axisScale[i]));
    const span = viewSpan ?? [diameter, diameter];
    if (!Array.isArray(span) || span.length !== 2 || !span.every(n => Number.isFinite(n) && n > 0)) {
      throw new Error('Surface3D: viewSpan needs two positive numbers');
    }
    const {c, w, h} = D.setup(canvas), K = D.colors();
    const scale = Math.max(0, Math.min((w - 62) / span[0], (h - 94) / span[1]));
    const center = ranges.map(r => (r[0] + r[1]) / 2), a = yaw * Math.PI / 180, b = pitch * Math.PI / 180;
    function project(x, y, z) {
      const xx = (x - center[0]) * axisScale[0], yy = (y - center[1]) * axisScale[1], zz = (z - center[2]) * axisScale[2];
      const horizontal = xx * Math.cos(a) - yy * Math.sin(a), forward = xx * Math.sin(a) + yy * Math.cos(a);
      return [w / 2 + scale * horizontal, h * .48 + scale * (forward * Math.sin(b) - zz * Math.cos(b)),
        forward * Math.cos(b) + zz * Math.sin(b)];
    }
    const [nx, ny] = mesh, [[x0, x1], [y0, y1], [z0, z1]] = ranges;
    const vertices = Array.from({length:ny + 1}, (_, j) => Array.from({length:nx + 1}, (_, i) => {
      const x = x0 + (x1 - x0) * i / nx, y = y0 + (y1 - y0) * j / ny, z = f(x, y);
      return Number.isFinite(z) && z >= z0 && z <= z1 ? project(x, y, z) : null;
    }));
    const faces = [];
    let skippedTriangles = 0;
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const q = [vertices[j][i], vertices[j][i + 1], vertices[j + 1][i + 1], vertices[j + 1][i]];
      for (const indices of [[0, 1, 2], [0, 2, 3]]) {
        const v = indices.map(k => q[k]);
        if (v.some(p => p === null)) { skippedTriangles++; continue; }
        faces.push({v, depth:v.reduce((s, p) => s + p[2], 0) / 3});
      }
    }
    faces.sort((a, b) => a.depth - b.depth);
    c.save();
    for (const face of faces) {
      c.beginPath(); face.v.forEach((p, i) => i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1])); c.closePath();
      c.fillStyle = K.paper2; c.fill();
      if (wire) { c.strokeStyle = K.ink3; c.lineWidth = .55; c.stroke(); }
    }
    c.restore();
    return {c, w, h, project, triangles:faces.length, skippedTriangles};
  }

  window.Surface3D = {draw};
})();
