"""Third family probe: dFdx/dFdy/fwidth usage census for the 15 affected
programs. Read-only: parses+analyzes each program, walks every function body
for 'builtin' expressions whose callee is one of the three derivative
builtins, and records the call site span, the ARGUMENT type (what's being
differentiated -- float/vec2/vec3/vec4), and the RESULT type. Also reports
whether any derivative call's result feeds into control flow (a branch
condition) since that would make the "record" pass's dummy zero-return
(see the JS reference) potentially change control flow between the record
and replay passes -- a correctness hazard worth flagging, not just an
admission-mechanics one.
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

KEYS = [
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


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, typed


def expr_nodes(value, in_condition=False):
    yield value, in_condition
    for child in value.children:
        yield from expr_nodes(child, in_condition)


def statement_nodes(statement):
    # Condition expressions live in `expressions` for if/for/while; treat the
    # first expression of an 'if'/'while' as a condition context.
    is_branchy = statement.kind in {"if", "for", "while", "dowhile"}
    for index, expression in enumerate(statement.expressions):
        condition = is_branchy and index == 0
        yield from expr_nodes(expression, condition)
    for child in statement.children:
        yield from statement_nodes(child)


def classify_key(key: str) -> dict:
    entry, typed = load(key)
    sites = []
    for function in typed.functions:
        if not function.body:
            continue
        for statement in function.body:
            for node, in_condition in statement_nodes(statement):
                if node.kind == "builtin" and node.callee in DERIVATIVE_BUILTINS:
                    arg_type = node.children[0].type.display() if node.children else "?"
                    sites.append({
                        "function": function.name,
                        "builtin": node.callee,
                        "span": f"{node.span.start_line}:{node.span.start_column}",
                        "argument_type": arg_type,
                        "result_type": node.type.display(),
                        "feeds_branch_condition": in_condition,
                    })
    builtins_used = sorted({s["builtin"] for s in sites})
    types_used = sorted({s["argument_type"] for s in sites})
    return {
        "key": key,
        "call_site_count": len(sites),
        "builtins_used": builtins_used,
        "argument_types_used": types_used,
        "any_feeds_branch_condition": any(s["feeds_branch_condition"] for s in sites),
        "sites": sites,
    }


def main() -> int:
    rows = [classify_key(key) for key in KEYS]
    builtin_counts: dict[str, int] = {}
    for row in rows:
        for builtin in row["builtins_used"]:
            builtin_counts[builtin] = builtin_counts.get(builtin, 0) + 1
    total_sites = sum(row["call_site_count"] for row in rows)
    branch_hazard_keys = [row["key"] for row in rows if row["any_feeds_branch_condition"]]
    out = {
        "family": "dFdx / dFdy / fwidth",
        "member_count": len(KEYS),
        "total_call_sites": total_sites,
        "keys_using_each_builtin_count": builtin_counts,
        "keys_where_derivative_feeds_a_branch_condition": branch_hazard_keys,
        "rows": rows,
    }
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
