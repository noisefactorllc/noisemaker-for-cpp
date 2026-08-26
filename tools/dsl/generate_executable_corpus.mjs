#!/usr/bin/env node
import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { authenticateCpuRoot, importCpu, sha256, EXPECTED } from './corpus_authority.mjs'

const ROOT = path.resolve(new URL('.', import.meta.url).pathname, '../..')
const COMPATIBILITY = path.join(ROOT, 'src/effects/generated/backend_compatibility.json')
const PROVENANCE = path.join(ROOT, 'src/effects/generated/effect_catalog.provenance.json')
const TYPED_MANIFEST = path.join(ROOT, 'src/typed_generated/typed_manifest.json')
const BACKEND_SHA256 = '2f5e6b1aeba98abe3c83d71c30e089a10736ddb1b5486396382aa4907f886e49'

function usage(message) {
  if (message) console.error(`generate_executable_corpus: ${message}`)
  console.error('usage: node generate_executable_corpus.mjs --cpu-root ABS --output ABS')
  process.exit(2)
}
const args = process.argv.slice(2)
function arg(name) { const i = args.indexOf(name); return i < 0 ? null : args[i + 1] ?? usage(`${name} requires a value`) }
const cpuRootArg = arg('--cpu-root'); const outputArg = arg('--output')
if (!cpuRootArg || !path.isAbsolute(cpuRootArg)) usage('explicit absolute --cpu-root is required')
if (!outputArg || !path.isAbsolute(outputArg)) usage('absolute --output is required')

function readJson(file, label) {
  const bytes = fs.readFileSync(file)
  let value
  try { value = JSON.parse(bytes) } catch (error) { throw new Error(`${label} is not valid JSON: ${error.message}`) }
  return { bytes, value }
}
function json(value) { return JSON.stringify(value) }
function number(value) { return Number.isInteger(value) ? String(value) : String(value) }
function color(value) {
  const channels = value.length === 4 ? value : [...value, 1]
  return `#${channels.slice(0, 3).map((channel) => Math.max(0, Math.min(255, Math.round(channel * 255))).toString(16).padStart(2, '0')).join('')}${channels.length === 4 && channels[3] !== 1 ? Math.max(0, Math.min(255, Math.round(channels[3] * 255))).toString(16).padStart(2, '0') : ''}`
}
function dslValue(param, value) {
  if (param.type === 'color' && Array.isArray(value)) return color(value)
  if (param.type === 'string') return JSON.stringify(value)
  if (param.type === 'bool' || param.type === 'boolean') return value ? 'true' : 'false'
  if (param.type === 'surface') return value === null || value === 'none' ? 'none' : 'o0'
  if (Array.isArray(value)) return `[${value.map((item) => number(item)).join(', ')}]`
  if (typeof value === 'number') return number(value)
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  return String(value)
}
function defaultArgs(effect) {
  return Object.entries(effect.params ?? {}).map(([name, param]) => `${name}: ${dslValue(param, param.default)}`).join(', ')
}
function sourceFor(effect) {
  const search = effect.kind === 'generator' ? [effect.namespace] : ['synth', effect.namespace].filter((item, index, list) => list.indexOf(item) === index)
  const call = `${effect.func}(${defaultArgs(effect)})`
  const chain = effect.kind === 'generator' ? call : `solid(color: #3a7).${call}`
  return `search ${search.join(', ')}\n${chain}.write(o0)\nrender(o0)\n`
}
function seedFor(id) {
  const value = Number.parseInt(sha256(Buffer.from(id)).slice(0, 8), 16) >>> 0
  return value === 0 ? 1 : value
}
function passRowsByEffect(rows) {
  const result = new Map()
  for (const row of rows) { if (!result.has(row.effect_id)) result.set(row.effect_id, []); result.get(row.effect_id).push(row) }
  return result
}
function firstFailure(effect, rows, source) {
  if (effect.domain !== 'image') return { stage: 'admission', effectId: effect.id, passIndex: 0, programKey: `${effect.id}:${effect.passes[0]?.program ?? ''}`, code: 'unsupported_domain', detail: `domain ${effect.domain} is not an image CPU corpus case` }
  if (!rows || rows.length !== effect.passes.length) {
    const row = rows?.find((entry) => entry.status !== 'compatible' && entry.status !== 'scatter')
    return { stage: 'admission', effectId: effect.id, passIndex: row?.pass_index ?? 0, programKey: row?.program_key ?? `${effect.id}:${effect.passes[row?.pass_index ?? 0]?.program ?? ''}`, code: row?.reasons?.[0]?.code ?? 'missing_pass', detail: row?.reasons?.[0]?.detail ?? 'complete pass set is not present in authenticated C++ admission metadata' }
  }
  const row = rows.find((entry) => !['compatible', 'scatter'].includes(entry.status))
  if (row) return { stage: 'admission', effectId: effect.id, passIndex: row.pass_index, programKey: row.program_key, code: row.status === 'incompatible' ? 'source_incompatible' : 'unsupported_pass', detail: row.reasons?.[0]?.detail ?? row.status }
  return null
}
function planFor(effect, rows, source) {
  const passKeys = rows.map((row) => row.program_key)
  const routes = [...new Set(rows.flatMap((row) => Object.values(row.authority_pass?.outputs ?? {})))]
  const formats = rows.map((row) => ({ passKey: row.program_key, format: 'rgba16f' }))
  const canonical = { effectId: effect.id, passKeys, routes, finalSurface: 'o0', width: 17, height: 11, formats, repeats: rows.map((row) => row.authority_pass?.repeat ?? 1), conditions: rows.map((row) => row.authority_pass?.conditions ?? null) }
  return { cpuPlanSha256: sha256(Buffer.from(json(canonical))), effectIds: [effect.id], passKeys, routes: ['o0'], finalSurface: 'o0', dimensions: { width: 17, height: 11 }, formats }
}
function coverage(effect, rows, kind) {
  const result = []
  if (effect.kind === 'generator') result.push('starter'); else result.push('filter-chain')
  if (rows.length >= 2) result.push('multipass')
  if (effect.externalTexture) result.push('external-texture')
  if (Object.values(effect.textures ?? {}).some((item) => item?.format)) result.push('format')
  for (const param of Object.values(effect.params ?? {})) {
    const type = param.type === 'boolean' ? 'bool' : param.type
    if (['number', 'float', 'int'].includes(type)) result.push('polymorphic-number')
    if (type === 'bool') result.push('polymorphic-bool')
    if (['enum', 'member', 'palette'].includes(type) || param.choices) result.push('polymorphic-enum')
    if (type.startsWith('vec')) result.push('polymorphic-vector')
    if (type === 'color') result.push('polymorphic-color')
    if (type === 'string') result.push('polymorphic-string')
    if (type === 'surface') result.push('polymorphic-surface')
  }
  if (kind === 'excluded' && effect.id === 'filter/text') result.push('source-incompatible')
  if (rows.some((row) => row.status === 'scatter')) result.push('scatter')
  return [...new Set(result)].sort()
}

