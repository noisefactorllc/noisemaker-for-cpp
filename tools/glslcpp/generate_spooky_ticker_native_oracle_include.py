#!/usr/bin/env python3
"""Materialize the standalone SpookyTicker oracle as a C++20 include."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/spooky-ticker-parity"
ORACLE = PACKAGE / "spooky-ticker-oracles.json"
INCLUDE = ROOT / "tests/oracles/spooky_ticker_expected.inc"
SCHEMA = "noisemaker-for-cpp.spooky-ticker.pixel-parity.v1"
PROGRAM = "filter/spookyTicker:spookyTicker"
FACTORY = "canonicalFactory147"
SOURCE_SHA = "d50ca880cd6c6c03dd01a7ae683316d42ed93baddaadce9f3b918be1c816d50f"
FACTORY_SHA = "9eb9fa9412b700f73e687209bb60803d121ab5e4e036a80d5552797011a0384b"

def digest(payload: bytes) -> str: return hashlib.sha256(payload).hexdigest()
def sidecar(path: Path, payload: bytes) -> str: return f"{digest(payload)}  {path.name}\n"
def reject_paths(value, label="oracle"):
    if isinstance(value, str):
        if value.startswith("/") or any(x in value for x in ("/private/", "/Users/", "/tmp/", "\\private\\", "\\Users\\")): raise ValueError(f"{label}: absolute path serialized")
    elif isinstance(value, list):
        for i, item in enumerate(value): reject_paths(item, f"{label}[{i}]")
    elif isinstance(value, dict):
        for key, item in value.items(): reject_paths(item, f"{label}.{key}")
def verify_sidecar(path: Path) -> bytes:
    payload = path.read_bytes()
    if path.with_name(path.name + ".sha256").read_text() != sidecar(path, payload): raise ValueError(f"sidecar drift: {path}")
    return payload
def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(verify_sidecar(path).decode(), object_pairs_hook=pairs)
def words(values, label):
    if not isinstance(values, list) or not values: raise ValueError(f"{label}: expected words")
    out=[]
    for i, value in enumerate(values):
        if not isinstance(value,str) or len(value)!=10 or not value.startswith("0x"): raise ValueError(f"{label}[{i}]: non-canonical word")
        n=int(value,16)
        if n>0xffffffff: raise ValueError(f"{label}[{i}]: overflow")
        out.append(n)
    return out
def bytes_values(values, label):
    if not isinstance(values,list) or any(isinstance(x,bool) or not isinstance(x,int) or not 0<=x<=255 for x in values): raise ValueError(f"{label}: invalid bytes")
    return values
def f32_word(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)): raise ValueError(f"{label}: invalid float")
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]
def int_word(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or not -(1 << 31) <= value < (1 << 31): raise ValueError(f"{label}: invalid int32")
    return value & 0xffffffff
def float_pair(values, label):
    if not isinstance(values, list) or len(values) != 2: raise ValueError(f"{label}: expected two floats")
    return [f32_word(x, f"{label}[{i}]") for i, x in enumerate(values)]
def validate(document):
    reject_paths(document)
    if document.get("schema") != SCHEMA or document.get("program_key") != PROGRAM: raise ValueError("schema/program lock mismatch")
    provenance=document.get("provenance",{}); factory=document.get("factory",{})
    if provenance.get("source_sha256") != SOURCE_SHA or factory.get("text_sha256") != FACTORY_SHA or factory.get("name") != FACTORY: raise ValueError("source/factory lock mismatch")
    if not factory.get("public_direct_identity") or factory.get("adapter_override"): raise ValueError("factory identity mismatch")
    cases=document.get("render_cases"); mutations=document.get("behavioral_mutation_ledger")
    if not isinstance(cases,list) or len(cases)!=7 or not isinstance(mutations,list) or len(mutations)!=10: raise ValueError("case/mutation cardinality mismatch")
    seen=set()
    expected_case_keys={"name","width","height","tile_rows","controls","input","output_f32_words_le","output_f32_sha256","output_rgba8_bytes","output_rgba8_sha256","input_immutable_exact_bits","input_lifetime_stable","public_direct_repeat_exact","distinct_storage"}
    expected_control_keys={"renderScale","time","speed","alpha","rows","seed","tileOffset","fullResolution"}
    expected_input_keys={"phase","f32_words_le","f32_sha256","rgba8_bytes","rgba8_sha256"}
    for case in cases:
        if set(case) != expected_case_keys: raise ValueError("case schema mismatch")
        name=case.get("name")
        if not isinstance(name,str) or name in seen: raise ValueError("duplicate case")
        seen.add(name); width,height=case.get("width"),case.get("height")
        if not isinstance(width,int) or not isinstance(height,int) or width<=0 or height<=0: raise ValueError(f"{name}: dimensions")
        expected=width*height*4; controls=case.get("controls")
        if not isinstance(controls,dict) or set(controls)!=expected_control_keys: raise ValueError(f"{name}: controls schema")
        for key in ("renderScale","time","speed","alpha"): f32_word(controls[key],f"{name}.controls.{key}")
        for key in ("rows","seed"): int_word(controls[key],f"{name}.controls.{key}")
        tile_offset=float_pair(controls["tileOffset"],f"{name}.controls.tileOffset"); full_resolution=float_pair(controls["fullResolution"],f"{name}.controls.fullResolution")
        if any(word == 0xffffffff for word in full_resolution): raise ValueError(f"{name}: invalid fullResolution")
        fwords=words(case.get("output_f32_words_le"),f"{name}.f32"); rgba=bytes_values(case.get("output_rgba8_bytes"),f"{name}.rgba")
        if len(fwords)!=expected or len(rgba)!=expected: raise ValueError(f"{name}: output cardinality")
        if digest(b"".join(struct.pack("<I",x) for x in fwords))!=case.get("output_f32_sha256") or digest(bytes(rgba))!=case.get("output_rgba8_sha256"): raise ValueError(f"{name}: output hash")
        if not all(case.get(k) is True for k in ("input_immutable_exact_bits","input_lifetime_stable","public_direct_repeat_exact","distinct_storage")): raise ValueError(f"{name}: identity guarantee")
        inp=case.get("input",{});
        if not isinstance(inp,dict) or set(inp)!=expected_input_keys: raise ValueError(f"{name}: input schema")
        if isinstance(inp.get("phase"),bool) or not isinstance(inp.get("phase"),int): raise ValueError(f"{name}: input phase")
        iw=words(inp.get("f32_words_le"),f"{name}.input.f32"); ib=bytes_values(inp.get("rgba8_bytes"),f"{name}.input.rgba")
        if len(iw)!=expected or len(ib)!=expected or digest(b"".join(struct.pack("<I",x) for x in iw))!=inp.get("f32_sha256") or digest(bytes(ib))!=inp.get("rgba8_sha256"): raise ValueError(f"{name}: input fixture")
    for mutation in mutations:
        if not mutation.get("name") or not mutation.get("anchor_text") or not mutation.get("replacement_text"): raise ValueError("incomplete mutation")
        if digest(mutation["anchor_text"].encode())!=mutation.get("anchor_sha256") or digest(mutation["replacement_text"].encode())!=mutation.get("replacement_sha256"): raise ValueError(f"{mutation['name']}: text hash")
        results=mutation.get("required_witness_results")
        if not isinstance(results,list) or not results or any(x.get("mismatched_lanes",0)<=0 or x.get("mismatched_bytes",0)<=0 for x in results): raise ValueError(f"{mutation['name']}: inert witness")
    comparer=document.get("comparer_self_tests")
    if set(comparer or {}) != {"good_equal","dimensions_mismatch","short_lane_count","long_lane_count","rgba8_mismatch","signed_zero_rejected","nan_payload_rejected","hostile_dimension_guard"} or not all(comparer.values()): raise ValueError("strict comparer lock mismatch")
    return cases,mutations
def cpp_string(value): return json.dumps(value, ensure_ascii=True)
def emit(document,cases,mutations):
    out=["// Authenticated filter/spookyTicker oracle; generated by generate_spooky_ticker_native_oracle_include.py.","#include <array>","#include <cstddef>","#include <cstdint>","#include <span>","#include <string_view>","","namespace noisemaker_spooky_ticker_oracle {","","struct ControlRecord { std::uint32_t render_scale_word; std::uint32_t time_word; std::uint32_t speed_word; std::uint32_t alpha_word; std::uint32_t rows_word; std::uint32_t seed_word; std::array<std::uint32_t, 2> tile_offset_words; std::array<std::uint32_t, 2> full_resolution_words; };","struct CaseRecord { std::string_view name; std::size_t width; std::size_t height; std::size_t tile_rows; ControlRecord controls; std::span<const std::uint32_t> input_f32_words; std::span<const std::uint8_t> input_rgba8_bytes; std::span<const std::uint32_t> output_f32_words; std::span<const std::uint8_t> output_rgba8_bytes; bool input_immutable_exact_bits; bool input_lifetime_stable; bool public_direct_repeat_exact; bool distinct_storage; };","struct MutationResult { std::string_view case_name; std::size_t mismatched_lanes; std::size_t mismatched_bytes; };","struct MutationRecord { std::string_view name; std::string_view anchor_text; std::string_view replacement_text; std::span<const MutationResult> required_results; };","struct ComparerSelfTests { bool good_equal; bool dimensions_mismatch; bool short_lane_count; bool long_lane_count; bool rgba8_mismatch; bool signed_zero_rejected; bool nan_payload_rejected; bool hostile_dimension_guard; };",""]
    for i,case in enumerate(cases):
        inp=case["input"]
        out.append(f"inline constexpr std::array<std::uint32_t, {len(inp['f32_words_le'])}> input_f32_words_{i}{{{{{', '.join(x+'u' for x in inp['f32_words_le'])}}}}};")
        out.append(f"inline constexpr std::array<std::uint8_t, {len(inp['rgba8_bytes'])}> input_rgba8_bytes_{i}{{{{{', '.join(str(x)+'u' for x in inp['rgba8_bytes'])}}}}};")
        out.append(f"inline constexpr std::array<std::uint32_t, {len(case['output_f32_words_le'])}> output_f32_words_{i}{{{{{', '.join(x+'u' for x in case['output_f32_words_le'])}}}}};")
        out.append(f"inline constexpr std::array<std::uint8_t, {len(case['output_rgba8_bytes'])}> output_rgba8_bytes_{i}{{{{{', '.join(str(x)+'u' for x in case['output_rgba8_bytes'])}}}}};")
    for i,m in enumerate(mutations): out.append(f"inline constexpr std::array<MutationResult, {len(m['required_witness_results'])}> mutation_results_{i}{{{{{', '.join('{'+cpp_string(x['case'])+', '+str(x['mismatched_lanes'])+'u, '+str(x['mismatched_bytes'])+'u}' for x in m['required_witness_results'])}}}}};")
    out.append(""); case_rows=[]
    for i,c in enumerate(cases):
        controls=c["controls"]
        words_text=(f"{{{f32_word(controls['renderScale'],'renderScale')}u, {f32_word(controls['time'],'time')}u, {f32_word(controls['speed'],'speed')}u, {f32_word(controls['alpha'],'alpha')}u, {int_word(controls['rows'],'rows')}u, {int_word(controls['seed'],'seed')}u, {{{', '.join(str(x)+'u' for x in float_pair(controls['tileOffset'],'tileOffset'))}}}, {{{', '.join(str(x)+'u' for x in float_pair(controls['fullResolution'],'fullResolution'))}}}}}")
        case_rows.append('{'+cpp_string(c['name'])+', '+str(c['width'])+'u, '+str(c['height'])+'u, '+str(c['tile_rows'])+'u, '+words_text+', input_f32_words_'+str(i)+', input_rgba8_bytes_'+str(i)+', output_f32_words_'+str(i)+', output_rgba8_bytes_'+str(i)+', true, true, true, true}')
    out.append(f"inline constexpr std::array<CaseRecord, {len(cases)}> kCases{{{{\n  {',\n  '.join(case_rows)}\n}}}};")
    out.append(f"inline constexpr std::array<MutationRecord, {len(mutations)}> kMutations{{{{\n  {',\n  '.join('{'+cpp_string(m['name'])+', '+cpp_string(m['anchor_text'])+', '+cpp_string(m['replacement_text'])+', mutation_results_'+str(i)+'}' for i,m in enumerate(mutations))}\n}}}};")
    out.append("inline constexpr auto kMutationWitnesses = kMutations;"); c=document["comparer_self_tests"]; out.append("inline constexpr ComparerSelfTests kComparerSelfTests{"+", ".join("true" if c[k] else "false" for k in ("good_equal","dimensions_mismatch","short_lane_count","long_lane_count","rgba8_mismatch","signed_zero_rejected","nan_payload_rejected","hostile_dimension_guard"))+"};"); out.extend(["","} // namespace noisemaker_spooky_ticker_oracle",""]); return "\n".join(out)
def main(mode):
    document=load(ORACLE); cases,mutations=validate(document); generated=emit(document,cases,mutations).encode()
    if mode=="--write": INCLUDE.parent.mkdir(parents=True,exist_ok=True); INCLUDE.write_bytes(generated); INCLUDE.with_name(INCLUDE.name+".sha256").write_text(sidecar(INCLUDE,generated)); Path(__file__).with_name(Path(__file__).name+".sha256").write_text(sidecar(Path(__file__),Path(__file__).read_bytes())); print("SpookyTicker native oracle include written")
    elif verify_sidecar(INCLUDE)!=generated: raise ValueError("SpookyTicker native oracle include drift")
    elif mode=="--check": print("SpookyTicker native oracle include checked")
    else:
        with tempfile.TemporaryDirectory(prefix="spooky-ticker-materializer-") as raw:
            forged=Path(raw)/ORACLE.name; forged.write_text(json.dumps({**document,"schema":"forged"})); forged.with_name(forged.name+".sha256").write_text(sidecar(forged,forged.read_bytes()))
            try: validate(load(forged))
            except ValueError: pass
            else: raise ValueError("matching-sidecar semantic forgery accepted")
        print("matching-sidecar forgery probes rejected")
if __name__=="__main__":
    try: main(sys.argv[1])
    except (OSError,ValueError,IndexError,json.JSONDecodeError) as e: print(f"error: {e}",file=sys.stderr); raise SystemExit(1)
