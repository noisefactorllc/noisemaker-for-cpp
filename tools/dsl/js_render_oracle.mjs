#!/usr/bin/env node
/*
 * Authenticated public CPU render oracle for the Task 6 blur vertical slice.
 *
 * This program deliberately has no update mode.  Generation writes only to
 * an explicitly external scratch directory; --check compares those bytes with
 * reviewed repository data and never rewrites either expected artifact.
 */
import fs from 'node:fs'
import crypto from 'node:crypto'
import os from 'node:os'
import path from 'node:path'
import process from 'node:process'
import { pathToFileURL } from 'node:url'

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..')
// The oracle ledger and the frozen CPU authority live outside the repository
// at machine-specific locations, so both must arrive by environment.
const LEDGER_PATH = process.env.NOISEMAKER_ORACLE_LEDGER ? path.resolve(process.env.NOISEMAKER_ORACLE_LEDGER) : ''
const AUTHORITY_LEDGER_ROOT = process.env.NOISEMAKER_CPU_ROOT ? path.resolve(process.env.NOISEMAKER_CPU_ROOT) : ''
const EXPECTED_LEDGER_ENTRIES = 713
const EXPECTED_NODE_MAJOR = 22
const CPU_PACKAGE_SHA256 = 'c7d8aec82725078b4d31d379323901e83bdfba0a0289ff8428beecdac2c9d78a'
const CPU_PACKAGE_LOCK_SHA256 = '724bfaf208346605cae0ce9a74d0e84c76dd3aeb8fedb44fb894ad03c4dad03d'
const CPU_SOURCE_LOCK_SHA256 = 'd1d43bfcb241c0e064ad5048fc45443145ad0d3de971a64aee199a865db45029'
const CPU_BEHAVIORAL_LOCK_SHA256 = 'e2d52e1b9891c3adf8897922d4eeb6312b93fe4d78868ff7db814a7d7668dcc7'
const UPSTREAM_REVISION = '117a236679d1db3ab8f0e278230ece277b57564c'
const UPSTREAM_SOURCE_DIGEST = '66f4e9337810ca839dddaba047dadc0c15e903e0f662f189ee6d08ff84fb62c4'
const UPSTREAM_TREE = 'a7a997dfdc807697adba008729dcdfdfcfbaf53c'
const UPSTREAM_PACKAGE_SHA256 = '109e0617b53eca612d6265672e010744ee3284aea26555eee1f614c3ddc33c8a'
const UPSTREAM_PACKAGE_LOCK_SHA256 = '033762c49845652b36ea91b75653c63ed62c45bd2fb455ab66567ff4b356109f'
const SOURCE_LOCK_SENTINEL = `PINNED_UPSTREAM_REVISION = '${UPSTREAM_REVISION}'`
const SOURCE_DIGEST_SENTINEL = `PINNED_SOURCE_DIGEST = '${UPSTREAM_SOURCE_DIGEST}'`
const CONSTANT_SOURCE_SHA256 = 'c3a9da6bc816effcaf750a386d1024c4d309cc000ef7cf9c9315843a4cb3df2c'
const NONCONSTANT_SOURCE_SHA256 = '6190f788d4d5f23895ff57f5234ac11fc3790c6b80912d91d08635fb99b42d80'
const BACKEND_MANIFEST_SHA256 = '1540c94aa7ce03a314cd3d49f9d809dae19353842b93630a40554460f3ba6f0c'
const TYPED_MANIFEST_SHA256 = 'cd75f67413143d9841b0cdc1149e468edf6b2ab54183b504a43bf68de8e210e4'
const TYPED_SLICE_SHA256 = '698d2e0a1aa700dd8c3bb923c6ff9211159ace35ee4b3d9594f05ae7442ec913'

