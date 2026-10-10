import {readFile, mkdtemp, mkdir, writeFile, rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';
const hashes = {
  'src/effects/generated/canonical-kernels.js': 'eda3ca5153d7759cbf9e92982cc8579c2474828f770d29343c38dc31fcac9904',
  'src/csl/glsl-kernel.js': 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa',
  'src/csl/glsl-runtime.js': 'b47fa69f3358822c314315ad985c14c94fff5c973ff98fe953d7304135b84722',
  'src/runtime/sampler.js': '1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328',
  'src/runtime/surface.js': '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
};
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const [cpuRoot, inputPath] = process.argv.slice(2);
if (!cpuRoot || !inputPath) throw new Error('usage: reference.mjs CPU_ROOT INPUT_JSON');
const scratch = await mkdtemp(resolve(tmpdir(), 'roll-reference-'));
try {
  // Import only an authenticated, regular-file copy of the complete five-file closure.
  await writeFile(resolve(scratch, 'package.json'), '{"type":"module"}');
  for (const [name, digest] of Object.entries(hashes)) {
    const bytes = await readFile(resolve(cpuRoot, name));
    if (sha(bytes) !== digest) throw new Error(`CPU source hash mismatch: ${name}`);
    await mkdir(dirname(resolve(scratch, name)), {recursive: true});
    await writeFile(resolve(scratch, name), bytes);
  }
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
    const feedbackTex = new Surface(width, height, floats(test.feedbackFloat32, width * height * 4));
    const noteGridTex = new Surface(128, 16, floats(test.gridFloat32, 128 * 16 * 4));
    feedbackTex.filter = test.filter;
    noteGridTex.filter = 'nearest';
    const kernel = bindCanonicalKernel(canonicalKernelFactories['synth/roll:roll'], {
      width, height, time: 1.25, deltaTime: test.delta_time,
      uniforms: {lineColor: test.color, gain: test.gain, speed: test.speed, midiClockCount: 42},
      textures: {feedbackTex, noteGridTex},
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
  console.log(JSON.stringify({cpu_revision: '5b686a45b5c56329adf0c63cbcf572eb6f23fad1', source_hashes: hashes, results}));
} finally { await rm(scratch, {recursive: true, force: true}); }
