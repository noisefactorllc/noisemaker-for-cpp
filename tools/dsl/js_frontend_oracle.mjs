#!/usr/bin/env node
import fs from 'node:fs'
import crypto from 'node:crypto'
import path from 'node:path'
import process from 'node:process'
import { pathToFileURL } from 'node:url'

function usage(message) {
  if (message) console.error(`js_frontend_oracle: ${message}`)
  console.error('usage: node js_frontend_oracle.mjs --cpu-root ABS --fixtures FILE [--output FILE] [--check FILE]')
  process.exit(2)
}

const args = process.argv.slice(2)
function argument(name) {
  const index = args.indexOf(name)
  return index < 0 ? null : args[index + 1]
}
const cpuRoot = argument('--cpu-root')
const fixturesPath = argument('--fixtures')
const outputPath = argument('--output')
const checkPath = argument('--check')
const compilerMode = args.includes('--compiler')

if (compilerMode) {
  await runCompilerOracle({ cpuRoot, fixturesPath, outputPath, checkPath })
  process.exit(0)
}
const EXPECTED_MODULE_SHA256 = new Map([
  ['src/dsl/parser.js', '260798bbcb5ae4e1409a726f6f0225b262cd5c586703b810d39892195e505518'],
  ['src/dsl/tokenize.js', '83249cc23e612f6b2655ec2a1cdfcbdf1bbe83179793531b45c63fc8738f3cc2'],
  ['src/dsl/error.js', 'fdc8a674431666d48a8094e3c7021120df3767226c870e7bb9eb88aa25abde93']
])
if (!cpuRoot || !fixturesPath || !path.isAbsolute(cpuRoot)) usage('explicit absolute --cpu-root is required')
const requestedRoot = path.resolve(cpuRoot)
if (!fs.existsSync(requestedRoot)) usage('CPU root is not a directory')
const rootStat = fs.lstatSync(requestedRoot)
if (rootStat.isSymbolicLink()) usage('CPU root must be a real path, not a symlink')
if (!rootStat.isDirectory()) usage('CPU root is not a directory')
const realRoot = fs.realpathSync(requestedRoot)
if (realRoot !== requestedRoot) usage('CPU root must be a real path, not a symlink')
const tokenizePath = path.join(realRoot, 'src', 'dsl', 'tokenize.js')
if (!fs.existsSync(tokenizePath)) usage(`validated CPU root lacks ${path.relative(realRoot, tokenizePath)}`)
function moduleKey(modulePath) {
  const relative = path.relative(realRoot, modulePath)
  if (relative.startsWith('..' + path.sep) || path.isAbsolute(relative)) usage('CPU import closure escapes the CPU root')
  return relative.split(path.sep).join('/')
}
function authenticateModule(modulePath, expectedKey) {
  if (!fs.existsSync(modulePath)) usage(`validated CPU root lacks ${expectedKey}`)
  const stat = fs.lstatSync(modulePath)
  if (stat.isSymbolicLink()) usage(`CPU import must not be a symlink: ${expectedKey}`)
  if (!stat.isFile()) usage(`CPU import must be a regular file: ${expectedKey}`)
  const realPath = fs.realpathSync(modulePath)
  if (realPath !== modulePath) usage(`CPU import must not escape real root: ${expectedKey}`)
  const actualKey = moduleKey(realPath)
  if (actualKey !== expectedKey) usage(`CPU import path mismatch: ${actualKey}`)
  const source = fs.readFileSync(realPath)
  const actualHash = crypto.createHash('sha256').update(source).digest('hex')
  if (actualHash !== EXPECTED_MODULE_SHA256.get(expectedKey)) usage(`CPU import authority sha256 mismatch: ${expectedKey}`)
  const imports = [...source.toString('utf8').matchAll(/\bimport\s+(?:[^'"\n]+\s+from\s+)?['"]([^'"]+)['"]/g)].map((match) => match[1])
  for (const specifier of imports) {
    if (!specifier.startsWith('./')) usage(`unexpected CPU import in ${expectedKey}: ${specifier}`)
    const importedPath = path.resolve(path.dirname(realPath), specifier)
    const importedKey = moduleKey(importedPath)
    if (!EXPECTED_MODULE_SHA256.has(importedKey)) usage(`unexpected CPU import closure module: ${importedKey}`)
    authenticateModule(importedPath, importedKey)
  }
}
// Authenticate the lexer first to retain the established forged-module/symlink diagnostics;
// then authenticate the parser and its complete recursive closure before importing either.
authenticateModule(tokenizePath, 'src/dsl/tokenize.js')
const parserPath = path.join(realRoot, 'src', 'dsl', 'parser.js')
if (!fs.existsSync(parserPath)) usage(`validated CPU root lacks ${path.relative(realRoot, parserPath)} (sha256-authenticated closure required)`)
authenticateModule(parserPath, 'src/dsl/parser.js')
const fixtures = JSON.parse(fs.readFileSync(fixturesPath, 'utf8'))
if (!Array.isArray(fixtures)) usage('fixtures must be an array')
const { parseDsl } = await import(pathToFileURL(parserPath).href)

function taggedNumber(value) {
  if (Number.isNaN(value)) return 'number:NaN'
  if (value === Infinity) return 'number:+Infinity'
  if (value === -Infinity) return 'number:-Infinity'
  if (Object.is(value, -0)) return 'number:-0'
  return `number:${String(value)}`
}
function indexFor(source, line, column) {
  let currentLine = 1
  let currentColumn = 1
  let index = 0
  for (let offset = 0; offset < source.length; ) {
    if (currentLine === line && currentColumn === column) return index
    const code = source.codePointAt(offset)
    const units = code > 0xffff ? 2 : 1
    const char = source.slice(offset, offset + units)
    offset += units
    index += units
    if (char === '\n') { currentLine += 1; currentColumn = 1 }
    else currentColumn += units
  }
  return index
}
function canonicalToken(token) {
  const result = { type: token.type, lexeme: token.lexeme }
  if (token.value !== undefined) result.value = typeof token.value === 'number' ? taggedNumber(token.value) : token.value
  result.sourceName = token.sourceName
  result.line = token.line
  result.column = token.column
  result.index = token.index
  return result
}
function canonicalLocation(value) {
  return { sourceName: value.sourceName, line: value.line, column: value.column, index: value.index }
}
function canonicalValue(value) {
  if (typeof value === 'number') return { kind: 'number', value: taggedNumber(value) }
  if (typeof value === 'string') return { kind: 'string', value }
  if (typeof value === 'boolean') return { kind: 'boolean', value }
  if (Array.isArray(value)) return value.map(canonicalValue)
  if (value && typeof value === 'object') {
    if (value.kind === 'DslProgram') return canonicalProgram(value)
    if (value.kind === 'Binding') return { kind: 'Binding', name: value.name, value: canonicalValue(value.value), loc: canonicalLocation(value.loc) }
    if (value.kind === 'Chain') return { kind: 'Chain', calls: value.calls.map(canonicalValue), loc: canonicalLocation(value.loc) }
    if (value.kind === 'Call') return {
      kind: 'Call', name: value.name,
      args: value.args.map((arg) => ({ name: arg.name, value: canonicalValue(arg.value), loc: canonicalLocation(arg.loc) })),
      argMode: value.argMode, loc: canonicalLocation(value.loc)
    }
    if (value.kind === 'surface') return { kind: 'surface', name: value.name, loc: canonicalLocation(value.loc) }
    if (value.kind === 'vector') return { kind: 'vector', width: value.width, values: value.values.map(canonicalValue), loc: canonicalLocation(value.loc) }
    if (value.kind === 'identifier') return { kind: 'identifier', name: value.name, loc: canonicalLocation(value.loc) }
    if (value.kind === 'unary') return { kind: 'unary', operator: value.operator, argument: canonicalValue(value.argument), loc: canonicalLocation(value.loc) }
    if (value.kind === 'binary') return { kind: 'binary', operator: value.operator, left: canonicalValue(value.left), right: canonicalValue(value.right), loc: canonicalLocation(value.loc) }
  }
  return value
}
function canonicalProgram(program) {
  return {
    kind: 'DslProgram', search: program.search,
    bindings: program.bindings.map(canonicalValue),
    chains: program.chains.map(canonicalValue),
    render: program.render ? { kind: 'surface', name: program.render.name, loc: canonicalLocation(program.render.loc) } : null,
    loc: canonicalLocation(program.loc)
  }
}
function canonicalCase(entry) {
  try {
    if (entry.parse) {
      return { name: entry.name, ast: canonicalProgram(parseDsl(entry.source, { sourceName: entry.sourceName ?? entry.name })) }
    }
    // Keep the lexer corpus stable while allowing parser cases in the same file.
    const { tokenizeDsl } = awaitTokenize()
    return { name: entry.name, tokens: tokenizeDsl(entry.source, { sourceName: entry.sourceName ?? entry.name }).map(canonicalToken) }
  } catch (error) {
    const sourceName = error.sourceName ?? entry.sourceName ?? entry.name
    const line = error.line ?? 1
    const column = error.column ?? 1
    return {
      name: entry.name,
      error: {
        name: error.name,
        message: error.message,
        sourceName,
        line,
        column,
        index: indexFor(entry.source, line, column)
      }
    }
  }
}
function awaitTokenize() {
  return tokenizeModule
}
const tokenizeModule = await import(pathToFileURL(path.join(realRoot, 'src', 'dsl', 'tokenize.js')).href)
const text = fixtures.map(canonicalCase).map((entry) => JSON.stringify(entry)).join('\n') + '\n'
if (checkPath) {
  const expected = fs.readFileSync(checkPath, 'utf8')
  if (expected !== text) {
    console.error('js_frontend_oracle: checked expected stream differs')
    process.exit(1)
  }
}
if (outputPath) fs.writeFileSync(outputPath, text)
else process.stdout.write(text)

async function runCompilerOracle({ cpuRoot, fixturesPath, outputPath, checkPath }) {
  function fail(message) { console.error(`js_frontend_oracle: ${message}`); process.exit(2) }
  if (!cpuRoot || (!fixturesPath && !args.includes('--list')) || !path.isAbsolute(cpuRoot)) fail('explicit absolute --cpu-root is required')
  const root = path.resolve(cpuRoot)
  if (!fs.existsSync(root) || !fs.lstatSync(root).isDirectory()) fail('CPU root is not a directory')
  if (fs.realpathSync(root) !== root || fs.lstatSync(root).isSymbolicLink()) fail('CPU root must be a real path, not a symlink')
  const expected = new Map([
    ['src/dsl/compiler.js', '6823f61f16c933563f3f14dc3d9b195f3952116df968235de796c44a8f9d756a'],
    ['src/dsl/error.js', 'fdc8a674431666d48a8094e3c7021120df3767226c870e7bb9eb88aa25abde93'],
    ['src/dsl/parser.js', '260798bbcb5ae4e1409a726f6f0225b262cd5c586703b810d39892195e505518'],
    ['src/dsl/tokenize.js', '83249cc23e612f6b2655ec2a1cdfcbdf1bbe83179793531b45c63fc8738f3cc2'],
    ['src/effects/definition.js', 'fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02'],
    ['src/effects/registry.js', '8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618'],
    ['src/effects/generated/upstream-snapshot.js', 'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090']
  ])
  const customExpected = new Map([...expected].filter(([key]) => !key.endsWith('upstream-snapshot.js')))
  const fixtures = JSON.parse(fs.readFileSync(fixturesPath, 'utf8'))
  if (!Array.isArray(fixtures)) fail('fixtures must be an array')
  function keyOf(file) {
    const relative = path.relative(root, file)
    if (relative.startsWith('..' + path.sep) || path.isAbsolute(relative)) fail('CPU import closure escapes the CPU root')
    return relative.split(path.sep).join('/')
  }
  function authenticate(file, key, hashes) {
    if (!hashes.has(key)) fail(`unexpected CPU import closure module: ${key}`)
    if (!fs.existsSync(file)) fail(`validated CPU root lacks ${key}`)
    const stat = fs.lstatSync(file)
    if (stat.isSymbolicLink()) fail(`CPU import must not be a symlink: ${key}`)
    if (!stat.isFile() || fs.realpathSync(file) !== file) fail(`CPU import must be a regular file: ${key}`)
    if (keyOf(file) !== key) fail(`CPU import path mismatch: ${key}`)
    const bytes = fs.readFileSync(file)
    if (crypto.createHash('sha256').update(bytes).digest('hex') !== hashes.get(key)) fail(`CPU import authority sha256 mismatch: ${key}`)
    const imports = [...bytes.toString('utf8').matchAll(/\bimport\s+(?:[^'"\n]+\s+from\s+)?['"]([^'"]+)['"]/g)].map((match) => match[1])
    for (const specifier of imports) {
      if (!specifier.startsWith('./')) fail(`unexpected CPU import in ${key}: ${specifier}`)
      const imported = path.resolve(path.dirname(file), specifier)
      authenticate(imported, keyOf(imported), hashes)
    }
  }
  const modes = new Set(fixtures.map((fixture) => fixture.registryMode))
  const hashes = modes.has('catalog_records') ? expected : customExpected
  for (const key of hashes.keys()) authenticate(path.join(root, ...key.split('/')), key, hashes)
  const compiler = await import(pathToFileURL(path.join(root, 'src/dsl/compiler.js')).href)
  const { EffectDefinition } = await import(pathToFileURL(path.join(root, 'src/effects/definition.js')).href)
  const { EffectRegistry } = await import(pathToFileURL(path.join(root, 'src/effects/registry.js')).href)
  const snapshot = modes.has('catalog_records') ? await import(pathToFileURL(path.join(root, 'src/effects/generated/upstream-snapshot.js')).href) : null
  if (args.includes('--list')) {
    if (!snapshot) fail('--list requires catalog_records closure')
    process.stdout.write(JSON.stringify(snapshot.effectRecords.map((record) => `${record.namespace}/${record.func}`).sort((left, right) => left.localeCompare(right))) + '\n')
    return
  }
  const compatibilityPath = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../src/effects/generated/backend_compatibility.json')
  let compatibility = null
  if (snapshot) {
    const compatibilityBytes = fs.readFileSync(compatibilityPath)
    const compatibilityHash = crypto.createHash('sha256').update(compatibilityBytes).digest('hex')
    if (compatibilityHash !== '1540c94aa7ce03a314cd3d49f9d809dae19353842b93630a40554460f3ba6f0c') fail('compatibility manifest sha256 mismatch')
    compatibility = JSON.parse(compatibilityBytes)
  }
  function customDefinitions() {
    const pass = (name) => [{ name: 'main', program: name, inputs: {}, outputs: { color: 'outputTex' } }]
    const params = {
      f: { type: 'float', default: 1 }, i: { type: 'int', default: 2 }, flag: { type: 'boolean', default: true },
      c: { type: 'color', default: [0, 0, 0] }, v2: { type: 'vec2', default: [0, 0] }, v3: { type: 'vec3', default: [0, 0, 0] },
      v4: { type: 'vec4', default: [0, 0, 0, 0] }, m: { type: 'mat3', default: [1,0,0,0,1,0,0,0,1] },
      e: { type: 'enum', default: 1, choices: { one: 1, zero: 0, marker: null } },
      member: { type: 'member', default: 1, choices: { brushed: 1, other: 2 } },
      palette: { type: 'palette', default: 1, choices: { brushed: 1, other: 2 } },
      str: { type: 'string', default: 'plain', choices: { plain: 'plain', bold: 'bold' } },
      surf: { type: 'surface', default: null }, vol: { type: 'volume', default: 'volume' }, geo: { type: 'geometry', default: 'geo' }
    }
    return [
      { namespace: 'fixture', func: 'all', kind: 'generator', domain: 'image', params, passes: pass('all') },
      { namespace: 'fixture', func: 'source', kind: 'generator', domain: 'image', params: { first: { type: 'int', default: 1 }, second: { type: 'int', default: 2 } }, passes: pass('source') },
      { namespace: 'fixture', func: 'alias', kind: 'generator', domain: 'image', paramAliases: { strength: 'amount' }, params: { amount: { type: 'float', default: 1 } }, passes: pass('alias') },
      { namespace: 'fixture', func: 'bounded', kind: 'generator', domain: 'image', params: { amount: { type: 'float', default: 1, min: 0, max: 2 } }, passes: pass('bounded') },
      { namespace: 'fixture', func: 'required', kind: 'generator', domain: 'image', params: { amount: { type: 'float' } }, passes: pass('required') },
      { namespace: 'fixture', func: 'mixer', kind: 'mixer', domain: 'image', params: {}, passes: pass('mixer') },
      { namespace: 'fixture', func: 'volumeGen', kind: 'generator', domain: 'volume-generator', params: {}, passes: pass('volumeGen') },
      { namespace: 'fixture', func: 'volumeFilter', kind: 'filter', domain: 'volume-filter', params: {}, passes: pass('volumeFilter') },
      { namespace: 'fixture', func: 'volumeRender', kind: 'filter', domain: 'volume-renderer', params: {}, passes: pass('volumeRender') },
      { namespace: 'fixture', func: 'loopBegin', kind: 'filter', domain: 'loop-begin', params: {}, passes: pass('loopBegin') },
      { namespace: 'fixture', func: 'loopEnd', kind: 'filter', domain: 'loop-end', params: {}, passes: pass('loopEnd') }
    ].map((spec) => new EffectDefinition(spec))
  }
  function registryFor(fixture) {
    return fixture.registryMode === 'catalog_records' ? new EffectRegistry(snapshot.effectRecords.map((record) => new EffectDefinition(record))) : new EffectRegistry(customDefinitions())
  }
  function tagged(value) {
    if (typeof value === 'number') {
      if (Number.isNaN(value)) return { kind: 'number', value: 'number:NaN' }
      if (value === Infinity) return { kind: 'number', value: 'number:+Infinity' }
      if (value === -Infinity) return { kind: 'number', value: 'number:-Infinity' }
      if (Object.is(value, -0)) return { kind: 'number', value: 'number:-0' }
      return { kind: 'number', value: `number:${String(value)}` }
    }
    if (value === null) return { kind: 'null' }
    if (typeof value === 'boolean') return { kind: 'boolean', value }
    if (typeof value === 'string') return { kind: 'string', value }
    if (Array.isArray(value)) return { kind: 'array', values: value.map(tagged) }
    if (value?.kind === 'input') return { kind: 'surface', value: { kind: 'input' } }
    if (value?.kind === 'surface') return { kind: 'surface', value: { kind: 'named', name: value.name, index: Number(value.name.slice(1)) } }
    return tagged(null)
  }
  function loc(value) { return { sourceName: value.sourceName, line: value.line, column: value.column, index: value.index } }
  function admission(definition, index) {
    const pass = definition.passes[index]
    const key = `${definition.id}:${pass.program}`
    let row = compatibility?.reference_passes?.find((item) => item.effect_id === definition.id && item.pass_index === index && item.program_key === key)
    if (!row) row = compatibility?.scatter?.program_key === key ? compatibility.scatter : null
    const status = row?.status === 'registered' ? 'scatter' : (row?.status ?? 'compatible')
    const reasons = row?.reasons ?? []
    if (status === 'scatter' && reasons.length === 0) reasons.push({ code: 'explicit_scatter_adapter', detail: key })
    return { index, name: pass.name, programKey: key, status, reasons }
  }
  function indexFor(source, line, column) {
    let currentLine = 1, currentColumn = 1, index = 0
    for (let offset = 0; offset < source.length;) {
      if (currentLine === line && currentColumn === column) return index
      const code = source.codePointAt(offset), units = code > 0xffff ? 2 : 1, text = source.slice(offset, offset + (code > 0xffff ? 2 : 1))
      offset += code > 0xffff ? 2 : 1; index += units
      if (text === '\n') { currentLine += 1; currentColumn = 1 } else currentColumn += units
    }
    return index
  }
  function canonical(fixture) {
    try {
      if (fixture.sourceSha256 && crypto.createHash('sha256').update(Buffer.from(fixture.source, 'utf8')).digest('hex') !== fixture.sourceSha256) fail(`fixture source sha256 mismatch: ${fixture.name}`)
      const registry = registryFor(fixture)
      const compiled = compiler.compileDsl(fixture.source, registry, { sourceName: fixture.sourceName ?? fixture.name })
      const availability = []
      const chains = compiled.chains.map((chain) => ({ loc: loc(chain.loc), steps: chain.steps.map((step) => {
        if (step.kind === 'read') return { kind: 'read', surface: step.surface, loc: loc(step.loc) }
        if (step.kind === 'write') return { kind: 'write', surface: step.surface, loc: loc(step.loc) }
        const passes = step.definition.passes.map((_, index) => admission(step.definition, index))
        availability.push(...passes)
        const params = Object.keys(step.params).map((name) => ({ name, value: tagged(step.params[name]) }))
        return { kind: 'effect', effectId: step.definition.id, domain: step.definition.domain, effectKind: step.definition.kind, params, explicitParams: [...step.explicitParams], passes, loc: loc(step.loc) }
      }) }))
      const executable = availability.every((pass) => pass.status === 'compatible' || pass.status === 'scatter')
      if (fixture.options?.requireExecutable && !executable) {
        const unavailable = availability.find((pass) => pass.status !== 'compatible' && pass.status !== 'scatter')
        const step = compiled.chains.flatMap((chain) => chain.steps).find((item) => item.kind === 'effect' && item.definition.passes.some((pass) => `${item.definition.id}:${pass.program}` === unavailable.programKey))
        throw Object.assign(new Error(`${step.loc.sourceName}:${step.loc.line}:${step.loc.column}: Effect pass "${unavailable.programKey}" unavailable: ${unavailable.reasons.map((reason) => `${reason.code} (${reason.detail})`).join(': ')}`), { sourceName: step.loc.sourceName, line: step.loc.line, column: step.loc.column })
      }
      const provenance = fixture.registryMode === 'catalog_records'
        ? { kind: 'manifest', schema: 'noisemaker-cpp.effect-catalog-generator.v1', generatedPayloadSha256: 'c657378b1f21081acf4eb4a1cbbad9c6261b2010f2e42ef17e038b3e1a971f8d', normalizedRecordStreamSha256: '6ced4d890dc665f5f3d1196286260b972ae6858ccc9d045ec94c4e81479bf996', authorityLock: compatibility.authority?.cpu_behavioral_lock ?? '', cpuRevision: compatibility.authority?.cpu_revision ?? compatibility.authority?.cpu_behavioral_lock ?? '', sourceLockSha256: compatibility.authority?.source_lock_sha256 ?? '', upstreamRevision: compatibility.authority?.upstream_revision ?? '', upstreamTree: 'a7a997dfdc807697adba008729dcdfdfcfbaf53c', compatibilitySha256: '1540c94aa7ce03a314cd3d49f9d809dae19353842b93630a40554460f3ba6f0c', counts: { definitions: 205, passes: 305, referenceProgramKeys: 295, backendPrograms: 212, compatiblePrograms: 210, incompatiblePrograms: 1, missingPasses: 93, scatterPasses: 1, executableDefinitions: 166, incompleteDefinitions: 39 } }
        : { kind: 'custom', schema: 'noisemaker-cpp.execution-plan.custom', generatedPayloadSha256: '', normalizedRecordStreamSha256: 'custom', authorityLock: 'custom', cpuRevision: '', sourceLockSha256: '', upstreamRevision: '', upstreamTree: '', compatibilitySha256: 'custom', counts: { definitions: 0, passes: 0, referenceProgramKeys: 0, backendPrograms: 0, compatiblePrograms: 0, incompatiblePrograms: 0, missingPasses: 0, scatterPasses: 0, executableDefinitions: 0, incompleteDefinitions: 0 } }
      return { name: fixture.name, plan: { schema: 'noisemaker-cpp.execution-plan.v1', search: [...compiled.search], chains, renderSurface: compiled.renderSurface, requireExecutable: !!fixture.options?.requireExecutable, executable, availability, provenance } }
    } catch (error) {
      const sourceName = error.sourceName ?? fixture.sourceName ?? fixture.name, line = error.line ?? 1, column = error.column ?? 1
      return { name: fixture.name, error: { name: error.name === 'DslError' ? 'DslError' : 'DslError', message: error.message, sourceName, line, column, index: indexFor(fixture.source, line, column) } }
    }
  }
  const text = fixtures.map(canonical).map((entry) => JSON.stringify(entry)).join('\n') + '\n'
  if (checkPath && fs.readFileSync(checkPath, 'utf8') !== text) { console.error('js_frontend_oracle: checked expected stream differs'); process.exit(1) }
  if (outputPath) fs.writeFileSync(outputPath, text)
  else if (!checkPath) process.stdout.write(text)
}
