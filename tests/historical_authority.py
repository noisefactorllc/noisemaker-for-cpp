"""Exact, test-only authority context for pre-migration artifact reconstruction."""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import importlib.util
import pathlib
import sys
from unittest import mock

from tests import corpus_census
from tools.glslcpp import check_corpus, emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import (
    dynamic_define_hoist, fixed_array_in_parameter_proof, lens_distortion_comparer_profile,
    mutable_global_array_profile, noise_frontend_profile, out_inout_admission_profile, typed_ir)


# Original source bytes from noisemaker-for-cpp a15c4b6816a3cb4a1811a03429e4fbf84530c722.
# Unlike Classic Noise's scalar constants, Glitch's old structural verifier
# cannot authenticate the new nested guard shape. Preserve its entire original
# verifier, including every negative check, only for the old corpus context.
_GLITCH_PROFILE_SHA256 = "1cd2fae1915c3dca8b41e25aa06d2e4872bd659cdac725983a40f1163c058de5"
_COMPATIBILITY_SHA256 = "9a55bad28d4b7d9a8ab2cd4ad9af772b6d21a33ccf52f6d55deab5ddfa55eb6a"
_PRE_5976B7A6_CONSTANTS_SHA256 = "be337fed1a31e0dd07eb8b15e162a3f49c2e6372eb119fd1c0145400aaa57fba"
_NOISE_CONSTANTS = {
    "RAW_BYTES": 31258,
    "RAW_SHA256": "8629349c5cc4d44d7b4b7c1f0b3f27fe4fe82793461f26544c80a4fb5076d138",
    "NORMALIZED_BYTES": 14064,
    "NORMALIZED_SHA256": "9f97d19e355f32e3821057ba8859770a87cbec56c57946d14378764deb8da0f0",
    "OCTAVES_CALL_SPAN": "604:17-604:70",
    "OCTAVES_CALL_SHA256": "f9fe584857c36403bd636de831765b93b5559017183c4010dabc6c9adf1ea119",
    "OCTAVES_LOOP_SPAN": "533:5-558:6",
    "OCTAVES_LOOP_SHA256": "4430989cf0b3baeba7fd80c3c91bb4668a046978f707a3432815b4475f5cf8f5",
    "PRE_FUNCTIONS_SHA256": "c030e6d65da27c8aa1797ba1f53ca16d084e918e86247e1de47f67128de2d781",
    "PRE_WHOLE_PROGRAM_SHA256": "09adbca2ee6c780313fa55b584d8eb0a262c6b4c7c0ff3636349813b4302301f",
    "INTERFACE_SHA256": "82b04cb03ee9125c8fc9bfdcae13de8345bd65608bff0bc16a61ae488efcfb58",
    "PROJECTED_FUNCTIONS_SHA256": "1d89f895127b4fc13d12ce5f9b804203431eabff396f5aa3be972b0d95184187",
    "PROJECTED_WHOLE_PROGRAM_SHA256": "9633a89d1c5b065910d9f72bd7ea64fb0fadbec54b56475d9b92057473e93ab7",
    "PROJECTED_INTERFACE_SHA256": "43f05e6de87b33471bc2057d14d4a65326e2dab0797027c17caaf3010ef1d788",
}


def _glitch_profile():
    path = pathlib.Path(__file__).parent / "fixtures/historical/glitch_mat4_chain_profile.py"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != _GLITCH_PROFILE_SHA256:
        raise AssertionError("historical Glitch verifier source drift")
    name = "tools.glslcpp.frontend._historical_glitch_mat4_chain_profile"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves the declaring module during class construction.
    with mock.patch.dict(sys.modules, {name: module}):
        exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def _pre_5976b7a6_constants():
    """The profile constants the 0ed489ec corpus sources authenticate against.

    The 5976b7a6 corpus moved five programs' sources and 8ae8e2a fixed vector
    equality; the live profiles pin the new identities. Values are evaluated
    with only the live record classes in scope.
    """
    path = pathlib.Path(__file__).parent / "fixtures/historical/pre_5976b7a6_profile_constants.py"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != _PRE_5976B7A6_CONSTANTS_SHA256:
        raise AssertionError("historical pre-5976b7a6 profile constants drift")
    namespace = {"__builtins__": {"frozenset": frozenset}}
    for module in (fixed_array_in_parameter_proof, mutable_global_array_profile,
                   out_inout_admission_profile, typed_ir):
        for name, value in vars(module).items():
            if isinstance(value, type):
                namespace.setdefault(name, value)
    exec(compile(raw, str(path), "exec"), namespace)
    return namespace["VALUES"]


