"""Validate the frozen CPU effect schema and emit a dependency-free C++ catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pathlib
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from tools.dsl import generate_backend_compatibility as backend

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_COMPATIBILITY = ROOT / "src/effects/generated/backend_compatibility.json"
CATALOG_SCHEMA = "noisemaker-cpp.cpu-effect-catalog.v1"
GENERATOR_SCHEMA = "noisemaker-cpp.effect-catalog-generator.v1"
BACKEND_SCHEMA = "noisemaker-cpp.backend-compatibility.v1"
CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
COMPATIBILITY_SHA256 = "aa79eb9c505811137a5bef5b08b12e80ae63769bd01c748730ff48a42b956580"
EFFECT_KEYS = frozenset({
    "id", "directoryName", "name", "namespace", "func", "kind", "domain", "tags",
    "description", "paramAliases", "params", "passes", "textures", "externalTexture",
    "outputTex3d", "outputGeo", "outputXyz", "outputVel", "outputRgba", "iterated", "loopRole",
})
PARAM_KEYS = frozenset({"type", "default", "define", "uniform", "zero", "enum", "choices", "min", "max", "texture", "colorModeUniform", "cpuOnly"})
PASS_KEYS = frozenset({"name", "program", "inputs", "outputs", "uniforms", "count", "repeat", "conditions", "viewport", "blend", "drawMode", "drawBuffers"})
TEXTURE_KEYS = frozenset({"width", "height", "format"})
DIMENSION_KEYS = frozenset({"default", "param", "paramDefault", "screenDivide", "inputOverride", "power"})


class CatalogError(ValueError):
    pass


def _decode(value: Any, context: str = "value") -> Any:
    if not isinstance(value, dict) or "$type" not in value:
        raise CatalogError(f"untyped value envelope in {context}")
    kind = value["$type"]
    if kind == "null":
        if set(value) != {"$type"}: raise CatalogError(f"malformed null envelope in {context}")
        return None
    if kind in {"string", "boolean"}:
        if set(value) != {"$type", "value"}: raise CatalogError(f"malformed {kind} envelope in {context}")
        if kind == "string" and not isinstance(value["value"], str): raise CatalogError(f"malformed string envelope in {context}")
        if kind == "boolean" and not isinstance(value["value"], bool): raise CatalogError(f"malformed boolean envelope in {context}")
        return value["value"]
    if kind == "number":
        if set(value) != {"$type", "value"}: raise CatalogError(f"malformed number envelope in {context}")
        number = value["value"]
        if number == "NaN": return math.nan
        if number == "+Infinity": return math.inf
        if number == "-Infinity": return -math.inf
        if number == "-0": return -0.0
        if isinstance(number, (int, float)) and not isinstance(number, bool): return number
        raise CatalogError(f"malformed number envelope in {context}")
    if kind == "array":
        if set(value) != {"$type", "items"} or not isinstance(value["items"], list): raise CatalogError(f"malformed array envelope in {context}")
        return [_decode(item, f"{context}[{index}]") for index, item in enumerate(value["items"])]
    if kind == "object":
        if set(value) != {"$type", "entries"} or not isinstance(value["entries"], list): raise CatalogError(f"malformed object envelope in {context}")
        result: dict[str, Any] = {}
        for index, entry in enumerate(value["entries"]):
            if not isinstance(entry, list) or len(entry) != 2 or not isinstance(entry[0], str): raise CatalogError(f"malformed object entry in {context}[{index}]")
            if entry[0] in result: raise CatalogError(f"duplicate object key in {context}: {entry[0]}")
            result[entry[0]] = _decode(entry[1], f"{context}.{entry[0]}")
        return result
    raise CatalogError(f"unknown value envelope type in {context}: {kind}")


def _check_keys(value: Any, allowed: frozenset[str], context: str) -> None:
    if not isinstance(value, dict):
        raise CatalogError(f"{context} must be an object")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise CatalogError(f"unknown schema field(s) in {context}: {', '.join(unknown)}")


def load_export(path: pathlib.Path) -> list[dict[str, Any]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CatalogError(f"unable to read CPU catalog export: {error}") from error
    _check_keys(document, frozenset({"schema", "records"}), "catalog export")
    if document.get("schema") != CATALOG_SCHEMA or not isinstance(document.get("records"), list):
        raise CatalogError("CPU catalog export schema mismatch")
    records = []
    for index, record in enumerate(document["records"]):
        if not isinstance(record, dict): raise CatalogError(f"effect[{index}] must be an object")
        records.append({key: _decode(value, f"effect[{index}].{key}") for key, value in record.items()})
    if len(records) != 205:
        raise CatalogError(f"CPU definition count drift: {len(records)}")
    for index, effect in enumerate(records):
        _check_keys(effect, EFFECT_KEYS, f"effect[{index}]")
        for name, parameter in (effect.get("params") or {}).items():
            _check_keys(parameter, PARAM_KEYS, f"effect[{index}].params.{name}")
        for pass_index, current_pass in enumerate(effect.get("passes") or []):
            _check_keys(current_pass, PASS_KEYS, f"effect[{index}].passes[{pass_index}]")
        for name, texture in (effect.get("textures") or {}).items():
            _check_keys(texture, TEXTURE_KEYS, f"effect[{index}].textures.{name}")
            for dimension_name in ("width", "height"):
                dimension = texture.get(dimension_name)
                if isinstance(dimension, dict):
                    _check_keys(dimension, DIMENSION_KEYS, f"effect[{index}].textures.{name}.{dimension_name}")
    return records


def export_records(cpu_root: pathlib.Path) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="noisemaker-catalog-export-") as directory:
        output = pathlib.Path(directory) / "catalog.json"
        exporter = ROOT / "tools/dsl/export_cpu_catalog.mjs"
        result = subprocess.run(["node", str(exporter), "--cpu-root", str(cpu_root), "--output", str(output)],
                                check=False, text=True, capture_output=True)
        if result.returncode:
            detail = result.stderr.strip() or result.stdout.strip()
            raise CatalogError(f"CPU catalog export failed: {detail}")
        return load_export(output)


def _authority(cpu_root: pathlib.Path, shader_git: pathlib.Path, compatibility: dict[str, Any]) -> dict[str, Any]:
    try:
        authority = backend._authority(cpu_root, shader_git)
    except Exception as error:
        raise CatalogError(f"CPU/upstream authority lock rejected: {error}") from error
    persisted = compatibility.get("authority")
    if not isinstance(persisted, dict):
        raise CatalogError("compatibility authority provenance missing")
    for key in ("cpu_behavioral_file_count", "cpu_behavioral_lock", "cpu_package_lock_sha256", "cpu_package_sha256", "cpu_source_lock_sha256", "source_lock_sha256", "upstream_package_lock_sha256", "upstream_package_sha256", "upstream_revision", "upstream_tree"):
        if authority.get(key) != persisted.get(key):
            raise CatalogError(f"compatibility authority mismatch: {key}")
    if compatibility.get("corpus_revision") != CORPUS_REVISION:
        raise CatalogError("compatibility corpus revision mismatch")
    # Content-addressed on purpose: the behavioral lock identifies the exact
    # authority bytes, works for git and non-git roots alike, and never falls
    # back silently to a second meaning the way a failed `git rev-parse` did.
    authority["cpu_revision"] = authority["cpu_behavioral_lock"]
    return authority


def _validate_compatibility(compatibility: dict[str, Any], records: list[dict[str, Any]], compatibility_path: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Authenticate and join every backend status to every authority pass."""
    try:
        if hashlib.sha256(compatibility_path.read_bytes()).hexdigest() != COMPATIBILITY_SHA256:
            raise CatalogError("compatibility manifest SHA-256 mismatch")
    except OSError as error:
        raise CatalogError(f"unable to read compatibility manifest: {error}") from error
    try:
        backend.validate_document(compatibility, repository=ROOT)
    except Exception as error:
        raise CatalogError(f"compatibility manifest structural validation failed: {error}") from error
    canonical = compatibility.get("canonical_programs")
    closure = compatibility.get("reference_key_closure")
    passes = compatibility.get("reference_passes")
    if not isinstance(canonical, list) or len({row.get("program_key") for row in canonical}) != len(canonical):
        raise CatalogError("compatibility canonical keys are not unique")
    if not isinstance(closure, list) or len(closure) != 295 or closure != sorted(set(closure)):
        raise CatalogError("compatibility key closure is not the exact ordered 295-key set")
    status_by_key = {row["program_key"]: row["status"] for row in canonical}
    scatter = compatibility.get("scatter")
    if not isinstance(scatter, dict) or scatter.get("program_key") != "filter/wormhole:deposit" or scatter.get("status") != "registered":
        raise CatalogError("compatibility scatter row is not exact")
    status_by_key[scatter["program_key"]] = "scatter"
    joined = {key: status_by_key.get(key, "missing") for key in closure}
    if any(status not in {"compatible", "incompatible", "missing", "scatter"} for status in joined.values()):
        raise CatalogError("compatibility joined status is unknown")
    expected_passes: list[tuple[str, int, str | None, str]] = []
    for effect in records:
        for index, current_pass in enumerate(effect.get("passes", [])):
            key = f"{effect['namespace']}/{effect['directoryName']}:{current_pass.get('program')}"
            expected_passes.append((effect["id"], index, current_pass.get("name"), key))
    if len(expected_passes) != 305 or not isinstance(passes, list) or len(passes) != len(expected_passes):
        raise CatalogError("compatibility reference pass cardinality drift")
    for row, expected in zip(passes, expected_passes):
        if (row.get("effect_id"), row.get("pass_index"), row.get("pass_name"), row.get("program_key")) != expected:
            raise CatalogError("compatibility reference pass ordering/identity drift")
        if row.get("status") != joined[expected[3]]:
            raise CatalogError(f"compatibility status mismatch for {expected[3]}")
        effect = next(effect for effect in records if effect["id"] == expected[0])
        current_pass = effect["passes"][expected[1]]
        expected_authority = {"blend": current_pass.get("blend", False), "inputs": current_pass.get("inputs", {}),
                              "name": current_pass.get("name"), "outputs": current_pass.get("outputs", {}),
                              "repeat": current_pass.get("repeat"), "uniforms": current_pass.get("uniforms", {})}
        if row.get("authority_pass") != expected_authority:
            raise CatalogError(f"compatibility authority pass projection mismatch for {expected[3]} pass {expected[1]}")
    if {row["program_key"] for row in passes} != set(closure):
        raise CatalogError("compatibility reference pass/key closure mismatch")
    pass_statuses = Counter(row["status"] for row in passes)
    backend_statuses = Counter(row["status"] for row in canonical)
    backend_statuses["scatter"] = 1
    effect_status: dict[str, list[str]] = defaultdict(list)
    for row in passes:
        effect_status[row["effect_id"]].append(row["status"])
    executable = sum(all(status in {"compatible", "scatter"} for status in values) for values in effect_status.values())
    derived = {"definitions": len(records), "passes": len(passes), "reference_program_keys": len(closure),
               "backend_programs": sum(backend_statuses.values()), "compatible_programs": backend_statuses["compatible"],
               "incompatible_programs": backend_statuses["incompatible"], "missing_passes": pass_statuses["missing"],
               "scatter_passes": pass_statuses["scatter"], "executable_definitions": executable,
               "incomplete_definitions": len(records) - executable}
    return compatibility, derived