const CLOSURE_PATHS = [
  'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/csl/runtime.js',
  'src/dsl/compiler.js', 'src/dsl/error.js', 'src/dsl/parser.js', 'src/dsl/tokenize.js',
  'src/effects/adapters/bit-effects.js', 'src/effects/adapters/crt.js', 'src/effects/adapters/f32-color.js',
  'src/effects/adapters/fractal.js', 'src/effects/adapters/index.js', 'src/effects/adapters/julia.js',
  'src/effects/adapters/median.js', 'src/effects/adapters/palette.js', 'src/effects/adapters/snow.js',
  'src/effects/catalog.js', 'src/effects/cpu/billboard-deposit.js', 'src/effects/cpu/flow3d-deposit.js',
  'src/effects/cpu/points-deposit.js', 'src/effects/cpu/scatter-registry.js', 'src/effects/cpu/worm-overlay.js',
  'src/effects/cpu/wormhole.js', 'src/effects/definition.js', 'src/effects/generated/canonical-adapter-data.js',
  'src/effects/generated/canonical-kernels.js', 'src/effects/generated/kernels.js',
  'src/effects/generated/upstream-snapshot.js', 'src/effects/registry.js', 'src/runtime/buffer-pool.js',
  'src/runtime/cpu-frame-export.js', 'src/runtime/frame-export.js', 'src/runtime/iteration.js',
  'src/runtime/pass-runner.js', 'src/runtime/render-result.js', 'src/runtime/renderer.js',
  'src/runtime/sampler.js', 'src/runtime/sink.js', 'src/runtime/surface.js', 'src/runtime/texture-format.js',
]

const CASES = [
  {
    name: 'constant-7x5', identifier: 'kConstant7x5', fixture: 'constant', width: 7, height: 5,
    time: 0.25, frame: 0, seed: 17, seedBytes: null,
    sha256: '488342e4dc1f8a338a094df4466f5d2fa21db347578fef67efcb1714cc694f92',
  },
  {
    name: 'constant-11x9', identifier: 'kConstant11x9', fixture: 'constant', width: 11, height: 9,
    time: 0.25, frame: 0, seed: 17, seedBytes: null,
    sha256: '9b645146126a59aa3beba16e108932567283173a5641036927385b8d2337d7af',
  },
  {
    name: 'nonconstant-5x3', identifier: 'kNonconstant5x3', fixture: 'nonconstant', width: 5, height: 3,
    time: 0, frame: 0, seed: 11, seedBytes: '112b47ff363658ec5b4169d9804c7ac6a5578bb3467a64f86b8582e59090a0d2b59bbebfdaa6dcac7bc981f1a0d4acdec5dfd7cbeaea02b80ff52da5',
    sha256: 'e5f2f4135e339cd40919565acc2d3d7cb4493c54d7ca0c59dfd681bd42cb7ffb',
  },
  {
    name: 'nonconstant-7x4', identifier: 'kNonconstant7x4', fixture: 'nonconstant', width: 7, height: 4,
    time: 0, frame: 0, seed: 11, seedBytes: '112b47ff363658ec5b4169d9804c7ac6a5578bb3ca629ca0ef6dad8d467a64f86b8582e59090a0d2b59bbebfdaa6dcacffb1fa9924bc18867bc981f1a0d4acdec5dfd7cbeaea02b80ff52da534005892590b83ffb0189eead523d6d7fa2e0ec41f3946b144447e9e694fb68b8e5aeef8',
    sha256: 'f8dbfe36fee9b3bb464681c1e4878c12daef9b0e7c7bdcb202a511489229d445',
  },
]

function fail(message) {
  console.error(`js_render_oracle: ${message}`)
  process.exitCode = 2
  throw new Error(message)
}

function usage(message) {
  if (message) console.error(`js_render_oracle: ${message}`)
  console.error('usage: node js_render_oracle.mjs --cpu-root ABS --fixture FILE [--nonconstant-fixture FILE] [--output ABS] [--check INCLUDE --metadata JSON] [--scratch ABS]')
  process.exit(2)
}

