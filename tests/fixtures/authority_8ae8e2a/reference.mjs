import {readFile, lstat, mkdtemp, mkdir, writeFile, rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';
// The complete relative-import closure of the four modules this capture drives,
// at noisemaker-for-cpu 7f473400ac744025d46221bf527b43c1b5c1ef4e.
const hashes = {
  'src/effects/generated/canonical-kernels.js': '86fc0a3b6fdd2227341b2b59e0d7dd4177980f1b78b57e61c85c8f7525391423',
  'src/csl/glsl-kernel.js': 'f5664e2c90289c82f7109cea910fb5de71ae08f5c2204fb569299a9c49a645ff',
  'src/csl/glsl-runtime.js': 'ad71e22deeb31ad1f19f81923704c9ad0e1ef0475f9a333e0d5fe9088051eebd',
  'src/csl/metal-division.js': '104cda4fda758fcdfd20f69264a92c1190830102814aec8aa9706058642ce2a8',
  'src/csl/metal-reciprocal-data.js': '08905259e72a066e77675f98b9700d6c3a6467662f5de562d8f8e1e14d082c87',
  'src/csl/metal-reciprocal-grid.js': 'bd6613830c4239ff9b21a4157875a7c92ced898fd706e735527f39552be11e39',
  'src/runtime/pass-runner.js': 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa',
  'src/runtime/sampler.js': '5a3e494e79f431605fecd682fd9fe6fc8437dde1332f1dc872632af59d0eeaf5',
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
    const sourcePath = resolve(cpuRoot, name);
    const stat = await lstat(sourcePath);
    if (stat.isSymbolicLink() || !stat.isFile()) throw new Error(`CPU source must be a regular file: ${name}`);
    const bytes = await readFile(sourcePath);
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
  console.log(JSON.stringify({cpu_revision: '7f473400ac744025d46221bf527b43c1b5c1ef4e', source_hashes: hashes, results}));
} finally { await rm(scratch, {recursive: true, force: true}); }
