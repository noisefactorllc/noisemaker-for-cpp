from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import types
import unittest

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
KEY = "synth/testPattern:testPattern"
SOURCE = CORPUS / "sources/synth/testPattern/testPattern.glsl"


def _module():
    from tools.glslcpp.frontend import testpattern_profile

    return testpattern_profile


def _program(raw: str | None = None, key: str = KEY):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    defines = generate_typed_slice._defaults(ROOT, key)
    return analyze_program(parse_program(raw, key, defines), key)


def _scratch_relocked(module, candidate):
    """Load a private profile copy with only coarse fingerprints refrozen.

    This keeps AST/site locks live while allowing a candidate mutation to
    reach the semantic guard it is intended to exercise.  The production
    module and the candidate are never modified in place.
    """
    scratch = types.ModuleType(module.__name__ + "__scratch")
    scratch.__dict__.update({
        "__file__": module.__file__,
        "__package__": module.__package__,
    })
    source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
    exec(compile(source, module.__file__, "exec"), scratch.__dict__)
    raw = candidate.raw_source.encode("utf-8")
    normalized = candidate.source.encode("utf-8")
    scratch.RAW_BYTES = len(raw)
    scratch.RAW_SHA256 = hashlib.sha256(raw).hexdigest()
    scratch.NORMALIZED_BYTES = len(normalized)
    scratch.NORMALIZED_SHA256 = hashlib.sha256(normalized).hexdigest()
    scratch.FUNCTIONS_SHA256 = scratch._sha(candidate.functions)
    scratch.WHOLE_SHA256 = scratch._whole(candidate)
    scratch.INTERFACE_SHA256 = scratch._interface(candidate)
    return scratch


def _authenticate_relocked(module, candidate):
    scratch = _scratch_relocked(module, candidate)
    source_hash = hashlib.sha256(candidate.raw_source.encode()).hexdigest()
    return scratch, scratch.authenticate_testpattern_frontend(
        candidate, source_hash, scratch.PROFILE)


def _replace_expression(value, predicate, replacement):
    children = tuple(_replace_expression(child, predicate, replacement)
                     for child in value.children)
    value = dataclasses.replace(value, children=children)
    return replacement(value) if predicate(value) else value


def _replace_statement(statement, predicate, replacement):
    expressions = tuple(_replace_expression(item, predicate, replacement)
                        for item in statement.expressions)
    children = tuple(_replace_statement(item, predicate, replacement)
                     for item in statement.children)
    return dataclasses.replace(statement, expressions=expressions,
                               children=children)


def _replace_function(program, function_name, transform):
    functions = []
    for function in program.functions:
        if function.name == function_name:
            function = dataclasses.replace(function,
                                            body=transform(function.body))
        functions.append(function)
    return dataclasses.replace(program, functions=tuple(functions))


def _drop_expression(value, predicate):
    children = tuple(
        _drop_expression(child, predicate)
        for child in value.children if not predicate(child)
    )
    return dataclasses.replace(value, children=children)


def _drop_from_statement(statement, predicate):
    expressions = tuple(
        _drop_expression(item, predicate)
        for item in statement.expressions if not predicate(item)
    )
    children = tuple(_drop_from_statement(item, predicate)
                     for item in statement.children)
    return dataclasses.replace(statement, expressions=expressions,
                               children=children)


def _index_predicate(line):
    return lambda value: (value.kind == "index"
                          and value.span.start_line == line)


