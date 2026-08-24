// GAP 3b — direct sampler-vs-sampler comparison, JS side. READ-ONLY
// consumer of the real, unmodified noisemaker-for-cpu sampler
// (src/runtime/sampler.js: sampleNearestBottomLeft, sampleBilinear) and
// Surface (src/runtime/surface.js). Same 4x4 texture and (u,v) coordinate
// list as gap3b_sampler_compare.cpp, so results can be diffed directly.
//
// For each coordinate this prints THREE numbers per sampler:
//   - sampleNearestBottomLeft(surface,u,v)         [production convention,
//     matches C++'s sample_nearest_bottom_left(surface,u,v) call sites]
//   - sampleBilinear(surface,u,v)                  [naive, NO flip]
//   - sampleBilinear(surface,u,1-v)                [REAL production
//     convention -- this is exactly what glsl-runtime.js's #texture does
//     for filter==='linear', line 198]

import { sampleNearestBottomLeft, sampleBilinear } from '../noisemaker-for-cpu/src/runtime/sampler.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'
import { writeFileSync } from 'node:fs'

const W = 4, H = 4
const data = new Float32Array(W * H * 4)
for (let y = 0; y < H; y += 1) {
  for (let x = 0; x < W; x += 1) {
    const idx = (y * W + x) * 4
    const linear = y * W + x
    data[idx + 0] = linear / 16
    data[idx + 1] = x / 4
    data[idx + 2] = y / 4
    data[idx + 3] = 1
  }
}
const surface = new Surface(W, H, data)

const coords = [
  { u: 0.125, v: 0.125, label: 'interior' },
  { u: 0.5, v: 0.5, label: 'center' },
  { u: 0.9, v: 0.1, label: 'interior-2' },
  { u: 0.0, v: 0.0, label: 'boundary-00' },
  { u: 1.0, v: 1.0, label: 'boundary-11' },
  { u: 0.0, v: 1.0, label: 'boundary-01' },
  { u: 1.0, v: 0.0, label: 'boundary-10' },
  { u: -0.3, v: 0.2, label: 'neg-u' },
  { u: 1.7, v: 0.5, label: 'over-u' },
  { u: -0.01, v: -0.01, label: 'neg-both-small' },
  { u: 1.5, v: 1.5, label: 'over-both' },
  { u: -2.3, v: 3.7, label: 'far-out' },
  { u: 0.5, v: -5.0, label: 'far-neg-v' },
  { u: 5.0, v: 0.5, label: 'far-over-u' },
]

let lines = ['label,u,v,nearest_bl_r,nearest_bl_g,nearest_bl_b,nearest_bl_a,' +
  'bilinear_naive_unflipped_r,bilinear_naive_unflipped_g,bilinear_naive_unflipped_b,bilinear_naive_unflipped_a,' +
  'bilinear_production_flipped_r,bilinear_production_flipped_g,bilinear_production_flipped_b,bilinear_production_flipped_a']
const raw = []  // [nearest(4), bilinear_production_flipped(4)] per coord, matches gap3b_sampler_compare.cpp's raw layout
for (const c of coords) {
  const nearest = new Float32Array(4)
  sampleNearestBottomLeft(surface, c.u, c.v, nearest)
  const bilinearNaive = new Float32Array(4)
  sampleBilinear(surface, c.u, c.v, bilinearNaive)
  const bilinearProd = new Float32Array(4)
  sampleBilinear(surface, c.u, 1 - c.v, bilinearProd)  // real #texture convention (glsl-runtime.js:198)
  lines.push([c.label, c.u, c.v,
    ...nearest, ...bilinearNaive, ...bilinearProd].join(','))
  raw.push(...nearest, ...bilinearProd)
}
writeFileSync(new URL('./gap3b_sampler_compare_reference.csv', import.meta.url), lines.join('\n') + '\n')
writeFileSync(new URL('./gap3b_sampler_compare_reference.f32', import.meta.url), Buffer.from(new Float32Array(raw).buffer))
console.log('wrote gap3b_sampler_compare_reference.csv and .f32 (' + coords.length + ' coords)')
