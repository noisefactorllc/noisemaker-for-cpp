#!/usr/bin/env python3
"""End-to-end DSL parity proof for synth/remap:remap.

Item 4 of the remap custom_adapter integration: not just noisemaker::effects::
bind_remap called directly with hand-built Bindings (that is
tests/test_generated_kernels.cpp's typed_remap_* suite, oracle-verified
against remapFactory directly), but the WHOLE pipeline -- DSL source text
parsed and compiled by the SAME registry/executor the real renderer uses --
compared byte-for-byte against the JS authority through the same runner
tests.test_dsl_corpus_parity.py uses for every other program.

Each case below is a small multi-effect DSL program: one or two source
effects (solid()/noise()) write to o0/o1, then remap(...) actively wires
zone0_tex/zone1_tex to them with real zone geometry, feathering, and/or
bounds -- unlike the executable-corpus's own auto-generated remap fixture,
which (being built from bare default parameters) never activates a zone at
all. Rendered once through tools/benchmark/run_cpu_case.mjs (the authority)
and once through noisemaker-dsl-cpu-case (the C++ executor), and compared
with zero tolerance via tools.benchmark.exact_compare.

Usage:
  NOISEMAKER_DSL_CPU_CASE=<build>/noisemaker-dsl-cpu-case \\
    python3 docs/port-engineering/remap-parity/remap_dsl_parity.py \\
      --cpu-root /Users/alex/platform/.nm-cpp-work/authority/61aa869
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.benchmark.corpus_lane import JS_RUNNER  # noqa: E402
from tools.benchmark.exact_compare import compare_rgba8, format_diagnostics  # noqa: E402

# Each case is a standalone multi-effect DSL program. Widths/heights are
# deliberately non-square throughout (the executable-corpus's own remap
# fixture, and this lane's earlier direct-kernel oracle, already cover a mix
# of square and non-square; every case here is non-square so this specific
# proof never accidentally relies on width==height).
#
# Genuine DSL-level tiling (fullResolution != render width/height) is NOT
# exercised here: src/runtime/renderer.js's own render(source, options) always
# derives fullResolution from options.width/height (see its passUniforms()/
# canonicalBindings construction) -- there is no render-option that detaches
# the two in the ordinary DSL render path, only in the separate tiled-export
# code path this proof does not drive. Tiling with a real tileOffset is
# already covered at the direct-kernel level (test_generated_kernels.cpp's
# oracle cases "tiled" and "bounds-tiled-nonsquare").
CASES: list[dict[str, object]] = [
    {
        "name": "single-zone-triangle",
        "width": 7, "height": 5, "time": 0.0, "frame": 0, "seed": 1.0,
        "source": (
            "search synth\n"
            "solid(color: [0.9, 0.2, 0.1]).write(o0)\n"
            "remap(zoneCount: 1, smoothEdge: 0, bgColor: [0.05, 0.05, 0.05], bgAlpha: 1, "
            "zone0_tex: o0, zone0_count: 3, zone0_alpha: 1, "
            "zone0_v0: [0, 0, 1, 0], zone0_v1: [0.5, 1, 0, 0]).write(o1)\n"
            "render(o1)\n"
        ),
    },
    {
        "name": "feathered-square",
        "width": 8, "height": 6, "time": 0.0, "frame": 0, "seed": 2.0,
        "source": (
            "search synth\n"
            "solid(color: [0.1, 0.6, 0.3]).write(o0)\n"
            "remap(zoneCount: 1, smoothEdge: 0.8, bgColor: [0.02, 0.02, 0.08], bgAlpha: 1, "
            "zone0_tex: o0, zone0_count: 4, zone0_alpha: 0.85, "
            "zone0_v0: [0.15, 0.15, 0.85, 0.15], zone0_v1: [0.85, 0.85, 0.15, 0.85]).write(o1)\n"
            "render(o1)\n"
        ),
    },
    {
        "name": "bounds-rejected-zone",
        "width": 9, "height": 5, "time": 0.0, "frame": 0, "seed": 3.0,
        "source": (
            "search synth\n"
            "solid(color: [0.8, 0.8, 0.1]).write(o0)\n"
            "remap(zoneCount: 1, smoothEdge: 0, bgColor: [0.1, 0.1, 0.1], bgAlpha: 1, "
            "zone0_tex: o0, zone0_count: 4, zone0_alpha: 1, zone0_bounds: [0.5, 0, 1, 1], "
            "zone0_v0: [0, 0, 1, 0], zone0_v1: [1, 1, 0, 1]).write(o1)\n"
            "render(o1)\n"
        ),
    },
    {
        "name": "overlapping-translucent-zones",
        "width": 8, "height": 5, "time": 0.0, "frame": 0, "seed": 4.0,
        "source": (
            "search synth\n"
            "solid(color: [0.8, 0.1, 0.1]).write(o0)\n"
            "solid(color: [0.1, 0.1, 0.8]).write(o1)\n"
            "remap(zoneCount: 2, smoothEdge: 0, bgColor: [0.2, 0.1, 0.05], bgAlpha: 0.8, "
            "zone0_tex: o0, zone0_count: 4, zone0_alpha: 0.5, "
            "zone0_v0: [0, 0, 0.8, 0], zone0_v1: [0.8, 1, 0, 1], "
            "zone1_tex: o1, zone1_count: 4, zone1_alpha: 0.9, "
            "zone1_v0: [0.2, 0, 1, 0], zone1_v1: [1, 1, 0.2, 1]).write(o2)\n"
            "render(o2)\n"
        ),
    },
    {
        "name": "bounds-with-feather-dilation",
        "width": 8, "height": 5, "time": 0.0, "frame": 0, "seed": 5.0,
        "source": (
            "search synth\n"
            "solid(color: [0.3, 0.7, 0.9]).write(o0)\n"
            "remap(zoneCount: 1, smoothEdge: 1, bgColor: [0.05, 0.2, 0.1], bgAlpha: 1, "
            "zone0_tex: o0, zone0_count: 4, zone0_alpha: 1, zone0_bounds: [0.3, 0.3, 0.7, 0.7], "
            "zone0_v0: [0, 0, 1, 0], zone0_v1: [1, 1, 0, 1]).write(o1)\n"
            "render(o1)\n"
        ),
    },
    {
        "name": "eight-zone-strips",
        "width": 16, "height": 7, "time": 0.0, "frame": 0, "seed": 6.0,
        "source": (
            "search synth\n"
            "solid(color: [0.9, 0.9, 0.9]).write(o0)\n"
            "remap(zoneCount: 8, smoothEdge: 0, bgColor: [0, 0, 0], bgAlpha: 1, "
            + ", ".join(
                f"zone{z}_tex: o0, zone{z}_count: 4, zone{z}_alpha: {0.1 + z * 0.1:.2f}, "
                f"zone{z}_v0: [{z / 8:.4f}, 0, {(z + 1) / 8:.4f}, 0], "
                f"zone{z}_v1: [{(z + 1) / 8:.4f}, 1, {z / 8:.4f}, 1]"
                for z in range(8)
            )
            + ").write(o1)\n"
            "render(o1)\n"
        ),
    },
    {
        "name": "noise-source-single-zone",
        "width": 11, "height": 6, "time": 0.25, "frame": 3, "seed": 7.0,
        "source": (
            "search synth\n"
            "noise().write(o0)\n"
            "remap(zoneCount: 1, smoothEdge: 0.3, bgColor: [0.1, 0.1, 0.1], bgAlpha: 1, "
            "zone0_tex: o0, zone0_count: 5, zone0_alpha: 0.95, "
            "zone0_v0: [0.5, 0.05, 0.95, 0.35], zone0_v1: [0.7, 0.95, 0.15, 0.6], "
            "zone0_v2: [0.05, 0.35, 0, 0]).write(o1)\n"
            "render(o1)\n"
        ),
    },
    {
        "name": "degenerate-and-inactive-zones",
        "width": 6, "height": 9, "time": 0.0, "frame": 0, "seed": 8.0,
        "source": (
            "search synth\n"
            "solid(color: [0.4, 0.5, 0.9]).write(o0)\n"
            "remap(zoneCount: 2, smoothEdge: 0, bgColor: [0.25, 0.35, 0.45], bgAlpha: 0.6, "
            "zone0_tex: o0, zone0_count: 2, zone0_alpha: 1, "
            "zone0_v0: [0.1, 0.1, 0.9, 0.9], "
            "zone1_count: 4, zone1_alpha: 1, "
            "zone1_v0: [0, 0, 1, 0], zone1_v1: [1, 1, 0, 1]).write(o1)\n"
            "render(o1)\n"
        ),
    },
]


def resolve_driver() -> pathlib.Path:
    import os
    configured = os.environ.get("NOISEMAKER_DSL_CPU_CASE")
    if not configured:
        raise SystemExit("NOISEMAKER_DSL_CPU_CASE must point at the built noisemaker-dsl-cpu-case")
    driver = pathlib.Path(configured)
    if not driver.is_file():
        raise SystemExit(f"NOISEMAKER_DSL_CPU_CASE is not a file: {driver}")
    return driver


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu-root", required=True, type=pathlib.Path)
    args = parser.parse_args()
    cpu_root = args.cpu_root.resolve()
    if not cpu_root.is_dir():
        raise SystemExit(f"--cpu-root is not a directory: {cpu_root}")

    node = shutil.which("node")
    if not node:
        raise SystemExit("node is required for the authority runner")
    driver = resolve_driver()

    results = []
    with tempfile.TemporaryDirectory(prefix="remap-dsl-parity-") as td:
        scratch = pathlib.Path(td)
        for case in CASES:
            name = case["name"]
            source_text = case["source"]
            source_sha256 = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
            source_path = scratch / f"{name}.dsl"
            source_path.write_text(source_text, encoding="utf-8")

            record = {
                "id": name, "recordKind": "admitted",
                "source": source_text, "sourceSha256": source_sha256,
                "options": {
                    "width": case["width"], "height": case["height"],
                    "time": case["time"], "frame": case["frame"], "seed": case["seed"],
                },
            }
            case_path = scratch / f"{name}.json"
            case_path.write_text(json.dumps(record), encoding="utf-8")

            js_raw = scratch / f"{name}.js.rgba8"
            js_meta = scratch / f"{name}.js.json"
            js = subprocess.run(
                [node, str(JS_RUNNER), "--cpu-root", str(cpu_root), "--case", str(case_path),
                 "--rgba8-output", str(js_raw), "--metadata-output", str(js_meta)],
                capture_output=True, text=True)
            if js.returncode != 0:
                results.append((name, False, f"authority refused: {js.stderr.strip()[:300]}"))
                continue

            cpp_raw = scratch / f"{name}.cpp.rgba8"
            cpp_meta = scratch / f"{name}.cpp.json"
            cpp = subprocess.run(
                [str(driver), "--source-file", str(source_path), "--source-sha256", source_sha256,
                 "--width", str(case["width"]), "--height", str(case["height"]),
                 "--time", repr(case["time"]), "--frame", str(case["frame"]), "--seed", repr(case["seed"]),
                 "--rgba8-output", str(cpp_raw), "--metadata-output", str(cpp_meta)],
                capture_output=True, text=True)
            if cpp.returncode != 0:
                detail = cpp.stdout.strip() or cpp.stderr.strip()
                results.append((name, False, f"executor refused: {detail[:300]}"))
                continue

            comparison = compare_rgba8(case["width"], case["height"], js_raw.read_bytes(), cpp_raw.read_bytes())
            if comparison["ok"]:
                results.append((name, True, "byte-exact"))
            else:
                results.append((name, False, format_diagnostics(comparison)))

    exact = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    print(f"\n{exact}/{len(results)} cases byte-exact through the full DSL pipeline "
          "(node run_cpu_case.mjs vs. noisemaker-dsl-cpu-case).")
    return 0 if exact == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
