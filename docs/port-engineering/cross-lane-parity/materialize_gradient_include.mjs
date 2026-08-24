import { createHash } from 'node:crypto'
import { readFile, writeFile } from 'node:fs/promises'
import { basename, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const SCHEMA = 'noisemaker-cpp-gradient-oracle-v2'
const here = new URL('.', import.meta.url)
const DEFAULT_JSON = fileURLToPath(new URL('./gradient_expected.json', here))
const DEFAULT_INCLUDE = fileURLToPath(new URL('./gradient_expected.inc', here))

function sha256(value) {
  return createHash('sha256').update(value).digest('hex')
}

function parseArgs(argv) {
  const args = { json: DEFAULT_JSON, include: DEFAULT_INCLUDE, mode: 'check' }
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '--json' || arg === '--include') {
      const value = argv[++index]
      if (!value) throw new Error(`${arg} requires a value`)
      args[arg.slice(2)] = resolve(value)
    } else if (arg === '--write' || arg === '--check' || arg === '--self-test') {
      args.mode = arg.slice(2)
    } else {
      throw new Error(`unknown argument: ${arg}`)
    }
  }
  return args
}

function validate(record) {
  if (record?.schema !== SCHEMA || record.identity !== 'synth/gradient:gradient') {
    throw new Error('materializer identity mismatch')
  }
  const width = record.witness?.width
  const height = record.witness?.height
  const length = width * height * 4
  if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0
      || !Number.isInteger(length)) throw new Error('invalid witness dimensions')
  if (!Array.isArray(record.output?.words) || record.output.words.length !== length
      || !record.output.words.every((word) => /^0x[0-9a-f]{8}$/.test(word))) {
    throw new Error('invalid exact Float32 witness')
  }
  if (!Array.isArray(record.output?.bytes) || record.output.bytes.length !== length
      || !record.output.bytes.every((byte) => Number.isInteger(byte) && byte >= 0 && byte <= 255)) {
    throw new Error('invalid exact RGBA8 witness')
  }
  if (record.provenance?.cpu_root !== '<CPU_ROOT>') throw new Error('unstable provenance')
  const canonical = record.provenance.source_files['src/effects/generated/canonical-kernels.js']
  if (!/^[0-9a-f]{64}$/.test(canonical?.sha256 ?? '')) throw new Error('missing canonical source hash')
  if (record.mutant_ledger?.status !== 'fail-closed') throw new Error('unproven mutant ledger')
}

function render(record, jsonBytes) {
  const { width, height } = record.witness
  const words = record.output.words
  const bytes = record.output.bytes
  const line = (values, format) => {
    const lines = []
    for (let index = 0; index < values.length; index += 8) {
      lines.push(`    ${values.slice(index, index + 8).map(format).join(', ')},`)
    }
    return lines.join('\n')
  }
  const canonicalHash = record.provenance.source_files['src/effects/generated/canonical-kernels.js'].sha256
  return `#pragma once
namespace gradient_oracle {
inline constexpr char kOracleJsonSha256[] = "${sha256(jsonBytes)}";
inline constexpr char kCanonicalFactorySourceSha256[] = "${canonicalHash}";
inline constexpr unsigned kWidth = ${width}U;
inline constexpr unsigned kHeight = ${height}U;
inline constexpr std::array<std::uint32_t, ${words.length}> kWords{
${line(words, (word) => word)}
};
inline constexpr std::array<std::uint8_t, ${bytes.length}> kBytes{
${line(bytes, (byte) => `${byte}U`)}
};
}  // namespace gradient_oracle
`
}

async function writeSidecar(path, bytes) {
  await writeFile(`${path}.sha256`, `${sha256(bytes)}  ${basename(path)}\n`)
}

async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv)
  const jsonBytes = await readFile(args.json)
  const record = JSON.parse(jsonBytes.toString('utf8'))
  validate(record)
  const expected = render(record, jsonBytes)
  if (args.mode === 'self-test') {
    validate(JSON.parse(jsonBytes.toString('utf8')))
    if (!expected.includes(`kOracleJsonSha256[] = "${sha256(jsonBytes)}"`)) {
      throw new Error('JSON/include provenance guard failed')
    }
    const existing = await readFile(args.include, 'utf8')
    if (existing !== expected) throw new Error('include self-test reproducibility mismatch')
    console.log('gradient include materializer self-test: ok')
    return
  }
  let existing = null
  try { existing = await readFile(args.include, 'utf8') } catch (error) {
    if (args.mode === 'check' && error.code !== 'ENOENT') throw error
  }
  if (args.mode === 'write') {
    await writeFile(args.include, expected)
    await writeSidecar(args.include, Buffer.from(expected))
    const scriptPath = fileURLToPath(import.meta.url)
    await writeSidecar(scriptPath, await readFile(scriptPath))
    console.log(`gradient include materializer write: ${args.include}`)
  } else {
    if (existing !== expected) throw new Error(`gradient include check failed: ${args.include}`)
    const sidecar = await readFile(`${args.include}.sha256`, 'utf8')
    const expectedSidecar = `${sha256(Buffer.from(expected))}  ${basename(args.include)}\n`
    if (sidecar !== expectedSidecar) throw new Error('gradient include sidecar mismatch')
    const scriptPath = fileURLToPath(import.meta.url)
    const scriptSidecar = await readFile(`${scriptPath}.sha256`, 'utf8')
    const expectedScriptSidecar = `${sha256(await readFile(scriptPath))}  ${basename(scriptPath)}\n`
    if (scriptSidecar !== expectedScriptSidecar) throw new Error('materializer script sidecar mismatch')
    console.log('gradient include materializer check: ok')
  }
}

main().catch((error) => {
  console.error(error.stack || error.message)
  process.exitCode = 1
})
