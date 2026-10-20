"""Which float divisions the emitter lowers to Metal division.

The rule is the CPU authority's (scripts/upstream/compile-glsl.js): a float
division whose divisor holds a run-time value calls `$runtime.fdiv`. The unit
cases below pin each branch of tools/glslcpp/frontend/metal_division.py. The
census case compares the classifier with the authority's own generated
kernels when NOISEMAKER_CPU_ROOT names the pinned authority.
"""
from __future__ import annotations

import collections
import os
import pathlib
import re
import unittest

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.metal_division import metal_division_sites
from tools.glslcpp.frontend.semantic import analyze_program

HEADER = """#version 300 es
precision highp float;
uniform vec2 resolution;
uniform float scale;
uniform int count;
const float K = 4.0;
float g = 2.0;
out vec4 fragColor;
"""


def _routed(body: str, *, defines: dict | None = None, extra: str = "") -> list[str]:
    source = HEADER + extra + body
    program = analyze_program(parse_program(source, "test/metal:metal", defines or {}), "test/metal:metal")
    sites = metal_division_sites(program)
    text = program.source
    return [text[node.span.start:node.span.end] for node in sites.nodes]


class MetalDivisionClassifierTests(unittest.TestCase):
    def test_uniform_divisor_is_routed(self):
        self.assertEqual(_routed("void main() { float a = gl_FragCoord.x / resolution.x; fragColor = vec4(a); }"),
                         ["gl_FragCoord.x / resolution.x"])

    def test_constant_divisors_keep_the_float64_division(self):
        self.assertEqual(_routed("void main() { float a = gl_FragCoord.x / 3.0; float b = a / K; fragColor = vec4(b); }"), [])

    def test_gl_frag_coord_divisor_is_routed(self):
        self.assertEqual(_routed("void main() { float a = 1.0 / gl_FragCoord.y; fragColor = vec4(a); }"),
                         ["1.0 / gl_FragCoord.y"])

    def test_main_local_follows_its_initializer(self):
        routed = _routed("void main() { float r = resolution.y; float c = 1.0; float a = 2.0 / r; float b = 2.0 / c;"
                         " fragColor = vec4(a, b, 0.0, 1.0); }")
        self.assertEqual(routed, ["2.0 / r"])

    def test_global_variable_follows_its_initializer(self):
        self.assertEqual(_routed("void main() { float a = gl_FragCoord.x / g; fragColor = vec4(a); }"), [])

    def test_helper_parameters_and_locals_are_unknown(self):
        routed = _routed("float f(float d) { float e = scale; return 1.0 / d + 1.0 / e; }"
                         " void main() { fragColor = vec4(f(scale)); }")
        self.assertEqual(routed, [])

    def test_helper_division_by_a_uniform_is_routed(self):
        self.assertEqual(_routed("float f(float x) { return x / scale; } void main() { fragColor = vec4(f(1.0)); }"),
                         ["x / scale"])

    def test_main_local_without_initializer_is_unknown(self):
        self.assertEqual(_routed("void main() { float d; d = scale; float a = 1.0 / d; fragColor = vec4(a); }"), [])

    def test_integer_division_is_never_routed(self):
        self.assertEqual(_routed("void main() { int a = 7 / count; fragColor = vec4(float(a)); }"), [])

    def test_compound_vector_by_scalar_is_routed(self):
        self.assertEqual(_routed("void main() { vec2 v = gl_FragCoord.xy; v /= scale; fragColor = vec4(v, 0.0, 1.0); }"),
                         ["v /= scale"])

    def test_compound_single_lane_keeps_the_float64_division(self):
        self.assertEqual(_routed("void main() { vec2 v = gl_FragCoord.xy; v.x /= scale; float s = gl_FragCoord.x;"
                                 " s /= scale; fragColor = vec4(v, s, 1.0); }"), [])

    def test_compound_multi_lane_swizzle_is_routed(self):
        self.assertEqual(_routed("void main() { vec3 v = gl_FragCoord.xyz; v.xy /= scale; fragColor = vec4(v, 1.0); }"),
                         ["v.xy /= scale"])

    def test_runtime_define_names_are_constants(self):
        routed = _routed("void main() { float a = gl_FragCoord.x / float(MODE); fragColor = vec4(a); }",
                         defines={"MODE": 3})
        self.assertEqual(routed, [])


