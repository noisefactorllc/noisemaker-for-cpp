"""Independent verification of the bitops cluster doc's reachability claims:
for every one of the 75 currently-unported programs, find every bitwise
binary-operator site (&, |, ^, <<, >>) in the typed IR and tag it with
whether its enclosing function is reachable from main() at the program's
authorized define map (same BFS as run_census.py).
"""
from __future__ import annotations
import json, pathlib, sys

SNAPSHOT_TS = "20260812T225121Z"
REPO = pathlib.Path(f"docs/port-engineering/census/snapshot/{SNAPSHOT_TS}/repo")
sys.path.insert(0, str(REPO))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

sys.path.insert(0, "docs/port-engineering/census")
from run_census import call_graph_reachable_from_main  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}
SLICE = json.loads((REPO / "tools/glslcpp/typed_slice.json").read_text())
TYPED = {row["program_key"] for row in SLICE["programs"]}

BIT_OPS = {"&", "|", "^", "<<", ">>"}


def bitwise_sites(program):
    reachable_fns = call_graph_reachable_from_main(program)
    sites = []

    def walk_expr(value, fn_name, reachable):
        if value is None:
            return
        kind = getattr(value, "kind", None)
        op = getattr(value, "operator", None)
        if kind == "binary" and op in BIT_OPS:
            span = getattr(value, "span", None)
            loc = f"{span.start_line}:{span.start_column}" if span else "?"
            sites.append({"operator": op, "in_function": fn_name,
                           "function_reachable_from_main": reachable, "loc": loc})
        for c in getattr(value, "children", ()) or ():
            walk_expr(c, fn_name, reachable)
        for e in getattr(value, "expressions", ()) or ():
            walk_expr(e, fn_name, reachable)

    def walk_stmt(value, fn_name, reachable):
        if value is None:
            return
        for e in getattr(value, "expressions", ()) or ():
            walk_expr(e, fn_name, reachable)
        for c in getattr(value, "children", ()) or ():
            walk_stmt(c, fn_name, reachable)

    for fn in program.functions:
        name = getattr(fn, "name", None)
        reachable = name in reachable_fns
        for st in getattr(fn, "body", ()) or ():
            walk_stmt(st, name, reachable)
    return sites


def main():
    remaining = sorted(k for k in ENTRIES if k not in TYPED)
    out = {}
    for key in remaining:
        entry = ENTRIES[key]
        raw = (CORPUS / entry["source"]).read_text()
        defines = gen._defaults(REPO, key)
        try:
            program = analyze_program(parse_program(raw, key, defines), key)
        except Exception as error:  # noqa: BLE001
            out[key] = {"error": str(error)}
            continue
        sites = bitwise_sites(program)
        if sites:
            out[key] = {"sites": sites,
                         "any_reachable": any(s["function_reachable_from_main"] for s in sites)}
    path = pathlib.Path("docs/port-engineering/census/bitwise_sites_probe.json")
    path.write_text(json.dumps(out, indent=1, sort_keys=True))
    for k, v in out.items():
        print(k, "-> any_reachable:", v.get("any_reachable"), "n_sites:", len(v.get("sites", [])))
    print("total programs with bitwise binary-op sites:", len(out))


if __name__ == "__main__":
    main()
