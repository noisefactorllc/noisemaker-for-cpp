from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import unittest

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import remap_profile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources/synth/remap/remap.glsl")
KEY = remap_profile.KEY


def _program(key: str = KEY):
    raw = SOURCE.read_text(encoding="utf-8")
    defines = generate_typed_slice._defaults(ROOT, key)
    return analyze_program(parse_program(raw, key, defines), key)


def _walk_expr(value):
    yield value
    for child in value.children:
        yield from _walk_expr(child)


def _replace_expr(value, predicate):
    children = tuple(_replace_expr(child, predicate) for child in value.children)
    value = dataclasses.replace(value, children=children)
    if predicate(value):
        return dataclasses.replace(value, operator="-")
    return value


def _replace_statement(statement, predicate):
    return dataclasses.replace(
        statement,
        expressions=tuple(_replace_expr(item, predicate)
                          for item in statement.expressions),
        children=tuple(_replace_statement(item, predicate)
                       for item in statement.children),
    )


class RemapFrontendProfileTests(unittest.TestCase):
    def test_profile_authenticates_block_bindings_indexes_and_fixed_loops(self):
        program = _program()
        proof = remap_profile.authenticate_remap_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(),
            remap_profile.PROFILE)
        self.assertEqual(proof.program_key, KEY)
        self.assertEqual(proof.uniform_block.block_name, "RemapUniforms")
        self.assertEqual(proof.data_field.name, "data")
        self.assertEqual(tuple(item.index_shape for item in proof.indexes),
                         ("binary", "binary", "literal", "literal"))
        self.assertEqual(tuple(item.index_literal for item in proof.indexes[-2:]),
                         (0, 1))
        self.assertEqual(tuple(item.bound for item in proof.loops), (64, 8, 64))
        self.assertEqual(proof.source_constants, remap_profile.SOURCE_CONSTANTS)
        self.assertEqual(len(proof.consumed_objects), len({id(x) for x in proof.consumed_objects}))

    def test_binding_contract_is_exact_and_rejects_missing_extra_or_wrong_carrier(self):
        module = remap_profile
        program = _program()
        expected = {name: object() for name in module.BINDING_NAMES}
        self.assertEqual(module.preflight_remap_bindings(program).runtime_abi,
                         module.RUNTIME_BINDING_ABI)
        self.assertIs(module.preflight_remap_bindings(program, expected),
                      module.preflight_remap_bindings(program))
        for candidate in (
                {name: object() for name in module.BINDING_NAMES[:-1]},
                {**expected, "forged": object()},
                {"forged": object(), **{name: object() for name in module.BINDING_NAMES[1:]}}):
            with self.assertRaises(ValueError):
                module.preflight_remap_bindings(program, candidate)

    def test_profile_rejects_wrong_profile_source_foreign_key_and_tree_mutation(self):
        program = _program()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        for args in ((program, source_hash, "wrong-profile"),
                     (program, "0" * 64, remap_profile.PROFILE),
                     (_program("synth/foreign:foreign"), source_hash,
                      remap_profile.PROFILE)):
            with self.assertRaises(ValueError):
                remap_profile.authenticate_remap_frontend(*args)

        def mutate(value):
            return value.kind == "index" and value.span.start_line == 31

        functions = tuple(
            dataclasses.replace(function, body=tuple(
                _replace_statement(statement, mutate)
                for statement in function.body))
            for function in program.functions)
        changed = dataclasses.replace(program, functions=functions)
        with self.assertRaisesRegex(ValueError, "function, whole-program, or interface"):
            remap_profile.authenticate_remap_frontend(changed, source_hash,
                                                       remap_profile.PROFILE)

    def test_profile_rejects_unrelated_proof_and_uniform_block_carrier(self):
        program = _program()
        source_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "unrelated proof"):
            remap_profile.authenticate_remap_frontend(
                dataclasses.replace(program, fixed_nine_table_proof=object()),
                source_hash, remap_profile.PROFILE)
        with self.assertRaisesRegex(ValueError, "source, define"):
            remap_profile.authenticate_remap_frontend(
                dataclasses.replace(program, uniform_blocks=()),
                source_hash, remap_profile.PROFILE)


if __name__ == "__main__":
    unittest.main()
