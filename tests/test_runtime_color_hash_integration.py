"""Exact Classic Noise and Moodscape dynamic production admissions."""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
import unittest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp import generate_typed_slice as generator
from tools.glslcpp import emit_typed_cpp as emitter
from tools.glslcpp.frontend import dynamic_define_hoist, parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import noise_frontend_profile as noise
from tools.glslcpp.frontend import moodscape_frontend_profile as moodscape
from tools.glslcpp.frontend import moodscape_dynamic_profile as moodscape_dynamic

SOURCE_ROOT = (Path(generator.__file__).resolve().parent / "corpus"
               / CORPUS_REVISION / "sources")


def candidate(kind: str, runtime: bool):
    profile = noise if kind == "noise" else moodscape
    source_root = SOURCE_ROOT if runtime else (SOURCE_ROOT.parents[1] / "32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3/sources")
    raw = (source_root / "classicNoisedeck" / kind / f"{kind}.glsl").read_text()
    digest = hashlib.sha256(raw.encode()).hexdigest()
    expected = ({"noise": "513f8278e29564b7f2b0735b539b5990b53dc920d487fffb87d54a0c92fc5f0b",
                 "moodscape": "2b020887bfb1a4dd366b1583e4ff68fd47193bd4993ba1052170de0981aabfa1"}[kind]
                if runtime else profile.RAW_SHA256)
    assert digest == expected, "fixture source identity mismatch"
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
        projected = noise.apply_noise_frontend(analyzed, digest, selected)
    elif runtime:
        selected = moodscape_dynamic.PROFILE
        projected, _ = moodscape_dynamic.apply(
            analyzed, digest, selected)
    else:
        selected = moodscape.PROFILE
        projected = moodscape.apply_moodscape_frontend(
            analyzed, digest, selected)
    return digest, projected, selected


def validate(kind: str, program, source_hash: str, carrier: str | None):
    generator.validate_capabilities(
        program, generator.APPROVED_CAPABILITIES,
        source_hash=source_hash, numeric_literal_contract="glsl-f32",
        **{f"{kind}_frontend_profile": carrier},
        **({"prng_boolean_mix_select_profile": "prng-boolean-mix-select-v1"}
           if any(d.kind == "str" for d in program.preprocessor_defines) else {}))


def emit(kind: str, program, source_hash: str, carrier: str | None):
    return emitter.render_typed_cpp(
        program, program.key, source_hash,
        numeric_literal_contract="glsl-f32",
        **{f"{kind}_frontend_profile": carrier},
        **({"prng_boolean_mix_select_profile": "prng-boolean-mix-select-v1"}
           if any(d.kind == "str" for d in program.preprocessor_defines) else {}))


class RuntimeColorHashIntegrationTests(unittest.TestCase):
    def test_both_runtime_candidates_validate_and_emit(self):
        for kind in ("noise", "moodscape"):
            with self.subTest(kind=kind):
                digest, program, carrier = candidate(kind, True)
                validate(kind, program, digest, carrier)
                text = emit(kind, program, digest, carrier)
                self.assertIn("noisemaker::float_bits_to_uint", text)
                self.assertIn("static_cast<std::size_t>", text)

    def test_original_default_candidates_still_validate_and_emit(self):
        for kind in ("noise", "moodscape"):
            with self.subTest(kind=kind):
                digest, program, carrier = candidate(kind, False)
                validate(kind, program, digest, carrier)
                self.assertIn("Typed IR program", emit(
                    kind, program, digest, carrier))

    def test_noise_runtime_palette_preserves_uniform_precision(self):
        digest, program, carrier = candidate("noise", True)
        text = emit("noise", program, digest, carrier)
        for name in ("paletteOffset", "paletteAmp", "paletteFreq", "palettePhase"):
            self.assertIn(f"glsl::DVec3 {name}", text)

    def test_source_tree_and_carrier_forgery_reject(self):
        for kind in ("noise", "moodscape"):
            digest, program, carrier = candidate(kind, True)
            forged = (
                (dataclasses.replace(program, source=program.source + "\n"),
                 digest, carrier),
                (dataclasses.replace(program, functions=program.functions[:-1]),
                 digest, carrier),
                (program, "0" * 64, carrier),
                (program, digest, "wrong-profile"),
                (program, digest, None),
            )
            for index, (changed, source_hash, changed_carrier) in enumerate(forged):
                with self.subTest(kind=kind, mutation=index):
                    with self.assertRaises((ValueError, RuntimeError)):
                        validate(kind, changed, source_hash, changed_carrier)
                    with self.assertRaises((ValueError, RuntimeError)):
                        emit(kind, changed, source_hash, changed_carrier)


if __name__ == "__main__":
    unittest.main()
