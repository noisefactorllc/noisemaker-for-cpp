#!/usr/bin/env node
// Source-bound exact-pixel oracle for filter/snow:snow.
//
// filter/snow is corpus-status "adapter": the authority never runs a
// typed-generated kernel for this program. It always dispatches the
// hand-written CPU adapter `snowFactory` (src/effects/adapters/snow.js).
// That file, byte for byte, is the ground truth this generator measures --
// not the GLSL source under tools/glslcpp/corpus/.../filter/snow/snow.glsl,
// which the authority never executes for this program at all.
//
// Usage:
//   node snow_oracle_generator.mjs --cpu-root <immutable authority checkout> --write
//   node snow_oracle_generator.mjs --cpu-root <immutable authority checkout> --check
//
// --write regenerates snow-oracles.json (+ its .sha256 sidecar) and the
// human-readable report. --check re-derives every case and the mutation
// sensitivity probes from scratch and confirms the checked-in files are
// byte-identical AND that the checked-in sha256 sidecars still verify --
// this is the "oracle determinism" proof: two independent runs of this
// generator, against the same immutable snapshot, produce the exact same
// bytes.
import crypto from 'node:crypto'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const outputPath = path.join(here, 'snow-oracles.json')
const reportPath = path.join(here, 'snow-oracle-report.md')
const programKey = 'filter/snow:snow'
const factorySourceRelative = 'src/effects/adapters/snow.js'

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

// A minimal duck-typed Surface: snow.js's texelOffset() reads only
// `.width`/`.height`, and the kernel reads only `.data` -- see
// src/runtime/surface.js's own Surface for the real shape this mirrors.
// Row 0 is the TOP of the image (matches noisemaker::Surface::from_rgba8 on
// the C++ side): texelOffset's own y-flip is what maps GL fragCoord (bottom
// origin) onto this top-down storage, exactly as
// noisemaker::texel_fetch_bottom_left does in the native port.
function makeInputTexture(width, height) {
  const data = new Float32Array(width * height * 4)
  for (let index = 0; index < data.length; index += 1) {
    // Same deterministic byte pattern as the native test fixture
    // (patterned_seed in tests/test_graph_features.cpp), pushed through
    // Surface::from_rgba8's own float32 conversion (byte / 255).
    const byteValue = (index * 37 + 11) % 256
    data[index] = Math.fround(byteValue / 255)
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

// A minimal $runtime: snowFactory never calls anything on it except
// beginPixel (see the kernel body) -- everything else is untyped plain
// JS/Math, this is a hand-written adapter, not an IR-emitted kernel.
function makeRuntime() {
  return {
    beginPixel(context) {
      if (!context.uv) throw new Error('context.uv is required')
      void context.uv[0]
      void context.uv[1]
    },
  }
}

function f32(value) { return Math.fround(value) }
function byteFromFloat(value) {
  // Mirrors noisemaker::byte_from_float (src/surface.cpp) exactly, so the
  // frozen RGBA8 bytes below compare byte-for-byte against
  // Surface::to_rgba8() with no independent rounding drift.
  if (!Number.isFinite(value) || value <= 0) return 0
  if (value >= 1) return 255
  return Math.floor(value * 255 + 0.5)
}

async function loadFactory(sourcePath) {
  const module = await import(pathToFileURL(sourcePath).href + `?cachebust=${process.pid}-${Math.random()}`)
  return module.snowFactory
}

function runCase(factory, spec) {
  const { width, height, alpha, time, pause, density } = spec
  const bindings = Object.freeze({ inputTex: makeInputTexture(width, height), alpha, time, pause, density })
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
        const value = f32(out[lane])
        floatWords[base + lane] = `0x${Buffer.from(Float32Array.of(value).buffer).readUInt32LE(0).toString(16).padStart(8, '0')}`
        rgba8[base + lane] = byteFromFloat(value)
      }
    }
  }
  return { floatWords, rgba8 }
}

