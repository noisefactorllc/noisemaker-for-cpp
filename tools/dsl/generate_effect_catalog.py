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
EFFECT_KEYS = frozenset({
    "id", "directoryName", "name", "namespace", "func", "kind", "domain", "tags",
    "description", "paramAliases", "params", "passes", "textures", "externalTexture",
    "outputTex3d", "outputGeo", "outputXyz", "outputVel", "outputRgba", "iterated", "loopRole",
})
PARAM_KEYS = frozenset({"type", "default", "define", "uniform", "zero", "enum", "choices", "min", "max", "texture", "colorModeUniform", "cpuOnly"})
PASS_KEYS = frozenset({"name", "program", "inputs", "outputs", "uniforms", "count", "repeat", "conditions", "viewport", "blend", "drawMode", "drawBuffers"})
TEXTURE_KEYS = frozenset({"width", "height", "format"})


class CatalogError(ValueError):
    pass


def _decode(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode(item) for item in value]
    if isinstance(value, dict):
        return {key: _decode(item) for key, item in value.items()}
    if value == "number:NaN":
        return math.nan
    if value == "number:+Infinity":
        return math.inf
    if value == "number:-Infinity":
        return -math.inf
    if value == "number:-0":
        return -0.0
    return value


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
    records = [_decode(record) for record in document["records"]]
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
    for key in ("cpu_behavioral_lock", "source_lock_sha256", "upstream_revision", "upstream_tree"):
        if authority.get(key) != persisted.get(key):
            raise CatalogError(f"compatibility authority mismatch: {key}")
    try:
        revision = subprocess.run(["git", "-C", str(cpu_root), "rev-parse", "HEAD"], check=True,
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        revision = authority["cpu_behavioral_lock"]
    authority["cpu_revision"] = revision
    return authority


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
    """Encode doubles with the same tags as the Node exporter."""
    if isinstance(value, float):
        if math.isnan(value): return "number:NaN"
        if math.isinf(value): return "number:-Infinity" if value < 0 else "number:+Infinity"
        if value == 0.0 and math.copysign(1.0, value) < 0: return "number:-0"
        return value
    if isinstance(value, list): return [_canonical_json_value(item) for item in value]
    if isinstance(value, dict): return {key: _canonical_json_value(item) for key, item in value.items()}
    return value


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


def _dimension(value: Any) -> str:
    raw = cpp_value(value)
    if isinstance(value, str):
        if value == "input":
            kind = "DimensionKind::input"
        elif value == "screen":
            kind = "DimensionKind::screen"
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
        lines += ["    e.parameters.push_back(std::move(p));", "  }"]
    for name, texture in (effect.get("textures") or {}).items():
        lines += ["  {", "    TextureDefinition t;", f"    t.name = {_cpp_string(name)};", f"    t.width = {_dimension(texture.get('width'))};", f"    t.height = {_dimension(texture.get('height'))};", f"    t.format = {_cpp_string(str(texture.get('format', ''))) };"]
        lines += ["    e.textures.push_back(std::move(t));", "  }"]
    for current_pass in effect.get("passes", []):
        lines += ["  {", "    PassDefinition p;", f"    p.name = {_cpp_string(str(current_pass.get('name', '')))};", f"    p.program = {_cpp_string(str(current_pass.get('program', '')))};"]
        for key, field in (("inputs", "inputs"), ("outputs", "outputs")):
            pairs = "{" + ", ".join("{" + _cpp_string(k) + ", " + _cpp_string(str(v)) + "}" for k, v in (current_pass.get(key) or {}).items()) + "}"
            lines.append(f"    p.{field} = {pairs};")
        if "uniforms" in current_pass: lines.append(f"    p.uniforms = {_raw_pairs(current_pass['uniforms'])};")
        for key in ("count", "repeat", "conditions", "viewport", "drawBuffers"):
            if key in current_pass: lines.append(f"    p.{ {'drawBuffers':'draw_buffers'}.get(key,key) } = {cpp_value(current_pass[key])};")
        if "blend" in current_pass: lines.append(f"    p.blend = {'true' if current_pass['blend'] else 'false'};")
        if "drawMode" in current_pass: lines.append(f"    p.draw_mode = {_cpp_optional_string(current_pass['drawMode'])};")
        lines += ["    e.passes.push_back(std::move(p));", "  }"]
    for key, field in (("externalTexture", "external_texture"), ("outputTex3d", "output_tex3d"), ("outputGeo", "output_geo"), ("outputXyz", "output_xyz"), ("outputVel", "output_velocity"), ("outputRgba", "output_rgba"), ("loopRole", "loop_role")):
        if key in effect and effect[key] is not None: lines.append(f"  e.{field} = {_cpp_optional_string(effect[key])};")
    if "iterated" in effect: lines.append(f"  e.iterated = {'true' if effect['iterated'] else 'false'};")
    lines += ["  return e;", "}"]
    return lines


def _emit_cpp(records: list[dict[str, Any]], compatibility: dict[str, Any], authority: dict[str, Any], normalized_hash: str) -> bytes:
    lines = ["// Generated by tools/dsl/generate_effect_catalog.py; do not edit.", '#include "noisemaker/effects/catalog.hpp"', "#include <cmath>", "#include <limits>", "#include <utility>", "", "namespace noisemaker::effects {", ""]
    for index, effect in enumerate(records): lines.extend(_emit_effect(index, effect)); lines.append("")
    lines += ["const EffectDefinition* EffectCatalog::find(const std::string& id) const {", "  const auto found = index.find(id);", "  if (found != index.end()) return &definitions[found->second];", "  for (std::size_t i = 0; i < definitions.size(); ++i) {", "    if (definitions[i].id == id) { index.emplace(id, i); return &definitions[i]; }", "  }", "  return nullptr;", "}", "", "const EffectCatalog& effect_catalog() {", "  static const EffectCatalog catalog = [] {", "    EffectCatalog c;"]
    lines += [f"    c.provenance.schema = {_cpp_string(GENERATOR_SCHEMA)};", f"    c.provenance.cpu_behavioral_lock = {_cpp_string(authority['cpu_behavioral_lock'])};", f"    c.provenance.cpu_revision = {_cpp_string(authority['cpu_revision'])};", f"    c.provenance.source_lock_sha256 = {_cpp_string(authority['source_lock_sha256'])};", f"    c.provenance.upstream_revision = {_cpp_string(authority['upstream_revision'])};", f"    c.provenance.normalized_record_stream_sha256 = {_cpp_string(normalized_hash)};", f"    c.provenance.first_effect_id = {_cpp_string(records[0]['id'])};", f"    c.provenance.last_effect_id = {_cpp_string(records[-1]['id'])};"]
    counts = compatibility["_derived_counts"]
    for field, key in (("definitions", "definitions"), ("passes", "passes"), ("reference_program_keys", "reference_program_keys"), ("backend_programs", "backend_programs"), ("compatible_programs", "compatible_programs"), ("incompatible_programs", "incompatible_programs"), ("missing_passes", "missing_passes"), ("scatter_passes", "scatter_passes"), ("executable_definitions", "executable_definitions"), ("incomplete_definitions", "incomplete_definitions")):
        lines.append(f"    c.provenance.counts.{field} = {counts[key]};")
    for index in range(len(records)): lines.append(f"    c.definitions.push_back(make_effect_{index}());")
    all_rows = {row["program_key"]: row for row in compatibility["canonical_programs"]}
    all_rows[compatibility["scatter"]["program_key"]] = compatibility["scatter"]
    for key in compatibility["reference_key_closure"]:
        row = all_rows.get(key)
        if row is None: row = {"program_key": key, "status": "missing", "reasons": [{"code": "missing_backend_program", "detail": key}]}
        reasons = row.get("reasons", [])
        lines += ["    {", "      ProgramCompatibility p;", f"      p.program_key = {_cpp_string(key)};", f"      p.status = {_cpp_string(str(row.get('status', 'missing')))};", "      p.reasons = {" + ", ".join("{" + _cpp_string(str(r.get('code',''))) + ", " + _cpp_string(str(r.get('detail',''))) + "}" for r in reasons) + "};"]
        if row.get("factory", {}).get("canonical"): lines.append(f"      p.canonical_factory = {_cpp_optional_string(row['factory']['canonical'])};")
        if row.get("new_raw_sha256"): lines.append(f"      p.source_sha256 = {_cpp_optional_string(row['new_raw_sha256'])};")
        if row.get("semantic", {}).get("old_typed_ir_sha256"): lines.append(f"      p.semantic_sha256 = {_cpp_optional_string(row['semantic']['old_typed_ir_sha256'])};")
        lines += ["      c.compatibility.push_back(std::move(p));", "    }"]
    lines += ["    return c;", "  }();", "  return catalog;", "}", "", "}  // namespace noisemaker::effects", ""]
    return "\n".join(lines).encode("utf-8")


def generate(*, cpu_root: pathlib.Path, shader_git: pathlib.Path, compatibility_path: pathlib.Path = DEFAULT_COMPATIBILITY,
             input_path: pathlib.Path | None = None) -> tuple[bytes, bytes]:
    if cpu_root.is_symlink() or not cpu_root.is_dir(): raise CatalogError("--cpu-root must name a real directory")
    if shader_git.is_symlink() or not shader_git.is_dir(): raise CatalogError("--shader-git must name a real directory")
    try: compatibility = json.loads(compatibility_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise CatalogError(f"unable to read compatibility manifest: {error}") from error
    if compatibility.get("schema") != "noisemaker-cpp.backend-compatibility.v1": raise CatalogError("compatibility schema mismatch")
    records = load_export(input_path) if input_path is not None else export_records(cpu_root)
    authority = _authority(cpu_root, shader_git, compatibility)
    passes = compatibility.get("reference_passes", [])
    canonical = compatibility.get("canonical_programs", [])
    closure = compatibility.get("reference_key_closure", [])
    canonical_by_key = {row["program_key"]: row for row in canonical}
    canonical_by_key[compatibility["scatter"]["program_key"]] = compatibility["scatter"]
    statuses = {key: canonical_by_key.get(key, {"status": "missing"})["status"] for key in closure}
    if set(statuses) != set(closure): raise CatalogError("reference key compatibility closure mismatch")
    if len(passes) != 305 or len(closure) != 295: raise CatalogError("ordered compatibility counts drift")
    effect_status: dict[str, list[str]] = defaultdict(list)
    for current_pass in passes: effect_status[current_pass["effect_id"]].append(current_pass["status"])
    executable = sum(all(status in {"compatible", "scatter"} for status in values) for values in effect_status.values())
    derived = {"definitions": len(records), "passes": len(passes), "reference_program_keys": len(closure), "backend_programs": len(canonical) + 1,
               "compatible_programs": sum(status == "compatible" for status in statuses.values()), "incompatible_programs": sum(status == "incompatible" for status in statuses.values()),
               "missing_passes": sum(row["status"] == "missing" for row in passes), "scatter_passes": sum(row["status"] == "scatter" for row in passes),
               "executable_definitions": executable, "incomplete_definitions": len(records) - executable}
    compatibility = dict(compatibility); compatibility["_derived_counts"] = derived
    normalized = b"\n".join(json.dumps(_canonical_json_value(record), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() for record in records) + b"\n"
    normalized_hash = hashlib.sha256(normalized).hexdigest()
    cpp = _emit_cpp(records, compatibility, authority, normalized_hash)
    provenance = {"schema": GENERATOR_SCHEMA, "authority": {key: authority[key] for key in ("cpu_behavioral_lock", "cpu_revision", "source_lock_sha256", "upstream_revision", "upstream_tree")},
                  "counts": derived, "first_effect_id": records[0]["id"], "last_effect_id": records[-1]["id"],
                  "normalized_record_stream_sha256": normalized_hash, "generated_sha256": hashlib.sha256(cpp).hexdigest()}
    return cpp, (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-root", type=pathlib.Path, required=True)
    parser.add_argument("--shader-git", type=pathlib.Path, required=True)
    parser.add_argument("--compatibility", type=pathlib.Path, default=DEFAULT_COMPATIBILITY)
    parser.add_argument("--input", type=pathlib.Path)
    parser.add_argument("--output-dir", type=pathlib.Path, default=ROOT / "src/effects/generated")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        cpp, provenance = generate(cpu_root=args.cpu_root, shader_git=args.shader_git,
                                   compatibility_path=args.compatibility, input_path=args.input)
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
