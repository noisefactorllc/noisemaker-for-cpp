from __future__ import annotations

import dataclasses
import copy
import hashlib
import importlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "filter/scanlineError:scanlineError"
PROFILE = "scanline-error-float-bits-ingress-v1"
RAW_SHA256 = "66556b29659b479edd397f8e0c87c176cafa7560c426eab8211b6939a08f2198"
SOURCE = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources/filter/scanlineError/scanlineError.glsl")
MODULE = "tools.glslcpp.frontend.scanline_error_float_bits_ingress_profile"


def _profile():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError("Scanline Error ingress profile module is absent")
    return importlib.import_module(MODULE)


def _analyzed(raw: str | None = None, key: str = KEY):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(
        parse_program(raw, key, generate_typed_slice._defaults(ROOT, KEY)), key)


class ScanlineErrorFloatBitsIngressProfileTests(unittest.TestCase):
    def test_slice_schema_accepts_exact_single_scanline_profile_row(self):
        spec = copy.deepcopy(generate_typed_slice.load_slice(ROOT))
        spec["programs"] = [item for item in spec["programs"]
                            if item["program_key"] != KEY]
        spec["programs"].append({
            "defines": {},
            "program_key": KEY,
            "scanline_error_float_bits_ingress_profile": PROFILE,
        })
        spec["programs"].sort(key=lambda item: item["program_key"])
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            target = repository / "tools/glslcpp/typed_slice.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(spec), encoding="utf-8")
            loaded = generate_typed_slice.load_slice(repository)
        carriers = [item for item in loaded["programs"]
                    if "scanline_error_float_bits_ingress_profile" in item]
        self.assertEqual([{
            "defines": {},
            "program_key": KEY,
            "scanline_error_float_bits_ingress_profile": PROFILE,
        }], carriers)

    def test_exact_profile_authenticates_three_candidate_owned_ingresses(self):
        profile = _profile()
        program = _analyzed()
        proof = profile.authenticate_scanline_error_float_bits_ingress(
            program, RAW_SHA256, PROFILE)
        self.assertIs(proof.host,
                      next(item for item in program.functions if item.id == 69))
        self.assertEqual(3, len(proof.ingresses))
        self.assertTrue(all(item.kind == "builtin" and
                            item.callee == "floatBitsToUint"
                            for item in proof.ingresses))
        self.assertTrue(all(item.type.display() == "uint"
                            for item in proof.ingresses))
        self.assertTrue(all(len(item.children) == 1 and
                            item.children[0].type.display() == "float"
                            for item in proof.ingresses))
        self.assertTrue(all(parent is proof.parent for parent in proof.parents))
        self.assertIs(profile.apply_scanline_error_float_bits_ingress(
            program, RAW_SHA256, PROFILE), program)

    def test_profile_rejects_carrier_source_key_and_tree_mutations(self):
        profile = _profile()
        program = _analyzed()
        cases = [
            (program, RAW_SHA256, None),
            (program, RAW_SHA256, "wrong"),
            (program, "0" * 64, PROFILE),
            (dataclasses.replace(program, key="filter/other:other"),
             RAW_SHA256, PROFILE),
            (dataclasses.replace(program, fixed_nine_table_proof=object()),
             RAW_SHA256, PROFILE),
            (dataclasses.replace(program, functions=program.functions[:-1]),
             RAW_SHA256, PROFILE),
        ]
        raw = SOURCE.read_text(encoding="utf-8")
        for anchor, replacement in (
                ("floatBitsToUint(p.x)", "uint(p.x)"),
                ("floatBitsToUint(p.y)", "floatBitsToUint(p.x)"),
                ("uvec3 seed = uvec3(",
                 "uint extraBits = floatBitsToUint(p.x);\n    uvec3 seed = uvec3(")):
            mutated = raw.replace(anchor, replacement)
            cases.append((_analyzed(mutated),
                          hashlib.sha256(mutated.encode()).hexdigest(), PROFILE))
        for index, (candidate, source_hash, carrier) in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                profile.authenticate_scanline_error_float_bits_ingress(
                    candidate, source_hash, carrier)

    def test_validator_and_emitter_admit_only_authenticated_objects(self):
        profile = _profile()
        program = _analyzed()
        kwargs = {"source_hash": RAW_SHA256,
                  "scanline_error_float_bits_ingress_profile": PROFILE}
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES, **kwargs)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, RAW_SHA256, "scanline_probe", "bind_scanline_probe",
            scanline_error_float_bits_ingress_profile=PROFILE)
        helper = rendered.split(" hashNoise(", 2)[2].split("\n}\n", 1)[0]
        self.assertEqual(3, helper.count("noisemaker::float_bits_to_uint("))
        self.assertIn("glsl::UVec3(noisemaker::float_bits_to_uint(", helper)
        self.assertNotIn("glsl::detail::float_to_uint32", helper)

        separate = _analyzed()
        separate_proof = profile.authenticate_scanline_error_float_bits_ingress(
            separate, RAW_SHA256, PROFILE)
        with mock.patch(
                "tools.glslcpp.generate_typed_slice."
                "authenticate_scanline_error_float_bits_ingress",
                return_value=separate_proof), self.assertRaises(
                    generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES, **kwargs)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp."
                "authenticate_scanline_error_float_bits_ingress",
                return_value=separate_proof), self.assertRaises(
                    emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                program, KEY, RAW_SHA256, "scanline_probe",
                "bind_scanline_probe",
                scanline_error_float_bits_ingress_profile=PROFILE)

    def test_node_level_ingress_logic_rejects_past_refrozen_coarse_hash_gate(self):
        profile = _profile()
        coarse = "source, function, whole-program, or interface mismatch"

        def walk_expression(value):
            yield value
            for child in value.children:
                yield from walk_expression(child)

        def walk_statement(value):
            yield value
            for child in value.children:
                yield from walk_statement(child)

        def sites(program):
            host = next(item for item in program.functions if item.id == 69)
            return [node
                    for statement in host.body
                    for owner in walk_statement(statement)
                    for expression in owner.expressions
                    for node in walk_expression(expression)
                    if node.kind == "builtin" and
                    node.callee == "floatBitsToUint"]

        def ingress_parent(program):
            host = next(item for item in program.functions if item.id == 69)
            return host.body[0].expressions[0].children[0]

        def rename_first(candidate):
            object.__setattr__(sites(candidate)[0], "callee", "abs")

        def orphan_second(candidate):
            object.__setattr__(sites(candidate)[1], "children", ())

        def widen_third(candidate):
            node = sites(candidate)[2]
            object.__setattr__(node, "children",
                               (*node.children, node.children[0]))

        def retype_first_child(candidate):
            from tools.glslcpp.frontend.semantic_types import vector
            object.__setattr__(sites(candidate)[0].children[0], "type",
                               vector("float", 2))

        def append_fourth_ingress(candidate):
            parent = ingress_parent(candidate)
            fourth = dataclasses.replace(parent.children[0])
            object.__setattr__(parent, "children", (*parent.children, fourth))

        def swap_xy_children(candidate):
            first, second, _ = sites(candidate)
            first_child = first.children[0]
            second_child = second.children[0]
            object.__setattr__(first, "children", (second_child,))
            object.__setattr__(second, "children", (first_child,))

        def forge_wrong_parent(candidate):
            from tools.glslcpp.frontend.semantic_types import vector
            object.__setattr__(ingress_parent(candidate), "type",
                               vector("uint", 2))

        cases = (
            ("first ingress renamed", rename_first,
             "ingress cardinality mismatch"),
            ("second ingress loses its child", orphan_second,
             "ingress node identity mismatch"),
            ("third ingress gains a second child", widen_third,
             "ingress node identity mismatch"),
            ("first ingress child retyped to vec2", retype_first_child,
             "ingress node identity mismatch"),
            ("explicit fourth ingress appended", append_fourth_ingress,
             "ingress cardinality mismatch"),
            ("x and y child objects swapped", swap_xy_children,
             "ingress node identity mismatch"),
            ("shared parent retyped to uvec2", forge_wrong_parent,
             "shared ingress parent structure mismatch"),
        )
        baseline_functions = profile._sha(_analyzed().functions)
        for label, mutate, expected in cases:
            with self.subTest(node_axis=label):
                candidate = _analyzed()
                mutate(candidate)
                self.assertNotEqual(
                    baseline_functions, profile._sha(candidate.functions), label)
                normalized = candidate.source.encode("utf-8")
                loop_proof = candidate.counted_loop_proof
                with mock.patch.multiple(
                        profile,
                        _FUNCTIONS_SHA256=profile._sha(candidate.functions),
                        _WHOLE_SHA256=profile._whole(candidate),
                        _INTERFACE_SHA256=profile._interface(candidate),
                        _NORMALIZED_SHA256=hashlib.sha256(normalized).hexdigest(),
                        _NORMALIZED_BYTES=len(normalized),
                        _LOOP_PROOF=(loop_proof.loop_count,
                                     loop_proof.unproved_loop_count,
                                     loop_proof.max_effective_depth,
                                     loop_proof.max_lexical_product,
                                     loop_proof.entrypoint_charge,
                                     loop_proof.call_graph_acyclic)):
                    with self.assertRaises(ValueError) as raised:
                        profile.authenticate_scanline_error_float_bits_ingress(
                            candidate, RAW_SHA256, PROFILE)
                message = str(raised.exception)
                self.assertNotIn(coarse, message,
                                 f"{label} was absorbed by the coarse gate")
                self.assertIn(expected, message, label)

        profile.authenticate_scanline_error_float_bits_ingress(
            _analyzed(), RAW_SHA256, PROFILE)

    def test_both_authorities_fail_closed_without_exact_carrier(self):
        _profile()
        program = _analyzed()
        for carrier in (None, "wrong"):
            with self.subTest(authority="validator", carrier=carrier), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=RAW_SHA256,
                    scanline_error_float_bits_ingress_profile=carrier)
            with self.subTest(authority="emitter", carrier=carrier), \
                    self.assertRaises(emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, RAW_SHA256, "scanline_probe",
                    "bind_scanline_probe",
                    scanline_error_float_bits_ingress_profile=carrier)

        foreign = _analyzed(key="filter/other:other")
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256,
                scanline_error_float_bits_ingress_profile=PROFILE)
        with self.assertRaises(emit_typed_cpp.TypedEmissionError):
            emit_typed_cpp.render_typed_cpp(
                foreign, foreign.key, RAW_SHA256, "scanline_probe",
                "bind_scanline_probe",
                scanline_error_float_bits_ingress_profile=PROFILE)

    def test_global_vocabularies_remain_frozen_and_foreign_builtin_is_rejected(self):
        _profile()
        frozen = {
            "capabilities": (44, "6ddb906dc859e45ee613b580dc6988c663d2aff22db9c365ece3097d126a4aea"),
            "types": (17, "aa4ab00ac3b34ece6681eaa55435817b7908c9b8ea421a6eca1931f6ab4791c7"),
            "binary": (17, "cceb35790b79fa895906c57d7e81f0056fac404cf7448eec9b8d9dbb49b705b0"),
            "assignment": (6, "99a6ede7544a02082e0b72d83690c3b68d8c846e221078e3e90ac10463d498e2"),
        }
        values = {
            "capabilities": generate_typed_slice.APPROVED_CAPABILITIES,
            "types": generate_typed_slice.APPROVED_TYPES,
            "binary": generate_typed_slice.APPROVED_BINARY_OPERATORS,
            "assignment": generate_typed_slice.APPROVED_ASSIGNMENT_OPERATORS,
        }
        for name, value in values.items():
            self.assertEqual(frozen[name][0], len(value))
            self.assertEqual(frozen[name][1],
                             hashlib.sha256(repr(value).encode()).hexdigest())
        self.assertNotIn("floatBitsToUint", generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertNotIn("floatBitsToUint", generate_typed_slice._BUILTINS)
        self.assertNotIn("floatBitsToUint", emit_typed_cpp._BUILTIN_NAMES)

        raw = ("out vec4 fragColor;"
               "void main(){fragColor=vec4(float(floatBitsToUint(1.0)));}")
        foreign = analyze_program(parse_program(raw, "test:foreign", {}),
                                  "test:foreign")
        source_hash = hashlib.sha256(raw.encode()).hexdigest()
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    "unsupported builtin floatBitsToUint"):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        with self.assertRaisesRegex(emit_typed_cpp.TypedEmissionError,
                                    "unsupported builtin floatBitsToUint"):
            emit_typed_cpp.render_typed_cpp(
                foreign, foreign.key, source_hash, "foreign", "bind_foreign")


if __name__ == "__main__":
    unittest.main()
