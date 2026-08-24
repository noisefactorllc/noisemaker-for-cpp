import { createHash } from 'node:crypto'
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { basename, join, relative, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const IDENTITY = 'synth/gradient:gradient'
const SCHEMA = 'noisemaker-cpp-gradient-oracle-v2'
const CANONICAL_SOURCE = 'src/effects/generated/canonical-kernels.js'
const ALIAS_NEEDLE = 'var rotatedCentered = centered;'
const ALIAS_REPLACEMENT = 'var rotatedCentered = new $runtime.PooledFloat32Array(centered);'
const SOURCE_FILES = Object.freeze([
  'package.json',
  'package-lock.json',
  CANONICAL_SOURCE,
  'src/csl/glsl-kernel.js',
  'src/runtime/pass-runner.js',
  'src/runtime/surface.js',
])
const WITNESS = Object.freeze({
  width: 6,
  height: 5,
  time: 0.25,
  seed: 7,
  uniforms: Object.freeze({
    gradientType: 1,
    rotation: 0.4,
    repeat: 4,
    speed: 0,
    colorCount: 2,
    color1: [0, 0, 0],
    color2: [1, 1, 1],
    color3: [0.5, 0.5, 0.5],
    color4: [0.2, 0.2, 0.2],
  }),
})

const here = new URL('.', import.meta.url)
const DEFAULT_JSON = new URL('./gradient_expected.json', here)

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex')
}

function countExact(source, needle) {
  let count = 0
  let offset = 0
  while (true) {
    const found = source.indexOf(needle, offset)
    if (found < 0) return count
    count += 1
    offset = found + needle.length
  }
}

function transformCanonicalSource(source) {
  const matchCount = countExact(source, ALIAS_NEEDLE)
  if (matchCount !== 1) {
    throw new Error(`Gradient alias transform requires exactly one match; found ${matchCount}`)
  }
  const transformed = source.replace(ALIAS_NEEDLE, ALIAS_REPLACEMENT)
  if (countExact(transformed, ALIAS_NEEDLE) !== 0
      || countExact(transformed, ALIAS_REPLACEMENT) !== 1) {
    throw new Error('Gradient alias transform did not produce one exact replacement')
  }
  return { matchCount, canonicalSource: source, transformed }
}

async function writeSidecar(path, bytes) {
  await writeFile(`${path}.sha256`, `${sha256(bytes)}  ${basename(path)}\n`)
}

function parseArgs(argv) {
  const args = { cpuRoot: null, json: filePath(DEFAULT_JSON), mode: 'check' }
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '--cpu-root' || arg === '--json') {
      const value = argv[++index]
      if (!value) throw new Error(`${arg} requires a value`)
      if (arg === '--cpu-root') args.cpuRoot = value
      else args.json = resolve(value)
    } else if (arg === '--write' || arg === '--check' || arg === '--self-test'
               || arg === '--assert-mutant-equals-authority') {
      args.mode = arg.slice(2)
    } else {
      throw new Error(`unknown argument: ${arg}`)
    }
  }
  if (!args.cpuRoot) throw new Error('--cpu-root is required')
  return args
}

function filePath(url) {
  return fileURLToPath(url)
}

async function importAuthority(cpuRoot) {
  const root = resolve(cpuRoot)
  const moduleAt = (name) => import(pathToFileURL(join(root, name)).href)
  const [{ canonicalKernelFactories }, { bindCanonicalKernel, createCanonicalBindings },
    { runPass }, { Surface }] = await Promise.all([
    moduleAt('src/effects/generated/canonical-kernels.js'),
    moduleAt('src/csl/glsl-kernel.js'),
    moduleAt('src/runtime/pass-runner.js'),
    moduleAt('src/runtime/surface.js'),
  ])
  if (!Object.isFrozen(canonicalKernelFactories)) {
    throw new Error('canonical factory registry must be immutable')
  }
  const factory = canonicalKernelFactories[IDENTITY]
  if (typeof factory !== 'function') throw new Error(`missing canonical factory: ${IDENTITY}`)
  return { root, factory, bindCanonicalKernel, createCanonicalBindings, runPass, Surface }
}

