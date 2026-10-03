import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';

const sourceHashes = {
  'src/effects/cpu/mesh-render.js': '4fa90cc2681e51dce259e79bf807fb352868cc5e31823a313c818b7c1deeb051',
  'src/runtime/surface.js': '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
};
const [cpuRoot, casesPath] = process.argv.slice(2);
if (!cpuRoot || !casesPath) throw new Error('usage: reference.mjs CPU_ROOT CASES_JSON');
const modules = {};
for (const [path, hash] of Object.entries(sourceHashes)) {
  const bytes = await readFile(resolve(cpuRoot, path));
  if (createHash('sha256').update(bytes).digest('hex') !== hash) throw new Error(`CPU source hash mismatch: ${path}`);
  modules[path] = await import(`data:text/javascript;base64,${bytes.toString('base64')}`);
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
console.log(JSON.stringify({cpu_revision: '26d6f42be38da7172f602373e844f85a8155356f', source_hashes: sourceHashes, results}));
