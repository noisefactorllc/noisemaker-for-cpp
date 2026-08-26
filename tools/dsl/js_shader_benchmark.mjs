#!/usr/bin/env node

import {spawnSync} from 'node:child_process'
import {createRequire} from 'node:module'
import fs from 'node:fs'
import http from 'node:http'
import os from 'node:os'
import path from 'node:path'
import {pathToFileURL} from 'node:url'

import {
    AUTHORITY_LEDGER_ENV,
    EXPECTED as CPU_AUTHORITY,
    authenticateCpuRoot as authenticateCpuAuthority,
    resolveAuthorityLedger,
} from './corpus_authority.mjs'
import {
    BENCHMARK_MODE,
    BENCHMARK_SAMPLES,
    BENCHMARK_SCHEMA,
    BENCHMARK_WARMUPS,
    BenchmarkError,
    FENCE_CALIBRATION_SAMPLES,
    ORIENTATION_AUTHENTICATION,
    ORIENTATION_CONTRACT,
    PLAYWRIGHT_VERSION,
    RENDER_OPTION_KEYS,
    UPSTREAM_REVISION,
    UPSTREAM_TREE,
    assertUpstreamPinAgreement,
    authenticateProbeOrientation,
    classifyAdapter,
    compareExactRgba8,
    describeContract,
    relateRenderOptions,
    renderOptionSet,
    resolvePinnedPlaywrightRoot,
    reverseRows,
    sha256,
    summarizeSamples,
    validateBenchmarkResult,
} from './shader_benchmark_lib.mjs'

// The tree under test. Derived from this file's own location, never from a
// session path: the generated documents this lane authenticates against are
// the ones sitting next to it in the repository.
const REPO_ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..')
const COMPATIBILITY_DOCUMENT = path.join(REPO_ROOT, 'src/effects/generated/backend_compatibility.json')
const CATALOG_PROVENANCE_DOCUMENT = path.join(REPO_ROOT, 'src/effects/generated/effect_catalog.provenance.json')

const BOOLEAN_FLAGS = new Set(['--describe', '--allow-software'])
const HEX_64 = /^[0-9a-f]{64}$/

// Probe geometry. Both extents stay under 255 so every probe channel is an
// exact 8-bit value, and they differ so a transposed readback cannot pass.
const PROBE_WIDTH = 13
const PROBE_HEIGHT = 7

const PROBE_GLSL = `#version 300 es
precision highp float;
uniform float probeHeight;
out vec4 fragColor;
void main() {
    float column = floor(gl_FragCoord.x);
    float row = floor(gl_FragCoord.y);
    fragColor = vec4((row + 1.0) / 255.0, (column + 1.0) / 255.0, (probeHeight - row) / 255.0, 1.0);
}
`

const PROBE_WGSL = `
@group(0) @binding(0) var<uniform> probeHeight: f32;
@fragment
fn main(@builtin(position) position: vec4<f32>) -> @location(0) vec4<f32> {
    let column = floor(position.x);
    let row = floor(position.y);
    return vec4<f32>((row + 1.0) / 255.0, (column + 1.0) / 255.0, (probeHeight - row) / 255.0, 1.0);
}
`

function parseArguments(argv) {
    const values = new Map()
    for (let index = 0; index < argv.length; index++) {
        const key = argv[index]
        if (!key.startsWith('--')) throw new BenchmarkError('ERR_ARGUMENTS', `unexpected argument: ${key}`)
        if (values.has(key)) throw new BenchmarkError('ERR_ARGUMENTS', `duplicate argument: ${key}`)
        if (BOOLEAN_FLAGS.has(key)) { values.set(key, true); continue }
        const value = argv[++index]
        if (value === undefined || value.startsWith('--')) throw new BenchmarkError('ERR_ARGUMENTS', `${key} requires a value`)
        values.set(key, value)
    }
    return values
}

function requireArgument(values, name) {
    const value = values.get(name)
    if (!value) throw new BenchmarkError('ERR_ARGUMENTS', `${name} is required`)
    return value
}

function realRegularFile(input, label) {
    const absolute = path.resolve(input)
    const real = fs.realpathSync(absolute)
    if (real !== absolute) throw new BenchmarkError('ERR_PATH', `${label} must be a real, non-symlinked path`)
    if (!fs.statSync(real).isFile()) throw new BenchmarkError('ERR_PATH', `${label} must be a regular file`)
    return real
}

function realDirectory(input, label) {
    const absolute = path.resolve(input)
    const real = fs.realpathSync(absolute)
    if (real !== absolute) throw new BenchmarkError('ERR_PATH', `${label} must be a real, non-symlinked path`)
    if (!fs.statSync(real).isDirectory()) throw new BenchmarkError('ERR_PATH', `${label} must be a directory`)
    return real
}

function readJsonFile(input, label) {
    const file = realRegularFile(input, label)
    try {
        return {file, value: JSON.parse(fs.readFileSync(file, 'utf8'))}
    } catch (error) {
        throw new BenchmarkError('ERR_JSON', `${label} is not valid JSON`, {file, message: error.message})
    }
}

function checkedGitOutput(args, cwd, label) {
    const result = spawnSync('git', args, {cwd, encoding: 'utf8'})
    if (result.status !== 0) throw new BenchmarkError('ERR_GIT', `${label}: ${(result.stderr || result.stdout).trim()}`)
    return result.stdout.trim()
}

/**
 * Authenticate the generated documents of the tree under test. Nothing in this
 * lane is allowed to accept a case whose provenance describes a different
 * tree, so the payload hashes are read here and matched against the case.
 */
function authenticateTreeDocuments() {
    const compatibilityFile = realRegularFile(COMPATIBILITY_DOCUMENT, 'backend compatibility document')
    const compatibilitySha256 = sha256(fs.readFileSync(compatibilityFile))
    const provenance = readJsonFile(CATALOG_PROVENANCE_DOCUMENT, 'effect catalog provenance document').value
    const catalogPayloadSha256 = provenance?.generated_payload_sha256
    if (!HEX_64.test(catalogPayloadSha256 || '')) {
        throw new BenchmarkError('ERR_TREE_PROVENANCE', 'effect catalog provenance has no generated_payload_sha256')
    }
    return {compatibilitySha256, catalogPayloadSha256}
}

