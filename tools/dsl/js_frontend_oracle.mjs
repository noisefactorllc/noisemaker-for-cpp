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
