from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib
import importlib.util
import json
import pathlib
import re
import tempfile
import types
import unittest
from unittest import mock

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tests.historical_cross_lane import historical_cross_lane


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "filter/glyphMap:glyphMap"
PROFILE = "glyph-map-nonnegative-int-shift-v1"
RAW_SHA256 = "853c3c15f300cf56ba3c11d5613cb91bfcb14b8b2f1be6bb5193e71397fdcea1"
SOURCE = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources/filter/glyphMap/glyphMap.glsl")
MODULE = "tools.glslcpp.frontend.glyph_map_nonnegative_int_shift_profile"


def _profile():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError("Glyph Map shift profile module is absent")
    return importlib.import_module(MODULE)


def _analyzed(raw: str | None = None, key: str = KEY):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(
        parse_program(raw, key, generate_typed_slice._defaults(ROOT, key)), key)


class GlyphMapNonnegativeIntShiftProfileTests(unittest.TestCase):
    def test_current_program_rejects_without_profile(self):
        program = _analyzed()
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    "unsupported binary operator &"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256)
        with self.assertRaisesRegex(emit_typed_cpp.TypedEmissionError,
                                    "unsupported binary operator &"):
            emit_typed_cpp.render_typed_cpp(
                program, KEY, RAW_SHA256, "glyph_probe", "bind_glyph_probe")

    def test_exact_profile_authenticates_candidate_owned_shift_and_mask(self):
        profile = _profile()
        program = _analyzed()
        proof = profile.authenticate_glyph_map_nonnegative_int_shift(
            program, RAW_SHA256, PROFILE)
        self.assertIs(proof.mask.children[0], proof.shift)
        self.assertEqual("&", proof.mask.operator)
        self.assertEqual(">>", proof.shift.operator)
        self.assertEqual("int", proof.mask.type.display())
        self.assertEqual("int", proof.shift.type.display())
        self.assertIs(profile.apply_glyph_map_nonnegative_int_shift(
            program, RAW_SHA256, PROFILE), program)

    def test_slice_schema_accepts_exact_single_glyph_profile_row(self):
        spec = copy.deepcopy(generate_typed_slice.load_slice(ROOT))
        spec["programs"] = [item for item in spec["programs"]
                            if item["program_key"] != KEY]
        spec["programs"].append({
            "defines": {},
            "glyph_map_nonnegative_int_shift_profile": PROFILE,
            "program_key": KEY,
        })
        spec["programs"].sort(key=lambda item: item["program_key"])
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            target = repository / "tools/glslcpp/typed_slice.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(spec), encoding="utf-8")
            loaded = generate_typed_slice.load_slice(repository)
        carriers = [item for item in loaded["programs"]
                    if "glyph_map_nonnegative_int_shift_profile" in item]
        self.assertEqual([{
            "defines": {},
            "glyph_map_nonnegative_int_shift_profile": PROFILE,
            "program_key": KEY,
        }], carriers)

    def test_authenticated_emission_preserves_canonical_self_assignment_as_noop(self):
        program = _analyzed()
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, RAW_SHA256, "glyph_probe", "bind_glyph_probe",
            glyph_map_nonnegative_int_shift_profile=PROFILE)
        self.assertNotIn("glyphIdx = glyphIdx;", rendered)
        self.assertIn("(void)glyphIdx;", rendered)

    def test_validator_and_emitter_admit_exact_profile_once(self):
        program = _analyzed()
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=RAW_SHA256,
            glyph_map_nonnegative_int_shift_profile=PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, RAW_SHA256, "glyph_probe", "bind_glyph_probe",
            glyph_map_nonnegative_int_shift_profile=PROFILE)
        self.assertEqual(1, rendered.count("glsl::detail::js_shift_right("))
        self.assertEqual(1, rendered.count("glsl::detail::js_bitwise_and("))
        self.assertNotIn(" >> ", rendered)

    def test_profile_rejects_carrier_key_tree_and_source_mutations(self):
        profile = _profile()
        program = _analyzed()
        candidates = [
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
        mutations = (
            ("const int GLYPH_COUNT = 16;", "const int GLYPH_COUNT = 15;"),
            ("const int GLYPH_COUNT = 16;",
             "const int EXTRA = 1;\nconst int GLYPH_COUNT = 16;"),
            ("const int GLYPH_COUNT = 16;",
             "#define EXTRA 1\nconst int GLYPH_COUNT = 16;"),
            ("(row >> (4 - x)) & 1", "(row >> (4 - x)) & 3"),
            ("row >> (4 - x)", "row >> x"),
            ("int bit = (row >> (4 - x)) & 1;",
             "int extra = row >> 1;\n    int bit = (row >> (4 - x)) & 1;"),
            ("return float(bit);", "return float(bit + 1);"),
            ("int row = 0;", "int row = 1;"),
            ("if (y == 5) row = 4;", "if (y == 5) row = 9;"),
            ("gx = clamp(gx, 0, 4);", "gx = clamp(gx, 0, 3);"),
            ("glyphPixel(glyphIdx, gx, gy)", "glyphPixel(glyphIdx, gy, gx)"),
        )
        for anchor, replacement in mutations:
            self.assertEqual(1, raw.count(anchor), anchor)
            mutated = raw.replace(anchor, replacement)
            candidates.append((
                _analyzed(mutated), hashlib.sha256(mutated.encode()).hexdigest(),
                PROFILE))
        for index, (candidate, source_hash, carrier) in enumerate(candidates):
            with self.subTest(index=index), self.assertRaises(ValueError):
                profile.authenticate_glyph_map_nonnegative_int_shift(
                    candidate, source_hash, carrier)

    def test_both_authorities_fail_closed_for_wrong_carrier_foreign_key_and_collision(self):
        program = _analyzed()
        for carrier in (None, "wrong"):
            with self.subTest(authority="validator", carrier=carrier), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=RAW_SHA256,
                    glyph_map_nonnegative_int_shift_profile=carrier)
            with self.subTest(authority="emitter", carrier=carrier), \
                    self.assertRaises(emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, RAW_SHA256, "glyph_probe", "bind_glyph_probe",
                    glyph_map_nonnegative_int_shift_profile=carrier)

        foreign = dataclasses.replace(program, key="filter/other:other")
        for authority in ("validator", "emitter"):
            with self.subTest(authority=authority), self.assertRaises(
                    generate_typed_slice.GeneratorError if authority == "validator"
                    else emit_typed_cpp.TypedEmissionError):
                if authority == "validator":
                    generate_typed_slice.validate_capabilities(
                        foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=RAW_SHA256,
                        glyph_map_nonnegative_int_shift_profile=PROFILE)
                else:
                    emit_typed_cpp.render_typed_cpp(
                        foreign, foreign.key, RAW_SHA256, "glyph_probe",
                        "bind_glyph_probe",
                        glyph_map_nonnegative_int_shift_profile=PROFILE)

        for authority in ("validator", "emitter"):
            with self.subTest(authority=authority), self.assertRaises(
                    generate_typed_slice.GeneratorError if authority == "validator"
                    else emit_typed_cpp.TypedEmissionError):
                if authority == "validator":
                    generate_typed_slice.validate_capabilities(
                        program, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=RAW_SHA256,
                        glyph_map_nonnegative_int_shift_profile=PROFILE,
                        runtime_loop_bound_profile="runtime-loop-bound-v1")
                else:
                    emit_typed_cpp.render_typed_cpp(
                        program, KEY, RAW_SHA256, "glyph_probe",
                        "bind_glyph_probe",
                        glyph_map_nonnegative_int_shift_profile=PROFILE,
                        runtime_loop_bound_profile="runtime-loop-bound-v1")

    def test_both_authorities_reject_cross_candidate_and_copied_proof_nodes(self):
        profile = _profile()
        program = _analyzed()
        separate = _analyzed()
        cross_candidate = profile.authenticate_glyph_map_nonnegative_int_shift(
            separate, RAW_SHA256, PROFILE)
        copied_nodes = dataclasses.replace(
            profile.authenticate_glyph_map_nonnegative_int_shift(
                program, RAW_SHA256, PROFILE),
            mask=copy.deepcopy(cross_candidate.mask),
            shift=copy.deepcopy(cross_candidate.shift),
            _candidate=program)
        kwargs = {
            "source_hash": RAW_SHA256,
            "glyph_map_nonnegative_int_shift_profile": PROFILE,
        }
        for name, proof in (("cross-candidate", cross_candidate),
                            ("copied-nodes", copied_nodes)):
            with self.subTest(name=name, authority="validator"), mock.patch.object(
                    generate_typed_slice,
                    "authenticate_glyph_map_nonnegative_int_shift",
                    return_value=proof), self.assertRaises(
                        generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES, **kwargs)
            with self.subTest(name=name, authority="emitter"), mock.patch(
                    "tools.glslcpp.emit_typed_cpp."
                    "authenticate_glyph_map_nonnegative_int_shift",
                    return_value=proof), self.assertRaises(
                        emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, RAW_SHA256, "glyph_probe", "bind_glyph_probe",
                    glyph_map_nonnegative_int_shift_profile=PROFILE)

    def test_both_authorities_reject_forged_site_order_duplicate_omission_and_parent(self):
        profile = _profile()
        program = _analyzed()
        proof = profile.authenticate_glyph_map_nonnegative_int_shift(
            program, RAW_SHA256, PROFILE)
        copied_shift = copy.deepcopy(proof.shift)
        forged = {
            "reordered": types.SimpleNamespace(
                _candidate=program, sites=(proof.shift, proof.mask),
                mask=proof.shift, shift=proof.mask,
                self_assignment=proof.self_assignment),
            "duplicated": types.SimpleNamespace(
                _candidate=program, sites=(proof.mask, proof.mask),
                mask=proof.mask, shift=proof.mask,
                self_assignment=proof.self_assignment),
            "omitted": types.SimpleNamespace(
                _candidate=program, sites=(proof.mask,),
                mask=proof.mask, shift=None,
                self_assignment=proof.self_assignment),
            "wrong-parent": types.SimpleNamespace(
                _candidate=program, sites=(proof.mask, copied_shift),
                mask=proof.mask, shift=copied_shift,
                self_assignment=proof.self_assignment),
        }
        kwargs = {
            "source_hash": RAW_SHA256,
            "glyph_map_nonnegative_int_shift_profile": PROFILE,
        }
        for name, candidate in forged.items():
            with self.subTest(name=name, authority="validator"), mock.patch.object(
                    generate_typed_slice,
                    "authenticate_glyph_map_nonnegative_int_shift",
                    return_value=candidate), self.assertRaises(
                        generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES, **kwargs)
            with self.subTest(name=name, authority="emitter"), mock.patch(
                    "tools.glslcpp.emit_typed_cpp."
                    "authenticate_glyph_map_nonnegative_int_shift",
                    return_value=candidate), self.assertRaises(
                        emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, RAW_SHA256, "glyph_probe", "bind_glyph_probe",
                    glyph_map_nonnegative_int_shift_profile=PROFILE)

    def test_slice_schema_rejects_every_noncanonical_glyph_carrier(self):
        exact = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text(
            encoding="utf-8"))
        row = next(item for item in exact["programs"]
                   if item["program_key"] == KEY)
        self.assertEqual({
            "defines": {},
            "glyph_map_nonnegative_int_shift_profile": PROFILE,
            "program_key": KEY,
        }, row)
        mutations = {}
        wrong = copy.deepcopy(exact)
        next(item for item in wrong["programs"]
             if item["program_key"] == KEY)[
                 "glyph_map_nonnegative_int_shift_profile"] = "wrong"
        mutations["wrong-profile"] = wrong
        missing = copy.deepcopy(exact)
        del next(item for item in missing["programs"]
                 if item["program_key"] == KEY)[
                     "glyph_map_nonnegative_int_shift_profile"]
        mutations["missing-profile"] = missing
        extra = copy.deepcopy(exact)
        next(item for item in extra["programs"]
             if item["program_key"] == KEY)["extra"] = True
        mutations["extra-field"] = extra
        duplicate = copy.deepcopy(exact)
        duplicate["programs"].append(copy.deepcopy(row))
        duplicate["programs"].sort(key=lambda item: item["program_key"])
        mutations["duplicate-row"] = duplicate
        foreign = copy.deepcopy(exact)
        next(item for item in foreign["programs"]
             if item["program_key"] == "synth/gradient:gradient")[
                 "glyph_map_nonnegative_int_shift_profile"] = PROFILE
        mutations["foreign-key"] = foreign
        collision = copy.deepcopy(exact)
        next(item for item in collision["programs"]
             if item["program_key"] == KEY)[
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

    def test_global_vocabularies_remain_frozen(self):
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

    def test_glyph_map_is_exact_single_program_delta_from_scanline_177(self):
        # MILESTONE reconstruction of Glyph-178 over Scanline-177: everything
        # that landed after Glyph Map is excluded below, and cellRefract joins
        # the exclusion set so the frozen reconstruction stays exactly as-is.
        # Grime is the established exception: it was already present when
        # these artifact pins were recorded, so subtracting it would describe
        # a different projection and invalidate the frozen hashes.
        current_spec = copy.deepcopy(generate_typed_slice.load_slice(ROOT))
        with historical_cross_lane(current_spec):
            current_spec["programs"] = [
                item for item in current_spec["programs"]
                if item["program_key"] not in {
                    "classicNoisedeck/moodscape:moodscape",
                    "filter/emboss:emboss", "filter/edge:edge",
                    "classicNoisedeck/glitch:glitch",
                    "classicNoisedeck/shapeMixer:shapeMixer",
                    "classicNoisedeck/shapes:shapes",
                    "synth/shape:shape",
                    "filter/normalMap:normalMap",
                    "classicNoisedeck/cellRefract:cellRefract",
                    "mixer/distortion:distortion",
                    "classicNoisedeck/kaleido:kaleido",
                    "classicNoisedeck/effects:effects",
                     "filter/wobble:wobble",
                    "filter/parallax:parallax",
                     "filter/lightLeak:lightLeak",
                     "synth/newton:newton",
                     "synth/noise:noise",
                     "synth/mandelbrot:mandelbrot",
                     "classicNoisedeck/fractal:fractal",
                     "synth/remap:remap", "synth/testPattern:testPattern",
                     "classicNoisedeck/bitEffects:bitEffects",
                     "classicNoisedeck/colorLab:colorLab",
                     "classicNoisedeck/noise:noise",
                     "filter/historicPalette:historicPalette", "filter/median:median",
                     "filter/osd:osd", "filter/palette:palette",
                     "filter/spookyTicker:spookyTicker", "filter/texture:texture"}]
            prior_spec = copy.deepcopy(current_spec)
            prior_spec["programs"] = [
                item for item in prior_spec["programs"]
                if item["program_key"] != KEY]
            with mock.patch.object(generate_typed_slice, "load_slice",
                                   return_value=current_spec):
                current = generate_typed_slice.generate_outputs(ROOT)
            with mock.patch.object(generate_typed_slice, "load_slice",
                                   return_value=prior_spec):
                prior = generate_typed_slice.generate_outputs(ROOT)
            current["include/noisemaker/generated/catalog.hpp"] = (
                generate_typed_slice.render_catalog_header(current_spec))
            prior["include/noisemaker/generated/catalog.hpp"] = (
                generate_typed_slice.render_catalog_header(prior_spec))
        expected_current = {
            "src/typed_generated/typed_slice.cpp":
                "13911a23e95d6f3a6e18e74043bc8afa3dd3a852854dff884290edc78d881bce",
            "src/typed_generated/typed_manifest.json":
                "28426b635570f1fe6d87396ca72244187cc514568fc19d409a158c34663c1a6c",
            "include/noisemaker/generated/catalog.hpp":
                "5b29f9b683ae0d365c9ede4e6011ebcc854904b6447c6bf6aca3a60acdc7cbcb",
        }
        expected_prior = {
            "src/typed_generated/typed_slice.cpp":
                "89464e137c638d0c8092a508bc7b6d20635cc940ee635e37d75d9b79f79aacfe",
            "src/typed_generated/typed_manifest.json":
                "85e913831cc0ec35e63156d6c34f86a42f2d15991ddfae0db9e6bd6970b0a6b5",
            "include/noisemaker/generated/catalog.hpp":
                "82012db9635dc83725aad87bf240cfecc619dbc1f56f02be069a11a5be36f88d",
        }
        for label, outputs, expected in (
                ("glyph178", current, expected_current),
                ("scanline177", prior, expected_prior)):
            for path, digest in expected.items():
                with self.subTest(state=label, artifact=path):
                    self.assertEqual(
                        digest, hashlib.sha256(outputs[path]).hexdigest())

        marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")

        def blocks(payload: bytes):
            source = payload.decode()
            starts = list(marker.finditer(source))
            catalog = source.index(
                "\nnamespace {\nconstexpr std::array<KernelFactory")
            return {
                match.group(1): source[
                    match.start():(starts[index + 1].start()
                                   if index + 1 < len(starts) else catalog)]
                for index, match in enumerate(starts)
            }

        current_blocks = blocks(current["src/typed_generated/typed_slice.cpp"])
        prior_blocks = blocks(prior["src/typed_generated/typed_slice.cpp"])
        self.assertEqual((179, 178),
                         (len(current_blocks), len(prior_blocks)))
        self.assertEqual({KEY}, set(current_blocks) - set(prior_blocks))
        ordinal = re.compile(r"typed_[0-9]+")
        for key, block in prior_blocks.items():
            with self.subTest(unaffected_program=key):
                self.assertEqual(
                    ordinal.sub("typed_SENTINEL", block),
                    ordinal.sub("typed_SENTINEL", current_blocks[key]))

        current_manifest = json.loads(
            current["src/typed_generated/typed_manifest.json"])
        prior_manifest = json.loads(
            prior["src/typed_generated/typed_manifest.json"])
        current_rows = {item["program_key"]: item
                        for item in current_manifest["programs"]}
        prior_rows = {item["program_key"]: item
                      for item in prior_manifest["programs"]}
        self.assertEqual((179, 178),
                         (len(current_rows), len(prior_rows)))
        self.assertEqual({KEY}, set(current_rows) - set(prior_rows))
        self.assertEqual(PROFILE, current_rows[KEY][
            "glyph_map_nonnegative_int_shift_profile"])


if __name__ == "__main__":
    unittest.main()