function authenticateShaderGit(rootInput) {
    const root = realDirectory(rootInput, 'shader Git root')
    if (checkedGitOutput(['cat-file', '-t', UPSTREAM_REVISION], root, 'upstream commit lookup') !== 'commit') {
        throw new BenchmarkError('ERR_UPSTREAM_PIN', 'pinned upstream object is not a commit')
    }
    const tree = checkedGitOutput(['rev-parse', `${UPSTREAM_REVISION}^{tree}`], root, 'upstream tree lookup')
    if (tree !== UPSTREAM_TREE) {
        throw new BenchmarkError('ERR_UPSTREAM_PIN', `upstream tree mismatch: expected ${UPSTREAM_TREE}, got ${tree}`)
    }
    return root
}

function archivePinnedShader(shaderGit) {
    const scratch = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'noisemaker-shader-benchmark-')))
    if (scratch === REPO_ROOT || scratch.startsWith(`${REPO_ROOT}${path.sep}`)) {
        fs.rmSync(scratch, {recursive: true})
        throw new BenchmarkError('ERR_SCRATCH', 'TMPDIR must be outside the checkout')
    }
    const archive = path.join(scratch, 'upstream.tar')
    const root = path.join(scratch, 'noisemaker')
    const archived = spawnSync('git', [
        'archive', '--format=tar', `--output=${archive}`, '--prefix=noisemaker/', UPSTREAM_REVISION,
    ], {cwd: shaderGit, encoding: 'utf8'})
    if (archived.status !== 0) {
        fs.rmSync(scratch, {recursive: true})
        throw new BenchmarkError('ERR_ARCHIVE', `git archive failed: ${(archived.stderr || archived.stdout).trim()}`)
    }
    const extracted = spawnSync('tar', ['-xf', archive, '-C', scratch], {encoding: 'utf8'})
    if (extracted.status !== 0) {
        fs.rmSync(scratch, {recursive: true})
        throw new BenchmarkError('ERR_ARCHIVE', `archive extraction failed: ${(extracted.stderr || extracted.stdout).trim()}`)
    }
    fs.unlinkSync(archive)
    return {scratch, root}
}

async function authenticateArchivedSource(cpuRoot, upstreamRoot) {
    const sourceLock = await import(`${pathToFileURL(path.join(cpuRoot, 'scripts/upstream/source-lock.js')).href}?task7`)
    if (sourceLock.PINNED_UPSTREAM_REVISION !== CPU_AUTHORITY.upstreamRevision ||
        sourceLock.PINNED_SOURCE_DIGEST !== CPU_AUTHORITY.upstreamSourceDigest) {
        throw new BenchmarkError('ERR_CPU_AUTHORITY', 'CPU source-lock constants do not match the benchmark contract')
    }
    sourceLock.assertPinnedSource(upstreamRoot, CPU_AUTHORITY.upstreamSourceDigest)
}

const MIME = new Map([
    ['.html', 'text/html; charset=utf-8'], ['.js', 'text/javascript; charset=utf-8'],
    ['.mjs', 'text/javascript; charset=utf-8'], ['.json', 'application/json; charset=utf-8'],
    ['.glsl', 'text/plain; charset=utf-8'], ['.wgsl', 'text/plain; charset=utf-8'],
    ['.css', 'text/css; charset=utf-8'],
])

async function serveDirectory(root) {
    const server = http.createServer((request, response) => {
        try {
            const pathname = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname)
            const candidate = path.resolve(root, `.${pathname}`)
            if (candidate !== root && !candidate.startsWith(`${root}${path.sep}`)) throw new Error('path escapes root')
            const real = fs.realpathSync(candidate)
            if (real !== candidate || (real !== root && !real.startsWith(`${root}${path.sep}`))) throw new Error('symlinked path')
            const stat = fs.statSync(real)
            if (!stat.isFile()) throw new Error('not a file')
            response.writeHead(200, {
                'Content-Type': MIME.get(path.extname(real)) || 'application/octet-stream',
                'Cache-Control': 'no-store',
                'Cross-Origin-Opener-Policy': 'same-origin',
                'Cross-Origin-Embedder-Policy': 'require-corp',
            })
            fs.createReadStream(real).pipe(response)
        } catch {
            response.writeHead(404, {'Content-Type': 'text/plain; charset=utf-8'})
            response.end('not found')
        }
    })
    await new Promise((resolve, reject) => {
        server.once('error', reject)
        server.listen(0, '127.0.0.1', resolve)
    })
    const address = server.address()
    return {
        url: `http://127.0.0.1:${address.port}`,
        close: () => new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve())),
    }
}

