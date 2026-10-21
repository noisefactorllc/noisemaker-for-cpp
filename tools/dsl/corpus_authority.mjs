import fs from 'node:fs'
import crypto from 'node:crypto'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

// No authority path is baked into this file. The CPU authority root always
// arrives from an explicit argument, and its ledger from an explicit argument,
// the NOISEMAKER_CPU_AUTHORITY_LEDGER environment variable, or the ledger that
// the caller-supplied root is itself packaged with. A session-absolute or
// home-absolute constant here would make the checked-in tree unusable off this
// machine, so there is none.
export const AUTHORITY_LEDGER_ENV = 'NOISEMAKER_CPU_AUTHORITY_LEDGER'

export const EXPECTED = Object.freeze({
  ledgerEntries: 895,
  packageSha256: 'cb5c3d4f898b2eec37a84e60adc1405baa14712715f95262cc5778b472fcba21',
  packageLockSha256: '724bfaf208346605cae0ce9a74d0e84c76dd3aeb8fedb44fb894ad03c4dad03d',
  sourceLockSha256: '3c69af0332f8298e601164ced21504a9b9cf0e0ea50d9779751cdf23e7b03efe',
  behavioralLockSha256: 'df6e11a1671a8e141926d6d0a8a7f79b1394d801d47ea39a157190173d8878ed',
  behavioralFileCount: 98,
  upstreamRevision: 'b71a896a4dbdbc01e682b277f6d9a41fe786485e',
  upstreamSourceDigest: '6f620dfc3ed249938df917beba75b4e80612e053226813e1004587c8c2483699',
})

const FROZEN_KERNEL_EXPECTED = Object.freeze({
  ledgerEntries: 893,
  packageSha256: 'cb5c3d4f898b2eec37a84e60adc1405baa14712715f95262cc5778b472fcba21',
  packageLockSha256: '724bfaf208346605cae0ce9a74d0e84c76dd3aeb8fedb44fb894ad03c4dad03d',
  sourceLockSha256: '594eac7141434eb19d97fbff77cc414e1556380fc5be3db8360e2fc7bd96c20c',
  behavioralLockSha256: '30424f99ee8a25535a921ed9d9c364c881b858cb4491a9130f5c4bf4bc499d4b',
  behavioralFileCount: 98,
})

export function sha256(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex') }

function realFile(file, label) {
  const candidate = path.resolve(file)
  const stat = fs.lstatSync(candidate)
  if (stat.isSymbolicLink() || !stat.isFile() || fs.realpathSync(candidate) !== candidate) {
    throw new Error(`${label} must be a non-symlink regular file: ${candidate}`)
  }
  return candidate
}

function realRoot(root) {
  const candidate = path.resolve(root)
  const stat = fs.lstatSync(candidate)
  if (stat.isSymbolicLink() || !stat.isDirectory() || fs.realpathSync(candidate) !== candidate) {
    throw new Error(`CPU authority must be a non-symlink directory: ${candidate}`)
  }
  return candidate
}

function sourceFiles(directory, result = []) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const file = path.join(directory, entry.name)
    if (entry.isSymbolicLink()) throw new Error(`CPU behavioral source must not contain a symlink: ${file}`)
    if (entry.isDirectory()) sourceFiles(file, result)
    else if (entry.isFile()) result.push(file)
    else throw new Error(`CPU behavioral source contains a non-file: ${file}`)
  }
  return result
}

function behavioralDigest(root) {
  const files = sourceFiles(path.join(root, 'src'))
  files.push(path.join(root, 'scripts/upstream/source-lock.js'), path.join(root, 'package.json'), path.join(root, 'package-lock.json'))
  files.sort((left, right) => path.relative(root, left).localeCompare(path.relative(root, right)))
  const hash = crypto.createHash('sha256')
  for (const file of files) {
    const relative = path.relative(root, file).split(path.sep).join('/')
    const bytes = fs.readFileSync(realFile(file, 'CPU behavioral source'))
    hash.update(relative); hash.update('\0'); hash.update(String(bytes.length)); hash.update('\0'); hash.update(bytes)
  }
  return { files, digest: hash.digest('hex') }
}

