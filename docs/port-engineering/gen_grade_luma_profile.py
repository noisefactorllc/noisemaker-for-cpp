import json

d = json.load(open('docs/port-engineering/task32_probe_output.json'))

LUMA_KEYS = ["filter/grade:creative", "filter/grade:hslSecondary", "filter/grade:primary",
             "filter/grade:vignette", "filter/grade:wheels"]
SHORT = {
    "filter/grade:creative": "creative",
    "filter/grade:hslSecondary": "hslsecondary",
    "filter/grade:primary": "primary",
    "filter/grade:vignette": "vignette",
    "filter/grade:wheels": "wheels",
}

def pyrepr(s):
    return repr(s)

lines = []
lines.append('"""Exact identity profiles for the five grade-cluster LUMA_WEIGHTS globals."""')
lines.append("")
lines.append("from __future__ import annotations")
lines.append("")
lines.append("import hashlib")
lines.append("")
lines.append("from .typed_ir import TypedDeclaration, TypedExpression, TypedProgram, TypedStatement")
lines.append("")
lines.append("")
lines.append('KEYS = (')
for k in LUMA_KEYS:
    lines.append(f'    {pyrepr(k)},')
lines.append(')')
lines.append('PROFILES = {')
for k in LUMA_KEYS:
    lines.append(f'    {pyrepr(k)}: {pyrepr("grade-" + SHORT[k] + "-luma-weights-v1")},')
lines.append('}')
lines.append('_OPTIONAL_PROOF_FIELDS = (')
lines.append('    "fixed_nine_table_proof",')
lines.append('    "fixed_grid_counter_store_proof",')
lines.append('    "fixed_array_in_parameter_proof",')
lines.append('    "fixed_affine_centers13_proof",')
lines.append(')')
lines.append('')
lines.append('__all__ = ("KEYS", "PROFILES", "authenticate_grade_luma_weights", "apply_grade_luma_weights")')
lines.append('')
lines.append('')
lines.append('def _sha(value: object) -> str:')
lines.append('    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()')
lines.append('')
lines.append('')
lines.append('def _span(value: object) -> str:')
lines.append('    span = getattr(value, "span")')
lines.append('    return (f"{span.start_line}:{span.start_column}-"')
lines.append('            f"{span.end_line}:{span.end_column}")')
lines.append('')
lines.append('')
lines.append('def _whole_fingerprint(program: TypedProgram) -> str:')
lines.append('    return _sha((')
lines.append('        program.key, program.source, program.raw_source, program.declarations,')
lines.append('        program.functions, program.resources, program.body_status,')
lines.append('        program.local_type_names, program.structs, program.uniform_blocks,')
lines.append('        program.interface_symbols, program.builtin_symbols,')
lines.append('        program.counted_loop_proof, program.preprocessor_defines,')
lines.append('    ))')
lines.append('')
lines.append('')
lines.append('def _interface_fingerprint(program: TypedProgram) -> str:')
lines.append('    return _sha((')
lines.append('        program.declarations, program.resources, program.local_type_names,')
lines.append('        program.structs, program.uniform_blocks, program.interface_symbols,')
lines.append('        program.builtin_symbols, program.preprocessor_defines,')
lines.append('    ))')
lines.append('')
lines.append('')

# _LOCKS dict
lines.append('_LOCKS = {')
for k in LUMA_KEYS:
    entry = d[k]
    decl = next(x for x in entry["declarations"] if x["name"] == "LUMA_WEIGHTS")
    reads = entry["luma_weight_reads"]
    lines.append(f'    {pyrepr(k)}: {{')
    lines.append(f'        "profile": {pyrepr("grade-" + SHORT[k] + "-luma-weights-v1")},')
    lines.append(f'        "raw_bytes": {entry["raw_bytes"]},')
    lines.append(f'        "raw_sha256": {pyrepr(entry["raw_sha256"])},')
    lines.append(f'        "normalized_bytes": {entry["normalized_bytes"]},')
    lines.append(f'        "normalized_sha256": {pyrepr(entry["normalized_sha256"])},')
    lines.append(f'        "whole_sha256": {pyrepr(entry["whole_sha256"])},')
    lines.append(f'        "interface_sha256": {pyrepr(entry["interface_sha256"])},')
    lines.append(f'        "functions_sha256": {pyrepr(entry["functions_sha256"])},')
    lines.append(f'        "num_declarations": {entry["num_declarations"]},')
    lines.append(f'        "declaration_index": {decl["index"]},')
    lines.append(f'        "symbol_id": {decl["symbol_id"]},')
    lines.append(f'        "declaration_span": {pyrepr(decl["span"])},')
    lines.append(f'        "declaration_sha256": {pyrepr(decl["sha256"])},')
    lines.append(f'        "initializer_span": {pyrepr(decl["initializer_span"])},')
    lines.append(f'        "initializer_sha256": {pyrepr(decl["initializer_sha256"])},')
    lines.append(f'        "lanes": (')
    for lane in decl["lanes"]:
        lines.append(f'            ({pyrepr(lane["literal"])}, {lane["value"]}, {pyrepr(lane["span"])}, {pyrepr(lane["sha256"])}),')
    lines.append(f'        ),')
    lines.append(f'        "reads": (')
    for r in reads:
        lines.append(f'            ({r["function_id"]}, {pyrepr(r["function_name"])}, {pyrepr(r["span"])}, {pyrepr(r["sha256"])}),')
    lines.append(f'        ),')
    lines.append(f'    }},')
lines.append('}')

with open('docs/port-engineering/grade_luma_weights_locks.py.txt', 'w') as f:
    f.write("\n".join(lines))
print("wrote", len(lines), "lines")
