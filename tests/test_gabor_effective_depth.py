from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.gabor_effective_depth_profile import (
    GABOR_KEY,
    PROFILE,
    GaborEffectiveDepthContract,
    authenticate_gabor_effective_depth,
    validate_gabor_effective_depth_contract,
    validate_gabor_metadata,
)
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import loop_proof
from tools.glslcpp.frontend.typed_ir import PreprocessorDefine


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
RAW_SHA256 = "91665da2d584d6d88b38e8ba314dfc0b546dd49d29aa161f5d66aecf6bf67bf5"


def _raw_source():
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    entry = next(item for item in manifest["programs"]
                 if item["program_key"] == GABOR_KEY)
    return (CORPUS / entry["source"]).read_text(encoding="utf-8")


def _analyzed(raw=None, key=GABOR_KEY, defines=None):
    raw = _raw_source() if raw is None else raw
    defines = {} if defines is None else defines
    return analyze_program(parse_program(raw, key, defines), key)


def _walk(statements):
    for statement in statements:
        yield statement
        yield from _walk(statement.children)


class GaborEffectiveDepthProfileTests(unittest.TestCase):
    def test_exact_candidate_returns_candidate_owned_depth_four_contract(self):
        program = _analyzed()
        self.assertEqual(RAW_SHA256,
                         hashlib.sha256(program.raw_source.encode()).hexdigest())

        contract = authenticate_gabor_effective_depth(
            program, RAW_SHA256, PROFILE)
        self.assertIs(contract,
                      validate_gabor_effective_depth_contract(contract))
        self.assertEqual(GABOR_KEY, contract.key)
        self.assertEqual(4, contract.maximum_effective_depth)
        self.assertIs(program.counted_loop_proof, contract.program_proof)
        self.assertEqual((4, 0, 4, 72, 425, True), (
            contract.program_proof.loop_count,
            contract.program_proof.unproved_loop_count,
            contract.program_proof.max_effective_depth,
            contract.program_proof.max_lexical_product,
            contract.program_proof.entrypoint_charge,
            contract.program_proof.call_graph_acyclic,
        ))

        candidate_loops = tuple(
            statement
            for function in program.functions
            for statement in _walk(function.body)
            if statement.kind in {"for", "while", "dowhile"}
        )
        self.assertEqual(4, len(contract.loops))
        self.assertTrue(all(actual is expected for actual, expected
                            in zip(contract.loops, candidate_loops)))
        self.assertEqual(
            (program.functions[0], program.functions[0],
             program.functions[0], program.functions[1]),
            contract.owners,
        )

    def test_profile_key_source_and_define_contract_fail_closed(self):
        program = _analyzed()
        for profile in (None, "gabor-effective-depth-4-v0", ""):
            with self.subTest(profile=profile), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                authenticate_gabor_effective_depth(program, RAW_SHA256, profile)
        with self.assertRaisesRegex(ValueError, "profile on foreign key"):
            authenticate_gabor_effective_depth(
                dataclasses.replace(program, key="synth/julia:julia"),
                RAW_SHA256, PROFILE)
        with self.assertRaisesRegex(ValueError, "exact caller source hash"):
            authenticate_gabor_effective_depth(program, "0" * 64, PROFILE)
        comment_drift = dataclasses.replace(
            program,
            raw_source=program.raw_source.replace(
                "Gabor noise — sparse convolution",
                "Gabor noise - sparse convolution"),
        )
        with self.assertRaisesRegex(ValueError, "source, define"):
            authenticate_gabor_effective_depth(comment_drift, RAW_SHA256, PROFILE)
        defined = dataclasses.replace(
            program,
            preprocessor_defines=(PreprocessorDefine("EXTRA", "int", "1"),),
        )
        with self.assertRaisesRegex(ValueError, "source, define"):
            authenticate_gabor_effective_depth(defined, RAW_SHA256, PROFILE)

    def test_genuinely_analyzed_foreign_program_rejects_both_authorities(self):
        source = ("out vec4 fragColor;\n"
                  "void main() { fragColor = vec4(0.25); }\n")
        key = "synth/foreign:foreign"
        source_hash = hashlib.sha256(source.encode()).hexdigest()
        foreign = _analyzed(source, key=key)
        self.assertEqual(key, foreign.key)

        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "Gabor effective-depth carrier on foreign key"):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                gabor_effective_depth_profile=PROFILE)
        with self.assertRaisesRegex(
                TypedEmissionError,
                "Gabor effective-depth carrier on foreign key"):
            render_typed_cpp(
                foreign, foreign.key, source_hash,
                gabor_effective_depth_profile=PROFILE)

    def test_oracle_source_mutations_are_rejected_with_their_own_hashes(self):
        raw = _raw_source()
        mutations = {
            "inner-bound-nine": (
                "for (int k = 0; k < 8; k++) {",
                "for (int k = 0; k < 9; k++) {"),
            "outer-bound-six": (
                "for (int i = 0; i < 5; i++) {",
                "for (int i = 0; i < 6; i++) {"),
            "neighbor-order-swap": (
                "for (int dy = -1; dy <= 1; dy++) {\n"
                "        for (int dx = -1; dx <= 1; dx++) {",
                "for (int dx = -1; dx <= 1; dx++) {\n"
                "        for (int dy = -1; dy <= 1; dy++) {"),
            "remove-density-break": (
                "if (k >= impulses) break;", "if (false) break;"),
            "remove-octave-break": (
                "if (i >= oct) break;", "if (false) break;"),
        }
        for name, (anchor, replacement) in mutations.items():
            with self.subTest(name=name):
                self.assertEqual(1, raw.count(anchor))
                mutated_raw = raw.replace(anchor, replacement)
                candidate = _analyzed(mutated_raw)
                candidate_hash = hashlib.sha256(mutated_raw.encode()).hexdigest()
                with self.assertRaises(ValueError):
                    authenticate_gabor_effective_depth(
                        candidate, candidate_hash, PROFILE)

    def test_complete_typed_candidate_inventory_is_authenticated(self):
        program = _analyzed()
        mutations = {
            "function-order": dataclasses.replace(
                program, functions=tuple(reversed(program.functions))),
            "function-id": dataclasses.replace(
                program, functions=(dataclasses.replace(
                    program.functions[0], signature=dataclasses.replace(
                        program.functions[0].signature, id=999)),
                    *program.functions[1:])),
            "declaration": dataclasses.replace(
                program, declarations=program.declarations[:-1]),
            "resource": dataclasses.replace(
                program, resources=dataclasses.replace(
                    program.resources,
                    uniforms=program.resources.uniforms[:-1])),
            "struct": dataclasses.replace(program, structs=(object(),)),
            "uniform-block": dataclasses.replace(
                program, uniform_blocks=(object(),)),
            "foreign-proof": dataclasses.replace(
                program, fixed_nine_table_proof=object()),
            "program-proof": dataclasses.replace(
                program, counted_loop_proof=dataclasses.replace(
                    program.counted_loop_proof, entrypoint_charge=426)),
        }
        first_loop = next(statement for statement in _walk(program.functions[0].body)
                          if statement.kind == "for")

        def replace_statement(statement):
            if statement is first_loop:
                return dataclasses.replace(
                    statement,
                    loop_proof=dataclasses.replace(
                        statement.loop_proof, effective_depth=3))
            return dataclasses.replace(
                statement,
                children=tuple(replace_statement(child)
                               for child in statement.children))

        mutations["loop-proof"] = dataclasses.replace(
            program, functions=(dataclasses.replace(
                program.functions[0],
                body=tuple(replace_statement(statement)
                           for statement in program.functions[0].body)),
                *program.functions[1:]))
        for name, candidate in mutations.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                authenticate_gabor_effective_depth(
                    candidate, RAW_SHA256, PROFILE)

    def test_contract_validator_rejects_forgery_and_cross_candidate_objects(self):
        program = _analyzed()
        contract = authenticate_gabor_effective_depth(
            program, RAW_SHA256, PROFILE)
        separate = authenticate_gabor_effective_depth(
            _analyzed(), RAW_SHA256, PROFILE)
        forged = {
            "key": dataclasses.replace(contract, key="synth/other:other"),
            "maximum-three": dataclasses.replace(
                contract, maximum_effective_depth=3),
            "maximum-five": dataclasses.replace(
                contract, maximum_effective_depth=5),
            "copied-proof": dataclasses.replace(
                contract, program_proof=dataclasses.replace(
                    contract.program_proof)),
            "missing-owner": dataclasses.replace(
                contract, owners=contract.owners[:-1]),
            "reordered-owner": dataclasses.replace(
                contract, owners=tuple(reversed(contract.owners))),
            "missing-loop": dataclasses.replace(
                contract, loops=contract.loops[:-1]),
            "reordered-loop": dataclasses.replace(
                contract, loops=tuple(reversed(contract.loops))),
            "cross-candidate": GaborEffectiveDepthContract(
                contract.key, contract.maximum_effective_depth,
                contract.program_proof, separate.owners, separate.loops,
                contract._candidate),
        }
        for name, candidate in forged.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                    ValueError, "malformed authenticated"):
                validate_gabor_effective_depth_contract(candidate)

    def test_complete_metadata_record_is_exact(self):
        metadata = json.loads((CORPUS / "metadata.json").read_text(encoding="utf-8"))
        effect = metadata["effects"]["synth/gabor"]
        validate_gabor_metadata(effect)
        mutations = []
        for parameter in effect["params"]:
            changed = copy.deepcopy(effect)
            changed["params"][parameter]["default"] = -999
            mutations.append((f"{parameter}-default", changed))
        for name, value in (("type", "filter"), ("func", "other"),
                            ("namespace", "other"), ("passes", [])):
            changed = copy.deepcopy(effect)
            changed[name] = value
            mutations.append((name, changed))
        for name, candidate in mutations:
            with self.subTest(name=name), self.assertRaisesRegex(
                    ValueError, "metadata contract mismatch"):
                validate_gabor_metadata(candidate)

    def test_only_profiled_exact_gabor_passes_both_authorities(self):
        program = _analyzed()
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                r"synth/gabor:gabor:54:13: unsupported counted-for safety charge"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256)
        with self.assertRaisesRegex(
                TypedEmissionError,
                r"synth/gabor:gabor:54:13: unsupported counted-for safety charge"):
            render_typed_cpp(program, GABOR_KEY, RAW_SHA256)

        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=RAW_SHA256,
            gabor_effective_depth_profile=PROFILE)
        emitted = render_typed_cpp(
            program, GABOR_KEY, RAW_SHA256,
            gabor_effective_depth_profile=PROFILE)
        self.assertIn("// Typed IR program: synth/gabor:gabor", emitted)

    def test_profile_is_foreign_closed_collision_closed_and_does_not_widen_limits(self):
        program = _analyzed()
        foreign = dataclasses.replace(program, key="synth/foreign:foreign")
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError, "carrier on foreign key"):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256,
                gabor_effective_depth_profile=PROFILE)
        with self.assertRaisesRegex(TypedEmissionError, "carrier on foreign key"):
            render_typed_cpp(
                foreign, foreign.key, RAW_SHA256,
                gabor_effective_depth_profile=PROFILE)
        for authority in ("validator", "emitter"):
            with self.subTest(authority=authority), self.assertRaisesRegex(
                    (generate_typed_slice.GeneratorError
                     if authority == "validator" else TypedEmissionError),
                    r"(?:profile|carrier) on foreign key|profile metadata mismatch"):
                if authority == "validator":
                    generate_typed_slice.validate_capabilities(
                        program, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=RAW_SHA256,
                        gabor_effective_depth_profile=PROFILE,
                        runtime_loop_bound_profile="runtime-loop-bound-v1")
                else:
                    render_typed_cpp(
                        program, GABOR_KEY, RAW_SHA256,
                        gabor_effective_depth_profile=PROFILE,
                        runtime_loop_bound_profile="runtime-loop-bound-v1")

        self.assertEqual(512, loop_proof.COUNTED_FOR_V1_MAX_TRIP_COUNT)
        self.assertEqual(262144, loop_proof.COUNTED_FOR_V1_MAX_LEXICAL_PRODUCT)
        self.assertEqual(262656, loop_proof.COUNTED_FOR_V1_MAX_ENTRYPOINT_CHARGE)
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "unsupported counted-for safety charge"):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256)
        with self.assertRaisesRegex(
                TypedEmissionError, "unsupported counted-for safety charge"):
            render_typed_cpp(foreign, foreign.key, RAW_SHA256)

    def test_both_authorities_reject_cross_candidate_authenticator_results(self):
        program = _analyzed()
        other_program = _analyzed()
        other_contract = authenticate_gabor_effective_depth(
            other_program, RAW_SHA256, PROFILE)
        with mock.patch.object(
                generate_typed_slice, "authenticate_gabor_effective_depth",
                return_value=other_contract):
            with self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    "candidate identity mismatch"):
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=RAW_SHA256,
                    gabor_effective_depth_profile=PROFILE)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp.authenticate_gabor_effective_depth",
                return_value=other_contract):
            with self.assertRaisesRegex(
                    TypedEmissionError, "candidate identity mismatch"):
                render_typed_cpp(
                    program, GABOR_KEY, RAW_SHA256,
                    gabor_effective_depth_profile=PROFILE)

    def test_each_authority_authenticates_independently(self):
        program = _analyzed()
        clean_contract = authenticate_gabor_effective_depth(
            program, RAW_SHA256, PROFILE)
        mutated = dataclasses.replace(
            program, raw_source=program.raw_source + "\n")
        with mock.patch.object(
                generate_typed_slice, "authenticate_gabor_effective_depth",
                return_value=clean_contract):
            with self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    mutated, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=RAW_SHA256,
                    gabor_effective_depth_profile=PROFILE)
            with self.assertRaises(TypedEmissionError):
                render_typed_cpp(
                    mutated, GABOR_KEY, RAW_SHA256,
                    gabor_effective_depth_profile=PROFILE)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp.authenticate_gabor_effective_depth",
                return_value=clean_contract):
            with self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    mutated, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=RAW_SHA256,
                    gabor_effective_depth_profile=PROFILE)
            with self.assertRaises(TypedEmissionError):
                render_typed_cpp(
                    mutated, GABOR_KEY, RAW_SHA256,
                    gabor_effective_depth_profile=PROFILE)

    def test_slice_schema_admits_only_the_exact_gabor_row(self):
        spec_path = ROOT / "tools/glslcpp/typed_slice.json"
        exact = json.loads(spec_path.read_text(encoding="utf-8"))
        loaded = generate_typed_slice.load_slice(ROOT)
        row = next(item for item in loaded["programs"]
                   if item["program_key"] == GABOR_KEY)
        self.assertEqual({
            "defines": {},
            "gabor_effective_depth_profile": PROFILE,
            "program_key": GABOR_KEY,
        }, row)

        mutations = {}
        wrong = copy.deepcopy(exact)
        next(item for item in wrong["programs"]
             if item["program_key"] == GABOR_KEY)[
                 "gabor_effective_depth_profile"] = "wrong"
        mutations["wrong-profile"] = wrong
        missing = copy.deepcopy(exact)
        del next(item for item in missing["programs"]
                 if item["program_key"] == GABOR_KEY)[
                     "gabor_effective_depth_profile"]
        mutations["missing-profile"] = missing
        extra = copy.deepcopy(exact)
        next(item for item in extra["programs"]
             if item["program_key"] == GABOR_KEY)["extra"] = True
        mutations["extra-field"] = extra
        duplicate = copy.deepcopy(exact)
        duplicate["programs"].append(copy.deepcopy(row))
        duplicate["programs"].sort(key=lambda item: item["program_key"])
        mutations["duplicate-row"] = duplicate
        foreign = copy.deepcopy(exact)
        next(item for item in foreign["programs"]
             if item["program_key"] == "synth/gradient:gradient")[
                 "gabor_effective_depth_profile"] = PROFILE
        mutations["foreign-key"] = foreign
        collision = copy.deepcopy(exact)
        next(item for item in collision["programs"]
             if item["program_key"] == GABOR_KEY)[
                 "runtime_loop_bound_profile"] = "runtime-loop-bound-v1"
        mutations["carrier-collision"] = collision

        for name, candidate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                repository = pathlib.Path(temp)
                target = repository / "tools/glslcpp/typed_slice.json"
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.load_slice(repository)


if __name__ == "__main__":
    unittest.main()
