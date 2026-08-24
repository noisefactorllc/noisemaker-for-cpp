"""Read-only reachability probe for the 16 (+6 adjacent) loop-proof-family
programs. Mirrors roadmap2/reachability_probe.py's technique (build the call
graph from `call`-node signature_ids starting at main(), BFS/DFS forward)
but applied to programs that are still BLOCKED (never reached PASS in
gate-chain-all-output.json, so they're absent from roadmap2's own
reachability-output.json, which only covers the 35 PASS rows).

For each program, reports whether the FUNCTION containing each unproved loop
is reachable from main() under the corpus's default (authorized) define map.
READ-ONLY: only imports frontend modules and parses corpus text already
checked into noisemaker-for-cpp. Writes nothing back to that repo.
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
from tools.glslcpp.frontend.loop_proof import attach_counted_loop_proofs  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = [
    "classicNoisedeck/effects:effects",
    "classicNoisedeck/fractal:fractal",
    "classicNoisedeck/noise:noise",
    "filter/blur:blurH",
    "filter/blur:blurV",
    "filter/dither:dither",
    "filter/lightLeak:lightLeak",
    "filter/median:median",
    "filter/normalize:statsFinal",
    "filter/oilPaint:oilFlatten",
    "filter/parallax:parallax",
    "filter/reindex:nmReindexReduce",
    "filter/reindex:nmReindexStats",
    "filter/smooth:smoothBlend",
    "filter/tetraColorArray:tetraColorArray",
    "filter/zoomBlur:zoomBlur",
    "synth/mandelbrot:mandelbrot",
    "synth/noise:noise",
    "synth/testPattern:testPattern",
    "synth/gabor:gabor",
    "synth/newton:newton",
    "synth/julia:julia",
]


def expression_nodes(value):
    yield value
    for child in value.children:
        yield from expression_nodes(child)


def statement_nodes(value):
    for expression in value.expressions:
        yield from expression_nodes(expression)
    for child in value.children:
        yield from statement_nodes(child)


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
        for statement in function.body:
            for value in statement_nodes(statement):
                if (value.kind == "call" and value.signature_id in definitions
                        and value.signature_id not in reachable):
                    reachable.add(value.signature_id)
                    pending.append(value.signature_id)
    return reachable, definitions


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, typed


def classify_key(key: str) -> dict:
    entry, typed = load(key)
    reachable, definitions = reachable_signature_ids(typed)
    annotated_functions = attach_counted_loop_proofs(typed.functions, key)
    by_name = {f.name: f for f in annotated_functions}

    def walk(statement, depth):
        is_loop = statement.kind in ("for", "while", "dowhile")
        if is_loop:
            yield statement, depth + 1
        for child in statement.children:
            yield from walk(child, depth + 1 if is_loop else depth)

    findings = []
    for function in annotated_functions:
        if not function.body:
            continue
        sid = function.signature.id
        for statement in function.body:
            for loop_stmt, depth in walk(statement, 0):
                if loop_stmt.loop_proof is not None:
                    continue  # only report unproved loops
                findings.append({
                    "function": function.name,
                    "signature_id": sid,
                    "span": f"{loop_stmt.span.start_line}:{loop_stmt.span.start_column}",
                    "function_reachable_from_main": sid in reachable,
                })
    return {
        "key": key,
        "main_present": any(f.name == "main" for f in typed.functions),
        "total_reachable_functions": len(reachable),
        "total_defined_functions": len(definitions),
        "unproved_loop_reachability": findings,
    }


def main() -> int:
    rows = [classify_key(key) for key in KEYS]
    print(json.dumps({"corpus_revision": REVISION, "rows": rows}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
