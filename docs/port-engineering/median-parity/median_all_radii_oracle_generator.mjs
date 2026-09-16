#!/usr/bin/env node
// Source-bound exact-pixel oracle for filter/median:median, covering every
// allowed radius (1, 2, 3) -- unlike the original median_oracle_generator.mjs
// / median-oracles.json package in this same directory (kept, unmodified, as
// evidence), which the report says leaves the typed-slice integration
// "prepared-only" and does not exercise the hand-written adapter across every
// radius, size-vs-window relationship, tie/duplicate record, translucent
// input, or NaN/negative channel value.
//
// filter/median is corpus-status "adapter": the authority never runs the
// typed kernel emitted from median.glsl. It always dispatches its own
// hand-written CPU adapter (src/effects/adapters/median.js, registered in
// src/effects/adapters/index.js). That file, byte for byte, is the ground
// truth this generator measures.
//
// Usage:
//   node median_all_radii_oracle_generator.mjs --cpu-root <immutable authority checkout> --write
//   node median_all_radii_oracle_generator.mjs --cpu-root <immutable authority checkout> --check
//
// --write regenerates median-all-radii-oracles.json (+ .sha256 sidecar) and
// the human-readable report. --check re-derives every case and every source-
// anchor mutation probe from scratch and confirms the checked-in files are
// byte-identical AND that the checked-in sha256 sidecars still verify -- two
// independent runs against the same immutable snapshot produce the exact
// same bytes.
import crypto from 'node:crypto'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'median-all-radii-oracles.json')
const reportPath = path.join(here, 'median-all-radii-oracle-report.md')
const programKey = 'filter/median:median'
const factorySourceRelative = 'src/effects/adapters/median.js'

const sha256 = v => crypto.createHash('sha256').update(v).digest('hex')
function checked(target, payload) {
  fs.writeFileSync(target, payload)
  fs.writeFileSync(`${target}.sha256`, `${sha256(payload)}  ${path.basename(target)}\n`)
}
function verifySidecar(target) {
  const payload = fs.readFileSync(target)
  const sidecar = fs.readFileSync(`${target}.sha256`, 'utf8')
  if (sidecar !== `${sha256(payload)}  ${path.basename(target)}\n`) {
    throw new Error(`sidecar drift: ${target}`)
  }
  return payload
}

const argv = process.argv.slice(2)
const mode = argv.filter(x => ['--write', '--check'].includes(x))
if (mode.length !== 1) throw new Error('choose exactly one of --write or --check')
const ci = argv.indexOf('--cpu-root')
if (ci < 0 || ci + 1 >= argv.length) throw new Error('--cpu-root <immutable snapshot> is required')
const cpuRootArg = path.resolve(argv[ci + 1])
const st = fs.lstatSync(cpuRootArg)
if (st.isSymbolicLink() || !st.isDirectory()) throw new Error('--cpu-root must be a non-symlink directory')
const cpuRoot = fs.realpathSync(cpuRootArg)

const factoryPath = path.join(cpuRoot, factorySourceRelative)
const factorySource = fs.readFileSync(factoryPath, 'utf8')
const factorySha256 = sha256(factorySource)

// A minimal duck-typed Surface: medianFactory's kernel reads only
// `.width`/`.height`/`.data` (see src/runtime/surface.js's real Surface for
// the shape this mirrors). Row 0 is the TOP of the image, matching
// noisemaker::Surface::from_rgba8/the raw-float32 Surface constructor on the
// C++ side -- medianKernel's own `surface.height - 1 - y` flip is what maps
// GL fragCoord (bottom origin) onto this top-down storage, exactly as
// noisemaker::texel_fetch_bottom_left does in the native port.
function makeInputTexture(width, height, pixelFn) {
  const data = new Float32Array(width * height * 4)
  for (let row = 0; row < height; row += 1) {
    for (let col = 0; col < width; col += 1) {
      const [r, g, b, a] = pixelFn(col, row, width, height)
      const base = (row * width + col) * 4
      data[base + 0] = Math.fround(r)
      data[base + 1] = Math.fround(g)
      data[base + 2] = Math.fround(b)
      data[base + 3] = Math.fround(a)
    }
  }
  return { width, height, data }
}

