"""Read-only frontier census for the C++20 port, run against a frozen snapshot.

Adapted from docs/port-engineering/frontier_census.py (prior agent),
extended to:
  - run against a FROZEN snapshot of tools/glslcpp (immune to concurrent edits
    from the agent actively working on generate_typed_slice.py/emit_typed_cpp.py/
    typed_slice.json/tests/test_typed_generator.py)
  - record reachability of the terminal blocker's callee/construct from main()
    at the program's authorized define map, via a best-effort call-graph BFS
  - record whether the blocker is a builtin call, and if so, whether that
    callee is reachable from main (dead-code detection)

Never writes under . or
../noisemaker-for-cpu. Never runs git.
"""
from __future__ import annotations

import json
import pathlib
import sys
import traceback

SNAPSHOT_TS = "20260812T225121Z"
REPO = pathlib.Path(f"docs/port-engineering/census/snapshot/{SNAPSHOT_TS}/repo")
sys.path.insert(0, str(REPO))

from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp import check_corpus  # noqa: E402
from tools.glslcpp.frontend import parse_program, FrontendError  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

SLICE = json.loads((REPO / "tools/glslcpp/typed_slice.json").read_text())
TYPED = {row["program_key"] for row in SLICE["programs"]}

GRADE_KEYS = {
    "filter/grade:creative", "filter/grade:hslSecondary", "filter/grade:lut",
    "filter/grade:primary", "filter/grade:vignette", "filter/grade:wheels",
}


