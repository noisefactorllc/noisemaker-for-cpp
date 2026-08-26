import {createHash} from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'

export const UPSTREAM_REVISION = '117a236679d1db3ab8f0e278230ece277b57564c'
export const UPSTREAM_TREE = 'a7a997dfdc807697adba008729dcdfdfcfbaf53c'
export const PLAYWRIGHT_VERSION = '1.62.1'
export const BENCHMARK_SCHEMA = 'noisemaker-cpp.benchmark-result.v2'
export const BENCHMARK_ERROR_SCHEMA = 'noisemaker-cpp.benchmark-error.v1'
export const BENCHMARK_MODE = 'fenced_frame'
export const BENCHMARK_WARMUPS = 5
export const BENCHMARK_SAMPLES = 30
export const FENCE_CALIBRATION_SAMPLES = 30

// The contract the driver renders against: readback row 0 is the top row of
// the image as the authenticated CPU runner emits it. The contract is never
// assumed; it is authenticated per backend and per render-target format by a
// probe that runs through the same rasterizer path as the measurements
// (`ORIENTATION_AUTHENTICATION`).
export const ORIENTATION_CONTRACT = 'top_down'
export const ORIENTATION_AUTHENTICATION = 'render_path_probe_per_backend_per_format'
export const READBACK_ORIENTATIONS = ['top_down', 'bottom_up']

// A renderer string matching any of these is a CPU rasterizer, not a GPU.
const SOFTWARE_RENDERER_PATTERN =
    /swiftshader|llvmpipe|lavapipe|software\s*(rasterizer|renderer|adapter)?|microsoft basic render|generic renderer/i

const CHANNEL_NAMES = ['r', 'g', 'b', 'a']
const HEX_64 = /^[0-9a-f]{64}$/

// Every option that changes the rendered image, with the value the renderers
// apply when the case leaves it out. Both lanes read this one list, so an
// option can never be applied by one side and ignored by the other.
export const RENDER_OPTION_DEFAULTS = Object.freeze({
    time: 0, frame: 0, seed: 0, oneShot: 'ready', renderScale: 1,
})
export const RENDER_OPTION_KEYS = Object.freeze([
    ...Object.keys(RENDER_OPTION_DEFAULTS), 'width', 'height',
])

// A throughput figure measured at one resolution, on one fence mechanism, is
// a property of that pairing and of nothing else.
export const THROUGHPUT_BASIS = 'fenced_frame_wall_clock_including_fence_overhead'

export function sha256(data) {
    return createHash('sha256').update(data).digest('hex')
}

export class BenchmarkError extends Error {
    constructor(code, message, detail = null) {
        super(message)
        this.name = 'BenchmarkError'
        this.code = code
        this.detail = detail
    }

    toDocument() {
        return {
            schema: BENCHMARK_ERROR_SCHEMA,
            code: this.code,
            message: this.message,
            detail: this.detail,
        }
    }
}

/**
 * The upstream pin this lane renders against and the pin the CPU authority
 * authenticates must be one value. The disagreement is raised as a
 * `BenchmarkError` from inside the driver's `main()` rather than thrown at
 * module load, so it reaches the operator as the same structured
 * `noisemaker-cpp.benchmark-error.v1` document as every other refusal instead
 * of as a raw Node stack trace.
 */
export function assertUpstreamPinAgreement(cpuAuthorityRevision) {
    if (cpuAuthorityRevision !== UPSTREAM_REVISION) {
        throw new BenchmarkError('ERR_PIN_DRIFT',
            'shader benchmark and CPU authority disagree on the upstream revision',
            {benchmark: UPSTREAM_REVISION, cpuAuthority: cpuAuthorityRevision ?? null})
    }
    return true
}

/**
 * The full set of render-affecting options a document was produced with, with
 * this lane's defaults applied, so two documents are compared on the values
 * the renderer actually used rather than on which keys happen to be spelled
 * out.
 */
export function renderOptionSet(options, width, height) {
    if (!options || typeof options !== 'object' || Array.isArray(options)) {
        throw new BenchmarkError('ERR_EXPECTED_OPTIONS', 'render options must be an object')
    }
    const unknown = Object.keys(options).filter(key => !RENDER_OPTION_KEYS.includes(key))
    if (unknown.length) {
        throw new BenchmarkError('ERR_EXPECTED_OPTIONS',
            `render options name keys this lane does not apply: ${unknown.join(', ')}`, {options: unknown})
    }
    const applied = {width, height}
    for (const [key, fallback] of Object.entries(RENDER_OPTION_DEFAULTS)) {
        applied[key] = options[key] === undefined ? fallback : options[key]
    }
    return applied
}