function normalizeCase(record, treeAuthority) {
    if (!record || typeof record !== 'object' || record.recordKind === 'excluded') {
        throw new BenchmarkError('ERR_CASE', 'case must be an admitted object')
    }
    if (typeof record.id !== 'string' || record.id.length === 0) throw new BenchmarkError('ERR_CASE', 'case id is required')
    if (typeof record.source !== 'string' || sha256(Buffer.from(record.source, 'utf8')) !== record.sourceSha256) {
        throw new BenchmarkError('ERR_CASE', 'case source SHA-256 mismatch')
    }
    if (!Number.isSafeInteger(record.width) || record.width <= 0 ||
        !Number.isSafeInteger(record.height) || record.height <= 0) {
        throw new BenchmarkError('ERR_CASE', 'case dimensions are invalid')
    }
    const plan = record.plan || {}
    const effectIds = plan.effectIds || record.effectIds
    if (!Array.isArray(effectIds) || effectIds.length === 0 || effectIds.some(value => typeof value !== 'string')) {
        throw new BenchmarkError('ERR_CASE', 'case plan.effectIds must be nonempty')
    }
    const planSha256 = plan.cpuPlanSha256 || record.planSha256
    if (!HEX_64.test(planSha256 || '')) throw new BenchmarkError('ERR_CASE', 'case CPU plan SHA-256 is required')
    const provenance = record.provenance || {}
    const cpuBehavioralLock = provenance.cpuBehavioralLock || provenance.behavioral_lock_sha256
    const catalogPayloadSha256 = provenance.catalogPayloadSha256 || provenance.catalog_payload_sha256
    const compatibilitySha256 = provenance.compatibilitySha256 || provenance.compatibility_sha256
    for (const [name, value] of [['cpuBehavioralLock', cpuBehavioralLock],
        ['catalogPayloadSha256', catalogPayloadSha256], ['compatibilitySha256', compatibilitySha256]]) {
        if (!HEX_64.test(value || '')) throw new BenchmarkError('ERR_CASE', `case provenance.${name} is missing or malformed`)
    }
    // The case must describe the tree under test and the authenticated CPU
    // authority, not some earlier generation of either.
    if (cpuBehavioralLock !== CPU_AUTHORITY.behavioralLockSha256) {
        throw new BenchmarkError('ERR_CASE_PROVENANCE', 'case CPU behavioral lock does not match the authenticated CPU authority', {
            caseValue: cpuBehavioralLock, authority: CPU_AUTHORITY.behavioralLockSha256,
        })
    }
    if (catalogPayloadSha256 !== treeAuthority.catalogPayloadSha256) {
        throw new BenchmarkError('ERR_CASE_PROVENANCE', 'case catalog payload hash does not match the tree under test', {
            caseValue: catalogPayloadSha256, tree: treeAuthority.catalogPayloadSha256,
        })
    }
    if (compatibilitySha256 !== treeAuthority.compatibilitySha256) {
        throw new BenchmarkError('ERR_CASE_PROVENANCE', 'case backend-compatibility hash does not match the tree under test', {
            caseValue: compatibilitySha256, tree: treeAuthority.compatibilitySha256,
        })
    }
    // Options the shader lane cannot honour are refused, never dropped: the
    // CPU lane applies all of them, so silently ignoring one would compare two
    // different programs.
    const options = record.options || {}
    const oneShot = options.oneShot ?? 'ready'
    if (oneShot !== 'ready') {
        throw new BenchmarkError('ERR_UNSUPPORTED_OPTION',
            'the shader lane renders a single ready frame and cannot honour oneShot', {oneShot})
    }
    const renderScale = options.renderScale ?? 1
    if (renderScale !== 1) {
        throw new BenchmarkError('ERR_UNSUPPORTED_OPTION',
            'the shader lane renders at the case dimensions and cannot honour renderScale', {renderScale})
    }
    if (Array.isArray(record.seedSurfaces) && record.seedSurfaces.length > 0) {
        throw new BenchmarkError('ERR_UNSUPPORTED_OPTION',
            'the shader lane cannot seed surfaces; the CPU lane would render a different program',
            {seedSurfaces: record.seedSurfaces.map(seed => seed?.name ?? null)})
    }
    for (const key of Object.keys(options)) {
        if (!RENDER_OPTION_KEYS.includes(key)) {
            throw new BenchmarkError('ERR_UNSUPPORTED_OPTION', `the shader lane does not apply case option ${key}`, {option: key})
        }
    }
    if (options.width !== undefined && options.width !== record.width) {
        throw new BenchmarkError('ERR_CASE', 'case options.width disagrees with the case width')
    }
    if (options.height !== undefined && options.height !== record.height) {
        throw new BenchmarkError('ERR_CASE', 'case options.height disagrees with the case height')
    }
    return {
        id: record.id, source: record.source, sourceSha256: record.sourceSha256,
        width: record.width, height: record.height,
        options: {
            time: Number(options.time ?? 0), frame: Number(options.frame ?? 0),
            seed: Number(options.seed ?? 0), oneShot, renderScale,
        },
        plan: {
            cpuPlanSha256: planSha256,
            effectIds,
            passKeys: Array.isArray(plan.passKeys) ? plan.passKeys : null,
            finalSurface: plan.finalSurface || null,
        },
        provenance: {cpuBehavioralLock, catalogPayloadSha256, compatibilitySha256},
    }
}

/**
 * The expected image must come from the authenticated CPU runner and must
 * describe this exact case. A hand-authored expectation cannot satisfy this.
 */
