"""Task 32, task 3 (reachability half): for each of the four round-family
candidates, build the real call graph from `main()` (following `call` nodes'
signature_id, exactly as future-precompute/analyze_candidates.py and
task-31-target-reselection.md's method do) and determine whether the
function that contains each `round(...)` builtin call site is reachable.

A closure that is dead code at the program's authorized define map cannot be
validated by full-render parity (this is exactly what disqualified Caustic in
Task 31 -- see docs/port-engineering/task-31-target-reselection.md).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = (
    "filter/fxaa:fxaa",
    "filter/grain:grain",
    "filter/normalMap:normalMap",
    "filter/snow:snow",
)


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, raw, defines, typed


def span(value) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


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


def main() -> int:
    rows = []
    for key in KEYS:
        entry, raw, defines, program = load(key)

        definitions = {f.signature.id: f for f in program.functions if f.body}
        try:
            main_fn = next(f for f in program.functions if f.name == "main")
        except StopIteration:
            rows.append({"key": key, "error": "no main() function found"})
            continue

        reachable = {main_fn.signature.id}
        pending = [main_fn.signature.id]
        while pending:
            fid = pending.pop()
            function = definitions[fid]
            for _, value in function_nodes(function):
                if (value.kind == "call" and value.signature_id in definitions
                        and value.signature_id not in reachable):
                    reachable.add(value.signature_id)
                    pending.append(value.signature_id)

        all_functions = [{
            "id": f.signature.id, "name": f.name,
            "reachable_from_main": f.signature.id in reachable,
        } for f in program.functions if f.body]

        round_sites = []
        for function in program.functions:
            if not function.body:
                continue
            for path, value in function_nodes(function):
                if value.kind == "builtin" and value.callee == "round":
                    round_sites.append({
                        "owner_function": function.name,
                        "owner_signature_id": function.signature.id,
                        "owner_reachable_from_main": function.signature.id in reachable,
                        "path": list(path),
                        "span": span(value),
                        "argument_types": [c.type.display() for c in value.children],
                        "result_type": value.type.display(),
                    })

        # Also record, for each round-owning function, which OTHER functions
        # (if any) call it, and whether *those* callers are themselves
        # reachable -- this traces the full path back to main(), not just a
        # single hop, matching the rigor of the task-31 method.
        callers_of = {}
        for function in program.functions:
            if not function.body:
                continue
            for _, value in function_nodes(function):
                if value.kind == "call" and value.signature_id in definitions:
                    callers_of.setdefault(value.signature_id, []).append({
                        "caller_function": function.name,
                        "caller_signature_id": function.signature.id,
                        "caller_reachable_from_main": function.signature.id in reachable,
                    })

        round_owner_ids = sorted({site["owner_signature_id"] for site in round_sites})
        call_paths = {
            str(fid): callers_of.get(fid, []) for fid in round_owner_ids
        }

        rows.append({
            "key": key,
            "defines": defines,
            "main_signature_id": main_fn.signature.id,
            "total_functions_with_body": len(all_functions),
            "reachable_function_ids": sorted(reachable),
            "all_functions": all_functions,
            "round_call_sites": round_sites,
            "callers_of_round_owning_functions": call_paths,
            "any_round_site_reachable": any(s["owner_reachable_from_main"] for s in round_sites),
            "all_round_sites_reachable": all(s["owner_reachable_from_main"] for s in round_sites) if round_sites else None,
        })

    payload = {
        "schema": "noisemaker-for-cpp.task32.reachability.v1",
        "corpus_revision": REVISION,
        "method": "call graph from main(), following `call` node signature_id, one BFS pass; round() sites located as `builtin` nodes with callee=='round'; owner function membership in the reachable set determines liveness, matching task-31-target-reselection.md's method.",
        "rows": rows,
    }
    out = Path(__file__).with_name("reachability-output.json")
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
