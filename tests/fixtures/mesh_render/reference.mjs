import {authenticateCpuRoot} from '../../../tools/dsl/corpus_authority.mjs';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const sourceHashes = {
  'src/effects/cpu/mesh-render.js': 'ea9480452c59bcc51aa33fa0e699368b3dcadc6c629569a3b0fa7142186ee499',
  'src/runtime/external-input.js': '705f8f27b29e6ddc2334eb1e9af6ad57004063d848ea3bee9356626218c12757',
  'src/runtime/surface.js': '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
};
const [cpuRoot, casesPath] = process.argv.slice(2);
if (!cpuRoot || !casesPath) throw new Error('usage: reference.mjs CPU_ROOT CASES_JSON');
const modules = {};
for (const [path, hash] of Object.entries(sourceHashes)) {
  const bytes = await readFile(resolve(cpuRoot, path));
  if (createHash('sha256').update(bytes).digest('hex') !== hash) throw new Error(`CPU source hash mismatch: ${path}`);
  modules[path] = bytes;
}
authenticateCpuRoot(cpuRoot);
// mesh-render.js imports ../../runtime/external-input.js, so each module
// loads from the authenticated root once every file in the closure matched.
for (const path of Object.keys(modules)) {
  modules[path] = await import(pathToFileURL(resolve(cpuRoot, path)).href);
}
const {meshRenderTrianglesAdapter} = modules['src/effects/cpu/mesh-render.js'];
const {Surface} = modules['src/runtime/surface.js'];
const cases = JSON.parse(await readFile(casesPath, 'utf8'));
const results = cases.map(test => {
  const destination = new Surface(test.width, test.height);
  destination.clear(test.clear);
  const positions = new Float32Array(test.positions);
  const normalData = new Float32Array(test.normals);
  const meshData = {positionData: positions, normalData, texWidth: test.tex_width, texHeight: test.tex_height};
  const {pixels} = meshRenderTrianglesAdapter({uniforms: test.uniforms, bindings: test.bindings,
    destination, externalInputs: {meshData}});
  return {name: test.name, pixels, words: Array.from(new Uint32Array(destination.data.buffer)), rgba8: Array.from(destination.toRgba8())};
});
console.log(JSON.stringify({cpu_revision: '9b7294820eec2a0b95c66790b1dae374fa079c13', source_hashes: sourceHashes, results}));
