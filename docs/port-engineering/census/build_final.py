"""Assemble frontier-census.json from the raw census + supplementary probes.

Read-only synthesis step; writes only under docs/port-engineering/census/.
"""
from __future__ import annotations
import json, pathlib

BASE = pathlib.Path("docs/port-engineering/census")
raw = json.loads((BASE / "raw_census.json").read_text())
rows = {r["key"]: r for r in raw["rows"]}
global_decl = {r["key"]: r for r in json.loads((BASE / "global_decl_probe.json").read_text())}
relaxed_global = {r["key"]: r for r in json.loads((BASE / "relaxed_global_probe.json").read_text())}
bitwise_sites = json.loads((BASE / "bitwise_sites_probe.json").read_text())
relaxed2 = {r["key"]: r for r in json.loads((BASE / "relaxed2_mat3_probe.json").read_text())}
relaxed3 = {r["key"]: r for r in json.loads((BASE / "relaxed3_mat3_probe.json").read_text())}

GRADE_KEYS = [
    "filter/grade:creative", "filter/grade:hslSecondary", "filter/grade:lut",
    "filter/grade:primary", "filter/grade:vignette", "filter/grade:wheels",
]

LOOP_TERMINAL_16 = {
    "classicNoisedeck/fractal:fractal", "filter/blur:blurH", "filter/blur:blurV",
    "filter/dither:dither", "filter/lightLeak:lightLeak", "filter/normalize:statsFinal",
    "filter/oilPaint:oilFlatten", "filter/parallax:parallax",
    "filter/reindex:nmReindexReduce", "filter/reindex:nmReindexStats",
    "filter/smooth:smoothBlend", "filter/tetraColorArray:tetraColorArray",
    "filter/zoomBlur:zoomBlur", "synth/mandelbrot:mandelbrot",
    "synth/noise:noise", "synth/testPattern:testPattern",
}

BITOPS_DEAD_5 = {
    "classicNoisedeck/caustic:caustic", "classicNoisedeck/effects:effects",
    "classicNoisedeck/moodscape:moodscape", "classicNoisedeck/noise:noise",
    "synth/noise:noise",
}

MATRIX_9_CANDIDATES = {
    "classicNoisedeck/cellNoise:cellNoise", "classicNoisedeck/colorLab:colorLab",
    "classicNoisedeck/effects:effects", "classicNoisedeck/glitch:glitch",
    "classicNoisedeck/moodscape:moodscape", "classicNoisedeck/noise:noise",
    "classicNoisedeck/shapes:shapes", "filter/adjust:adjust", "filter/colorspace:colorspace",
}
MATRIX_6_REAL_TARGETS = {
    "classicNoisedeck/cellNoise:cellNoise", "classicNoisedeck/colorLab:colorLab",
    "classicNoisedeck/shapes:shapes", "filter/adjust:adjust",
    "filter/colorspace:colorspace", "classicNoisedeck/glitch:glitch",
}


def tail(msg):
    if msg is None or msg == "pass":
        return msg
    return msg.rsplit(": ", 1)[-1]