function normalizeExpectation(document, testCase) {
    if (!document || typeof document !== 'object') throw new BenchmarkError('ERR_EXPECTED', 'expected record must be an object')
    if (document.schema !== 'noisemaker-cpp.dsl-cpu-expectation.v1') {
        throw new BenchmarkError('ERR_EXPECTED',
            'expected document must be a noisemaker-cpp.dsl-cpu-expectation.v1 produced by tools/benchmark/run_cpu_case.mjs',
            {schema: document.schema ?? null})
    }
    if (document.id !== testCase.id) throw new BenchmarkError('ERR_EXPECTED', 'expected document is for another case', {expected: testCase.id, actual: document.id})
    if (document.sourceSha256 !== testCase.sourceSha256) throw new BenchmarkError('ERR_EXPECTED', 'expected document DSL source hash differs from the case')
    if (document.planSha256 && document.planSha256 !== testCase.plan.cpuPlanSha256) {
        throw new BenchmarkError('ERR_EXPECTED', 'expected document CPU plan hash differs from the case')
    }
    if (document.width !== testCase.width || document.height !== testCase.height) {
        throw new BenchmarkError('ERR_EXPECTED', 'expected document dimensions differ from the case')
    }
    // Identity binds the expectation to the case's *program*; this binds it to
    // the case's *render*. Without it the driver will compare a case rendered
    // at one time/frame/seed against an expectation rendered at another and
    // sign the verdict — pass or fail — as if it were about one program.
    const optionRelation = relateRenderOptions(
        renderOptionSet(testCase.options, testCase.width, testCase.height),
        renderOptionSet(document.options,
            document.options?.width ?? document.width, document.options?.height ?? document.height))
    if (optionRelation.status !== 'bound') {
        throw new BenchmarkError('ERR_EXPECTED_OPTIONS',
            'expected document was rendered with different options than the case', optionRelation)
    }
    if (document.format !== 'rgba8' || document.orientation !== 'top-down') {
        throw new BenchmarkError('ERR_EXPECTED', 'expected document must be top-down raw RGBA8')
    }
    const authority = document.authority || {}
    for (const [key, value] of [
        ['behavioralLockSha256', CPU_AUTHORITY.behavioralLockSha256],
        ['packageSha256', CPU_AUTHORITY.packageSha256],
        ['packageLockSha256', CPU_AUTHORITY.packageLockSha256],
        ['sourceLockSha256', CPU_AUTHORITY.sourceLockSha256],
        ['upstreamRevision', CPU_AUTHORITY.upstreamRevision],
        ['upstreamSourceDigest', CPU_AUTHORITY.upstreamSourceDigest],
    ]) {
        if (authority[key] !== value) {
            throw new BenchmarkError('ERR_EXPECTED_AUTHORITY',
                `expected document authority.${key} does not match the authenticated CPU authority`,
                {documentValue: authority[key] ?? null, authority: value})
        }
    }
    if (authority.behavioralLockSha256 !== testCase.provenance.cpuBehavioralLock) {
        throw new BenchmarkError('ERR_EXPECTED_AUTHORITY', 'expected document and case disagree on the CPU behavioral lock')
    }
    if (!HEX_64.test(document.runner?.sha256 || '')) {
        throw new BenchmarkError('ERR_EXPECTED_AUTHORITY', 'expected document must identify the CPU runner that produced it')
    }
    if (typeof document.rgba8Base64 !== 'string' || document.rgba8Base64.length === 0) {
        throw new BenchmarkError('ERR_EXPECTED', 'expected document must carry raw RGBA8 bytes')
    }
    const data = Uint8Array.from(Buffer.from(document.rgba8Base64, 'base64'))
    if (data.length !== testCase.width * testCase.height * 4) {
        throw new BenchmarkError('ERR_EXPECTED', 'expected RGBA8 byte length does not match the case dimensions')
    }
    const digest = sha256(data)
    if (document.rgba8Sha256 !== digest) throw new BenchmarkError('ERR_EXPECTED', 'expected RGBA8 SHA-256 mismatch')
    // A uniform expectation is legitimate but carries no spatial information;
    // the record says so rather than letting it stand in for one that does.
    let uniform = true
    for (let index = 4; index < data.length && uniform; index++) {
        if (data[index] !== data[index % 4]) uniform = false
    }
    return {
        width: document.width, height: document.height, data, sha256: digest, uniform,
        identity: {
            schema: document.schema, id: document.id,
            rgba8Sha256: digest, runnerSha256: document.runner.sha256,
            cpuBehavioralLock: authority.behavioralLockSha256,
            options: document.options ?? null,
        },
    }
}

function arraysEqual(left, right) {
    return Array.isArray(left) && Array.isArray(right) && left.length === right.length &&
        left.every((value, index) => value === right[index])
}

function isOrderedSubsequence(needle, haystack) {
    let cursor = 0
    for (const item of needle) {
        cursor = haystack.indexOf(item, cursor)
        if (cursor < 0) return false
        cursor++
    }
    return true
}

/**
 * Relate the shader graph to the two authenticated expectations: the effect
 * order the DSL source resolves to, and the pass projection the CPU plan
 * records for the effect under test. Neither relation is relabeled — a
 * disagreement is a mismatch, and an unavailable projection says so.
 */
function relateGraph(testCase, sourceEffectIds, actual) {
    if (!arraysEqual(sourceEffectIds, actual.effectIds)) {
        return {
            status: 'mismatch', reason: 'source_effect_order_mismatch',
            expectedEffectIds: sourceEffectIds, actual,
        }
    }
    if (!testCase.plan.passKeys || !testCase.plan.finalSurface) {
        return {
            status: 'projection_unavailable', reason: 'cpu_plan_projection_incomplete',
            expectedEffectIds: sourceEffectIds, actual,
        }
    }
    if (testCase.plan.finalSurface !== actual.finalSurface) {
        return {
            status: 'mismatch', reason: 'final_surface_mismatch',
            expectedEffectIds: sourceEffectIds, expected: testCase.plan, actual,
        }
    }
    if (!isOrderedSubsequence(testCase.plan.passKeys, actual.passKeys)) {
        return {
            status: 'mismatch', reason: 'cpu_plan_pass_keys_absent_from_shader_graph',
            expectedEffectIds: sourceEffectIds, expected: testCase.plan, actual,
        }
    }
    if (arraysEqual(testCase.plan.passKeys, actual.passKeys) &&
        arraysEqual(testCase.plan.effectIds, actual.effectIds)) {
        return {status: 'exact', reason: null, expectedEffectIds: sourceEffectIds, expected: testCase.plan, actual}
    }
    // The corpus plan projects only the effect under test; the source-derived
    // effect order above is what proves the rest of the graph.
    return {
        status: 'cpu_plan_projection_contained',
        reason: 'cpu_plan_records_only_the_effect_under_test',
        expectedEffectIds: sourceEffectIds, expected: testCase.plan, actual,
    }
}

