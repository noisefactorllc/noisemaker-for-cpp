"""Exact identity profile for Rotate's sole by-value ``mat2`` helper return."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "rotate-mat2-return-v1"
ROTATE_KEY = "filter/rotate:rot"

_RAW_BYTES = 1197
_RAW_SHA256 = "c23e8462e8240f25a715fa3eb05e567269c8d410d27943ba346ebccdd0de1f8f"
_NORMALIZED_BYTES = 964
_NORMALIZED_SHA256 = "e0e2b723289b08cbfcd6f1fc0a8481869e674de3cfedc0ec5df6d96f64748bb5"
_FUNCTIONS_SHA256 = "f5b9f47764c12f05a55925aaca0cf99027ef0b78f67d0122df657f068ba23d56"
_WHOLE_SHA256 = "3e4312d4c94a8d8b207aa351f8974f417cb5acd63d45a70b1f4a8e606ed2e1b6"
_INTERFACE_SHA256 = "bfdeb36f89cb3dd84ec4339564e5d830f0f18c9f011d4b563f3cca45973e28df"
_PROFILE_SHA256 = "2cfd54eca913518997b359a75e179eb45a323bf50c635b8d2d70874a1dfec76c"
_HELPER_SIGNATURE_SHA256 = "a04f91d3f994b30e78f97d04ca5b572c1a94425c25150c6af69345ec8119fd8f"
_HELPER_SHA256 = "f88f6345a607d84afbe28d4859e3afd70f0c75c0c0e51e4de42cc7f1e2051006"
_CONSTRUCTOR_SHA256 = "e663648e5aadc5bbaf20fe171459a9a64e2deb713a46665e63e3a6c08d416796"
_CALL_SHA256 = "5328e90c21b68b353d8c9ab9caf2a1f3ba59d9de557d72729978670f851ff1b1"
_PARENT_SHA256 = "4e166653131410b87db5123dfe23746cd54e3096b4728e7ea22cd908607d766f"
_CHILDREN = (
    ("id", "float", None, 17, None, "17:17-17:18",
     "75c1efb26380f681fdb7d200802991dd855d454356d3f0ee1ad70c8bf84b47c3"),
    ("unary", "float", "-", None, 18, "17:20-17:22",
     "cfc377557bca9165a99aab8e6fcdda7efa668f943a4b47bbfb67b51fa9d390e5"),
    ("id", "float", None, 18, None, "17:24-17:25",
     "86d88e25ce225b8d3b4c83361b2f88364d67a06c413c8391a998409c97bc949e"),
    ("id", "float", None, 17, None, "17:27-17:28",
     "93ee2e627a305854a7395d722e32df1d45ff16bbbff524d91455893d4b5bd11d"),
)
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

__all__ = ("PROFILE", "ROTATE_KEY", "authenticate_rotate_mat2_return",
           "apply_rotate_mat2_return")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for item in value.expressions:
        yield from _walk_expression(item)
    for child in value.children:
        yield from _walk_statement(child)


def _profile_tuple() -> tuple[object, ...]:
    return (
        PROFILE, ROTATE_KEY, _RAW_SHA256, (), _FUNCTIONS_SHA256,
        _WHOLE_SHA256, _INTERFACE_SHA256,
        (10, "rotate2D", _HELPER_SIGNATURE_SHA256, _HELPER_SHA256,
         "14:1-18:2", 3),
        ((2, "e0", 0), "17:12-17:29", _CONSTRUCTOR_SHA256, _CHILDREN),
        ((8, "e0", 0, 1, 0), "35:10-35:40", _CALL_SHA256, 10,
         "binary", 0, _PARENT_SHA256),
        ((8, "e0", 0, 1), "35:10-35:45", _PARENT_SHA256, "*",
         ("mat2", "vec2")),
    )


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_rotate_mat2_return(
        program: TypedProgram, source_hash: str | None,
        profile: str | None,
) -> tuple[TypedFunction, TypedExpression, TypedExpression, TypedExpression]:
    """Authenticate and return the exact helper/constructor/call/parent objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != ROTATE_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or program.preprocessor_defines != () or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    proof = program.counted_loop_proof
    if (proof is None or proof.loop_count != 0 or proof.unproved_loop_count != 0
            or proof.max_effective_depth != 0 or proof.max_lexical_product != 0
            or proof.entrypoint_charge != 0 or not proof.call_graph_acyclic):
        raise _fail("loop or call graph profile mismatch")
    if (len(program.declarations) != 7
            or [(item.symbol.id, item.symbol.name, item.type.display(),
                 item.symbol.storage) for item in program.declarations]
            != [(1, "inputTex", "sampler2D", "uniform"),
                (2, "rotation", "float", "uniform"),
                (3, "wrap", "int", "uniform"),
                (4, "speed", "int", "uniform"),
                (5, "time", "float", "uniform"),
                (6, "fragColor", "vec4", "output"),
                (7, "TAU", "float", "const")]
            or program.resources.uniforms != (
                "inputTex", "rotation", "wrap", "speed", "time")
            or program.resources.samplers != ("inputTex",)
            or program.resources.outputs != ("fragColor",)
            or not program.resources.uses_texture
            or program.resources.uses_derivatives):
        raise _fail("declaration, resource, or binding signature mismatch")
    if len(program.functions) != 2:
        raise _fail("function cardinality mismatch")
    main, helper = program.functions
    if ((main.id, main.name, main.return_type.display(), len(main.parameters),
         len(main.body), _sha(main.signature), _sha(main), _span(main))
            != (9, "main", "void", 0, 13,
                "376c8ad924b449a468dbc7277a4ad97d9539a2e42c44eb40cbd54d28e153e8aa",
                "0b677d94fa375cae65644c2daedcfb15572e54ecf496b6904d3256a62456fbc4",
                "20:1-52:2")
            or (helper.id, helper.name, helper.return_type.display(),
                len(helper.parameters), len(helper.body), _sha(helper.signature),
                _sha(helper), _span(helper))
            != (10, "rotate2D", "mat2", 1, 3, _HELPER_SIGNATURE_SHA256,
                _HELPER_SHA256, "14:1-18:2")):
        raise _fail("function identity, signature, body, or order mismatch")
    parameter = helper.parameters[0]
    if ((parameter.id, parameter.name, parameter.type.display(),
         parameter.storage, parameter.direction, _span(parameter))
            != (8, "angle", "float", "parameter", "in", "14:15-14:26")):
        raise _fail("helper parameter mismatch")
    for statement, symbol_id, name, builtin in zip(
            helper.body[:2], (17, 18), ("c", "s"), ("cos", "sin")):
        if statement.kind != "decl" or len(statement.expressions) != 1:
            raise _fail("helper local statement shape mismatch")
        declaration = statement.expressions[0]
        initializer = declaration.children[0] if len(declaration.children) == 1 else None
        symbol = declaration.symbol
        if (symbol is None or
            (symbol.id, symbol.name, declaration.type.display(),
             symbol.storage, getattr(initializer, "kind", None),
             getattr(initializer, "callee", None),
             initializer.type.display())
                != (symbol_id, name, "float", "local", "builtin", builtin,
                    "float")):
            raise _fail("helper local or builtin mismatch")
    returned = helper.body[2]
    if returned.kind != "return" or len(returned.expressions) != 1:
        raise _fail("helper return statement shape mismatch")
    constructor = returned.expressions[0]
    if (constructor.kind != "construct" or constructor.type.display() != "mat2"
            or constructor.constructor_type is None
            or constructor.constructor_type.display() != "mat2"
            or constructor.category != "rvalue" or _span(constructor) != "17:12-17:29"
            or _sha(constructor) != _CONSTRUCTOR_SHA256
            or len(constructor.children) != 4):
        raise _fail("matrix constructor mismatch")
    for child, expected in zip(constructor.children, _CHILDREN):
        child_symbol = (child.children[0].symbol_id
                        if child.kind == "unary" and child.children else None)
        actual = (child.kind, child.type.display(), child.operator,
                  child.symbol_id, child_symbol, _span(child), _sha(child))
        if actual != expected:
            raise _fail("matrix constructor child mismatch")
    assignment = main.body[8].expressions[0]
    parent = assignment.children[1]
    call = parent.children[0]
    if (parent.kind != "binary" or parent.operator != "*"
            or parent.type.display() != "vec2" or len(parent.children) != 2
            or tuple(child.type.display() for child in parent.children)
            != ("mat2", "vec2") or _span(parent) != "35:10-35:45"
            or _sha(parent) != _PARENT_SHA256 or parent.children[0] is not call
            or call.kind != "call" or call.signature_id != helper.signature.id
            or call.type.display() != "mat2" or _span(call) != "35:10-35:40"
            or _sha(call) != _CALL_SHA256 or len(call.children) != 1
            or _sha(call.children[0])
            != "7f64717ca093bb2c2aee8f6826280dda7416010622ee6fac942d8148852406a0"):
        raise _fail("matrix helper call or direct parent mismatch")
    matrix_values: list[tuple[TypedFunction, TypedExpression]] = []
    calls: list[TypedExpression] = []
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if value.type.kind == "matrix":
                    matrix_values.append((function, value))
                if value.kind == "call" and value.signature_id == helper.signature.id:
                    calls.append(value)
    if matrix_values != [(main, call), (helper, constructor)] or calls != [call]:
        raise _fail("matrix expression, call, or ownership cardinality mismatch")
    if (sum(item.return_type.kind == "matrix" for item in program.functions) != 1
            or any(parameter.type.kind == "matrix" for item in program.functions
                   for parameter in item.parameters)):
        raise _fail("matrix return or parameter cardinality mismatch")
    return helper, constructor, call, parent


def apply_rotate_mat2_return(program: TypedProgram, source_hash: str | None,
                             profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_rotate_mat2_return(program, source_hash, profile)
    return program
