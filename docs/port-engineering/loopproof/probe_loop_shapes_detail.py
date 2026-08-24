"""Read-only detailed loop-shape probe for the loop-proof family.

Runs the REAL frontend (parser + semantic analyzer + attach_counted_loop_proofs
from tools/glslcpp/frontend/loop_proof.py) against each program's corpus
source, exactly as the generator does, then walks every for/while/dowhile
statement node (proved or not) and records exact structural facts:

  - source span (start/end line:col) and the raw source text for that span
  - loop kind (for / while / dowhile)
  - induction variable name, declared type, and initializer AST shape
  - bound expression AST shape (literal / id-with-storage / swizzle / other)
  - update expression operator/kind
  - whether the loop body contains return / break / continue
  - lexical nesting depth (count of enclosing for/while/dowhile, 1-based)
  - whether attach_counted_loop_proofs actually proved this specific loop

This is READ-ONLY: it only imports frontend modules and parses corpus text
already checked into the noisemaker-for-cpp repo. It writes nothing back to
that repo. Output goes only to docs/port-engineering/loopproof/.
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
    _integer_literal, _contains_return, attach_counted_loop_proofs,
    summarize_counted_loop_proofs)

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

# All 22 keys whose gate chain touches loop_proof_bypass (verified against
# roadmap2/gate-chain-all-output.json). Includes the 16-program terminal
# loop-shape set plus the 6 adjacent keys needed for honest classification
# (effects, classicNoisedeck/noise -- terminal-blocked on matrix family
# first; median -- terminal-blocked on post-increment; gabor/newton/julia --
# budget-only / struct-blocked, not shape-blocked).
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

# The 16-program terminal non-canonical-loop-shape set (derived from
# roadmap2/gate-chain-all-output.json: touches loop_proof_bypass AND the
# fully-walked chain's LAST entry is still the "for"/"while" statement
# itself with status NO_GENERIC_PATCH -- i.e. no other capability gate is
# the actual final blocker).
TERMINAL_16 = [
    "classicNoisedeck/fractal:fractal",
    "filter/blur:blurH",
    "filter/blur:blurV",
    "filter/dither:dither",
    "filter/lightLeak:lightLeak",
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
    # IMPORTANT: TypedStatement/TypedExpression spans are line/column
    # positions in the NORMALIZED source (typed.source), not the raw corpus
    # file (typed.raw_source) -- normalize() rewrites comments to blank runs
    # and injects the uniform prelude, changing both line count and column
    # offsets relative to the raw file. Slice against typed.source.
    return entry, typed, typed.source


def slice_span(raw: str, span) -> str:
    lines = raw.splitlines()
    sl, sc, el, ec = span.start_line, span.start_column, span.end_line, span.end_column
    if sl == el:
        return lines[sl - 1][sc - 1:ec - 1]
    parts = [lines[sl - 1][sc - 1:]]
    for ln in range(sl, el - 1):
        parts.append(lines[ln])
    parts.append(lines[el - 1][:ec - 1])
    return "\n".join(parts)


def bound_shape(bound_expression) -> dict:
    literal = _integer_literal(bound_expression)
    if literal is not None:
        return {"shape": "int-literal", "value": literal}
    if bound_expression.kind == "id":
        sym = bound_expression.symbol
        storage = sym.storage if sym is not None else "?"
        name = sym.name if sym is not None else (bound_expression.callee or "?")
        writable = sym.writable if sym is not None else None
        return {"shape": f"id:storage={storage}", "name": name, "writable": writable}
    if bound_expression.kind == "member" or bound_expression.member is not None:
        return {"shape": "swizzle/member", "member": bound_expression.member,
                "base_kind": bound_expression.children[0].kind if bound_expression.children else None}
    if bound_expression.kind == "builtin":
        return {"shape": f"builtin-call:{bound_expression.callee}"}
    if bound_expression.kind == "binary":
        return {"shape": f"binary:{bound_expression.operator}"}
    return {"shape": f"other:{bound_expression.kind}"}


def induction_init_shape(declaration) -> dict:
    if not declaration.children:
        return {"shape": "none"}
    init = declaration.children[0]
    literal = _integer_literal(init)
    if literal is not None:
        return {"shape": "int-literal", "value": literal}
    if init.kind == "id":
        sym = init.symbol
        return {"shape": f"id:storage={sym.storage if sym else '?'}",
                "name": sym.name if sym else init.callee}
    return {"shape": f"other:{init.kind}"}


def contains_kind(value, kinds) -> bool:
    if value.kind in kinds:
        return True
    return any(contains_kind(child, kinds) for child in value.children)


def classify_loop(statement, raw: str, depth: int) -> dict:
    finding: dict = {
        "kind": statement.kind,
        "depth": depth,
        "span": f"{statement.span.start_line}:{statement.span.start_column}-"
                f"{statement.span.end_line}:{statement.span.end_column}",
        "proved": statement.loop_proof is not None,
    }
    if statement.loop_proof is not None:
        p = statement.loop_proof
        finding["proof"] = {
            "trip_count": p.trip_count, "lexical_depth": p.lexical_depth,
            "effective_depth": p.effective_depth, "lexical_product": p.lexical_product,
            "entrypoint_charge": p.entrypoint_charge, "bound_kind": p.bound_kind,
        }

    body_children = statement.children[-1:] if statement.children else ()
    contains_return = any(contains_kind(c, {"return"}) for c in body_children)
    contains_break = any(contains_kind(c, {"break"}) for c in body_children)
    contains_continue = any(contains_kind(c, {"continue"}) for c in body_children)
    finding["body_contains"] = {
        "return": contains_return, "break": contains_break, "continue": contains_continue,
    }

    header_text = None
    if statement.kind == "for":
        if len(statement.children) == 2 and len(statement.expressions) == 2:
            initializer, _body = statement.children
            condition, update = statement.expressions
            decl = None
            if (initializer.kind == "decl" and len(initializer.expressions) == 1
                    and initializer.expressions[0].kind == "declaration"):
                decl = initializer.expressions[0]
            finding["induction"] = {
                "declared": decl is not None,
                "name": decl.symbol.name if decl is not None and decl.symbol else None,
                "type": decl.type.display() if decl is not None else None,
                "storage": decl.symbol.storage if decl is not None and decl.symbol else None,
                "init": induction_init_shape(decl) if decl is not None else {"shape": "no-decl"},
            }
            finding["condition"] = {
                "kind": condition.kind,
                "operator": condition.operator if condition.kind == "binary" else None,
            }
            if condition.kind == "binary" and len(condition.children) == 2:
                _lhs, bound_expr = condition.children
                finding["bound"] = bound_shape(bound_expr)
            else:
                finding["bound"] = {"shape": f"non-binary-condition:{condition.kind}"}
            finding["update"] = {
                "kind": update.kind, "operator": update.operator,
            }
        else:
            finding["induction"] = {"declared": False, "note": "malformed for-node arity"}
        header_span_end_line = statement.children[0].span.end_line if statement.children else statement.span.start_line
        header_text = None
    if statement.kind in ("while", "dowhile"):
        # condition is the sole expression on these node kinds
        finding["condition"] = {
            "kind": statement.expressions[0].kind if statement.expressions else None,
        }

    finding["source_text"] = slice_span(raw, statement.span)
    return finding


def walk(function, depth_map: dict):
    """Yield (statement, nesting_depth) for every for/while/dowhile node,
    nesting_depth = 1-based count of enclosing loop statements including self."""
    def rec(statement, depth):
        is_loop = statement.kind in ("for", "while", "dowhile")
        next_depth = depth + 1 if is_loop else depth
        if is_loop:
            yield statement, next_depth
        for child in statement.children:
            yield from rec(child, next_depth)
    for statement in function.body:
        yield from rec(statement, 0)


def classify_key(key: str) -> dict:
    entry, typed, raw = load(key)
    annotated_functions = attach_counted_loop_proofs(typed.functions, key)
    summary = summarize_counted_loop_proofs(annotated_functions)
    findings = []
    for function in annotated_functions:
        if not function.body:
            continue
        for statement, depth in walk(function, {}):
            f = classify_loop(statement, raw, depth)
            f["function"] = function.name
            findings.append(f)
    return {
        "key": key,
        "source_file": entry["source"],
        "loops": findings,
        "program_summary": {
            "loop_count": summary.loop_count,
            "unproved_loop_count": summary.unproved_loop_count,
            "max_effective_depth": summary.max_effective_depth,
            "max_lexical_product": summary.max_lexical_product,
            "entrypoint_charge": summary.entrypoint_charge,
            "call_graph_acyclic": summary.call_graph_acyclic,
        },
        "in_terminal_16": key in TERMINAL_16,
    }


def main() -> int:
    rows = [classify_key(key) for key in KEYS]
    out = {
        "corpus_revision": REVISION,
        "keys_probed": len(rows),
        "terminal_16_count": sum(1 for r in rows if r["in_terminal_16"]),
        "rows": rows,
    }
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
