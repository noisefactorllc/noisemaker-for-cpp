#!/usr/bin/env node

// Export the CPU authority's ordered effectRecords without importing any live
// checkout.  This file intentionally has no package dependencies: the Python
// generator validates the resulting schema and joins authenticated backend
// evidence afterwards.
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

function usage(message) {
  if (message) console.error(`error: ${message}`)
  console.error('usage: export_cpu_catalog.mjs --cpu-root PATH --output PATH')
  process.exitCode = 2
}

function parseArgs(argv) {
  const args = {}
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    if (arg === '--cpu-root' || arg === '--output') {
      if (i + 1 >= argv.length) return usage(`${arg} requires a value`)
      args[arg.slice(2)] = argv[++i]
    } else if (arg === '--help') {
      return usage()
    } else {
      return usage(`unknown argument: ${arg}`)
    }
  }
  if (!args['cpu-root']) return usage('--cpu-root is required')
  if (!args.output) return usage('--output is required')
  return args
}

// JSON itself cannot represent these JavaScript Number values. Every value is
// typed, so a genuine authority string/object/array can never collide with a
// numeric sentinel. Records retain their observable top-level field keys and
// order; nested values use the envelope.
function encode(value) {
  if (typeof value === 'number') {
    if (Number.isNaN(value)) return { $type: 'number', value: 'NaN' }
    if (value === Infinity) return { $type: 'number', value: '+Infinity' }
    if (value === -Infinity) return { $type: 'number', value: '-Infinity' }
    if (Object.is(value, -0)) return { $type: 'number', value: '-0' }
    return { $type: 'number', value }
  }
  if (typeof value === 'string') return { $type: 'string', value }
  if (typeof value === 'boolean') return { $type: 'boolean', value }
  if (value === null) return { $type: 'null' }
  if (Array.isArray(value)) return { $type: 'array', items: value.map(encode) }
  const entries = []
  for (const [key, child] of Object.entries(value)) {
    if (child !== undefined) entries.push([key, encode(child)])
  }
  return { $type: 'object', entries }
}

function encodeRecord(record) {
  const result = {}
  for (const [key, value] of Object.entries(record)) {
    if (value !== undefined) result[key] = encode(value)
  }
  return result
}

async function main() {
  const args = parseArgs(process.argv.slice(2))
  if (!args) return
  const root = path.resolve(args['cpu-root'])
  let stat
  try { stat = fs.lstatSync(root) } catch { return usage(`CPU authority does not exist: ${root}`) }
  if (!stat.isDirectory() || stat.isSymbolicLink()) return usage(`CPU authority must be a real directory: ${root}`)
  const modulePath = path.join(root, 'src/effects/generated/upstream-snapshot.js')
  let effectRecords
  try {
    ({ effectRecords } = await import(pathToFileURL(modulePath).href))
  } catch (error) {
    console.error(`error: unable to load CPU effect records: ${error.message}`)
    process.exitCode = 1
    return
  }
  if (!Array.isArray(effectRecords)) {
    console.error('error: CPU effect records are not an array')
    process.exitCode = 1
    return
  }
  const document = {
    schema: 'noisemaker-cpp.cpu-effect-catalog.v1',
    records: effectRecords.map(encodeRecord),
  }
  const output = path.resolve(args.output)
  fs.mkdirSync(path.dirname(output), { recursive: true })
  fs.writeFileSync(output, `${JSON.stringify(document, null, 2)}\n`)
}

main().catch((error) => {
  console.error(`error: ${error.stack || error}`)
  process.exitCode = 1
})