export function resolveAuthorityLedger(root, explicit = null) {
  const candidates = [
    explicit ? { source: 'argument', value: explicit } : null,
    process.env[AUTHORITY_LEDGER_ENV] ? { source: AUTHORITY_LEDGER_ENV, value: process.env[AUTHORITY_LEDGER_ENV] } : null,
    { source: 'packaged-with-root', value: `${path.dirname(path.resolve(root))}.sha256` },
  ].filter(Boolean)
  for (const candidate of candidates) {
    if (!path.isAbsolute(candidate.value)) throw new Error(`oracle ledger from ${candidate.source} must be an absolute path`)
    if (fs.existsSync(candidate.value)) return { source: candidate.source, path: candidate.value }
    if (candidate.source !== 'packaged-with-root') throw new Error(`oracle ledger from ${candidate.source} does not exist: ${candidate.value}`)
  }
  throw new Error(`no oracle ledger for CPU authority ${root}: pass one explicitly or set ${AUTHORITY_LEDGER_ENV}`)
}

function verifyLedger(root, ledgerArg, expected) {
  const ledger = realFile(resolveAuthorityLedger(root, ledgerArg).path, 'oracle ledger')
  const lines = fs.readFileSync(ledger, 'utf8').split(/\r?\n/).filter(Boolean)
  if (lines.length !== expected.ledgerEntries) throw new Error(`oracle ledger entry count mismatch: expected ${expected.ledgerEntries}, received ${lines.length}`)
  for (const line of lines) {
    const match = line.match(/^([0-9a-f]{64})  (.+)$/)
    if (!match) throw new Error('oracle ledger has a malformed entry')
    const file = realFile(match[2], 'oracle ledger file')
    if (!file.startsWith(`${root}${path.sep}`) && file !== root) throw new Error(`oracle ledger escapes CPU authority: ${file}`)
    if (sha256(fs.readFileSync(file)) !== match[1]) throw new Error(`oracle ledger sha256 mismatch: ${file}`)
  }
}

function authenticateRoot(rootArg, ledgerArg, expected) {
  if (!rootArg || !path.isAbsolute(path.resolve(rootArg))) throw new Error('CPU authority root must be given explicitly')
  const root = realRoot(rootArg)
  const packagePath = realFile(path.join(root, 'package.json'), 'CPU package.json')
  const lockPath = realFile(path.join(root, 'package-lock.json'), 'CPU package-lock.json')
  const sourceLockPath = realFile(path.join(root, 'scripts/upstream/source-lock.js'), 'CPU source-lock.js')
  if (sha256(fs.readFileSync(packagePath)) !== expected.packageSha256) throw new Error('CPU package.json sha256 mismatch')
  if (sha256(fs.readFileSync(lockPath)) !== expected.packageLockSha256) throw new Error('CPU package-lock.json sha256 mismatch')
  if (sha256(fs.readFileSync(sourceLockPath)) !== expected.sourceLockSha256) throw new Error('CPU source-lock.js sha256 mismatch')
  const behavioral = behavioralDigest(root)
  if (behavioral.files.length !== expected.behavioralFileCount || behavioral.digest !== expected.behavioralLockSha256) throw new Error('CPU behavioral lock mismatch')
  verifyLedger(root, ledgerArg, expected)
  return root
}

export function authenticateCpuRoot(rootArg, ledgerArg = null) {
  return authenticateRoot(rootArg, ledgerArg, EXPECTED)
}

export function authenticate3ccCpuRoot(rootArg, ledgerArg = null) {
  return authenticateRoot(rootArg, ledgerArg, FROZEN_KERNEL_EXPECTED)
}

export async function importCpu(rootArg, ledgerArg = null) {
  const root = authenticateCpuRoot(rootArg, ledgerArg)
  const sourceLock = await import(pathToFileURL(path.join(root, 'scripts/upstream/source-lock.js')).href)
  if (sourceLock.PINNED_UPSTREAM_REVISION !== EXPECTED.upstreamRevision || sourceLock.PINNED_SOURCE_DIGEST !== EXPECTED.upstreamSourceDigest) throw new Error('CPU upstream revision/source lock mismatch')
  const snapshot = await import(pathToFileURL(path.join(root, 'src/effects/generated/upstream-snapshot.js')).href)
  const catalog = await import(pathToFileURL(path.join(root, 'src/effects/catalog.js')).href)
  const api = await import(pathToFileURL(path.join(root, 'src/index.js')).href)
  return { root, sourceLock, snapshot, catalog, api }
}
