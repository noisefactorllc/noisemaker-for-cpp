"""Full gate-chain walker for the 81 unported noisemaker-for-cpp corpus
programs (revision a024dc3a960cc44af454abc7aebce50456c194e6).

READ-ONLY. Never writes under noisemaker-for-cpp or noisemaker-for-cpu.
All monkeypatches are function-object / table substitutions restored in
`finally`, with pre/post identity+hash snapshots proving restoration.

Method (extends future-precompute/analyze_candidates.py and
future-precompute/task32/probe_gate_chain.py to a general N-gate walk):

For each program, starting unpatched:
  1. Run validate_capabilities + render_typed_cpp.
  2. If both pass -> done (chain cleared).
  3. Otherwise take the first failing message (validator preferred; if
     validator passes but emitter fails, use the emitter's message -- this
     itself is evidence, since it means the two independent gates disagree).
  4. Classify the message against a library of known gate patterns.
  5. If a generic bypass/generalization patch exists for that gate, ADD it to
     the active patch set (cumulative -- previously cleared gates stay
     cleared) and go to 1.
  6. If no generic patch exists for the message, stop: this program is
     blocked on something that is not mechanically generalizable by this
     probe technique (flagged NO_GENERIC_PATCH, with the raw message kept).
  7. Cap at 8 gates (MAX_DEPTH); if still blocked, flag DEEP_GT_8.

Every "patch" here is an explicit PROBE -- it widens an admission rule or
deletes a single-identity gate to ask "what's the next blocker", exactly the
technique the existing scripts already use for `round`/`reflect`/etc. None of
this is a real capability implementation; every real fix in this codebase is
authenticated by an exact per-program SHA-256/object-identity profile, not a
name-based allowlist (see gate-chain-output.json's own docstring precedent).
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import re
import sys
import traceback
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

TYPED = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text())
TYPED_KEYS = set(row["program_key"] for row in TYPED["programs"])
ALL_KEYS = set(ENTRIES.keys())
UNPORTED_KEYS = sorted(ALL_KEYS - TYPED_KEYS)

MAX_DEPTH = 8

# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, raw, defines, typed


def first_line(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else f"{type(error).__name__}"


# ---------------------------------------------------------------------------
# Pristine original source captured ONCE at import time.
# ---------------------------------------------------------------------------

_ORIG_VALIDATE_SRC = inspect.getsource(gen.validate_capabilities)
_ORIG_EMIT_GLOBALS_SRC = inspect.getsource(emit._Emitter._validate_source_globals)
_ORIG_EMIT_EXPRESSION_SRC = inspect.getsource(emit._Emitter.expression)
_ORIG_EMIT_LOOPS_SRC = inspect.getsource(emit._Emitter._validate_counted_loops)
_ORIG_EMIT_TYPE_SRC = inspect.getsource(emit._Emitter.type)
_ORIG_EMIT_PARAM_TYPE_SRC = inspect.getsource(emit._Emitter.function_parameter_type)

_ORIG_APPROVED_CAPABILITIES = gen.APPROVED_CAPABILITIES
_ORIG_BUILTINS = gen._BUILTINS
_ORIG_APPROVED_TYPES = gen.APPROVED_TYPES
_ORIG_APPROVED_BINARY_OPERATORS = gen.APPROVED_BINARY_OPERATORS
_ORIG_EMIT_TYPES = dict(emit._TYPES)
_ORIG_EMIT_BUILTIN_NAMES = dict(emit._BUILTIN_NAMES)
_ORIG_EMIT_BINARY_OPERATORS = emit._BINARY_OPERATORS


def _dedent_from_class_body(src: str) -> str:
    """inspect.getsource on a method returns it indented as a class member
    (4 spaces). Strip exactly one level so it compiles standalone."""
    lines = src.splitlines()
    return "\n".join(line[4:] if line.startswith("    ") else line for line in lines) + "\n"


# ---------------------------------------------------------------------------
# Gate patch library. Each patch is a (needle, replacement) applied via
# str.replace(needle, replacement, 1) to the PRISTINE original source of the
# named target function -- never to a previously-patched string -- so any
# subset/order of patches composes safely as long as needles occupy disjoint
# regions (verified per-patch with an `assert count==1` at call time against
# the pristine text).
# ---------------------------------------------------------------------------


class Patch:
    def __init__(self, gate_id, description, *, validate_subs=(), emit_globals_subs=(),
                 emit_expression_subs=(), emit_loops_subs=(), emit_type_subs=(),
                 emit_param_type_subs=(),
                 table_deltas=None, mechanical=True, note=""):
        self.gate_id = gate_id
        self.description = description
        self.validate_subs = validate_subs
        self.emit_globals_subs = emit_globals_subs
        self.emit_expression_subs = emit_expression_subs
        self.emit_loops_subs = emit_loops_subs
        self.emit_type_subs = emit_type_subs
        self.emit_param_type_subs = emit_param_type_subs
        self.table_deltas = table_deltas or {}
        self.mechanical = mechanical
        self.note = note


def sub(needle, replacement):
    return (needle, replacement)


PATCHES: dict[str, Patch] = {}


def register(patch: Patch) -> None:
    PATCHES[patch.gate_id] = patch


# --- global_admission (Patch A, verbatim from task32/probe_gate_chain.py) --
register(Patch(
    "global_admission",
    "Drop float-only restriction on const-global admission; recurse construct "
    "initializers (vecN/matN constructor calls) in both validator and emitter.",
    validate_subs=[
        sub(
            '        if storage != "const" or declaration.type != FLOAT or declaration.initializer is None:\n'
            '            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")\n'
            '\n'
            '        def global_initializer(value) -> None:\n'
            '            if value.type != FLOAT:\n'
            '                raise GeneratorError(f"{location(value)}: unsupported global initializer type {value.type.display()}")\n'
            '            if value.kind == "literal":\n',
            '        if storage != "const" or declaration.initializer is None:\n'
            '            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")\n'
            '\n'
            '        def global_initializer(value) -> None:\n'
            '            if value.kind == "construct":\n'
            '                for child in value.children:\n'
            '                    global_initializer(child)\n'
            '                return\n'
            '            if value.kind == "literal":\n'
        ),
        sub(
            '        reject_type(declaration.type, declaration)\n'
            '        if declaration.type.kind == "matrix":\n'
            '            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")\n'
            '        if declaration.symbol.storage not in {"uniform", "output", "const"}:\n',
            '        reject_type(declaration.type, declaration)\n'
            '        if declaration.type.kind == "matrix" and declaration.symbol.storage != "const":\n'
            '            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")\n'
            '        if declaration.symbol.storage not in {"uniform", "output", "const"}:\n'
        ),
    ],
    emit_globals_subs=[
        sub(
            '            if (declaration.symbol.storage != "const" or declaration.type.display() != "float"\n'
            '                    or declaration.initializer is None):\n'
            '                raise _error(self.program, declaration, "unsupported source global declaration")\n'
            '            dependencies: list[int] = []\n'
            '\n'
            '            def initializer(value: TypedExpression) -> None:\n'
            '                if value.type.display() != "float":\n'
            '                    raise _error(self.program, value, "unsupported source const global initializer type")\n'
            '                if value.kind == "literal":\n',
            '            if (declaration.symbol.storage != "const"\n'
            '                    or declaration.initializer is None):\n'
            '                raise _error(self.program, declaration, "unsupported source global declaration")\n'
            '            dependencies: list[int] = []\n'
            '\n'
            '            def initializer(value: TypedExpression) -> None:\n'
            '                if value.kind == "construct":\n'
            '                    for child in value.children:\n'
            '                        initializer(child)\n'
            '                    return\n'
            '                if value.kind == "literal":\n'
        ),
    ],
))

# --- global_admission_shift: extend the const-global initializer walker to
# also admit <<, >>, ^, & (bitEffects needs <<; nothing else in the corpus
# was observed to need this, but the probe is general).
register(Patch(
    "global_admission_shift",
    "Extend const-global initializer walker binary-operator set from "
    "{+,-,*,/} to also admit {<<,>>,^,&} (probe of bitEffects's `mask = (1 "
    "<< BIT_COUNT) - 1` shape).",
    validate_subs=[
        sub(
            '            if value.kind == "binary" and value.operator in {"+", "-", "*", "/"} and len(value.children) == 2:\n'
            '                global_initializer(value.children[0])\n'
            '                global_initializer(value.children[1])\n'
            '                return\n',
            '            if value.kind == "binary" and value.operator in {"+", "-", "*", "/", "<<", ">>", "^", "&"} and len(value.children) == 2:\n'
            '                global_initializer(value.children[0])\n'
            '                global_initializer(value.children[1])\n'
            '                return\n',
        ),
    ],
    emit_globals_subs=[
        sub(
            '                if value.kind == "binary" and value.operator in {"+", "-", "*", "/"}:\n'
            '                    if len(value.children) != 2:\n'
            '                        raise _error(self.program, value, "malformed source const global initializer")\n'
            '                    initializer(value.children[0])\n'
            '                    initializer(value.children[1])\n'
            '                    return\n',
            '                if value.kind == "binary" and value.operator in {"+", "-", "*", "/", "<<", ">>", "^", "&"}:\n'
            '                    if len(value.children) != 2:\n'
            '                        raise _error(self.program, value, "malformed source const global initializer")\n'
            '                    initializer(value.children[0])\n'
            '                    initializer(value.children[1])\n'
            '                    return\n',
        ),
    ],
    mechanical=False,
    note="Requires global_admission first (composes). Bitwise-shift const "
         "global initializers are outside today's admitted operator set on "
         "both sides.",
))

# --- global_admission_swizzle: admit a swizzle-of-earlier-admitted-global as
# a const global initializer dependency (scanlineError's TIME_SEED_LINE
# shape: BASE_SEED_LINE.x + 97.0).
register(Patch(
    "global_admission_swizzle",
    "Admit `swizzle` of an earlier-admitted const global as a dependency "
    "inside the const-global initializer walker (both validator+emitter).",
    validate_subs=[
        sub(
            '            if value.kind == "id":\n'
            '                dependency = admitted_globals.get(value.symbol_id)\n'
            '                if (dependency is None or value.symbol is None\n'
            '                        or value.symbol.id != value.symbol_id\n'
            '                        or dependency.symbol.id != value.symbol_id):\n'
            '                    raise GeneratorError(\n'
            '                        f"{location(value)}: global initializer dependency must name an earlier admitted const float")\n'
            '                return\n',
            '            if value.kind == "id":\n'
            '                dependency = admitted_globals.get(value.symbol_id)\n'
            '                if (dependency is None or value.symbol is None\n'
            '                        or value.symbol.id != value.symbol_id\n'
            '                        or dependency.symbol.id != value.symbol_id):\n'
            '                    raise GeneratorError(\n'
            '                        f"{location(value)}: global initializer dependency must name an earlier admitted const float")\n'
            '                return\n'
            '            if value.kind == "swizzle" and value.children:\n'
            '                global_initializer(value.children[0])\n'
            '                return\n',
        ),
    ],
    emit_globals_subs=[
        sub(
            '                if value.kind == "id":\n'
            '                    if (value.symbol_id not in admitted or value.symbol is None\n'
            '                            or value.symbol.id != value.symbol_id):\n'
            '                        raise _error(\n'
            '                            self.program, value,\n'
            '                            "source const global dependency must name an earlier admitted declaration")\n'
            '                    if value.symbol_id not in dependencies:\n'
            '                        dependencies.append(value.symbol_id)\n'
            '                    return\n',
            '                if value.kind == "id":\n'
            '                    if (value.symbol_id not in admitted or value.symbol is None\n'
            '                            or value.symbol.id != value.symbol_id):\n'
            '                        raise _error(\n'
            '                            self.program, value,\n'
            '                            "source const global dependency must name an earlier admitted declaration")\n'
            '                    if value.symbol_id not in dependencies:\n'
            '                        dependencies.append(value.symbol_id)\n'
            '                    return\n'
            '                if value.kind == "swizzle" and value.children:\n'
            '                    initializer(value.children[0])\n'
            '                    return\n',
        ),
    ],
    mechanical=False,
    note="Requires global_admission first. Swizzle-of-dependency initializer "
         "shape is outside today's walker.",
))

# --- array_global_admission: widen reject_type's array branch to admit any
# const-storage global array whose element type is already approved, purely
# for probing what's downstream of normalMap's ivec2[9]/float[9] tables.
register(Patch(
    "array_global_admission",
    "Widen reject_type's array branch to admit any const-storage global "
    "array (probe of normalMap's SOBEL_OFFSETS[9]/SOBEL_X_KERNEL[9]/"
    "SOBEL_Y_KERNEL[9] const array-of-vector/float globals).",
    validate_subs=[
        sub(
            '            if (getattr(value, "kind", None) == "id"\n'
            '                    and (getattr(value, "symbol_id", None), value.span,\n'
            '                         typ.display()) in proved_array_arguments):\n'
            '                used.add(FIXED_ARRAY_PARAMETER_CAPABILITY)\n'
            '                return\n'
            '            raise GeneratorError(f"{location(value)}: unsupported typed type {typ.display()}")\n'
            '        if typ.display() == "bvec2":\n',
            '            if (getattr(value, "kind", None) == "id"\n'
            '                    and (getattr(value, "symbol_id", None), value.span,\n'
            '                         typ.display()) in proved_array_arguments):\n'
            '                used.add(FIXED_ARRAY_PARAMETER_CAPABILITY)\n'
            '                return\n'
            '            return  # PROBE: array_global_admission (maximally permissive)\n'
            '        if typ.display() == "bvec2":\n',
        ),
    ],
    emit_type_subs=[
        sub(
            '    def type(self, value: object) -> str:\n'
            '        name = value.display()\n'
            '        try:\n'
            '            return _TYPES[name]\n'
            '        except KeyError as error:\n'
            '            raise _error(self.program, value, f"unsupported typed type {name}") from error\n',
            '    def type(self, value: object) -> str:\n'
            '        name = value.display()\n'
            '        if name.endswith("]") and "[" in name:  # PROBE: array_global_admission\n'
            '            base, _, rest = name.partition("[")\n'
            '            count = rest.rstrip("]")\n'
            '            base_cpp = _TYPES.get(base, base)\n'
            '            return f"std::array<{base_cpp}, {count}>"\n'
            '        try:\n'
            '            return _TYPES[name]\n'
            '        except KeyError as error:\n'
            '            raise _error(self.program, value, f"unsupported typed type {name}") from error\n',
        ),
    ],
    emit_param_type_subs=[
        sub(
            '        raise _error(self.program, parameter,\n'
            '                     f"unsupported typed type {parameter.type.display()}")\n',
            '        return self.type(parameter.type)  # PROBE: array_global_admission\n',
        ),
    ],
    mechanical=False,
    note="Const array-of-vector/float global admission is materially larger "
         "scope than scalar/vector/matrix generalization (task32 finding, "
         "confirmed): array types are rejected by a separate, earlier gate. "
         "Also required a second, previously-undiscovered emitter-side gap: "
         "_Emitter.type() has no array-display fallback at all (found by "
         "this engine, not by task32 -- normalMap's array-of-vector globals "
         "still need array declarations to be *emitted*, not just admitted).",
))

register(Patch(
    "scalar_uint_xor_admission",
    "Widen the `^` type-shape check to also accept plain int^int / "
    "uint^uint scalar XOR (not only uvecN^uvecN, and not only the "
    "caustic/perlin identity-gated scalar-uint sites), in both modules. "
    "Found by this engine: grain's `uint(cell.x) ^ seed` needs uint^uint; "
    "bitEffects/synth-bitwise separately need int^int (`(a ^ 0xFFFFFFFF) & "
    "mask`, `a ^ b` with signed int operands) -- a further distinct "
    "widening this engine found by continuing past the uint-only case.",
    validate_subs=[
        sub(
            '                else:\n'
            '                    if (left_type not in {"uvec2", "uvec3", "uvec4"}\n'
            '                            or right_type != left_type):\n'
            '                        raise GeneratorError(\n'
            '                            f"{location(value)}: unsupported binary operator ^")\n'
            '                    used.add("uint-vector-bitwise")\n',
            '                else:\n'
            '                    if not ((left_type in {"uvec2", "uvec3", "uvec4"} and right_type == left_type)\n'
            '                            or (left_type in {"uint", "int"} and right_type == left_type)):\n'
            '                        raise GeneratorError(\n'
            '                            f"{location(value)}: unsupported binary operator ^")\n'
            '                    used.add("uint-vector-bitwise")\n',
        ),
    ],
    emit_expression_subs=[
        sub(
            '                if (left_type not in {"uvec2", "uvec3", "uvec4"}\n'
            '                        or right_type != left_type):\n'
            '                    raise _error(self.program, value, "unsupported binary operator ^")\n'
            '                return (f"glsl::bitwise_xor({self.expression(value.children[0])}, "\n'
            '                        f"{self.expression(value.children[1])})")\n',
            '                if (left_type in {"uint", "int"} and right_type == left_type):\n'
            '                    return (f"({self.expression(value.children[0])} ^ "\n'
            '                            f"{self.expression(value.children[1])})")\n'
            '                if (left_type not in {"uvec2", "uvec3", "uvec4"}\n'
            '                        or right_type != left_type):\n'
            '                    raise _error(self.program, value, "unsupported binary operator ^")\n'
            '                return (f"glsl::bitwise_xor({self.expression(value.children[0])}, "\n'
            '                        f"{self.expression(value.children[1])})")\n',
        ),
    ],
    mechanical=True,
    note="int^int / uint^uint is ordinary C++ `^`; no runtime gap, purely a "
         "generator admission gap (like round). Structurally identical "
         "relaxation to the existing uvecN^uvecN rule.",
))

# --- matrix_type_admission: table-only (no source patch needed since
# reject_type / _Emitter.type() do live module-global lookups).
register(Patch(
    "matrix_type_admission",
    "Add mat3/mat4 to APPROVED_TYPES (validator) and emit._TYPES (emitter, "
    "placeholder spelling) -- table-only, no source rewrite needed since "
    "both lookups are live module-global reads.",
    table_deltas={"approved_types": ("mat3", "mat4"),
                  "emit_types": {"mat3": "glsl::Mat3", "mat4": "glsl::Mat4"}},
    mechanical=True,
))

register(Patch(
    "bvec_type_admission",
    "Add bvec2/bvec3/bvec4 to APPROVED_TYPES and emit._TYPES, AND delete "
    "bvec2's own single-identity gate in reject_type (bvec2 is deliberately "
    "absent from APPROVED_TYPES and admitted only for the exact node "
    "authenticated by extrude-bvec2-relational-reduction-v1 -- same pattern "
    "as round/tanh/floatBitsToUint, just on a TYPE instead of a builtin).",
    validate_subs=[sub(
        '        if typ.display() == "bvec2":\n'
        '            # `bvec2` is deliberately absent from APPROVED_TYPES. It is admitted\n'
        '            # only as the result type of an exact authenticated Extrude\n'
        '            # relational node, which is immediately consumed by its paired\n'
        '            # `all`. Type admission is a separate authority from builtin\n'
        '            # admission, so both must independently agree.\n'
        '            if any(value is item for item in authorized_extrude_relationals):\n'
        '                return\n'
        '            raise GeneratorError(f"{location(value)}: unsupported typed type {typ.display()}")\n',
        '        if False and typ.display() == "bvec2":\n'
        '            raise GeneratorError(f"{location(value)}: unsupported typed type {typ.display()}")\n',
    )],
    table_deltas={"approved_types": ("bvec2", "bvec3", "bvec4"),
                  "emit_types": {"bvec2": "glsl::BVec2", "bvec3": "glsl::BVec3",
                                 "bvec4": "glsl::BVec4"}},
    mechanical=False,
    note="waves/emboss need bvec2 constructed from any/notEqual/etc. without "
         "extrude's authenticated identity -- a real fix needs its own "
         "per-program profile, following this codebase's precedent.",
))

# --- bitwise operator admission ---
register(Patch(
    "bitwise_and_admission",
    "Add `&` to APPROVED_BINARY_OPERATORS (validator) / _BINARY_OPERATORS "
    "(emitter). No existing per-`&` type-shape check exists in either "
    "elif-chain, so this falls through to the generic scalar-vector-"
    "arithmetic bucket with NO type restriction -- a materially weaker "
    "guarantee than the existing `^`/`>>` int-vector-only gates.",
    table_deltas={"approved_binary_operators": ("&",),
                  "emit_binary_operators": ("&",)},
    mechanical=False,
    note="Unlike ^/>>, there is no type-shape enforcement block for & in "
         "either module today; admitting it structurally is weaker than the "
         "existing precedent.",
))
register(Patch(
    "unary_bitwise_not_admission",
    "Widen the unary-operator allowlist from {+,-,!} to also admit `~` "
    "(bitwise NOT), in both modules.",
    validate_subs=[sub(
        '        elif value.kind == "unary" and value.operator not in {"+", "-", "!"}:\n'
        '            raise GeneratorError(f"{location(value)}: unsupported unary operator {value.operator}")\n',
        '        elif value.kind == "unary" and value.operator not in {"+", "-", "!", "~"}:\n'
        '            raise GeneratorError(f"{location(value)}: unsupported unary operator {value.operator}")\n',
    )],
    emit_expression_subs=[sub(
        '            if value.operator not in {"+", "-", "!"}:\n'
        '                raise _error(self.program, value, f"unsupported unary operator {value.operator}")\n',
        '            if value.operator not in {"+", "-", "!", "~"}:\n'
        '                raise _error(self.program, value, f"unsupported unary operator {value.operator}")\n',
    )],
    mechanical=True,
    note="`~` (bitwise NOT) is ordinary C++ unary ~; synth/bitwise's xnor "
         "op (`~(a ^ b)`) needs this.",
))
register(Patch(
    "bitwise_or_admission",
    "Add `|` to APPROVED_BINARY_OPERATORS / _BINARY_OPERATORS. No type-shape "
    "check block exists for | either (same caveat as &).",
    table_deltas={"approved_binary_operators": ("|",),
                  "emit_binary_operators": ("|",)},
    mechanical=False,
    note="No type-shape enforcement block for | exists in either module. "
         "bitEffects's `(a ^ 0xFFFFFFFF) & mask | (b & mask)`-style chains "
         "and synth/bitwise's `or`/`xnor` op table need this.",
))
register(Patch(
    "shift_left_admission",
    "Add `<<` to APPROVED_BINARY_OPERATORS / _BINARY_OPERATORS. Same caveat "
    "as bitwise_and_admission: no type-shape check block exists for <<.",
    table_deltas={"approved_binary_operators": ("<<",),
                  "emit_binary_operators": ("<<",)},
    mechanical=False,
    note="No type-shape enforcement block for << exists in either module.",
))

# --- uvecN >> uvecN (component-wise shift by a vector; grain's pcg3d) ---
register(Patch(
    "uvec_shift_by_vector",
    "Widen the `>>` type-shape check to also accept uvecN >> uvecN "
    "(component-wise shift) AND plain scalar int>>int / uint>>uint, not "
    "only uvecN >> uint, in both modules.",
    validate_subs=[
        sub(
            '            elif value.operator == ">>":\n'
            '                if left_type not in {"uvec2", "uvec3", "uvec4"} or right_type != "uint":\n'
            '                    raise GeneratorError(f"{location(value)}: unsupported binary operator >>")\n'
            '                used.add("uint-vector-bitwise")\n',
            '            elif value.operator == ">>":\n'
            '                if not (\n'
            '                    (left_type in {"uvec2", "uvec3", "uvec4"} and right_type in {"uint", left_type})\n'
            '                    or (left_type in {"int", "uint"} and right_type == left_type)\n'
            '                ):\n'
            '                    raise GeneratorError(f"{location(value)}: unsupported binary operator >>")\n'
            '                used.add("uint-vector-bitwise")\n',
        ),
    ],
    emit_expression_subs=[
        sub(
            '            if value.operator == ">>":\n'
            '                if left_type not in {"uvec2", "uvec3", "uvec4"} or right_type != "uint":\n'
            '                    raise _error(self.program, value, "unsupported binary operator >>")\n'
            '                return (f"glsl::shift_right({self.expression(value.children[0])}, "\n'
            '                        f"{self.expression(value.children[1])})")\n',
            '            if value.operator == ">>":\n'
            '                if left_type in {"int", "uint"} and right_type == left_type:\n'
            '                    return (f"({self.expression(value.children[0])} >> "\n'
            '                            f"{self.expression(value.children[1])})")\n'
            '                if left_type not in {"uvec2", "uvec3", "uvec4"} or right_type not in {"uint", left_type}:\n'
            '                    raise _error(self.program, value, "unsupported binary operator >>")\n'
            '                return (f"glsl::shift_right({self.expression(value.children[0])}, "\n'
            '                        f"{self.expression(value.children[1])})")\n',
        ),
    ],
    mechanical=False,
    note="grain's `v ^ (v >> uvec3(16u))` needs uvec3>>uvec3 (today only "
         "uvecN>>uint is approved, asymmetric with uvecN^uvecN). "
         "glyphMap/osd/spookyTicker separately need plain scalar int>>int / "
         "uint>>uint shift (`row >> (4-x)`), a third, distinct combination "
         "this engine found by continuing past the vector case.",
))

# --- builtin admission, generated per-name at runtime (see make_builtin_patch)

_IDENTITY_GATED_BUILTINS = {"round", "tanh", "floatBitsToUint", "all", "lessThanEqual"}


def make_builtin_patch(name: str) -> Patch:
    gate_id = f"builtin:{name}"
    if gate_id in PATCHES:
        return PATCHES[gate_id]
    if name not in _IDENTITY_GATED_BUILTINS:
        patch = Patch(
            gate_id, f"Admit builtin `{name}` by name into APPROVED_CAPABILITIES/"
                      f"_BUILTINS/emit._BUILTIN_NAMES (table-only; no identity gate "
                      f"exists for this builtin today).",
            table_deltas={"approved_capabilities": (name,), "emit_builtin_names": {name: name}},
            mechanical=True,
            note="No object-identity gate exists for this builtin; ordinary "
                 "table admission is structurally sufficient (does not mean "
                 "the C++ semantics are correct -- see discriminability).",
        )
        register(patch)
        return patch
    # Identity-gated builtins need a source rewrite deleting their
    # single-authenticated-node gate, exactly the technique task32 proved for
    # `round`.
    if name == "round":
        v_needle = ('            if value.callee == "round":\n'
                    '                if value is not authorized_round:\n'
                    '                    raise GeneratorError(f"{location(value)}: unsupported builtin round")\n'
                    '            elif value.callee == "tanh":\n')
        v_repl = '            if value.callee == "tanh":\n'
        e_needle = ('                if value.callee == "round":\n'
                    '                    raise _error(self.program, value, "unsupported builtin round")\n'
                    '                if value.callee == "tanh":\n')
        e_repl = '                if value.callee == "tanh":\n'
        used_needle = ('            if value.callee not in {"round", "all", "lessThanEqual",\n'
                       '                                    "floatBitsToUint", "tanh"}:\n'
                       '                used.add(value.callee)\n')
        used_repl = ('            if value.callee not in {"all", "lessThanEqual",\n'
                     '                                    "floatBitsToUint", "tanh"}:\n'
                     '                used.add(value.callee)\n')
        patch = Patch(gate_id, "Delete round's single-identity gate (GATHER_SORTED_KEY-only); "
                                "admit by name.",
                      validate_subs=[sub(v_needle, v_repl), sub(used_needle, used_repl)],
                      emit_expression_subs=[sub(e_needle, e_repl)],
                      table_deltas={"approved_capabilities": ("round",), "emit_builtin_names": {"round": "round"}},
                      mechanical=False,
                      note="round already exists correctly in the C++ runtime "
                           "(glsl_round = floor(x+0.5)); the gate is purely "
                           "generator-side identity scoping.")
        register(patch)
        return patch
    if name == "tanh":
        v_needle = ('            elif value.callee == "tanh":\n'
                    '                # Admitted only for the exact node authenticated by\n'
                    '                # curl-vector-math-tanh-wide-mod-v1. Never enters the\n'
                    '                # capability vocabulary and never joins _BUILTINS.\n'
                    '                if (authorized_curl_tanh is None\n'
                    '                        or value is not authorized_curl_tanh):\n'
                    '                    raise GeneratorError(\n'
                    '                        f"{location(value)}: unsupported builtin {value.callee}")\n'
                    '                visited_curl_nodes.append(value)\n'
                    '            elif value.callee == "floatBitsToUint":\n')
        v_repl = '            elif value.callee == "floatBitsToUint":\n'
        e_needle = ('                if value.callee == "tanh":\n'
                    '                    proof = self.authorized_curl_proof\n'
                    '                    if proof is None or value is not proof.tanh_site:\n'
                    '                        raise _error(self.program, value,\n'
                    '                                     f"unsupported builtin {value.callee}")\n'
                    '                    if len(arguments) != 1:\n'
                    '                        raise _error(self.program, value, "tanh arity")\n'
                    '                    self.emitted_curl_nodes.append(value)\n'
                    '                    # Lane-wise, non-narrowing: the JavaScript transpiler\n'
                    '                    # scalarises this assignment, so it hands Math.tanh the\n'
                    '                    # full-precision operand and narrows only the result.\n'
                    '                    # Narrowing the argument here costs bit-exact parity.\n'
                    '                    return f"glsl::tanh_lanewise({arguments[0]})"\n')
        e_repl = ('                if value.callee == "tanh":\n'
                  '                    if len(arguments) != 1:\n'
                  '                        raise _error(self.program, value, "tanh arity")\n'
                  '                    return f"glsl::tanh_lanewise({arguments[0]})"\n')
        used_needle = ('            if value.callee not in {"round", "all", "lessThanEqual",\n'
                       '                                    "floatBitsToUint", "tanh"}:\n'
                       '                used.add(value.callee)\n')
        used_repl = ('            if value.callee not in {"round", "all", "lessThanEqual",\n'
                     '                                    "floatBitsToUint"}:\n'
                     '                used.add(value.callee)\n')
        patch = Patch(gate_id, "Delete tanh's single-identity gate (curl-only); admit by name.",
                      validate_subs=[sub(v_needle, v_repl), sub(used_needle, used_repl)],
                      emit_expression_subs=[sub(e_needle, e_repl)],
                      table_deltas={"approved_capabilities": ("tanh",), "emit_builtin_names": {"tanh": "tanh"}},
                      mechanical=False,
                      note="Math.tanh reference is direct in the JS runtime; "
                           "glsl::tanh_lanewise already exists (curl uses it).")
        register(patch)
        return patch
    if name == "floatBitsToUint":
        v_needle = ('            elif value.callee == "floatBitsToUint":\n'
                    '                # Admitted only for the exact node authenticated by\n'
                    '                # caustic-float-bits-scalar-word-hash-v1. Never enters the\n'
                    '                # capability vocabulary.\n'
                    '                if (authorized_caustic_ingress is None\n'
                    '                        or value is not authorized_caustic_ingress):\n'
                    '                    raise GeneratorError(\n'
                    '                        f"{location(value)}: unsupported builtin {value.callee}")\n'
                    '                visited_caustic_ingress.append(value)\n'
                    '            elif value.callee in {"all", "lessThanEqual"}:\n')
        v_repl = '            elif value.callee in {"all", "lessThanEqual"}:\n'
        e_needle = ('                if value.callee == "floatBitsToUint":\n'
                    '                    proof = self.authorized_caustic_proof\n'
                    '                    if proof is None or value is not proof.ingress:\n'
                    '                        raise _error(self.program, value,\n'
                    '                                     f"unsupported builtin {value.callee}")\n'
                    '                    if len(arguments) != 1:\n'
                    '                        raise _error(self.program, value, "floatBitsToUint arity")\n'
                    '                    self.emitted_caustic_nodes.append(value)\n'
                    '                    # Delegates to the existing, tested bit-reinterpretation\n'
                    '                    # helper. Must NOT be confused with float_to_uint32, which\n'
                    '                    # is GLSL numeric conversion (truncate + wrap).\n'
                    '                    return f"noisemaker::float_bits_to_uint({arguments[0]})"\n')
        e_repl = ('                if value.callee == "floatBitsToUint":\n'
                  '                    if len(arguments) != 1:\n'
                  '                        raise _error(self.program, value, "floatBitsToUint arity")\n'
                  '                    return f"noisemaker::float_bits_to_uint({arguments[0]})"\n')
        used_needle = ('            if value.callee not in {"round", "all", "lessThanEqual",\n'
                       '                                    "floatBitsToUint", "tanh"}:\n'
                       '                used.add(value.callee)\n')
        used_repl = ('            if value.callee not in {"round", "all", "lessThanEqual",\n'
                     '                                    "tanh"}:\n'
                     '                used.add(value.callee)\n')
        patch = Patch(gate_id, "Delete floatBitsToUint's single-identity gate (caustic-only); "
                                "admit by name.",
                      validate_subs=[sub(v_needle, v_repl), sub(used_needle, used_repl)],
                      emit_expression_subs=[sub(e_needle, e_repl)],
                      table_deltas={"approved_capabilities": ("floatBitsToUint",),
                                    "emit_builtin_names": {"floatBitsToUint": "floatBitsToUint"}},
                      mechanical=False,
                      note="noisemaker::float_bits_to_uint already exists in the C++ runtime.")
        register(patch)
        return patch
    if name in {"all", "lessThanEqual"}:
        v_needle = ('            elif value.callee in {"all", "lessThanEqual"}:\n'
                    '                # Admitted only for the exact nodes authenticated by\n'
                    '                # extrude-bvec2-relational-reduction-v1, by object identity.\n'
                    '                # Like `round`, these never enter the capability vocabulary.\n'
                    '                authorized_extrude_nodes = (*authorized_extrude_reductions,\n'
                    '                                            *authorized_extrude_relationals)\n'
                    '                if not any(value is item for item in authorized_extrude_nodes):\n'
                    '                    raise GeneratorError(\n'
                    '                        f"{location(value)}: unsupported builtin {value.callee}")\n'
                    '                visited_extrude_nodes.append(value)\n'
                    '            elif value.callee not in _BUILTINS:\n')
        v_repl = '            elif value.callee not in _BUILTINS:\n'
        e_needle = ('                if value.callee in {"all", "lessThanEqual"}:\n'
                    '                    # Emitted only for the exact nodes this emitter itself\n'
                    '                    # authenticated. `bvec2` and these two builtins are absent\n'
                    '                    # from _TYPES/_BUILTIN_NAMES so no other program can reach\n'
                    '                    # them.\n'
                    '                    proof = self.authorized_extrude_proof\n'
                    '                    nodes = (() if proof is None else\n'
                    '                             (*proof.reductions, *proof.relationals))\n'
                    '                    if not any(value is item for item in nodes):\n'
                    '                        raise _error(self.program, value,\n'
                    '                                     f"unsupported builtin {value.callee}")\n'
                    '                    self.emitted_extrude_nodes.append(value)\n'
                    '                    if value.callee == "all":\n'
                    '                        if len(arguments) != 1:\n'
                    '                            raise _error(self.program, value, "all arity")\n'
                    '                        return f"glsl::all({arguments[0]})"\n'
                    '                    if len(arguments) != 2:\n'
                    '                        raise _error(self.program, value, "lessThanEqual arity")\n'
                    '                    return f"glsl::lessThanEqual({arguments[0]}, {arguments[1]})"\n')
        e_repl = ('                if value.callee == "all":\n'
                  '                    if len(arguments) != 1:\n'
                  '                        raise _error(self.program, value, "all arity")\n'
                  '                    return f"glsl::all({arguments[0]})"\n'
                  '                if value.callee == "lessThanEqual":\n'
                  '                    if len(arguments) != 2:\n'
                  '                        raise _error(self.program, value, "lessThanEqual arity")\n'
                  '                    return f"glsl::lessThanEqual({arguments[0]}, {arguments[1]})"\n')
        patch = Patch("builtin:all_lessThanEqual",
                      "Delete all/lessThanEqual's single-identity gate (extrude-only); "
                      "admit both by name (they share one gate).",
                      validate_subs=[sub(v_needle, v_repl)],
                      emit_expression_subs=[sub(e_needle, e_repl)],
                      table_deltas={"approved_capabilities": ("all", "lessThanEqual"),
                                    "emit_builtin_names": {"all": "all", "lessThanEqual": "lessThanEqual"}},
                      mechanical=True,
                      note="glsl::all / glsl::lessThanEqual already exist (extrude uses them). "
                           "JS reference implements the whole vector-relational family generically.")
        register(patch)
        PATCHES["builtin:all"] = patch
        PATCHES["builtin:lessThanEqual"] = patch
        return patch
    raise AssertionError(name)


# --- index expression admission (probe: bypass the proof requirement) ---
register(Patch(
    "index_expression_admission",
    "PROBE: bypass the array-index proof requirement entirely (accept any "
    "`id[literal-or-id]` site) in both validator and emitter, to reveal "
    "what's downstream of `unsupported typed expression index` for the "
    "filter/grade.glsl cluster and others. NOT a real capability -- the real "
    "proofs (fixed-nine/fixed-grid/task19/task20) are each a whole-program, "
    "per-key authenticated structure.",
    validate_subs=[
        sub(
            '            if not base_valid or not (\n'
            '                    store_valid or read_valid or grid_store_valid or grid_read_valid\n'
            '                    or task19_store_valid or task19_read_valid or task20_valid):\n'
            '                raise GeneratorError(f"{location(value)}: unsupported typed expression index")\n',
            '            if value.children[0].symbol is None:\n'
            '                raise GeneratorError(f"{location(value)}: unsupported typed expression index")\n'
            '            # PROBE: index_expression_admission -- bypass proof requirement\n',
        ),
    ],
    emit_expression_subs=[
        sub(
            '            if not self._proved_index(value):\n'
            '                raise _error(self.program, value, "unsupported typed expression index")\n'
            '            return f"{self.expression(value.children[0])}[{self.expression(value.children[1])}]"\n',
            '            if not self._proved_index(value) and value.children[0].symbol is None:\n'
            '                raise _error(self.program, value, "unsupported typed expression index")\n'
            '            return f"{self.expression(value.children[0])}[{self.expression(value.children[1])}]"\n',
        ),
    ],
    mechanical=False,
    note="Real fix needs per-program authenticated array proofs, not a "
         "structural bypass; this probe answers 'is indexing the ONLY "
         "remaining blocker' for its cluster.",
))

# --- struct / uniform block / varying admission (unconditional-reject probes)
register(Patch(
    "struct_admission",
    "PROBE: bypass the unconditional `if typed.structs: raise` gate.",
    validate_subs=[sub(
        '    if typed.structs:\n'
        '        raise GeneratorError(f"{location(typed.structs[0])}: unsupported struct declaration")\n',
        '    if False and typed.structs:\n'
        '        raise GeneratorError(f"{location(typed.structs[0])}: unsupported struct declaration")\n',
    )],
    mechanical=False,
    note="Validator-only bypass; the emitter has no struct-lowering path at "
         "all (no struct type table, no member-access codegen), so this "
         "probe primarily proves whether struct is the ONLY gate before "
         "hitting the emitter's own unmodeled-struct wall.",
))
register(Patch(
    "uniform_block_admission",
    "PROBE: bypass the unconditional `if typed.uniform_blocks: raise` gate.",
    validate_subs=[sub(
        '    if typed.uniform_blocks:\n'
        '        raise GeneratorError(f"{location(typed.uniform_blocks[0])}: unsupported uniform block")\n',
        '    if False and typed.uniform_blocks:\n'
        '        raise GeneratorError(f"{location(typed.uniform_blocks[0])}: unsupported uniform block")\n',
    )],
    mechanical=False,
    note="No uniform-block lowering exists in the emitter either.",
))
register(Patch(
    "varying_admission",
    "PROBE: bypass the unconditional `if typed.interface_symbols: raise` gate.",
    validate_subs=[sub(
        '    if typed.interface_symbols:\n'
        '        raise GeneratorError(f"{location(typed.interface_symbols[0])}: unsupported varying")\n',
        '    if False and typed.interface_symbols:\n'
        '        raise GeneratorError(f"{location(typed.interface_symbols[0])}: unsupported varying")\n',
    )],
    mechanical=False,
    note="A varying like v_texCoord still needs an emitter-side symbol "
         "mapping to become a usable C++ expression; this probe only proves "
         "structural admission, matching the roadmap's 'unmapped typed "
         "symbol v_texCoord' finding for wobble.",
))

# --- parameter direction (inout/out) and sampler-parameter admission ---
register(Patch(
    "inout_parameter_admission",
    "PROBE: allow parameter.direction in {in, inout, out} instead of only "
    "`in` (validator-only; the emitter has no by-reference parameter ABI).",
    validate_subs=[sub(
        '            if parameter.direction != "in":\n'
        '                raise GeneratorError(\n'
        '                    f"{typed.key}:{parameter.span.start_line}:{parameter.span.start_column}: "\n'
        '                    f"unsupported parameter direction {parameter.direction}")\n',
        '            if parameter.direction not in {"in", "inout", "out"}:\n'
        '                raise GeneratorError(\n'
        '                    f"{typed.key}:{parameter.span.start_line}:{parameter.span.start_column}: "\n'
        '                    f"unsupported parameter direction {parameter.direction}")\n'
        '            # PROBE: inout_parameter_admission\n',
    )],
    mechanical=False,
    note="No C++ by-reference parameter-passing convention exists in the "
         "emitter today; this is validator-only and will not itself produce "
         "correct C++.",
))
register(Patch(
    "sampler_parameter_admission",
    "PROBE: bypass the unauthenticated-sampler-parameter gate (only the "
    "Focus-Blur borrowed-sampler profile is admitted today); also set "
    "emit._TYPES['sampler2D'] to a placeholder so the emitter doesn't fail "
    "immediately on the type name.",
    validate_subs=[sub(
        '            if (parameter.type.kind == "sampler"\n'
        '                    and (authorized_focus_blur_proof is None\n'
        '                         or function is not authorized_focus_blur_proof.helper\n'
        '                         or not any(parameter is item for item in\n'
        '                                    authorized_focus_blur_proof.sampler_parameters))):\n'
        '                raise GeneratorError(\n'
        '                    f"{location(parameter)}: unsupported sampler parameter")\n',
        '            if False and (parameter.type.kind == "sampler"\n'
        '                    and (authorized_focus_blur_proof is None\n'
        '                         or function is not authorized_focus_blur_proof.helper\n'
        '                         or not any(parameter is item for item in\n'
        '                                    authorized_focus_blur_proof.sampler_parameters))):\n'
        '                raise GeneratorError(\n'
        '                    f"{location(parameter)}: unsupported sampler parameter")\n',
    )],
    table_deltas={"emit_types": {"sampler2D": "const Surface&"}},
    mechanical=False,
    note="mixer/distortion needs a general sampler2D function-parameter "
         "ABI, distinct from the single-key Focus-Blur borrowed-sampler "
         "profile already shipped.",
))

# --- non-const (mutable) global module state admission ---
register(Patch(
    "mutable_global_admission",
    "PROBE: bypass the `storage != 'const'` global-declaration rejection "
    "entirely for plain module-level globals (cellRefract/kaleido/"
    "synth/shape). This does NOT give the emitted C++ function persistent "
    "state across invocations -- it only proves what the validator/emitter "
    "would say next, which is the actual question this gate should answer.",
    validate_subs=[
        sub(
            '        if storage != "const" or declaration.type != FLOAT or declaration.initializer is None:\n'
            '            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")\n'
            '\n'
            '        def global_initializer(value) -> None:\n'
            '            if value.type != FLOAT:\n'
            '                raise GeneratorError(f"{location(value)}: unsupported global initializer type {value.type.display()}")\n'
            '            if value.kind == "literal":\n',
            '        if storage not in {"const", "global"} or (\n'
            '                storage == "const" and declaration.initializer is None):\n'
            '            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")\n'
            '        if storage == "global":\n'
            '            admitted_globals[declaration.symbol.id] = declaration\n'
            '            continue\n'
            '\n'
            '        def global_initializer(value) -> None:\n'
            '            if value.kind == "construct":\n'
            '                for child in value.children:\n'
            '                    global_initializer(child)\n'
            '                return\n'
            '            if value.kind == "literal":\n'
        ),
        sub(
            '        if (value.kind == "assign" and value.children\n'
            '                and targets_admitted_global(value.children[0])):\n'
            '            raise GeneratorError(f"{location(value)}: write to source const global")\n',
            '        pass  # PROBE: mutable_global_admission -- writes to a plain\n'
            '        # non-const `global`-storage declaration are the whole point of\n'
            '        # this family, not an error; skip the const-write ban entirely.\n',
        ),
        sub(
            '        reject_type(declaration.type, declaration)\n'
            '        if declaration.type.kind == "matrix":\n'
            '            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")\n'
            '        if declaration.symbol.storage not in {"uniform", "output", "const"}:\n'
            '            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")\n',
            '        reject_type(declaration.type, declaration)\n'
            '        if declaration.type.kind == "matrix" and declaration.symbol.storage not in {"const", "global"}:\n'
            '            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")\n'
            '        if declaration.symbol.storage not in {"uniform", "output", "const", "global"}:\n'
            '            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")\n',
        ),
    ],
    emit_globals_subs=[
        sub(
            '            if (declaration.symbol.storage != "const" or declaration.type.display() != "float"\n'
            '                    or declaration.initializer is None):\n'
            '                raise _error(self.program, declaration, "unsupported source global declaration")\n'
            '            dependencies: list[int] = []\n'
            '\n'
            '            def initializer(value: TypedExpression) -> None:\n'
            '                if value.type.display() != "float":\n'
            '                    raise _error(self.program, value, "unsupported source const global initializer type")\n'
            '                if value.kind == "literal":\n',
            '            if declaration.symbol.storage == "global":\n'
            '                self.source_global_dependencies[declaration.symbol.id] = ()\n'
            '                admitted.add(declaration.symbol.id)\n'
            '                continue\n'
            '            if (declaration.symbol.storage != "const"\n'
            '                    or declaration.initializer is None):\n'
            '                raise _error(self.program, declaration, "unsupported source global declaration")\n'
            '            dependencies: list[int] = []\n'
            '\n'
            '            def initializer(value: TypedExpression) -> None:\n'
            '                if value.kind == "construct":\n'
            '                    for child in value.children:\n'
            '                        initializer(child)\n'
            '                    return\n'
            '                if value.kind == "literal":\n'
        ),
    ],
    mechanical=False,
    note="Architecturally the biggest departure from the pure-per-pixel-"
         "function model (roadmap's own flag, unchanged by this probe): "
         "even if admission passed, the emitted C++ function has no thread-"
         "safe/re-entrant persistent-state ABI. This patch answers 'is this "
         "the ONLY remaining blocker' -- not 'is this safe to ship'.",
))

# --- loop-proof bypass (reveals whether a program ALSO needs other
# capabilities besides its loop shape) ---
register(Patch(
    "loop_proof_bypass",
    "PROBE: bypass BOTH the per-loop safety-charge raise and the program-"
    "level counted-for-proof raise (validator + emitter), to reveal whether "
    "a loop-proof-family program has a SECOND blocker once its loop-shape "
    "issue is set aside. Does not change what the frontend recorded as "
    "'unproved' -- only whether validate_capabilities/render_typed_cpp "
    "refuse to proceed past it.",
    validate_subs=[
        sub(
            '            if (proof.trip_count > 128 or proof.lexical_depth > 3\n'
            '                    or proof.effective_depth > 3 or proof.lexical_product > 4096\n'
            '                    or proof.entrypoint_charge > 4096\n'
            '                    or min(proof.trip_count, proof.lexical_depth, proof.effective_depth,\n'
            '                           proof.lexical_product, proof.entrypoint_charge) < 0):\n'
            '                raise GeneratorError(f"{location(actual)}: unsupported counted-for safety charge")\n',
            '            if False:\n'
            '                raise GeneratorError(f"{location(actual)}: unsupported counted-for safety charge")\n',
        ),
        sub(
            '    if not recomputed_program_proof.call_graph_acyclic:\n'
            '        offender = next((function for function in recomputed_functions if function.body), typed)\n'
            '        raise GeneratorError(\n'
            '            f"{location(offender)}: unsupported counted-for program proof")\n'
            '    if (recomputed_program_proof.unproved_loop_count\n'
            '            or recomputed_program_proof.max_effective_depth > 3\n'
            '            or recomputed_program_proof.max_lexical_product > 4096\n'
            '            or recomputed_program_proof.entrypoint_charge > 4096):\n',
            '    if not recomputed_program_proof.call_graph_acyclic:\n'
            '        offender = next((function for function in recomputed_functions if function.body), typed)\n'
            '        raise GeneratorError(\n'
            '            f"{location(offender)}: unsupported counted-for program proof (acyclic)")\n'
            '    if False and (recomputed_program_proof.unproved_loop_count\n'
            '            or recomputed_program_proof.max_effective_depth > 3\n'
            '            or recomputed_program_proof.max_lexical_product > 4096\n'
            '            or recomputed_program_proof.entrypoint_charge > 4096):\n',
        ),
    ],
    emit_loops_subs=[
        sub(
            '            if proof is not None and (\n'
            '                    proof.trip_count > 128 or proof.lexical_depth > 3\n'
            '                    or proof.effective_depth > 3 or proof.lexical_product > 4096\n'
            '                    or proof.entrypoint_charge > 4096\n'
            '                    or min(proof.trip_count, proof.lexical_depth, proof.effective_depth,\n'
            '                           proof.lexical_product, proof.entrypoint_charge) < 0):\n'
            '                raise _error(self.program, actual, "unsupported counted-for safety charge")\n',
            '            if False:\n'
            '                raise _error(self.program, actual, "unsupported counted-for safety charge")\n',
        ),
        sub(
            '        if not summary.call_graph_acyclic:\n'
            '            offender = next((function for function in recomputed if function.body), self.program)\n'
            '            raise _error(self.program, offender, "unsupported counted-for program proof")\n'
            '        if (summary.unproved_loop_count\n'
            '                or summary.max_effective_depth > 3\n'
            '                or summary.max_lexical_product > 4096\n'
            '                or summary.entrypoint_charge > 4096):\n',
            '        if not summary.call_graph_acyclic:\n'
            '            offender = next((function for function in recomputed if function.body), self.program)\n'
            '            raise _error(self.program, offender, "unsupported counted-for program proof (acyclic)")\n'
            '        if False and (summary.unproved_loop_count\n'
            '                or summary.max_effective_depth > 3\n'
            '                or summary.max_lexical_product > 4096\n'
            '                or summary.entrypoint_charge > 4096):\n',
        ),
    ],
    mechanical=False,
    note="This bypass does not make an unproved loop provably-bounded; a "
         "real fix needs new structural proof logic per loop shape "
         "(non-canonical for/while/parametric-bound/etc, see roadmap SS3.3). "
         "It exists here purely to reveal whether loop-proof-family programs "
         "have additional, unrelated downstream blockers.",
))

# ---------------------------------------------------------------------------
# Classification: map a raw error message's first line to a gate_id.
# ---------------------------------------------------------------------------

_BUILTIN_RE = re.compile(r"unsupported builtin (\w+)")

# When the SAME gate_id re-triggers after already being applied, it means
# that gate's patch covers one root cause of a shared error message but not
# another (e.g. "unsupported global declaration" is raised both for
# wrong-type CONST globals and for genuinely non-const mutable globals --
# two structurally different capabilities sharing one message). Escalate to
# a strictly-broader alternative patch instead of giving up immediately.
ESCALATIONS = {
    "global_admission": "mutable_global_admission",
}


def classify(message: str) -> str | None:
    if "unsupported global declaration" in message or \
       "unsupported source global declaration" in message or \
       "unsupported global initializer type" in message or \
       "unsupported source const global initializer type" in message:
        return "global_admission"
    if "unsupported global initializer expression binary" in message or \
       "unsupported source const global initializer" in message and "binary" in message:
        return "global_admission_shift"
    if "unsupported global initializer expression swizzle" in message:
        return "global_admission_swizzle"
    m = _BUILTIN_RE.search(message)
    if m:
        return f"builtin:{m.group(1)}"
    if "unsupported typed type mat3" in message or "unsupported typed type mat4" in message:
        return "matrix_type_admission"
    if "unsupported typed type bvec" in message:
        return "bvec_type_admission"
    if re.search(r"unsupported typed type \w+\[\d+\]", message):
        return "array_global_admission"
    if "unsupported binary operator &" in message:
        return "bitwise_and_admission"
    if "unsupported binary operator |" in message:
        return "bitwise_or_admission"
    if "unsupported unary operator ~" in message:
        return "unary_bitwise_not_admission"
    if "unsupported binary operator <<" in message:
        return "shift_left_admission"
    if "unsupported binary operator >>" in message:
        return "uvec_shift_by_vector"
    if "unsupported binary operator ^" in message:
        return "scalar_uint_xor_admission"
    if "unsupported typed expression index" in message:
        return "index_expression_admission"
    if "unsupported struct declaration" in message:
        return "struct_admission"
    if "unsupported uniform block" in message:
        return "uniform_block_admission"
    if "unsupported varying" in message:
        return "varying_admission"
    if "unsupported parameter direction" in message:
        return "inout_parameter_admission"
    if "unsupported sampler parameter" in message:
        return "sampler_parameter_admission"
    if "unsupported counted-for safety charge" in message or \
       "unsupported counted-for program proof" in message:
        return "loop_proof_bypass"
    return None


# ---------------------------------------------------------------------------
# Compile / apply machinery
# ---------------------------------------------------------------------------


def _apply_subs(original_src: str, subs) -> str:
    out = original_src
    for needle, replacement in subs:
        count = out.count(needle)
        if count != 1:
            raise AssertionError(f"needle not uniquely found (count={count}): {needle[:80]!r}")
        out = out.replace(needle, replacement, 1)
    return out


def _compile_function(src: str, module_namespace: dict, func_name: str, dedent=False):
    text = _dedent_from_class_body(src) if dedent else src
    namespace = dict(module_namespace)
    exec(compile(text, f"<patched {func_name}>", "exec"), namespace)
    return namespace[func_name]


def snapshot_state():
    return {
        "validate_id": id(gen.validate_capabilities),
        "validate_sha256": hashlib.sha256(inspect.getsource(gen.validate_capabilities).encode()).hexdigest(),
        "emit_globals_id": id(emit._Emitter._validate_source_globals),
        "emit_globals_sha256": hashlib.sha256(inspect.getsource(emit._Emitter._validate_source_globals).encode()).hexdigest(),
        "emit_expression_id": id(emit._Emitter.expression),
        "emit_expression_sha256": hashlib.sha256(inspect.getsource(emit._Emitter.expression).encode()).hexdigest(),
        "emit_loops_id": id(emit._Emitter._validate_counted_loops),
        "emit_loops_sha256": hashlib.sha256(inspect.getsource(emit._Emitter._validate_counted_loops).encode()).hexdigest(),
        "emit_type_id": id(emit._Emitter.type),
        "emit_type_sha256": hashlib.sha256(inspect.getsource(emit._Emitter.type).encode()).hexdigest(),
        "emit_param_type_id": id(emit._Emitter.function_parameter_type),
        "emit_param_type_sha256": hashlib.sha256(inspect.getsource(emit._Emitter.function_parameter_type).encode()).hexdigest(),
        "APPROVED_CAPABILITIES": gen.APPROVED_CAPABILITIES,
        "_BUILTINS": sorted(gen._BUILTINS),
        "APPROVED_TYPES": gen.APPROVED_TYPES,
        "APPROVED_BINARY_OPERATORS": gen.APPROVED_BINARY_OPERATORS,
        "_BUILTIN_NAMES": dict(emit._BUILTIN_NAMES),
        "_TYPES": dict(emit._TYPES),
        "_BINARY_OPERATORS": emit._BINARY_OPERATORS,
    }


def restored(pre, post) -> bool:
    return pre == post


def run_with_patches(typed, entry, patch_ids: list[str]):
    """Apply the UNION of patches named in patch_ids simultaneously (each
    patch's substitutions are applied to the PRISTINE original source, so any
    subset composes as long as needled regions are disjoint -- verified by
    the count==1 assertion inside _apply_subs). Restore everything in
    `finally`. Returns (result_dict, pre_snapshot, post_snapshot)."""
    pre = snapshot_state()

    old_validate = gen.validate_capabilities
    old_emit_globals = emit._Emitter._validate_source_globals
    old_emit_expression = emit._Emitter.expression
    old_emit_loops = emit._Emitter._validate_counted_loops
    old_emit_type = emit._Emitter.type
    old_emit_param_type = emit._Emitter.function_parameter_type
    old_caps, old_builtins = gen.APPROVED_CAPABILITIES, gen._BUILTINS
    old_types, old_binops = gen.APPROVED_TYPES, gen.APPROVED_BINARY_OPERATORS
    old_emit_names = dict(emit._BUILTIN_NAMES)
    old_emit_types = dict(emit._TYPES)
    old_emit_binops = emit._BINARY_OPERATORS

    patches = [PATCHES[pid] for pid in patch_ids]

    try:
        # 1. Table deltas first (live-lookup functions need this even if we
        # never recompile; recompiled functions need it captured in their
        # namespace snapshot, so it must happen before any exec()).
        extra_caps, extra_types, extra_binops = [], [], []
        extra_emit_names, extra_emit_types, extra_emit_binops = {}, [], []
        for patch in patches:
            deltas = patch.table_deltas
            extra_caps.extend(deltas.get("approved_capabilities", ()))
            extra_types.extend(deltas.get("approved_types", ()))
            extra_binops.extend(deltas.get("approved_binary_operators", ()))
            extra_emit_names.update(deltas.get("emit_builtin_names", {}))
            extra_emit_types.extend(deltas.get("emit_types", {}).items())
            extra_emit_binops.extend(deltas.get("emit_binary_operators", ()))
        if extra_caps:
            gen.APPROVED_CAPABILITIES = tuple(dict.fromkeys((*old_caps, *extra_caps)))
            gen._BUILTINS = frozenset(item for item in gen.APPROVED_CAPABILITIES if item not in {
                "assign", "blocks", "conditional", "constructors", "functions", "if",
                "integer-modulo", "mat2-vector-multiply", "multi-declarations",
                "scalar-vector-arithmetic", "swizzles", "uint-vector-bitwise",
                "counted-for-v1",
            } and item not in {p for p in old_caps if p not in old_builtins})
            # Simplify: _BUILTINS = old_builtins plus any newly-added cap that
            # isn't one of the known non-builtin structural capabilities.
            _NON_BUILTIN = {
                "assign", "blocks", "conditional", "constructors", "functions", "if",
                "integer-modulo", "mat2-vector-multiply", "multi-declarations",
                "scalar-vector-arithmetic", "swizzles", "uint-vector-bitwise",
                "counted-for-v1",
            }
            gen._BUILTINS = frozenset(old_builtins | {c for c in extra_caps if c not in _NON_BUILTIN})
        if extra_types:
            gen.APPROVED_TYPES = tuple(dict.fromkeys((*old_types, *extra_types)))
        if extra_binops:
            gen.APPROVED_BINARY_OPERATORS = tuple(dict.fromkeys((*old_binops, *extra_binops)))
        if extra_emit_names:
            emit._BUILTIN_NAMES.update(extra_emit_names)
        if extra_emit_types:
            emit._TYPES.update(dict(extra_emit_types))
        if extra_emit_binops:
            emit._BINARY_OPERATORS = frozenset({*old_emit_binops, *extra_emit_binops})

        # 2. Source patches: recompile only if at least one patch touches
        # that target.
        v_subs = [s for p in patches for s in p.validate_subs]
        eg_subs = [s for p in patches for s in p.emit_globals_subs]
        ee_subs = [s for p in patches for s in p.emit_expression_subs]
        el_subs = [s for p in patches for s in p.emit_loops_subs]
        et_subs = [s for p in patches for s in p.emit_type_subs]
        ept_subs = [s for p in patches for s in p.emit_param_type_subs]

        module_ns_gen = dict(gen.__dict__)
        module_ns_emit = dict(emit.__dict__)

        if v_subs:
            patched_src = _apply_subs(_ORIG_VALIDATE_SRC, v_subs)
            gen.validate_capabilities = _compile_function(
                patched_src, module_ns_gen, "validate_capabilities")
        if eg_subs:
            patched_src = _apply_subs(_ORIG_EMIT_GLOBALS_SRC, eg_subs)
            emit._Emitter._validate_source_globals = _compile_function(
                patched_src, module_ns_emit, "_validate_source_globals", dedent=True)
        if ee_subs:
            patched_src = _apply_subs(_ORIG_EMIT_EXPRESSION_SRC, ee_subs)
            emit._Emitter.expression = _compile_function(
                patched_src, module_ns_emit, "expression", dedent=True)
        if el_subs:
            patched_src = _apply_subs(_ORIG_EMIT_LOOPS_SRC, el_subs)
            emit._Emitter._validate_counted_loops = _compile_function(
                patched_src, module_ns_emit, "_validate_counted_loops", dedent=True)
        if et_subs:
            patched_src = _apply_subs(_ORIG_EMIT_TYPE_SRC, et_subs)
            emit._Emitter.type = _compile_function(
                patched_src, module_ns_emit, "type", dedent=True)
        if ept_subs:
            patched_src = _apply_subs(_ORIG_EMIT_PARAM_TYPE_SRC, ept_subs)
            emit._Emitter.function_parameter_type = _compile_function(
                patched_src, module_ns_emit, "function_parameter_type", dedent=True)

        try:
            gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES,
                                      source_hash=entry["raw_sha256"])
            validator = "pass"
        except Exception as error:  # noqa: BLE001
            validator = first_line(error)

        try:
            cpp = emit.render_typed_cpp(typed, typed.key, entry["raw_sha256"],
                                        "roadmap2_gate_chain", "bind_roadmap2_gate_chain")
            emitter = "pass"
            cpp_sha256 = hashlib.sha256(cpp.encode()).hexdigest()
            cpp_bytes = len(cpp.encode())
        except Exception as error:  # noqa: BLE001
            emitter = first_line(error)
            cpp_sha256 = None
            cpp_bytes = None
    finally:
        gen.validate_capabilities = old_validate
        emit._Emitter._validate_source_globals = old_emit_globals
        emit._Emitter.expression = old_emit_expression
        emit._Emitter._validate_counted_loops = old_emit_loops
        emit._Emitter.type = old_emit_type
        emit._Emitter.function_parameter_type = old_emit_param_type
        gen.APPROVED_CAPABILITIES = old_caps
        gen._BUILTINS = old_builtins
        gen.APPROVED_TYPES = old_types
        gen.APPROVED_BINARY_OPERATORS = old_binops
        emit._BUILTIN_NAMES.clear()
        emit._BUILTIN_NAMES.update(old_emit_names)
        emit._TYPES.clear()
        emit._TYPES.update(old_emit_types)
        emit._BINARY_OPERATORS = old_emit_binops

    post = snapshot_state()
    return ({"validator": validator, "emitter": emitter,
             "cpp_sha256": cpp_sha256, "cpp_bytes": cpp_bytes},
            pre, post)


def walk_chain(key: str, max_depth: int = MAX_DEPTH):
    entry, raw, defines, typed = load(key)
    chain = []
    active: list[str] = []
    restored_all = True
    for depth in range(max_depth + 1):
        result, pre, post = run_with_patches(typed, entry, active)
        ok = restored(pre, post)
        restored_all = restored_all and ok
        if result["validator"] == "pass" and result["emitter"] == "pass":
            chain.append({"depth": depth, "active_patches": list(active),
                          "result": result, "restored": ok, "status": "PASS"})
            return {"key": key, "chain": chain, "final_status": "PASS",
                    "restored_all": restored_all, "gates_needed": list(active)}
        message = result["validator"] if result["validator"] != "pass" else result["emitter"]
        gate_id = classify(message)
        if gate_id is not None and gate_id.startswith("builtin:"):
            name = gate_id.split(":", 1)[1]
            make_builtin_patch(name)  # ensure it's registered (dynamic)
        if gate_id is None or gate_id not in PATCHES:
            chain.append({"depth": depth, "active_patches": list(active), "result": result,
                          "restored": ok, "status": "NO_GENERIC_PATCH",
                          "blocker_message": message, "classified_gate": gate_id})
            return {"key": key, "chain": chain, "final_status": "NO_GENERIC_PATCH",
                    "restored_all": restored_all, "gates_needed": list(active),
                    "terminal_blocker": message, "terminal_gate": gate_id}
        if gate_id in active:
            escalation = ESCALATIONS.get(gate_id)
            if escalation is not None and escalation not in active:
                # global_admission and mutable_global_admission target the
                # SAME source region with mutually-exclusive replacement
                # text (const-only generalization vs. const-or-plain-global
                # admission) -- they cannot both be active, so escalate by
                # SWAPPING, not appending.
                active = [escalation if g == gate_id else g for g in active]
                chain.append({"depth": depth, "active_patches": list(active), "result": result,
                              "restored": ok, "status": "ESCALATED",
                              "blocker_message": message, "classified_gate": gate_id,
                              "escalated_to": escalation})
                continue
            # Classifier returned a gate we already applied -- means the
            # patch didn't clear it (bug in patch or genuinely insufficient).
            chain.append({"depth": depth, "active_patches": list(active), "result": result,
                          "restored": ok, "status": "PATCH_INSUFFICIENT",
                          "blocker_message": message, "classified_gate": gate_id})
            return {"key": key, "chain": chain, "final_status": "PATCH_INSUFFICIENT",
                    "restored_all": restored_all, "gates_needed": list(active),
                    "terminal_blocker": message, "terminal_gate": gate_id}
        chain.append({"depth": depth, "active_patches": list(active), "result": result,
                      "restored": ok, "status": "BLOCKED", "blocker_message": message,
                      "classified_gate": gate_id})
        active.append(gate_id)
    return {"key": key, "chain": chain, "final_status": "DEEP_GT_8",
            "restored_all": restored_all, "gates_needed": list(active)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--keys", nargs="*", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    keys = args.keys if args.keys else UNPORTED_KEYS
    rows = []
    for key in keys:
        try:
            rows.append(walk_chain(key))
        except Exception as error:  # noqa: BLE001
            rows.append({"key": key, "final_status": "PROBE_ERROR",
                        "error": f"{type(error).__name__}: {error}",
                        "traceback": traceback.format_exc()})
            # Sanity: make sure module state is sane after an unexpected
            # failure -- re-snapshot against pristine originals.
            gen.validate_capabilities = gen.validate_capabilities
    payload = {
        "schema": "noisemaker-for-cpp.roadmap2.gate-chain.v2",
        "corpus_revision": REVISION,
        "unported_count": len(UNPORTED_KEYS),
        "keys_probed": len(keys),
        "max_depth": MAX_DEPTH,
        "rows": rows,
    }
    out = Path(args.out) if args.out else Path(__file__).with_name("gate-chain-all-output.json")
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(out)
