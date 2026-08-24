"""Reachability probe for every program whose full gate chain mechanically
clears (PASS in gate-chain-all-output.json). Same technique as
future-precompute/analyze_candidates.py / task32/probe_reachability.py:
build the call graph from `call`-node signature_ids starting at `main`, then
for each gate a program needed, find the actual AST site(s) that gate's
capability was exercised at and check whether the OWNING function is in the
reachable set.

READ-ONLY. No writes under noisemaker-for-cpp/noisemaker-for-cpu.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, "docs/port-engineering/roadmap2")

import gate_chain_engine as gce  # noqa: E402


def expression_nodes(value, path=()):
    yield path, value
    for index, child in enumerate(value.children):
        yield from expression_nodes(child, (*path, index))


def statement_nodes(value, path=()):
    for index, expression in enumerate(value.expressions):
        yield from expression_nodes(expression, (*path, f"e{index}"))
    for index, child in enumerate(value.children):
        yield from statement_nodes(child, (*path, f"s{index}"))


def function_nodes(function):
    for index, statement in enumerate(function.body):
        yield from statement_nodes(statement, (index,))


def reachable_signature_ids(typed):
    definitions = {f.signature.id: f for f in typed.functions if f.body}
    main = next((f for f in typed.functions if f.name == "main"), None)
    if main is None:
        return set(), definitions
    reachable = {main.signature.id}
    pending = [main.signature.id]
    while pending:
        sid = pending.pop()
        function = definitions.get(sid)
        if function is None:
            continue
        for _, value in function_nodes(function):
            if (value.kind == "call" and value.signature_id in definitions
                    and value.signature_id not in reachable):
                reachable.add(value.signature_id)
                pending.append(value.signature_id)
    return reachable, definitions


def span_text(value) -> str:
    s = value.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"


def analyze(key: str) -> dict:
    entry, raw, defines, typed = gce.load(key)
    reachable, definitions = reachable_signature_ids(typed)

    builtin_sites = []  # {callee, owner, owner_reachable, span}
    global_symbol_refs = {}  # symbol_id -> list of (owner_reachable, span)
    index_sites = []
    for function in typed.functions:
        owner_reachable = function.signature.id in reachable
        for path, value in function_nodes(function):
            if value.kind == "builtin":
                builtin_sites.append({
                    "callee": value.callee, "owner": function.name,
                    "owner_signature_id": function.signature.id,
                    "owner_reachable": owner_reachable,
                    "span": span_text(value),
                })
            elif value.kind == "id" and value.symbol_id is not None:
                global_symbol_refs.setdefault(value.symbol_id, []).append(
                    (owner_reachable, span_text(value)))
            elif value.kind == "index":
                index_sites.append({
                    "owner": function.name, "owner_reachable": owner_reachable,
                    "span": span_text(value),
                })

    declarations = []
    for d in typed.declarations:
        if d.symbol.storage in {"uniform", "output"}:
            continue
        refs = global_symbol_refs.get(d.symbol.id, [])
        any_reachable_ref = any(r for r, _ in refs)
        declarations.append({
            "name": d.symbol.name, "storage": d.symbol.storage,
            "type": d.type.display(), "symbol_id": d.symbol.id,
            "reference_count": len(refs),
            "any_reference_reachable": any_reachable_ref,
        })

    # main-level "is main itself reachable" is trivially true; report whether
    # main exists and whether every declared function is dead weight.
    dead_functions = [f.name for f in typed.functions
                      if f.body and f.signature.id not in reachable]

    return {
        "key": key,
        "main_present": any(f.name == "main" for f in typed.functions),
        "reachable_function_count": len(reachable),
        "total_function_count": sum(1 for f in typed.functions if f.body),
        "dead_functions": dead_functions,
        "builtin_sites": builtin_sites,
        "declarations": declarations,
        "index_site_count": len(index_sites),
        "index_sites_any_reachable": any(s["owner_reachable"] for s in index_sites),
    }


if __name__ == "__main__":
    data = json.loads(open("docs/port-engineering/roadmap2/gate-chain-all-output.json").read())
    rows = {r["key"]: r for r in data["rows"]}
    FREE = {"filter/invert:inv", "synth/solid:solid"}
    pass_keys = sorted(k for k, r in rows.items() if k not in FREE and r["final_status"] == "PASS")
    out = {}
    for key in pass_keys:
        out[key] = analyze(key)
    payload = {
        "schema": "noisemaker-for-cpp.roadmap2.reachability.v1",
        "corpus_revision": gce.REVISION,
        "keys": pass_keys,
        "rows": out,
    }
    dest = Path("docs/port-engineering/roadmap2/reachability-output.json")
    dest.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(dest)