async function provenance(root) {
  const sources = {}
  for (const name of SOURCE_FILES) {
    const bytes = await readFile(join(root, name))
    sources[name] = { bytes: bytes.length, sha256: sha256(bytes) }
  }
  return {
    cpu_root: '<CPU_ROOT>',
    source_files: sources,
    public_identity: IDENTITY,
    factory_export: 'canonicalKernelFactories["synth/gradient:gradient"]',
    binding_api: ['createCanonicalBindings', 'bindCanonicalKernel', 'runPass', 'Surface'],
    forbidden_authorities: [
      'canonicalAdapterFactories',
      'effects/adapters/',
      'effects/catalog.js',
      'runtime/cpu-frame-export.js',
    ],
  }
}

async function renderFactory(factory, authority) {
  const { width, height } = WITNESS
  const options = {
    width,
    height,
    time: WITNESS.time,
    seed: WITNESS.seed,
    uniforms: {
      ...WITNESS.uniforms,
      color1: new Float32Array(WITNESS.uniforms.color1),
      color2: new Float32Array(WITNESS.uniforms.color2),
      color3: new Float32Array(WITNESS.uniforms.color3),
      color4: new Float32Array(WITNESS.uniforms.color4),
    },
  }
  const destination = new authority.Surface(width, height)
  authority.createCanonicalBindings(options)
  const kernel = authority.bindCanonicalKernel(factory, options)
  authority.runPass({ kernel, destination })
  const words = Array.from(new Uint32Array(destination.data.buffer),
                           (bits) => `0x${bits.toString(16).padStart(8, '0')}`)
  return { words, bytes: Array.from(destination.toRgba8()) }
}

async function renderAuthority(authority) {
  return renderFactory(authority.factory, authority)
}

async function renderUnaliasedMutant(authority, source) {
  const tempRoot = await mkdtemp(join(tmpdir(), 'noisemaker-gradient-mutant-'))
  const modulePath = join(tempRoot, 'canonical-kernels.mjs')
  try {
    await writeFile(modulePath, source)
    const module = await import(`${pathToFileURL(modulePath).href}?gradient-mutant`)
    if (!Object.isFrozen(module.canonicalKernelFactories)) {
      throw new Error('mutant canonical factory registry must be immutable')
    }
    const factory = module.canonicalKernelFactories[IDENTITY]
    if (typeof factory !== 'function') throw new Error(`mutant missing canonical factory: ${IDENTITY}`)
    return renderFactory(factory, authority)
  } finally {
    await rm(tempRoot, { recursive: true, force: true })
  }
}

function compareExact(canonical, mutant) {
  const words = []
  for (let index = 0; index < canonical.words.length; index += 1) {
    if (canonical.words[index] !== mutant.words[index]) words.push(index)
  }
  const bytes = []
  for (let index = 0; index < canonical.bytes.length; index += 1) {
    if (canonical.bytes[index] !== mutant.bytes[index]) bytes.push(index)
  }
  const first = (values, left, right) => values.length === 0 ? null : ({
    index: values[0], canonical: left[values[0]], mutant: right[values[0]],
  })
  return {
    float32_word_difference_count: words.length,
    rgba8_byte_difference_count: bytes.length,
    first_float32_mismatch: first(words, canonical.words, mutant.words),
    first_rgba8_mismatch: first(bytes, canonical.bytes, mutant.bytes),
  }
}

function buildRecord(sourceProvenance, output, transform, comparison) {
  return {
    schema: SCHEMA,
    identity: IDENTITY,
    witness: WITNESS,
    provenance: sourceProvenance,
    output,
    mutant_ledger: {
      status: 'fail-closed',
      kind: 'unaliased-temporary-emission',
      transform: {
        needle: ALIAS_NEEDLE,
        replacement: ALIAS_REPLACEMENT,
        match_count: transform.matchCount,
        canonical_source_sha256: sha256(Buffer.from(transform.canonicalSource)),
        transformed_source_sha256: sha256(Buffer.from(transform.transformed)),
      },
      comparison,
      acceptance: 'the executable transform must produce nonzero exact divergence; no hard-coded ledger is trusted',
    },
  }
}

