"""Source-locked comparer profile for the Lens tint site.

The one `color.rgb == vec3(1.0)` predicate is emitted as GLSL vector equality
(every lane equal), as the authority compiles it (all(equal())).
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "lens-tint-vector-equality-v1"
LENS_KEY = "classicNoisedeck/lensDistortion:lensDistortion"
RAW_BYTES = 8192
RAW_SHA256 = "925f4150c4029d13c35de55203d58cb91d8a1f9abfb8146fbb40dcf7cfc1b402"
NORMALIZED_BYTES = 7646
NORMALIZED_SHA256 = "5a28ab1e571db951bafcbf6b4e59b6ec488d08308785f86e999b7c1639ac27b7"
INTERFACE_SHA256 = "eba53b76b6673ca7f57a1622c24c902d2ed8fe711802bf92064d7e419bce2693"
PRE_MAIN_SHA256 = "f7e69cce9ea76f95421cad4ce14f617ab193beab8af149ac7a1139d52423c675"
PRE_FUNCTIONS_SHA256 = "2104d6186cd8a42acc8506b0cbdddbee05873a022043783573dbaa6c31c78e33"
PRE_WHOLE_SHA256 = "79ea379a1b97f660c09b5dc748acc92c17512a7115716d42e38e79abe2085536"
FINAL_MAIN_SHA256 = "5e230dc77f0948fc63f0388f9e814985d90fc7135a387e3c0c4a7e823bc1263c"
FINAL_FUNCTIONS_SHA256 = "10fd8ca6c968b92ee912ecb28f4ab6fb0a8c8e6a34958c7b750e22279adf194b"
FINAL_WHOLE_SHA256 = "0727313b7b8e6faae302aa3fbd298a44b35314ca2d71b2e1eaecb129f67042ec"
PROFILE_SHA256 = "d2eaf21073062eea8cadeb7937a2cc890fa295d86793da36aa9958cef51e8c09"

# Raw corpus source line 271 becomes normalized typed-source line 263.
RAW_SOURCE_LINE = 271
SITE_PATH = (21, "e0", 0, 1, 1)
ASSIGNMENT_SPAN = "263:5-263:133"
ASSIGNMENT_SHA256 = "92fffd2e2fbd111ce9567ad1c87cc1e4b1bc71ab4f53a088f8742c4cdea6e847"
MIX_SPAN = "263:17-263:133"
MIX_SHA256 = "d42942c8392d2e8d514bbe5a32657a66e1d28f759c2caef1914f37d830a971a3"
SITE_SPAN = "263:33-263:118"
SITE_SHA256 = "a49316fcf059c002ee01b31389c86cc662c2c159ea3e5a110c151097037be735"
PREDICATE_SPAN = "263:33-263:55"
PREDICATE_SHA256 = "0181757256e1b0442b6bd201c860fde2150b1501bf8c6b24b1dcaf0605d7443c"
LEFT_SHA256 = "9379db8cbbabf330533ae67fa686741c2574e38166fc27d0bed934cd81c19360"
RIGHT_SHA256 = "17b2e7953da9f7c270071ea4152a323cf6d3511bc33304890ee072658059e68c"
TRUE_ARM_SHA256 = "9a46189ed455e74e5a2716cd30e68e60e3cdc6ebd992dbd2b57cb1bafef73519"
FALSE_ARM_SHA256 = "3310822d5f90db831d88b3f98ee693b26177ecb4a96ab0a48ebe6e784616d150"
ALPHA_SHA256 = "782f4fc9ddb7ac1528e784d70527f99c5d52ec10fb467da7ef10fc1696e1b241"

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
