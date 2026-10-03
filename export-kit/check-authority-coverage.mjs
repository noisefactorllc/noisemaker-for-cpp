#!/usr/bin/env node
// Fails unless this kit's compat list names exactly the effects the JS authority renders.
// usage: node export-kit/check-authority-coverage.mjs --cpu-root <noisemaker-for-cpu checkout>
//
// Read the current runtime registry: historical snapshot exclusions can survive after effects
// are implemented. Neither those exclusions nor a generated compat list define current support.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const index = process.argv.indexOf('--cpu-root')
assert.ok(index > 1 && process.argv[index + 1], 'usage: node export-kit/check-authority-coverage.mjs --cpu-root <dir>')
const cpuRoot = path.resolve(process.argv[index + 1])
const catalog = await import(pathToFileURL(path.join(cpuRoot, 'src/effects/catalog.js')).href)
const authority = catalog.createDefaultRegistry().list().map(effect => effect.id).sort()
assert.ok(authority.length > 0, 'authority runtime registry has no effects')

const kit = JSON.parse(await readFile(new URL('compat-effects.json', import.meta.url), 'utf8'))
const kitSet = new Set(kit)
const authoritySet = new Set(authority)
const missing = authority.filter(id => !kitSet.has(id))
const extra = kit.filter(id => !authoritySet.has(id))

console.log(`authority renders ${authority.length} effects; this kit claims ${kit.length}`)
if (missing.length) console.log(`missing from this kit (${missing.length}):\n  ${missing.join('\n  ')}`)
if (extra.length) console.log(`claimed but not rendered by the authority (${extra.length}):\n  ${extra.join('\n  ')}`)
process.exitCode = missing.length || extra.length ? 1 : 0
