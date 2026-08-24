from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import pathlib
import unittest
from unittest import mock

from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.typed_ir import PreprocessorDefine, TypedExpression
from tools.glslcpp.generate_typed_slice import (
    APPROVED_CAPABILITIES,
    GeneratorError,
    validate_capabilities,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
KEY = "filter/tetraColorArray:tetraColorArray"
SOURCE = CORPUS / "sources/filter/tetraColorArray/tetraColorArray.glsl"


class RuntimeLoopBoundTetraTests(unittest.TestCase):
    def _unproved(self, key: str = KEY):
        source = SOURCE.read_text(encoding="utf-8")
        return analyze_program(parse_program(source, key, {}), key)

    def _profiled(self):
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, apply_runtime_loop_bound,
        )
        program = self._unproved()
        source_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
        return apply_runtime_loop_bound(program, source_hash, PROFILE), source_hash

    def _assert_both_authorities_reject(self, program, source_hash: str,
                                        **extra) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import PROFILE
        kwargs = {"runtime_loop_bound_profile": PROFILE, **extra}
        with self.assertRaises((GeneratorError, ValueError)):
            validate_capabilities(program, APPROVED_CAPABILITIES,
                                  source_hash=source_hash, **kwargs)
        with self.assertRaises((TypedEmissionError, ValueError)):
            render_typed_cpp(program, program.key, source_hash, **kwargs)

    def test_no_profile_analysis_remains_unproved(self) -> None:
        program = self._unproved()
        self.assertEqual(program.counted_loop_proof.loop_count, 0)
        self.assertEqual(program.counted_loop_proof.unproved_loop_count, 1)

    def test_exact_profile_attaches_seven_trip_proof_for_both_authorities(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE,
            apply_runtime_loop_bound,
        )

        unproved = self._unproved()
        source_hash = hashlib.sha256(unproved.raw_source.encode("utf-8")).hexdigest()
        program = apply_runtime_loop_bound(unproved, source_hash, PROFILE)
        proof = program.counted_loop_proof
        self.assertEqual((proof.loop_count, proof.unproved_loop_count), (1, 0))
        self.assertEqual((proof.max_effective_depth, proof.max_lexical_product,
                          proof.entrypoint_charge), (1, 7, 7))
        validate_capabilities(
            program, APPROVED_CAPABILITIES, source_hash=source_hash,
            runtime_loop_bound_profile=PROFILE)
        rendered = render_typed_cpp(
            program, KEY, source_hash,
            runtime_loop_bound_profile=PROFILE)
        guard = "if (colorCount < 2 || colorCount > 8)"
        extraction = 'const auto colorCount = bindings.get<std::int32_t>("colorCount");'
        state = "const auto state = std::make_shared<typed_kernel::State>("
        self.assertEqual(rendered.count(extraction), 1)
        self.assertEqual(rendered.count(guard), 1)
        self.assertLess(rendered.index(extraction), rendered.index(guard))
        self.assertLess(rendered.index(guard), rendered.index(state))

    def test_profile_is_exact_keyed_and_mutation_closed(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE,
            apply_runtime_loop_bound,
        )

        unproved = self._unproved()
        source_hash = hashlib.sha256(unproved.raw_source.encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "exact profile carrier required"):
            apply_runtime_loop_bound(unproved, source_hash, "wrong")
        foreign = dataclasses.replace(unproved, key="filter/foreign:foreign")
        with self.assertRaisesRegex(ValueError, "profile on foreign key"):
            apply_runtime_loop_bound(foreign, source_hash, PROFILE)
        changed = dataclasses.replace(unproved, raw_source=unproved.raw_source + "\n")
        with self.assertRaisesRegex(ValueError, "source or define profile mismatch"):
            apply_runtime_loop_bound(changed, source_hash, PROFILE)

    def test_missing_carrier_is_rejected_only_at_admission(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import PROFILE

        unproved = self._unproved()
        source_hash = hashlib.sha256(unproved.raw_source.encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(GeneratorError, "exact runtime-loop-bound carrier required"):
            validate_capabilities(unproved, APPROVED_CAPABILITIES,
                                  source_hash=source_hash)
        with self.assertRaisesRegex(TypedEmissionError, "exact profile carrier required"):
            render_typed_cpp(unproved, KEY, source_hash)
        foreign = dataclasses.replace(unproved, key="filter/foreign:foreign")
        with self.assertRaisesRegex(GeneratorError, "runtime-loop-bound carrier on foreign key"):
            validate_capabilities(foreign, APPROVED_CAPABILITIES,
                                  source_hash=source_hash,
                                  runtime_loop_bound_profile=PROFILE)

    def test_metadata_contract_is_exact(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            validate_tetra_metadata,
        )

        metadata = json.loads((CORPUS / "metadata.json").read_text(encoding="utf-8"))
        effect = metadata["effects"]["filter/tetraColorArray"]
        validate_tetra_metadata(effect)
        for field, value in (("type", "float"), ("min", 1),
                             ("default", 5), ("max", 9)):
            changed = copy.deepcopy(effect)
            changed["params"]["colorCount"][field] = value
            with self.assertRaisesRegex(ValueError, "metadata contract mismatch"):
                validate_tetra_metadata(changed)

    def test_seed_and_guard_share_one_immutable_maximum(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE,
            authenticate_runtime_loop_bound,
        )

        program = self._unproved()
        source_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
        contract = authenticate_runtime_loop_bound(program, source_hash, PROFILE)
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual((contract.minimum, contract.default, contract.maximum),
                         (2, 6, 8))
        self.assertEqual(contract.seed.maximum, contract.maximum)
        with self.assertRaises(TypeError):
            dataclasses.replace(contract, maximum=9)

    def test_seed_constructor_rejects_identity_and_nonintegral_maxima(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            RuntimeScalarBoundSeed,
        )
        program = self._unproved()
        parameter = next(function.parameters[1] for function in program.functions
                         if function.name == "sampleColorArray")
        with self.assertRaisesRegex(ValueError, "symbol identity mismatch"):
            RuntimeScalarBoundSeed(parameter.id + 1, 8, "test", parameter)
        for bad in (-1, 8.0, True):
            with self.subTest(maximum=bad):
                with self.assertRaisesRegex(ValueError, "nonnegative int"):
                    RuntimeScalarBoundSeed(parameter.id, bad, "test", parameter)

    def test_both_authorities_reject_a_replaced_seed_maximum(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE,
            authenticate_runtime_loop_bound,
        )
        program, source_hash = self._profiled()
        contract = authenticate_runtime_loop_bound(program, source_hash, PROFILE)
        assert contract is not None
        malformed = dataclasses.replace(
            contract, seed=dataclasses.replace(contract.seed, maximum=9))
        with mock.patch(
                "tools.glslcpp.frontend.runtime_loop_bound_profile."
                "authenticate_runtime_loop_bound", return_value=malformed):
            with self.assertRaisesRegex(GeneratorError, "malformed authenticated"):
                validate_capabilities(
                    program, APPROVED_CAPABILITIES, source_hash=source_hash,
                    runtime_loop_bound_profile=PROFILE)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp.authenticate_runtime_loop_bound",
                return_value=malformed):
            with self.assertRaisesRegex(TypedEmissionError,
                                        "malformed authenticated"):
                render_typed_cpp(
                    program, KEY, source_hash,
                    runtime_loop_bound_profile=PROFILE)

    def test_identity_mutation_matrix_rejects_in_both_authorities(self) -> None:
        program, source_hash = self._profiled()

        def replace_function(target, replacement):
            return dataclasses.replace(
                program, functions=tuple(replacement if item is target else item
                                         for item in program.functions))

        helper = next(item for item in program.functions
                      if item.name == "sampleColorArray")
        main = next(item for item in program.functions if item.name == "main")
        changed_parameter = dataclasses.replace(helper.parameters[1], name="otherCount")
        changed_helper_parameter = dataclasses.replace(
            helper, signature=dataclasses.replace(
                helper.signature,
                parameters=(helper.parameters[0], changed_parameter,
                            helper.parameters[2])))

        def mutate_expression(value, predicate, transform):
            children = tuple(mutate_expression(child, predicate, transform)
                             for child in value.children)
            rebuilt = dataclasses.replace(value, children=children)
            return transform(rebuilt) if predicate(rebuilt) else rebuilt

        def mutate_statement(value, predicate, transform):
            expressions = tuple(mutate_expression(item, predicate, transform)
                                for item in value.expressions)
            children = tuple(mutate_statement(child, predicate, transform)
                             for child in value.children)
            return dataclasses.replace(value, expressions=expressions,
                                       children=children)

        changed_call_main = dataclasses.replace(
            main, body=tuple(mutate_statement(
                statement,
                lambda item: isinstance(item, TypedExpression)
                and item.kind == "call" and item.callee == "sampleColorArray",
                lambda item: dataclasses.replace(item, callee="otherHelper"))
                for statement in main.body))
        changed_argument_main = dataclasses.replace(
            main, body=tuple(mutate_statement(
                statement,
                lambda item: isinstance(item, TypedExpression)
                and item.kind == "call" and item.callee == "sampleColorArray",
                lambda item: dataclasses.replace(
                    item, children=(item.children[0], item.children[0],
                                    item.children[2])))
                for statement in main.body))

        def contains_sample_call(statement) -> bool:
            stack = list(statement.expressions)
            while stack:
                item = stack.pop()
                if item.kind == "call" and item.callee == "sampleColorArray":
                    return True
                stack.extend(item.children)
            return any(contains_sample_call(child) for child in statement.children)

        call_statement = next(item for item in main.body
                              if contains_sample_call(item))
        loop_statement = next(item for item in helper.body if item.kind == "for")
        mutations = {
            "normalized-source": dataclasses.replace(
                program, source=program.source + "\n"),
            "defines": dataclasses.replace(
                program, preprocessor_defines=(PreprocessorDefine("X", "int", "1"),)),
            "interface-resources": dataclasses.replace(
                program, resources=dataclasses.replace(
                    program.resources,
                    uniforms=program.resources.uniforms + ("foreign",))),
            "helper": replace_function(
                helper, dataclasses.replace(
                    helper, signature=dataclasses.replace(
                        helper.signature, name="sampleColorArray2"))),
            "parameter": replace_function(helper, changed_helper_parameter),
            "call": replace_function(main, changed_call_main),
            "argument": replace_function(main, changed_argument_main),
            "second-caller": replace_function(
                main, dataclasses.replace(main, body=main.body + (call_statement,))),
            "second-loop": replace_function(
                helper, dataclasses.replace(
                    helper, body=helper.body + (loop_statement,))),
        }
        for name, changed in mutations.items():
            with self.subTest(mutation=name):
                self._assert_both_authorities_reject(changed, source_hash)

    def test_submitted_proof_tamper_rejects_in_both_authorities(self) -> None:
        program, source_hash = self._profiled()
        tampered = dataclasses.replace(
            program, counted_loop_proof=dataclasses.replace(
                program.counted_loop_proof, entrypoint_charge=8))
        self._assert_both_authorities_reject(tampered, source_hash)

    def test_duplicate_and_colliding_runtime_seeds_reject(self) -> None:
        from tools.glslcpp.frontend.loop_proof import attach_counted_loop_proofs
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE,
            authenticate_runtime_loop_bound,
        )
        program = self._unproved()
        source_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
        contract = authenticate_runtime_loop_bound(program, source_hash, PROFILE)
        assert contract is not None
        with self.assertRaisesRegex(ValueError, "duplicate runtime"):
            attach_counted_loop_proofs(
                program.functions, KEY,
                runtime_scalar_bounds=(contract.seed, contract.seed))
        source_seed = (contract.seed.symbol_id, contract.seed.maximum,
                       "collision", contract.seed.symbol)
        with self.assertRaisesRegex(ValueError, "colliding counted-loop seed"):
            attach_counted_loop_proofs(
                program.functions, KEY, source_global_bounds=(source_seed,),
                runtime_scalar_bounds=(contract.seed,))

    def test_every_unrelated_carrier_is_mutually_exclusive(self) -> None:
        program, source_hash = self._profiled()
        carrier_names = (
            "compatibility_transform", "custom_comparer_profile",
            "source_global_literal_int_profile", "gather_sorted_round_profile",
            "literal_vec3_lane_index_profile", "smooth_edge_luma_weights_profile",
            "perlin_scalar_uint_xor_profile", "bitwise_scalar_int_ops_profile",
            "rotate_mat2_return_profile", "focus_blur_borrowed_sampler_profile",
            "extrude_bvec2_relational_reduction_profile", "caustic_word_hash_profile",
            "edge_bvec3_contour_profile",
            "curl_vector_math_profile", "grade_luma_weights_profile",
            "grade_index_expression_profile", "derivative_admission_profile",
            "linear_srgb_lane_index_profile", "reflect_admission_profile",
            "posterize_round_profile", "as_u32_round_profile",
            "ceil_admission_profile", "waves_any_notequal_profile",
            "inout_vec3_swap_profile",
        )
        for name in carrier_names:
            with self.subTest(carrier=name):
                self._assert_both_authorities_reject(
                    program, source_hash, **{name: "foreign-profile"})
        with self.subTest(carrier="numeric_literal_contract"):
            self._assert_both_authorities_reject(
                program, source_hash, numeric_literal_contract="source-double")

    def test_stats_tail_remains_fail_closed_with_or_without_profile(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import PROFILE
        source_root = CORPUS / "sources"
        rows = (("filter/normalize:statsFinal",
                 source_root / "filter/normalize/statsFinal.glsl"),)
        for key, path in rows:
            source = path.read_text(encoding="utf-8")
            program = analyze_program(parse_program(source, key, {}), key)
            source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
            for carrier in (None, PROFILE):
                with self.subTest(key=key, carrier=carrier):
                    kwargs = ({"runtime_loop_bound_profile": carrier}
                              if carrier is not None else {})
                    with self.assertRaises((GeneratorError, ValueError)):
                        validate_capabilities(
                            program, APPROVED_CAPABILITIES,
                            source_hash=source_hash, **kwargs)
                    with self.assertRaises((TypedEmissionError, ValueError)):
                        render_typed_cpp(program, key, source_hash, **kwargs)


class RuntimeLoopBoundBlurTests(unittest.TestCase):
    def _unproved(self, short: str):
        key = f"filter/blur:{short}"
        source = (CORPUS / f"sources/filter/blur/{short}.glsl").read_text(
            encoding="utf-8")
        return analyze_program(parse_program(source, key, {}), key)

    def _profiled(self, short: str):
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, apply_runtime_loop_bound,
        )
        program = self._unproved(short)
        source_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
        return apply_runtime_loop_bound(program, source_hash, PROFILE), source_hash

    def test_exact_profiles_attach_127_trip_proof_and_binary64_guard(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import PROFILE
        for short, axis in (("blurH", "radiusX"), ("blurV", "radiusY")):
            with self.subTest(short=short):
                program, source_hash = self._profiled(short)
                proof = program.counted_loop_proof
                self.assertEqual((proof.loop_count, proof.unproved_loop_count), (1, 0))
                self.assertEqual((proof.max_effective_depth,
                                  proof.max_lexical_product,
                                  proof.entrypoint_charge), (1, 127, 127))
                validate_capabilities(
                    program, APPROVED_CAPABILITIES, source_hash=source_hash,
                    runtime_loop_bound_profile=PROFILE)
                rendered = render_typed_cpp(
                    program, program.key, source_hash,
                    runtime_loop_bound_profile=PROFILE)
                extraction = f'const auto {axis} = bindings.get_number("{axis}");'
                scale = 'const auto renderScale = bindings.get_number("renderScale");'
                product = f"const double runtime_loop_product = {axis} * renderScale;"
                radius = ("const std::int32_t runtime_loop_radius = "
                          "static_cast<std::int32_t>(runtime_loop_product);")
                state = "const auto state = std::make_shared<typed_kernel::State>("
                for expected in (extraction, scale, product, radius,
                                 "std::isfinite", "state.runtime_loop_radius"):
                    self.assertIn(expected, rendered)
                self.assertEqual(rendered.count(extraction), 1)
                self.assertEqual(rendered.count(scale), 1)
                self.assertEqual(rendered.count(
                    f'bindings.get_number("{axis}")'), 1)
                self.assertEqual(rendered.count(
                    'bindings.get_number("renderScale")'), 1)
                self.assertEqual(rendered.count(product), 1)
                self.assertEqual(rendered.count(radius), 1)
                self.assertLess(rendered.index(product), rendered.index(state))
                self.assertIn("runtime_loop_radius", rendered[rendered.index(state):])

    def test_no_profile_stays_unproved_and_admission_requires_carrier(self) -> None:
        for short in ("blurH", "blurV"):
            program = self._unproved(short)
            source_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
            self.assertEqual((program.counted_loop_proof.loop_count,
                              program.counted_loop_proof.unproved_loop_count), (0, 1))
            with self.assertRaisesRegex(GeneratorError,
                                        "exact runtime-loop-bound carrier required"):
                validate_capabilities(program, APPROVED_CAPABILITIES,
                                      source_hash=source_hash)
            with self.assertRaisesRegex(TypedEmissionError,
                                        "exact profile carrier required"):
                render_typed_cpp(program, program.key, source_hash)

    def test_blur_metadata_contract_is_exact(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            validate_blur_metadata,
        )
        metadata = json.loads((CORPUS / "metadata.json").read_text(encoding="utf-8"))
        effect = metadata["effects"]["filter/blur"]
        validate_blur_metadata(effect)
        for axis, field, value in (("radiusX", "type", "int"),
                                   ("radiusY", "min", -1),
                                   ("radiusX", "default", 4),
                                   ("radiusY", "max", 51),
                                   ("radiusX", "uniform", "radiusY"),
                                   ("radiusY", "zero", 1)):
            changed = copy.deepcopy(effect)
            changed["params"][axis][field] = value
            with self.subTest(axis=axis, field=field):
                with self.assertRaisesRegex(ValueError, "metadata contract mismatch"):
                    validate_blur_metadata(changed)

    def test_blur_source_interface_axis_and_loop_mutations_fail_closed(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import PROFILE
        for short in ("blurH", "blurV"):
            program, source_hash = self._profiled(short)
            main = program.functions[0]
            loop = next(item for item in main.body if item.kind == "for")
            radius_statement = next(
                item for item in main.body
                if item.kind == "decl" and item.expressions[0].symbol.name == "radius")
            radius = radius_statement.expressions[0]
            construct = radius.children[0]
            product = construct.children[0]
            swapped_product = dataclasses.replace(
                product, children=(product.children[1], product.children[0]))
            swapped_radius = dataclasses.replace(
                radius, children=(dataclasses.replace(
                    construct, children=(swapped_product,)),))
            swapped_statement = dataclasses.replace(
                radius_statement, expressions=(swapped_radius,))
            guard = next(item for item in main.body if item.kind == "if")
            changed_guard = dataclasses.replace(
                guard, expressions=(dataclasses.replace(
                    guard.expressions[0], operator="<"),))
            def replace_statement(target, replacement):
                return dataclasses.replace(
                    program, functions=(dataclasses.replace(
                        main, body=tuple(replacement if item is target else item
                                         for item in main.body)),))
            mutations = (
                dataclasses.replace(program, source=program.source + "\n"),
                dataclasses.replace(program, resources=dataclasses.replace(
                    program.resources,
                    uniforms=program.resources.uniforms + ("foreign",))),
                dataclasses.replace(program, functions=(dataclasses.replace(
                    main, body=main.body + (loop,)),)),
                replace_statement(radius_statement, swapped_statement),
                replace_statement(guard, changed_guard),
            )
            for ordinal, changed in enumerate(mutations):
                with self.subTest(short=short, mutation=ordinal):
                    with self.assertRaises((GeneratorError, ValueError)):
                        validate_capabilities(
                            changed, APPROVED_CAPABILITIES,
                            source_hash=source_hash,
                            runtime_loop_bound_profile=PROFILE)
                    with self.assertRaises((TypedEmissionError, ValueError)):
                        render_typed_cpp(
                            changed, changed.key, source_hash,
                            runtime_loop_bound_profile=PROFILE)

    def test_blur_seed_guard_and_precomputed_state_share_one_contract(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, authenticate_runtime_loop_bound,
        )
        for short in ("blurH", "blurV"):
            program, source_hash = self._profiled(short)
            contract = authenticate_runtime_loop_bound(program, source_hash, PROFILE)
            assert contract is not None
            self.assertEqual((contract.minimum, contract.uniform_maximum,
                              contract.default, contract.maximum), (0, 50, 5, 63))
            self.assertEqual(contract.seed.maximum, contract.maximum)
            malformed = dataclasses.replace(
                contract, seed=dataclasses.replace(contract.seed, maximum=64))
            with mock.patch(
                    "tools.glslcpp.frontend.runtime_loop_bound_profile."
                    "authenticate_runtime_loop_bound", return_value=malformed):
                with self.assertRaisesRegex(GeneratorError,
                                            "malformed authenticated"):
                    validate_capabilities(
                        program, APPROVED_CAPABILITIES,
                        source_hash=source_hash,
                        runtime_loop_bound_profile=PROFILE)
            with mock.patch(
                    "tools.glslcpp.emit_typed_cpp.authenticate_runtime_loop_bound",
                    return_value=malformed):
                with self.assertRaisesRegex(TypedEmissionError,
                                            "malformed authenticated"):
                    render_typed_cpp(
                        program, program.key, source_hash,
                        runtime_loop_bound_profile=PROFILE)

    def test_blur_rejects_every_unrelated_carrier(self) -> None:
        carrier_names = (
            "compatibility_transform", "custom_comparer_profile",
            "source_global_literal_int_profile", "gather_sorted_round_profile",
            "literal_vec3_lane_index_profile", "smooth_edge_luma_weights_profile",
            "perlin_scalar_uint_xor_profile", "bitwise_scalar_int_ops_profile",
            "rotate_mat2_return_profile", "focus_blur_borrowed_sampler_profile",
            "extrude_bvec2_relational_reduction_profile", "caustic_word_hash_profile",
            "edge_bvec3_contour_profile",
            "curl_vector_math_profile", "grade_luma_weights_profile",
            "grade_index_expression_profile", "derivative_admission_profile",
            "linear_srgb_lane_index_profile", "reflect_admission_profile",
            "posterize_round_profile", "as_u32_round_profile",
            "ceil_admission_profile", "waves_any_notequal_profile",
            "inout_vec3_swap_profile",
        )
        from tools.glslcpp.frontend.runtime_loop_bound_profile import PROFILE
        for short in ("blurH", "blurV"):
            program, source_hash = self._profiled(short)
            for name in carrier_names:
                kwargs = {"runtime_loop_bound_profile": PROFILE,
                          name: "foreign-profile"}
                with self.subTest(short=short, carrier=name):
                    with self.assertRaises((GeneratorError, ValueError)):
                        validate_capabilities(
                            program, APPROVED_CAPABILITIES,
                            source_hash=source_hash, **kwargs)
                    with self.assertRaises((TypedEmissionError, ValueError)):
                        render_typed_cpp(
                            program, program.key, source_hash, **kwargs)


class RuntimeLoopBoundStatsTests(unittest.TestCase):
    KEY = "filter/normalize:statsFinal"
    SOURCE = CORPUS / "sources/filter/normalize/statsFinal.glsl"

    def _unproved(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        return analyze_program(parse_program(source, self.KEY, {}), self.KEY)

    def _profiled(self):
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, apply_runtime_loop_bound,
        )
        program = self._unproved()
        source_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
        return apply_runtime_loop_bound(program, source_hash, PROFILE), source_hash

    def _assert_both_authorities_reject(self, program, source_hash: str,
                                        **extra) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import PROFILE
        kwargs = {"runtime_loop_bound_profile": PROFILE, **extra}
        with self.assertRaises((GeneratorError, ValueError)):
            validate_capabilities(program, APPROVED_CAPABILITIES,
                                  source_hash=source_hash, **kwargs)
        with self.assertRaises((TypedEmissionError, ValueError)):
            render_typed_cpp(program, self.KEY, source_hash, **kwargs)

    def test_exact_profile_attaches_lane_qualified_nested_proof(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, apply_runtime_loop_bound,
        )

        unproved = self._unproved()
        self.assertEqual((unproved.counted_loop_proof.loop_count,
                          unproved.counted_loop_proof.unproved_loop_count), (0, 2))
        source_hash = hashlib.sha256(unproved.raw_source.encode("utf-8")).hexdigest()
        program = apply_runtime_loop_bound(unproved, source_hash, PROFILE)
        proof = program.counted_loop_proof
        self.assertEqual((proof.loop_count, proof.unproved_loop_count), (2, 0))
        self.assertEqual((proof.max_effective_depth,
                          proof.max_lexical_product,
                          proof.entrypoint_charge), (2, 4096, 4160))
        validate_capabilities(
            program, APPROVED_CAPABILITIES, source_hash=source_hash,
            runtime_loop_bound_profile=PROFILE)
        rendered = render_typed_cpp(
            program, self.KEY, source_hash,
            runtime_loop_bound_profile=PROFILE)
        extraction = 'const auto& inputTex = bindings.texture("inputTex");'
        guard = """if (inputTex.width() < 1U || inputTex.width() > 64U ||
      inputTex.height() < 1U || inputTex.height() > 64U) {
    throw glsl::KernelBindingError("filter/normalize:statsFinal inputTex dimensions must be in [1,64]");
  }
  const std::size_t runtime_loop_width = inputTex.width();
  const std::size_t runtime_loop_height = inputTex.height();
  if (runtime_loop_width > 4096U / runtime_loop_height ||
      runtime_loop_width * runtime_loop_height > 4096U) {
    throw glsl::KernelBindingError("filter/normalize:statsFinal inputTex dimensions must be in [1,64]");
  }"""
        state = "const auto state = std::make_shared<typed_kernel::State>("
        contract = ('PassContract{ExactOutputExtent{1U, 1U, '
                    '"filter/normalize:statsFinal output dimensions must be 1x1"}}')
        self.assertEqual(rendered.count(extraction), 1)
        self.assertEqual(rendered.count(guard), 1)
        self.assertEqual(rendered.count(contract), 1)
        self.assertLess(rendered.index(extraction), rendered.index(guard))
        self.assertLess(rendered.index(guard), rendered.index(state))

    def test_stats_guard_literals_are_derived_from_authenticated_lane_seeds(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, authenticate_runtime_loop_bound,
        )

        program, source_hash = self._profiled()
        contract = authenticate_runtime_loop_bound(program, source_hash, PROFILE)
        assert contract is not None
        # This bypasses the frozen-profile validator deliberately: it isolates
        # whether emission consumes the authenticated record or duplicates its
        # current literal values.  Lane 0 is width and lane 1 is height.
        altered = dataclasses.replace(
            contract,
            lane_seeds=(
                dataclasses.replace(contract.lane_seeds[0], maximum=11),
                dataclasses.replace(contract.lane_seeds[1], maximum=7),
            ),
        )
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp.authenticate_runtime_loop_bound",
                return_value=altered), mock.patch(
                    "tools.glslcpp.emit_typed_cpp.validate_runtime_loop_contract",
                    side_effect=lambda value: value):
            rendered = render_typed_cpp(
                program, self.KEY, source_hash,
                runtime_loop_bound_profile=PROFILE)
        expected_guard = """if (inputTex.width() < 1U || inputTex.width() > 7U ||
      inputTex.height() < 1U || inputTex.height() > 11U) {
    throw glsl::KernelBindingError("filter/normalize:statsFinal inputTex dimensions must be in [1,64]");
  }
  const std::size_t runtime_loop_width = inputTex.width();
  const std::size_t runtime_loop_height = inputTex.height();
  if (runtime_loop_width > 77U / runtime_loop_height ||
      runtime_loop_width * runtime_loop_height > 77U) {
    throw glsl::KernelBindingError("filter/normalize:statsFinal inputTex dimensions must be in [1,64]");
  }"""
        self.assertEqual(rendered.count(expected_guard), 1)

    def test_stats_profile_is_required_only_at_admission(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, apply_runtime_loop_bound,
        )

        program = self._unproved()
        source_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(GeneratorError,
                                    "exact runtime-loop-bound carrier required"):
            validate_capabilities(program, APPROVED_CAPABILITIES,
                                  source_hash=source_hash)
        with self.assertRaisesRegex(TypedEmissionError,
                                    "exact profile carrier required"):
            render_typed_cpp(program, self.KEY, source_hash)
        self.assertEqual(program.counted_loop_proof.unproved_loop_count, 2)
        with self.assertRaisesRegex(ValueError, "exact profile carrier required"):
            apply_runtime_loop_bound(program, source_hash, None)

    def test_stats_source_interface_lane_loop_fetch_and_proof_mutations_reject(self) -> None:
        program, source_hash = self._profiled()
        main = program.functions[0]

        def mutate_expression(value, predicate, transform):
            children = tuple(mutate_expression(child, predicate, transform)
                             for child in value.children)
            current = dataclasses.replace(value, children=children)
            return transform(current) if predicate(current) else current

        def mutate_statement(value, predicate, transform):
            expressions = tuple(mutate_expression(item, predicate, transform)
                                for item in value.expressions)
            children = tuple(mutate_statement(child, predicate, transform)
                             for child in value.children)
            current = dataclasses.replace(value, expressions=expressions,
                                           children=children)
            return transform(current) if predicate(current) else current

        def with_main(transform):
            changed = dataclasses.replace(
                main, body=tuple(transform(item) for item in main.body))
            return dataclasses.replace(program, functions=(changed,))

        mutations = {
            "raw-source": dataclasses.replace(
                program, raw_source=program.raw_source + "\n"),
            "normalized-source": dataclasses.replace(
                program, source=program.source + "\n"),
            "interface": dataclasses.replace(
                program, resources=dataclasses.replace(
                    program.resources,
                    uniforms=program.resources.uniforms + ("foreign",))),
            "swizzle-lane": with_main(lambda statement: mutate_statement(
                statement,
                lambda item: item.kind == "swizzle" and item.member == "y",
                lambda item: dataclasses.replace(item, member="x"))),
            "loop-header": with_main(lambda statement: mutate_statement(
                statement,
                lambda item: item.kind == "for" and item.expressions[0].operator == "<",
                lambda item: dataclasses.replace(
                    item, expressions=(dataclasses.replace(
                        item.expressions[0], operator="<="), item.expressions[1])))),
            "fetch-lod": with_main(lambda statement: mutate_statement(
                statement,
                lambda item: item.kind == "literal" and item.span.start_line == 20
                and item.span.start_column == 60,
                lambda item: dataclasses.replace(item, literal_value=1))),
            "proof": dataclasses.replace(
                program, counted_loop_proof=dataclasses.replace(
                    program.counted_loop_proof, entrypoint_charge=4096)),
        }
        for name, changed in mutations.items():
            with self.subTest(mutation=name):
                self._assert_both_authorities_reject(changed, source_hash)

    def test_stats_lane_seed_and_pass_carriers_are_jointly_authenticated(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, authenticate_runtime_loop_bound,
        )
        program, source_hash = self._profiled()
        contract = authenticate_runtime_loop_bound(program, source_hash, PROFILE)
        assert contract is not None
        self.assertIsNone(contract.seed)
        self.assertEqual(tuple((seed.lane, seed.maximum)
                               for seed in contract.lane_seeds), ((1, 64), (0, 64)))
        self.assertEqual(contract.exact_output_extent, (1, 1))
        for malformed in (
                dataclasses.replace(
                    contract, lane_seeds=(dataclasses.replace(
                        contract.lane_seeds[0], maximum=65),
                        contract.lane_seeds[1])),
                dataclasses.replace(contract, exact_output_extent=(2, 1))):
            with mock.patch(
                    "tools.glslcpp.frontend.runtime_loop_bound_profile."
                    "authenticate_runtime_loop_bound", return_value=malformed):
                with self.assertRaisesRegex(GeneratorError,
                                            "malformed authenticated"):
                    validate_capabilities(
                        program, APPROVED_CAPABILITIES, source_hash=source_hash,
                        runtime_loop_bound_profile=PROFILE)
            with mock.patch(
                    "tools.glslcpp.emit_typed_cpp.authenticate_runtime_loop_bound",
                    return_value=malformed):
                with self.assertRaisesRegex(TypedEmissionError,
                                            "malformed authenticated"):
                    render_typed_cpp(
                        program, self.KEY, source_hash,
                        runtime_loop_bound_profile=PROFILE)

    def test_stats_duplicate_lane_seed_and_unrelated_carrier_reject(self) -> None:
        from tools.glslcpp.frontend.loop_proof import attach_counted_loop_proofs
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, authenticate_runtime_loop_bound,
        )
        program, source_hash = self._profiled()
        contract = authenticate_runtime_loop_bound(program, source_hash, PROFILE)
        assert contract is not None
        with self.assertRaisesRegex(ValueError, "duplicate runtime lane"):
            attach_counted_loop_proofs(
                program.functions, self.KEY,
                runtime_lane_bounds=(contract.lane_seeds[0],
                                     contract.lane_seeds[0]))
        self._assert_both_authorities_reject(
            program, source_hash, custom_comparer_profile="foreign-profile")


if __name__ == "__main__":
    unittest.main()
