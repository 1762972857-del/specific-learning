/* Drafting primitives shared by topic labs: canvas plotting in drawing
   conventions, parameter binding, pointer drag, a fixed-step clock, slide-rule
   sliders and the Markdown reader. Plain browser JS, no dependencies.
   Colours come from draft.css; never hard-code them here or in pages. */
(() => {
  'use strict';
  let palette;
  function colors() {
    if (palette) return palette;
    const s = getComputedStyle(document.documentElement), v = n => s.getPropertyValue(n).trim();
    return palette = {paper:v('--paper'), paper2:v('--paper-2'), ink:v('--ink'), ink2:v('--ink-2'), ink3:v('--ink-3'), ink4:v('--ink-4'),
      accent:v('--accent'), accentInk:v('--accent-ink'), accentWash:v('--accent-wash'), fog:v('--fog'), fogWash:v('--fog-wash'),
      mono:v('--mono'), sans:v('--sans'), serif:v('--serif')};
  }

  // ---------------------------------------------------------------- scales
  function step(span, count = 5) {
    const raw = span / Math.max(1, count), p = 10 ** Math.floor(Math.log10(raw)), f = raw / p;
    return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p;
  }
  /** Round tick values covering [min, max]. */
  function ticks(min, max, count = 5) {
    const s = step(max - min, count), values = [];
    for (let i = Math.ceil(min / s - 1e-9); i * s <= max + s * 1e-9; i++) values.push(+(i * s).toPrecision(12));
    return {values, step:s};
  }
  /** Format v with as many decimals as the tick step needs. */
  function fmt(v, s) {
    const d = Math.max(0, -Math.floor(Math.log10(s) + 1e-9));
    return (Math.abs(v) < s * 1e-6 ? 0 : v).toFixed(d);
  }
  /** Size a canvas to its CSS box at device resolution and clear it. */
  function setup(canvas) {
    const w = canvas.clientWidth, h = canvas.clientHeight, d = Math.min(devicePixelRatio || 1, 2);
    if (canvas.width !== Math.round(w * d) || canvas.height !== Math.round(h * d)) {
      canvas.width = Math.round(w * d); canvas.height = Math.round(h * d);
    }
    const c = canvas.getContext('2d');
    c.setTransform(d, 0, 0, d, 0, 0); c.clearRect(0, 0, w, h); c.lineJoin = 'round';
    return {c, w, h};
  }
  /** Pixel box {l,t,r,b} inside an element (or a canvas filling it), relative to `origin`'s top-left. */
  function box(el, pad = {}, origin = el) {
    const o = origin.getBoundingClientRect(), r = el.getBoundingClientRect(), p = {t:30, r:20, b:40, l:56, ...pad};
    return {l:r.left - o.left + p.l, t:r.top - o.top + p.t, r:r.right - o.left - p.r, b:r.bottom - o.top - p.b};
  }
  /**
   * Map data to a pixel box. Log axes clamp at their lower bound.
   * equal:true keeps one data unit the same length on both axes (geometry, optics,
   * vectors): the shorter span is widened about its centre, and the frame reports
   * the ranges actually used in .x/.y.
   */
  function frame(bx, [x0, x1], [y0, y1], {logX = false, logY = false, equal = false} = {}) {
    if (equal) {
      const w = bx.r - bx.l, h = bx.b - bx.t, ppu = Math.min(w / (x1 - x0), h / (y1 - y0));
      const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, hx = w / ppu / 2, hy = h / ppu / 2;
      [x0, x1, y0, y1] = [cx - hx, cx + hx, cy - hy, cy + hy];
    }
    const tx = logX ? v => Math.log10(Math.max(v, x0)) : v => v, ty = logY ? v => Math.log10(Math.max(v, y0)) : v => v;
    const a0 = tx(x0), a1 = tx(x1), b0 = ty(y0), b1 = ty(y1);
    const X = v => bx.l + (tx(v) - a0) / (a1 - a0) * (bx.r - bx.l), Y = v => bx.b - (ty(v) - b0) / (b1 - b0) * (bx.b - bx.t);
    return {box:bx, x:[x0, x1], y:[y0, y1], logX, logY, equal, X, Y,
      // Inverse maps (linear axes only) for pointer input.
      ix: px => x0 + (px - bx.l) / (bx.r - bx.l) * (x1 - x0), iy: py => y0 + (bx.b - py) / (bx.b - bx.t) * (y1 - y0)};
  }
  /** Clip drawing to a pixel box while fn runs. */
  function clip(c, bx, fn, pad = 2) {
    c.save(); c.beginPath(); c.rect(bx.l - pad, bx.t - pad, bx.r - bx.l + 2 * pad, bx.b - bx.t + 2 * pad); c.clip(); fn(); c.restore();
  }

  // ---------------------------------------------------------------- marks
  /** Line types carry series identity; colour carries attention. */
  const DASH = {solid:[], chain:[10, 3, 2, 3], dash:[5, 4], dot:[.1, 3.6], fine:[3, 3]};
  const WEIGHT = {fine:.75, axis:1, data:2, bold:2.6};
  function path(c, pts, {color, width = 1, dash = [], cap = 'butt'} = {}) {
    if (pts.length < 2) return;
    c.save(); c.beginPath();
    pts.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y));
    c.strokeStyle = color || colors().ink; c.lineWidth = width; c.lineCap = dash === DASH.dot ? 'round' : cap; c.setLineDash(dash); c.stroke(); c.restore();
  }
  function poly(c, pts, {fill, stroke, width = 1, dash = []} = {}) {
    if (pts.length < 3) return;
    c.save(); c.beginPath(); pts.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.closePath();
    if (fill) { c.fillStyle = fill; c.fill(); }
    if (stroke) { c.strokeStyle = stroke; c.lineWidth = width; c.lineCap = dash === DASH.dot ? 'round' : 'butt'; c.setLineDash(dash); c.stroke(); }
    c.restore();
  }
  /** Text with a paper halo so it stays legible over lines. */
  function text(c, s, x, y, {font, color, align = 'left', base = 'alphabetic', halo = true} = {}) {
    const P = colors();
    c.save(); c.font = font || `11px ${P.mono}`; c.textAlign = align; c.textBaseline = base;
    if (halo) { c.strokeStyle = P.paper; c.lineWidth = 4; c.lineJoin = 'round'; c.strokeText(s, x, y); }
    c.fillStyle = color || P.ink; c.fillText(s, x, y); c.restore();
  }
  function measure(c, s, font) { c.save(); c.font = font || `11px ${colors().mono}`; const w = c.measureText(s).width; c.restore(); return w; }
  function arrow(c, x, y, dx, dy, color, len = 7, half = 2.3) {
    const n = Math.hypot(dx, dy) || 1, ux = dx / n, uy = dy / n;
    c.beginPath(); c.moveTo(x, y);
    c.lineTo(x - ux * len - uy * half, y - uy * len + ux * half);
    c.lineTo(x - ux * len + uy * half, y - uy * len - ux * half);
    c.closePath(); c.fillStyle = color || colors().ink; c.fill();
  }
  /** Vector from (x0,y0) to (x1,y1) in pixels; the head scales down for short vectors. */
  function vector(c, x0, y0, x1, y1, {color, width = 2, dash = [], head = 10} = {}) {
    const n = Math.hypot(x1 - x0, y1 - y0); if (n < .5) return;
    const h = Math.min(head, .45 * n), ux = (x1 - x0) / n, uy = (y1 - y0) / n;
    path(c, [[x0, y0], [x1 - ux * h * .7, y1 - uy * h * .7]], {color, width, dash});
    arrow(c, x1, y1, ux, uy, color || colors().ink, h, h * .36);
  }
  function dot(c, x, y, {color, r = 3.5, hollow = false} = {}) {
    const P = colors();
    c.beginPath(); c.arc(x, y, r + 2, 0, 7); c.fillStyle = P.paper; c.fill();
    c.beginPath(); c.arc(x, y, r, 0, 7);
    if (hollow) { c.strokeStyle = color || P.ink; c.lineWidth = 1.5; c.stroke(); }
    else { c.fillStyle = color || P.ink; c.fill(); }
  }
  /** Registration cross: the mark for a draggable point or a datum. */
  function cross(c, x, y, {color, r = 7} = {}) {
    const col = color || colors().ink;
    path(c, [[x - r, y], [x + r, y]], {color:col, width:1.25}); path(c, [[x, y - r], [x, y + r]], {color:col, width:1.25});
    c.beginPath(); c.arc(x, y, r * .55, 0, 7); c.strokeStyle = col; c.lineWidth = 1.25; c.stroke();
  }
  /**
   * Axes with outward ticks. Registration crosses at tick intersections replace a full grid;
   * pass grid:false where the grid itself is the object (e.g. a transformed lattice).
   * origin:true draws axes through (0,0) instead of on the box edge.
   */
  function axes(c, F, {xTicks, yTicks, xFmt = String, yFmt = String, xLabel, yLabel, showX = true, showY = true, marks = [], grid = true, origin = false}) {
    const P = colors(), {l, t, r, b} = F.box, small = `11px ${P.mono}`;
    const ax = origin ? Math.round(F.X(0)) + .5 : l + .5, ay = origin ? Math.round(F.Y(0)) + .5 : b + .5;
    if (grid) {
      c.save(); c.strokeStyle = P.ink4; c.lineWidth = 1;
      for (const xv of xTicks) for (const yv of yTicks) {
        const x = Math.round(F.X(xv)) + .5, y = Math.round(F.Y(yv)) + .5;
        if (Math.abs(x - ax) < 3 || Math.abs(y - ay) < 3) continue;
        c.beginPath(); c.moveTo(x - 4, y); c.lineTo(x + 4, y); c.moveTo(x, y - 4); c.lineTo(x, y + 4); c.stroke();
      }
      c.restore();
    }
    if (origin) { path(c, [[l, ay], [r, ay]], {color:P.ink}); path(c, [[ax, t], [ax, b]], {color:P.ink}); }
    else path(c, [[l + .5, t], [l + .5, b + .5], [r, b + .5]], {color:P.ink});
    for (const v of xTicks) {
      const x = Math.round(F.X(v)) + .5;
      if (origin && v === 0) continue;
      path(c, [[x, ay], [x, ay + 5]], {color:P.ink});
      if (showX) text(c, xFmt(v), x, ay + 17, {align:'center', color:P.ink2, font:small, halo:origin});
    }
    for (const v of yTicks) {
      const y = Math.round(F.Y(v)) + .5;
      if (origin && v === 0) continue;
      path(c, [[ax - 5, y], [ax, y]], {color:P.ink});
      if (showY) text(c, yFmt(v), ax - 8, y + 4, {align:'right', color:P.ink2, font:small, halo:origin});
    }
    for (const m of marks) {
      const x = Math.round(F.X(m.v)) + .5;
      path(c, [[x, ay], [x, ay + 9]], {color:P.ink, width:1.5});
      text(c, m.label, x, ay + 30, {align:'center', font:`italic 13px ${P.serif}`, halo:false});
    }
    if (yLabel) text(c, yLabel, origin ? ax + 8 : l, t - 9, {color:P.ink2, font:`11px ${P.sans}`, halo:false});
    if (xLabel) text(c, xLabel, r, (origin ? ay : b) + 30, {align:'right', color:P.ink2, font:`11px ${P.sans}`, halo:false});
  }
  /** Horizontal dimension at height y between x1 and x2; ext = feature y for extension lines. */
  function dimH(c, x1, x2, y, label, {ext, color} = {}) {
    const col = color || colors().ink, w = Math.abs(x2 - x1);
    if (ext !== undefined) for (const x of [x1, x2]) path(c, [[x, ext + Math.sign(y - ext) * 3], [x, y + Math.sign(y - ext) * 4]], {color:col, width:.75});
    if (w >= 18) { path(c, [[x1, y], [x2, y]], {color:col, width:.75}); arrow(c, x1, y, -1, 0, col); arrow(c, x2, y, 1, 0, col); }
    else { path(c, [[x1 - 14, y], [x2 + 14, y]], {color:col, width:.75}); arrow(c, x1, y, 1, 0, col); arrow(c, x2, y, -1, 0, col); }
    text(c, label, (x1 + x2) / 2, y - 5, {align:'center', color:col});
  }
  function dimV(c, x, y1, y2, label, {color} = {}) {
    const col = color || colors().ink, h = Math.abs(y2 - y1), lo = Math.max(y1, y2), hi = Math.min(y1, y2);
    if (h >= 18) { path(c, [[x, lo], [x, hi]], {color:col, width:.75}); arrow(c, x, hi, 0, -1, col); arrow(c, x, lo, 0, 1, col); }
    else { path(c, [[x, hi - 14], [x, lo + 14]], {color:col, width:.75}); arrow(c, x, hi, 0, 1, col); arrow(c, x, lo, 0, -1, col); }
    text(c, label, x + 7, (y1 + y2) / 2 + 4, {color:col});
  }
  /** Leader: anchor dot → elbow → shelf → label. */
  function leader(c, ax, ay, tx, ty, label, {color, textColor, font} = {}) {
    const col = color || colors().ink, dir = tx >= ax ? 1 : -1;
    path(c, [[ax, ay], [tx, ty], [tx + dir * 12, ty]], {color:col, width:.75});
    c.beginPath(); c.arc(ax, ay, 1.8, 0, 7); c.fillStyle = col; c.fill();
    text(c, label, tx + dir * 16, ty + 4, {align:dir > 0 ? 'left' : 'right', color:textColor || col, font});
  }
  /** Detail view: dashed source circle, connector, and a magnified circular inset. Label the magnification honestly. */
  function detail(c, {sx, sy, sr, cx, cy, r, draw, label}) {
    const P = colors(), dx = cx - sx, dy = cy - sy, n = Math.hypot(dx, dy) || 1;
    c.save(); c.setLineDash(DASH.fine); c.strokeStyle = P.ink2; c.lineWidth = 1;
    c.beginPath(); c.arc(sx, sy, sr, 0, 7); c.stroke(); c.restore();
    path(c, [[sx + dx / n * sr, sy + dy / n * sr], [cx - dx / n * r, cy - dy / n * r]], {color:P.ink2, dash:DASH.fine});
    c.save(); c.beginPath(); c.arc(cx, cy, r, 0, 7); c.fillStyle = P.paper; c.fill(); c.clip(); draw(c); c.restore();
    c.beginPath(); c.arc(cx, cy, r, 0, 7); c.strokeStyle = P.ink; c.lineWidth = 1; c.stroke();
    if (label) text(c, label, cx, cy + r + 15, {align:'center', font:`600 10px ${P.sans}`});
  }
  /**
   * Signed scalar → fill colour for fields: fog (negative) ↔ paper (zero) ↔ vermilion wash (positive).
   * When a page uses this, the "current selection" moves to ink + registration cross,
   * and the title block must say what the two ends mean.
   */
  function channels(s) {
    if (s.startsWith('#')) return [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16));
    const m = (s.match(/\d+(\.\d+)?/g) || []).map(Number); return m.length >= 3 ? m.slice(0, 3) : [0, 0, 0];
  }
  function signed(u) {
    const P = colors(), t = Math.max(-1, Math.min(1, u));
    const a = channels(P.paper), z = channels(t < 0 ? P.fog : P.accent), k = Math.abs(t) * (t < 0 ? .85 : .6);
    return `rgb(${a.map((v, i) => Math.round(v + (z[i] - v) * k)).join(' ')})`;
  }
  /** One-sided magnitude → paper→ink ramp. */
  function ramp(u) { const t = Math.max(0, Math.min(1, u)); return `rgb(${channels(colors().ink).join(' ')} / ${(t * 85).toFixed(1)}%)`; }

  // ---------------------------------------------------------------- state & input
  /**
   * Wire every [data-param] control under root to one state object.
   * A range and a number input sharing data-param stay in sync; selects and
   * checkboxes are supported. Every change goes through update(patch).
   */
  function bindParams(root, update) {
    const controls = [...root.querySelectorAll('[data-param]')];
    for (const el of controls) {
      const key = el.dataset.param;
      el.addEventListener(el.type === 'number' ? 'change' : 'input', () => {
        const v = readControl(el);
        if (v === undefined) syncParams(root, {[key]:null}); else update({[key]:v});
      });
    }
    return controls;
  }
  /** Control value as bindParams reads it; number inputs clamp to min/max, undefined = empty or invalid. */
  function readControl(el) {
    if (el.type === 'checkbox') return el.checked;
    if (el.tagName === 'SELECT' || el.type === 'text') return el.value;
    const n = Number(el.value), lo = el.min === '' ? -Infinity : +el.min, hi = el.max === '' ? Infinity : +el.max;
    if (el.type !== 'number') return +el.value;
    return el.value === '' || !Number.isFinite(n) ? undefined : Math.max(lo, Math.min(hi, n));
  }
  /** Write state values back into the controls (after presets, drags, reset). null = restore from range. */
  function syncParams(root, state) {
    for (const el of root.querySelectorAll('[data-param]')) {
      const key = el.dataset.param; if (!(key in state)) continue;
      let v = state[key];
      if (v === null) { const twin = root.querySelector(`input[type=range][data-param="${key}"]`); v = twin ? +twin.value : el.defaultValue; }
      if (el.type === 'checkbox') el.checked = !!v;
      else if (document.activeElement !== el || el.type !== 'number') el.value = v;
    }
  }
  /**
   * Shared controls that edit the selected item. [data-sel="key"] controls (also ones added later) edit
   * get(state)[key]; an edit calls update(set(state, key, value)), never mutating state. The selection
   * itself is an ordinary state key. Call the returned sync(state) from update() after syncParams.
   */
  function bindSelected(root, update, {get, set}) {
    let last;
    const sync = state => {
      last = state; const t = get(state);
      for (const el of root.querySelectorAll('[data-sel]')) {
        const v = t?.[el.dataset.sel]; if (v === undefined) continue;
        if (el.type === 'checkbox') el.checked = !!v;
        else if (document.activeElement !== el || el.type !== 'number') el.value = v;
      }
    };
    const onEdit = e => {
      const el = e.target, key = el.dataset?.sel;
      if (key === undefined || (e.type === 'change') !== (el.type === 'number')) return;
      const v = readControl(el);
      if (v === undefined) sync(last); else update(set(last, key, v));
    };
    root.addEventListener('input', onEdit); root.addEventListener('change', onEdit);
    return sync;
  }
  /**
   * Pointer dragging on a canvas. hit(px,py) returns a handle (any truthy value) or null;
   * move(handle, px, py) writes state. Keyboard users keep the parameter table.
   */
  function drag(canvas, {hit, move, end, cursor = 'grab'}) {
    canvas.dataset.drag = '';
    let active = null;
    const at = e => { const r = canvas.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    canvas.addEventListener('pointerdown', e => {
      const h = hit(...at(e)); if (!h) return;
      active = h; canvas.setPointerCapture(e.pointerId); canvas.style.cursor = 'grabbing'; e.preventDefault(); move(active, ...at(e));
    });
    canvas.addEventListener('pointermove', e => {
      if (active) { move(active, ...at(e)); return; }
      canvas.style.cursor = hit(...at(e)) ? cursor : '';
    });
    const stop = e => { if (!active) return; const h = active; active = null; canvas.style.cursor = ''; canvas.releasePointerCapture?.(e.pointerId); end?.(h); };
    canvas.addEventListener('pointerup', stop); canvas.addEventListener('pointercancel', stop);
  }
  /**
   * Fixed-step clock for time evolution. The model advances in steps of dt
   * (physical time); `rate` maps one wall-clock second to model seconds.
   * Pausing, hiding the tab or a slow frame never changes the model's dt.
   * Under prefers-reduced-motion the clock never autoplays; play() still works on request.
   */
  function clock({dt, rate = 1, step: advance, render, maxSteps = 240, onState}) {
    let playing = false, last = 0, acc = 0, raf = 0;
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    function frameFn(now) {
      if (!playing) return;
      acc += Math.min((now - last) / 1000, .25) * rate; last = now;
      let n = 0;
      while (acc >= dt && n < maxSteps) { advance(dt); acc -= dt; n++; }
      if (n === maxSteps) acc = 0;  // fall behind rather than spiral
      render(); raf = requestAnimationFrame(frameFn);
    }
    const api = {
      get playing() { return playing; }, reduce,
      play() { if (playing) return; playing = true; last = performance.now(); acc = 0; raf = requestAnimationFrame(frameFn); onState?.(true); },
      pause() { playing = false; cancelAnimationFrame(raf); onState?.(false); },
      toggle() { playing ? api.pause() : api.play(); },
      stepOnce(n = 1) { api.pause(); for (let i = 0; i < n; i++) advance(dt); render(); },
    };
    document.addEventListener('visibilitychange', () => { if (document.hidden && playing) { api.pause(); api.resumeOnShow = true; } else if (!document.hidden && api.resumeOnShow) { api.resumeOnShow = false; api.play(); } });
    return api;
  }

  // ---------------------------------------------------------------- sliders
  /** Draw a tick scale under every input.ruler; the scale insets by the thumb half-width in CSS. */
  function rulers(rootEl = document) {
    for (const input of rootEl.querySelectorAll('input[type=range].ruler')) {
      let scale = input.nextElementSibling;
      if (!scale?.classList.contains('scale')) { scale = document.createElement('div'); scale.className = 'scale'; input.after(scale); }
      scale.setAttribute('aria-hidden', 'true');
      const min = +input.min, max = +input.max, {values, step:s} = ticks(min, max, 4), minor = s / 5, at = v => (v - min) / (max - min) * 100;
      let html = '';
      for (let i = Math.ceil(min / minor - 1e-9); i * minor <= max + 1e-9; i++) {
        const v = i * minor, major = values.some(m => Math.abs(m - v) < minor * 1e-6);
        html += `<i class="${major ? 'major' : ''}" style="left:${at(v)}%"></i>`;
        if (major) html += `<span style="left:${at(v)}%">${fmt(v, s)}</span>`;
      }
      scale.innerHTML = html;
    }
  }

  // ---------------------------------------------------------------- maths & reader
  /** Render every [data-tex] element with KaTeX; .formula elements are display maths. */
  function math(root = document) {
    if (!window.katex) return;
    for (const e of root.querySelectorAll('[data-tex]')) katex.render(e.dataset.tex, e, {throwOnError:false, displayMode:e.classList.contains('formula'), trust:false});
  }
  function setMath(el, tex) { el.dataset.tex = tex; math(el.parentElement || document); }

  /** UI text; a page may `Object.assign(Draft.strings, {...})` before Draft.shell(). */
  const strings = {table:'Scrollable table', noNotes:'No bundled Markdown found.',
    renderFailed:'Could not render the notes. Use the download link to read them.',
    statusFile:'Local file · bundled notes', statusHttp:'Local assets · no external requests'};

  /**
   * Header tabs: data-view="experiment" scrolls to the lab; any other data-view opens
   * the bundled note with that key (guide, annotated, …) in the reader sheet.
   */
  function shell() {
    const overlay = document.querySelector('.reader-overlay'), reader = document.querySelector('.markdown-reader');
    const body = document.querySelector('.markdown-body'), closeButton = document.querySelector('[data-close-reader]');
    const titleEl = document.querySelector('[data-reader-title]'), download = document.querySelector('[data-download-notes]');
    const main = document.querySelector('main'), tabs = [...document.querySelectorAll('.sheet-nav a[data-view]')];
    const notes = window.MARKDOWN_NOTES || {}, rendered = {};
    let returnFocus, current = null;
    function select(view) {
      for (const tab of tabs) {
        const active = tab.dataset.view === view;
        tab.classList.toggle('active', active);
        if (active) tab.setAttribute('aria-current', 'page'); else tab.removeAttribute('aria-current');
      }
    }
    function renderMarkdown(note, source) {
      const tex = [];
      // Protect code and TeX before Markdown interprets underscores and backslashes.
      const protectedSource = source.replace(/```[\s\S]*?```|`[^`\n]+`|\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$(?!\$)[^$\n]+\$/g, token => {
        if (token.startsWith('`')) return token;
        const display = token.startsWith('$$') || token.startsWith('\\[');
        const edge = token.startsWith('$') && !display ? 1 : 2;
        const id = tex.push({tex:token.slice(edge, -edge), display}) - 1;
        return `<span data-reader-math="${id}"></span>`;
      });
      body.innerHTML = window.marked ? marked.parse(protectedSource) : `<pre>${source.replace(/[&<>]/g, ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;'}[ch]))}</pre>`;
      for (const placeholder of body.querySelectorAll('[data-reader-math]')) {
        const item = tex[Number(placeholder.dataset.readerMath)];
        if (window.katex) katex.render(item.tex, placeholder, {displayMode:item.display, throwOnError:false, output:'htmlAndMathml'});
        else placeholder.textContent = item.tex;
      }
      // Keep native table sizing; the outer card clips corners and owns scrolling.
      for (const table of body.querySelectorAll('table')) {
        const card = document.createElement('div');
        card.className = 'table-card'; card.tabIndex = 0;
        card.setAttribute('role', 'region'); card.setAttribute('aria-label', strings.table);
        table.before(card); card.append(table);
      }
      const base = new URL(note.url, location.href);
      for (const img of body.querySelectorAll('img')) {
        const file = img.getAttribute('src').split('/').pop();
        img.src = window.FIGURE_DATA?.[file] || new URL(img.getAttribute('src'), base).href;
        img.loading = 'lazy';
      }
      for (const a of body.querySelectorAll('a[href]')) {
        const href = a.getAttribute('href');
        if (/^https?:/i.test(href)) { a.target = '_blank'; a.rel = 'noopener'; }
        else if (!/^(?:[a-z]+:|#|\/)/i.test(href)) a.href = new URL(href, base).href;
      }
      body.scrollTop = 0;
    }
    async function load(key) {
      const note = notes[key];
      if (!note) { body.textContent = strings.noNotes; return; }
      if (titleEl) titleEl.textContent = note.title || key;
      if (download) { download.href = note.url; download.setAttribute('download', note.file.split('/').pop()); }
      if (!rendered[key] && /^https?:$/.test(location.protocol)) {
        try { const response = await fetch(note.url); if (response.ok) note.source = await response.text(); }
        catch { /* The bundled copy keeps the reader available offline. */ }
      }
      rendered[key] = true; renderMarkdown(note, note.source);
    }
    function openReader(key) {
      if (current !== key) load(key).catch(() => { body.textContent = strings.renderFailed; });
      current = key;
      if (overlay.classList.contains('open')) { select(key); return; }
      returnFocus = document.activeElement;
      overlay.inert = false; overlay.setAttribute('aria-hidden', 'false'); overlay.classList.add('open');
      document.body.classList.add('reader-open'); main.inert = true;
      select(key); closeButton.focus();
    }
    function closeReader() {
      overlay.classList.remove('open'); overlay.setAttribute('aria-hidden', 'true'); overlay.inert = true;
      document.body.classList.remove('reader-open'); main.inert = false;
      select('experiment'); returnFocus?.focus();
    }
    for (const tab of tabs) tab.addEventListener('click', event => {
      event.preventDefault();
      if (tab.dataset.view === 'experiment') { if (overlay.classList.contains('open')) closeReader(); document.getElementById('experiment')?.scrollIntoView(); }
      else openReader(tab.dataset.view);
    });
    closeButton.addEventListener('click', closeReader);
    overlay.addEventListener('click', event => { if (event.target === overlay) closeReader(); });
    reader.addEventListener('keydown', event => {
      if (event.key === 'Escape') { event.preventDefault(); closeReader(); }
      if (event.key === 'Tab') {
        const focusable = [...overlay.querySelectorAll('a[href],button,input,[tabindex="0"]')].filter(el => el.getClientRects().length);
        const first = focusable[0], last = focusable.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    });
    const status = document.querySelector('[data-shell-status]');
    if (status) status.textContent = location.protocol === 'file:' ? strings.statusFile : strings.statusHttp;
  }
  /** Save a bundled note as a .md file. */
  function downloadNote(key = 'guide') {
    const note = window.MARKDOWN_NOTES?.[key]; if (!note) return;
    const url = URL.createObjectURL(new Blob([note.source], {type:'text/markdown;charset=utf-8'})), a = document.createElement('a');
    a.href = url; a.download = note.file.split('/').pop(); a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  window.Draft = {colors, ticks, step, fmt, setup, box, frame, clip, DASH, WEIGHT, path, poly, text, measure, arrow, vector, dot, cross,
    axes, dimH, dimV, leader, detail, signed, ramp, bindParams, syncParams, bindSelected, drag, clock, rulers, math, setMath, shell, downloadNote, strings};
})();
