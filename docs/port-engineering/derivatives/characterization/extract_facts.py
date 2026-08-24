#!/usr/bin/env python3
"""Read-only fact extraction for the 17 derivative-blocked programs.

Imports the real, unmodified glslcpp frontend from
. (never writes into that repo) and
runs parse_program + analyze_program against each of the 17 programs at their
authorized (_defaults) preprocessor define map. Extracts:

  - corpus manifest entry (source path, sizes, hashes)
  - authorized define map
  - success/failure of parse+analyze (this IS the "would it land" check)
  - the exact resources tuple the gate must assert
  - declarations tuple (gate shape, matching validate_current_vocabulary_degauss)
  - function profile tuple (id, name, body-stmt-count, sha256(repr(function)))
  - every dFdx/dFdy/fwidth call site: builtin, arg type, enclosing function,
    span (typed.source-relative, i.e. TypedExpression.span, NOT raw corpus
    line numbers), and full stack of enclosing if-guards with each guard's
    referenced-identifier storages (to classify frame-constant vs
    per-pixel-varying)
  - any other diagnostic distinguishing "blocked solely by derivatives" from
    "blocked by X as well"

Output: derivative-program-facts.json (machine-readable) written into this
same directory. This script performs no writes into noisemaker-for-cpp and
runs no git command anywhere.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import traceback

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp import check_corpus  # noqa: E402
from tools.glslcpp.frontend import FrontendError, parse_program  # noqa: E402
from tools.glslcpp.frontend.diagnostics import SemanticError  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp import generate_typed_slice as gts  # noqa: E402
from tools.glslcpp.generate_typed_slice import GeneratorError, _defaults  # noqa: E402

CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS_ROOT = REPO / "tools/glslcpp/corpus" / CORPUS_REVISION

# The 17, in the order given in the task brief.
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
    "filter/posterize:posterize",
    "filter/spiral:spiral",
    "filter/stamp:stThreshold",
    "filter/step:step",
    "filter/stipple:stipple",
    "filter/tunnel:tunnel",
    "filter/warp:warp",
    "filter/waves:waves",
]

DERIVATIVE_BUILTINS = {"dFdx", "dFdy", "fwidth"}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _span_dict(span) -> dict:
    return {
        "start": span.start, "end": span.end,
        "start_line": span.start_line, "start_column": span.start_column,
        "end_line": span.end_line, "end_column": span.end_column,
    }


def _type_display(t) -> str:
    return t.display()


def _declarations_tuple(typed):
    return tuple(
        (declaration.symbol.id, declaration.symbol.name,
         declaration.type.display(), declaration.symbol.storage,
         declaration.symbol.writable, declaration.symbol.direction,
         None if declaration.initializer is None else (
             declaration.initializer.kind, declaration.initializer.literal))
        for declaration in typed.declarations)


def _function_profiles(typed):
    return tuple(
        (function.signature.id, function.signature.name, len(function.body),
         _sha256(repr(function).encode("utf-8")))
        for function in typed.functions)


def _resources_tuple(typed):
    r = typed.resources
    return (r.uniforms, r.samplers, r.outputs, r.uses_texture, r.uses_derivatives)


def _identifier_storages(expr) -> list[tuple[str, str]]:
    """All (name, storage) pairs for every identifier reachable in expr."""
    out: list[tuple[str, str]] = []

    def walk(e):
        if e.kind == "id" and e.symbol is not None:
            out.append((e.symbol.name, e.symbol.storage))
        if e.kind == "swizzle" and e.children and e.children[0].kind == "id" and e.children[0].symbol is not None:
            pass  # already captured via recursion below
        for c in e.children:
            walk(c)
    walk(expr)
    return out


def _condition_summary(expr) -> dict:
    storages = _identifier_storages(expr)
    kinds = {storage for _, storage in storages}
    frame_constant = kinds <= {"uniform", "const"}
    return {
        "text_kind": expr.kind,
        "identifiers": sorted(set(storages)),
        "storage_kinds": sorted(kinds),
        "frame_constant": frame_constant,
    }


def _find_derivative_sites(typed):
    """Walk every function body; report each dFdx/dFdy/fwidth call site with
    its enclosing function, arg type, span, and the stack of enclosing if
    guards (condition expr storage-classified for frame-constant safety)."""
    sites = []

    for function in typed.functions:
        fn_name = function.signature.name

        def walk_stmt(stmt, guard_stack, loop_depth):
            if stmt.kind == "if":
                condition = stmt.expressions[0]
                children = stmt.children
                walk_stmt(children[0], guard_stack + [{"branch": "then", "condition": condition}], loop_depth)
                if len(children) > 1:
                    walk_stmt(children[1], guard_stack + [{"branch": "else", "condition": condition}], loop_depth)
                return
            if stmt.kind in {"for", "while", "dowhile"}:
                for expr in stmt.expressions:
                    walk_expr(expr, guard_stack, loop_depth)
                for child in stmt.children:
                    walk_stmt(child, guard_stack, loop_depth + 1)
                return
            for expr in stmt.expressions:
                walk_expr(expr, guard_stack, loop_depth)
            for child in stmt.children:
                walk_stmt(child, guard_stack, loop_depth)

        def walk_expr(expr, guard_stack, loop_depth):
            if expr.kind == "builtin" and expr.callee in DERIVATIVE_BUILTINS:
                arg = expr.children[0] if expr.children else None
                sites.append({
                    "builtin": expr.callee,
                    "enclosing_function": fn_name,
                    "arg_type": arg.type.display() if arg is not None else None,
                    "return_type": expr.type.display(),
                    "span": _span_dict(expr.span),
                    "guard_stack": [
                        {"branch": g["branch"], **_condition_summary(g["condition"]),
                         "condition_span": _span_dict(g["condition"].span)}
                        for g in guard_stack
                    ],
                    "unconditional": len(guard_stack) == 0,
                    "enclosing_loop_depth": loop_depth,
                })
            for child in expr.children:
                walk_expr(child, guard_stack, loop_depth)

        for stmt in function.body:
            walk_stmt(stmt, [], 0)

    return sites


def run_validator_beyond_derivatives(typed, raw_source: str) -> dict:
    """Call the real validate_capabilities() (the generator's full-vocabulary
    proof), in-memory-patched to ALSO admit dFdx/dFdy/fwidth by name (a
    test-only bypass of the frozen-44 rule, never written to any file), so we
    can see whether GeneratorError still fires for an UNRELATED reason once
    derivatives are out of the way. This is read-only: it mutates the already
    -imported module's globals for the duration of one call in this process
    only; nothing is written to disk and no other process is affected.

    Returns {"clean": True} if validate_capabilities raises nothing once
    derivatives are admitted (i.e. the program is blocked SOLELY by
    derivatives), or {"clean": False, "error": "..."} with the exact
    GeneratorError text if something else also blocks it.
    """
    original_builtins = gts._BUILTINS
    original_capabilities = gts.APPROVED_CAPABILITIES
    patched_builtins = frozenset(original_builtins | {"dFdx", "dFdy", "fwidth"})
    patched_capabilities = tuple(original_capabilities) + ("dFdx", "dFdy", "fwidth")
    source_hash = _sha256(raw_source.encode("utf-8"))
    try:
        gts._BUILTINS = patched_builtins
        gts.APPROVED_CAPABILITIES = patched_capabilities
        try:
            gts.validate_capabilities(
                typed, patched_capabilities,
                source_hash=source_hash,
                compatibility_transform=None,
                custom_comparer_profile=None,
                numeric_literal_contract="glsl-f32",
                source_global_literal_int_profile=None,
                gather_sorted_round_profile=None,
                literal_vec3_lane_index_profile=None,
                smooth_edge_luma_weights_profile=None,
                perlin_scalar_uint_xor_profile=None,
                rotate_mat2_return_profile=None,
                focus_blur_borrowed_sampler_profile=None,
                extrude_bvec2_relational_reduction_profile=None,
                caustic_word_hash_profile=None,
                curl_vector_math_profile=None,
            )
            return {"clean": True, "error": None}
        except GeneratorError as error:
            return {"clean": False, "error": str(error)}
        except Exception as error:  # noqa: BLE001
            return {"clean": False, "error": f"UNEXPECTED {type(error).__name__}: {error}",
                    "traceback": traceback.format_exc()}
    finally:
        gts._BUILTINS = original_builtins
        gts.APPROVED_CAPABILITIES = original_capabilities


def _main_call_sites(typed) -> list[dict]:
    """Every user-function call expression reachable in main()'s own body
    (not transitively into helpers), with guard/loop context -- used to prove
    call-graph reachability and invocation multiplicity for any derivative
    site that lives inside a helper function rather than main() itself
    (only filter/halftone:halftone has this shape among the 17)."""
    main_fn = next((f for f in typed.functions if f.signature.name == "main"), None)
    if main_fn is None:
        return []
    sites: list[dict] = []

    def walk_stmt(stmt, guard_stack, loop_depth):
        if stmt.kind == "if":
            condition = stmt.expressions[0]
            children = stmt.children
            walk_stmt(children[0], guard_stack + [{"branch": "then", "condition": condition}], loop_depth)
            if len(children) > 1:
                walk_stmt(children[1], guard_stack + [{"branch": "else", "condition": condition}], loop_depth)
            return
        if stmt.kind in {"for", "while", "dowhile"}:
            for expr in stmt.expressions:
                walk_expr(expr, guard_stack, loop_depth)
            for child in stmt.children:
                walk_stmt(child, guard_stack, loop_depth + 1)
            return
        for expr in stmt.expressions:
            walk_expr(expr, guard_stack, loop_depth)
        for child in stmt.children:
            walk_stmt(child, guard_stack, loop_depth)

    def walk_expr(expr, guard_stack, loop_depth):
        if expr.kind == "call" and expr.callee:
            sites.append({
                "callee": expr.callee,
                "span": _span_dict(expr.span),
                "loop_depth": loop_depth,
                "guard_stack": [
                    {"branch": g["branch"], **_condition_summary(g["condition"])}
                    for g in guard_stack
                ],
                "unconditional": len(guard_stack) == 0,
            })
        for child in expr.children:
            walk_expr(child, guard_stack, loop_depth)

    for stmt in main_fn.body:
        walk_stmt(stmt, [], 0)
    return sites


def _manifest_entry(key: str) -> dict:
    manifest = check_corpus._load_json(CORPUS_ROOT / "manifest.json", "manifest")
    entries = {item["program_key"]: item for item in check_corpus._validate_manifest(manifest)}
    return entries[key]


def _metadata(repository: pathlib.Path) -> dict:
    root = check_corpus._corpus_root(repository)
    return check_corpus._load_json(root / "metadata.json", "metadata")


def process(key: str) -> dict:
    result: dict = {"program_key": key}
    try:
        entry = _manifest_entry(key)
    except Exception as error:  # noqa: BLE001
        result["manifest_error"] = repr(error)
        return result
    result["manifest_entry"] = {
        k: v for k, v in entry.items()
    }
    source_path = CORPUS_ROOT / entry["source"]
    raw_source = source_path.read_text(encoding="utf-8")
    result["raw_bytes_actual"] = len(raw_source.encode("utf-8"))
    result["raw_sha256_actual"] = _sha256(raw_source.encode("utf-8"))

    defines = _defaults(REPO, key)
    result["authorized_defines"] = defines
    metadata = _metadata(REPO)
    effect_id = key.split(":", 1)[0]
    result["metadata_effect"] = metadata.get("effects", {}).get(effect_id)

    try:
        parsed = parse_program(raw_source, key, defines)
    except FrontendError as error:
        result["stage"] = "parse"
        result["success"] = False
        result["error"] = str(error)
        return result
    except Exception as error:  # noqa: BLE001
        result["stage"] = "parse"
        result["success"] = False
        result["error"] = f"UNEXPECTED {type(error).__name__}: {error}"
        result["traceback"] = traceback.format_exc()
        return result

    result["normalized_bytes_actual"] = len(parsed["source"].encode("utf-8"))
    result["normalized_sha256_actual"] = _sha256(parsed["source"].encode("utf-8"))

    try:
        typed = analyze_program(parsed, key)
    except SemanticError as error:
        result["stage"] = "analyze"
        result["success"] = False
        result["error"] = str(error)
        result["diagnostics"] = [
            {"code": d.code, "message": d.message, "span": _span_dict(d.span)}
            for d in error.diagnostics
        ]
        return result
    except Exception as error:  # noqa: BLE001
        result["stage"] = "analyze"
        result["success"] = False
        result["error"] = f"UNEXPECTED {type(error).__name__}: {error}"
        result["traceback"] = traceback.format_exc()
        return result

    result["stage"] = "complete"
    result["success"] = True
    result["body_status"] = typed.body_status
    result["resources"] = {
        "uniforms": list(typed.resources.uniforms),
        "samplers": list(typed.resources.samplers),
        "outputs": list(typed.resources.outputs),
        "uses_texture": typed.resources.uses_texture,
        "uses_derivatives": typed.resources.uses_derivatives,
    }
    result["resources_tuple_gate_order"] = [
        list(typed.resources.uniforms), list(typed.resources.samplers),
        list(typed.resources.outputs), typed.resources.uses_texture,
        typed.resources.uses_derivatives,
    ]
    result["declarations"] = [
        {
            "id": d[0], "name": d[1], "type": d[2], "storage": d[3],
            "writable": d[4], "direction": d[5], "initializer": d[6],
        }
        for d in _declarations_tuple(typed)
    ]
    result["function_profiles"] = [
        {"id": f[0], "name": f[1], "body_stmt_count": f[2], "sha256": f[3]}
        for f in _function_profiles(typed)
    ]
    result["local_type_names"] = list(typed.local_type_names)
    result["structs"] = [s.name for s in typed.structs]
    result["uniform_blocks"] = [u.block_name for u in typed.uniform_blocks]
    result["interface_symbols"] = [
        {"name": s.name, "type": s.type.display(), "storage": s.storage}
        for s in typed.interface_symbols
    ]
    result["builtin_symbols"] = [
        {"name": s.name, "type": s.type.display(), "storage": s.storage}
        for s in typed.builtin_symbols
    ]
    proof = typed.counted_loop_proof
    result["counted_loop_proof"] = None if proof is None else {
        "loop_count": proof.loop_count,
        "unproved_loop_count": proof.unproved_loop_count,
        "max_effective_depth": proof.max_effective_depth,
        "max_lexical_product": proof.max_lexical_product,
        "entrypoint_charge": proof.entrypoint_charge,
        "call_graph_acyclic": proof.call_graph_acyclic,
    }
    result["preprocessor_defines"] = [
        {"name": p.name, "kind": p.kind, "canonical_value": p.canonical_value}
        for p in typed.preprocessor_defines
    ]
    result["foreign_proofs_present"] = {
        "fixed_nine_table_proof": typed.fixed_nine_table_proof is not None,
        "fixed_grid_counter_store_proof": typed.fixed_grid_counter_store_proof is not None,
        "fixed_array_in_parameter_proof": typed.fixed_array_in_parameter_proof is not None,
        "fixed_affine_centers13_proof": typed.fixed_affine_centers13_proof is not None,
    }
    result["derivative_call_sites"] = _find_derivative_sites(typed)
    result["derivative_call_count"] = len(result["derivative_call_sites"])
    result["main_call_sites"] = _main_call_sites(typed)
    result["validator_beyond_derivatives"] = run_validator_beyond_derivatives(typed, raw_source)

    # Exact whole-program / interface / functions-tuple hashes, computed the
    # same way validate_current_vocabulary_degauss/_crt do (see
    # generate_typed_slice.py:400-421). These are stable NOW: the frontend
    # (parse_program/analyze_program) needs no change to admit these 17 (see
    # body_semantic.py's existing "derivative" builtin family) -- only the
    # generator's frozen-vocabulary walk (validate_capabilities) needs the
    # node-identity admission described in the architecture doc. So these
    # hashes are exactly what a future validate_current_vocabulary_<name>
    # gate would assert.
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
    result["gate_hashes"] = {
        "functions_sha256": functions_sha256,
        "whole_sha256": whole_sha256,
        "interface_sha256": interface_sha256,
    }
    return result


def main() -> int:
    facts = {"corpus_revision": CORPUS_REVISION, "programs": {}}
    for key in PROGRAM_KEYS:
        facts["programs"][key] = process(key)
    out_path = pathlib.Path(__file__).resolve().parent / "derivative-program-facts.json"
    out_path.write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    success = sum(1 for v in facts["programs"].values() if v.get("success"))
    print(f"success: {success}/{len(PROGRAM_KEYS)}")
    for key, v in facts["programs"].items():
        if not v.get("success"):
            print(f"  FAIL {key}: stage={v.get('stage')} error={v.get('error')}")
    clean = sum(1 for v in facts["programs"].values()
                if v.get("success") and v.get("validator_beyond_derivatives", {}).get("clean"))
    print(f"validator-clean-beyond-derivatives: {clean}/{len(PROGRAM_KEYS)}")
    for key, v in facts["programs"].items():
        vbd = v.get("validator_beyond_derivatives")
        if v.get("success") and vbd and not vbd.get("clean"):
            print(f"  OTHER BLOCKER {key}: {vbd.get('error')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