function assertRecord(record) {
  if (record.schema !== SCHEMA || record.identity !== IDENTITY) throw new Error('oracle identity mismatch')
  if (record.provenance?.cpu_root !== '<CPU_ROOT>') throw new Error('unstable CPU root provenance')
  if (record.provenance.factory_export !== 'canonicalKernelFactories["synth/gradient:gradient"]') {
    throw new Error('foreign or adapter factory provenance')
  }
  if (!Array.isArray(record.provenance.binding_api)
      || record.provenance.binding_api.join(',') !== 'createCanonicalBindings,bindCanonicalKernel,runPass,Surface') {
    throw new Error('live or non-canonical binding API')
  }
  const expectedLength = WITNESS.width * WITNESS.height * 4
  if (record.output?.words?.length !== expectedLength || record.output?.bytes?.length !== expectedLength) {
    throw new Error('incomplete exact witness')
  }
  const ledger = record.mutant_ledger
  const comparison = ledger?.comparison
  if (ledger?.status !== 'fail-closed'
      || ledger.transform?.needle !== ALIAS_NEEDLE
      || ledger.transform?.replacement !== ALIAS_REPLACEMENT
      || ledger.transform?.match_count !== 1
      || !/^[0-9a-f]{64}$/.test(ledger.transform?.canonical_source_sha256 ?? '')
      || !/^[0-9a-f]{64}$/.test(ledger.transform?.transformed_source_sha256 ?? '')
      || comparison?.float32_word_difference_count <= 0
      || comparison?.rgba8_byte_difference_count <= 0
      || comparison?.first_float32_mismatch == null
      || comparison?.first_rgba8_mismatch == null) {
    throw new Error('unproven unaliased mutant')
  }
}

async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv)
  const authority = await importAuthority(args.cpuRoot)
  const canonicalSource = await readFile(join(authority.root, CANONICAL_SOURCE), 'utf8')
  const transform = transformCanonicalSource(canonicalSource)
  const output = await renderAuthority(authority)
  const mutant = await renderUnaliasedMutant(authority, transform.transformed)
  const comparison = compareExact(output, mutant)
  const record = buildRecord(await provenance(authority.root), output, transform, comparison)
  assertRecord(record)
  const serialized = `${JSON.stringify(record, null, 2)}\n`
  if (args.mode === 'assert-mutant-equals-authority') {
    if (comparison.float32_word_difference_count !== 0
        || comparison.rgba8_byte_difference_count !== 0) {
      throw new Error(`temporary mutant differs from authority: ${comparison.float32_word_difference_count} Float32 words, ${comparison.rgba8_byte_difference_count} RGBA8 bytes`)
    }
    console.log('temporary mutant unexpectedly matches authority')
    return
  }
  if (args.mode === 'self-test') {
    assertRecord(JSON.parse(serialized))
    const existing = await readFile(args.json, 'utf8')
    if (existing !== serialized) throw new Error('oracle self-test reproducibility mismatch')
    console.log('gradient oracle self-test: ok')
    return
  }
  let existing = null
  try { existing = await readFile(args.json, 'utf8') } catch (error) {
    if (args.mode === 'check' && error.code !== 'ENOENT') throw error
  }
  if (args.mode === 'write') {
    await writeFile(args.json, serialized)
    await writeSidecar(args.json, Buffer.from(serialized))
    const scriptPath = filePath(import.meta.url)
    const scriptBytes = await readFile(scriptPath)
    await writeSidecar(scriptPath, scriptBytes)
    console.log(`gradient oracle write: ${relative(process.cwd(), args.json)}`)
  } else if (existing !== serialized) {
    throw new Error(`gradient oracle check failed: ${args.json}`)
  } else {
    const jsonSidecar = await readFile(`${args.json}.sha256`, 'utf8')
    if (jsonSidecar !== `${sha256(Buffer.from(existing))}  ${basename(args.json)}\n`) {
      throw new Error('gradient oracle JSON sidecar mismatch')
    }
    const scriptPath = filePath(import.meta.url)
    const scriptSidecar = await readFile(`${scriptPath}.sha256`, 'utf8')
    const scriptBytes = await readFile(scriptPath)
    if (scriptSidecar !== `${sha256(scriptBytes)}  ${basename(scriptPath)}\n`) {
      throw new Error('gradient oracle script sidecar mismatch')
    }
    console.log('gradient oracle check: ok')
  }
}

main().catch((error) => {
  console.error(error.stack || error.message)
  process.exitCode = 1
})
