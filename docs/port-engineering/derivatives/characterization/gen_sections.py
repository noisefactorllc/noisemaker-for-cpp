#!/usr/bin/env python3
"""Generate the per-program markdown sections from derivative-program-facts.json.
Read-only; writes only into this characterization/ directory."""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
facts = json.loads((HERE / "derivative-program-facts.json").read_text())


def fmt_span(s):
    if s["start_line"] == s["end_line"]:
        return f"{s['start_line']}:{s['start_column']}-{s['end_column']}"
    return f"{s['start_line']}:{s['start_column']}-{s['end_line']}:{s['end_column']}"


def guard_text(site):
    if site["unconditional"]:
        return "unconditional"
    parts = []
    for g in site["guard_stack"]:
        ids = ", ".join(f"{n}({s})" for n, s in g["identifiers"])
        safety = "frame-constant" if g["frame_constant"] else "**PER-PIXEL-VARYING (unsafe)**"
        parts.append(f"{g['branch']}-branch of `if` on [{ids}] -> {safety}")
    return "; ".join(parts)


out = []
for key in facts["programs"]:
    v = facts["programs"][key]
    entry = v["manifest_entry"]
    out.append(f"### `{key}`\n")
    out.append(f"- Source: `{entry['source']}` ({entry['raw_bytes']} raw bytes, "
                f"sha256 `{entry['raw_sha256']}`; {entry['normalized_bytes']} normalized bytes, "
                f"sha256 `{entry['normalized_sha256']}`)\n")
    out.append(f"- Authorized define map (`_defaults`): `{json.dumps(v['authorized_defines'])}`\n")
    r = v["resources"]
    out.append("- **Expected resources tuple** (gate field order: uniforms, samplers, outputs, "
                "uses_texture, uses_derivatives):\n")
    out.append("  ```python\n"
                f"  ({tuple(r['uniforms'])!r},\n"
                f"   {tuple(r['samplers'])!r},\n"
                f"   {tuple(r['outputs'])!r},\n"
                f"   {r['uses_texture']!r}, {r['uses_derivatives']!r})\n"
                "  ```\n")
    out.append(f"- Declarations: {len(v['declarations'])} globals; Functions: {len(v['function_profiles'])} "
                f"(`{', '.join(f['name'] for f in v['function_profiles'])}`)\n")
    out.append(f"- `local_type_names`: `{v['local_type_names']}`\n")
    out.append(f"- `structs`: `{v['structs']}` / `uniform_blocks`: `{v['uniform_blocks']}` "
                f"(both empty for all 17)\n")
    proof = v["counted_loop_proof"]
    out.append(f"- `counted_loop_proof`: loop_count={proof['loop_count']}, "
                f"unproved_loop_count={proof['unproved_loop_count']}, "
                f"max_effective_depth={proof['max_effective_depth']}, "
                f"max_lexical_product={proof['max_lexical_product']}, "
                f"entrypoint_charge={proof['entrypoint_charge']}, "
                f"call_graph_acyclic={proof['call_graph_acyclic']}\n")
    out.append(f"- Foreign proofs (fixed_nine/fixed_grid/fixed_array_in_parameter/fixed_affine_centers13): "
                f"all `None` -- {v['foreign_proofs_present']}\n")
    gh = v["gate_hashes"]
    out.append(f"- Gate hashes (computed from the CURRENT, unmodified frontend output -- stable "
                f"across the future vocabulary-admission fix, see note below): "
                f"`functions_sha256={gh['functions_sha256']}`, "
                f"`whole_sha256={gh['whole_sha256']}`, `interface_sha256={gh['interface_sha256']}`\n")
    out.append("\n**Derivative call sites:**\n\n")
    out.append("| # | builtin | arg type | enclosing fn | span (typed.source) | loop depth | guard |\n")
    out.append("|---|---------|----------|---------------|----------------------|------------|-------|\n")
    for i, s in enumerate(v["derivative_call_sites"]):
        out.append(f"| {i} | `{s['builtin']}` | `{s['arg_type']}` | `{s['enclosing_function']}` | "
                    f"{fmt_span(s['span'])} | {s['enclosing_loop_depth']} | {guard_text(s)} |\n")
    vbd = v["validator_beyond_derivatives"]
    verdict = "CLEAN -- no other blocker" if vbd["clean"] else f"OTHER BLOCKER: `{vbd['error']}`"
    out.append(f"\n**validate_capabilities() beyond derivatives:** {verdict}\n\n")
    out.append("---\n\n")

(HERE / "_sections.md").write_text("".join(out), encoding="utf-8")
print("wrote _sections.md")