def _number_text(value: float) -> str:
    if math.isnan(value):
        return "std::numeric_limits<double>::quiet_NaN()"
    if math.isinf(value):
        return "-std::numeric_limits<double>::infinity()" if value < 0 else "std::numeric_limits<double>::infinity()"
    if value == 0.0 and math.copysign(1.0, value) < 0:
        return "-0.0"
    text = repr(value)
    if text == "-0.0":
        return text
    if "e" not in text and "." not in text:
        text += ".0"
    return text


def _canonical_json_value(value: Any) -> Any:
    """Encode one value with exactly the export/load typed-envelope contract."""
    if value is None: return {"$type": "null"}
    if isinstance(value, bool): return {"$type": "boolean", "value": value}
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value): number: Any = "NaN"
        elif isinstance(value, float) and math.isinf(value): number = "-Infinity" if value < 0 else "+Infinity"
        elif isinstance(value, float) and value == 0.0 and math.copysign(1.0, value) < 0: number = "-0"
        else: number = value
        return {"$type": "number", "value": number}
    if isinstance(value, str): return {"$type": "string", "value": value}
    if isinstance(value, list): return {"$type": "array", "items": [_canonical_json_value(item) for item in value]}
    if isinstance(value, dict):
        return {"$type": "object", "entries": [[key, _canonical_json_value(item)] for key, item in value.items()]}
    raise CatalogError(f"cannot canonicalize value of type {type(value).__name__}")