def _cpu_root() -> pathlib.Path | None:
    value = os.environ.get("NOISEMAKER_CPU_ROOT")
    return pathlib.Path(value) if value else None


class ScatterSeedTermTests(unittest.TestCase):
    def test_emitted_seed_term_multiplies_before_float32_store(self):
        import hashlib
        import shutil
        import subprocess
        import tempfile
        from tools.glslcpp import generate_typed_slice as generator
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend.scatter_jitter_cross_lane_assignment_profile import PROFILE

        root = pathlib.Path(__file__).resolve().parents[1]
        key = "filter/scatter:scatterJitter"
        source = (root / "tools/glslcpp/corpus" / generator.check_corpus.REVISION /
                  "sources/filter/scatter/scatterJitter.glsl").read_text()
        parsed = parse_program(generator.transform_generic_dynamic_source(source, key), key,
                               generator.GENERIC_DYNAMIC_DEFINE_TYPES[key])
        parsed["raw_source"] = source
        program = analyze_program(parsed, key)
        emitted = render_typed_cpp(
            program, key, hashlib.sha256(source.encode()).hexdigest(),
            numeric_literal_contract="source-double",
            scatter_jitter_cross_lane_assignment_profile=PROFILE)
        statement = next(line for line in emitted.splitlines() if "glsl::Vec2 rnd = " in line)
        start = statement.index("noisemaker::f32(")
        opening = statement.index("(", start)
        depth = 1
        end = opening + 1
        while depth:
            depth += (statement[end] == "(") - (statement[end] == ")")
            end += 1
        expression = statement[start:end]
        # Node 26 captures of the authority's float((seed) * 101.7).
        expected = [3528156774, 3469436519, 3268109926, 0,
                    1120626278, 1321952871, 1380673126]
        unit = ('#include "noisemaker/numeric.hpp"\n#include <bit>\n'
                '#include <cstdint>\n#include <iostream>\n'
                'struct State { std::int32_t seed; };\nint main() {\n'
                'for (std::int32_t seed : {INT32_MIN, -16777217, -1, 0, 1, 16777217, INT32_MAX}) {\n'
                'const State state{seed};\nstd::cout << std::bit_cast<std::uint32_t>(' +
                expression + ') << "\\n";\n}}\n')
        compiler = shutil.which("c++") or shutil.which("clang++")
        self.assertIsNotNone(compiler, "a C++ compiler is required")
        with tempfile.TemporaryDirectory(prefix="scatter-seed-term-") as temporary:
            cpp = pathlib.Path(temporary) / "probe.cpp"
            binary = pathlib.Path(temporary) / "probe"
            cpp.write_text(unit)
            result = subprocess.run(
                [compiler, "-std=c++20", "-ffp-contract=off", "-Wall", "-Wextra", "-Werror",
                 "-I", str(root / "include"), str(cpp), str(root / "src/numeric.cpp"),
                 "-o", str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([int(value) for value in result.stdout.splitlines()], expected)


class NumberStorageTests(unittest.TestCase):
    def _probe(self, body, *, expected=(2.3333333333333335, -2.3333333333333335, 0.875),
               local_names=("q",), output="q", uniforms="", state_fields="",
               state_rows=("{3}", "{-3}", "{8}"), emitted=None, prelude=""):
        import hashlib
        import shutil
        import subprocess
        import tempfile
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp

        if emitted is None:
            key = "test/number:probe"
            source = ("#version 300 es\nprecision highp float;\nuniform int width;\n" + uniforms +
                      "\nout vec4 fragColor;\nvoid main() { " + body + " }\n")
            program = analyze_program(parse_program(source, key), key)
            emitted = render_typed_cpp(program, key, hashlib.sha256(source.encode()).hexdigest())
        declarations = [line for line in emitted.splitlines()
                        if any(re.search(r"\b" + re.escape(name) + r" = ", line)
                               for name in local_names)]
        self.assertEqual(len(declarations), len(local_names), declarations)
        root = pathlib.Path(__file__).resolve().parents[1]
        unit = ('#include "noisemaker/glsl_runtime.hpp"\n'
                '#include <array>\n#include <iostream>\n#include <iomanip>\n#include <cmath>\n'
                'namespace glsl = noisemaker::glsl;\n'
                'struct State { std::int32_t width; ' + state_fields + ' };\n' +
                '\nint main() { for (const State& state : '
                'std::array<State, ' + str(len(state_rows)) + '>{' +
                ', '.join('State' + row for row in state_rows) + '}) {\n'
                '[[maybe_unused]] const glsl::PixelContext context{};\n' +
                prelude + '\n' + '\n'.join(declarations) + '\nstd::cout << std::setprecision(17) << '
                'static_cast<double>(' + output + ') << "\\n";\n}}\n')
        compiler = shutil.which("c++") or shutil.which("clang++")
        self.assertIsNotNone(compiler, "a C++ compiler is required")
        with tempfile.TemporaryDirectory(prefix="number-storage-") as temporary:
            cpp, binary = pathlib.Path(temporary) / "probe.cpp", pathlib.Path(temporary) / "probe"
            cpp.write_text(unit)
            result = subprocess.run(
                [compiler, "-std=c++20", "-ffp-contract=off", "-Wall", "-Wextra", "-Werror",
                 "-I", str(root / "include"), str(cpp), str(root / "src/glsl_runtime.cpp"),
                 str(root / "src/numeric.cpp"), str(root / "src/surface.cpp"),
                 "-o", str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([float(value) for value in result.stdout.splitlines()], list(expected))

    def test_integer_quotient_keeps_cpu_number_local(self):
        self._probe("int q = 7 / width; fragColor = vec4(float(q));")

    def test_catalog_integer_quotients_preserve_cpu_branch_choices(self):
        import hashlib
        import json
        from tools.glslcpp import check_corpus

        root = pathlib.Path(__file__).resolve().parents[1]
        generated = (root / "src/typed_generated/typed_slice.cpp").read_text()
        manifest = json.loads((root / "src/typed_generated/typed_manifest.json").read_text())
        for key in ("points/flock:agent", "points/life:agent", "points/flow:agent",
                    "filter/median:median", "filter/pixelSort:computeRank",
                    "filter/pixelSort:findBrightest", "filter/pixelSort:gatherSorted"):
            with self.subTest(program=key):
                row = next(item for item in manifest["programs"] if item["program_key"] == key)
                source = root / "tools/glslcpp/corpus" / check_corpus.REVISION / row["source"]
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), row["source_sha256"])
                marker = "// Typed IR program: " + key + "\n"
                self.assertEqual(generated.count(marker), 1)
                body = generated.split(marker, 1)[1].split("// Typed IR program:", 1)[0]
                if key == "filter/median:median":
                    self._probe("", local_names=("medianIndex",), output="medianIndex",
                                state_rows=("{1}",), expected=(12.0,), emitted=body,
                                prelude="(void)state;")
                elif key.startswith("filter/pixelSort:"):
                    count = re.search(r"\bconst int NUM_SAMPLES = (\d+);", source.read_text())
                    self.assertIsNotNone(count)
                    samples = int(count.group(1))
                    self.assertEqual(samples, 64 if key.endswith(":gatherSorted") else 32)
                    self._probe("", local_names=("NUM_SAMPLES", "sampleX"), output="sampleX",
                                state_rows=("{17}", "{1048577}"),
                                expected=(16.0, 1032193.0 if samples == 64 else 1015809.0),
                                emitted=body,
                                prelude=f"const std::int32_t s = {samples - 1};"
                                        " const std::int32_t width = state.width;")
                elif key == "points/flow:agent":
                    self._probe("", local_names=("quarterSize", "band"), output="band",
                                state_rows=("{65}",), expected=(0.0,), emitted=body,
                                prelude="const std::int32_t totalAgents = state.width * state.width;"
                                        " const std::int32_t agentIndex = 1056;")
                else:
                    self._probe("", local_names=("sy",), output="sy", state_rows=("{64}",),
                                expected=(1.015625,), emitted=body,
                                prelude="const std::int32_t sampleIdx = 65;"
                                        " const glsl::IVec2 stateSize{state.width, state.width};")

    def test_literal_ternary_quotients_keep_cpu_number_values(self):
        self._probe("int q = width > 0 ? 7 / width : 8 / width; fragColor = vec4(float(q));",
                    expected=(2.3333333333333335, -2.6666666666666665, 0.875))

    def test_parenthesized_name_does_not_restore_integer_division(self):
        self._probe("int n = 7; int q = (n) / width; fragColor = vec4(float(q));",
                    local_names=("n", "q"))

    def test_parenthesized_quotient_does_not_restore_integer_division(self):
        self._probe("int n = 7; int q = (n / width); fragColor = vec4(float(q));",
                    local_names=("n", "q"))

    def test_parenthesized_ternary_quotients_keep_number_values(self):
        self._probe("int n = 7; int q = width > 0 ? (n / width) : (n / width);"
                    " fragColor = vec4(float(q));", local_names=("n", "q"))

    def test_bare_name_still_restores_integer_division(self):
        self._probe("int n = 7; int q = n / width; fragColor = vec4(float(q));",
                    local_names=("n", "q"), expected=(2.0, -2.0, 0.0))

    def test_name_ternary_still_restores_integer_division(self):
        self._probe("int n = 7; int q = width > 0 ? n / width : n / width;"
                    " fragColor = vec4(float(q));", local_names=("n", "q"),
                    expected=(2.0, -2.0, 0.0))

    def test_number_local_remainder_keeps_fraction(self):
        self._probe("int q = 7 / width; int r = q % 2; fragColor = vec4(float(r));",
                    local_names=("q", "r"), output="r",
                    expected=(0.3333333333333335, -0.3333333333333335, 0.875))

    def test_trailing_integer_cast_preserves_source_grouping(self):
        for denominator, expected in (
                ("int(width)", (2.0, -2.0, 0.0)),
                ("(int(width))", (2.3333333333333335, -2.3333333333333335, 0.875))):
            with self.subTest(denominator=denominator):
                self._probe("int a = 7; int q = a / " + denominator +
                            "; fragColor = vec4(float(q));", local_names=("a", "q"), expected=expected)

    def test_trailing_cast_coerces_the_additive_prefix(self):
        self._probe("int a = -1; int q = 1 + a / int(width); fragColor = vec4(float(q));",
                    local_names=("a", "q"), expected=(0.0, 1.0, 0.0))

    def test_grouped_trailing_cast_keeps_its_own_boundary(self):
        self._probe("int a = -1; int q = 1 + (a / int(width)); fragColor = vec4(float(q));",
                    local_names=("a", "q"), expected=(1.0, 1.0, 1.0))

    def test_operator_after_cast_keeps_the_fractional_quotient(self):
        self._probe("int a = -1; int q = a / int(width) + 1; fragColor = vec4(float(q));",
                    local_names=("a", "q"), expected=(0.6666666666666667, 1.3333333333333333, 0.875))

    def test_trailing_uint_cast_keeps_the_signed_cpu_number(self):
        self._probe("uint a = 7u; uint q = a / uint(width); fragColor = vec4(float(q));",
                    local_names=("a", "q"), expected=(2.0, -2.0, 0.0))

    def test_component_index_still_restores_integer_division(self):
        self._probe("int q = values.x / width; fragColor = vec4(float(q));",
                    uniforms="uniform ivec2 values;", state_fields="glsl::IVec2 values;",
                    state_rows=("{3, glsl::IVec2{7, 8}}", "{-3, glsl::IVec2{7, 8}}",
                                "{8, glsl::IVec2{7, 8}}"), expected=(2.0, -2.0, 0.0))

    def test_dynamic_index_keeps_existing_admission_guard(self):
        import hashlib
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp

        key = "test/number:probe"
        source = ("#version 300 es\nprecision highp float;\nuniform int width;\n"
                  "uniform int i;\nuniform ivec2 values;\nout vec4 fragColor;\n"
                  "void main() { int q = values[i] / width;"
                  "fragColor = vec4(float(q)); }\n")
        program = analyze_program(parse_program(source, key), key)
        with self.assertRaisesRegex(TypedEmissionError, "unsupported typed expression index"):
            render_typed_cpp(program, key, hashlib.sha256(source.encode()).hexdigest())

    def test_pixel_sort_sample_rejects_changed_source(self):
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp

        root = pathlib.Path(__file__).resolve().parents[1]
        for name in ("computeRank", "findBrightest", "gatherSorted"):
            key = "filter/pixelSort:" + name
            with self.subTest(program=key):
                path = (root / "tools/glslcpp/corpus" / check_corpus.REVISION /
                        "sources/filter/pixelSort" / (name + ".glsl"))
                source = path.read_text()
                self.assertEqual(source.count("int sampleX = (s * width) / NUM_SAMPLES;"), 1)
                changed = source.replace("int sampleX = (s * width) / NUM_SAMPLES;",
                                         "int sampleX = (s + width) / NUM_SAMPLES;")
                program = analyze_program(parse_program(changed, key), key)
                expected = ("source digest mismatch for discarded local counter"
                            if name == "computeRank" else "PixelSort sample source changed")
                with self.assertRaisesRegex(TypedEmissionError, expected):
                    render_typed_cpp(program, key, hashlib.sha256(changed.encode()).hexdigest())
                original = analyze_program(parse_program(source, key), key)
                forged = dataclasses.replace(original, raw_source=changed)
                with self.assertRaisesRegex(TypedEmissionError, "PixelSort sample source changed"):
                    render_typed_cpp(forged, key, hashlib.sha256(source.encode()).hexdigest())

class MetalDivisionAuthorityCensusTests(unittest.TestCase):
    """Per factory and function, the classifier agrees with the authority's generated kernels."""

    def test_classifier_matches_the_authority_kernels(self):
        cpu_root = _cpu_root()
        if cpu_root is None:
            self.skipTest("NOISEMAKER_CPU_ROOT must identify the pinned CPU authority")
        from tools.glslcpp import check_corpus
        from tools.glslcpp import emit_typed_cpp
        from tools.glslcpp import generate_typed_slice as g

        text = (cpu_root / "src/effects/generated/canonical-kernels.js").read_text(encoding="utf-8")
        index = {int(number): key for key, number in re.findall(r'"([^"]+)": canonicalFactory(\d+),', text)}
        parts = re.split(r"\nfunction canonicalFactory(\d+)\(", text)
        authority: dict[str, collections.Counter] = {}
        for position in range(1, len(parts), 2):
            functions = re.split(r"\n  function ([A-Za-z_$][\w$]*) \(", parts[position + 1])
            counts = collections.Counter()
            for item in range(1, len(functions), 2):
                counts[functions[item]] += len(re.findall(r"\$runtime\.fdiv\(|\.divideMetal\(", functions[item + 1]))
            authority[index[int(parts[position])]] = counts

        slice_spec = g.load_slice()
        root = check_corpus._corpus_root(g._ROOT)
        checked = 0
        for position, entry in enumerate(g._source_entries(g._ROOT, slice_spec)):
            key = entry["program_key"]
            if key not in authority or key in emit_typed_cpp.AUTHORITY_ADAPTER_PROGRAMS:
                continue
            row = slice_spec["programs"][position]
            source = (root / entry["source"]).read_text(encoding="utf-8")
            defines = row["defines"]
            if key == g.NOISE_RUNTIME_DEFINE_KEY and row.get("runtime_define_profile") == g.NOISE_RUNTIME_DEFINE_PROFILE:
                source, defines = g.transform_noise_source(source, key), g.NOISE_DYNAMIC_DEFINES
            elif (key in g.GENERIC_DYNAMIC_DEFINE_TYPES
                  and row.get("runtime_define_profile") == g.GENERIC_RUNTIME_DEFINE_PROFILE):
                source, defines = g.transform_generic_dynamic_source(source, key), g.GENERIC_DYNAMIC_DEFINE_TYPES[key]
            program = analyze_program(parse_program(source, key, defines), key)
            sites = metal_division_sites(program)
            owner = {}
            for function in program.functions:
                stack = list(function.body)
                while stack:
                    statement = stack.pop()
                    stack.extend(statement.children)
                    expressions = list(statement.expressions)
                    while expressions:
                        expression = expressions.pop()
                        owner[id(expression)] = function.name
                        expressions.extend(expression.children)
            native = collections.Counter(owner[id(node)] for node in sites.nodes)
            for function in set(native) | {name for name, count in authority[key].items() if count}:
                with self.subTest(program=key, function=function):
                    # The authority writes a routed vector division as one call or as one
                    # call per lane, so its text holds between one and four calls per site.
                    self.assertEqual(native[function] > 0, authority[key][function] > 0)
                    self.assertLessEqual(native[function], authority[key][function])
            checked += 1
        self.assertGreater(checked, 250)


if __name__ == "__main__":
    unittest.main()