function browserProgram(baseUrl, input) {
    const encoded = JSON.stringify({...input, baseUrl})
    return `<!doctype html><meta charset="utf-8"><canvas id="canvas"></canvas><script type="module">
const config=${encoded};
const probeGlsl=${JSON.stringify(PROBE_GLSL)};
const probeWgsl=${JSON.stringify(PROBE_WGSL)};
const errors=[];
window.addEventListener('error', event => errors.push(String(event.error?.message || event.message)));
const describeThrown=value=>{
  if(value instanceof Error) return {message:value.message,stack:value.stack,code:value.code??null,diagnostics:value.diagnostics??null};
  if(value&&typeof value==='object'){
    let serialized=null;
    try{serialized=JSON.parse(JSON.stringify(value));}catch(error){serialized=String(value);}
    return {message:value.message??JSON.stringify(serialized),stack:value.stack??null,code:value.code??null,diagnostics:value.diagnostics??null,value:serialized};
  }
  return {message:String(value),stack:null,code:null,diagnostics:null};
};
const run=async()=>{
  const module=await import(config.baseUrl+'/shaders/src/index.js');
  const {CanvasRenderer,lex,parse,isIOFunction}=module;
  // The effect load set is resolved from the authenticated DSL source through
  // the pinned upstream parser and the pinned upstream manifest, not from the
  // CPU plan projection, which lists only the effect under test.
  const resolveEffects=manifest=>{
    const ast=parse(lex(config.source));
    const searchOrder=Array.isArray(ast.namespace?.searchOrder)?ast.namespace.searchOrder:[];
    const ordered=[];const unresolved=[];
    const visit=node=>{
      if(Array.isArray(node)){for(const item of node)visit(item);return;}
      if(!node||typeof node!=='object')return;
      if(node.type==='Call'&&typeof node.name==='string'){
        if(!isIOFunction(node.name)){
          const candidates=[];
          if(node.namespace&&node.namespace.resolved)candidates.push(node.namespace.resolved+'/'+node.name);
          for(const ns of searchOrder)candidates.push(ns+'/'+node.name);
          const found=candidates.find(candidate=>Object.prototype.hasOwnProperty.call(manifest,candidate));
          if(found){if(!ordered.includes(found))ordered.push(found);}
          else unresolved.push({name:node.name,candidates});
        }
      }
      for(const value of Object.values(node))visit(value);
    };
    visit(ast.plans);
    if(unresolved.length)throw {code:'ERR_EFFECT_UNRESOLVED',message:'DSL calls do not resolve to pinned upstream effects',unresolved};
    return {searchOrder,effectIds:ordered};
  };
  const canvasFor=()=>{const canvas=document.createElement('canvas');canvas.width=config.width;canvas.height=config.height;document.body.append(canvas);return canvas;};
  const manifestRenderer=new CanvasRenderer({canvas:canvasFor(),width:config.width,height:config.height,basePath:config.baseUrl+'/shaders',preferWebGPU:config.backend==='webgpu',onError:error=>errors.push(String(error?.message||error))});
  await manifestRenderer.loadManifest();
  const resolved=resolveEffects(manifestRenderer.manifest);
  const missing=config.planEffectIds.filter(id=>!resolved.effectIds.includes(id));
  if(missing.length)throw {code:'ERR_PLAN_SOURCE_DISAGREEMENT',message:'CPU plan names effects the DSL source does not call',missing,resolved:resolved.effectIds};
  manifestRenderer.stop();await manifestRenderer.dispose({loseContext:false});
  const makeRenderer=async()=>{
    const renderer=new CanvasRenderer({canvas:canvasFor(),width:config.width,height:config.height,basePath:config.baseUrl+'/shaders',preferWebGPU:config.backend==='webgpu',onError:error=>errors.push(String(error?.message||error))});
    await renderer.loadManifest();
    const loaded=await renderer.loadEffects(resolved.effectIds);
    if(loaded.length!==resolved.effectIds.length)throw {code:'ERR_EFFECT_LOAD_FAILED',message:'not every resolved effect loaded',requested:resolved.effectIds,loaded:loaded.length};
    const pipeline=await renderer.compile(config.source); renderer.stop();
    if(!pipeline)throw {code:'ERR_NO_PIPELINE',message:'shader compilation returned no pipeline'};
    const name=pipeline.backend?.getName?.(); const expectedName=config.backend==='webgpu'?'WebGPU':'WebGL2';
    if(name!==expectedName)throw {code:'ERR_BACKEND_MISMATCH',message:'backend mismatch: expected '+expectedName+', got '+name};
    pipeline.globalUniforms.seed=config.options.seed; pipeline.frameIndex=config.options.frame; pipeline.syncTime(config.options.time);
    return {renderer,pipeline};
  };
  // Yielding through a MessageChannel task keeps the fence poll off
  // setTimeout's clamp, whose floor was two milliseconds in this browser.
  const channel=new MessageChannel();
  const yieldTask=()=>new Promise(resolve=>{channel.port1.onmessage=()=>resolve();channel.port2.postMessage(0);});
  const fenceMechanism=config.backend==='webgpu'?'webgpu_queue_on_submitted_work_done':'webgl2_fence_sync_message_channel_poll';
  const fence=async backend=>{
    if(backend.device?.queue?.onSubmittedWorkDone){await backend.device.queue.onSubmittedWorkDone();return;}
    const gl=backend.gl; if(!gl)throw {code:'ERR_NO_FENCE',message:'backend exposes no fence'};
    const sync=gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE,0); gl.flush();
    const deadline=performance.now()+10000;
    try{for(;;){
      const status=gl.clientWaitSync(sync,gl.SYNC_FLUSH_COMMANDS_BIT,0);
      if(status===gl.ALREADY_SIGNALED||status===gl.CONDITION_SATISFIED)return;
      if(status===gl.WAIT_FAILED)throw {code:'ERR_FENCE_FAILED',message:'WebGL fence wait failed'};
      if(performance.now()>deadline)throw {code:'ERR_FENCE_TIMEOUT',message:'WebGL fence did not signal within 10s'};
      await yieldTask();
    }}finally{gl.deleteSync(sync);}
  };
  const outputId=pipeline=>{const surface=pipeline.graph?.renderSurface;const id=surface?pipeline.frameReadTextures?.get(surface):null;if(!surface||!id)throw {code:'ERR_NO_RENDER_ROUTE',message:'final render route is missing'};return {surface,id};};
  const graphProjection=pipeline=>{const passes=pipeline.graph?.passes||[];const effectIds=[];const passKeys=[];const infrastructurePasses=[];for(const pass of passes){const rawKey=String(pass.effectKey||'');const effectName=rawKey.includes('.')?rawKey.slice(rawKey.lastIndexOf('.')+1):rawKey;const effectId=(pass.effectNamespace&&effectName)?pass.effectNamespace+'/'+effectName:null;let program=String(pass.program||'').replace(/^node_\\d+_/,'').replace(/__[A-Z0-9_]+_.+$/,'');if(effectId){if(!effectIds.includes(effectId))effectIds.push(effectId);passKeys.push(effectId+':'+program);}else{infrastructurePasses.push(String(pass.id||pass.program||'unknown'));}}return {effectIds,passKeys,finalSurface:pipeline.graph?.renderSurface||null,infrastructurePasses};};
  // Orientation probe. It compiles a program and draws a full-screen triangle
  // through the very same backend entry points the measured passes use, so it
  // observes the rasterizer's own row convention rather than an upload/readback
  // round trip. Its pattern varies with the shader-space row, so a flipped
  // readback cannot satisfy it.
  const orientationProbe=async(backend,format,index)=>{
    const textureId='__task7_orientation_'+index;
    const programId='__task7_orientation_program_'+index;
    backend.createTexture(textureId,{width:config.probeWidth,height:config.probeHeight,format,usage:['render','sample','copySrc','copyDst']});
    await backend.compileProgram(programId,config.backend==='webgpu'?{wgsl:probeWgsl}:{glsl:probeGlsl});
    backend.beginFrame({});
    backend.executePass({id:programId,program:programId,outputs:{color:textureId},clear:true,uniforms:{probeHeight:config.probeHeight}},{});
    backend.endFrame();
    await fence(backend);
    const read=await backend.readPixels(textureId);
    backend.destroyTexture(textureId);
    return {format,width:read.width,height:read.height,data:Array.from(read.data)};
  };
  const correctness=await makeRenderer();
  correctness.pipeline.render(config.options.time); await fence(correctness.pipeline.backend);
  const route=outputId(correctness.pipeline);
  const texture=correctness.pipeline.backend.textures.get(route.id);
  const pixels=await correctness.pipeline.backend.readPixels(route.id);
  const graph=graphProjection(correctness.pipeline); const passCount=correctness.pipeline.lastPassCount;
  const format={requested:texture?.format||null,actual:texture?.gpuFormat||texture?.format||null};
  const probeFormats=[...new Set([texture?.format||'rgba16f','rgba8unorm','rgba16f'])];
  const probes=[];
  for(let index=0;index<probeFormats.length;index++)probes.push(await orientationProbe(correctness.pipeline.backend,probeFormats[index],index));
  await correctness.renderer.dispose({loseContext:false});
  const timing=await makeRenderer(); const sampleNs=[]; const fenceFloorNs=[];
  for(let index=0;index<${BENCHMARK_WARMUPS};index++){timing.pipeline.syncTime(config.options.time);timing.pipeline.render(config.options.time);await fence(timing.pipeline.backend);}
  for(let index=0;index<${FENCE_CALIBRATION_SAMPLES};index++){const start=performance.now();await fence(timing.pipeline.backend);fenceFloorNs.push(Math.round((performance.now()-start)*1e6));}
  for(let index=0;index<${BENCHMARK_SAMPLES};index++){timing.pipeline.syncTime(config.options.time);const start=performance.now();timing.pipeline.render(config.options.time);await fence(timing.pipeline.backend);sampleNs.push(Math.round((performance.now()-start)*1e6));}
  await timing.renderer.dispose({loseContext:false});
  // Adapter identity for both lanes, always, so two records are never taken
  // for like-for-like when their renderers differ.
  const probeCanvas=document.createElement('canvas');
  const gl=probeCanvas.getContext('webgl2');
  const debugInfo=gl&&gl.getExtension('WEBGL_debug_renderer_info');
  const webgl=gl?{
    renderer:String(debugInfo?gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)),
    vendor:String(debugInfo?gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL):gl.getParameter(gl.VENDOR)),
    version:String(gl.getParameter(gl.VERSION)),
    shadingLanguageVersion:String(gl.getParameter(gl.SHADING_LANGUAGE_VERSION)),
  }:null;
  let webgpu=null;
  if(navigator.gpu){
    const adapter=await navigator.gpu.requestAdapter();
    if(adapter){
      const info=adapter.info||(adapter.requestAdapterInfo?await adapter.requestAdapterInfo():null);
      webgpu={vendor:String(info?.vendor??''),architecture:String(info?.architecture??''),device:String(info?.device??''),description:String(info?.description??''),isFallbackAdapter:adapter.isFallbackAdapter===true};
    }
  }
  if(errors.length)throw {code:'ERR_BROWSER_ERRORS',message:'browser errors: '+errors.join(' | '),errors};
  return {
    backend:config.backend,
    pixels:{width:pixels.width,height:pixels.height,data:Array.from(pixels.data)},
    probes,graph,passCount,format,sampleNs,fenceFloorNs,fenceMechanism,
    resolvedEffectIds:resolved.effectIds,searchOrder:resolved.searchOrder,
    adapter:{webgl,webgpu},
  };
};
window.__task7=run().then(value=>({ok:true,value}),error=>({ok:false,error:describeThrown(error)}));
</script>`
}