def _canonical_record(record: dict[str, Any]) -> dict[str, Any]:
    """Keep record field keys observable while enveloping every field value."""
    return {key: _canonical_json_value(value) for key, value in record.items()}


def _cpp_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def cpp_value(value: Any) -> str:
    if value is None:
        return "Value::null()"
    if isinstance(value, bool):
        return f"Value::boolean_value({'true' if value else 'false'})"
    if isinstance(value, (int, float)):
        return f"Value::number_value({_number_text(float(value))})"
    if isinstance(value, str):
        return f"Value::string_value({_cpp_string(value)})"
    if isinstance(value, list):
        return "Value::array_value({" + ", ".join(cpp_value(item) for item in value) + "})"
    if isinstance(value, dict):
        return "Value::object_value({" + ", ".join(
            "{" + _cpp_string(str(key)) + ", " + cpp_value(child) + "}" for key, child in value.items()) + "})"
    raise CatalogError(f"cannot serialize value of type {type(value).__name__}")


def _cpp_optional_string(value: Any) -> str:
    return f"std::string({_cpp_string(value)})"


def _texture_format(value: Any, context: str = "texture.format") -> str:
    if not isinstance(value, str):
        raise CatalogError(f"{context} must be a string when present")
    return value


def _blend(value: Any, context: str = "pass.blend") -> str:
    if isinstance(value, bool):
        return f"BlendDefinition{{BlendKind::boolean, {'true' if value else 'false'}, {{}}}}"
    if isinstance(value, list) and len(value) == 2 and all(isinstance(factor, str) for factor in value):
        return (
            "BlendDefinition{BlendKind::factors, false, "
            f"{{{_cpp_string(value[0])}, {_cpp_string(value[1])}}}}}"
        )
    raise CatalogError(f"{context} must be a boolean or an ordered two-string factor array")