def first_line(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else f"{type(error).__name__}"


def call_graph_reachable_from_main(program) -> set[str]:
    """BFS the function-call graph starting at 'main', over typed IR.

    Returns the set of function names transitively reachable (including
    'main' itself if present). Best-effort: only follows direct 'call' kind
    expression nodes naming a function defined in this program. Does not
    attempt to model #if-eliminated branches beyond what the preprocessor
    already stripped during parse_program (which IS driven by the program's
    authorized define map, so preprocessor-dead branches are already gone
    from the typed IR by the time we get here).
    """
    by_name = {}
    for fn in program.functions:
        name = getattr(fn, "name", None)
        if name:
            by_name.setdefault(name, []).append(fn)

    def walk_expr(value, calls: set[str]):
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

    def walk_stmt(value, calls: set[str]):
        if value is None:
            return
        for expr in getattr(value, "expressions", ()) or ():
            walk_expr(expr, calls)
        for child in getattr(value, "children", ()) or ():
            walk_stmt(child, calls)
        init = getattr(value, "initializer", None)
        if init is not None:
            walk_expr(init, calls)

    visited: set[str] = set()
    frontier = ["main"] if "main" in by_name else []
    while frontier:
        name = frontier.pop()
        if name in visited:
            continue
        visited.add(name)
        for fn in by_name.get(name, ()):
            calls: set[str] = set()
            for stmt in getattr(fn, "body", ()) or ():
                walk_stmt(stmt, calls)
            for callee in calls:
                if callee in by_name and callee not in visited:
                    frontier.append(callee)
    return visited


def builtin_call_sites(program) -> list[dict]:
    """Every builtin (non-user-defined) call expression, with reachability tag."""
    by_name = {getattr(fn, "name", None) for fn in program.functions}
    reachable_fns = call_graph_reachable_from_main(program)
    sites = []

    def walk_expr(value, enclosing_fn_name, enclosing_reachable):
        if value is None:
            return
        kind = getattr(value, "kind", None)
        callee = getattr(value, "callee", None)
        if kind == "builtin" and isinstance(callee, str):
            span = getattr(value, "span", None)
            loc = (f"{span.start_line}:{span.start_column}" if span is not None else "?")
            sites.append({
                "callee": callee,
                "in_function": enclosing_fn_name,
                "function_reachable_from_main": enclosing_reachable,
                "loc": loc,
            })
        for child in getattr(value, "children", ()) or ():
            walk_expr(child, enclosing_fn_name, enclosing_reachable)
        for expr in getattr(value, "expressions", ()) or ():
            walk_expr(expr, enclosing_fn_name, enclosing_reachable)

    def walk_stmt(value, enclosing_fn_name, enclosing_reachable):
        if value is None:
            return
        for expr in getattr(value, "expressions", ()) or ():
            walk_expr(expr, enclosing_fn_name, enclosing_reachable)
        for child in getattr(value, "children", ()) or ():
            walk_stmt(child, enclosing_fn_name, enclosing_reachable)
        init = getattr(value, "initializer", None)
        if init is not None:
            walk_expr(init, enclosing_fn_name, enclosing_reachable)

    for fn in program.functions:
        name = getattr(fn, "name", None)
        reachable = name in reachable_fns
        for stmt in getattr(fn, "body", ()) or ():
            walk_stmt(stmt, name, reachable)
    return sites


def census_one(key: str) -> dict:
    entry = ENTRIES[key]
    row = {
        "key": key,
        "raw_bytes": entry["raw_bytes"],
        "raw_sha256": entry["raw_sha256"],
        "source": entry["source"],
        "defines": None,
        "parse": None,
        "validator": None,
        "emitter": None,
        "builtins_used": None,
        "builtin_call_sites": None,
        "main_reachable_functions": None,
        "structs": None,
        "uniform_blocks": None,
        "interface_symbols": None,
    }
    try:
        raw = (CORPUS / entry["source"]).read_text()
        defines = gen._defaults(REPO, key)
        row["defines"] = defines
    except Exception as error:  # noqa: BLE001
        row["parse"] = f"DEFAULTS-ERROR: {first_line(error)}"
        row["parse_type"] = type(error).__name__
        return row

    try:
        parsed = parse_program(raw, key, defines)
        program = analyze_program(parsed, key)
        row["parse"] = "pass"
    except Exception as error:  # noqa: BLE001
        row["parse"] = first_line(error)
        row["parse_type"] = type(error).__name__
        row["parse_traceback"] = traceback.format_exc()
        return row

    try:
        used = sorted({
            name
            for function in program.functions
            for name in getattr(function, "builtins", ()) or ()
        })
        row["builtins_used"] = used
    except Exception:  # noqa: BLE001
        pass

    try:
        row["builtin_call_sites"] = builtin_call_sites(program)
    except Exception as error:  # noqa: BLE001
        row["builtin_call_sites"] = f"ERROR: {first_line(error)}"

    try:
        row["main_reachable_functions"] = sorted(call_graph_reachable_from_main(program))
    except Exception as error:  # noqa: BLE001
        row["main_reachable_functions"] = f"ERROR: {first_line(error)}"

    try:
        row["structs"] = len(program.structs)
        row["uniform_blocks"] = len(program.uniform_blocks)
        row["interface_symbols"] = len(program.interface_symbols)
    except Exception:  # noqa: BLE001
        pass

    try:
        gen.validate_capabilities(
            program, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"]
        )
        row["validator"] = "pass"
    except Exception as error:  # noqa: BLE001
        row["validator"] = first_line(error)
        row["validator_type"] = type(error).__name__

    try:
        emit.render_typed_cpp(
            program, key, entry["raw_sha256"], "census_probe", "bind_census_probe"
        )
        row["emitter"] = "pass"
    except Exception as error:  # noqa: BLE001
        row["emitter"] = first_line(error)
        row["emitter_type"] = type(error).__name__
    return row


def main() -> int:
    all_keys = sorted(ENTRIES)
    assert len(all_keys) == 212, f"expected 212 corpus programs, got {len(all_keys)}"
    remaining = [key for key in all_keys if key not in TYPED]
    assert len(TYPED) == 137, f"expected 137 currently-typed rows (131+6 grade), got {len(TYPED)}"
    assert len(remaining) == 75, f"expected 75 currently-remaining rows, got {len(remaining)}"
    assert GRADE_KEYS <= TYPED, "grade cluster expected already landed in typed_slice.json"

    rows = []
    for key in remaining:
        try:
            rows.append(census_one(key))
        except Exception:  # noqa: BLE001
            rows.append({"key": key, "crash": traceback.format_exc()})

    out = {
        "snapshot_ts": SNAPSHOT_TS,
        "revision": REVISION,
        "corpus_total": len(ENTRIES),
        "typed_total_now": len(TYPED),
        "grade_landed_now": sorted(GRADE_KEYS),
        "unported_81_total": len(remaining) + len(GRADE_KEYS),
        "remaining_75_after_grade": len(remaining),
        "rows": rows,
    }
    outpath = pathlib.Path("docs/port-engineering/census/raw_census.json")
    outpath.write_text(json.dumps(out, indent=1, sort_keys=True))
    print("wrote", outpath, "rows:", len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
