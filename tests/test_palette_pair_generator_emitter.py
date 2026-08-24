from __future__ import annotations

import hashlib
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.generate_kernels import GeneratorError


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources"
HISTORIC_KEY = "filter/historicPalette:historicPalette"
PALETTE_KEY = "filter/palette:palette"


def _typed(key: str):
    source = (CORPUS / key.split(":", 1)[0] / (key.split(":", 1)[1] + ".glsl")).read_text()
    return analyze_program(parse_program(source, key, {}), key)


class PalettePairGeneratorEmitterTests(unittest.TestCase):
    def test_rows_remain_exactly_landed_in_the_sorted_slice(self):
        spec = generate_typed_slice.load_slice(ROOT)
        self.assertEqual(211, len(spec["programs"]))
        rows = spec["programs"]
        self.assertEqual(HISTORIC_KEY, rows[66]["program_key"])
        self.assertEqual(PALETTE_KEY, rows[91]["program_key"])
        self.assertEqual(
            {"defines": {}, "program_key": HISTORIC_KEY,
             "historic_palette_profile": "historic-palette-frontend-admission-v1"},
            rows[66],
        )
        self.assertEqual(
            {"defines": {}, "program_key": PALETTE_KEY,
             "palette_frontend_profile": "palette-frontend-admission-v1"},
            rows[91],
        )

    def test_historic_and_palette_emitter_lowerings_are_profile_bound(self):
        historic = _typed(HISTORIC_KEY)
        palette = _typed(PALETTE_KEY)
        historic_hash = hashlib.sha256(historic.raw_source.encode()).hexdigest()
        palette_hash = hashlib.sha256(palette.raw_source.encode()).hexdigest()
        historic_cpp = render_typed_cpp(
            historic, HISTORIC_KEY, historic_hash,
            historic_palette_profile="historic-palette-frontend-admission-v1",
        )
        palette_cpp = render_typed_cpp(
            palette, PALETTE_KEY, palette_hash,
            palette_frontend_profile="palette-frontend-admission-v1",
        )
        self.assertIn("struct HistoricPalette", historic_cpp)
        self.assertIn("static_cast<std::size_t>(idx)", historic_cpp)
        self.assertIn("struct PaletteEntry", palette_cpp)
        self.assertIn(
            "PALETTES[static_cast<std::size_t>((state.paletteIndex - std::int32_t(1)))]",
            palette_cpp)
        self.assertIn("PALETTE_COUNT", palette_cpp)

    def test_generator_seams_require_exact_profile_identity(self):
        for key, profile_name in (
                (HISTORIC_KEY, "historic-palette-frontend-admission-v1"),
                (PALETTE_KEY, "palette-frontend-admission-v1")):
            typed = _typed(key)
            source_hash = hashlib.sha256(typed.raw_source.encode()).hexdigest()
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                **({"historic_palette_profile": profile_name}
                   if key == HISTORIC_KEY else
                   {"palette_frontend_profile": profile_name}))
            with self.assertRaises(GeneratorError):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash)
            foreign = ("palette-frontend-admission-v1"
                       if key == HISTORIC_KEY
                       else "historic-palette-frontend-admission-v1")
            with self.assertRaises(GeneratorError):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    **({"historic_palette_profile": foreign}
                       if key == HISTORIC_KEY
                       else {"palette_frontend_profile": foreign}))
            with self.assertRaises(TypedEmissionError):
                render_typed_cpp(typed, key, source_hash)
            with self.assertRaises(TypedEmissionError):
                render_typed_cpp(
                    typed, key, source_hash,
                    **({"historic_palette_profile": foreign}
                       if key == HISTORIC_KEY
                       else {"palette_frontend_profile": foreign}))

    def test_emitted_tables_constructors_fields_counts_and_ledgers_are_exact(self):
        historic = _typed(HISTORIC_KEY)
        palette = _typed(PALETTE_KEY)
        historic_hash = hashlib.sha256(historic.raw_source.encode()).hexdigest()
        palette_hash = hashlib.sha256(palette.raw_source.encode()).hexdigest()
        historic_cpp = render_typed_cpp(
            historic, HISTORIC_KEY, historic_hash,
            historic_palette_profile="historic-palette-frontend-admission-v1")
        palette_cpp = render_typed_cpp(
            palette, PALETTE_KEY, palette_hash,
            palette_frontend_profile="palette-frontend-admission-v1")
        self.assertEqual(1, historic_cpp.count("struct HistoricPalette final"))
        self.assertEqual(21, historic_cpp.count("HistoricPalette{"))
        self.assertEqual(5, sum(historic_cpp.count(
            f"  glsl::FloatExpr<3> color{i}{{}};")
                                for i in range(1, 6)))
        historic_table = next(line for line in historic_cpp.splitlines()
                              if "std::array<HistoricPalette, 21> PALETTES" in line)
        self.assertEqual(105, historic_table.count("glsl::FloatExpr<3>("))
        self.assertEqual(1, historic_cpp.count(
            "PALETTES[static_cast<std::size_t>(idx)]"))
        self.assertEqual(1, palette_cpp.count("struct PaletteEntry final"))
        self.assertEqual(55, palette_cpp.count("PaletteEntry{"))
        self.assertEqual(4, sum(palette_cpp.count(
            f"  glsl::FloatExpr<4> {name}{{}};")
                                for name in ("amp", "freq", "offset", "phase")))
        palette_table = next(line for line in palette_cpp.splitlines()
                             if "std::array<PaletteEntry, 55> PALETTES" in line)
        self.assertEqual(220, palette_table.count("glsl::FloatExpr<4>("))
        self.assertEqual(1, palette_cpp.count(
            "PALETTES[static_cast<std::size_t>((state.paletteIndex - std::int32_t(1)))]"))
        self.assertEqual(2, palette_cpp.count("PALETTE_COUNT"))

    def test_palette_tables_preserve_plain_number_until_authenticated_storage(self):
        """The adapter tables are JS Number arrays, not source-f32 vectors.

        This is intentionally an emitter-contract test rather than a numeric
        tolerance test: converting any table lane to ``glsl::Vec`` before the
        profile's proven storage boundary loses the source double and causes
        the native aggregate oracle's last-bit failures.
        """
        historic = _typed(HISTORIC_KEY)
        palette = _typed(PALETTE_KEY)
        historic_hash = hashlib.sha256(historic.raw_source.encode()).hexdigest()
        palette_hash = hashlib.sha256(palette.raw_source.encode()).hexdigest()
        historic_cpp = render_typed_cpp(
            historic, HISTORIC_KEY, historic_hash,
            historic_palette_profile="historic-palette-frontend-admission-v1")
        palette_cpp = render_typed_cpp(
            palette, PALETTE_KEY, palette_hash,
            palette_frontend_profile="palette-frontend-admission-v1")

        # The immutable records retain Number lanes.  Only the Float32Array
        # equivalent output/mix boundary may materialize these expressions.
        self.assertEqual(5, sum(
            historic_cpp.count(f"  glsl::FloatExpr<3> color{i}{{}};")
            for i in range(1, 6)))
        self.assertEqual(4, sum(
            palette_cpp.count(f"  glsl::FloatExpr<4> {name}{{}};")
            for name in ("amp", "freq", "offset", "phase")))
        self.assertNotIn("glsl::Vec3 color1{};", historic_cpp)
        self.assertNotIn("glsl::Vec4 amp{};", palette_cpp)

        historic_table = next(line for line in historic_cpp.splitlines()
                              if "std::array<HistoricPalette, 21> PALETTES" in line)
        palette_table = next(line for line in palette_cpp.splitlines()
                             if "std::array<PaletteEntry, 55> PALETTES" in line)
        self.assertNotIn("static_cast<float>(0.165)", historic_table)
        self.assertNotIn("static_cast<float>(0.56851584)", palette_table)
        tau_line = next(line for line in palette_cpp.splitlines()
                        if "const double TAU" in line)
        self.assertEqual("  const double TAU = 6.283185307179586;", tau_line)

        # Palette's cosine helper receives the retained-double xyz swizzles,
        # and its exact Math.cos path must not call the ordinary GLSL builtin,
        # which materializes FloatExpr lanes to f32 before evaluating cosine.
        cosine_decl = next(line for line in palette_cpp.splitlines()
                           if "cosinePalette(" in line and "noexcept;" in line)
        self.assertIn("glsl::FloatExpr<3> amp", cosine_decl)
        self.assertIn("glsl::FloatExpr<3> freq", cosine_decl)
        cosine_body = palette_cpp[palette_cpp.index("[[nodiscard]] glsl::Vec3 cosinePalette(",
                                                    palette_cpp.index(cosine_decl)):
                                  palette_cpp.index("\n}",
                                                    palette_cpp.index("[[nodiscard]] glsl::Vec3 cosinePalette(",
                                                                      palette_cpp.index(cosine_decl))) + 2]
        self.assertIn("palette_cosine_number_cos", cosine_body)
        self.assertNotIn("glsl::cos", cosine_body)
        self.assertIn("noisemaker::fdlibm::cos", palette_cpp)
        self.assertIn("palette_cosine_number_clamp", cosine_body)

    def test_palette_proofs_carry_exact_plain_number_adapter_sites(self):
        """Profile proofs expose the source-bound numeric adapter sites."""
        from tools.glslcpp.frontend.historic_palette_profile import (
            authenticate_historic_palette,
        )
        from tools.glslcpp.frontend.palette_frontend_profile import (
            authenticate_palette_frontend,
        )

        historic = _typed(HISTORIC_KEY)
        palette = _typed(PALETTE_KEY)
        historic_proof = authenticate_historic_palette(
            historic, hashlib.sha256(historic.raw_source.encode()).hexdigest(),
            "historic-palette-frontend-admission-v1")
        palette_proof = authenticate_palette_frontend(
            palette, hashlib.sha256(palette.raw_source.encode()).hexdigest(),
            "palette-frontend-admission-v1")

        self.assertEqual("glsl::FloatExpr<3>", historic_proof.table_native_type)
        self.assertEqual("glsl::FloatExpr<4>", palette_proof.table_native_type)
        self.assertEqual("TAU", palette_proof.tau_declaration.symbol.name)
        self.assertIs(palette_proof.tau_initializer,
                      palette_proof.tau_declaration.initializer)
        self.assertEqual("cosinePalette", palette_proof.cosine_function.name)
        self.assertEqual("cos", palette_proof.cosine_site.callee)
        self.assertEqual("clamp", palette_proof.cosine_clamp_site.callee)
        self.assertEqual(2, len(palette_proof.cosine_vector_sites))

        self.assertEqual("dot", historic_proof.luminance_site.callee)
        self.assertEqual("+", historic_proof.t_initializer.operator)
        self.assertEqual("fract", historic_proof.fract_site.callee)
        self.assertEqual("sampleHistoricPalette",
                         historic_proof.sample_function.name)
        self.assertEqual(7, len(historic_proof.sample_member_sites))
        self.assertEqual("dot", palette_proof.luminance_site.callee)
        self.assertEqual("+", palette_proof.t_initializer.operator)
        self.assertEqual("hsv2rgb", palette_proof.hsv_function.name)
        self.assertEqual("oklab2rgb", palette_proof.oklab_function.name)

    def test_adapter_number_arithmetic_is_emitted_only_at_authenticated_sites(self):
        historic = _typed(HISTORIC_KEY)
        palette = _typed(PALETTE_KEY)
        historic_cpp = render_typed_cpp(
            historic, HISTORIC_KEY,
            hashlib.sha256(historic.raw_source.encode()).hexdigest(),
            historic_palette_profile="historic-palette-frontend-admission-v1")
        palette_cpp = render_typed_cpp(
            palette, PALETTE_KEY,
            hashlib.sha256(palette.raw_source.encode()).hexdigest(),
            palette_frontend_profile="palette-frontend-admission-v1")

        self.assertEqual(2, historic_cpp.count(
            "historic_palette_number_luminance("))
        self.assertEqual(2, palette_cpp.count(
            "palette_number_luminance("))
        self.assertIn("historic_palette_number_fract(t)", historic_cpp)
        self.assertIn("((lum * 0.9999) * state.repeat)", historic_cpp)
        self.assertIn("(state.offset * 0.01)", historic_cpp)
        self.assertIn("(lum * state.repeat)", palette_cpp)
        self.assertIn("(state.offset * 0.01)", palette_cpp)
        self.assertIn("const double mod2 = hp - (2.0 * std::floor(hp / 2.0));",
                      palette_cpp)
        self.assertIn("palette_number_linear_to_srgb(red)", palette_cpp)

        sample_start = historic_cpp.index(
            "[[nodiscard]] glsl::Vec3 sampleHistoricPalette(",
            historic_cpp.index("noexcept;"))
        sample_end = historic_cpp.index("\n}", sample_start) + 2
        sample_body = historic_cpp[sample_start:sample_end]
        self.assertIn("historic_palette_number_smoothstep", sample_body)
        self.assertIn("historic_palette_number_mix_store", sample_body)
        self.assertNotIn("glsl::smoothstep", sample_body)
        self.assertNotIn("glsl::mix", sample_body)


if __name__ == "__main__":
    unittest.main()