def _dimension(value: Any) -> str:
    raw = cpp_value(value)
    if isinstance(value, str):
        if value == "input":
            kind = "DimensionKind::input"
        elif value == "screen":
            kind = "DimensionKind::screen"
        elif value == "resolution":
            kind = "DimensionKind::resolution"
        elif value.endswith("%"):
            kind = "DimensionKind::screen_division"
        else:
            kind = "DimensionKind::unknown"
        return f"DimensionExpression{{{kind}, {_cpp_string(value)}, std::string(), 0.0, 0.0, 1, {raw}}}"
    if isinstance(value, (int, float)):
        return f"DimensionExpression{{DimensionKind::literal, std::string(), std::string(), {_number_text(float(value))}, 0.0, 1, {raw}}}"
    if isinstance(value, dict):
        if "param" in value and "power" in value:
            kind = "DimensionKind::power"
            power = int(value["power"])
        elif "param" in value and "paramDefault" in value:
            kind = "DimensionKind::parameter_default"
            power = 1
        elif "param" in value:
            kind = "DimensionKind::parameter"
            power = 1
        elif "screenDivide" in value:
            kind = "DimensionKind::screen_division"
            power = 1
        else:
            kind = "DimensionKind::unknown"
            power = 1
        parameter = value.get("param", value.get("screenDivide", ""))
        default = value.get("default", value.get("paramDefault", 0.0))
        override = value.get("inputOverride", "")
        return f"DimensionExpression{{{kind}, {_cpp_string(str(parameter))}, {_cpp_string(str(override))}, 0.0, {_number_text(float(default))}, {power}, {raw}}}"
    return f"DimensionExpression{{DimensionKind::unknown, std::string(), std::string(), 0.0, 0.0, 1, {raw}}}"


def _raw_pairs(value: dict[str, Any], skip: set[str] | None = None) -> str:
    skip = skip or set()
    pairs = ["{" + _cpp_string(key) + ", " + cpp_value(child) + "}" for key, child in value.items() if key not in skip]
    return "{" + ", ".join(pairs) + "}"


