#!/usr/bin/env python3
"""Read-only extraction of exact node-identity facts for the 15 landable
derivative programs (posterize/waves excluded per the task brief).

Imports the real, unmodified glslcpp frontend from
. (never writes into that repo).
Computes, for each program, exactly the facts a
derivative-admission profile module needs to freeze:

  - raw/normalized byte lengths + sha256
  - authorized define map
  - functions_sha256 / whole_sha256 / interface_sha256 (same recipe as
    validate_current_vocabulary_degauss/_crt and the curl/extrude profiles)
  - counted_loop_proof tuple
  - resources tuple (uniforms, samplers, outputs, uses_texture, uses_derivatives)
  - function inventory tuple (id, name, return type, param count, body stmt
    count, span)
  - EVERY dFdx/dFdy/fwidth call site anywhere in the whole program (not just
    main), each as (callee, owning function id, path, span, result type,
    node sha256, parent kind, child type tuple, child sha256 tuple) -- same
    shape as curl_vector_math_profile.py's _NODES
  - the statement ancestor chain (kind, span) for each site

Output: admission-facts.json in this directory.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp import check_corpus  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp.generate_typed_slice import _defaults  # noqa: E402

CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS_ROOT = REPO / "tools/glslcpp/corpus" / CORPUS_REVISION

PROGRAM_KEYS = [
    "filter/bulge:bulge",
    "filter/celShading:celShadingColor",
    "filter/halftone:halftone",
    "filter/lens:lens",
    "filter/lensWarp:lensWarp",
    "filter/octaveWarp:octaveWarp",
    "filter/pinch:pinch",
    "filter/polar:polar",
    "filter/pondRipples:pondRipples",
    "filter/spiral:spiral",
    "filter/stamp:stThreshold",
    "filter/step:step",
    "filter/stipple:stipple",
    "filter/tunnel:tunnel",
    "filter/warp:warp",
]

DERIVATIVE_BUILTINS = {"dFdx", "dFdy", "fwidth"}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


def _manifest_entry(key: str) -> dict:
    manifest = check_corpus._load_json(CORPUS_ROOT / "manifest.json", "manifest")
    entries = {item["program_key"]: item for item in check_corpus._validate_manifest(manifest)}
    return entries[key]


def _walk_expression(value, parent=None, path=()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value, path=(), ancestors=()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, epath in _walk_expression(expression, None, (*path, f"e{index}")):
            yield item, parent, epath, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def process(key: str) -> dict:
    entry = _manifest_entry(key)
    source_path = CORPUS_ROOT / entry["source"]
    raw_source = source_path.read_text(encoding="utf-8")
    raw_bytes_actual = len(raw_source.encode("utf-8"))
    raw_sha256_actual = _sha256(raw_source.encode("utf-8"))

    defines = _defaults(REPO, key)

    parsed = parse_program(raw_source, key, defines)
    normalized_bytes_actual = len(parsed["source"].encode("utf-8"))
    normalized_sha256_actual = _sha256(parsed["source"].encode("utf-8"))

    typed = analyze_program(parsed, key)

    functions_sha256 = _sha256(repr(typed.functions).encode("utf-8"))
    whole = (
        typed.key, typed.source, typed.raw_source, typed.declarations,
        typed.functions, typed.resources, typed.body_status,
        typed.local_type_names, typed.structs, typed.uniform_blocks,
        typed.interface_symbols, typed.builtin_symbols,
        typed.counted_loop_proof, typed.preprocessor_defines,
    )
    whole_sha256 = _sha256(repr(whole).encode("utf-8"))
    interface = (
        typed.declarations, typed.resources, typed.local_type_names,
        typed.structs, typed.uniform_blocks, typed.interface_symbols,
        typed.builtin_symbols, typed.preprocessor_defines,
    )
    interface_sha256 = _sha256(repr(interface).encode("utf-8"))

    r = typed.resources
    resources_tuple = (r.uniforms, r.samplers, r.outputs, r.uses_texture, r.uses_derivatives)
    preprocessor_defines_tuple = tuple(
        (item.name, item.kind, item.canonical_value) for item in typed.preprocessor_defines)

    functions_tuple = tuple(
        (f.signature.id, f.signature.name, f.return_type.display(),
         len(f.parameters), len(f.body), _span(f))
        for f in sorted(typed.functions, key=lambda item: item.signature.id)
    )

    proof = typed.counted_loop_proof
    loop_proof_tuple = None if proof is None else (
        proof.loop_count, proof.unproved_loop_count, proof.max_effective_depth,
        proof.max_lexical_product, proof.entrypoint_charge, proof.call_graph_acyclic)

    # Census every dFdx/dFdy/fwidth site in the WHOLE program.
    located = []
    for function in sorted(typed.functions, key=lambda item: item.signature.id):
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement, (index,)):
                if item.kind == "builtin" and item.callee in DERIVATIVE_BUILTINS:
                    located.append((item.callee, function.signature.id, path, item, parent, chain))

    nodes = tuple(
        (callee, owner, path, _span(item),
         "" if item.type is None else item.type.display(), _sha(item),
         "None" if parent is None else parent.kind,
         tuple("" if child.type is None else child.type.display() for child in item.children),
         tuple(_sha(child) for child in item.children))
        for callee, owner, path, item, parent, _chain in located)

    ancestors = tuple(
        (tuple(item.kind for item in chain), tuple(_span(item) for item in chain))
        for _callee, _owner, _path, _item, _parent, chain in located)

    return {
        "program_key": key,
        "raw_bytes": raw_bytes_actual,
        "raw_sha256": raw_sha256_actual,
        "normalized_bytes": normalized_bytes_actual,
        "normalized_sha256": normalized_sha256_actual,
        "defines": defines,
        "preprocessor_defines": preprocessor_defines_tuple,
        "functions_sha256": functions_sha256,
        "whole_sha256": whole_sha256,
        "interface_sha256": interface_sha256,
        "loop_proof": loop_proof_tuple,
        "resources": resources_tuple,
        "functions": functions_tuple,
        "nodes": nodes,
        "ancestors": ancestors,
        "structs_empty": typed.structs == (),
        "uniform_blocks_empty": typed.uniform_blocks == (),
        "body_status": typed.body_status,
    }


def main() -> int:
    out = {}
    for key in PROGRAM_KEYS:
        out[key] = process(key)
    out_path = pathlib.Path(__file__).resolve().parent / "admission-facts.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True, default=list) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    for key, v in out.items():
        print(key, "nodes:", len(v["nodes"]), "defines:", v["defines"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