function makeContext(width, height, fragX, fragY) {
  return {
    fragCoord: [fragX, fragY],
    uv: [fragX / width, fragY / height],
    resolution: [width, height],
  }
}

// medianKernel calls only `$runtime.beginPixel(context)` -- everything else
// is untyped plain JS/Math against `$bindings`, this is a hand-written
// adapter, not an IR-emitted kernel.
function makeRuntime() {
  return { beginPixel() {} }
}

function byteFromFloat(value) {
  // Mirrors noisemaker::byte_from_float (src/surface.cpp) exactly, so the
  // frozen RGBA8 bytes below compare byte-for-byte against
  // Surface::to_rgba8() with no independent rounding drift. NaN is neither
  // finite nor `<= 0`/`>= 1`, so it falls through to `Math.floor(NaN*255+0.5)`
  // = NaN, which this mirrors by returning 0 for any non-finite value up
  // front -- matching byte_from_float's own `std::isfinite` gate.
  if (!Number.isFinite(value) || value <= 0) return 0
  if (value >= 1) return 255
  return Math.floor(value * 255 + 0.5)
}

async function loadFactory(sourcePath) {
  const module = await import(pathToFileURL(sourcePath).href + `?cachebust=${process.pid}-${Math.random()}`)
  return module.medianFactory
}

function runCase(factory, spec) {
  const { width, height, radius, threshold, pixelFn } = spec
  const bindings = Object.freeze({
    inputTex: makeInputTexture(width, height, pixelFn),
    RADIUS: radius,
    threshold,
  })
  const runtime = makeRuntime()
  const kernel = factory(bindings, runtime)
  const floatWords = new Array(width * height * 4)
  const rgba8 = new Array(width * height * 4)
  const out = new Float32Array(4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const fragX = x + 0.5
      const fragY = height - y - 0.5
      const context = makeContext(width, height, fragX, fragY)
      out.fill(0)
      kernel(context, out)
      const base = (y * width + x) * 4
      for (let lane = 0; lane < 4; lane += 1) {
        const value = Math.fround(out[lane])
        floatWords[base + lane] = `0x${Buffer.from(Float32Array.of(value).buffer).readUInt32LE(0).toString(16).padStart(8, '0')}`
        rgba8[base + lane] = byteFromFloat(value)
      }
    }
  }
  return { floatWords, rgba8 }
}

// --- Pixel generators -------------------------------------------------
// Deterministic, non-constant gradient: every channel varies with position
// so no two pixels are accidentally identical unless a case deliberately
// wants that (the tie/duplicate generators below).
function gradientPixel(col, row, width, height) {
  const r = (col + 1) / (width + 1)
  const g = (row + 1) / (height + 1)
  const b = ((col * 3 + row * 5) % 11) / 10
  const a = 1
  return [r, g, b, a]
}

// A 2-color checkerboard: every window at radius>=1 on a size this small
// contains multiple pixels with the EXACT same (r, g, b) -- a genuine full-
// tuple duplicate, not just a brightness tie -- forcing the fixed-pivot
// selection loop to run against records the `<` comparisons call equal.
function checkerboardPixel(col, row) {
  const on = (col + row) % 2 === 0
  return on ? [0.75, 0.25, 0.5, 1] : [0.2, 0.6, 0.1, 1]
}

// Two colors with DIFFERENT red and DIFFERENT green (so their packed
// redGreen keys differ) but the SAME `Math.fround`-chained luminance bit
// pattern (a genuine brightness tie), found by a brute-force scan of the
// authority's own floatToHalf/luminance formula: with blue fixed at 0.5,
// red=0 and red=0.505 both land on luminance bit pattern 1056964607. This
// forces the pivot's tie-break down to the packed redGreen key -- exactly
// the second comparator level (`redGreen[record] < pivotRedGreen`) the
// `tiebreak-redgreen-direction` mutation below targets.
//
// (A brightness-AND-redGreen tie with DIFFERENT blue turns out to be
// unconstructible: for fixed red/green, blue contributes to luminance via a
// bare `+ fround(blue * 0.0722)` with no compensating term, and a blue
// change large enough to shift its packed half-code is, at every magnitude
// in [0, 1], far larger than the float32 rounding granularity of the sum --
// so it always also changes brightness. The `blue[record] < pivotBlue`
// comparator is consequently only ever evaluated between bit-identical
// blue values, and its direction is therefore provably unobservable; no
// mutation of it belongs in this file.)
function redGreenTiePixel(col, row) {
  const on = (col + row) % 2 === 0
  return on ? [0, 0.6486297249794006, 0.5, 1] : [0.5049999952316284, 0.49851369857788086, 0.5, 1]
}

