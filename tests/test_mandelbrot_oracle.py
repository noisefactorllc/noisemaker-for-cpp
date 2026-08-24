from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import shutil
import copy
import runpy

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/mandelbrot-parity"
GENERATOR = PACKAGE / "mandelbrot_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_mandelbrot_native_oracle_include.py"
ORACLE = PACKAGE / "mandelbrot-oracles.json"
REPORT = PACKAGE / "mandelbrot-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/mandelbrot_expected.inc"


def _authority() -> pathlib.Path:
    value = os.environ.get("NOISEMAKER_CPU_ROOT")
    if not value or not pathlib.Path(value).is_dir():
        pytest.skip("NOISEMAKER_CPU_ROOT unavailable; authority test skipped")
    return pathlib.Path(value)


def _sidecar(path: pathlib.Path) -> None:
    sidecar = pathlib.Path(f"{path}.sha256")
    assert sidecar.is_file(), sidecar
    assert sidecar.read_text() == f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"


def test_package_and_sidecars_are_exact_and_semantic() -> None:
    for path in (GENERATOR, MATERIALIZER, ORACLE, REPORT, INCLUDE):
        assert path.is_file(), path
        _sidecar(path)
    doc = json.loads(ORACLE.read_text())
    assert doc["schema"] == "noisemaker-for-cpp.mandelbrot.pixel-parity.v1"
    assert doc["program_key"] == "synth/mandelbrot:mandelbrot"
    assert doc["factory"]["name"] == "canonicalFactory252"
    assert doc["provenance"]["cpu_snapshot"]["immutable_snapshot"] is True
    assert len(doc["provenance"]["cpu_snapshot"]["import_closure"]) == 22
    assert len(doc["render_cases"]) >= 6
    assert len(doc["render_cases"]) == 7
    assert doc["comparer_self_tests"] == {
        "dimensions_before_access": True,
        "first_mismatch_reported": True,
        "raw_words_and_rgba8_independent": True,
        "cases": {"good": True, "dimensions": True, "short": True, "long": True,
                   "rgba8_count": True, "rgba8_mismatch": True, "signed_zero": True,
                   "nan_payload": True},
    }
    assert doc["mutation_anchor_cardinality"]["by_group"] == {
        "cross-lane-assignment": 1, "df64-carrier": 2,
        "out-materialization": 10, "iteration-loop": 2,
        "log-sites": 3, "normal-three-sample": 3,
    }
    assert len(doc["mutation_ledger"]) == 21
    assert all(m["independent"] and m["anchor_occurrence_count"] == (2 if m["name"].startswith("out-transform-") else 1) and m["witness_cases"] for m in doc["mutation_ledger"])
    names = {m["name"] for m in doc["mutation_ledger"]}
    assert {"cross-lane-dz-assignment", "out-getPOI-cX", "out-getPOI-cY", "out-transform-re", "out-transform-im", "log-distance-magnitude"} <= names
    for mutant in doc["mutation_ledger"]:
        assert len(mutant["results"]) == len(doc["render_cases"])
        assert len(mutant["result_sha256"]) == 64
        for row in mutant["results"]:
            assert set(row) == {"case", "differs", "changed_float32_lanes", "changed_rgba8_bytes", "float32_witness", "rgba8_witness"}
            assert row["differs"] == (row["changed_float32_lanes"] > 0 or row["changed_rgba8_bytes"] > 0)
            if row["changed_float32_lanes"]:
                assert row["float32_witness"]["expected"] != row["float32_witness"]["actual"]
            else:
                assert row["float32_witness"] is None
            if row["changed_rgba8_bytes"]:
                assert row["rgba8_witness"]["expected"] != row["rgba8_witness"]["actual"]
            else:
                assert row["rgba8_witness"] is None
    for case in doc["render_cases"]:
        n = case["width"] * case["height"] * 4
        assert len(case["expected"]["f32_words_le"]) == n
        assert len(case["expected"]["rgba8_bytes"]) == n
        assert case["input_immutable_exact_bits"] is True


