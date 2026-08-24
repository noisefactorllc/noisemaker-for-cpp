#!/usr/bin/env python3
"""Fail-closed materializer for the authenticated Moodscape pixel oracle."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/moodscape-parity"
ORACLE = PACKAGE / "moodscape-oracles.json"
REPORT = PACKAGE / "moodscape-oracle-report.md"
GENERATOR = PACKAGE / "moodscape_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_moodscape_native_oracle_include.py"
OUTPUT = ROOT / "tests/oracles/moodscape_expected.inc"
SCHEMA = "noisemaker-for-cpp.moodscape.pixel-parity.v1"
KEY = "classicNoisedeck/moodscape:moodscape"
SOURCE = "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/moodscape/moodscape.glsl"
SOURCE_SHA = "a2580a36096208dd7a63965d2b277be9356f29a8d3af634d1736df9142db1a44"
FACTORY_SHA = "70db1168604045e22ac0c74f4b58a96d5e4ed2c6e107ec2fe3b2beab08ca479d"
EXPECTED_CLOSURE = [
    ("src/csl/glsl-kernel.js", "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa"), ("src/csl/glsl-runtime.js", "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072"), ("src/csl/runtime.js", "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee"), ("src/effects/adapters/bit-effects.js", "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7"), ("src/effects/adapters/crt.js", "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc"), ("src/effects/adapters/f32-color.js", "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046"), ("src/effects/adapters/fractal.js", "0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29"), ("src/effects/adapters/index.js", "40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267"), ("src/effects/adapters/julia.js", "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5"), ("src/effects/adapters/median.js", "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583"), ("src/effects/adapters/palette.js", "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452"), ("src/effects/adapters/snow.js", "202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366"), ("src/effects/catalog.js", "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4"), ("src/effects/definition.js", "fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02"), ("src/effects/generated/canonical-adapter-data.js", "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab"), ("src/effects/generated/canonical-kernels.js", "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe"), ("src/effects/generated/kernels.js", "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01"), ("src/effects/generated/upstream-snapshot.js", "e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090"), ("src/effects/registry.js", "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618"), ("src/runtime/pass-runner.js", "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa"), ("src/runtime/sampler.js", "1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328"), ("src/runtime/surface.js", "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59"),
]
NAMES = ["NOISE_TYPE", "COLOR_MODE", "time", "seed", "wrap", "resolution", "tileOffset", "fullResolution", "noiseScale", "refractAmt", "speed", "hueRotation", "hueRange", "intensity", "ridges"]
RUNTIME_ABI = {"NOISE_TYPE":"int32", "COLOR_MODE":"int32", "time":"float", "seed":"int32", "wrap":"bool", "resolution":"Vec2", "tileOffset":"Vec2", "fullResolution":"Vec2", "noiseScale":"float", "refractAmt":"float", "speed":"float", "hueRotation":"float", "hueRange":"float", "intensity":"float", "ridges":"bool"}
SOURCE_ABI = {"time":"float", "seed":"int", "wrap":"bool", "resolution":"vec2", "tileOffset":"vec2", "fullResolution":"vec2", "noiseScale":"float", "refractAmt":"float", "speed":"float", "hueRotation":"float", "hueRange":"float", "intensity":"float", "ridges":"bool"}
CASES = [("default-public",4,3,.25,44,[0,0],[4,3],85,5,25,180,25,0,True,True),("tiny-origin",1,1,0,0,[0,0],[1,1],1,0,0,0,0,-100,False,False),("negative-intensity",6,5,-1.5,7,[0,0],[6,5],42,67,100,35,90,-75,True,False),("tile-offset",5,4,2.75,91,[2,1],[11,9],100,33,13,270,55,40,False,True),("hue-extremes",7,3,19.25,3,[0,0],[7,3],12,100,1,359,100,100,True,False),("zero-speed",3,2,.125,214,[1,0],[8,7],2,1,0,90,1,1,False,True)]
MUTATION_PINS = {
    "noise-frequency": ("xFreq = map(noiseScale, 1, 100, 1, 0.25);", "xFreq = map(noiseScale, 1, 100, 1, 0.5);", "ed551f6db2cd336b2cbe03fd8621cfff0f4985f0a579a65e4175b5d3fd32f89b", (("default-public",36,36,False),("tiny-origin",0,0,True),("negative-intensity",90,74,False),("tile-offset",60,59,False),("hue-extremes",63,60,False),("zero-speed",18,10,False))),
    "refract-amount": ("var ref = map(refractAmt, 0, 100, 0, 2.5);", "var ref = map(refractAmt, 0, 100, 0, 1.5);", "6c8c4d0d1f86ad31908e5898a7b2e69c29c52fe34f0e8d3f1f7a5426da979eb9", (("default-public",36,28,False),("tiny-origin",0,0,True),("negative-intensity",90,63,False),("tile-offset",60,58,False),("hue-extremes",63,59,False),("zero-speed",18,14,False))),
    "hue-range-factor": ("color[0] = (color[0] * hueRange) * 0.009999999776482582;", "color[0] = (color[0] * hueRange) * 0.019999999552965164;", "dc61a38fc3f0adab907429edd5401bd614e409f2de250c1e906d99fe8c09cd0e", (("default-public",22,12,False),("tiny-origin",0,0,True),("negative-intensity",69,44,False),("tile-offset",48,45,False),("hue-extremes",43,29,False),("zero-speed",6,2,False))),
    "simplex-speed-factor": ("var scaledTime10 = ((simplexValue(st, xFreq, yFreq, s + 50, time)) * speed) * 0.0024999999441206455;", "var scaledTime10 = ((simplexValue(st, xFreq, yFreq, s + 50, time)) * speed) * 0.004999999888241291;", "8a0bc0ccd72472a1414b3375104cb66e16a063bb6086b068466fd2d4b55752be", (("default-public",36,35,False),("tiny-origin",0,0,True),("negative-intensity",90,58,False),("tile-offset",60,58,False),("hue-extremes",63,37,False),("zero-speed",0,0,True))),
    "brightness-map": ("var bright = map(intensity, -100, 100, -0.4000000059604645, 0.4000000059604645);", "var bright = map(intensity, -100, 100, -0.20000000298023224, 0.20000000298023224);", "9ea561fce3ff1733e54fb4455927fc93707d5e8b8621cb3bd10c7dfe0084d2cb", (("default-public",0,0,True),("tiny-origin",3,3,False),("negative-intensity",90,90,False),("tile-offset",60,59,False),("hue-extremes",63,57,False),("zero-speed",18,11,False))),
}
TOP = {"schema","schema_version","program_key","effect_key","runtime_key","corpus_revision","upstream_revision","defines","exactness_contract","comparer_self_tests","authority","factory","provenance","runtime_binding_names","runtime_binding_abi","source_uniform_abi","output_abi","render_cases","mutation_anchor_cardinality","mutation_ledger","claim_boundaries"}

class OracleError(RuntimeError): pass
def digest(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def sidecar(path: Path) -> None:
    if not path.is_file() or not Path(f"{path}.sha256").is_file() or Path(f"{path}.sha256").read_text() != f"{digest(path.read_bytes())}  {path.name}\n": raise OracleError(f"missing or stale sidecar: {path}")
def pairs(items):
    out = {}
    for key, value in items:
        if key in out: raise OracleError(f"duplicate JSON key: {key}")
        out[key] = value
    return out
def load() -> dict:
    sidecar(ORACLE)
    try: return json.loads(ORACLE.read_text(), object_pairs_hook=pairs)
    except (OSError, json.JSONDecodeError) as exc: raise OracleError(f"invalid oracle JSON: {exc}") from exc
def f32(value, label):
    if isinstance(value, bool) or not isinstance(value,(int,float)) or not math.isfinite(float(value)): raise OracleError(f"{label}: expected finite number")
    try: return f"0x{struct.unpack('<I',struct.pack('<f',float(value)))[0]:08x}"
    except (OverflowError,struct.error) as exc: raise OracleError(f"{label}: outside Float32 range") from exc
def word_digest(values):
    try: return digest(b"".join(struct.pack("<I",int(value,16)) for value in values))
    except (TypeError,ValueError,struct.error) as exc: raise OracleError("invalid Float32 word") from exc
def valid_word(value):
    return isinstance(value, str) and len(value) == 10 and value.startswith("0x") and all(char in "0123456789abcdef" for char in value[2:])
def validate_source_file(root: Path = ROOT) -> bytes:
    try: payload = (root / SOURCE).read_bytes()
    except OSError as exc: raise OracleError("local GLSL source bytes drift") from exc
    if len(payload) != 19559 or digest(payload) != SOURCE_SHA: raise OracleError("local GLSL source bytes drift")
    return payload

def validate(doc: dict) -> None:
    if not isinstance(doc,dict) or set(doc) != TOP: raise OracleError("document fields mismatch")
    if (doc["schema"],doc["schema_version"],doc["program_key"],doc["effect_key"],doc["runtime_key"]) != (SCHEMA,1,KEY,"classicNoisedeck/moodscape",KEY): raise OracleError("schema or program identity mismatch")
    if doc["corpus_revision"] != "a024dc3a960cc44af454abc7aebce50456c194e6" or doc["upstream_revision"] != "117a236679d1db3ab8f0e278230ece277b57564c": raise OracleError("revision provenance mismatch")
    if doc["defines"] != {"NOISE_TYPE":10,"COLOR_MODE":2} or doc["runtime_binding_names"] != NAMES or doc["runtime_binding_abi"] != RUNTIME_ABI or doc["source_uniform_abi"] != SOURCE_ABI: raise OracleError("ABI mismatch")
    if doc["output_abi"] != {"name":"fragColor","source_type":"vec4","runtime_type":"Vec4","role":"output"}: raise OracleError("output ABI mismatch")
    if doc["factory"] != {"name":"canonicalFactory11","text_sha256":FACTORY_SHA,"public_factory_is_canonical_identity":True,"canonical_adapter_factories_own_key":False}: raise OracleError("factory provenance mismatch")
    if doc["provenance"] != {"source":{"relative_path":SOURCE,"bytes":19559,"sha256":SOURCE_SHA},"generator":{"relative_path":"docs/port-engineering/moodscape-parity/moodscape_oracle_generator.mjs"},"materializer":{"relative_path":"tools/glslcpp/generate_moodscape_native_oracle_include.py"}}: raise OracleError("source provenance mismatch")
    validate_source_file()
    authority = doc["authority"]; expected_closure = [{"relative_path":p,"sha256":h} for p,h in EXPECTED_CLOSURE]
    if authority != {"node_version":"v24.7.0","oracle":"unmodified canonical Moodscape factory from immutable CPU snapshot","cpu_root_argument":"<immutable-cpu-snapshot-root>","immutable_snapshot":True,"realpath_containment_checked":True,"live_checkout_rejected":True,"closure_cardinality":22,"import_closure":expected_closure}: raise OracleError("authority closure provenance mismatch")
    expected_tests = {"good","dimensions_before_access","f32_short_count","f32_long_count","rgba8_short_count","rgba8_long_count","signed_zero","nan_payload","rgba_mismatch","control_mutation_rejected"}
    if set(doc["comparer_self_tests"]) != expected_tests or not all(value is True for value in doc["comparer_self_tests"].values()): raise OracleError("comparer self-test failure")
    if doc["exactness_contract"] != {"float32":"raw little-endian uint32 words; signed zero and NaN payloads significant","rgba8":"complete independent RGBA8 bytes","tolerance":"none","comparison":"dimensions, counts, every uint32 word, every RGBA8 byte"}: raise OracleError("exactness contract mismatch")
    if len(doc["render_cases"]) != 6: raise OracleError("render case census mismatch")
    for case, frozen in zip(doc["render_cases"], CASES):
        keys = {"name","width","height","time","seed","tileOffset","fullResolution","noiseScale","refractAmt","speed","hueRotation","hueRange","intensity","ridges","wrap","expected","f32_byte_count","rgba8_byte_count","repeat","storage","controls_snapshot"}
        controls = tuple(case.get(key) for key in ("name","width","height","time","seed","tileOffset","fullResolution","noiseScale","refractAmt","speed","hueRotation","hueRange","intensity","ridges","wrap"))
        if set(case) != keys or controls != frozen: raise OracleError(f"case controls mismatch: {case.get('name')}")
        count = case["width"] * case["height"] * 4; output = case["expected"]
        if case["f32_byte_count"] != count * 4 or case["rgba8_byte_count"] != count or set(output) != {"f32_words_le","f32_sha256","rgba8_bytes","rgba8_sha256"}: raise OracleError(f"case counts mismatch: {case.get('name')}")
        if not isinstance(output["f32_words_le"],list) or len(output["f32_words_le"]) != count or any(not valid_word(word) for word in output["f32_words_le"]) or output["f32_sha256"] != word_digest(output["f32_words_le"]): raise OracleError(f"Float32 digest mismatch: {case.get('name')}")
        if not isinstance(output["rgba8_bytes"],list) or len(output["rgba8_bytes"]) != count or any(type(v) is not int or not 0 <= v <= 255 for v in output["rgba8_bytes"]) or output["rgba8_sha256"] != digest(bytes(output["rgba8_bytes"])): raise OracleError(f"RGBA8 digest mismatch: {case.get('name')}")
        if case["repeat"] != {"exact":True,"dimensions":True,"f32_words":True,"rgba8_bytes":True} or case["storage"] != {"distinct_surface_objects":True,"distinct_f32_backing_stores":True} or case["controls_snapshot"] != {"unchanged":True,"typed_array_bits_unchanged":True}: raise OracleError(f"repeat/storage proof mismatch: {case.get('name')}")
    if len(doc["mutation_ledger"]) != 5 or doc["mutation_anchor_cardinality"] != {"total":5,"anchors":{name:1 for name in MUTATION_PINS}}: raise OracleError("mutation census/cardinality mismatch")
    if any(not isinstance(mutation, dict) for mutation in doc["mutation_ledger"]): raise OracleError("mutation entries must be objects")
    mutation_names = tuple(mutation.get("name") for mutation in doc["mutation_ledger"])
    if mutation_names != tuple(MUTATION_PINS) or len(set(mutation_names)) != len(mutation_names): raise OracleError("mutation ledger order or uniqueness mismatch")
    mutation_keys = {"name","anchor","replacement","anchor_sha256","replacement_sha256","mutated_factory_sha256","independent","anchor_cardinality","witnesses","results"}
    for mutation in doc["mutation_ledger"]:
        if set(mutation) != mutation_keys: raise OracleError(f"mutation fields mismatch: {mutation.get('name')}")
        anchor, replacement, factory_sha, frozen_rows = MUTATION_PINS[mutation["name"]]
        expected_witnesses = tuple(row[0] for row in frozen_rows if row[1] > 0 and row[2] > 0)
        if (mutation["anchor"] != anchor or mutation["replacement"] != replacement or mutation["independent"] is not True or mutation["anchor_cardinality"] != 1 or mutation["mutated_factory_sha256"] != factory_sha or mutation["anchor_sha256"] != digest(anchor.encode()) or mutation["replacement_sha256"] != digest(replacement.encode())): raise OracleError(f"mutation provenance mismatch: {mutation.get('name')}")
        if type(mutation["witnesses"]) is not list or tuple(mutation["witnesses"]) != expected_witnesses or len(set(mutation["witnesses"])) != len(mutation["witnesses"]): raise OracleError(f"mutation witnesses mismatch: {mutation.get('name')}")
        if not isinstance(mutation["results"], list) or len(mutation["results"]) != 6 or any(not isinstance(row, dict) or set(row) != {"case","exact","changed_float32_lanes","changed_rgba8_bytes"} for row in mutation["results"]): raise OracleError(f"mutation result mismatch: {mutation.get('name')}")
        if tuple((row["case"], row["changed_float32_lanes"], row["changed_rgba8_bytes"], row["exact"]) for row in mutation["results"]) != frozen_rows: raise OracleError(f"mutation result authority mismatch: {mutation.get('name')}")
        if not all(row["changed_float32_lanes"] > 0 and row["changed_rgba8_bytes"] > 0 for row in mutation["results"] if row["case"] in expected_witnesses): raise OracleError(f"mutation witness evidence mismatch: {mutation.get('name')}")
    if doc["claim_boundaries"] != {"canonical_factory_only":True,"typed_slice_landing":False,"shared_emitter_modified":False,"samplers":False,"input_textures":False}: raise OracleError("claim boundaries mismatch")

def render(doc: dict, oracle_sha256: str | None = None) -> bytes:
    oracle_sha256 = oracle_sha256 or digest(ORACLE.read_bytes()); lines = ["// Generated by generate_moodscape_native_oracle_include.py; exact JSON authority.","#pragma once","#include <array>","#include <cstdint>","#include <span>","#include <string_view>","","namespace noisemaker_moodscape_oracle {"]
    lines += [f'inline constexpr std::string_view kSchema = "{SCHEMA}";',f'inline constexpr std::string_view kProgramKey = "{KEY}";',f'inline constexpr std::string_view kOracleJsonSha256 = "{oracle_sha256}";',f'inline constexpr std::string_view kFactorySha256 = "{FACTORY_SHA}";',f'inline constexpr std::string_view kSourceSha256 = "{SOURCE_SHA}";','inline constexpr std::uint32_t kSourceBytes = 19559U;',f'inline constexpr std::string_view kSourceRelativePath = "{SOURCE}";','struct ImportClosureEntry { std::string_view relativePath; std::string_view sha256; };','inline constexpr std::uint32_t kImportClosureCardinality = 22U;','inline constexpr std::array<ImportClosureEntry, 22> kImportClosure = {']
    lines += [f'  ImportClosureEntry{{"{p}", "{h}"}},' for p,h in EXPECTED_CLOSURE]; lines += ['};','struct Float32Word { std::uint32_t bits; };','struct Vec2Float32 { Float32Word x; Float32Word y; };','struct CaseControls { Float32Word time; std::int32_t seed; bool wrap; Vec2Float32 resolution; Vec2Float32 tileOffset; Vec2Float32 fullResolution; Float32Word noiseScale; Float32Word refractAmt; Float32Word speed; Float32Word hueRotation; Float32Word hueRange; Float32Word intensity; bool ridges; };','struct RuntimeBinding { std::string_view name; std::string_view runtimeAbi; std::string_view sourceAbi; };','inline constexpr std::array<RuntimeBinding, 15> kRuntimeBindings = {']
    for name in NAMES: lines.append(f'  RuntimeBinding{{"{name}", "{RUNTIME_ABI[name]}", "{SOURCE_ABI.get(name, "define")}"}},')
    lines += ['};','struct CaseSummary { std::string_view name; std::uint32_t width, height; std::string_view f32Sha256, rgba8Sha256; std::uint32_t f32ByteCount, rgba8ByteCount; CaseControls controls; bool repeatExact, distinctSurfaceObjects, distinctF32BackingStores, controlsUnchanged; };']
    summaries = []
    for index, case in enumerate(doc["render_cases"]):
        out = case["expected"]; words = [f32(case[key],key) for key in ("time","noiseScale","refractAmt","speed","hueRotation","hueRange","intensity")]; vectors = {name:[f32(v,name) for v in case[name]] for name in ("tileOffset","fullResolution")}; res = [f32(case["width"],"resolution"),f32(case["height"],"resolution")]
        controls = f'Float32Word{{{words[0]}}}, {case["seed"]}, {str(case["wrap"]).lower()}, Vec2Float32{{Float32Word{{{res[0]}}}, Float32Word{{{res[1]}}}}}, Vec2Float32{{Float32Word{{{vectors["tileOffset"][0]}}}, Float32Word{{{vectors["tileOffset"][1]}}}}}, Vec2Float32{{Float32Word{{{vectors["fullResolution"][0]}}}, Float32Word{{{vectors["fullResolution"][1]}}}}}, ' + ', '.join(f'Float32Word{{{word}}}' for word in words[1:]) + f', {str(case["ridges"]).lower()}'
        lines.append(f'inline constexpr CaseControls kCase{index}Controls{{{controls}}};'); lines.append(f'inline constexpr std::array<std::uint32_t, {len(out["f32_words_le"])}> kCase{index}F32 = {{{", ".join(out["f32_words_le"])}}};'); lines.append(f'inline constexpr std::array<std::uint8_t, {len(out["rgba8_bytes"])}> kCase{index}Rgba8 = {{{", ".join(str(v) for v in out["rgba8_bytes"])}}};')
        summaries.append(f'  CaseSummary{{"{case["name"]}", {case["width"]}U, {case["height"]}U, "{out["f32_sha256"]}", "{out["rgba8_sha256"]}", {case["f32_byte_count"]}U, {case["rgba8_byte_count"]}U, kCase{index}Controls, true, true, true, true}}')
    lines += [f'inline constexpr std::array<CaseSummary, {len(summaries)}> kCases = {{',',\n'.join(summaries),'};','struct MutationResult { std::string_view caseName; bool exact; std::uint32_t changedFloat32Lanes, changedRgba8Bytes; };','struct MutationSummary { std::string_view name, anchor, replacement, anchorSha256, replacementSha256, mutatedFactorySha256; std::span<const std::string_view> witnesses; std::span<const MutationResult> results; };']
    pairs = []
    for index, mutation in enumerate(doc["mutation_ledger"]):
        witness_name = f"kMutation{index}Witnesses"; result_name = f"kMutation{index}Results"; lines.append(f'inline constexpr std::array<std::string_view, {len(mutation["witnesses"])}> {witness_name} = {{{", ".join(chr(34)+name+chr(34) for name in mutation["witnesses"])}}};'); result_values = ', '.join(f'MutationResult{{"{row["case"]}", {str(row["exact"]).lower()}, {row["changed_float32_lanes"]}U, {row["changed_rgba8_bytes"]}U}}' for row in mutation["results"]); lines.append(f'inline constexpr std::array<MutationResult, 6> {result_name} = {{{result_values}}};'); pairs.append(f'  MutationSummary{{"{mutation["name"]}", R"anchor({mutation["anchor"]})anchor", R"replacement({mutation["replacement"]})replacement", "{mutation["anchor_sha256"]}", "{mutation["replacement_sha256"]}", "{mutation["mutated_factory_sha256"]}", {witness_name}, {result_name}}}')
    lines += [f'inline constexpr std::array<MutationSummary, {len(pairs)}> kMutations = {{',',\n'.join(pairs),'};','}  // namespace noisemaker_moodscape_oracle','']; return '\n'.join(lines).encode()

def main() -> int:
    parser = argparse.ArgumentParser(); group = parser.add_mutually_exclusive_group(required=True); group.add_argument("--write",action="store_true"); group.add_argument("--check",action="store_true"); group.add_argument("--self-test",action="store_true"); args = parser.parse_args()
    for path in (GENERATOR,ORACLE,REPORT,MATERIALIZER): sidecar(path)
    document = load(); validate(document); output = render(document)
    if args.write: OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_bytes(output); Path(f"{OUTPUT}.sha256").write_text(f"{digest(output)}  {OUTPUT.name}\n"); print(f"moodscape include written ({digest(output)})")
    elif args.self_test:
        checks=[]
        for label, mutate in (("schema",lambda d:d.__setitem__("schema","forged")),("closure",lambda d:d["authority"]["import_closure"].pop()),("comparer",lambda d:d["comparer_self_tests"].__setitem__("rgba_mismatch",False)),("mutation",lambda d:d["mutation_ledger"][0].__setitem__("independent",False))):
            forged=json.loads(json.dumps(document)); mutate(forged)
            try: validate(forged)
            except OracleError: checks.append((label,True))
            else: checks.append((label,False))
        for label,ok in checks: print(f"  [{'ok' if ok else 'FAIL'}] {label} forge rejected")
        if not all(ok for _,ok in checks): raise OracleError("self-test accepted forged document")
        print(f"strict schema, authority, comparer, and mutation self-tests verified ({len(checks)}/{len(checks)})")
    else:
        sidecar(OUTPUT)
        if OUTPUT.read_bytes() != output: raise OracleError("generated include drift")
        print(f"moodscape include check passed ({digest(output)})")
    return 0
if __name__ == "__main__": raise SystemExit(main())
