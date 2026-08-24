"""Source-locked canonical-JavaScript comparer profile for Lens tint."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "canonical-js-vector-equality-result-truthiness-v1"
LENS_KEY = "classicNoisedeck/lensDistortion:lensDistortion"
RAW_BYTES = 8269
RAW_SHA256 = "f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444"
NORMALIZED_BYTES = 7723
NORMALIZED_SHA256 = "6586c49b079a3b0f4aa3538c8e735e70db088ff2e5d2ea1037e9e9c5486fdf52"
INTERFACE_SHA256 = "53e759b54c0710d9cb3375cc2353878abebec06b378aeaaf9d745c6ecfd2b4ca"
PRE_MAIN_SHA256 = "dc6d4d2a3b5c50598a879dc6679553b3f89d964a19f5d4c79716970a7f2493ee"
PRE_FUNCTIONS_SHA256 = "263870c469a9dc3b1f4d5f3a2498864c6da4ff4eaf2cc3efaf198376e4d304c1"
PRE_WHOLE_SHA256 = "f63fb6dba6626791c248501bcfc5ca1c94f073a0593f34dbe846056fe35c81f5"
FINAL_MAIN_SHA256 = "8de6658184c69cb679f0453e37e37f538eebabb0e14f720d1eeea61e715d30ec"
FINAL_FUNCTIONS_SHA256 = "c166fa2b38ec68661fb4d73be1bfb3eef4f879da7d82dbfca44deba1b651a756"
FINAL_WHOLE_SHA256 = "e5dbb049717ce77ba79a36c6ea39ddde88e561df1ba06c98fba0ddd179a63d2e"
PROFILE_SHA256 = "8dece8742d7539614d36045515985712aa7c05addc705490aa0ec3b6d4d07916"

# Raw corpus source line 273 becomes normalized typed-source line 265.
RAW_SOURCE_LINE = 273
SITE_PATH = (21, "e0", 0, 1, 1)
ASSIGNMENT_SPAN = "265:5-265:133"
ASSIGNMENT_SHA256 = "fcad293a35aaa5e8d58fb79a67440fd40a6813a4e3cb5f6621967a419aa0c1ab"
MIX_SPAN = "265:17-265:133"
MIX_SHA256 = "0821c5cc7a1190eda7fa50f0c6b681297beee3bec14122ef35ef1df8bc496158"
SITE_SPAN = "265:33-265:118"
SITE_SHA256 = "d0ed1263c4e79948ce8a260a4d46d3ea4fd2f603e741f711048e59fe67ea0daa"
PREDICATE_SPAN = "265:33-265:55"
PREDICATE_SHA256 = "54bdae95beb11464b7552e4625c5da13588b0856fd92158e3202e96a69ee192a"
LEFT_SHA256 = "48cee70a2575caafe9de2730b82198828ab45dc22f26b7728b9348351e6b3d88"
RIGHT_SHA256 = "7d19f613fdc4eb2dfecf2b5a85b1ab12b46573ea6636ced78712f919814f9c31"
TRUE_ARM_SHA256 = "5c2f390c2f4dea3e0c0288634599181961adc98a3579c2842e3ab18581be2324"
FALSE_ARM_SHA256 = "12a3174e1007a3d465ed76b1fde3168b4923a59e3d1e2a7454cf80522321e78e"
ALPHA_SHA256 = "5078bdeff5e3426961135e7133704398f563ba88e4d99ca249b96a35982a8793"

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _profile_tuple() -> tuple[object, ...]:
    return (
        PROFILE, LENS_KEY, RAW_SHA256, NORMALIZED_SHA256, {},
        RAW_SOURCE_LINE, SITE_PATH,
        ASSIGNMENT_SPAN, ASSIGNMENT_SHA256, MIX_SPAN, MIX_SHA256,
        SITE_SPAN, SITE_SHA256, PREDICATE_SPAN, PREDICATE_SHA256,
        LEFT_SHA256, RIGHT_SHA256, TRUE_ARM_SHA256, FALSE_ARM_SHA256,
        ALPHA_SHA256, PRE_FUNCTIONS_SHA256, FINAL_FUNCTIONS_SHA256,
        PRE_WHOLE_SHA256, FINAL_WHOLE_SHA256, INTERFACE_SHA256,
    )


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _site_at(main: object) -> tuple[TypedExpression, TypedExpression, TypedExpression]:
    value: object = main.body[SITE_PATH[0]]
    expression_root = False
    for step in SITE_PATH[1:]:
        if isinstance(step, str):
            if not step.startswith("e"):
                raise _fail("invalid frozen site path")
            value = getattr(value, "expressions")[int(step[1:])]
            expression_root = True
        elif expression_root:
            if step != 0:
                raise _fail("frozen expression-root marker mismatch")
            expression_root = False
        else:
            value = getattr(value, "children")[step]
    if expression_root:
        raise _fail("frozen path omitted its expression-root marker")
    assignment = main.body[SITE_PATH[0]].expressions[0]
    mix = assignment.children[1]
    site = value
    if not all(isinstance(value, TypedExpression)
               for value in (assignment, mix, site)):
        raise _fail("target path did not resolve expressions")
    if mix.children[1] is not site:
        raise _fail("target path ancestry mismatch")
    return assignment, mix, site


def _authenticate(program: TypedProgram, source_hash: str | None,
                  profile: str | None, *, final: bool) -> TypedExpression:
    if profile != PROFILE:
        raise _fail("exact custom comparer profile carrier required")
    if program.key != LENS_KEY or source_hash != RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")
    if PROFILE_SHA256 != _sha(_profile_tuple()):
        raise _fail("internal frozen profile tuple mismatch")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or program.preprocessor_defines != () or program.body_status != "analyzed"
            or _interface_fingerprint(program) != INTERFACE_SHA256):
        raise _fail("source, define, body, or interface profile mismatch")
    if any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("optional proof carrier is not absent")
    proof = program.counted_loop_proof
    if (proof is None or proof.loop_count != 0 or proof.unproved_loop_count != 0
            or proof.max_effective_depth != 0 or proof.max_lexical_product != 0
            or proof.entrypoint_charge != 0 or not proof.call_graph_acyclic):
        raise _fail("loop or call graph profile mismatch")
    mains = [function for function in program.functions if function.name == "main"]
    if (len(program.functions) != 8 or len(mains) != 1
            or mains[0].id != 38 or len(mains[0].body) != 25):
        raise _fail("main function profile mismatch")
    main = mains[0]
    expected_main = FINAL_MAIN_SHA256 if final else PRE_MAIN_SHA256
    expected_functions = FINAL_FUNCTIONS_SHA256 if final else PRE_FUNCTIONS_SHA256
    expected_whole = FINAL_WHOLE_SHA256 if final else PRE_WHOLE_SHA256
    if (_sha(main) != expected_main or _sha(program.functions) != expected_functions
            or _whole_fingerprint(program) != expected_whole):
        raise _fail("function or whole-program profile mismatch")

    assignment, mix, site = _site_at(main)
    if (_span(assignment) != ASSIGNMENT_SPAN or _sha(assignment) != ASSIGNMENT_SHA256
            or assignment.kind != "assign" or assignment.operator != "="
            or len(assignment.children) != 2):
        raise _fail("target assignment profile mismatch")
    if (_span(mix) != MIX_SPAN or _sha(mix) != MIX_SHA256
            or mix.kind != "builtin" or mix.callee != "mix"
            or mix.type.display() != "vec3" or len(mix.children) != 3
            or _sha(mix.children[2]) != ALPHA_SHA256):
        raise _fail("surrounding mix profile mismatch")
    if (_span(site) != SITE_SPAN or _sha(site) != SITE_SHA256
            or site.kind != "conditional" or site.type.display() != "vec3"
            or site.category != "rvalue" or len(site.children) != 3
            or _sha(site.children[1]) != TRUE_ARM_SHA256
            or _sha(site.children[2]) != FALSE_ARM_SHA256):
        raise _fail("target conditional or arm profile mismatch")
    predicate = site.children[0]
    if (_span(predicate) != PREDICATE_SPAN or _sha(predicate) != PREDICATE_SHA256
            or predicate.kind != "binary" or predicate.operator != "=="
            or predicate.type.display() != "bool" or predicate.category != "rvalue"
            or len(predicate.children) != 2
            or predicate.children[0].type.display() != "vec3"
            or predicate.children[1].type.display() != "vec3"
            or _sha(predicate.children[0]) != LEFT_SHA256
            or _sha(predicate.children[1]) != RIGHT_SHA256):
        raise _fail("target predicate profile mismatch")

    candidates = []
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if (value.kind == "conditional" and len(value.children) == 3
                        and value.children[0].kind == "binary"
                        and value.children[0].operator == "=="
                        and value.children[0].children
                        and value.children[0].children[0].type.display()
                        in {"vec2", "vec3", "vec4"}):
                    candidates.append(value)
    if candidates != [site]:
        raise _fail("unexpected extra or missing vector-equality conditional site")
    return predicate


def authenticate_lens_custom_comparer_pre(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedExpression:
    """Authenticate the original typed Lens predicate before lane rewriting."""
    return _authenticate(program, source_hash, profile, final=False)


def authenticate_lens_custom_comparer_final(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedExpression:
    """Return authority for only the final-tree Lens tint predicate."""
    return _authenticate(program, source_hash, profile, final=True)
