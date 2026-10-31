import {authenticateCpu9b729482Root} from '../../../tools/dsl/corpus_authority.mjs';
import {readFile, mkdtemp, mkdir, writeFile, rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';
const hashes = {
  'src/effects/generated/canonical-kernels.js': '2d2ad7a462d2f5e858d1ff339b0be48db097dbf3e7848bde08b90e7e3df1f869',
  'src/csl/glsl-kernel.js': 'f5664e2c90289c82f7109cea910fb5de71ae08f5c2204fb569299a9c49a645ff',
  'src/csl/glsl-runtime.js': '7f05e207246152aafa8b1777c230be86f266b398fcd535dc9c0e5f0b4f81fd30',
  'src/runtime/sampler.js': '5a3e494e79f431605fecd682fd9fe6fc8437dde1332f1dc872632af59d0eeaf5',
  'src/runtime/surface.js': '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
  'src/csl/metal-division.js': '104cda4fda758fcdfd20f69264a92c1190830102814aec8aa9706058642ce2a8',
  'src/csl/metal-reciprocal-data.js': '08905259e72a066e77675f98b9700d6c3a6467662f5de562d8f8e1e14d082c87',
  'src/csl/metal-reciprocal-grid.js': 'bd6613830c4239ff9b21a4157875a7c92ced898fd706e735527f39552be11e39',
};
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const [cpuRoot, inputPath] = process.argv.slice(2);
if (!cpuRoot || !inputPath) throw new Error('usage: reference.mjs CPU_ROOT INPUT_JSON');
const scratch = await mkdtemp(resolve(tmpdir(), 'reverb-reference-'));
try {
  // Import only an authenticated, regular-file copy of the complete eight-file closure.
  await writeFile(resolve(scratch, 'package.json'), '{"type":"module"}');
  for (const [name, digest] of Object.entries(hashes)) {
    const bytes = await readFile(resolve(cpuRoot, name));
    if (sha(bytes) !== digest) throw new Error(`CPU source hash mismatch: ${name}`);
    await mkdir(dirname(resolve(scratch, name)), {recursive: true});
    await writeFile(resolve(scratch, name), bytes);
  }
  authenticateCpu9b729482Root(cpuRoot);
  const {canonicalKernelFactories} = await import(pathToFileURL(resolve(scratch, 'src/effects/generated/canonical-kernels.js')));
  const {bindCanonicalKernel} = await import(pathToFileURL(resolve(scratch, 'src/csl/glsl-kernel.js')));
  const {Surface} = await import(pathToFileURL(resolve(scratch, 'src/runtime/surface.js')));
  function floats(hex, size) {
    if (typeof hex !== 'string' || hex.length !== size * 8 || !/^[0-9a-f]+$/i.test(hex)) throw new Error('invalid float32 input');
    const bytes = Buffer.from(hex, 'hex'), out = new Float32Array(size), words = new Uint32Array(out.buffer);
    for (let i = 0; i < size; ++i) words[i] = bytes.readUInt32LE(i * 4);
    return out;
  }
  const results = [];
  for (const test of JSON.parse(await readFile(inputPath, 'utf8'))) {
    const {width, height} = test;
    const inputTex = new Surface(width, height, floats(test.inputFloat32, width * height * 4));
    const kernel = bindCanonicalKernel(canonicalKernelFactories['filter/reverb:reverb'], {
      width, height, time: test.time, uniforms: {...test.uniforms, renderScale: 1}, textures: {inputTex},
    });
    const destination = new Surface(width, height), out = new Float32Array(4);
    for (let y = 0; y < height; ++y) for (let x = 0; x < width; ++x) {
      kernel({fragCoord: [x + 0.5, height - y - 0.5, 0, 1],
        uv: [(x + 0.5) / width, (height - y - 0.5) / height], resolution: [width, height]}, out);
      destination.data.set(out, (y * width + x) * 4);
    }
    const words = new Uint32Array(destination.data.buffer), bytes = Buffer.alloc(words.length * 4);
    for (let i = 0; i < words.length; ++i) bytes.writeUInt32LE(words[i], i * 4);
    results.push({name: test.name, float32_sha256: sha(bytes), rgba8_sha256: sha(destination.toRgba8()),
      float32_bytes: bytes.length, rgba8_bytes: words.length});
  }
  console.log(JSON.stringify({cpu_revision: '9b7294820eec2a0b95c66790b1dae374fa079c13', source_hashes: hashes, results}));
} finally { await rm(scratch, {recursive: true, force: true}); }
