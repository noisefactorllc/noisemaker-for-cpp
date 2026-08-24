import sys, hashlib
sys.path.insert(0, '.')
from tools.glslcpp import check_corpus
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp import emit_typed_cpp as emit
from tools.glslcpp.check_semantics import _metadata_defaults
from tools.glslcpp.emit_typed_cpp import render_typed_cpp

repo = check_corpus._ROOT.resolve()
root = check_corpus._corpus_root(repo)
manifest = check_corpus._load_json(root / "manifest.json", "manifest")
metadata = check_corpus._load_json(root / "metadata.json", "metadata")
programs = check_corpus._validate_manifest(manifest)
key = "classicNoisedeck/caustic:caustic"
entry = next(p for p in programs if p["program_key"] == key)
defines = _metadata_defaults(metadata, key)
src_text = (root / entry["source"]).read_text(encoding="utf-8")
parsed = parse_program(src_text, key, defines)
typed = analyze_program(parsed, key)
source_hash = hashlib.sha256(typed.raw_source.encode("utf-8")).hexdigest()

# find nodes
float_bits_node = None
xor_nodes = []
def walk(node):
    global float_bits_node
    if node.kind == "builtin" and node.callee == "floatBitsToUint":
        float_bits_node = node
    if node.kind == "binary" and node.operator == "^":
        lt = node.children[0].type.display(); rt = node.children[1].type.display()
        if lt == "uint" and rt == "uint":
            xor_nodes.append(node)
    for c in node.children: walk(c)
def walk_stmt(stmt):
    for e in stmt.expressions: walk(e)
    for c in stmt.children: walk_stmt(c)
for fn in typed.functions:
    for stmt in fn.body: walk_stmt(stmt)
assert float_bits_node is not None
assert len(xor_nodes) == 3

# snapshot globals
snap_builtins = gen._BUILTINS
snap_builtin_names = dict(emit._BUILTIN_NAMES)
snap_perlin_key_gen = gen.PERLIN_KEY
snap_perlin_key_emit = emit.PERLIN_KEY
snap_auth_gen = gen.authenticate_perlin_scalar_uint_xor
snap_auth_emit = emit.authenticate_perlin_scalar_uint_xor

def fake_authenticate(program, source_hash_arg, profile):
    return tuple(xor_nodes)

try:
    # STEP 1: naive builtin widening only
    gen._BUILTINS = frozenset(gen._BUILTINS | {"floatBitsToUint"})
    emit._BUILTIN_NAMES = {**emit._BUILTIN_NAMES, "floatBitsToUint": "float_bits_to_uint"}
    try:
        gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES)
        print("step1 validator: NO ERROR")
    except gen.GeneratorError as e:
        print("step1 validator error:", e)
    try:
        render_typed_cpp(typed, key, source_hash)
        print("step1 emitter: NO ERROR")
    except Exception as e:
        print("step1 emitter error:", e)

    # STEP 2: also generalize the perlin scalar xor mechanism to admit the 3 caustic nodes
    gen.PERLIN_KEY = key
    emit.PERLIN_KEY = key
    gen.authenticate_perlin_scalar_uint_xor = fake_authenticate
    emit.authenticate_perlin_scalar_uint_xor = fake_authenticate
    try:
        gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES,
                                   perlin_scalar_uint_xor_profile=gen.PERLIN_SCALAR_UINT_XOR_PROFILE)
        print("step2 validator: NO ERROR (full pass)")
    except gen.GeneratorError as e:
        print("step2 validator error:", e)
    try:
        out = render_typed_cpp(typed, key, source_hash,
                                perlin_scalar_uint_xor_profile=emit.PERLIN_SCALAR_UINT_XOR_PROFILE)
        print("step2 emitter: PASS, rendered bytes:", len(out.encode('utf-8')))
    except Exception as e:
        print("step2 emitter error:", e)
finally:
    gen._BUILTINS = snap_builtins
    emit._BUILTIN_NAMES = snap_builtin_names
    gen.PERLIN_KEY = snap_perlin_key_gen
    emit.PERLIN_KEY = snap_perlin_key_emit
    gen.authenticate_perlin_scalar_uint_xor = snap_auth_gen
    emit.authenticate_perlin_scalar_uint_xor = snap_auth_emit

print("restored _BUILTINS ==", gen._BUILTINS == snap_builtins)
print("restored _BUILTIN_NAMES ==", emit._BUILTIN_NAMES == snap_builtin_names)
print("restored PERLIN_KEY gen ==", gen.PERLIN_KEY == snap_perlin_key_gen)
try:
    gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES)
    print("post-restore validator: NO ERROR (unexpected)")
except gen.GeneratorError as e:
    print("post-restore validator error (should match step0):", e)