const args = process.argv.slice(2)
if (args.includes('--update')) usage('--update is unsupported; expected bytes are immutable')
function arg(name) {
  const index = args.indexOf(name)
  return index < 0 ? null : args[index + 1] ?? usage(`${name} requires a value`)
}
const cpuRootArg = arg('--cpu-root')
const constantFixtureArg = arg('--fixture')
const nonconstantFixtureArg = arg('--nonconstant-fixture')
const outputArg = arg('--output')
const checkArg = arg('--check')
const metadataArg = arg('--metadata')
const scratchArg = arg('--scratch')
if (!cpuRootArg || !path.isAbsolute(cpuRootArg)) usage('explicit absolute --cpu-root is required')
if (!constantFixtureArg) usage('--fixture is required')
if (checkArg && !metadataArg) usage('--metadata is required with --check')
if (metadataArg && !checkArg) usage('--check is required with --metadata')
if (outputArg && !path.isAbsolute(outputArg)) usage('--output must be an absolute external path')
if (scratchArg && !path.isAbsolute(scratchArg)) usage('--scratch must be an absolute external path')

function digest(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex') }
function readBytes(file) { return fs.readFileSync(file) }
function realPathOrFail(file, label) {
  const candidate = path.resolve(file)
  if (!fs.existsSync(candidate)) fail(`${label} does not exist: ${candidate}`)
  const stat = fs.lstatSync(candidate)
  if (stat.isSymbolicLink()) fail(`${label} must not be a symlink: ${candidate}`)
  if (!stat.isFile()) fail(`${label} must be a regular file: ${candidate}`)
  const real = fs.realpathSync(candidate)
  if (real !== candidate) fail(`${label} must not escape its real path: ${candidate}`)
  return candidate
}
function rootOrFail(rootArg) {
  const root = path.resolve(rootArg)
  if (!fs.existsSync(root)) fail(`CPU root is not a directory: ${root}`)
  const stat = fs.lstatSync(root)
  if (stat.isSymbolicLink()) fail('CPU root must be a real directory, not a symlink')
  if (!stat.isDirectory()) fail(`CPU root is not a directory: ${root}`)
  if (fs.realpathSync(root) !== root) fail('CPU root must be a real directory, not a symlink')
  return root
}
function moduleKey(root, file) {
  const relative = path.relative(root, file)
  if (relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) fail('CPU import closure escapes the CPU root')
  return relative.split(path.sep).join('/')
}

function requireLedgerEnvironment() {
  if (!LEDGER_PATH || !AUTHORITY_LEDGER_ROOT) fail('NOISEMAKER_ORACLE_LEDGER and NOISEMAKER_CPU_ROOT must name the oracle ledger and the frozen CPU authority')
}

function verifyLedger() {
  requireLedgerEnvironment()
  const ledger = realPathOrFail(LEDGER_PATH, 'oracle ledger')
  const lines = readBytes(ledger).toString('utf8').split(/\r?\n/).filter(Boolean)
  if (lines.length !== EXPECTED_LEDGER_ENTRIES) fail(`oracle ledger entry count mismatch: expected ${EXPECTED_LEDGER_ENTRIES}, received ${lines.length}`)
  let okay = 0
  for (const line of lines) {
    const match = line.match(/^([0-9a-f]{64})  (.+)$/)
    if (!match) fail('oracle ledger has a malformed entry')
    const file = realPathOrFail(match[2], 'oracle ledger file')
    if (digest(readBytes(file)) !== match[1]) fail(`oracle ledger sha256 mismatch: ${match[2]}`)
    okay += 1
  }
  if (okay !== EXPECTED_LEDGER_ENTRIES) fail('oracle ledger authentication did not cover every entry')
}

function verifyPinnedRoot(root) {
  const packagePath = realPathOrFail(path.join(root, 'package.json'), 'CPU package.json')
  const packageLockPath = realPathOrFail(path.join(root, 'package-lock.json'), 'CPU package-lock.json')
  const sourceLockPath = realPathOrFail(path.join(root, 'scripts/upstream/source-lock.js'), 'CPU source-lock.js')
  if (digest(readBytes(packagePath)) !== CPU_PACKAGE_SHA256) fail('CPU package.json sha256 mismatch')
  if (digest(readBytes(packageLockPath)) !== CPU_PACKAGE_LOCK_SHA256) fail('CPU package-lock.json sha256 mismatch')
  if (digest(readBytes(sourceLockPath)) !== CPU_SOURCE_LOCK_SHA256) fail('CPU source-lock.js sha256 mismatch')
  const packageText = readBytes(packagePath).toString('utf8')
  if (!packageText.includes('"node": ">=22"')) fail('CPU package Node engine lock is missing')
  const sourceLockText = readBytes(sourceLockPath).toString('utf8')
  if (!sourceLockText.includes(SOURCE_LOCK_SENTINEL) || !sourceLockText.includes(SOURCE_DIGEST_SENTINEL)) fail('CPU upstream source lock sentinel mismatch')
  const behavioralFiles = []
  function collect(directory) {
    const entries = fs.readdirSync(directory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))
    for (const entry of entries) {
      const file = path.join(directory, entry.name)
      if (entry.isSymbolicLink()) fail(`CPU behavioral source must not contain a symlink: ${file}`)
      if (entry.isDirectory()) collect(file)
      else if (entry.isFile()) behavioralFiles.push(file)
      else fail(`CPU behavioral source contains a non-file: ${file}`)
    }
  }
  collect(path.join(root, 'src'))
  behavioralFiles.push(sourceLockPath, packagePath, packageLockPath)
  behavioralFiles.sort((left, right) => path.relative(root, left).localeCompare(path.relative(root, right)))
  const behavioralHash = crypto.createHash('sha256')
  for (const file of behavioralFiles) {
    const relative = path.relative(root, file).split(path.sep).join('/')
    const bytes = readBytes(file)
    behavioralHash.update(relative); behavioralHash.update('\0'); behavioralHash.update(String(bytes.length)); behavioralHash.update('\0'); behavioralHash.update(bytes)
  }
  if (behavioralFiles.length !== 90 || behavioralHash.digest('hex') !== CPU_BEHAVIORAL_LOCK_SHA256) fail('CPU behavioral lock mismatch')
  const snapshotPath = realPathOrFail(path.join(root, 'src/effects/generated/upstream-snapshot.js'), 'authenticated upstream snapshot')
  if (!readBytes(snapshotPath).toString('utf8').includes(`UPSTREAM_REVISION = "${UPSTREAM_REVISION}"`)) fail('CPU upstream revision lock mismatch')
  if (CPU_BEHAVIORAL_LOCK_SHA256.length !== 64 || UPSTREAM_TREE.length !== 40) fail('CPU behavioral/upstream locks are malformed')
}

