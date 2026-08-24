import json
import pathlib
import sys

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

CORPUS = REPO / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"

GRADE_KEYS = {
    "primary": "sources/filter/grade/primary.glsl",
    "hslSecondary": "sources/filter/grade/hslSecondary.glsl",
    "wheels": "sources/filter/grade/wheels.glsl",
    "vignette": "sources/filter/grade/vignette.glsl",
    "creative": "sources/filter/grade/creative.glsl",
    "lut": "sources/filter/grade/lut.glsl",
}


def walk_expr(value):
    yield value
    for child in value.children:
        yield from walk_expr(child)


def walk_stmt(stmt):
    for expr in stmt.expressions:
        yield from walk_expr(expr)
    for child in stmt.children:
        yield from walk_stmt(child)


def main():
    results = {}
    for name, relsrc in GRADE_KEYS.items():
        raw_path = CORPUS / relsrc
        raw_source = raw_path.read_text(encoding="utf-8")
        key = f"filter/grade:{name}"
        parsed = parse_program(raw_source, key)
        typed = analyze_program(parsed, key)

        by_id = {fn.id: fn for fn in typed.functions}
        by_name = {}
        for fn in typed.functions:
            by_name.setdefault(fn.name, []).append(fn)

        calls_by_fn = {}
        for fn in typed.functions:
            callees = set()
            for stmt in fn.body:
                for expr in walk_stmt(stmt):
                    if expr.kind == "call" and expr.signature_id is not None:
                        callees.add(expr.signature_id)
            calls_by_fn[fn.id] = callees

        main_fns = [fn for fn in typed.functions if fn.name == "main"]
        assert len(main_fns) == 1, (name, "expected exactly one main")
        main_fn = main_fns[0]

        reachable = set()
        stack = [main_fn.id]
        while stack:
            fid = stack.pop()
            if fid in reachable:
                continue
            reachable.add(fid)
            for callee in calls_by_fn.get(fid, ()):
                if callee not in reachable:
                    stack.append(callee)

        all_ids = set(by_id.keys())
        unreachable = all_ids - reachable
        results[name] = {
            "total_functions": len(all_ids),
            "reachable_count": len(reachable & all_ids),
            "unreachable": sorted(
                (fid, by_id[fid].name) for fid in unreachable),
        }

    for name, r in results.items():
        print(f"{name}: {r['reachable_count']}/{r['total_functions']} reachable; "
              f"unreachable={r['unreachable']}")

    out = pathlib.Path("docs/port-engineering/task32-review/reachability_output.json")
    out.write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
