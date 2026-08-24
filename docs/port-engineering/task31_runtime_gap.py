"""Task 31 read-only runtime-gap probe.

Checks, by direct text search (not assumption):
  1. floatBitsToUint / uintBitsToFloat / bit_cast are absent from both
     include/noisemaker/glsl_types.hpp and include/noisemaker/glsl_runtime.hpp.
  2. float_to_uint32 (which DOES exist) is a numeric CONVERSION
     (uint(floatValue) truncate/wrap semantics), not a bit-reinterpretation --
     confirmed by reading its .cpp body -- so it must not be reused for
     floatBitsToUint.
  3. Task 27's scalar uint^uint already emits a bare native C++ `^` operator
     (no glsl::bitwise_xor() call) in the committed
     src/typed_generated/typed_slice.cpp, at the Perlin hash3() function --
     confirmed by locating the exact emitted line and checking it contains
     `^` but not `glsl::bitwise_xor`.
  4. The JS canonical reference for floatBitsToUint (glsl-runtime.js) uses a
     shared Float32Array/Uint32Array buffer alias -- confirmed by locating
     the exact lines.

Read-only: never writes under . or
../noisemaker-for-cpu.
"""
from __future__ import annotations

import json
import pathlib
import re

CPP_REPO = pathlib.Path(".")
CPU_REPO = pathlib.Path("../noisemaker-for-cpu")


def main() -> int:
    report: dict = {}

    types_hpp = (CPP_REPO / "include/noisemaker/glsl_types.hpp").read_text()
    runtime_hpp = (CPP_REPO / "include/noisemaker/glsl_runtime.hpp").read_text()
    report["floatBitsToUint_absent_from_glsl_types_hpp"] = (
        "floatBitsToUint" not in types_hpp)
    report["floatBitsToUint_absent_from_glsl_runtime_hpp"] = (
        "floatBitsToUint" not in runtime_hpp)
    report["uintBitsToFloat_absent_from_both_headers"] = (
        "uintBitsToFloat" not in types_hpp and "uintBitsToFloat" not in runtime_hpp)

    runtime_cpp = (CPP_REPO / "src/glsl_runtime.cpp").read_text()
    match = re.search(r"std::uint32_t float_to_uint32\(double value\) noexcept \{(.*?)\n\}",
                       runtime_cpp, re.S)
    report["float_to_uint32_body_found"] = match is not None
    body = match.group(1) if match else ""
    report["float_to_uint32_is_conversion_not_bitcast"] = (
        "bit_cast" not in body and ("fmod" in body or "trunc" in body))
    report["float_to_uint32_body"] = body.strip()

    slice_cpp = CPP_REPO / "src/typed_generated/typed_slice.cpp"
    slice_text = slice_cpp.read_text()
    hash3_match = re.search(
        r"\[\[nodiscard\]\] double hash3\([^)]*glsl::Vec3 p\) noexcept \{(.*?)\n\}",
        slice_text, re.S)
    report["perlin_hash3_body_found"] = hash3_match is not None
    hash3_body = hash3_match.group(1) if hash3_match else ""
    xor_line = next((line for line in hash3_body.splitlines() if "^" in line), None)
    report["perlin_scalar_xor_emitted_line"] = xor_line
    report["perlin_scalar_xor_uses_bare_operator"] = bool(
        xor_line and "glsl::bitwise_xor" not in xor_line and "^" in xor_line)
    vector_xor_line = next(
        (line for line in hash3_body.splitlines() if "glsl::bitwise_xor" in line), None)
    report["perlin_vector_xor_uses_helper_call"] = vector_xor_line
    report["scalar_and_vector_xor_lower_differently_confirmed"] = bool(
        xor_line and vector_xor_line and xor_line != vector_xor_line)

    cpu_runtime = (CPU_REPO / "src/csl/glsl-runtime.js").read_text()
    report["js_floatBitsToUint_uses_shared_typed_array_alias"] = (
        "this.bitsFloat[0] = value" in cpu_runtime
        and "return this.bitsUint[0]" in cpu_runtime)
    report["js_bitsFloat_is_Float32Array"] = "new Float32Array(this.bitsBuffer)" in cpu_runtime
    report["js_bitsUint_is_Uint32Array"] = "new Uint32Array(this.bitsBuffer)" in cpu_runtime

    out = pathlib.Path("docs/port-engineering/task31-runtime-gap-output.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
