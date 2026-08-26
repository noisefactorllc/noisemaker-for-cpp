"""Contract tests for the pinned upstream shader benchmark driver."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "tools/dsl/shader_benchmark_lib.mjs"
DRIVER = ROOT / "tools/dsl/js_shader_benchmark.mjs"
CPU_RUNNER = ROOT / "tools/benchmark/run_cpu_case.mjs"
CORPUS = ROOT / "tests/fixtures/dsl/executable-corpus.json"
AUTHORITY = ROOT / "tools/dsl/corpus_authority.mjs"
CATALOG_PROVENANCE = ROOT / "src/effects/generated/effect_catalog.provenance.json"
COMPATIBILITY = ROOT / "src/effects/generated/backend_compatibility.json"

# Scratch comes from the platform temp convention, honouring the same TMPDIR
# override the driver itself validates. A literal macOS scratch root is not
# portable: on Linux `TemporaryDirectory(dir=...)` on a path that does not
# exist raises FileNotFoundError, so these tests would error rather than run.
# It is resolved because the driver refuses a non-canonical path.
SCRATCH_PARENT = os.path.realpath(tempfile.gettempdir())

# Every path this lane needs comes from the environment. Nothing here may name
# an operator home directory or a session scratch directory: those constants
# make a checked-in file unusable on any other machine.
CPU_ROOT_ENV = "NOISEMAKER_CPU_ROOT"
SHADER_GIT_ENV = "NOISEMAKER_SHADER_GIT"
PLAYWRIGHT_ENV = "NOISEMAKER_PLAYWRIGHT_ROOT"

LANE_FILES = (
    "tools/dsl/js_shader_benchmark.mjs",
    "tools/dsl/shader_benchmark_lib.mjs",
    "tools/dsl/corpus_authority.mjs",
    "tools/benchmark/run_cpu_case.mjs",
    "tools/benchmark/exact_compare.py",
    "tests/test_benchmark_shader.py",
    "tests/test_benchmark_cpu_corpus.py",
)

VALID_RECORD = """{
  schema: 'noisemaker-cpp.benchmark-result.v2',
  program: {id:'synth/solid+filter/blur#default',sourceSha256:'a'.repeat(64),planSha256:'b'.repeat(64),width:17,height:11,options:{time:0.25,frame:0,seed:17,oneShot:'ready',renderScale:1}},
  provenance: {
    cpuBehavioralLock:'c'.repeat(64),cpuSourceLockSha256:'d'.repeat(64),upstreamSourceDigest:'e'.repeat(64),
    upstreamRevision:'117a236679d1db3ab8f0e278230ece277b57564c',upstreamTree:'a7a997dfdc807697adba008729dcdfdfcfbaf53c',
    catalogPayloadSha256:'1'.repeat(64),compatibilitySha256:'2'.repeat(64),
    expectation:{schema:'noisemaker-cpp.dsl-cpu-expectation.v1',id:'synth/solid+filter/blur#default',rgba8Sha256:'3'.repeat(64),runnerSha256:'4'.repeat(64),cpuBehavioralLock:'c'.repeat(64)}
  },
  platform: {
    driver:'webgl2',os:'darwin',arch:'arm64',runtime:'browser',compiler:'GLSL',flags:['--use-angle=metal'],
    browser:'Chromium',playwright:'1.62.1',gpu:'webgl2; renderer=ANGLE (Apple, ANGLE Metal Renderer: Apple M2)',
    adapter:{webgl:{renderer:'ANGLE (Apple, ANGLE Metal Renderer: Apple M2)',vendor:'Google Inc. (Apple)'},webgpu:null,software:false,allowSoftware:false},
    readback:{contract:'top_down',authentication:'render_path_probe_per_backend_per_format',orientation:'top_down',normalized:false,probedFormats:['rgba16f','rgba8unorm'],measuredFormat:'rgba16f'}
  },
  mode:'fenced_frame',warmups:5,samples:30,sampleNs:Array(30).fill(1),
  timing:{fence:{mechanism:'webgl2_fence_sync_message_channel_poll',floorNs:1000,calibrationSamples:30,usesSetTimeout:false}},
  summary:{medianNs:100000,p95Ns:100000,pixels:187,fenceFloorNs:1000,megapixelsPerSecond:1.87,throughputSuppressedReason:null,passCount:3,
    measured:{resolution:{width:17,height:11,pixels:187},basis:'fenced_frame_wall_clock_including_fence_overhead',
      timingResolutionNs:1000,megapixelsPerSecond:1.87,nanosecondsPerPixel:534.7593582887701,comparableAcrossBackends:false}},
  output:{width:17,height:11,rgba8Sha256:'5'.repeat(64),rawRgba8Sha256:'5'.repeat(64)},
  correctness:{status:'pass',comparisonId:'fixture',graph:{
    status:'exact',reason:null,
    sourceEffectIds:['synth/solid','filter/blur'],
    cpuPlan:{effectIds:['synth/solid','filter/blur'],passKeys:['synth/solid:solid','filter/blur:blurH','filter/blur:blurV'],finalSurface:'o0',cpuPlanSha256:'b'.repeat(64)},
    actual:{effectIds:['synth/solid','filter/blur'],passKeys:['synth/solid:solid','filter/blur:blurH','filter/blur:blurV'],finalSurface:'o0',infrastructurePasses:['node_2_write_blit']}
  }}
}"""


# The retained 17x11 Solid->Blur case, the lane's oldest end-to-end evidence.
# The corpus generator emits one record per effect and never a two-effect
# chain, so this case cannot come from executable-corpus.json; until now it
# lived only as a hand-maintained scratch file, which is how its provenance
# went stale and how its missing options.width/height came to be patched in by
# hand without disclosure. It is defined here instead, stamped from the tree's
# own generated documents so it cannot go stale, and self-consistent by
# construction: options.width/height MUST equal the case dimensions, or the CPU
# runner renders its 512x512 default and the driver refuses the expectation.
RETAINED_BLUR_ID = "synth/solid+filter/blur#default"
RETAINED_BLUR_SOURCE = "search synth, filter\nsolid().blur(radiusX: 3, radiusY: 2).write(o0)\nrender(o0)\n"
RETAINED_BLUR_RGBA8_SHA256 = "5462562a69fbf2751af9aecf9b8e423104c866b5465e8a4402ae00214eac928a"
RETAINED_BLUR_WIDTH = 17
RETAINED_BLUR_HEIGHT = 11


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


def retained_blur_case() -> dict:
    """Build the retained Solid->Blur case from the tree it will run against."""
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    plan = {
        "effectIds": ["synth/solid", "filter/blur"],
        "passKeys": ["synth/solid:solid", "filter/blur:blurH", "filter/blur:blurV"],
        "routes": ["o0"],
        "finalSurface": "o0",
        "dimensions": {"width": RETAINED_BLUR_WIDTH, "height": RETAINED_BLUR_HEIGHT},
    }
    # The plan hash digests the very projection it stamps, so a hand-edited
    # projection cannot keep an inherited hash.
    plan = {"cpuPlanSha256": canonical_sha256(plan), **plan}
    return {
        "schema": "noisemaker-cpp.dsl-executable-corpus.v1",
        "recordKind": "admitted",
        "id": RETAINED_BLUR_ID,
        "source": RETAINED_BLUR_SOURCE,
        "sourceSha256": hashlib.sha256(RETAINED_BLUR_SOURCE.encode("utf-8")).hexdigest(),
        "width": RETAINED_BLUR_WIDTH,
        "height": RETAINED_BLUR_HEIGHT,
        "options": {
            "width": RETAINED_BLUR_WIDTH,
            "height": RETAINED_BLUR_HEIGHT,
            "time": 0.25,
            "frame": 0,
            "seed": 17,
            "oneShot": "ready",
            "renderScale": 1,
        },
        "search": ["synth", "filter"],
        "plan": plan,
        # The authenticated provenance of the tree this case runs against,
        # taken from the generated corpus rather than transcribed.
        "provenance": dict(corpus["records"][0]["provenance"]),
    }


def run_node(source: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", "--input-type=module", "-e", source, *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def required_directory(variable: str) -> pathlib.Path | None:
    value = os.environ.get(variable)
    if not value:
        return None
    path = pathlib.Path(value)
    return path if path.is_dir() else None


class ShaderBenchmarkContractTest(unittest.TestCase):
    def test_exact_comparer_reports_bounded_coordinate_channel_diagnostics(self) -> None:
        script = f"""
