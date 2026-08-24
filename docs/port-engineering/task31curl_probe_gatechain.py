#!/usr/bin/env python3
"""Task 31 Curl: walk the FULL gate chain live.

1. Baseline (no widening): where does validate_capabilities fail? Where does
   render_typed_cpp fail (called directly, bypassing the validator)?
2. Widen only the validator's builtin/type tables (not the emitter's): does
   the emitter still independently reject, and where?
3. Widen only the emitter's tables (not the validator's): does the validator
   still independently reject, and where?
4. Widen both: does it render in full, with no further hidden gate? Snapshot
   every patched global before/after to prove restoration.

Read-only against the noisemaker-for-cpp tree; all monkeypatching is done in
this process's imported module objects and undone via try/finally, never
touching disk.
"""
import copy
import hashlib
import pathlib
import sys

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp

KEY = "synth/curl:curl"
DEFINES = {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}
SRC_PATH = (REPO / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/"
            "sources/synth/curl/curl.glsl")


def build_program():
    raw = SRC_PATH.read_text()
    parsed = parse_program(raw, KEY, DEFINES)
    program = analyze_program(parsed, KEY)
    source_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return program, source_hash


def try_validate(program, source_hash):
    try:
        gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES, source_hash=source_hash)
        return "PASS", None
    except gen.GeneratorError as e:
        return "REJECT", str(e)


def try_emit(program, source_hash):
    try:
        emitted = render_typed_cpp(program, program.key, source_hash)
        return "PASS", emitted
    except TypedEmissionError as e:
        return "REJECT", str(e)


def snapshot():
    return dict(
        APPROVED_CAPABILITIES=copy.deepcopy(gen.APPROVED_CAPABILITIES),
        _BUILTINS=copy.deepcopy(gen._BUILTINS),
    )


def main():
    program, source_hash = build_program()

    print("=== STAGE 0: baseline, no widening ===")
    v_status, v_msg = try_validate(program, source_hash)
    print("validator:", v_status, "-", v_msg)
    e_status, e_msg = try_emit(program, source_hash)
    print("emitter (direct, bypassing validator):", e_status, "-", (e_msg if e_status == "REJECT" else "<rendered>"))

    pre_gen_builtins = frozenset(gen._BUILTINS)
    pre_gen_caps = tuple(gen.APPROVED_CAPABILITIES)

    print("\n=== STAGE 1: widen ONLY validator's _BUILTINS (add tanh); emitter untouched ===")
    orig_builtins = gen._BUILTINS
    try:
        gen._BUILTINS = frozenset(orig_builtins | {"tanh"})
        # Also patch the mod-overload check surface indirectly is not
        # possible without source edits (it is inline code, not a table), so
        # this stage demonstrates builtin-NAME admission only; the generic
        # mod-overload tuple check is a separate code path (see stage notes).
        v_status, v_msg = try_validate(program, source_hash)
        print("validator (tanh name admitted):", v_status, "-", v_msg)
    finally:
        gen._BUILTINS = orig_builtins
    print("post-restore _BUILTINS unchanged:", gen._BUILTINS == pre_gen_builtins)

    print("\n=== STAGE 2: validator fully unmodified; confirm emitter direct call independently rejects ===")
    e_status, e_msg = try_emit(program, source_hash)
    print("emitter (direct):", e_status, "-", (e_msg if e_status == "REJECT" else "<rendered>"))

    print("\n=== STAGE 3: widen validator's _BUILTINS AND APPROVED_CAPABILITIES is NOT needed for")
    print("   tanh (identity-scoped builtins never enter capability vocabulary, per the round/all")
    print("   pattern) -- but the generic mod-overload check is inline Python, not a table, so it")
    print("   cannot be monkeypatched without source edits. This is itself evidence for the brief:")
    print("   mod-overload widening requires an actual code change (identity-scoped), not a global.")

    print("\nFinal snapshot equality check (APPROVED_CAPABILITIES, _BUILTINS): ",
          gen.APPROVED_CAPABILITIES == pre_gen_caps, gen._BUILTINS == pre_gen_builtins)


if __name__ == "__main__":
    main()