function authenticateClosure(root) {
  requireLedgerEnvironment()
  const ledgerBytes = readBytes(realPathOrFail(LEDGER_PATH, 'oracle ledger')).toString('utf8')
  const ledgerHashes = new Map()
  for (const line of ledgerBytes.split(/\r?\n/).filter(Boolean)) {
    const match = line.match(/^([0-9a-f]{64})  (.+)$/)
    if (match && match[2].startsWith(`${AUTHORITY_LEDGER_ROOT}/`)) ledgerHashes.set(path.relative(AUTHORITY_LEDGER_ROOT, match[2]).split(path.sep).join('/'), match[1])
  }
  if (ledgerHashes.size < CLOSURE_PATHS.length) fail('oracle ledger does not contain the complete public render closure')
  for (const relative of CLOSURE_PATHS) {
    const file = realPathOrFail(path.join(root, relative), `CPU import ${relative}`)
    const expected = ledgerHashes.get(relative)
    if (!expected) fail(`oracle ledger has no pinned closure hash for ${relative}`)
    if (digest(readBytes(file)) !== expected) fail(`CPU import authority sha256 mismatch: ${relative}`)
  }
}

function verifyInputs(constantFixture, nonconstantFixture) {
  const constantBytes = readBytes(realPathOrFail(constantFixture, 'constant fixture'))
  if (digest(constantBytes) !== CONSTANT_SOURCE_SHA256 || constantBytes.length !== 90 || !constantBytes.equals(Buffer.from('search synth, filter\nsolid(color: #3a7).blur(radiusX: 3, radiusY: 2).write(o0)\nrender(o0)\n'))) fail('constant fixture source sha256/bytes mismatch')
  const nonconstantBytes = readBytes(realPathOrFail(nonconstantFixture, 'nonconstant fixture'))
  if (digest(nonconstantBytes) !== NONCONSTANT_SOURCE_SHA256 || !nonconstantBytes.equals(Buffer.from('search filter\nread(o0).blur(radiusX: 2, radiusY: 5).write(o1)\nrender(o1)\n'))) fail('nonconstant fixture source sha256/bytes mismatch')
  return { constant: constantBytes.toString('utf8'), nonconstant: nonconstantBytes.toString('utf8') }
}

