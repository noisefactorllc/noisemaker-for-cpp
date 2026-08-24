#!/usr/bin/env python3
"""Fail-closed materializer for the Classic Noise canonical CPU oracle."""
from __future__ import annotations
import argparse, copy, hashlib, json, math, pathlib, re, struct

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/classic-noise-parity"
ORACLE = PACKAGE / "classic-noise-oracles.json"
GENERATOR = PACKAGE / "classic_noise_oracle_generator.mjs"
REPORT = PACKAGE / "classic-noise-oracle-report.md"
TARGET = ROOT / "tests/oracles/classic_noise_expected.inc"
SOURCE = "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/noise/noise.glsl"
SCHEMA = "noisemaker-for-cpp.classic-noise.pixel-parity.v1"
KEY = "classicNoisedeck/noise:noise"
FACTORY_SHA256 = "b5b2743ef755306503df6ab2ab5dd81ab944a121e0fd383ef8d641db4d247424"
WORD = re.compile(r"^0x[0-9a-f]{8}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
DEFINES = {"NOISE_TYPE": 10, "REFRACT_MODE": 2, "LOOP_OFFSET": 300, "METRIC": 0, "COLOR_MODE": 6}
NAMES = ["NOISE_TYPE", "REFRACT_MODE", "LOOP_OFFSET", "METRIC", "COLOR_MODE", "time", "seed", "resolution", "tileOffset", "fullResolution", "xScale", "yScale", "octaves", "ridges", "refractAmt", "kaleido", "loopScale", "speed", "paletteMode", "paletteOffset", "paletteAmp", "paletteFreq", "palettePhase", "cyclePalette", "rotatePalette", "repeatPalette", "hueRange", "hueRotation", "wrap"]
COMPARER_TESTS = {"good", "dimensions_before_access", "f32_short_count", "f32_long_count", "rgba8_mismatch", "signed_zero", "nan_payload", "control_mutation_rejected"}
MUTATION_NAMES = {"mutable-global-frame", "runtime-loop-bound", "owner-speed-control", "hue-range-factor", "refract-amount"}
RUNTIME_ABI = {"NOISE_TYPE":"int32", "REFRACT_MODE":"int32", "LOOP_OFFSET":"int32", "METRIC":"int32", "COLOR_MODE":"int32", "time":"float", "seed":"int32", "resolution":"Vec2", "tileOffset":"Vec2", "fullResolution":"Vec2", "xScale":"float", "yScale":"float", "octaves":"int32", "ridges":"bool", "refractAmt":"float", "kaleido":"float", "loopScale":"float", "speed":"float", "paletteMode":"int32", "paletteOffset":"Vec3", "paletteAmp":"Vec3", "paletteFreq":"Vec3", "palettePhase":"Vec3", "cyclePalette":"int32", "rotatePalette":"float", "repeatPalette":"float", "hueRange":"float", "hueRotation":"float", "wrap":"bool"}
SOURCE_ABI = {"time":"float", "seed":"int", "resolution":"vec2", "tileOffset":"vec2", "fullResolution":"vec2", "xScale":"float", "yScale":"float", "octaves":"int", "ridges":"bool", "refractAmt":"float", "kaleido":"float", "loopScale":"float", "speed":"float", "paletteMode":"int", "paletteOffset":"vec3", "paletteAmp":"vec3", "paletteFreq":"vec3", "palettePhase":"vec3", "cyclePalette":"int", "rotatePalette":"float", "repeatPalette":"float", "hueRange":"float", "hueRotation":"float", "wrap":"bool"}

class OracleError(RuntimeError):
    pass

def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def sidecar(path: pathlib.Path) -> bytes:
    companion = pathlib.Path(f"{path}.sha256")
    if not path.is_file() or not companion.is_file():
        raise OracleError(f"missing checked asset: {path}")
    payload = path.read_bytes()
    if companion.read_text() != f"{digest(payload)}  {path.name}\n":
        raise OracleError(f"stale sidecar: {path}")
    return payload

def strict_json(payload: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise OracleError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    def parse_constant(value):
        raise OracleError(f"non-finite JSON constant: {value}")
    try:
        return json.loads(payload, object_pairs_hook=pairs, parse_constant=parse_constant)
    except OracleError:
        raise
    except (ValueError, TypeError) as error:
        raise OracleError(f"invalid JSON: {error}") from error

def exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise OracleError(f"{label}: field set drift")
    return value

def check_hash(value, label):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise OracleError(f"{label}: malformed SHA-256")

def check_words(value, count, label):
    if not isinstance(value, list) or len(value) != count or any(not isinstance(x, str) or not WORD.fullmatch(x) for x in value):
        raise OracleError(f"{label}: malformed word array")

def check_bytes(value, count, label):
    if not isinstance(value, list) or len(value) != count or any(type(x) is not int or not 0 <= x <= 255 for x in value):
        raise OracleError(f"{label}: malformed byte array")

def word_digest(words):
    return digest(b"".join(struct.pack("<I", int(word, 16)) for word in words))

def validate(document):
    top = {"schema","schema_version","program_key","effect_key","runtime_key","corpus_revision","upstream_revision","defines","exactness_contract","comparer_self_tests","authority","factory","provenance","runtime_binding_names","runtime_binding_abi","source_uniform_abi","output_abi","render_cases","mutation_anchor_cardinality","mutation_ledger","prepared_mechanisms","claim_boundaries"}
    if not isinstance(document, dict) or set(document) != top:
        raise OracleError("document fields mismatch")
    if (document["schema"], document["schema_version"], document["program_key"], document["effect_key"], document["runtime_key"]) != (SCHEMA, 1, KEY, "classicNoisedeck/noise", KEY):
        raise OracleError("identity drift")
    if document["defines"] != DEFINES or document["runtime_binding_names"] != NAMES or document["runtime_binding_abi"] != RUNTIME_ABI or document["source_uniform_abi"] != SOURCE_ABI:
        raise OracleError("define or ABI drift")
    exact(document["factory"], {"name","text_sha256","public_factory_is_canonical_identity","canonical_adapter_factories_own_key"}, "factory")
    check_hash(document["factory"]["text_sha256"], "factory hash")
    if document["factory"]["name"] != "canonicalFactory12" or document["factory"]["text_sha256"] != FACTORY_SHA256 or not document["factory"]["public_factory_is_canonical_identity"] or document["factory"]["canonical_adapter_factories_own_key"]:
        raise OracleError("factory identity drift")
    if document["output_abi"] != {"name":"fragColor","source_type":"vec4","runtime_type":"Vec4","role":"output"}:
        raise OracleError("output ABI drift")
    provenance = document["provenance"]
    exact(provenance, {"source","generator","materializer"}, "provenance")
    if provenance["source"] != {"relative_path":SOURCE,"bytes":31255,"sha256":"4cd68543729f94788ef6fa2a484dd47d76154814b027128bef5eb9c8d7461663"}:
        raise OracleError("source provenance drift")
    exact(document["authority"], {"node_version","oracle","cpu_root_argument","immutable_snapshot","realpath_containment_checked","live_checkout_rejected","closure_cardinality","import_closure"}, "authority")
    if document["authority"]["closure_cardinality"] != 22 or len(document["authority"]["import_closure"]) != 22:
        raise OracleError("closure cardinality drift")
    if not all(isinstance(x, dict) and set(x) == {"relative_path","sha256"} and isinstance(x["relative_path"], str) and SHA.fullmatch(x["sha256"]) for x in document["authority"]["import_closure"]):
        raise OracleError("closure entry drift")
    if set(document["comparer_self_tests"]) != COMPARER_TESTS or not all(document["comparer_self_tests"].values()):
        raise OracleError("comparer self-test failure")
    if len(document["render_cases"]) != 8:
        raise OracleError("case count drift")
    for case in document["render_cases"]:
        required = {"name","width","height","time","seed","resolution","tileOffset","fullResolution","xScale","yScale","octaves","ridges","refractAmt","kaleido","loopScale","speed","paletteMode","paletteOffset","paletteAmp","paletteFreq","palettePhase","cyclePalette","rotatePalette","repeatPalette","hueRange","hueRotation","wrap","expected","f32_byte_count","rgba8_byte_count","repeat","storage","controls_snapshot"}
        exact(case, required, f"case {case.get('name')}")
        count = case["width"] * case["height"] * 4
        output = exact(case["expected"], {"f32_words_le","f32_sha256","rgba8_bytes","rgba8_sha256"}, "expected")
        check_words(output["f32_words_le"], count, "output words"); check_bytes(output["rgba8_bytes"], count, "output bytes")
        if any(word != "0x3f800000" for word in output["f32_words_le"][3::4]) or any(byte != 255 for byte in output["rgba8_bytes"][3::4]):
            raise OracleError(f"alpha lane drift: {case['name']}")
        check_hash(output["f32_sha256"], "output f32 hash"); check_hash(output["rgba8_sha256"], "output rgba8 hash")
        if output["f32_sha256"] != word_digest(output["f32_words_le"]): raise OracleError(f"f32 digest drift: {case['name']}")
        if output["rgba8_sha256"] != digest(bytes(output["rgba8_bytes"])): raise OracleError(f"rgba8 digest drift: {case['name']}")
        if case["f32_byte_count"] != count * 4 or case["rgba8_byte_count"] != count: raise OracleError(f"count drift: {case['name']}")
        if case["repeat"] != {"exact":True,"dimensions":True,"f32_words":True,"rgba8_bytes":True} or case["storage"] != {"distinct_surface_objects":True,"distinct_f32_backing_stores":True} or case["controls_snapshot"] != {"unchanged":True,"typed_array_bits_unchanged":True}: raise OracleError(f"runtime control drift: {case['name']}")
    if len(document["mutation_ledger"]) != 5 or {item.get("name") for item in document["mutation_ledger"]} != MUTATION_NAMES or document["mutation_anchor_cardinality"] != {"total":5,"anchors":{item["name"]:1 for item in document["mutation_ledger"]}}:
        raise OracleError("mutation census drift")
    for mutation in document["mutation_ledger"]:
        exact(mutation, {"name","anchor","replacement","anchor_sha256","replacement_sha256","mutated_factory_sha256","independent","anchor_cardinality","witnesses","results"}, "mutation")
        if type(mutation["independent"]) is not bool or not mutation["independent"] or type(mutation["anchor_cardinality"]) is not int or mutation["anchor_cardinality"] != 1 or not isinstance(mutation["witnesses"], list) or not mutation["witnesses"] or len(mutation["witnesses"]) != len(set(mutation["witnesses"])): raise OracleError(f"mutation witness drift: {mutation['name']}")
        for key in ("anchor_sha256","replacement_sha256","mutated_factory_sha256"): check_hash(mutation[key], f"mutation {key}")
        rows = {row["case"]: row for row in mutation["results"]}
        if set(rows) != {case["name"] for case in document["render_cases"]}: raise OracleError(f"mutation rows drift: {mutation['name']}")
        if len(mutation["results"]) != len(document["render_cases"]): raise OracleError(f"mutation result count drift: {mutation['name']}")
        for row in mutation["results"]:
            exact(row, {"case", "exact", "changed_float32_lanes", "changed_rgba8_bytes"}, "mutation result")
            if type(row["exact"]) is not bool or type(row["changed_float32_lanes"]) is not int or type(row["changed_rgba8_bytes"]) is not int or row["changed_float32_lanes"] < 0 or row["changed_rgba8_bytes"] < 0:
                raise OracleError(f"mutation result drift: {mutation['name']}")
        for witness in mutation["witnesses"]:
            if witness not in rows: raise OracleError(f"mutation witness case drift: {mutation['name']}")
            if rows[witness]["changed_float32_lanes"] <= 0 or rows[witness]["changed_rgba8_bytes"] <= 0: raise OracleError(f"mutation witness has no positive evidence: {mutation['name']}")

def emit(document):
    q = lambda value: json.dumps(str(value))
    def cxx_words(values): return ", ".join(f"0x{int(v,16):08x}u" for v in values)
    def cxx_bytes(values): return ", ".join(str(int(v)) for v in values)
    lines = ["// Generated by generate_classic_noise_native_oracle_include.py; exact JSON authority.", "#pragma once", "#include <cstdint>", "#include <string>", "#include <vector>", "namespace noisemaker_classic_noise_oracle {", "struct Binding { const char* name; const char* runtime_abi; const char* source_abi; };", "struct Case { const char* name; std::uint32_t width, height; std::vector<std::uint32_t> f32; const char* f32_sha256; std::vector<std::uint8_t> rgba8; const char* rgba8_sha256; bool repeat_exact; bool distinct_storage; bool controls_unchanged; };", "struct MutationResult { const char* case_name; bool exact; std::uint32_t changed_float32_lanes; std::uint32_t changed_rgba8_bytes; };", "struct Mutation { const char* name; const char* anchor; const char* replacement; const char* anchor_sha256; const char* replacement_sha256; const char* mutated_factory_sha256; bool independent; std::uint32_t anchor_cardinality; std::vector<const char*> witnesses; std::vector<MutationResult> results; };", f"inline constexpr const char* kSchema = {q(document['schema'])};", f"inline constexpr const char* kProgramKey = {q(KEY)};", f"inline constexpr const char* kFactorySha256 = {q(document['factory']['text_sha256'])};", f"inline constexpr const char* kSourceSha256 = {q(document['provenance']['source']['sha256'])};", f"inline constexpr std::uint32_t kSourceBytes = {document['provenance']['source']['bytes']}U;", f"inline constexpr std::uint32_t kImportClosureCardinality = {document['authority']['closure_cardinality']}U;", f"inline constexpr std::uint32_t kRuntimeBindingCardinality = {len(NAMES)}U;", "inline const std::vector<Binding> kRuntimeBindings = {"]
    for name in NAMES: lines.append(f"  {{{q(name)}, {q(RUNTIME_ABI[name])}, {q('define' if name in DEFINES else SOURCE_ABI[name])}}},")
    lines += ["};", "inline const std::vector<Case> kCases = {"]
    for case in document["render_cases"]:
        output = case["expected"]
        lines.append(f"  {{{q(case['name'])}, {case['width']}U, {case['height']}U, {{{cxx_words(output['f32_words_le'])}}}, {q(output['f32_sha256'])}, {{{cxx_bytes(output['rgba8_bytes'])}}}, {q(output['rgba8_sha256'])}, true, true, true}},")
    lines += ["};", "inline const std::vector<Mutation> kMutations = {"]
    for mutation in document["mutation_ledger"]:
        witnesses = "{" + ", ".join(q(witness) for witness in mutation["witnesses"]) + "}"
        results = "{" + ", ".join("{" + ", ".join((q(row["case"]), str(row["exact"]).lower(), f"{row['changed_float32_lanes']}U", f"{row['changed_rgba8_bytes']}U")) + "}" for row in mutation["results"]) + "}"
        lines.append(f"  {{{q(mutation['name'])}, {q(mutation['anchor'])}, {q(mutation['replacement'])}, {q(mutation['anchor_sha256'])}, {q(mutation['replacement_sha256'])}, {q(mutation['mutated_factory_sha256'])}, {str(mutation['independent']).lower()}, {mutation['anchor_cardinality']}U, {witnesses}, {results}}},")
    lines += ["};", "} // namespace noisemaker_classic_noise_oracle", ""]
    return "\n".join(lines).encode()

def main():
    parser = argparse.ArgumentParser(); group = parser.add_mutually_exclusive_group(required=True); group.add_argument("--write", action="store_true"); group.add_argument("--check", action="store_true"); group.add_argument("--self-test", action="store_true"); args = parser.parse_args()
    document = strict_json(sidecar(ORACLE)); sidecar(GENERATOR); sidecar(REPORT); validate(document); rendered = emit(document)
    if args.write:
        TARGET.parent.mkdir(parents=True, exist_ok=True); TARGET.write_bytes(rendered); pathlib.Path(f"{TARGET}.sha256").write_text(f"{digest(rendered)}  {TARGET.name}\n"); print(f"classic noise include written ({digest(rendered)})")
    elif args.check:
        if sidecar(TARGET) != rendered: raise OracleError("generated include drift")
        print(f"classic noise include check passed ({digest(rendered)})")
    else:
        checks = [("schema", document["schema"] == SCHEMA), ("cases", len(document["render_cases"]) == 8), ("mutations", len(document["mutation_ledger"]) == 5), ("sidecars", True)]
        for label, ok in checks: print(f"  [{'ok' if ok else 'FAIL'}] {label}")
        if not all(ok for _, ok in checks): raise OracleError("Classic Noise materializer self-test failed")
        print(f"strict schema and payload self-tests verified ({len(checks)}/{len(checks)})")

if __name__ == "__main__":
    main()