import {{compareExactRgba8}} from {json.dumps(LIBRARY.as_uri())};
const expected = Uint8Array.from([0, 1, 2, 3, 4, 5, 6, 7]);
const actual = Uint8Array.from([0, 9, 2, 3, 4, 5, 0, 7]);
console.log(JSON.stringify(await compareExactRgba8(
  {{width: 2, height: 1, data: expected}},
  {{width: 2, height: 1, data: actual}}
)));
"""
        result = run_node(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        comparison = json.loads(result.stdout)
        self.assertEqual(comparison["status"], "failed")
        self.assertEqual(comparison["mismatchCount"], 2)
        self.assertEqual(comparison["maxDelta"], 8)
        self.assertEqual(
            comparison["firstMismatch"],
            {"x": 0, "y": 0, "channel": 1, "channelName": "g", "expected": 1, "actual": 9},
        )
        self.assertEqual(len(comparison["expectedSha256"]), 64)
        self.assertEqual(len(comparison["actualSha256"]), 64)
        self.assertNotEqual(comparison["expectedSha256"], comparison["actualSha256"])

    def test_exact_comparer_rejects_dimensions_and_lengths_before_bytes(self) -> None:
        script = f"""
import {{compareExactRgba8}} from {json.dumps(LIBRARY.as_uri())};
const dimension = await compareExactRgba8(
  {{width: 1, height: 2, data: Uint8Array.from([0,0,0,0,0,0,0,0])}},
  {{width: 2, height: 1, data: Uint8Array.from([0,0,0,0,0,0,0,0])}}
);
const length = await compareExactRgba8(
  {{width: 2, height: 1, data: Uint8Array.from([0,0,0,0,0,0,0,0])}},
  {{width: 2, height: 1, data: Uint8Array.from([0,0,0,0])}}
);
console.log(JSON.stringify({{dimension, length}}));
"""
        result = run_node(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        comparisons = json.loads(result.stdout)
        self.assertEqual(comparisons["dimension"]["reason"], "dimension_mismatch")
        self.assertIsNone(comparisons["dimension"]["firstMismatch"])
        self.assertEqual(comparisons["length"]["reason"], "length_mismatch")
        self.assertIsNone(comparisons["length"]["firstMismatch"])

    def test_orientation_probe_expectation_is_vertically_asymmetric_and_catches_a_flip(self) -> None:
        # The probe pattern must distinguish an image from its own vertical
        # flip; the previous 2x2 round-trip probe could not, which is how a
        # flipped WebGPU readback passed while the driver said top_down.
        script = f"""
