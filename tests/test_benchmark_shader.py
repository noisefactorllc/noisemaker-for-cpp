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
    "tools/dsl/generate_executable_corpus.mjs",
    "tools/dsl/js_render_oracle.mjs",
    "tools/benchmark/run_cpu_case.mjs",
    "tools/benchmark/exact_compare.py",
    "tools/benchmark/corpus_lane.py",
    "tools/benchmark/two_pass_corpus.py",
    "tools/benchmark/run_cpp_benchmark.cpp",
    "tools/benchmark/run_cpp_case.cpp",
    "tools/benchmark/corpus_case.cpp",
    "tools/benchmark/corpus_case.hpp",
    "tests/test_benchmark_shader.py",
    "tests/test_benchmark_cpu_corpus.py",
    "tests/test_benchmark_cpu_exact.py",
    "tests/test_dsl_corpus_parity.py",
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


# ---------------------------------------------------------------------------
# The step-9 expansion protocol.
#
# The expansion runs the whole admitted corpus on both backends and records one
# manifest. The manifest itself lives outside the repository — it names an
# adapter, a browser build and a machine, and none of those are properties of
# this tree. What IS a property of this tree is the shape the manifest must
# have and the claims a summary derived from it is allowed to make, so that is
# what is pinned here: the schema, the per-lane statuses, the evidence a
# mismatch must carry, the refusal form, and the splits and ledger that must
# accompany any "N exact" claim.
#
# Nothing below pins a count, an adapter string, a timing figure or an
# intersection size. An adapter-dependent result must never become a frozen
# expectation: a different GPU legitimately produces different numbers, and a
# contract that went red for that reason would be measuring the machine.
# ---------------------------------------------------------------------------

EXPANSION_MANIFEST_SCHEMA = "noisemaker-cpp.shader-expansion-manifest.v1"
EXPANSION_SUMMARY_SCHEMA = "noisemaker-cpp.shader-expansion-summary.v1"

# A lane either compared bytes and they matched, compared bytes and they did
# not, or never reached the comparer. There is no fourth status, and in
# particular no status that reports a divergence as anything other than a
# failure.
LANE_STATUSES = ("byte_exact", "mismatch", "refused")
RENDERED_LANE_STATUSES = ("byte_exact", "mismatch")

# Graph verdicts that may accompany a byte-exact lane. `mismatch` and
# `projection_unavailable` are proof the shader lane did not run the program
# the CPU plan describes, so they can never sign an exact result.
PROVEN_GRAPH_STATUSES = ("exact", "cpu_plan_projection_contained")

EXPANSION_REQUIRED_KEYS = (
    "schema", "generated", "checkout", "commit", "corpusFixtureSha256",
    "backends", "recordCount", "records",
)


class ExpansionContractError(AssertionError):
    """A manifest or summary that does not meet the expansion contract."""


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ExpansionContractError(message)


def _require_sha256(value: object, where: str) -> None:
    _require(
        isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value),
        f"{where} must be a lowercase sha256 digest",
    )


