#!/usr/bin/env python3
"""Materialize ``tests/oracles/parallax190_expected.inc`` from the checked
parallax190 JavaScript oracle.

The oracle JSON is the only input. No C++ output participates in any expected
array, and this script never renders anything itself -- it transcribes.

Usage::

    python3 tools/glslcpp/generate_parallax_native_oracle_include.py --write
    python3 tools/glslcpp/generate_parallax_native_oracle_include.py --check
    python3 tools/glslcpp/generate_parallax_native_oracle_include.py --self-test

``--self-test`` exercises the transcription helpers against hand-computed
expectations, so a green ``--check`` is not the only thing standing behind the
generated file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

REPOSITORY = pathlib.Path(__file__).resolve().parents[2]
ORACLE = REPOSITORY / "docs/port-engineering/counted-for-parity/parallax190-oracles.json"
TARGET = REPOSITORY / "tests/oracles/parallax190_expected.inc"
PROGRAM_KEY = "filter/parallax:parallax"
SCHEMA = "parallax190-oracles-v1"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"


class MaterializationError(RuntimeError):
    """The oracle payload does not satisfy the contract this file transcribes."""


def _sidecar_digest(path: pathlib.Path) -> str:
    text = (path.parent / f"{path.name}.sha256").read_text(encoding="utf-8")
    return text.split()[0]


def load_oracle() -> dict:
    payload_bytes = ORACLE.read_bytes()
    digest = hashlib.sha256(payload_bytes).hexdigest()
    if digest != _sidecar_digest(ORACLE):
        raise MaterializationError("parallax190-oracles.json does not match its sidecar")
    payload = json.loads(payload_bytes)
    if payload.get("schema") != SCHEMA:
        raise MaterializationError(f"unexpected schema {payload.get('schema')!r}")
    if payload.get("program_key") != PROGRAM_KEY:
        raise MaterializationError(f"unexpected program key {payload.get('program_key')!r}")
    if payload.get("corpus_revision") != CORPUS_REVISION:
        raise MaterializationError("corpus revision drift")
    if not payload.get("cases"):
        raise MaterializationError("oracle carries no cases")
    payload["_sha256"] = digest
    return payload


def word_rows(words: list[str], per_row: int = 8) -> str:
    """Eight hex words per line, each with the ``U`` suffix C++ needs."""
    lines = []
    for start in range(0, len(words), per_row):
        chunk = words[start:start + per_row]
        lines.append("    " + " ".join(f"{value}U," for value in chunk))
    return "\n".join(lines)


def byte_rows(values: list[int], per_row: int = 16) -> str:
    lines = []
    for start in range(0, len(values), per_row):
        chunk = values[start:start + per_row]
        lines.append("    " + " ".join(f"{value}U," for value in chunk))
    return "\n".join(lines)


def render(payload: dict) -> str:
    cases = payload["cases"]
    ledger = payload["mutation_ledger"]
    binding_names = payload["binding_names"]

    out: list[str] = []
    add = out.append
    add("")
    add("// Generated from the checked canonical JavaScript parallax oracle.")
    add("// Do not edit; C++ output never participates in these expected")
    add("// arrays.")
    add("//")
    add("// filter/parallax:parallax is typed row 190. It shipped WITHOUT an")
    add("// oracle package and was wrong: the JavaScript's `var prevUV =")
    add("// rayUV` aliases one PooledFloat32Array and the march writes rayUV")
    add("// in place, so the refinement `mix(rayUV, prevUV, w)` is")
    add("// mix(x, x, w) == x -- a no-op. The emitter value-copied and")
    add("// performed the interpolation. See DEFECTS-FOUND.md item 6.")
    add("//")
    add("// The `refinement-copy-restored` mutant below IS that emission.")
    add("// Its witness set is the regression guard. Note that the")
    add("// `full-basic` case does NOT witness it -- the defect was invisible")
    add("// at that shape, which is exactly why the case is kept.")
    add("#pragma once")
    add("")
    add("namespace parallax190_oracle {")
    add("")
    add(f'inline constexpr std::string_view kOracleSha256 = "{payload["_sha256"]}";')
    add(f'inline constexpr std::string_view kProgramKey = "{PROGRAM_KEY}";')
    add(f'inline constexpr std::string_view kCorpusRevision = "{CORPUS_REVISION}";')
    add(f'inline constexpr std::string_view kFactoryTextSha256 = "{payload["factory"]["text_sha256"]}";')
    add(f"inline constexpr std::size_t kCaseCount = {len(cases)}U;")
    add(f"inline constexpr std::size_t kBindingCount = {len(binding_names)}U;")
    add("")
    add(f"inline constexpr std::array<std::string_view, {len(binding_names)}> kBindingNames{{{{")
    add("    " + ", ".join(f'"{name}"' for name in binding_names) + ",")
    add("}};")
    add("")

    for index, case in enumerate(cases):
        for label, record in (("Input", case["input"]), ("Height", case["height_map"])):
            words = record["f32_words_le"]
            add(f"inline constexpr std::array<std::uint32_t, {len(words)}> "
                f"kCase{index}{label}Words{{{{")
            add(word_rows(words))
            add("}};")
            add("")
        expected = case["expected"]
        words = expected["f32_words_le"]
        add(f"inline constexpr std::array<std::uint32_t, {len(words)}> "
            f"kCase{index}ExpectedWords{{{{")
        add(word_rows(words))
        add("}};")
        add("")
        rgba8 = expected["rgba8_bytes"]
        add(f"inline constexpr std::array<std::uint8_t, {len(rgba8)}> "
            f"kCase{index}ExpectedRgba8{{{{")
        add(byte_rows(rgba8))
        add("}};")
        add("")

    add("struct CaseView {")
    add("  std::string_view name;")
    add("  std::string_view route;")
    add("  std::size_t width;")
    add("  std::size_t height;")
    add("  std::size_t input_width;")
    add("  std::size_t input_height;")
    add("  std::size_t height_width;")
    add("  std::size_t height_height;")
    add("  std::string_view input_f32_sha256;")
    add("  std::string_view height_f32_sha256;")
    add("  std::string_view expected_f32_sha256;")
    add("  std::string_view expected_rgba8_sha256;")
    add("  std::span<const std::uint32_t> input_words;")
    add("  std::span<const std::uint32_t> height_words;")
    add("  std::span<const std::uint32_t> expected_words;")
    add("  std::span<const std::uint8_t> expected_rgba8;")
    add("  std::uint32_t tile_offset_x_word;")
    add("  std::uint32_t tile_offset_y_word;")
    add("  std::uint32_t full_resolution_x_word;")
    add("  std::uint32_t full_resolution_y_word;")
    add("  std::uint32_t direction_x_word;")
    add("  std::uint32_t direction_y_word;")
    add("  std::uint32_t direction_z_word;")
    add("  std::uint32_t pivot_word;")
    add("};")
    add("")
    add(f"inline constexpr std::array<CaseView, {len(cases)}> kCases{{{{")
    for index, case in enumerate(cases):
        bindings = case["bindings"]
        add("  CaseView{"
            f'"{case["name"]}", "{case["route"]}", '
            f'{case["width"]}U, {case["height"]}U, '
            f'{case["input"]["width"]}U, {case["input"]["height"]}U, '
            f'{case["height_map"]["width"]}U, {case["height_map"]["height"]}U, '
            f'"{case["input"]["f32_sha256"]}", '
            f'"{case["height_map"]["f32_sha256"]}", '
            f'"{case["expected"]["f32_sha256"]}", '
            f'"{case["expected"]["rgba8_sha256"]}", '
            f"kCase{index}InputWords, kCase{index}HeightWords, "
            f"kCase{index}ExpectedWords, kCase{index}ExpectedRgba8, "
            f'{bindings["tileOffset"][0]}U, {bindings["tileOffset"][1]}U, '
            f'{bindings["fullResolution"][0]}U, {bindings["fullResolution"][1]}U, '
            f'{bindings["direction"][0]}U, {bindings["direction"][1]}U, '
            f'{bindings["direction"][2]}U, {bindings["pivot"]}U}},')
    add("}};")
    add("")
    add("// One row per (mutant, case). `witnesses` is true where the mutant's")
    add("// render differs from the canonical render -- measured by the oracle")
    add("// generator, transcribed here, never recomputed natively.")
    add("struct MutantWitnessView {")
    add("  std::string_view mutant;")
    add("  std::string_view case_name;")
    add("  bool witnesses;")
    add("  std::size_t changed_lane_count;")
    add("};")
    add("")
    witnesses = [(entry["name"], row["case"], row["differs"], row["changed_lane_count"])
                 for entry in ledger for row in entry["rows"]]
    add(f"inline constexpr std::array<MutantWitnessView, {len(witnesses)}> "
        "kMutantWitnesses{{")
    for mutant, case_name, differs, changed in witnesses:
        add(f'  MutantWitnessView{{"{mutant}", "{case_name}", '
            f'{"true" if differs else "false"}, {changed}U}},')
    add("}};")
    add("")
    add("// The defect guard, named so a native test can assert on it directly")
    add("// rather than rediscovering which mutant matters.")
    add('inline constexpr std::string_view kDefectMutant = "refinement-copy-restored";')
    add('inline constexpr std::string_view kInvariantMutant = "refinement-weight-negated";')
    add('inline constexpr std::string_view kNonWitnessingCase = "full-basic";')
    add("")
    add("}  // namespace parallax190_oracle")
    add("")
    return "\n".join(out)


def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    checks.append(("word_rows emits eight per line with the U suffix",
                   word_rows(["0x1U".replace("U", "")] * 0) == ""))
    rows = word_rows([f"0x0000000{i}" for i in range(9)])
    checks.append(("word_rows wraps after eight", len(rows.split("\n")) == 2))
    checks.append(("word_rows suffixes every word",
                   rows.count("U,") == 9))
    checks.append(("word_rows indents four spaces",
                   all(line.startswith("    ") for line in rows.split("\n"))))
    byte_lines = byte_rows(list(range(17)))
    checks.append(("byte_rows wraps after sixteen", len(byte_lines.split("\n")) == 2))
    checks.append(("byte_rows suffixes every byte", byte_lines.count("U,") == 17))

    payload = load_oracle()
    cases = payload["cases"]
    checks.append(("oracle carries the six designed cases", len(cases) == 6))
    checks.append(("every case names a route",
                   all(case["route"] in {"full", "tile"} for case in cases)))
    checks.append(("expected lane count matches width*height*4",
                   all(len(case["expected"]["f32_words_le"])
                       == case["width"] * case["height"] * 4 for case in cases)))
    checks.append(("expected byte count matches lane count",
                   all(len(case["expected"]["rgba8_bytes"])
                       == len(case["expected"]["f32_words_le"]) for case in cases)))
    checks.append(("input lane count matches its own extent",
                   all(len(case["input"]["f32_words_le"])
                       == case["input"]["width"] * case["input"]["height"] * 4
                       for case in cases)))
    checks.append(("height lane count matches its own extent",
                   all(len(case["height_map"]["f32_words_le"])
                       == case["height_map"]["width"] * case["height_map"]["height"] * 4
                       for case in cases)))
    checks.append(("case names are unique",
                   len({case["name"] for case in cases}) == len(cases)))
    checks.append(("alpha is uniformly 1.0 in every case",
                   all(case["expected"]["alpha_f32_word"] == "0x3f800000" for case in cases)))
    checks.append(("at least one tile-route case exists",
                   any(case["route"] == "tile" for case in cases)))
    checks.append(("mismatched-maps really has differing map extents",
                   any(case["input"]["width"] != case["height_map"]["width"]
                       for case in cases)))

    ledger = payload["mutation_ledger"]
    defect = next((entry for entry in ledger if entry["name"] == "refinement-copy-restored"), None)
    checks.append(("the defect mutant is in the ledger", defect is not None))
    if defect is not None:
        checks.append(("the defect mutant is discriminated by at least one case",
                       len(defect["discriminating_cases"]) > 0))
        checks.append(("full-basic does NOT witness the defect mutant",
                       "full-basic" not in defect["discriminating_cases"]))
        checks.append(("the defect mutant's witnessing rows carry a nonzero lane count",
                       all(row["changed_lane_count"] > 0
                           for row in defect["rows"] if row["differs"])))
        checks.append(("the defect mutant's non-witnessing rows carry a zero lane count",
                       all(row["changed_lane_count"] == 0
                           for row in defect["rows"] if not row["differs"])))
    invariant = next((entry for entry in ledger
                      if entry["name"] == "refinement-weight-negated"), None)
    checks.append(("the invariant mutant is in the ledger", invariant is not None))
    if invariant is not None:
        checks.append(("the invariant mutant moves no lane on any case",
                       all(not row["differs"] for row in invariant["rows"])))
        checks.append(("the invariant mutant is budgeted as an invariant",
                       invariant["budgeted_as"] == "measured invariant"))
    checks.append(("every non-invariant ledger entry discriminates something",
                   all(entry["discriminating_cases"]
                       for entry in ledger
                       if entry["budgeted_as"] != "measured invariant")))
    checks.append(("every ledger row names a real case",
                   all(row["case"] in {case["name"] for case in cases}
                       for entry in ledger for row in entry["rows"])))
    checks.append(("the ledger covers every case for every mutant",
                   all(len(entry["rows"]) == len(cases) for entry in ledger)))

    alias = payload["alias_contract"]
    checks.append(("the alias contract names the declaration",
                   alias["declaration"] == "var prevUV = rayUV;"))
    checks.append(("the alias contract records the in-place update",
                   "rayUV[0] =" in alias["in_place_update"]))
    checks.append(("the alias contract records the refinement write",
                   "mix(rayUV, prevUV, w)" in alias["refinement_write"]))

    checks.append(("the comparer self-tests all passed in the generator",
                   all(row["pass"] for row in payload["comparer_self_tests"])))
    checks.append(("a control is recorded",
                   len(payload["controls"]) >= 1))
    checks.append(("external time and seed are inert",
                   payload["controls"][0]["result"] == "identical"))

    rendered = render(payload)
    checks.append(("rendered include opens the namespace",
                   "namespace parallax190_oracle {" in rendered))
    checks.append(("rendered include closes the namespace",
                   rendered.rstrip().endswith("}  // namespace parallax190_oracle")))
    checks.append(("rendered include carries every case name",
                   all(f'"{case["name"]}"' in rendered for case in cases)))
    checks.append(("rendered include names the defect mutant",
                   "kDefectMutant" in rendered))
    checks.append(("rendered include contains no C++ comment about editing it",
                   "Do not edit" in rendered))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    print(f"{len(checks) - len(failed)}/{len(checks)} self-test checks passed")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()

    if arguments.self_test:
        return self_test()

    payload = load_oracle()
    rendered = render(payload)
    if arguments.write:
        TARGET.write_text(rendered, encoding="utf-8")
        digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        (TARGET.parent / f"{TARGET.name}.sha256").write_text(
            f"{digest}  {TARGET.name}\n", encoding="utf-8")
        print(f"generate_parallax_native_oracle_include: wrote {TARGET.name} "
              f"({len(rendered)} bytes, {digest})")
        return 0

    if not TARGET.exists():
        print(f"generate_parallax_native_oracle_include: {TARGET} is missing", file=sys.stderr)
        return 1
    actual = TARGET.read_text(encoding="utf-8")
    if actual != rendered:
        print("generate_parallax_native_oracle_include: include drift", file=sys.stderr)
        return 1
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    if _sidecar_digest(TARGET) != digest:
        print("generate_parallax_native_oracle_include: sidecar drift", file=sys.stderr)
        return 1
    print("generate_parallax_native_oracle_include: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
