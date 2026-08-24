"""Second-order probe for the 'unsupported counted-for program proof' /
'unsupported counted-for safety charge' family (22 keys).

Read-only: parses+analyzes each program with the real frontend, then calls
the real (unmodified) tools.glslcpp.frontend.loop_proof machinery --
attach_counted_loop_proofs / summarize_counted_loop_proofs -- to recompute the
exact CountedLoopProgramProof the validator itself would compute, and walks
every individual CountedLoopProof + every un-annotated for/while/dowhile
statement to report, per key: WHY the proof fails (unbounded/non-canonical
loop shape making it "unproved", vs a proved loop that still blows a budget)
and the exact numbers against the exact budgets read out of
generate_typed_slice.py:
  - program-level (line ~1732-1735): unproved_loop_count>0, OR
    max_effective_depth>3, OR max_lexical_product>4096, OR
    entrypoint_charge>4096  => "unsupported counted-for program proof"
  - per-loop (line ~1570-1575, tighter): trip_count>128, OR
    lexical_depth>3, OR effective_depth>3, OR lexical_product>4096, OR
    entrypoint_charge>4096 => "unsupported counted-for safety charge"
  - call_graph_acyclic is False (recursion through the counted-loop call
    graph) => "unsupported counted-for program proof" (call-graph gate)

No monkeypatching is needed or attempted: these budgets are numeric
constants baked directly into generate_typed_slice.py's source, not flags in
gen.APPROVED_CAPABILITIES / gen._BUILTINS, so there is nothing to toggle --
admitting this family means literally raising those constants (or replacing
the whole-program aggregate check with a different rule), which is a design
decision to size, not a boolean to flip. This probe instead establishes HOW
FAR each program is over budget (or whether it's "unproved" for a structural
reason no budget increase would fix), which is exactly the sizing evidence a
real capability decision needs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp.frontend.loop_proof import (  # noqa: E402
    attach_counted_loop_proofs, summarize_counted_loop_proofs)

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = [
    "classicNoisedeck/effects:effects",
    "classicNoisedeck/fractal:fractal",
    "classicNoisedeck/noise:noise",
    "filter/blur:blurH",
    "filter/blur:blurV",
    "filter/dither:dither",
    "filter/lightLeak:lightLeak",
    "filter/median:median",
    "filter/normalize:statsFinal",
    "filter/oilPaint:oilFlatten",
    "filter/parallax:parallax",
    "filter/reindex:nmReindexReduce",
    "filter/reindex:nmReindexStats",
    "filter/smooth:smoothBlend",
    "filter/tetraColorArray:tetraColorArray",
    "filter/zoomBlur:zoomBlur",
    "synth/gabor:gabor",
    "synth/julia:julia",
    "synth/mandelbrot:mandelbrot",
    "synth/newton:newton",
    "synth/noise:noise",
    "synth/testPattern:testPattern",
]

PROGRAM_UNPROVED_MAX = 0
PROGRAM_DEPTH_MAX = 3
PROGRAM_PRODUCT_MAX = 4096
PROGRAM_CHARGE_MAX = 4096
LOOP_TRIP_MAX = 128
LOOP_DEPTH_MAX = 3
LOOP_PRODUCT_MAX = 4096
LOOP_CHARGE_MAX = 4096


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, typed


def walk_statements(function):
    def rec(statement, depth):
        yield statement, depth
        child_depth = depth + 1 if statement.kind == "for" and statement.loop_proof is not None else depth
        for child in statement.children:
            yield from rec(child, child_depth)
    for statement in function.body:
        yield from rec(statement, 0)


def loop_findings(functions):
    proved = []
    unproved = []
    for function in functions:
        for statement, _ in walk_statements(function):
            if statement.kind in {"for", "while", "dowhile"}:
                if statement.loop_proof is None:
                    unproved.append({
                        "function": function.name,
                        "kind": statement.kind,
                        "span": f"{statement.span.start_line}:{statement.span.start_column}",
                    })
                else:
                    proof = statement.loop_proof
                    over = []
                    if proof.trip_count > LOOP_TRIP_MAX:
                        over.append(f"trip_count={proof.trip_count}>{LOOP_TRIP_MAX}")
                    if proof.lexical_depth > LOOP_DEPTH_MAX:
                        over.append(f"lexical_depth={proof.lexical_depth}>{LOOP_DEPTH_MAX}")
                    if proof.effective_depth > LOOP_DEPTH_MAX:
                        over.append(f"effective_depth={proof.effective_depth}>{LOOP_DEPTH_MAX}")
                    if proof.lexical_product > LOOP_PRODUCT_MAX:
                        over.append(f"lexical_product={proof.lexical_product}>{LOOP_PRODUCT_MAX}")
                    if proof.entrypoint_charge > LOOP_CHARGE_MAX:
                        over.append(f"entrypoint_charge={proof.entrypoint_charge}>{LOOP_CHARGE_MAX}")
                    proved.append({
                        "function": function.name,
                        "span": f"{statement.span.start_line}:{statement.span.start_column}",
                        "bound_kind": proof.bound_kind,
                        "trip_count": proof.trip_count,
                        "lexical_depth": proof.lexical_depth,
                        "effective_depth": proof.effective_depth,
                        "lexical_product": proof.lexical_product,
                        "entrypoint_charge": proof.entrypoint_charge,
                        "over_budget": over,
                    })
    return proved, unproved


def classify(key: str) -> dict:
    entry, typed = load(key)
    functions = attach_counted_loop_proofs(typed.functions, key)
    summary = summarize_counted_loop_proofs(functions)
    proved, unproved = loop_findings(functions)

    reasons = []
    if not summary.call_graph_acyclic:
        reasons.append("call_graph_not_acyclic (recursion through counted-loop call graph)")
    if summary.unproved_loop_count:
        # Distinguish while/dowhile (never provable by this mechanism) from
        # for-loops whose shape doesn't match the narrow canonical pattern.
        kinds = sorted({item["kind"] for item in unproved})
        reasons.append(f"unproved_loop_count={summary.unproved_loop_count} (kinds={kinds})")
    if summary.max_effective_depth > PROGRAM_DEPTH_MAX:
        reasons.append(f"max_effective_depth={summary.max_effective_depth}>{PROGRAM_DEPTH_MAX}")
    if summary.max_lexical_product > PROGRAM_PRODUCT_MAX:
        reasons.append(f"max_lexical_product={summary.max_lexical_product}>{PROGRAM_PRODUCT_MAX}")
    if summary.entrypoint_charge > PROGRAM_CHARGE_MAX:
        reasons.append(f"entrypoint_charge={summary.entrypoint_charge}>{PROGRAM_CHARGE_MAX}")
    per_loop_over = [item for item in proved if item["over_budget"]]

    return {
        "key": key,
        "loop_count": summary.loop_count,
        "unproved_loop_count": summary.unproved_loop_count,
        "max_effective_depth": summary.max_effective_depth,
        "max_lexical_product": summary.max_lexical_product,
        "entrypoint_charge": summary.entrypoint_charge,
        "call_graph_acyclic": summary.call_graph_acyclic,
        "program_level_reasons": reasons,
        "unproved_loops": unproved,
        "per_loop_over_budget": per_loop_over,
    }


def main() -> int:
    rows = [classify(key) for key in KEYS]

    # Bucket each key by its DOMINANT reason (first reason in program_level_reasons,
    # which mirrors the order the real validator's own if-chain checks them:
    # call-graph, then unproved-loop-count, then the three numeric budgets).
    def dominant(row: dict) -> str:
        if not row["call_graph_acyclic"]:
            return "recursion (call graph not acyclic)"
        if row["unproved_loop_count"]:
            kinds = set()
            for item in row["unproved_loops"]:
                kinds.add(item["kind"])
            if kinds == {"while"} or kinds == {"dowhile"} or kinds == {"while", "dowhile"}:
                return "unproved: while/dowhile loop (mechanism only proves canonical for-loops)"
            return "unproved: non-canonical for-loop shape (bound not literal/local-const/reverb-clamp, or body has return, etc.)"
        overs = []
        if row["max_effective_depth"] > PROGRAM_DEPTH_MAX:
            overs.append("depth")
        if row["max_lexical_product"] > PROGRAM_PRODUCT_MAX:
            overs.append("lexical_product")
        if row["entrypoint_charge"] > PROGRAM_CHARGE_MAX:
            overs.append("entrypoint_charge")
        if overs:
            return "over budget: " + "+".join(overs)
        if row["per_loop_over_budget"]:
            return "over budget: per-loop safety-charge only (program aggregate is fine)"
        return "NO REASON FOUND -- inconsistent with census (should not happen)"

    tag_counts: dict[str, int] = {}
    for row in rows:
        tag = dominant(row)
        row["dominant_reason"] = tag
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    out = {
        "family": "unsupported counted-for program proof / safety charge",
        "member_count": len(KEYS),
        "budgets": {
            "program_level": {
                "unproved_loop_count_max": PROGRAM_UNPROVED_MAX,
                "max_effective_depth_max": PROGRAM_DEPTH_MAX,
                "max_lexical_product_max": PROGRAM_PRODUCT_MAX,
                "entrypoint_charge_max": PROGRAM_CHARGE_MAX,
            },
            "per_loop_safety_charge": {
                "trip_count_max": LOOP_TRIP_MAX,
                "lexical_depth_max": LOOP_DEPTH_MAX,
                "effective_depth_max": LOOP_DEPTH_MAX,
                "lexical_product_max": LOOP_PRODUCT_MAX,
                "entrypoint_charge_max": LOOP_CHARGE_MAX,
            },
        },
        "dominant_reason_distribution": tag_counts,
        "rows": rows,
    }
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