// Case matrix: sizes (including non-square), every parameter extreme that
// changes control flow, and enough seed/time spread to exercise
// snowNoise's two branches (time===0 exactly vs. not, and the
// z_base epsilon ternary in the same function) at multiple pixels.
const cases = [
  { name: '1x1-alpha-zero', width: 1, height: 1, alpha: 0, time: 0.25, pause: 0, density: 50 },
  { name: '1x1-alpha-one', width: 1, height: 1, alpha: 1, time: 0.25, pause: 0, density: 50 },
  { name: '3x1-time-zero', width: 3, height: 1, alpha: 0.5, time: 0, pause: 0, density: 50 },
  { name: '1x3-pause-true', width: 1, height: 3, alpha: 0.5, time: 0.6, pause: 1, density: 50 },
  { name: '4x3-pause-boundary-exact', width: 4, height: 3, alpha: 0.5, time: 0.6, pause: 0.5, density: 50 },
  { name: '4x3-pause-boundary-just-above', width: 4, height: 3, alpha: 0.5, time: 0.6, pause: 0.500001, density: 50 },
  { name: '4x3-pause-between-tenth-and-half', width: 4, height: 3, alpha: 0.5, time: 0.6, pause: 0.3, density: 50 },
  { name: '5x7-density-zero', width: 5, height: 7, alpha: 0.75, time: 0.9, pause: 0, density: 0 },
  { name: '5x7-density-negative', width: 5, height: 7, alpha: 0.75, time: 0.9, pause: 0, density: -10 },
  { name: '5x7-density-hundred', width: 5, height: 7, alpha: 0.75, time: 0.9, pause: 0, density: 100 },
  { name: '5x7-density-above-range', width: 5, height: 7, alpha: 0.75, time: 0.9, pause: 0, density: 250 },
  { name: '7x5-alpha-near-zero', width: 7, height: 5, alpha: 1e-4, time: 1.75, pause: 0, density: 40 },
  { name: '7x5-alpha-above-one', width: 7, height: 5, alpha: 1.5, time: 1.75, pause: 0, density: 40 },
  { name: '7x5-alpha-below-zero', width: 7, height: 5, alpha: -0.5, time: 1.75, pause: 0, density: 40 },
  // time=0.25 lands cos(time*TAU) at ~-4.4e-8, already below the real
  // epsilon (1e-7) -- zBase is 0 either side of the mutation below. This
  // case instead uses time=1.75, whose cosine (~6.6e-7) sits strictly
  // between the real epsilon and the mutated one, so the mutation flips it.
  { name: '9x2-cosine-just-above-epsilon', width: 9, height: 2, alpha: 0.6, time: 1.75, pause: 0, density: 60 },
  { name: '2x9-cosine-near-half-turn', width: 2, height: 9, alpha: 0.6, time: 0.5, pause: 0, density: 60 },
  { name: '2x9-cosine-near-full-turn', width: 2, height: 9, alpha: 0.6, time: 1.0, pause: 0, density: 60 },
  { name: '17x11-default-like', width: 17, height: 11, alpha: 0.5, time: 0.25, pause: 0, density: 75 },
  { name: '17x11-large-time', width: 17, height: 11, alpha: 0.5, time: 137.375, pause: 0, density: 75 },
  { name: '11x17-transposed', width: 11, height: 17, alpha: 0.5, time: 0.25, pause: 0, density: 75 },
  { name: '13x1-negative-time', width: 13, height: 1, alpha: 0.5, time: -3.5, pause: 0, density: 75 },
]

