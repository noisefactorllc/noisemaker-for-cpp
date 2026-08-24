from __future__ import annotations

import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEY = "filter/watercolor:wcSimplify"
entry = ENTRIES[KEY]
raw = (CORPUS / entry["source"]).read_text()
defines = gen._defaults(REPO, KEY)
program = analyze_program(parse_program(raw, KEY, defines), KEY)


def sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def whole_fingerprint(program) -> str:
    return sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def interface_fingerprint(program) -> str:
    return sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


sort2 = next(fn for fn in program.functions if fn.name == "sort2")
main = next(fn for fn in program.functions if fn.name == "main")

print("RAW_BYTES =", len(program.raw_source.encode("utf-8")))
print("RAW_SHA256 =", hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest())
print("NORMALIZED_BYTES =", len(program.source.encode("utf-8")))
print("NORMALIZED_SHA256 =", hashlib.sha256(program.source.encode("utf-8")).hexdigest())
print("FUNCTIONS_SHA256 =", sha(program.functions))
print("WHOLE_SHA256 =", whole_fingerprint(program))
print("INTERFACE_SHA256 =", interface_fingerprint(program))
print("SORT2_BODY_SHA256 =", sha(sort2.body))
print("SORT2_SIGNATURE_ID =", sort2.signature.id)
print("SORT2_PARAM_IDS =", [p.id for p in sort2.parameters])
print("body_status =", program.body_status)
print("preprocessor_defines =", program.preprocessor_defines)
print("counted_loop_proof =", program.counted_loop_proof)


def walk_expr(v, out):
    out.append(v)
    for c in v.children:
        walk_expr(c, out)


def walk_stmt(v, out):
    for e in v.expressions:
        walk_expr(e, out)
    for c in v.children:
        walk_stmt(c, out)


sites = []
for fn in program.functions:
    for s in fn.body:
        results = []
        walk_stmt(s, results)
        for node in results:
            if node.kind == "call" and node.signature_id == sort2.signature.id:
                sites.append((fn.name, fn.signature.id, node))

print(f"CALL_SITE_COUNT = {len(sites)}")
print("CALL_SITES = (")
for fn_name, fn_id, node in sites:
    span = node.span
    arg_ids = tuple(a.symbol_id for a in node.children)
    print(f"    ({fn_name!r}, {fn_id}, {span.start_line}, {span.start_column}, "
          f"{span.end_line}, {span.end_column}, {arg_ids!r}, {sha(node)!r}),")
print(")")