def test_generator_check_self_test_and_materializer_contract() -> None:
    authority = _authority()
    env = os.environ.copy()
    check = subprocess.run(["node", str(GENERATOR), "--check", "--cpu-root", str(authority)], cwd=ROOT, env=env, text=True, capture_output=True)
    assert check.returncode == 0, check.stdout + check.stderr
    self_test = subprocess.run(["node", str(GENERATOR), "--self-test", "--cpu-root", str(authority)], cwd=ROOT, env=env, text=True, capture_output=True)
    assert self_test.returncode == 0, self_test.stdout + self_test.stderr
    materializer = subprocess.run([sys.executable, str(MATERIALIZER), "--self-test"], cwd=ROOT, text=True, capture_output=True)
    assert materializer.returncode == 0, materializer.stdout + materializer.stderr
    assert subprocess.run([sys.executable, str(MATERIALIZER), "--check"], cwd=ROOT, text=True).returncode == 0


def test_materializer_rejects_forged_semantic_fields_even_with_recomputed_payload() -> None:
    module = runpy.run_path(str(MATERIALIZER))
    validate = module["validate"]
    error = module["MaterializationError"]
    source = json.loads(ORACLE.read_text())
    def word_digest(words: list[str]) -> str:
        return hashlib.sha256(b"".join(int(word, 16).to_bytes(4, "little") for word in words)).hexdigest()
    def forge_input_digest(doc: dict) -> None:
        obj = doc["render_cases"][0]["input"]
        obj["f32_words_le"][0] = "0x80000000"
        obj["f32_sha256"] = word_digest(obj["f32_words_le"])
    def forge_expected_digest(doc: dict) -> None:
        obj = doc["render_cases"][0]["expected"]
        obj["f32_words_le"][0] = "0x80000000"
        obj["f32_sha256"] = word_digest(obj["f32_words_le"])
    def forge_rgba_digest(doc: dict) -> None:
        obj = doc["render_cases"][0]["expected"]
        obj["rgba8_bytes"][0] = (obj["rgba8_bytes"][0] + 1) % 256
        obj["rgba8_sha256"] = hashlib.sha256(bytes(obj["rgba8_bytes"])).hexdigest()
    def forge_mirrored_controls(doc: dict) -> None:
        case = doc["render_cases"][0]
        case["time"] = 0.5
        case["bindings"]["time"] = 0.5
    mutations = [
        ("schema version", lambda d: d.__setitem__("schema_version", 2)),
        ("snapshot argument", lambda d: d["provenance"]["cpu_snapshot"].__setitem__("argument", "/tmp/authority")),
        ("cross lane contract", lambda d: d["cross_lane_assignment_profile"].__setitem__("contract", "forged")),
        ("factory hash", lambda d: d["factory"].__setitem__("text_sha256", "0" * 64)),
        ("binding names", lambda d: d["runtime_binding_names"].reverse()),
        ("exactness", lambda d: d["exactness_contract"].__setitem__("tolerance", "1e-5")),
        ("control", lambda d: d["control_group"]["repeatability"].__setitem__("identical_float32", False)),
        ("cross lane", lambda d: d["cross_lane_assignment_profile"].__setitem__("status", "unverified")),
        ("claim authority", lambda d: d["claim_boundaries"].__setitem__("authority", "local reimplementation")),
        ("input words and recomputed digest", forge_input_digest),
        ("expected words and recomputed digest", forge_expected_digest),
        ("RGBA bytes and recomputed digest", forge_rgba_digest),
        ("mirrored controls", forge_mirrored_controls),
        ("unknown input field", lambda d: d["render_cases"][0]["input"].__setitem__("extra", 1)),
        ("unknown mutation field", lambda d: d["mutation_ledger"][0].__setitem__("extra", 1)),
        ("mutation mechanism", lambda d: d["mutation_ledger"][0].__setitem__("mechanism", "uniform perturbation")),
        ("mutation anchor", lambda d: d["mutation_ledger"][0].__setitem__("source_anchor", "forged anchor")),
        ("mutation witness", lambda d: d["mutation_ledger"][0]["results"][1]["float32_witness"].__setitem__("actual", "0x00000000")),
    ]
    for label, mutate in mutations:
        candidate = copy.deepcopy(source)
        mutate(candidate)
        with pytest.raises(error, match="schema|argument|field|contract|provenance|digest|hash|mechanism|Float32|profile|dimension|count"):
            validate(candidate)


