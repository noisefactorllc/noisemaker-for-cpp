#!/usr/bin/env python3
"""Exhaustive DSL sweep for filter/median:median across radius x size x seed.

Complements the hand-crafted pixel-parity oracle
(median_all_radii_oracle_generator.mjs) with an END-TO-END check: for every
allowed radius (1, 2, 3) crossed with >=3 render sizes and >=3 distinct noise
inputs, compile and render the SAME `.median(radius: ..., threshold: 0)` DSL
program through both drivers this repo's parity lane already trusts --

  * the JS CPU authority runner (tools/benchmark/run_cpu_case.mjs), and
  * the C++ executor driver (noisemaker-dsl-cpu-case, built from this repo)

-- and compares the rendered RGBA8 bytes exactly (zero tolerance), the same
comparer tests/test_dsl_corpus_parity.py uses. This exercises the FULL graph
executor path (DSL parse -> compile -> admit -> bind -> render), not just
bind_median called directly the way tests/test_median_kernel.cpp does, so it
also proves the custom-adapter routing change (RADIUS reaching `Bindings` as
a real compile-define binding) actually works for every allowed radius, not
only the one the corpus happens to exercise.

Usage:
  python3 median_radius_sweep.py --cpu-root <immutable authority checkout> \\
      --driver <path to noisemaker-dsl-cpu-case>

Exits non-zero (and prints every divergence) if the divergent count is not
exactly zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.benchmark.exact_compare import compare_rgba8, format_diagnostics  # noqa: E402

JS_RUNNER = ROOT / "tools/benchmark/run_cpu_case.mjs"

RADII = (1, 2, 3)
SIZES = ((5, 5), (8, 6), (11, 9))
SEEDS = (1, 7, 42)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_case(radius: int, width: int, height: int, seed: int) -> dict:
    source = (
        "search synth, filter\n"
        f"noise(seed: {seed}).median(radius: {radius}, threshold: 0).write(o0)\n"
        "render(o0)\n"
    )
    return {
        "id": f"median-sweep-r{radius}-{width}x{height}-seed{seed}",
        "recordKind": "admitted",
        "source": source,
        "sourceSha256": sha256_hex(source.encode("utf-8")),
        "options": {"width": width, "height": height, "time": 0.0, "frame": 0, "seed": 1.0},
    }


def run_js(node: str, cpu_root: pathlib.Path, ledger: pathlib.Path | None, case_path: pathlib.Path,
          raw_output: pathlib.Path, metadata_output: pathlib.Path) -> subprocess.CompletedProcess:
    args = [node, str(JS_RUNNER), "--cpu-root", str(cpu_root), "--case", str(case_path),
           "--rgba8-output", str(raw_output), "--metadata-output", str(metadata_output)]
    if ledger is not None:
        args += ["--authority-ledger", str(ledger)]
    return subprocess.run(args, capture_output=True, text=True)


def run_cpp(driver: pathlib.Path, source_path: pathlib.Path, record: dict,
           raw_output: pathlib.Path, metadata_output: pathlib.Path) -> subprocess.CompletedProcess:
    options = record["options"]
    return subprocess.run(
        [str(driver),
         "--source-file", str(source_path), "--source-sha256", record["sourceSha256"],
         "--width", str(options["width"]), "--height", str(options["height"]),
         "--time", repr(options["time"]), "--frame", str(options["frame"]),
         "--seed", repr(options["seed"]),
         "--rgba8-output", str(raw_output), "--metadata-output", str(metadata_output)],
        capture_output=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu-root", required=True, type=pathlib.Path)
    parser.add_argument("--driver", required=True, type=pathlib.Path)
    parser.add_argument("--authority-ledger", type=pathlib.Path, default=None)
    args = parser.parse_args()

    cpu_root = args.cpu_root.resolve()
    driver = args.driver.resolve()
    ledger = args.authority_ledger.resolve() if args.authority_ledger else None
    if ledger is None:
        env_ledger = os.environ.get("NOISEMAKER_CPU_AUTHORITY_LEDGER")
        ledger = pathlib.Path(env_ledger).resolve() if env_ledger else None
    if not driver.is_file():
        raise SystemExit(f"driver not found: {driver}")
    import shutil
    node = shutil.which("node")
    if node is None:
        raise SystemExit("node is required")

    total = 0
    js_refused = []
    cpp_refused = []
    divergent = []
    exact = 0

    with tempfile.TemporaryDirectory(prefix="median-radius-sweep-") as tmp:
        scratch = pathlib.Path(tmp)
        for radius in RADII:
            for width, height in SIZES:
                for seed in SEEDS:
                    total += 1
                    record = build_case(radius, width, height, seed)
                    name = record["id"]
                    source_path = scratch / "case.dsl"
                    source_path.write_text(record["source"], encoding="utf-8")
                    case_path = scratch / "case.json"
                    case_path.write_text(json.dumps(record), encoding="utf-8")

                    js_raw = scratch / "js.rgba8"
                    js_meta = scratch / "js.json"
                    js = run_js(node, cpu_root, ledger, case_path, js_raw, js_meta)
                    if js.returncode != 0:
                        js_refused.append((name, (js.stdout or js.stderr).strip()[:200]))
                        continue

                    cpp_raw = scratch / "cpp.rgba8"
                    cpp_meta = scratch / "cpp.json"
                    cpp = run_cpp(driver, source_path, record, cpp_raw, cpp_meta)
                    if cpp.returncode != 0:
                        cpp_refused.append((name, (cpp.stdout or cpp.stderr).strip()[:200]))
                        continue

                    result = compare_rgba8(width, height, js_raw.read_bytes(), cpp_raw.read_bytes())
                    if result["ok"]:
                        exact += 1
                    else:
                        divergent.append((name, format_diagnostics(result)))

    print(f"total cases: {total} ({len(RADII)} radii x {len(SIZES)} sizes x {len(SEEDS)} seeds)")
    print(f"exact: {exact}")
    print(f"js refused: {len(js_refused)}")
    for name, detail in js_refused:
        print(f"  js-refused: {name}: {detail}")
    print(f"cpp refused: {len(cpp_refused)}")
    for name, detail in cpp_refused:
        print(f"  cpp-refused: {name}: {detail}")
    print(f"divergent: {len(divergent)}")
    for name, detail in divergent:
        print(f"  DIVERGENT {name}\n{detail}")

    if js_refused or cpp_refused or divergent:
        return 1
    if exact != total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
