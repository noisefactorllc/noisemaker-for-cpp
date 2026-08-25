"""Generate the authenticated C++ backend compatibility census.

The generator deliberately has two external authority inputs.  It never
checks out or mutates the shader repository: source blobs are read with
``git cat-file`` at the pinned commit.  The checked-in JSON is evidence for
the later catalog/compiler stages, not a hand-maintained allow-list.
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile
import sys
from collections import Counter, defaultdict
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from tools.glslcpp import check_corpus, check_semantics, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.lexer import tokenize
from tools.glslcpp.frontend.preprocess import normalize
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "src/effects/generated/backend_compatibility.json"
UPSTREAM_REVISION = "117a236679d1db3ab8f0e278230ece277b57564c"
UPSTREAM_TREE = "a7a997dfdc807697adba008729dcdfdfcfbaf53c"
SOURCE_LOCK_SHA256 = "66f4e9337810ca839dddaba047dadc0c15e903e0f662f189ee6d08ff84fb62c4"
CPU_PACKAGE_SHA256 = "c7d8aec82725078b4d31d379323901e83bdfba0a0289ff8428beecdac2c9d78a"
CPU_LOCK_SHA256 = "724bfaf208346605cae0ce9a74d0e84c76dd3aeb8fedb44fb894ad03c4dad03d"
UPSTREAM_PACKAGE_SHA256 = "109e0617b53eca612d6265672e010744ee3284aea26555eee1f614c3ddc33c8a"
UPSTREAM_LOCK_SHA256 = "033762c49845652b36ea91b75653c63ed62c45bd2fb455ab66567ff4b356109f"
CORPUS_REVISION = check_corpus.REVISION
SCATTER_KEY = "filter/wormhole:deposit"
RESERVED_RUNTIME = frozenset({
    "resolution", "fullResolution", "renderScale", "tileOffset", "time",
    "frame", "seed", "deltaTime",
})
# These uniforms are supplied by the canonical CPU binding layer rather than
# by an effect parameter or pass map. Keep the list explicit: an unlisted
# typed uniform must remain an admission failure instead of silently becoming
# a pass-derived value.
PASS_DERIVED_BINDINGS = {
    "aspect": "fullResolution_aspect_ratio",
    "centerLoX": "canonical_center_low_x_default",
    "centerLoY": "canonical_center_low_y_default",
    "data": "remap_uniform_data",
    "LOOP_OFFSET": "typed_compile_define",
    "motion": "canonical_motion_default",
    "NOISE_TYPE": "typed_compile_define",
    "size": "canonical_size_default",
    "splatSource": "canonical_splat_source_default",
    "speed": "canonical_speed_default",
}
CPP_TYPES = {
    "float": "float", "int": "std::int32_t", "uint": "std::uint32_t",
    "bool": "bool", "vec2": "glsl::Vec2", "vec3": "glsl::Vec3",
    "vec4": "glsl::Vec4", "ivec2": "glsl::IVec2", "ivec3": "glsl::IVec3",
    "ivec4": "glsl::IVec4", "uvec2": "glsl::UVec2", "uvec3": "glsl::UVec3",
    "uvec4": "glsl::UVec4", "mat2": "glsl::Mat2", "mat3": "glsl::Mat3",
}
SUPPORTED_DRAW_MODES = frozenset({"fragment", "triangles"})


class CompatibilityError(ValueError):
    """Fail-closed generation error."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _regular_files(root: pathlib.Path) -> list[pathlib.Path]:
    if root.is_symlink() or not root.is_dir():
        raise CompatibilityError(f"authority directory missing or symlink: {root}")
    result: list[pathlib.Path] = []
    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = pathlib.Path(current)
        for name in dirs:
            if (current_path / name).is_symlink():
                raise CompatibilityError(f"authority source tree contains symlink: {current_path / name}")
        for name in names:
            path = current_path / name
            if path.is_symlink():
                raise CompatibilityError(f"authority source tree contains symlink: {path}")
            if not path.is_file():
                raise CompatibilityError(f"authority source tree contains non-file: {path}")
            result.append(path)
    return result


def behavioral_lock(cpu_root: pathlib.Path) -> tuple[str, int]:
    files = _regular_files(cpu_root / "src")
    for relative in ("scripts/upstream/source-lock.js", "package.json", "package-lock.json"):
        path = cpu_root / relative
        if path.is_symlink() or not path.is_file():
            raise CompatibilityError(f"missing CPU authority file: {relative}")
        files.append(path)
    files.sort(key=lambda item: item.relative_to(cpu_root).as_posix())
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(cpu_root).as_posix()
        data = path.read_bytes()
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(str(len(data)).encode())
        digest.update(b"\0")
        digest.update(data)
    return digest.hexdigest(), len(files)


def _git(shader_git: pathlib.Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(shader_git), *args], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr.decode(errors="replace").strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        raise CompatibilityError(f"shader git command failed: {' '.join(args)}: {detail}") from error
    return result.stdout


def _git_blob(shader_git: pathlib.Path, revision: str, relative: str) -> bytes:
    return _git(shader_git, "cat-file", "blob", f"{revision}:{relative}")


def _source_digest(shader_git: pathlib.Path, revision: str) -> str:
    records = _git(shader_git, "ls-tree", "-r", "-z", revision, "--", "shaders/effects", "shaders/src")
    paths: list[str] = []
    for record in records.split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, kind, _ = header.decode().split()
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise CompatibilityError(f"upstream source tree contains unsupported entry: {raw_path!r}")
        paths.append(raw_path.decode())
    # Node's String.prototype.localeCompare (used by the CPU source-lock
    # module) orders these path names case-insensitively on the pinned host.
    # The upstream tree contains the uppercase HELP_TEMPLATE.md sentinel, so
    # plain byte/Unicode sorting would authenticate a different stream.
    paths.sort(key=str.lower)
    digest = hashlib.sha256()
    for relative in paths:
        data = _git_blob(shader_git, revision, relative)
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(str(len(data)).encode())
        digest.update(b"\0")
        digest.update(data)
    return digest.hexdigest()