import {{orientationProbeExpectation, authenticateProbeOrientation, reverseRows}} from {json.dumps(LIBRARY.as_uri())};
const expectation = orientationProbeExpectation(13, 7);
const flipped = reverseRows(13, 7, expectation.data);
const garbage = Uint8Array.from(expectation.data.map((value, index) => index === 17 ? (value ^ 0x5a) : value));
const asymmetric = Buffer.compare(Buffer.from(expectation.data), Buffer.from(flipped)) !== 0;
console.log(JSON.stringify({{
  asymmetric,
  topDown: await authenticateProbeOrientation(13, 7, expectation.data),
  bottomUp: await authenticateProbeOrientation(13, 7, flipped),
  broken: await authenticateProbeOrientation(13, 7, garbage),
}}));
"""
        result = run_node(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertTrue(values["asymmetric"])
        self.assertEqual(values["topDown"]["orientation"], "top_down")
        self.assertFalse(values["topDown"]["normalized"])
        self.assertEqual(values["bottomUp"]["orientation"], "bottom_up")
        self.assertTrue(values["bottomUp"]["normalized"])
        self.assertIsNone(values["broken"]["orientation"])

    def test_benchmark_record_requires_fenced_mode_five_warmups_and_thirty_samples(self) -> None:
        script = f"""
