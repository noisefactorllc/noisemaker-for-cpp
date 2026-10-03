"""Corpus cardinalities derived from the committed vendored/pending split.

Tests that used to pin "212 programs / 211 typed rows / 213 catalog rows /
167 effects" read those facts from here instead. Every value is computed from
the pinned corpus manifest and ``pending.json`` (see
``tools/glslcpp/corpus_ratchet.py``), whose closure over the JS authority's
program set ``check_corpus --check`` enforces, so a count can never silently
drift away from what the authority ships.
"""

from __future__ import annotations

import functools
import hashlib
import json
import pathlib

from tools.glslcpp import check_corpus

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION
HISTORICAL_REVISION = "0ed489ec46842bffba33ee2ec65a218b6dda51f5"
HISTORICAL_CORPUS = ROOT / "tools/glslcpp/corpus" / HISTORICAL_REVISION
_HISTORICAL_DOCUMENT_SHA256 = {
    "manifest.json": "1feb7bfa85b0ede3bb07fa51e612c33707bce5dad0c621e75c6a644b6b3dcc86",
    "metadata.json": "b6055f69cbe503b562ec939a7654eb87e7dd335837514fe8cc7861a8738fe382",
    "pending.json": "fffd7422e304e57aad01941151f315e187edb2b5954d0e360d46b93e64293601",
}
_RETIRED_ROWS = (
    {"defines": {}, "program_key": "filter/bc:bc"},
    {"defines": {}, "linear_srgb_lane_index_profile": "linear-srgb-colorspace-lane-index-v1",
     "program_key": "filter/colorspace:colorspace"},
    {"defines": {}, "program_key": "filter/hs:hs"},
)


def historical_document(name: str) -> dict:
    """Read an immutable historical authority document, checking its original bytes."""
    raw = (HISTORICAL_CORPUS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != _HISTORICAL_DOCUMENT_SHA256[name]:
        raise AssertionError(f"historical authority document drift: {name}")
    return json.loads(raw)
# The two frozen-fragment programs dispatched through hand-written legacy
# factories as well as their typed rows (src/generated/filter_invert.cpp,
# synth_solid.cpp): the catalog carries both physical rows for each.
LEGACY_DUPLICATE_KEYS = ("filter/invert:inv", "synth/solid:solid")


@functools.lru_cache(maxsize=None)
def manifest_programs() -> tuple[dict, ...]:
    return tuple(json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))["programs"])


@functools.lru_cache(maxsize=None)
def pending() -> dict:
    return json.loads((CORPUS / "pending.json").read_text(encoding="utf-8"))


def vendored_count() -> int:
    return len(manifest_programs())


def pending_count() -> int:
    return len(pending()["pending"])


def authority_program_count() -> int:
    return len(pending()["authority"]["programs"])


def metadata_effect_count() -> int:
    return len({entry["effect_id"] for entry in manifest_programs()})


def typed_keys() -> list[str]:
    """Fragment factory keys, excluding scatter and the exact whole-pass mesh route."""
    return sorted(entry["program_key"] for entry in manifest_programs()
                  if entry["runtime_key"] is not None
                  and entry["program_key"] != "render/meshRender:render")


def typed_count() -> int:
    return len(typed_keys())


def mrt_keys() -> list[str]:
    return sorted(entry["program_key"] for entry in manifest_programs() if len(entry["outputs"]) > 1)


def single_output_typed_count() -> int:
    return typed_count() - len(set(mrt_keys()) & set(typed_keys()))


def catalog_row_count() -> int:
    """Physical single-output KernelFactory rows: typed rows plus the legacy duplicates."""
    return single_output_typed_count() + len(LEGACY_DUPLICATE_KEYS)


def ordinal(key: str) -> int:
    """A program's live sorted ordinal in the typed slice (its `typed_<n>` namespace)."""
    return typed_keys().index(key)


def typed_key_sha256() -> str:
    import hashlib

    return hashlib.sha256(("\n".join(typed_keys()) + "\n").encode()).hexdigest()


