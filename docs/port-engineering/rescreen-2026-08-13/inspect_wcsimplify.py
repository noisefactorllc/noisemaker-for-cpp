from __future__ import annotations

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

print("raw_sha256 (entry):", entry["raw_sha256"])
import hashlib
print("raw_sha256 (recomputed):", hashlib.sha256(program.raw_source.encode()).hexdigest())
print("source_sha256:", hashlib.sha256(program.source.encode()).hexdigest())
print("defines:", program.preprocessor_defines)
print("declarations:")
for d in program.declarations:
    print(" ", d.symbol.name, d.symbol.storage, d.type.display())

print("functions:")
for fn in program.functions:
    print(" ", fn.name, "sig_id=", fn.signature.id, "ret=", fn.return_type.display(),
          "params=", [(p.name, p.id, p.type.display(), p.direction) for p in fn.parameters])

sort2 = next(fn for fn in program.functions if fn.name == "sort2")
print("sort2 body statements:")
for s in sort2.body:
    print("  kind=", s.kind, "span=", s.span, "nexpr=", len(s.expressions), "nchild=", len(s.children))
    for e in s.expressions:
        print("     expr kind=", e.kind, "type=", e.type.display(), "op=", getattr(e, "operator", None))

def walk_expr(v, out):
    out.append(v)
    for c in v.children:
        walk_expr(c, out)

def walk_stmt(v, out):
    for e in v.expressions:
        walk_expr(e, out)
    for c in v.children:
        walk_stmt(c, out)

main = next(fn for fn in program.functions if fn.name == "main")
sites = []
for s in main.body:
    results = []
    walk_stmt(s, results)
    for node in results:
        if node.kind == "call" and node.signature_id == sort2.signature.id:
            sites.append(node)

print(f"call sites to sort2 from main: {len(sites)}")
for i, node in enumerate(sites):
    args = node.children
    print(f"  [{i}] span={node.span} args=", [(a.kind, a.symbol_id, getattr(a, 'category', None),
                                               getattr(getattr(a, 'symbol', None), 'name', None),
                                               getattr(getattr(a, 'symbol', None), 'storage', None))
                                              for a in args])
print("sort2 signature id:", sort2.signature.id)