def _authority_pass_cpp(authority_pass: dict[str, Any]) -> list[str]:
    lines = [f"      p.authority_pass.name = {_cpp_string(str(authority_pass.get('name', '')))};"]
    for key, value in (authority_pass.get("inputs") or {}).items():
        lines.append(f"      p.authority_pass.inputs.emplace_back({_cpp_string(str(key))}, {_cpp_string(str(value))});")
    for key, value in (authority_pass.get("outputs") or {}).items():
        lines.append(f"      p.authority_pass.outputs.emplace_back({_cpp_string(str(key))}, {_cpp_string(str(value))});")
    for key, value in (authority_pass.get("uniforms") or {}).items():
        lines.append(f"      p.authority_pass.uniforms.emplace_back({_cpp_string(str(key))}, {cpp_value(value)});")
    lines.extend([f"      p.authority_pass.blend = {cpp_value(authority_pass.get('blend', False))};",
                  f"      p.authority_pass.repeat = {cpp_value(authority_pass.get('repeat'))};"])
    return lines


def _emit_effect(index: int, effect: dict[str, Any]) -> list[str]:
    lines = [f"static EffectDefinition make_effect_{index}() {{", "  EffectDefinition e;"]
    assignments = {
        "id": effect.get("id", ""), "directory_name": effect.get("directoryName", ""),
        "name": effect.get("name", ""), "name_space": effect.get("namespace", ""),
        "function": effect.get("func", ""), "kind": effect.get("kind", ""),
        "domain": effect.get("domain", ""), "description": effect.get("description", ""),
    }
    for field, value in assignments.items():
        lines.append(f"  e.{field} = {_cpp_string(str(value))};")
    lines.append("  e.tags = {" + ", ".join(_cpp_string(str(x)) for x in effect.get("tags", [])) + "};")
    lines.append("  e.parameter_aliases = {" + ", ".join("{" + _cpp_string(k) + ", " + _cpp_string(v) + "}" for k, v in (effect.get("paramAliases") or {}).items()) + "};")
    for name, parameter in (effect.get("params") or {}).items():
        lines += ["  {", "    ParameterDefinition p;", f"    p.name = {_cpp_string(name)};", f"    p.type = {_cpp_string(str(parameter.get('type', '')))};"]
        if "default" in parameter: lines.append(f"    p.default_value = {cpp_value(parameter['default'])};")
        for key, field in (("define", "define"), ("uniform", "uniform"), ("texture", "texture"), ("colorModeUniform", "color_mode_uniform")):
            if key in parameter: lines.append(f"    p.{field} = {_cpp_optional_string(parameter[key])};")
        if "zero" in parameter: lines.append(f"    p.zero = {cpp_value(parameter['zero'])};")
        for key, field in (("enum", "enum_values"), ("choices", "choices")):
            if key in parameter:
                if key == "enum" and isinstance(parameter[key], str):
                    lines.append(f"    p.enum_name = {_cpp_optional_string(parameter[key])};")
                else:
                    lines.append(f"    p.{field} = {_raw_pairs(parameter[key])};")
        for key in ("min", "max"):
            if key in parameter: lines.append(f"    p.{key} = {cpp_value(parameter[key])};")
        if parameter.get("cpuOnly") is not None: lines.append(f"    p.cpu_only = {'true' if parameter['cpuOnly'] else 'false'};")
        lines.append(f"    p.raw = {_raw_pairs(parameter)};")
        lines += ["    e.parameters.push_back(std::move(p));", "  }"]
    for name, texture in (effect.get("textures") or {}).items():
        lines += ["  {", "    TextureDefinition t;", f"    t.name = {_cpp_string(name)};", f"    t.width = {_dimension(texture.get('width'))};", f"    t.height = {_dimension(texture.get('height'))};"]
        if "format" in texture:
            format_value = _texture_format(texture["format"], f"{effect.get('id', '<effect>')}.{name}.format")
            lines.append(f"    t.format = {_cpp_optional_string(format_value)};")
        lines.append(f"    t.raw = {_raw_pairs(texture)};")
        lines += ["    e.textures.push_back(std::move(t));", "  }"]
    for current_pass in effect.get("passes", []):
        lines += ["  {", "    PassDefinition p;", f"    p.name = {_cpp_string(str(current_pass.get('name', '')))};", f"    p.program = {_cpp_string(str(current_pass.get('program', '')))};"]
        for key, field in (("inputs", "inputs"), ("outputs", "outputs")):
            pairs = "{" + ", ".join("{" + _cpp_string(k) + ", " + _cpp_string(str(v)) + "}" for k, v in (current_pass.get(key) or {}).items()) + "}"
            lines.append(f"    p.{field} = {pairs};")
        if "uniforms" in current_pass: lines.append(f"    p.uniforms = {_raw_pairs(current_pass['uniforms'])};")
        for key in ("count", "repeat", "conditions", "viewport", "drawBuffers"):
            if key in current_pass: lines.append(f"    p.{ {'drawBuffers':'draw_buffers'}.get(key,key) } = {cpp_value(current_pass[key])};")
        if "blend" in current_pass:
            blend_context = f"{effect.get('id', '<effect>')}.{current_pass.get('name', '<pass>')}.blend"
            lines.append(f"    p.blend = {_blend(current_pass['blend'], blend_context)};")
        if "drawMode" in current_pass: lines.append(f"    p.draw_mode = {_cpp_optional_string(current_pass['drawMode'])};")
        lines.append(f"    p.raw = {_raw_pairs(current_pass)};")
        lines += ["    e.passes.push_back(std::move(p));", "  }"]
    for key, field in (("externalTexture", "external_texture"), ("outputTex3d", "output_tex3d"), ("outputGeo", "output_geo"), ("outputXyz", "output_xyz"), ("outputVel", "output_velocity"), ("outputRgba", "output_rgba"), ("loopRole", "loop_role")):
        if key in effect and effect[key] is not None: lines.append(f"  e.{field} = {_cpp_optional_string(effect[key])};")
    if "iterated" in effect: lines.append(f"  e.iterated = {'true' if effect['iterated'] else 'false'};")
    lines.append(f"  e.raw = {_raw_pairs(effect)};")
    lines += ["  return e;", "}"]
    return lines