import {{validateBenchmarkResult}} from {json.dumps(LIBRARY.as_uri())};
const base = {VALID_RECORD};
const ok = validateBenchmarkResult(base);
const reject = (mutate) => {{ try {{ validateBenchmarkResult(mutate(structuredClone(base))); return null; }} catch (error) {{ return error.message; }} }};
console.log(JSON.stringify({{
  ok,
  shortWarmup: reject(value => {{ value.warmups = 4; return value; }}),
  shortSamples: reject(value => {{ value.samples = 29; value.sampleNs = Array(29).fill(1); return value; }}),
  wrongMode: reject(value => {{ value.mode = 'render_only'; return value; }}),
  quantizedFence: reject(value => {{ value.timing.fence.usesSetTimeout = true; return value; }}),
  missingFence: reject(value => {{ delete value.timing; return value; }}),
  softwareRenderer: reject(value => {{ value.platform.adapter.software = true; return value; }}),
  missingAdapter: reject(value => {{ delete value.platform.adapter; return value; }}),
  unprobedFormat: reject(value => {{ value.platform.readback.measuredFormat = 'rgba32f'; return value; }}),
  unauthenticatedOrientation: reject(value => {{ value.platform.readback.orientation = 'assumed'; return value; }}),
  relabeledGraphMismatch: reject(value => {{ value.correctness.graph.status = 'mismatch'; value.correctness.graph.reason = 'graph_projection_mismatch'; return value; }}),
  reasonlessGraph: reject(value => {{ value.correctness.graph.status = 'cpu_plan_projection_contained'; value.correctness.graph.reason = null; return value; }}),
  operandlessGraph: reject(value => {{ delete value.correctness.graph.actual; return value; }}),
  unsourcedGraph: reject(value => {{ value.correctness.graph.sourceEffectIds = []; return value; }}),
  planlessGraph: reject(value => {{ delete value.correctness.graph.cpuPlan; return value; }}),
  comparableThroughput: reject(value => {{ value.summary.measured.comparableAcrossBackends = true; return value; }}),
  unlabeledThroughput: reject(value => {{ delete value.summary.measured; return value; }}),
  wrongThroughputResolution: reject(value => {{ value.summary.measured.resolution = {{width:512,height:512,pixels:262144}}; return value; }}),
  freeFloatingExpectation: reject(value => {{ delete value.provenance.expectation; return value; }}),
  legacyStatus: reject(value => {{ value.correctness.status = 'same-dsl-bytes'; return value; }}),
}}));
"""
        result = run_node(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertTrue(values["ok"])
        self.assertIn("warmups", values["shortWarmup"])
        self.assertIn("samples", values["shortSamples"])
        self.assertIn("fenced_frame", values["wrongMode"])
        self.assertIn("setTimeout", values["quantizedFence"])
        self.assertIn("timing", values["missingFence"])
        self.assertIn("--allow-software", values["softwareRenderer"])
        self.assertIn("platform.adapter", values["missingAdapter"])
        self.assertIn("measuredFormat", values["unprobedFormat"])
        self.assertIn("orientation", values["unauthenticatedOrientation"])
        self.assertIn("cannot be reported as a pass", values["relabeledGraphMismatch"])
        self.assertIn("reason", values["reasonlessGraph"])
        self.assertIn("correctness.graph.actual", values["operandlessGraph"])
        self.assertIn("correctness.graph.sourceEffectIds", values["unsourcedGraph"])
        self.assertIn("correctness.graph.cpuPlan", values["planlessGraph"])
        self.assertIn("cross-backend comparability", values["comparableThroughput"])
        self.assertIn("summary.measured", values["unlabeledThroughput"])
        self.assertIn("resolution the program was rendered at", values["wrongThroughputResolution"])
        self.assertIn("expectation", values["freeFloatingExpectation"])
        self.assertIn("correctness.status", values["legacyStatus"])

    def test_throughput_is_suppressed_when_the_median_sits_inside_the_fence_floor(self) -> None:
        script = f"""
import {{summarizeSamples}} from {json.dumps(LIBRARY.as_uri())};
console.log(JSON.stringify({{
  dominated: summarizeSamples(Array(30).fill(600000), {{width: 17, height: 11}}, 500000),
  clear: summarizeSamples(Array(30).fill(6000000), {{width: 17, height: 11}}, 50000),
}}));
"""
        result = run_node(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertIsNone(values["dominated"]["megapixelsPerSecond"])
        self.assertEqual(values["dominated"]["throughputSuppressedReason"], "median_within_two_fence_floors")
        self.assertIsNotNone(values["clear"]["megapixelsPerSecond"])
        self.assertEqual(values["clear"]["fenceFloorNs"], 50000)

    def test_a_fence_dominated_lane_still_publishes_its_measurement_with_its_resolution(self) -> None:
        # The WebGL2 lane's median sits inside its own fence floor at corpus
        # dimensions, so it publishes no cross-backend throughput at all. What
        # it did measure is still published — labelled with the resolution and
        # the timing floor it was measured at, and refusing comparability —
        # rather than leaving one lane with a figure and the other with none.
        script = f"""
