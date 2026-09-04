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
  ledgerEntries: 714,
  packageSha256: 'c7d8aec82725078b4d31d379323901e83bdfba0a0289ff8428beecdac2c9d78a',
  packageLockSha256: '724bfaf208346605cae0ce9a74d0e84c76dd3aeb8fedb44fb894ad03c4dad03d',
  sourceLockSha256: 'fd90ff2fb463245f86c61fe21b773982cd6d1709111c2582d0a57b3dec9ecc73',
  behavioralLockSha256: '1e4a1148d9fdf0ef3c58e2170b552af8dfebec5435b263da71a2527ca866d792',
  behavioralFileCount: 90,
  upstreamRevision: 'ee523ab910cacf4b6a52c0886fe019bfe89e2933',
  upstreamSourceDigest: '7ba23000f4cf9bb0a532639b7c26b8fb8cc1a58d5ae5d9e95ebf9b25f9e0fbad',
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

function verifyLedger(root, ledgerArg) {
  const ledger = realFile(resolveAuthorityLedger(root, ledgerArg).path, 'oracle ledger')
  const lines = fs.readFileSync(ledger, 'utf8').split(/\r?\n/).filter(Boolean)
  if (lines.length !== EXPECTED.ledgerEntries) throw new Error(`oracle ledger entry count mismatch: expected ${EXPECTED.ledgerEntries}, received ${lines.length}`)
  for (const line of lines) {
    const match = line.match(/^([0-9a-f]{64})  (.+)$/)
    if (!match) throw new Error('oracle ledger has a malformed entry')
    const file = realFile(match[2], 'oracle ledger file')
    if (!file.startsWith(`${root}${path.sep}`) && file !== root) throw new Error(`oracle ledger escapes CPU authority: ${file}`)
    if (sha256(fs.readFileSync(file)) !== match[1]) throw new Error(`oracle ledger sha256 mismatch: ${file}`)
  }
}

export function authenticateCpuRoot(rootArg, ledgerArg = null) {
  if (!rootArg || !path.isAbsolute(path.resolve(rootArg))) throw new Error('CPU authority root must be given explicitly')
  const root = realRoot(rootArg)
  const packagePath = realFile(path.join(root, 'package.json'), 'CPU package.json')
  const lockPath = realFile(path.join(root, 'package-lock.json'), 'CPU package-lock.json')
  const sourceLockPath = realFile(path.join(root, 'scripts/upstream/source-lock.js'), 'CPU source-lock.js')
  if (sha256(fs.readFileSync(packagePath)) !== EXPECTED.packageSha256) throw new Error('CPU package.json sha256 mismatch')
  if (sha256(fs.readFileSync(lockPath)) !== EXPECTED.packageLockSha256) throw new Error('CPU package-lock.json sha256 mismatch')
  if (sha256(fs.readFileSync(sourceLockPath)) !== EXPECTED.sourceLockSha256) throw new Error('CPU source-lock.js sha256 mismatch')
  const behavioral = behavioralDigest(root)
  if (behavioral.files.length !== EXPECTED.behavioralFileCount || behavioral.digest !== EXPECTED.behavioralLockSha256) throw new Error('CPU behavioral lock mismatch')
  verifyLedger(root, ledgerArg)
  return root
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
