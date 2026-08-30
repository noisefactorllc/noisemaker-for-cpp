import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

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
// agree on stays a plain scalar, and every leaf they disagree on becomes
// `{ arch_divergent, by_arch: { arm64, x64 } }` so the divergence is explicit
// and attributable rather than hidden in a single hash. `--check` re-renders
// on the current architecture and verifies the frozen package's selection for
// THAT architecture, so the gate stays meaningful on either machine.
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

function isPlainObject(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function mergeArch(left, right, leftArch, rightArch, at) {
  if (JSON.stringify(left) === JSON.stringify(right)) return left
  if (Array.isArray(left) && Array.isArray(right)) {
    if (left.length !== right.length) throw new Error(`${at}: captures disagree on array length (${left.length} vs ${right.length}) -- that is a structural difference, not an arch materialization difference`)
    return left.map((value, index) => mergeArch(value, right[index], leftArch, rightArch, `${at}[${index}]`))
  }
  if (isPlainObject(left) && isPlainObject(right)) {
    const leftKeys = Object.keys(left)
    const rightKeys = Object.keys(right)
    if (leftKeys.join('\u0000') !== rightKeys.join('\u0000')) throw new Error(`${at}: captures disagree on object keys -- that is a structural difference, not an arch materialization difference`)
    const merged = {}
    for (const objectKey of leftKeys) merged[objectKey] = mergeArch(left[objectKey], right[objectKey], leftArch, rightArch, `${at}.${objectKey}`)
    return merged
  }
  return { arch_divergent: ARCH_DIVERGENCE_REASON, by_arch: { [leftArch]: left, [rightArch]: right } }
}

function selectArch(node, arch, at) {
  if (isPlainObject(node) && Object.prototype.hasOwnProperty.call(node, 'arch_divergent') && isPlainObject(node.by_arch)) {
    if (!Object.prototype.hasOwnProperty.call(node.by_arch, arch)) throw new Error(`${at}: frozen package has no capture for architecture "${arch}"`)
    return selectArch(node.by_arch[arch], arch, at)
  }
  if (Array.isArray(node)) return node.map((value, index) => selectArch(value, arch, `${at}[${index}]`))
  if (isPlainObject(node)) {
    const selected = {}
    for (const objectKey of Object.keys(node)) selected[objectKey] = selectArch(node[objectKey], arch, `${at}.${objectKey}`)
    return selected
  }
  return node
}

function freeze(captures) {
  if (captures.length !== SUPPORTED_ARCHES.length) throw new Error(`--freeze needs exactly ${SUPPORTED_ARCHES.length} captures, one per supported architecture`)
  for (const capture of captures) {
    if (capture.schema !== CAPTURE_SCHEMA) throw new Error(`capture schema drift: ${capture.schema}`)
    if (!SUPPORTED_ARCHES.includes(capture.arch)) throw new Error(`capture records unsupported architecture "${capture.arch}"`)
  }
  const ordered = SUPPORTED_ARCHES.map((arch) => {
    const matches = captures.filter((capture) => capture.arch === arch)
    if (matches.length !== 1) throw new Error(`expected exactly one capture for architecture "${arch}", got ${matches.length}`)
    return matches[0]
  })
  const [first, second] = ordered
  const merged = mergeArch(first.document, second.document, first.arch, second.arch, '$')
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
  const selected = selectArch(body, ARCH, '$')
  if (JSON.stringify(selected) !== JSON.stringify(live.document)) throw new Error(`${outputPath} is not the exact frozen canonical oracle output for architecture "${ARCH}"`)
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