import {{summarizeSamples}} from {json.dumps(LIBRARY.as_uri())};
console.log(JSON.stringify(summarizeSamples(Array(30).fill(797500), {{width: 17, height: 11}}, 590000)));
"""
        result = run_node(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertIsNone(summary["megapixelsPerSecond"])
        self.assertEqual(summary["throughputSuppressedReason"], "median_within_two_fence_floors")
        measured = summary["measured"]
        self.assertEqual(measured["resolution"], {"width": 17, "height": 11, "pixels": 187})
        self.assertEqual(measured["basis"], "fenced_frame_wall_clock_including_fence_overhead")
        self.assertEqual(measured["timingResolutionNs"], 590000)
        self.assertAlmostEqual(measured["megapixelsPerSecond"], 187 * 1000 / 797500)
        self.assertAlmostEqual(measured["nanosecondsPerPixel"], 797500 / 187)
        self.assertFalse(measured["comparableAcrossBackends"])

    def test_an_expectation_rendered_with_other_options_is_refused_not_compared(self) -> None:
        # The false pass this closes: a case at time 99 / frame 1234 / seed 1
        # compared against an expectation rendered at 0.25 / 0 / 1548099368,
        # signed `correctness: pass`. Case identity does not bind the render.
        script = f"""
import {{relateRenderOptions, renderOptionSet}} from {json.dumps(LIBRARY.as_uri())};
const caseSet = renderOptionSet({{time: 99, frame: 1234, seed: 1}}, 17, 11);
const drifted = renderOptionSet({{width: 17, height: 11, time: 0.25, frame: 0, seed: 1548099368,
  oneShot: 'ready', renderScale: 1}}, 17, 11);
const same = renderOptionSet({{width: 17, height: 11, time: 99, frame: 1234, seed: 1}}, 17, 11);
const defaulted = renderOptionSet({{width: 17, height: 11, time: 99, frame: 1234, seed: 1,
  oneShot: 'ready', renderScale: 1}}, 17, 11);
const reject = (thunk) => {{ try {{ thunk(); return null; }} catch (error) {{ return {{code: error.code, message: error.message}}; }} }};
console.log(JSON.stringify({{
  drifted: relateRenderOptions(caseSet, drifted),
  bound: relateRenderOptions(caseSet, same),
  defaultsAreSymmetric: relateRenderOptions(same, defaulted),
  dimensionDrift: relateRenderOptions(caseSet, renderOptionSet({{time: 99, frame: 1234, seed: 1}}, 512, 512)),
  missingOptions: reject(() => renderOptionSet(null, 17, 11)),
  unknownOption: reject(() => renderOptionSet({{time: 99, warp: 3}}, 17, 11)),
}}));
"""
        result = run_node(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertEqual(values["drifted"]["status"], "disagreement")
        self.assertEqual(
            sorted(entry["option"] for entry in values["drifted"]["differing"]),
            ["frame", "seed", "time"],
        )
        self.assertEqual(values["bound"]["status"], "bound")
        self.assertEqual(values["bound"]["differing"], [])
        self.assertEqual(values["defaultsAreSymmetric"]["status"], "bound")
        self.assertEqual(
            sorted(entry["option"] for entry in values["dimensionDrift"]["differing"]),
            ["height", "width"],
        )
        self.assertEqual(values["missingOptions"]["code"], "ERR_EXPECTED_OPTIONS")
        self.assertEqual(values["unknownOption"]["code"], "ERR_EXPECTED_OPTIONS")
        self.assertIn("warp", values["unknownOption"]["message"])

    def test_pin_drift_is_a_structured_refusal_not_a_module_load_stack_trace(self) -> None:
        script = f"""
