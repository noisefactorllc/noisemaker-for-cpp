"""Read-only probe: census every `index`-kind node in the six grade programs.

Does NOT modify any file under noisemaker-for-cpp. Only imports and calls
parse_program/analyze_program (pure functions) on in-memory source text.
"""
import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

CORPUS = REPO / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())

GRADE_KEYS = {
    "primary": "sources/filter/grade/primary.glsl",
    "hslSecondary": "sources/filter/grade/hslSecondary.glsl",
    "wheels": "sources/filter/grade/wheels.glsl",
    "vignette": "sources/filter/grade/vignette.glsl",
    "creative": "sources/filter/grade/creative.glsl",
    "lut": "sources/filter/grade/lut.glsl",
}


def walk_expr(value, parent=None, in_function=None):
    yield value, parent
    for child in value.children:
        yield from walk_expr(child, value, in_function)


def walk_stmt(stmt, function_name):
    for expr in stmt.expressions:
        yield from walk_expr(expr, None, function_name)
    for child in stmt.children:
        yield from walk_stmt(child, function_name)


def main():
    results = {}
    for name, relsrc in GRADE_KEYS.items():
        raw_path = CORPUS / relsrc
        raw_source = raw_path.read_text(encoding="utf-8")
        key = f"filter/grade:{name}"
        parsed = parse_program(raw_source, key)
        typed = analyze_program(parsed, key)
        sites = []
        for fn in typed.functions:
            for stmt in fn.body:
                for expr, parent in walk_stmt(stmt, fn.name):
                    if expr.kind != "index":
                        continue
                    base, index = expr.children
                    is_write = (parent is not None and parent.kind == "assign"
                                and parent.operator == "=" and parent.children[0] is expr)
                    sites.append({
                        "function": fn.name,
                        "span": f"{expr.span.start_line}:{expr.span.start_column}-{expr.span.end_line}:{expr.span.end_column}",
                        "base_kind": base.kind,
                        "base_symbol_name": base.symbol.name if base.symbol else None,
                        "base_type": base.type.display(),
                        "index_kind": index.kind,
                        "index_literal_value": index.literal_value if index.kind == "literal" else None,
                        "index_symbol_name": index.symbol.name if (index.kind == "id" and index.symbol) else None,
                        "category": expr.category,
                        "is_write_lvalue_of_assign": is_write,
                        "expr_type": expr.type.display(),
                    })
        results[name] = {
            "raw_sha256": hashlib.sha256(raw_source.encode()).hexdigest(),
            "raw_bytes": len(raw_source.encode()),
            "function_count": len(typed.functions),
            "index_site_count": len(sites),
            "sites": sites,
        }
        # cross-check manifest hash
        manifest_entry = next(p for p in MANIFEST["programs"] if p["program_key"] == key)
        assert manifest_entry["raw_sha256"] == results[name]["raw_sha256"], (name, "raw sha mismatch")

    out = pathlib.Path("docs/port-engineering/task32-review/index_census_output.json")
    out.write_text(json.dumps(results, indent=2))
    total = sum(r["index_site_count"] for r in results.values())
    print("total index sites:", total)
    for name, r in results.items():
        kinds = set((s["base_kind"], s["index_kind"]) for s in r["sites"])
        literal_indices = [s for s in r["sites"] if s["index_kind"] == "literal"]
        non_id_base = [s for s in r["sites"] if s["base_kind"] != "id"]
        print(f"{name}: {r['index_site_count']} sites, shape-set={kinds}, "
              f"literal_index_count={len(literal_indices)}, non_id_base_count={len(non_id_base)}")


if __name__ == "__main__":
    main()
