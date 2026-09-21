"""Compile fresh loop-bound kernels and exercise their real uniform bindings."""

from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from tools.glslcpp.emit_typed_cpp import render_typed_cpp
from tools.glslcpp.check_corpus import REVISION
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.runtime_loop_bound_profile import PROFILE, apply_runtime_loop_bound
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION / "sources"


class ConvolutionFeedbackBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        compiler = os.environ.get("CXX") or shutil.which("c++")
        if compiler is None:
            raise RuntimeError("a C++20 compiler is required")
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        directory = pathlib.Path(temporary.name)
        cls.executable = directory / "binding-check"
        harness = ['#include "noisemaker/kernel.hpp"',
                   '#include "noisemaker/sampler.hpp"',
                   '#include <iostream>', '#include <string>',
                   'namespace noisemaker {']
        for name, effect in (("cfBlur", "convolutionFeedback"),
                             ("cfSharpen", "convolutionFeedback"),
                             ("blurH", "blur"), ("blurV", "blur")):
            key = f"filter/{effect}:{name}"
            raw = (CORPUS / f"filter/{effect}/{name}.glsl").read_text(encoding="utf-8")
            digest = hashlib.sha256(raw.encode()).hexdigest()
            program = analyze_program(parse_program(raw, key), key)
            program = apply_runtime_loop_bound(program, digest, PROFILE)
            harness.append(render_typed_cpp(
                program, key, digest, f"kernel_{name}", f"bind_{name}",
                runtime_loop_bound_profile=PROFILE))
        harness.append(r'''
}  // namespace noisemaker
int main(int argc, char** argv) {
  using namespace noisemaker;
  if (argc != 2) return 2;
  const std::string mode = argv[1];
  Surface input(1, 1);
  for (int pass = 0; pass < 4; ++pass) {
    const bool integer_radius = pass < 2;
    const char* radius_name = pass == 0 ? "blurRadius" : pass == 1 ? "sharpenRadius" :
                              pass == 2 ? "radiusX" : "radiusY";
    auto factory = pass == 0 ? &bind_cfBlur : pass == 1 ? &bind_cfSharpen :
                   pass == 2 ? &bind_blurH : &bind_blurV;
    if (!integer_radius && mode != "valid") continue;
    for (const std::int32_t radius : {1, 4, 5, 10}) {
      glsl::Bindings bindings;
      bindings.set_texture("inputTex", input);
      bindings.set_uniform("renderScale", 0.5);
      bindings.set_uniform("blurAmount", 1.0);
      bindings.set_uniform("sharpenAmount", 1.0);
      bindings.set_uniform("tileOffset", glsl::Vec2(0.0f));
      bindings.set_uniform("fullResolution", glsl::Vec2(1.0f));
      if (mode == "wrong-type") bindings.set_uniform(radius_name, double(radius));
      else if (mode == "out-of-range") bindings.set_uniform(radius_name, std::int32_t(11));
      else if (integer_radius) bindings.set_uniform(radius_name, radius);
      else bindings.set_uniform(radius_name, double(radius) + 0.25);
      bool rejected = false;
      try { (void)factory(bindings); }
      catch (const glsl::KernelBindingError& error) {
        rejected = true;
        if (mode == "valid") std::cerr << radius_name << ": " << error.what() << '\n';
      }
      if (rejected != (mode != "valid")) return 1;
    }
  }
  return 0;
}
''')
        source = directory / "binding-check.cpp"
        source.write_text("\n".join(harness), encoding="utf-8")
        sources = ("surface", "numeric", "sampler", "fdlibm", "fdlibm_off",
                   "glsl_runtime", "kernel")
        compiled = subprocess.run([
            compiler, "-std=c++20", "-O0", "-Wall", "-Wextra", "-Wpedantic",
            "-Werror", "-ffp-contract=off", "-I", str(ROOT / "include"),
            str(source), *(str(ROOT / f"src/{name}.cpp") for name in sources),
            "-o", str(cls.executable),
        ], text=True, capture_output=True, check=False)
        if compiled.returncode:
            raise AssertionError(compiled.stdout + compiled.stderr)

    def run_case(self, mode: str) -> None:
        result = subprocess.run([str(self.executable), mode], text=True,
                                capture_output=True, check=False)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_integer_feedback_and_fractional_blur_radius_bindings_are_accepted(self) -> None:
        self.run_case("valid")

    def test_float_binding_cannot_bypass_integer_radius_abi(self) -> None:
        self.run_case("wrong-type")

    def test_radius_guard_still_rejects_out_of_range_integer(self) -> None:
        self.run_case("out-of-range")


if __name__ == "__main__":
    unittest.main()