def validate_expansion_lane(lane: object, record: dict, backend: str) -> None:
    """One backend's verdict on one record."""
    where = f"{record.get('id')}/{backend}"
    _require(isinstance(lane, dict), f"{where}: lane must be an object")
    status = lane.get("status")
    _require(status in LANE_STATUSES, f"{where}: status must be one of {LANE_STATUSES}, got {status!r}")

    if status == "refused":
        # A refusal is a first-class outcome, but it has to say what refused
        # and why, or it is indistinguishable from a result that was dropped.
        _require(isinstance(lane.get("code"), str) and lane["code"].startswith("ERR_"),
                 f"{where}: a refusal must name an ERR_ code")
        _require(isinstance(lane.get("stage"), str) and lane["stage"],
                 f"{where}: a refusal must name the stage that refused")
        _require(isinstance(lane.get("reason"), str) and lane["reason"],
                 f"{where}: a refusal must carry a reason")
        _require("comparison" not in lane,
                 f"{where}: a refusal never compared bytes, so it may not carry a comparison")
        return

    comparison = lane.get("comparison")
    _require(isinstance(comparison, dict), f"{where}: a rendered lane must carry its comparison")
    _require_sha256(comparison.get("expectedSha256"), f"{where}: comparison.expectedSha256")
    _require_sha256(comparison.get("actualSha256"), f"{where}: comparison.actualSha256")
    count = comparison.get("mismatchCount")
    _require(isinstance(count, int) and count >= 0, f"{where}: comparison.mismatchCount must be an integer")

    if status == "byte_exact":
        _require(count == 0, f"{where}: byte_exact with {count} mismatching bytes is a relabeled failure")
        _require(comparison["expectedSha256"] == comparison["actualSha256"],
                 f"{where}: byte_exact with two different image hashes is a relabeled failure")
        _require(comparison.get("firstMismatch") is None,
                 f"{where}: byte_exact may not name a first divergence")
    else:
        _require(count > 0, f"{where}: a mismatch must count the bytes that diverged")
        _require(comparison["expectedSha256"] != comparison["actualSha256"],
                 f"{where}: a mismatch must show two different image hashes")
        first = comparison.get("firstMismatch")
        _require(isinstance(first, dict), f"{where}: a mismatch must name its first divergence")
        for key in ("x", "y", "channel", "channelName", "expected", "actual"):
            _require(key in first, f"{where}: firstMismatch must name {key}")
        _require(isinstance(comparison.get("maxDelta"), int),
                 f"{where}: a mismatch must carry its maximum channel delta")

    graph = lane.get("graph")
    _require(isinstance(graph, dict), f"{where}: a rendered lane must carry its graph verdict")
    _require(isinstance(graph.get("status"), str), f"{where}: graph.status must be a string")
    if status == "byte_exact":
        _require(graph["status"] in PROVEN_GRAPH_STATUSES,
                 f"{where}: graph {graph['status']!r} cannot accompany a byte_exact lane")
    _require(isinstance(graph.get("sourceEffectIds"), list) and graph["sourceEffectIds"],
             f"{where}: the graph verdict must name the effects that resolved")
    _require(isinstance(graph.get("actualPassKeys"), list) and graph["actualPassKeys"],
             f"{where}: the graph verdict must name the passes that ran")

    binding = lane.get("optionsBinding")
    _require(isinstance(binding, dict), f"{where}: a rendered lane must record its options binding")
    _require(binding.get("status") == "bound",
             f"{where}: a lane compared under drifting render options is not a comparison of one program")
    _require(binding.get("differing") == [], f"{where}: a bound options set has no differing options")

    adapter = lane.get("adapter")
    _require(isinstance(adapter, dict), f"{where}: a rendered lane must record the adapter it ran on")
    renderer = (adapter.get("webgl") or {}).get("renderer")
    _require(isinstance(renderer, str) and renderer, f"{where}: the adapter must name its renderer")
    _require(adapter.get("software") is False or adapter.get("allowSoftware") is True,
             f"{where}: a software rasterizer result must be marked as one")

    timing = lane.get("timing")
    _require(isinstance(timing, dict), f"{where}: a rendered lane must record its timing")
    measured = timing.get("measured")
    _require(isinstance(measured, dict), f"{where}: timing must publish what this lane measured")
    resolution = measured.get("resolution")
    _require(isinstance(resolution, dict), f"{where}: the measurement must name its own resolution")
    _require(resolution.get("width") == record.get("width")
             and resolution.get("height") == record.get("height"),
             f"{where}: the measurement resolution must be the resolution the record rendered at")
    _require(measured.get("comparableAcrossBackends") is False,
             f"{where}: no lane measurement is comparable across backends")


