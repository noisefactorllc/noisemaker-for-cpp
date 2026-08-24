"""Layer 4: on top of layers 1-3, provisionally admit matrix indexing
(any index into a matrix-typed base), reflect(), mat3 constructors, mat3*vec3
and mat3*mat3 binary expressions, mat3 return types and mat3 parameters --
to find each of the 7 mat3-family programs' true NEXT blocker (or PASS),
plus main()-reachability of the matrix-touching code, per program.

Never writes to the real repo.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen0  # noqa: E402
from tools.glslcpp import generate_typed_slice_relaxed4 as gen4  # noqa: E402
from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = HERE / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

MAT3_KEYS = [
    "classicNoisedeck/cellNoise:cellNoise",
    "classicNoisedeck/colorLab:colorLab",
    "classicNoisedeck/moodscape:moodscape",
    "classicNoisedeck/shapeMixer:shapeMixer",
    "classicNoisedeck/shapes:shapes",
    "filter/adjust:adjust",
    "filter/colorspace:colorspace",
]


def first_line(error) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def call_graph_reachable_from_main(program) -> set[str]:
    by_name = {}
    for fn in program.functions:
        name = getattr(fn, "name", None)
        if name:
            by_name.setdefault(name, []).append(fn)

    def walk_expr(value, calls):
        if value is None:
            return
        kind = getattr(value, "kind", None)
        callee = getattr(value, "callee", None)
        if kind in ("call", "builtin") and isinstance(callee, str):
            calls.add(callee)
        for child in getattr(value, "children", ()) or ():
            walk_expr(child, calls)
        for expr in getattr(value, "expressions", ()) or ():
            walk_expr(expr, calls)

    def walk_stmt(value, calls):
        if value is None:
            return
        for expr in getattr(value, "expressions", ()) or ():
            walk_expr(expr, calls)
        for child in getattr(value, "children", ()) or ():
            walk_stmt(child, calls)
        init = getattr(value, "initializer", None)
        if init is not None:
            walk_expr(init, calls)

    visited = set()
    frontier = ["main"] if "main" in by_name else []
    while frontier:
        name = frontier.pop()
        if name in visited:
            continue
        visited.add(name)
        for fn in by_name.get(name, ()):
            calls = set()
            for stmt in getattr(fn, "body", ()) or ():
                walk_stmt(stmt, calls)
            for callee in calls:
                if callee in by_name and callee not in visited:
                    frontier.append(callee)
    return visited


def matrix_touching_functions(program) -> dict:
    """Functions containing any matrix-typed expression node (construct,
    binary, index-into-matrix, id-of-matrix-type, global decl reference)."""
    touching = set()

    def touches_matrix(value) -> bool:
        found = False
        if getattr(value, "type", None) is not None and value.type.kind == "matrix":
            found = True
        for child in getattr(value, "children", ()) or ():
            if touches_matrix(child):
                found = True
        return found

    def walk_stmt(value, fn_name):
        if value is None:
            return
        for expr in getattr(value, "expressions", ()) or ():
            if touches_matrix(expr):
                touching.add(fn_name)
        for child in getattr(value, "children", ()) or ():
            walk_stmt(child, fn_name)

    for fn in program.functions:
        name = getattr(fn, "name", None)
        for stmt in getattr(fn, "body", ()) or ():
            walk_stmt(stmt, name)
    return touching


def main() -> int:
    results = []
    for key in MAT3_KEYS:
        entry = ENTRIES[key]
        raw = (CORPUS / entry["source"]).read_text()
        defines = gen0._defaults(HERE, key)
        program = analyze_program(parse_program(raw, key, defines), key)
        row = {"key": key}

        reachable = call_graph_reachable_from_main(program)
        touching = matrix_touching_functions(program)
        row["main_reachable_functions"] = sorted(reachable)
        row["matrix_touching_functions"] = sorted(touching)
        row["matrix_code_reachable_from_main"] = bool(touching & reachable)
        row["matrix_touching_functions_NOT_reachable"] = sorted(touching - reachable)

        try:
            gen4.validate_capabilities(program, gen4.APPROVED_CAPABILITIES,
                                        source_hash=entry["raw_sha256"])
            row["layer4_blocker"] = "VALIDATOR-PASS"
            try:
                emit.render_typed_cpp(program, key, entry["raw_sha256"],
                                       "probe", "bind_probe")
                row["layer4_emitter"] = "pass (unexpected -- real emitter has no mat3 support)"
            except Exception as error:  # noqa: BLE001
                row["layer4_emitter"] = first_line(error)
        except gen4.GeneratorError as error:
            row["layer4_blocker"] = first_line(error)
        results.append(row)

    out = HERE.parent / "probe_layer4.json"
    out.write_text(json.dumps(results, indent=1, sort_keys=True))
    for r in results:
        print(r["key"])
        print("  layer4_blocker:", r["layer4_blocker"])
        print("  layer4_emitter:", r.get("layer4_emitter"))
        print("  matrix_touching_functions:", r["matrix_touching_functions"])
        print("  matrix code reachable from main():", r["matrix_code_reachable_from_main"])
        print("  matrix-touching fns NOT reachable:", r["matrix_touching_functions_NOT_reachable"])
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
