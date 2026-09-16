// Re-derivation script for the `generated_invert_linear_width_three_matches_js_exact_bits_and_nearest_default`
// native test (tests/test_generated_kernels.cpp), part of the 0ed489ec46842bffba33ee2ec65a218b6dda51f5
// resync (CPU authority 61aa869). See docs/runbook conventions used by sibling
// docs/port-engineering/task-*-oracle-generator.mjs scripts for the resolveCpuRoot() pattern.
//
// Contract reproduced from the native test: a 3x1 Surface constructed directly from
// 12 raw float32 samples (NOT from RGBA8 bytes), run once with `filter = 'linear'`
// and once with the JS Surface default filter (nearest/bottom-left, i.e. `filter`
// left unset), through the canonical `filter/invert:inv` kernel with no `mode`
// uniform bound (so `mode == 1` is false and the kernel takes the default/else
// branch). The output surface is the same 3x1 extent. We print the raw Float32
// output data as hex bit patterns (via Float32Array + DataView, matching the
// C++ side's `float_bits_to_uint`), for direct comparison against the frozen
// `js_linear_bits` / `js_nearest_bits` arrays in the test.
//
// Usage: NOISEMAKER_CPU_ROOT=<authority dir> node invert_linear_width_three_oracle_generator.mjs

import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

function resolveCpuRoot() {
  const candidates = [process.env.NOISEMAKER_CPU_ROOT, process.env.NOISEMAKER_FOR_CPU]
  for (const candidate of candidates) {
    if (!candidate) continue
    const root = path.resolve(candidate)
    if (fs.existsSync(path.join(root, 'src/effects/catalog.js'))) return root
  }
  throw new Error('JS authority not found: set NOISEMAKER_CPU_ROOT (or NOISEMAKER_FOR_CPU) to a noisemaker-for-cpu checkout')
}
const cpuRoot = resolveCpuRoot()
const authority = (relative) => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const { canonicalKernelFactories } = await authority('src/effects/catalog.js')
const { bindCanonicalKernel } = await authority('src/csl/glsl-kernel.js')
const { runPass } = await authority('src/runtime/pass-runner.js')
const { Surface } = await authority('src/runtime/surface.js')

const PIXELS = new Float32Array([
  0.0, 0.125, 0.25, 1.0,
  1.0, 0.5, 0.75, 0.5,
  0.0, 0.875, 0.375, 0.25,
])

function bitsHex(f32) {
  const view = new DataView(new ArrayBuffer(4))
  view.setFloat32(0, f32, true)
  return '0x' + view.getUint32(0, true).toString(16).padStart(8, '0')
}

function runInvert(filter) {
  const input = new Surface(3, 1, PIXELS.slice())
  if (filter) input.filter = filter
  const kernel = bindCanonicalKernel(canonicalKernelFactories['filter/invert:inv'], {
    width: 3,
    height: 1,
    textures: { inputTex: input },
  })
  const destination = new Surface(3, 1)
  runPass({ kernel, destination })
  return destination.data
}

const linear = runInvert('linear')
const nearest = runInvert(undefined)

console.log('js_linear_bits:')
console.log(Array.from(linear).map(bitsHex).join(', '))
console.log('js_nearest_bits:')
console.log(Array.from(nearest).map(bitsHex).join(', '))
