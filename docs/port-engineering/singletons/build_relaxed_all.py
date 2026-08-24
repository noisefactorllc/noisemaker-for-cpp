"""Builds a single aggressively-relaxed copy of generate_typed_slice.py inside
the read-only probe_tree (a plain `cp -R` snapshot of tools/glslcpp taken by
the triage agent; never the real tools/glslcpp).

Purpose: downstream-blocker discovery only. Each patch provisionally admits
exactly one class of construct that a specific singleton/cluster program is
known (from docs/port-engineering/census/frontier-census.json, itself
produced this same way -- see docs/port-engineering/census/probe_relaxed*.py)
to be rejected on, so that re-running the real validate_capabilities() walk
past that point reveals the NEXT real blocker. It does not imply any of these
admissions are a real, shippable mechanism -- most are almost certainly
separate bespoke work (mat3 vs mat4 vs uniform-block vs inout are unrelated
capabilities), exactly as documented in probe_relaxed_global.py's docstring.

Never writes under tools/, src/, include/, tests/, or CMakeLists.txt.
Never runs git.
"""
from __future__ import annotations

import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "probe_tree" / "tools" / "glslcpp" / "generate_typed_slice.py"
DST = HERE / "probe_tree" / "tools" / "glslcpp" / "generate_typed_slice_relaxed_all.py"

text = SRC.read_text()
original = text
patches = []


def apply(label: str, old: str, new: str) -> None:
    global text
    count = text.count(old)
    assert count == 1, f"{label}: expected exactly 1 occurrence, found {count}"
    text = text.replace(old, new, 1)
    patches.append(label)


# 1. mat3 / mat4 type admission (reject_type). Mirrors
#    census/probe_relaxed2_mat3.py's mat3 layer, extended to mat4 for glitch.
apply(
    "reject_type: admit mat3/mat4",
    '''    def reject_type(typ, value) -> None:
        if typ.kind == "array":''',
    '''    def reject_type(typ, value) -> None:
        if typ.display() in ("mat3", "mat4"):
            # RELAXED PROBE: provisionally admit as a typed type to find the
            # NEXT blocker behind it. Never used outside this read-only probe.
            return
        if typ.kind == "array":''',
)

# 2. Global declaration storage-class/type admission -- the FIRST, stricter
#    gate (const-float-chain only; everything else including mat3/mat4,
#    int/uint/vec3 consts, and mutable scratch globals like synth/shape's
#    hits this before ever reaching the second, redundant declarations-loop
#    gate below). Mirrors census/probe_relaxed.py's target gate.
apply(
    "global declaration (gate 1, const-float-chain only): admit any storage/type",
    '''        if storage != "const" or declaration.type != FLOAT or declaration.initializer is None:
            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")''',
    '''        if storage != "const" or declaration.type != FLOAT or declaration.initializer is None:
            # RELAXED PROBE: treat as provisionally admitted so downstream
            # blockers become visible. Never used outside this read-only
            # census-style probe; the real generator is untouched.
            admitted_globals[declaration.symbol.id] = declaration
            continue''',
)

# 2b. Global declaration storage-class admission -- the SECOND, redundant
#     gate (declarations loop further down). Mirrors census/probe_relaxed.py.
apply(
    "global declaration (gate 2, redundant declarations loop): admit any storage",
    '''        if declaration.symbol.storage not in {"uniform", "output", "const"}:
            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")''',
    '''        if declaration.symbol.storage not in {"uniform", "output", "const"}:
            # RELAXED PROBE: treat as provisionally admitted so downstream
            # blockers become visible. Never used outside this read-only
            # census-style probe; the real generator is untouched.
            admitted_globals[declaration.symbol.id] = declaration
            continue''',
)

# 2b. Global matrix declaration (fwdA-shaped const mat3/mat4 globals).
apply(
    "global matrix declaration: admit mat3/mat4",
    '''        if declaration.type.kind == "matrix":
            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")''',
    '''        if declaration.type.kind == "matrix" and declaration.type.display() not in ("mat3", "mat4"):
            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")''',
)