// Small, source-anchored mutations. Each replaces an exact, unique
// substring of snow.js in a scratch copy, re-runs the FULL case matrix
// through the mutated module, and records which cases changed. A
// mutation that changes nothing would mean the oracle is not actually
// sensitive to that source region -- `requiredWitnessCases` pins at least
// one case that MUST change for every mutation below.
const mutations = [
  {
    name: 'pause-threshold',
    anchor: 'const time = $bindings.pause > 0.5 ? 0 : $bindings.time',
    replacement: 'const time = $bindings.pause > 0.1 ? 0 : $bindings.time',
    requiredWitnessCases: ['4x3-pause-between-tenth-and-half'],
  },
  {
    name: 'static-seed-x',
    anchor: 'const STATIC_SEED = new Float32Array([37, 17, 53])',
    replacement: 'const STATIC_SEED = new Float32Array([38, 17, 53])',
    requiredWitnessCases: ['17x11-default-like'],
  },
  {
    name: 'limiter-seed-x',
    anchor: 'const LIMITER_SEED = new Float32Array([113, 71, 193])',
    replacement: 'const LIMITER_SEED = new Float32Array([114, 71, 193])',
    requiredWitnessCases: ['17x11-default-like'],
  },
  {
    name: 'density-scale',
    anchor: 'const density = Math.max(mul($bindings.density, F32(0.01)), F32(0.0001))',
    replacement: 'const density = Math.max(mul($bindings.density, F32(0.02)), F32(0.0001))',
    requiredWitnessCases: ['17x11-default-like'],
  },
  {
    name: 'limiter-cap',
    anchor: 'const limiterMask = mul(F32(Math.pow(Math.min(limiterValue, F32(0.99)), exponent)), alpha)',
    replacement: 'const limiterMask = mul(F32(Math.pow(Math.min(limiterValue, F32(0.5)), exponent)), alpha)',
    requiredWitnessCases: ['17x11-default-like'],
  },
  {
    name: 'time-seed-offset-x',
    anchor: 'const TIME_SEED_OFFSETS = new Float32Array([97, 57, 131])',
    replacement: 'const TIME_SEED_OFFSETS = new Float32Array([98, 57, 131])',
    requiredWitnessCases: ['17x11-large-time'],
  },
  {
    name: 'zbase-epsilon',
    anchor: 'const zBase = Math.abs(cosineValue) < F32(0.0000001) ? 0 : mul(cosineValue, speed)',
    replacement: 'const zBase = Math.abs(cosineValue) < F32(0.5) ? 0 : mul(cosineValue, speed)',
    requiredWitnessCases: ['9x2-cosine-just-above-epsilon'],
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

  const scratchDir = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'snow-oracle-'))
  try {
    const mutationResults = []
    for (const mutation of mutations) {
      const occurrences = factorySource.split(mutation.anchor).length - 1
      if (occurrences !== 1) {
        throw new Error(`mutation ${mutation.name}: anchor must occur exactly once (found ${occurrences})`)
      }
      const mutatedSource = factorySource.replace(mutation.anchor, mutation.replacement)
      const mutatedPath = path.join(scratchDir, `snow.${mutation.name}.mjs`)
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
      schema: 'noisemaker-for-cpp.snow.pixel-parity.v1',
      schemaVersion: 1,
      programKey,
      sourceRelativePath: factorySourceRelative,
      sourceBytes: factorySource.length,
      sourceSha256: factorySha256,
      exactFloat32: true,
      exactRgba8: true,
      toleranceNone: true,
      comparisonOrder: 'dimensions, then every float32 word, then every RGBA8 byte',
      inputTextureRule:
        'Surface::from_rgba8((index*37+11)%256 per byte), row 0 is the top of the image',
      cases: cases.map(spec => ({
        name: spec.name,
        width: spec.width,
        height: spec.height,
        controls: { alpha: spec.alpha, time: spec.time, pause: spec.pause, density: spec.density },
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
        '# filter/snow:snow pixel-parity oracle',
        '',
        `Source: \`${factorySourceRelative}\` (${factorySource.length} bytes, sha256 ${factorySha256})`,
        '',
        `${cases.length} cases, ${mutations.length} source-anchor mutation probes.`,
        '',
        '## Cases',
        '',
        ...cases.map(spec => `- \`${spec.name}\` (${spec.width}x${spec.height}, alpha=${spec.alpha}, time=${spec.time}, pause=${spec.pause}, density=${spec.density})`),
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
      throw new Error('snow-oracles.json is stale: re-run with --write')
    }
    process.stdout.write('snow oracle is deterministic and matches the checked-in files\n')
  } finally {
    fs.rmSync(scratchDir, { recursive: true, force: true })
  }
}

main().catch(error => {
  process.stderr.write(`${error.stack || error}\n`)
  process.exitCode = 1
})