# The typed slice immediately before the corpus expansion that introduced the
# vendored/pending ratchet: 211 rows with this exact sorted key-list digest.
# Milestone reconstructions and "row landed at ordinal N" pins that predate the
# expansion are measured on the explicitly reconstructed historical slice.
PRE_EXPANSION_TYPED_KEY_SHA256 = "29a148b26cfe4f550ac82325810655eb0e5ffad2c3a4e5241e42600bac9f76c1"


@functools.lru_cache(maxsize=None)
def expansion_keys() -> frozenset[str]:
    """Corpus programs vendored by the authority-projected expansion.

    Derived, not listed: exactly the vendored programs whose effect metadata was
    projected from the authority record (metadata provenance
    ``authority_projected``) rather than carried by the pre-expansion snapshot.
    """
    metadata = json.loads((CORPUS / "metadata.json").read_text(encoding="utf-8"))
    projected = set(metadata["provenance"].get("authority_projected", []))
    return frozenset(entry["program_key"] for entry in manifest_programs() if entry["effect_id"] in projected)


def without_expansion(spec: dict) -> dict:
    """Reconstruct the historical pre-expansion slice from the live carriers.

    Restore only the three explicitly retired rows from the old authority;
    later authority additions and expansion rows do not belong to this slice.
    The original 211-row key digest remains mandatory.
    """
    import copy
    import hashlib

    if spec.get("revision") not in {HISTORICAL_REVISION, CORPUS.name}:
        raise AssertionError("historical slice projection requires a known authority revision")
    result = copy.deepcopy(spec)
    historical = historical_document("manifest.json")
    known = (set(typed_keys()) if spec["revision"] != HISTORICAL_REVISION else
             {item["program_key"] for item in historical["programs"]
              if item["runtime_key"] is not None})
    unknown = {item["program_key"] for item in result["programs"]} - known
    if unknown:
        raise AssertionError(f"historical slice projection contains unknown authority keys: {sorted(unknown)}")
    metadata = historical_document("metadata.json")
    projected = set(metadata["provenance"].get("authority_projected", []))
    historical_keys = {item["program_key"] for item in historical["programs"]
                       if item["runtime_key"] is not None and item["effect_id"] not in projected}
    result["programs"] = [item for item in result["programs"]
                          if item["program_key"] in historical_keys]
    if spec["revision"] != HISTORICAL_REVISION:
        present = {item["program_key"] for item in result["programs"]}
        result["programs"].extend(copy.deepcopy(item) for item in _RETIRED_ROWS
                                  if item["program_key"] not in present)
    result["programs"].sort(key=lambda item: item["program_key"])
    result["revision"] = HISTORICAL_REVISION
    result["compatibility_transforms"]["filter/corrupt:corrupt"] = "corrupt-sample-uv-alias-v1"
    keys = [item["program_key"] for item in result["programs"]]
    digest = hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest()
    if digest != PRE_EXPANSION_TYPED_KEY_SHA256:
        raise AssertionError(f"pre-expansion projection drift: {len(keys)} rows, key sha {digest}")
    return result


def pre_expansion_manifest(manifest: dict) -> dict:
    """Return the original 212-program corpus, independently of the live census."""
    import copy

    revision = manifest.get("revision")
    if revision not in {HISTORICAL_REVISION, CORPUS.name}:
        raise AssertionError("historical manifest projection requires a known authority revision")
    pinned = json.loads((ROOT / "tools/glslcpp/corpus" / revision / "manifest.json").read_text())
    if manifest != pinned:
        raise AssertionError("historical manifest projection requires the exact pinned manifest")
    result = copy.deepcopy(historical_document("manifest.json"))
    projected = set(historical_document("metadata.json")["provenance"].get("authority_projected", []))
    result["programs"] = [item for item in result["programs"] if item["effect_id"] not in projected]
    if len(result["programs"]) != 212:
        raise AssertionError(f"pre-expansion corpus projection drift: {len(result['programs'])} programs")
    return result
