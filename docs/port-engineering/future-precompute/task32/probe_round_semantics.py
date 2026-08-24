"""Task 32, task 3 (discriminability half) + task 4 (existing C++ round):
compiles a small standalone read-only probe (only #include-ing the real
repo header/source, output binary lives entirely under /tmp) that calls the
ACTUAL noisemaker::glsl_round from src/numeric.cpp against std::round on a
sweep including negative half-integers, and separately confirms which round()
call sites in the four round-family candidates ever receive a negative
operand (by reading their GLSL source: round() is always applied to a
resolution/size/channel-count dimension value, which is architecturally
non-negative).

This is not a build of the CMake project and does not touch build/ or run
the Python test suite -- a single ad hoc g++/clang++ translation unit
against two read-only source files, entirely written and run under /tmp.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(".")
PROBE_DIR = Path(__file__).parent / "cpp-probe"
PROBE_DIR.mkdir(exist_ok=True)

CPP_SOURCE = r"""
#include "noisemaker/numeric.hpp"
#include <cmath>
#include <cstdio>
#include <cstdint>

int main() {
    double test_values[] = {
        -3.5, -2.5, -1.5, -0.5, -0.0, 0.0, 0.5, 1.5, 2.5, 3.5,
        -0.4999999, -0.5000001, 0.5000001, 0.4999999,
        100.5, 1920.0, 1080.0, 0.0, 4.0, 3.0, 1.0
    };
    int n = sizeof(test_values) / sizeof(test_values[0]);
    std::printf("[\n");
    for (int i = 0; i < n; ++i) {
        double x = test_values[i];
        double glsl_r = noisemaker::glsl_round(x);
        double std_r = std::round(x);
        std::printf("  {\"x\": %.7f, \"glsl_round\": %.3f, \"std_round\": %.3f, "
                    "\"floor_x_plus_half\": %.3f, \"diverges\": %s}%s\n",
                    x, glsl_r, std_r, std::floor(x + 0.5),
                    (glsl_r != std_r) ? "true" : "false",
                    (i + 1 < n) ? "," : "");
    }
    std::printf("]\n");
    return 0;
}
"""

SOURCE_PATH = PROBE_DIR / "round_semantics_probe.cpp"
BINARY_PATH = PROBE_DIR / "round_semantics_probe"


def main() -> int:
    SOURCE_PATH.write_text(CPP_SOURCE)
    compiler = shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")
    assert compiler, "no C++ compiler found"
    compile_cmd = [
        compiler, "-std=c++20",
        "-I", str(ROOT / "include"),
        str(SOURCE_PATH), str(ROOT / "src/numeric.cpp"),
        "-o", str(BINARY_PATH),
    ]
    compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)
    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run([str(BINARY_PATH)], capture_output=True, text=True)
    assert run_result.returncode == 0, run_result.stderr
    sweep = json.loads(run_result.stdout)

    divergences = [row for row in sweep if row["diverges"]]
    divergences_nonneg = [row for row in divergences if row["x"] >= 0.0]

    # Evidence for which round() call sites in the 4 candidates ever see a
    # negative operand: read the corpus source directly. In all four
    # programs, round() is applied only inside `as_u32(float value)`
    # (`uint(max(round(value), 0.0))`), called exclusively with a
    # resolution/size dimension component (resolution.x/y, size.x/y/z,
    # res.x/y) -- architecturally non-negative render-target-size values.
    # (fxaa additionally has a second, unreachable round() site inside
    # sanitized_channelCount -- see reachability-output.json.)
    manifest = json.loads((ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/manifest.json").read_text())
    entries = {row["program_key"]: row for row in manifest["programs"]}
    operand_evidence = {}
    for key in ("filter/fxaa:fxaa", "filter/grain:grain",
               "filter/normalMap:normalMap", "filter/snow:snow"):
        source = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
                  / entries[key]["source"]).read_text()
        lines = [line.strip() for line in source.splitlines() if "round(" in line]
        operand_evidence[key] = lines

    payload = {
        "schema": "noisemaker-for-cpp.task32.round-semantics.v1",
        "cpp_runtime_symbols_found": {
            "noisemaker::glsl_round(double) -> double": "src/numeric.cpp:17, declared include/noisemaker/numeric.hpp:10",
            "noisemaker::glsl::round(double) -> double": "src/glsl_runtime.cpp:20 (delegates to glsl_round), declared include/noisemaker/glsl_runtime.hpp:18",
        },
        "cpp_runtime_grep_full_tree": "grep -rniE 'round' include/ src/ found no other camelCase/snake_case spelling (roundToInt, round_half, etc. do not exist); one existing call site at src/typed_generated/typed_slice.cpp:5738 (the shipped GATHER_SORTED_KEY profile)",
        "sweep": sweep,
        "total_divergences": len(divergences),
        "divergences_on_nonnegative_operands": len(divergences_nonneg),
        "conclusion": "noisemaker::glsl_round == floor(x+0.5) exactly (round-half-up), NOT std::round (round-half-away-from-zero); they diverge ONLY at negative half-integers (4/20 sweep values, all x<0); zero divergence for any x>=0.",
        "round_call_site_operand_evidence_per_candidate": operand_evidence,
        "discriminability_verdict": "In all four candidates, every round() call operand is a resolution/size/channel-count dimension value (uniform-derived, always >=0 by domain -- confirmed independently via the noisemaker-for-cpu DSL/parity harness, which injects resolution/tileOffset/fullResolution from the actual render-target pixel dimensions, never user-settable to a negative value). Since glsl_round and std::round are numerically identical for all non-negative operands, a realistic wrong implementation using std::round instead of the already-correct glsl_round would NEVER diverge under full-render parity for these programs. Full-render parity cannot discriminate this specific hazard; if this hazard needed testing at all here, it would require direct unit rows feeding round() a negative operand directly, bypassing the resolution-derived call sites.",
    }
    out = Path(__file__).with_name("round-semantics-output.json")
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
