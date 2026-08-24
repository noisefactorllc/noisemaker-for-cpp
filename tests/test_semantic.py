"""Focused contracts for the immutable GLSL semantic frontier."""

from __future__ import annotations

import pathlib
import sys
import unittest
import copy
import json
import subprocess


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

from tools.glslcpp.check_corpus import _corpus_root


def _task23_complete_ir_forgery_matrix(testcase, program, global_name):
    """Return every Task 23 design-row forgery with exact target assertions."""
    import dataclasses
    from tools.glslcpp.frontend.semantic_types import FLOAT, INT, UINT, VOID
    from tools.glslcpp.frontend.typed_ir import (
        FunctionSignature, PreprocessorDefine, Symbol, TypedDeclaration,
        TypedExpression, TypedFunction, TypedStatement)

    declaration_matches = [item for item in program.declarations
                           if item.symbol.name == global_name]
    testcase.assertEqual(1, len(declaration_matches))
    declaration = declaration_matches[0]
    initializer = declaration.initializer
    testcase.assertIsNotNone(initializer)
    testcase.assertEqual(("const", False, "in", "int", "literal", "rvalue", ()), (
        declaration.symbol.storage, declaration.symbol.writable,
        declaration.symbol.direction, declaration.type.display(),
        initializer.kind, initializer.category, initializer.children))
    testcase.assertIsInstance(initializer.literal_value, int)
    bound_value = initializer.literal_value

    def with_declaration(changed):
        return dataclasses.replace(
            program, declarations=tuple(
                changed if item is declaration else item
                for item in program.declarations))

    def literal(spelling, value):
        return dataclasses.replace(
            initializer, literal=spelling, literal_value=value)

    def replace_first_expression(candidate, predicate, transform, label):
        replaced = 0
        def expression(value):
            nonlocal replaced
            children = tuple(expression(child) for child in value.children)
            changed = dataclasses.replace(value, children=children)
            if replaced == 0 and predicate(changed):
                changed = transform(changed)
                replaced += 1
            return changed
        def statement(value):
            return dataclasses.replace(
                value,
                expressions=tuple(expression(item) for item in value.expressions),
                children=tuple(statement(child) for child in value.children))
        functions = tuple(dataclasses.replace(
            function, body=tuple(statement(item) for item in function.body))
            for function in candidate.functions)
        testcase.assertEqual(1, replaced, label)
        return dataclasses.replace(candidate, functions=functions)

    read_predicate = lambda value: (
        value.kind == "id" and value.symbol_id == declaration.symbol.id)

    def map_source_loop(candidate, transform, label):
        replaced = 0
        def statement(value):
            nonlocal replaced
            children = tuple(statement(child) for child in value.children)
            changed = dataclasses.replace(value, children=children)
            if (changed.loop_proof is not None
                    and changed.loop_proof.bound_kind
                    == "source-global-const-literal"):
                changed = transform(changed)
                replaced += 1
            return changed
        functions = tuple(dataclasses.replace(
            function, body=tuple(statement(item) for item in function.body))
            for function in candidate.functions)
        testcase.assertEqual(1, replaced, label)
        return dataclasses.replace(candidate, functions=functions)

    def map_source_loop_bound(candidate, transform, label):
        replaced = 0
        def expression(value, in_bound=False):
            nonlocal replaced
            children = tuple(expression(child, in_bound) for child in value.children)
            changed = dataclasses.replace(value, children=children)
            if in_bound and replaced == 0 and read_predicate(changed):
                changed = transform(changed)
                replaced += 1
            return changed
        def statement(value):
            source_loop = (value.loop_proof is not None
                           and value.loop_proof.bound_kind
                           == "source-global-const-literal")
            expressions = tuple(
                expression(item, source_loop and index == 0)
                for index, item in enumerate(value.expressions))
            return dataclasses.replace(
                value, expressions=expressions,
                children=tuple(statement(child) for child in value.children))
        functions = tuple(dataclasses.replace(
            function, body=tuple(statement(item) for item in function.body))
            for function in candidate.functions)
        testcase.assertEqual(1, replaced, label)
        return dataclasses.replace(candidate, functions=functions)

    forgeries = {
        "wrong-key": dataclasses.replace(program, key=program.key + ":forged"),
        "raw-source": dataclasses.replace(program, raw_source=program.raw_source + "\n"),
        "normalized-source": dataclasses.replace(program, source=program.source + "\n"),
        "declaration-name": with_declaration(dataclasses.replace(
            declaration, symbol=dataclasses.replace(
                declaration.symbol, name=global_name + "_forged"))),
        "declaration-id": with_declaration(dataclasses.replace(
            declaration, symbol=dataclasses.replace(
                declaration.symbol, id=declaration.symbol.id + 10000))),
        "declaration-storage": with_declaration(dataclasses.replace(
            declaration, symbol=dataclasses.replace(
                declaration.symbol, storage="uniform"))),
        "declaration-writable": with_declaration(dataclasses.replace(
            declaration, symbol=dataclasses.replace(
                declaration.symbol, writable=True))),
        "literal-spelling": with_declaration(dataclasses.replace(
            declaration, initializer=literal("0" + str(bound_value), bound_value))),
        "literal-value": with_declaration(dataclasses.replace(
            declaration, initializer=literal(str(bound_value), bound_value + 1))),
        "initializer-zero": with_declaration(dataclasses.replace(
            declaration, initializer=literal("0", 0))),
        "initializer-signed": with_declaration(dataclasses.replace(
            declaration, initializer=literal("-" + str(bound_value), -bound_value))),
        "initializer-suffix": with_declaration(dataclasses.replace(
            declaration, initializer=literal(str(bound_value) + "u", bound_value))),
        "initializer-hex": with_declaration(dataclasses.replace(
            declaration, initializer=literal(hex(bound_value), bound_value))),
        "initializer-octal": with_declaration(dataclasses.replace(
            declaration, initializer=literal("0" + format(bound_value, "o"), bound_value))),
    }

    type_symbol = dataclasses.replace(declaration.symbol, type=UINT)
    forgeries["declaration-type"] = with_declaration(dataclasses.replace(
        declaration, symbol=type_symbol, type=UINT,
        initializer=dataclasses.replace(initializer, type=UINT,
                                        literal=str(bound_value) + "u")))
    unary_child = initializer
    forgeries["initializer-unary"] = with_declaration(dataclasses.replace(
        declaration, initializer=TypedExpression(
            "unary", INT, initializer.span, "rvalue", children=(unary_child,),
            operator="+")))
    half = TypedExpression("literal", INT, initializer.span, "rvalue",
                           literal=str(bound_value // 2),
                           literal_value=bound_value // 2)
    forgeries["initializer-binary"] = with_declaration(dataclasses.replace(
        declaration, initializer=TypedExpression(
            "binary", INT, initializer.span, "rvalue", children=(half, half),
            operator="+")))
    forgeries["initializer-cast"] = with_declaration(dataclasses.replace(
        declaration, initializer=TypedExpression(
            "call", INT, initializer.span, "rvalue", children=(initializer,),
            callee="int")))
    forgeries["initializer-constructor"] = with_declaration(dataclasses.replace(
        declaration, initializer=TypedExpression(
            "construct", INT, initializer.span, "rvalue",
            children=(initializer,), constructor_type=INT)))
    forgeries["initializer-id"] = with_declaration(dataclasses.replace(
        declaration, initializer=TypedExpression(
            "id", INT, initializer.span, "readonly lvalue",
            symbol_id=declaration.symbol.id, symbol=declaration.symbol)))
    forgeries["missing-global"] = dataclasses.replace(
        program, declarations=tuple(item for item in program.declarations
                                    if item is not declaration))
    extra_symbol = Symbol(
        declaration.symbol.id + 10000, global_name + "_EXTRA", INT,
        "const", declaration.symbol.span, False)
    extra = TypedDeclaration(extra_symbol, INT, declaration.span, initializer)
    forgeries["extra-global"] = dataclasses.replace(
        program, declarations=program.declarations + (extra,))
    dependency_symbol = dataclasses.replace(
        extra_symbol, name=global_name + "_BASE")
    dependency = TypedDeclaration(
        dependency_symbol, INT, declaration.span, initializer)
    dependent_initializer = TypedExpression(
        "id", INT, initializer.span, "readonly lvalue",
        symbol_id=dependency_symbol.id, symbol=dependency_symbol)
    dependent_declaration = dataclasses.replace(
        declaration, initializer=dependent_initializer)
    forgeries["dependent-global"] = dataclasses.replace(
        program, declarations=tuple(
            dependency if item is declaration else item
            for item in program.declarations) + (dependent_declaration,))

    if program.preprocessor_defines:
        first_define = program.preprocessor_defines[0]
        forged_defines = (dataclasses.replace(
            first_define, canonical_value=str(int(first_define.canonical_value) + 1)),
            *program.preprocessor_defines[1:])
    else:
        forged_defines = (PreprocessorDefine("TASK23_FORGED", "int", "1"),)
    forgeries["define"] = dataclasses.replace(
        program, preprocessor_defines=tuple(forged_defines))

    float_globals = [item for item in program.declarations
                     if item.symbol.storage == "const"
                     and item.type == FLOAT and item.initializer is not None]
    if float_globals:
        float_declaration = float_globals[0]
        testcase.assertEqual("literal", float_declaration.initializer.kind)
        changed_float = dataclasses.replace(
            float_declaration,
            initializer=dataclasses.replace(
                float_declaration.initializer,
                literal=str(float(float_declaration.initializer.literal_value) + 0.25),
                literal_value=float(float_declaration.initializer.literal_value) + 0.25))
        forgeries["const-float-drift"] = dataclasses.replace(
            program, declarations=tuple(
                changed_float if item is float_declaration else item
                for item in program.declarations))

    forgeries["read-id"] = replace_first_expression(
        program, read_predicate,
        lambda value: dataclasses.replace(
            value, symbol_id=declaration.symbol.id + 10000), "read-id")
    forgeries["read-span"] = replace_first_expression(
        program, read_predicate,
        lambda value: dataclasses.replace(
            value, span=dataclasses.replace(
                value.span, end_column=value.span.end_column + 1)), "read-span")

    owner_index = None
    def contains_read(statement):
        def expression(value):
            return read_predicate(value) or any(expression(child)
                                                for child in value.children)
        return (any(expression(item) for item in statement.expressions)
                or any(contains_read(child) for child in statement.children))
    for index, function in enumerate(program.functions):
        if any(contains_read(item) for item in function.body):
            owner_index = index
            break
    testcase.assertIsNotNone(owner_index)
    owner = program.functions[owner_index]

    def insert_owner_statement(statement, *, extra_functions=()):
        functions = list(program.functions)
        body = list(owner.body)
        insertion = len(body)
        if body and body[-1].kind == "return":
            insertion -= 1
        body.insert(insertion, statement)
        functions[owner_index] = dataclasses.replace(owner, body=tuple(body))
        functions.extend(extra_functions)
        return dataclasses.replace(program, functions=tuple(functions))

    global_lvalue = TypedExpression(
        "id", INT, initializer.span, "lvalue",
        symbol_id=declaration.symbol.id, symbol=declaration.symbol)
    assignment = TypedExpression(
        "assign", INT, initializer.span, "rvalue",
        children=(global_lvalue, initializer), operator="=")
    testcase.assertEqual(("assign", "=", declaration.symbol.id), (
        assignment.kind, assignment.operator, assignment.children[0].symbol_id))
    forgeries["write"] = insert_owner_statement(
        TypedStatement("expr", initializer.span, (assignment,)))

    update = TypedExpression(
        "post", INT, initializer.span, "rvalue",
        children=(global_lvalue,), operator="++")
    testcase.assertEqual(("post", "++", declaration.symbol.id), (
        update.kind, update.operator, update.children[0].symbol_id))
    forgeries["update"] = insert_owner_statement(
        TypedStatement("expr", initializer.span, (update,)))

    all_signature_ids = [function.signature.id for function in program.functions]
    escape_signature_id = max(all_signature_ids) + 10000
    escape_parameter = Symbol(
        declaration.symbol.id + 20000, "escaped", INT, "parameter",
        owner.span, True)
    escape_signature = FunctionSignature(
        escape_signature_id, "task23Escape", VOID, (escape_parameter,), (),
        owner.span)
    escape_function = TypedFunction(escape_signature, owner.span, ())
    escape_argument = dataclasses.replace(
        global_lvalue, category="readonly lvalue")
    escape_call = TypedExpression(
        "call", VOID, initializer.span, "rvalue", children=(escape_argument,),
        signature_id=escape_signature_id, callee=escape_signature.name)
    testcase.assertEqual(
        (escape_signature_id, 1, INT, True, declaration.symbol.id),
        (escape_call.signature_id, len(escape_signature.parameters),
         escape_signature.parameters[0].type,
         escape_signature.parameters[0].writable,
         escape_call.children[0].symbol_id))
    forgeries["escape"] = insert_owner_statement(
        TypedStatement("expr", initializer.span, (escape_call,)),
        extra_functions=(escape_function,))

    owner_functions = list(program.functions)
    owner_functions[owner_index] = dataclasses.replace(
        owner, signature=dataclasses.replace(
            owner.signature, name=owner.name + "_forged"))
    forgeries["read-owner"] = dataclasses.replace(
        program, functions=tuple(owner_functions))

    shadow_symbol = Symbol(
        declaration.symbol.id + 30000, global_name, INT, "local",
        owner.span, True)
    shadow_declaration = TypedExpression(
        "declaration", INT, owner.span, "rvalue",
        symbol_id=shadow_symbol.id, symbol=shadow_symbol,
        children=(initializer,))
    testcase.assertEqual((global_name, INT, "local", True, "rvalue",
                          initializer.type), (
        shadow_declaration.symbol.name, shadow_declaration.type,
        shadow_declaration.symbol.storage, shadow_declaration.symbol.writable,
        shadow_declaration.category,
        shadow_declaration.children[0].type))
    forgeries["shadow"] = insert_owner_statement(
        TypedStatement("decl", owner.span, (shadow_declaration,)))

    def literalized(value):
        return TypedExpression(
            "literal", INT, value.span, "rvalue",
            literal=str(bound_value), literal_value=bound_value)
    forgeries["literalized-loop-bound"] = map_source_loop_bound(
        program, literalized, "literalized-loop-bound")
    forgeries["wrong-id-loop-bound"] = map_source_loop_bound(
        program, lambda value: dataclasses.replace(
            value, symbol_id=declaration.symbol.id + 10000),
        "wrong-id-loop-bound")

    proof_fields = {
        "proof-bound-kind": ("bound_kind", "literal"),
        "proof-trips": ("trip_count", bound_value + 1),
        "proof-lexical-depth": ("lexical_depth", 4),
        "proof-effective-depth": ("effective_depth", 4),
        "proof-product": ("lexical_product", 4097),
        "proof-charge": ("entrypoint_charge", 4097),
    }
    for label, (field, value) in proof_fields.items():
        forgeries[label] = map_source_loop(
            program,
            lambda statement, field=field, value=value: dataclasses.replace(
                statement, loop_proof=dataclasses.replace(
                    statement.loop_proof, **{field: value})), label)

    return_expressions = ()
    if owner.return_type != VOID:
        def find_return(statement):
            if (statement.kind == "return" and len(statement.expressions) == 1
                    and statement.expressions[0].type == owner.return_type):
                return statement.expressions
            for child in statement.children:
                found = find_return(child)
                if found:
                    return found
            return ()
        for owner_statement in owner.body:
            return_expressions = find_return(owner_statement)
            if return_expressions:
                break
        testcase.assertEqual(1, len(return_expressions))
    def add_return(statement):
        testcase.assertEqual("for", statement.kind)
        testcase.assertEqual(2, len(statement.children))
        body = statement.children[1]
        testcase.assertEqual("block", body.kind)
        changed_body = dataclasses.replace(
            body, children=body.children + (
                TypedStatement("return", body.span, return_expressions),))
        return dataclasses.replace(
            statement, children=(statement.children[0], changed_body))
    forgeries["return-in-loop"] = map_source_loop(
        program, add_return, "return-in-loop")

    def has_source_loop(statement):
        return ((statement.loop_proof is not None
                 and statement.loop_proof.bound_kind
                 == "source-global-const-literal")
                or any(has_source_loop(child) for child in statement.children))
    testcase.assertTrue(any(has_source_loop(item) for item in owner.body))
    recursive_arguments = tuple(TypedExpression(
        "id", parameter.type, parameter.span,
        "lvalue" if parameter.writable else "readonly lvalue",
        symbol_id=parameter.id, symbol=parameter)
        for parameter in owner.parameters)
    recursive_call = TypedExpression(
        "call", owner.return_type, owner.span, "rvalue",
        signature_id=owner.signature.id, callee=owner.name,
        children=recursive_arguments)
    testcase.assertEqual(
        (owner.signature.id, tuple(parameter.type for parameter in owner.parameters)),
        (recursive_call.signature_id,
         tuple(argument.type for argument in recursive_call.children)))
    recursive_statement = TypedStatement(
        "expr" if owner.return_type == VOID else "return", owner.span,
        (recursive_call,))
    forgeries["recursion"] = insert_owner_statement(recursive_statement)
    required = {
        "wrong-key", "raw-source", "normalized-source", "define",
        "declaration-name", "declaration-id", "declaration-storage",
        "declaration-type", "declaration-writable", "literal-spelling",
        "literal-value", "initializer-zero", "initializer-signed",
        "initializer-suffix", "initializer-hex", "initializer-octal",
        "initializer-unary", "initializer-binary", "initializer-cast",
        "initializer-constructor", "initializer-id", "missing-global",
        "extra-global", "dependent-global", "shadow", "write", "update",
        "escape", "read-owner", "read-id", "read-span",
        "literalized-loop-bound", "wrong-id-loop-bound", "proof-bound-kind",
        "proof-trips", "proof-lexical-depth", "proof-effective-depth",
        "proof-product", "proof-charge", "return-in-loop", "recursion",
    }
    if float_globals:
        required.add("const-float-drift")
    testcase.assertEqual(required, set(forgeries))
    return forgeries


class SemanticTests(unittest.TestCase):
    def test_task23_literal_source_global_int_profiles_attach_exact_counted_loop_proofs(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        expected = {
            "filter/bloom:ntapGather": ("MAX_TAPS", 8, 64, (64,), 1, 64, 64, {}),
            "filter/directionalBlur:directionalBlur": ("N", 6, 32, (32,), 1, 32, 32, {}),
            "filter/spinBlur:spinBlur": ("N", 9, 32, (32,), 1, 32, 32, {}),
            "filter/strokes:stkSmear": ("MAX_TAPS", 8, 24, (3, 3, 24), 2, 24, 72, {"MODE": 0}),
            "filter/vaseline:upsample": ("TAP_COUNT", 8, 32, (32,), 1, 32, 32, {}),
            "filter/wind:wind": ("MAX_STEPS", 8, 128, (128,), 1, 128, 128, {"METHOD": 1}),
        }
        root = _corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())

        def loop_proofs(functions):
            result = []
            def visit(statement):
                if statement.loop_proof is not None:
                    result.append(statement.loop_proof)
                for child in statement.children:
                    visit(child)
            for function in functions:
                for statement in function.body:
                    visit(statement)
            return tuple(result)

        for key, facts in expected.items():
            name, symbol_id, value, trips, depth, product, charge, defines = facts
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            typed = analyze_program(
                parse_program(raw, key, defines), key,
                source_global_literal_int_profile="source-global-literal-int-v1")
            declaration = next(item for item in typed.declarations
                               if item.symbol.name == name)
            proofs = loop_proofs(typed.functions)
            with self.subTest(key=key):
                self.assertEqual((symbol_id, "const", "int", False, value), (
                    declaration.symbol.id, declaration.symbol.storage,
                    declaration.type.display(), declaration.symbol.writable,
                    declaration.initializer.literal_value))
                self.assertEqual(trips, tuple(item.trip_count for item in proofs))
                self.assertTrue(all(item.bound_kind == "source-global-const-literal"
                                    for item in proofs if item.trip_count not in (3,)))
                self.assertEqual((len(trips), 0, depth, product, charge, True), (
                    typed.counted_loop_proof.loop_count,
                    typed.counted_loop_proof.unproved_loop_count,
                    typed.counted_loop_proof.max_effective_depth,
                    typed.counted_loop_proof.max_lexical_product,
                    typed.counted_loop_proof.entrypoint_charge,
                    typed.counted_loop_proof.call_graph_acyclic))

    def test_task23_literal_int_four_modes_and_literal_matrix_fail_closed(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.loop_proof import (
            attach_counted_loop_proofs, clear_counted_loop_proofs,
            summarize_counted_loop_proofs,
            validate_source_global_literal_int_program)
        from tools.glslcpp.frontend.semantic import analyze_program

        profile = "source-global-literal-int-v1"
        root = _corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        key = "filter/strokes:stkSmear"
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == key)
        raw = (root / entry["source"]).read_text()
        post = analyze_program(parse_program(raw, key, {"MODE": 0}), key,
                               source_global_literal_int_profile=profile)
        canonical_pre_functions = attach_counted_loop_proofs(post.functions, key)
        canonical_pre = dataclasses.replace(
            post, functions=canonical_pre_functions,
            counted_loop_proof=summarize_counted_loop_proofs(
                canonical_pre_functions))
        cleared_functions = clear_counted_loop_proofs(post.functions)
        cleared_summary = summarize_counted_loop_proofs(cleared_functions)
        self.assertEqual(
            "dc58c8e53799e41f8ab4c9263af336b37540ee58b1418cac6d3734e878bc7bc6",
            hashlib.sha256(repr(cleared_functions).encode()).hexdigest())
        self.assertEqual((0, 3), (
            cleared_summary.loop_count, cleared_summary.unproved_loop_count))
        self.assertEqual(
            "5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9",
            hashlib.sha256(repr(canonical_pre_functions).encode()).hexdigest())
        self.assertEqual((2, 1, 24), (
            canonical_pre.counted_loop_proof.loop_count,
            canonical_pre.counted_loop_proof.unproved_loop_count,
            canonical_pre.counted_loop_proof.entrypoint_charge))
        self.assertEqual((3, 0, 72), (
            post.counted_loop_proof.loop_count,
            post.counted_loop_proof.unproved_loop_count,
            post.counted_loop_proof.entrypoint_charge))
        validate_source_global_literal_int_program(post, profile)
        for candidate, carrier in (
                (canonical_pre, None), (canonical_pre, profile),
                (post, None), (post, "wrong"),
                (dataclasses.replace(post, functions=cleared_functions), profile)):
            with self.subTest(carrier=carrier, pre=candidate is canonical_pre), self.assertRaises(
                    ValueError):
                validate_source_global_literal_int_program(candidate, carrier)

        bloom_key = "filter/bloom:ntapGather"
        bloom_entry = next(item for item in manifest["programs"]
                           if item["program_key"] == bloom_key)
        bloom_raw = (root / bloom_entry["source"]).read_text()
        mutations = {
            "zero": "const int MAX_TAPS = 0;",
            "negative": "const int MAX_TAPS = -64;",
            "hex": "const int MAX_TAPS = 0x40;",
            "unary": "const int MAX_TAPS = +64;",
            "binary": "const int MAX_TAPS = 32 + 32;",
            "cast": "const int MAX_TAPS = int(64);",
            "identifier": "const int BASE_TAPS = 64;\nconst int MAX_TAPS = BASE_TAPS;",
            "type": "const uint MAX_TAPS = 64u;",
            "mutable": "int MAX_TAPS = 64;",
            "renamed": "const int OTHER_TAPS = 64;",
            "extra": "const int MAX_TAPS = 64;\nconst int EXTRA = 1;",
        }
        original = "const int MAX_TAPS = 64;"
        for name, replacement in mutations.items():
            candidate = bloom_raw.replace(original, replacement, 1)
            with self.subTest(literal_mutation=name), self.assertRaises(
                    SemanticError):
                analyze_program(parse_program(candidate, bloom_key, {}), bloom_key,
                                source_global_literal_int_profile=profile)

        ordinary = analyze_program(parse_program(
            "out vec4 fragColor; void main(){ fragColor=vec4(1.0); }",
            "fixture/foreign"), "fixture/foreign")
        self.assertEqual(0, ordinary.counted_loop_proof.loop_count)
        with self.assertRaisesRegex(SemanticError, "E_SOURCE_GLOBAL_LITERAL_INT"):
            analyze_program(parse_program(
                "out vec4 fragColor; void main(){ fragColor=vec4(1.0); }",
                "fixture/foreign"), "fixture/foreign",
                source_global_literal_int_profile=profile)

    def test_task23_six_key_forgery_and_four_mode_matrix_is_closed(self) -> None:
        import dataclasses
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.loop_proof import (
            attach_counted_loop_proofs, clear_counted_loop_proofs,
            summarize_counted_loop_proofs,
            validate_source_global_literal_int_program)
        from tools.glslcpp.frontend.semantic import analyze_program

        profile = "source-global-literal-int-v1"
        profiles = {
            "filter/bloom:ntapGather": ({}, "MAX_TAPS"),
            "filter/directionalBlur:directionalBlur": ({}, "N"),
            "filter/spinBlur:spinBlur": ({}, "N"),
            "filter/strokes:stkSmear": ({"MODE": 0}, "MAX_TAPS"),
            "filter/vaseline:upsample": ({}, "TAP_COUNT"),
            "filter/wind:wind": ({"METHOD": 1}, "MAX_STEPS"),
        }
        root = _corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())

        def replace_first_loop(functions, update):
            replaced = 0
            def statement(value):
                nonlocal replaced
                proof = value.loop_proof
                if proof is not None and replaced == 0:
                    proof = update(proof)
                    replaced += 1
                return dataclasses.replace(
                    value, loop_proof=proof,
                    children=tuple(statement(child) for child in value.children))
            result = tuple(dataclasses.replace(
                function, body=tuple(statement(item) for item in function.body))
                for function in functions)
            self.assertEqual(1, replaced)
            return result

        def replace_first_read(program, symbol_id):
            replaced = 0
            def expression(value):
                nonlocal replaced
                changed = value
                if (value.kind == "id" and value.symbol_id == symbol_id
                        and replaced == 0):
                    changed = dataclasses.replace(value, symbol_id=symbol_id + 10000)
                    replaced += 1
                return dataclasses.replace(
                    changed,
                    children=tuple(expression(child) for child in changed.children))
            def statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(expression(item) for item in value.expressions),
                    children=tuple(statement(child) for child in value.children))
            functions = tuple(dataclasses.replace(
                function, body=tuple(statement(item) for item in function.body))
                for function in program.functions)
            self.assertEqual(1, replaced)
            return dataclasses.replace(program, functions=functions)

        for key, (defines, global_name) in profiles.items():
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            post = analyze_program(
                parse_program(raw, key, defines), key,
                source_global_literal_int_profile=profile)
            pre_functions = attach_counted_loop_proofs(post.functions, key)
            pre = dataclasses.replace(
                post, functions=pre_functions,
                counted_loop_proof=summarize_counted_loop_proofs(pre_functions))
            cleared_functions = clear_counted_loop_proofs(post.functions)
            cleared = dataclasses.replace(
                post, functions=cleared_functions,
                counted_loop_proof=summarize_counted_loop_proofs(cleared_functions))
            forged_functions = replace_first_loop(
                post.functions,
                lambda proof: dataclasses.replace(
                    proof, trip_count=proof.trip_count + 1))
            forged = dataclasses.replace(
                post, functions=forged_functions,
                counted_loop_proof=dataclasses.replace(
                    post.counted_loop_proof,
                    entrypoint_charge=post.counted_loop_proof.entrypoint_charge + 1))

            validate_source_global_literal_int_program(post, profile)
            rejected_modes = (
                ("pre-absent", pre, None),
                ("pre-exact", pre, profile),
                ("post-absent", post, None),
                ("post-wrong", post, "wrong"),
                ("cleared-exact", cleared, profile),
                ("forged-post-exact", forged, profile),
            )
            for mode, candidate, carrier in rejected_modes:
                with self.subTest(key=key, mode=mode), self.assertRaises(ValueError):
                    validate_source_global_literal_int_program(candidate, carrier)

            forgeries = _task23_complete_ir_forgery_matrix(
                self, post, global_name)
            forgeries["submitted-callgraph-summary"] = dataclasses.replace(
                post, counted_loop_proof=dataclasses.replace(
                    post.counted_loop_proof, call_graph_acyclic=False))
            for name, candidate in forgeries.items():
                with self.subTest(key=key, forgery=name), self.assertRaises(ValueError):
                    validate_source_global_literal_int_program(candidate, profile)

    def test_refract_post_transform_retains_exact_fixed_array_input_parameter_proof(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
            attach_fixed_array_in_parameter_proof,
        )
        from tools.glslcpp.frontend.refract_compatibility import (
            apply_refract_truthy_vector_noops,
        )
        from tools.glslcpp.frontend.semantic import analyze_program

        root = _corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "classicNoisedeck/refract:refract")
        raw = (root / entry["source"]).read_text()
        analyzed = analyze_program(parse_program(raw, entry["program_key"], {}),
                                   entry["program_key"])
        self.assertIsNone(analyzed.fixed_array_in_parameter_proof)
        typed = attach_fixed_array_in_parameter_proof(
            apply_refract_truthy_vector_noops(analyzed))
        proof = typed.fixed_array_in_parameter_proof
        self.assertIsNotNone(proof)
        self.assertEqual("fixed-array-in-parameter-v1", proof.proof_kind)
        self.assertEqual("refract-fixed-array-in-parameter-v1", proof.source_profile)
        self.assertEqual(entry["raw_sha256"], proof.raw_source_sha256)
        self.assertEqual(
            "bff1818ad5db7e637a01d6f10476cebba8ac04d6ffdf467d02508fa23671757e",
            proof.normalized_source_sha256)
        self.assertEqual(
            "b404a801dea1ba438da7bad20d7cae059d0aa7f25c76610221ca07546fdfe2f6",
            proof.canonical_factory_sha256)
        self.assertEqual((), proof.define_contract)
        self.assertEqual(11, len(proof.binding_signature))
        self.assertEqual((2, 3, 7, 15),
                         tuple(item.blend_mode for item in proof.compatibility_sites))
        self.assertEqual((0.0, 1.0, 1.0, 1.0),
                         tuple(item.equality_constant for item in proof.compatibility_sites))
        self.assertEqual(("max", "min", "min", "min"),
                         tuple(item.false_builtin for item in proof.compatibility_sites))
        self.assertTrue(all(item.target_symbol_id == 47
                            and item.source_symbol_id in (33, 34)
                            for item in proof.compatibility_sites))
        self.assertEqual(("Kernel9", "Offsets9", "const Kernel9&"),
                         (proof.kernel_alias, proof.offsets_alias,
                          proof.parameter.native_abi))
        self.assertEqual((38, 1, 19, "kernel", "float[9]", "float", 9, "in"),
                         (proof.parameter.owner_signature_id,
                          proof.parameter.parameter_ordinal,
                          proof.parameter.symbol_id,
                          proof.parameter.symbol_name,
                          proof.parameter.array_type,
                          proof.parameter.element_type,
                          proof.parameter.extent,
                          proof.parameter.direction))
        self.assertEqual(2, proof.parameter.reads_per_iteration)
        self.assertEqual((39, 40),
                         tuple(item.owner_signature_id for item in proof.caller_tables))
        self.assertEqual((57, 60),
                         tuple(item.symbol_id for item in proof.caller_tables))
        self.assertEqual(("deriv_x", "deriv_y"),
                         tuple(item.symbol_name for item in proof.caller_tables))
        self.assertEqual(((0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0),
                          (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0)),
                         tuple(item.number_values for item in proof.caller_tables))
        self.assertTrue(all(item.literal_indices == tuple(range(9))
                            and item.literal_store_statement_indices == tuple(range(2, 11))
                            and item.declaration_statement_index == 1
                            and item.native_alias == "Kernel9"
                            for item in proof.caller_tables))
        self.assertEqual((38, 51, "offset", "vec2[9]", "vec2", 9,
                          "Offsets9", 2, tuple(range(3, 12))),
                         (proof.offset_table.owner_signature_id,
                          proof.offset_table.symbol_id,
                          proof.offset_table.symbol_name,
                          proof.offset_table.array_type,
                          proof.offset_table.element_type,
                          proof.offset_table.extent,
                          proof.offset_table.native_alias,
                          proof.offset_table.declaration_statement_index,
                          proof.offset_table.literal_store_statement_indices))
        self.assertIsNone(proof.offset_table.number_values)
        self.assertEqual((54, 9, 9, 18, 42),
                         (proof.induction_symbol_id, proof.loop_trip_count,
                          proof.lexical_product, proof.entrypoint_charge,
                          proof.main_signature_id))
        self.assertEqual((1, 3, 35, 32, 27, 3, 30, 2, 2),
                         (proof.array_parameter_count,
                          proof.array_declaration_count,
                          proof.array_typed_expression_count,
                          proof.array_identifier_reference_count,
                          proof.literal_store_count,
                          proof.induction_read_count,
                          proof.index_expression_count,
                          proof.whole_array_argument_count,
                          proof.array_call_count))
        self.assertTrue(proof.no_alias_copy_escape_return_or_post_call_use)
        self.assertTrue(proof.complete_initialization_dominates_reads)
        self.assertTrue(proof.caller_tables_never_simultaneously_live)
        self.assertTrue(proof.parameter_read_only_and_synchronous)
        self.assertTrue(proof.mode_zero_array_free)
        self.assertEqual(144, proof.raw_simultaneous_payload_bytes)
        self.assertEqual(
            "36d7815ce5aa9efedf3144e199ae7b49dc5819c751475b815708424269033229",
            proof.interface_sha256)
        self.assertEqual(
            "4c9e125cd4dda55f2688c362a5ab7e81acf1b08c9e284bc5c25e04da39020188",
            proof.typed_ir_sha256)
        self.assertEqual(
            "93329ab73d54ff1eb3b8ec43da8570365d58de8caaa1a36252ef1ad30a709de2",
            proof.whole_program_sha256)

    def test_cellrefract_convolve_fixed_array_input_parameter_record_is_frozen(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
            attach_fixed_array_in_parameter_proof,
        )
        from tools.glslcpp.frontend.semantic import analyze_program

        def span(value) -> str:
            return (f"{value.start_line}:{value.start_column}"
                    f"-{value.end_line}:{value.end_column}")

        root = _corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "classicNoisedeck/cellRefract:cellRefract")
        raw = (root / entry["source"]).read_text()
        analyzed = analyze_program(
            parse_program(raw, entry["program_key"], {"KERNEL": 0, "SHAPE": 1}),
            entry["program_key"])
        self.assertIsNone(analyzed.fixed_array_in_parameter_proof)
        typed = attach_fixed_array_in_parameter_proof(analyzed)
        proof = typed.fixed_array_in_parameter_proof
        self.assertIsNotNone(proof)
        self.assertEqual("fixed-array-in-parameter-v1", proof.proof_kind)
        self.assertEqual("cellrefract-convolve-v1", proof.source_profile)
        self.assertEqual(entry["raw_sha256"], proof.raw_source_sha256)
        self.assertEqual(
            "31cce61e01275d44d46556bfc13edeea4383dcfbcfde024fd7c54a624933bd3c",
            proof.normalized_source_sha256)
        self.assertEqual(
            "329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3",
            proof.canonical_factory_sha256)
        self.assertEqual(
            ("KERNEL", "int", "0", "SHAPE", "int", "1"),
            tuple(item for define in proof.define_contract
                  for item in (define.name, define.kind, define.canonical_value)))
        self.assertEqual(15, len(proof.binding_signature))
        self.assertEqual(("inputTex:sampler2D", "time:float", "seed:int",
                          "resolution:vec2", "tileOffset:vec2",
                          "fullResolution:vec2", "scale:float", "cellScale:float",
                          "cellSmooth:float", "variation:float", "speed:float",
                          "refractAmt:float", "direction:float", "wrap:int",
                          "effectWidth:float"), proof.binding_signature)
        self.assertEqual((), proof.compatibility_sites)
        self.assertEqual(("Kernel9", "Offsets9", "const Kernel9&"),
                         (proof.kernel_alias, proof.offsets_alias,
                          proof.parameter.native_abi))
        self.assertEqual("82:5-91:6", span(proof.convolve_loop_span))
        self.assertEqual((104, 9, 9, 30, 71),
                         (proof.induction_symbol_id, proof.loop_trip_count,
                          proof.lexical_product, proof.entrypoint_charge,
                          proof.main_signature_id))
        parameter = proof.parameter
        self.assertEqual((66, 1, 23, "kernel", "float[9]", "float", 9, "in"),
                         (parameter.owner_signature_id, parameter.parameter_ordinal,
                          parameter.symbol_id, parameter.symbol_name,
                          parameter.array_type, parameter.element_type,
                          parameter.extent, parameter.direction))
        self.assertEqual("66:29-66:44", span(next(
            item.span for function in typed.functions
            if function.signature.id == 66 and function.body
            for item in function.parameters if item.id == 23)))
        self.assertEqual(2, parameter.reads_per_iteration)
        self.assertEqual(("87:25-87:34", "90:25-90:34"),
                         tuple(span(item) for item in parameter.induction_read_spans))
        self.assertEqual(("203:12-203:46", "204:12-204:46", "223:12-223:45",
                          "224:12-224:45", "242:11-242:44", "243:11-243:44",
                          "269:15-269:48", "270:15-270:48"),
                         tuple(span(item) for item in parameter.direct_call_spans))
        self.assertEqual(("203:30-203:37", "204:30-204:37", "223:30-223:37",
                          "224:30-224:37", "242:29-242:36", "243:29-243:36",
                          "269:33-269:40", "270:33-270:40"),
                         tuple(span(item) for item in parameter.direct_argument_spans))
        tables = proof.caller_tables
        self.assertEqual(8, len(tables))
        self.assertEqual((67, 67, 84, 84, 81, 81, 73, 73),
                         tuple(item.owner_signature_id for item in tables))
        self.assertEqual((107, 108, 162, 163, 152, 153, 131, 132),
                         tuple(item.symbol_id for item in tables))
        self.assertEqual(("deriv_x", "deriv_y") + ("sobel_x", "sobel_y") * 3,
                         tuple(item.symbol_name for item in tables))
        self.assertEqual(((1, 2, 11), (11, 12, 21), (1, 2, 11),
                          (11, 12, 21), (0, 1, 10), (10, 11, 20),
                          (1, 2, 11), (11, 12, 21)),
                         tuple((item.declaration_statement_index,
                                item.literal_store_statement_indices[0],
                                item.literal_store_statement_indices[-1] + 1)
                               for item in tables))
        sobel_x = (1.0, 0.0, -1.0, 2.0, 0.0, -2.0, 1.0, 0.0, -1.0)
        sobel_y = (1.0, 2.0, 1.0, 0.0, 0.0, 0.0, -1.0, -2.0, -1.0)
        self.assertEqual(((0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0),
                          (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0),
                          sobel_x, sobel_y, sobel_x, sobel_y, sobel_x, sobel_y),
                         tuple(item.number_values for item in tables))
        self.assertTrue(all(item.array_type == "float[9]"
                            and item.element_type == "float" and item.extent == 9
                            and item.native_alias == "Kernel9"
                            and item.literal_indices == tuple(range(9))
                            and item.induction_read_spans == ()
                            and len(item.literal_store_spans) == 9
                            and len(item.literal_index_spans) == 9
                            for item in tables))
        self.assertEqual(("193:8-193:18", "198:8-198:18", "213:8-213:18",
                          "218:8-218:18", "230:8-230:18", "235:8-235:18",
                          "259:11-259:21", "264:11-264:21"),
                         tuple(span(item.declaration_span) for item in tables))
        offset = proof.offset_table
        self.assertEqual((66, 101, "offset", "vec2[9]", "vec2", 9, "Offsets9",
                          1, tuple(range(2, 11))),
                         (offset.owner_signature_id, offset.symbol_id,
                          offset.symbol_name, offset.array_type,
                          offset.element_type, offset.extent, offset.native_alias,
                          offset.declaration_statement_index,
                          offset.literal_store_statement_indices))
        self.assertEqual("68:10-68:19", span(offset.declaration_span))
        self.assertIsNone(offset.number_values)
        self.assertEqual(("84:50-84:59",),
                         tuple(span(item) for item in offset.induction_read_spans))
        self.assertEqual((1, 9, 146, 137, 126, 3, 129, 8, 8),
                         (proof.array_parameter_count,
                          proof.array_declaration_count,
                          proof.array_typed_expression_count,
                          proof.array_identifier_reference_count,
                          proof.literal_store_count, proof.induction_read_count,
                          proof.index_expression_count,
                          proof.whole_array_argument_count,
                          proof.array_call_count))
        self.assertTrue(proof.no_alias_copy_escape_return_or_post_call_use)
        self.assertTrue(proof.complete_initialization_dominates_reads)
        self.assertTrue(proof.parameter_read_only_and_synchronous)
        # Derived, not transcribed: within every caller the second table is
        # fully initialized before the first table's consuming convolve call
        # (derivatives 199-201 precede 203), so the pairs DO coexist.
        self.assertFalse(proof.caller_tables_never_simultaneously_live)
        self.assertFalse(proof.mode_zero_array_free)
        self.assertEqual(144, proof.raw_simultaneous_payload_bytes)
        self.assertEqual(
            "09c626e4a6923f856dac399e76972de809ccc8efeb3d49c59d5f69eb8ed17352",
            proof.interface_sha256)
        self.assertEqual(
            "e7e3fd532c4fcc8116655ca64d2b73e6c0905d221cc485014315d29b22b27a6b",
            proof.typed_ir_sha256)
        self.assertEqual(
            "144e3e4c035bf5af4102d3bfed99afabe2f403b8a6c2c2794802adb0ca51d40b",
            proof.whole_program_sha256)
        # The unreachability witness: `convolutionKernel` collapsed to
        # `return color;` by the frozen KERNEL=0 define, and main invokes no
        # array caller (the frozen fact this span + empty tuple record).
        self.assertEqual("280:5-280:18", span(proof.mode_one_span))
        self.assertEqual((), proof.main_derivative_call_spans)
        # Caller-table records align positionally with the whole-array
        # argument spans the validator zips against them.
        def walk(value):
            yield value
            for child in value.children:
                yield from walk(child)

        def walk_statement(statement):
            yield statement
            for expression in statement.expressions:
                yield from walk(expression)
            for child in statement.children:
                yield from walk_statement(child)

        for table, argument_span, call_span in zip(
                tables, parameter.direct_argument_spans,
                parameter.direct_call_spans):
            call = next(value for function in typed.functions if function.body
                        for statement in function.body
                        for value in walk_statement(statement)
                        if value.kind == "call" and value.callee == "convolve"
                        and value.span == call_span)
            self.assertEqual(table.symbol_id, call.children[1].symbol_id)
            self.assertEqual(argument_span, call.children[1].span)

    def test_fixed_grid_counter_store_programs_retain_exact_structural_proof(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = _corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        expected = {
            "filter/celShading:celShadingEdges": {
                "profile": "cel-shading-edges-3x3-v1",
                "body_count": 13,
                "array_index": 5,
                "counter_index": 6,
                "loop_index": 7,
                "inner_count": 5,
                "rhs": "cel-wrapped-fetch-luminosity-v1",
            },
            "filter/outline:outlineSobel": {
                "profile": "outline-sobel-3x3-v1",
                "body_count": 14,
                "array_index": 6,
                "counter_index": 7,
                "loop_index": 8,
                "inner_count": 4,
                "rhs": "outline-wrapped-fetch-red-v1",
            },
        }
        for key, facts in expected.items():
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            typed = analyze_program(parse_program(raw, key, {}), key)
            with self.subTest(key=key):
                proof = typed.fixed_grid_counter_store_proof
                self.assertIsNotNone(proof)
                self.assertEqual("fixed-grid-counter-store-v1", proof.proof_kind)
                self.assertEqual(facts["profile"], proof.source_profile)
                self.assertEqual(facts["body_count"], proof.main_body_statement_count)
                self.assertEqual(2, proof.early_return_statement_index)
                self.assertEqual(facts["array_index"], proof.array_declaration_statement_index)
                self.assertEqual(facts["counter_index"], proof.counter_declaration_statement_index)
                self.assertEqual(facts["loop_index"], proof.outer_loop_statement_index)
                self.assertEqual(facts["inner_count"], proof.inner_body_statement_count)
                self.assertEqual(facts["rhs"], proof.store_rhs_profile)
                self.assertEqual((0, 8, 9, 9),
                                 (proof.store_lower_bound, proof.store_upper_bound,
                                  proof.store_count, proof.counter_final_value))
                self.assertEqual(12, proof.literal_read_count)
                self.assertEqual((0, 1, 2, 3, 5, 6, 7, 8),
                                 proof.literal_read_unique_indices)
                self.assertEqual(((0, 2), (1, 1), (2, 2), (3, 1),
                                  (5, 1), (6, 2), (7, 1), (8, 2)),
                                 proof.literal_read_occurrence_counts)
                self.assertEqual((1, 13, 14, 13, 1, 2),
                                 (proof.array_declaration_count,
                                  proof.array_reference_count,
                                  proof.array_typed_expression_count,
                                  proof.index_expression_count,
                                  proof.counter_declaration_count,
                                  proof.counter_reference_count))
                self.assertEqual((3, 9, 12, 72),
                                 (proof.per_loop_trip_count,
                                  proof.lexical_product,
                                  proof.entrypoint_charge,
                                  proof.raw_payload_bytes))
                self.assertEqual("unary", proof.loop_update_expression_kind)
                self.assertEqual("post", proof.counter_update_source_kind)
                self.assertTrue(proof.counter_update_value_discarded)
                self.assertTrue(proof.store_precedes_update)
                self.assertTrue(proof.dominates_array)
                self.assertTrue(proof.dominates_fetch)
                self.assertTrue(proof.dominates_grid)
                self.assertTrue(proof.dominates_store)
                self.assertTrue(proof.dominates_counter_update)
                self.assertTrue(proof.no_array_initializer)
                self.assertTrue(proof.no_copy_alias_escape_or_abi_use)
                self.assertTrue(proof.no_alternate_array_write)
                self.assertTrue(proof.no_alternate_counter_use)
                self.assertTrue(proof.no_dynamic_read)
                self.assertTrue(proof.no_index_after_grid)
                self.assertEqual(64, len(proof.typed_ir_sha256))
                self.assertEqual(64, len(proof.whole_program_sha256))

    def test_fixed_nine_programs_retain_raw_source_defines_and_structural_proof(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = _corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        expected = {
            "filter/sharpen:sharpen": (("kernel", "offsets"), 144),
            "filter/sobel:sobel": (("sobel_x", "sobel_y", "offsets"), 216),
        }
        for key, (roles, payload_bytes) in expected.items():
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            with self.subTest(key=key):
                typed = analyze_program(parse_program(raw, key, {}), key)
                self.assertEqual(raw, typed.raw_source)
                self.assertEqual((), typed.preprocessor_defines)
                proof = typed.fixed_nine_table_proof
                self.assertIsNotNone(proof)
                self.assertEqual("fixed-nine-local-literal-init-counted-read-v1",
                                 proof.proof_kind)
                self.assertEqual(roles, tuple(item.role for item in proof.arrays))
                self.assertTrue(all(item.extent == 9 for item in proof.arrays))
                self.assertTrue(all(item.literal_store_indices == tuple(range(9))
                                    for item in proof.arrays))
                self.assertEqual(9, proof.trip_count)
                self.assertEqual(payload_bytes, proof.raw_payload_bytes)

    def test_preprocessor_define_provenance_is_sorted_typed_and_immutable(self) -> None:
        from tools.glslcpp.frontend import FrontendError, parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = "out vec4 fragColor; void main(){fragColor=vec4(1.0);}"
        caller_defines = {"Z": 1, "A": True, "N": -0.0, "S": "value"}
        typed = analyze_program(parse_program(source, "defines", caller_defines), "defines")
        caller_defines["Z"] = 99
        self.assertEqual(
            (("A", "bool", "true"), ("N", "float", "-0x0.0p+0"),
             ("S", "str", "value"), ("Z", "int", "1")),
            tuple((item.name, item.kind, item.canonical_value)
                  for item in typed.preprocessor_defines))
        self.assertNotEqual(
            analyze_program(parse_program(source, "defines", {"A": True}), "defines").preprocessor_defines,
            analyze_program(parse_program(source, "defines", {"A": 1}), "defines").preprocessor_defines)
        for invalid in ({1: "value"}, {"A": float("nan")},
                        {"A": float("inf")}, {"A": object()}):
            with self.subTest(invalid=repr(invalid)), self.assertRaises(FrontendError):
                parse_program(source, "defines", invalid)

    def test_compute_rank_carries_exact_discarded_local_counter_proof(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = _corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/pixelSort:computeRank")
        typed = analyze_program(
            parse_program((root / entry["source"]).read_text(), entry["program_key"]),
            entry["program_key"])

        proofs = []
        def walk(statement):
            if statement.counter_proof is not None:
                proofs.append(statement.counter_proof)
            for child in statement.children:
                walk(child)
        main = next(function for function in typed.functions if function.name == "main")
        for statement in main.body:
            walk(statement)

        self.assertEqual(1, len(proofs))
        proof = proofs[0]
        self.assertEqual("discarded-local-counter-statement-v1", proof.proof_kind)
        self.assertEqual("int", proof.target_type)
        self.assertEqual(0, proof.initial_value)
        self.assertEqual("++", proof.update_operator)
        self.assertTrue(proof.value_discarded)
        self.assertEqual(32, proof.containing_loop_trip_count)
        self.assertEqual(1, proof.max_updates_per_visit)
        self.assertEqual((0, 32), (proof.lower_bound, proof.upper_bound))
        self.assertNotEqual(proof.target_symbol_id, proof.induction_symbol_id)
        self.assertEqual(proof.target_symbol_id, proof.initializer_symbol_id)
        self.assertEqual(
            "otherLum>myLum||(otherLum==myLum&&sampleX<x)",
            proof.predicate_profile)
        self.assertEqual(4, proof.loop_body_statement_count)
        self.assertEqual(1, proof.skip_conditional_index)
        self.assertEqual(3, proof.counter_conditional_index)
        self.assertEqual(4, len({proof.sample_x_symbol_id, proof.x_symbol_id,
                                 proof.other_luminance_symbol_id,
                                 proof.own_luminance_symbol_id}))
        self.assertLess(proof.initializer_span.start, proof.statement_span.start)
        self.assertLessEqual(proof.containing_loop_span.start, proof.statement_span.start)

    def test_analyzer_returns_frozen_typed_program_with_spans(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        parsed = parse_program("out vec4 fragColor; void main() { fragColor = vec4(1.0); }", "fixture")
        typed = analyze_program(parsed, "fixture")
        self.assertEqual("fixture", typed.key)
        self.assertTrue(typed.declarations)
        self.assertEqual("vec4", typed.declarations[0].type.display())
        self.assertEqual("fixture", typed.declarations[0].span.program_key)
        with self.assertRaises((AttributeError, TypeError)):
            typed.key = "changed"  # type: ignore[misc]

    def test_parse_wrapper_carries_a_frozen_span_for_every_ast_node(self) -> None:
        from tools.glslcpp.frontend import parse_program

        parsed = parse_program("\nfloat f(float x) { return x + 1.0; }\nvoid main() { f(1.0); }", "spans")
        before = copy.deepcopy(parsed["ast"])
        self.assertGreater(len(parsed["spans"]), 6)
        self.assertEqual("spans", parsed["spans"][0][1].program_key)
        self.assertEqual(before, parsed["ast"])

    def test_span_table_is_bounded_and_distinguishes_repeated_names(self) -> None:
        from tools.glslcpp.frontend import parse_program

        source = "float f(float x) { float y = x; return x + y; } void main() { float y = f(1.0); }"
        parsed = parse_program(source, "repeat")
        table = dict(parsed["spans"])
        first_return = table[("decls", 0, "body", 1)]
        second_local = table[("decls", 1, "body", 0)]
        self.assertEqual("return x + y;", parsed["source"][first_return.start:first_return.end])
        self.assertEqual("float y = f(1.0);", parsed["source"][second_local.start:second_local.end])
        self.assertLess(first_return.end, second_local.start)

    def test_every_parser_mapping_has_a_nonfallback_exact_span(self) -> None:
        from tools.glslcpp.frontend import parse_program

        parsed = parse_program("struct S { vec2 data[2]; }; uniform Settings { vec4 values[3]; } cfg; void main() { for (int i = 0; i < 2; ++i) { vec2 p = cfg.values[i].xy; } }", "ranges")
        paths: list[tuple[object, ...]] = []
        def walk(value, path=()):
            if isinstance(value, dict):
                paths.append(path)
                for key, child in value.items(): walk(child, path + (key,))
            elif isinstance(value, (list, tuple)):
                for index, child in enumerate(value): walk(child, path + (index,))
        walk(parsed["ast"])
        table = dict(parsed["spans"])
        self.assertEqual(set(paths), set(table))
        for path in paths:
            span = table[path]
            self.assertLess(span.start, span.end)
            if path:
                self.assertLess(span.end - span.start, len(parsed["source"]))
        self.assertEqual("vec4 values[3]", parsed["source"][table[("decls", 1, "members", 0)].start:table[("decls", 1, "members", 0)].end])

    def test_pinned_corpus_has_no_missing_or_whole_program_mapping_span(self) -> None:
        from tools.glslcpp.frontend import parse_program
        root = _corpus_root(REPOSITORY)
        programs = json.loads((root / "manifest.json").read_text())["programs"]
        def paths(value, path=()):
            if isinstance(value, dict):
                yield path
                for key, child in value.items(): yield from paths(child, path + (key,))
            elif isinstance(value, (list, tuple)):
                for index, child in enumerate(value): yield from paths(child, path + (index,))
        for record in programs:
            with self.subTest(program=record["program_key"]):
                parsed = parse_program((root / record["source"]).read_text(), record["program_key"])
                table = dict(parsed["spans"])
                for path in paths(parsed["ast"]):
                    self.assertIn(path, table)
                    if path:
                        self.assertLess(table[path].end - table[path].start, len(parsed["source"]))

    def test_declaration_analysis_preserves_parameter_directions_and_body_result(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        typed = analyze_program(parse_program("uniform sampler2D src; out vec4 fragColor; float f(in float x, out vec2 y) { y = vec2(x); return x; } void main() {}", "decl"))
        function = next(item for item in typed.functions if item.name == "f")
        self.assertEqual(("in", "out"), tuple(item.direction for item in function.parameters))
        self.assertEqual(("src",), typed.resources.samplers)
        self.assertEqual("analyzed", typed.body_status)

    def test_struct_uniform_block_and_prototype_definition_are_retained(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        typed = analyze_program(parse_program("struct S { vec2 uv; float weight; }; uniform Settings { vec4 data[2]; } cfg; float f(in float x); float f(in float x) { return x; } void main() {}", "records"))
        self.assertEqual(("S",), tuple(item.name for item in typed.structs))
        self.assertEqual(("uv", "weight"), tuple(item.name for item in typed.structs[0].fields))
        self.assertEqual(("Settings",), tuple(item.block_name for item in typed.uniform_blocks))
        self.assertEqual("cfg", typed.uniform_blocks[0].instance_name)
        occurrences = [item for item in typed.functions if item.name == "f"]
        self.assertEqual(2, len(occurrences))
        self.assertEqual(occurrences[0].signature.id, occurrences[1].signature.id)
        self.assertEqual(1, len(occurrences[0].signature.declaration_spans))
        self.assertIsNotNone(occurrences[0].signature.definition_span)
        self.assertEqual("uniform_block", next(item.symbol.storage for item in typed.declarations if item.symbol.name == "cfg"))
        self.assertNotIn("data", typed.resources.uniforms)

    def test_parameter_and_interface_spans_include_their_leading_tokens(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        parsed = parse_program("layout(std140) uniform Settings { vec4 data[2]; } cfg; float f(inout vec2 value, out float result) { result = value.x; return result; } void main() {}", "leading")
        typed = analyze_program(parsed)
        table = dict(parsed["spans"])
        self.assertTrue(parsed["source"][table[("decls", 0)].start:].startswith("layout"))
        function = next(item for item in typed.functions if item.name == "f")
        self.assertEqual("inout vec2 value", parsed["source"][function.parameters[0].span.start:function.parameters[0].span.end])
        self.assertEqual("out float result", parsed["source"][function.parameters[1].span.start:function.parameters[1].span.end])

    def test_declarations_fail_closed_for_unknown_and_incompatible_redeclarations(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        for source, code in (("mystery x; void main() {}", "E_UNKNOWN_TYPE"),
                             ("float x; int x; void main() {}", "E_DUPLICATE_SYMBOL"),
                             ("float f(float x); int f(float x) { return 0; } void main() {}", "E_INCOMPATIBLE_SIGNATURE"),
                             ("int main() { return 0; }", "E_MAIN_SIGNATURE")):
            with self.subTest(source=source):
                with self.assertRaises(SemanticError) as context:
                    analyze_program(parse_program(source, "bad"))
                self.assertIn(code, str(context.exception))

    def test_semantic_tool_reports_stable_explicit_body_boundary(self) -> None:
        command = [sys.executable, str(REPOSITORY / "tools/glslcpp/check_semantics.py"), "--report"]
        first = subprocess.check_output(command, cwd="/tmp", text=True)
        second = subprocess.check_output(command, cwd="/tmp", text=True)
        self.assertEqual(first, second)
        report = json.loads(first)
        self.assertEqual(212, report["body_success"])
        self.assertEqual("complete", report["body_analysis"])
        self.assertEqual("not attempted", report["emission"])
        self.assertEqual("not attempted", report["compile"])
        self.assertEqual((622, 646), (report["variant_candidates"], report["variant_success"]))
        self.assertEqual(215, report["global_initializer_success"])
        self.assertNotIn(str(REPOSITORY), first)

    def test_all_212_pinned_programs_pass_the_body_checker(self) -> None:
        from tools.glslcpp.check_semantics import declaration_report
        report = declaration_report()
        self.assertEqual(212, report["body_success"])
        self.assertEqual("complete", report["body_analysis"])

    def test_body_analysis_resolves_scope_expression_and_assignment(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        typed = analyze_program(parse_program(
            "out vec4 fragColor; float f(float x) { float y = x + 1.0; return y; } "
            "void main() { float x = f(2.0); fragColor = vec4(x); }", "body"))
        self.assertEqual("analyzed", typed.body_status)
        main = next(item for item in typed.functions if item.name == "main")
        self.assertEqual("decl", main.body[0].kind)
        self.assertEqual("assign", main.body[1].expressions[0].kind)
        self.assertEqual("vec4", main.body[1].expressions[0].type.display())

    def test_body_analysis_rejects_implicit_conversion_and_bad_condition(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        for source, code in (
            ("void main() { float x = 1; }", "E_TYPE"),
            ("void main() { if (1) {} }", "E_CONDITION"),
            ("void main() { float x; x = 1; }", "E_TYPE"),
        ):
            with self.subTest(source=source):
                with self.assertRaises(SemanticError) as context:
                    analyze_program(parse_program(source, "bad-body"))
                self.assertIn(code, str(context.exception))

    def test_typed_expression_retains_emitter_sufficient_operation_data(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        typed = analyze_program(parse_program(
            "out vec4 fragColor; void main() { vec2 p = vec2(1.0, 2.0); p.xy += vec2(3.0); fragColor = vec4(p, 0.0, 1.0); }", "ir"))
        body = next(item for item in typed.functions if item.name == "main").body
        assignment = body[1].expressions[0]
        self.assertEqual("+=", assignment.operator)
        self.assertEqual("swizzle", assignment.children[0].kind)
        self.assertEqual("xy", assignment.children[0].member)
        constructor = body[0].expressions[0].children[0]
        self.assertEqual("construct", constructor.kind)
        self.assertEqual("vec2", constructor.constructor_type.display())
        self.assertEqual("1.0", constructor.children[0].literal)

    def test_calls_out_parameters_and_uniform_writes_are_strict(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        for source, code in (
            ("void f(out float x) {} void main() { f(1.0); }", "E_NO_OVERLOAD"),
            ("uniform float x; void main() { x = 1.0; }", "E_NOT_WRITABLE"),
            ("void main() { vec2 p; p.xx = vec2(1.0); }", "E_NOT_WRITABLE"),
        ):
            with self.subTest(source=source):
                with self.assertRaises(SemanticError) as context:
                    analyze_program(parse_program(source, "strict"))
                self.assertIn(code, str(context.exception))

    def test_global_initializers_are_typed_retained_and_source_ordered(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        typed = analyze_program(parse_program(
            "const float a = 1.0; const vec2 b = vec2(a, 2.0); void main() {}", "globals"))
        declarations = {item.symbol.name: item for item in typed.declarations}
        self.assertEqual("const", declarations["a"].symbol.storage)
        self.assertEqual("literal", declarations["a"].initializer.kind)
        self.assertEqual("construct", declarations["b"].initializer.kind)
        self.assertEqual(declarations["a"].symbol.id, declarations["b"].initializer.children[0].symbol_id)
        self.assertEqual("gl_FragCoord", typed.builtin_symbols[0].name)
        with self.assertRaises(SemanticError) as context:
            analyze_program(parse_program("const float a = b; float b = 1.0; void main() {}", "order"))
        self.assertIn("E_UNKNOWN_SYMBOL", str(context.exception))

    def test_task14_source_const_globals_have_stable_identity_and_are_read_only(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        source = ("const float PI = 3.141592653589793; out vec4 fragColor; "
                  "float helper(float x) { return x + PI; } "
                  "void main() { fragColor = vec4(helper(PI)); }")
        typed = analyze_program(parse_program(source, "task14-const-global"),
                                "task14-const-global")
        declaration = next(item for item in typed.declarations if item.symbol.name == "PI")
        helper = next(item for item in typed.functions if item.name == "helper")
        main = next(item for item in typed.functions if item.name == "main")
        helper_reference = helper.body[0].expressions[0].children[1]
        main_reference = main.body[0].expressions[0].children[1].children[0].children[0]
        self.assertEqual("literal", declaration.initializer.kind)
        self.assertEqual(declaration.symbol.id, helper_reference.symbol_id)
        self.assertEqual(declaration.symbol.id, main_reference.symbol_id)
        self.assertFalse(declaration.symbol.writable)

        writes = {
            "direct": "PI = 1.0;",
            "compound": "PI += 1.0;",
            "prefix": "++PI;",
            "postfix": "PI++;",
        }
        for name, statement in writes.items():
            candidate = ("const float PI = 3.141592653589793; out vec4 fragColor; "
                         f"void main() {{ {statement} fragColor = vec4(PI); }}")
            with self.subTest(name=name), self.assertRaisesRegex(
                    SemanticError, rf"task14-write-{name}:1:\d+: E_NOT_WRITABLE"):
                analyze_program(parse_program(candidate, f"task14-write-{name}"),
                                f"task14-write-{name}")

        for name, candidate in {
            "forward": ("const float TAU = PI * 2.0; const float PI = 3.0; "
                        "out vec4 fragColor; void main(){fragColor=vec4(TAU);}"),
            "cycle": ("const float PI = TAU / 2.0; const float TAU = PI * 2.0; "
                      "out vec4 fragColor; void main(){fragColor=vec4(TAU);}"),
        }.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                    SemanticError, rf"task14-{name}:1:.*E_UNKNOWN_SYMBOL"):
                analyze_program(parse_program(candidate, f"task14-{name}"),
                                f"task14-{name}")

    def test_strict_builtin_and_constant_index_rules(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        for source, code in (
            ("void main() { clamp(true, true, true); }", "E_NO_OVERLOAD"),
            ("void main() { mix(1, 2, 0); }", "E_NO_OVERLOAD"),
            ("void main() { vec2 p; float x = p[2]; }", "E_INDEX_BOUNDS"),
            ("void main() { float p[uint(2)]; }", "E_ARRAY_SIZE"),
        ):
            with self.subTest(source=source):
                with self.assertRaises(SemanticError) as context:
                    analyze_program(parse_program(source, "strict2"))
                self.assertIn(code, str(context.exception))

    def test_if_arms_have_lexical_scope_even_without_source_braces(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        leaking_sources = (
            "void main() { if (true) float branch = 1.0; branch = 2.0; }",
            "void main() { if (true) float branch = 1.0; else branch = 2.0; }",
        )
        for source in leaking_sources:
            with self.subTest(source=source), self.assertRaises(SemanticError) as context:
                analyze_program(parse_program(source, "if-arm-scope"))
            self.assertIn("E_UNKNOWN_SYMBOL", str(context.exception))

        typed = analyze_program(parse_program(
            "void main() { float value = 0.0; if (true) float value = 1.0; else value = 2.0; value = 3.0; }",
            "if-arm-shadow"))
        main = next(function for function in typed.functions if function.name == "main")
        outer_id = main.body[0].expressions[0].symbol_id
        then_id = main.body[1].children[0].expressions[0].symbol_id
        else_target_id = main.body[1].children[1].expressions[0].children[0].symbol_id
        final_target_id = main.body[2].expressions[0].children[0].symbol_id
        self.assertNotEqual(outer_id, then_id)
        self.assertEqual(outer_id, else_target_id)
        self.assertEqual(outer_id, final_target_id)

    def test_hex_int_bit_pattern_and_explicit_uint_constructor_are_retained(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        typed = analyze_program(parse_program(
            "const int bits = 0xffffffff; const uint ubits = uint(0xffffffff); void main() {}", "hex"))
        values = {item.symbol.name: item.initializer for item in typed.declarations}
        self.assertEqual(-1, values["bits"].literal_value)
        self.assertEqual("0xffffffff", values["ubits"].children[0].literal)
        self.assertEqual(-1, values["ubits"].children[0].literal_value)

    def test_builtin_directional_families_follow_glsl_signatures(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        valid = "void main() { vec2 p = vec2(1.0); min(p, 1.0); mod(p, 1.0); step(1.0, p); pow(p, p); }"
        analyze_program(parse_program(valid, "builtin-valid"))
        for expression in ("min(1.0, vec2(1.0))", "mod(1.0, vec2(1.0))",
                           "pow(1.0, vec2(1.0))", "step(vec2(1.0), 1.0)"):
            with self.subTest(expression=expression):
                with self.assertRaises(SemanticError) as context:
                    analyze_program(parse_program(f"void main() {{ {expression}; }}", "builtin-invalid"))
                self.assertIn("E_NO_OVERLOAD", str(context.exception))

    def test_glsl_constructor_conversion_and_ordered_scalar_rules(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        analyze_program(parse_program(
            "void main() { vec2 a = vec2(vec3(1.0)); vec4 b = vec4(mat2(1.0)); mat3 c = mat3(mat2(1.0)); }", "construct-valid"))
        for source, code in (
            ("void main() { bool b = vec2(1.0) < vec2(2.0); }", "E_OPERATOR"),
            ("void main() { vec3 b = vec3(mat2(1.0)); }", "E_CONSTRUCTOR"),
        ):
            with self.subTest(source=source):
                with self.assertRaises(SemanticError) as context:
                    analyze_program(parse_program(source, "construct-invalid"))
                self.assertIn(code, str(context.exception))

    def test_scoped_int_constant_expressions_drive_extents_and_bounds(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        analyze_program(parse_program(
            "const int G = 1 + 1; void main() { const int N = (G << 1) - 2; float a[1 + 1]; float b[N]; { const int N = 4; float c[N]; float x = c[N - 1]; } }", "constant-valid"))
        for source, code in (
            ("void main() { float a[uint(2)]; }", "E_ARRAY_SIZE"),
            ("void main() { float a[true ? 2 : 3]; }", "E_ARRAY_SIZE"),
            ("void main() { float a[1 / 0]; }", "E_ARRAY_SIZE"),
            ("void main() { float a[-1]; }", "E_ARRAY_SIZE"),
            ("void main() { int n = 2; float a[n]; }", "E_ARRAY_SIZE"),
            ("void main() { float a[2]; float x = a[1 + 1]; }", "E_INDEX_BOUNDS"),
        ):
            with self.subTest(source=source):
                with self.assertRaises(SemanticError) as context:
                    analyze_program(parse_program(source, "constant-invalid"))
                self.assertIn(code, str(context.exception))

    def test_counted_for_proof_retains_stable_induction_identity_and_exact_charges(self) -> None:
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        typed = analyze_program(parse_program(
            "void main() { for (int y = -1; y <= 1; y++) { "
            "for (int x = 0; x < 4; ++x) { if (x == 2) continue; } } }",
            "counted-proof"))
        main = next(function for function in typed.functions if function.name == "main")
        outer = main.body[0]
        inner = outer.children[1].children[0]
        self.assertEqual("for", outer.kind)
        self.assertEqual("for", inner.kind)
        self.assertEqual((3, 1, 1, 12, 15), (
            outer.loop_proof.trip_count,
            outer.loop_proof.lexical_depth,
            outer.loop_proof.effective_depth,
            outer.loop_proof.lexical_product,
            outer.loop_proof.entrypoint_charge,
        ))
        self.assertEqual((4, 2, 2, 12, 15), (
            inner.loop_proof.trip_count,
            inner.loop_proof.lexical_depth,
            inner.loop_proof.effective_depth,
            inner.loop_proof.lexical_product,
            inner.loop_proof.entrypoint_charge,
        ))
        induction = outer.children[0].expressions[0].symbol_id
        self.assertEqual(induction, outer.loop_proof.induction_symbol_id)
        self.assertEqual(induction, outer.expressions[0].children[0].symbol_id)
        self.assertEqual(induction, outer.expressions[1].children[0].symbol_id)
        self.assertEqual((2, 12, 15, 2, True), (
            typed.counted_loop_proof.max_effective_depth,
            typed.counted_loop_proof.max_lexical_product,
            typed.counted_loop_proof.entrypoint_charge,
            typed.counted_loop_proof.loop_count,
            typed.counted_loop_proof.call_graph_acyclic,
        ))


if __name__ == "__main__":
    unittest.main()
