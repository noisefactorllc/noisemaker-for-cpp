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
PACKAGE = REPOSITORY / "docs/port-engineering/kaleido-parity"
GENERATOR = PACKAGE / "kaleido187_oracle_generator.mjs"
MATERIALIZER = REPOSITORY / "tools/glslcpp/generate_kaleido_native_oracle_include.py"
ORACLE = PACKAGE / "kaleido187-oracles.json"
REPORT = PACKAGE / "kaleido187-oracle-report.md"
INCLUDE = REPOSITORY / "tests/oracles/kaleido187_expected.inc"


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


def test_kaleido_oracle_package_is_self_consistent() -> None:
    for path in (GENERATOR, MATERIALIZER, ORACLE, REPORT, INCLUDE):
        assert path.is_file(), path
        sidecar = _sidecar(path)
        assert sidecar.is_file(), sidecar
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        assert sidecar.read_text() == f"{expected}  {path.name}\n"

    document = json.loads(ORACLE.read_text())
    assert document["schema"] == "noisemaker-for-cpp.kaleido187.pixel-parity.v1"
    assert document["program_key"] == "classicNoisedeck/kaleido:kaleido"
    assert document["factory"]["name"] == "canonicalFactory9"
    assert document["runtime_binding_abi"]["wrap"] == "bool"
    assert document["write_only_tables_axis"]["oracle_discriminable"] is False
    assert len(document["render_cases"]) >= 3
    rows = document["native_expected_rejection"]
    assert len(rows) == 11
    assert [row["binding_name"] for row in rows] == document["runtime_binding_names"]
    assert all(row["status"] == "pending_shared_native_integration" for row in rows)
    include_text = INCLUDE.read_text()
    assert "kNativeExpectedRejections" in include_text
    assert include_text.count("NativeExpectedAbiCategory") >= 1
    assert all(row["binding_name"] in include_text for row in rows)


def test_kaleido_generator_check_requires_authority_snapshot() -> None:
    snapshot = _authority_snapshot()
    assert subprocess.run(
        ["node", str(GENERATOR), "--check", "--cpu-root", str(snapshot)],
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    ).returncode == 0

def test_generator_rejects_modified_unpinned_runtime_dependency() -> None:
    snapshot = _authority_snapshot()
    with tempfile.TemporaryDirectory() as raw:
        clone = pathlib.Path(raw) / "cpu"
        shutil.copytree(snapshot, clone)
        dependency = clone / "src/csl/runtime.js"
        dependency.write_bytes(dependency.read_bytes() + b"\n// deliberate unpinned dependency mutation\n")
        result = subprocess.run(
            ["node", str(GENERATOR), "--check", "--cpu-root", str(clone)],
            cwd=REPOSITORY,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "import closure" in result.stderr


def test_generator_self_tests_cover_closure_and_pending_abi_contract() -> None:
    snapshot = _authority_snapshot()
    generator = subprocess.run(
        ["node", str(GENERATOR), "--self-test", "--cpu-root", str(snapshot)],
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    )
    assert generator.returncode == 0
    assert "modified unpinned dependency rejected" in generator.stdout
    assert "missing import-closure entry rejected" in generator.stdout
    assert "extra import-closure entry rejected" in generator.stdout
    assert "native ABI table is complete and pending" in generator.stdout


def test_materializer_self_tests_and_check_are_standalone() -> None:
    materializer = subprocess.run(
        [sys.executable, str(MATERIALIZER), "--self-test"],
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    )
    assert materializer.returncode == 0
    assert "semantic mandatory fields rejected" in materializer.stdout
    assert "bool-as-int rejected" in materializer.stdout
    assert "mutation count sabotage rejected" in materializer.stdout
    assert "native ABI table sabotage rejected" in materializer.stdout
    assert "semantic carrier sabotage rejected" in materializer.stdout
    assert "mutation ledger exactness rejected" in materializer.stdout
    assert subprocess.run(
        [sys.executable, str(MATERIALIZER), "--check"],
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    ).returncode == 0

def test_generated_include_is_valid_cxx20_and_exposes_native_table() -> None:
    compiler = shutil.which("c++") or shutil.which("clang++")
    if compiler is None:
        pytest.skip("C++20 compiler is unavailable")
    with tempfile.TemporaryDirectory() as raw:
        translation_unit = pathlib.Path(raw) / "kaleido_include_smoke.cpp"
        translation_unit.write_text(
            "#include <array>\n"
            "#include <cstddef>\n"
            "#include <cstdint>\n"
            "#include <span>\n"
            "#include <string_view>\n"
            "#include <type_traits>\n"
            '#include "tests/oracles/kaleido187_expected.inc"\n'
            "static_assert(kaleido187_oracle::kControls.size() == 4);\n"
            "static_assert(kaleido187_oracle::kNativeExpectedRejections.size() == 11);\n"
            "static_assert(std::is_same_v<decltype(kaleido187_oracle::kNativeExpectedRejections[0].expected_category), kaleido187_oracle::NativeExpectedAbiCategory>);\n"
        )
        result = subprocess.run(
            [compiler, "-std=c++20", "-I", str(REPOSITORY), "-fsyntax-only", str(translation_unit)],
            cwd=REPOSITORY,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_test_source_has_no_run_specific_paths() -> None:
    source = pathlib.Path(__file__).read_text()
    forbidden = ("/" + "private/" + "tmp", "/" + "Users/", "noisemaker-cpp-" + "continuation")
    assert all(value not in source for value in forbidden)
