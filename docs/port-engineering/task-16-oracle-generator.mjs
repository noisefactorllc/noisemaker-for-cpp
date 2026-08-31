import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

// The per-architecture capture/merge/select scaffolding is shared with
// docs/port-engineering/future-precompute/cheap-unlocks/bitwise_oracle_generator.mjs
// rather than copied into it: two near-identical copies had already drifted
// apart in strictness. The specifier resolves against THIS FILE, so the
// generator stays runnable exactly as committed from any working directory.
import {
  divergenceWhitelist,
  mergeArch,
  orderCaptures,
  requireIdenticalProvenance,
  selectArch,
} from './arch-capture.mjs'

// The JS CPU authority arrives by ENV, never by a machine-specific path.
// (Historical note, 2026-08-30: this generator used to `import
// '../noisemaker-for-cpu/...'` -- resolved against THIS FILE, i.e.
// docs/noisemaker-for-cpu -- while reading canonical-kernels.js through
// '../noisemaker-for-cpu' resolved against CWD. No single checkout layout
// satisfies both, so the generator was unrunnable exactly as committed and had
// to be mirrored into scratch to run at all. Roots now resolve from
// NOISEMAKER_CPU_ROOT or NOISEMAKER_FOR_CPU, with the historical
// sibling-of-CWD path kept as the last fallback. Imports are dynamic because
// the root is only known at run time.)
function resolveCpuRoot() {
  const candidates = [process.env.NOISEMAKER_CPU_ROOT, process.env.NOISEMAKER_FOR_CPU, '../noisemaker-for-cpu']
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

// This package's `width-one` case pins the bytes of a NaN that the HARDWARE
// manufactures (`float(x)/float(width-1)` is 0.0/0.0 at width 1). The sign of
// that NaN is an ISA property -- AArch64 `fdiv` yields 0x7fc00000, x86-64 SSE2
// `divsd` yields the "QNaN indefinite" 0xffc00000 -- and V8 does NOT
// canonicalize NaN, so the JS authority inherits it. One hash therefore cannot
// speak for both architectures; the frozen package records one capture per
// architecture. A THIRD architecture must fail loudly here rather than
// silently inherit either capture.
const SUPPORTED_ARCHES = ['arm64', 'x64']
const ARCH = process.arch
if (!SUPPORTED_ARCHES.includes(ARCH)) {
  throw new Error(`unsupported architecture "${ARCH}": this package records authority captures for ${SUPPORTED_ARCHES.join(' and ')} only -- capture ${ARCH} against the JS authority before running here`)
}
const ARCH_DIVERGENCE_REASON = 'hardware-manufactured NaN (0.0/0.0): the sign bit is an ISA property (AArch64 fdiv 0x7fc00000 vs x86-64 SSE2 divsd 0xffc00000) and V8 does not canonicalize NaN, so the JS authority itself differs per architecture. See docs/port-engineering/x86-64-divergences/x86-64-divergences-report.md.'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'task-16-oracles.json')
const key = 'filter/pixelSort:computeRank'
const cppRoot = '.'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/pixelSort/computeRank.glsl')
const canonicalKernelsPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex')
}

function bytes(value) {
  return Buffer.from(value.buffer, value.byteOffset, value.byteLength)
}

function sameBytes(left, right) {
  return left.byteLength === right.byteLength && Buffer.compare(bytes(left), bytes(right)) === 0
}

function printable(value) {
  if (Number.isNaN(value)) return 'NaN'
  if (value === Infinity) return 'Infinity'
  if (value === -Infinity) return '-Infinity'
  return value
}

function probe(surface, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  // Read the STORED bits straight out of the surface's own buffer. Never
  // re-store through `new Float32Array([value])`: on x86-64, V8 canonicalizes
  // NaN in some typed-array constructor/tier paths, so that spelling reports
  // an UNSTABLE NaN sign (observed flipping between the first and later
  // renders in one process) that does not match the bytes actually in the
  // surface. A DataView read reports what was stored, on every arch.
  const view = new DataView(surface.data.buffer, surface.data.byteOffset, surface.data.byteLength)
  const bits = []
  for (let lane = 0; lane < 4; lane += 1) {
    bits.push(`0x${view.getUint32((offset + lane) * 4, true).toString(16).padStart(8, '0')}`)
  }
  return {
    at: [x, y],
    values: values.map(printable),
    f32_bits_le: bits,
  }
}

