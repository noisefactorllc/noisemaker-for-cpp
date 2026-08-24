"""Immutable proof construction for the deliberately narrow counted-for subset."""

from __future__ import annotations

from collections import deque
from dataclasses import replace
import hashlib
import re

from .typed_ir import (CountedLoopProgramProof, CountedLoopProof, TypedExpression,
                       TypedFunction, TypedProgram, TypedStatement)


_MAX_CHARGE = (1 << 63) - 1
SOURCE_GLOBAL_LITERAL_INT_CAPABILITY = "source-global-literal-int-v1"


_SOURCE_GLOBAL_LITERAL_INT_PROFILES = {
    "filter/bloom:ntapGather": {
        "raw": "f11c983976cb8450d611e8d888bd151a4c2cfdda8d9d772f906608dedb99d237",
        "source": "1d20c3bccadf30a1f6c3c6f8903ed805287933fcc1257d3ae6d4b98c5d0b9f81",
        "defines": (), "integer": ("MAX_TAPS", 8, "64", 64),
        "globals": (("MAX_TAPS", 8, "int", "64"),
                    ("GOLDEN_ANGLE", 9, "float", "2.39996323"),
                    ("PI", 10, "float", "3.14159265359")),
        "reads": (("main", 11, 30, 35, 30, 43), ("main", 11, 37, 25, 37, 33)),
        "pre_functions": "a000425b8ae57882a6877bf2c390f3d1fb3ce226d0181f0fa76d8851d7a79163",
        "post_functions": "66138a890082a6185afea09a5f9a169114193bf0134b6153737a663b27a86270",
        "pre_whole": "915a83f7673ec52fd79e8ed7a0a02094f720fbaa575db63318227f14c3aa2f51",
        "post_whole": "ff1fa1ba17abb3bdcd8daf7059b517609db49cfc62c10836b86ea86a1d4c696c",
        "interface": "b1bbe45469447847e91fbb66b6ee1b0cfc5a5a07cdac53cb322a728e295b8fb8",
    },
    "filter/directionalBlur:directionalBlur": {
        "raw": "1e4a9d6371683b75a1dbefa968e1536e0017e921fe02f80e600e8f1482e8691c",
        "source": "587b19df3989bf8bb649a86265f4210561077ccadcec30f0a92077510bcbf668",
        "defines": (), "integer": ("N", 6, "32", 32),
        "globals": (("N", 6, "int", "32"),),
        "reads": (("main", 9, 22, 42, 22, 43), ("main", 9, 26, 25, 26, 26),
                  ("main", 9, 27, 37, 27, 38), ("main", 9, 31, 29, 31, 30)),
        "pre_functions": "8c0e81f16787bce2ab63a414b9774702ce3ceac9be71f7bad46c9bccde14ddfa",
        "post_functions": "6e57feabe450d500b7ac2ddf328e855d72e0eb2c764c89b94c6c6f9afa184f96",
        "pre_whole": "30011a8fd6f15943857b5d978a5383cbf0408becbfcdd2a8e9fd08eddab11153",
        "post_whole": "21e4cc0784b7bbffa453e549776e3ed332df1219bf77d1c42bf32d650f8c1f7b",
        "interface": "3934c143ad58175d44458d78b2641badf31363c0f8438b1b5f656cbf6e269858",
    },
    "filter/spinBlur:spinBlur": {
        "raw": "a5ee242e189066b55d4d5c3140e957418bdff582b367d1f6d4cdfee4c333b405",
        "source": "b829271f6c58fccde0e5723cd2bc7d7d3f47acfeb4cf1ce157bc996fb04ff1ee",
        "defines": (), "integer": ("N", 9, "32", 32),
        "globals": (("N", 9, "int", "32"),),
        "reads": (("main", 16, 45, 37, 45, 38), ("main", 16, 54, 25, 54, 26),
                  ("main", 16, 55, 41, 55, 42), ("main", 16, 60, 29, 60, 30)),
        "pre_functions": "f9563d0e1e160ac48d4f6b0becdcb4ced10342039f0ef8c0a09f822e0c8cc8e8",
        "post_functions": "974b46a9db569acad639c8fd500c839f48f15b9bd42baac27374e204ca1d9e51",
        "pre_whole": "5d3e1a5f3907bc1678620013f2a5e6854c386d12af60a1e92bc196c06ee7e6bc",
        "post_whole": "af920749f40d2f9eafcfa3bf9d1ffccf3164571475e1b9162053cba5b3e43bff",
        "interface": "4b4d07b3a0cd718e48c976ef202de9dff5e7c35d422c371f6243ff0fbf9fa723",
    },
    "filter/strokes:stkSmear": {
        "raw": "dac057232a650f3c9eb56829aa12507b639d8632f6fc132cbd067a28996fa4db",
        "source": "796bad6231e640aec7c6f471465f57112f77394d921bff9902833955e1e20f15",
        "defines": (("MODE", "int", "0"),), "integer": ("MAX_TAPS", 8, "24", 24),
        "globals": (("MAX_TAPS", 8, "int", "24"),),
        "reads": (("smear", 39, 156, 26, 156, 34),),
        "pre_functions": "5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9",
        "post_functions": "0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344",
        "pre_whole": "b7b6c65e3275843bd141f9b0c1fcf40daad671dcbeebef2db6a4684ec750790c",
        "post_whole": "5ac93407e6a52ef895a887b3817c781d58ac9b974afe30415f31c6b4a9e8cbbf",
        "interface": "8fe812a5bdfa275782969cb6146b0e8005e8dc521af9e5b10926bc49d2b89fef",
    },
    "filter/vaseline:upsample": {
        "raw": "39055a214903d09a9b2dd8db9ec5b2023a920c22707ec424ae90d5fb90ebf461",
        "source": "1785f58af7b191e5a4f1a55223476d12372c97f87c062d34ecefe07550b05c93",
        "defines": (), "integer": ("TAP_COUNT", 8, "32", 32),
        "globals": (("TAP_COUNT", 8, "int", "32"),
                    ("RADIUS", 9, "float", "48.0"),
                    ("GOLDEN_ANGLE", 10, "float", "2.39996323"),
                    ("BRIGHTNESS_ADJUST", 11, "float", "0.15")),
        "reads": (("main", 16, 49, 25, 49, 34), ("main", 16, 50, 36, 50, 45)),
        "pre_functions": "9f2f11099585a38441157f4e4bb847808c4fd81df1c69cc79d1b651b0fe90374",
        "post_functions": "2e86ae95c587a74560e8cdd1d72bdf3f1d5cc9a14183ed136dc1950a590b2389",
        "pre_whole": "5771c7b74d9e30e47f0b84438bc40e16d4c0da36346325862bef6516c5f0d60d",
        "post_whole": "831676d46152cd861a4f658fb6bfe75c06c3a8275d2b9acaae00ae8038cc39a6",
        "interface": "fc9fd33b3e14a9808c66c17f3b358d79be3b97c11c6fd6ea281ce51118e0de9e",
    },
    "filter/wind:wind": {
        "raw": "68eb0f4deca51ab5352307fa06509b153cf19a29cea4820d054adafa42655f22",
        "source": "665e842850e766cbf988212669457fb9fd76dff59e52a2f7b2cedd242e490fa4",
        "defines": (("METHOD", "int", "1"),), "integer": ("MAX_STEPS", 8, "128", 128),
        "globals": (("MAX_STEPS", 8, "int", "128"),
                    ("STEP_PX", 9, "float", "1.0"),
                    ("MAX_REACH", 10, "float", "128.0")),
        "reads": (("main", 13, 46, 26, 46, 35),),
        "pre_functions": "214d03b9c58da73392e8b05200035b6e81244dbec06705302a237da23081ef6d",
        "post_functions": "70e4d4612ed144e0beb110e8fbbaf5d02b60e27e23fbf6961a30ac8d43bbb8e4",
        "pre_whole": "b08edc234c42aa039867a7c549eff408e7c3c51cfa28d0951a437a00043a2dc0",
        "post_whole": "6a5cb2724a9dfa61aaf5f7879a65fe9ec3cd353b7e815f20eb0915e4a103f9e0",
        "interface": "455e2e5350b3a027556adc181e5ce3099ca395f801add229956b750d31acdf85",
    },
}
SOURCE_GLOBAL_LITERAL_INT_KEYS = frozenset(_SOURCE_GLOBAL_LITERAL_INT_PROFILES)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement_expressions(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement_expressions(child)


def clear_counted_loop_proofs(
        functions: tuple[TypedFunction, ...]) -> tuple[TypedFunction, ...]:
    """Return the exact submitted tree with only counted-loop proofs cleared."""
    return tuple(replace(function, body=tuple(_clear_proofs(statement)
                                               for statement in function.body))
                 for function in functions)


def authenticate_source_global_literal_int(
        *, key: str, raw_source: str, source: str,
        preprocessor_defines: tuple[object, ...], declarations: tuple[object, ...],
        functions: tuple[TypedFunction, ...], profile: str | None,
) -> tuple[tuple[int, int, str, object], ...]:
    """Authenticate the closed Task 23 pre-proof profile and return one bound seed."""
    expected = _SOURCE_GLOBAL_LITERAL_INT_PROFILES.get(key)
    if expected is None:
        if profile is not None:
            raise ValueError(f"{key}: source-global literal-int profile is not admitted")
        return ()
    if profile is None:
        return ()
    if profile != SOURCE_GLOBAL_LITERAL_INT_CAPABILITY:
        raise ValueError(f"{key}: exact source-global literal-int profile required")
    if _text_sha(raw_source) != expected["raw"] or _text_sha(source) != expected["source"]:
        raise ValueError(f"{key}: source-global literal-int source digest mismatch")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in preprocessor_defines)
    if defines != expected["defines"]:
        raise ValueError(f"{key}: source-global literal-int define profile mismatch")
    if functions != attach_counted_loop_proofs(functions, key):
        raise ValueError(f"{key}: source-global literal-int authentication requires canonical pre-proof functions")
    if _sha(functions) != expected["pre_functions"]:
        raise ValueError(f"{key}: source-global literal-int pre-function profile mismatch")

    source_globals = tuple(item for item in declarations
                           if item.symbol.storage not in {"uniform", "output"})
    actual_globals = tuple((item.symbol.name, item.symbol.id, item.type.display(),
                            item.initializer.literal if item.initializer is not None else None)
                           for item in source_globals)
    if actual_globals != expected["globals"]:
        raise ValueError(f"{key}: source-global literal-int declaration profile mismatch")
    integer_name, integer_id, integer_literal, integer_value = expected["integer"]
    integer = next((item for item in source_globals if item.symbol.id == integer_id), None)
    if (integer is None or integer.symbol.name != integer_name
            or integer.symbol.storage != "const" or integer.symbol.writable
            or integer.symbol.direction != "in" or integer.type.display() != "int"
            or integer.initializer is None or integer.initializer.kind != "literal"
            or integer.initializer.type.display() != "int"
            or integer.initializer.category != "rvalue"
            or integer.initializer.children
            or integer.initializer.literal != integer_literal
            or integer.initializer.literal_value != integer_value
            or re.fullmatch(r"[1-9][0-9]*", integer_literal) is None):
        raise ValueError(f"{key}: malformed source-global literal-int declaration")

    reads: list[tuple[object, ...]] = []
    for function in functions:
        for statement in function.body:
            for expression in _walk_statement_expressions(statement):
                if expression.kind == "id" and expression.symbol_id == integer_id:
                    span = expression.span
                    if (expression.symbol != integer.symbol
                            or expression.category != "readonly lvalue"):
                        raise ValueError(f"{key}: malformed source-global literal-int read")
                    reads.append((function.name, function.signature.id,
                                  span.start_line, span.start_column,
                                  span.end_line, span.end_column))
    if tuple(reads) != expected["reads"]:
        raise ValueError(f"{key}: source-global literal-int read profile mismatch")
    return ((integer_id, integer_value, "source-global-const-literal",
             integer.symbol),)