function translucentRampPixel(col, row, width) {
  const r = (col + 1) / (width + 1)
  const g = (row + 2) / 9
  const b = 1 - r
  const a = (col % 5) / 4 // 0, 0.25, 0.5, 0.75, 1 cycling
  return [r, g, b, a]
}

function hdrAndNegativePixel(col, row) {
  // Center pixel (radius=1, 3x3) plus its ring: mixes a negative red
  // channel and a >1 (HDR) green/blue channel with ordinary values. Negative
  // float32 values order OPPOSITE their unsigned bit pattern relative to
  // positive ones -- this proves the port compares raw bit patterns exactly
  // as median.js does (`floatBits`), never a "helpful" numeric comparison.
  const values = [
    [-0.3, 1.6, 0.2, 1], [0.1, 0.2, 0.3, 1], [-0.1, 1.9, 0.4, 1],
    [0.5, 0.05, 1.7, 1], [0.05, -0.6, 0.05, 1], [0.9, 0.3, -0.2, 1],
    [-1.5, 0.4, 0.4, 1], [0.2, 0.2, 0.2, 1], [1.3, -0.4, 0.9, 1],
  ]
  return values[row * 3 + col]
}

function nanChannelPixel(col, row) {
  // A single pixel (the window center at radius>=1, 3x3) carries a NaN red
  // channel; every other sample is an ordinary finite gradient value.
  if (row === 1 && col === 1) return [Number.NaN, 0.4, 0.6, 1]
  return gradientPixel(col, row, 3, 3)
}