def cluster_for(key: str, r: dict) -> tuple[str, list[str], str, str]:
    """Returns (cluster, downstream_blockers, reachable, unlock_cost)."""
    v = r["validator"]
    t = tail(v)

    if v == "pass":
        return ("Zero-blocker (administrative only)", [], "n/a - fully valid",
                "FREE: parse+validate+emit all PASS today; needs only a typed_slice.json row + digest")

    if t == "unsupported builtin dFdx" or t == "unsupported builtin fwidth":
        return ("Derivatives (dFdx/dFdy/fwidth)", [], "yes (BFS-confirmed reachable)",
                "FREE once derivatives mechanism ships (prototype closed 2196/2196 exact; "
                "15-program integration characterized)")

    if t == "unsupported builtin round":
        return ("Builtin admission: round", ["derivatives (fwidth, reachable)"], "yes",
                "Bespoke: needs round() node-identity admission scoped to this call site, "
                "THEN derivatives mechanism")

    if t == "unsupported builtin any":
        return ("Builtin admission: any", ["derivatives (dFdx/dFdy, reachable)"], "yes",
                "Bespoke: any() has zero existing admission path anywhere in the generator; "
                "needs new node-identity admission, THEN derivatives mechanism")

    if t == "unsupported builtin reflect":
        return ("Builtin admission: reflect", [], "yes",
                "Bespoke: reflect() has zero existing admission path; likely cheap "
                "(same node-identity pattern as round/tanh/any) but unbuilt")

    if t == "unsupported counted-for program proof":
        in16 = key in LOOP_TERMINAL_16
        note = ("Loop-proof cluster's characterized 16" if in16 else
                "SAME failure signature (unproved loop, non-cyclic) as the characterized 16, "
                "but ABSENT from that study's terminal_16 list -- flagged as a gap")
        cost = ("Mechanical: per-shape fix already designed by the loop-proof study" if in16 else
                "Uncertain: same mechanism class, but not yet triaged into a shape group by "
                "any prior document; needs the same treatment as the 16")
        if key == "filter/median:median":
            cost = ("Hard: while-loop quickselect, explicitly flagged 'not soundly provable "
                    "statically' -- no known mechanism")
        return ("Loop-proof (program-proof gate)", [], note, cost)

    if t == "unsupported counted-for safety charge":
        return ("Loop-proof (safety-charge / per-loop budget gate)", [],
                "yes (acyclic, single over-budget loop)",
                "Budget-cap increase or bespoke bound proof (gabor: depth cap 4>3; "
                "julia/newton: trip_count/entrypoint_charge over cap -- NEWLY characterized here, "
                "absent from all prior loop-proof docs)")

    if t == "unsupported binary operator ^" and "bitwise" in key:
        return ("Bitwise (clean)", [], "yes",
                "Bespoke: needs the signed-arithmetic >> family plus XOR admission; "
                "sole program blocked ONLY on bitwise")

    if t == "unsupported global declaration":
        g = global_decl.get(key, {})
        rel = relaxed_global.get(key, {})
        next_blocker = rel.get("next_after_relaxed_global_admission")
        type_display = g.get("type_display")
        family = "?"
        if g.get("storage") == "global":
            family = f"non-const mutable global scratch ({type_display})"
        elif type_display == "mat3":
            family = "matrix (const global mat3 'fwdA')"
        elif type_display in ("int", "uint") and g.get("storage") == "const":
            family = f"const scalar table ({type_display})"
        elif type_display == "vec3":
            family = "const vector table (vec3)"
        elif "[" in str(type_display):
            family = f"const/array table ({type_display})"
        downstream = [next_blocker] if next_blocker and next_blocker != "VALIDATOR-PASS" else []
        if next_blocker == "VALIDATOR-PASS":
            emitter_after = rel.get("emitter_after_relaxed")
            downstream = [f"validator PASS after relaxed global admission; emitter: {emitter_after}"]
        in_matrix_9 = key in MATRIX_9_CANDIDATES
        in_matrix_6 = key in MATRIX_6_REAL_TARGETS
        note = ""
        if family.startswith("matrix"):
            note = (" [matrix-dispatch cluster member; " +
                     ("one of the prior study's 6 real targets" if in_matrix_6 else
                      "prior study's 3 dead-code exclusions" if key in {"classicNoisedeck/moodscape:moodscape"} else
                      "NOT in the prior study's 9-candidate list at all -- new finding") + "]")
        cluster = f"Global declaration: {family}{note}"
        cost = "Bespoke, multi-gate: NONE of the 25 land from a single admission (verified by relaxed-probe chaining); each needs 2-4 additional distinct fixes"
        return (cluster, downstream, "n/a (declaration exists unconditionally; not control-flow gated)", cost)

    if t == "unsupported varying":
        if key == "filter/wormhole:deposit":
            return ("STRUCTURALLY INELIGIBLE (varying: vColor)", [], "n/a",
                    "Likely never portable under the current per-pixel kernel architecture; "
                    "see structural-ineligibility finding")
        return ("Varying admission (v_texCoord)", [], "yes",
                "New mechanism (zero existing admission path for ANY varying); "
                "grime lands to floatBitsToUint next, not fully free")

    if t == "exact Caustic word hash profile carrier required":
        return ("Caustic word-hash profile (bespoke, mostly built)", [], "no (dead at NOISE_TYPE default per bitops study)",
                "Cheap-ish: authenticate_caustic_word_hash() already implemented; needs slice-row wiring, "
                "but functionally dead code once landed")

    if t == "unsupported typed type mat4":
        return ("Matrix (mat4 / chained-product, glitch)", [], "yes",
                "Part of the matrix-dispatch cluster's slice C (chained T*Q*S product, "
                "double-accumulation narrowing hazard); 1 of the 6 real targets")

    if t == "unsupported sampler parameter":
        return ("Sampler-as-parameter (distortion)", ["derivatives (dFdx/dFdy, reachable)", "reflect (reachable)"], "yes",
                "Bespoke: passing a sampler2D as a function argument is unsupported; "
                "CONTRADICTS prior roadmap claim that distortion is blocked on local arrays")

    if t == "unsupported parameter direction inout":
        return ("inout parameter direction (watercolor)", [], "yes",
                "Bespoke, singleton: no other program needs inout parameters")

    if t == "unsupported uniform block":
        return ("Uniform block (remap)", [], "yes",
                "Bespoke, singleton: no other program declares a GLSL uniform block")

    return (f"UNCLASSIFIED: {t}", [], "unknown", "not determined")


