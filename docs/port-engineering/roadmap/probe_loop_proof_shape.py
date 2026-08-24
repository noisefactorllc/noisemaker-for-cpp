"""Third pass on the loop-proof family: for every UNPROVED for-loop (the
dominant sub-reason found by probe_loop_proof.py, 18/22 keys), determine
exactly which structural precondition of the canonical-shape matcher in
tools/glslcpp/frontend/loop_proof.py:_annotate_statement fails first, by
replicating that function's exact sequence of checks (read-only mirror, not
a monkeypatch -- there's no flag to flip here, the shape matcher is the
capability). This tells us whether the 18 "unproved" loops are unprovable for
one common structural reason (e.g. "bound is a uniform read, not a literal")
or many different ones.

Also reports, for while/dowhile loops (median) and program-level bodies with
`return` inside the loop, the same classification.
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
from tools.glslcpp.frontend.loop_proof import (  # noqa: E402
    _integer_literal, _contains_return, attach_counted_loop_proofs)

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
]


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, typed


def classify_for_loop(value) -> str:
    """Mirror _annotate_statement's canonical-shape checks, in order, and
    report the first one that fails. `value` is a TypedStatement with
    kind=='for'."""
    if len(value.children) != 2 or len(value.expressions) != 2:
        return "malformed for-node shape (not exactly init+body children, cond+update expressions)"
    initializer, body = value.children
    if (initializer.kind != "decl" or len(initializer.expressions) != 1
            or initializer.expressions[0].kind != "declaration"):
        return "initializer is not a single int declaration"
    declaration = initializer.expressions[0]
    if declaration.type.display() != "int":
        return f"induction variable is not int (is {declaration.type.display()})"
    if declaration.symbol is None or declaration.symbol.storage != "local":
        return "induction variable is not a plain local"
    if len(declaration.children) != 1:
        return "induction variable has no single initializer expression"
    start = _integer_literal(declaration.children[0])
    condition, update = value.expressions
    if start is None:
        return "start value is not an integer literal"
    if condition.kind != "binary" or condition.operator not in {"<", "<="}:
        op = condition.operator if condition.kind == "binary" else condition.kind
        return f"condition operator is not < or <= (is {op!r})"
    if len(condition.children) != 2:
        return "condition is not a simple binary comparison"
    induction, bound_expression = condition.children
    symbol_id = declaration.symbol_id
    if (symbol_id is None or induction.kind != "id" or induction.symbol_id != symbol_id):
        return "condition left-hand side is not the induction variable"
    if (update.kind not in {"post", "unary"} or update.operator != "++"
            or len(update.children) != 1 or update.children[0].kind != "id"
            or update.children[0].symbol_id != symbol_id):
        return f"update is not induction++ (kind={update.kind!r} op={update.operator!r})"
    bound = _integer_literal(bound_expression)
    if bound is None:
        if bound_expression.kind == "id":
            sym = bound_expression.symbol
            storage = sym.storage if sym is not None else "?"
            return f"loop bound is not a literal or already-proved local const -- it's an id read of storage={storage!r} ({bound_expression.callee or (sym.name if sym else '?')})"
        return f"loop bound is not a literal or an id (kind={bound_expression.kind!r})"
    if _contains_return(body):
        return "loop body contains a return statement"
    return "SHAPE OK (would be proved) -- unproved must come from elsewhere (bug in this mirror?)"


def walk(function):
    def rec(statement):
        yield statement
        for child in statement.children:
            yield from rec(child)
    for statement in function.body:
        yield from rec(statement)


def classify_key(key: str) -> dict:
    entry, typed = load(key)
    # Attach real proofs first (same call the validator makes) so we only
    # classify loops that are ACTUALLY left unproved after attachment --
    # not every for-loop in the file, most of which are already fine.
    annotated_functions = attach_counted_loop_proofs(typed.functions, key)
    findings = []
    for function in annotated_functions:
        if not function.body:
            continue
        for statement in walk(function):
            if statement.kind == "for" and statement.loop_proof is None:
                findings.append({
                    "function": function.name,
                    "span": f"{statement.span.start_line}:{statement.span.start_column}",
                    "kind": "for",
                    "reason": classify_for_loop(statement),
                })
            elif statement.kind in {"while", "dowhile"}:
                findings.append({
                    "function": function.name,
                    "span": f"{statement.span.start_line}:{statement.span.start_column}",
                    "kind": statement.kind,
                    "reason": f"{statement.kind} loop -- mechanism only ever proves 'for' loops",
                })
    return {"key": key, "loops": findings}


def main() -> int:
    rows = [classify_key(key) for key in KEYS]
    tag_counts: dict[str, int] = {}
    for row in rows:
        for loop in row["loops"]:
            # bucket by a short prefix so "loop bound is not a literal... uniform"
            # groups together regardless of the exact uniform name
            reason = loop["reason"]
            if reason.startswith("loop bound is not a literal or an id read of storage='uniform'"):
                bucket = "loop bound reads a uniform (runtime-variable trip count)"
            elif "storage='uniform'" in reason:
                bucket = "loop bound reads a uniform (runtime-variable trip count)"
            elif "mechanism only ever proves 'for' loops" in reason:
                bucket = "while/dowhile (never provable)"
            elif reason.startswith("loop bound is not a literal or an id read of storage="):
                bucket = reason.split(" -- ")[0][:55]
            else:
                bucket = reason
            tag_counts[bucket] = tag_counts.get(bucket, 0) + 1
    out = {
        "family": "unsupported counted-for program proof -- for-loop shape mismatch detail",
        "rows": rows,
        "reason_bucket_distribution": tag_counts,
    }
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
