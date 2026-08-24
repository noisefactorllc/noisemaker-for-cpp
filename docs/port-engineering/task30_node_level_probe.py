"""Find mutations that reach the Extrude profile's NODE-LEVEL logic.

The 47 existing single-axis mutations are all absorbed by the coarse
whole-program/function/interface hash gate, so the module's node-walk,
pairing, ancestry and bvec2-escape checks are never exercised. This probe
recomputes the frozen coarse hashes for each mutated tree so the coarse gate
passes, letting the node-level logic actually run, and reports which specific
check fires.
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp.frontend import extrude_bvec2_relational_reduction_profile as P  # noqa: E402

REV = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REV
ENTRY = {r["program_key"]: r for r in
         json.loads((CORPUS / "manifest.json").read_text())["programs"]}[P.EXTRUDE_KEY]
RAW = (CORPUS / ENTRY["source"]).read_text()
SHA = ENTRY["raw_sha256"]


def build():
    return analyze_program(
        parse_program(RAW, P.EXTRUDE_KEY, gen._defaults(ROOT, P.EXTRUDE_KEY)),
        P.EXTRUDE_KEY)


@contextlib.contextmanager
def coarse_gate_recomputed(program):
    """Re-freeze the coarse hashes to match `program` so node logic runs."""
    names = ("_FUNCTIONS_SHA256", "_WHOLE_SHA256", "_INTERFACE_SHA256",
             "_NORMALIZED_SHA256", "_NORMALIZED_BYTES", "_LOOP_PROOF")
    saved = {n: getattr(P, n) for n in names}
    try:
        P._FUNCTIONS_SHA256 = P._sha(program.functions)
        P._WHOLE_SHA256 = P._whole(program)
        P._INTERFACE_SHA256 = P._interface(program)
        normalized = program.source.encode("utf-8")
        P._NORMALIZED_SHA256 = hashlib.sha256(normalized).hexdigest()
        P._NORMALIZED_BYTES = len(normalized)
        proof = program.counted_loop_proof
        if proof is not None:
            P._LOOP_PROOF = (proof.loop_count, proof.unproved_loop_count,
                             proof.max_effective_depth, proof.max_lexical_product,
                             proof.entrypoint_charge, proof.call_graph_acyclic)
        yield
    finally:
        for n, v in saved.items():
            setattr(P, n, v)


def walk_expr(v):
    yield v
    for c in v.children:
        yield from walk_expr(c)


def walk_stmt(s):
    yield s
    for c in s.children:
        yield from walk_stmt(c)


def nodes(program, callee):
    main = next(f for f in program.functions if f.id == 36)
    return [n for st in main.body for s in walk_stmt(st) for e in s.expressions
            for n in walk_expr(e) if n.kind == "builtin" and n.callee == callee]


def attempt(label, mutate):
    program = build()
    try:
        mutate(program)
    except Exception as error:  # noqa: BLE001
        print(f"  {label:38s} MUTATION FAILED: {str(error)[:50]}")
        return
    baseline = build()
    if P._sha(program.functions) == P._sha(baseline.functions):
        print(f"  {label:38s} NO-OP (tree unchanged) -- vacuous")
        return
    with coarse_gate_recomputed(program):
        try:
            P.authenticate_extrude_bvec2_relational_reduction(program, SHA, P.PROFILE)
            print(f"  {label:38s} !! ACCEPTED -- node logic did not catch it")
        except ValueError as error:
            message = str(error).split(": ", 1)[1] if ": " in str(error) else str(error)
            coarse = "source, define, function, whole-program, or interface mismatch"
            tag = "COARSE" if message == coarse else "NODE  "
            print(f"  {label:38s} {tag} {message[:60]}")


def main() -> int:
    print("Mutations with the coarse gate recomputed (so node logic runs):\n")

    def retarget_all_to_any(p):
        object.__setattr__(nodes(p, "all")[1], "callee", "any")

    def retarget_le_to_lt(p):
        object.__setattr__(nodes(p, "lessThanEqual")[0], "callee", "lessThan")

    def drop_reduction_child(p):
        node = nodes(p, "all")[0]
        object.__setattr__(node, "children", ())

    def swap_reduction_child(p):
        a0, a1 = nodes(p, "all")
        object.__setattr__(a0, "children", (a1.children[0],))

    def extra_relational_arg(p):
        node = nodes(p, "lessThanEqual")[0]
        object.__setattr__(node, "children",
                           (*node.children, node.children[0]))

    def widen_result_type(p):
        node = nodes(p, "lessThanEqual")[0]
        object.__setattr__(node, "type", nodes(p, "all")[0].type)

    for label, fn in (
            ("all -> any", retarget_all_to_any),
            ("lessThanEqual -> lessThan", retarget_le_to_lt),
            ("reduction loses its child", drop_reduction_child),
            ("reduction consumes wrong relational", swap_reduction_child),
            ("relational gains a third argument", extra_relational_arg),
            ("relational result retyped bool", widen_result_type),
    ):
        attempt(label, fn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
