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

if (args.includes('--update')) usage('--update is unsupported; use --output with a new path and review it')

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
  const FIXTURE_SHA256 = '2cddd52470fe345cd70936141316aeae1ccf0b1d259bc23bb2bdc26c318828b6'
  const EXPECTED_STREAM_SHA256 = '4cf79daa1a05e06d3ee3e8f940b6d64a38b6922cc9d26e76309ab45eb93a81f5'
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
  const fixtureBytes = fs.readFileSync(fixturesPath)
  if (crypto.createHash('sha256').update(fixtureBytes).digest('hex') !== FIXTURE_SHA256) fail('compiler fixture corpus sha256 mismatch')
  if (checkPath) {
    const expectedBytes = fs.readFileSync(checkPath)
    if (crypto.createHash('sha256').update(expectedBytes).digest('hex') !== EXPECTED_STREAM_SHA256) fail('compiler expected stream sha256 mismatch')
  }
  const fixtures = JSON.parse(fixtureBytes.toString('utf8'))
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
    if (compatibilityHash !== 'c338050922d3ab90c3d6928f62f085c474ecc423e891671e6ebde2621892fb86') fail('compatibility manifest sha256 mismatch')
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
  function pairs(value) { return Object.entries(value ?? {}) }
  function taggedEffect(value) {
    if (value === null || value === undefined) return { kind: 'null' }
    if (typeof value === 'boolean') return { kind: 'boolean', value }
    if (typeof value === 'number') return { kind: 'number', value: taggedNumber(value) }
    if (typeof value === 'string') return { kind: 'string', value }
    if (Array.isArray(value)) return { kind: 'array', values: value.map(taggedEffect) }
    return { kind: 'object', entries: Object.entries(value).map(([name, item]) => [name, taggedEffect(item)]) }
  }
  function optionalEffect(value, present = value !== undefined && value !== null) {
    return present ? { present: true, value: taggedEffect(value) } : { present: false }
  }
  function optionalString(value, present = value !== undefined && value !== null) {
    return present ? { present: true, value: String(value) } : { present: false }
  }
  function dimension(value) {
    const result = { kind: 'unknown', parameter: '', inputOverride: '', literal: taggedNumber(0), defaultValue: taggedNumber(0), power: 1, raw: taggedEffect(value) }
    if (typeof value === 'number') { result.kind = 'literal'; result.literal = taggedNumber(value); return result }
    if (typeof value === 'string') {
      if (value === 'input') { result.kind = 'input'; result.parameter = 'input' }
      else if (value === 'screen') { result.kind = 'screen'; result.parameter = 'screen' }
      else if (value === 'resolution') { result.kind = 'resolution'; result.parameter = 'resolution' }
      else if (value.endsWith('%')) { result.kind = 'screen_division'; result.parameter = value }
      return result
    }
    if (value && typeof value === 'object') {
      result.parameter = value.param ?? value.screenDivide ?? ''
      result.inputOverride = value.inputOverride ?? ''
      result.defaultValue = taggedNumber(value.default ?? value.paramDefault ?? 0)
      result.power = value.power ?? 1
      if (value.paramDefault !== undefined) result.kind = 'parameter_default'
      else if (value.power !== undefined) result.kind = 'power'
      else if (value.screenDivide !== undefined) result.kind = 'screen_division'
      else if (value.param !== undefined) result.kind = 'parameter'
    }
    return result
  }
  function definitionProjection(definition, rawRecord = null) {
    const source = rawRecord ?? {}
    const params = Object.entries(definition.params ?? {}).map(([name, param]) => {
      const recordParam = rawRecord?.params?.[name] ?? null
      return {
      name, type: param.type ?? '', default: optionalEffect(param.default, Object.prototype.hasOwnProperty.call(param, 'default')), define: optionalString(param.define), uniform: optionalString(param.uniform),
      zero: optionalEffect(param.zero), enumValues: pairs(param.enumValues).map(([key, item]) => [key, taggedEffect(item)]), enumName: optionalString(param.enumName ?? recordParam?.enum), choices: pairs(param.choices).map(([key, item]) => [key, taggedEffect(item)]),
      min: optionalEffect(param.min), max: optionalEffect(param.max), texture: optionalString(param.texture), colorModeUniform: optionalString(param.colorModeUniform),
      cpuOnly: param.cpuOnly === true, raw: rawRecord ? Object.entries(param).map(([key, item]) => [key, taggedEffect(item)]) : []
      }
    })
    const passes = (definition.passes ?? []).map((pass) => {
      const blend = pass.blend === undefined || pass.blend === null ? { present: false } : {
        present: true,
        value: Array.isArray(pass.blend) ? { kind: 'factors', enabled: true, factors: [...pass.blend] } : { kind: 'boolean', enabled: pass.blend === true, factors: ['', ''] }
      }
      return {
        name: pass.name, program: pass.program, inputs: pairs(pass.inputs), outputs: pairs(pass.outputs), uniforms: pairs(pass.uniforms).map(([name, value]) => [name, taggedEffect(value)]),
        count: optionalEffect(pass.count), repeat: optionalEffect(pass.repeat), conditions: optionalEffect(pass.conditions), viewport: optionalEffect(pass.viewport), blend,
        drawMode: optionalString(pass.drawMode), drawBuffers: optionalEffect(pass.drawBuffers), raw: rawRecord ? Object.entries(pass).map(([key, item]) => [key, taggedEffect(item)]) : []
      }
    })
    const textures = Object.entries(definition.textures ?? {}).map(([name, texture]) => ({
      name, width: dimension(texture.width), height: dimension(texture.height), format: optionalString(texture.format), raw: rawRecord ? Object.entries(texture).map(([key, item]) => [key, taggedEffect(item)]) : []
    }))
    const raw = rawRecord ? Object.entries(rawRecord).map(([key, item]) => [key, taggedEffect(item)]) : []
    return {
      id: definition.id, directoryName: definition.directoryName ?? source.directoryName ?? '', name: definition.name ?? source.name ?? definition.func ?? '', namespace: definition.namespace, func: definition.func,
      kind: definition.kind, domain: definition.domain, tags: [...(definition.tags ?? [])], description: definition.description ?? '', parameterAliases: pairs(definition.paramAliases),
      parameters: params, passes, textures, externalTexture: optionalString(definition.externalTexture), outputTex3d: optionalString(definition.outputTex3d), outputGeo: optionalString(definition.outputGeo),
      outputXyz: optionalString(source.outputXyz), outputVelocity: optionalString(source.outputVel), outputRgba: optionalString(source.outputRgba), iterated: definition.iterated === true,
      loopRole: optionalString(definition.loopRole), raw
    }
  }
  const dimensionKinds = new Map(['input', 'screen', 'literal', 'parameter', 'parameter_default', 'power', 'screen_division', 'resolution', 'unknown'].map((name, index) => [name, index]))
  class CanonicalWriter {
    constructor() { this.parts = [] }
    token(value) { const text = String(value); this.parts.push(`${Buffer.byteLength(text, 'utf8')}:${text}`) }
    boolean(value) { this.token(value ? 'true' : 'false') }
    size(value) { this.token(String(value)) }
    number(value) {
      const bytes = new ArrayBuffer(8), view = new DataView(bytes); view.setFloat64(0, Number(value), false)
      const high = view.getUint32(0, false).toString(16).padStart(8, '0'), low = view.getUint32(4, false).toString(16).padStart(8, '0')
      this.token(`number-bits:${high}${low}`)
    }
    optional(value) { this.boolean(value) }
    output() { return this.parts.join('') }
  }
  function writeEffectValue(writer, value) {
    const kinds = { null: 0, boolean: 1, number: 2, string: 3, array: 4, object: 5 }; writer.size(kinds[value.kind])
    writer.boolean(value.kind === 'boolean' ? value.value : false); writer.number(value.kind === 'number' ? Number(String(value.value).replace(/^number:/, '')) : 0); writer.token(value.kind === 'string' ? value.value : '')
    const array = value.kind === 'array' ? value.values : []; writer.size(array.length); array.forEach((item) => writeEffectValue(writer, item))
    const entries = value.kind === 'object' ? value.entries : []; writer.size(entries.length); entries.forEach(([name, item]) => { writer.token(name); writeEffectValue(writer, item) })
  }
  function writePlanValue(writer, value) {
    const kind = value?.kind ?? 'null'; const kinds = { null: 0, boolean: 1, number: 2, string: 3, array: 4, surface: 5 }; writer.size(kinds[kind])
    if (kind === 'boolean') writer.boolean(value.value)
    else if (kind === 'number') writer.number(Number(String(value.value).replace(/^number:/, '')))
    else if (kind === 'string') writer.token(value.value)
    else if (kind === 'array') { writer.size(value.values.length); value.values.forEach((item) => writePlanValue(writer, item)) }
    else if (kind === 'surface') { const surface = value.value; writer.size(surface.kind === 'input' ? 1 : 2); writer.token(surface.name ?? ''); writer.size(surface.index ?? 0) }
  }
  function writePairs(writer, values, valueWriter) { writer.size(values.length); values.forEach(([name, value]) => { writer.token(name); valueWriter(writer, value) }) }
  function writeOptionalEffect(writer, value) { writer.optional(value.present); if (value.present) writeEffectValue(writer, value.value) }
  function writeOptionalString(writer, value) { writer.optional(value.present); if (value.present) writer.token(value.value) }
  function writeDimension(writer, value) { writer.size(dimensionKinds.get(value.kind)); writer.token(value.parameter); writer.token(value.inputOverride); writer.number(Number(String(value.literal).replace(/^number:/, ''))); writer.number(Number(String(value.defaultValue).replace(/^number:/, ''))); writer.number(value.power); writeEffectValue(writer, value.raw) }
  function writeDefinition(writer, value) {
    ;[value.id, value.directoryName, value.name, value.namespace, value.func, value.kind, value.domain].forEach((item) => writer.token(item)); writer.size(value.tags.length); value.tags.forEach((item) => writer.token(item)); writer.token(value.description); writePairs(writer, value.parameterAliases, (out, item) => out.token(item))
    writer.size(value.parameters.length); value.parameters.forEach((item) => { writer.token(item.name); writer.token(item.type); writeOptionalEffect(writer, item.default); writeOptionalString(writer, item.define); writeOptionalEffect(writer, item.zero); writePairs(writer, item.choices, writeEffectValue); writePairs(writer, item.enumValues, writeEffectValue); writeOptionalString(writer, item.enumName); writeOptionalEffect(writer, item.min); writeOptionalEffect(writer, item.max); writeOptionalString(writer, item.uniform); writeOptionalString(writer, item.texture); writeOptionalString(writer, item.colorModeUniform); writer.boolean(item.cpuOnly); writePairs(writer, item.raw, writeEffectValue) })
    writer.size(value.passes.length); value.passes.forEach((item) => { writer.token(item.name); writer.token(item.program); writePairs(writer, item.inputs, (out, entry) => out.token(entry)); writePairs(writer, item.outputs, (out, entry) => out.token(entry)); writePairs(writer, item.uniforms, writeEffectValue); writeOptionalEffect(writer, item.count); writeOptionalEffect(writer, item.repeat); writeOptionalEffect(writer, item.conditions); writeOptionalEffect(writer, item.viewport); writer.optional(item.blend.present); if (item.blend.present) { writer.size(item.blend.value.kind === 'factors' ? 1 : 0); writer.boolean(item.blend.value.enabled); writer.token(item.blend.value.factors[0]); writer.token(item.blend.value.factors[1]) } writeOptionalString(writer, item.drawMode); writeOptionalEffect(writer, item.drawBuffers); writePairs(writer, item.raw, writeEffectValue) })
    writer.size(value.textures.length); value.textures.forEach((item) => { writer.token(item.name); writeDimension(writer, item.width); writeDimension(writer, item.height); writeOptionalString(writer, item.format); writePairs(writer, item.raw, writeEffectValue) })
    writeOptionalString(writer, value.externalTexture); writeOptionalString(writer, value.outputTex3d); writeOptionalString(writer, value.outputGeo); writeOptionalString(writer, value.outputXyz); writeOptionalString(writer, value.outputVelocity); writeOptionalString(writer, value.outputRgba); writer.boolean(value.iterated); writeOptionalString(writer, value.loopRole); writePairs(writer, value.raw, writeEffectValue)
  }
  function writeBinding(writer, value) { ;[value.name, value.type, value.source, value.sourceName, value.resource, value.cppType].forEach((item) => writer.token(item ?? '')) }
  function writeOutput(writer, value) { writer.size(value.slot); writer.token(value.physicalName); writer.token(value.logicalRoute); writer.token(value.cppType) }
  function writeAuthority(writer, value) { writer.token(value.name); writePairs(writer, value.inputs, (out, item) => out.token(item)); writePairs(writer, value.outputs, (out, item) => out.token(item)); writePairs(writer, value.uniforms, writePlanValue); writer.token(value.blendKind); writer.boolean(value.blend); writer.token(value.blendFactors[0]); writer.token(value.blendFactors[1]); writer.optional(value.repeat.present); if (value.repeat.present) writePlanValue(writer, value.repeat.value) }
  function writeAdmission(writer, value) {
    writer.size(value.index); writer.token(value.name); writer.token(value.programKey); writer.size({ compatible: 0, scatter: 1, missing: 2, incompatible: 3 }[value.status]); writer.size(value.reasons.length); value.reasons.forEach((item) => { writer.token(item.code); writer.token(item.detail) }); writer.token(value.canonicalFactory); writer.token(value.sourceSha256); writer.token(value.semanticSha256); writer.size(value.capabilities.length); value.capabilities.forEach((item) => writer.token(item)); writer.token(value.dimensionality); writer.token(value.drawMode); [value.samplers, value.uniforms].forEach((items) => { writer.size(items.length); items.forEach((item) => writeBinding(writer, item)) }); writer.size(value.outputs.length); value.outputs.forEach((item) => writeOutput(writer, item)); writeAuthority(writer, value.authorityPass); writer.optional(value.scatter !== null); if (value.scatter !== null) { const item = value.scatter; ;[item.adapter, item.registry, item.drawMode, item.dimensionality, item.count, item.inputTexture, item.destinationMutation].forEach((entry) => writer.token(entry)); writer.boolean(item.blend); writer.size(item.uniforms.length); item.uniforms.forEach((entry) => writeBinding(writer, entry)); writer.size(item.outputs.length); item.outputs.forEach((entry) => writeOutput(writer, entry)) }
  }
  function hashSnapshot(value) { const writer = new CanonicalWriter(); writeDefinition(writer, value.definition); writer.size(value.admissions.length); value.admissions.forEach((item) => writeAdmission(writer, item)); return crypto.createHash('sha256').update(writer.output()).digest('hex') }
  function surfaceValue(value, location = null) { if (!value) return { kind: 'none', name: '', index: 0, loc: location }; if (typeof value === 'string') return { kind: 'named', name: value, index: Number(value.slice(1)), loc: location }; if (value.kind === 'input') return { kind: 'input', name: '', index: 0, loc: location }; return { kind: 'named', name: value.name, index: Number(String(value.name).slice(1)), loc: location } }
  function writeSurface(writer, value) { writer.size({ none: 0, input: 1, named: 2 }[value.kind]); writer.token(value.name); writer.size(value.index); const location = value.loc ?? { sourceName: '', line: 0, column: 0, index: 0 }; writer.token(location.sourceName); writer.size(location.line); writer.size(location.column); writer.size(location.index) }
  function writeStep(writer, value) {
    if (value.kind === 'read' || value.kind === 'write') { writer.token(value.kind); writeSurface(writer, surfaceValue(value.surface, value.surfaceLocation ?? value.loc)); writer.token(value.loc.sourceName); writer.size(value.loc.line); writer.size(value.loc.column); writer.size(value.loc.index); return }
    writer.token('effect'); writer.token(value.effectId); writer.token(value.domain); writer.token(value.effectKind); writer.size(value.snapshotIndex); writer.size(value.params.length); value.params.forEach((item) => { writer.token(item.name); writePlanValue(writer, item.value) }); writer.size(value.explicitParams.length); value.explicitParams.forEach((item) => writer.token(item)); writer.size(value.passes.length); value.passes.forEach((item) => writeAdmission(writer, item)); const location = value.loc; writer.token(location.sourceName); writer.size(location.line); writer.size(location.column); writer.size(location.index)
  }
  function hashPlan(value, renderLocation) { const writer = new CanonicalWriter(); writer.size(value.search.length); value.search.forEach((item) => writer.token(item)); writer.size(value.effects.length); value.effects.forEach((item) => { writeDefinition(writer, item.definition); writer.size(item.admissions.length); item.admissions.forEach((admissionValue) => writeAdmission(writer, admissionValue)) }); writer.size(value.chains.length); value.chains.forEach((chain) => { writer.token(chain.loc.sourceName); writer.size(chain.loc.line); writer.size(chain.loc.column); writer.size(chain.loc.index); writer.size(chain.steps.length); chain.steps.forEach((item) => writeStep(writer, item)) }); writeSurface(writer, surfaceValue(value.renderSurface, renderLocation)); writer.boolean(value.requireExecutable); writer.boolean(value.executable); writer.size(value.availability.length); value.availability.forEach((item) => writeAdmission(writer, item)); return crypto.createHash('sha256').update(writer.output()).digest('hex') }

  function admission(definition, index) {
    const pass = definition.passes[index]
    const key = `${definition.id}:${pass.program}`
    const reference = compatibility?.reference_passes?.find((item) => item.effect_id === definition.id && item.pass_index === index && item.program_key === key)
    const row = compatibility?.canonical_programs?.find((item) => item.program_key === key)
    const scatterRow = compatibility?.scatter?.program_key === key ? compatibility.scatter : null
    const status = reference?.status === 'scatter' || scatterRow ? 'scatter' : (reference?.status ?? 'compatible')
    const reasons = (reference?.reasons ?? []).map((reason) => ({ code: reason.code, detail: reason.detail }))
    if (status === 'scatter' && reasons.length === 0) reasons.push({ code: 'explicit_scatter_adapter', detail: key })
    const blend = pass.blend
    const authorityPass = {
      name: pass.name, inputs: pairs(pass.inputs), outputs: pairs(pass.outputs), uniforms: pairs(pass.uniforms).map(([name, value]) => [name, tagged(value)]),
      blendKind: Array.isArray(blend) ? 'factors' : (typeof blend === 'boolean' ? 'boolean' : 'none'),
      blend: Array.isArray(blend) ? true : (blend === true),
      blendFactors: Array.isArray(blend) ? [...blend] : ['', ''],
      repeat: pass.repeat == null ? { present: false } : { present: true, value: tagged(pass.repeat) }
    }
    const bindings = (items) => (items ?? []).map((item) => ({ name: item.name ?? '', type: item.type ?? '', source: item.source ?? '', sourceName: item.source_name ?? '', resource: item.resource ?? '', cppType: item.cpp_type ?? '' }))
    const outputs = (items) => (items ?? []).map((item) => ({ slot: item.slot, physicalName: item.physical_name ?? '', logicalRoute: item.logical_route ?? '', cppType: item.cpp_type ?? '' }))
    const scatterBindings = (items) => (items ?? []).map((item) => ({ name: item.name ?? '', type: item.type ?? '', cppType: item.cpp_type ?? '', source: item.source ?? '', sourceName: item.source_name ?? '', resource: item.resource ?? '' }))
    const result = {
      index, name: pass.name, programKey: key, status, reasons,
      canonicalFactory: row?.factory?.canonical ?? '', sourceSha256: row?.new_raw_sha256 ?? '', semanticSha256: row?.semantic?.old_typed_ir_sha256 ?? '',
      capabilities: [...(row?.capabilities ?? [])], dimensionality: row?.dimensionality ?? '', drawMode: row?.draw_mode ?? '',
      samplers: bindings(row?.samplers), uniforms: bindings(row?.uniforms), outputs: outputs(row?.outputs), authorityPass
    }
    const scatterOutputs = scatterRow?.outputs ?? (scatterRow?.output_abi
      ? (scatterRow.output_abi.canonical_slots ?? []).map((slot, outputIndex) => ({
        slot,
        physical_name: scatterRow.output_abi.physical_names?.[outputIndex] ?? '',
        logical_route: scatterRow.output_abi.logical_routes?.[outputIndex] ?? scatterRow.output_route ?? '',
        // The registered scatter contract currently has one vec4 output; retain
        // the C++ ABI type in the cross-language projection rather than dropping
        // this load-bearing output field when the manifest uses output_abi arrays.
        cpp_type: scatterRow.output_abi.cpp_type ?? 'glsl::Vec4'
      }))
      : [])
    result.scatter = status === 'scatter' ? {
      adapter: scatterRow?.adapter ?? 'noisemaker::scatter::wormhole::adapter', registry: scatterRow?.registry ?? 'noisemaker::scatter::resolve_scatter_adapter',
      drawMode: scatterRow?.draw_mode ?? 'points', dimensionality: scatterRow?.dimensionality ?? 'image', count: scatterRow?.count ?? 'input',
      inputTexture: scatterRow?.input_texture ?? 'inputTex', destinationMutation: scatterRow?.destination_mutation ?? 'in_place_accumulate', blend: scatterRow?.blend ?? true,
      uniforms: scatterBindings(scatterRow?.uniforms), outputs: scatterOutputs.map((item) => ({ slot: item.slot, physicalName: item.physical_name, logicalRoute: item.logical_route, cppType: item.cpp_type }))
    } : null
    return result
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
      const snapshots = []
      const snapshotIndexes = new Map()
      const chains = compiled.chains.map((chain, chainIndex) => ({ loc: loc(chain.loc), steps: chain.steps.map((step, stepIndex) => {
        const surfaceLocation = compiled.ast?.chains?.[chainIndex]?.calls?.[stepIndex]?.args?.[0]?.value?.loc ?? null
        if (step.kind === 'read') return { kind: 'read', surface: step.surface, loc: loc(step.loc), surfaceLocation: loc(surfaceLocation ?? step.loc) }
        if (step.kind === 'write') return { kind: 'write', surface: step.surface, loc: loc(step.loc), surfaceLocation: loc(surfaceLocation ?? step.loc) }
        const passes = step.definition.passes.map((_, index) => admission(step.definition, index))
        availability.push(...passes)
        const params = Object.keys(step.params).map((name) => ({ name, value: tagged(step.params[name]) }))
        let snapshotIndex = snapshotIndexes.get(step.definition.id)
        if (snapshotIndex === undefined) {
          snapshotIndex = snapshots.length
          snapshotIndexes.set(step.definition.id, snapshotIndex)
          const rawRecord = snapshot?.effectRecords?.find((record) => record.id === step.definition.id) ?? null
          const snapshotValue = { effectId: step.definition.id, definition: definitionProjection(step.definition, rawRecord), admissions: passes, snapshotSha256: '' }
          snapshotValue.snapshotSha256 = hashSnapshot(snapshotValue)
          snapshots.push(snapshotValue)
        }
        return { kind: 'effect', effectId: step.definition.id, domain: step.definition.domain, effectKind: step.definition.kind, snapshotIndex, params, explicitParams: [...step.explicitParams], passes, loc: loc(step.loc) }
      }) }))
      const executable = availability.every((pass) => pass.status === 'compatible' || pass.status === 'scatter')
      if (fixture.options?.requireExecutable && !executable) {
        const unavailable = availability.find((pass) => pass.status !== 'compatible' && pass.status !== 'scatter')
        const step = compiled.chains.flatMap((chain) => chain.steps).find((item) => item.kind === 'effect' && item.definition.passes.some((pass) => `${item.definition.id}:${pass.program}` === unavailable.programKey))
        throw Object.assign(new Error(`${step.loc.sourceName}:${step.loc.line}:${step.loc.column}: Effect pass "${unavailable.programKey}" unavailable: ${unavailable.reasons.map((reason) => `${reason.code} (${reason.detail})`).join(': ')}`), { sourceName: step.loc.sourceName, line: step.loc.line, column: step.loc.column })
      }
      const provenance = fixture.registryMode === 'catalog_records'
        ? { sourceSha256: crypto.createHash('sha256').update(Buffer.from(fixture.source, 'utf8')).digest('hex'), sourceName: fixture.sourceName ?? fixture.name, planPayloadSha256: '', kind: 'manifest', schema: 'noisemaker-cpp.effect-catalog-generator.v1', backendSchema: 'noisemaker-cpp.backend-compatibility.v1', corpusRevision: 'a024dc3a960cc44af454abc7aebce50456c194e6', generatedPayloadSha256: '4f744f6e62e9592554094f692ca113e9f95dd601ac573b7bc75f02a409b2232c', normalizedRecordStreamSha256: '6ced4d890dc665f5f3d1196286260b972ae6858ccc9d045ec94c4e81479bf996', authorityLock: compatibility.authority?.cpu_behavioral_lock ?? '', cpuRevision: compatibility.authority?.cpu_revision ?? compatibility.authority?.cpu_behavioral_lock ?? '', sourceLockSha256: compatibility.authority?.source_lock_sha256 ?? '', cpuPackageSha256: compatibility.authority?.cpu_package_sha256 ?? '', cpuPackageLockSha256: compatibility.authority?.cpu_package_lock_sha256 ?? '', cpuSourceLockSha256: compatibility.authority?.cpu_source_lock_sha256 ?? '', upstreamRevision: compatibility.authority?.upstream_revision ?? '', upstreamTree: 'a7a997dfdc807697adba008729dcdfdfcfbaf53c', upstreamPackageSha256: compatibility.authority?.upstream_package_sha256 ?? '', upstreamPackageLockSha256: compatibility.authority?.upstream_package_lock_sha256 ?? '', compatibilitySha256: 'c338050922d3ab90c3d6928f62f085c474ecc423e891671e6ebde2621892fb86', counts: { definitions: 205, passes: 305, referenceProgramKeys: 295, backendPrograms: 212, compatiblePrograms: 210, incompatiblePrograms: 1, missingPasses: 93, scatterPasses: 1, executableDefinitions: 166, incompleteDefinitions: 39 } }
        : { sourceSha256: crypto.createHash('sha256').update(Buffer.from(fixture.source, 'utf8')).digest('hex'), sourceName: fixture.sourceName ?? fixture.name, planPayloadSha256: '', kind: 'custom', schema: 'noisemaker-cpp.execution-plan.custom', backendSchema: '', corpusRevision: '', generatedPayloadSha256: '', normalizedRecordStreamSha256: 'custom', authorityLock: 'custom', cpuRevision: '', sourceLockSha256: '', cpuPackageSha256: '', cpuPackageLockSha256: '', cpuSourceLockSha256: '', upstreamRevision: '', upstreamTree: '', upstreamPackageSha256: '', upstreamPackageLockSha256: '', compatibilitySha256: 'custom', counts: { definitions: 0, passes: 0, referenceProgramKeys: 0, backendPrograms: 0, compatiblePrograms: 0, incompatiblePrograms: 0, missingPasses: 0, scatterPasses: 0, executableDefinitions: 0, incompleteDefinitions: 0 } }
      const plan = { schema: 'noisemaker-cpp.execution-plan.v1', search: [...compiled.search], effects: snapshots, chains, renderSurface: compiled.renderSurface, requireExecutable: !!fixture.options?.requireExecutable, executable, availability, provenance }
      const renderLocation = compiled.ast?.render?.loc ?? [...chains].reverse().flatMap((chain) => [...chain.steps].reverse()).find((step) => step.kind === 'write')?.surfaceLocation ?? null
      provenance.planPayloadSha256 = hashPlan(plan, renderLocation)
      chains.forEach((chain) => chain.steps.forEach((step) => { delete step.surfaceLocation }))
      return { name: fixture.name, plan }
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