class TestPatternFrontendProfileTests(unittest.TestCase):
    def test_profile_is_prepared_and_row_contract_is_explicit(self):
        module = _module()
        self.assertEqual(module.KEYS, ())
        self.assertEqual(module.PREPARED_KEYS, (KEY,))
        self.assertEqual(module.PROFILES, {KEY: module.PROFILE})
        self.assertEqual(module.ALLOWED_ROW_FIELDS[KEY], frozenset({
            "defines", "program_key", "testpattern_profile",
        }))
        self.assertEqual(module.REQUIRED_COMPANION_PROFILES[KEY], ())

    def test_authentication_returns_only_the_three_dynamic_indexes_and_round(self):
        module = _module()
        program = _program()
        proof = module.authenticate_testpattern_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(),
            module.PROFILE)
        self.assertEqual(proof.program_key, KEY)
        self.assertEqual(proof.global_array.name, "GLYPH")
        self.assertEqual(proof.local_arrays, ("digits", "colors"))
        self.assertEqual(proof.dynamic_index_names,
                         ("GLYPH", "digits", "colors"))
        self.assertEqual(proof.dynamic_index_spans,
                         ("30:14-30:26", "74:25-74:50", "121:17-121:28"))
        self.assertEqual(proof.round_span, "171:20-171:33")
        self.assertEqual(proof.loop_bounds, ((0, 3), (0, 3)))
        self.assertEqual(proof.num_digits_range, (1, 3))
        self.assertEqual(len(proof.consumed_objects), len({
            id(item) for item in proof.consumed_objects
        }))

    def test_binding_preflight_is_exact_and_zero_grid_is_authorized_clamp_input(self):
        module = _module()
        program = _program()
        contract = module.preflight_testpattern_bindings(program)
        self.assertEqual(contract.names, module.BINDING_NAMES)
        self.assertEqual(contract.source_abi, module.SOURCE_BINDING_ABI)
        self.assertEqual(contract.runtime_abi, module.RUNTIME_BINDING_ABI)
        self.assertEqual(contract.defaults, (("gridSize", 4), ("pattern", 0)))
        self.assertEqual(contract.grid_size_range, (0, 16))
        self.assertEqual(contract.pattern_range, (0, 6))
        for grid_size in (0, 1, 16):
            bindings = {"resolution": (1, 1), "tileOffset": (0, 0),
                        "fullResolution": (1, 1), "gridSize": grid_size,
                        "pattern": 0}
            self.assertIs(module.preflight_testpattern_bindings(
                program, bindings), contract)
        for bad_grid in (-1, 17):
            with self.assertRaisesRegex(ValueError, "gridSize"):
                module.preflight_testpattern_bindings(
                    program, {"resolution": (1, 1), "tileOffset": (0, 0),
                              "fullResolution": (1, 1), "gridSize": bad_grid,
                              "pattern": 0})
        for bad_pattern in (-1, 7):
            with self.assertRaisesRegex(ValueError, "pattern"):
                module.preflight_testpattern_bindings(
                    program, {"resolution": (1, 1), "tileOffset": (0, 0),
                              "fullResolution": (1, 1), "gridSize": 0,
                              "pattern": bad_pattern})

    def test_binding_preflight_rejects_missing_extra_or_wrong_abi(self):
        module = _module()
        program = _program()
        expected = {"resolution": (1, 1), "tileOffset": (0, 0),
                    "fullResolution": (1, 1), "gridSize": 4, "pattern": 0}
        missing = dict(expected)
        missing.pop("pattern")
        for candidate in (missing, {**expected, "forged": 1},
                          {**expected, "gridSize": 4.0},
                          {**expected, "pattern": True}):
            with self.assertRaises(ValueError):
                module.preflight_testpattern_bindings(program, candidate)

        resources = program.resources
        changed = dataclasses.replace(
            program,
            resources=dataclasses.replace(resources,
                                          uniforms=("resolution", "pattern")))
        with self.assertRaisesRegex(ValueError, "binding or resource"):
            module.preflight_testpattern_bindings(changed)

    def test_authentication_carries_the_source_specific_dynamic_loop_proof(self):
        module = _module()
        program = _program()
        proof = module.authenticate_testpattern_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(),
            module.PROFILE)
        self.assertEqual(proof.binding_preflight.grid_size_range, (0, 16))
        self.assertEqual(proof.binding_preflight.pattern_range, (0, 6))
        self.assertEqual(proof.dynamic_loop_owner, (29, "renderNumber"))
        self.assertEqual(proof.dynamic_loop_bound_symbol_id, 65)
        self.assertEqual(proof.dynamic_loop_bound_range, (1, 3))

    def test_wrong_profile_key_hash_and_foreign_source_fail_closed(self):
        module = _module()
        program = _program()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        for args, message in (
            ((program, source_hash, "wrong"), "exact"),
            ((_program(key="synth/foreign:foreign"), source_hash,
              module.PROFILE), "key"),
            ((program, "0" * 64, module.PROFILE), "source"),
        ):
            with self.subTest(message=message):
                with self.assertRaises(ValueError):
                    module.authenticate_testpattern_frontend(*args)

        foreign = _program(raw="void main() {}", key="synth/foreign:foreign")
        with self.assertRaises(ValueError):
            module.authenticate_testpattern_frontend(foreign, "0" * 64,
                                                      module.PROFILE)

    def test_missing_or_forged_dynamic_site_is_rejected_by_identity_census(self):
        module = _module()
        program = _program()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()

        def replace_expression(value, predicate, replacement):
            children = tuple(replace_expression(child, predicate, replacement)
                             for child in value.children)
            value = dataclasses.replace(value, children=children)
            return replacement(value) if predicate(value) else value

        def replace_statement(statement, predicate, replacement):
            expressions = tuple(replace_expression(item, predicate, replacement)
                                for item in statement.expressions)
            children = tuple(replace_statement(item, predicate, replacement)
                             for item in statement.children)
            return dataclasses.replace(statement, expressions=expressions,
                                       children=children)

        color_bars = next(item for item in program.functions
                          if item.name == "colorBars")
        forged = dataclasses.replace(
            color_bars,
            body=tuple(replace_statement(
                statement,
                lambda value: value.kind == "index"
                and value.span.start_line == 121,
                lambda value: dataclasses.replace(value, member="forged"))
                for statement in color_bars.body))
        changed = dataclasses.replace(
            program,
            functions=tuple(forged if item is color_bars else item
                            for item in program.functions))
        with self.assertRaises(ValueError):
            module.authenticate_testpattern_frontend(changed, source_hash,
                                                      module.PROFILE)

    def _assert_rejected_by_guard(self, module, candidate, message):
        pattern = module.PROFILE + ": " + message
        with self.assertRaises(ValueError) as context:
            _authenticate_relocked(module, candidate)
        self.assertEqual(str(context.exception), pattern)

    def test_array_declaration_and_initializer_locks_are_independent(self):
        module = _module()
        program = _program()
        glyph = next(item for item in program.declarations
                      if item.symbol.name == "GLYPH")

        changed_literal = dataclasses.replace(
            glyph.initializer.children[0], literal_value=0)
        changed_initializer = dataclasses.replace(
            glyph.initializer,
            children=(changed_literal, *glyph.initializer.children[1:]))
        changed = dataclasses.replace(
            program,
            declarations=(dataclasses.replace(
                glyph, initializer=changed_initializer),))
        self._assert_rejected_by_guard(
            module, changed, "GLYPH literal payload mismatch")

        changed_initializer = dataclasses.replace(
            glyph.initializer, children=glyph.initializer.children[:-1])
        changed = dataclasses.replace(
            program,
            declarations=(dataclasses.replace(
                glyph, initializer=changed_initializer),))
        self._assert_rejected_by_guard(
            module, changed, "GLYPH declaration or literal initializer mismatch")

        changed = dataclasses.replace(
            program, declarations=tuple(item for item in program.declarations
                                        if item is not glyph))
        self._assert_rejected_by_guard(
            module, changed, "array declaration census mismatch")

        colors_initializer = next(
            value for function, value in module._declaration_nodes(program)
            if function is not None and value.symbol.name == "colors")
        changed = _replace_function(
            program, "renderNumber",
            lambda body: tuple(_replace_statement(
                statement,
                lambda value: (value.kind == "declaration"
                               and value.symbol.name == "digits"),
                lambda value: dataclasses.replace(
                    value, children=(colors_initializer.children[0],)))
                for statement in body))
        self._assert_rejected_by_guard(
            module, changed, "digits local array contract mismatch")

        changed = _replace_function(
            program, "colorBars",
            lambda body: tuple(_replace_statement(
                statement,
                lambda value: (value.kind == "declaration"
                               and value.symbol.name == "colors"),
                lambda value: dataclasses.replace(
                    value,
                    children=(dataclasses.replace(
                        value.children[0],
                        children=value.children[0].children[:-1]),)))
                for statement in body))
        self._assert_rejected_by_guard(
            module, changed, "colors local array contract mismatch")

    def test_each_index_lock_and_index_census_reject_mutations(self):
        module = _module()
        program = _program()
        sites = (
            ("sampleGlyph", 30, "GLYPH index site identity mismatch"),
            ("renderNumber", 74, "digits index site identity mismatch"),
            ("colorBars", 121, "colors index site identity mismatch"),
            ("renderNumber", 56, "digits index site identity mismatch"),
        )
        for function_name, line, message in sites:
            with self.subTest(function_name=function_name, line=line):
                changed = _replace_function(
                    program, function_name,
                    lambda body, line=line: tuple(_replace_statement(
                        statement,
                        _index_predicate(line),
                        lambda value: dataclasses.replace(
                            value, member="forged"))
                        for statement in body))
                self._assert_rejected_by_guard(module, changed, message)

                changed = _replace_function(
                    program, function_name,
                    lambda body, line=line: tuple(_drop_from_statement(
                        statement, _index_predicate(line))
                        for statement in body))
                self._assert_rejected_by_guard(
                    module, changed,
                    message.replace("identity mismatch",
                                    "missing or duplicated"))

        color_bars = next(item for item in program.functions
                          if item.name == "colorBars")
        return_statement = next(item for item in color_bars.body
                                if item.kind == "return")
        extra = next(value for value in module._walk_statement(return_statement)
                     if value.kind == "index")
        changed_return = dataclasses.replace(
            return_statement,
            expressions=return_statement.expressions + (extra,))
        changed = dataclasses.replace(
            program,
            functions=tuple(
                dataclasses.replace(item, body=tuple(
                    changed_return if statement is return_statement else statement
                    for statement in item.body))
                if item is color_bars else item
                for item in program.functions))
        self._assert_rejected_by_guard(
            module, changed, "colors index site missing or duplicated")

    def test_loop_num_digits_and_round_locks_are_independent(self):
        module = _module()
        program = _program()
        render = next(item for item in program.functions
                      if item.name == "renderNumber")
        first_loop = next(item for item in render.body if item.kind == "for")
        changed_first = dataclasses.replace(
            first_loop,
            loop_proof=dataclasses.replace(first_loop.loop_proof,
                                            bound_value=2))
        changed = _replace_function(
            program, "renderNumber",
            lambda body: tuple(changed_first if item is first_loop else item
                               for item in body))
        self._assert_rejected_by_guard(
            module, changed, "digit extraction loop bound mismatch")

        second_loop = [item for item in render.body if item.kind == "for"][1]
        condition = dataclasses.replace(second_loop.expressions[0],
                                        operator="<=")
        changed_second = dataclasses.replace(
            second_loop,
            expressions=(condition, second_loop.expressions[1]))
        changed = _replace_function(
            program, "renderNumber",
            lambda body: tuple(changed_second if item is second_loop else item
                               for item in body))
        self._assert_rejected_by_guard(
            module, changed, "numDigits loop bound mismatch")

        guarded_if = render.body[1]
        assignment = guarded_if.children[0].expressions[0]
        changed_assignment = dataclasses.replace(
            assignment,
            children=(assignment.children[0],
                      dataclasses.replace(assignment.children[1],
                                           literal_value=4)))
        changed_if = dataclasses.replace(
            guarded_if,
            children=(dataclasses.replace(
                guarded_if.children[0], expressions=(changed_assignment,)),))
        changed = _replace_function(
            program, "renderNumber",
            lambda body: tuple(changed_if if item is guarded_if else item
                               for item in body))
        self._assert_rejected_by_guard(
            module, changed, "numDigits range proof mismatch")

        changed = _replace_function(
            program, "dotGrid",
            lambda body: tuple(_replace_statement(
                statement,
                lambda value: (value.kind == "builtin"
                               and value.callee == "round"),
                lambda value: dataclasses.replace(value, callee="floor"))
                for statement in body))
        self._assert_rejected_by_guard(
            module, changed, "round(vec2) census mismatch")

    def test_optional_carriers_and_unknown_rows_fail_closed(self):
        module = _module()
        program = _program()
        for field in ("fixed_nine_table_proof", "fixed_grid_counter_store_proof",
                      "fixed_array_in_parameter_proof",
                      "fixed_affine_centers13_proof"):
            with self.subTest(field=field):
                changed = dataclasses.replace(program, **{field: object()})
                self._assert_rejected_by_guard(
                    module, changed, "unrelated proof carrier is not absent")
        with self.assertRaisesRegex(ValueError,
                                    module.PROFILE + ": unknown Test Pattern row"):
            module.allowed_row_fields("synth/foreign:foreign")

    def test_apply_is_an_identity_checked_prepared_contract(self):
        module = _module()
        program = _program()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        result = module.apply_testpattern_frontend(program, source_hash,
                                                   module.PROFILE)
        self.assertIs(result, program)
