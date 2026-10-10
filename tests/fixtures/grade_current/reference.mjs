import {readFile, lstat, mkdtemp, mkdir, writeFile, rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';

const hashes = {
  'src/effects/generated/canonical-kernels.js': 'eda3ca5153d7759cbf9e92982cc8579c2474828f770d29343c38dc31fcac9904',
  'src/csl/glsl-runtime.js': 'b47fa69f3358822c314315ad985c14c94fff5c973ff98fe953d7304135b84722',
  'src/runtime/sampler.js': '1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328',
  'src/runtime/surface.js': '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
  'src/runtime/texture-format.js': '10af8fd92813c7872eecf51b203c01a4e6ebc79a4c5fa7d38661a12192efbcfe',
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
  console.log(JSON.stringify({cpu_revision: '5b686a45b5c56329adf0c63cbcf572eb6f23fad1',
    source_hashes: hashes, pixels: raw.length, float32_sha256: sha(Buffer.concat(raw)),
    rgba8_sha256: sha(Buffer.from(rgba8))}));
} finally {
  await rm(scratch, {recursive: true, force: true});
}