/**
 * Relate two render-option sets. Case identity is not enough to bind an
 * expectation to a case: the same DSL source rendered at a different time,
 * frame or seed is a different image, so a disagreement here must refuse the
 * pair rather than let the comparer sign a verdict about two different
 * programs.
 */
export function relateRenderOptions(caseOptions, expectationOptions) {
    const differing = RENDER_OPTION_KEYS
        .filter(key => !Object.is(caseOptions[key], expectationOptions[key]))
        .map(key => ({option: key, case: caseOptions[key] ?? null, expectation: expectationOptions[key] ?? null}))
    return {
        status: differing.length === 0 ? 'bound' : 'disagreement',
        differing,
        case: caseOptions,
        expectation: expectationOptions,
    }
}

export function isSoftwareRenderer(description) {
    return typeof description === 'string' && SOFTWARE_RENDERER_PATTERN.test(description)
}

/**
 * Classify an adapter record. Every string the browser reports about the
 * renderer is examined, so a software fallback cannot hide in a field the
 * driver forgot to read.
 */
export function classifyAdapter(adapter) {
    const strings = []
    const collect = value => {
        if (typeof value === 'string') strings.push(value)
        else if (value && typeof value === 'object') for (const item of Object.values(value)) collect(item)
    }
    collect(adapter)
    const software = strings.some(isSoftwareRenderer) || adapter?.webgpu?.isFallbackAdapter === true
    return {software, evidence: strings.filter(isSoftwareRenderer)}
}

function checkedImage(image, label) {
    if (!image || !Number.isSafeInteger(image.width) || image.width <= 0 ||
        !Number.isSafeInteger(image.height) || image.height <= 0) {
        throw new Error(`${label} image must have positive safe integer dimensions`)
    }
    if (!(image.data instanceof Uint8Array)) {
        throw new Error(`${label} image data must be Uint8Array`)
    }
    return image
}

/** Reverse the row order of a top-down RGBA8 buffer. */
export function reverseRows(width, height, data) {
    if (!(data instanceof Uint8Array) || data.length !== width * height * 4) {
        throw new Error('reverseRows requires a complete RGBA8 buffer')
    }
    const rowBytes = width * 4
    const out = new Uint8Array(data.length)
    for (let y = 0; y < height; y++) {
        out.set(data.subarray((height - 1 - y) * rowBytes, (height - y) * rowBytes), y * rowBytes)
    }
    return out
}

export async function compareExactRgba8(expectedInput, actualInput) {
    const expected = checkedImage(expectedInput, 'expected')
    const actual = checkedImage(actualInput, 'actual')
    const expectedSha256 = sha256(expected.data)
    const actualSha256 = sha256(actual.data)
    const common = {
        expected: {width: expected.width, height: expected.height, length: expected.data.length},
        actual: {width: actual.width, height: actual.height, length: actual.data.length},
        expectedSha256,
        actualSha256,
    }
    if (expected.width !== actual.width || expected.height !== actual.height) {
        return {
            status: 'failed', reason: 'dimension_mismatch', ...common,
            firstMismatch: null, mismatchCount: null, maxDelta: null,
        }
    }
    const expectedLength = expected.width * expected.height * 4
    if (expected.data.length !== expectedLength || actual.data.length !== expectedLength) {
        return {
            status: 'failed', reason: 'length_mismatch', ...common,
            firstMismatch: null, mismatchCount: null, maxDelta: null,
        }
    }
    let firstMismatch = null
    let mismatchCount = 0
    let maxDelta = 0
    for (let index = 0; index < expectedLength; index++) {
        const expectedByte = expected.data[index]
        const actualByte = actual.data[index]
        if (expectedByte === actualByte) continue
        const delta = Math.abs(expectedByte - actualByte)
        mismatchCount++
        maxDelta = Math.max(maxDelta, delta)
        if (firstMismatch === null) {
            const pixel = Math.floor(index / 4)
            const channel = index % 4
            firstMismatch = {
                x: pixel % expected.width,
                y: Math.floor(pixel / expected.width),
                channel,
                channelName: CHANNEL_NAMES[channel],
                expected: expectedByte,
                actual: actualByte,
            }
        }
    }
    return {
        status: mismatchCount === 0 ? 'pass' : 'failed',
        reason: mismatchCount === 0 ? null : 'byte_mismatch',
        ...common,
        firstMismatch,
        mismatchCount,
        maxDelta,
    }
}