// --- Case matrix --------------------------------------------------------
// Every allowed radius (1, 2, 3), sizes both matching and strictly smaller
// than that radius's window (2*radius+1) in one or both dimensions, non-
// square sizes, ties/duplicates at two different tuple levels, a
// translucent-alpha ramp, HDR/negative channel values, a NaN channel, and a
// small threshold sweep on one fixed input.
// `generator` names the pixelFn so the native test (tests/test_median_kernel.cpp)
// can rebuild the identical input Surface in C++ without duplicating case-by-
// case pixel data -- it re-implements each named generator once and looks it
// up by this tag, the same way this file looks up `pixelFn`.
const cases = [
  { name: 'r1-3x3-window-exact', width: 3, height: 3, radius: 1, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r1-1x1-heavy-clamp', width: 1, height: 1, radius: 1, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r2-5x5-window-exact', width: 5, height: 5, radius: 2, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r2-2x2-heavy-clamp', width: 2, height: 2, radius: 2, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r2-7x4-nonsquare', width: 7, height: 4, radius: 2, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r3-7x7-window-exact', width: 7, height: 7, radius: 3, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r3-3x3-heavy-clamp', width: 3, height: 3, radius: 3, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r3-9x5-nonsquare', width: 9, height: 5, radius: 3, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r3-1x9-strip', width: 1, height: 9, radius: 3, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r2-9x11-transposed', width: 9, height: 11, radius: 2, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r2-ties-checkerboard', width: 6, height: 6, radius: 2, threshold: 0, generator: 'checkerboard', pixelFn: checkerboardPixel },
  { name: 'r1-ties-redgreen-tiebreak', width: 3, height: 3, radius: 1, threshold: 0, generator: 'redGreenTie', pixelFn: redGreenTiePixel },
  { name: 'r2-translucent-ramp', width: 5, height: 4, radius: 2, threshold: 0, generator: 'translucentRamp', pixelFn: translucentRampPixel },
  { name: 'r1-hdr-and-negative', width: 3, height: 3, radius: 1, threshold: 0, generator: 'hdrAndNegative', pixelFn: hdrAndNegativePixel },
  { name: 'r2-nan-channel', width: 3, height: 3, radius: 2, threshold: 0, generator: 'nanChannel', pixelFn: nanChannelPixel },
  { name: 'r3-nan-with-threshold', width: 3, height: 3, radius: 3, threshold: 50, generator: 'nanChannel', pixelFn: nanChannelPixel },
  { name: 'r2-threshold-zero', width: 4, height: 4, radius: 2, threshold: 0, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r2-threshold-mid', width: 4, height: 4, radius: 2, threshold: 12, generator: 'gradient', pixelFn: gradientPixel },
  { name: 'r2-threshold-hundred', width: 4, height: 4, radius: 2, threshold: 100, generator: 'gradient', pixelFn: gradientPixel },
]

// Small, source-anchored mutations. Each replaces an exact, unique substring
// of median.js in a scratch copy, re-runs the FULL case matrix through the
// mutated module, and records which cases changed. `requiredWitnessCases`
// pins at least one case that MUST change for every mutation below -- a
// mutation that changes nothing would mean the oracle is not actually
// sensitive to that source region.
const mutations = [
  {
    name: 'luminance-red-weight',
    anchor: 'red * 0.2126',
    replacement: 'red * 0.3',
    requiredWitnessCases: ['r2-5x5-window-exact'],
  },
  {
    name: 'luminance-green-weight',
    anchor: 'green * 0.7152',
    replacement: 'green * 0.8',
    requiredWitnessCases: ['r3-7x7-window-exact'],
  },
  {
    name: 'half-round-bias',
    anchor: 'fraction += 0x1000',
    replacement: 'fraction += 0x0800',
    requiredWitnessCases: ['r3-7x7-window-exact'],
  },
  {
    name: 'median-index-formula',
    anchor: 'const medianIndex = (count - 1) >> 1',
    replacement: 'const medianIndex = (count + 1) >> 1',
    requiredWitnessCases: ['r2-5x5-window-exact'],
  },
  {
    name: 'threshold-divisor',
    anchor: '$bindings.threshold / 100',
    replacement: '$bindings.threshold / 10',
    requiredWitnessCases: ['r2-threshold-mid'],
  },
  {
    name: 'half-exponent-bias',
    anchor: 'Math.pow(2, exponent - 15) * (1 + fraction / 1024)',
    replacement: 'Math.pow(2, exponent - 14) * (1 + fraction / 1024)',
    requiredWitnessCases: ['r1-3x3-window-exact'],
  },
  {
    name: 'tiebreak-redgreen-direction',
    anchor: 'redGreen[record] < pivotRedGreen',
    replacement: 'redGreen[record] > pivotRedGreen',
    requiredWitnessCases: ['r1-ties-redgreen-tiebreak'],
  },
]

async function runFullMatrix(factory) {
  const results = {}
  for (const spec of cases) results[spec.name] = runCase(factory, spec)
  return results
}

function compareResults(a, b) {
  let changedFloat = 0
  let changedRgba8 = 0
  for (let index = 0; index < a.floatWords.length; index += 1) {
    if (a.floatWords[index] !== b.floatWords[index]) changedFloat += 1
    if (a.rgba8[index] !== b.rgba8[index]) changedRgba8 += 1
  }
  return { changedFloat, changedRgba8, differs: changedFloat > 0 }
}

async function main() {
  const canonicalFactory = await loadFactory(factoryPath)
  const canonical = await runFullMatrix(canonicalFactory)

  const scratchDir = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'median-oracle-'))
  try {
    const mutationResults = []
    for (const mutation of mutations) {
      const occurrences = factorySource.split(mutation.anchor).length - 1
      if (occurrences !== 1) {
        throw new Error(`mutation ${mutation.name}: anchor must occur exactly once (found ${occurrences})`)
      }
      const mutatedSource = factorySource.replace(mutation.anchor, mutation.replacement)
      const mutatedPath = path.join(scratchDir, `median.${mutation.name}.mjs`)
      fs.writeFileSync(mutatedPath, mutatedSource)
      const mutatedFactory = await loadFactory(mutatedPath)
      const mutatedRun = await runFullMatrix(mutatedFactory)
      const perCase = cases.map(spec => ({
        name: spec.name,
        ...compareResults(canonical[spec.name], mutatedRun[spec.name]),
      }))
      const changedCaseNames = perCase.filter(item => item.differs).map(item => item.name)
      for (const required of mutation.requiredWitnessCases) {
        if (!changedCaseNames.includes(required)) {
          throw new Error(
            `mutation ${mutation.name}: required witness case ${required} did not change -- ` +
            'oracle is not sensitive to this source region')
        }
      }
      mutationResults.push({
        name: mutation.name,
        anchor: mutation.anchor,
        replacement: mutation.replacement,
        anchorSha256: sha256(mutation.anchor),
        replacementSha256: sha256(mutation.replacement),
        results: perCase,
        changedCases: changedCaseNames,
      })
    }

    const document = {
      schema: 'noisemaker-for-cpp.median.pixel-parity.v2-all-radii',
      schemaVersion: 1,
      programKey,
      sourceRelativePath: factorySourceRelative,
      sourceBytes: factorySource.length,
      sourceSha256: factorySha256,
      exactFloat32: true,
      exactRgba8: true,
      toleranceNone: true,
      comparisonOrder: 'dimensions, then every float32 word, then every RGBA8 byte',
      inputTextureRule: 'raw Float32Array RGBA data (Math.fround per channel), row 0 is the top of the image',
      cases: cases.map(spec => ({
        name: spec.name,
        width: spec.width,
        height: spec.height,
        generator: spec.generator,
        controls: { radius: spec.radius, threshold: spec.threshold },
        outputFloat32Words: canonical[spec.name].floatWords,
        outputRgba8: canonical[spec.name].rgba8,
        outputFloat32Sha256: sha256(canonical[spec.name].floatWords.join(',')),
        outputRgba8Sha256: sha256(Buffer.from(canonical[spec.name].rgba8)),
      })),
      mutations: mutationResults,
    }
    const payload = JSON.stringify(document, null, 2) + '\n'

    if (mode[0] === '--write') {
      checked(outputPath, payload)
      const reportLines = [
        '# filter/median:median all-radii pixel-parity oracle',
        '',
        `Source: \`${factorySourceRelative}\` (${factorySource.length} bytes, sha256 ${factorySha256})`,
        '',
        `${cases.length} cases, ${mutations.length} source-anchor mutation probes.`,
        '',
        'Supersedes nothing -- the original median_oracle_generator.mjs / ' +
          'median-oracles.json package in this directory is kept as evidence. ' +
          'This package additionally covers radius 1 and 3 (not just 2), sizes ' +
          'smaller than the kernel window, ties/duplicate records at two ' +
          'different comparator levels, a translucent-alpha ramp, HDR and ' +
          'negative channel values, a NaN channel, and a threshold sweep.',
        '',
        '## Cases',
        '',
        ...cases.map(spec => `- \`${spec.name}\` (${spec.width}x${spec.height}, radius=${spec.radius}, threshold=${spec.threshold})`),
        '',
        '## Mutation sensitivity',
        '',
        ...mutationResults.map(item => `- \`${item.name}\`: changed ${item.changedCases.length}/${cases.length} cases (${item.changedCases.join(', ')})`),
        '',
      ]
      checked(reportPath, reportLines.join('\n'))
      process.stdout.write(`wrote ${outputPath} and ${reportPath}\n`)
      return
    }

    // --check: the checked-in files must verify against their own sidecars
    // AND must be byte-identical to a from-scratch re-derivation -- this is
    // the oracle determinism proof.
    const existingPayload = verifySidecar(outputPath)
    verifySidecar(reportPath)
    if (existingPayload.toString() !== payload) {
      throw new Error('median-all-radii-oracles.json is stale: re-run with --write')
    }
    process.stdout.write('median all-radii oracle is deterministic and matches the checked-in files\n')
  } finally {
    fs.rmSync(scratchDir, { recursive: true, force: true })
  }
}

main().catch(error => {
  process.stderr.write(`${error.stack || error}\n`)
  process.exitCode = 1
})
