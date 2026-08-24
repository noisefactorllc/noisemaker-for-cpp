"""For every program whose terminal validator blocker is 'unsupported global
declaration', introspect the OFFENDING declaration directly (replicating the
exact admission predicate at generate_typed_slice.py:2016-2037 and :2099-2104)
to sub-classify: const array vs const non-float scalar/vector vs non-const
global vs global matrix vs array-typed uniform/output (which are legal), etc.

Read-only. Runs against the same frozen snapshot as run_census.py.
"""
from __future__ import annotations

import json
import pathlib
import sys

SNAPSHOT_TS = "20260812T225121Z"
REPO = pathlib.Path(f"docs/port-engineering/census/snapshot/{SNAPSHOT_TS}/repo")
sys.path.insert(0, str(REPO))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp import check_corpus  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}


def classify(key: str) -> dict:
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(REPO, key)
    program = analyze_program(parse_program(raw, key, defines), key)

    admitted_literal_ints = {
        declaration.symbol.id for declaration in program.declarations
        if (key in gen.SOURCE_GLOBAL_LITERAL_INT_KEYS
            and declaration.symbol.storage == "const"
            and declaration.type.display() == "int")
    }

    for declaration in program.declarations:
        storage = declaration.symbol.storage
        if storage in {"uniform", "output"}:
            continue
        if declaration.symbol.id in admitted_literal_ints:
            continue
        # (smooth_edge_luma_weights / grade_luma_weights authorized declarations
        # are single specific instances tied to specific profiles/keys; none of
        # the remaining-75 keys are grade or celShading/smooth so this simplified
        # replica is faithful for this corpus slice.)
        if storage != "const" or declaration.type.display() != "float" or declaration.initializer is None:
            array_len = getattr(declaration.type, "array_length", None)
            return {
                "key": key,
                "offending_symbol": getattr(declaration.symbol, "name", "?"),
                "storage": storage,
                "type_kind": declaration.type.kind,
                "type_display": declaration.type.display(),
                "array_length": array_len,
                "has_initializer": declaration.initializer is not None,
                "loc": f"{declaration.span.start_line}:{declaration.span.start_column}"
                if getattr(declaration, "span", None) else "?",
            }
    return {"key": key, "offending_symbol": None, "note": "no offending global at this stage (blocker is elsewhere in the pipeline for this key)"}


def main() -> int:
    raw_census = json.loads(pathlib.Path("docs/port-engineering/census/raw_census.json").read_text())
    keys = [r["key"] for r in raw_census["rows"]
            if isinstance(r.get("validator"), str) and r["validator"].endswith("unsupported global declaration")]
    results = [classify(k) for k in keys]
    out = pathlib.Path("docs/port-engineering/census/global_decl_probe.json")
    out.write_text(json.dumps(results, indent=1, sort_keys=True))
    for r in results:
        print(r["key"], "::", {k: v for k, v in r.items() if k != "key"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
