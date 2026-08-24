from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import emit_typed_cpp as emit
from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}
KEYS = (
    "mixer/focusBlur:focusBlur",
    "filter/lighting:lighting",
    "classicNoisedeck/caustic:caustic",
    "filter/extrude:extrude",
    "filter/waves:waves",
    "synth/curl:curl",
    "filter/posterize:posterize",
    "filter/watercolor:wcSimplify",
)


def digest(value: object) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()


def span(value: object) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


def first(error: Exception) -> str:
    return str(error).splitlines()[0]


def expression_nodes(value, path):
    yield path, value
    for index, child in enumerate(value.children):
        yield from expression_nodes(child, (*path, index))


def statement_nodes(value, path):
    for index, expression in enumerate(value.expressions):
        yield from expression_nodes(expression, (*path, f"e{index}"))
    for index, child in enumerate(value.children):
        yield from statement_nodes(child, (*path, f"s{index}"))


def function_nodes(function):
    for index, statement in enumerate(function.body):
        yield from statement_nodes(statement, (index,))


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, raw, defines, typed


def probe(program, source_hash, validator_extra=(), emitter_extra=(), sampler_parameter=False):
    old_caps, old_builtins = gen.APPROVED_CAPABILITIES, gen._BUILTINS
    old_names, old_types = dict(emit._BUILTIN_NAMES), dict(emit._TYPES)
    try:
        if validator_extra:
            gen.APPROVED_CAPABILITIES = (*old_caps, *validator_extra)
            gen._BUILTINS = frozenset((*old_builtins, *validator_extra))
        if emitter_extra:
            emit._BUILTIN_NAMES.update({name: name for name in emitter_extra})
        if sampler_parameter:
            emit._TYPES["sampler2D"] = "const Surface&"
        try:
            gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES,
                                      source_hash=source_hash)
            validator = "pass"
        except Exception as error:
            validator = first(error)
        try:
            cpp = emit.render_typed_cpp(program, program.key, source_hash,
                                        "future_probe", "bind_future_probe")
            emitter = "pass"
            cpp_hash = hashlib.sha256(cpp.encode()).hexdigest()
            cpp_bytes = len(cpp.encode())
        except Exception as error:
            emitter = first(error)
            cpp_hash = None
            cpp_bytes = None
        return {"validator": validator, "emitter": emitter,
                "cpp_sha256": cpp_hash, "cpp_bytes": cpp_bytes,
                "cpp": cpp if cpp_hash is not None else None}
    finally:
        gen.APPROVED_CAPABILITIES = old_caps
        gen._BUILTINS = old_builtins
        emit._BUILTIN_NAMES.clear()
        emit._BUILTIN_NAMES.update(old_names)
        emit._TYPES.clear()
        emit._TYPES.update(old_types)


target_builtins = {
    "filter/lighting:lighting": ("reflect",),
    "classicNoisedeck/caustic:caustic": ("floatBitsToUint",),
    "filter/extrude:extrude": ("all",),
    "filter/waves:waves": ("any",),
    "synth/curl:curl": ("tanh",),
    "filter/posterize:posterize": ("round",),
}

