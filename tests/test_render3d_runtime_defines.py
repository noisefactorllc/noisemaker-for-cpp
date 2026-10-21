"""Exact runtime-define proof for both current 3D renderer programs."""

import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.loop_proof import (
    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
    validate_source_global_literal_int_program)
from tools.glslcpp.frontend.struct_frontier_profile import (
    PROFILES, RENDER_DYNAMIC_PROFILES, authenticate_struct_frontier)
from tools.glslcpp.frontend.cross_builtin_profile import (
    PROFILE as CROSS_PROFILE, RENDER_DYNAMIC_PROFILE,
    authenticate_cross_sites)
from tools.glslcpp.generate_typed_slice import (
    APPROVED_CAPABILITIES, GENERIC_DYNAMIC_DEFINE_TYPES,
    validate_capabilities)
from tools.glslcpp.emit_typed_cpp import render_typed_cpp


CORPUS = (Path(__file__).resolve().parents[1]
          / f"tools/glslcpp/corpus/{CORPUS_REVISION}/sources/render")
CASES = (("render3d", "render3d"),
         ("renderCubemap3d", "renderCubemap3d"))


def program(effect, pass_name, defines):
    key = f"render/{effect}:{pass_name}"
    source = (CORPUS / effect / f"{pass_name}.glsl").read_text()
    parsed = parse_program(source, key, defines)
    if isinstance(defines["FILTERING"], str):
        parsed["raw_source"] = source
    typed = analyze_program(
        parsed, key,
        source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
    return typed, hashlib.sha256(source.encode()).hexdigest()


class Render3dRuntimeDefineTests(unittest.TestCase):
    def test_dynamic_tree_has_exact_proofs_and_emits_both_runtime_defines(self):
        for effect, pass_name in CASES:
            with self.subTest(effect=effect):
                key = f"render/{effect}:{pass_name}"
                self.assertEqual(GENERIC_DYNAMIC_DEFINE_TYPES[key],
                                 {"FILTERING": "int", "INVERT": "bool"})
                typed, source_hash = program(
                    effect, pass_name, GENERIC_DYNAMIC_DEFINE_TYPES[key])
                validate_source_global_literal_int_program(
                    typed, SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
                frontier = authenticate_struct_frontier(
                    typed, source_hash, RENDER_DYNAMIC_PROFILES[key])
                self.assertEqual((len(frontier.structs), len(frontier.locals),
                                  len(frontier.members), len(frontier.consumed)),
                                 (2, 4, 29, 47))
                kwargs = dict(
                    source_global_literal_int_profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
                    struct_frontier_profile=RENDER_DYNAMIC_PROFILES[key])
                if effect == "render3d":
                    self.assertEqual(len(authenticate_cross_sites(
                        typed, source_hash, RENDER_DYNAMIC_PROFILE)), 2)
                    kwargs["cross_builtin_profile"] = RENDER_DYNAMIC_PROFILE
                validate_capabilities(
                    typed, APPROVED_CAPABILITIES, source_hash=source_hash,
                    **kwargs)
                emitted = render_typed_cpp(
                    typed, key, source_hash, "render_runtime_probe",
                    "bind_render_runtime_probe", **kwargs)
                self.assertIn('bindings.get<std::int32_t>("FILTERING")', emitted)
                self.assertIn('bindings.get<bool>("INVERT")', emitted)
                self.assertEqual(emitted.count(
                    "voxelBounds = glsl::Vec3("
                    "std::numeric_limits<float>::quiet_NaN());"), 1)
                self.assertEqual(emitted.count("  double dist;"), 1)

    def test_default_tree_and_dynamic_tree_cannot_use_each_others_locks(self):
        for effect, pass_name in CASES:
            with self.subTest(effect=effect):
                key = f"render/{effect}:{pass_name}"
                default, source_hash = program(
                    effect, pass_name, {"FILTERING": 0, "INVERT": False})
                dynamic, _ = program(
                    effect, pass_name, {"FILTERING": "int", "INVERT": "bool"})
                self.assertIsNotNone(authenticate_struct_frontier(
                    default, source_hash, PROFILES[key]))
                for candidate, profile in ((default, RENDER_DYNAMIC_PROFILES[key]),
                                           (dynamic, PROFILES[key])):
                    with self.assertRaises(ValueError):
                        authenticate_struct_frontier(candidate, source_hash, profile)
                with self.assertRaises(ValueError):
                    authenticate_struct_frontier(
                        dynamic, "0" * 64, RENDER_DYNAMIC_PROFILES[key])
                if effect == "render3d":
                    self.assertEqual(len(authenticate_cross_sites(
                        default, source_hash, CROSS_PROFILE)), 2)
                    for candidate, profile in ((default, RENDER_DYNAMIC_PROFILE),
                                               (dynamic, CROSS_PROFILE)):
                        with self.assertRaises(ValueError):
                            authenticate_cross_sites(candidate, source_hash, profile)


if __name__ == "__main__":
    unittest.main()
