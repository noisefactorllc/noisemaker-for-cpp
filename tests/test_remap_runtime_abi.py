from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class RemapRuntimeAbiTests(unittest.TestCase):
    def test_named_std140_carrier_is_owned_copyable_and_uniform_value_alternative(self):
        source = r'''
#include "noisemaker/glsl_runtime.hpp"
#include <type_traits>
#include <utility>
static void install(noisemaker::glsl::Bindings& bindings) {
  noisemaker::glsl::RemapUniformData payload{};
  payload.data[266] = noisemaker::glsl::Vec4(1, 2, 3, 4);
  bindings.set_uniform("data", payload);
  payload.data[266] = noisemaker::glsl::Vec4(9, 9, 9, 9);
}
int main() {
  using noisemaker::glsl::RemapUniformData;
  static_assert(std::is_copy_constructible_v<RemapUniformData>);
  static_assert(std::is_copy_assignable_v<RemapUniformData>);
  static_assert(std::is_same_v<decltype(RemapUniformData{}.data),
                               std::array<noisemaker::glsl::Vec4, 267>>);
  noisemaker::glsl::Bindings bindings;
  install(bindings);
  const auto copy = bindings.get<RemapUniformData>("data");
  return copy.data[266] == noisemaker::glsl::Vec4(1, 2, 3, 4) ? 0 : 1;
}
'''
        with tempfile.TemporaryDirectory(prefix="remap-runtime-abi-") as td:
            path = pathlib.Path(td) / "probe.cpp"
            binary = pathlib.Path(td) / "probe"
            path.write_text(source)
            result = subprocess.run(
                ["c++", "-std=c++20", "-I", str(ROOT / "include"),
                 str(path), str(ROOT / "src/glsl_runtime.cpp"),
                 str(ROOT / "src/numeric.cpp"), "-o", str(binary)],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            executed = subprocess.run([str(binary)], text=True, capture_output=True)
            self.assertEqual(executed.returncode, 0, executed.stderr)


if __name__ == "__main__":
    unittest.main()