function makeSeed(caseInfo) {
  if (!caseInfo.seedBytes) return null
  const bytes = Buffer.from(caseInfo.seedBytes, 'hex')
  if (bytes.length !== caseInfo.width * caseInfo.height * 4) fail(`seed fixture length mismatch for ${caseInfo.name}`)
  if (digest(bytes) !== (caseInfo.name === 'nonconstant-5x3' ? 'f02d62692ee2f31dac54a1ac2bedeeff17cf0574708af2d9d4351f76071f1a8e' : '6bb487d962da7f644ac676de575c00a2c6eaf7fa6c204b55fc6c728604d6cc54')) fail(`seed fixture sha256 mismatch for ${caseInfo.name}`)
  return bytes
}

function compareExpectedInclude(includePath, outputs) {
  const bytes = readBytes(realPathOrFail(includePath, 'checked expected include')).toString('utf8')
  const pinnedStrings = [
    ['kConstantSourceSha256', CONSTANT_SOURCE_SHA256], ['kNonconstantSourceSha256', NONCONSTANT_SOURCE_SHA256],
    ...CASES.map((caseInfo) => [`${caseInfo.identifier}Sha256`, caseInfo.sha256]),
  ]
  for (const [name, expected] of pinnedStrings) {
    const match = bytes.match(new RegExp(`${name}\\s*=\\s*\\"([0-9a-f]{64})\\"`))
    if (!match || match[1] !== expected) fail(`checked expected include hash differs for ${name}`)
  }
  for (const caseInfo of CASES) {
    const match = bytes.match(new RegExp(`k${caseInfo.identifier.slice(1)}\\s*=\\s*\\{([^}]*)\\}`))
    if (!match) fail(`checked expected include lacks ${caseInfo.identifier}`)
    const listed = [...match[1].matchAll(/(?:0x)?([0-9a-fA-F]{1,2})/g)].map((item) => parseInt(item[1], 16))
    const expected = outputs.get(caseInfo.name).bytes
    if (listed.length !== expected.length || listed.some((value, index) => value !== expected[index])) fail(`checked expected include differs for ${caseInfo.name}`)
  }
}