async function runBrowser(playwrightRoot, baseUrl, backend, testCase) {
    const require = createRequire(path.join(playwrightRoot, 'package.json'))
    const {chromium} = require('playwright')
    // Both lanes get the same ANGLE backend so the WebGL2 lane cannot quietly
    // land on a CPU rasterizer while the WebGPU lane runs on the GPU.
    const angle = process.platform === 'darwin' ? '--use-angle=metal' : '--use-angle=vulkan'
    const launchArgs = backend === 'webgpu'
        ? ['--enable-unsafe-webgpu', '--enable-features=Vulkan', angle]
        : [angle]
    const browser = await chromium.launch({headless: true, args: launchArgs})
    try {
        const page = await browser.newPage({viewport: {width: testCase.width, height: testCase.height}})
        const consoleErrors = []
        page.on('console', message => {if (message.type() === 'error') consoleErrors.push(message.text())})
        page.on('pageerror', error => consoleErrors.push(error.message))
        page.on('response', response => {
            if (response.status() >= 400) consoleErrors.push(`HTTP ${response.status()} ${response.url()}`)
        })
        page.on('requestfailed', request => consoleErrors.push(`REQUEST ${request.failure()?.errorText || 'failed'} ${request.url()}`))
        await page.goto(`${baseUrl}/shaders/effects/manifest.json`, {waitUntil: 'load'})
        await page.setContent(browserProgram(baseUrl, {
            backend, source: testCase.source, width: testCase.width, height: testCase.height,
            options: testCase.options, planEffectIds: testCase.plan.effectIds,
            probeWidth: PROBE_WIDTH, probeHeight: PROBE_HEIGHT,
        }), {waitUntil: 'load'})
        // The page always resolves with a discriminated envelope, so a browser
        // failure arrives with its real message, code and diagnostics instead
        // of crossing page.evaluate as the string "Object".
        const envelope = await page.evaluate(() => window.__task7)
        if (!envelope?.ok) {
            throw new BenchmarkError(envelope?.error?.code || 'ERR_BROWSER', envelope?.error?.message || 'browser program failed', {
                stack: envelope?.error?.stack ?? null,
                diagnostics: envelope?.error?.diagnostics ?? null,
                value: envelope?.error?.value ?? null,
                consoleErrors,
            })
        }
        if (consoleErrors.length) {
            throw new BenchmarkError('ERR_BROWSER_CONSOLE', `browser console errors: ${consoleErrors.join(' | ')}`, {consoleErrors})
        }
        const browserVersion = browser.version()
        await page.close()
        return {result: envelope.value, browserVersion, launchArgs}
    } finally {
        await browser.close()
    }
}