def _emit_cpp(records: list[dict[str, Any]], compatibility: dict[str, Any], authority: dict[str, Any], normalized_hash: str, payload_hash: str) -> bytes:
    lines = ["// Generated by tools/dsl/generate_effect_catalog.py; do not edit.", '#include "noisemaker/effects/catalog.hpp"', "#include <cmath>", "#include <limits>", "#include <utility>", "", "namespace noisemaker::effects {", ""]
    for index, effect in enumerate(records): lines.extend(_emit_effect(index, effect)); lines.append("")
    lines += ["const EffectDefinition* EffectCatalog::find(const std::string& id) const {", "  const auto found = index.find(id);", "  if (found != index.end()) return &definitions[found->second];", "  for (std::size_t i = 0; i < definitions.size(); ++i) {", "    if (definitions[i].id == id) { index.emplace(id, i); return &definitions[i]; }", "  }", "  return nullptr;", "}", "", "const EffectCatalog& effect_catalog() {", "  static const EffectCatalog catalog = [] {", "    EffectCatalog c;"]
    lines += [f"    c.provenance.schema = {_cpp_string(GENERATOR_SCHEMA)};", f"    c.provenance.backend_schema = {_cpp_string(BACKEND_SCHEMA)};", f"    c.provenance.corpus_revision = {_cpp_string(CORPUS_REVISION)};", f"    c.provenance.cpu_behavioral_lock = {_cpp_string(authority['cpu_behavioral_lock'])};", f"    c.provenance.cpu_behavioral_file_count = {authority['cpu_behavioral_file_count']};", f"    c.provenance.cpu_revision = {_cpp_string(authority['cpu_revision'])};", f"    c.provenance.source_lock_sha256 = {_cpp_string(authority['source_lock_sha256'])};", f"    c.provenance.cpu_package_sha256 = {_cpp_string(authority['cpu_package_sha256'])};", f"    c.provenance.cpu_package_lock_sha256 = {_cpp_string(authority['cpu_package_lock_sha256'])};", f"    c.provenance.cpu_source_lock_sha256 = {_cpp_string(authority['cpu_source_lock_sha256'])};", f"    c.provenance.upstream_revision = {_cpp_string(authority['upstream_revision'])};", f"    c.provenance.upstream_tree = {_cpp_string(authority.get('upstream_tree', ''))};", f"    c.provenance.upstream_package_sha256 = {_cpp_string(authority['upstream_package_sha256'])};", f"    c.provenance.upstream_package_lock_sha256 = {_cpp_string(authority['upstream_package_lock_sha256'])};", f"    c.provenance.generated_payload_sha256 = {_cpp_string(payload_hash)};", f"    c.provenance.normalized_record_stream_sha256 = {_cpp_string(normalized_hash)};", f"    c.provenance.compatibility_sha256 = {_cpp_string(COMPATIBILITY_SHA256)};", f"    c.provenance.first_effect_id = {_cpp_string(records[0]['id'])};", f"    c.provenance.last_effect_id = {_cpp_string(records[-1]['id'])};"]
    counts = compatibility["_derived_counts"]
    for field, key in (("definitions", "definitions"), ("passes", "passes"), ("reference_program_keys", "reference_program_keys"), ("backend_programs", "backend_programs"), ("compatible_programs", "compatible_programs"), ("incompatible_programs", "incompatible_programs"), ("missing_passes", "missing_passes"), ("scatter_passes", "scatter_passes"), ("executable_definitions", "executable_definitions"), ("incomplete_definitions", "incomplete_definitions")):
        lines.append(f"    c.provenance.counts.{field} = {counts[key]};")
    backend_counts = compatibility["counts"]
    for field, key in (("backend_fragment_rows", "fragment_rows"), ("backend_unique_fragment_keys", "unique_fragment_keys"), ("backend_raw_exact", "raw_exact"), ("backend_semantic_exact", "semantic_exact")):
        lines.append(f"    c.provenance.{field} = {backend_counts[key]};")
    for index in range(len(records)): lines.append(f"    c.definitions.push_back(make_effect_{index}());")
    for row in compatibility["canonical_programs"]:
        lines += ["    {", "      ProgramCompatibility p;", f"      p.effect_id = {_cpp_string(row['effect_id'])};", f"      p.program = {_cpp_string(row['program'])};", f"      p.program_key = {_cpp_string(row['program_key'])};", f"      p.status = {_cpp_string(str(row.get('status', 'incompatible')))};", "      p.reasons = {" + ", ".join("{" + _cpp_string(str(r.get('code',''))) + ", " + _cpp_string(str(r.get('detail',''))) + "}" for r in row.get('reasons', [])) + "};"]
        if row.get("factory", {}).get("canonical"): lines.append(f"      p.canonical_factory = {_cpp_optional_string(row['factory']['canonical'])};")
        if row.get("new_raw_sha256"): lines.append(f"      p.source_sha256 = {_cpp_optional_string(row['new_raw_sha256'])};")
        if row.get("semantic", {}).get("old_typed_ir_sha256"): lines.append(f"      p.semantic_sha256 = {_cpp_optional_string(row['semantic']['old_typed_ir_sha256'])};")
        lines.append(f"      p.raw = {_raw_pairs(row)};")
        lines += ["      c.canonical_programs.push_back(std::move(p));", "    }"]
    record_by_id = {record["id"]: record for record in records}
    for reference in compatibility["reference_passes"]:
        effect = record_by_id[reference["effect_id"]]
        authority_pass = reference["authority_pass"]
        lines += ["    {", "      ReferencePassCompatibility p;", f"      p.effect_id = {_cpp_string(reference['effect_id'])};", f"      p.pass_index = {reference['pass_index']};", f"      p.pass_name = {_cpp_string(reference['pass_name'])};", f"      p.program_key = {_cpp_string(reference['program_key'])};", f"      p.status = {_cpp_string(reference['status'])};", "      p.reasons = {" + ", ".join("{" + _cpp_string(str(r.get('code',''))) + ", " + _cpp_string(str(r.get('detail',''))) + "}" for r in reference.get('reasons', [])) + "};"]
        lines += _authority_pass_cpp(authority_pass)
        lines += ["      c.reference_passes.push_back(std::move(p));", "    }"]
    scatter = compatibility["scatter"]
    lines += ["    {", "      ScatterCompatibility s;", f"      s.program_key = {_cpp_string(scatter['program_key'])};", f"      s.adapter = {_cpp_string(scatter['adapter'])};", f"      s.registry = {_cpp_string(scatter['registry'])};", f"      s.draw_mode = {_cpp_string(scatter['draw_mode'])};", f"      s.dimensionality = {_cpp_string(scatter['dimensionality'])};", f"      s.count = {_cpp_string(scatter['count'])};", f"      s.input_texture = {_cpp_string(scatter['input_texture'])};", f"      s.destination_mutation = {_cpp_string(scatter['destination_mutation'])};", f"      s.blend = {'true' if scatter['blend'] else 'false'};"]
    for uniform in scatter["uniforms"]:
        lines.append("      s.uniforms.push_back({" + ", ".join(_cpp_string(str(uniform.get(k, ''))) for k in ("name", "type", "cpp_type", "source", "source_name", "resource")) + "});")
    for output in scatter.get("outputs", [{"slot": 0, "physical_name": "fragColor", "logical_route": scatter.get("output_route", ""), "cpp_type": "glsl::Vec4"}]):
        lines.append("      s.outputs.push_back({" + str(output.get("slot", 0)) + ", " + ", ".join(_cpp_string(str(output.get(k, ''))) for k in ("physical_name", "logical_route", "cpp_type")) + "});")
    lines += ["      s.reasons = {{\"explicit_scatter_adapter\", \"filter/wormhole:deposit\"}};", "      c.scatter = std::move(s);", "    }"]
    lines += ["    return c;", "  }();", "  return catalog;", "}", "", "}  // namespace noisemaker::effects", ""]
    return "\n".join(lines).encode("utf-8")