@contextlib.contextmanager
def historical_authority(spec: dict):
    """Select the immutable old corpus and its exact source authenticators."""
    if spec.get("revision") != corpus_census.HISTORICAL_REVISION:
        raise ValueError("historical reconstruction requires an explicit historical slice")
    for name in ("manifest.json", "metadata.json", "pending.json"):
        corpus_census.historical_document(name)
    glitch = _glitch_profile()
    # Preserve exactly the source identity and ABI inputs consumed by the two
    # compatibility readers. The fixture records its original full-document
    # digest; generated-TU hashes and other unused report fields are omitted.
    compatibility = (pathlib.Path(__file__).parent /
                     "fixtures/historical/backend_compatibility.json").read_bytes()
    if hashlib.sha256(compatibility).hexdigest() != _COMPATIBILITY_SHA256:
        raise AssertionError("historical compatibility projection drift")
    original_read_text = pathlib.Path.read_text
    compatibility_path = corpus_census.ROOT / "src/effects/generated/backend_compatibility.json"

    def historical_read_text(path, *args, **kwargs):
        if path == compatibility_path:
            return compatibility.decode("utf-8")
        return original_read_text(path, *args, **kwargs)

    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(emit_typed_cpp, "OSD_GLYPH_INDEX_TRUNCATES", False))
        stack.enter_context(mock.patch.object(emit_typed_cpp, "CURRENT_AUTHORITY_VALUE_COPIES", False))
        stack.enter_context(mock.patch.object(pathlib.Path, "read_text", historical_read_text))
        stack.enter_context(mock.patch.object(
            check_corpus, "REVISION", corpus_census.HISTORICAL_REVISION))
        # The historical authority shipped exactly these five adapter-status
        # programs; the live allowlist grew with the particle-family scatter
        # contracts and must not retroactively apply to frozen revisions.
        stack.enter_context(mock.patch.object(check_corpus, "_ADAPTERS", frozenset({
            "classicNoisedeck/fractal:fractal",
            "filter/historicPalette:historicPalette",
            "filter/palette:palette",
            "synth/julia:julia",
            "synth/remap:remap",
        })))
        stack.enter_context(mock.patch.object(
            check_corpus, "_CORPUS_RELATIVE",
            pathlib.PurePosixPath("tools/glslcpp/corpus") / corpus_census.HISTORICAL_REVISION))
        for module in (generate_typed_slice, emit_typed_cpp):
            stack.enter_context(mock.patch.object(
                module, "authenticate_glitch_mat4_chain", glitch.authenticate_glitch_mat4_chain))
        stack.enter_context(mock.patch.object(
            generate_typed_slice, "apply_glitch_mat4_chain", glitch.apply_glitch_mat4_chain))
        for name, value in _NOISE_CONSTANTS.items():
            stack.enter_context(mock.patch.object(noise_frontend_profile, name, value))
        # The historical vector equality was an always-truthy typed array, the
        # refract arms were rewritten to no-ops, and every profile authenticates
        # the 0ed489ec sources.
        stack.enter_context(mock.patch.object(emit_typed_cpp, "CURRENT_AUTHORITY_VECTOR_EQUALITY", False))
        stack.enter_context(mock.patch.object(fixed_array_in_parameter_proof, "_COMPATIBILITY_RHS", "noop"))
        for module_name, attribute, keys, value in _pre_5976b7a6_constants():
            module = sys.modules[module_name]
            if keys is None:
                stack.enter_context(mock.patch.object(module, attribute, value))
            else:
                stack.enter_context(mock.patch.dict(getattr(module, attribute), value))
        historical_lens_profile = lens_distortion_comparer_profile.PROFILE
        for module in (generate_typed_slice, emit_typed_cpp):
            stack.enter_context(mock.patch.object(
                module, "LENS_CUSTOM_COMPARER_PROFILE", historical_lens_profile))
        old_hoist = dataclasses.replace(
            dynamic_define_hoist.PROFILES[noise_frontend_profile.KEY],
            raw_sha256=_NOISE_CONSTANTS["RAW_SHA256"], raw_bytes=_NOISE_CONSTANTS["RAW_BYTES"])
        stack.enter_context(mock.patch.dict(
            dynamic_define_hoist.PROFILES, {noise_frontend_profile.KEY: old_hoist}))
        yield