function formulaSurface() {
  const width = 11
  const height = 9
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const lane = (y * width + x) * 4
      data[lane] = ((17 * x + 31 * y + 13) % 101) / 100
      data[lane + 1] = ((7 * x + 19 * y + 23) % 97) / 96
      data[lane + 2] = ((29 * x + 11 * y + 5) % 89) / 88
      data[lane + 3] = 0.35 + ((3 * x + 5 * y + 1) % 13) / 20
    }
  }
  return new Surface(width, height, data)
}

function flatTieSurface() {
  const width = 11
  const height = 9
  const data = new Float32Array(width * height * 4)
  for (let lane = 0; lane < data.length; lane += 4) data.set([0.5, 0.25, 0.75, 1], lane)
  return new Surface(width, height, data)
}

function widthOneSurface() {
  return new Surface(1, 1, new Float32Array([0.5, 0.25, 0.75, 1]))
}

function render(lumTex, width, height) {
  const factory = canonicalKernelFactories[key]
  if (typeof factory !== 'function') throw new Error(`missing canonical factory ${key}`)
  const kernel = bindCanonicalKernel(factory, {
    width,
    height,
    time: 0.375,
    frame: 7,
    deltaTime: 1 / 60,
    seed: 19,
    tileOffset: new Float32Array([2, 1]),
    fullResolution: new Float32Array([13, 11]),
    textures: { lumTex },
  })
  const destination = new Surface(width, height)
  runPass({ kernel, destination, time: 0.375, seed: 19 })
  return destination
}

function caseResult(name, makeSampler, width, height, coverage, construction) {
  const first = render(makeSampler(), width, height)
  const second = render(makeSampler(), width, height)
  const firstRgba8 = first.toRgba8()
  const secondRgba8 = second.toRgba8()
  if (!sameBytes(first.data, second.data) || !sameBytes(firstRgba8, secondRgba8)) {
    throw new Error(`${name}: canonical repeat was not byte-identical`)
  }
  const probes = width === 1 ? [probe(first, 0, 0)] : [probe(first, 0, 0), probe(first, 4, 3), probe(first, 8, 6)]
  return {
    name,
    output: { width, height, storage: 'top-down Float32Array; lane=(y*width+x)*4' },
    sampler: construction,
    coverage,
    f32_sha256: sha256(bytes(first.data)),
    rgba8_sha256: sha256(bytes(firstRgba8)),
    probes,
    repeat_identity: { f32_bytes: true, rgba8_bytes: true },
  }
}

function build() {
  const source = fs.readFileSync(sourcePath)
  const canonical = fs.readFileSync(canonicalKernelsPath)
  const factory = canonicalKernelFactories[key]
  const document = {
    program: {
      key,
      corpus_revision: 'a024dc3a960cc44af454abc7aebce50456c194e6',
      source: 'sources/filter/pixelSort/computeRank.glsl',
      source_sha256: sha256(source),
      defines: {},
      binding_signature: ['lumTex:sampler2D@1/S1'],
      output: 'fragColor:vec4',
    },
    provenance: {
      node: process.version,
      api: 'canonicalKernelFactories+bindCanonicalKernel+runPass+Surface',
      canonical_kernels_path: 'src/effects/generated/canonical-kernels.js',
      canonical_kernels_sha256: sha256(canonical),
      factory_to_string_sha256: sha256(Buffer.from(factory.toString(), 'utf8')),
      factory_hash_contract: 'SHA-256 of exact UTF-8 Function.prototype.toString() for canonicalKernelFactories[key]',
      generator: 'task-16-oracle-generator.mjs',
    },
    execution: {
      fragment_origin: 'bottom-left: runPass uses fragCoord=(x+0.5,height-y-0.5)',
      output_storage: 'top-down Surface Float32Array',
      sampler_storage: 'top-down Surface Float32Array; texelFetch uses GLSL bottom-left coordinates',
      float_bytes: 'host little-endian Float32Array bytes, with probe bits read little-endian',
      context: { time: 0.375, frame: 7, deltaTime: 1 / 60, seed: 19, tileOffset: [2, 1], fullResolution: [13, 11] },
      verification: 'each case is independently double-rendered; F32 and RGBA8 byte arrays must match before hashes are recorded',
    },
    cases: [
      caseResult('formula', formulaSurface, 9, 7,
        ['strict-otherLum-greater-than', 'continue-skip', 'zero-and-positive-rank', 'non-square-sampler-output', 'orientation'],
        {
          width: 11,
          height: 9,
          construction: 'R=((17*x+31*y+13)%101)/100; G=((7*x+19*y+23)%97)/96; B=((29*x+11*y+5)%89)/88; A=0.35+((3*x+5*y+1)%13)/20; each assignment stores to Float32Array',
        }),
      caseResult('flat-tie', flatTieSurface, 9, 7,
        ['equal-luminance-tie-break', 'sampleX-less-than-x', 'continue-skip', 'zero-and-positive-rank', 'non-square-sampler-output'],
        { width: 11, height: 9, construction: 'every texel is Float32Array [0.5,0.25,0.75,1]' }),
      caseResult('width-one', widthOneSurface, 1, 1,
        ['width-minus-one-zero-denominator', 'quiet-nan-blue-lane', 'all-samples-continue'],
        { width: 1, height: 1, construction: 'the single texel is Float32Array [0.5,0.25,0.75,1]' }),
    ],
  }
  return document
}