rows = []
for key in KEYS:
    entry, raw, defines, program = load(key)
    initial = probe(program, entry["raw_sha256"])
    target = target_builtins.get(key, ())
    projected = probe(program, entry["raw_sha256"], target, target,
                      key == "mixer/focusBlur:focusBlur")
    if key == "mixer/focusBlur:focusBlur" and projected["cpp"] is not None:
        wrapper = """#include \"noisemaker/generated/catalog.hpp\"\n\n#include <array>\n#include <cstdint>\n#include <memory>\n#include <stdexcept>\n\n#include \"noisemaker/sampler.hpp\"\n\nnamespace noisemaker::generated {\n"""
        wrapper += projected["cpp"]
        wrapper += "\n}  // namespace noisemaker::generated\n"
        Path(__file__).with_name("focus-blur-borrowed-sampler-projection.cpp").write_text(
            wrapper)
    initial.pop("cpp", None)
    projected.pop("cpp", None)
    definitions = {f.signature.id: f for f in program.functions if f.body}
    main = next(function for function in program.functions if function.name == "main")
    reachable = {main.signature.id}
    pending = [main.signature.id]
    while pending:
        function = definitions[pending.pop()]
        for _, value in function_nodes(function):
            if (value.kind == "call" and value.signature_id in definitions
                    and value.signature_id not in reachable):
                reachable.add(value.signature_id)
                pending.append(value.signature_id)
    builtin_sites = []
    call_sites = []
    for function in program.functions:
        for path, value in function_nodes(function):
            if value.kind == "builtin":
                builtin_sites.append({
                    "owner": function.name,
                    "owner_signature_id": function.signature.id,
                    "owner_reachable": function.signature.id in reachable,
                    "path": list(path), "span": span(value),
                    "callee": value.callee, "signature_id": value.signature_id,
                    "result_type": value.type.display(),
                    "argument_types": [x.type.display() for x in value.children],
                    "sha256": digest(value),
                })
            elif value.kind == "call":
                call_sites.append({
                    "owner": function.name,
                    "owner_signature_id": function.signature.id,
                    "path": list(path), "span": span(value),
                    "callee": value.callee, "signature_id": value.signature_id,
                    "result_type": value.type.display(),
                    "argument_types": [x.type.display() for x in value.children],
                    "argument_symbol_ids": [x.symbol_id for x in value.children],
                    "argument_symbol_names": [x.symbol.name if x.symbol else None for x in value.children],
                    "sha256": digest(value),
                })
    declarations = [{
        "id": d.symbol.id, "name": d.symbol.name, "type": d.type.display(),
        "storage": d.symbol.storage, "writable": d.symbol.writable,
        "direction": d.symbol.direction, "span": span(d),
        "initializer_sha256": digest(d.initializer) if d.initializer else None,
    } for d in program.declarations]
    functions = [{
        "id": f.signature.id, "name": f.name, "return": f.return_type.display(),
        "span": span(f), "body_statement_count": len(f.body),
        "sha256": digest(f),
        "parameters": [{"id": p.id, "name": p.name,
                        "type": p.type.display(), "direction": p.direction,
                        "span": span(p)} for p in f.parameters],
    } for f in program.functions]
    whole = (program.key, program.source, program.raw_source, program.declarations,
             program.functions, program.resources, program.body_status,
             program.local_type_names, program.structs, program.uniform_blocks,
             program.interface_symbols, program.builtin_symbols,
             program.counted_loop_proof, program.preprocessor_defines)
    interface = (program.declarations, program.resources, program.local_type_names,
                 program.structs, program.uniform_blocks,
                 program.interface_symbols, program.builtin_symbols,
                 program.preprocessor_defines)
    rows.append({
        "key": key, "source": entry["source"], "defines": defines,
        "raw_bytes": len(raw.encode()), "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "normalized_bytes": len(program.source.encode()),
        "normalized_sha256": hashlib.sha256(program.source.encode()).hexdigest(),
        "whole_program_sha256": digest(whole), "interface_sha256": digest(interface),
        "function_tuple_sha256": digest(program.functions),
        "declarations": declarations, "functions": functions,
        "resources": dataclasses.asdict(program.resources),
        "loop_proof": dataclasses.asdict(program.counted_loop_proof),
        "reachable_function_ids": sorted(reachable),
        "builtin_sites": builtin_sites, "call_sites": call_sites,
        "initial_probe": initial,
        "target_builtins_temporarily_admitted": list(target),
        "post_target_probe": projected,
    })

typed_keys = sorted(row["program_key"] for row in json.loads(
    (ROOT / "tools/glslcpp/typed_slice.json").read_text())["programs"])
payload = {
    "schema": "noisemaker-for-cpp.future-precompute.candidates.v1",
    "corpus_revision": REVISION,
    "accepted_start": {
        "typed_count": len(typed_keys),
        "typed_sorted_sha256": hashlib.sha256(("\n".join(typed_keys) + "\n").encode()).hexdigest(),
        "public_count": len(typed_keys) + 2,
        "unported_count": len(ENTRIES) - len(typed_keys) - 2,
    },
    "probe_method": {
        "validator": "current validator; second probe temporarily adds only named builtin to local capability tuple",
        "emitter": "current emitter; second probe temporarily maps only named builtin or sampler2D parameter spelling",
        "warning": "post-target probes reveal the next mechanical blocker; they are not authorization or proof profiles",
    },
    "rows": rows,
}
out = Path(__file__).with_name("candidate-analysis.json")
out.write_text(json.dumps(payload, indent=2) + "\n")
print(out)