import {{assertUpstreamPinAgreement, BenchmarkError}} from {json.dumps(LIBRARY.as_uri())};
let document = null;
try {{ assertUpstreamPinAgreement('0'.repeat(40)); }}
catch (error) {{ document = error instanceof BenchmarkError ? error.toDocument() : {{raw: String(error)}}; }}
console.log(JSON.stringify({{
  agrees: assertUpstreamPinAgreement('117a236679d1db3ab8f0e278230ece277b57564c'),
  document,
}}));
"""
        result = run_node(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertTrue(values["agrees"])
        self.assertEqual(values["document"]["schema"], "noisemaker-cpp.benchmark-error.v1")
        self.assertEqual(values["document"]["code"], "ERR_PIN_DRIFT")
        self.assertEqual(values["document"]["detail"]["benchmark"], "117a236679d1db3ab8f0e278230ece277b57564c")

    def test_driver_describes_exact_pinned_platform_contract(self) -> None:
        result = subprocess.run(
            ["node", str(DRIVER), "--describe"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        description = json.loads(result.stdout)
        self.assertEqual(description["schema"], "noisemaker-cpp.benchmark-result.v2")
        self.assertEqual(description["upstreamRevision"], "117a236679d1db3ab8f0e278230ece277b57564c")
        self.assertEqual(description["upstreamTree"], "a7a997dfdc807697adba008729dcdfdfcfbaf53c")
        self.assertEqual(description["playwrightVersion"], "1.62.1")
        self.assertEqual(description["orientation"], {
            "contract": "top_down",
            "authentication": "render_path_probe_per_backend_per_format",
        })
        self.assertEqual(description["format"], "rgba8")
        self.assertEqual(description["comparison"], "exact_rgba8_all_channels")
        self.assertEqual(
            description["timing"],
            {"mode": "fenced_frame", "warmups": 5, "samples": 30, "fenceCalibrationSamples": 30},
        )

    def test_committed_lane_files_name_no_operator_or_session_absolute_path(self) -> None:
        # Patterns are assembled at runtime so this scanner does not match its
        # own source text. The bare temp roots are banned too: a hardcoded
        # macOS scratch root is not a session path, but it is not portable
        # either, and the portable form is the platform temp convention.
        banned = (
            "/" + "Users/", "/private/" + "tmp", "/" + "tmp/noisemaker-cpp",
            '"/' + 'tmp"', "'/" + "tmp'", "/" + "var/folders",
        )
        offenders = []
        for relative in LANE_FILES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for line_number, line in enumerate(text.splitlines(), start=1):
                if any(pattern in line for pattern in banned):
                    offenders.append(f"{relative}:{line_number}: {line.strip()}")
        self.assertEqual(offenders, [], "committed lane files must take their paths from flags or the environment")

    def test_retained_blur_case_is_self_consistent_with_the_tree_it_runs_against(self) -> None:
        record = retained_blur_case()
        self.assertEqual(
            record["sourceSha256"],
            hashlib.sha256(record["source"].encode("utf-8")).hexdigest(),
        )
        # The correction that had been made by hand and never disclosed: with
        # no options.width/height the CPU runner renders 512x512 and the driver
        # refuses the expectation on dimensions.
        self.assertEqual(record["options"]["width"], record["width"])
        self.assertEqual(record["options"]["height"], record["height"])
        self.assertEqual(record["plan"]["dimensions"], {"width": record["width"], "height": record["height"]})
        plan = {key: value for key, value in record["plan"].items() if key != "cpuPlanSha256"}
        self.assertEqual(record["plan"]["cpuPlanSha256"], canonical_sha256(plan))
        self.assertEqual(record["plan"]["effectIds"], ["synth/solid", "filter/blur"])
        provenance = record["provenance"]
        catalog = json.loads(CATALOG_PROVENANCE.read_text(encoding="utf-8"))
        self.assertEqual(provenance["catalogPayloadSha256"], catalog["generated_payload_sha256"])
        self.assertEqual(
            provenance["compatibilitySha256"],
            hashlib.sha256(COMPATIBILITY.read_bytes()).hexdigest(),
        )
        authority = run_node(
            f"import {{EXPECTED}} from {json.dumps(AUTHORITY.as_uri())};"
            " console.log(JSON.stringify(EXPECTED));"
        )
        self.assertEqual(authority.returncode, 0, authority.stderr)
        self.assertEqual(
            provenance["cpuBehavioralLock"],
            json.loads(authority.stdout)["behavioralLockSha256"],
        )

    def test_driver_rejects_the_unpinned_playwright_before_launch(self) -> None:
        # A synthesised unpinned installation keeps this probe machine
        # independent: it no longer depends on an operator home checkout.
        with tempfile.TemporaryDirectory(prefix="noisemaker-unpinned-playwright-", dir=SCRATCH_PARENT) as directory:
            package = pathlib.Path(directory) / "node_modules/playwright/package.json"
            package.parent.mkdir(parents=True)
            package.write_text(json.dumps({"name": "playwright", "version": "1.61.0"}), encoding="utf-8")
            result = subprocess.run(
                ["node", str(DRIVER), "--probe-playwright", directory],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Playwright version mismatch", result.stderr)
            self.assertNotIn("browser launched", result.stdout)

    def test_driver_refuses_a_case_whose_provenance_describes_another_tree(self) -> None:
        record = next(
            item for item in json.loads(CORPUS.read_text(encoding="utf-8"))["records"]
            if item["id"] == "synth/gradient#default"
        )
        record = json.loads(json.dumps(record))
        record["provenance"]["catalogPayloadSha256"] = "0" * 64
        with tempfile.TemporaryDirectory(prefix="noisemaker-stale-case-", dir=SCRATCH_PARENT) as directory:
            case = pathlib.Path(directory) / "case.json"
            case.write_text(json.dumps(record), encoding="utf-8")
            expected = pathlib.Path(directory) / "expected.json"
            expected.write_text(json.dumps({"schema": "noisemaker-cpp.dsl-cpu-expectation.v1"}), encoding="utf-8")
            cpu_root = required_directory(CPU_ROOT_ENV)
            shader_git = required_directory(SHADER_GIT_ENV)
            playwright = required_directory(PLAYWRIGHT_ENV)
            if not (cpu_root and shader_git and playwright):
                self.skipTest(f"{CPU_ROOT_ENV}, {SHADER_GIT_ENV} and {PLAYWRIGHT_ENV} must name real directories")
            result = subprocess.run(
                [
                    "node", str(DRIVER), "--backend", "webgl2",
                    "--cpu-root", str(cpu_root), "--shader-git", str(shader_git),
                    "--playwright-root", str(playwright),
                    "--case", str(case), "--expected", str(expected),
                ],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            error = json.loads(result.stderr.strip().splitlines()[-1])
            self.assertEqual(error["code"], "ERR_CASE_PROVENANCE")
            self.assertIn("catalog payload", error["message"])


class ShaderBenchmarkBrowserTest(unittest.TestCase):
    """End-to-end runs against a real browser on a vertically asymmetric case."""

    CASE_ID = "synth/gradient#default"

    def setUp(self) -> None:
        self.cpu_root = required_directory(CPU_ROOT_ENV)
        self.shader_git = required_directory(SHADER_GIT_ENV)
        self.playwright = required_directory(PLAYWRIGHT_ENV)
        if not (self.cpu_root and self.shader_git and self.playwright):
            self.skipTest(
                f"{CPU_ROOT_ENV}, {SHADER_GIT_ENV} and {PLAYWRIGHT_ENV} must name real directories "
                "for the end-to-end browser lane"
            )

    def drive(self, directory: pathlib.Path, backend: str, expected: str = "expected.json"
              ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "node", str(DRIVER), "--backend", backend,
                "--cpu-root", str(self.cpu_root), "--shader-git", str(self.shader_git),
                "--playwright-root", str(self.playwright),
                "--case", str(directory / "case.json"),
                "--expected", str(directory / expected),
            ],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )

    def run_backend(self, directory: pathlib.Path, backend: str) -> dict:
        result = self.drive(directory, backend)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def render_cpu_expectation(self, directory: pathlib.Path, record: dict) -> dict:
        (directory / "case.json").write_text(json.dumps(record), encoding="utf-8")
        cpu = subprocess.run(
            [
                "node", str(CPU_RUNNER), "--cpu-root", str(self.cpu_root),
                "--case", str(directory / "case.json"),
                "--rgba8-output", str(directory / "expected.rgba8"),
                "--metadata-output", str(directory / "expected.meta.json"),
                "--expectation-output", str(directory / "expected.json"),
            ],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(cpu.returncode, 0, cpu.stderr)
        return json.loads((directory / "expected.json").read_text(encoding="utf-8"))

    def test_both_backends_authenticate_their_readback_and_agree_on_the_image(self) -> None:
        record = next(
            item for item in json.loads(CORPUS.read_text(encoding="utf-8"))["records"]
            if item["id"] == self.CASE_ID
        )
        with tempfile.TemporaryDirectory(prefix="noisemaker-shader-e2e-", dir=SCRATCH_PARENT) as name:
            directory = pathlib.Path(name)
            expectation = self.render_cpu_expectation(directory, record)
            pixels = base64.b64decode(expectation["rgba8Base64"])
            rows = {pixels[row * 17 * 4:(row + 1) * 17 * 4] for row in range(11)}
            self.assertGreater(len(rows), 1, "the end-to-end case must be vertically asymmetric")

            outputs = {}
            for backend in ("webgl2", "webgpu"):
                document = self.run_backend(directory, backend)
                benchmark = document["benchmark"]
                adapter = benchmark["platform"]["adapter"]
                self.assertFalse(adapter["software"], f"{backend} landed on a software rasterizer: {adapter}")
                self.assertTrue(adapter["webgl"]["renderer"])
                readback = benchmark["platform"]["readback"]
                self.assertIn(readback["orientation"], ("top_down", "bottom_up"))
                self.assertEqual(readback["authentication"], "render_path_probe_per_backend_per_format")
                self.assertIn(readback["measuredFormat"], readback["probedFormats"])
                self.assertFalse(benchmark["timing"]["fence"]["usesSetTimeout"])
                self.assertGreaterEqual(benchmark["timing"]["fence"]["calibrationSamples"], 30)
                outputs[backend] = benchmark["output"]["rgba8Sha256"]
            # Orientation is authenticated per backend, so after normalisation
            # the two lanes must produce the same image bytes.
            self.assertEqual(outputs["webgl2"], outputs["webgpu"])

    def test_retained_blur_case_is_byte_exact_on_both_backends(self) -> None:
        # The lane's retained end-to-end evidence, run from its tracked
        # definition rather than from a hand-maintained scratch file. This is
        # also the only automated assertion that the driver can reproduce the
        # CPU authority's bytes exactly end to end.
        with tempfile.TemporaryDirectory(prefix="noisemaker-shader-blur-", dir=SCRATCH_PARENT) as name:
            directory = pathlib.Path(name)
            expectation = self.render_cpu_expectation(directory, retained_blur_case())
            self.assertEqual(expectation["rgba8Sha256"], RETAINED_BLUR_RGBA8_SHA256)
            for backend in ("webgl2", "webgpu"):
                benchmark = self.run_backend(directory, backend)["benchmark"]
                self.assertEqual(benchmark["correctness"]["status"], "pass", benchmark["correctness"])
                self.assertEqual(benchmark["correctness"]["comparison"]["mismatchCount"], 0)
                self.assertEqual(benchmark["output"]["rgba8Sha256"], RETAINED_BLUR_RGBA8_SHA256)
                graph = benchmark["correctness"]["graph"]
                self.assertEqual(graph["status"], "exact")
                # The operands travel with the verdict.
                self.assertEqual(graph["sourceEffectIds"], ["synth/solid", "filter/blur"])
                self.assertEqual(graph["actual"]["passKeys"], graph["cpuPlan"]["passKeys"])
                measured = benchmark["summary"]["measured"]
                self.assertEqual(measured["resolution"]["pixels"], 17 * 11)
                self.assertFalse(measured["comparableAcrossBackends"])

    def test_driver_refuses_an_expectation_rendered_with_other_options(self) -> None:
        # End to end, on the driver itself: the pair that used to be signed
        # `correctness: pass` now never reaches the comparer.
        record = next(
            item for item in json.loads(CORPUS.read_text(encoding="utf-8"))["records"]
            if item["id"] == "filter/invert#default"
        )
        with tempfile.TemporaryDirectory(prefix="noisemaker-shader-options-", dir=SCRATCH_PARENT) as name:
            directory = pathlib.Path(name)
            self.render_cpu_expectation(directory, record)
            drifted = json.loads(json.dumps(record))
            drifted["options"] = {**drifted["options"], "time": 99, "frame": 1234, "seed": 1}
            (directory / "case.json").write_text(json.dumps(drifted), encoding="utf-8")
            result = self.drive(directory, "webgl2")
            self.assertNotEqual(result.returncode, 0, result.stdout)
            error = json.loads(result.stderr.strip().splitlines()[-1])
            self.assertEqual(error["schema"], "noisemaker-cpp.benchmark-error.v1")
            self.assertEqual(error["code"], "ERR_EXPECTED_OPTIONS")
            self.assertEqual(
                sorted(entry["option"] for entry in error["detail"]["differing"]),
                ["frame", "seed", "time"],
            )


if __name__ == "__main__":
    unittest.main()
