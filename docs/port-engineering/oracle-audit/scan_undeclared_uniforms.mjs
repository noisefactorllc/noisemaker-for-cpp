import fs from 'node:fs'

const files = [
  'docs/port-engineering/task-15-oracle-generator.mjs',
  'docs/port-engineering/task-16-oracle-generator.mjs',
  'docs/port-engineering/task-17-oracle-generator.mjs',
  'docs/port-engineering/task-18-oracle-generator.mjs',
  'docs/port-engineering/task-19-oracle-generator.mjs',
  'docs/port-engineering/task-20-oracle-generator.mjs',
  'docs/port-engineering/task-21-oracle-generator.mjs',
  'docs/port-engineering/task-22-oracle-generator.mjs',
  'docs/port-engineering/task-23-oracle-generator.mjs',
  'docs/port-engineering/task-24-oracle-generator.mjs',
  'docs/port-engineering/task-25-oracle-generator.mjs',
  'docs/port-engineering/task-26-oracle-generator.mjs',
  'docs/port-engineering/task-27-oracle-generator.mjs',
  'docs/port-engineering/task-28-oracle-generator.mjs',
  'docs/port-engineering/task-29-oracle-generator.mjs',
  'docs/port-engineering/future-precompute/task30/extrude_oracle_generator.mjs',
  'docs/port-engineering/future-precompute/task31-curl/curl_oracle_generator.mjs',
  'docs/port-engineering/future-precompute/task31/caustic_oracle_generator.mjs',
  'docs/port-engineering/future-precompute/task32-grade/grade_oracle_generator.mjs',
]

// Extract uniform key names used anywhere as `uniforms: { key: ... }` object
// literal property names (shallow -- top-level keys of each such literal).
function extractUniformKeys(text) {
  const keys = new Set()
  const re = /uniforms\s*:\s*\{/g
  let m
  while ((m = re.exec(text))) {
    let i = text.indexOf('{', m.index)
    const start = i
    let depth = 0
    for (; i < text.length; i += 1) {
      if (text[i] === '{') depth += 1
      else if (text[i] === '}') { depth -= 1; if (depth === 0) break }
    }
    const body = text.slice(start + 1, i)
    // Only match keys at this literal's top level (depth 0 relative to body) --
    // approximate by matching `identifier:` not preceded by another `{` immediately before on the same nesting.
    // Good enough for these generators' flat uniform literals; spread-only args (...defaults) are ignored (no colon).
    const keyRe = /(^|[{,\s])([A-Za-z_$][A-Za-z0-9_$]*)\s*:/g
    let km
    let localDepth = 0
    for (let j = 0; j < body.length; j += 1) {
      if (body[j] === '{' || body[j] === '[') localDepth += 1
      else if (body[j] === '}' || body[j] === ']') localDepth -= 1
    }
    while ((km = keyRe.exec(body))) keys.add(km[2])
  }
  return keys
}

// Extract declared binding/uniform names from any `'name:type@N'`-style
// signature strings anywhere in the file (binding_signature, uniform_binding_signature, etc).
function extractSignatureNames(text) {
  const names = new Set()
  const re = /'([A-Za-z_][A-Za-z0-9_]*):[A-Za-z0-9]+@\d+(?:\/S\d+)?'/g
  let m
  while ((m = re.exec(text))) names.add(m[1])
  return names
}

for (const file of files) {
  const text = fs.readFileSync(file, 'utf8')
  const uniformKeys = extractUniformKeys(text)
  const sigNames = extractSignatureNames(text)
  if (sigNames.size === 0) {
    console.log(`${file} :: no binding-signature strings found (nothing to cross-check against) -- uniform keys used: ${[...uniformKeys].sort().join(', ')}`)
    continue
  }
  const undeclared = [...uniformKeys].filter((k) => !sigNames.has(k))
  console.log(`${file} :: uniform keys=${uniformKeys.size} signature names=${sigNames.size}${undeclared.length ? ` UNDECLARED: ${undeclared.join(', ')}` : ' -- all uniform keys appear in a declared binding signature'}`)
}