async function main() {
  authenticateCpuRoot(cpuRootArg)
  const { snapshot, catalog, api } = await importCpu(cpuRootArg)
  const compatibility = readJson(COMPATIBILITY, 'backend compatibility')
  const provenance = readJson(PROVENANCE, 'effect catalog provenance')
  const typed = readJson(TYPED_MANIFEST, 'typed manifest')
  if (sha256(compatibility.bytes) !== BACKEND_SHA256) throw new Error('backend compatibility sha256 mismatch')
  const typedManifestSha256 = sha256(typed.bytes)
  if (!typed.value || typed.value.schema !== 1 || !Array.isArray(typed.value.programs) || typed.value.programs.length === 0 || !typed.value.typed_slice_sha256 || typed.value.programs.some((row) => row.output_sha256 !== typed.value.typed_slice_sha256)) throw new Error('typed manifest is not an authenticated emitter manifest')
  const rowsByEffect = passRowsByEffect(compatibility.value.reference_passes)
  const records = []
  for (const effect of [...snapshot.effectRecords].sort((a, b) => a.id.localeCompare(b.id))) {
    const rows = rowsByEffect.get(effect.id) ?? []
    const source = sourceFor(effect)
    const sourceSha256 = sha256(Buffer.from(source))
    const options = { width: 17, height: 11, time: 0.25, frame: 0, seed: seedFor(`${effect.id}#default`), oneShot: 'ready', renderScale: 1 }
    const provenanceRecord = { cpuBehavioralLock: EXPECTED.behavioralLockSha256, sourceLockSha256: EXPECTED.sourceLockSha256, upstreamSourceDigest: EXPECTED.upstreamSourceDigest, upstreamRevision: EXPECTED.upstreamRevision, upstreamTree: 'a7a997dfdc807697adba008729dcdfdfcfbaf53c', compatibilitySha256: BACKEND_SHA256, typedManifestSha256, catalogPayloadSha256: provenance.value.generated_payload_sha256 }
    const admissionFailure = firstFailure(effect, rows, source)
    let failure = admissionFailure
    if (!failure && effect.domain === 'image') {
      try { api.compileDsl(source, catalog.createDefaultRegistry(), { sourceName: `${effect.id}#default` }) }
      catch (error) { failure = { stage: 'preflight', effectId: effect.id, passIndex: 0, programKey: rows[0]?.program_key ?? '', code: 'registry_preflight', detail: error.message } }
    }
    const kind = failure ? 'excluded' : 'admitted'
    const record = { schema: 'noisemaker-cpp.dsl-executable-corpus.v1', recordKind: kind, id: `${effect.id}#default`, effectId: effect.id, variant: 'default', sourceName: `${effect.id.replaceAll('/', '__')}__default.dsl`, source, sourceSha256, width: options.width, height: options.height, options, search: effect.kind === 'generator' ? [effect.namespace] : ['synth', effect.namespace].filter((item, index, list) => list.indexOf(item) === index), parameters: Object.fromEntries(Object.entries(effect.params ?? {}).map(([name, param]) => [name, param.default])), coverage: coverage(effect, rows, kind), provenance: provenanceRecord }
    if (failure) { record.firstFailure = failure; record.allReasons = [{ code: failure.code, detail: failure.detail }, ...(rows.flatMap((row) => row.reasons ?? []).map((reason) => ({ code: reason.code, detail: reason.detail })))]; record.allReasons = [...new Map(record.allReasons.map((item) => [`${item.code}:${item.detail}`, item])).values()] }
    else record.plan = planFor(effect, rows, source)
    records.push(record)
  }
  const buckets = {}
  for (const bucket of ['starter', 'filter-chain', 'multipass', 'conditions', 'numeric-repeat', 'string-repeat', 'custom-viewport', 'format', 'secondary-surface', 'external-texture', 'linear-filter', 'polymorphic-number', 'polymorphic-bool', 'polymorphic-enum', 'polymorphic-vector', 'polymorphic-color', 'polymorphic-string', 'polymorphic-surface', 'scatter', 'source-incompatible']) {
    const count = records.filter((record) => record.recordKind === 'admitted' && record.coverage.includes(bucket)).length
    buckets[bucket] = count ? { available: true, count } : { available: false, count: 0, reason: 'no admitted definition in authenticated current intersection' }
  }
  const counts = { admitted: records.filter((record) => record.recordKind === 'admitted').length, excluded: records.filter((record) => record.recordKind === 'excluded').length, variants: records.length, coverage: Object.fromEntries(Object.entries(buckets).map(([key, value]) => [key, value.count])) }
  const manifest = { schema: 'noisemaker-cpp.dsl-executable-corpus.v1', generator: 'generate_executable_corpus.mjs', provenance: { compatibilitySha256: BACKEND_SHA256, typedManifestSha256, catalogPayloadSha256: provenance.value.generated_payload_sha256, cpuBehavioralLock: EXPECTED.behavioralLockSha256, sourceLockSha256: EXPECTED.sourceLockSha256, upstreamSourceDigest: EXPECTED.upstreamSourceDigest, upstreamRevision: EXPECTED.upstreamRevision, upstreamTree: 'a7a997dfdc807697adba008729dcdfdfcfbaf53c', }, counts, coverage: buckets, records }
  const canonical = Buffer.from(json(manifest))
  manifest.manifestSha256 = sha256(canonical)
  const output = path.resolve(outputArg)
  if (fs.existsSync(output) && fs.lstatSync(output).isSymbolicLink()) throw new Error('output must not be a symlink')
  fs.mkdirSync(path.dirname(output), { recursive: true })
  fs.writeFileSync(output, `${JSON.stringify(manifest, null, 2)}\n`, { flag: 'w' })
  console.log(JSON.stringify({ output, manifestSha256: manifest.manifestSha256, counts }, null, 2))
}
main().catch((error) => { console.error(`generate_executable_corpus: ${error.message}`); process.exitCode = 1 })