/**
 * Expected bytes of the render-path orientation probe, in the top-down
 * contract orientation. Row r (from the top) carries the fragment whose
 * shader-space row index is height-1-r, so the pattern is vertically
 * asymmetric by construction and a flipped readback cannot satisfy it.
 */
export function orientationProbeExpectation(width, height) {
    if (!Number.isSafeInteger(width) || width <= 0 || width > 254 ||
        !Number.isSafeInteger(height) || height <= 0 || height > 254) {
        throw new Error('orientation probe dimensions must be within 1..254')
    }
    const data = new Uint8Array(width * height * 4)
    for (let row = 0; row < height; row++) {
        const shaderRow = height - 1 - row
        for (let column = 0; column < width; column++) {
            const offset = (row * width + column) * 4
            data[offset] = shaderRow + 1
            data[offset + 1] = column + 1
            data[offset + 2] = height - shaderRow
            data[offset + 3] = 255
        }
    }
    return {width, height, data, sha256: sha256(data)}
}

/**
 * Authenticate one probe readback. Returns the orientation the backend
 * actually reads back in, never an assumption: exactly one of the two
 * orientations may match, and neither matching is a hard failure.
 */
export async function authenticateProbeOrientation(width, height, readback) {
    const expectation = orientationProbeExpectation(width, height)
    const actual = {width, height, data: readback}
    const topDown = await compareExactRgba8(expectation, actual)
    if (topDown.status === 'pass') {
        return {orientation: 'top_down', normalized: false, expectedSha256: expectation.sha256, comparison: topDown}
    }
    const flipped = {
        width, height,
        data: readback.length === width * height * 4 ? reverseRows(width, height, readback) : readback,
    }
    const bottomUp = await compareExactRgba8(expectation, flipped)
    if (bottomUp.status === 'pass') {
        return {orientation: 'bottom_up', normalized: true, expectedSha256: expectation.sha256, comparison: bottomUp}
    }
    return {
        orientation: null, normalized: null, expectedSha256: expectation.sha256,
        comparison: topDown, flippedComparison: bottomUp,
    }
}

function requiredObject(value, name) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
        throw new Error(`${name} must be an object`)
    }
    return value
}

function requiredString(value, name) {
    if (typeof value !== 'string' || value.length === 0) {
        throw new Error(`${name} must be a non-empty string`)
    }
    return value
}

function requiredSha(value, name) {
    if (typeof value !== 'string' || !HEX_64.test(value)) {
        throw new Error(`${name} must be a lowercase SHA-256`)
    }
}

function requiredStringArray(value, name, {allowEmpty = false} = {}) {
    if (!Array.isArray(value) || (!allowEmpty && value.length === 0) ||
        value.some(entry => typeof entry !== 'string' || entry.length === 0)) {
        throw new Error(`${name} must be an array of nonempty strings`)
    }
    return value
}

