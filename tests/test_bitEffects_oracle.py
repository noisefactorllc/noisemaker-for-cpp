from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = REPOSITORY / "docs/port-engineering/bit-effects-parity"
GENERATOR = PACKAGE / "bitEffects_oracle_generator.mjs"
MATERIALIZER = REPOSITORY / "tools/glslcpp/generate_bitEffects_native_oracle_include.py"
ORACLE = PACKAGE / "bitEffects-oracles.json"
REPORT = PACKAGE / "bitEffects-oracle-report.md"
INCLUDE = REPOSITORY / "tests/oracles/bitEffects_expected.inc"


def _sidecar(path: pathlib.Path) -> pathlib.Path:
    return path.with_name(path.name + ".sha256")


def _authority_snapshot() -> pathlib.Path:
    configured = os.environ.get("NOISEMAKER_CPU_ROOT")
    if not configured:
        pytest.skip("NOISEMAKER_CPU_ROOT is unset; immutable-authority test skipped")
    snapshot = pathlib.Path(configured)
    if not snapshot.is_dir():
        pytest.skip("NOISEMAKER_CPU_ROOT does not name a directory; immutable-authority test skipped")
    return snapshot


def test_bitEffects_oracle_package_is_authenticated_and_exact() -> None:
    for path in (GENERATOR, MATERIALIZER, ORACLE, REPORT, INCLUDE):
        assert path.is_file(), path
        sidecar = _sidecar(path)
        assert sidecar.is_file(), sidecar
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        assert sidecar.read_text() == f"{expected}  {path.name}\n"

    document = json.loads(ORACLE.read_text())
    assert document["schema"] == "noisemaker-for-cpp.bitEffects.pixel-parity.v1"
    assert document["program_key"] == "classicNoisedeck/bitEffects:bitEffects"
    assert document["factory"]["name"] == "canonicalFactory0"
    assert document["source"]["raw_sha256"]
    assert document["source"]["normalized_sha256"]
    assert document["strict_comparer_self_tests"]["status"] == "passed"
    assert len(document["render_cases"]) >= 16
    assert {case["bindings"]["MODE"] for case in document["render_cases"]} == {0, 1}
    frozen_defines = {
        "COLOR_SCHEME": 20,
        "FORMULA": 0,
        "INTERP": 0,
        "MASK_COLOR_SCHEME": 1,
        "MASK_FORMULA": 10,
        "MODE": 1,
    }
    native_cases = [
        case for case in document["render_cases"]
        if case.get("native_direct_compatible") is True
    ]
    assert len(native_cases) >= 4
    assert all(
        {name: case["bindings"][name] for name in frozen_defines}
        == frozen_defines
        for case in native_cases
    )
    assert len(document["source_mutation_ledger"]) >= 3
    assert all(row["witness_case"] for row in document["source_mutation_ledger"])
    assert "kCases" in INCLUDE.read_text()


def test_bitEffects_generator_check_and_self_test() -> None:
    snapshot = _authority_snapshot()
    for args in (("--check",), ("--self-test",)):
        result = subprocess.run(
            ["node", str(GENERATOR), *args, "--cpu-root", str(snapshot)],
            cwd=REPOSITORY,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    with tempfile.TemporaryDirectory() as raw:
        clone = pathlib.Path(raw) / "cpu"
        shutil.copytree(snapshot, clone)
        dependency = clone / "src/csl/runtime.js"
        dependency.write_bytes(dependency.read_bytes() + b"\n// unpinned mutation\n")
        result = subprocess.run(
            ["node", str(GENERATOR), "--check", "--cpu-root", str(clone)],
            cwd=REPOSITORY,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "import closure" in result.stderr


def test_bitEffects_materializer_self_test_and_check() -> None:
    self_test = subprocess.run(
        [sys.executable, str(MATERIALIZER), "--self-test"],
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    )
    assert self_test.returncode == 0, self_test.stdout + self_test.stderr
    assert "mutation ledger" in self_test.stdout
    assert "unsafe case name rejected" in self_test.stdout
    assert "non-integer define rejected" in self_test.stdout
    checked = subprocess.run(
        [sys.executable, str(MATERIALIZER), "--check"],
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_bitEffects_include_is_valid_cxx20() -> None:
    compiler = shutil.which("c++") or shutil.which("clang++")
    if compiler is None:
        pytest.skip("C++20 compiler is unavailable")
    with tempfile.TemporaryDirectory() as raw:
        translation_unit = pathlib.Path(raw) / "bitEffects_include_smoke.cpp"
        translation_unit.write_text(
            "#include <array>\n#include <cstdint>\n#include <span>\n#include <string_view>\n"
            '#include "tests/oracles/bitEffects_expected.inc"\n'
            "static_assert(bitEffects_oracle::kCases.size() >= 20);\n"
            "static_assert(bitEffects_oracle::kNativeDirectCases.size() >= 4);\n"
        )
        result = subprocess.run(
            [compiler, "-std=c++20", "-I", str(REPOSITORY), "-fsyntax-only", str(translation_unit)],
            cwd=REPOSITORY,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_bitEffects_test_source_has_no_run_specific_paths() -> None:
    source = pathlib.Path(__file__).read_text()
    forbidden = ("/" + "private/" + "tmp", "/" + "Users/", "noisemaker-cpp-" + "continuation")
    assert all(value not in source for value in forbidden)
