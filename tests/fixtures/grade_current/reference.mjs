import {authenticateCpuRoot} from '../../../tools/dsl/corpus_authority.mjs';
import {readFile, lstat, mkdtemp, mkdir, writeFile, rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';

const hashes = {
  'src/effects/generated/canonical-kernels.js': '2d2ad7a462d2f5e858d1ff339b0be48db097dbf3e7848bde08b90e7e3df1f869',
  'src/csl/glsl-runtime.js': '7f05e207246152aafa8b1777c230be86f266b398fcd535dc9c0e5f0b4f81fd30',
  'src/runtime/sampler.js': '5a3e494e79f431605fecd682fd9fe6fc8437dde1332f1dc872632af59d0eeaf5',
  'src/runtime/surface.js': '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
  'src/runtime/texture-format.js': '10af8fd92813c7872eecf51b203c01a4e6ebc79a4c5fa7d38661a12192efbcfe',
  'src/csl/metal-division.js': '104cda4fda758fcdfd20f69264a92c1190830102814aec8aa9706058642ce2a8',
  'src/csl/metal-reciprocal-data.js': '08905259e72a066e77675f98b9700d6c3a6467662f5de562d8f8e1e14d082c87',
  'src/csl/metal-reciprocal-grid.js': 'bd6613830c4239ff9b21a4157875a7c92ced898fd706e735527f39552be11e39',
};
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const cpuRoot = process.argv[2];
if (!cpuRoot) throw new Error('usage: reference.mjs CPU_ROOT');
const scratch = await mkdtemp(resolve(tmpdir(), 'grade-current-reference-'));
try {
  await writeFile(resolve(scratch, 'package.json'), '{"type":"module"}');
  // Authenticate the complete import closure before executing any CPU code.
  for (const [name, digest] of Object.entries(hashes)) {
    const source = resolve(cpuRoot, name);
    if (!(await lstat(source)).isFile()) throw new Error(`CPU source must be a regular file: ${name}`);
    const bytes = await readFile(source);
    if (sha(bytes) !== digest) throw new Error(`CPU source hash mismatch: ${name}`);
    await mkdir(dirname(resolve(scratch, name)), {recursive: true});
    await writeFile(resolve(scratch, name), bytes);
  }
  authenticateCpuRoot(cpuRoot);
  const {canonicalKernelFactories} = await import(pathToFileURL(resolve(scratch, 'src/effects/generated/canonical-kernels.js')));
  const {bindGlslKernel} = await import(pathToFileURL(resolve(scratch, 'src/csl/glsl-runtime.js')));
  const {Surface} = await import(pathToFileURL(resolve(scratch, 'src/runtime/surface.js')));
  const {quantizeTexture} = await import(pathToFileURL(resolve(scratch, 'src/runtime/texture-format.js')));
  const raw = [], rgba8 = [];
  for (const color of [[.2, .6666667, .46666667, .8], [.91, .13, .37, 1]]) {
    for (let preset = 0; preset <= 22; ++preset) for (const alpha of [0, .25, .5, .9553096459809837, 1]) {
      const inputTex = new Surface(1, 1, new Float32Array(color));
      const kernel = bindGlslKernel(canonicalKernelFactories['filter/grade:lut'], {
        inputTex, preset, alpha, tileOffset: [0, 0], fullResolution: [1, 1],
      });
      const output = new Surface(1, 1);
      kernel({fragCoord: [.5, .5, 0, 1], uv: [.5, .5], resolution: [1, 1]}, output.data);
      quantizeTexture(output, 'rgba16f');
      const words = new Uint32Array(output.data.buffer), bytes = Buffer.alloc(16);
      for (let lane = 0; lane < 4; ++lane) bytes.writeUInt32LE(words[lane], lane * 4);
      raw.push(bytes);
      rgba8.push(...output.toRgba8());
    }
  }
  console.log(JSON.stringify({cpu_revision: '9b7294820eec2a0b95c66790b1dae374fa079c13',
    source_hashes: hashes, pixels: raw.length, float32_sha256: sha(Buffer.concat(raw)),
    rgba8_sha256: sha(Buffer.from(rgba8))}));
} finally {
  await rm(scratch, {recursive: true, force: true});
}