export function validateBenchmarkResult(input) {
    const value = requiredObject(input, 'benchmark result')
    if (value.schema !== BENCHMARK_SCHEMA) throw new Error(`schema must be ${BENCHMARK_SCHEMA}`)
    const program = requiredObject(value.program, 'program')
    requiredString(program.id, 'program.id')
    requiredSha(program.sourceSha256, 'program.sourceSha256')
    requiredSha(program.planSha256, 'program.planSha256')
    if (!Number.isSafeInteger(program.width) || program.width <= 0 ||
        !Number.isSafeInteger(program.height) || program.height <= 0) {
        throw new Error('program dimensions must be positive safe integers')
    }
    requiredObject(program.options, 'program.options')
    const provenance = requiredObject(value.provenance, 'provenance')
    for (const key of ['cpuBehavioralLock', 'cpuSourceLockSha256', 'upstreamSourceDigest',
        'catalogPayloadSha256', 'compatibilitySha256']) {
        requiredSha(provenance[key], `provenance.${key}`)
    }
    if (provenance.upstreamRevision !== UPSTREAM_REVISION) throw new Error('upstream revision mismatch')
    if (provenance.upstreamTree !== UPSTREAM_TREE) throw new Error('upstream tree mismatch')
    // The expected bytes are attributed to the authenticated CPU runner that
    // produced them; a free-floating expectation cannot reach this record.
    const expectation = requiredObject(provenance.expectation, 'provenance.expectation')
    requiredString(expectation.schema, 'provenance.expectation.schema')
    requiredString(expectation.id, 'provenance.expectation.id')
    for (const key of ['rgba8Sha256', 'runnerSha256', 'cpuBehavioralLock']) {
        requiredSha(expectation[key], `provenance.expectation.${key}`)
    }
    const platform = requiredObject(value.platform, 'platform')
    for (const key of ['driver', 'os', 'arch', 'runtime', 'compiler', 'browser', 'playwright', 'gpu']) {
        requiredString(platform[key], `platform.${key}`)
    }
    if (platform.playwright !== PLAYWRIGHT_VERSION) throw new Error('platform Playwright version mismatch')
    // Adapter identity is mandatory: two lanes on different renderers must
    // never be presentable as like-for-like.
    const adapter = requiredObject(platform.adapter, 'platform.adapter')
    const webgl = requiredObject(adapter.webgl, 'platform.adapter.webgl')
    requiredString(webgl.renderer, 'platform.adapter.webgl.renderer')
    requiredString(webgl.vendor, 'platform.adapter.webgl.vendor')
    if (platform.driver === 'webgpu') {
        const webgpu = requiredObject(adapter.webgpu, 'platform.adapter.webgpu')
        requiredString(webgpu.vendor, 'platform.adapter.webgpu.vendor')
        requiredString(webgpu.architecture, 'platform.adapter.webgpu.architecture')
    }
    if (typeof adapter.software !== 'boolean') throw new Error('platform.adapter.software must be a boolean')
    if (typeof adapter.allowSoftware !== 'boolean') throw new Error('platform.adapter.allowSoftware must be a boolean')
    if (adapter.software && !adapter.allowSoftware) {
        throw new Error('a software rasterizer result requires an explicit --allow-software run')
    }
    const readback = requiredObject(platform.readback, 'platform.readback')
    if (readback.contract !== ORIENTATION_CONTRACT) throw new Error('platform.readback.contract must be the top_down contract')
    if (readback.authentication !== ORIENTATION_AUTHENTICATION) {
        throw new Error('platform.readback.authentication must name the render-path probe')
    }
    if (!READBACK_ORIENTATIONS.includes(readback.orientation)) {
        throw new Error('platform.readback.orientation must be authenticated')
    }
    if (typeof readback.normalized !== 'boolean') throw new Error('platform.readback.normalized must be a boolean')
    if (!Array.isArray(readback.probedFormats) || readback.probedFormats.length === 0 ||
        readback.probedFormats.some(entry => typeof entry !== 'string' || entry.length === 0)) {
        throw new Error('platform.readback.probedFormats must name every probed render-target format')
    }
    if (!readback.probedFormats.includes(readback.measuredFormat)) {
        throw new Error('platform.readback.measuredFormat must itself have been probed')
    }
    if (value.mode !== BENCHMARK_MODE) throw new Error(`shader benchmark mode must be ${BENCHMARK_MODE}`)
    if (!Number.isSafeInteger(value.warmups) || value.warmups < BENCHMARK_WARMUPS) {
        throw new Error(`warmups must be at least ${BENCHMARK_WARMUPS}`)
    }
    if (!Number.isSafeInteger(value.samples) || value.samples < BENCHMARK_SAMPLES) {
        throw new Error(`samples must be at least ${BENCHMARK_SAMPLES}`)
    }
    if (!Array.isArray(value.sampleNs) || value.sampleNs.length !== value.samples ||
        value.sampleNs.some(sample => !Number.isSafeInteger(sample) || sample < 0)) {
        throw new Error('sampleNs must contain one nonnegative integer per sample')
    }
    // Timing resolution is part of the record, so a quantized lane is never
    // silently compared against an unquantized one.
    const timing = requiredObject(value.timing, 'timing')
    const fence = requiredObject(timing.fence, 'timing.fence')
    requiredString(fence.mechanism, 'timing.fence.mechanism')
    if (!Number.isSafeInteger(fence.floorNs) || fence.floorNs < 0) {
        throw new Error('timing.fence.floorNs must be a measured nonnegative integer')
    }
    if (!Number.isSafeInteger(fence.calibrationSamples) || fence.calibrationSamples < FENCE_CALIBRATION_SAMPLES) {
        throw new Error(`timing.fence.calibrationSamples must be at least ${FENCE_CALIBRATION_SAMPLES}`)
    }
    if (fence.usesSetTimeout !== false) throw new Error('timing.fence must not be setTimeout-quantized')
    const summary = requiredObject(value.summary, 'summary')
    if (!Number.isSafeInteger(summary.medianNs) || summary.medianNs < 0) throw new Error('summary.medianNs must be an integer')
    if (summary.megapixelsPerSecond !== null && !(typeof summary.megapixelsPerSecond === 'number')) {
        throw new Error('summary.megapixelsPerSecond must be a number or null when suppressed')
    }
    if (summary.megapixelsPerSecond === null && !summary.throughputSuppressedReason) {
        throw new Error('a suppressed throughput must state its reason')
    }
    // A lane whose median sits inside its own fence floor publishes no
    // cross-lane throughput, but it still measured something. What it measured
    // is published here, carrying the resolution and the timing floor it was
    // measured at and an explicit refusal to be read across backends, so the
    // asymmetry between the two lanes is disclosed instead of being an absence.
    const measured = requiredObject(summary.measured, 'summary.measured')
    const resolution = requiredObject(measured.resolution, 'summary.measured.resolution')
    if (resolution.width !== program.width || resolution.height !== program.height ||
        resolution.pixels !== program.width * program.height) {
        throw new Error('summary.measured.resolution must be the resolution the program was rendered at')
    }
    if (summary.pixels !== resolution.pixels) throw new Error('summary.pixels must be the measured pixel count')
    if (measured.basis !== THROUGHPUT_BASIS) throw new Error(`summary.measured.basis must be ${THROUGHPUT_BASIS}`)
    if (!Number.isSafeInteger(measured.timingResolutionNs) || measured.timingResolutionNs < 0) {
        throw new Error('summary.measured.timingResolutionNs must be the measured fence floor')
    }
    if (measured.megapixelsPerSecond !== null && typeof measured.megapixelsPerSecond !== 'number') {
        throw new Error('summary.measured.megapixelsPerSecond must be a number or null')
    }
    if (measured.comparableAcrossBackends !== false) {
        throw new Error('summary.measured must never claim cross-backend comparability')
    }
    const output = requiredObject(value.output, 'output')
    if (output.width !== program.width || output.height !== program.height) {
        throw new Error('output dimensions must match program dimensions')
    }
    requiredSha(output.rgba8Sha256, 'output.rgba8Sha256')
    requiredSha(output.rawRgba8Sha256, 'output.rawRgba8Sha256')
    const correctness = requiredObject(value.correctness, 'correctness')
    if (!['pass', 'failed'].includes(correctness.status)) {
        throw new Error('correctness.status must be pass or failed')
    }
    requiredString(correctness.comparisonId, 'correctness.comparisonId')
    const graph = requiredObject(correctness.graph, 'correctness.graph')
    if (!['exact', 'cpu_plan_projection_contained', 'projection_unavailable', 'mismatch'].includes(graph.status)) {
        throw new Error('correctness.graph.status is invalid')
    }
    if (graph.status !== 'exact' && !graph.reason) {
        throw new Error('a non-exact graph relation must carry its reason inside the record')
    }
    // The verdict travels with its operands. An archived benchmark document
    // names which effects the DSL source resolved to, which passes the shader
    // graph actually ran, and what the CPU plan projected — not just the word
    // the three of them were reduced to.
    requiredStringArray(graph.sourceEffectIds, 'correctness.graph.sourceEffectIds')
    const actualGraph = requiredObject(graph.actual, 'correctness.graph.actual')
    requiredStringArray(actualGraph.effectIds, 'correctness.graph.actual.effectIds')
    requiredStringArray(actualGraph.passKeys, 'correctness.graph.actual.passKeys')
    requiredString(actualGraph.finalSurface, 'correctness.graph.actual.finalSurface')
    requiredStringArray(actualGraph.infrastructurePasses, 'correctness.graph.actual.infrastructurePasses',
        {allowEmpty: true})
    const cpuPlan = requiredObject(graph.cpuPlan, 'correctness.graph.cpuPlan')
    requiredStringArray(cpuPlan.effectIds, 'correctness.graph.cpuPlan.effectIds')
    if (cpuPlan.passKeys !== null) requiredStringArray(cpuPlan.passKeys, 'correctness.graph.cpuPlan.passKeys')
    if (cpuPlan.finalSurface !== null) requiredString(cpuPlan.finalSurface, 'correctness.graph.cpuPlan.finalSurface')
    if (['projection_unavailable', 'mismatch'].includes(graph.status) && correctness.status !== 'failed') {
        throw new Error('an unproven graph relation cannot be reported as a pass')
    }
    return true
}

