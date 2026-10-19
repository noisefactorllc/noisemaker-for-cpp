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
