"""Task 32, task 5: projected post-task state if all four round-family
candidates (filter/fxaa:fxaa, filter/grain:grain, filter/normalMap:normalMap,
filter/snow:snow) were added to typed_slice.json.

This is a hypothetical requested explicitly by the task ("if all four
land") -- it does NOT imply all four are actually validated-ready; see
gate-chain-output.json and reachability-output.json for the evidence that
only filter/fxaa:fxaa clears the full mechanical gate chain with a live,
reachable round() site, and even that one is not full-render discriminable
for the round hazard specifically (see round-semantics-output.json).

Method:
  - typed_keys = current tools/glslcpp/typed_slice.json programs, sorted.
  - projected_typed_keys = typed_keys + the 4 candidate keys, sorted.
  - public = sorted(typed + ("filter/invert:inv", "synth/solid:solid")),
    per tests/test_typed_generator.py's own formula (grepped, not assumed).
  - typed-list hash = sha256(newline-joined sorted typed keys + trailing
    newline) -- reproduces the exact recipe implied by the task's stated
    current hash, verified below against the given
    ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2.
  - public-list hash computed the same way.
  - ordinal = zero-based index in the sorted typed list (this is the
    generated `typed_NN` namespace ordinal per task-31-ordinal-blast-
    radius.md's documented convention).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(".")

GIVEN_CURRENT_HASH = "ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2"

CANDIDATE_KEYS = [
    "filter/fxaa:fxaa",
    "filter/grain:grain",
    "filter/normalMap:normalMap",
    "filter/snow:snow",
]

PUBLIC_EXTRA = ("filter/invert:inv", "synth/solid:solid")


def sha256_of_sorted_list(keys: list[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(keys)) + "\n").encode()).hexdigest()


def main() -> int:
    slice_data = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text())
    current_typed = sorted(p["program_key"] for p in slice_data["programs"])
    current_hash = sha256_of_sorted_list(current_typed)
    assert current_hash == GIVEN_CURRENT_HASH, (current_hash, GIVEN_CURRENT_HASH)

    manifest = json.loads((ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/manifest.json").read_text())
    corpus_count = len(manifest["programs"])

    current_public = sorted((*current_typed, *PUBLIC_EXTRA))
    current_unported = corpus_count - len(current_public)

    assert not (set(CANDIDATE_KEYS) & set(current_typed)), "candidate already typed"

    projected_typed = sorted((*current_typed, *CANDIDATE_KEYS))
    projected_public = sorted((*projected_typed, *PUBLIC_EXTRA))
    projected_unported = corpus_count - len(projected_public)

    projected_typed_hash = sha256_of_sorted_list(projected_typed)
    projected_public_hash = sha256_of_sorted_list(projected_public)

    ordinals = {}
    for key in CANDIDATE_KEYS:
        idx = projected_typed.index(key)
        before = projected_typed[idx - 1] if idx > 0 else None
        after = projected_typed[idx + 1] if idx + 1 < len(projected_typed) else None
        ordinals[key] = {
            "zero_based_typed_ordinal": idx,
            "namespace": f"typed_{idx}",
            "neighbour_before": before,
            "neighbour_after": after,
        }

    # Also report every EXISTING key whose ordinal shifts (any key that
    # sorts after any of the 4 new insertion points moves up by however many
    # of the 4 candidates sort before it).
    shifted = []
    for old_idx, key in enumerate(current_typed):
        new_idx = projected_typed.index(key)
        if new_idx != old_idx:
            shifted.append({"key": key, "old_ordinal": old_idx, "new_ordinal": new_idx,
                            "delta": new_idx - old_idx})

    payload = {
        "schema": "noisemaker-for-cpp.task32.projected-state.v1",
        "current_state": {
            "typed_count": len(current_typed),
            "typed_sorted_sha256": current_hash,
            "public_count": len(current_public),
            "unported_count": current_unported,
            "corpus_count": corpus_count,
        },
        "candidate_keys_added": CANDIDATE_KEYS,
        "projected_state_if_all_four_land": {
            "typed_count": len(projected_typed),
            "typed_sorted_sha256": projected_typed_hash,
            "public_count": len(projected_public),
            "unported_count": projected_unported,
            "corpus_count": corpus_count,
        },
        "candidate_ordinals": ordinals,
        "existing_keys_with_shifted_ordinal_count": len(shifted),
        "existing_keys_with_shifted_ordinal": shifted,
        "warning": "This is the hypothetical the task explicitly requested ('if all four land'). Per gate-chain-output.json and reachability-output.json, only filter/fxaa:fxaa actually clears validator+emitter AND has a live/reachable round() site under const-global+round admission alone; grain needs an additional uvec3>>uvec3 capability, normalMap needs const-array-of-vector global admission (a materially larger scope than the const-global generalization tested here), and snow's only round() call site is unreachable dead code (as_u32 is never called from main), disqualifying it from full-render-parity validation regardless of whether it type-checks.",
    }
    out = Path(__file__).with_name("projected-state-output.json")
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