def main():
    out_rows = []
    for key in sorted(rows):
        r = rows[key]
        cluster, downstream, reachable, cost = cluster_for(key, r)
        bw = bitwise_sites.get(key)
        out_rows.append({
            "program_key": key,
            "terminal_blocker": r["validator"] if r["validator"] != "pass" else "PASS (no blocker)",
            "cluster": cluster,
            "downstream_blockers": downstream,
            "reachable": reachable,
            "unlock_cost": cost,
            "touches_bitwise_ops": bool(bw),
            "bitwise_reachable": bw["any_reachable"] if bw else None,
            "bitwise_dead_confirmed": key in BITOPS_DEAD_5,
            "raw_sha256": r["raw_sha256"],
            "defines": r["defines"],
            "structs": r["structs"], "uniform_blocks": r["uniform_blocks"],
            "interface_symbols": r["interface_symbols"],
        })
    for key in sorted(GRADE_KEYS):
        out_rows.append({
            "program_key": key,
            "terminal_blocker": "LANDED (in typed_slice.json as of this census)",
            "cluster": "Grade (landed)",
            "downstream_blockers": [],
            "reachable": "n/a",
            "unlock_cost": "DONE",
            "raw_sha256": None, "defines": None,
            "structs": None, "uniform_blocks": None, "interface_symbols": None,
        })
    assert len(out_rows) == 81, len(out_rows)

    from collections import Counter
    cluster_counts = Counter(r["cluster"] for r in out_rows)

    payload = {
        "schema": "noisemaker-for-cpp.frontier-census.v1",
        "generated_from_snapshot": raw["snapshot_ts"],
        "corpus_revision": raw["revision"],
        "corpus_total": raw["corpus_total"],
        "unported_total": 81,
        "rows": out_rows,
        "cluster_counts": dict(cluster_counts.most_common()),
    }
    (BASE / "frontier-census.json").write_text(json.dumps(payload, indent=1, sort_keys=True))
    print("wrote frontier-census.json,", len(out_rows), "rows")
    for c, n in cluster_counts.most_common():
        print(f"  {n:3d}  {c}")


if __name__ == "__main__":
    main()