def test_generated_include_compiles_as_cxx20() -> None:
    compiler = shutil.which("c++") or shutil.which("clang++")
    if compiler is None:
        pytest.skip("C++ compiler unavailable")
    with tempfile.TemporaryDirectory(prefix="mandelbrot-include-") as raw:
        unit = pathlib.Path(raw) / "smoke.cpp"
        unit.write_text('#include "tests/oracles/mandelbrot_expected.inc"\nint main() { const auto& controls = mandelbrot_oracle::kCases.front().bindings; return static_cast<int>(mandelbrot_oracle::kBindingNames.size() + mandelbrot_oracle::kBindingAbi.size() + controls.iterations); }\n')
        result = subprocess.run([compiler, "-std=c++20", "-I", str(ROOT), "-fsyntax-only", str(unit)], cwd=ROOT, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr


def test_generator_rejects_transitive_mutation_and_nonliteral_import() -> None:
    authority = _authority()
    with tempfile.TemporaryDirectory(prefix="mandelbrot-oracle-") as raw:
        clone = pathlib.Path(raw) / "cpu"
        import shutil
        shutil.copytree(authority, clone)
        runtime = clone / "src/csl/runtime.js"
        runtime.write_text(runtime.read_text() + "\nexport const deliberateMutation = 1\n")
        bad = subprocess.run(["node", str(GENERATOR), "--check", "--cpu-root", str(clone)], cwd=ROOT, text=True, capture_output=True)
        assert bad.returncode != 0
        assert "import closure" in bad.stderr
        runtime.write_text(runtime.read_text() + "\nvoid import(dynamicSpecifier)\n")
        bad_dynamic = subprocess.run(["node", str(GENERATOR), "--check", "--cpu-root", str(clone)], cwd=ROOT, text=True, capture_output=True)
        assert bad_dynamic.returncode != 0
        assert "nonliteral dynamic import" in bad_dynamic.stderr


def test_generator_rejects_literal_extra_import_and_symlink_or_live_roots() -> None:
    authority = _authority()
    with tempfile.TemporaryDirectory(prefix="mandelbrot-oracle-paths-") as raw:
        base = pathlib.Path(raw)
        link = base / "cpp-link"
        link.symlink_to(ROOT, target_is_directory=True)
        escaped = subprocess.run(["node", str(GENERATOR), "--check", "--cpu-root", str(link)], cwd=ROOT, text=True, capture_output=True)
        assert escaped.returncode != 0
        assert "C++ repository" in escaped.stderr
        live = subprocess.run(["node", str(GENERATOR), "--check", "--cpu-root", str(authority)], cwd=ROOT, env={**os.environ, "NOISEMAKER_FOR_CPU": str(authority)}, text=True, capture_output=True)
        assert live.returncode != 0
        assert "immutable snapshot" in live.stderr or "live checkout" in live.stderr
        clone = base / "cpu"
        import shutil
        shutil.copytree(authority, clone)
        dependency = clone / "src/csl/runtime.js"
        dependency.write_text(dependency.read_text() + "\nimport './literal-extra.js'\n")
        (clone / "src/csl/literal-extra.js").write_text("export const literalExtra = 1\n")
        extra = subprocess.run(["node", str(GENERATOR), "--check", "--cpu-root", str(clone)], cwd=ROOT, text=True, capture_output=True)
        assert extra.returncode != 0
        assert "import closure" in extra.stderr
