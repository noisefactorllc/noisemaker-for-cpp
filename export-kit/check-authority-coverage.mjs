#!/usr/bin/env node
// Fails unless this kit's compat list names exactly the effects the JS authority renders.
// usage: node export-kit/check-authority-coverage.mjs --cpu-root <noisemaker-for-cpu checkout>
//
// The authority's renderable set is derived from its generated upstream snapshot the same way
// noisemaker-for-cpu documents it (export-kit/README-generation.md there): every sourceEffectId
// minus the snapshot's excludedEffects. The authority's own committed compat-effects.json is not
// used, because it is a generated file that can lag its snapshot.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const index = process.argv.indexOf('--cpu-root')
assert.ok(index > 1 && process.argv[index + 1], 'usage: node export-kit/check-authority-coverage.mjs --cpu-root <dir>')
const cpuRoot = path.resolve(process.argv[index + 1])
const snapshot = await import(pathToFileURL(path.join(cpuRoot, 'src/effects/generated/upstream-snapshot.js')).href)
assert.ok(Array.isArray(snapshot.sourceEffectIds) && snapshot.sourceEffectIds.length > 0, 'authority snapshot has no sourceEffectIds')
const excluded = new Set(Object.values(snapshot.excludedEffects ?? {}).flat())
const authority = snapshot.sourceEffectIds.filter(id => !excluded.has(id)).sort()

const kit = JSON.parse(await readFile(new URL('compat-effects.json', import.meta.url), 'utf8'))
const kitSet = new Set(kit)
const authoritySet = new Set(authority)
const missing = authority.filter(id => !kitSet.has(id))
const extra = kit.filter(id => !authoritySet.has(id))

console.log(`authority renders ${authority.length} effects; this kit claims ${kit.length}`)
if (missing.length) console.log(`missing from this kit (${missing.length}):\n  ${missing.join('\n  ')}`)
if (extra.length) console.log(`claimed but not rendered by the authority (${extra.length}):\n  ${extra.join('\n  ')}`)
process.exitCode = missing.length || extra.length ? 1 : 0