# 3. Uniform block admission (synth/remap).
apply(
    "uniform blocks: admit",
    '''    if typed.uniform_blocks:
        raise GeneratorError(f"{location(typed.uniform_blocks[0])}: unsupported uniform block")''',
    '''    if typed.uniform_blocks:
        pass  # RELAXED PROBE: provisionally admitted.''',
)

# 4. Varying / interface-symbol admission, restricted to vec2 (matches the
#    known v_texCoord shape). Mirrors census/probe_relaxed_varying.py.
apply(
    "varying: admit vec2 interface symbols",
    '''    if typed.interface_symbols:
        raise GeneratorError(f"{location(typed.interface_symbols[0])}: unsupported varying")''',
    '''    if any(sym.type.display() != "vec2" for sym in typed.interface_symbols):
        raise GeneratorError(f"{location(typed.interface_symbols[0])}: unsupported varying")''',
)

# 5. Sampler-as-parameter admission (mixer/distortion).
apply(
    "sampler parameter: admit",
    '''            if (parameter.type.kind == "sampler"
                    and (authorized_focus_blur_proof is None
                         or function is not authorized_focus_blur_proof.helper
                         or not any(parameter is item for item in
                                    authorized_focus_blur_proof.sampler_parameters))):
                raise GeneratorError(
                    f"{location(parameter)}: unsupported sampler parameter")''',
    '''            if (parameter.type.kind == "sampler"
                    and (authorized_focus_blur_proof is None
                         or function is not authorized_focus_blur_proof.helper
                         or not any(parameter is item for item in
                                    authorized_focus_blur_proof.sampler_parameters))):
                pass  # RELAXED PROBE: provisionally admitted.''',
)

# 5b. Sampler-expression admission (the use, inside a function body, of a
#     sampler that arrived as a parameter -- distortion's second hop once
#     patch 5 admits the parameter itself).
apply(
    "sampler expression: admit",
    '''    def expression(value, context: str = "rvalue") -> None:
        if (value.type.kind == "sampler"
                and getattr(value.symbol, "storage", None) != "uniform"
                and authorized_focus_blur_proof is None):
            raise GeneratorError(
                f"{location(value)}: unsupported sampler expression")''',
    '''    def expression(value, context: str = "rvalue") -> None:
        if (value.type.kind == "sampler"
                and getattr(value.symbol, "storage", None) != "uniform"
                and authorized_focus_blur_proof is None):
            pass  # RELAXED PROBE: provisionally admitted.''',
)

# 6. Parameter direction admission (filter/watercolor inout; also covers
#    `out`, needed for filter/lightLeak and the wider loop-proof cluster).
apply(
    "parameter direction: admit inout/out",
    '''            if parameter.direction != "in":
                raise GeneratorError(
                    f"{typed.key}:{parameter.span.start_line}:{parameter.span.start_column}: "
                    f"unsupported parameter direction {parameter.direction}")''',
    '''            if parameter.direction != "in":
                pass  # RELAXED PROBE: provisionally admitted.''',
)

# 7. `reflect` builtin admission (filter/lighting), by the same
#    node-identity-free provisional pattern used to probe round/tanh/any
#    upstream. Deliberately does NOT touch the real per-node authentication
#    machinery for round/tanh/floatBitsToUint/all -- only adds a new elif.
apply(
    "builtin: admit reflect/any provisionally",
    '''            elif value.callee not in _BUILTINS:
                raise GeneratorError(f"{location(value)}: unsupported builtin {value.callee}")''',
    '''            elif value.callee in ("reflect", "any"):
                pass  # RELAXED PROBE: provisionally admitted.
            elif value.callee not in _BUILTINS:
                raise GeneratorError(f"{location(value)}: unsupported builtin {value.callee}")''',
)