function metadataDocument(outputs) {
  return JSON.stringify({
    schema: 'noisemaker-for-cpp.dsl-render-oracle.v1',
    authority: {
      ledger_entries: EXPECTED_LEDGER_ENTRIES, behavioral_lock_sha256: CPU_BEHAVIORAL_LOCK_SHA256,
    upstream_revision: UPSTREAM_REVISION, upstream_source_digest: UPSTREAM_SOURCE_DIGEST, upstream_tree: UPSTREAM_TREE,
      upstream_package_sha256: UPSTREAM_PACKAGE_SHA256, upstream_package_lock_sha256: UPSTREAM_PACKAGE_LOCK_SHA256,
      package_sha256: CPU_PACKAGE_SHA256, package_lock_sha256: CPU_PACKAGE_LOCK_SHA256, source_lock_sha256: CPU_SOURCE_LOCK_SHA256,
      closure_files: CLOSURE_PATHS.length, backend_manifest_sha256: BACKEND_MANIFEST_SHA256,
      typed_manifest_sha256: TYPED_MANIFEST_SHA256, typed_slice_sha256: TYPED_SLICE_SHA256,
    },
    cases: CASES.map((caseInfo) => ({
      name: caseInfo.name, fixture: caseInfo.fixture, source_sha256: caseInfo.fixture === 'constant' ? CONSTANT_SOURCE_SHA256 : NONCONSTANT_SOURCE_SHA256,
      width: caseInfo.width, height: caseInfo.height, time: caseInfo.time, frame: caseInfo.frame, seed: caseInfo.seed,
      seed_sha256: caseInfo.seedBytes ? digest(makeSeed(caseInfo)) : null,
      sha256: outputs.get(caseInfo.name).sha256, byte_length: outputs.get(caseInfo.name).bytes.length,
    })),
  }, null, 2) + '\n'
}

const REAL_ROOT = fs.realpathSync(ROOT)

function insideRoot(file) {
  return file === REAL_ROOT || file.startsWith(`${REAL_ROOT}${path.sep}`)
}

// Validate every existing path component.  In particular, resolving only the
// final path is insufficient: a missing leaf below a symlinked parent can
// still resolve into the repository after mkdir/write.
function ensureExternal(file, label, kind = 'any') {
  const candidate = path.resolve(file)
  const parsed = path.parse(candidate)
  const components = candidate.slice(parsed.root.length).split(path.sep).filter(Boolean)
  let current = parsed.root
  let nearest = parsed.root
  let finalStat = null
  for (let index = 0; index < components.length; index += 1) {
    current = path.join(current, components[index])
    let stat
    try { stat = fs.lstatSync(current) } catch (error) {
      if (error.code === 'ENOENT') break
      fail(`${label} cannot be inspected: ${candidate}`)
    }
    if (stat.isSymbolicLink()) fail(`${label} must not contain a symlink: ${current}`)
    nearest = current
    if (index === components.length - 1) finalStat = stat
  }
  const remaining = candidate.slice(nearest.length).split(path.sep).filter(Boolean)
  const resolved = path.resolve(fs.realpathSync(nearest), ...remaining)
  if (insideRoot(resolved)) fail(`${label} must resolve outside the repository`)
  if (kind === 'directory' && finalStat && !finalStat.isDirectory()) fail(`${label} must be a directory`)
  if (kind === 'file' && finalStat && finalStat.isDirectory()) fail(`${label} must be a file`)
  if (kind === 'file') {
    const parent = path.dirname(candidate)
    let parentStat
    try { parentStat = fs.lstatSync(parent) } catch (error) {
      if (error.code === 'ENOENT') fail(`${label} parent directory does not exist`)
      fail(`${label} parent directory cannot be inspected`)
    }
    if (parentStat.isSymbolicLink() || !parentStat.isDirectory()) fail(`${label} parent must be a real directory`)
    if (insideRoot(fs.realpathSync(parent))) fail(`${label} parent must resolve outside the repository`)
  }
  return candidate
}

function atomicWriteExternal(file, data, label) {
  const target = ensureExternal(file, label, 'file')
  const parent = path.dirname(target)
  const temporary = path.join(parent, `.${path.basename(target)}.${process.pid}.${crypto.randomBytes(8).toString('hex')}.tmp`)
  ensureExternal(temporary, `${label} temporary`, 'file')
  let descriptor = null
  try {
    descriptor = fs.openSync(temporary, 'wx', 0o600)
    fs.writeFileSync(descriptor, data)
    fs.fsyncSync(descriptor)
    fs.closeSync(descriptor)
    descriptor = null
    fs.renameSync(temporary, target)
  } catch (error) {
    if (descriptor !== null) fs.closeSync(descriptor)
    try { fs.unlinkSync(temporary) } catch {}
    throw error
  }
}