def _authority(cpu_root: pathlib.Path, shader_git: pathlib.Path) -> dict[str, Any]:
    cpu_package = (cpu_root / "package.json").read_bytes()
    cpu_lock = (cpu_root / "package-lock.json").read_bytes()
    source_lock = (cpu_root / "scripts/upstream/source-lock.js").read_text(encoding="utf-8")
    if _sha(cpu_package) != CPU_PACKAGE_SHA256:
        raise CompatibilityError("CPU package.json SHA-256 mismatch")
    if _sha(cpu_lock) != CPU_LOCK_SHA256:
        raise CompatibilityError("CPU package-lock.json SHA-256 mismatch")
    lock_match = re.search(r"PINNED_SOURCE_DIGEST\s*=\s*'([0-9a-f]{64})'", source_lock)
    revision_match = re.search(r"PINNED_UPSTREAM_REVISION\s*=\s*'([0-9a-f]{40})'", source_lock)
    if not lock_match or lock_match.group(1) != SOURCE_LOCK_SHA256:
        raise CompatibilityError("CPU source-lock digest declaration mismatch")
    if not revision_match or revision_match.group(1) != UPSTREAM_REVISION:
        raise CompatibilityError("CPU source-lock revision declaration mismatch")
    behavioral, file_count = behavioral_lock(cpu_root)
    revision = _git(shader_git, "rev-parse", "--verify", f"{UPSTREAM_REVISION}^{{commit}}").decode().strip()
    tree = _git(shader_git, "rev-parse", f"{UPSTREAM_REVISION}^{{tree}}").decode().strip()
    if revision != UPSTREAM_REVISION or tree != UPSTREAM_TREE:
        raise CompatibilityError("upstream revision/tree mismatch")
    upstream_package = _git_blob(shader_git, UPSTREAM_REVISION, "package.json")
    upstream_lock = _git_blob(shader_git, UPSTREAM_REVISION, "package-lock.json")
    if _sha(upstream_package) != UPSTREAM_PACKAGE_SHA256:
        raise CompatibilityError("upstream package.json SHA-256 mismatch")
    if _sha(upstream_lock) != UPSTREAM_LOCK_SHA256:
        raise CompatibilityError("upstream package-lock.json SHA-256 mismatch")
    if _source_digest(shader_git, UPSTREAM_REVISION) != SOURCE_LOCK_SHA256:
        raise CompatibilityError("upstream source-lock digest mismatch")
    return {
        "cpu_behavioral_lock": behavioral,
        "cpu_behavioral_file_count": file_count,
        "cpu_package_sha256": CPU_PACKAGE_SHA256,
        "cpu_package_lock_sha256": CPU_LOCK_SHA256,
        "cpu_source_lock_sha256": _sha((cpu_root / "scripts/upstream/source-lock.js").read_bytes()),
        "source_lock_sha256": SOURCE_LOCK_SHA256,
        "upstream_revision": UPSTREAM_REVISION,
        "upstream_tree": UPSTREAM_TREE,
        "upstream_package_sha256": UPSTREAM_PACKAGE_SHA256,
        "upstream_package_lock_sha256": UPSTREAM_LOCK_SHA256,
    }


