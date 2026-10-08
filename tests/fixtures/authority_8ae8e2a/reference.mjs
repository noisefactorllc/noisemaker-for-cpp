import {readFile, mkdtemp, mkdir, writeFile, rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';
// The complete relative-import closure of the four modules this capture drives,
// at noisemaker-for-cpu 8ae8e2a.
const hashes = {
  'src/effects/generated/canonical-kernels.js': 'f4f3c23286da0d72032a6156ed1bd641b93a39d54a6e1812079280d2d3243e70',
  'src/csl/glsl-kernel.js': 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa',
  'src/csl/glsl-runtime.js': 'a1ceb0e4580ba989ecebf8c06ceca81847434623c040deaa143a3014ea1fd9e5',
  'src/runtime/pass-runner.js': 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa',
  'src/runtime/sampler.js': '1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328',
  'src/runtime/surface.js': '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
};
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const [cpuRoot, casesPath] = process.argv.slice(2);
if (!cpuRoot || !casesPath) throw new Error('usage: reference.mjs CPU_ROOT CASES_JSON');
const scratch = await mkdtemp(resolve(tmpdir(), 'authority-8ae8e2a-reference-'));
try {
  // Import only an authenticated, regular-file copy of the complete closure.
  await writeFile(resolve(scratch, 'package.json'), '{"type":"module"}');
  for (const [name, digest] of Object.entries(hashes)) {
    const bytes = await readFile(resolve(cpuRoot, name));
    if (sha(bytes) !== digest) throw new Error(`CPU source hash mismatch: ${name}`);
    await mkdir(dirname(resolve(scratch, name)), {recursive: true});
    await writeFile(resolve(scratch, name), bytes);
  }
  const load = name => import(pathToFileURL(resolve(scratch, name)));
  const {canonicalKernelFactories} = await load('src/effects/generated/canonical-kernels.js');
  const {bindCanonicalKernel} = await load('src/csl/glsl-kernel.js');
  const {runPass} = await load('src/runtime/pass-runner.js');
  const {Surface} = await load('src/runtime/surface.js');
  // Top-down RGBA8: every fifth pixel (counting from the tag) is opaque white and
  // every seventh is all-zero, so vector equalities against vec4(1)/vec4(0) and
  // vec3(1) see both arms; the rest is an asymmetric formula.
  function texture({width, height, tag}) {
    const bytes = new Uint8Array(width * height * 4);
    for (let y = 0; y < height; ++y) for (let x = 0; x < width; ++x) {
      const index = y * width + x, lane = index * 4;
      if ((index + tag) % 5 === 0) bytes.set([255, 255, 255, 255], lane);
      else if ((index + tag) % 7 === 0) bytes.set([0, 0, 0, 0], lane);
      else bytes.set([(31 * x + 17 * y + 13 * tag) % 256, (11 * x + 47 * y + 29 * tag) % 256,
        (67 * x + 19 * y + 7 * tag) % 256, (255 - 23 * x - 37 * y - 5 * tag) & 255], lane);
    }
    return Surface.fromRgba8(width, height, bytes);
  }
  const results = [];
  for (const test of JSON.parse(await readFile(casesPath, 'utf8'))) {
    const factory = canonicalKernelFactories[test.key];
    if (typeof factory !== 'function') throw new Error(`missing canonical factory ${test.key}`);
    const uniforms = Object.fromEntries(Object.entries(test.uniforms).map(([name, [, value]]) => [name, value]));
    const textures = Object.fromEntries(Object.entries(test.textures).map(([name, spec]) => [name, texture(spec)]));
    const kernel = bindCanonicalKernel(factory, {
      width: test.width, height: test.height, time: test.time, frame: test.frame, deltaTime: 1 / 60,
      seed: test.seed, tileOffset: new Float32Array(test.tileOffset),
      fullResolution: new Float32Array(test.fullResolution), uniforms, textures,
    });
    const destination = new Surface(test.width, test.height);
    runPass({kernel, destination, time: test.time, seed: test.seed});
    const words = new Uint32Array(destination.data.buffer, destination.data.byteOffset, destination.data.length);
    const bytes = Buffer.alloc(words.length * 4);
    for (let i = 0; i < words.length; ++i) bytes.writeUInt32LE(words[i], i * 4);
    results.push({name: test.name, float32_sha256: sha(bytes), rgba8_sha256: sha(destination.toRgba8())});
  }
  console.log(JSON.stringify({cpu_revision: '8ae8e2ae97812952db49246a87b04d7e5a480494', source_hashes: hashes, results}));
} finally { await rm(scratch, {recursive: true, force: true}); }
