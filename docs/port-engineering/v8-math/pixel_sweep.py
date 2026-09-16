"""pixel_sweep.py -- the sweep that would have caught the v8-math hole.

Picks every corpus effect whose kernel is known (from this pass's own code
review) to call a transcendental this project ported/fixed -- atan2, hypot
(2 and 3 arg), log, log2, pow, sin, cos -- and renders each one through the
JS CPU authority AND a given C++ `noisemaker-dsl-cpu-case` driver, at
several sizes and at the record's own default parameters, requiring
byte-exact RGBA8 equality. Reports counts, not just pass/fail, and can run
against two different driver binaries (a "before" build and an "after"
build) to show the before/after effect of this pass's fixes.

Usage:
  NOISEMAKER_CPU_ROOT=<authority checkout> python3 pixel_sweep.py \
      --driver-before <path> --driver-after <path> [--sizes 64x64,97x61]

Reuses the SAME corpus/JS-runner/compare machinery
tests/test_dsl_corpus_parity.py already uses (tools.benchmark.corpus_lane,
tools.benchmark.exact_compare) rather than a second, divergent
implementation of "render and compare."
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.benchmark.corpus_lane import JS_RUNNER, load_corpus  # noqa: E402
from tools.benchmark.exact_compare import compare_rgba8, format_diagnostics  # noqa: E402

TARGET_EFFECT_IDS = {
    "synth/julia",
    "synth/mandelbrot",
    "synth/newton",
    "classicNoisedeck/fractal",
    "filter/wormhole",
}


def record_flags_for_size(record: dict, source_path: pathlib.Path, width: int, height: int) -> list[str]:
    options = record["options"]
    return [
        "--source-file", str(source_path),
        "--source-sha256", record["sourceSha256"],
        "--width", str(width), "--height", str(height),
        "--time", repr(options["time"]), "--frame", str(options["frame"]),
        "--seed", repr(options["seed"]),
    ]


def render_js(node: str, cpu_root: pathlib.Path, case_path: pathlib.Path,
               out_raw: pathlib.Path, out_meta: pathlib.Path) -> subprocess.CompletedProcess:
    # run_cpu_case.mjs has no --width/--height override: it reads
    # record.options.width/height from the case JSON itself, so the size
    # change has to be baked into the record written to case_path (see
    # sweep() below) rather than passed on this command line.
    env = dict(__import__("os").environ)
    return subprocess.run(
        [node, str(JS_RUNNER), "--cpu-root", str(cpu_root), "--case", str(case_path),
         "--rgba8-output", str(out_raw), "--metadata-output", str(out_meta)],
        capture_output=True, text=True, env=env)


def render_cpp(driver: pathlib.Path, record: dict, source_path: pathlib.Path,
                width: int, height: int, out_raw: pathlib.Path, out_meta: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(driver), *record_flags_for_size(record, source_path, width, height),
         "--rgba8-output", str(out_raw), "--metadata-output", str(out_meta)],
        capture_output=True, text=True)


def sweep(driver: pathlib.Path, cpu_root: pathlib.Path, node: str,
           records: list[dict], sizes: list[tuple[int, int]],
           times: list[float]) -> dict:
    exact = []
    divergent = []
    js_refused = []
    cpp_refused = []

    with tempfile.TemporaryDirectory(prefix="v8math-pixel-sweep-") as tmp:
        scratch = pathlib.Path(tmp)
        for record in records:
            name = record["effectId"]
            source = scratch / "case.dsl"
            source.write_text(record["source"], encoding="utf-8")

            for (width, height) in sizes:
              for time_value in times:
                label = f"{name} @ {width}x{height} t={time_value}"
                sized_record = dict(record)
                sized_record["options"] = dict(record["options"], width=width, height=height,
                                                time=time_value)
                case = scratch / "case.json"
                case.write_text(json.dumps(sized_record), encoding="utf-8")

                js_raw = scratch / "js.rgba8"
                js_meta = scratch / "js.json"
                js = render_js(node, cpu_root, case, js_raw, js_meta)
                if js.returncode != 0:
                    js_refused.append(label)
                    continue

                cpp_raw = scratch / "cpp.rgba8"
                cpp_meta = scratch / "cpp.json"
                cpp = render_cpp(driver, sized_record, source, width, height, cpp_raw, cpp_meta)
                if cpp.returncode != 0:
                    detail = (cpp.stdout or cpp.stderr or "").strip()[:200]
                    cpp_refused.append(f"{label}: {detail}")
                    continue

                result = compare_rgba8(width, height, js_raw.read_bytes(), cpp_raw.read_bytes())
                if result["ok"]:
                    exact.append(label)
                else:
                    divergent.append(f"{label}\n{format_diagnostics(result)}")

    return {
        "exact": exact,
        "divergent": divergent,
        "js_refused": js_refused,
        "cpp_refused": cpp_refused,
        "total": len(exact) + len(divergent) + len(js_refused) + len(cpp_refused),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--driver-before", type=pathlib.Path, default=None)
    parser.add_argument("--driver-after", type=pathlib.Path, required=True)
    parser.add_argument("--cpu-root", type=pathlib.Path, default=None)
    parser.add_argument("--sizes", default="64x64,97x61")
    parser.add_argument("--times", default="0.25")
    args = parser.parse_args()

    cpu_root = args.cpu_root or pathlib.Path(
        __import__("os").environ.get("NOISEMAKER_CPU_ROOT", ""))
    if not cpu_root or not cpu_root.is_dir():
        raise SystemExit("NOISEMAKER_CPU_ROOT (or --cpu-root) must be an authority checkout")

    node = shutil.which("node")
    if not node:
        raise SystemExit("node is required")

    sizes: list[tuple[int, int]] = []
    for chunk in args.sizes.split(","):
        w, h = chunk.split("x")
        sizes.append((int(w), int(h)))

    times = [float(t) for t in args.times.split(",")]

    manifest = load_corpus()
    records = [r for r in manifest["records"]
               if r["recordKind"] == "admitted" and r["effectId"] in TARGET_EFFECT_IDS]
    print(f"selected {len(records)} admitted records across "
          f"{sorted({r['effectId'] for r in records})} at sizes {sizes} and times {times}",
          file=sys.stderr)

    def report(result: dict, label: str) -> None:
        print(f"=== {label} ===")
        print(json.dumps({k: (v if k == "total" else len(v) if isinstance(v, list) else v)
                            for k, v in result.items()}, indent=2))
        for key in ("divergent", "cpp_refused", "js_refused"):
            if result[key]:
                print(f"-- {key} --")
                print("\n".join(result[key]))

    if args.driver_before is not None:
        before = sweep(args.driver_before, cpu_root, node, records, sizes, times)
        report(before, "BEFORE")

    after = sweep(args.driver_after, cpu_root, node, records, sizes, times)
    report(after, "AFTER")


if __name__ == "__main__":
    main()