function medianOf(values) {
    const sorted = [...values].sort((a, b) => a - b)
    return sorted.length % 2 === 0
        ? Math.round((sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2)
        : sorted[Math.floor(sorted.length / 2)]
}

async function authenticateReadbackOrientation(probes) {
    if (!Array.isArray(probes) || probes.length === 0) {
        throw new BenchmarkError('ERR_ORIENTATION', 'the browser returned no orientation probe')
    }
    const results = []
    for (const probe of probes) {
        const authenticated = await authenticateProbeOrientation(
            probe.width, probe.height, Uint8Array.from(probe.data))
        results.push({format: probe.format, ...authenticated})
    }
    const unauthenticated = results.filter(entry => entry.orientation === null)
    if (unauthenticated.length) {
        throw new BenchmarkError('ERR_ORIENTATION_UNAUTHENTICATED',
            'the render-path orientation probe matched neither the top-down contract nor its vertical flip',
            {probes: unauthenticated.map(entry => ({format: entry.format, comparison: entry.comparison, flippedComparison: entry.flippedComparison}))})
    }
    const orientations = [...new Set(results.map(entry => entry.orientation))]
    if (orientations.length !== 1) {
        throw new BenchmarkError('ERR_ORIENTATION_INCONSISTENT',
            'render-target formats disagree on readback orientation',
            {probes: results.map(entry => ({format: entry.format, orientation: entry.orientation}))})
    }
    return {orientation: orientations[0], normalized: results[0].normalized, probes: results}
}

async function execute(values) {
    const backend = requireArgument(values, '--backend')
    if (!['webgl2', 'webgpu'].includes(backend)) throw new BenchmarkError('ERR_ARGUMENTS', '--backend must be webgl2 or webgpu')
    const allowSoftware = values.get('--allow-software') === true
    // One authority path: the same deep CPU authentication the CPU lane uses,
    // ledger and behavioral digest included.
    const cpuRootArgument = requireArgument(values, '--cpu-root')
    const ledgerArgument = values.get('--authority-ledger') || null
    let cpuRoot
    let ledger
    try {
        cpuRoot = authenticateCpuAuthority(cpuRootArgument, ledgerArgument)
        ledger = resolveAuthorityLedger(cpuRoot, ledgerArgument)
    } catch (error) {
        throw new BenchmarkError('ERR_CPU_AUTHORITY', error.message, {ledgerEnvironmentVariable: AUTHORITY_LEDGER_ENV})
    }
    const shaderGit = authenticateShaderGit(requireArgument(values, '--shader-git'))
    const playwright = resolvePinnedPlaywrightRoot(requireArgument(values, '--playwright-root'))
    const treeAuthority = authenticateTreeDocuments()
    const testCase = normalizeCase(readJsonFile(requireArgument(values, '--case'), 'case file').value, treeAuthority)
    const expected = normalizeExpectation(readJsonFile(requireArgument(values, '--expected'), 'expected file').value, testCase)
    const archived = archivePinnedShader(shaderGit)
    let server
    try {
        await authenticateArchivedSource(cpuRoot, archived.root)
        server = await serveDirectory(archived.root)
        const {result, browserVersion, launchArgs} = await runBrowser(playwright.root, server.url, backend, testCase)

        const adapter = {...result.adapter, ...classifyAdapter(result.adapter), allowSoftware}
        if (adapter.software && !allowSoftware) {
            throw new BenchmarkError('ERR_SOFTWARE_RASTERIZER',
                'this lane landed on a software rasterizer; rerun with --allow-software to record it as such',
                {adapter, launchArgs})
        }

        const readback = await authenticateReadbackOrientation(result.probes)
        const rawPixels = Uint8Array.from(result.pixels.data)
        const oriented = readback.normalized
            ? reverseRows(result.pixels.width, result.pixels.height, rawPixels)
            : rawPixels
        const actual = {width: result.pixels.width, height: result.pixels.height, data: oriented}

        const comparison = await compareExactRgba8(expected, actual)
        const graph = relateGraph(testCase, result.resolvedEffectIds, result.graph)
        const fenceFloorNs = medianOf(result.fenceFloorNs)
        const summary = summarizeSamples(
            result.sampleNs, {width: testCase.width, height: testCase.height}, fenceFloorNs)
        summary.passCount = result.passCount
        const correctnessStatus =
            comparison.status === 'failed' || graph.status === 'mismatch' || graph.status === 'projection_unavailable'
                ? 'failed' : 'pass'
        const benchmark = {
            schema: BENCHMARK_SCHEMA,
            program: {
                id: testCase.id, sourceSha256: testCase.sourceSha256,
                planSha256: testCase.plan.cpuPlanSha256, width: testCase.width, height: testCase.height,
                options: testCase.options,
            },
            provenance: {
                cpuBehavioralLock: testCase.provenance.cpuBehavioralLock,
                cpuSourceLockSha256: CPU_AUTHORITY.sourceLockSha256,
                upstreamSourceDigest: CPU_AUTHORITY.upstreamSourceDigest,
                upstreamRevision: UPSTREAM_REVISION, upstreamTree: UPSTREAM_TREE,
                catalogPayloadSha256: testCase.provenance.catalogPayloadSha256,
                compatibilitySha256: testCase.provenance.compatibilitySha256,
                cpuAuthorityLedgerSource: ledger.source,
                expectation: {...expected.identity, uniform: expected.uniform},
            },
            platform: {
                driver: backend, os: process.platform, arch: process.arch, runtime: process.version,
                compiler: backend === 'webgpu' ? 'WGSL' : 'GLSL', flags: launchArgs, browser: browserVersion,
                playwright: PLAYWRIGHT_VERSION,
                gpu: `${backend}; renderer=${adapter.webgl?.renderer ?? 'unknown'}; requested=${result.format.requested}; actual=${result.format.actual}`,
                adapter,
                readback: {
                    contract: ORIENTATION_CONTRACT,
                    authentication: ORIENTATION_AUTHENTICATION,
                    orientation: readback.orientation,
                    normalized: readback.normalized,
                    probedFormats: readback.probes.map(entry => entry.format),
                    measuredFormat: result.format.requested,
                    probeDimensions: {width: PROBE_WIDTH, height: PROBE_HEIGHT},
                    probeExpectedSha256: readback.probes[0].expectedSha256,
                },
            },
            mode: BENCHMARK_MODE, warmups: BENCHMARK_WARMUPS, samples: BENCHMARK_SAMPLES,
            sampleNs: result.sampleNs,
            timing: {
                fence: {
                    mechanism: result.fenceMechanism,
                    floorNs: fenceFloorNs,
                    floorSamplesNs: result.fenceFloorNs,
                    calibrationSamples: result.fenceFloorNs.length,
                    usesSetTimeout: false,
                },
            },
            summary,
            output: {
                width: actual.width, height: actual.height,
                rgba8Sha256: sha256(actual.data), rawRgba8Sha256: sha256(rawPixels),
            },
            correctness: {
                status: correctnessStatus,
                comparisonId: `${testCase.id}:${expected.sha256}`,
                comparison: {
                    status: comparison.status, reason: comparison.reason,
                    mismatchCount: comparison.mismatchCount, maxDelta: comparison.maxDelta,
                    firstMismatch: comparison.firstMismatch,
                    expectedSha256: comparison.expectedSha256, actualSha256: comparison.actualSha256,
                },
                graph: {
                    status: graph.status, reason: graph.reason,
                    // The operands travel inside the validated record, so an
                    // archived benchmark document names which effects resolved
                    // and which passes ran rather than only the verdict.
                    sourceEffectIds: result.resolvedEffectIds,
                    cpuPlan: {
                        effectIds: testCase.plan.effectIds,
                        passKeys: testCase.plan.passKeys,
                        finalSurface: testCase.plan.finalSurface,
                        cpuPlanSha256: testCase.plan.cpuPlanSha256,
                    },
                    actual: {
                        effectIds: result.graph.effectIds,
                        passKeys: result.graph.passKeys,
                        finalSurface: result.graph.finalSurface,
                        infrastructurePasses: result.graph.infrastructurePasses ?? [],
                    },
                },
            },
        }
        validateBenchmarkResult(benchmark)
        return {
            benchmark, comparison, graph, readback,
            capture: {rgba8Base64: Buffer.from(actual.data).toString('base64')},
        }
    } finally {
        if (server) await server.close()
        fs.rmSync(archived.scratch, {recursive: true})
    }
}

async function main() {
    // One authority path: the upstream pin this lane renders against and the
    // pin the CPU authority authenticates must agree. Checked here rather than
    // at module load so the refusal is reported as the same structured error
    // document as every other failure.
    assertUpstreamPinAgreement(CPU_AUTHORITY.upstreamRevision)
    const values = parseArguments(process.argv.slice(2))
    if (values.get('--describe')) {
        if (values.size !== 1) throw new BenchmarkError('ERR_ARGUMENTS', '--describe accepts no other arguments')
        process.stdout.write(`${JSON.stringify(describeContract())}\n`)
        return
    }
    if (values.has('--probe-playwright')) {
        if (values.size !== 1) throw new BenchmarkError('ERR_ARGUMENTS', '--probe-playwright accepts no other arguments')
        const result = resolvePinnedPlaywrightRoot(values.get('--probe-playwright'))
        process.stdout.write(`${JSON.stringify(result)}\n`)
        return
    }
    process.stdout.write(`${JSON.stringify(await execute(values))}\n`)
}

main().catch(error => {
    const document = error instanceof BenchmarkError
        ? error.toDocument()
        : {schema: 'noisemaker-cpp.benchmark-error.v1', code: 'ERR_DRIVER', message: error?.message || String(error), detail: {stack: error?.stack ?? null}}
    process.stderr.write(`${JSON.stringify(document)}\n`)
    process.exitCode = 1
})
