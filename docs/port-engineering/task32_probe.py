import sys, json, pathlib, hashlib, dataclasses

ROOT = pathlib.Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.loop_proof import attach_counted_loop_proofs, summarize_counted_loop_proofs

CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
manifest = json.loads((CORPUS / "manifest.json").read_text())
progs = {p["program_key"]: p for p in manifest["programs"] if p["program_key"].startswith("filter/grade:")}

KEYS = ["filter/grade:primary", "filter/grade:hslSecondary", "filter/grade:wheels",
        "filter/grade:vignette", "filter/grade:creative", "filter/grade:lut"]

def sha(v):
    return hashlib.sha256(repr(v).encode("utf-8")).hexdigest()

def span(v):
    s = v.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"

def whole_fp(program):
    return sha((program.key, program.source, program.raw_source, program.declarations,
                program.functions, program.resources, program.body_status,
                program.local_type_names, program.structs, program.uniform_blocks,
                program.interface_symbols, program.builtin_symbols,
                program.counted_loop_proof, program.preprocessor_defines))

def interface_fp(program):
    return sha((program.declarations, program.resources, program.local_type_names,
                program.structs, program.uniform_blocks, program.interface_symbols,
                program.builtin_symbols, program.preprocessor_defines))

def walk_expr(v):
    yield v
    for c in v.children:
        yield from walk_expr(c)

def walk_stmt(v):
    for e in v.expressions:
        yield from walk_expr(e)
    for c in v.children:
        yield from walk_stmt(c)

out = {}
for key in KEYS:
    p = progs[key]
    src_path = CORPUS / p["source"]
    raw = src_path.read_text(encoding="utf-8")
    raw_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    assert raw_sha == p["raw_sha256"], (key, raw_sha, p["raw_sha256"])
    parsed = parse_program(raw, key, {})
    typed = analyze_program(parsed, key)
    # attach counted loop proofs like the real pipeline does
    functions = attach_counted_loop_proofs(typed.functions, key)
    program_proof = summarize_counted_loop_proofs(functions)
    typed = dataclasses.replace(typed, functions=functions, counted_loop_proof=program_proof)

    entry = {
        "raw_bytes": len(raw.encode("utf-8")),
        "raw_sha256": raw_sha,
        "normalized_bytes": len(typed.source.encode("utf-8")),
        "normalized_sha256": hashlib.sha256(typed.source.encode("utf-8")).hexdigest(),
        "whole_sha256": whole_fp(typed),
        "interface_sha256": interface_fp(typed),
        "functions_sha256": sha(typed.functions),
        "preprocessor_defines": typed.preprocessor_defines,
        "body_status": typed.body_status,
        "counted_loop_proof": dataclasses.asdict(typed.counted_loop_proof) if typed.counted_loop_proof else None,
        "num_declarations": len(typed.declarations),
        "declarations": [],
        "functions": [],
        "index_sites": [],
    }

    for i, d in enumerate(typed.declarations):
        entry["declarations"].append({
            "index": i,
            "symbol_id": d.symbol.id,
            "name": d.symbol.name,
            "storage": d.symbol.storage,
            "writable": d.symbol.writable,
            "direction": d.symbol.direction,
            "type": d.type.display(),
            "span": span(d),
            "sha256": sha(d),
            "initializer_kind": d.initializer.kind if d.initializer else None,
            "initializer_sha256": sha(d.initializer) if d.initializer else None,
            "initializer_span": span(d.initializer) if d.initializer else None,
            "lanes": ([{"literal": c.literal, "value": c.literal_value, "span": span(c), "sha256": sha(c)}
                       for c in d.initializer.children] if d.initializer else None),
        })

    for f in typed.functions:
        finfo = {
            "id": f.id, "name": f.name, "num_params": len(f.parameters),
            "body_len": len(f.body), "sha256": sha(f),
            "params": [(pm.id, pm.name, pm.type.display(), pm.storage, pm.direction) for pm in f.parameters],
        }
        entry["functions"].append(finfo)

    # find LUMA_WEIGHTS reads (id-kind nodes with symbol name LUMA_WEIGHTS)
    luma_symbol_id = None
    for d in typed.declarations:
        if d.symbol.name == "LUMA_WEIGHTS":
            luma_symbol_id = d.symbol.id
    def walk_with_parent(v, parent=None, cidx=None):
        yield v, parent, cidx
        for i, c in enumerate(v.children):
            yield from walk_with_parent(c, v, i)

    def statement_expr_roots(st):
        """Yield (expression_root) for this statement and all nested statements."""
        for e in st.expressions:
            yield e
        for c in st.children:
            yield from statement_expr_roots(c)

    reads = []
    for f in typed.functions:
        for st in f.body:
            for e_root in statement_expr_roots(st):
                for node, parent, cidx in walk_with_parent(e_root):
                    if node.kind == "id" and node.symbol_id == luma_symbol_id:
                        reads.append({"function_id": f.id, "function_name": f.name, "span": span(node), "sha256": sha(node)})
    entry["luma_weight_reads"] = reads

    for f in typed.functions:
        for st in f.body:
            for e_root in statement_expr_roots(st):
                for node, parent, cidx in walk_with_parent(e_root):
                    if node.kind == "index":
                        base, index = node.children
                        role = ("write" if parent is not None and parent.kind == "assign"
                                and parent.operator == "=" and cidx == 0 else "read")
                        entry["index_sites"].append({
                            "function_id": f.id, "function_name": f.name,
                            "span": span(node), "sha256": sha(node),
                            "category": node.category,
                            "role": role,
                            "base_kind": base.kind, "base_symbol_id": base.symbol_id,
                            "base_name": base.symbol.name if base.symbol else None,
                            "base_type": base.type.display(),
                            "base_storage": base.symbol.storage if base.symbol else None,
                            "base_writable": base.symbol.writable if base.symbol else None,
                            "index_kind": index.kind, "index_symbol_id": index.symbol_id,
                            "index_name": index.symbol.name if index.symbol else None,
                            "index_storage": index.symbol.storage if index.symbol else None,
                        })

    out[key] = entry

pathlib.Path("docs/port-engineering/task32_probe_output.json").write_text(json.dumps(out, indent=2, default=str))
print("OK", {k: (len(v["index_sites"]), len(v["luma_weight_reads"])) for k, v in out.items()})
