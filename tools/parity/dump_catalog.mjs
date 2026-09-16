#!/usr/bin/env node
// Dumps the authenticated CPU authority's effect catalog to JSON so the
// Python sweep harness (tools/parity/sweep.py) can generate variants without
// re-importing the authority for every variant it builds. Authentication
// reuses corpus_authority.mjs -- there is no second trust path here.
//
// This file is read-only with respect to the authority: it never writes
// into the CPU root and never mutates the snapshot it imports.
import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { importCpu } from '../dsl/corpus_authority.mjs'

function usage(message) {
  if (message) console.error(`dump_catalog: ${message}`)
  console.error('usage: node dump_catalog.mjs --cpu-root ABS --output ABS [--authority-ledger ABS]')
  process.exit(2)
}
const args = process.argv.slice(2)
function arg(name) { const i = args.indexOf(name); return i < 0 ? null : args[i + 1] ?? usage(`${name} requires a value`) }
const cpuRootArg = arg('--cpu-root')
const outputArg = arg('--output')
const ledgerArg = arg('--authority-ledger')
if (!cpuRootArg || !path.isAbsolute(cpuRootArg)) usage('explicit absolute --cpu-root is required')
if (!outputArg || !path.isAbsolute(outputArg)) usage('absolute --output is required')
if (ledgerArg && !path.isAbsolute(ledgerArg)) usage('--authority-ledger must be absolute')

// Ported verbatim from noisemaker-for-cpu's own bin/noisemaker-cpu.js
// (effectProgram's needsParticlePipeline helper): detects an effect (e.g.
// points/heightGrid) that reads a particle-state global
// (global_xyz/vel/rgba/points_trail) as an input before any of its OWN
// passes writes it -- unlike the self-sufficient agent sims (physarum,
// flock, ...), it can only run chained after an upstream render/pointsEmit()
// that already created that state. The sweep harness needs this to build a
// program that has a chance of compiling instead of a guaranteed refusal.
function needsParticlePipeline(effect) {
  const written = new Set()
  for (const pass of effect.passes) {
    for (const input of Object.values(pass.inputs ?? {})) {
      if (/^global_(xyz|vel|rgba|points_trail)$/.test(input) && !written.has(input)) return true
    }
    for (const output of Object.values(pass.outputs ?? {})) written.add(output)
  }
  return false
}

async function main() {
  const { snapshot } = await importCpu(cpuRootArg, ledgerArg)
  // Only the fields the variant generator needs. Frozen/cloned catalog
  // objects serialize fine through JSON.stringify; nothing here is a
  // function or a Map.
  const effects = [...snapshot.effectRecords].sort((a, b) => a.id.localeCompare(b.id)).map((effect) => ({
    id: effect.id,
    namespace: effect.namespace,
    func: effect.func,
    kind: effect.kind,
    domain: effect.domain,
    iterated: effect.iterated === true,
    externalTexture: effect.externalTexture ?? null,
    needsParticlePipeline: needsParticlePipeline(effect),
    params: effect.params ?? {},
  }))
  const output = path.resolve(outputArg)
  if (fs.existsSync(output) && fs.lstatSync(output).isSymbolicLink()) throw new Error('output must not be a symlink')
  fs.mkdirSync(path.dirname(output), { recursive: true })
  fs.writeFileSync(output, `${JSON.stringify({ effects }, null, 2)}\n`)
  console.log(JSON.stringify({ output, count: effects.length }))
}
main().catch((error) => { console.error(`dump_catalog: ${error.message}`); process.exitCode = 1 })
