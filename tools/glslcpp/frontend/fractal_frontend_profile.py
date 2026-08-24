"""Prepared, source-bound frontend admission for ``classicNoisedeck/fractal``.

This module authenticates the exact corpus program, its GLSL interface, and
the canonical ``iterations`` metadata contract. It carries the counted-loop
proof and runtime range into the generator/emitter without registering a live
row or changing shared semantics for other programs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from dataclasses import replace
import hashlib

from . import loop_proof as _loop_proof
from .loop_proof import (CountedLoopProof, attach_counted_loop_proofs,
                          clear_counted_loop_proofs,
                          summarize_counted_loop_proofs)
from .runtime_loop_bound_profile import (RuntimeLoopBoundContract,
                                         RuntimeScalarBoundSeed)
from .typed_ir import TypedExpression, TypedProgram, TypedStatement

KEY = "classicNoisedeck/fractal:fractal"
PROFILE = "fractal-frontend-admission-v1"
KEYS: tuple[str, ...] = ()
PREPARED_KEYS = (KEY,)
PROFILES = {KEY: PROFILE}
PREPARED_PROFILES = {KEY: PROFILE}
ALLOWED_ROW_FIELDS = {KEY: frozenset({"defines", "program_key", "fractal_frontend_profile"})}
REQUIRED_COMPANION_PROFILES = {KEY: ()}

RAW_BYTES = 10067
RAW_SHA256 = "a73c8044185be58e3ae1b0f14b954dbaa7bb8852290b821dba44167fee5e037b"
NORMALIZED_BYTES = 9061
NORMALIZED_SHA256 = "d30bc823bc8beba8b818b13724ddc980e52c3545765a5ea38766fab41cf3aea6"
FUNCTIONS_SHA256 = "a08043b809f87dcc7f2a0a8f43f5b3dd63bfb68450348a693bbe309c9be7c5fb"
WHOLE_SHA256 = "5ce86aceb917477e3009af39caf0de1d444d59333bbde66f006c5a2e94c5eb2e"
INTERFACE_SHA256 = "0cb82dafe2f8d9a48703ef2e82a804a0a5f8d1febdba8be766b9ee7a83db3e3b"

SOURCE_UNIFORMS = (
    ("time", "float"), ("resolution", "vec2"), ("tileOffset", "vec2"),
    ("fullResolution", "vec2"), ("type", "int"), ("symmetry", "int"),
    ("offsetX", "float"), ("offsetY", "float"), ("centerX", "float"),
    ("centerY", "float"), ("zoomAmt", "float"), ("speed", "float"),
    ("rotation", "float"), ("iterations", "int"), ("mode", "int"),
    ("colorMode", "int"), ("paletteMode", "int"),
    ("paletteOffset", "vec3"), ("paletteAmp", "vec3"),
    ("paletteFreq", "vec3"), ("palettePhase", "vec3"),
    ("cyclePalette", "int"), ("rotatePalette", "float"),
    ("repeatPalette", "float"), ("hueRange", "float"),
    ("levels", "float"), ("bgColor", "vec3"), ("bgAlpha", "float"),
    ("cutoff", "float"),
)
RUNTIME_UNIFORM_ABI = tuple(
    (name, {"float": "number", "int": "int32", "vec2": "Vec2", "vec3": "Vec3"}[kind])
    for name, kind in SOURCE_UNIFORMS
)
OUTPUT_ABI = ("fragColor", "vec4", "Vec4", "output")
MATRIX_CONSTANTS = ("fwdA", "fwdB", "invB", "invA")
FUNCTION_NAMES = (
    "divide", "fpx", "fx", "hsv2rgb", "julia", "linearToSrgb",
    "linear_srgb_from_oklab", "main", "mandelbrot", "map", "newton",
    "offset", "oklab_from_linear_srgb", "pal", "periodicFunction", "rgb2hsv",
    "rotate2D",
)
LOOP_SPANS = (
    ("julia", "261:5-269:6"), ("linearToSrgb", "119:5-125:6"),
    ("mandelbrot", "301:5-310:6"), ("newton", "220:5-231:6"),
)
UNPROVED_LOOP_SPANS = LOOP_SPANS[0:1] + LOOP_SPANS[2:]


@dataclass(frozen=True, slots=True)
class FractalIterationContract:
    """The one metadata record shared by proof maxima and the runtime guard."""

    uniform_name: str
    uniform_type: str
    minimum: int
    default: int
    maximum: int
    metadata_ui: tuple[tuple[str, str], ...]

    def metadata_record(self) -> dict[str, object]:
        return {
            "default": self.default,
            "max": self.maximum,
            "min": self.minimum,
            "type": self.uniform_type,
            "ui": dict(self.metadata_ui),
            "uniform": self.uniform_name,
        }

    def loop_maximum(self, function_name: str) -> int:
        if function_name == "julia":
            return self.maximum * 2
        if function_name in {"mandelbrot", "newton"}:
            return self.maximum
        raise ValueError(f"{PROFILE}: unknown iteration loop {function_name}")


@dataclass(frozen=True, slots=True)
class FractalModeContract:
    """The source domain for the two mode branches in fractal helpers."""

    uniform_name: str
    uniform_type: str
    choices: tuple[tuple[str, int], ...]
    default: int
    metadata_ui: tuple[tuple[str, str], ...]

    @property
    def minimum(self) -> int:
        return min(value for _name, value in self.choices)

    @property
    def maximum(self) -> int:
        return max(value for _name, value in self.choices)

    def metadata_record(self) -> dict[str, object]:
        return {
            "choices": dict(self.choices),
            "default": self.default,
            "type": self.uniform_type,
            "ui": dict(self.metadata_ui),
            "uniform": self.uniform_name,
        }


ITERATIONS_CONTRACT = FractalIterationContract(
    "iterations", "int", 1, 50, 50,
    (("category", "rendering"), ("control", "slider"),
     ("label", "iterations")),
)
MODE_CONTRACT = FractalModeContract(
    "mode", "int", (("iter", 0), ("z", 1)), 0,
    (("category", "rendering"), ("control", "dropdown"),
     ("label", "mode")),
)
TERMINAL_FALLBACK_FUNCTIONS = ("julia", "mandelbrot", "newton")


LOOP_BOUNDS = {
    "julia": ("261:5-269:6", ITERATIONS_CONTRACT.loop_maximum("julia"),
              "fractal-iterations-times-two"),
    "newton": ("220:5-231:6", ITERATIONS_CONTRACT.loop_maximum("newton"),
               "fractal-iterations"),
    "mandelbrot": ("301:5-310:6",
                   ITERATIONS_CONTRACT.loop_maximum("mandelbrot"),
                   "fractal-float-iterations"),
}
LINEAR_SRGB_INDEX_SPANS = (
    "120:13-120:22", "121:13-121:20", "121:23-121:32",
    "123:13-123:20", "123:35-123:44")
MATRIX_CONSTRUCTOR_SPAN = "305:13-305:31"
ALPHA_BRANCH_SPAN = "341:5-344:6"
ALPHA_ASSIGNMENT_SPAN = "342:9-342:50"
ALPHA_CONSTRUCT_SPAN = "342:21-342:50"
ALPHA_PRODUCT_SPAN = "342:35-342:49"
ALPHA_LITERAL_SPAN = "342:45-342:49"
ALPHA_BG_SYMBOL_ID = 28
ALPHA_BG_SYMBOL_NAME = "bgAlpha"
ALPHA_LITERAL_SPELLING = "0.01"
ALPHA_LITERAL_VALUE = 0.01
HSV_FUNCTION_NAME = "hsv2rgb"
HSV_FUNCTION_SIGNATURE_ID = 60
HSV_PARAMETER_NAME = "hsv"
HSV_PARAMETER_SYMBOL_ID = 40
HSV_CALL_SPANS = ("174:17-174:31", "369:21-369:47")
HUE_SCALE_ASSIGNMENT_SPAN = "368:9-368:31"
HUE_SCALE_PRODUCT_SPAN = "368:15-368:30"
HUE_SCALE_LITERAL_SPAN = "368:26-368:30"
HUE_SCALE_TARGET_SYMBOL_ID = 104
HUE_SCALE_UNIFORM_SYMBOL_ID = 25
DISTANCE_FRACT_ASSIGNMENT_SPAN = "353:5-353:17"
DISTANCE_FRACT_BUILTIN_SPAN = "353:9-353:17"
DISTANCE_MAP_ASSIGNMENT_SPAN = "352:5-352:49"
DISTANCE_MAP_SUM_SPAN = "352:9-352:49"
DISTANCE_REPEAT_PRODUCT_SPAN = "352:9-352:26"
DISTANCE_ROTATE_PRODUCT_SPAN = "352:29-352:49"
DISTANCE_ROTATE_LITERAL_SPAN = "352:45-352:49"
PALETTE_FUNCTION_NAME = "pal"
PALETTE_FUNCTION_SIGNATURE_ID = 70
PALETTE_PARAMETER_NAME = "t"
PALETTE_PARAMETER_SYMBOL_ID = 49
PALETTE_CALL_SPAN = "365:21-365:27"
NEWTON_FUNCTION_NAME = "newton"
NEWTON_FUNCTION_SIGNATURE_ID = 67
NEWTON_PARAMETER_NAME = "st"
NEWTON_PARAMETER_SYMBOL_ID = 54
NEWTON_CALL_SPAN = "336:13-336:23"
NEWTON_BODY_SPANS = (
    "205:5-205:40", "206:5-206:64", "207:5-207:47",
    "209:5-209:48", "210:5-210:59", "211:5-211:59",
    "213:5-213:28", "214:5-214:28", "216:5-216:17",
    "217:5-217:22", "218:5-218:14", "220:5-231:6",
    "233:5-237:6",
)
JULIA_FUNCTION_SPAN = "243:1-282:2"
JULIA_FUNCTION_SIGNATURE_ID = 61
JULIA_PARAMETER_NAME = "st"
JULIA_PARAMETER_SYMBOL_ID = 55
JULIA_CALL_SPAN = "334:13-334:22"
JULIA_CALL_SIGNATURE_ID = 61
JULIA_CALL_PARAMETER_SYMBOL_ID = 102
JULIA_BODY_SPANS = (
    "245:5-245:53", "246:5-246:12", "247:5-247:53", "248:5-248:58",
    "249:5-249:61", "250:5-250:61", "251:5-251:103", "253:5-253:33",
    "254:5-254:77", "256:5-256:57", "257:5-257:57", "259:5-259:14",
    "260:5-260:37", "261:5-269:6", "272:5-274:6", "276:5-281:6",
)
JULIA_Z_DECLARATION_SPAN = "246:5-246:12"
JULIA_INITIAL_STORE_SPANS = ("256:5-256:57", "257:5-257:57")
JULIA_LOOP_SPAN = "261:5-269:6"
JULIA_ITERATION_X_DECLARATION_SPAN = "263:9-263:49"
JULIA_ITERATION_Y_DECLARATION_SPAN = "264:9-264:49"
JULIA_ESCAPE_GUARD_SPAN = "266:9-266:41"
JULIA_STATE_STORE_SPANS = ("267:9-267:17", "268:9-268:17")
JULIA_CUTOFF_GUARD_SPAN = "272:5-274:6"
JULIA_MODE_GUARD_SPAN = "276:5-281:6"
JULIA_MODE_ZERO_RETURN_SPAN = "277:9-277:48"
JULIA_MODE_ONE_RETURN_SPAN = "280:9-280:26"
JULIA_NUMBER_ANCHOR_SPANS = (
    JULIA_Z_DECLARATION_SPAN, *JULIA_INITIAL_STORE_SPANS,
    JULIA_LOOP_SPAN, JULIA_ITERATION_X_DECLARATION_SPAN,
    JULIA_ITERATION_Y_DECLARATION_SPAN, JULIA_ESCAPE_GUARD_SPAN,
    *JULIA_STATE_STORE_SPANS, JULIA_CUTOFF_GUARD_SPAN,
    JULIA_MODE_GUARD_SPAN, JULIA_MODE_ZERO_RETURN_SPAN,
    JULIA_MODE_ONE_RETURN_SPAN,
)
MANDELBROT_FUNCTION_SPAN = "287:1-322:2"
MANDELBROT_FUNCTION_SIGNATURE_ID = 65
MANDELBROT_PARAMETER_NAME = "st"
MANDELBROT_PARAMETER_SYMBOL_ID = 56
MANDELBROT_CALL_SPAN = "338:13-338:27"
MANDELBROT_CALL_SIGNATURE_ID = 65
MANDELBROT_CALL_PARAMETER_SYMBOL_ID = 102
MANDELBROT_BODY_SPANS = (
    "288:5-288:53", "289:5-289:53", "290:5-290:58", "292:5-292:33",
    "293:5-293:29", "294:5-294:61", "296:5-296:24", "297:5-297:63",
    "298:5-298:73", "300:5-300:19", "301:5-310:6", "312:5-315:6",
    "317:5-321:6",
)
MANDELBROT_Z_DECLARATION_SPAN = "296:5-296:24"
MANDELBROT_C_DECLARATION_SPAN = "297:5-297:63"
MANDELBROT_INITIAL_STATE_SPAN = "298:5-298:73"
MANDELBROT_LOOP_COUNTER_DECLARATION_SPAN = "300:5-300:19"
MANDELBROT_LOOP_SPAN = "301:5-310:6"
MANDELBROT_MATRIX_CONSTRUCTOR_SPAN = MATRIX_CONSTRUCTOR_SPAN
MANDELBROT_MATRIX_UPDATE_SPAN = "305:9-305:40"
MANDELBROT_ESCAPE_GUARD_SPAN = "307:9-309:10"
MANDELBROT_FULL_ITERATION_GUARD_SPAN = "312:5-315:6"
MANDELBROT_MODE_GUARD_SPAN = "317:5-321:6"
MANDELBROT_MODE_ZERO_RETURN_SPAN = "318:9-318:36"
MANDELBROT_MODE_ONE_RETURN_SPAN = "320:9-320:46"
MANDELBROT_NUMBER_ANCHOR_SPANS = (
    MANDELBROT_Z_DECLARATION_SPAN, MANDELBROT_C_DECLARATION_SPAN,
    MANDELBROT_INITIAL_STATE_SPAN, MANDELBROT_LOOP_COUNTER_DECLARATION_SPAN,
    MANDELBROT_LOOP_SPAN, MANDELBROT_MATRIX_UPDATE_SPAN,
    MANDELBROT_ESCAPE_GUARD_SPAN, MANDELBROT_FULL_ITERATION_GUARD_SPAN,
    MANDELBROT_MODE_GUARD_SPAN, MANDELBROT_MODE_ZERO_RETURN_SPAN,
    MANDELBROT_MODE_ONE_RETURN_SPAN,
)
FRONTEND_BLOCKER = (
    "counted-loop proof required for julia, mandelbrot, and newton iteration "
    "loops (first exact node: julia 261:5-269:6)"
)

_EXPECTED_EXPR_KINDS = {
    "id": 371, "literal": 239, "binary": 206, "swizzle": 73,
    "assign": 61, "declaration": 60, "builtin": 45, "construct": 41,
    "unary": 31, "call": 30, "index": 5, "post": 3, "conditional": 1,
}
_EXPECTED_OPERATORS = {
    "*": 74, "-": 54, "=": 48, "/": 33, "+": 25, "==": 21, "<": 12,
    "+=": 8, "<=": 7, "&&": 6, "++": 4, ">": 3, "-=": 3, "*=": 2,
    "!=": 1,
}


@dataclass(frozen=True, slots=True)
class FractalFrontendProof:
    program: TypedProgram
    source_uniforms: tuple[tuple[str, str], ...]
    matrix_constants: tuple[str, ...]
    functions: tuple[str, ...]
    loops: tuple[tuple[str, str], ...]
    unproved_loops: tuple[tuple[str, str], ...]
    blocker: str
    iterations_contract: FractalIterationContract
    mode_contract: FractalModeContract
    terminal_fallback_functions: tuple[str, ...]
    linear_srgb_indexes: tuple[TypedExpression, ...]
    matrix_constructor: TypedExpression
    alpha_branch: TypedStatement
    alpha_assignment: TypedExpression
    alpha_construct: TypedExpression
    alpha_product: TypedExpression
    alpha_literal: TypedExpression
    hsv_function: object
    hsv_parameter: object
    hsv_calls: tuple[TypedExpression, ...]
    hue_scale_assignment: TypedExpression
    hue_scale_product: TypedExpression
    hue_scale_literal: TypedExpression
    distance_fract_assignment: TypedExpression
    distance_fract_builtin: TypedExpression
    distance_map_assignment: TypedExpression
    distance_map_sum: TypedExpression
    distance_repeat_product: TypedExpression
    distance_rotate_product: TypedExpression
    distance_rotate_literal: TypedExpression
    palette_function: object
    palette_parameter: object
    palette_call: TypedExpression
    newton_function: object
    newton_parameter: object
    newton_call: TypedExpression
    julia_function: object
    julia_parameter: object
    julia_call: TypedExpression
    julia_body_spans: tuple[str, ...]
    julia_number_anchors: tuple[TypedStatement, ...]
    mandelbrot_function: object
    mandelbrot_parameter: object
    mandelbrot_call: TypedExpression
    mandelbrot_body_spans: tuple[str, ...]
    mandelbrot_number_anchors: tuple[TypedStatement, ...]


def _preproof_program(program: TypedProgram) -> TypedProgram:
    """Normalize either an analyzed or Fractal-proofed tree to the live AST."""
    functions = attach_counted_loop_proofs(
        clear_counted_loop_proofs(program.functions), program.key)
    return replace(
        program, functions=functions,
        counted_loop_proof=summarize_counted_loop_proofs(functions))


def _span(value: object) -> str:
    s = value.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"


def _replace_fractal_loops(value, function_name: str, seen: list[str]):
    if value.kind == "for":
        span = _span(value)
        bound_spec = LOOP_BOUNDS.get(function_name)
        if bound_spec is not None and span == bound_spec[0]:
            if len(value.children) != 2 or len(value.expressions) != 2:
                raise ValueError(f"{PROFILE}: malformed {function_name} loop")
            initializer = value.children[0]
            if initializer.kind == "decl" and len(initializer.expressions) == 1:
                declaration = initializer.expressions[0]
                symbol = declaration.symbol
                symbol_id = declaration.symbol_id
                start = declaration.children[0] if len(declaration.children) == 1 else None
            elif (initializer.kind == "expr" and len(initializer.expressions) == 1
                  and initializer.expressions[0].kind == "assign"
                  and initializer.expressions[0].operator == "="
                  and len(initializer.expressions[0].children) == 2):
                assignment = initializer.expressions[0]
                symbol = assignment.children[0].symbol
                symbol_id = assignment.children[0].symbol_id
                start = assignment.children[1]
                declaration = assignment
            else:
                declaration = None
                symbol = None
                symbol_id = None
                start = None
            if (symbol is None or symbol.name != "i" or symbol_id != symbol.id
                    or start is None or start.kind != "literal"
                    or float(start.literal_value) != 0.0):
                raise ValueError(f"{PROFILE}: {function_name} induction identity drift")
            condition, update = value.expressions
            if (condition.kind != "binary" or condition.operator != "<"
                    or len(condition.children) != 2
                    or condition.children[0].kind != "id"
                    or condition.children[0].symbol_id != symbol_id
                    or update.kind not in {"post", "unary"}
                    or update.operator != "++"
                    or len(update.children) != 1
                    or update.children[0].kind != "id"
                    or update.children[0].symbol_id != symbol_id):
                raise ValueError(f"{PROFILE}: {function_name} loop control drift")
            _name, maximum, provenance = bound_spec
            seen.append(function_name)
            proof = CountedLoopProof(
                symbol_id, 0, maximum, "<", "++", provenance,
                maximum, 1, 1, maximum, 0)
            return replace(value, loop_proof=proof,
                           children=tuple(
                               _replace_fractal_loops(child, function_name, seen)
                               for child in value.children))
    return replace(value, children=tuple(
        _replace_fractal_loops(child, function_name, seen)
        for child in value.children))


def _entrypoint_charge(functions) -> int:
    definitions = {function.signature.id: function
                   for function in functions if function.body}
    cache: dict[int, int] = {}
    charging: set[int] = set()

    def charge(signature_id: int) -> int:
        if signature_id not in definitions:
            return 0
        if signature_id in cache:
            return cache[signature_id]
        if signature_id in charging:
            return _loop_proof._MAX_CHARGE + 1
        charging.add(signature_id)
        value = sum(
            _loop_proof._statement_charge(statement, charge)
            for statement in definitions[signature_id].body)
        charging.remove(signature_id)
        cache[signature_id] = value
        return value

    main = next((function for function in functions
                 if function.name == "main" and function.body), None)
    if main is None:
        raise ValueError(f"{PROFILE}: main function missing")
    return charge(main.signature.id)


def _attach_fractal_loop_proofs(program: TypedProgram) -> TypedProgram:
    baseline = attach_counted_loop_proofs(
        clear_counted_loop_proofs(program.functions), program.key)
    seen: list[str] = []
    functions = tuple(
        replace(function, body=tuple(
            _replace_fractal_loops(statement, function.name, seen)
            for statement in function.body))
        for function in baseline)
    if tuple(seen) != ("julia", "mandelbrot", "newton"):
        raise ValueError(f"{PROFILE}: exact dynamic loop census mismatch")
    entry_charge = _entrypoint_charge(functions)
    functions = tuple(replace(function, body=tuple(
        _loop_proof._replace_metrics(statement, 0, entry_charge)
        for statement in function.body)) for function in functions)
    return replace(
        program, functions=functions,
        counted_loop_proof=summarize_counted_loop_proofs(functions))


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source, program.declarations,
                 program.functions, program.resources, program.body_status,
                 program.local_type_names, program.structs, program.uniform_blocks,
                 program.interface_symbols, program.builtin_symbols,
                 program.counted_loop_proof, program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources, program.local_type_names,
                 program.structs, program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _walk_statement_nodes(value):
    yield value
    for child in value.children:
        yield from _walk_statement_nodes(child)


def _expressions(program: TypedProgram):
    values = []
    for declaration in program.declarations:
        if declaration.initializer is not None:
            values.extend(_walk_expression(declaration.initializer))
    for function in program.functions:
        for statement in function.body:
            values.extend(_walk_statement(statement))
    return tuple(values)


def _span(value: object) -> str:
    s = value.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_fractal_metadata(effect: object) -> None:
    """Authenticate the exact corpus iteration and mode metadata records."""
    try:
        params = effect["params"]  # type: ignore[index]
        actual_iterations = params[ITERATIONS_CONTRACT.uniform_name]
        actual_mode = params[MODE_CONTRACT.uniform_name]
    except (KeyError, TypeError):
        raise _fail("metadata contract mismatch") from None
    if (actual_iterations != ITERATIONS_CONTRACT.metadata_record()
            or actual_mode != MODE_CONTRACT.metadata_record()):
        raise _fail("metadata contract mismatch")


def authenticate_fractal_frontend(program: TypedProgram, source_hash: str | None,
                                  profile: str | None) -> FractalFrontendProof:
    if program.key != KEY:
        raise _fail("selected key is not classicNoisedeck/fractal:fractal")
    if profile != PROFILE:
        raise _fail("exact prepared profile required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    canonical = _preproof_program(program)
    if (source_hash != RAW_SHA256 or len(raw) != RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or _sha(canonical.functions) != FUNCTIONS_SHA256
            or _whole(canonical) != WHOLE_SHA256
            or _interface(canonical) != INTERFACE_SHA256):
        raise _fail("source, function, whole-program, or interface lock mismatch")
    resources = program.resources
    if (resources.uniforms, resources.samplers, resources.outputs,
            resources.uses_texture, resources.uses_derivatives) != (
                tuple(name for name, _ in SOURCE_UNIFORMS), (), ("fragColor",),
                False, False):
        raise _fail("uniform or output interface mismatch")
    declarations = tuple((d.symbol.name, d.type.display(), d.symbol.storage,
                          d.symbol.writable) for d in program.declarations)
    if tuple(name for name, *_ in declarations[:29]) != tuple(name for name, _ in SOURCE_UNIFORMS):
        raise _fail("uniform declaration census mismatch")
    if declarations[29:] != (("fragColor", "vec4", "output", True),
                              ("fwdA", "mat3", "const", False),
                              ("fwdB", "mat3", "const", False),
                              ("invB", "mat3", "const", False),
                              ("invA", "mat3", "const", False)):
        raise _fail("output/matrix declaration census mismatch")
    if tuple(function.name for function in program.functions) != FUNCTION_NAMES:
        raise _fail("function identity census mismatch")
    expressions = _expressions(program)
    if Counter(item.kind for item in expressions) != Counter(_EXPECTED_EXPR_KINDS):
        raise _fail("expression-kind cardinality mismatch")
    if Counter(item.operator for item in expressions if item.operator is not None) != Counter(_EXPECTED_OPERATORS):
        raise _fail("operator cardinality mismatch")
    loops = tuple((function.name, _span(statement))
                  for function in program.functions
                  for root in function.body
                  for statement in _walk_statement_nodes(root)
                  if statement.kind == "for")
    if loops != LOOP_SPANS:
        raise _fail("loop identity census mismatch")
    indexes = tuple(item for item in expressions if item.kind == "index")
    if tuple(_span(item) for item in indexes) != LINEAR_SRGB_INDEX_SPANS:
        raise _fail("linear sRGB index identity census mismatch")
    matrices = tuple(item for item in expressions
                     if item.kind == "construct" and item.type.display() == "mat2")
    fractal_matrix = next((item for item in matrices
                           if _span(item) == MATRIX_CONSTRUCTOR_SPAN), None)
    if (len(matrices) != 2
            or fractal_matrix is None
            or len(fractal_matrix.children) != 3
            or fractal_matrix.children[0].type.display() != "vec2"
            or any(item.type.display() != "float"
                   for item in fractal_matrix.children[1:])):
        raise _fail("Mandelbrot mat2 constructor identity census mismatch")
    main = next((item for item in program.functions
                 if item.name == "main" and item.body), None)
    julia_function = next((item for item in program.functions
                           if item.name == "julia" and item.body), None)
    mandelbrot_function = next((item for item in program.functions
                                if item.name == "mandelbrot" and item.body), None)
    julia_parameter = (julia_function.parameters[0]
                       if julia_function is not None
                       and len(julia_function.parameters) == 1 else None)
    mandelbrot_parameter = (mandelbrot_function.parameters[0]
                            if mandelbrot_function is not None
                            and len(mandelbrot_function.parameters) == 1 else None)
    julia_calls = tuple(item for item in expressions
                        if item.kind == "call"
                        and item.signature_id == JULIA_CALL_SIGNATURE_ID)
    mandelbrot_calls = tuple(item for item in expressions
                             if item.kind == "call"
                             and item.signature_id == MANDELBROT_CALL_SIGNATURE_ID)
    julia_call = julia_calls[0] if len(julia_calls) == 1 else None
    mandelbrot_call = (mandelbrot_calls[0]
                       if len(mandelbrot_calls) == 1 else None)

    def statement(function, span):
        return next((item for root in function.body
                     for item in _walk_statement_nodes(root)
                     if _span(item) == span), None)

    julia_z = (statement(julia_function, JULIA_Z_DECLARATION_SPAN)
               if julia_function is not None else None)
    julia_loop = (statement(julia_function, JULIA_LOOP_SPAN)
                  if julia_function is not None else None)
    julia_escape = (statement(julia_function, JULIA_ESCAPE_GUARD_SPAN)
                    if julia_function is not None else None)
    julia_cutoff = (statement(julia_function, JULIA_CUTOFF_GUARD_SPAN)
                    if julia_function is not None else None)
    julia_mode = (statement(julia_function, JULIA_MODE_GUARD_SPAN)
                  if julia_function is not None else None)
    julia_mode_zero_return = (
        statement(julia_function, JULIA_MODE_ZERO_RETURN_SPAN)
        if julia_function is not None else None)
    julia_mode_one_return = (
        statement(julia_function, JULIA_MODE_ONE_RETURN_SPAN)
        if julia_function is not None else None)
    julia_stores = tuple(
        statement(julia_function, span) for span in JULIA_STATE_STORE_SPANS)
    julia_initial_stores = tuple(
        statement(julia_function, span) for span in JULIA_INITIAL_STORE_SPANS)
    julia_iteration_declarations = tuple(
        statement(julia_function, span) for span in (
            JULIA_ITERATION_X_DECLARATION_SPAN,
            JULIA_ITERATION_Y_DECLARATION_SPAN))
    mandelbrot_z = (statement(mandelbrot_function,
                              MANDELBROT_Z_DECLARATION_SPAN)
                    if mandelbrot_function is not None else None)
    mandelbrot_c = (statement(mandelbrot_function,
                              MANDELBROT_C_DECLARATION_SPAN)
                   if mandelbrot_function is not None else None)
    mandelbrot_initial = (statement(mandelbrot_function,
                                    MANDELBROT_INITIAL_STATE_SPAN)
                          if mandelbrot_function is not None else None)
    mandelbrot_counter = (statement(
        mandelbrot_function, MANDELBROT_LOOP_COUNTER_DECLARATION_SPAN)
                          if mandelbrot_function is not None else None)
    mandelbrot_loop = (statement(mandelbrot_function, MANDELBROT_LOOP_SPAN)
                       if mandelbrot_function is not None else None)
    mandelbrot_update = (statement(mandelbrot_function,
                                   MANDELBROT_MATRIX_UPDATE_SPAN)
                         if mandelbrot_function is not None else None)
    mandelbrot_escape = (statement(mandelbrot_function,
                                   MANDELBROT_ESCAPE_GUARD_SPAN)
                         if mandelbrot_function is not None else None)
    mandelbrot_full = (statement(mandelbrot_function,
                                 MANDELBROT_FULL_ITERATION_GUARD_SPAN)
                       if mandelbrot_function is not None else None)
    mandelbrot_mode = (statement(mandelbrot_function,
                                 MANDELBROT_MODE_GUARD_SPAN)
                       if mandelbrot_function is not None else None)
    mandelbrot_mode_zero_return = (
        statement(mandelbrot_function, MANDELBROT_MODE_ZERO_RETURN_SPAN)
        if mandelbrot_function is not None else None)
    mandelbrot_mode_one_return = (
        statement(mandelbrot_function, MANDELBROT_MODE_ONE_RETURN_SPAN)
        if mandelbrot_function is not None else None)
    julia_body_spans = (tuple(_span(item) for item in julia_function.body)
                        if julia_function is not None else ())
    mandelbrot_body_spans = (
        tuple(_span(item) for item in mandelbrot_function.body)
        if mandelbrot_function is not None else ())
    if (
            julia_function is None
            or _span(julia_function) != JULIA_FUNCTION_SPAN
            or julia_function.signature.id != JULIA_FUNCTION_SIGNATURE_ID
            or julia_function.return_type.display() != "float"
            or julia_parameter is None
            or julia_parameter.name != JULIA_PARAMETER_NAME
            or julia_parameter.id != JULIA_PARAMETER_SYMBOL_ID
            or julia_parameter.type.display() != "vec2"
            or julia_parameter.direction != "in"
            or julia_body_spans != JULIA_BODY_SPANS
            or julia_call is None
            or _span(julia_call) != JULIA_CALL_SPAN
            or julia_call.signature_id != JULIA_CALL_SIGNATURE_ID
            or len(julia_call.children) != 1
            or julia_call.children[0].kind != "id"
            or julia_call.children[0].symbol_id != JULIA_CALL_PARAMETER_SYMBOL_ID
            or julia_call.children[0].symbol.name != "st"
            or julia_z is None
            or julia_z.kind != "decl"
            or len(julia_z.expressions) != 1
            or julia_z.expressions[0].kind != "declaration"
            or julia_z.expressions[0].symbol_id != 86
            or julia_z.expressions[0].symbol.name != "z"
            or julia_z.expressions[0].type.display() != "vec2"
            or len(julia_initial_stores) != 2
            or any(item is None or item.kind != "expr"
                   or len(item.expressions) != 1
                   or item.expressions[0].kind != "assign"
                   for item in julia_initial_stores)
            or len(julia_iteration_declarations) != 2
            or any(item is None or item.kind != "decl"
                   or len(item.expressions) != 1
                   or item.expressions[0].kind != "declaration"
                   for item in julia_iteration_declarations)
            or julia_loop is None or julia_loop.kind != "for"
            or julia_escape is None or julia_escape.kind != "if"
            or len(julia_stores) != 2
            or any(item is None or item.kind != "expr"
                   or len(item.expressions) != 1
                   or item.expressions[0].kind != "assign"
                   for item in julia_stores)
            or julia_cutoff is None or julia_cutoff.kind != "if"
            or julia_mode is None or julia_mode.kind != "if"):
        raise _fail("Julia Number helper identity mismatch")
    if (julia_mode_zero_return is None
            or julia_mode_zero_return.kind != "return"
            or julia_mode_one_return is None
            or julia_mode_one_return.kind != "return"):
        raise _fail("Julia Number mode return identity mismatch")
    if (
            mandelbrot_function is None
            or _span(mandelbrot_function) != MANDELBROT_FUNCTION_SPAN
            or mandelbrot_function.signature.id
            != MANDELBROT_FUNCTION_SIGNATURE_ID
            or mandelbrot_function.return_type.display() != "float"
            or mandelbrot_parameter is None
            or mandelbrot_parameter.name != MANDELBROT_PARAMETER_NAME
            or mandelbrot_parameter.id != MANDELBROT_PARAMETER_SYMBOL_ID
            or mandelbrot_parameter.type.display() != "vec2"
            or mandelbrot_parameter.direction != "in"
            or mandelbrot_body_spans != MANDELBROT_BODY_SPANS
            or mandelbrot_call is None
            or _span(mandelbrot_call) != MANDELBROT_CALL_SPAN
            or mandelbrot_call.signature_id != MANDELBROT_CALL_SIGNATURE_ID
            or len(mandelbrot_call.children) != 1
            or mandelbrot_call.children[0].kind != "id"
            or mandelbrot_call.children[0].symbol_id
            != MANDELBROT_CALL_PARAMETER_SYMBOL_ID
            or mandelbrot_call.children[0].symbol.name != "st"
            or mandelbrot_z is None or mandelbrot_z.kind != "decl"
            or len(mandelbrot_z.expressions) != 1
            or mandelbrot_z.expressions[0].kind != "declaration"
            or mandelbrot_z.expressions[0].symbol_id != 109
            or mandelbrot_z.expressions[0].symbol.name != "z"
            or mandelbrot_z.expressions[0].type.display() != "vec2"
            or mandelbrot_c is None or mandelbrot_c.kind != "decl"
            or mandelbrot_c.expressions[0].symbol_id != 110
            or mandelbrot_c.expressions[0].symbol.name != "c"
            or mandelbrot_initial is None or mandelbrot_initial.kind != "expr"
            or mandelbrot_initial.expressions[0].operator != "+="
            or mandelbrot_counter is None or mandelbrot_counter.kind != "decl"
            or mandelbrot_loop is None or mandelbrot_loop.kind != "for"
            or mandelbrot_update is None or mandelbrot_update.kind != "expr"
            or mandelbrot_update.expressions[0].kind != "assign"
            or mandelbrot_escape is None or mandelbrot_escape.kind != "if"
            or mandelbrot_full is None or mandelbrot_full.kind != "if"
            or mandelbrot_mode is None or mandelbrot_mode.kind != "if"):
        raise _fail("Mandelbrot Number helper identity mismatch")
    if (mandelbrot_mode_zero_return is None
            or mandelbrot_mode_zero_return.kind != "return"
            or mandelbrot_mode_one_return is None
            or mandelbrot_mode_one_return.kind != "return"):
        raise _fail("Mandelbrot Number mode return identity mismatch")
    julia_number_anchors = (
        julia_z, *julia_initial_stores, julia_loop,
        *julia_iteration_declarations, julia_escape, *julia_stores,
        julia_cutoff, julia_mode, julia_mode_zero_return,
        julia_mode_one_return)
    mandelbrot_number_anchors = (
        mandelbrot_z, mandelbrot_c, mandelbrot_initial, mandelbrot_counter,
        mandelbrot_loop, mandelbrot_update, mandelbrot_escape,
        mandelbrot_full, mandelbrot_mode, mandelbrot_mode_zero_return,
        mandelbrot_mode_one_return)
    alpha_branch = next(
        (item for item in main.body if item.kind == "if"
         and _span(item) == ALPHA_BRANCH_SPAN), None) if main is not None else None
    if (alpha_branch is None or len(alpha_branch.expressions) != 1
            or len(alpha_branch.children) != 1):
        raise _fail("background alpha branch identity mismatch")
    guard = alpha_branch.expressions[0]
    if (guard.kind != "binary" or guard.operator != "=="
            or len(guard.children) != 2
            or guard.children[0].kind != "id"
            or guard.children[0].symbol_id != 104
            or guard.children[0].symbol.name != "d"
            or guard.children[1].kind != "literal"
            or guard.children[1].literal != "1.0"
            or guard.children[1].literal_value != 1.0):
        raise _fail("background alpha guard identity mismatch")
    block = alpha_branch.children[0]
    assignment_statement = (block.children[0] if block.kind == "block"
                             and len(block.children) == 2 else None)
    alpha_assignment = (
        assignment_statement.expressions[0]
        if assignment_statement is not None
        and assignment_statement.kind == "expr"
        and len(assignment_statement.expressions) == 1 else None)
    if (alpha_assignment is None
            or _span(alpha_assignment) != ALPHA_ASSIGNMENT_SPAN
            or alpha_assignment.kind != "assign"
            or alpha_assignment.operator != "="
            or alpha_assignment.type.display() != "vec4"
            or len(alpha_assignment.children) != 2
            or alpha_assignment.children[0].kind != "id"
            or alpha_assignment.children[0].symbol_id != 30
            or alpha_assignment.children[0].symbol.name != "fragColor"):
        raise _fail("background alpha output assignment identity mismatch")
    alpha_construct = alpha_assignment.children[1]
    if (alpha_construct.kind != "construct"
            or _span(alpha_construct) != ALPHA_CONSTRUCT_SPAN
            or alpha_construct.type.display() != "vec4"
            or alpha_construct.constructor_type.display() != "vec4"
            or len(alpha_construct.children) != 2
            or alpha_construct.children[0].kind != "id"
            or alpha_construct.children[0].symbol_id != 27
            or alpha_construct.children[0].symbol.name != "bgColor"):
        raise _fail("background alpha vec4 identity mismatch")
    alpha_product = alpha_construct.children[1]
    if (alpha_product.kind != "binary" or alpha_product.operator != "*"
            or _span(alpha_product) != ALPHA_PRODUCT_SPAN
            or alpha_product.type.display() != "float"
            or len(alpha_product.children) != 2
            or alpha_product.children[0].kind != "id"
            or alpha_product.children[0].symbol_id != ALPHA_BG_SYMBOL_ID
            or alpha_product.children[0].symbol.name != ALPHA_BG_SYMBOL_NAME):
        raise _fail("background alpha product identity mismatch")
    alpha_literal = alpha_product.children[1]
    if (alpha_literal.kind != "literal"
            or _span(alpha_literal) != ALPHA_LITERAL_SPAN
            or alpha_literal.type.display() != "float"
            or alpha_literal.literal != ALPHA_LITERAL_SPELLING
            or alpha_literal.literal_value != ALPHA_LITERAL_VALUE):
        raise _fail("background alpha literal identity mismatch")
    hsv_function = next((item for item in program.functions
                         if item.name == HSV_FUNCTION_NAME), None)
    hsv_parameter = (hsv_function.parameters[0]
                     if hsv_function is not None
                     and len(hsv_function.parameters) == 1 else None)
    if (hsv_function is None
            or hsv_function.signature.id != HSV_FUNCTION_SIGNATURE_ID
            or hsv_function.return_type.display() != "vec3"
            or hsv_parameter is None
            or hsv_parameter.name != HSV_PARAMETER_NAME
            or hsv_parameter.id != HSV_PARAMETER_SYMBOL_ID
            or hsv_parameter.type.display() != "vec3"
            or hsv_parameter.direction != "in"):
        raise _fail("Number-preserving HSV function identity mismatch")
    hsv_calls = tuple(sorted(
        (item for item in expressions
         if item.kind == "call"
         and item.signature_id == HSV_FUNCTION_SIGNATURE_ID),
        key=lambda item: (item.span.start_line, item.span.start_column)))
    if (tuple(_span(item) for item in hsv_calls) != HSV_CALL_SPANS
            or any(item.type.display() != "vec3"
                   or len(item.children) != 1 for item in hsv_calls)
            or hsv_calls[0].children[0].kind != "id"
            or hsv_calls[0].children[0].symbol_id != 124
            or hsv_calls[1].children[0].kind != "construct"
            or hsv_calls[1].children[0].type.display() != "vec3"
            or len(hsv_calls[1].children[0].children) != 3
            or hsv_calls[1].children[0].children[0].kind != "id"
            or hsv_calls[1].children[0].children[0].symbol_id
            != HUE_SCALE_TARGET_SYMBOL_ID):
        raise _fail("Number-preserving HSV call census mismatch")
    hue_scale_assignment = next(
        (item for item in expressions
         if item.kind == "assign"
         and _span(item) == HUE_SCALE_ASSIGNMENT_SPAN), None)
    if (hue_scale_assignment is None
            or hue_scale_assignment.operator != "*="
            or hue_scale_assignment.type.display() != "float"
            or len(hue_scale_assignment.children) != 2
            or hue_scale_assignment.children[0].kind != "id"
            or hue_scale_assignment.children[0].symbol_id
            != HUE_SCALE_TARGET_SYMBOL_ID):
        raise _fail("Number-preserving hue-scale assignment mismatch")
    hue_scale_product = hue_scale_assignment.children[1]
    if (hue_scale_product.kind != "binary"
            or hue_scale_product.operator != "*"
            or _span(hue_scale_product) != HUE_SCALE_PRODUCT_SPAN
            or hue_scale_product.type.display() != "float"
            or len(hue_scale_product.children) != 2
            or hue_scale_product.children[0].kind != "id"
            or hue_scale_product.children[0].symbol_id
            != HUE_SCALE_UNIFORM_SYMBOL_ID
            or hue_scale_product.children[0].symbol.name != "hueRange"):
        raise _fail("Number-preserving hue-scale product mismatch")
    hue_scale_literal = hue_scale_product.children[1]
    if (hue_scale_literal.kind != "literal"
            or _span(hue_scale_literal) != HUE_SCALE_LITERAL_SPAN
            or hue_scale_literal.type.display() != "float"
            or hue_scale_literal.literal != "0.01"
            or hue_scale_literal.literal_value != 0.01):
        raise _fail("Number-preserving hue-scale literal mismatch")
    distance_fract_assignment = next(
        (item for item in expressions
         if item.kind == "assign"
         and _span(item) == DISTANCE_FRACT_ASSIGNMENT_SPAN), None)
    if (distance_fract_assignment is None
            or distance_fract_assignment.operator != "="
            or distance_fract_assignment.type.display() != "float"
            or len(distance_fract_assignment.children) != 2
            or distance_fract_assignment.children[0].kind != "id"
            or distance_fract_assignment.children[0].symbol_id
            != HUE_SCALE_TARGET_SYMBOL_ID):
        raise _fail("Number-preserving distance fract assignment mismatch")
    distance_fract_builtin = distance_fract_assignment.children[1]
    if (distance_fract_builtin.kind != "builtin"
            or _span(distance_fract_builtin) != DISTANCE_FRACT_BUILTIN_SPAN
            or distance_fract_builtin.callee != "fract"
            or distance_fract_builtin.signature_id != -18
            or distance_fract_builtin.type.display() != "float"
            or len(distance_fract_builtin.children) != 1
            or distance_fract_builtin.children[0].kind != "id"
            or distance_fract_builtin.children[0].symbol_id
            != HUE_SCALE_TARGET_SYMBOL_ID):
        raise _fail("Number-preserving distance fract builtin mismatch")
    distance_map_assignment = next(
        (item for item in expressions
         if item.kind == "assign"
         and _span(item) == DISTANCE_MAP_ASSIGNMENT_SPAN), None)
    if (distance_map_assignment is None
            or distance_map_assignment.operator != "="
            or distance_map_assignment.type.display() != "float"
            or len(distance_map_assignment.children) != 2
            or distance_map_assignment.children[0].kind != "id"
            or distance_map_assignment.children[0].symbol_id
            != HUE_SCALE_TARGET_SYMBOL_ID):
        raise _fail("Number-preserving distance map assignment mismatch")
    distance_map_sum = distance_map_assignment.children[1]
    if (distance_map_sum.kind != "binary"
            or distance_map_sum.operator != "+"
            or _span(distance_map_sum) != DISTANCE_MAP_SUM_SPAN
            or len(distance_map_sum.children) != 2):
        raise _fail("Number-preserving distance map sum mismatch")
    distance_repeat_product, distance_rotate_product = distance_map_sum.children
    if (distance_repeat_product.kind != "binary"
            or distance_repeat_product.operator != "*"
            or _span(distance_repeat_product) != DISTANCE_REPEAT_PRODUCT_SPAN
            or len(distance_repeat_product.children) != 2
            or distance_repeat_product.children[0].kind != "id"
            or distance_repeat_product.children[0].symbol_id
            != HUE_SCALE_TARGET_SYMBOL_ID
            or distance_repeat_product.children[1].kind != "id"
            or distance_repeat_product.children[1].symbol_id != 24
            or distance_repeat_product.children[1].symbol.name
            != "repeatPalette"):
        raise _fail("Number-preserving distance repeat product mismatch")
    if (distance_rotate_product.kind != "binary"
            or distance_rotate_product.operator != "*"
            or _span(distance_rotate_product) != DISTANCE_ROTATE_PRODUCT_SPAN
            or len(distance_rotate_product.children) != 2
            or distance_rotate_product.children[0].kind != "id"
            or distance_rotate_product.children[0].symbol_id != 23
            or distance_rotate_product.children[0].symbol.name
            != "rotatePalette"):
        raise _fail("Number-preserving distance rotate product mismatch")
    distance_rotate_literal = distance_rotate_product.children[1]
    if (distance_rotate_literal.kind != "literal"
            or _span(distance_rotate_literal)
            != DISTANCE_ROTATE_LITERAL_SPAN
            or distance_rotate_literal.type.display() != "float"
            or distance_rotate_literal.literal != "0.01"
            or distance_rotate_literal.literal_value != 0.01):
        raise _fail("Number-preserving distance rotate literal mismatch")
    palette_function = next((item for item in program.functions
                             if item.name == PALETTE_FUNCTION_NAME), None)
    palette_parameter = (palette_function.parameters[0]
                         if palette_function is not None
                         and len(palette_function.parameters) == 1 else None)
    palette_calls = tuple(
        item for item in expressions
        if item.kind == "call"
        and item.signature_id == PALETTE_FUNCTION_SIGNATURE_ID)
    palette_call = palette_calls[0] if len(palette_calls) == 1 else None
    if (palette_function is None
            or palette_function.signature.id != PALETTE_FUNCTION_SIGNATURE_ID
            or palette_function.return_type.display() != "vec3"
            or palette_parameter is None
            or palette_parameter.name != PALETTE_PARAMETER_NAME
            or palette_parameter.id != PALETTE_PARAMETER_SYMBOL_ID
            or palette_parameter.type.display() != "float"
            or palette_parameter.direction != "in"
            or palette_call is None
            or _span(palette_call) != PALETTE_CALL_SPAN
            or palette_call.type.display() != "vec3"
            or len(palette_call.children) != 1
            or palette_call.children[0].kind != "id"
            or palette_call.children[0].symbol_id
            != HUE_SCALE_TARGET_SYMBOL_ID):
        raise _fail("Number-preserving palette-mode-zero identity mismatch")
    newton_function = next((item for item in program.functions
                            if item.name == NEWTON_FUNCTION_NAME), None)
    newton_parameter = (newton_function.parameters[0]
                        if newton_function is not None
                        and len(newton_function.parameters) == 1 else None)
    newton_calls = tuple(
        item for item in expressions
        if item.kind == "call"
        and item.signature_id == NEWTON_FUNCTION_SIGNATURE_ID)
    newton_call = newton_calls[0] if len(newton_calls) == 1 else None
    if (newton_function is None
            or newton_function.signature.id != NEWTON_FUNCTION_SIGNATURE_ID
            or newton_function.return_type.display() != "float"
            or newton_parameter is None
            or newton_parameter.name != NEWTON_PARAMETER_NAME
            or newton_parameter.id != NEWTON_PARAMETER_SYMBOL_ID
            or newton_parameter.type.display() != "vec2"
            or newton_parameter.direction != "in"
            or tuple(_span(item) for item in newton_function.body)
            != NEWTON_BODY_SPANS
            or newton_call is None
            or _span(newton_call) != NEWTON_CALL_SPAN
            or newton_call.type.display() != "float"
            or len(newton_call.children) != 1
            or newton_call.children[0].kind != "id"
            or newton_call.children[0].symbol_id != 102
            or newton_call.children[0].symbol.name != "st"):
        raise _fail("Number-preserving Newton identity mismatch")
    helper_returns = {function.name: function.return_type.display()
                      for function in program.functions
                      if function.name in TERMINAL_FALLBACK_FUNCTIONS}
    if (tuple(helper_returns) != TERMINAL_FALLBACK_FUNCTIONS
            or any(value != "float" for value in helper_returns.values())):
        raise _fail("terminal fallback function identity mismatch")
    mode_uniform = next((item.symbol for item in program.declarations
                         if item.symbol.name == MODE_CONTRACT.uniform_name), None)
    if (mode_uniform is None
            or mode_uniform.type.display() != MODE_CONTRACT.uniform_type
            or mode_uniform.storage != "uniform" or mode_uniform.writable):
        raise _fail("mode uniform contract mismatch")
    return FractalFrontendProof(program, SOURCE_UNIFORMS, MATRIX_CONSTANTS,
                                FUNCTION_NAMES, loops, UNPROVED_LOOP_SPANS,
                                FRONTEND_BLOCKER, ITERATIONS_CONTRACT,
                                MODE_CONTRACT, TERMINAL_FALLBACK_FUNCTIONS,
                                indexes, fractal_matrix, alpha_branch,
                                alpha_assignment, alpha_construct,
                                alpha_product, alpha_literal, hsv_function,
                                hsv_parameter, hsv_calls,
                                hue_scale_assignment, hue_scale_product,
                                hue_scale_literal, distance_fract_assignment,
                                distance_fract_builtin,
                                distance_map_assignment, distance_map_sum,
                                distance_repeat_product,
                                distance_rotate_product,
                                distance_rotate_literal, palette_function,
                                palette_parameter, palette_call,
                                newton_function, newton_parameter,
                                newton_call, julia_function, julia_parameter,
                                julia_call, julia_body_spans,
                                julia_number_anchors,
                                mandelbrot_function, mandelbrot_parameter,
                                mandelbrot_call, mandelbrot_body_spans,
                                mandelbrot_number_anchors)


def authenticate_fractal_runtime_contract(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> RuntimeLoopBoundContract:
    """Return the guard contract carried by the authenticated Fractal proof."""
    proof = authenticate_fractal_frontend(program, source_hash, profile)
    contract = proof.iterations_contract
    if contract != ITERATIONS_CONTRACT:
        raise _fail("iterations runtime contract mismatch")
    uniform = next((item.symbol for item in program.declarations
                    if item.symbol.name == contract.uniform_name), None)
    if (uniform is None or uniform.type.display() != contract.uniform_type
            or uniform.storage != "uniform" or uniform.writable):
        raise _fail("iterations uniform contract mismatch")
    seed = RuntimeScalarBoundSeed(
        uniform.id, contract.maximum,
        "fractal-metadata-uniform-direct-parameter", uniform)
    return RuntimeLoopBoundContract(
        KEY, seed, "integer-range", contract.uniform_name,
        contract.minimum, contract.maximum, contract.default,
        f"{KEY} iterations must be in [{contract.minimum},{contract.maximum}]")


def apply_fractal_frontend(program: TypedProgram, source_hash: str | None,
                           profile: str | None) -> TypedProgram:
    authenticate_fractal_frontend(program, source_hash, profile)
    return _attach_fractal_loop_proofs(program)


__all__ = (
    "KEY", "PROFILE", "KEYS", "PREPARED_KEYS", "PROFILES", "PREPARED_PROFILES",
    "ALLOWED_ROW_FIELDS", "REQUIRED_COMPANION_PROFILES", "RAW_BYTES", "RAW_SHA256",
    "NORMALIZED_BYTES", "NORMALIZED_SHA256", "SOURCE_UNIFORMS", "RUNTIME_UNIFORM_ABI",
    "OUTPUT_ABI", "MATRIX_CONSTANTS", "FUNCTION_NAMES", "LOOP_SPANS",
    "UNPROVED_LOOP_SPANS", "LOOP_BOUNDS", "LINEAR_SRGB_INDEX_SPANS",
    "MATRIX_CONSTRUCTOR_SPAN", "FRONTEND_BLOCKER", "FractalIterationContract",
    "FractalModeContract", "ITERATIONS_CONTRACT", "MODE_CONTRACT",
    "TERMINAL_FALLBACK_FUNCTIONS", "FractalFrontendProof",
    "ALPHA_BRANCH_SPAN", "ALPHA_ASSIGNMENT_SPAN", "ALPHA_CONSTRUCT_SPAN",
    "ALPHA_PRODUCT_SPAN", "ALPHA_LITERAL_SPAN", "ALPHA_BG_SYMBOL_ID",
    "ALPHA_BG_SYMBOL_NAME", "ALPHA_LITERAL_SPELLING", "ALPHA_LITERAL_VALUE",
    "HSV_FUNCTION_NAME", "HSV_FUNCTION_SIGNATURE_ID", "HSV_PARAMETER_NAME",
    "HSV_PARAMETER_SYMBOL_ID", "HSV_CALL_SPANS", "HUE_SCALE_ASSIGNMENT_SPAN",
    "HUE_SCALE_PRODUCT_SPAN", "HUE_SCALE_LITERAL_SPAN",
    "HUE_SCALE_TARGET_SYMBOL_ID", "HUE_SCALE_UNIFORM_SYMBOL_ID",
    "DISTANCE_FRACT_ASSIGNMENT_SPAN", "DISTANCE_FRACT_BUILTIN_SPAN",
    "DISTANCE_MAP_ASSIGNMENT_SPAN", "DISTANCE_MAP_SUM_SPAN",
    "DISTANCE_REPEAT_PRODUCT_SPAN", "DISTANCE_ROTATE_PRODUCT_SPAN",
    "DISTANCE_ROTATE_LITERAL_SPAN",
    "PALETTE_FUNCTION_NAME", "PALETTE_FUNCTION_SIGNATURE_ID",
    "PALETTE_PARAMETER_NAME", "PALETTE_PARAMETER_SYMBOL_ID",
    "PALETTE_CALL_SPAN",
    "NEWTON_FUNCTION_NAME", "NEWTON_FUNCTION_SIGNATURE_ID",
    "NEWTON_PARAMETER_NAME", "NEWTON_PARAMETER_SYMBOL_ID",
    "NEWTON_CALL_SPAN", "NEWTON_BODY_SPANS",
    "JULIA_FUNCTION_SPAN", "JULIA_FUNCTION_SIGNATURE_ID",
    "JULIA_PARAMETER_NAME", "JULIA_PARAMETER_SYMBOL_ID", "JULIA_CALL_SPAN",
    "JULIA_CALL_SIGNATURE_ID", "JULIA_CALL_PARAMETER_SYMBOL_ID",
    "JULIA_BODY_SPANS", "JULIA_Z_DECLARATION_SPAN",
    "JULIA_INITIAL_STORE_SPANS", "JULIA_LOOP_SPAN",
    "JULIA_ITERATION_X_DECLARATION_SPAN",
    "JULIA_ITERATION_Y_DECLARATION_SPAN", "JULIA_ESCAPE_GUARD_SPAN",
    "JULIA_STATE_STORE_SPANS", "JULIA_CUTOFF_GUARD_SPAN",
    "JULIA_MODE_GUARD_SPAN", "JULIA_MODE_ZERO_RETURN_SPAN",
    "JULIA_MODE_ONE_RETURN_SPAN", "JULIA_NUMBER_ANCHOR_SPANS",
    "MANDELBROT_FUNCTION_SPAN",
    "MANDELBROT_FUNCTION_SIGNATURE_ID", "MANDELBROT_PARAMETER_NAME",
    "MANDELBROT_PARAMETER_SYMBOL_ID", "MANDELBROT_CALL_SPAN",
    "MANDELBROT_CALL_SIGNATURE_ID", "MANDELBROT_CALL_PARAMETER_SYMBOL_ID",
    "MANDELBROT_BODY_SPANS", "MANDELBROT_Z_DECLARATION_SPAN",
    "MANDELBROT_C_DECLARATION_SPAN", "MANDELBROT_INITIAL_STATE_SPAN",
    "MANDELBROT_LOOP_COUNTER_DECLARATION_SPAN", "MANDELBROT_LOOP_SPAN",
    "MANDELBROT_MATRIX_CONSTRUCTOR_SPAN", "MANDELBROT_MATRIX_UPDATE_SPAN",
    "MANDELBROT_ESCAPE_GUARD_SPAN", "MANDELBROT_FULL_ITERATION_GUARD_SPAN",
    "MANDELBROT_MODE_GUARD_SPAN", "MANDELBROT_MODE_ZERO_RETURN_SPAN",
    "MANDELBROT_MODE_ONE_RETURN_SPAN", "MANDELBROT_NUMBER_ANCHOR_SPANS",
    "authenticate_fractal_metadata",
    "authenticate_fractal_frontend", "authenticate_fractal_runtime_contract",
    "apply_fractal_frontend",
)
