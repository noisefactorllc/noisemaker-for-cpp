#!/usr/bin/env python3
"""Byte-exact proof: noisemaker-render's --input/--texture vs the JS CLI's.

Renders every case in cases.json through BOTH the JS CPU authority's CLI
(`bin/noisemaker-cpu.js render ... --input/--texture`) and the built
`noisemaker-render --input/--texture ... --raw-rgba8`, decodes the JS PNG to
raw top-down RGBA8, and compares the two frames byte-for-byte.

This is the tool that captured the `rgba8Sha256` values frozen into
cases.json (see tests/test_external_textures.py, which checks
noisemaker-render's output against those frozen hashes on every run without
needing node or the JS authority present). Re-run this script with
--capture after touching a fixture PNG or a .dsl program here, to refresh the
frozen hashes from the authority.

Usage:
    python3 compare_with_js_authority.py \
        --cpu-root /path/to/js-cpu-authority \
        [--cpp-cli /path/to/build/noisemaker-render] \
        [--node node] [--capture]

Env fallbacks: NOISEMAKER_CPU_ROOT for --cpu-root, NOISEMAKER_RENDER_CLI for
--cpp-cli (defaulting to build-lane/noisemaker-render next to the repo root).
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

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CASES_PATH = HERE / "cases.json"

DECODE_SNIPPET = """
import {{ readFile, writeFile }} from 'node:fs/promises'
const {{ decodePng }} = await import({png_module!r})
const img = decodePng(await readFile({png_path!r}))
await writeFile({raw_path!r}, Buffer.from(img.data))
"""


def load_cases() -> list[dict]:
    document = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    assert document["schema"] == "noisemaker-cpp.external-texture-cases.v1"
    return document["cases"]


def texture_args(case: dict) -> list[str]:
    args: list[str] = []
    if case.get("input"):
        args += ["--input", str(HERE / case["input"])]
    for assignment in case.get("textures", []):
        name, _, filename = assignment.partition("=")
        args += ["--texture", f"{name}={HERE / filename}"]
    return args


def run_js(node: str, cpu_root: pathlib.Path, case: dict, work: pathlib.Path) -> bytes:
    dsl = HERE / case["dsl"]
    png_out = work / f"{case['name']}-js.png"
    cli = cpu_root / "bin" / "noisemaker-cpu.js"
    args = [
        node, str(cli), "render", str(dsl),
        "--width", str(case["width"]), "--height", str(case["height"]),
        *texture_args(case), "--output", str(png_out),
    ]
    result = subprocess.run(args, cwd=str(cpu_root), text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"JS authority render failed for {case['name']}: {result.stderr}")
    raw_out = work / f"{case['name']}-js.rgba8"
    png_module = str((cpu_root / "src" / "node" / "png.js").resolve())
    snippet = DECODE_SNIPPET.format(
        png_module=png_module, png_path=str(png_out), raw_path=str(raw_out),
    )
    decode = subprocess.run([node, "--input-type=module", "-"], input=snippet,
                            text=True, capture_output=True)
    if decode.returncode != 0:
        raise RuntimeError(f"JS PNG decode failed for {case['name']}: {decode.stderr}")
    return raw_out.read_bytes()


def run_cpp(cli: pathlib.Path, case: dict, work: pathlib.Path) -> bytes:
    dsl = HERE / case["dsl"]
    raw_out = work / f"{case['name']}-cpp.rgba8"
    args = [
        str(cli), str(dsl),
        "--width", str(case["width"]), "--height", str(case["height"]),
        *texture_args(case), "--raw-rgba8", str(raw_out),
        "-o", str(work / f"{case['name']}-cpp.png"),
    ]
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"noisemaker-render failed for {case['name']}: {result.stderr}")
    return raw_out.read_bytes()


def default_cpp_cli() -> pathlib.Path | None:
    import os
    env = os.environ.get("NOISEMAKER_RENDER_CLI")
    if env:
        return pathlib.Path(env)
    guess = ROOT / "build-lane" / "noisemaker-render"
    return guess if guess.exists() else None


def main() -> int:
    import os

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-root", default=os.environ.get("NOISEMAKER_CPU_ROOT"))
    parser.add_argument("--cpp-cli", default=None)
    parser.add_argument("--node", default=shutil.which("node") or "node")
    parser.add_argument("--capture", action="store_true",
                        help="rewrite cases.json's rgba8Sha256 fields from the JS authority")
    args = parser.parse_args()

    if not args.cpu_root:
        parser.error("--cpu-root or NOISEMAKER_CPU_ROOT is required")
    cpu_root = pathlib.Path(args.cpu_root).resolve()
    if not (cpu_root / "bin" / "noisemaker-cpu.js").is_file():
        parser.error(f"{cpu_root} does not look like the JS CPU authority (no bin/noisemaker-cpu.js)")

    cpp_cli = pathlib.Path(args.cpp_cli) if args.cpp_cli else default_cpp_cli()
    if not cpp_cli or not cpp_cli.is_file():
        parser.error("--cpp-cli or NOISEMAKER_RENDER_CLI must name a built noisemaker-render binary")

    document = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = document["cases"]
    failures = []
    with tempfile.TemporaryDirectory(prefix="external-textures-compare-") as directory:
        work = pathlib.Path(directory)
        for case in cases:
            js_bytes = run_js(args.node, cpu_root, case, work)
            cpp_bytes = run_cpp(cpp_cli, case, work)
            js_hash = hashlib.sha256(js_bytes).hexdigest()
            cpp_hash = hashlib.sha256(cpp_bytes).hexdigest()
            byte_exact = js_bytes == cpp_bytes
            status = "OK" if byte_exact else "MISMATCH"
            print(f"{case['name']}: {status} js={js_hash[:12]} cpp={cpp_hash[:12]} "
                 f"({len(js_bytes)} bytes)")
            if not byte_exact:
                failures.append(case["name"])
            elif args.capture:
                case["rgba8Sha256"] = cpp_hash
            elif case.get("rgba8Sha256") != cpp_hash:
                failures.append(f"{case['name']} (frozen hash out of date)")

    if args.capture:
        document["cases"] = cases
        CASES_PATH.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        print(f"captured {len(cases)} frozen hashes into {CASES_PATH}")
        return 0

    if failures:
        print(f"FAILED: {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"All {len(cases)} cases are byte-exact against the JS authority.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
