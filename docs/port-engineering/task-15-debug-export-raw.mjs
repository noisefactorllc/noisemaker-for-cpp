import fs from 'node:fs'

const generator = 'docs/port-engineering/task-15-oracle-generator.mjs'
let source = fs.readFileSync(generator, 'utf8')
source = source.replaceAll("from '/Users/", "from 'file:///Users/")
source = source.replace(
  'f: sha256(f32),',
  "raw: Buffer.from(f32).toString('base64'), u: Object.fromEntries(Object.entries(uniforms).map(([name, value]) => [name, ArrayBuffer.isView(value) ? Array.from(value) : value])), f: sha256(f32),",
)
source = source.replace(
  "console.log(JSON.stringify({ ...result, output: outputPath, written: process.argv.includes('--write'), oracle_sha256: sha256(payload) }))",
  "fs.writeFileSync('docs/port-engineering/task-15-debug-raw.json', JSON.stringify(oracle))",
)
await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`)