export function summarizeSamples(sampleNs, resolution, fenceFloorNs) {
    if (!Array.isArray(sampleNs) || sampleNs.length === 0 ||
        sampleNs.some(sample => !Number.isSafeInteger(sample) || sample < 0)) {
        throw new Error('sampleNs must be a nonempty array of nonnegative integers')
    }
    // The resolution is an operand, not a footnote: at 17x11 a fenced frame is
    // mostly fence, and the only honest way to publish that measurement is
    // next to the dimensions and the timing floor it was taken at.
    if (!resolution || typeof resolution !== 'object' ||
        !Number.isSafeInteger(resolution.width) || resolution.width <= 0 ||
        !Number.isSafeInteger(resolution.height) || resolution.height <= 0) {
        throw new Error('resolution must carry positive safe integer width and height')
    }
    const pixels = resolution.width * resolution.height
    if (!Number.isSafeInteger(fenceFloorNs) || fenceFloorNs < 0) throw new Error('fenceFloorNs must be a nonnegative integer')
    const sorted = [...sampleNs].sort((a, b) => a - b)
    const medianNs = sorted.length % 2 === 0
        ? Math.round((sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2)
        : sorted[Math.floor(sorted.length / 2)]
    const p95Ns = sorted[Math.max(0, Math.ceil(sorted.length * 0.95) - 1)]
    // A median that sits inside the fence mechanism's own floor measures the
    // fence, not the render, so no throughput figure is derived from it.
    const dominatedByFence = medianNs <= 2 * fenceFloorNs
    return {
        medianNs,
        p95Ns,
        pixels,
        fenceFloorNs,
        medianAboveFenceFloorNs: Math.max(0, medianNs - fenceFloorNs),
        megapixelsPerSecond: dominatedByFence || medianNs === 0 ? null : pixels * 1000 / medianNs,
        throughputSuppressedReason: dominatedByFence
            ? 'median_within_two_fence_floors'
            : (medianNs === 0 ? 'median_is_zero' : null),
        // Published on every record, suppressed or not. It is the wall clock
        // this lane really measured, fence overhead included, expressed per
        // pixel at the one resolution it was measured at. It is not a backend
        // comparison and says so; the suppressed `megapixelsPerSecond` above
        // remains the only figure that would have been one.
        measured: {
            resolution: {width: resolution.width, height: resolution.height, pixels},
            basis: THROUGHPUT_BASIS,
            timingResolutionNs: fenceFloorNs,
            megapixelsPerSecond: medianNs === 0 ? null : pixels * 1000 / medianNs,
            nanosecondsPerPixel: medianNs === 0 ? null : medianNs / pixels,
            comparableAcrossBackends: false,
        },
    }
}

export function resolvePinnedPlaywrightRoot(rootInput) {
    const root = fs.realpathSync(rootInput)
    if (root !== path.resolve(rootInput)) throw new Error('Playwright root must be a real, non-symlinked path')
    const packagePath = path.join(root, 'node_modules', 'playwright', 'package.json')
    const packageReal = fs.realpathSync(packagePath)
    if (packageReal !== packagePath) throw new Error('Playwright package path must not be symlinked')
    const document = JSON.parse(fs.readFileSync(packageReal, 'utf8'))
    if (document.version !== PLAYWRIGHT_VERSION) {
        throw new Error(`Playwright version mismatch: expected ${PLAYWRIGHT_VERSION}, got ${document.version ?? 'missing'}`)
    }
    return {root, packagePath: packageReal, version: document.version}
}

export function describeContract() {
    return {
        schema: BENCHMARK_SCHEMA,
        upstreamRevision: UPSTREAM_REVISION,
        upstreamTree: UPSTREAM_TREE,
        playwrightVersion: PLAYWRIGHT_VERSION,
        orientation: {contract: ORIENTATION_CONTRACT, authentication: ORIENTATION_AUTHENTICATION},
        format: 'rgba8',
        comparison: 'exact_rgba8_all_channels',
        timing: {
            mode: BENCHMARK_MODE,
            warmups: BENCHMARK_WARMUPS,
            samples: BENCHMARK_SAMPLES,
            fenceCalibrationSamples: FENCE_CALIBRATION_SAMPLES,
        },
        throughput: {
            basis: THROUGHPUT_BASIS,
            crossBackendFigure: 'suppressed while the median sits within two measured fence floors',
            publishedWith: ['resolution', 'timingResolutionNs'],
            comparableAcrossBackends: false,
        },
        renderOptions: RENDER_OPTION_KEYS,
        adapter: {recorded: true, softwareRasterizer: 'refused unless --allow-software'},
    }
}
