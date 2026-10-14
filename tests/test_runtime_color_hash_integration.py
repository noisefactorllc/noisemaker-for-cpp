"""Exact Classic Noise and Moodscape dynamic production admissions."""

from __future__ import annotations

import dataclasses
from pathlib import Path
import unittest

from tools.glslcpp import generate_typed_slice as generator
from tools.glslcpp import emit_typed_cpp as emitter
from tools.glslcpp.frontend import dynamic_define_hoist, parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import noise_frontend_profile as noise
from tools.glslcpp.frontend import moodscape_frontend_profile as moodscape
from tools.glslcpp.frontend import moodscape_dynamic_profile as moodscape_dynamic

SOURCE_ROOT = (Path(generator.__file__).resolve().parent / "corpus"
               / "6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d" / "sources")


def candidate(kind: str, runtime: bool):
    profile = noise if kind == "noise" else moodscape
    raw = (SOURCE_ROOT / "classicNoisedeck" / kind / f"{kind}.glsl").read_text()
    defines = ({name: "int" for name, _, _ in profile.FIXED_DEFINES}
               if kind == "noise" else {"COLOR_MODE": "int", "NOISE_TYPE": "int"})
    if not runtime:
        defines = ({name: int(value) for name, _, value in profile.FIXED_DEFINES}
                   if kind == "noise" else {"COLOR_MODE": 2, "NOISE_TYPE": 10})
    source = dynamic_define_hoist.transform_source(raw, profile.KEY) if runtime else raw
    parsed = parse_program(source, profile.KEY, defines)
    parsed["raw_source"] = raw
    analyzed = analyze_program(parsed, profile.KEY)
    if kind == "noise":
        selected = noise.PROFILE
        projected = noise.apply_noise_frontend(analyzed, noise.RAW_SHA256, selected)
    elif runtime:
        selected = moodscape_dynamic.PROFILE
        projected, _ = moodscape_dynamic.apply(
            analyzed, moodscape.RAW_SHA256, selected)
    else:
        selected = moodscape.PROFILE
        projected = moodscape.apply_moodscape_frontend(
            analyzed, moodscape.RAW_SHA256, selected)
    return profile, projected, selected


def validate(kind: str, program, source_hash: str, carrier: str | None):
    generator.validate_capabilities(
        program, generator.APPROVED_CAPABILITIES,
        source_hash=source_hash, numeric_literal_contract="glsl-f32",
        **{f"{kind}_frontend_profile": carrier})


def emit(kind: str, program, source_hash: str, carrier: str | None):
    return emitter.render_typed_cpp(
        program, program.key, source_hash,
        numeric_literal_contract="glsl-f32",
        **{f"{kind}_frontend_profile": carrier})


class RuntimeColorHashIntegrationTests(unittest.TestCase):
    def test_both_runtime_candidates_validate_and_emit(self):
        for kind in ("noise", "moodscape"):
            with self.subTest(kind=kind):
                profile, program, carrier = candidate(kind, True)
                validate(kind, program, profile.RAW_SHA256, carrier)
                text = emit(kind, program, profile.RAW_SHA256, carrier)
                self.assertIn("noisemaker::float_bits_to_uint", text)
                self.assertIn("static_cast<std::size_t>", text)

    def test_original_default_candidates_still_validate_and_emit(self):
        for kind in ("noise", "moodscape"):
            with self.subTest(kind=kind):
                profile, program, carrier = candidate(kind, False)
                validate(kind, program, profile.RAW_SHA256, carrier)
                self.assertIn("Typed IR program", emit(
                    kind, program, profile.RAW_SHA256, carrier))

    def test_noise_runtime_palette_preserves_uniform_precision(self):
        profile, program, carrier = candidate("noise", True)
        text = emit("noise", program, profile.RAW_SHA256, carrier)
        for name in ("paletteOffset", "paletteAmp", "paletteFreq", "palettePhase"):
            self.assertIn(f"glsl::DVec3 {name}", text)

    def test_source_tree_and_carrier_forgery_reject(self):
        for kind in ("noise", "moodscape"):
            profile, program, carrier = candidate(kind, True)
            forged = (
                (dataclasses.replace(program, source=program.source + "\n"),
                 profile.RAW_SHA256, carrier),
                (dataclasses.replace(program, functions=program.functions[:-1]),
                 profile.RAW_SHA256, carrier),
                (program, "0" * 64, carrier),
                (program, profile.RAW_SHA256, "wrong-profile"),
                (program, profile.RAW_SHA256, None),
            )
            for index, (changed, source_hash, changed_carrier) in enumerate(forged):
                with self.subTest(kind=kind, mutation=index):
                    with self.assertRaises((ValueError, RuntimeError)):
                        validate(kind, changed, source_hash, changed_carrier)
                    with self.assertRaises((ValueError, RuntimeError)):
                        emit(kind, changed, source_hash, changed_carrier)


if __name__ == "__main__":
    unittest.main()