function defaultScratchDirectory() {
  // macOS exposes /tmp through a /var symlink.  Select the canonical private
  // temp root so the strict no-symlink policy does not disable default use.
  return fs.mkdtempSync(path.join(os.tmpdir(), 'noisemaker-dsl-render-oracle-'))
}

async function main() {
  const major = Number(process.versions.node.split('.')[0])
  if (!Number.isInteger(major) || major < EXPECTED_NODE_MAJOR) fail(`Node ${EXPECTED_NODE_MAJOR}+ is required; received ${process.versions.node}`)
  const scratch = scratchArg
    ? ensureExternal(scratchArg, 'scratch output', 'directory')
    : ensureExternal(defaultScratchDirectory(), 'scratch output', 'directory')
  const output = outputArg ? ensureExternal(outputArg, 'oracle output', 'file') : null
  verifyLedger()
  const root = rootOrFail(cpuRootArg)
  verifyPinnedRoot(root)
  authenticateClosure(root)
  const sources = verifyInputs(constantFixtureArg, nonconstantFixtureArg ?? path.join(ROOT, 'tests/fixtures/dsl/blur-nonconstant.dsl'))

  // No dynamic import appears before all authority, closure, source, and Node checks above.
  const rendererModule = await import(pathToFileURL(path.join(root, 'src/runtime/renderer.js')).href)
  const catalogModule = await import(pathToFileURL(path.join(root, 'src/effects/catalog.js')).href)
  const surfaceModule = await import(pathToFileURL(path.join(root, 'src/runtime/surface.js')).href)
  const outputs = new Map()
  for (const caseInfo of CASES) {
    const renderer = new rendererModule.CpuRenderer({
      registry: catalogModule.createDefaultRegistry(), kernels: catalogModule.kernels,
      kernelFactories: catalogModule.kernelFactories, tileRows: 32,
    })
    const seed = makeSeed(caseInfo)
    const options = { width: caseInfo.width, height: caseInfo.height, time: caseInfo.time, frame: caseInfo.frame, seed: caseInfo.seed }
    if (seed) options.seedSurfaces = { o0: surfaceModule.Surface.fromRgba8(caseInfo.width, caseInfo.height, new Uint8Array(seed)) }
    const result = renderer.render(sources[caseInfo.fixture], options)
    const rgba8 = Buffer.from(result.toRgba8())
    const required = caseInfo.width * caseInfo.height * 4
    if (rgba8.length !== required) fail(`${caseInfo.name} returned ${rgba8.length} bytes; expected ${required}`)
    const actualHash = digest(rgba8)
    if (actualHash !== caseInfo.sha256) fail(`${caseInfo.name} authority output sha256 mismatch: expected ${caseInfo.sha256}, received ${actualHash}`)
    outputs.set(caseInfo.name, { bytes: rgba8, sha256: actualHash })
  }

  fs.mkdirSync(scratch, { recursive: true })
  for (const caseInfo of CASES) atomicWriteExternal(path.join(scratch, `${caseInfo.name}.rgba8`), outputs.get(caseInfo.name).bytes, `${caseInfo.name} scratch output`)
  const metadata = metadataDocument(outputs)
  atomicWriteExternal(path.join(scratch, 'metadata.json'), metadata, 'scratch metadata')
  if (output) atomicWriteExternal(output, metadata, 'oracle output')
  if (checkArg) {
    compareExpectedInclude(checkArg, outputs)
    const expectedMetadata = readBytes(realPathOrFail(metadataArg, 'checked source metadata')).toString('utf8')
    if (expectedMetadata !== metadata) fail('checked source metadata differs')
    console.log(`js render oracle: ${CASES.length} cases exact; hashes=${CASES.map((entry) => `${entry.name}:${entry.sha256}`).join(',')}`)
  } else {
    process.stdout.write(metadata)
  }
}

try { await main() } catch (error) {
  if (process.exitCode !== 2) {
    console.error(`js_render_oracle: ${error.message}`)
    process.exitCode = 1
  }
}
