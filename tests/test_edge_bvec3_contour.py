from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib
import importlib.util
import json
import pathlib
import tempfile
import types
import unittest
from unittest import mock

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tests.historical_cross_lane import historical_cross_lane


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "filter/edge:edge"
PROFILE = "edge-bvec3-contour-v1"
RAW_SHA256 = "841f9f547d06aace8444953f401009abd02758f9dff271097b2799424c1db5d0"
SOURCE = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources/filter/edge/edge.glsl")
MODULE = "tools.glslcpp.frontend.edge_bvec3_contour_profile"


def _profile():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError("Edge bvec3 contour profile module is absent")
    return importlib.import_module(MODULE)


def _analyzed(raw: str | None = None, key: str = KEY):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(
        parse_program(raw, key, generate_typed_slice._defaults(ROOT, key)), key)


class EdgeBvec3ContourProfileTests(unittest.TestCase):
    def test_current_program_requires_exact_profile_at_both_boundaries(self):
        program = _analyzed()
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                r"filter/edge:edge:.*exact Edge bvec3 contour profile carrier required"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256)
        with self.assertRaisesRegex(
                emit_typed_cpp.TypedEmissionError,
                r"filter/edge:edge:.*exact Edge bvec3 contour profile carrier required"):
            emit_typed_cpp.render_typed_cpp(
                program, KEY, RAW_SHA256, "edge_probe", "bind_edge_probe")

    def test_exact_profile_returns_candidate_owned_complete_closure(self):
        profile = _profile()
        program = _analyzed()
        proof = profile.authenticate_edge_bvec3_contour(
            program, RAW_SHA256, PROFILE)
        self.assertIs(proof._candidate, program)
        self.assertIs(profile.apply_edge_bvec3_contour(
            program, RAW_SHA256, PROFILE), program)
        self.assertEqual((12, 2, 2, 6, 6, 22), (
            len(proof.bvec_nodes), len(proof.relationals),
            len(proof.declarations), len(proof.id_reads),
            len(proof.swizzles), len(proof.consumed_objects)))
        self.assertEqual(("greaterThanEqual", "lessThan"),
                         tuple(item.callee for item in proof.relationals))
        self.assertEqual((40, 41),
                         tuple(item.symbol_id for item in proof.declarations))
        self.assertIs(proof.constructor, proof.declarations[1].children[0])
        self.assertEqual(
            ("73:11-74:69", "73:26-74:69", "73:38-73:76",
             "74:39-74:69", "75:11-85:6", "75:22-85:6",
             "76:9-76:21", "79:9-79:21", "82:9-82:21",
             "86:17-86:25", "86:41-86:49", "86:65-86:73"),
            tuple(profile._span(item) for item in proof.bvec_nodes))
        self.assertEqual(
            (("r", 40), ("g", 40), ("b", 40),
             ("r", 41), ("g", 41), ("b", 41)),
            tuple((item.member, item.children[0].symbol_id)
                  for item in proof.swizzles))

    def test_profile_admits_exact_validator_and_emitter_shape_only(self):
        profile = _profile()
        program = _analyzed()
        splat = profile.authenticate_edge_center_splat(
            program, RAW_SHA256, PROFILE)
        self.assertIs(splat._candidate, program)
        self.assertEqual(12, len(splat.consumed_objects))
        self.assertIs(splat.statement, splat.statement_parent_chain[-1])
        self.assertEqual(
            (("if", "106:5-138:6"), ("block", "109:12-138:6"),
             ("if", "134:9-136:10"), ("block", "134:22-136:10"),
             ("expr", "135:13-135:58")),
            tuple((item.kind, profile._span(item))
                  for item in splat.statement_parent_chain))
        self.assertEqual(("135:13-135:58", "135:13-135:57",
                          "135:28-135:57", "135:33-135:56"),
                         tuple(profile._span(item) for item in (
                             splat.statement, splat.assignment,
                             splat.constructor, splat.dot)))
        self.assertEqual((59, 59, 14), (
            splat.target.symbol_id, splat.dot_target.symbol_id,
            splat.luma.symbol_id))
        generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=RAW_SHA256,
            edge_bvec3_contour_profile=PROFILE)
        rendered = emit_typed_cpp.render_typed_cpp(
            program, KEY, RAW_SHA256, "edge_probe", "bind_edge_probe",
            edge_bvec3_contour_profile=PROFILE)
        self.assertEqual(2, rendered.count("glsl::BVec3 "))
        self.assertEqual(1, rendered.count("glsl::BVec3("))
        self.assertEqual(1, rendered.count("glsl::greaterThanEqual("))
        self.assertEqual(1, rendered.count("glsl::lessThan("))
        self.assertEqual(6, (rendered.count("(centerOnSide)")
                             + rendered.count("(crossing)")))
        stores = tuple(
            f"glsl::set_swizzle<{lane}>(centerSample, "
            "glsl::dot(centerSample, LUMA));"
            for lane in range(3))
        for store in stores:
            self.assertEqual(1, rendered.count(store))
        self.assertIn(("\n      ").join(stores), rendered)
        self.assertLess(rendered.index(stores[0]), rendered.index(stores[1]))
        self.assertLess(rendered.index(stores[1]), rendered.index(stores[2]))
        self.assertNotIn(
            "centerSample = glsl::Vec3(glsl::FloatExpr<3>(glsl::dot(",
            rendered)

    def test_center_splat_mutations_fail_after_coarse_refreeze(self):
        profile = _profile()
        raw = SOURCE.read_text(encoding="utf-8")
        mutations = (
            ("reversed-dot-route",
             "centerSample = vec3(dot(centerSample, LUMA));",
             "centerSample = vec3(dot(LUMA, centerSample));"),
            ("extra-self-splat",
             "centerSample = vec3(dot(centerSample, LUMA));",
             "centerSample = vec3(dot(centerSample, LUMA));\n"
             "        centerSample = vec3(dot(centerSample, LUMA));"),
        )
        for name, anchor, replacement in mutations:
            self.assertEqual(1, raw.count(anchor), name)
            changed = raw.replace(anchor, replacement)
            candidate = _analyzed(changed)
            raw_bytes = candidate.raw_source.encode()
            normalized = candidate.source.encode()
            replacements = {
                "_RAW_BYTES": len(raw_bytes),
                "_RAW_SHA256": hashlib.sha256(raw_bytes).hexdigest(),
                "_NORMALIZED_BYTES": len(normalized),
                "_NORMALIZED_SHA256": hashlib.sha256(normalized).hexdigest(),
                "_FUNCTIONS_SHA256": profile._sha(candidate.functions),
                "_WHOLE_SHA256": profile._whole(candidate),
                "_INTERFACE_SHA256": profile._interface(candidate),
            }
            with self.subTest(name=name), mock.patch.multiple(
                    profile, **replacements):
                profile_hash = profile._sha(profile._profile_tuple())
                with mock.patch.object(profile, "_PROFILE_SHA256", profile_hash), \
                        self.assertRaisesRegex(
                            ValueError, "center-splat closure"):
                    profile.authenticate_edge_center_splat(
                        candidate, replacements["_RAW_SHA256"], PROFILE)

    def test_profile_rejects_carrier_key_source_and_exact_route_mutations(self):
        profile = _profile()
        program = _analyzed()
        candidates = (
            (program, RAW_SHA256, None),
            (program, RAW_SHA256, "wrong"),
            (program, "0" * 64, PROFILE),
            (dataclasses.replace(program, key="filter/other:other"),
             RAW_SHA256, PROFILE),
            (dataclasses.replace(program, functions=program.functions[:-1]),
             RAW_SHA256, PROFILE),
        )
        for candidate, source_hash, carrier in candidates:
            with self.subTest(candidate=(candidate.key, source_hash, carrier)), \
                    self.assertRaises(ValueError):
                profile.authenticate_edge_bvec3_contour(
                    candidate, source_hash, carrier)

        raw = SOURCE.read_text(encoding="utf-8")
        mutations = (
            ("greaterThanEqual(centerRGB, vec3(lvl))",
             "lessThanEqual(centerRGB, vec3(lvl))"),
            ("lessThan(centerRGB, vec3(lvl))",
             "greaterThanEqual(centerRGB, vec3(lvl))"),
            ("centerOnSide.r &&", "centerOnSide.g &&"),
            ("centerOnSide.g && (upperSide",
             "centerOnSide.b && (upperSide"),
            ("bvec3 crossing = bvec3(",
             "bvec3 extra = greaterThanEqual(centerRGB, vec3(lvl));\n"
             "    bvec3 crossing = bvec3("),
        )
        for anchor, replacement in mutations:
            self.assertEqual(1, raw.count(anchor), anchor)
            changed = raw.replace(anchor, replacement)
            candidate = _analyzed(changed)
            with self.subTest(anchor=anchor), self.assertRaises(ValueError):
                profile.authenticate_edge_bvec3_contour(
                    candidate, hashlib.sha256(changed.encode()).hexdigest(),
                    PROFILE)

    def test_detailed_census_rejects_route_mutations_after_coarse_refreeze(self):
        profile = _profile()
        raw = SOURCE.read_text(encoding="utf-8")
        mutations = (
            ("upper-relational", "greaterThanEqual(centerRGB, vec3(lvl))",
             "lessThanEqual(centerRGB, vec3(lvl))"),
            ("lower-relational", "lessThan(centerRGB, vec3(lvl))",
             "greaterThanEqual(centerRGB, vec3(lvl))"),
            ("red-source-lane", "centerOnSide.r &&", "centerOnSide.g &&"),
            ("crossing-output-lane", "crossing.g ?", "crossing.b ?"),
            ("extra-storage", "bvec3 crossing = bvec3(",
             "bvec3 extra = greaterThanEqual(centerRGB, vec3(lvl));\n"
             "    bvec3 crossing = bvec3("),
        )
        for name, anchor, replacement in mutations:
            self.assertEqual(1, raw.count(anchor), name)
            changed = raw.replace(anchor, replacement)
            candidate = _analyzed(changed)
            raw_bytes = candidate.raw_source.encode()
            normalized = candidate.source.encode()
            replacements = {
                "_RAW_BYTES": len(raw_bytes),
                "_RAW_SHA256": hashlib.sha256(raw_bytes).hexdigest(),
                "_NORMALIZED_BYTES": len(normalized),
                "_NORMALIZED_SHA256": hashlib.sha256(normalized).hexdigest(),
                "_FUNCTIONS_SHA256": profile._sha(candidate.functions),
                "_WHOLE_SHA256": profile._whole(candidate),
                "_INTERFACE_SHA256": profile._interface(candidate),
            }
            with self.subTest(name=name), mock.patch.multiple(
                    profile, **replacements):
                profile_hash = profile._sha(profile._profile_tuple())
                with mock.patch.object(profile, "_PROFILE_SHA256", profile_hash), \
                        self.assertRaisesRegex(ValueError, "closure|route|host"):
                    profile.authenticate_edge_bvec3_contour(
                        candidate, replacements["_RAW_SHA256"], PROFILE)

    def test_both_authorities_reject_foreign_and_forged_proofs(self):
        profile = _profile()
        program = _analyzed()
        exact = profile.authenticate_edge_bvec3_contour(
            program, RAW_SHA256, PROFILE)
        separate = _analyzed()
        cross = profile.authenticate_edge_bvec3_contour(
            separate, RAW_SHA256, PROFILE)
        copied = copy.deepcopy(exact.bvec_nodes[2])
        copied_nodes = (*exact.bvec_nodes[:2], copied, *exact.bvec_nodes[3:])
        forged = {
            "cross-candidate": cross,
            "deep-copy": dataclasses.replace(
                exact, bvec_nodes=copied_nodes,
                relationals=(copied, exact.relationals[1])),
            "reordered": dataclasses.replace(
                exact, bvec_nodes=(exact.bvec_nodes[1], exact.bvec_nodes[0],
                                  *exact.bvec_nodes[2:])),
            "duplicated": dataclasses.replace(
                exact, swizzles=(*exact.swizzles[:-1], exact.swizzles[-2])),
            "omitted": types.SimpleNamespace(
                _candidate=program, bvec_nodes=exact.bvec_nodes,
                relationals=exact.relationals, declarations=exact.declarations,
                constructor=exact.constructor, id_reads=exact.id_reads,
                swizzles=exact.swizzles[:-1],
                consumed_objects=exact.consumed_objects),
            "wrong-parent": dataclasses.replace(
                exact, constructor=exact.bvec_nodes[1]),
        }
        for name, proof in forged.items():
            with self.subTest(name=name, authority="validator"), \
                    mock.patch.object(
                        generate_typed_slice,
                        "authenticate_edge_bvec3_contour",
                        return_value=proof), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=RAW_SHA256,
                    edge_bvec3_contour_profile=PROFILE)
            with self.subTest(name=name, authority="emitter"), mock.patch(
                    "tools.glslcpp.emit_typed_cpp."
                    "authenticate_edge_bvec3_contour",
                    return_value=proof), self.assertRaises(
                        emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, RAW_SHA256, "edge_probe", "bind_edge_probe",
                    edge_bvec3_contour_profile=PROFILE)

    def test_both_authorities_reject_forged_center_splat_proofs(self):
        profile = _profile()
        program = _analyzed()
        exact = profile.authenticate_edge_center_splat(
            program, RAW_SHA256, PROFILE)
        cross = profile.authenticate_edge_center_splat(
            _analyzed(), RAW_SHA256, PROFILE)
        forged = {
            "cross-candidate": cross,
            "deep-copy-assignment": dataclasses.replace(
                exact, assignment=copy.deepcopy(exact.assignment)),
            "wrong-ancestry": dataclasses.replace(
                exact,
                statement_parent_chain=(
                    *exact.statement_parent_chain[:-2],
                    exact.statement_parent_chain[-1],
                    exact.statement_parent_chain[-2])),
        }
        for name, proof in forged.items():
            with self.subTest(name=name, authority="validator"), \
                    mock.patch.object(
                        generate_typed_slice,
                        "authenticate_edge_center_splat",
                        return_value=proof), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    program, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=RAW_SHA256,
                    edge_bvec3_contour_profile=PROFILE)
            with self.subTest(name=name, authority="emitter"), mock.patch(
                    "tools.glslcpp.emit_typed_cpp."
                    "authenticate_edge_center_splat",
                    return_value=proof), self.assertRaises(
                        emit_typed_cpp.TypedEmissionError):
                emit_typed_cpp.render_typed_cpp(
                    program, KEY, RAW_SHA256, "edge_probe", "bind_edge_probe",
                    edge_bvec3_contour_profile=PROFILE)
    def test_slice_schema_accepts_only_single_exact_edge_carrier(self):
        spec = copy.deepcopy(generate_typed_slice.load_slice(ROOT))
        spec["programs"] = [item for item in spec["programs"]
                            if item["program_key"] != KEY]
        row = {
            "defines": {},
            "edge_bvec3_contour_profile": PROFILE,
            "program_key": KEY,
        }
        spec["programs"].append(row)
        spec["programs"].sort(key=lambda item: item["program_key"])
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            target = repository / "tools/glslcpp/typed_slice.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(spec), encoding="utf-8")
            loaded = generate_typed_slice.load_slice(repository)
        self.assertEqual([row], [
            item for item in loaded["programs"]
            if "edge_bvec3_contour_profile" in item])

    def test_slice_schema_rejects_noncanonical_edge_carriers(self):
        exact = json.loads((ROOT / "tools/glslcpp/typed_slice.json").read_text(
            encoding="utf-8"))
        row = next(item for item in exact["programs"]
                   if item["program_key"] == KEY)
        self.assertEqual({
            "defines": {},
            "edge_bvec3_contour_profile": PROFILE,
            "program_key": KEY,
        }, row)
        mutations = {}
        wrong = copy.deepcopy(exact)
        next(item for item in wrong["programs"]
             if item["program_key"] == KEY)[
                 "edge_bvec3_contour_profile"] = "wrong"
        mutations["wrong"] = wrong
        missing = copy.deepcopy(exact)
        del next(item for item in missing["programs"]
                 if item["program_key"] == KEY)["edge_bvec3_contour_profile"]
        mutations["missing"] = missing
        extra = copy.deepcopy(exact)
        next(item for item in extra["programs"]
             if item["program_key"] == KEY)["extra"] = True
        mutations["extra-field"] = extra
        duplicate = copy.deepcopy(exact)
        duplicate["programs"].append(copy.deepcopy(row))
        duplicate["programs"].sort(key=lambda item: item["program_key"])
        mutations["duplicate"] = duplicate
        foreign = copy.deepcopy(exact)
        next(item for item in foreign["programs"]
             if item["program_key"] == "synth/gradient:gradient")[
                 "edge_bvec3_contour_profile"] = PROFILE
        mutations["foreign"] = foreign
        collision = copy.deepcopy(exact)
        next(item for item in collision["programs"]
             if item["program_key"] == KEY)[
                 "runtime_loop_bound_profile"] = "runtime-loop-bound-v1"
        mutations["collision"] = collision
        for name, candidate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                repository = pathlib.Path(temp)
                target = repository / "tools/glslcpp/typed_slice.json"
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.load_slice(repository)

    def test_edge_is_exact_single_program_delta_from_glyph_178(self):
        import re

        # MILESTONE reconstruction of Edge-179 over Glyph-178: everything that
        # landed after Edge is excluded below, and cellRefract joins the
        # exclusion set so the frozen 179/178 counts and hashes stay exactly
        # as-is.
        current_spec = copy.deepcopy(generate_typed_slice.load_slice(ROOT))
        with historical_cross_lane(current_spec):
            current_spec["programs"] = [
                item for item in current_spec["programs"]
                if item["program_key"] not in {
                    "classicNoisedeck/moodscape:moodscape",
                    "filter/emboss:emboss",
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
                     "synth/remap:remap",
                     "synth/testPattern:testPattern",
                     "classicNoisedeck/bitEffects:bitEffects",
                     "classicNoisedeck/colorLab:colorLab",
                     "classicNoisedeck/noise:noise",
                     "filter/historicPalette:historicPalette",
                     "filter/median:median", "filter/osd:osd",
                     "filter/palette:palette", "filter/spookyTicker:spookyTicker",
                     "filter/texture:texture",
                    # Removal-set insertion 2026-08-25: `filter/dither:dither` and
                                        # `synth/julia:julia` landed AFTER this milestone and were absent from
                                        # the projection, so it was measuring a slice two rows too large.
                                        # Adding the landed keys is the correct repair -- the frozen counts
                                        # below are unchanged, which is the proof this is the right one. The
                                        # set now equals the next milestone's exclusions plus its own row.
                                        # See task-7-typed-generator-census-repair.md.
                    "filter/dither:dither",
                    "synth/julia:julia",
                 }]
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

        # Re-frozen 2026-08-25 because the DSL/Task-7 emitter now writes
        # FactoryRoute/define metadata into the emitted artifacts. The projection
        # above is corrected first (the frozen COUNTS match again), so this
        # measures the same milestone under the new emitter. Derived from a
        # measured regeneration of this test's own projection; see
        # task-7-typed-generator-census-repair.md.
        expected_current = {
            "src/typed_generated/typed_slice.cpp":
                "67c70a8a66792d57844d50a8409757891264a951e6b56d06ba41bded78ff7e3f",
            "src/typed_generated/typed_manifest.json":
                "0225c98b4ad08ff9a3c5036ec49de0464cec13649d369ce92c4de556d765d8a0",
            "include/noisemaker/generated/catalog.hpp":
                "b493116184614b37edc2416ebb9c16822bab9032aaadc28e60650020f33b8f42",
        }
        expected_prior = {
            "src/typed_generated/typed_slice.cpp":
                "05c57f4e5c38c4fd6e1afae4ed1e222237d76b2e51cb65ff8d0478d21db9f3be",
            "src/typed_generated/typed_manifest.json":
                "0da0d1d4f140048f4c3d729c5b4159cbd7d08c8f62cb59a6601f613ab071c26a",
            "include/noisemaker/generated/catalog.hpp":
                "a9e99e5bc57bb06d2e0307b8255fc39a2fb769b7e9aff808e18b2bd4de1b4f53",
        }
        for label, outputs, expected in (
                ("edge179", current, expected_current),
                ("glyph178", prior, expected_prior)):
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
        self.assertEqual((180, 179),
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
        self.assertEqual((180, 179),
                         (len(current_rows), len(prior_rows)))
        self.assertEqual({KEY}, set(current_rows) - set(prior_rows))
        self.assertEqual(PROFILE, current_rows[KEY][
            "edge_bvec3_contour_profile"])

    def test_global_vocabularies_remain_frozen(self):
        values = {
            "capabilities": (generate_typed_slice.APPROVED_CAPABILITIES, 44,
                "6ddb906dc859e45ee613b580dc6988c663d2aff22db9c365ece3097d126a4aea"),
            "types": (generate_typed_slice.APPROVED_TYPES, 17,
                "aa4ab00ac3b34ece6681eaa55435817b7908c9b8ea421a6eca1931f6ab4791c7"),
            "binary": (generate_typed_slice.APPROVED_BINARY_OPERATORS, 17,
                "cceb35790b79fa895906c57d7e81f0056fac404cf7448eec9b8d9dbb49b705b0"),
            "assignment": (generate_typed_slice.APPROVED_ASSIGNMENT_OPERATORS, 6,
                "99a6ede7544a02082e0b72d83690c3b68d8c846e221078e3e90ac10463d498e2"),
            "emitter-types": (emit_typed_cpp._TYPES, 16,
                "35bc343afc6ddda237a7d27601b214abdcd5fe668d0dc1d6d5aebd03ad5f7fba"),
            "validator-builtins": (tuple(sorted(generate_typed_slice._BUILTINS)), 25,
                "97358ee6a1b503ff8aed40f3aa104136704e2b528f7d2aadb32a24bd53ebe4b7"),
            "emitter-builtins": (emit_typed_cpp._BUILTIN_NAMES, 22,
                "664d62a0dd0e600ac1e6e0c95387a54d6cf72369742401bf68faa4245e5cea64"),
        }
        for name, (value, count, digest) in values.items():
            with self.subTest(name=name):
                self.assertEqual(count, len(value))
                self.assertEqual(digest,
                                 hashlib.sha256(repr(value).encode()).hexdigest())


if __name__ == "__main__":
    unittest.main()
