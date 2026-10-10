from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from tools.glslcpp import check_corpus, emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.grade_value_copy_profile import KEY, authenticate_grade_value_copy
from tools.glslcpp.frontend.semantic import analyze_program
from tests.gate import full_run_only


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILE = "grade-lut-index-expression-v1"
EXPECTED = "4c08b6837bf6354ae08b2a35f49f37d18c04ec9c8dfcf4776032468e12c50193"
REFERENCE = ROOT / "tests/fixtures/grade_current/reference.mjs"


def program():
    source = (ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION /
              "sources/filter/grade/lut.glsl").read_text()
    return analyze_program(parse_program(source, KEY, generate_typed_slice._defaults(ROOT, KEY)), KEY)


def render(typed):
    return emit_typed_cpp.render_typed_cpp(
        typed, KEY, hashlib.sha256(typed.raw_source.encode()).hexdigest(),
        grade_index_expression_profile=PROFILE, namespace="grade_copy", factory="bind_grade_copy")


class GradeValueCopyTests(unittest.TestCase):
    def test_reference_reproduces_capture_from_authenticated_cpu(self):
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT is required to reproduce the Grade capture")
        result = subprocess.run(["node", str(REFERENCE), configured], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = json.loads(result.stdout)
        self.assertEqual(captured["cpu_revision"], "5b686a45b5c56329adf0c63cbcf572eb6f23fad1")
        self.assertEqual(captured["pixels"], 230)
        self.assertEqual(captured["float32_sha256"], EXPECTED)
        self.assertEqual(captured["rgba8_sha256"], "0b5bec91de3a56e47fb5f54ea24fac0c73ec47ff8d11dffc801b18e03d7ba8b3")

    def test_reference_rejects_changed_cpu_before_import(self):
        with tempfile.TemporaryDirectory(prefix="grade-forged-authority-") as raw:
            path = pathlib.Path(raw) / "src/effects/generated/canonical-kernels.js"
            path.parent.mkdir(parents=True)
            path.write_text("throw new Error('untrusted module executed');\n")
            result = subprocess.run(["node", str(REFERENCE), raw], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CPU source hash mismatch", result.stderr)
        self.assertNotIn("untrusted module executed", result.stderr)

    def test_exact_copy_site_reuses_whole_source_and_ir_authentication(self):
        typed = program()
        digest = hashlib.sha256(typed.raw_source.encode()).hexdigest()
        declaration = authenticate_grade_value_copy(typed, digest, PROFILE)
        self.assertEqual((declaration.symbol.name, declaration.children[0].symbol.name), ("graded", "rgb"))
        self.assertEqual((declaration.symbol_id, declaration.children[0].symbol_id), (127, 126))
        for altered, source_hash, profile in (
                (dataclasses.replace(typed, key="filter/grade:primary"), digest, PROFILE),
                (dataclasses.replace(typed, raw_source=typed.raw_source + "\n"), digest, PROFILE),
                (dataclasses.replace(typed, functions=tuple(reversed(typed.functions))), digest, PROFILE),
                (typed, "0" * 64, PROFILE), (typed, digest, None)):
            with self.subTest(key=altered.key, source_hash=source_hash, profile=profile):
                with self.assertRaises(ValueError):
                    authenticate_grade_value_copy(altered, source_hash, profile)

    def test_live_emission_copies_original_and_historical_emission_keeps_alias(self):
        typed = program()
        self.assertIn("glsl::Vec3 graded = rgb;", render(typed))
        self.assertNotIn("glsl::Vec3& graded = rgb;", render(typed))
        with mock.patch.object(emit_typed_cpp, "CURRENT_AUTHORITY_VALUE_COPIES", False):
            self.assertIn("glsl::Vec3& graded = rgb;", render(typed))

    def test_alias_collector_regression_fails_emitted_copy_census(self):
        original = emit_typed_cpp._Emitter._collect_pooled_vector_aliases

        def alias_copy(self, statement):
            original(self, statement)
            for declaration in statement.expressions:
                if any(declaration is node for node in self.authorized_vector_value_copies):
                    self.alias_declaration_symbol_ids.add(declaration.symbol_id)
                    self.alias_source_symbol_ids.add(declaration.children[0].symbol_id)

        with mock.patch.object(emit_typed_cpp._Emitter, "_collect_pooled_vector_aliases", alias_copy):
            with self.assertRaisesRegex(emit_typed_cpp.TypedEmissionError, "value-copy emission mismatch"):
                render(program())

    @full_run_only
    def test_emitted_lut_matches_cpu26d_all_presets_and_alpha_blends(self):
        # Independent canonicalFactory59 capture from authenticated CPU
        # 5b686a45b5c56329adf0c63cbcf572eb6f23fad1, behavioral lock
        # 8c4ba7bde134ad664e80fba4690d48bb16f7af5e37d98ee232fe5dc3239b79f6.
        # Two float32 input colors, presets 0..22 and five alpha values cover
        # 230 pixels. Capture includes the production RGBA16F pass store.
        body = render(program())
        unit = '''
#include "noisemaker/kernel.hpp"
#include "noisemaker/sampler.hpp"
#include "noisemaker/texture_format.hpp"
#include <bit>
#include <iostream>
namespace noisemaker {
''' + body + r'''
}
int main() {
  using namespace noisemaker;
  for (const auto color : {glsl::Vec4(.2F, .6666667F, .46666667F, .8F),
                           glsl::Vec4(.91F, .13F, .37F, 1.F)}) {
    Surface input(1U, 1U);
    for (std::size_t lane = 0; lane < 4; ++lane) input.data()[lane] = color[lane];
    for (int preset = 0; preset <= 22; ++preset) for (double alpha : {0., .25, .5, .9553096459809837, 1.}) {
      glsl::Bindings bindings;
      bindings.set_texture("inputTex", input);
      bindings.set_uniform("preset", static_cast<std::int32_t>(preset));
      bindings.set_uniform("alpha", alpha);
      bindings.set_uniform("tileOffset", glsl::Vec2(0.F));
      bindings.set_uniform("fullResolution", glsl::Vec2(1.F));
      const auto kernel = bind_grade_copy(bindings);
      glsl::PixelContext context;
      context.frag_coord = glsl::Vec4(.5F, .5F, 0.F, 1.F);
      context.resolution = glsl::Vec2(1.F);
      glsl::Vec4 value;
      kernel.run_pixel(context, value);
      Surface output(1U, 1U);
      for (std::size_t lane = 0; lane < 4; ++lane) output.data()[lane] = value[lane];
      quantize_texture(output, TextureFormat::rgba16f);
      for (float lane : output.data()) {
        const auto word = std::bit_cast<std::uint32_t>(lane);
        for (unsigned shift = 0; shift < 32; shift += 8) std::cout.put(static_cast<char>((word >> shift) & 255U));
      }
    }
  }
}
'''
        compiler = shutil.which("c++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory(prefix="grade-value-copy-") as raw:
            path, binary = pathlib.Path(raw) / "probe.cpp", pathlib.Path(raw) / "probe"
            path.write_text(unit)
            sources = ["surface", "numeric", "sampler", "glsl_runtime", "kernel", "texture_format", "fdlibm"]
            built = subprocess.run([compiler, "-std=c++20", "-ffp-contract=off", "-I", str(ROOT / "include"),
                                    str(path), *(str(ROOT / f"src/{name}.cpp") for name in sources),
                                    "-o", str(binary)], capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            result = subprocess.run([str(binary)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout), 230 * 16)
        self.assertEqual(hashlib.sha256(result.stdout).hexdigest(), EXPECTED)


if __name__ == "__main__":
    unittest.main()