// ---------------------------------------------------------------------------
// Per-architecture capture, merge and verification.
//
// `--capture` renders on WHATEVER architecture node is running and emits that
// one architecture's document. `--freeze a.json b.json` merges one capture per
// supported architecture into the frozen package: every leaf the two captures
// agree on stays a plain scalar, and a leaf they disagree on becomes
// `{ arch_divergent, by_arch: { arm64, x64 } }` -- but ONLY at the whitelisted
// paths below. Any other disagreement, and any disagreement at all in the
// provenance leaves, throws with the offending path named; see
// ./arch-capture.mjs for why that guard belongs on the freeze path.
// `--check` re-renders on the current architecture and verifies the frozen
// package's selection for THAT architecture, plus the file's canonical
// formatting, so the gate stays meaningful on either machine.
// ---------------------------------------------------------------------------
const FROZEN_SCHEMA = 'noisemaker-for-cpp.task16-canonical-oracles.v2'
const CAPTURE_SCHEMA = 'noisemaker-for-cpp.task16-canonical-oracles.arch-capture.v1'

function captureDocument() {
  return {
    schema: CAPTURE_SCHEMA,
    arch: ARCH,
    node: process.version,
    v8: process.versions.v8,
    document: build(),
  }
}

// THE ONLY LEAVES THAT MAY DIFFER PER ARCHITECTURE, and why exactly these.
// The `width-one` case renders `float(x)/float(width-1)` = 0.0/0.0 into the
// blue lane, so its whole-surface F32 hash and that lane's raw bits carry the
// sign of a hardware-manufactured NaN. Nothing else in this package can:
// `formula` and `flat-tie` are finite on every architecture, the RGBA8 hashes
// are sign-blind because `toRgba8()` maps any NaN to 0, and every remaining
// leaf is either a recorded provenance fact or a finite computed value. Any
// other disagreement between two captures is a REAL difference -- a port bug
// on one ISA, a capture taken against the wrong authority checkout, a corpus
// revision mismatch -- and `mergeArch` throws on it, naming the path, rather
// than stamping it with the NaN explanation and minting a permanently green
// per-architecture pin out of it.
const ARCH_DIVERGENT_CASE = 'width-one'
const ARCH_DIVERGENT_LANE = 2  // blue

function allowedDivergentPaths(document) {
  const index = document.cases.findIndex((entry) => entry.name === ARCH_DIVERGENT_CASE)
  if (index < 0) throw new Error(`no "${ARCH_DIVERGENT_CASE}" case in this capture: the per-architecture divergence whitelist cannot be derived`)
  const base = `$.cases[${index}]`
  const paths = [`${base}.f32_sha256`]
  const probes = document.cases[index].probes ?? []
  for (let probeIndex = 0; probeIndex < probes.length; probeIndex += 1) {
    paths.push(`${base}.probes[${probeIndex}].f32_bits_le[${ARCH_DIVERGENT_LANE}]`)
  }
  return paths
}

