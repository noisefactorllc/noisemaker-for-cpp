import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {authenticateCpuRoot} from '../../tools/dsl/corpus_authority.mjs';
const rootArg = process.argv.indexOf('--cpu-root');
const ledgerArg = process.argv.indexOf('--ledger');
assert.ok(rootArg > 0 && ledgerArg > 0, 'pass --cpu-root ROOT --ledger FILE');
const root = authenticateCpuRoot(process.argv[rootArg + 1], process.argv[ledgerArg + 1]);
const load=p=>import(pathToFileURL(`${root}/${p}`).href);
const {canonicalKernelFactories,kernelFactories}=await load('src/effects/catalog.js');
const {createCanonicalBindings}=await load('src/csl/glsl-kernel.js');
const {Surface}=await load('src/runtime/surface.js');
const {bindGlslKernel}=await load('src/csl/glsl-runtime.js');
const {runPass}=await load('src/runtime/pass-runner.js');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=a=>Buffer.from(a.buffer,a.byteOffset,a.byteLength);
const key='synth/perlin:perlin',factory=canonicalKernelFactories[key];
assert.equal(kernelFactories.get(key),factory);
const cases=[];
for (const [width,height] of [[7,5],[11,3]]) for(const DIMENSIONS of [2,3]) for(const warpIterations of [0,2]) for(const octaves of [1,6]) for(const colorMode of [0,1]) {
 const uniforms={DIMENSIONS,resolution:[width,height],fullResolution:[width+6,height+4],tileOffset:[-3,2],aspect:Math.fround(width/height),time:.375,scale:25.5,seed:17,octaves,colorMode,ridges:warpIterations?1:0,warpIterations,warpScale:37.25,warpIntensity:62.5,speed:1.75};
 const before=structuredClone(uniforms);
 function render(){const out=new Surface(width,height); const kernel=bindGlslKernel(factory,{...createCanonicalBindings({width,height,time:uniforms.time,seed:uniforms.seed,tileOffset:uniforms.tileOffset,fullResolution:uniforms.fullResolution,uniforms}),aspect:uniforms.aspect}); runPass({kernel,destination:out});return out;}
 const out=render(), again=render();assert.deepEqual(bytes(out.data),bytes(again.data));assert.deepEqual(uniforms,before);
 cases.push({width,height,uniforms,f32:hash(bytes(out.data)),rgba8:hash(bytes(out.toRgba8())),words:Array.from(new Uint32Array(out.data.buffer)),rgba8Bytes:Array.from(out.toRgba8())});
}
process.stdout.write(JSON.stringify({cpu:'4307ca9f26fc415e4fc5e75227d429d35cc741cd',factory_sha256:hash(factory.toString()),cases})+'\n');
