"""Shared corpus-lane helpers for the JS CPU and C++ CPU drivers.

Everything here was previously inline in ``tests/test_dsl_corpus_parity.py``.
It moved so the parity test, the benchmark contract test, and the two-pass
corpus runner read one authenticated corpus, resolve one CPU authority, and
build one record-to-argv mapping. There is deliberately no second corpus
reader anywhere in the lane.

The relation helpers re-derive ``relationSha256`` in Python from a lane's
emitted relation document. That makes the digest a three-way agreement -- the
C++ driver, the JS runner, and this module each build the canonical byte
stream independently -- rather than one implementation trusted twice.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import unittest
from typing import Any, Iterable

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORPUS = ROOT / "tests/fixtures/dsl/executable-corpus.json"
CORPUS_ORACLE = ROOT / "tests/oracles/dsl_executable_corpus.sha256"
EXCLUSIONS = ROOT / "tests/oracles/dsl_corpus_parity_exclusions.json"
JS_RUNNER = ROOT / "tools/benchmark/run_cpu_case.mjs"

RELATION_SCHEMA = "noisemaker-cpp.plan-relation.v1"
BENCHMARK_SCHEMA = "noisemaker-cpp.cpu-benchmark-result.v1"
DIVERGENCE_SCHEMA = "noisemaker-cpp.corpus-divergence.v1"

# The floors the JS shader lane already uses (BENCHMARK_WARMUPS /
# BENCHMARK_SAMPLES in tools/dsl/shader_benchmark_lib.mjs).
BENCHMARK_WARMUPS = 5
BENCHMARK_SAMPLES = 30

# The measured counter-example behind the passKey rule. The JS CPU pass object
# carries both a display `name` and a census `program`; the C++ `program_key`
# is `<effectId>:<program>`. Keying a cross-lane relation on `name` looks
# entirely reasonable and diverges on all 166 admitted records.
PASS_KEY_COUNTEREXAMPLE = {
    "effectId": "classicNoisedeck/bitEffects",
    "name": "render",
    "program": "bitEffects",
    "passKey": "classicNoisedeck/bitEffects:bitEffects",
}

# The canonical relation separators. Unit separator between a field name, its
# element count, and each element; record separator terminating every field.
_UNIT = "\x1f"
_RECORD = "\x1e"

# Field order is the cross-lane contract. `relationSha256` is excluded because
# it is the digest of everything above it.
RELATION_FIELDS: tuple[str, ...] = (
    "schema",
    "recordId",
    "sourceSha256",
    "stepKinds",
    "effectIds",
    "passKeys",
    "passFormats",
    "reads",
    "routes",
    "finalSurface",
    "dimensions",
    "passCount",
)

_SCALAR_FIELDS = frozenset({"schema", "recordId", "sourceSha256", "finalSurface"})


def resolve_driver(env_name: str, description: str) -> pathlib.Path:
    """Resolve an externally built driver binary from the environment."""
    configured = os.environ.get(env_name)
    if not configured:
        raise unittest.SkipTest(f"{env_name} must point at the external {description} build")
    candidate = pathlib.Path(configured)
    if not (candidate.is_file() and os.access(candidate, os.X_OK)):
        raise AssertionError(f"{env_name} is not an executable file: {candidate}")
    return candidate


def resolve_cpu_root() -> pathlib.Path:
    value = os.environ.get("NOISEMAKER_CPU_ROOT")
    if not value:
        raise unittest.SkipTest("NOISEMAKER_CPU_ROOT must identify the frozen CPU authority")
    root = pathlib.Path(value)
    if not root.is_absolute() or not root.is_dir():
        raise AssertionError("NOISEMAKER_CPU_ROOT must be an absolute directory")
    return root


def load_corpus() -> dict:
    """Load the corpus only through its own authenticated manifest digest."""
    manifest = json.loads(CORPUS.read_text(encoding="utf-8"))
    expected = CORPUS_ORACLE.read_text(encoding="utf-8").strip()
    if manifest["manifestSha256"] != expected:
        raise AssertionError(
            f"corpus manifest digest drift: {manifest['manifestSha256']} != {expected}")
    return manifest


def admitted_records(manifest: dict) -> list[dict]:
    return [item for item in manifest["records"] if item["recordKind"] == "admitted"]


def load_exclusions() -> dict:
    return json.loads(EXCLUSIONS.read_text(encoding="utf-8"))


def record_flags(record: dict, source_path: os.PathLike[str] | str) -> list[str]:
    """The record-to-argv mapping both C++ drivers accept.

    ``repr`` is the float spelling the parity lane has always used for
    ``time`` and ``seed``; it must stay exactly that so the JS runner and both
    C++ drivers receive identical decimal text for the same record.
    """
    options = record["options"]
    return [
        "--source-file", str(source_path),
        "--source-sha256", record["sourceSha256"],
        "--width", str(options["width"]), "--height", str(options["height"]),
        "--time", repr(options["time"]), "--frame", str(options["frame"]),
        "--seed", repr(options["seed"]),
    ]


def _canonical_field(name: str, values: Iterable[str]) -> str:
    items = list(values)
    return f"{name}{_UNIT}{len(items)}" + "".join(f"{_UNIT}{item}" for item in items) + _RECORD


def normalize_relation(document: dict[str, Any]) -> dict[str, Any]:
    """The comparable projection of a lane's relation document.

    ``relationSha256`` is excluded: it is derived, and a field-level diff has
    to be able to name the field that moved rather than two opaque digests.
    """
    missing = [field for field in RELATION_FIELDS if field not in document]
    if missing:
        raise AssertionError(f"relation document is missing {missing}")
    if document["schema"] != RELATION_SCHEMA:
        raise AssertionError(f"unexpected relation schema {document['schema']!r}")
    return {field: document[field] for field in RELATION_FIELDS}


def canonical_relation_bytes(document: dict[str, Any]) -> bytes:
    normalized = normalize_relation(document)
    parts: list[str] = []
    for field in RELATION_FIELDS:
        value = normalized[field]
        if field in _SCALAR_FIELDS:
            parts.append(_canonical_field(field, [str(value)]))
        elif field == "dimensions":
            parts.append(_canonical_field(field, [str(value["width"]), str(value["height"])]))
        elif field == "passCount":
            parts.append(_canonical_field(field, [str(value)]))
        else:
            parts.append(_canonical_field(field, [str(item) for item in value]))
    return "".join(parts).encode("utf-8")


def relation_sha256(document: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_relation_bytes(document)).hexdigest()


def relation_field_diff(left: dict[str, Any], right: dict[str, Any]) -> list[dict[str, Any]]:
    """Field-by-field divergences between two relation documents."""
    normalized_left = normalize_relation(left)
    normalized_right = normalize_relation(right)
    return [
        {"field": field, "js": normalized_left[field], "cpp": normalized_right[field]}
        for field in RELATION_FIELDS
        if normalized_left[field] != normalized_right[field]
    ]


def contains_declared_tail(observed: list[str], declared: list[str]) -> bool:
    """The corpus record's static plan is a containment oracle, never equality.

    ``tools/dsl/generate_executable_corpus.mjs`` builds ``record.plan`` from the
    compatibility rows for the subject effect alone, so it omits the starter
    effect that 138 of the 166 admitted records chain and it hardcodes one
    format spelling. What it does guarantee is that the subject effect's ids
    and pass keys are the tail of the live projection.
    """
    if len(declared) > len(observed):
        return False
    return observed[len(observed) - len(declared):] == declared
