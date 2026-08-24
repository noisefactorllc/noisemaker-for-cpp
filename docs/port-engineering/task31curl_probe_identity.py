#!/usr/bin/env python3
"""Task 31 Curl: freeze target identity (raw/normalized bytes+hash, defines,
function count, whole/interface hash, loop proof, resources, factory
identity). Read-only: does not modify the noisemaker-for-cpp tree.
"""
import hashlib
import pathlib
import sys

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

KEY = "synth/curl:curl"
DEFINES = {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}
SRC_PATH = (REPO / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/"
            "sources/synth/curl/curl.glsl")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha_repr(value) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _whole(program):
    return _sha_repr((program.key, program.source, program.raw_source,
                       program.declarations, program.functions, program.resources,
                       program.body_status, program.local_type_names, program.structs,
                       program.uniform_blocks, program.interface_symbols,
                       program.builtin_symbols, program.counted_loop_proof,
                       program.preprocessor_defines))


def _interface(program):
    return _sha_repr((program.declarations, program.resources,
                       program.local_type_names, program.structs,
                       program.uniform_blocks, program.interface_symbols,
                       program.builtin_symbols, program.preprocessor_defines))


def span(value):
    s = value.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"


def main():
    raw = SRC_PATH.read_text()
    raw_bytes = raw.encode("utf-8")
    print("raw bytes:", len(raw_bytes))
    print("raw sha256:", sha(raw_bytes))

    parsed = parse_program(raw, KEY, DEFINES)
    program = analyze_program(parsed, KEY)

    normalized_bytes = program.source.encode("utf-8")
    print("normalized bytes:", len(normalized_bytes))
    print("normalized sha256:", sha(normalized_bytes))

    defines = tuple((d.name, d.kind, d.canonical_value) for d in program.preprocessor_defines)
    print("defines:", defines)

    print("function count:", len(program.functions))
    for f in program.functions:
        print(f"  id={f.id} name={f.name} return={f.return_type.display()} "
              f"params={len(f.parameters)} body_stmts={len(f.body)} span={span(f)}")

    print("whole-program sha256:", _whole(program))
    print("interface sha256:", _interface(program))

    proof = program.counted_loop_proof
    if proof is not None:
        print("loop proof tuple:", (proof.loop_count, proof.unproved_loop_count,
              proof.max_effective_depth, proof.max_lexical_product,
              proof.entrypoint_charge, proof.call_graph_acyclic))
    else:
        print("loop proof: None")

    r = program.resources
    print("resources uniforms:", r.uniforms)
    print("resources samplers:", r.samplers)
    print("resources outputs:", r.outputs)
    print("resources uses_texture:", r.uses_texture)
    print("resources uses_derivatives:", r.uses_derivatives)

    print("structs:", program.structs)
    print("uniform_blocks:", program.uniform_blocks)
    print("body_status:", program.body_status)

    print("functions sha256 (tuple):", _sha_repr(program.functions))

    main_fn = next((f for f in program.functions if f.name == "main"), None)
    print("main id:", main_fn.id if main_fn else None)
    print("main span:", span(main_fn) if main_fn else None)


if __name__ == "__main__":
    main()
