import sys, hashlib
sys.path.insert(0, '.')
from tools.glslcpp import check_corpus
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

repo = check_corpus._ROOT.resolve()
root = check_corpus._corpus_root(repo)
manifest = check_corpus._load_json(root / "manifest.json", "manifest")
metadata = check_corpus._load_json(root / "metadata.json", "metadata")
programs = check_corpus._validate_manifest(manifest)

key = "classicNoisedeck/caustic:caustic"
entry = next(p for p in programs if p["program_key"] == key)
print("defines entry", entry.get("defines"))

def metadata_defaults(metadata, program_key):
    # replicate check_semantics._metadata_defaults minimal behavior
    from tools.glslcpp.check_semantics import _metadata_defaults
    return _metadata_defaults(metadata, program_key)

defines = metadata_defaults(metadata, key)
print("resolved defines used for parse:", defines)

src_text = (root / entry["source"]).read_text(encoding="utf-8")
parsed = parse_program(src_text, key, defines)
typed = analyze_program(parsed, key)

print("function count:", len(typed.functions))
fn_names = [(f.name, getattr(f, 'id', None)) for f in typed.functions]
for n in fn_names:
    print(" fn:", n)

# Walk every function, find floatBitsToUint builtin nodes and scalar ^ (uint,uint->uint) nodes
float_bits_sites = []
xor_sites = []
all_xor_any_type = []

def walk(node, owner_fn):
    if node is None:
        return
    if node.kind == "builtin" and node.callee == "floatBitsToUint":
        float_bits_sites.append((owner_fn, node))
    if node.kind == "binary" and node.operator == "^":
        all_xor_any_type.append((owner_fn, node))
        lt = node.children[0].type.display()
        rt = node.children[1].type.display()
        if lt == "uint" and rt == "uint":
            xor_sites.append((owner_fn, node))
    for c in node.children:
        walk(c, owner_fn)

def walk_stmt(stmt, owner_fn):
    for e in stmt.expressions:
        walk(e, owner_fn)
    for c in stmt.children:
        walk_stmt(c, owner_fn)

for fn in typed.functions:
    for stmt in fn.body:
        walk_stmt(stmt, fn.name)

print()
print("floatBitsToUint sites:", len(float_bits_sites))
for owner, node in float_bits_sites:
    print("  owner=", owner, "span=", node.location if hasattr(node,'location') else None, "type=", node.type.display())

print("scalar uint^uint sites:", len(xor_sites))
for owner, node in xor_sites:
    print("  owner=", owner, "type=", node.type.display())

print("ALL ^ sites (any type):", len(all_xor_any_type))
for owner, node in all_xor_any_type:
    lt = node.children[0].type.display()
    rt = node.children[1].type.display()
    print("  owner=", owner, "left=", lt, "right=", rt, "result=", node.type.display())

print()
print("=== Independent hash re-derivation using extrude profile's exact _sha/_whole/_interface method ===")
def _sha(value):
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()

def _whole(program):
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))

def _interface(program):
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))

raw = typed.raw_source.encode("utf-8")
normalized = typed.source.encode("utf-8")
print("raw bytes", len(raw), hashlib.sha256(raw).hexdigest())
print("normalized bytes", len(normalized), hashlib.sha256(normalized).hexdigest())
print("functions tuple sha", _sha(typed.functions))
print("whole sha", _whole(typed))
print("interface sha", _interface(typed))
print("loop proof:", typed.counted_loop_proof)
print("resources:", typed.resources)
print("structs:", typed.structs)
print("uniform_blocks:", typed.uniform_blocks)
defines = tuple((item.name, item.kind, item.canonical_value) for item in typed.preprocessor_defines)
print("defines tuple:", defines)
