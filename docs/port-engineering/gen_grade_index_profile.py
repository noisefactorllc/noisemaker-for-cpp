import json

d = json.load(open('docs/port-engineering/task32_probe_output.json'))

INDEX_KEYS = ["filter/grade:creative", "filter/grade:hslSecondary", "filter/grade:lut",
              "filter/grade:primary", "filter/grade:vignette", "filter/grade:wheels"]
SHORT = {
    "filter/grade:creative": "creative",
    "filter/grade:hslSecondary": "hslsecondary",
    "filter/grade:lut": "lut",
    "filter/grade:primary": "primary",
    "filter/grade:vignette": "vignette",
    "filter/grade:wheels": "wheels",
}

def pyrepr(s):
    return repr(s)

lines = []
lines.append('_LOCKS = {')
for k in INDEX_KEYS:
    entry = d[k]
    sites = entry["index_sites"]
    lines.append(f'    {pyrepr(k)}: {{')
    lines.append(f'        "profile": {pyrepr("grade-" + SHORT[k] + "-index-expression-v1")},')
    lines.append(f'        "raw_bytes": {entry["raw_bytes"]},')
    lines.append(f'        "raw_sha256": {pyrepr(entry["raw_sha256"])},')
    lines.append(f'        "normalized_bytes": {entry["normalized_bytes"]},')
    lines.append(f'        "normalized_sha256": {pyrepr(entry["normalized_sha256"])},')
    lines.append(f'        "whole_sha256": {pyrepr(entry["whole_sha256"])},')
    lines.append(f'        "interface_sha256": {pyrepr(entry["interface_sha256"])},')
    lines.append(f'        "functions_sha256": {pyrepr(entry["functions_sha256"])},')
    lines.append(f'        "sites": (')
    for s in sites:
        lines.append(
            f'            ({s["function_id"]}, {pyrepr(s["function_name"])}, {pyrepr(s["span"])}, '
            f'{pyrepr(s["sha256"])}, {pyrepr(s["role"])}, {s["base_symbol_id"]}, {pyrepr(s["base_name"])}, '
            f'{pyrepr(s["base_storage"])}, '
            f'{s["index_symbol_id"]}, {pyrepr(s["index_name"])}),'
        )
    lines.append(f'        ),')
    lines.append(f'    }},')
lines.append('}')

with open('docs/port-engineering/grade_index_expression_locks.py.txt', 'w') as f:
    f.write("\n".join(lines))
print("wrote", len(lines), "lines")
