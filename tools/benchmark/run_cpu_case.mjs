#!/usr/bin/env node
/* Authenticated JS CPU runner. Raw output is top-down RGBA8 and never PNG. */
import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { importCpu, sha256, EXPECTED, AUTHORITY_LEDGER_ENV } from '../dsl/corpus_authority.mjs'

function usage(message) { if (message) console.error(`run_cpu_case: ${message}`); console.error(`usage: node run_cpu_case.mjs --cpu-root ABS --case FILE --rgba8-output ABS --metadata-output ABS [--expectation-output ABS] [--authority-ledger ABS]\n  the CPU authority ledger comes from --authority-ledger, ${AUTHORITY_LEDGER_ENV}, or the ledger packaged with --cpu-root`); process.exit(2) }
const args = process.argv.slice(2)
function arg(name) { const index = args.indexOf(name); return index < 0 ? null : args[index + 1] ?? usage(`${name} requires a value`) }
const cpuRoot = arg('--cpu-root'); const caseArg = arg('--case'); const rawArg = arg('--rgba8-output'); const metadataArg = arg('--metadata-output')
const expectationArg = arg('--expectation-output'); const ledgerArg = arg('--authority-ledger')
if (!cpuRoot || !path.isAbsolute(cpuRoot) || !caseArg || !rawArg || !metadataArg || ![rawArg, metadataArg].every((value) => path.isAbsolute(value))) usage('absolute CPU root, case, raw output, and metadata output are required')
if (expectationArg && !path.isAbsolute(expectationArg)) usage('--expectation-output must be absolute')
if (ledgerArg && !path.isAbsolute(ledgerArg)) usage('--authority-ledger must be absolute')
const record = JSON.parse(fs.readFileSync(caseArg, 'utf8'))
if (record.recordKind !== 'admitted') throw new Error('CPU runner refuses excluded corpus records')
if (sha256(Buffer.from(record.source)) !== record.sourceSha256) throw new Error('case source sha256 mismatch')
const { catalog, api } = await importCpu(cpuRoot, ledgerArg)
const renderer = new api.CpuRenderer({ registry: catalog.createDefaultRegistry(), kernels: catalog.kernels, kernelFactories: catalog.kernelFactories })
const seedSurfaces = {}
for (const seed of record.seedSurfaces ?? []) {
  if (!seed.rgba8) throw new Error(`seed surface ${seed.name} is missing raw RGBA8 bytes`)
  const bytes = Uint8Array.from(Buffer.from(seed.rgba8, 'hex'))
  seedSurfaces[seed.name] = api.Surface.fromRgba8(seed.width, seed.height, bytes)
}
const options = { ...record.options, seedSurfaces: Object.keys(seedSurfaces).length ? seedSurfaces : undefined }
const result = renderer.render(record.source, options)
const bytes = Buffer.from(result.toRgba8())
const rawOutput = path.resolve(rawArg); const metadataOutput = path.resolve(metadataArg)
const outputs = [rawOutput, metadataOutput]
if (expectationArg) outputs.push(path.resolve(expectationArg))
for (const output of outputs) { if (fs.existsSync(output) && fs.lstatSync(output).isSymbolicLink()) throw new Error(`output must not be a symlink: ${output}`); fs.mkdirSync(path.dirname(output), { recursive: true }) }
fs.writeFileSync(rawOutput, bytes)
const metadata = { schema: 'noisemaker-cpp.dsl-cpu-run.v1', id: record.id, sourceSha256: record.sourceSha256, width: result.width, height: result.height, format: 'rgba8', orientation: 'top-down', rgba8Sha256: sha256(bytes), byteLength: bytes.length, planSha256: record.plan?.cpuPlanSha256 ?? null }
fs.writeFileSync(metadataOutput, `${JSON.stringify(metadata, null, 2)}\n`)
if (expectationArg) {
  // The expectation document binds these bytes to the runner that produced
  // them and to the authenticated CPU authority they were produced from, so a
  // consumer can never treat a hand-written image as CPU-authored truth.
  const runnerFile = fs.realpathSync(new URL(import.meta.url).pathname)
  const expectation = {
    schema: 'noisemaker-cpp.dsl-cpu-expectation.v1',
    id: record.id,
    sourceSha256: record.sourceSha256,
    planSha256: record.plan?.cpuPlanSha256 ?? null,
    width: result.width,
    height: result.height,
    format: 'rgba8',
    orientation: 'top-down',
    rgba8Sha256: sha256(bytes),
    byteLength: bytes.length,
    rgba8Base64: bytes.toString('base64'),
    options: { ...record.options },
    seedSurfaceNames: Object.keys(seedSurfaces).sort(),
    runner: { name: 'tools/benchmark/run_cpu_case.mjs', sha256: sha256(fs.readFileSync(runnerFile)) },
    authority: {
      behavioralLockSha256: EXPECTED.behavioralLockSha256,
      packageSha256: EXPECTED.packageSha256,
      packageLockSha256: EXPECTED.packageLockSha256,
      sourceLockSha256: EXPECTED.sourceLockSha256,
      upstreamRevision: EXPECTED.upstreamRevision,
      upstreamSourceDigest: EXPECTED.upstreamSourceDigest,
      ledgerEntries: EXPECTED.ledgerEntries,
      behavioralFileCount: EXPECTED.behavioralFileCount,
    },
    caseProvenance: record.provenance ?? null,
  }
  fs.writeFileSync(path.resolve(expectationArg), `${JSON.stringify(expectation, null, 2)}\n`)
}
console.log(JSON.stringify(metadata))
