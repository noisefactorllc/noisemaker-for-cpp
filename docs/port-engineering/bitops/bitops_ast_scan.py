"""Read-only AST-level bitwise/shift frontier scan for the unported corpus.

For every corpus program key NOT in the current 131-typed slice, this:
  1. Derives default preprocessor defines from metadata (same helper the
     project's own check_semantics module uses).
  2. Parses + semantically analyzes the program via the live frontend
     (parse_program / analyze_program) -- this performs real #if/#ifdef
     reachability at the *preprocessor* level (dead #if branches are already
     excluded from the returned AST).
  3. Walks the resulting TypedProgram AST for bitwise/shift operator sites:
     binary &, |, ^, <<, >>; compound assign &=, |=, ^=, <<=, >>=; unary ~.
  4. Computes call-graph reachability from every function actually invoked
     by fragment-shader execution (main, if present, else every function
     that is not itself called by anything -- but this corpus's shaders all
     define main) so a bitwise site sitting in a function that is defined
     but never called under these defines is correctly flagged unreachable
     (the Task-27 Perlin trap).
  5. Classifies each site's exact type shape against the operators/types the
     *live* validator (tools/glslcpp/generate_typed_slice.py) currently
     admits, so pcg-style `uvecN ^= uvecN` / `uvecN >> uint` hash reuse does
     NOT get miscounted as a blocker.
  6. Also runs the real validator (validate_capabilities) to capture its
     first-raised blocker message, for cross-reference.

Writes docs/port-engineering/bitops/bitops_ast_scan.json

Strictly read-only against ..
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp import check_corpus, check_semantics  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

BIT_BINARY = {"&", "|", "^", "<<", ">>"}
BIT_ASSIGN = {"&=", "|=", "^=", "<<=", ">>="}
BIT_UNARY = {"~"}

# Shapes the *current* validator already admits generically (see
# generate_typed_slice.py around the "uint-vector-bitwise" capability):
#   uvecN ^ uvecN        (same uvec type both sides)
#   uvecN >> uint         (vector left, *scalar* uint shift count)
#   uvecN ^= uvecN        (compound assign, same uvec type)
VEC_UINT_TYPES = {"uvec2", "uvec3", "uvec4"}


def admitted_shape(op: str, left_type: str, right_type: str) -> bool:
    if op == "^":
        return left_type in VEC_UINT_TYPES and right_type == left_type
    if op == ">>":
        return left_type in VEC_UINT_TYPES and right_type == "uint"
    if op == "^=":
        return left_type in VEC_UINT_TYPES and right_type == left_type
    return False  # &, |, <<, ~, &=, |=, <<=, >>= : never admitted today


def walk_expr(expr):
    yield expr
    for child in expr.children:
        yield from walk_expr(child)


def walk_stmt(stmt):
    for e in stmt.expressions:
        yield from walk_expr(e)
    for c in stmt.children:
        yield from walk_stmt(c)


def call_ids_in(expr):
    for node in walk_expr(expr):
        if node.kind == "call" and node.signature_id is not None:
            yield node.signature_id


def function_call_graph(program):
    """Map function.id -> set of signature_ids it calls (direct)."""
    calls = {f.id: set() for f in program.functions}
    for f in program.functions:
        for stmt in f.body:
            for e in stmt.expressions:
                calls[f.id].update(call_ids_in(e))
            # also walk nested statement expressions (loops/if bodies)
            stack = list(stmt.children)
            while stack:
                s = stack.pop()
                for e in s.expressions:
                    calls[f.id].update(call_ids_in(e))
                stack.extend(s.children)
    return calls


def reachable_function_ids(program):
    calls = function_call_graph(program)
    main = next((f for f in program.functions if f.name == "main"), None)
    if main is None:
        # No main in this AST shape (shouldn't happen for a render program);
        # treat everything as reachable rather than silently hiding sites.
        return set(calls.keys()), False
    seen = set()
    stack = [main.id]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(calls.get(cur, ()))
    return seen, True


def bitwise_sites(program, reachable_ids):
    sites = []
    for f in program.functions:
        is_reachable = f.id in reachable_ids
        for stmt in f.body:
            stack_stmts = [stmt]
            while stack_stmts:
                s = stack_stmts.pop()
                for e in s.expressions:
                    for node in walk_expr(e):
                        rec = classify_node(node, f, is_reachable)
                        if rec is not None:
                            sites.append(rec)
                stack_stmts.extend(s.children)
    return sites


def classify_node(node, func, is_reachable):
    if node.kind == "binary" and node.operator in BIT_BINARY:
        left, right = node.children
        lt = left.type.display() if left.type else "?"
        rt = right.type.display() if right.type else "?"
        return {
            "function": func.name, "function_id": func.id,
            "reachable": is_reachable, "kind": "binary",
            "operator": node.operator, "left_type": lt, "right_type": rt,
            "result_type": node.type.display() if node.type else "?",
            "span": f"{node.span.start_line}:{node.span.start_column}",
            "admitted_today": admitted_shape(node.operator, lt, rt),
        }
    if node.kind == "assign" and node.operator in BIT_ASSIGN:
        left, right = node.children
        lt = left.type.display() if left.type else "?"
        rt = right.type.display() if right.type else "?"
        return {
            "function": func.name, "function_id": func.id,
            "reachable": is_reachable, "kind": "assign",
            "operator": node.operator, "left_type": lt, "right_type": rt,
            "result_type": node.type.display() if node.type else "?",
            "span": f"{node.span.start_line}:{node.span.start_column}",
            "admitted_today": admitted_shape(node.operator, lt, rt),
        }
    if node.kind == "unary" and node.operator in BIT_UNARY:
        operand = node.children[0]
        ot = operand.type.display() if operand.type else "?"
        return {
            "function": func.name, "function_id": func.id,
            "reachable": is_reachable, "kind": "unary",
            "operator": node.operator, "left_type": ot, "right_type": None,
            "result_type": node.type.display() if node.type else "?",
            "span": f"{node.span.start_line}:{node.span.start_column}",
            "admitted_today": False,
        }
    return None


def main():
    root = check_corpus._corpus_root(REPO)
    manifest = check_corpus._load_json(root / "manifest.json", "manifest")
    entries = {item["program_key"]: item
               for item in check_corpus._validate_manifest(manifest)}
    metadata = check_corpus._load_json(root / "metadata.json", "metadata")

    slice_spec = gen.load_slice(REPO)
    typed_keys = {item["program_key"] for item in slice_spec["programs"]}

    remaining = sorted(set(entries) - typed_keys)
    results = []
    for key in remaining:
        entry = entries[key]
        source = (root / entry["source"]).read_text(encoding="utf-8")
        defines = check_semantics._metadata_defaults(metadata, key)
        record = {"key": key, "source": entry["source"], "defines": defines}
        try:
            parsed = parse_program(source, key, defines)
            typed = analyze_program(parsed, key)
        except Exception as error:  # noqa: BLE001
            record["stage"] = "parse/analyze"
            record["error"] = f"{type(error).__name__}: {error}"
            results.append(record)
            continue

        reachable_ids, had_main = reachable_function_ids(typed)
        sites = bitwise_sites(typed, reachable_ids)
        record["had_main"] = had_main
        record["bitwise_sites"] = sites
        record["reachable_bitwise_sites"] = [s for s in sites if s["reachable"]]
        record["unreachable_bitwise_sites"] = [s for s in sites if not s["reachable"]]
        record["reachable_unadmitted_sites"] = [
            s for s in sites if s["reachable"] and not s["admitted_today"]]

        try:
            gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES)
            record["validator_first_error"] = "PASS"
        except gen.GeneratorError as error:
            record["validator_first_error"] = str(error)
        except Exception as error:  # noqa: BLE001
            record["validator_first_error"] = f"{type(error).__name__}: {error}"

        results.append(record)

    out = pathlib.Path("docs/port-engineering/bitops/bitops_ast_scan.json")
    out.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print("scanned:", len(results))
    with_bitwise = [r for r in results if r.get("bitwise_sites")]
    print("programs with any bitwise/shift AST node:", len(with_bitwise))
    with_reachable_unadmitted = [r for r in results if r.get("reachable_unadmitted_sites")]
    print("programs with reachable NOT-yet-admitted bitwise:", len(with_reachable_unadmitted))
    with_unreachable_only = [
        r for r in results
        if r.get("bitwise_sites") and not r.get("reachable_bitwise_sites")]
    print("programs where ALL bitwise sites are unreachable (dead):", len(with_unreachable_only))


if __name__ == "__main__":
    raise SystemExit(main())
