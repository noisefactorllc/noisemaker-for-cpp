from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from tools.glslcpp import check_corpus, emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tests.gate import full_run_only


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEYS = ("synth/scope:scope", "synth/spectrum:spectrum")


def audio_program(key):
    effect, shader = key.split(":")
    corpus = ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION
    relative = f"{effect}/{shader}.glsl"
    source = next(path for section in ("sources", "pending-sources")
                  if (path := corpus / section / relative).exists()).read_text()
    return analyze_program(parse_program(source, key), key)


class AudioUniformProfileTests(unittest.TestCase):
    @full_run_only
    def test_emitted_audio_kernels_match_cpu26d_float32_captures(self):
        # Immutable CPU 26d6f42be38da7172f602373e844f85a8155356f factories
        # 284/287: 8x8 pixels plus exact x endpoints, first with an asymmetric
        # float32 waveform and then zero input. Hashes cover every float lane.
        expected = (
            "5a791fff742d60260b4c9aa17d2d8c1e164c2bf0515924c67283fccc92df359b",
            "3fe4fe4e2665e4491ef0a473f17edbfdd994c686fe278eb88b952bbf6c7872f7",
        )
        bodies = []
        for key in KEYS:
            program = audio_program(key)
            name = key.split(":")[1]
            bodies.append(emit_typed_cpp.render_typed_cpp(
                program, key, hashlib.sha256(program.raw_source.encode()).hexdigest(),
                namespace=f"audio_{name}", factory=f"bind_audio_{name}"))
        unit = '''
#include "noisemaker/kernel.hpp"
#include "noisemaker/sampler.hpp"
#include <bit>
#include <iostream>
namespace noisemaker {
''' + "\n".join(bodies) + r'''
}
int main() {
  using namespace noisemaker;
  for (int kind = 0; kind < 2; ++kind) for (int zero = 0; zero < 2; ++zero) {
    glsl::AudioUniform128 samples;
    for (int i = 0; i < 128; ++i) samples.data[i] = zero ? 0.0F : f32(((i * 37) % 131) / 130.0);
    glsl::Bindings bindings;
    bindings.set_uniform("resolution", glsl::Vec2(8.0F));
    bindings.set_uniform("fullResolution", glsl::Vec2(8.0F));
    bindings.set_uniform("tileOffset", glsl::Vec2(0.0F));
    bindings.set_uniform(kind == 0 ? "audioWaveform" : "audioSpectrum", samples);
    bindings.set_uniform("lineColor", glsl::DVec3(.123456789, .75, .951234567));
    bindings.set_uniform("lineThickness", zero ? .75 : .35);
    bindings.set_uniform("gain", zero ? 1.0 : 1.37);
    const auto kernel = kind == 0 ? bind_audio_scope(bindings) : bind_audio_spectrum(bindings);
    samples.data.fill(99.0F);
    bindings = glsl::Bindings{};
    auto sample = [&](float x, float y, bool invalid) {
      glsl::PixelContext context;
      context.frag_coord = glsl::Vec4(x, y, 0.0F, 1.0F);
      context.resolution = glsl::Vec2(8.0F);
      glsl::Vec4 output;
      kernel.run_pixel(context, output);
      for (std::size_t lane = 0; lane < 4; ++lane) {
        if (invalid) { if (!std::isnan(output[lane])) return false; continue; }
        const auto word = std::bit_cast<std::uint32_t>(output[lane]);
        for (unsigned shift = 0; shift < 32; shift += 8) std::cout.put(static_cast<char>((word >> shift) & 255U));
      }
      return true;
    };
    for (int y = 0; y < 8; ++y) for (int x = 0; x < 8; ++x) sample(x + .5F, 7.5F - y, false);
    for (float x : {0.0F, 8.0F}) sample(x, 4.5F, false);
    for (float x : {-1.0F, 9.0F}) if (!sample(x, 4.5F, true)) return 1;
  }
  return 0;
}
'''
        compiler = shutil.which("c++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory(prefix="audio-kernels-") as raw:
            path = pathlib.Path(raw) / "probe.cpp"
            binary = pathlib.Path(raw) / "probe"
            path.write_text(unit)
            sources = ["surface", "numeric", "sampler", "glsl_runtime", "kernel"]
            built = subprocess.run(
                [compiler, "-std=c++20", "-ffp-contract=off", "-I", str(ROOT / "include"),
                 str(path), *(str(ROOT / f"src/{name}.cpp") for name in sources),
                 "-o", str(binary)], capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            result = subprocess.run([str(binary)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout), 2 * 528 * 4)
        for kind, digest in enumerate(expected):
            self.assertEqual(hashlib.sha256(result.stdout[kind*2112:(kind+1)*2112]).hexdigest(), digest)

    @full_run_only
    def test_audio_uniform_owns_float32_words_and_checks_read_bounds(self):
        unit = r'''
#include "noisemaker/graph/executor.hpp"
#include <bit>
#include <cmath>
int main() {
  using noisemaker::glsl::AudioUniform128;
  noisemaker::graph::ExecutionInputs inputs;
  if (inputs.audio_state) return 1;
  inputs.audio_state.emplace();
  for (float value : inputs.audio_state->waveform.data) if (value != 0) return 2;
  AudioUniform128 value;
  value.data[0] = std::bit_cast<float>(0x80000000U);
  value.data[1] = std::bit_cast<float>(0x7f800001U);
  value.data[127] = 1.234567F;
  noisemaker::glsl::Bindings bindings;
  bindings.set_uniform("audioWaveform", value);
  value.data.fill(99.0F);
  auto owned = bindings.get<AudioUniform128>("audioWaveform");
  if (std::bit_cast<unsigned>(owned.data[0]) != 0x80000000U) return 3;
  if (std::bit_cast<unsigned>(owned.data[1]) != 0x7f800001U) return 4;
  if (owned.sample(127) != static_cast<double>(1.234567F)) return 5;
  if (!std::isnan(owned.sample(-1)) || !std::isnan(owned.sample(128))) return 6;
  if (!std::isnan(owned.sample(INT64_MAX))) return 7;
  try { (void)bindings.get<double>("audioWaveform"); return 8; }
  catch (const noisemaker::glsl::KernelBindingError&) {}
  return 0;
}
'''
        compiler = shutil.which("c++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory(prefix="audio-uniform128-") as raw:
            path = pathlib.Path(raw) / "probe.cpp"
            binary = pathlib.Path(raw) / "probe"
            path.write_text(unit)
            built = subprocess.run(
                [compiler, "-std=c++20", "-I", str(ROOT / "include"),
                 str(path), str(ROOT / "src/glsl_runtime.cpp"),
                 str(ROOT / "src/numeric.cpp"), "-o", str(binary)],
                capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_exact_audio_sources_validate_and_emit_checked_owned_arrays(self):
        for key in KEYS:
            with self.subTest(key=key):
                program = audio_program(key)
                digest = hashlib.sha256(program.raw_source.encode()).hexdigest()
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=digest)
                emitted = emit_typed_cpp.render_typed_cpp(program, key, digest)
                self.assertIn("glsl::AudioUniform128", emitted)
                self.assertEqual(emitted.count(".sample("), 2)

    def test_audio_source_or_ir_mutations_refuse_at_both_authorities(self):
        for key in KEYS:
            program = audio_program(key)
            digest = hashlib.sha256(program.raw_source.encode()).hexdigest()
            for changed in (
                dataclasses.replace(program, key="synth/foreign:foreign"),
                dataclasses.replace(program, raw_source=program.raw_source + "\n"),
                dataclasses.replace(program, functions=program.functions * 2),
                dataclasses.replace(program, declarations=program.declarations[:-1]),
            ):
                with self.subTest(key=key, changed=changed.key):
                    with self.assertRaises(generate_typed_slice.GeneratorError):
                        generate_typed_slice.validate_capabilities(
                            changed, generate_typed_slice.APPROVED_CAPABILITIES,
                            source_hash=digest)
                    with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                        emit_typed_cpp.render_typed_cpp(changed, changed.key, digest)

    def test_changed_array_shape_names_and_reads_do_not_expand_admission(self):
        for key in KEYS:
            program = audio_program(key)
            uniform = "audioWaveform" if key == KEYS[0] else "audioSpectrum"
            for raw in (
                program.raw_source.replace("[128]", "[127]"),
                program.raw_source.replace("[128]", "[129]"),
                program.raw_source.replace(uniform, "foreignSamples"),
                program.raw_source.replace(f"{uniform}[i1]", f"{uniform}[i0]"),
                program.raw_source.replace("float s0 =", f"float unused = {uniform}[0];\n    float s0 ="),
            ):
                changed = analyze_program(parse_program(raw, key), key)
                digest = hashlib.sha256(raw.encode()).hexdigest()
                with self.subTest(key=key, digest=digest):
                    with self.assertRaises(generate_typed_slice.GeneratorError):
                        generate_typed_slice.validate_capabilities(
                            changed, generate_typed_slice.APPROVED_CAPABILITIES, source_hash=digest)
                    with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                        emit_typed_cpp.render_typed_cpp(changed, key, digest)
            with self.assertRaises(emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(program, key, "0" * 64)


if __name__ == "__main__":
    unittest.main()