// Leaves that can never legitimately be architecture-divergent, checked before
// the merge so a mismatch is reported as what it is: the corpus revision the
// source came from, the source bytes themselves, and the whole authority
// provenance block (node version, authority file hash, factory text hash).
// Captures that disagree here were taken against different checkouts, and a
// package merged from them would describe neither.
const PROVENANCE_PATHS = [
  '$.program.corpus_revision',
  '$.program.source_sha256',
  '$.provenance',
]

function freeze(captures) {
  const ordered = orderCaptures(captures, SUPPORTED_ARCHES, CAPTURE_SCHEMA)
  requireIdenticalProvenance(ordered, PROVENANCE_PATHS)
  const [first, second] = ordered
  const merged = mergeArch(first.document, second.document, first.arch, second.arch, {
    reason: ARCH_DIVERGENCE_REASON,
    allowedDivergentPaths: divergenceWhitelist(ordered, allowedDivergentPaths),
  })
  const document = {
    schema: FROZEN_SCHEMA,
    arch_captures: ordered.map((capture) => ({ arch: capture.arch, node: capture.node, v8: capture.v8 })),
    arch_divergence: {
      reason: ARCH_DIVERGENCE_REASON,
      shape: 'any leaf the architectures disagree on is recorded as { arch_divergent, by_arch: { <arch>: <value> } }; every other leaf is a plain value both architectures produced.',
      third_architecture: 'unsupported: this generator refuses to run on an architecture with no recorded capture rather than let it inherit another architecture\'s bytes.',
    },
    ...merged,
  }
  return `${JSON.stringify(document, null, 2)}\n`
}

function check() {
  const live = captureDocument()
  const frozen = JSON.parse(fs.readFileSync(outputPath, 'utf8'))
  if (frozen.schema !== FROZEN_SCHEMA) throw new Error(`${outputPath}: schema drift (${frozen.schema})`)
  const recorded = (frozen.arch_captures ?? []).find((capture) => capture.arch === ARCH)
  if (!recorded) throw new Error(`${outputPath}: no recorded capture for architecture "${ARCH}"`)
  if (recorded.node !== live.node || recorded.v8 !== live.v8) throw new Error(`${outputPath}: capture for "${ARCH}" was taken with node ${recorded.node} / V8 ${recorded.v8}, this run is node ${live.node} / V8 ${live.v8}`)
  const { schema: _schema, arch_captures: _archCaptures, arch_divergence: _archDivergence, ...body } = frozen
  const selected = selectArch(body, ARCH)
  if (JSON.stringify(selected) !== JSON.stringify(live.document)) throw new Error(`${outputPath} is not the exact frozen canonical oracle output for architecture "${ARCH}"`)
  // The structural comparison above cannot see the file's own bytes: it runs
  // on the parsed graph, so whitespace, indentation and the trailing newline
  // are invisible to it. Re-serialize the parsed document and compare it to
  // the file text, exactly as the sibling bitwise generator does, so the
  // package's canonical formatting is gated too.
  if (fs.readFileSync(outputPath, 'utf8') !== `${JSON.stringify(frozen, null, 2)}\n`) {
    throw new Error(`${outputPath} is not canonically formatted (re-serializing the parsed document does not reproduce the file bytes)`)
  }
  return `ok ${path.basename(outputPath)} (${ARCH}, node ${live.node})\n`
}

const argv = process.argv.slice(2)
if (argv.length === 1 && argv[0] === '--capture') {
  process.stdout.write(`${JSON.stringify(captureDocument(), null, 2)}\n`)
} else if (argv.length === SUPPORTED_ARCHES.length + 1 && argv[0] === '--freeze') {
  process.stdout.write(freeze(argv.slice(1).map((file) => JSON.parse(fs.readFileSync(file, 'utf8')))))
} else if (argv.length === 1 && argv[0] === '--check') {
  process.stdout.write(check())
} else {
  throw new Error('usage: node task-16-oracle-generator.mjs --check | --capture | --freeze <arm64-capture.json> <x64-capture.json>')
}
