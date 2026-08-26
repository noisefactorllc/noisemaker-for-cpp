#!/usr/bin/env node
/* Authenticated JS CPU runner. Raw output is top-down RGBA8 and never PNG. */
import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { importCpu, sha256, EXPECTED, AUTHORITY_LEDGER_ENV } from '../dsl/corpus_authority.mjs'

function usage(message) { if (message) console.error(`run_cpu_case: ${message}`); console.error(`usage: node run_cpu_case.mjs --cpu-root ABS --case FILE --rgba8-output ABS --metadata-output ABS [--expectation-output ABS] [--plan-relation-output ABS] [--authority-ledger ABS]\n  the CPU authority ledger comes from --authority-ledger, ${AUTHORITY_LEDGER_ENV}, or the ledger packaged with --cpu-root`); process.exit(2) }
const args = process.argv.slice(2)
function arg(name) { const index = args.indexOf(name); return index < 0 ? null : args[index + 1] ?? usage(`${name} requires a value`) }
const cpuRoot = arg('--cpu-root'); const caseArg = arg('--case'); const rawArg = arg('--rgba8-output'); const metadataArg = arg('--metadata-output')
const expectationArg = arg('--expectation-output'); const ledgerArg = arg('--authority-ledger')
// Additive and opt-in: absent, every byte this runner writes and prints is
// exactly what the frozen parity lane already validates.
const relationArg = arg('--plan-relation-output')
if (!cpuRoot || !path.isAbsolute(cpuRoot) || !caseArg || !rawArg || !metadataArg || ![rawArg, metadataArg].every((value) => path.isAbsolute(value))) usage('absolute CPU root, case, raw output, and metadata output are required')
if (expectationArg && !path.isAbsolute(expectationArg)) usage('--expectation-output must be absolute')
if (ledgerArg && !path.isAbsolute(ledgerArg)) usage('--authority-ledger must be absolute')
if (relationArg && !path.isAbsolute(relationArg)) usage('--plan-relation-output must be absolute')
const record = JSON.parse(fs.readFileSync(caseArg, 'utf8'))
if (record.recordKind !== 'admitted') throw new Error('CPU runner refuses excluded corpus records')
if (sha256(Buffer.from(record.source)) !== record.sourceSha256) throw new Error('case source sha256 mismatch')
const { catalog, api } = await importCpu(cpuRoot, ledgerArg)
const registry = catalog.createDefaultRegistry()
const renderer = new api.CpuRenderer({ registry, kernels: catalog.kernels, kernelFactories: catalog.kernelFactories })
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
if (relationArg) outputs.push(path.resolve(relationArg))
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

if (relationArg) {
  // The cross-lane normalized plan relation. It is projected from the JS CPU
  // authority's own compiled plan, never from the corpus record's static
  // `plan` projection -- that projection omits the starter effect on 138 of
  // 166 records and hardcodes one format spelling, so it is a containment
  // oracle only.
  //
  // `passKey` keys on `pass.program`, NEVER on `pass.name`. The two differ:
  // `classicNoisedeck/bitEffects` carries `{name:"render", program:"bitEffects"}`
  // and `synth/solid` carries `{name:"main", program:"solid"}`, so keying on
  // the name diverges from the C++ `program_key` on every single record.
  const plan = api.compileDsl(record.source, registry, options)
  const stepKinds = []; const effectIds = []; const passKeys = []; const passFormats = []; const reads = []; const routes = []
  for (const chain of plan.chains) {
    for (const step of chain.steps) {
      stepKinds.push(step.kind)
      if (step.kind === 'read') { reads.push(step.surface); continue }
      if (step.kind === 'write') { routes.push(step.surface); continue }
      const definition = step.definition
      effectIds.push(definition.id)
      for (const pass of definition.passes) {
        if (typeof pass.program !== 'string' || pass.program.length === 0) throw new Error(`pass ${definition.id}:${pass.name} has no program name`)
        passKeys.push(`${definition.id}:${pass.program}`)
        // The declared output-texture format, with an explicit rgba16f
        // default. Spellings are emitted verbatim -- rgba16float is NOT
        // aliased to rgba16f, because both lanes already agree on the raw
        // spelling and an alias table would hide a real divergence.
        const route = Object.values(pass.outputs ?? {})[0]
        passFormats.push(definition.textures?.[route]?.format ?? 'rgba16f')
      }
    }
  }
  const relation = {
    schema: 'noisemaker-cpp.plan-relation.v1',
    recordId: record.id,
    sourceSha256: record.sourceSha256,
    stepKinds, effectIds, passKeys, passFormats, reads, routes,
    finalSurface: plan.renderSurface,
    dimensions: { width: record.options.width, height: record.options.height },
    passCount: result.stats.passes,
  }
  const field = (name, values) => `${name}\u001f${values.length}${values.map((value) => `\u001f${value}`).join('')}\u001e`
  const canonical = [
    field('schema', [relation.schema]),
    field('recordId', [relation.recordId]),
    field('sourceSha256', [relation.sourceSha256]),
    field('stepKinds', relation.stepKinds),
    field('effectIds', relation.effectIds),
    field('passKeys', relation.passKeys),
    field('passFormats', relation.passFormats),
    field('reads', relation.reads),
    field('routes', relation.routes),
    field('finalSurface', [relation.finalSurface]),
    field('dimensions', [String(relation.dimensions.width), String(relation.dimensions.height)]),
    field('passCount', [String(relation.passCount)]),
  ].join('')
  relation.relationSha256 = sha256(Buffer.from(canonical, 'utf8'))
  fs.writeFileSync(path.resolve(relationArg), `${JSON.stringify(relation, null, 2)}\n`)
}
console.log(JSON.stringify(metadata))
