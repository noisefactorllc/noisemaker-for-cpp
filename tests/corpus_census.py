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
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/0ed489ec46842bffba33ee2ec65a218b6dda51f5"
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
    """Every vendored program except a scatter member (null runtime key), sorted."""
    return sorted(entry["program_key"] for entry in manifest_programs() if entry["runtime_key"] is not None)


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
# expansion are measured on this projection of the live slice.
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
    """A deep copy of a typed-slice spec with every expansion row removed.

    Fails loudly unless the result is exactly the pre-expansion 211-row slice,
    so a projection can never silently drift from the state it reconstructs.
    """
    import copy
    import hashlib

    result = copy.deepcopy(spec)
    result["programs"] = [item for item in result["programs"] if item["program_key"] not in expansion_keys()]
    keys = [item["program_key"] for item in result["programs"]]
    digest = hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest()
    if digest != PRE_EXPANSION_TYPED_KEY_SHA256:
        raise AssertionError(f"pre-expansion projection drift: {len(keys)} rows, key sha {digest}")
    return result


def pre_expansion_manifest(manifest: dict) -> dict:
    """A corpus manifest document with every expansion program removed (the 212-program corpus)."""
    import copy

    result = copy.deepcopy(manifest)
    result["programs"] = [item for item in result["programs"] if item["program_key"] not in expansion_keys()]
    if len(result["programs"]) != 212:
        raise AssertionError(f"pre-expansion corpus projection drift: {len(result['programs'])} programs")
    return result
