"""Task 31: exact C++ runtime gap check for tanh / mod(vec3|vec4,float) /
reflect / floatBitsToUint, plus the matching JS reference lookup. READ-ONLY:
only reads files, writes nothing under noisemaker-for-cpp or noisemaker-for-cpu.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

CPP_ROOT = Path(".")
JS_ROOT = Path("../noisemaker-for-cpu")

RUNTIME_HPP = CPP_ROOT / "include/noisemaker/glsl_runtime.hpp"
JS_RUNTIME = JS_ROOT / "src/csl/glsl-runtime.js"


def grep(path: Path, pattern: str) -> list[str]:
    text = path.read_text()
    out = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if re.search(pattern, line):
            out.append(f"{lineno}: {line.strip()}")
    return out


def main() -> int:
    report = {
        "cpp_runtime_file": str(RUNTIME_HPP),
        "js_runtime_file": str(JS_RUNTIME),
        "tanh": {
            "cpp_hits": grep(RUNTIME_HPP, r"\btanh\b"),
            "js_hits": grep(JS_RUNTIME, r"\btanh\b"),
            "conclusion": "absent from C++ runtime entirely; JS is a 1-line Math.tanh unary map",
        },
        "mod_vec3_vec4_float": {
            "cpp_mod_overload_lines": grep(RUNTIME_HPP, r"\bmod\("),
            "conclusion": (
                "all 5 vector mod() template overloads are constrained "
                "`requires(N == 2)`; no N==3/N==4 instantiation exists. "
                "Needs relaxing the constraint on the existing templates, "
                "not a brand-new function."
            ),
        },
        "reflect": {
            "cpp_hits": grep(RUNTIME_HPP, r"\breflect\b"),
            "js_hits": grep(JS_RUNTIME, r"\breflect\b"),
            "conclusion": (
                "already implemented GENERICALLY for any N (template<size_t N>, "
                "no N==2/3 constraint) -- works for vec3 today with ZERO runtime "
                "changes needed. Only the codegen/validator admission gate is missing."
            ),
        },
        "floatBitsToUint": {
            "cpp_hits": grep(RUNTIME_HPP, r"floatBitsToUint|floatBitsToInt|uintBitsToFloat"),
            "js_hits": grep(JS_RUNTIME, r"floatBitsToUint|uintBitsToFloat"),
            "conclusion": (
                "absent from C++ runtime entirely; JS aliases a shared Float32Array/"
                "Uint32Array buffer. C++ equivalent is a 1-line std::bit_cast<uint32_t>(float)."
            ),
        },
        "scalar_uint_xor": {
            "note": (
                "Not a runtime-function question at all: uint32_t ^ uint32_t is a "
                "native C++ operator. The existing vector case already emits a "
                "glsl::bitwise_xor() helper call; the diagnostic probe in "
                "probe_task31.py confirmed emitting a bare `(left ^ right)` C++ "
                "expression for the scalar case renders and the emitter reports "
                "`pass` once the two admission gates are cleared."
            ),
        },
        "float9_fixed_nine_runtime": {
            "note": (
                "No new runtime primitive needed either -- Sharpen/Sobel already "
                "prove and emit float[9]/vec2[9] local tables as native_element_type "
                "double / glsl::Vec2 arrays via prove_fixed_nine_local_tables(). "
                "The gap for Lighting is that prove_fixed_nine_local_tables() "
                "hardcodes searching only the function literally named 'main' "
                "(tools/glslcpp/frontend/fixed_nine_table_proof.py:93, "
                "`mains = [f for f in functions if f.name == 'main' and f.body]`, "
                "then indexes main.body[declaration_index] directly), but Lighting's "
                "three float[9]/vec2[9] tables (sobel_x, sobel_y, offsets) are "
                "declared inside a helper function calculateNormal(), not main. "
                "Reuse therefore requires generalizing that hardcoded function-name "
                "search, not just adding new profile-dict entries as done for "
                "Sharpen->Sobel."
            ),
        },
    }
    out = Path(__file__).with_name("runtime-gap-check-output.json")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(out)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
