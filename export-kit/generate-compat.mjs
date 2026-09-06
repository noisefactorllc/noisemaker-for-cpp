#!/usr/bin/env node
// Run from any directory; --check verifies the committed list without writing.
import assert from 'node:assert/strict'
import { readFile, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const root = new URL('../', import.meta.url)
const backend = JSON.parse(await readFile(new URL('src/effects/generated/backend_compatibility.json', root), 'utf8'))
assert.equal(backend.schema, 'noisemaker-cpp.backend-compatibility.v1')
assert.ok(backend.reference_passes.length > 0, 'missing reference passes')

// The executor rejects measured divergences even when backend metadata admits
// their kernels. Read its guard as well; fail if its declaration changes shape.
const executor = await readFile(new URL('src/graph/executor.cpp', root), 'utf8')
const guard = executor.match(/std::array<MeasuredParityExclusion,\s*(\d+)>\s+kMeasuredParityExclusions\s*=\s*\{\{([\s\S]*?)\}\};/)
assert.ok(guard, 'cannot locate the executor parity exclusions')
const excludedKeys = [...guard[2].matchAll(/\{\s*"([^"\n]+:[^"\n]+)"/g)].map(match => match[1])
assert.equal(excludedKeys.length, Number(guard[1]), 'cannot read every executor parity exclusion')
const excluded = new Set(excludedKeys)
const overlayGuard = executor.match(/bool is_worm_overlay_resource\([^)]*\)[^{]*\{([^}]+)\}/)
assert.ok(overlayGuard, 'cannot locate the executor overlay exclusions')
const overlayEffects = [...overlayGuard[1].matchAll(/effect_id\s*==\s*"([^"]+)"/g)].map(match => match[1])
assert.ok(overlayEffects.length > 0, 'cannot read executor overlay exclusions')
const effects = new Map()
for (const pass of backend.reference_passes) {
  assert.match(pass.effect_id, /^[A-Za-z0-9_]+\/[A-Za-z0-9_]+$/)
  assert.equal(typeof pass.program_key, 'string')
  const admitted = pass.status === 'compatible' && !excluded.has(pass.program_key)
  effects.set(pass.effect_id, (effects.get(pass.effect_id) ?? true) && admitted)
}
// The shipped CLI renders output only; it cannot supply media's imageTex.
effects.delete('synth/media')
for (const id of overlayEffects) effects.delete(id)
const output = JSON.stringify([...effects].filter(([, admitted]) => admitted).map(([id]) => id).sort(), null, 2) + '\n'
const target = new URL('export-kit/compat-effects.json', root)
assert.ok(process.argv.slice(2).every(arg => arg === '--check'), 'usage: node export-kit/generate-compat.mjs [--check]')
if (process.argv.includes('--check')) {
  assert.equal(await readFile(target, 'utf8'), output, 'regenerate export-kit/compat-effects.json')
} else {
  await writeFile(target, output)
}
console.log(`${fileURLToPath(target)}: ${JSON.parse(output).length} compatible effects`)
