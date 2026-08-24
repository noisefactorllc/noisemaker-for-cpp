"""Builds three further-hop relaxed variants, layered on top of
generate_typed_slice_relaxed_all.py (see build_relaxed_all.py), used to chase
individual downstream chains deeper than the single generic hop that script
provides:

  - generate_typed_slice_relaxed_all_plus_deriv: additionally admits
    dFdx/dFdy/fwidth regardless of node identity (mixer/distortion's 3rd hop,
    behind sampler-parameter/-expression).
  - generate_typed_slice_relaxed_all_plus_matctor: additionally admits mat3/
    mat4 constructors and any mat*mat / mat*vec binary product
    (classicNoisedeck/glitch's 2nd and 3rd hops, behind the mat4 type itself).
  - generate_typed_slice_relaxed_all_plus_texturelod: additionally admits
    `textureLod` two ways -- once routed through the ordinary `used.add`
    bookkeeping (which trips the frozen-vocabulary "missing capabilities"
    safety net, confirming that net works) and once excluded from it exactly
    like round/tanh/dFdx (filter/parallax's 2nd hop, behind loop-proof).

Must be run AFTER build_relaxed_all.py (reads its output as the base text).
Read-only w.r.t. the real repo; writes only under
docs/port-engineering/singletons/probe_tree/. Never runs git.
"""
from __future__ import annotations

import pathlib

HERE = pathlib.Path(__file__).resolve().parent
GLSLCPP_DIR = HERE / "probe_tree" / "tools" / "glslcpp"
BASE = GLSLCPP_DIR / "generate_typed_slice_relaxed_all.py"


def patched(old: str, new: str, text: str, label: str) -> str:
    count = text.count(old)
    assert count == 1, f"{label}: expected 1 occurrence, found {count}"
    return text.replace(old, new, 1)


base_text = BASE.read_text()

# --- plus_deriv: admit dFdx/dFdy/fwidth regardless of node identity. ---
text = patched(
    '''            elif value.callee in {"dFdx", "dFdy", "fwidth"}:
                # Admitted only for the exact nodes authenticated by
                # derivative-admission-v1, by object identity. Like
                # round/tanh/floatBitsToUint/all/lessThanEqual, these never
                # enter the frozen 44-entry capability vocabulary.
                if not any(value is item for item in authorized_derivative_nodes):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                visited_derivative_nodes.append(value)''',
    '''            elif value.callee in {"dFdx", "dFdy", "fwidth"}:
                pass  # RELAXED PROBE (extra hop): admitted regardless of node identity.''',
    base_text, "plus_deriv")
(GLSLCPP_DIR / "generate_typed_slice_relaxed_all_plus_deriv.py").write_text(text)

# --- plus_matctor: admit mat3/mat4 constructors and mat*mat / mat*vec products. ---
text = patched(
    '''        if value.kind == "construct":
            used.add("constructors")
            if value.type.kind == "matrix":
                if (value.type.display() != "mat2" or len(value.children) != 4
                        or any(child.type.display() != "float" for child in value.children)):
                    raise GeneratorError(f"{location(value)}: unsupported matrix constructor")
                used.add("mat2-vector-multiply")
            elif any(child.type.kind == "matrix" for child in value.children):
                raise GeneratorError(f"{location(value)}: unsupported matrix conversion")''',
    '''        if value.kind == "construct":
            used.add("constructors")
            if value.type.kind == "matrix":
                if value.type.display() == "mat2" and (len(value.children) != 4
                        or any(child.type.display() != "float" for child in value.children)):
                    raise GeneratorError(f"{location(value)}: unsupported matrix constructor")
                elif value.type.display() not in ("mat2", "mat3", "mat4"):
                    raise GeneratorError(f"{location(value)}: unsupported matrix constructor")
                # RELAXED PROBE (extra hop): mat3/mat4 constructors admitted.
                used.add("mat2-vector-multiply")''',
    base_text, "plus_matctor(construct)")
text = patched(
    '''            elif left.type.kind == "matrix" or right.type.kind == "matrix":
                if value.operator != "*" or left_type != "mat2" or right_type != "vec2":
                    raise GeneratorError(f"{location(value)}: unsupported matrix binary expression")
                used.add("mat2-vector-multiply")''',
    '''            elif left.type.kind == "matrix" or right.type.kind == "matrix":
                if value.operator != "*":
                    raise GeneratorError(f"{location(value)}: unsupported matrix binary expression")
                # RELAXED PROBE (extra hop): any mat*mat / mat*vec product admitted.
                used.add("mat2-vector-multiply")''',
    text, "plus_matctor(binary)")
(GLSLCPP_DIR / "generate_typed_slice_relaxed_all_plus_matctor.py").write_text(text)

# --- plus_texturelod: admit textureLod, excluded from `used` bookkeeping
#     (same treatment as round/tanh/dFdx) so the frozen-vocabulary
#     "missing capabilities" safety net at the end of validate_capabilities
#     is not tripped by this probe-only admission. ---
text = patched(
    '''            elif value.callee in ("reflect", "any"):
                pass  # RELAXED PROBE: provisionally admitted.
            elif value.callee not in _BUILTINS:''',
    '''            elif value.callee in ("reflect", "any", "textureLod"):
                pass  # RELAXED PROBE: provisionally admitted.
            elif value.callee not in _BUILTINS:''',
    base_text, "plus_texturelod(admit)")
text = patched(
    '''            if value.callee not in {"round", "all", "lessThanEqual",
                                    "floatBitsToUint", "tanh",
                                    "dFdx", "dFdy", "fwidth"}:
                used.add(value.callee)''',
    '''            if value.callee not in {"round", "all", "lessThanEqual",
                                    "floatBitsToUint", "tanh",
                                    "dFdx", "dFdy", "fwidth", "textureLod"}:
                used.add(value.callee)''',
    text, "plus_texturelod(used-exclude)")
(GLSLCPP_DIR / "generate_typed_slice_relaxed_all_plus_texturelod.py").write_text(text)

print("wrote 3 extra-hop variants under", GLSLCPP_DIR)
