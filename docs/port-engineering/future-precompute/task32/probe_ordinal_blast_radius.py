"""Task 32, task 6: ordinal blast radius of inserting the four round-family
candidates (filter/fxaa:fxaa, filter/grain:grain, filter/normalMap:normalMap,
filter/snow:snow) into typed_slice.json, following the method of
docs/port-engineering/task-31-ordinal-blast-radius.md: locate every
hardcoded `typed_NN` / `typed.index(...)` assertion in
tests/test_typed_generator.py, determine what LIVE view each one operates
over (full spec, or a named-exclusion-filtered subset -- these tests never
filter by "the N most recently added", always by an explicit fixed key
name list, so future additions are NOT automatically excluded), and compute
what each assertion's value is (a) actually, on the live tree, today, and
(b) after hypothetically inserting the 4 new candidate keys.

Also surfaces, as a byproduct and NOT the primary deliverable, that several
of these tests' hardcoded values are ALREADY inconsistent with the live
131-typed tree (short by exactly one entry -- synth/curl:curl, Task 31's
actual landed addition, is not reflected in some of these hardcoded
tuples/hashes). This predates this task, is independent of it, and this
script does not modify anything to "fix" it -- it is reported as observed
context because it affects how to read "current vs projected" deltas below.

Read-only: only generate_typed_slice.load_slice() is called (real
production code, not pytest), matching the technique already used
throughout this task's other probes. No test is executed via pytest/unittest
runners.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402

CANDIDATE_KEYS = [
    "filter/fxaa:fxaa",
    "filter/grain:grain",
    "filter/normalMap:normalMap",
    "filter/snow:snow",
]

EXCLUSION_SETS = {
    "none (full live spec)": frozenset(),
    "3-key {rotate:rot, focusBlur, extrude}": frozenset({
        "filter/rotate:rot", "mixer/focusBlur:focusBlur", "filter/extrude:extrude"}),
    "5-key {smoothEdge, perlin, rotate:rot, focusBlur, extrude}": frozenset({
        "filter/smooth:smoothEdge", "synth/perlin:perlin", "filter/rotate:rot",
        "mixer/focusBlur:focusBlur", "filter/extrude:extrude"}),
}

# Every hardcoded typed_NN / typed.index(...) site found by
# `grep -noE "typed_[0-9]+" tests/test_typed_generator.py | sort -t_ -k2 -n -u`
# and `grep -n "typed\.index(\|assertEqual([0-9]*, typed\."`, with the
# governing test function and its exclusion-set view determined by reading
# each test's source.
SITES = [
    {"line": 1362, "test": "test_task24_resource_contract_is_mechanical_and_mutation_closed",
     "hardcoded_ordinal": 53, "key": "filter/pixelSort:gatherSorted",
     "view": "none (full live spec)",
     "note": "embedded binder source string 'typed_53::State'; reads the on-disk src/typed_generated/typed_slice.cpp directly, not a fresh regeneration"},
    {"line": 7607, "test": "test_task21_degauss_exclusions_remain_closed",
     "hardcoded_ordinal": 22, "key": "filter/degauss:degauss",
     "view": "none (full live spec)",
     "note": "namespace-string assertion against a fresh full-spec generate_outputs() call (not the 3-key-excluded `keys` list used earlier in the same test for neighbour assertions)"},
    {"line": 9041, "test": "test_task27ish_lens_prismatic_literal_vec3_census (5-key view)",
     "hardcoded_ordinal": 2, "key": "classicNoisedeck/lensDistortion:lensDistortion",
     "view": "5-key {smoothEdge, perlin, rotate:rot, focusBlur, extrude}", "note": "LENS_KEY"},
    {"line": 9042, "test": "test_task27ish_lens_prismatic_literal_vec3_census (5-key view)",
     "hardcoded_ordinal": 59, "key": "filter/prismaticAberration:prismaticAberration",
     "view": "5-key {smoothEdge, perlin, rotate:rot, focusBlur, extrude}", "note": "PRISMATIC_KEY"},
    {"line": 9043, "test": "test_task27ish_lens_prismatic_literal_vec3_census (5-key view, current)",
     "hardcoded_ordinal": 52, "key": "filter/pixelSort:gatherSorted",
     "view": "5-key {smoothEdge, perlin, rotate:rot, focusBlur, extrude}",
     "note": "'current_blocks' -- gatherSorted position AFTER Lens+Prismatic are present"},
    {"line": 9045, "test": "test_task27ish_lens_prismatic_literal_vec3_census (5-key view, prior)",
     "hardcoded_ordinal": 51, "key": "filter/pixelSort:gatherSorted",
     "view": "5-key {smoothEdge, perlin, rotate:rot, focusBlur, extrude} MINUS {lensDistortion, prismaticAberration}",
     "note": "'prior_blocks' -- historical-style subtraction of Lens+Prismatic specifically (frozen point-in-time; safe under later additions by the same logic as task-31's Caustic analysis, included here only for completeness)"},
    {"line": 11299, "test": "test_task26_loader_admits_only_exact_smooth_carrier_and_census",
     "hardcoded_ordinal": 77, "key": "filter/smooth:smoothEdge",
     "view": "3-key {rotate:rot, focusBlur, extrude}", "note": "SMOOTH_EDGE_KEY"},
    {"line": 11155, "test": "test_task26_loader_admits_only_exact_smooth_carrier_and_census (duplicate index assertion)",
     "hardcoded_ordinal": 77, "key": "filter/smooth:smoothEdge",
     "view": "3-key {rotate:rot, focusBlur, extrude}", "note": "same as above, typed.index() form"},
    {"line": 12255, "test": "test_task27_generation_is_exact_single_program_delta_from_task26",
     "hardcoded_ordinal": 123, "key": "synth/perlin:perlin",
     "view": "3-key {rotate:rot, focusBlur, extrude}", "note": "PERLIN_KEY"},
    {"line": 13976, "test": "test_task29_schema_counts_hashes_and_real_task28_reconstruction_isolation",
     "hardcoded_ordinal": 111, "key": "mixer/focusBlur:focusBlur",
     "view": "none (full live spec)", "note": "FOCUS_BLUR_KEY"},
    {"line": 14054, "test": "test_task29_cpp_tables_switch_helpers_and_witnesses_are_exact_frozen_transcription",
     "hardcoded_ordinal": 111, "key": "mixer/focusBlur:focusBlur",
     "view": "none (full live spec)", "note": "FOCUS_BLUR_KEY, same test family"},
    {"line": 14649, "test": "test_task30_history_coexistence_and_live_schema_matches_130_program_state",
     "hardcoded_ordinal": 25, "key": "filter/extrude:extrude",
     "view": "none (full live spec)", "note": "EXTRUDE_KEY, typed.index() form"},
    {"line": 14672, "test": "test_task30_history_coexistence_and_live_schema_matches_130_program_state",
     "hardcoded_ordinal": 25, "key": "filter/extrude:extrude",
     "view": "none (full live spec)", "note": "EXTRUDE_KEY, embedded namespace-string form, same test"},
]


def sorted_view(all_keys: list[str], exclusion: frozenset[str], extra: list[str] = ()) -> list[str]:
    kept = [k for k in all_keys if k not in exclusion]
    return sorted((*kept, *extra))


def main() -> int:
    spec = gen.load_slice(ROOT)
    all_keys = [item["program_key"] for item in spec["programs"]]
    assert all_keys == sorted(all_keys), "spec programs not sorted -- unexpected"
    assert not (set(CANDIDATE_KEYS) & set(all_keys))

    rows = []
    for site in SITES:
        is_prior_view = "MINUS" in site["view"]
        exclusion = (EXCLUSION_SETS["5-key {smoothEdge, perlin, rotate:rot, focusBlur, extrude}"]
                    if is_prior_view else EXCLUSION_SETS[site["view"]])
        if is_prior_view:
            # The one deliberately-historical row (line 9045): additionally
            # subtract Lens+Prismatic to reproduce that test's `prior_spec`.
            extra_exclusion = {"classicNoisedeck/lensDistortion:lensDistortion",
                               "filter/prismaticAberration:prismaticAberration"}
            live_view = sorted_view(all_keys, exclusion | extra_exclusion)
            projected_view = sorted_view(all_keys, exclusion | extra_exclusion, CANDIDATE_KEYS)
        else:
            live_view = sorted_view(all_keys, exclusion)
            projected_view = sorted_view(all_keys, exclusion, CANDIDATE_KEYS)

        key = site["key"]
        live_ordinal = live_view.index(key) if key in live_view else None
        projected_ordinal = projected_view.index(key) if key in projected_view else None

        rows.append({
            "line": site["line"],
            "test": site["test"],
            "key": key,
            "view": site["view"],
            "note": site["note"],
            "hardcoded_value_in_test": site["hardcoded_ordinal"],
            "live_actual_ordinal_today": live_ordinal,
            "already_stale_vs_hardcoded": live_ordinal != site["hardcoded_ordinal"],
            "projected_ordinal_after_4_insertions": projected_ordinal,
            "would_shift_due_to_candidate_insertion": (
                projected_ordinal != live_ordinal if live_ordinal is not None else None),
            "shift_delta_from_live": (
                (projected_ordinal - live_ordinal) if live_ordinal is not None else None),
        })

    # Full-spec count assertions (the "(N, N+2, unported, 212)" tuples) --
    # separately verified per view for completeness.
    corpus = json.loads((ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/manifest.json").read_text())
    corpus_count = len(corpus["programs"])
    count_rows = []
    for view_name, exclusion in EXCLUSION_SETS.items():
        live_view = sorted_view(all_keys, exclusion)
        projected_view = sorted_view(all_keys, exclusion, CANDIDATE_KEYS)
        count_rows.append({
            "view": view_name,
            "live_typed_count_today": len(live_view),
            "projected_typed_count_after_4_insertions": len(projected_view),
        })

    payload = {
        "schema": "noisemaker-for-cpp.task32.ordinal-blast-radius.v1",
        "method": "Reproduce each governing test's exact exclusion-set filter against the live gen.load_slice() output (not pytest), compute the key's ordinal in that filtered+sorted view today and after inserting the 4 candidate keys (never excluded by any of these named-key exclusion sets, since they don't exist yet), and diff against the hardcoded value written in the test source.",
        "candidate_keys": CANDIDATE_KEYS,
        "sites": rows,
        "count_tuple_context_per_view": count_rows,
        "caveat": "Several sites are ALREADY stale relative to the live 131-typed tree (short by exactly 1 -- synth/curl:curl, landed by Task 31, is present in typed_slice.json but several of these hardcoded count/hash/ordinal tuples were written before Curl landed and were not updated, because these tests filter by an explicit fixed key-name exclusion list rather than 'everything added after task N'). This is independent of and predates this task's hypothetical 4-program insertion; it is reported as observed evidence, not asserted as a root cause, and nothing was changed to address it (read-only mandate).",
    }
    out = Path(__file__).with_name("ordinal-blast-radius-output.json")
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
