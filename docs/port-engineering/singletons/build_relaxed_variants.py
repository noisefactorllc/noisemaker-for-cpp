"""Builds targeted subset-relaxed copies of generate_typed_slice.py, reusing
the same 13 patches as build_relaxed_all.py, to ISOLATE individual hops in a
downstream blocker chain (e.g. "does lightLeak's blocker behind the loop-proof
gate specifically name `out`, or something else, when parameter-direction is
NOT also relaxed").

Same provenance/safety notes as build_relaxed_all.py: read-only w.r.t. the
real repo, writes only under docs/port-engineering/singletons/, never runs
git.
"""
from __future__ import annotations

import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "probe_tree" / "tools" / "glslcpp" / "generate_typed_slice.py"
GLSLCPP_DIR = HERE / "probe_tree" / "tools" / "glslcpp"

PATCHES = [
    ("mat3_mat4_type", '''    def reject_type(typ, value) -> None:
        if typ.kind == "array":''', '''    def reject_type(typ, value) -> None:
        if typ.display() in ("mat3", "mat4"):
            return
        if typ.kind == "array":'''),
    ("global_decl_gate1", '''        if storage != "const" or declaration.type != FLOAT or declaration.initializer is None:
            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")''',
     '''        if storage != "const" or declaration.type != FLOAT or declaration.initializer is None:
            admitted_globals[declaration.symbol.id] = declaration
            continue'''),
    ("global_decl_gate2", '''        if declaration.symbol.storage not in {"uniform", "output", "const"}:
            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")''',
     '''        if declaration.symbol.storage not in {"uniform", "output", "const"}:
            admitted_globals[declaration.symbol.id] = declaration
            continue'''),
    ("global_matrix_decl", '''        if declaration.type.kind == "matrix":
            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")''',
     '''        if declaration.type.kind == "matrix" and declaration.type.display() not in ("mat3", "mat4"):
            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")'''),
    ("uniform_block", '''    if typed.uniform_blocks:
        raise GeneratorError(f"{location(typed.uniform_blocks[0])}: unsupported uniform block")''',
     '''    if typed.uniform_blocks:
        pass'''),
    ("varying", '''    if typed.interface_symbols:
        raise GeneratorError(f"{location(typed.interface_symbols[0])}: unsupported varying")''',
     '''    if any(sym.type.display() != "vec2" for sym in typed.interface_symbols):
        raise GeneratorError(f"{location(typed.interface_symbols[0])}: unsupported varying")'''),
    ("sampler_param", '''            if (parameter.type.kind == "sampler"
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
                pass'''),
    ("sampler_expr", '''    def expression(value, context: str = "rvalue") -> None:
        if (value.type.kind == "sampler"
                and getattr(value.symbol, "storage", None) != "uniform"
                and authorized_focus_blur_proof is None):
            raise GeneratorError(
                f"{location(value)}: unsupported sampler expression")''',
     '''    def expression(value, context: str = "rvalue") -> None:
        if (value.type.kind == "sampler"
                and getattr(value.symbol, "storage", None) != "uniform"
                and authorized_focus_blur_proof is None):
            pass'''),
    ("param_direction", '''            if parameter.direction != "in":
                raise GeneratorError(
                    f"{typed.key}:{parameter.span.start_line}:{parameter.span.start_column}: "
                    f"unsupported parameter direction {parameter.direction}")''',
     '''            if parameter.direction != "in":
                pass'''),
    ("reflect_any_builtin", '''            elif value.callee not in _BUILTINS:
                raise GeneratorError(f"{location(value)}: unsupported builtin {value.callee}")''',
     '''            elif value.callee in ("reflect", "any"):
                pass
            elif value.callee not in _BUILTINS:
                raise GeneratorError(f"{location(value)}: unsupported builtin {value.callee}")'''),
    ("loopproof_safety_charge", '''        proof = actual.loop_proof
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
                raise GeneratorError(f"{location(actual)}: unsupported counted-for safety charge")'''),
    ("loopproof_program_proof", '''    if not recomputed_program_proof.call_graph_acyclic:
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
     '''    pass'''),
    ("loopproof_statement_for", '''        elif value.kind == "for":
            if value.loop_proof is None or len(value.expressions) != 2 or len(value.children) != 2:
                raise GeneratorError(f"{location(value)}: unsupported typed statement for")
            used.add("counted-for-v1")''',
     '''        elif value.kind == "for":
            if len(value.expressions) != 2 or len(value.children) != 2:
                raise GeneratorError(f"{location(value)}: unsupported typed statement for")
            used.add("counted-for-v1")'''),
]

LOOPPROOF_ONLY = {"loopproof_safety_charge", "loopproof_program_proof", "loopproof_statement_for"}
ALL_NAMES = {name for name, _, _ in PATCHES}


def build(module_name: str, include: set[str]) -> None:
    text = SRC.read_text()
    applied = 0
    for name, old, new in PATCHES:
        if name not in include:
            continue
        count = text.count(old)
        assert count == 1, f"{module_name}/{name}: expected 1 occurrence, found {count}"
        text = text.replace(old, new, 1)
        applied += 1
    dst = GLSLCPP_DIR / f"{module_name}.py"
    dst.write_text(text)
    print(f"wrote {dst} ({applied}/{len(include)} patches applied)")


# Variant A: loop-proof gates relaxed ONLY (nothing else). Isolates what
# breaks immediately behind the loop-proof gate for lightLeak/parallax/etc.
build("generate_typed_slice_relaxed_loopproof_only", LOOPPROOF_ONLY)

# Variant B: everything EXCEPT parameter-direction. Isolates whether `out`
# specifically (not something the paramdir patch was masking) is the real
# blocker once loop-proof and everything else is relaxed.
build("generate_typed_slice_relaxed_no_paramdir", ALL_NAMES - {"param_direction"})
