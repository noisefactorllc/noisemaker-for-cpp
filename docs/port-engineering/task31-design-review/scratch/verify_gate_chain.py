import sys, hashlib
sys.path.insert(0, '.')
from tools.glslcpp import check_corpus
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp import emit_typed_cpp as emit
from tools.glslcpp.check_semantics import _metadata_defaults

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

print("APPROVED_CAPABILITIES len:", len(gen.APPROVED_CAPABILITIES))

# Step 0: baseline, no patches
try:
    gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES)
    print("step0 validator: NO ERROR (unexpected)")
except gen.GeneratorError as e:
    print("step0 validator error:", e)

# Emitter needs a full program dict/slice-spec context normally via generate_outputs.
# Try direct construction similar to how emit_typed_cpp exposes a single-program emit path.
print([n for n in dir(emit) if 'emit' in n.lower() or 'Emitter' in n])

from tools.glslcpp.emit_typed_cpp import render_typed_cpp, _error

source_hash = hashlib.sha256(typed.raw_source.encode("utf-8")).hexdigest()
try:
    render_typed_cpp(typed, key, source_hash)
    print("step0 emitter: NO ERROR (unexpected)")
except Exception as e:
    print("step0 emitter error:", e)

# Step 1: naive admission of floatBitsToUint into _BUILTINS (diagnostic monkeypatch)
orig_builtins = set(gen._BUILTINS)
orig_builtin_names = set(emit._BUILTIN_NAMES)
try:
    gen._BUILTINS = gen._BUILTINS | {"floatBitsToUint"}
    emit._BUILTIN_NAMES = emit._BUILTIN_NAMES | {"floatBitsToUint"}
    try:
        gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES)
        print("step1 validator: NO ERROR (unexpected)")
    except gen.GeneratorError as e:
        print("step1 validator error:", e)
    try:
        render_typed_cpp(typed, key, source_hash)
        print("step1 emitter: NO ERROR (unexpected)")
    except Exception as e:
        print("step1 emitter error:", e)

    # Step 2: also generalize scalar xor gate to admit the 3 real Caustic XOR nodes
    # Find the 3 xor nodes and 1 floatBitsToUint node from typed tree again (reuse xor_sites, float_bits_sites from prior script if re-run standalone)
except Exception as outer:
    print("unexpected outer error", outer)
finally:
    gen._BUILTINS = orig_builtins
    emit._BUILTIN_NAMES = orig_builtin_names

print("restored _BUILTINS len:", len(gen._BUILTINS), "restored _BUILTIN_NAMES len:", len(emit._BUILTIN_NAMES))
# sanity: baseline error reproduces after restore
try:
    gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES)
    print("post-restore validator: NO ERROR (unexpected)")
except gen.GeneratorError as e:
    print("post-restore validator error (should match step0):", e)
