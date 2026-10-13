/* Run with node scripts/verify_selected.cjs. Covers Draft.bindSelected with a minimal fake DOM. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const control = (sel, type, min, max) => ({dataset:{sel}, type, tagName:'INPUT', min, max, value:''});
const xIn = control('x', 'number', '-3', '3'), xRange = control('x', 'range', '-3', '3'), yIn = control('y', 'number', '-3', '3');
const handlers = {}, controls = [xIn, xRange, yIn];
const root = {querySelectorAll: s => s === '[data-sel]' ? controls : [], addEventListener: (t, f) => (handlers[t] ||= []).push(f)};
const fire = (el, type) => (handlers[type] || []).forEach(f => f({target:el, type}));
const doc = {activeElement:null};
const sandbox = {window:{}, document:doc};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'assets/draft.js'), 'utf8'), sandbox);
const {bindSelected} = sandbox.window.Draft;

// Page contract: one state, update(patch) is the only writer, sync after every update.
const state = {i:'e1', e1:{x:1, y:0}, e2:{x:0, y:1}}, patches = [];
const set = (s, key, value) => ({[s.i]:{...s[s.i], [key]:value}});
const update = (patch = {}) => { patches.push(patch); Object.assign(state, patch); sync(state); };
const sync = bindSelected(root, update, {get:s => s[s.i], set});
update();
assert.deepEqual([xIn.value, xRange.value, yIn.value], [1, 1, 0]);

// Selection switch resyncs every control.
update({i:'e2'});
assert.deepEqual([xIn.value, xRange.value, yIn.value], [0, 0, 1]);

// Input edits only the selected item, through a patch; state objects are replaced, not mutated.
const e1 = state.e1; patches.length = 0;
xIn.value = '2.5'; fire(xIn, 'change');
assert.deepEqual(patches, [{e2:{x:2.5, y:1}}]);
assert.equal(state.e1, e1); assert.deepEqual(state.e1, {x:1, y:0});
assert.equal(xRange.value, 2.5);
// Range uses 'input'; number ignores 'input' (waits for 'change'); range ignores 'change'.
xRange.value = '-1'; fire(xRange, 'change'); fire(xRange, 'input');
assert.equal(patches.length, 2); assert.equal(state.e2.x, -1); assert.equal(xIn.value, -1);
yIn.value = '2'; fire(yIn, 'input'); assert.equal(patches.length, 2);

// Clamping to min/max, as bindParams does.
yIn.value = '99'; fire(yIn, 'change'); assert.equal(state.e2.y, 3); assert.equal(yIn.value, 3);
yIn.value = '-99'; fire(yIn, 'change'); assert.equal(state.e2.y, -3);

// Empty or invalid exact input restores the control without an update.
const n = patches.length; yIn.value = ''; fire(yIn, 'change');
assert.equal(patches.length, n); assert.equal(yIn.value, -3);

// A focused number input is not overwritten while the reader types.
doc.activeElement = xIn; xIn.value = '1.'; update({i:'e2'}); assert.equal(xIn.value, '1.');
console.log('verify_selected: ok');
