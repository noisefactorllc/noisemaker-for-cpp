from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import color_lab_frontend_profile as profile


ROOT = Path(__file__).resolve().parents[1]
KEY = "classicNoisedeck/colorLab:colorLab"


def _program():
    source_hash, program = profile.load_live_program(ROOT)
    return source_hash, program


class ColorLabGeneratorEmitterTests(unittest.TestCase):
    def test_row_204_is_exact_source_bound_and_sorted(self):
        spec = generate_typed_slice.load_slice(ROOT)
        rows = spec["programs"]
        # Live pin repinned 2026-08-25 from the tree: the DSL phase landed the
                # slice at 211 typed rows. Measured, never carried from a report; see
                # task-7-typed-generator-census-repair.md.
        self.assertEqual(211, len(rows))
        self.assertEqual(
            {
                "color_lab_frontend_profile": profile.PROFILE,
                "defines": {},
                "program_key": KEY,
            },
            rows[5],
        )
        keys = [row["program_key"] for row in rows]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(
            "29a148b26cfe4f550ac82325810655eb0e5ffad2c3a4e5241e42600bac9f76c1",
            hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest(),
        )
        self.assertEqual((KEY,), profile.KEYS)
        self.assertEqual((), profile.PREPARED_KEYS)
        self.assertEqual(
            frozenset({"color_lab_frontend_profile", "defines", "program_key"}),
            profile.allowed_row_fields(KEY),
        )

    def test_validator_and_apply_require_the_exact_profile_carrier(self):
        source_hash, program = _program()
        self.assertIs(
            program,
            profile.apply_color_lab_frontend(
                program, source_hash, profile.PROFILE),
        )
        generate_typed_slice.validate_capabilities(
            program,
            generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            color_lab_frontend_profile=profile.PROFILE,
        )
        with self.assertRaisesRegex(
            generate_typed_slice.GeneratorError,
            "exact ColorLab frontend profile carrier required",
        ):
            generate_typed_slice.validate_capabilities(
                program,
                generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
            )
        with self.assertRaisesRegex(
            generate_typed_slice.GeneratorError,
            "ColorLab frontend profile metadata mismatch",
        ):
            generate_typed_slice.validate_capabilities(
                program,
                generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                color_lab_frontend_profile="foreign-color-lab-profile",
            )

    def test_emitter_consumes_the_exact_identity_disjoint_index_closure(self):
        source_hash, program = _program()
        proof = profile.authenticate_color_lab_frontend(
            program, source_hash, profile.PROFILE)
        indexes = tuple(
            node for node in proof.consumed_nodes
            if getattr(node, "kind", None) == "index"
        )
        vector_equalities = tuple(
            node for node in proof.consumed_nodes
            if (getattr(node, "kind", None) == "binary"
                and getattr(node, "operator", None) == "=="
                and tuple(child.type.display() for child in node.children)
                == ("vec2", "vec2"))
        )
        self.assertEqual(1081, len(proof.consumed_nodes))
        self.assertEqual(1081, len({id(node) for node in proof.consumed_nodes}))
        self.assertEqual(13, len(indexes))
        self.assertEqual(6, len(vector_equalities))
        rendered = emit_typed_cpp.render_typed_cpp(
            program,
            KEY,
            source_hash,
            color_lab_frontend_profile=profile.PROFILE,
        )
        self.assertIn("context.frag_coord", rendered)
        self.assertIn("state.tileOffset", rendered)
        self.assertIn("state.fullResolution", rendered)
        self.assertIn("texture_size(*state.inputTex)", rendered)
        self.assertIn("linear[static_cast<std::size_t>(i)]", rendered)
        self.assertIn("srgb[static_cast<std::size_t>(i)]", rendered)
        self.assertIn(
            "rgb2hsv(state, context, glsl::swizzle<0, 1, 2>(color))"
            "[static_cast<std::size_t>(std::int32_t(2))]",
            rendered,
        )
        self.assertIn(
            "hsv[static_cast<std::size_t>(std::int32_t(0))]",
            rendered,
        )
        self.assertEqual(
            6,
            rendered.count(
                "glsl::canonical_js_vector_equality_result_is_truthy("),
        )
        with self.assertRaisesRegex(
            emit_typed_cpp.TypedEmissionError,
            "exact ColorLab frontend profile carrier required",
        ):
            emit_typed_cpp.render_typed_cpp(program, KEY, source_hash)
        with self.assertRaisesRegex(
            emit_typed_cpp.TypedEmissionError,
            "ColorLab frontend profile metadata mismatch",
        ):
            emit_typed_cpp.render_typed_cpp(
                program,
                KEY,
                source_hash,
                color_lab_frontend_profile="foreign-color-lab-profile",
            )

    def test_rendered_runtime_abi_matches_the_authenticated_profile(self):
        source_hash, program = _program()
        rendered = emit_typed_cpp.render_typed_cpp(
            program,
            KEY,
            source_hash,
            color_lab_frontend_profile=profile.PROFILE,
        )
        self.assertIn('bindings.texture("inputTex")', rendered)
        for name, native in profile.RUNTIME_UNIFORM_ABI:
            if native == "float":
                binding = f'bindings.get_number("{name}")'
            else:
                cxx = {
                    "Vec2": "glsl::Vec2",
                    "Vec3": "glsl::Vec3",
                    "bool": "bool",
                    "int32": "std::int32_t",
                }[native]
                binding = f'bindings.get<{cxx}>("{name}")'
            self.assertEqual(1, rendered.count(binding), (name, binding))


if __name__ == "__main__":
    unittest.main()