def _node_effect_records(cpu_root: pathlib.Path) -> list[dict[str, Any]]:
    module = (cpu_root / "src/effects/generated/upstream-snapshot.js").resolve()
    script = (
        "import {effectRecords} from " + json.dumps(module.as_uri()) + ";"
        "process.stdout.write(JSON.stringify(effectRecords));"
    )
    try:
        result = subprocess.run(["node", "--input-type=module", "-e", script], check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        value = json.loads(result.stdout)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        raise CompatibilityError(f"unable to load CPU effect records: {error}") from error
    if not isinstance(value, list):
        raise CompatibilityError("CPU effect records are not an array")
    return value


def _span_free(value: Any, field: str = "") -> Any:
    if (field in {"span", "source", "raw_source", "counted_loop_proof", "counter_proof",
                  "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
                  "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof"}
            or field.endswith("_span")):
        return None
    if dataclasses.is_dataclass(value):
        result: dict[str, Any] = {}
        for item in dataclasses.fields(value):
            child = _span_free(getattr(value, item.name), item.name)
            if child is not None:
                result[item.name] = child
        return result
    if isinstance(value, (tuple, list)):
        return [_span_free(item, field) for item in value]
    if isinstance(value, dict):
        return {key: _span_free(item, str(key)) for key, item in sorted(value.items())}
    if isinstance(value, float):
        return value.hex()
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return repr(value)


def _typed(source: str, key: str, defines: dict[str, Any]) -> Any:
    parsed = parse_program(source, key, defines)
    return analyze_program(parsed, key)


def _typed_hash(typed: Any) -> str:
    payload = json.dumps(_span_free(typed), sort_keys=True, separators=(",", ":")).encode()
    return _sha(payload)


def _canonical_token_hash(source: str) -> str:
    normalized = normalize(source)["source"]
    stream = [(token.kind, token.value) for token in tokenize(normalized)]
    return _sha(json.dumps(stream, separators=(",", ":")).encode())


def _cpp_type(display: str) -> str:
    if display in CPP_TYPES:
        return CPP_TYPES[display]
    if display.startswith("sampler"):
        return "const Surface&"
    return display


def _typed_manifest(repository: pathlib.Path, generated: dict[str, Any], corpus_keys: set[str]) -> dict[str, dict[str, Any]]:
    path = repository / "src/typed_generated/typed_manifest.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CompatibilityError(f"invalid typed manifest: {error}") from error
    generated_programs = generated.get("programs")
    if document != generated:
        raise CompatibilityError("typed manifest is not the authenticated emitter output")
    programs = document.get("programs")
    if not isinstance(programs, list):
        raise CompatibilityError("typed manifest programs missing")
    result: dict[str, dict[str, Any]] = {}
    for item in programs:
        key = item.get("program_key")
        if not isinstance(key, str) or key in result:
            raise CompatibilityError("typed manifest duplicate/malformed key")
        if not isinstance(item.get("source_sha256"), str) or not _SHA256.fullmatch(item["source_sha256"]):
            raise CompatibilityError(f"{key}: typed manifest source hash missing")
        if not isinstance(item.get("output_sha256"), str) or not _SHA256.fullmatch(item["output_sha256"]):
            raise CompatibilityError(f"{key}: typed manifest output hash missing")
        if not isinstance(item.get("factory"), str) or not item.get("typed_abi") \
                or not isinstance(item.get("factory_route"), dict):
            raise CompatibilityError(f"{key}: typed manifest emitter ABI missing")
        result[key] = item
    expected = corpus_keys - {SCATTER_KEY}
    if set(result) != expected:
        raise CompatibilityError("typed manifest/corpus closure mismatch")
    return result


def _authenticated_typed_manifest(repository: pathlib.Path) -> dict[str, Any]:
    try:
        generated = generate_typed_slice.generate_outputs(repository)
        manifest_bytes = generated["src/typed_generated/typed_manifest.json"]
        slice_bytes = generated["src/typed_generated/typed_slice.cpp"]
    except Exception as error:
        raise CompatibilityError(f"typed emitter authentication failed: {error}") from error
    manifest_path = repository / "src/typed_generated/typed_manifest.json"
    slice_path = repository / "src/typed_generated/typed_slice.cpp"
    if manifest_path.read_bytes() != manifest_bytes:
        raise CompatibilityError("typed manifest drift from authenticated emitter")
    if slice_path.read_bytes() != slice_bytes:
        raise CompatibilityError("typed_slice.cpp drift from authenticated emitter")
    try:
        return json.loads(manifest_bytes)
    except json.JSONDecodeError as error:
        raise CompatibilityError(f"authenticated typed manifest is invalid: {error}") from error


def _pass_index(effect: dict[str, Any], key: str) -> dict[str, Any]:
    _, program = key.split(":", 1)
    matches = [item for item in effect.get("passes", []) if item.get("program") == program]
    if len(matches) != 1:
        raise CompatibilityError(f"{key}: expected exactly one authority pass")
    return matches[0]


def _extent(effect: dict[str, Any], current_pass: dict[str, Any], route: str) -> dict[str, Any]:
    if route in effect.get("textures", {}):
        texture = effect["textures"][route]
        if isinstance(texture, dict):
            return {"width": texture.get("width", "screen"), "height": texture.get("height", "screen"),
                    "format": texture.get("format", "rgba8unorm")}
    viewport = current_pass.get("viewport")
    if isinstance(viewport, dict):
        return {"width": viewport.get("width", "screen"), "height": viewport.get("height", "screen"),
                "format": "rgba8unorm"}
    return {"width": "screen", "height": "screen", "format": "rgba8unorm"}


def _binding_abi(effect: dict[str, Any], current_pass: dict[str, Any], typed_record: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    params = effect.get("params", {})
    aliases = effect.get("paramAliases", {})
    # The CPU definition's public parameter name and shader uniform name are
    # intentionally allowed to differ (for example ``shape`` -> ``metric`` or
    # ``x`` -> ``scaleX``).  Build this map from the authority metadata rather
    # than guessing from identifiers in generated C++.
    param_by_uniform = {
        spec.get("uniform"): name for name, spec in params.items()
        if isinstance(spec, dict) and isinstance(spec.get("uniform"), str)
    }
    param_by_color_mode_uniform = {
        spec.get("colorModeUniform"): name for name, spec in params.items()
        if isinstance(spec, dict) and isinstance(spec.get("colorModeUniform"), str)
    }
    uniform_map = current_pass.get("uniforms", {})
    input_map = current_pass.get("inputs", {})
    uniforms: list[dict[str, Any]] = []
    samplers: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    typed_abi = typed_record.get("typed_abi")
    if not isinstance(typed_abi, dict):
        raise CompatibilityError(f"{typed_record.get('program_key')}: typed emitter ABI missing")
    typed_uniforms = typed_abi.get("uniforms")
    typed_samplers = typed_abi.get("samplers")
    if not isinstance(typed_uniforms, list) or not isinstance(typed_samplers, list):
        raise CompatibilityError(f"{typed_record.get('program_key')}: malformed typed emitter ABI")
    sampler_names = set(typed_samplers)
    for declaration in typed_uniforms:
        name = declaration.get("name") if isinstance(declaration, dict) else None
        typ = declaration.get("type") if isinstance(declaration, dict) else None
        if not isinstance(name, str) or not isinstance(typ, str):
            unresolved.append({"name": name, "reason": "malformed typed declaration"})
            continue
        if name in sampler_names:
            source = "resource" if name in input_map else ("external_texture" if effect.get("externalTexture") else None)
            item = {"name": name, "type": "sampler2D", "cpp_type": "const Surface&", "source": source,
                    "resource": input_map.get(name)}
            samplers.append(item)
            if source is None:
                unresolved.append({"name": name, "reason": "sampler has no resource source"})
            continue
        mapped = uniform_map.get(name, name)
        if mapped in params or mapped in aliases or name in params or name in param_by_uniform or name in param_by_color_mode_uniform:
            source = "effect_parameter"
            source_name = aliases.get(mapped, mapped)
            if name in param_by_uniform:
                source_name = param_by_uniform[name]
            elif name in param_by_color_mode_uniform:
                source_name = param_by_color_mode_uniform[name]
        elif mapped in RESERVED_RUNTIME or name in RESERVED_RUNTIME:
            source = "reserved_runtime_state"
            source_name = mapped if mapped in RESERVED_RUNTIME else name
        elif mapped in input_map or mapped in effect.get("textures", {}):
            source = "resource"
            source_name = mapped
        elif name in uniform_map:
            source = "pass_derived"
            source_name = mapped
        elif name in PASS_DERIVED_BINDINGS:
            source = "pass_derived"
            source_name = PASS_DERIVED_BINDINGS[name]
        else:
            source = None
            source_name = mapped
        item = {"name": name, "type": typ, "cpp_type": _cpp_type(typ), "source": source,
                "source_name": source_name}
        uniforms.append(item)
        if source is None:
            unresolved.append({"name": name, "reason": "unclassified binding"})
    return {"unresolved": unresolved}, uniforms, samplers


def _program_entry(repository: pathlib.Path, typed_rows: dict[str, dict[str, Any]], defines: dict[str, Any], effect: dict[str, Any], entry: dict[str, Any], old: bytes, new: bytes) -> dict[str, Any]:
    key = entry["program_key"]
    current_pass = _pass_index(effect, key)
    old_text = old.decode("utf-8")
    classification = "raw_exact" if old == new else "incompatible"
    old_token = _canonical_token_hash(old_text)
    new_token = _canonical_token_hash(new.decode("utf-8"))
    old_typed: Any = None
    new_typed: Any = None
    typed_record = typed_rows.get(key)
    if typed_record is None:
        raise CompatibilityError(f"{key}: missing authenticated typed emitter row")
    if typed_record.get("source_sha256") != _sha(old):
        raise CompatibilityError(f"{key}: typed manifest source hash mismatch")
    try:
        old_typed = _typed(old_text, key, defines)
        old_ir = _typed_hash(old_typed)
    except Exception as error:
        raise CompatibilityError(f"{key}: typed IR authority failed: {error}") from error
    new_ir = None
    if old != new:
        try:
            new_typed = _typed(new.decode("utf-8"), key, defines)
            new_ir = _typed_hash(new_typed)
        except Exception:
            new_ir = None
        if new_typed is not None and new_token == old_token and new_ir == old_ir:
            classification = "semantic_exact"
        else:
            classification = "incompatible"
    if classification == "semantic_exact":
        transform = "semantic-comment-only-v1"
    elif classification == "raw_exact":
        transform = typed_record.get("compatibility_transform", "none")
    else:
        transform = "none"
    abi, uniforms, samplers = _binding_abi(effect, current_pass, typed_record)
    typed_abi = typed_record["typed_abi"]
    physical_outputs = list(typed_abi["outputs"])
    logical_outputs = list(current_pass.get("outputs", {}).values())
    output_mismatch = len(logical_outputs) != len(physical_outputs)
    outputs = [{"slot": index, "physical_name": physical, "logical_route": logical_outputs[index] if index < len(logical_outputs) else None,
                "cpp_type": "glsl::Vec4"} for index, physical in enumerate(physical_outputs)]
    reasons: list[dict[str, str]] = []
    if classification == "incompatible":
        reasons.append({"code": "source_incompatible", "detail": "pinned source is not raw- or dual-semantic-equivalent"})
    if abi["unresolved"]:
        reasons.extend({"code": "unclassified_binding", "detail": item["name"]} for item in abi["unresolved"])
    if output_mismatch:
        reasons.append({"code": "output_abi_mismatch", "detail": f"physical={len(physical_outputs)} logical={len(logical_outputs)}"})
    draw_mode = current_pass.get("drawMode", "fragment")
    if draw_mode not in SUPPORTED_DRAW_MODES:
        reasons.append({"code": "unsupported_draw_mode", "detail": str(draw_mode)})
    if len(outputs) > 1:
        reasons.append({"code": "unsupported_output_count", "detail": str(len(outputs))})
    if effect.get("domain", "image") != "image":
        reasons.append({"code": "unsupported_dimensionality", "detail": str(effect.get("domain"))})
    status = "compatible" if not reasons else "incompatible"
    factory = typed_record.get("factory")
    extent = _extent(effect, current_pass, logical_outputs[0] if logical_outputs else "outputTex")
    return {
        "program_key": key, "effect_id": entry["effect_id"], "program": entry["program"],
        "source": entry["source"], "old_raw_sha256": _sha(old), "old_raw_bytes": len(old),
        "new_raw_sha256": _sha(new), "new_raw_bytes": len(new),
        "source_classification": classification,
        "semantic": {"old_token_sha256": old_token, "new_token_sha256": new_token,
                      "old_typed_ir_sha256": old_ir,
                      "new_typed_ir_sha256": old_ir if classification == "raw_exact" else new_ir},
        "compatibility_transform": transform,
        "uniforms": uniforms, "samplers": samplers,
        "outputs": outputs,
        "output_abi": {"cardinality": len(outputs), "logical_routes": logical_outputs,
                       "physical_names": physical_outputs, "canonical_slots": list(range(len(outputs)),),
                       "extent": extent, "single_output_canonical": len(outputs) == 1},
        "derivative_use": bool(typed_abi["uses_derivatives"]),
        "draw_mode": draw_mode, "dimensionality": effect.get("domain", "image"),
        "factory": {"canonical": factory, "legacy_public": factory,
                     "typed_manifest_output": typed_record.get("output"),
                     "typed_manifest_output_sha256": typed_record.get("output_sha256"),
                     "emitted_factory": typed_record.get("emitted_factory"),
                     "route": typed_record.get("factory_route")},
        "typed_abi_sha256": _sha(_encoded(typed_abi)),
        "capabilities": list(typed_record.get("capabilities", [])),
        "status": status, "reasons": reasons,
        "authority_pass": {"name": current_pass.get("name"), "inputs": current_pass.get("inputs", {}),
                            "outputs": current_pass.get("outputs", {}), "uniforms": current_pass.get("uniforms", {}),
                            "blend": current_pass.get("blend", False), "repeat": current_pass.get("repeat")},
    }


def _shader_path(entry: dict[str, Any]) -> str:
    relative = pathlib.PurePosixPath(entry["source"]).relative_to("sources")
    parts = relative.parts
    return pathlib.PurePosixPath("shaders", "effects", *parts[:2], "glsl", parts[-1]).as_posix()


def _scatter_source_entry(entry: dict[str, Any], old: bytes, new: bytes) -> dict[str, Any]:
    classification = "raw_exact" if old == new else "incompatible"
    return {
        "program_key": entry["program_key"], "effect_id": entry["effect_id"],
        "program": entry["program"], "source": entry["source"],
        "old_raw_sha256": _sha(old), "old_raw_bytes": len(old),
        "new_raw_sha256": _sha(new), "new_raw_bytes": len(new),
        "source_classification": classification,
        "semantic": None, "compatibility_transform": "none",
        "uniforms": [], "samplers": [],
        "outputs": [{"slot": 0, "physical_name": "fragColor",
                      "logical_route": "wormhole_accum", "cpp_type": "glsl::Vec4"}],
        "output_abi": {"cardinality": 1, "logical_routes": ["wormhole_accum"],
                       "physical_names": ["fragColor"], "canonical_slots": [0],
                       "extent": {"width": "screen", "height": "screen", "format": "rgba8unorm"},
                       "single_output_canonical": True},
        "derivative_use": False, "draw_mode": "points", "dimensionality": "image",
        "factory": {"canonical": None, "legacy_public": None,
                     "typed_manifest_output": None, "typed_manifest_output_sha256": None},
        "capabilities": [], "status": "registered", "reasons": [],
        "authority_pass": {},
    }


def _normalized_binding_abi(uniforms: list[dict[str, Any]], samplers: list[dict[str, Any]]) -> dict[str, Any]:
    def normalize(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{"name": item["name"], "cpp_type": item["cpp_type"], "source": item["source"]}
                for item in items]
    return {"uniforms": normalize(uniforms), "samplers": normalize(samplers)}


def _legacy_factory_body(text: str, name: str) -> str:
    match = re.search(
        rf"(BoundKernel\s+{re.escape(name)}\s*\([^)]*\)\s*\{{.*?\n\}})", text, re.DOTALL)
    if match is None:
        raise CompatibilityError(f"legacy factory body missing: {name}")
    return match.group(1)


def _legacy_factory_abi(text: str, body: str, key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    uniforms: list[dict[str, Any]] = []
    samplers: list[dict[str, Any]] = []
    calls = re.compile(
        r"(?:bindings|b)\.texture\(\"(?P<texture>[^\"]+)\"\)"
        r"|(?:bindings|b)\.get_or<(?P<get_or_type>[^>]+)>\(\"(?P<get_or_name>[^\"]+)\""
        r"|(?:bindings|b)\.get<(?P<get_type>[^>]+)>\(\"(?P<get_name>[^\"]+)\"\)"
        r"|(?:bindings|b)\.get_number\(\"(?P<number_name>[^\"]+)\"\)")
    for match in calls.finditer(body):
        if match.group("texture") is not None:
            samplers.append({"name": match.group("texture"), "cpp_type": "const Surface&", "source": "resource"})
        elif match.group("get_or_name") is not None:
            uniforms.append({"name": match.group("get_or_name"), "cpp_type": match.group("get_or_type"), "source": "effect_parameter"})
        elif match.group("get_name") is not None:
            uniforms.append({"name": match.group("get_name"), "cpp_type": match.group("get_type"), "source": "effect_parameter"})
        else:
            uniforms.append({"name": match.group("number_name"), "cpp_type": "double", "source": "effect_parameter"})
    if not uniforms and not samplers:
        raise CompatibilityError(f"{key}: legacy factory binding ABI is empty")
    callback_matches = re.findall(r"BoundKernel\s*\([^;\n]*,\s*&\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", body)
    if not callback_matches:
        raise CompatibilityError(f"{key}: legacy factory callback is missing")
    callback = callback_matches[-1]
    if not re.search(rf"\bvoid\s+{re.escape(callback)}\s*\([^)]*(?:glsl::)?Vec4&\s+\w+[^)]*\)", text):
        raise CompatibilityError(f"{key}: legacy factory output ABI is missing")
    binding_abi = _normalized_binding_abi(uniforms, samplers)
    output_abi = {"cardinality": 1, "cpp_type": "glsl::Vec4"}
    return binding_abi, output_abi


def _canonical_factory_abi(row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    # The public canonical ABI uses a stable name order for the legacy
    # equivalence contract. The implementation parser below preserves the
    # source call order and must match this explicit order; it must not sort
    # the implementation evidence after extraction.
    binding_abi = _normalized_binding_abi(
        sorted(row["uniforms"], key=lambda item: item["name"]),
        sorted(row["samplers"], key=lambda item: item["name"]),
    )
    output_abi = {
        "cardinality": row["output_abi"].get("cardinality"),
        "cpp_type": "glsl::Vec4" if row["output_abi"].get("cardinality") == 1 else None,
    }
    return binding_abi, output_abi


def _canonical_row_projection(row: dict[str, Any]) -> dict[str, Any]:
    projection = copy.deepcopy(row)
    projection.pop("row_kind", None)
    factory = projection.get("factory")
    if isinstance(factory, dict):
        factory.pop("legacy", None)
        factory.pop("legacy_public", None)
    return projection


def _legacy_factories(repository: pathlib.Path, rows: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Discover and authenticate legacy factories from independently parsed source."""
    result: dict[str, dict[str, Any]] = {}
    directory = repository / "src/generated"
    if directory.is_symlink() or not directory.is_dir():
        raise CompatibilityError("legacy generated factory directory missing")
    for path in sorted(directory.glob("*.cpp")):
        text = path.read_text(encoding="utf-8")
        program_match = re.search(r"^// Program: ([^\n]+)$", text, re.MULTILINE)
        source_match = re.search(r"^// Source SHA-256: ([0-9a-f]{64})$", text, re.MULTILINE)
        factory_match = re.search(r"\bBoundKernel (bind_[A-Za-z0-9_]+)\(const glsl::Bindings&", text)
        if not (program_match and source_match and factory_match):
            continue
        key = program_match.group(1)
        if key not in rows:
            raise CompatibilityError(f"legacy factory has no canonical row: {key}")
        if key in result:
            raise CompatibilityError(f"duplicate legacy factory metadata: {key}")
        row = rows[key]
        if source_match.group(1) != row["old_raw_sha256"]:
            raise CompatibilityError(f"legacy factory source drift: {key}")
        body = _legacy_factory_body(text, factory_match.group(1))
        binding_abi, output_abi = _legacy_factory_abi(text, body, key)
        expected_binding, expected_output = _canonical_factory_abi(row)
        if binding_abi != expected_binding or output_abi != expected_output:
            raise CompatibilityError(f"legacy factory ABI mismatch: {key}")
        result[key] = {
            "name": factory_match.group(1), "path": path.relative_to(repository).as_posix(),
            "source_sha256": _sha(path.read_bytes()),
            "source_program_sha256": source_match.group(1),
            "canonical_name": row["factory"]["canonical"],
            "implementation_identity": "source-body-bound",
            "body_sha256": _sha(body.encode()),
            "binding_abi": binding_abi,
            "binding_abi_sha256": _sha(_encoded(binding_abi)),
            "output_abi": output_abi,
            "output_abi_sha256": _sha(_encoded(output_abi)),
        }
    return result


def _custom_factory_route(repository: pathlib.Path, key: str) -> dict[str, Any]:
    if key != "classicNoisedeck/bitEffects:bitEffects":
        raise CompatibilityError(f"unknown custom factory route: {key}")
    source_path = repository / "src/effects/bit_effects.cpp"
    if source_path.is_symlink() or not source_path.is_file():
        raise CompatibilityError("custom factory source missing")
    source = source_path.read_text(encoding="utf-8")
    calls = []
    for match in re.finditer(r"b\.get<([^>]+)>\(\"([^\"]+)\"\)|b\.get_number\(\"([^\"]+)\"\)", source):
        cpp_type, typed_name, number_name = match.groups()
        calls.append({"name": typed_name or number_name,
                      "cpp_type": cpp_type or "double", "source": "custom_adapter"})
    if len(calls) != 20:
        raise CompatibilityError(f"{key}: custom factory binding ABI census drift")
    if not re.search(r"BoundKernel\s+bind_bit_effects\s*\([^)]*\)", source) \
            or not re.search(r"\bVec4&\s+\w+", source):
        raise CompatibilityError(f"{key}: custom factory identity/output ABI missing")
    emitted = "bind_" + key.replace("/", "_").replace(":", "_")
    return {
        "kind": "custom_adapter", "factory": "noisemaker::effects::bind_bit_effects",
        "emitted_factory": emitted, "source": source_path.relative_to(repository).as_posix(),
        "source_sha256": _sha(source_path.read_bytes()),
        "binding_abi": {"uniforms": calls, "samplers": []},
        "output_abi": {"cardinality": 1, "cpp_type": "glsl::Vec4"},
    }


def _factory_evidence(repository: pathlib.Path, typed_rows: dict[str, dict[str, Any]],
                     rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    selected: dict[str, dict[str, Any]] = {}
    for key in sorted(rows):
        if key == SCATTER_KEY:
            continue
        typed = typed_rows.get(key)
        if not isinstance(typed, dict) or not isinstance(typed.get("factory_route"), dict):
            raise CompatibilityError(f"{key}: selected factory evidence missing")
        route = typed["factory_route"]
        if route.get("kind") == "custom_adapter":
            expected_route = _custom_factory_route(repository, key)
            if route != expected_route:
                raise CompatibilityError(f"{key}: typed custom factory route drift")
        elif route.get("kind") == "typed_emitter":
            source = repository / str(route.get("source", ""))
            if source.is_symlink() or not source.is_file() or _sha(source.read_bytes()) != route.get("source_sha256"):
                raise CompatibilityError(f"{key}: typed factory source drift")
        else:
            raise CompatibilityError(f"{key}: unknown selected factory route")
        selected[key] = {"canonical": typed.get("factory"),
                         "emitted_factory": typed.get("emitted_factory"), "route": route}
    return {"selected": selected, "legacy": _legacy_factories(repository, rows)}


def generate(*, cpu_root: pathlib.Path, shader_git: pathlib.Path, repository: pathlib.Path = ROOT) -> dict[str, Any]:
    cpu_root = cpu_root.resolve(); shader_git = shader_git.resolve(); repository = repository.resolve()
    authority = _authority(cpu_root, shader_git)
    corpus = check_corpus.validate_corpus(repository)
    corpus_root = check_corpus._corpus_root(repository)
    manifest = check_corpus._load_json(corpus_root / "manifest.json", "manifest")
    entries = check_corpus._validate_manifest(manifest)
    corpus_keys = {item["program_key"] for item in entries}
    authenticated_typed = _authenticated_typed_manifest(repository)
    typed_rows = _typed_manifest(repository, authenticated_typed, corpus_keys)
    metadata = check_corpus._load_json(corpus_root / "metadata.json", "metadata")
    defines_by_key = {
        key: check_semantics._metadata_defaults(metadata, key)
        for key in typed_rows
    }
    effect_records = _node_effect_records(cpu_root)
    effects = {item["id"]: item for item in effect_records}
    source_rows: list[dict[str, Any]] = []
    for entry in entries:
        key = entry["program_key"]
        effect = effects.get(entry["effect_id"])
        if effect is None:
            raise CompatibilityError(f"{key}: authority effect missing")
        current_pass = _pass_index(effect, key)
        old = (corpus_root / entry["source"]).read_bytes()
        new = _git_blob(shader_git, UPSTREAM_REVISION, _shader_path(entry))
        if key == SCATTER_KEY:
            source_rows.append(_scatter_source_entry(entry, old, new))
        else:
            source_rows.append(_program_entry(repository, typed_rows, defines_by_key.get(key, {}), effect, entry, old, new))
    by_key = {item["program_key"]: item for item in source_rows}
    if len(by_key) != 212 or SCATTER_KEY not in by_key:
        raise CompatibilityError("corpus source closure cardinality drift")
    fragment_unique = [item for item in source_rows if item["program_key"] != SCATTER_KEY]
    if len(fragment_unique) != 211:
        raise CompatibilityError("fragment unique census drift")
    factory_evidence = _factory_evidence(repository, typed_rows, by_key)
    legacy_factories = factory_evidence["legacy"]
    duplicate_keys = sorted(legacy_factories)
    if duplicate_keys != ["filter/invert:inv", "synth/solid:solid"]:
        raise CompatibilityError("legacy factory census drift")
    fragment_rows = list(fragment_unique)
    for key in duplicate_keys:
        duplicate = json.loads(json.dumps(by_key[key]))
        duplicate["row_kind"] = "legacy_duplicate"
        duplicate["factory"]["legacy_public"] = legacy_factories[key]["name"]
        duplicate["factory"]["legacy"] = legacy_factories[key]
        fragment_rows.append(duplicate)
    for item in fragment_rows:
        item.setdefault("row_kind", "canonical")
    if len(fragment_rows) != 213:
        raise CompatibilityError("fragment row census drift")
    # Every reference pass gets one and only one status.  The source corpus is
    # the executable fragment closure; the remaining authority passes are
    # explicit missing rows, never silently omitted.
    reference_passes: list[dict[str, Any]] = []
    seen_pass_keys: Counter[str] = Counter()
    for effect in effect_records:
        for index, current_pass in enumerate(effect.get("passes", [])):
            key = f"{effect['id']}:{current_pass['program']}"
            seen_pass_keys[key] += 1
            if key == SCATTER_KEY:
                status, reasons = "scatter", [{"code": "explicit_scatter_adapter", "detail": "filter/wormhole:deposit"}]
            elif key in by_key:
                status, reasons = by_key[key]["status"], by_key[key]["reasons"]
            else:
                status, reasons = "missing", [{"code": "missing_backend_program", "detail": key}]
            reference_passes.append({"effect_id": effect["id"], "pass_index": index, "pass_name": current_pass.get("name"),
                                     "program_key": key, "status": status, "reasons": reasons})
    if len(reference_passes) != 305 or len(seen_pass_keys) != 295:
        raise CompatibilityError("reference pass status cardinality drift")
    scatter = by_key[SCATTER_KEY]
    scatter_contract = {
        "program_key": SCATTER_KEY, "status": "registered", "adapter": "noisemaker::scatter::wormhole::adapter",
        "registry": "noisemaker::scatter::resolve_scatter_adapter", "draw_mode": "points", "count": "input",
        "input_texture": "inputTex", "destination_mutation": "in_place_accumulate",
        "uniforms": [{"name": name, "cpp_type": "double", "source": "effect_parameter"}
                     for name in ("kink", "stride", "rotation", "wrap")],
        "binding_abi": {"uniforms": [{"name": name, "cpp_type": "double", "source": "effect_parameter"}
                                       for name in ("kink", "stride", "rotation", "wrap")],
                        "samplers": []},
        "output_route": "wormhole_accum", "blend": True,
        "source": scatter["source"], "old_raw_sha256": scatter["old_raw_sha256"],
        "new_raw_sha256": scatter["new_raw_sha256"], "source_classification": scatter["source_classification"],
        "output_abi": scatter["output_abi"], "dimensionality": scatter["dimensionality"],
        "reasons": [],
    }
    classifications = Counter(item["source_classification"] for item in source_rows)
    incompatible_keys = sorted(item["program_key"] for item in source_rows if item["source_classification"] == "incompatible")
    document = {
        "schema": "noisemaker-cpp.backend-compatibility.v1",
        "corpus_revision": CORPUS_REVISION,
        "authority": authority,
        "counts": {
            "definitions": len(effect_records), "reference_passes": len(reference_passes),
            "reference_program_keys": len(seen_pass_keys), "fragment_rows": len(fragment_rows),
            "unique_fragment_keys": len(fragment_unique), "duplicate_fragment_keys": duplicate_keys,
            "raw_exact": classifications["raw_exact"], "semantic_exact": classifications["semantic_exact"],
            "incompatible": classifications["incompatible"], "incompatible_keys": incompatible_keys,
            "status_compatible": sum(item["status"] == "compatible" for item in fragment_unique),
            "status_incompatible": sum(item["status"] == "incompatible" for item in fragment_unique),
        },
        "fragments": fragment_rows,
        "canonical_programs": sorted(fragment_unique, key=lambda item: item["program_key"]),
        "reference_passes": reference_passes,
        "reference_key_closure": sorted(seen_pass_keys),
        "scatter": scatter_contract,
    }
    validate_document(document, expected_source_hashes={
        item["program_key"]: item["new_raw_sha256"] for item in source_rows
    }, repository=repository, factory_evidence=factory_evidence)
    return document


def _encoded(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_BINDING_SOURCES = frozenset({
    "effect_parameter", "pass_literal", "pass_derived",
    "reserved_runtime_state", "resource", "external_texture",
})


def validate_document(document: dict[str, Any], *, expected_source_hashes: dict[str, str] | None = None,
                      repository: pathlib.Path = ROOT,
                      factory_evidence: dict[str, Any] | None = None) -> None:
    """Validate persisted admission evidence, failing closed on edits."""
    if document.get("schema") != "noisemaker-cpp.backend-compatibility.v1":
        raise CompatibilityError("backend compatibility schema mismatch")
    counts = document.get("counts")
    fragments = document.get("fragments")
    canonical = document.get("canonical_programs")
    references = document.get("reference_passes")
    scatter = document.get("scatter")
    if not isinstance(counts, dict) or not isinstance(fragments, list) or not isinstance(canonical, list) \
            or not isinstance(references, list) or not isinstance(scatter, dict):
        raise CompatibilityError("backend compatibility sections are malformed")
    if len(fragments) != 213 or len(canonical) != 211:
        raise CompatibilityError("backend compatibility census cardinality drift")
    canonical_keys = [item.get("program_key") for item in canonical]
    if len(set(canonical_keys)) != len(canonical_keys) or any(not isinstance(key, str) for key in canonical_keys):
        raise CompatibilityError("forged or duplicate canonical program key")
    if scatter.get("program_key") != SCATTER_KEY or scatter.get("status") != "registered":
        raise CompatibilityError("scatter registration missing or forged")
    if len(references) != 305 or any(not isinstance(item, dict) for item in references):
        raise CompatibilityError("reference pass status closure drift")
    allowed_statuses = {"compatible", "incompatible", "missing", "scatter"}
    reference_keys = document.get("reference_key_closure")
    if not isinstance(reference_keys, list) or len(reference_keys) != 295 \
            or sorted(set(reference_keys)) != sorted(reference_keys):
        raise CompatibilityError("reference key closure missing or forged")
    if {item.get("program_key") for item in references} != set(reference_keys):
        raise CompatibilityError("reference key membership drift")
    for item in references:
        if not isinstance(item.get("effect_id"), str) or not isinstance(item.get("pass_index"), int) \
                or item["pass_index"] < 0 or not isinstance(item.get("pass_name"), str):
            raise CompatibilityError("reference pass identity malformed")
        if item.get("status") not in allowed_statuses or not isinstance(item.get("program_key"), str):
            raise CompatibilityError("unknown reference pass status or key")
        if not isinstance(item.get("reasons"), list):
            raise CompatibilityError("reference pass reasons malformed")
        for reason in item["reasons"]:
            if not isinstance(reason, dict) or not isinstance(reason.get("code"), str) \
                    or not isinstance(reason.get("detail"), str):
                raise CompatibilityError("reference pass reason malformed")
        key = item["program_key"]
        if key in canonical_keys:
            expected_status = next(row["status"] for row in canonical if row["program_key"] == key)
            expected_reasons = next(row["reasons"] for row in canonical if row["program_key"] == key)
        elif key == SCATTER_KEY:
            expected_status = "scatter"
            expected_reasons = [{"code": "explicit_scatter_adapter", "detail": SCATTER_KEY}]
        else:
            expected_status = "missing"
            expected_reasons = [{"code": "missing_backend_program", "detail": key}]
        if item["status"] != expected_status or item["reasons"] != expected_reasons:
            raise CompatibilityError("reference pass status/reason is not recomputed closure")
    fragment_keys = [item.get("program_key") for item in fragments]
    if set(fragment_keys) != set(canonical_keys) or len(fragment_keys) != 213:
        raise CompatibilityError("fragment row closure drift")
    if any(not isinstance(item, dict) or item.get("program_key") not in set(canonical_keys)
           or item.get("row_kind") not in {"canonical", "legacy_duplicate"}
           for item in fragments):
        raise CompatibilityError("fragment row contents malformed")
    duplicate_fragment_keys = sorted(item.get("program_key") for item in fragments
                                     if item.get("row_kind") == "legacy_duplicate")
    if duplicate_fragment_keys != sorted(counts.get("duplicate_fragment_keys", [])) \
            or sorted(counts.get("duplicate_fragment_keys", [])) != ["filter/invert:inv", "synth/solid:solid"]:
        raise CompatibilityError("legacy duplicate row evidence drift")
    canonical_by_key = {row["program_key"]: row for row in canonical}
    for row in fragments:
        if row.get("row_kind") != "legacy_duplicate":
            continue
        canonical_row = canonical_by_key.get(row.get("program_key"))
        if canonical_row is None or _canonical_row_projection(row) != _canonical_row_projection(canonical_row):
            raise CompatibilityError("legacy duplicate differs from canonical row")
    if factory_evidence is None:
        typed_manifest = _authenticated_typed_manifest(repository)
        typed_programs = typed_manifest.get("programs")
        if not isinstance(typed_programs, list):
            raise CompatibilityError("authenticated typed factory evidence missing")
        typed_rows = {item.get("program_key"): item for item in typed_programs if isinstance(item, dict)}
        factory_evidence = _factory_evidence(
            repository, typed_rows, {row.get("program_key"): row for row in canonical})
    selected_evidence = factory_evidence.get("selected") if isinstance(factory_evidence, dict) else None
    legacy_evidence = factory_evidence.get("legacy") if isinstance(factory_evidence, dict) else None
    if not isinstance(selected_evidence, dict) or not isinstance(legacy_evidence, dict):
        raise CompatibilityError("authenticated factory evidence missing")
    for row in canonical:
        if not isinstance(row, dict) or row.get("status") not in {"compatible", "incompatible"} \
                or not isinstance(row.get("source"), str) \
                or not _SHA256.fullmatch(str(row.get("old_raw_sha256", ""))) \
                or not _SHA256.fullmatch(str(row.get("new_raw_sha256", ""))):
            raise CompatibilityError("source hash drift or malformed source row")
        if not row["source"].startswith("sources/") or ".." in pathlib.PurePosixPath(row["source"]).parts:
            raise CompatibilityError("source path escapes authenticated corpus")
        if expected_source_hashes is not None and row["new_raw_sha256"] != expected_source_hashes.get(row["program_key"]):
            raise CompatibilityError("source object drift")
        semantic = row.get("semantic")
        if not isinstance(semantic, dict) or not _SHA256.fullmatch(str(semantic.get("old_token_sha256", ""))) \
                or not _SHA256.fullmatch(str(semantic.get("old_typed_ir_sha256", ""))):
            raise CompatibilityError("semantic evidence malformed")
        if row.get("source_classification") == "semantic_exact":
            if not _SHA256.fullmatch(str(semantic.get("new_token_sha256", ""))) \
                    or not _SHA256.fullmatch(str(semantic.get("new_typed_ir_sha256", ""))) \
                    or semantic["new_token_sha256"] != semantic["old_token_sha256"] \
                    or semantic["new_typed_ir_sha256"] != semantic["old_typed_ir_sha256"]:
                raise CompatibilityError("semantic equality evidence incomplete")
        reasons = row.get("reasons")
        if not isinstance(reasons, list) or (row.get("status") == "compatible" and reasons) \
                or (row.get("status") != "compatible" and not reasons):
            raise CompatibilityError("status/reason admission mismatch")
        if any(not isinstance(reason, dict) or not isinstance(reason.get("code"), str)
               or not isinstance(reason.get("detail"), str) for reason in reasons):
            raise CompatibilityError("fragment reason malformed")
        if not isinstance(row.get("uniforms"), list) or not isinstance(row.get("samplers"), list):
            raise CompatibilityError("binding ABI malformed")
        if row.get("draw_mode") not in SUPPORTED_DRAW_MODES or row.get("dimensionality") != "image":
            raise CompatibilityError("unsupported draw mode or dimensionality")
        for binding in [*row["uniforms"], *row["samplers"]]:
            if not isinstance(binding, dict) or binding.get("source") not in _BINDING_SOURCES:
                raise CompatibilityError("unclassified binding in ABI")
        output_abi = row.get("output_abi")
        outputs = row.get("outputs")
        if not isinstance(output_abi, dict) or not isinstance(outputs, list) \
                or output_abi.get("cardinality") != len(outputs) \
                or output_abi.get("canonical_slots") != list(range(len(outputs))) \
                or output_abi.get("physical_names") != [item.get("physical_name") for item in outputs] \
                or output_abi.get("logical_routes") != [item.get("logical_route") for item in outputs]:
            raise CompatibilityError("output ABI mismatch")
        extent = output_abi.get("extent")
        if not isinstance(extent, dict) or set(extent) != {"width", "height", "format"}:
            raise CompatibilityError("output extent ABI malformed")
        factory = row.get("factory")
        if not isinstance(factory, dict) or not isinstance(factory.get("canonical"), str) \
                or not _SHA256.fullmatch(str(factory.get("typed_manifest_output_sha256", ""))):
            raise CompatibilityError("factory authentication missing")
        route = factory.get("route")
        if not isinstance(route, dict) or route.get("factory") != factory.get("canonical") \
                or route.get("kind") not in {"typed_emitter", "custom_adapter"} \
                or not isinstance(route.get("source"), str) \
                or not _SHA256.fullmatch(str(route.get("source_sha256", ""))):
            raise CompatibilityError("factory route authentication missing")
        route_path = repository / route["source"]
        if route_path.is_symlink() or not route_path.is_file() or _sha(route_path.read_bytes()) != route["source_sha256"]:
            raise CompatibilityError("factory implementation source drift")
        expected_factory = selected_evidence.get(row["program_key"])
        if not isinstance(expected_factory, dict) \
                or factory.get("canonical") != expected_factory.get("canonical") \
                or factory.get("emitted_factory") != expected_factory.get("emitted_factory") \
                or route != expected_factory.get("route"):
            raise CompatibilityError("selected factory evidence drift")
        if not _SHA256.fullmatch(str(row.get("typed_abi_sha256", ""))):
            raise CompatibilityError("typed emitter ABI evidence missing")
    for row in fragments:
        if row.get("row_kind") != "legacy_duplicate":
            continue
        factory = row.get("factory")
        legacy = factory.get("legacy") if isinstance(factory, dict) else None
        expected_legacy = legacy_evidence.get(row.get("program_key"))
        if not isinstance(legacy, dict) or not isinstance(expected_legacy, dict) \
                or legacy != expected_legacy \
                or legacy.get("canonical_name") != factory.get("canonical") \
                or factory.get("legacy_public") != expected_legacy.get("name"):
            raise CompatibilityError("legacy factory equivalence evidence missing")
    if not isinstance(scatter.get("source"), str) or not scatter["source"].startswith("sources/") \
            or ".." in pathlib.PurePosixPath(scatter["source"]).parts \
            or not _SHA256.fullmatch(str(scatter.get("old_raw_sha256", ""))) \
            or not _SHA256.fullmatch(str(scatter.get("new_raw_sha256", ""))) \
            or scatter.get("source_classification") not in {"raw_exact", "semantic_exact", "incompatible"} \
            or not isinstance(scatter.get("binding_abi"), dict) \
            or not isinstance(scatter.get("output_abi"), dict):
        raise CompatibilityError("scatter evidence bundle incomplete")
    if expected_source_hashes is not None and scatter["new_raw_sha256"] != expected_source_hashes.get(SCATTER_KEY):
        raise CompatibilityError("scatter source object drift")
    scatter_output = scatter["output_abi"]
    if scatter_output.get("cardinality") != 1 \
            or scatter_output.get("physical_names") != ["fragColor"] \
            or scatter_output.get("logical_routes") != ["wormhole_accum"] \
            or scatter_output.get("canonical_slots") != [0]:
        raise CompatibilityError("scatter output ABI mismatch")
    expected_scatter_bindings = [{"name": name, "cpp_type": "double", "source": "effect_parameter"}
                                 for name in ("kink", "stride", "rotation", "wrap")]
    if scatter.get("adapter") != "noisemaker::scatter::wormhole::adapter" \
            or scatter.get("registry") != "noisemaker::scatter::resolve_scatter_adapter" \
            or scatter.get("draw_mode") != "points" or scatter.get("dimensionality") != "image" \
            or scatter.get("count") != "input" or scatter.get("input_texture") != "inputTex" \
            or scatter.get("destination_mutation") != "in_place_accumulate" \
            or scatter.get("blend") is not True \
            or scatter.get("binding_abi") != {"uniforms": expected_scatter_bindings, "samplers": []} \
            or scatter.get("uniforms") != expected_scatter_bindings:
        raise CompatibilityError("scatter adapter contract forged")
    expected_counts = {
        "fragment_rows": len(fragments), "unique_fragment_keys": len(canonical),
        "reference_passes": len(references),
        "incompatible_keys": sorted(row["program_key"] for row in canonical
                                     if row.get("source_classification") == "incompatible"),
    }
    for name, value in expected_counts.items():
        if counts.get(name) != value:
            raise CompatibilityError(f"backend compatibility count drift: {name}")


def write(*, cpu_root: pathlib.Path, shader_git: pathlib.Path, repository: pathlib.Path = ROOT) -> None:
    data = _encoded(generate(cpu_root=cpu_root, shader_git=shader_git, repository=repository))
    target = repository / OUTPUT.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def check(*, cpu_root: pathlib.Path, shader_git: pathlib.Path, repository: pathlib.Path = ROOT) -> None:
    target = repository / OUTPUT.relative_to(ROOT)
    # Materialize the regenerated candidate in the system temporary area so a
    # failed check cannot mutate the checkout or leave a generated candidate in
    # the repository. Only the byte comparison is authoritative.
    expected = _encoded(generate(cpu_root=cpu_root, shader_git=shader_git, repository=repository))
    with tempfile.TemporaryDirectory(prefix="noisemaker-backend-compat-") as directory:
        candidate = pathlib.Path(directory) / "backend_compatibility.json"
        candidate.write_bytes(expected)
        if not target.is_file() or target.read_bytes() != candidate.read_bytes():
            raise CompatibilityError(f"backend compatibility manifest drift: {target}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-root", type=pathlib.Path, required=True)
    parser.add_argument("--shader-git", type=pathlib.Path, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")
    if not args.write and not args.check:
        parser.error("one of --write or --check is required")
    try:
        if args.write:
            write(cpu_root=args.cpu_root, shader_git=args.shader_git)
        else:
            check(cpu_root=args.cpu_root, shader_git=args.shader_git)
    except CompatibilityError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