# 8. Loop-proof safety-charge admission (synth/gabor, synth/julia,
#    synth/newton) -- the per-loop budget gate inside audit_loop_proofs.
apply(
    "loop-proof: admit safety-charge overruns",
    '''        proof = actual.loop_proof
        if proof is not None:
            if (proof.trip_count > 128 or proof.lexical_depth > 3
                    or proof.effective_depth > 3 or proof.lexical_product > 4096
                    or proof.entrypoint_charge > 4096
                    or min(proof.trip_count, proof.lexical_depth, proof.effective_depth,
                           proof.lexical_product, proof.entrypoint_charge) < 0):
                raise GeneratorError(f"{location(actual)}: unsupported counted-for safety charge")''',
    '''        proof = actual.loop_proof
        if proof is not None:
            if min(proof.trip_count, proof.lexical_depth, proof.effective_depth,
                   proof.lexical_product, proof.entrypoint_charge) < 0:
                raise GeneratorError(f"{location(actual)}: unsupported counted-for safety charge")
            # RELAXED PROBE: budget-cap overruns provisionally admitted.''',
)

# 9. Loop-proof program-proof admission (the whole-program call-graph /
#    unproved-loop / budget gate) -- filter/lightLeak, filter/parallax, and
#    the rest of the 20 still-unported loop-proof cluster programs.
apply(
    "loop-proof: admit program-proof rejections",
    '''    if not recomputed_program_proof.call_graph_acyclic:
        offender = next((function for function in recomputed_functions if function.body), typed)
        raise GeneratorError(
            f"{location(offender)}: unsupported counted-for program proof")
    if (recomputed_program_proof.unproved_loop_count
            or recomputed_program_proof.max_effective_depth > 3
            or recomputed_program_proof.max_lexical_product > 4096
            or recomputed_program_proof.entrypoint_charge > 4096):
        # Programs without a loop stay valid after the unconditional call-graph
        # check above; only an actual unproved or over-budget loop reaches here.
        if recomputed_program_proof.loop_count or recomputed_program_proof.unproved_loop_count:
            def first_loop(statements):
                for statement in statements:
                    if statement.kind in {"for", "while", "dowhile"}:
                        return statement
                    if (nested := first_loop(statement.children)) is not None:
                        return nested
                return None

            offender = next((candidate for function in recomputed_functions
                             if (candidate := first_loop(function.body)) is not None), typed)
            raise GeneratorError(
                f"{location(offender)}: unsupported counted-for program proof")''',
    '''    pass  # RELAXED PROBE: program-proof call-graph/unproved/budget gate provisionally admitted.''',
)

# 10. statement()'s per-`for` walk requires an attached, matching loop_proof
#     object; an unproved loop carries loop_proof=None (loop_proof.py:552),
#     so without this the walk would immediately re-hit an equivalent
#     rejection ("unsupported typed statement for") one line later instead of
#     actually descending into the loop body where the real downstream
#     construct lives.
apply(
    "statement(for): walk into unproved loops",
    '''        elif value.kind == "for":
            if value.loop_proof is None or len(value.expressions) != 2 or len(value.children) != 2:
                raise GeneratorError(f"{location(value)}: unsupported typed statement for")
            used.add("counted-for-v1")''',
    '''        elif value.kind == "for":
            if len(value.expressions) != 2 or len(value.children) != 2:
                raise GeneratorError(f"{location(value)}: unsupported typed statement for")
            used.add("counted-for-v1")  # RELAXED PROBE: loop_proof match not required.''',
)

DST.write_text(text)
print(f"wrote {DST} ({len(patches)} patches applied)")
for label in patches:
    print(" -", label)

# Keep a unified diff for the audit trail.
import difflib
diff = "".join(difflib.unified_diff(
    original.splitlines(keepends=True), text.splitlines(keepends=True),
    fromfile="generate_typed_slice.py (unmodified copy)",
    tofile="generate_typed_slice_relaxed_all.py",
))
(HERE / "generate_typed_slice_relaxed_all.diff").write_text(diff)
print(f"wrote {HERE / 'generate_typed_slice_relaxed_all.diff'}")