def validate_expansion_manifest(manifest: object) -> dict:
    """The step-9 expansion manifest contract. Returns the manifest."""
    _require(isinstance(manifest, dict), "the manifest must be an object")
    for key in EXPANSION_REQUIRED_KEYS:
        _require(key in manifest, f"the manifest must carry {key}")
    _require(manifest["schema"] == EXPANSION_MANIFEST_SCHEMA,
             f"the manifest schema must be {EXPANSION_MANIFEST_SCHEMA}")
    _require_sha256(manifest.get("corpusFixtureSha256"), "corpusFixtureSha256")
    backends = manifest["backends"]
    _require(isinstance(backends, list) and len(backends) >= 2 and len(set(backends)) == len(backends),
             "the expansion compares at least two named, distinct backends")
    records = manifest["records"]
    _require(isinstance(records, list) and records, "the manifest must carry records")
    _require(manifest["recordCount"] == len(records),
             "recordCount must equal the number of records carried")
    seen = set()
    for record in records:
        _require(isinstance(record, dict), "each record must be an object")
        identifier = record.get("id")
        _require(isinstance(identifier, str) and identifier, "each record must carry an id")
        _require(identifier not in seen, f"{identifier}: recorded twice")
        seen.add(identifier)
        expectation = record.get("expectation")
        _require(isinstance(expectation, dict), f"{identifier}: must carry its expectation state")
        if expectation.get("status") == "rendered":
            # The split is a property of the expectation image, so it must be
            # recorded per record — a summary cannot invent it later.
            for key in ("uniform", "spatiallyVarying", "flipSensitive"):
                _require(isinstance(expectation.get(key), bool),
                         f"{identifier}: expectation must classify {key}")
            _require(expectation["uniform"] is not expectation["spatiallyVarying"],
                     f"{identifier}: an expectation is uniform or spatially varying, not both or neither")
            _require(not (expectation["uniform"] and expectation["flipSensitive"]),
                     f"{identifier}: a uniform image cannot be vertically flip-sensitive")
            _require_sha256(expectation.get("rgba8Sha256"), f"{identifier}: expectation.rgba8Sha256")
        else:
            _require(isinstance(expectation.get("code"), str) and expectation["code"].startswith("ERR_"),
                     f"{identifier}: an unrendered expectation must name an ERR_ code")
        lanes = record.get("lanes")
        _require(isinstance(lanes, dict), f"{identifier}: must carry one lane per backend")
        _require(sorted(lanes) == sorted(backends),
                 f"{identifier}: lanes {sorted(lanes)} do not cover the declared backends {sorted(backends)}")
        for backend in backends:
            validate_expansion_lane(lanes[backend], record, backend)
    return manifest


