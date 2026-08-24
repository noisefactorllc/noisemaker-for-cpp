"""Validate the pinned GLSL corpus without a network, Node, or sibling tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
from collections import Counter
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from tools.glslcpp.frontend import FrontendError, parse_program
    from tools.glslcpp.frontend.preprocess import normalize
else:
    from .frontend import FrontendError, parse_program
    from .frontend.preprocess import normalize


SCHEMA = 1
REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
_ROOT = pathlib.Path(__file__).resolve().parents[2]
_CORPUS_RELATIVE = pathlib.PurePosixPath("tools/glslcpp/corpus") / REVISION
_ADAPTERS = frozenset({
    "classicNoisedeck/fractal:fractal",
    "filter/historicPalette:historicPalette",
    "filter/palette:palette",
    "synth/julia:julia",
})
_WINDOWS_DEVICES = frozenset({"CON", "PRN", "AUX", "NUL", "CLOCK$",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
    *(f"COM{suffix}" for suffix in "¹²³"), *(f"LPT{suffix}" for suffix in "¹²³")})


class CorpusError(ValueError):
    pass


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _corpus_root(repository: pathlib.Path) -> pathlib.Path:
    return repository.resolve() / _CORPUS_RELATIVE


def _load_json(path: pathlib.Path, label: str) -> dict[str, Any]:
    def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise CorpusError(f"{label}: duplicate JSON member {key!r}")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, CorpusError) as error:
        raise CorpusError(f"{label}: invalid JSON: {error}") from error
    if not isinstance(value, dict):
        raise CorpusError(f"{label}: expected object")
    return value


def _safe_source_path(root: pathlib.Path, relative: object, key: str) -> pathlib.Path:
    if not isinstance(relative, str) or not relative:
        raise CorpusError(f"{key}: source path must be a nonempty string")
    posix = pathlib.PurePosixPath(relative)
    windows = pathlib.PureWindowsPath(relative)
    parts = posix.parts
    if (relative != posix.as_posix() or "\\" in relative or ":" in relative or posix.is_absolute() or windows.is_absolute()
            or any(part in ("", ".", "..") for part in parts)
            or any(part.split(".", 1)[0].rstrip(" .").upper() in _WINDOWS_DEVICES for part in parts)):
        raise CorpusError(f"{key}: unsafe source path")
    path = root / pathlib.Path(*parts)
    try:
        resolved = path.resolve(strict=False)
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise CorpusError(f"{key}: source path escapes corpus") from error
    return path


def _walk_regular_files(root: pathlib.Path) -> set[str]:
    if root.is_symlink():
        raise CorpusError("corpus source root must not be a symlink")
    files: set[str] = set()
    for current, directories, names in os.walk(root, followlinks=False):
        current_path = pathlib.Path(current)
        if current_path.is_symlink():
            raise CorpusError("corpus source tree contains a symlink")
        for directory in directories:
            if (current_path / directory).is_symlink():
                raise CorpusError("corpus source tree contains a symlink")
        for name in names:
            path = current_path / name
            if path.is_symlink():
                raise CorpusError("corpus source tree contains a symlink")
            if not path.is_file():
                raise CorpusError("corpus source tree contains a non-file entry")
            files.add(path.relative_to(root).as_posix())
    return files


def _validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if set(manifest) != {"schema", "revision", "metadata_sha256", "programs"}:
        raise CorpusError("manifest: unexpected top-level fields")
    if manifest.get("schema") != SCHEMA or manifest.get("revision") != REVISION:
        raise CorpusError("manifest: unsupported schema or revision")
    metadata_hash = manifest.get("metadata_sha256")
    if not isinstance(metadata_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", metadata_hash):
        raise CorpusError("manifest: invalid metadata hash")
    programs = manifest.get("programs")
    if not isinstance(programs, list) or len(programs) != 212:
        raise CorpusError("manifest: expected exactly 212 programs")
    required = {"effect_id", "program", "program_key", "status", "source", "raw_bytes", "raw_sha256",
                "normalized_bytes", "normalized_sha256", "outputs", "varyings", "pass_index", "pass_name", "runtime_key"}
    keys: set[str] = set()
    sources: set[str] = set()
    runtime_keys: set[str] = set()
    for entry in programs:
        if not isinstance(entry, dict) or set(entry) != required:
            raise CorpusError("manifest: invalid program fields")
        key = entry["program_key"]
        if (not isinstance(entry["effect_id"], str) or not isinstance(entry["program"], str)
                or not isinstance(key, str) or key in keys or key != f"{entry['effect_id']}:{entry['program']}"):
            raise CorpusError("manifest: duplicate or malformed program key")
        keys.add(key)
        if entry["source"] in sources:
            raise CorpusError(f"{key}: duplicate source path")
        sources.add(entry["source"])
        if entry["status"] not in ("generated", "adapter"):
            raise CorpusError(f"{key}: invalid status")
        if (type(entry["raw_bytes"]) is not int or entry["raw_bytes"] < 0
                or type(entry["normalized_bytes"]) is not int or entry["normalized_bytes"] < 0
                or not all(isinstance(entry[field], str) and re.fullmatch(r"[0-9a-f]{64}", entry[field])
                           for field in ("raw_sha256", "normalized_sha256"))):
            raise CorpusError(f"{key}: invalid hash or size")
        if (not isinstance(entry["outputs"], list) or not isinstance(entry["varyings"], list)
                or not all(isinstance(value, str) for value in entry["outputs"] + entry["varyings"])
                or len(set(entry["outputs"])) != len(entry["outputs"])
                or len(set(entry["varyings"])) != len(entry["varyings"])
                or set(entry["outputs"]) & set(entry["varyings"])
                or type(entry["pass_index"]) is not int or entry["pass_index"] < 0 or not isinstance(entry["pass_name"], str)
                or (entry["runtime_key"] is not None and not isinstance(entry["runtime_key"], str))):
            raise CorpusError(f"{key}: outputs and varyings must be lists")
        if entry["runtime_key"] is not None:
            if entry["runtime_key"] in runtime_keys:
                raise CorpusError(f"{key}: duplicate runtime key")
            runtime_keys.add(entry["runtime_key"])
    if len(sources) != 212:
        raise CorpusError("manifest: source count gate drift")
    return sorted(programs, key=lambda entry: entry["program_key"])


def _validate_metadata(metadata: dict[str, Any], programs: list[dict[str, Any]]) -> None:
    if set(metadata) != {"schema", "revision", "provenance", "effects"}:
        raise CorpusError("metadata: unexpected top-level fields")
    if metadata.get("schema") != SCHEMA or metadata.get("revision") != REVISION:
        raise CorpusError("metadata: unsupported schema or revision")
    effects = metadata.get("effects")
    if not isinstance(effects, dict) or len(effects) != 167:
        raise CorpusError("metadata: expected exactly 167 effects")
    records_by_key = {entry["program_key"]: entry for entry in programs}
    pass_count = 0
    keyed = 0
    overrides = 0
    for effect_id, effect in sorted(effects.items()):
        if not isinstance(effect_id, str) or not isinstance(effect, dict) or not isinstance(effect.get("passes"), list):
            raise CorpusError(f"metadata: invalid effect {effect_id!r}")
        for index, current_pass in enumerate(effect["passes"]):
            pass_count += 1
            if not isinstance(current_pass, dict) or not isinstance(current_pass.get("program"), str):
                raise CorpusError(f"metadata: invalid pass {effect_id}:{index}")
            key = f"{effect_id}:{current_pass['program']}"
            record = records_by_key.get(key)
            if record is None:
                raise CorpusError(f"{key}: metadata pass has no canonical source")
            if record["pass_index"] != index or record["pass_name"] != current_pass.get("name"):
                raise CorpusError(f"{key}: metadata pass relationship drift")
            if record["runtime_key"] != current_pass.get("key"):
                raise CorpusError(f"{key}: runtime key relationship drift")
            if current_pass.get("key") is not None:
                keyed += 1
    wormhole = effects.get("filter/wormhole", {}).get("passes", [])
    if len(wormhole) < 2 or wormhole[1].get("program") != "deposit" or wormhole[1].get("key") is not None or wormhole[1].get("drawMode") != "points":
        raise CorpusError("filter/wormhole:deposit: expected points draw-op override")
    overrides = 1
    if (pass_count, keyed, overrides) != (212, 211, 1):
        raise CorpusError("metadata: pass/key/override gate drift")


def validate_corpus(repository: pathlib.Path | None = None) -> dict[str, Any]:
    """Fail-closed validation; return only deterministic, relative-path data."""
    repository = (repository or _ROOT).resolve()
    root = _corpus_root(repository)
    if root.is_symlink() or not root.is_dir():
        raise CorpusError("corpus root is missing or is a symlink")
    expected_top_level = {"manifest.json", "metadata.json", "sources"}
    actual_top_level = {entry.name for entry in root.iterdir()}
    if actual_top_level != expected_top_level:
        raise CorpusError(f"corpus top-level file set drift: expected {sorted(expected_top_level)}, got {sorted(actual_top_level)}")
    for name in expected_top_level:
        if (root / name).is_symlink():
            raise CorpusError(f"corpus top-level {name} must not be a symlink")
    if not (root / "manifest.json").is_file() or not (root / "metadata.json").is_file() or not (root / "sources").is_dir():
        raise CorpusError("corpus top-level entry type drift")
    manifest = _load_json(root / "manifest.json", "manifest")
    metadata = _load_json(root / "metadata.json", "metadata")
    programs = _validate_manifest(manifest)
    if _hash((root / "metadata.json").read_bytes()) != manifest["metadata_sha256"]:
        raise CorpusError("metadata: hash mismatch")
    _validate_metadata(metadata, programs)
    expected_sources: set[str] = set()
    errors: list[str] = []
    feature_counts: Counter[str] = Counter()
    for entry in programs:
        key = entry["program_key"]
        try:
            source_path = _safe_source_path(root, entry["source"], key)
            expected_sources.add(str(pathlib.PurePosixPath(entry["source"]).relative_to("sources")))
            if source_path.is_symlink() or not source_path.is_file():
                raise CorpusError(f"{key}: source missing or symlink")
            raw = source_path.read_bytes()
            if len(raw) != entry["raw_bytes"] or _hash(raw) != entry["raw_sha256"]:
                raise CorpusError(f"{key}: raw source hash or size mismatch")
            source = raw.decode("utf-8")
            normalized = normalize(source)
            normalized_bytes = normalized["source"].encode("utf-8")
            if len(normalized_bytes) != entry["normalized_bytes"] or _hash(normalized_bytes) != entry["normalized_sha256"]:
                raise CorpusError(f"{key}: normalized source hash or size mismatch")
            if normalized["outputs"] != entry["outputs"] or normalized["varyings"] != entry["varyings"]:
                raise CorpusError(f"{key}: normalized interface mismatch")
            parse_program(source, key)
            text = normalized["source"]
            for name, pattern in (("struct", r"\bstruct\b"), ("for", r"\bfor\b"), ("while", r"\bwhile\b"),
                                  ("do", r"\bdo\b"), ("ternary", r"\?"), ("uniform_block", r"\buniform\s+\w+\s*\{"),
                                  ("out_param", r"\b(?:out|inout)\b")):
                if __import__("re").search(pattern, text):
                    feature_counts[name] += 1
        except (CorpusError, FrontendError, UnicodeDecodeError, OSError, ValueError) as error:
            errors.append(str(error))
    actual_sources = _walk_regular_files(root / "sources")
    if actual_sources != expected_sources:
        errors.append(f"source file set drift: expected {sorted(expected_sources)}, got {sorted(actual_sources)}")
    adapters = {entry["program_key"] for entry in programs if entry["status"] == "adapter"}
    if adapters != _ADAPTERS:
        errors.append(f"adapter allowlist drift: expected {sorted(_ADAPTERS)}, got {sorted(adapters)}")
    statuses = Counter(entry["status"] for entry in programs)
    runtime_keys = sum(entry["runtime_key"] is not None for entry in programs)
    if errors:
        raise CorpusError("\n".join(sorted(errors)))
    return {
        "schema": SCHEMA,
        "revision": REVISION,
        "counts": {"effects": len(metadata["effects"]), "passes": len(programs), "sources": len(expected_sources),
                   "generated": statuses["generated"], "adapter": statuses["adapter"], "keyed_runtime": runtime_keys,
                   "draw_op_overrides": 1},
        "features": dict(sorted(feature_counts.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--report", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        report = validate_corpus()
    except CorpusError as error:
        print(f"check_corpus: {error}", file=sys.stderr)
        return 1
    if arguments.report:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("check_corpus: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
