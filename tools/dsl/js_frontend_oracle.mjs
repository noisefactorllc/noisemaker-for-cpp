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
const EXPECTED_TOKENIZE_SHA256 = '83249cc23e612f6b2655ec2a1cdfcbdf1bbe83179793531b45c63fc8738f3cc2'
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
const moduleStat = fs.lstatSync(tokenizePath)
if (moduleStat.isSymbolicLink()) usage('CPU tokenizer module must not be a symlink')
if (!moduleStat.isFile()) usage('CPU tokenizer module must be a regular file')
const realTokenizePath = fs.realpathSync(tokenizePath)
if (realTokenizePath !== tokenizePath) usage('CPU tokenizer module must not be a symlink')
const relativeModule = path.relative(realRoot, realTokenizePath)
if (relativeModule.startsWith('..' + path.sep) || path.isAbsolute(relativeModule)) usage('CPU tokenizer module escapes the CPU root')
const moduleSha256 = crypto.createHash('sha256').update(fs.readFileSync(realTokenizePath)).digest('hex')
if (moduleSha256 !== EXPECTED_TOKENIZE_SHA256) usage(`CPU tokenizer authority sha256 mismatch: ${moduleSha256}`)
const fixtures = JSON.parse(fs.readFileSync(fixturesPath, 'utf8'))
if (!Array.isArray(fixtures)) usage('fixtures must be an array')
const { tokenizeDsl } = await import(pathToFileURL(tokenizePath).href)

function jsonString(value) {
  return JSON.stringify(value)
}
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
function canonicalCase(entry) {
  try {
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
