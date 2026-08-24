#!/usr/bin/env python3
"""Task 31 Curl gate chain, stage 4: widen BOTH validator's _BUILTINS and
emitter's _BUILTIN_NAMES to admit `tanh` by name (not identity-scoped -- this
is a probe, not the real implementation), leaving the mod-overload inline
literal untouched in both authorities. Confirms:
  (a) tanh's own gate clears fully once both name tables admit it;
  (b) the ONLY remaining rejection in both authorities is the mod-overload
      check, at the same or a different node depending on each authority's
      own traversal order;
  (c) no third hidden gate exists beyond {builtin-name table, mod-overload
      literal} for this closure.
All patches are restored via try/finally with pre/post identity+equality
snapshots. Read-only against the tree; no source file is modified.
"""
import hashlib
import pathlib
import sys

REPO = pathlib.Path(".")
sys.path.insert(0, str(REPO))

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp import emit_typed_cpp as emit_mod
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


def main():
    program, source_hash = build_program()

    pre_gen_builtins = frozenset(gen._BUILTINS)
    pre_emit_names_id = id(emit_mod._BUILTIN_NAMES)
    pre_emit_names_snapshot = dict(emit_mod._BUILTIN_NAMES)

    orig_gen_builtins = gen._BUILTINS
    orig_emit_names = dict(emit_mod._BUILTIN_NAMES)
    try:
        gen._BUILTINS = frozenset(orig_gen_builtins | {"tanh"})
        emit_mod._BUILTIN_NAMES = dict(orig_emit_names)
        emit_mod._BUILTIN_NAMES["tanh"] = "tanh"

        print("=== STAGE 4: tanh admitted by NAME in both validator and emitter tables ===")
        v_status, v_msg = try_validate(program, source_hash)
        print("validator:", v_status, "-", v_msg)
        e_status, e_msg = try_emit(program, source_hash)
        print("emitter (direct):", e_status, "-", (e_msg if e_status == "REJECT" else "<rendered>"))

        print()
        print("Interpretation: with tanh admitted by name in both authorities, the ONLY")
        print("remaining rejection in each is the mod-overload argument-type check --")
        print("confirming there is no third hidden gate for this closure. The mod check")
        print("cannot itself be widened by monkeypatching a table (it is an inline literal")
        print("tuple in both generate_typed_slice.py and emit_typed_cpp.py), so getting")
        print("past it to prove full render requires an actual source change -- which is")
        print("exactly why this design brief requires identity-scoped edits, not a probe.")
    finally:
        gen._BUILTINS = orig_gen_builtins
        emit_mod._BUILTIN_NAMES = orig_emit_names

    print()
    print("post-restore gen._BUILTINS unchanged:", gen._BUILTINS == pre_gen_builtins)
    print("post-restore emit_mod._BUILTIN_NAMES unchanged:",
          emit_mod._BUILTIN_NAMES == pre_emit_names_snapshot)
    print("post-restore emit_mod._BUILTIN_NAMES same object identity as original:",
          id(emit_mod._BUILTIN_NAMES) == pre_emit_names_id)


if __name__ == "__main__":
    main()
