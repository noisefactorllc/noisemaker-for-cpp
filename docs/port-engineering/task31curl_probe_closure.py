#!/usr/bin/env python3
"""Task 31 Curl: enumerate every tanh and mod site in the whole program,
classify already-admitted vs novel overloads, compute per-node identity
(span, type, sha256, parent kind, child types/hashes, owning function,
ancestry), and determine reachability from main via the call graph.
Read-only.
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

ADMITTED_MOD_OVERLOADS = {("float", "float"), ("vec2", "float"), ("vec2", "vec2")}


def sha(value) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def span(value):
    s = value.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"


def walk_expression(value, parent=None, path=()):
    yield value, parent, path
    for i, child in enumerate(value.children):
        yield from walk_expression(child, value, (*path, i))


def walk_statement(value, path=(), ancestors=()):
    chain = (*ancestors, value)
    for i, expr in enumerate(value.expressions):
        for item, parent, epath in walk_expression(expr, None, (*path, f"e{i}")):
            yield item, parent, epath, chain
    for i, child in enumerate(value.children):
        yield from walk_statement(child, (*path, f"s{i}"), chain)


def build_call_graph(program):
    """function name/id -> set of callee function ids, via `call` nodes."""
    graph = {f.id: set() for f in program.functions}
    by_name = {}
    for f in program.functions:
        by_name.setdefault(f.name, []).append(f)
    for f in program.functions:
        for stmt in f.body:
            for item, parent, path, chain in walk_statement(stmt, (0,)):
                if item.kind == "call":
                    sig_id = getattr(item, "signature_id", None)
                    callee_fn = None
                    if sig_id is not None:
                        callee_fn = next((g for g in program.functions if g.id == sig_id), None)
                    if callee_fn is None:
                        # fallback: match by callee name + arg count if signature_id absent
                        name = getattr(item, "callee", None)
                        candidates = by_name.get(name, [])
                        if len(candidates) == 1:
                            callee_fn = candidates[0]
                    if callee_fn is not None:
                        graph[f.id].add(callee_fn.id)
    return graph


def reachable_from(graph, start_id):
    seen = set()
    stack = [start_id]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        for nxt in graph.get(cur, ()):
            if nxt not in seen:
                stack.append(nxt)
    return seen


def main():
    raw = SRC_PATH.read_text()
    parsed = parse_program(raw, KEY, DEFINES)
    program = analyze_program(parsed, KEY)

    fn_by_id = {f.id: f for f in program.functions}
    graph = build_call_graph(program)
    print("call graph (function id -> callee ids):")
    for fid, callees in sorted(graph.items()):
        print(f"  {fid} {fn_by_id[fid].name}: {sorted(callees)} "
              f"-> {sorted(fn_by_id[c].name for c in callees)}")

    main_fn = next(f for f in program.functions if f.name == "main")
    reachable = reachable_from(graph, main_fn.id)
    print("\nreachable function ids from main:", sorted(reachable))
    print("reachable function names from main:",
          sorted(fn_by_id[i].name for i in reachable))
    print("unreachable functions:",
          sorted(f.name for f in program.functions if f.id not in reachable))

    print("\n--- tanh and mod sites (whole program) ---")
    rows = []
    for f in program.functions:
        for index, stmt in enumerate(f.body):
            for item, parent, path, chain in walk_statement(stmt, (index,)):
                if item.kind == "builtin" and item.callee in ("tanh", "mod"):
                    child_types = tuple(
                        "" if c.type is None else c.type.display() for c in item.children)
                    child_shas = tuple(sha(c) for c in item.children)
                    admitted = None
                    if item.callee == "mod":
                        admitted = child_types in ADMITTED_MOD_OVERLOADS
                    rows.append(dict(
                        callee=item.callee,
                        owning_function=f.name,
                        owning_function_id=f.id,
                        owning_function_reachable=(f.id in reachable),
                        path=path,
                        span=span(item),
                        result_type=item.type.display() if item.type else None,
                        node_sha=sha(item),
                        parent_kind=None if parent is None else parent.kind,
                        parent_span=None if parent is None else span(parent),
                        child_types=child_types,
                        child_shas=child_shas,
                        already_admitted_overload=admitted,
                        ancestor_kinds=tuple(s.kind for s in chain),
                        ancestor_spans=tuple(span(s) for s in chain),
                    ))
    for row in rows:
        print()
        for k, v in row.items():
            print(f"  {k}: {v}")

    print(f"\ntotal tanh+mod sites: {len(rows)}")
    tanh_rows = [r for r in rows if r["callee"] == "tanh"]
    mod_rows = [r for r in rows if r["callee"] == "mod"]
    novel_mod_rows = [r for r in mod_rows if not r["already_admitted_overload"]]
    print(f"tanh sites: {len(tanh_rows)}")
    print(f"mod sites total: {len(mod_rows)}")
    print(f"mod sites already admitted by existing overload set: "
          f"{len(mod_rows) - len(novel_mod_rows)}")
    print(f"mod sites NOT already admitted (novel overload, e.g. vec3/vec4-by-scalar): "
          f"{len(novel_mod_rows)}")
    print(f"nodes requiring new authentication (tanh + novel mod): "
          f"{len(tanh_rows) + len(novel_mod_rows)}")

    print("\nreachability per site:")
    for r in rows:
        print(f"  {r['callee']} at {r['span']} in {r['owning_function']} "
              f"(id {r['owning_function_id']}): reachable={r['owning_function_reachable']} "
              f"already_admitted={r['already_admitted_overload']}")


if __name__ == "__main__":
    main()