def _checked_add(left: int, right: int) -> int:
    value = left + right
    return value if 0 <= value <= _MAX_CHARGE else _MAX_CHARGE + 1


def _checked_mul(left: int, right: int) -> int:
    if left < 0 or right < 0 or (left and right > _MAX_CHARGE // left):
        return _MAX_CHARGE + 1
    return left * right


def _integer_literal(value: TypedExpression) -> int | None:
    if value.kind == "literal" and value.type.display() == "int" and isinstance(value.literal_value, int):
        return value.literal_value
    if (value.kind == "unary" and value.operator == "-" and len(value.children) == 1
            and (operand := _integer_literal(value.children[0])) is not None):
        return -operand
    return None


def _contains_return(value: TypedStatement) -> bool:
    return value.kind == "return" or any(_contains_return(child) for child in value.children)


def _loop_products(value: TypedStatement) -> tuple[int, ...]:
    result: list[int] = []
    if value.loop_proof is not None:
        result.append(value.loop_proof.lexical_product)
    for child in value.children:
        result.extend(_loop_products(child))
    return tuple(result)


def _local_bound(value: TypedStatement, key: str) -> tuple[int, int, str, object] | None:
    if value.kind != "decl" or len(value.expressions) != 1:
        return None
    declaration = value.expressions[0]
    if (declaration.kind != "declaration" or declaration.type.display() != "int"
            or declaration.symbol is None
            or len(declaration.children) != 1):
        return None
    initializer = declaration.children[0]
    literal = _integer_literal(initializer)
    if declaration.symbol.storage == "const" and literal is not None:
        return declaration.symbol_id or 0, literal, "local-const-literal", declaration.symbol
    if (key != "filter/reverb:reverb" or declaration.symbol.name != "iters"
            or declaration.symbol.storage != "local"):
        return None
    if (initializer.kind != "builtin" or initializer.callee != "clamp"
            or len(initializer.children) != 3):
        return None
    source, minimum, maximum = initializer.children
    if (source.kind != "id" or source.symbol is None or source.symbol.storage != "uniform"
            or source.symbol.name != "iterations" or source.type.display() != "int"
            or _integer_literal(minimum) != 1 or _integer_literal(maximum) != 8):
        return None
    return declaration.symbol_id or 0, 8, "reverb-clamp-1-8", declaration.symbol


def _annotate_sequence(values: tuple[TypedStatement, ...], key: str, depth: int,
                       ancestor_product: int,
                       bounded: dict[int, tuple[int, str, object]]) -> tuple[TypedStatement, ...]:
    result: list[TypedStatement] = []
    active = dict(bounded)
    for value in values:
        annotated = _annotate_statement(value, key, depth, ancestor_product, active)
        result.append(annotated)
        bound = _local_bound(annotated, key)
        if bound is not None:
            symbol_id, maximum, kind, symbol = bound
            active[symbol_id] = (maximum, kind, symbol)
    return tuple(result)


def _annotate_statement(value: TypedStatement, key: str, depth: int,
                        ancestor_product: int,
                        bounded: dict[int, tuple[int, str, object]]) -> TypedStatement:
    if value.kind == "block":
        return replace(value, children=_annotate_sequence(
            value.children, key, depth, ancestor_product, bounded))
    if value.kind == "if":
        return replace(value, children=tuple(
            _annotate_statement(child, key, depth, ancestor_product, dict(bounded))
            for child in value.children))
    if value.kind != "for":
        return replace(value, children=tuple(
            _annotate_statement(child, key, depth, ancestor_product, dict(bounded))
            for child in value.children))

    # Every admitted form has an initializer statement and body, then exact
    # condition/update expressions. Anything else remains ordinary unproved IR.
    if len(value.children) != 2 or len(value.expressions) != 2:
        return value
    initializer, body = value.children
    if (initializer.kind != "decl" or len(initializer.expressions) != 1
            or initializer.expressions[0].kind != "declaration"):
        return value
    declaration = initializer.expressions[0]
    if (declaration.type.display() != "int" or declaration.symbol is None
            or declaration.symbol.storage != "local" or len(declaration.children) != 1):
        return value
    start = _integer_literal(declaration.children[0])
    condition, update = value.expressions
    if (start is None or condition.kind != "binary" or condition.operator not in {"<", "<="}
            or len(condition.children) != 2):
        return value
    induction, bound_expression = condition.children
    symbol_id = declaration.symbol_id
    if (symbol_id is None or declaration.symbol.id != symbol_id
            or induction.kind != "id" or induction.symbol_id != symbol_id
            or induction.symbol != declaration.symbol):
        return value
    if (update.kind not in {"post", "unary"} or update.operator != "++"
            or len(update.children) != 1 or update.children[0].kind != "id"
            or update.children[0].symbol_id != symbol_id
            or update.children[0].symbol != declaration.symbol):
        return value

    bound = _integer_literal(bound_expression)
    bound_kind = "literal"
    if bound is None and bound_expression.kind == "id" and bound_expression.symbol_id in bounded:
        bound, bound_kind, bound_symbol = bounded[bound_expression.symbol_id]
        if bound_expression.symbol != bound_symbol:
            return value
    if bound is None or _contains_return(body):
        return value
    trips = max(0, bound - start + (1 if condition.operator == "<=" else 0))
    current_product = _checked_mul(ancestor_product, trips)
    annotated_body = _annotate_statement(body, key, depth + 1, current_product, dict(bounded))
    descendant_products = _loop_products(annotated_body)
    product = max((current_product, *descendant_products))
    proof = CountedLoopProof(symbol_id, start, bound, condition.operator,
                             update.operator, bound_kind, trips, depth + 1,
                             depth + 1, product, 0)
    return replace(value, children=(initializer, annotated_body), loop_proof=proof)


def _expressions(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _expressions(child)


def _statement_calls(value: TypedStatement, depth: int = 0):
    for expression in value.expressions:
        for item in _expressions(expression):
            if item.kind == "call" and item.signature_id is not None:
                yield item.signature_id, depth
    child_depth = depth + 1 if value.kind == "for" and value.loop_proof is not None else depth
    for child in value.children:
        yield from _statement_calls(child, child_depth)


def _expression_charge(value: TypedExpression, function_charge) -> int:
    result = 0
    for child in value.children:
        result = _checked_add(result, _expression_charge(child, function_charge))
    if value.kind == "call" and value.signature_id is not None:
        result = _checked_add(result, function_charge(value.signature_id))
    return result


def _statement_charge(value: TypedStatement, function_charge) -> int:
    expression_charge = sum((_expression_charge(item, function_charge)
                             for item in value.expressions), 0)
    if value.kind == "if":
        arms = tuple(_statement_charge(child, function_charge) for child in value.children)
        return _checked_add(expression_charge, max(arms, default=0))
    if value.kind == "for" and value.loop_proof is not None:
        body = _statement_charge(value.children[1], function_charge)
        return _checked_mul(value.loop_proof.trip_count, _checked_add(1, body))
    result = expression_charge
    for child in value.children:
        result = _checked_add(result, _statement_charge(child, function_charge))
    return result


def _replace_metrics(value: TypedStatement, base_depth: int, entry_charge: int) -> TypedStatement:
    proof = value.loop_proof
    if proof is not None:
        proof = replace(proof, effective_depth=base_depth + proof.lexical_depth,
                        entrypoint_charge=entry_charge)
    return replace(value, loop_proof=proof,
                   children=tuple(_replace_metrics(child, base_depth, entry_charge)
                                  for child in value.children))


def _clear_proofs(value: TypedStatement) -> TypedStatement:
    return replace(value, loop_proof=None,
                   children=tuple(_clear_proofs(child) for child in value.children))


def attach_counted_loop_proofs(
        functions: tuple[TypedFunction, ...], key: str, *,
        source_global_bounds: tuple[tuple[int, int, str, object], ...] = (),
) -> tuple[TypedFunction, ...]:
    """Attach local and whole-entrypoint loop evidence without consulting source text."""
    clean = clear_counted_loop_proofs(functions)
    initial_bounds = {symbol_id: (maximum, kind, symbol)
                      for symbol_id, maximum, kind, symbol in source_global_bounds}
    if len(initial_bounds) != len(source_global_bounds):
        raise ValueError(f"{key}: duplicate source-global counted-loop seed")
    annotated = tuple(replace(function, body=_annotate_sequence(
        function.body, key, 0, 1, dict(initial_bounds)))
                      for function in clean)
    definitions = {function.signature.id: function for function in annotated if function.body}
    main = next((function for function in annotated if function.name == "main" and function.body), None)
    if main is None:
        return annotated

    # Maximum loop depth already active at each function entry. A growing
    # value after |functions| passes denotes an interprocedural cycle.
    base_depth = {signature_id: 0 for signature_id in definitions}
    queue = deque([main.signature.id])
    reachable = {main.signature.id}
    relaxations = 0
    while queue:
        signature_id = queue.popleft()
        function = definitions[signature_id]
        for statement in function.body:
            for callee, local_depth in _statement_calls(statement):
                if callee not in definitions:
                    continue
                newly_reachable = callee not in reachable
                reachable.add(callee)
                candidate = base_depth[signature_id] + local_depth
                if candidate > base_depth[callee] or newly_reachable:
                    base_depth[callee] = candidate
                    queue.append(callee)
                    relaxations += 1
                    if relaxations > max(1, len(definitions) * len(definitions)):
                        base_depth[callee] = _MAX_CHARGE
                        queue.clear()
                        break

    charging: set[int] = set()
    charge_cache: dict[int, int] = {}

    def function_charge(signature_id: int) -> int:
        if signature_id not in definitions:
            return 0
        if signature_id in charge_cache:
            return charge_cache[signature_id]
        if signature_id in charging:
            return _MAX_CHARGE + 1
        charging.add(signature_id)
        result = 0
        for statement in definitions[signature_id].body:
            result = _checked_add(result, _statement_charge(statement, function_charge))
        charging.remove(signature_id)
        charge_cache[signature_id] = result
        return result

    entry_charge = function_charge(main.signature.id)
    return tuple(replace(function, body=tuple(
        _replace_metrics(statement, base_depth.get(function.signature.id, 0), entry_charge)
        for statement in function.body)) for function in annotated)


def summarize_counted_loop_proofs(functions: tuple[TypedFunction, ...]) -> CountedLoopProgramProof:
    proofs: list[CountedLoopProof] = []
    unproved = 0
    definitions = {function.signature.id: function for function in functions if function.body}
    graph: dict[int, set[int]] = {signature_id: set() for signature_id in definitions}

    def statement(value: TypedStatement, owner: int) -> None:
        nonlocal unproved
        if value.kind in {"for", "while", "dowhile"}:
            if value.loop_proof is None:
                unproved += 1
            else:
                proofs.append(value.loop_proof)
        for expression in value.expressions:
            for item in _expressions(expression):
                if item.kind == "call" and item.signature_id in definitions:
                    graph[owner].add(item.signature_id)
        for child in value.children:
            statement(child, owner)

    for signature_id, function in definitions.items():
        for item in function.body:
            statement(item, signature_id)

    visiting: set[int] = set()
    visited: set[int] = set()

    def acyclic(node: int) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        result = all(acyclic(child) for child in graph[node])
        visiting.remove(node)
        visited.add(node)
        return result

    graph_acyclic = all(acyclic(node) for node in graph)
    return CountedLoopProgramProof(
        len(proofs), unproved,
        max((proof.effective_depth for proof in proofs), default=0),
        max((proof.lexical_product for proof in proofs), default=0),
        max((proof.entrypoint_charge for proof in proofs), default=0),
        graph_acyclic,
    )


def _whole_program_identity(program: TypedProgram, functions: tuple[TypedFunction, ...],
                            summary: CountedLoopProgramProof) -> tuple[object, ...]:
    return (
        program.key, program.source, program.raw_source, program.declarations,
        functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        summary, program.preprocessor_defines,
    )


def _interface_identity(program: TypedProgram) -> tuple[object, ...]:
    return (
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    )


def rebuild_authenticated_counted_loop_proofs(
        program: TypedProgram, profile: str | None,
) -> tuple[tuple[TypedFunction, ...], CountedLoopProgramProof]:
    """Rebuild counted-loop proof only from the authenticated proof-free tree."""
    cleared = clear_counted_loop_proofs(program.functions)
    pre_functions = attach_counted_loop_proofs(cleared, program.key)
    seed = authenticate_source_global_literal_int(
        key=program.key, raw_source=program.raw_source, source=program.source,
        preprocessor_defines=program.preprocessor_defines,
        declarations=program.declarations, functions=pre_functions, profile=profile)
    expected = _SOURCE_GLOBAL_LITERAL_INT_PROFILES.get(program.key)
    pre_summary = summarize_counted_loop_proofs(pre_functions)
    if expected is not None:
        if _sha(_whole_program_identity(program, pre_functions, pre_summary)) != expected["pre_whole"]:
            raise ValueError(f"{program.key}: source-global literal-int pre-program profile mismatch")
        if _sha(_interface_identity(program)) != expected["interface"]:
            raise ValueError(f"{program.key}: source-global literal-int interface profile mismatch")
    attached = attach_counted_loop_proofs(
        pre_functions, program.key, source_global_bounds=seed)
    return attached, summarize_counted_loop_proofs(attached)


def validate_source_global_literal_int_program(
        program: TypedProgram, profile: str | None) -> None:
    """Require the submitted Task 23 tree to equal independently rebuilt proof."""
    if program.key not in _SOURCE_GLOBAL_LITERAL_INT_PROFILES and profile is None:
        return
    attached, summary = rebuild_authenticated_counted_loop_proofs(program, profile)
    expected = _SOURCE_GLOBAL_LITERAL_INT_PROFILES[program.key]
    if program.functions != attached or program.counted_loop_proof != summary:
        raise ValueError(f"{program.key}: source-global literal-int post-proof mismatch")
    if _sha(attached) != expected["post_functions"]:
        raise ValueError(f"{program.key}: source-global literal-int post-function profile mismatch")
    if _sha(_whole_program_identity(program, attached, summary)) != expected["post_whole"]:
        raise ValueError(f"{program.key}: source-global literal-int post-program profile mismatch")
