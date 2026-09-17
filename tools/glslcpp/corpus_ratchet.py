"""Authority-closure ratchet for the pinned GLSL corpus.

The pinned corpus (``tools/glslcpp/corpus/<revision>/``) holds only programs
that pass the whole typed pipeline. Every other program the JS authority ships
is recorded, never silently omitted, in ``pending.json`` next to the corpus
manifest, together with the exact first blocker the real pipeline reports for
it. Three properties are enforced:

(a) closure -- the vendored program keys and the pending program keys are
    disjoint and their union is exactly the authority's program key set, as
    recorded from ``src/effects/generated/glsl-coverage.js``
    (``programCoverage``) of the pinned CPU authority;
(b) ratchet -- re-probing every pending program through the real pipeline
    yields exactly its recorded blocker. A program that starts passing, or
    fails differently, fails the check, so progress and regressions both have
    to be recorded deliberately;
(c) derived gates -- corpus cardinality gates are computed from this split
    (``vendored_count``/``authority_count``) instead of a hand-typed number.

Offline (``check_corpus --check``) the authority record is the committed
``pending.json`` ``authority`` section, and pending sources are the committed
``pending-sources/`` bytes. Online (``--cpu-root``/``--shader-git``) every
committed derivation is recomputed from the authority itself: the program key
set, both authority file digests, every pending source blob, every pending
effect projection, and every authority-projected metadata effect.

The probe runs the stages a vendored program faces, in pipeline order, using
the pipeline's own functions and no frontend profile (a pending program is no
profile's carrier):

1. ``corpus.pass_binding`` -- the corpus records one fragment pass per program
   (``check_corpus._validate_metadata``); a points/billboards pass is a scatter
   member, admitted only through the backend compatibility scatter contract.
2. ``corpus.parse`` -- ``normalize`` + ``parse_program`` (``check_corpus``).
3. ``semantics.defaults`` -- ``parse_program`` with the effect's default
   defines, ``analyze_program``, ``_validate_typed_ir`` (``check_semantics``).
4. ``semantics.variants`` -- every one-define-at-a-time variant
   (``check_semantics._define_variants``), first failure in its own order.
5. ``typed.defines`` -- the typed slice's integer default-define contract.
6. ``typed.validator`` -- ``generate_typed_slice.validate_capabilities``.
7. ``typed.emitter`` -- ``emit_typed_cpp.render_typed_cpp``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from tools.glslcpp import check_corpus
else:
    from . import check_corpus


SCHEMA = 1
PENDING_NAME = "pending.json"
PENDING_SOURCES = "pending-sources"
PROGRAM_COVERAGE = "src/effects/generated/glsl-coverage.js"
EFFECT_RECORDS = "src/effects/generated/upstream-snapshot.js"
SCATTER_DRAW_MODES = frozenset({"points", "billboards"})
STAGES = ("corpus.pass_binding", "corpus.parse", "semantics.defaults", "semantics.variants",
          "typed.defines", "typed.validator", "typed.emitter")
AUTHORITY_PROJECTED = "authority_projected"
_ROOT = pathlib.Path(__file__).resolve().parents[2]


class RatchetError(check_corpus.CorpusError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


# ---------------------------------------------------------------------------
# Shared record builders. The existing corpus manifest entries are reproduced
# byte-for-byte by `manifest_entry` (see `verify_builder_reproduces_manifest`),
# so vendored programs are built through the same code path.
# ---------------------------------------------------------------------------

def upstream_shader_path(effect_id: str, file: str) -> str:
    return f"shaders/effects/{effect_id}/glsl/{file}"


def runtime_key(effect_id: str, current_pass: dict[str, Any]) -> str | None:
    """The corpus runtime key: the program key, except for a scatter pass."""
    if current_pass.get("drawMode", "fragment") in SCATTER_DRAW_MODES:
        return None
    return f"{effect_id}:{current_pass['program']}"


def manifest_entry(effect_id: str, program: str, file: str, raw: bytes, status: str,
                   effect: dict[str, Any]) -> dict[str, Any]:
    from tools.glslcpp.frontend.preprocess import normalize

    matches = [(index, item) for index, item in enumerate(effect["passes"]) if item["program"] == program]
    if len(matches) != 1:
        raise RatchetError(f"{effect_id}:{program}: expected exactly one authority pass")
    pass_index, current_pass = matches[0]
    normalized = normalize(raw.decode("utf-8"))
    normalized_bytes = normalized["source"].encode("utf-8")
    return {
        "effect_id": effect_id, "program": program, "program_key": f"{effect_id}:{program}",
        "status": status, "source": f"sources/{effect_id}/{file}",
        "raw_bytes": len(raw), "raw_sha256": _sha(raw),
        "normalized_bytes": len(normalized_bytes), "normalized_sha256": _sha(normalized_bytes),
        "outputs": list(normalized["outputs"]), "varyings": list(normalized["varyings"]),
        "pass_index": pass_index, "pass_name": current_pass.get("name"),
        "runtime_key": runtime_key(effect_id, current_pass),
    }


def metadata_effect(record: dict[str, Any]) -> dict[str, Any]:
    """Project one authority effect record into the corpus metadata shape.

    The field set is the existing corpus metadata's (func, kind, namespace,
    params, passes, textures, and externalTexture only when present); each
    pass additionally carries its corpus runtime ``key``.
    """
    result: dict[str, Any] = {
        "func": record["func"], "kind": record["kind"], "namespace": record["namespace"],
        "params": record.get("params") or {},
        "passes": [dict(item, key=runtime_key(record["id"], item)) for item in record["passes"]],
        "textures": record.get("textures") or {},
    }
    if record.get("externalTexture"):
        result["externalTexture"] = record["externalTexture"]
    return json.loads(json.dumps(result))


# ---------------------------------------------------------------------------
# The probe.
# ---------------------------------------------------------------------------

def _diagnostic(error: BaseException) -> str:
    return f"{type(error).__name__}: {error}"


def probe_program(key: str, source_bytes: bytes, effect: dict[str, Any]) -> dict[str, str] | None:
    """Return the first blocker ``{"stage", "diagnostic"}``, or ``None`` if every stage passes."""
    from tools.glslcpp import check_semantics, generate_typed_slice
    from tools.glslcpp.emit_typed_cpp import render_typed_cpp
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.preprocess import normalize
    from tools.glslcpp.frontend.semantic import analyze_program

    effect_id, program = key.split(":", 1)
    passes = [item for item in effect["passes"] if item["program"] == program]
    scatter = sorted({item.get("drawMode") for item in passes if item.get("drawMode") in SCATTER_DRAW_MODES})
    if not passes:
        return {"stage": "corpus.pass_binding", "diagnostic": f"{key}: no authority pass runs this program"}
    if scatter:
        from tools.dsl.generate_backend_compatibility import SCATTER_KEY
        return {"stage": "corpus.pass_binding",
                "diagnostic": f"{key}: drawMode {'/'.join(scatter)} is a scatter pass; backend compatibility "
                              f"registers a scatter contract only for {SCATTER_KEY}"}
    if len(passes) != 1:
        names = ", ".join(str(item.get("name")) for item in passes)
        return {"stage": "corpus.pass_binding",
                "diagnostic": f"{key}: bound by {len(passes)} authority passes ({names}); the corpus "
                              "manifest records exactly one pass per program"}
    if passes[0].get("defines"):
        return {"stage": "corpus.pass_binding",
                "diagnostic": f"{key}: authority pass {passes[0].get('name')} declares pass-level defines "
                              f"{json.dumps(passes[0]['defines'], sort_keys=True)}; the typed slice bakes the "
                              "effect's default defines"}
    try:
        source = source_bytes.decode("utf-8")
        normalize(source)
        parse_program(source, key)
    except Exception as error:  # noqa: BLE001 -- the diagnostic is the record
        return {"stage": "corpus.parse", "diagnostic": _diagnostic(error)}
    metadata = {"effects": {effect_id: effect}}
    defaults = check_semantics._metadata_defaults(metadata, key)
    try:
        typed = analyze_program(parse_program(source, key, defaults), key)
        check_semantics._validate_typed_ir(typed)
    except Exception as error:  # noqa: BLE001
        return {"stage": "semantics.defaults", "diagnostic": _diagnostic(error)}
    try:
        variants = check_semantics._define_variants(metadata)
    except Exception as error:  # noqa: BLE001
        return {"stage": "semantics.variants", "diagnostic": _diagnostic(error)}
    for _, parameter, define, value in variants:
        defines = dict(defaults)
        defines[define] = value
        try:
            variant = analyze_program(parse_program(source, key, defines), key)
            check_semantics._validate_typed_ir(variant)
        except Exception as error:  # noqa: BLE001
            return {"stage": "semantics.variants",
                    "diagnostic": f"{parameter}:{define}={value!r}: {_diagnostic(error)}"}
    if any(not isinstance(name, str) or not isinstance(value, int) for name, value in defaults.items()):
        return {"stage": "typed.defines", "diagnostic": f"{key}: invalid default-define contract {defaults!r}"}
    source_hash = _sha(source_bytes)
    typed = analyze_program(parse_program(source, key, defaults), key, source_global_literal_int_profile=None)
    typed = generate_typed_slice.attach_fixed_array_in_parameter_proof(typed)
    typed = generate_typed_slice.attach_fixed_affine_centers13_proof(typed)
    try:
        generate_typed_slice.validate_capabilities(typed, generate_typed_slice.APPROVED_CAPABILITIES,
                                                   source_hash=source_hash)
    except Exception as error:  # noqa: BLE001
        return {"stage": "typed.validator", "diagnostic": _diagnostic(error)}
    try:
        render_typed_cpp(typed, key, source_hash, "typed_probe",
                         "bind_" + key.replace("/", "_").replace(":", "_"))
    except Exception as error:  # noqa: BLE001
        return {"stage": "typed.emitter", "diagnostic": _diagnostic(error)}
    return None


# ---------------------------------------------------------------------------
# Committed record: loading and offline validation.
# ---------------------------------------------------------------------------

_PENDING_FIELDS = {"program_key", "effect_id", "program", "authority_status", "source", "raw_bytes",
                   "raw_sha256", "blocker"}


def load_pending(root: pathlib.Path) -> dict[str, Any]:
    path = root / PENDING_NAME
    if path.is_symlink() or not path.is_file():
        raise RatchetError("pending.json is missing or is a symlink")
    document = check_corpus._load_json(path, "pending")
    if set(document) != {"schema", "revision", "authority", "effects", "pending"}:
        raise RatchetError("pending: unexpected top-level fields")
    if document["schema"] != SCHEMA or document["revision"] != check_corpus.REVISION:
        raise RatchetError("pending: unsupported schema or revision")
    authority = document["authority"]
    if not isinstance(authority, dict) or set(authority) != {
            "program_coverage", "program_coverage_sha256", "effect_records", "effect_records_sha256", "programs"}:
        raise RatchetError("pending: malformed authority record")
    if authority["program_coverage"] != PROGRAM_COVERAGE or authority["effect_records"] != EFFECT_RECORDS:
        raise RatchetError("pending: authority record names the wrong authority files")
    programs = authority["programs"]
    if not isinstance(programs, list) or not programs or any(
            not isinstance(item, dict) or set(item) != {"program_key", "status", "file"}
            or item["status"] not in ("generated", "adapter") for item in programs):
        raise RatchetError("pending: malformed authority program list")
    keys = [item["program_key"] for item in programs]
    if keys != sorted(set(keys)):
        raise RatchetError("pending: authority program keys must be unique and sorted")
    pending = document["pending"]
    if not isinstance(pending, list) or any(not isinstance(item, dict) or set(item) != _PENDING_FIELDS
                                            for item in pending):
        raise RatchetError("pending: malformed pending program record")
    pending_keys = [item["program_key"] for item in pending]
    if pending_keys != sorted(set(pending_keys)):
        raise RatchetError("pending: pending program keys must be unique and sorted")
    for item in pending:
        blocker = item["blocker"]
        if (not isinstance(blocker, dict) or set(blocker) != {"stage", "diagnostic"}
                or blocker["stage"] not in STAGES or not isinstance(blocker["diagnostic"], str)
                or not blocker["diagnostic"]):
            raise RatchetError(f"{item['program_key']}: malformed pending blocker")
    if not isinstance(document["effects"], dict):
        raise RatchetError("pending: malformed effect projections")
    return document


def validate_closure(root: pathlib.Path, manifest_programs: list[dict[str, Any]],
                     metadata: dict[str, Any]) -> dict[str, Any]:
    """Offline structural ratchet: (a) closure plus pending source identity. Fast."""
    document = load_pending(root)
    authority = {item["program_key"]: item for item in document["authority"]["programs"]}
    vendored = {item["program_key"] for item in manifest_programs}
    pending = {item["program_key"]: item for item in document["pending"]}
    errors: list[str] = []
    overlap = sorted(vendored & set(pending))
    if overlap:
        errors.append(f"ratchet: vendored and pending overlap: {overlap}")
    union = vendored | set(pending)
    if union != set(authority):
        errors.append(f"ratchet: vendored + pending != authority programs: missing "
                      f"{sorted(set(authority) - union)}, foreign {sorted(union - set(authority))}")
    expected_sources: set[str] = set()
    for key, item in sorted(pending.items()):
        effect_id, program = key.split(":", 1)
        record = authority.get(key)
        if record is None:
            continue
        expected = f"{PENDING_SOURCES}/{effect_id}/{record['file']}"
        if (item["effect_id"] != effect_id or item["program"] != program
                or item["authority_status"] != record["status"] or item["source"] != expected):
            errors.append(f"{key}: pending identity differs from the authority record")
            continue
        path = check_corpus._safe_source_path(root, item["source"], key)
        expected_sources.add(str(pathlib.PurePosixPath(item["source"]).relative_to(PENDING_SOURCES)))
        if path.is_symlink() or not path.is_file():
            errors.append(f"{key}: pending source missing or symlink")
            continue
        raw = path.read_bytes()
        if len(raw) != item["raw_bytes"] or _sha(raw) != item["raw_sha256"]:
            errors.append(f"{key}: pending source hash or size mismatch")
    for item in manifest_programs:
        record = authority.get(item["program_key"])
        if record is not None and item["source"] != f"sources/{item['effect_id']}/{record['file']}":
            errors.append(f"{item['program_key']}: vendored source file differs from the authority record")
    source_root = root / PENDING_SOURCES
    if source_root.is_symlink() or not source_root.is_dir():
        errors.append("pending-sources is missing or is a symlink")
    else:
        actual = check_corpus._walk_regular_files(source_root)
        if actual != expected_sources:
            errors.append(f"pending source file set drift: expected {sorted(expected_sources)}, got {sorted(actual)}")
    pending_effects = {key.split(":", 1)[0] for key in pending}
    expected_projected = sorted(pending_effects - set(metadata["effects"]))
    if sorted(document["effects"]) != expected_projected:
        errors.append(f"pending effect projections drift: expected {expected_projected}, got {sorted(document['effects'])}")
    if errors:
        raise RatchetError("\n".join(errors))
    return document


def effect_for(document: dict[str, Any], metadata: dict[str, Any], effect_id: str) -> dict[str, Any]:
    effect = metadata["effects"].get(effect_id) or document["effects"].get(effect_id)
    if effect is None:
        raise RatchetError(f"{effect_id}: no effect record for a pending program")
    return effect


def check_pending(repository: pathlib.Path | None = None) -> dict[str, Any]:
    """(b): re-probe every pending program; its blocker must be exactly the recorded one."""
    repository = (repository or _ROOT).resolve()
    check_corpus.validate_corpus(repository)
    root = check_corpus._corpus_root(repository)
    manifest = check_corpus._load_json(root / "manifest.json", "manifest")
    metadata = check_corpus._load_json(root / "metadata.json", "metadata")
    programs = check_corpus._validate_manifest(manifest)
    document = validate_closure(root, programs, metadata)
    errors: list[str] = []
    for item in document["pending"]:
        key = item["program_key"]
        raw = (root / item["source"]).read_bytes()
        blocker = probe_program(key, raw, effect_for(document, metadata, key.split(":", 1)[0]))
        if blocker is None:
            errors.append(f"{key}: now passes every probe stage; vendor it into the corpus "
                          "(python3 -m tools.glslcpp.corpus_ratchet --write ...)")
        elif blocker != item["blocker"]:
            errors.append(f"{key}: blocker changed\n  recorded: {item['blocker']}\n  probed:   {blocker}")
    if errors:
        raise RatchetError("\n".join(errors))
    return document


def summary(document: dict[str, Any], vendored_count: int) -> dict[str, Any]:
    stages: dict[str, int] = {}
    for item in document["pending"]:
        stages[item["blocker"]["stage"]] = stages.get(item["blocker"]["stage"], 0) + 1
    return {"authority_programs": len(document["authority"]["programs"]), "vendored": vendored_count,
            "pending": len(document["pending"]), "pending_by_stage": dict(sorted(stages.items()))}


# ---------------------------------------------------------------------------
# Online derivation from the authority.
# ---------------------------------------------------------------------------

def _node_export(module: pathlib.Path, name: str) -> Any:
    script = ("import {" + name + "} from " + json.dumps(module.resolve().as_uri()) + ";"
              "process.stdout.write(JSON.stringify(" + name + "));")
    try:
        result = subprocess.run(["node", "--input-type=module", "-e", script], check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return json.loads(result.stdout)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        raise RatchetError(f"unable to load {name} from the authority: {error}") from error


def _git_blob(shader_git: pathlib.Path, path: str) -> bytes:
    try:
        return subprocess.run(["git", "-C", str(shader_git), "cat-file", "blob", f"{check_corpus.REVISION}:{path}"],
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise RatchetError(f"shader git blob read failed: {path}") from error


def authority_derivation(cpu_root: pathlib.Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    cpu_root = cpu_root.resolve()
    coverage_path = cpu_root / PROGRAM_COVERAGE
    records_path = cpu_root / EFFECT_RECORDS
    for path in (coverage_path, records_path):
        if path.is_symlink() or not path.is_file():
            raise RatchetError(f"authority file missing or symlink: {path}")
    coverage = _node_export(coverage_path, "programCoverage")
    records = {item["id"]: item for item in _node_export(records_path, "effectRecords")}
    programs = sorted(({"program_key": f"{item['effectId']}:{item['program']}", "status": item["status"],
                        "file": item["file"]} for item in coverage), key=lambda item: item["program_key"])
    if len({item["program_key"] for item in programs}) != len(programs):
        raise RatchetError("authority programCoverage repeats a program key")
    pass_keys = {f"{effect_id}:{item['program']}" for effect_id, record in records.items() for item in record["passes"]}
    if pass_keys != {item["program_key"] for item in programs}:
        raise RatchetError("authority programCoverage differs from the effect records' pass closure")
    authority = {"program_coverage": PROGRAM_COVERAGE, "program_coverage_sha256": _sha(coverage_path.read_bytes()),
                 "effect_records": EFFECT_RECORDS, "effect_records_sha256": _sha(records_path.read_bytes()),
                 "programs": programs}
    return authority, records


def verify_authority(repository: pathlib.Path, cpu_root: pathlib.Path, shader_git: pathlib.Path) -> None:
    """Recompute every committed authority derivation and require exact equality."""
    repository = repository.resolve()
    root = check_corpus._corpus_root(repository)
    manifest = check_corpus._load_json(root / "manifest.json", "manifest")
    metadata = check_corpus._load_json(root / "metadata.json", "metadata")
    programs = check_corpus._validate_manifest(manifest)
    document = validate_closure(root, programs, metadata)
    authority, records = authority_derivation(cpu_root)
    errors: list[str] = []
    if authority != document["authority"]:
        errors.append("pending authority record differs from the live authority derivation")
    by_key = {item["program_key"]: item for item in authority["programs"]}
    for item in document["pending"]:
        record = by_key.get(item["program_key"])
        if record is None:
            continue
        blob = _git_blob(shader_git, upstream_shader_path(item["effect_id"], record["file"]))
        if _sha(blob) != item["raw_sha256"]:
            errors.append(f"{item['program_key']}: pending source differs from the upstream blob")
    for effect_id, projection in document["effects"].items():
        if effect_id not in records or metadata_effect(records[effect_id]) != projection:
            errors.append(f"{effect_id}: pending effect projection differs from the authority record")
    for effect_id in metadata.get("provenance", {}).get(AUTHORITY_PROJECTED, []):
        if effect_id not in records or metadata_effect(records[effect_id]) != metadata["effects"].get(effect_id):
            errors.append(f"{effect_id}: authority-projected metadata differs from the authority record")
    for entry in programs:
        record = by_key.get(entry["program_key"])
        if record is not None:
            blob = _git_blob(shader_git, upstream_shader_path(entry["effect_id"], record["file"]))
            if _sha(blob) != entry["raw_sha256"]:
                errors.append(f"{entry['program_key']}: vendored source differs from the upstream blob")
    if errors:
        raise RatchetError("\n".join(errors))


def verify_builder_reproduces_manifest(repository: pathlib.Path) -> None:
    """Every vendored manifest entry equals `manifest_entry` over its own committed bytes."""
    root = check_corpus._corpus_root(repository.resolve())
    manifest = check_corpus._load_json(root / "manifest.json", "manifest")
    metadata = check_corpus._load_json(root / "metadata.json", "metadata")
    mismatches = []
    for entry in check_corpus._validate_manifest(manifest):
        file = pathlib.PurePosixPath(entry["source"]).name
        built = manifest_entry(entry["effect_id"], entry["program"], file, (root / entry["source"]).read_bytes(),
                               entry["status"], metadata["effects"][entry["effect_id"]])
        if built != entry:
            mismatches.append(entry["program_key"])
    if mismatches:
        raise RatchetError(f"manifest builder does not reproduce: {mismatches}")


def _add_typed_slice_rows(repository: pathlib.Path, entries: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    """Give every promoted fragment program its plain typed-slice row (effect default defines)."""
    from tools.glslcpp import check_semantics

    path = repository / "tools/glslcpp/typed_slice.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    rows = {item["program_key"]: item for item in spec["programs"]}
    for entry in entries:
        if entry["runtime_key"] is None:
            continue
        rows.setdefault(entry["program_key"], {
            "defines": check_semantics._metadata_defaults(metadata, entry["program_key"]),
            "program_key": entry["program_key"]})
    spec["programs"] = [rows[key] for key in sorted(rows)]
    path.write_bytes(_json_bytes(spec))


def write(repository: pathlib.Path, cpu_root: pathlib.Path, shader_git: pathlib.Path) -> dict[str, Any]:
    """Promote every authority program that passes the probe; record the rest with their blockers."""
    repository = repository.resolve()
    root = check_corpus._corpus_root(repository)
    manifest = check_corpus._load_json(root / "manifest.json", "manifest")
    metadata = check_corpus._load_json(root / "metadata.json", "metadata")
    programs = {item["program_key"]: item for item in check_corpus._validate_manifest(manifest)}
    authority, records = authority_derivation(cpu_root)
    projected = set(metadata.get("provenance", {}).get(AUTHORITY_PROJECTED, []))
    pending: list[dict[str, Any]] = []
    promoted: list[str] = []
    pending_sources: dict[str, bytes] = {}
    for item in authority["programs"]:
        key = item["program_key"]
        if key in programs:
            continue
        effect_id, program = key.split(":", 1)
        raw = _git_blob(shader_git, upstream_shader_path(effect_id, item["file"]))
        effect = metadata["effects"].get(effect_id) or metadata_effect(records[effect_id])
        blocker = probe_program(key, raw, effect)
        if blocker is None:
            if effect_id not in metadata["effects"]:
                metadata["effects"][effect_id] = effect
                projected.add(effect_id)
            programs[key] = manifest_entry(effect_id, program, item["file"], raw, item["status"], effect)
            target = root / programs[key]["source"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            promoted.append(key)
            continue
        source = f"{PENDING_SOURCES}/{effect_id}/{item['file']}"
        pending_sources[source] = raw
        pending.append({"program_key": key, "effect_id": effect_id, "program": program,
                        "authority_status": item["status"], "source": source, "raw_bytes": len(raw),
                        "raw_sha256": _sha(raw), "blocker": blocker})
    if promoted:
        _add_typed_slice_rows(repository, [programs[key] for key in promoted], metadata)
    if projected:
        metadata.setdefault("provenance", {})[AUTHORITY_PROJECTED] = sorted(projected)
    metadata_bytes = _json_bytes(metadata)
    (root / "metadata.json").write_bytes(metadata_bytes)
    manifest["metadata_sha256"] = _sha(metadata_bytes)
    manifest["programs"] = [programs[key] for key in sorted(programs)]
    (root / "manifest.json").write_bytes(_json_bytes(manifest))
    effects = {key.split(":", 1)[0] for key in (item["program_key"] for item in pending)}
    document = {"schema": SCHEMA, "revision": check_corpus.REVISION, "authority": authority,
                "effects": {effect_id: metadata_effect(records[effect_id])
                            for effect_id in sorted(effects) if effect_id not in metadata["effects"]},
                "pending": pending}
    (root / PENDING_NAME).write_bytes(_json_bytes(document))
    source_root = root / PENDING_SOURCES
    if source_root.exists():
        if source_root.is_symlink() or not source_root.is_dir() or source_root.parent != root:
            raise RatchetError("refusing to replace an unexpected pending-sources entry")
        shutil.rmtree(source_root)
    for relative, data in sorted(pending_sources.items()):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {"promoted": promoted, **summary(document, len(programs))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="offline closure + re-probe; online derivation too "
                                                           "when --cpu-root/--shader-git are given")
    mode.add_argument("--write", action="store_true", help="promote passing programs, rewrite pending.json")
    mode.add_argument("--report", action="store_true")
    parser.add_argument("--cpu-root", type=pathlib.Path)
    parser.add_argument("--shader-git", type=pathlib.Path)
    arguments = parser.parse_args(argv)
    if (arguments.cpu_root is None) != (arguments.shader_git is None):
        parser.error("--cpu-root and --shader-git go together")
    try:
        if arguments.write:
            if arguments.cpu_root is None:
                parser.error("--write requires --cpu-root and --shader-git")
            print(json.dumps(write(_ROOT, arguments.cpu_root, arguments.shader_git), indent=2, sort_keys=True))
            return 0
        document = check_pending(_ROOT)
        if arguments.cpu_root is not None:
            verify_authority(_ROOT, arguments.cpu_root, arguments.shader_git)
        root = check_corpus._corpus_root(_ROOT)
        vendored = len(check_corpus._load_json(root / "manifest.json", "manifest")["programs"])
        report = summary(document, vendored)
        if arguments.report:
            report["pending_programs"] = {item["program_key"]: item["blocker"] for item in document["pending"]}
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"corpus_ratchet: ok ({report['vendored']} vendored + {report['pending']} pending = "
                  f"{report['authority_programs']} authority programs)")
    except check_corpus.CorpusError as error:
        print(f"corpus_ratchet: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