def generate(*, cpu_root: pathlib.Path, shader_git: pathlib.Path, compatibility_path: pathlib.Path = DEFAULT_COMPATIBILITY) -> tuple[bytes, bytes]:
    if cpu_root.is_symlink() or not cpu_root.is_dir(): raise CatalogError("--cpu-root must name a real directory")
    if shader_git.is_symlink() or not shader_git.is_dir(): raise CatalogError("--shader-git must name a real directory")
    try: compatibility = json.loads(compatibility_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise CatalogError(f"unable to read compatibility manifest: {error}") from error
    if compatibility.get("schema") != "noisemaker-cpp.backend-compatibility.v1": raise CatalogError("compatibility schema mismatch")
    records = export_records(cpu_root)
    authority = _authority(cpu_root, shader_git, compatibility)
    compatibility, derived = _validate_compatibility(compatibility, records, compatibility_path)
    compatibility = dict(compatibility); compatibility["_derived_counts"] = derived
    normalized = b"\n".join(json.dumps(_canonical_record(record), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() for record in records) + b"\n"
    normalized_hash = hashlib.sha256(normalized).hexdigest()
    placeholder_cpp = _emit_cpp(records, compatibility, authority, normalized_hash, "")
    payload_hash = hashlib.sha256(placeholder_cpp).hexdigest()
    cpp = _emit_cpp(records, compatibility, authority, normalized_hash, payload_hash)
    provenance = {"schema": GENERATOR_SCHEMA, "backend_schema": BACKEND_SCHEMA, "corpus_revision": CORPUS_REVISION, "compatibility_sha256": COMPATIBILITY_SHA256,
                  "authority": {key: authority[key] for key in ("cpu_behavioral_file_count", "cpu_behavioral_lock", "cpu_package_lock_sha256", "cpu_package_sha256", "cpu_source_lock_sha256", "source_lock_sha256", "upstream_package_lock_sha256", "upstream_package_sha256", "upstream_revision", "upstream_tree")},
                  "counts": derived, "backend_counts": compatibility["counts"], "first_effect_id": records[0]["id"], "last_effect_id": records[-1]["id"],
                  "normalized_record_stream_sha256": normalized_hash, "generated_payload_sha256": payload_hash}
    return cpp, (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-root", type=pathlib.Path, required=True)
    parser.add_argument("--shader-git", type=pathlib.Path, required=True)
    parser.add_argument("--compatibility", type=pathlib.Path, default=DEFAULT_COMPATIBILITY)
    parser.add_argument("--output-dir", type=pathlib.Path, default=ROOT / "src/effects/generated")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        cpp, provenance = generate(cpu_root=args.cpu_root, shader_git=args.shader_git,
                                   compatibility_path=args.compatibility)
        targets = [args.output_dir / "effect_catalog.cpp", args.output_dir / "effect_catalog.provenance.json"]
        if args.check:
            if not targets[0].is_file() or targets[0].read_bytes() != cpp: raise CatalogError(f"generated catalog drift: {targets[0]}")
            if not targets[1].is_file() or targets[1].read_bytes() != provenance: raise CatalogError(f"catalog provenance drift: {targets[1]}")
        else:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            targets[0].write_bytes(cpp); targets[1].write_bytes(provenance)
    except CatalogError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
