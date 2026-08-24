import fs from 'node:fs'

const RESERVED = ['time', 'globalTime', 'deltaTime', 'frame', 'tileOffset', 'fullResolution', 'resolution', 'aspect', 'aspectRatio']

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
  'docs/port-engineering/future-precompute/task31-curl/curl_oracle_generator.mjs.bak',
  'docs/port-engineering/future-precompute/task31/caustic_oracle_generator.mjs',
  'docs/port-engineering/future-precompute/task32-grade/grade_oracle_generator.mjs',
  'docs/port-engineering/future-precompute/focus_blur_oracle_generator.mjs',
]

// Find every `uniforms:` or `uniforms =` occurrence, then bracket-match the
// following `{ ... }` object literal (only when followed immediately by `{`
// -- skips `uniforms: definition.uniforms` / `uniforms: uniforms` identifier
// references, which are handled by the top-level-siblings check separately).
function extractObjectLiterals(text) {
  const results = []
  const re = /uniforms\s*[:=]\s*\{/g
  let m
  while ((m = re.exec(text))) {
    const start = m.index
    let depth = 0
    let i = text.indexOf('{', start)
    const objStart = i
    for (; i < text.length; i += 1) {
      if (text[i] === '{') depth += 1
      else if (text[i] === '}') {
        depth -= 1
        if (depth === 0) break
      }
    }
    const literal = text.slice(objStart, i + 1)
    const line = text.slice(0, start).split('\n').length
    results.push({ line, literal })
  }
  return results
}

for (const file of files) {
  const text = fs.readFileSync(file, 'utf8')
  const literals = extractObjectLiterals(text)
  const hits = []
  for (const { line, literal } of literals) {
    for (const key of RESERVED) {
      const propRe = new RegExp(`(^|[{,\\s])${key}\\s*:`, 'g')
      if (propRe.test(literal)) hits.push({ line, key })
    }
  }
  console.log(`${file} :: ${literals.length} uniforms-object-literal(s) found${hits.length ? '' : ', 0 reserved-key hits'}`)
  for (const h of hits) console.log(`    RESERVED KEY '${h.key}' inside uniforms literal at line ${h.line}`)
}
