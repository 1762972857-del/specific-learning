/* Run with node scripts/verify_surface3d.cjs. Browser checks are separate. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const ctx = {save(){}, restore(){}, beginPath(){}, moveTo(){}, lineTo(){}, closePath(){}, fill(){}, stroke(){}};
const sandbox = {window:{Draft:{setup:()=>({c:ctx,w:482,h:554}), colors:()=>({paper2:'paper',ink3:'ink'})}}};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root,'assets/surface3d.js'),'utf8'),sandbox);
const draw = options => sandbox.window.Surface3D.draw({}, options);
const domain = {x:[-1,1],y:[-1,1],z:[-1,1]};
const base = {f:()=>0,domain,mesh:[2,3],camera:{yaw:0,pitch:0},viewSpan:[4.2,4.6]};
const close = (actual, expected) => actual.forEach((n,i)=>assert(Math.abs(n-expected[i])<1e-10,`${actual} != ${expected}`));
const flat = draw(base);
assert.equal(flat.triangles,12); assert.equal(flat.skippedTriangles,0);
// At zero yaw/pitch: x goes right, z goes up, y is depth; 100 pixels/unit.
close(flat.project(0,0,0),[241,265.92,0]);
close(flat.project(1,0,0),[341,265.92,0]);
close(flat.project(0,1,0),[241,265.92,1]);
close(flat.project(0,0,1),[241,165.92,0]);
close(draw({...base,camera:{yaw:90,pitch:0}}).project(1,0,0),[241,265.92,1]);
close(draw({...base,camera:{yaw:0,pitch:90}}).project(0,1,0),[241,365.92,0]);
// Translating a world box must preserve centred projection; f cannot rescale it.
const translated = draw({...base,domain:{x:[10,12],y:[20,22],z:[30,32]},f:()=>31});
close(translated.project(12,21,31),flat.project(1,0,0));
close(draw({...base,f:()=>.8}).project(.5,.2,.3),flat.project(.5,.2,.3));
for (const f of [()=>NaN,()=>Infinity,()=>2]) {
  const missing = draw({...base,f}); assert.equal(missing.triangles,0); assert.equal(missing.skippedTriangles,12);
}
assert.throws(()=>draw({...base,domain:{...domain,x:[1,1]}}));
assert.throws(()=>draw({...base,mesh:[2.5,3]}));
assert.throws(()=>draw({...base,camera:{yaw:NaN}}));
// A bounded analytic surface exercises mesh construction at 36 camera settings.
for (const k of [.4,1,2.4]) for (const yaw of [-180,-55,0,180]) for (const pitch of [10,28,80]) {
  const surface = draw({f:(x,y)=>Math.sin(k*x)*Math.cos(k*y),domain:{x:[0,2*Math.PI],y:[0,2*Math.PI],z:[-1.1,1.1]},mesh:[60,60],camera:{yaw,pitch}});
  assert.equal(surface.triangles,7200); assert.equal(surface.skippedTriangles,0);
  close(surface.project(Math.PI,Math.PI,0),[241,265.92,0]);
}
console.log('Surface3D: projections, fixed scale, translated domains, missing samples, invalid inputs and 36 camera configurations passed.');
