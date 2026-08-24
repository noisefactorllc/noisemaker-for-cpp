"""Prepared, source-bound frontend admission for ``synth/testPattern``.

This module is intentionally a frontend-only lane.  It does not register a
live typed-slice row and does not widen the global type, builtin, or operator
vocabularies.  The future integration row must consume this complete proof
before it admits Test Pattern's two local arrays, one const global table, the
three dynamic *read* indexes, the bounded digit-store index, or ``round(vec2)``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import NamedTuple

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


KEY = "synth/testPattern:testPattern"
PROFILE = "testpattern-frontend-admission-v1"
TESTPATTERN_KEY = KEY
TESTPATTERN_PROFILE = PROFILE

# Prepared means the record is complete and independently authenticatable, but
# the key is deliberately absent from the live carrier registry until the
# integration lane lands the generated row and its companions.
KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = (KEY,)
PREPARED_PROFILES = {KEY: PROFILE}
TESTPATTERN_FRONTEND_KEYS = frozenset(PREPARED_PROFILES)

ALLOWED_ROW_FIELDS = {
    KEY: frozenset({"defines", "program_key", "testpattern_profile"}),
}
PREPARED_ROW_FIELDS = dict(ALLOWED_ROW_FIELDS)

# The source lane owns the array/index/round proof.  The future row is
# intentionally companion-free here: any required bitwise, counted-loop, or
# materialization companion must be measured independently by the integration
# lane and added to this tuple before the key moves to KEYS.
REQUIRED_COMPANION_PROFILES = {KEY: ()}

RAW_BYTES = 5919
RAW_SHA256 = "f913300a1312c6630d56fa1cc2faf2cb17fe0643d832473fdec7b66dd373cb20"
NORMALIZED_BYTES = 4450
NORMALIZED_SHA256 = "1f150d5cfdc5c037a460e081821f44e835095d63b4b20b67352999eadc8115aa"
FUNCTIONS_SHA256 = "4387188dbfcfd35c2918667c921bbe6c75068429f19e5768b028b4f1456061fc"
WHOLE_SHA256 = "c75f9c139f901d965d051f4c24eb95b02103fc86655641873c31044aa9a567bf"
INTERFACE_SHA256 = "cdc5ea07157c144ca39a20a853a6d105f83bcaa49e5e25681737caa4edec5c3a"

# The source has exactly five runtime bindings.  Keep the source and native
# spellings separate: the former authenticates the GLSL declarations while
# the latter is the ABI exposed by the C++ runtime/oracle.
BINDING_NAMES = ("resolution", "tileOffset", "fullResolution", "gridSize",
                 "pattern")
SOURCE_BINDING_ABI = (
    ("resolution", "vec2"), ("tileOffset", "vec2"),
    ("fullResolution", "vec2"), ("gridSize", "int"), ("pattern", "int"),
)
RUNTIME_BINDING_ABI = (
    ("resolution", "Vec2"), ("tileOffset", "Vec2"),
    ("fullResolution", "Vec2"), ("gridSize", "int32"),
    ("pattern", "int32"),
)
BINDING_DEFAULTS = (("gridSize", 4), ("pattern", 0))
# The canonical source metadata says gridSize min=1, but the authoritative
# oracle intentionally exercises gridSize=0, which the source clamps to one.
# This is therefore an execution preflight range, not a UI metadata range.
GRID_SIZE_RANGE = (0, 16)
PATTERN_RANGE = (0, 6)
_BINDING_ROWS = (
    (1, "resolution", "vec2", "uniform", False),
    (2, "tileOffset", "vec2", "uniform", False),
    (3, "fullResolution", "vec2", "uniform", False),
    (4, "gridSize", "int", "uniform", False),
    (5, "pattern", "int", "uniform", False),
)
_RESOURCES = ((BINDING_NAMES), (), ("fragColor",), False, False)

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)


class ArrayRecord(NamedTuple):
    name: str
    symbol_id: int
    type_name: str
    element_type: str
    extent: int
    storage: str
    writable: bool
    span: str
    sha256: str
    initializer_sha256: str | None


class IndexRecord(NamedTuple):
    owner_id: int
    owner_name: str
    array_name: str
    array_symbol_id: int
    index_symbol_ids: tuple[int, ...]
    span: str
    sha256: str
    node: TypedExpression


class BindingPreflight(NamedTuple):
    names: tuple[str, ...]
    source_abi: tuple[tuple[str, str], ...]
    runtime_abi: tuple[tuple[str, str], ...]
    defaults: tuple[tuple[str, int], ...]
    grid_size_range: tuple[int, int]
    pattern_range: tuple[int, int]
    resources: tuple


class FrontendProof(NamedTuple):
    program_key: str
    global_array: ArrayRecord
    local_arrays: tuple[str, ...]
    dynamic_indexes: tuple[IndexRecord, ...]
    digit_store_index: IndexRecord
    round_node: TypedExpression
    round_span: str
    loop_bounds: tuple[tuple[int, int], ...]
    num_digits_range: tuple[int, int]
    binding_preflight: BindingPreflight
    dynamic_loop_owner: tuple[int, str]
    dynamic_loop_bound_symbol_id: int
    dynamic_loop_bound_range: tuple[int, int]
    consumed_objects: tuple[object, ...]

    @property
    def dynamic_index_names(self) -> tuple[str, ...]:
        return tuple(item.array_name for item in self.dynamic_indexes)

    @property
    def dynamic_index_spans(self) -> tuple[str, ...]:
        return tuple(item.span for item in self.dynamic_indexes)


class _Lock(NamedTuple):
    owner_id: int
    owner_name: str
    array_name: str
    array_symbol_id: int
    index_symbol_ids: tuple[int, ...]
    span: str
    sha256: str


_DYNAMIC_INDEX_LOCKS = (
    _Lock(30, "sampleGlyph", "GLYPH", 7, (8,),
          "30:14-30:26",
          "6fec18a382551e166e6d8d9dc101f9b0259cd30cf043d5e372215f2c2d512a83"),
    _Lock(29, "renderNumber", "digits", 72, (65, 75),
          "74:25-74:50",
          "592a1ea3542361c6aecb24bb09c01a7b3227815091a200e31bc5d4c335d9f66e"),
    _Lock(22, "colorBars", "colors", 44, (43,),
          "121:17-121:28",
          "cd36fee1d3b7d17325642f70b372a0aa53f7796b21804a6dcb4ecd731e5c4db5"),
)
_DIGIT_STORE_LOCK = _Lock(
    29, "renderNumber", "digits", 72, (74,), "56:9-56:18",
    "1647c46e9c08c02c06fe4920b479394f6d98090f10d1d834b8242949b29f9bab")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = value.span
    return f"{span.start_line}:{span.start_column}-{span.end_line}:{span.end_column}"


def _whole(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


_BINDING_PREFLIGHT = BindingPreflight(
    BINDING_NAMES, SOURCE_BINDING_ABI, RUNTIME_BINDING_ABI,
    BINDING_DEFAULTS, GRID_SIZE_RANGE, PATTERN_RANGE, _RESOURCES)


def preflight_testpattern_bindings(
        program: TypedProgram, bindings: Mapping[str, object] | None = None
        ) -> BindingPreflight:
    """Authenticate Test Pattern's closed five-binding execution contract.

    ``bindings`` is optional so the generator can authenticate the static
    resource ABI without inventing a render input.  When supplied, it must be
    exactly the five runtime keys and only the two integer controls are
    value-checked here; surface/Vec2 validation remains the runtime's job.
    ``gridSize=0`` is intentionally accepted because the source clamps it to
    one and the frozen oracle covers that behavior.
    """
    if program.key != KEY:
        raise _fail("binding or resource key mismatch")
    declarations = tuple(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable)
        for item in program.declarations[:len(_BINDING_ROWS)])
    if declarations != _BINDING_ROWS:
        raise _fail("binding or resource declaration mismatch")
    resources = program.resources
    actual_resources = (resources.uniforms, resources.samplers,
                        resources.outputs, resources.uses_texture,
                        resources.uses_derivatives)
    if actual_resources != _RESOURCES:
        raise _fail("binding or resource profile mismatch")
    if bindings is not None:
        if not isinstance(bindings, Mapping) or tuple(bindings) != BINDING_NAMES:
            raise _fail("binding or resource names mismatch")
        grid_size = bindings["gridSize"]
        pattern = bindings["pattern"]
        if type(grid_size) is not int:
            raise _fail("gridSize binding type mismatch")
        if type(pattern) is not int:
            raise _fail("pattern binding type mismatch")
        if not GRID_SIZE_RANGE[0] <= grid_size <= GRID_SIZE_RANGE[1]:
            raise _fail("gridSize binding outside 0..16")
        if not PATTERN_RANGE[0] <= pattern <= PATTERN_RANGE[1]:
            raise _fail("pattern binding outside 0..6")
    return _BINDING_PREFLIGHT


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _program_nodes(program: TypedProgram):
    # Global initializers are part of the census.  A function-only walker would
    # let a forged array/index site hide in GLYPH's initializer.
    for declaration in program.declarations:
        if declaration.initializer is not None:
            yield None, declaration, declaration.initializer
            for value in _walk_expression(declaration.initializer):
                if value is not declaration.initializer:
                    yield None, declaration, value
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                yield function, None, value


def _function_inventory(program: TypedProgram) -> tuple:
    return tuple((
        function.signature.id, function.name, function.return_type.display(),
        len(function.parameters), len(function.body), _span(function), _sha(function),
    ) for function in program.functions)


def _array_record(value, *, initializer_sha256: str | None) -> ArrayRecord:
    typ = value.type
    if typ.kind != "array" or typ.element is None or typ.size is None:
        raise _fail("array declaration shape mismatch")
    symbol = value.symbol
    if (symbol is None
            or getattr(value, "symbol_id", symbol.id if symbol else None)
            != symbol.id):
        raise _fail("array declaration symbol identity mismatch")
    return ArrayRecord(
        symbol.name, symbol.id, typ.display(), typ.element.display(), typ.size,
        symbol.storage, symbol.writable, _span(value), _sha(value),
        initializer_sha256,
    )


def _declaration_nodes(program: TypedProgram):
    result = [(None, declaration) for declaration in program.declarations
              if declaration.type.kind == "array"]
    for function, _, value in _program_nodes(program):
        if (value.kind == "declaration" and value.type.kind == "array"):
            result.append((function, value))
    return result


def _find_function(program: TypedProgram, function_id: int, name: str) -> TypedFunction:
    matches = [item for item in program.functions
               if item.signature.id == function_id and item.name == name]
    if len(matches) != 1:
        raise _fail(f"{name} function identity mismatch")
    return matches[0]


def _lock_index(function: TypedFunction, lock: _Lock) -> IndexRecord:
    candidates = [value for statement in function.body
                  for value in _walk_statement(statement)
                  if value.kind == "index"]
    matches = [value for value in candidates if _span(value) == lock.span]
    if len(matches) != 1:
        raise _fail(f"{lock.array_name} index site missing or duplicated")
    value = matches[0]
    if (value.type.display() not in {"int", "vec3"}
            or len(value.children) != 2
            or value.children[0].kind != "id"
            or value.children[0].symbol_id != lock.array_symbol_id
            or value.children[0].symbol is None
            or value.children[0].symbol.id != lock.array_symbol_id
            or value.children[1].kind not in {"id", "binary"}
            or _sha(value) != lock.sha256):
        raise _fail(f"{lock.array_name} index site identity mismatch")
    index_ids = tuple(
        child.symbol_id for child in _walk_expression(value.children[1])
        if child.kind == "id" and child.symbol_id is not None)
    if index_ids != lock.index_symbol_ids:
        raise _fail(f"{lock.array_name} index expression mismatch")
    return IndexRecord(
        lock.owner_id, lock.owner_name, lock.array_name, lock.array_symbol_id,
        index_ids, lock.span, lock.sha256, value,
    )


def _authenticate(program: TypedProgram, source_hash: str | None,
                  profile: str | None) -> FrontendProof:
    if profile != PROFILE:
        raise _fail("exact prepared profile carrier required")
    if program.key != KEY:
        raise _fail("profile on foreign key")
    if source_hash != RAW_SHA256:
        raise _fail("exact caller source hash required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or program.body_status != "analyzed"
            or program.preprocessor_defines != ()
            or _sha(program.functions) != FUNCTIONS_SHA256
            or _whole(program) != WHOLE_SHA256
            or _interface(program) != INTERFACE_SHA256):
        raise _fail("raw, normalized, function, whole, or interface fingerprint mismatch")
    if any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")

    arrays = _declaration_nodes(program)
    if len(arrays) != 3:
        raise _fail("array declaration census mismatch")
    globals_ = [item for function, item in arrays if function is None]
    if len(globals_) != 1:
        raise _fail("GLYPH must be the only file-scope array")
    glyph = globals_[0]
    if (glyph.symbol.name != "GLYPH" or glyph.symbol.storage != "const"
            or glyph.symbol.writable or glyph.type.display() != "int[10]"
            or glyph.initializer is None
            or glyph.initializer.kind != "construct"
            or glyph.initializer.constructor_type.display() != "int[10]"
            or len(glyph.initializer.children) != 10
            or any(child.kind != "literal" or child.type.display() != "int"
                   for child in glyph.initializer.children)):
        raise _fail("GLYPH declaration or literal initializer mismatch")
    glyph_values = tuple(child.literal_value for child in glyph.initializer.children)
    if glyph_values != (31599, 9362, 29671, 29391, 23497,
                        31183, 31215, 29257, 31727, 31695):
        raise _fail("GLYPH literal payload mismatch")
    global_record = _array_record(
        glyph, initializer_sha256=_sha(glyph.initializer))

    local_records = {}
    for function, value in arrays:
        if function is None:
            continue
        name = value.symbol.name
        local_records[name] = (function, value)
    if set(local_records) != {"digits", "colors"}:
        raise _fail("local array declaration census mismatch")
    digits_fn, digits = local_records["digits"]
    colors_fn, colors = local_records["colors"]
    if (digits_fn.signature.id != 29 or digits.type.display() != "int[3]"
            or digits.symbol.storage != "local" or not digits.symbol.writable
            or digits.children):
        raise _fail("digits local array contract mismatch")
    if (colors_fn.signature.id != 22 or colors.type.display() != "vec3[8]"
            or colors.symbol.storage != "local" or not colors.symbol.writable
            or len(colors.children) != 1
            or colors.children[0].kind != "construct"
            or len(colors.children[0].children) != 8
            or any(child.kind != "construct" or child.type.display() != "vec3"
                   or len(child.children) != 3
                   or any(lane.kind != "literal" for lane in child.children)
                   for child in colors.children[0].children)):
        raise _fail("colors local array contract mismatch")

    sample = _find_function(program, 30, "sampleGlyph")
    render = _find_function(program, 29, "renderNumber")
    bars = _find_function(program, 22, "colorBars")
    dot = _find_function(program, 24, "dotGrid")
    dynamic = tuple(_lock_index(
        {30: sample, 29: render, 22: bars}[lock.owner_id], lock)
        for lock in _DYNAMIC_INDEX_LOCKS)
    digit_store = _lock_index(render, _DIGIT_STORE_LOCK)
    all_indexes = [value for function, _, value in _program_nodes(program)
                   if function is not None and value.kind == "index"]
    if len(all_indexes) != 4 or set(map(id, all_indexes)) != {
            id(item.node) for item in (*dynamic, digit_store)}:
        raise _fail("unexpected extra or missing index site")

    # The first loop is already a counted-for proof.  The second is the
    # source-specific dynamic bound: numDigits is initialized to 1 and can
    # only become 2 or 3 under the two monotone predicates.
    loops = [statement for statement in render.body if statement.kind == "for"]
    if len(loops) != 2:
        raise _fail("renderNumber loop census mismatch")
    first, second = loops
    if (first.loop_proof is None or first.loop_proof.start_value != 0
            or first.loop_proof.bound_value != 3
            or first.loop_proof.comparison != "<"
            or first.loop_proof.update != "++"
            or first.loop_proof.trip_count != 3):
        raise _fail("digit extraction loop bound mismatch")
    if (second.loop_proof is not None or len(second.expressions) != 2
            or second.expressions[0].kind != "binary"
            or second.expressions[0].operator != "<"
            or second.expressions[0].children[1].kind != "id"
            or second.expressions[0].children[1].symbol_id != 65
            or second.expressions[1].kind != "post"
            or second.expressions[1].operator != "++"):
        raise _fail("numDigits loop bound mismatch")
    num_digits_ids = [value for statement in render.body
                      for value in _walk_statement(statement)
                      if value.kind == "id" and value.symbol_id == 65]
    if len(num_digits_ids) < 5:
        raise _fail("numDigits identity census mismatch")
    # Exact source shape: declaration 1, then two guarded assignments to 2/3.
    if (render.body[0].expressions[0].symbol_id != 65
            or render.body[0].expressions[0].children[0].literal_value != 1
            or render.body[1].children[0].expressions[0].children[0].symbol_id != 65
            or render.body[1].children[0].expressions[0].children[1].literal_value != 2
            or render.body[2].children[0].expressions[0].children[0].symbol_id != 65
            or render.body[2].children[0].expressions[0].children[1].literal_value != 3):
        raise _fail("numDigits range proof mismatch")

    round_nodes = [value for function, _, value in _program_nodes(program)
                   if function is not None and value.kind == "builtin"
                   and value.callee == "round"]
    if len(round_nodes) != 1:
        raise _fail("round(vec2) census mismatch")
    round_node = round_nodes[0]
    if (round_node.type.display() != "vec2" or len(round_node.children) != 1
            or round_node.children[0].kind != "id"
            or round_node.children[0].symbol_id != 51
            or _span(round_node) != "171:20-171:33"
            or _sha(round_node) != "1ce16cb8d94238e87180c761e5606766bb1a119222f96a6bc30cfa32f90ee70f"):
        raise _fail("round(vec2) site identity mismatch")

    consumed = (
        glyph, glyph.initializer, digits, colors, colors.children[0],
        *(item.node for item in dynamic), digit_store.node, round_node,
        first, second,
    )
    if len(consumed) != len({id(item) for item in consumed}):
        raise _fail("frontend proof visitation ledger is not disjoint")
    binding_preflight = preflight_testpattern_bindings(program)
    return FrontendProof(
        KEY, global_record, ("digits", "colors"), dynamic, digit_store,
        round_node, _span(round_node), ((0, 3), (0, 3)), (1, 3),
        binding_preflight, (29, "renderNumber"), 65, (1, 3), consumed)


def authenticate_testpattern_frontend(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> FrontendProof:
    return _authenticate(program, source_hash, profile)


def apply_testpattern_frontend(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    _authenticate(program, source_hash, profile)
    return program


def allowed_row_fields(key: str) -> frozenset[str]:
    fields = ALLOWED_ROW_FIELDS.get(key) or PREPARED_ROW_FIELDS.get(key)
    if fields is None:
        raise _fail("unknown Test Pattern row")
    return fields


__all__ = (
    "KEY", "PROFILE", "TESTPATTERN_KEY", "TESTPATTERN_PROFILE", "KEYS",
    "PROFILES", "PREPARED_KEYS", "PREPARED_PROFILES",
    "TESTPATTERN_FRONTEND_KEYS", "ALLOWED_ROW_FIELDS", "PREPARED_ROW_FIELDS",
    "REQUIRED_COMPANION_PROFILES", "RAW_BYTES", "RAW_SHA256",
    "NORMALIZED_BYTES", "NORMALIZED_SHA256", "FUNCTIONS_SHA256", "WHOLE_SHA256",
    "INTERFACE_SHA256", "BINDING_NAMES", "SOURCE_BINDING_ABI",
    "RUNTIME_BINDING_ABI", "BINDING_DEFAULTS", "GRID_SIZE_RANGE",
    "PATTERN_RANGE", "BindingPreflight", "ArrayRecord", "IndexRecord",
    "FrontendProof",
    "authenticate_testpattern_frontend", "apply_testpattern_frontend",
    "preflight_testpattern_bindings", "allowed_row_fields",
)