def summarize_expansion_manifest(manifest: dict) -> dict:
    """Derive the only summary shape the expansion is allowed to publish."""
    validate_expansion_manifest(manifest)
    backends = list(manifest["backends"])
    records = manifest["records"]

    distributions = {}
    for backend in backends:
        counts = {status: 0 for status in LANE_STATUSES}
        codes: dict = {}
        graphs: dict = {}
        for record in records:
            lane = record["lanes"][backend]
            counts[lane["status"]] += 1
            if lane["status"] == "refused":
                codes[lane["code"]] = codes.get(lane["code"], 0) + 1
            else:
                status = lane["graph"]["status"]
                graphs[status] = graphs.get(status, 0) + 1
        distributions[backend] = {"counts": counts, "refusalCodes": codes, "graph": graphs}

    exact = {backend: {record["id"] for record in records
                       if record["lanes"][backend]["status"] == "byte_exact"}
             for backend in backends}
    intersection_ids = set.intersection(*exact.values())
    by_id = {record["id"]: record for record in records}
    uniform = sum(1 for i in intersection_ids if by_id[i]["expectation"]["uniform"])
    varying = sum(1 for i in intersection_ids if by_id[i]["expectation"]["spatiallyVarying"])
    flip = sum(1 for i in intersection_ids if by_id[i]["expectation"]["flipSensitive"])

    exclusions = []
    for record in records:
        if record["id"] in intersection_ids:
            continue
        reasons = []
        for backend in backends:
            lane = record["lanes"][backend]
            if lane["status"] == "refused":
                reasons.append(f"{backend}: refused {lane['code']} at {lane['stage']}")
            elif lane["status"] == "mismatch":
                comparison = lane["comparison"]
                reasons.append(
                    f"{backend}: mismatch {comparison['mismatchCount']} bytes, "
                    f"maxDelta {comparison['maxDelta']}")
        exclusions.append({"id": record["id"], "reason": "; ".join(reasons)})

    timing = {}
    for backend in backends:
        lanes = [record["lanes"][backend] for record in records
                 if record["lanes"][backend]["status"] in RENDERED_LANE_STATUSES]
        resolutions = sorted({(lane["timing"]["measured"]["resolution"]["width"],
                               lane["timing"]["measured"]["resolution"]["height"])
                              for lane in lanes})
        medians = sorted(lane["timing"]["medianNs"] for lane in lanes)
        timing[backend] = {
            "lanes": len(lanes),
            "resolutions": [{"width": w, "height": h} for w, h in resolutions],
            "medianOfMedianNs": medians[len(medians) // 2] if medians else None,
            "throughputPublished": sum(1 for lane in lanes
                                       if lane["timing"].get("megapixelsPerSecond") is not None),
            "comparableAcrossBackends": False,
        }

    adapters = {}
    for backend in backends:
        identities = set()
        for record in records:
            lane = record["lanes"][backend]
            if lane["status"] in RENDERED_LANE_STATUSES:
                adapter = lane["adapter"]
                identities.add((adapter["webgl"]["renderer"], adapter.get("browser"),
                                bool(adapter["software"])))
        adapters[backend] = [
            {"renderer": renderer, "browser": browser, "software": software}
            for renderer, browser, software in sorted(identities)
        ]

    return {
        "schema": EXPANSION_SUMMARY_SCHEMA,
        "recordCount": manifest["recordCount"],
        "backends": distributions,
        "intersection": {
            "total": len(intersection_ids),
            "uniform": uniform,
            "spatiallyVarying": varying,
            "flipSensitive": flip,
            "ids": sorted(intersection_ids),
        },
        "exclusions": exclusions,
        "timing": timing,
        "adapters": adapters,
    }


def validate_expansion_summary(summary: object, manifest: dict) -> dict:
    """What a published expansion summary must say, and must not say."""
    _require(isinstance(summary, dict), "the summary must be an object")
    _require(summary.get("schema") == EXPANSION_SUMMARY_SCHEMA,
             f"the summary schema must be {EXPANSION_SUMMARY_SCHEMA}")
    total_records = manifest["recordCount"]
    _require(summary.get("recordCount") == total_records,
             "the summary must account for every record in the manifest")

    for backend, distribution in summary["backends"].items():
        counts = distribution["counts"]
        _require(sorted(counts) == sorted(LANE_STATUSES),
                 f"{backend}: the distribution must name every lane status, including refusals")
        _require(sum(counts.values()) == total_records,
                 f"{backend}: the distribution must account for every record")

    intersection = summary["intersection"]
    # The mandatory split. "N exact" without it overstates what N proves,
    # because a constant-coloured image agrees on both backends for reasons
    # that have nothing to do with the effect under test.
    for key in ("total", "uniform", "spatiallyVarying", "flipSensitive"):
        _require(isinstance(intersection.get(key), int),
                 f"the intersection must publish {key} alongside its total")
    _require(intersection["uniform"] + intersection["spatiallyVarying"] == intersection["total"],
             "the uniform and spatially varying counts must partition the intersection")
    _require(intersection["flipSensitive"] <= intersection["spatiallyVarying"],
             "a flip-sensitive image is spatially varying by construction")
    _require(len(intersection["ids"]) == intersection["total"],
             "the intersection must enumerate the records it counts")

    exclusions = summary["exclusions"]
    excluded_ids = {entry["id"] for entry in exclusions}
    _require(excluded_ids.isdisjoint(set(intersection["ids"])),
             "a record cannot be both counted and excluded")
    _require(intersection["total"] + len(exclusions) == total_records,
             "every record is either in the intersection or in the exclusion ledger")
    for entry in exclusions:
        _require(isinstance(entry.get("reason"), str) and entry["reason"],
                 f"{entry.get('id')}: every exclusion must carry its own reason")

    # A cross-backend performance figure is not merely absent by omission; the
    # contract refuses it, because the two lanes fence on different mechanisms
    # with fence floors an order of magnitude apart. Checked before the lanes
    # are read, so a figure smuggled in beside them is refused as itself and
    # not as a malformed lane.
    banned = {"speedup", "backendRatio", "relativeThroughput", "crossBackendMegapixelsPerSecond"}
    present = banned.intersection(summary["timing"]) | banned.intersection(summary)
    _require(not present, f"the summary may not publish a cross-backend comparison figure: {sorted(present)}")
    for backend, lane in summary["timing"].items():
        # A lane that rendered nothing has nothing to label; a lane that
        # rendered must name the resolution it measured at.
        if lane["lanes"]:
            _require(lane.get("resolutions"),
                     f"{backend}: timing must name the resolution it was measured at")
        _require(lane.get("comparableAcrossBackends") is False,
                 f"{backend}: lane timings are not comparable across backends")

    for backend, identities in summary["adapters"].items():
        # A lane on which every record was refused never reached an adapter;
        # a lane that rendered must say which one it rendered on.
        if summary["timing"][backend]["lanes"]:
            _require(identities, f"{backend}: the summary must name the adapter the lane ran on")
        for identity in identities:
            _require(identity.get("renderer"), f"{backend}: an adapter identity must name its renderer")
    return summary


def _expansion_lane(**overrides) -> dict:
    lane = {
        "status": "byte_exact",
        "comparison": {"status": "pass", "reason": None, "mismatchCount": 0, "maxDelta": 0,
                       "firstMismatch": None, "expectedSha256": "a" * 64, "actualSha256": "a" * 64},
        "graph": {"status": "exact", "reason": None, "sourceEffectIds": ["synth/perlin"],
                  "cpuPlanPassKeys": ["synth/perlin:perlin"],
                  "actualPassKeys": ["synth/perlin:perlin"], "infrastructurePasses": []},
        "optionsBinding": {"status": "bound", "differing": [], "enforcedBy": "ERR_EXPECTED_OPTIONS"},
        "adapter": {"webgl": {"renderer": "some renderer"}, "webgpu": None,
                    "software": False, "allowSoftware": False, "browser": "Chromium/x"},
        "readback": {"orientation": "top_down", "normalized": False, "measuredFormat": "rgba16f",
                     "authentication": "render_path_probe_per_backend_per_format"},
        "timing": {"fenceMechanism": "some_fence", "fenceFloorNs": 1000, "medianNs": 5000,
                   "p95Ns": 6000, "megapixelsPerSecond": None,
                   "throughputSuppressedReason": "median_within_two_fence_floors",
                   "measured": {"resolution": {"width": 17, "height": 11, "pixels": 187},
                                "basis": "fenced_frame_wall_clock_including_fence_overhead",
                                "timingResolutionNs": 1000, "megapixelsPerSecond": 37.4,
                                "nanosecondsPerPixel": 26.7, "comparableAcrossBackends": False}},
        "output": {"rgba8Sha256": "a" * 64, "rawRgba8Sha256": "a" * 64},
    }
    lane.update(overrides)
    return lane


def _expansion_mismatch_lane(**overrides) -> dict:
    lane = _expansion_lane(status="mismatch")
    lane["comparison"] = {
        "status": "failed", "reason": None, "mismatchCount": 14, "maxDelta": 224,
        "firstMismatch": {"x": 5, "y": 2, "channel": 0, "channelName": "r",
                          "expected": 128, "actual": 127},
        "expectedSha256": "a" * 64, "actualSha256": "b" * 64,
    }
    lane.update(overrides)
    return lane


def _expansion_refused_lane(**overrides) -> dict:
    lane = {"status": "refused", "code": "ERR_COMPILATION_FAILED", "stage": "shader_compilation",
            "reason": "S005 Illegal chain structure", "graph": None,
            "optionsBinding": None, "adapter": None}
    lane.update(overrides)
    return lane


def _expansion_record(identifier: str, lanes: dict, expectation: dict | None = None) -> dict:
    return {
        "id": identifier,
        "namespace": identifier.split("/")[0],
        "width": 17, "height": 11,
        "caseOptions": {"width": 17, "height": 11, "time": 0.25, "frame": 0, "seed": 1,
                        "oneShot": "ready", "renderScale": 1},
        "expectation": expectation if expectation is not None else {
            "status": "rendered", "schema": "noisemaker-cpp.dsl-cpu-expectation.v1",
            "rgba8Sha256": "a" * 64, "runnerSha256": "c" * 64, "cpuBehavioralLock": "d" * 64,
            "options": {"width": 17, "height": 11, "time": 0.25, "frame": 0, "seed": 1,
                        "oneShot": "ready", "renderScale": 1},
            "uniform": False, "spatiallyVarying": True, "flipSensitive": True,
        },
        "lanes": lanes,
    }


def expansion_manifest_fixture(records: list) -> dict:
    return {
        "schema": EXPANSION_MANIFEST_SCHEMA,
        "generated": "1970-01-01T00:00:00+00:00",
        "checkout": "<checkout>", "commit": "0" * 40,
        "corpusFixtureSha256": "e" * 64,
        "backends": ["webgl2", "webgpu"],
        "recordCount": len(records),
        "records": records,
    }


class ShaderExpansionProtocolTest(unittest.TestCase):
    """The step-9 expansion contract: shape and claims, never this machine's numbers."""

    def conforming(self) -> dict:
        # Deliberately heterogeneous and deliberately tiny: the contract must
        # hold for any corpus, so the fixture is not a stand-in for the real
        # corpus and carries none of its counts.
        varying_exact = _expansion_record(
            "synth/perlin#default",
            {"webgl2": _expansion_lane(), "webgpu": _expansion_lane()})
        uniform_exact = _expansion_record(
            "filter/invert#default",
            {"webgl2": _expansion_lane(), "webgpu": _expansion_lane()})
        uniform_exact["expectation"].update(
            {"uniform": True, "spatiallyVarying": False, "flipSensitive": False})
        one_sided = _expansion_record(
            "synth/newton#default",
            {"webgl2": _expansion_mismatch_lane(), "webgpu": _expansion_lane()})
        refused = _expansion_record(
            "mixer/mashup#default",
            {"webgl2": _expansion_refused_lane(), "webgpu": _expansion_refused_lane()})
        no_expectation = _expansion_record(
            "synth/media#default",
            {"webgl2": _expansion_refused_lane(code="ERR_NO_CPU_EXPECTATION",
                                               stage="cpu_authority_render",
                                               reason="requires external texture"),
             "webgpu": _expansion_refused_lane(code="ERR_NO_CPU_EXPECTATION",
                                               stage="cpu_authority_render",
                                               reason="requires external texture")},
            expectation={"status": "refused", "code": "ERR_NO_CPU_EXPECTATION",
                         "stage": "cpu_authority_render",
                         "message": "requires external texture"})
        return expansion_manifest_fixture(
            [varying_exact, uniform_exact, one_sided, refused, no_expectation])

    def refusal(self, mutate) -> str:
        manifest = self.conforming()
        mutate(manifest)
        with self.assertRaises(ExpansionContractError) as caught:
            validate_expansion_manifest(manifest)
        return str(caught.exception)

    def test_a_conforming_manifest_and_its_summary_validate(self) -> None:
        manifest = self.conforming()
        validate_expansion_manifest(manifest)
        summary = summarize_expansion_manifest(manifest)
        validate_expansion_summary(summary, manifest)
        self.assertEqual(summary["intersection"]["total"], 2)
        self.assertEqual(summary["intersection"]["uniform"], 1)
        self.assertEqual(summary["intersection"]["spatiallyVarying"], 1)
        self.assertEqual(summary["intersection"]["flipSensitive"], 1)
        self.assertEqual(summary["backends"]["webgl2"]["counts"],
                         {"byte_exact": 2, "mismatch": 1, "refused": 2})
        self.assertEqual(summary["backends"]["webgpu"]["counts"],
                         {"byte_exact": 3, "mismatch": 0, "refused": 2})
        self.assertEqual(
            sorted(entry["id"] for entry in summary["exclusions"]),
            ["mixer/mashup#default", "synth/media#default", "synth/newton#default"])

    def test_the_contract_pins_no_hardware_dependent_count_or_identity(self) -> None:
        # The same contract must accept a run on another adapter, at another
        # resolution, with an entirely different distribution. If it did not,
        # it would be pinning this machine rather than the protocol.
        elsewhere = self.conforming()
        for record in elsewhere["records"]:
            record["width"] = 64
            record["height"] = 64
            for lane in record["lanes"].values():
                if lane["status"] == "refused":
                    continue
                lane["adapter"]["webgl"]["renderer"] = "another vendor, another device"
                lane["adapter"]["browser"] = "Chromium/other"
                lane["timing"]["measured"]["resolution"] = {"width": 64, "height": 64, "pixels": 4096}
                lane["timing"]["megapixelsPerSecond"] = 12.5
                lane["timing"]["throughputSuppressedReason"] = None
        validate_expansion_summary(summarize_expansion_manifest(elsewhere), elsewhere)

        # And a manifest holding a single record, all lanes refused, is a
        # legitimate expansion result: an empty intersection is a finding.
        single = expansion_manifest_fixture([_expansion_record(
            "mixer/mashup#default",
            {"webgl2": _expansion_refused_lane(), "webgpu": _expansion_refused_lane()})])
        summary = validate_expansion_summary(summarize_expansion_manifest(single), single)
        self.assertEqual(summary["intersection"]["total"], 0)
        self.assertEqual(len(summary["exclusions"]), 1)

    def test_a_divergence_may_not_be_relabeled_as_an_exact_result(self) -> None:
        def relabel(manifest):
            lane = manifest["records"][2]["lanes"]["webgl2"]
            lane["status"] = "byte_exact"
        self.assertIn("relabeled failure", self.refusal(relabel))

        def invent_status(manifest):
            manifest["records"][2]["lanes"]["webgl2"]["status"] = "within_tolerance"
        self.assertIn("status must be one of", self.refusal(invent_status))

        def unproven_graph(manifest):
            manifest["records"][0]["lanes"]["webgl2"]["graph"]["status"] = "projection_unavailable"
        self.assertIn("cannot accompany a byte_exact lane", self.refusal(unproven_graph))

        def exact_with_two_hashes(manifest):
            manifest["records"][0]["lanes"]["webgl2"]["comparison"]["actualSha256"] = "9" * 64
        self.assertIn("two different image hashes", self.refusal(exact_with_two_hashes))

    def test_a_mismatch_must_carry_its_first_divergence_counts_and_both_hashes(self) -> None:
        def drop_first(manifest):
            manifest["records"][2]["lanes"]["webgl2"]["comparison"]["firstMismatch"] = None
        self.assertIn("must name its first divergence", self.refusal(drop_first))

        def drop_coordinate(manifest):
            del manifest["records"][2]["lanes"]["webgl2"]["comparison"]["firstMismatch"]["channelName"]
        self.assertIn("firstMismatch must name channelName", self.refusal(drop_coordinate))

        def zero_count(manifest):
            manifest["records"][2]["lanes"]["webgl2"]["comparison"]["mismatchCount"] = 0
        self.assertIn("must count the bytes that diverged", self.refusal(zero_count))

        def one_hash(manifest):
            manifest["records"][2]["lanes"]["webgl2"]["comparison"]["actualSha256"] = "a" * 64
        self.assertIn("two different image hashes", self.refusal(one_hash))

    def test_a_refusal_must_name_its_code_stage_and_reason(self) -> None:
        for key, expected in (("code", "must name an ERR_ code"),
                              ("stage", "must name the stage that refused"),
                              ("reason", "must carry a reason")):
            def drop(manifest, key=key):
                del manifest["records"][3]["lanes"]["webgl2"][key]
            self.assertIn(expected, self.refusal(drop))

        def silent_drop(manifest):
            manifest["records"][3]["lanes"]["webgl2"]["code"] = "skipped"
        self.assertIn("must name an ERR_ code", self.refusal(silent_drop))

        def missing_lane(manifest):
            del manifest["records"][3]["lanes"]["webgpu"]
        self.assertIn("do not cover the declared backends", self.refusal(missing_lane))

    def test_a_rendered_lane_must_be_options_bound_and_off_a_software_rasterizer(self) -> None:
        def drifted(manifest):
            binding = manifest["records"][0]["lanes"]["webgl2"]["optionsBinding"]
            binding["status"] = "disagreement"
            binding["differing"] = ["seed"]
        self.assertIn("not a comparison of one program", self.refusal(drifted))

        def software(manifest):
            manifest["records"][0]["lanes"]["webgl2"]["adapter"]["software"] = True
        self.assertIn("must be marked as one", self.refusal(software))

        def anonymous(manifest):
            manifest["records"][0]["lanes"]["webgl2"]["adapter"]["webgl"]["renderer"] = ""
        self.assertIn("must name its renderer", self.refusal(anonymous))

        def foreign_resolution(manifest):
            manifest["records"][0]["lanes"]["webgl2"]["timing"]["measured"]["resolution"] = {
                "width": 512, "height": 512, "pixels": 262144}
        self.assertIn("resolution the record rendered at", self.refusal(foreign_resolution))

        def comparable(manifest):
            manifest["records"][0]["lanes"]["webgl2"]["timing"]["measured"]["comparableAcrossBackends"] = True
        self.assertIn("comparable across backends", self.refusal(comparable))

    def test_every_record_must_classify_its_expectation_image(self) -> None:
        def unclassified(manifest):
            del manifest["records"][0]["expectation"]["flipSensitive"]
        self.assertIn("must classify flipSensitive", self.refusal(unclassified))

        def both(manifest):
            manifest["records"][0]["expectation"]["uniform"] = True
        self.assertIn("not both or neither", self.refusal(both))

        def impossible(manifest):
            expectation = manifest["records"][1]["expectation"]
            expectation["flipSensitive"] = True
        self.assertIn("cannot be vertically flip-sensitive", self.refusal(impossible))

    def test_the_manifest_must_bind_itself_to_a_tree_and_a_corpus(self) -> None:
        def wrong_schema(manifest):
            manifest["schema"] = "noisemaker-cpp.shader-expansion-manifest.v0"
        self.assertIn("schema must be", self.refusal(wrong_schema))

        for key in ("commit", "corpusFixtureSha256", "backends"):
            def drop(manifest, key=key):
                del manifest[key]
            self.assertIn(f"must carry {key}", self.refusal(drop))

        def miscounted(manifest):
            manifest["recordCount"] = manifest["recordCount"] + 1
        self.assertIn("recordCount must equal", self.refusal(miscounted))

        def one_backend(manifest):
            manifest["backends"] = ["webgl2"]
            for record in manifest["records"]:
                del record["lanes"]["webgpu"]
        self.assertIn("at least two named, distinct backends", self.refusal(one_backend))

    def summary_refusal(self, mutate) -> str:
        manifest = self.conforming()
        summary = summarize_expansion_manifest(manifest)
        mutate(summary)
        with self.assertRaises(ExpansionContractError) as caught:
            validate_expansion_summary(summary, manifest)
        return str(caught.exception)

    def test_an_exact_claim_must_publish_the_uniform_varying_flip_split(self) -> None:
        for key in ("uniform", "spatiallyVarying", "flipSensitive"):
            def drop(summary, key=key):
                del summary["intersection"][key]
            self.assertIn(f"must publish {key}", self.summary_refusal(drop))

        def inflate(summary):
            summary["intersection"]["total"] += 1
        self.assertIn("must partition the intersection", self.summary_refusal(inflate))

        def more_flip_than_varying(summary):
            summary["intersection"]["flipSensitive"] = summary["intersection"]["spatiallyVarying"] + 1
        self.assertIn("spatially varying by construction", self.summary_refusal(more_flip_than_varying))

    def test_every_excluded_record_must_carry_its_own_reason(self) -> None:
        def drop_ledger(summary):
            summary["exclusions"] = []
        self.assertIn("intersection or in the exclusion ledger", self.summary_refusal(drop_ledger))

        def blank_reason(summary):
            summary["exclusions"][0]["reason"] = ""
        self.assertIn("every exclusion must carry its own reason", self.summary_refusal(blank_reason))

        def double_count(summary):
            summary["intersection"]["ids"] = sorted(
                set(summary["intersection"]["ids"]) | {summary["exclusions"][0]["id"]})
            summary["intersection"]["total"] += 1
            summary["intersection"]["spatiallyVarying"] += 1
        self.assertIn("both counted and excluded", self.summary_refusal(double_count))

        def hide_refusals(summary):
            del summary["backends"]["webgl2"]["counts"]["refused"]
        self.assertIn("including refusals", self.summary_refusal(hide_refusals))

    def test_the_summary_may_not_publish_a_cross_backend_performance_figure(self) -> None:
        def speedup(summary):
            summary["timing"]["speedup"] = 4.1
        self.assertIn("may not publish a cross-backend comparison", self.summary_refusal(speedup))

        def comparable(summary):
            summary["timing"]["webgl2"]["comparableAcrossBackends"] = True
        self.assertIn("not comparable across backends", self.summary_refusal(comparable))

        def unlabelled(summary):
            summary["timing"]["webgl2"]["resolutions"] = []
        self.assertIn("must name the resolution", self.summary_refusal(unlabelled))

    def test_the_summary_must_name_the_adapter_each_lane_ran_on(self) -> None:
        def anonymous(summary):
            summary["adapters"]["webgl2"] = []
        self.assertIn("must name the adapter", self.summary_refusal(anonymous))

        def nameless(summary):
            summary["adapters"]["webgl2"][0]["renderer"] = ""
        self.assertIn("must name its renderer", self.summary_refusal(nameless))


if __name__ == "__main__":
    unittest.main()
