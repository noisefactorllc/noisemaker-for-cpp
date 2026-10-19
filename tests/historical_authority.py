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
_EFFECTS_FIXED_ARRAY_PROOF_SHA256 = "2f337505095bc75566724c4e52cf99f045f2ae0d84533b489950b5d4490bdaba"
_CRT_PROFILE_SHA256 = "703faf71656bf6a36afeb12ad12a4e8aa390b850aac4c9e79f9e527d4ad8c669"
_GLYPH_PROFILE_SHA256 = "f5af521501fe990e27e5168c4710fb38d06098416d08f22f2f6c9bb8e7759a14"
_COMPATIBILITY_SHA256 = "9a55bad28d4b7d9a8ab2cd4ad9af772b6d21a33ccf52f6d55deab5ddfa55eb6a"
_PRE_5976B7A6_CONSTANTS_SHA256 = "be337fed1a31e0dd07eb8b15e162a3f49c2e6372eb119fd1c0145400aaa57fba"
_CRT_VOCABULARY = {'CRT_ENTRY': {'effect_id': 'filter/crt',
               'normalized_bytes': 18054,
               'normalized_sha256': 'acd1c3f05c6d02052592aeb46bbbc49d23e18f4e83530498687903e00b4623fe',
               'outputs': ['fragColor'],
               'pass_index': 0,
               'pass_name': 'main',
               'program': 'crt',
               'program_key': 'filter/crt:crt',
               'raw_bytes': 19560,
               'raw_sha256': '62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c',
               'runtime_key': 'filter/crt:crt',
               'source': 'sources/filter/crt/crt.glsl',
               'status': 'generated',
               'varyings': []},
 'CRT_FUNCTIONS_SHA256': '1b67fa6d01135e98434bc9e6a4627f0d23565c81fa1e17cbdba10082e23e37a3',
 'CRT_FUNCTION_PROFILES': ((89,
                            'adjust_hue',
                            5,
                            'e48700fa4c4e07b3f55826d5b45cc919ea3e3ed5c520d0fb762f388892d607d3'),
                           (90,
                            'adjust_saturation',
                            4,
                            '05d846a08395fe65bc96437ce61acb012ba42f905f8b82eed6e4c41cfc4bbe9e'),
                           (91,
                            'animated_simplex_value',
                            8,
                            '352197ac3de92c0139a70f84075bf77cbf585cdbaf7920d9fd5635a4562500e7'),
                           (92,
                            'apply_vignette',
                            2,
                            'f2be0a5b59234e10cb6403d7fa881740929c6a120bba24f54cfabf0364d3eff3'),
                           (93,
                            'as_u32',
                            1,
                            '52db13ad3a1814e7408c7afb86ea6b875af0b89ec4cefbaf9b6078ba7b70cd6f'),
                           (94,
                            'blend_cosine',
                            3,
                            '4dba47b2ab19f66ba1c2e7cb7824e93951ead432702e77ac44e1375d771a6860'),
                           (95,
                            'blend_linear',
                            1,
                            '3c55bf9e312fceaa81ee58684251eb71e53dd972b51ea28c2ead7e65f40d6b2c'),
                           (96,
                            'clamp01',
                            1,
                            '5d20dd2c183bed0c13746cb3ca3b1340aeeefb280a82223bb73e9df82393a7fb'),
                           (97,
                            'clamp_index',
                            3,
                            'f180eb54bf36b9bda58df0be4f5520ec321af37952ffc3372fdd075ed8ac22cf'),
                           (98,
                            'compute_lens_offsets',
                            13,
                            '47332fcd4c91de0b794ebed756eb93e469c6d418e612e6abea0673ad93c62258'),
                           (99,
                            'compute_singularity',
                            5,
                            '51d8463de86bad652cedd483550364be941996653ce3417113620f45bad04c31'),
                           (100,
                            'fade',
                            1,
                            'e292a88053f33c4eadd9bfbe7ede0df78a45922f4f10134574beed4ff119714f'),
                           (101,
                            'fade_vec3',
                            1,
                            '649a934deb2e66089979eadcc97ff9732e0c3617c505707d07f72cdcbacc6cf8'),
                           (102,
                            'freq_for_shape',
                            7,
                            'dad7778bd028bfb3f898099751b2337e45f8254b79f2dede38e8d1fd0a660448'),
                           (103,
                            'get_scanline_base_values',
                            5,
                            'f172e85e6ba08b699b6753cda6e6b1d3a82591c88f7266efd94e22e6a46ac072'),
                           (104,
                            'get_scanline_value_interpolated',
                            3,
                            '1f3f67102c445c517df6e5f0f6e3ac2865cc5a0bad6dfbe24477664c61535667'),
                           (105,
                            'hash3',
                            3,
                            '498c7c564d712125c5d86a6371fc8033ab07499b579291c7fd04eb10066cadf2'),
                           (106,
                            'hsv_to_rgb',
                            15,
                            '43873d4b1e9fa8682543ecb3f4f562c747b49beeae64fbe5e281ec9d6bb98cb0'),
                           (107,
                            'lerp',
                            1,
                            '9d9ecb55ef978a8f50aa2664d1e753245d279ce25810b674f7e4ee1d32714f98'),
                           (108,
                            'main',
                            31,
                            'da62c05d1a013b993bcf4820fd84fb4b7eee640e30fa8df4c226d717fd4fb1e2'),
                           (109,
                            'mod289_vec3',
                            1,
                            '9eef4a5ee9d393857c69b44f28b32f697ba7adf253d8d2bbfcfe08554b3a03b3'),
                           (110,
                            'mod289_vec4',
                            1,
                            '2eadd7753b5e226b3c7e18c91462fb0b56c641203c8e1cafdca9b08a36485fb0'),
                           (111,
                            'normalized_sine',
                            1,
                            'c18a96221435819ea0d4de84dd9702765f1439d0e93309146631d83291f6f5a8'),
                           (112,
                            'periodic_value',
                            1,
                            '8869f721c8c67579e0a669f21dea07cec5352a3a053c6ba28edb655e2522ab52'),
                           (113,
                            'permute',
                            1,
                            'bd33a4e74b18f065bbf132ed4c6d40c137e29fe246ae8577f17bb552c35a0f98'),
                           (114,
                            'random_scalar',
                            1,
                            '9af506d4fd1b6092bc8e5eb5985333598e3e4cfd6a5133c33cb762d635f0a74d'),
                           (115,
                            'rgb_to_hsv',
                            7,
                            '7fddfbe7b05e204b136e5a18150cda42252fc39d9b762f00df8fdb05902a9f47'),
                           (116,
                            'sample_scanline_bilinear',
                            19,
                            '37225bab20e4eca1744dd30dd529de0c5930613d4c7073b354c49abfbc99fcd4'),
                           (117,
                            'simplex_noise',
                            46,
                            'c6fb1af5432cf0cbbf4e2812dca9b1d0935aa4532d23c70a0cf545d4d988a8b5'),
                           (118,
                            'simplex_random',
                            4,
                            'eef49ca4ef3414fc4140bd7ecfcca4d487c02a9c5416b410659d0486c3553819'),
                           (119,
                            'singularity_mask',
                            9,
                            '95b752c42a2327d3a4acc983892aaf9ed8a8c651fcc69b34f87d51023dd128e9'),
                           (120,
                            'taylor_inv_sqrt',
                            1,
                            'e04f914557a482d00efaa82d837e3357aeab07514b8aabecf2ca8ad60ad96ab1'),
                           (121,
                            'value_noise_3d',
                            19,
                            '2cc121f41b402b9c6594f6b02d9fa481ce61ba8573031426aee848f0af5933b1'),
                           (122,
                            'wrap_float',
                            4,
                            '06faad9ae9e7d10ebe30997326fb11ebd0d4a3a77e5358ae750aab25ec2ad8a2'),
                           (123,
                            'wrap_unit',
                            3,
                            '7b081cf2d2412e6c5fe636f06acdb6c47028c38965553c3b606e30a6602f3ef8')),
 'CRT_INTERFACE_SHA256': '9336d2b596c0efd955af699a27c788938c99d0e1e5c6438f66054e15fc135490',
 'CRT_WHOLE_SHA256': '7aa853a51316b1122750af1155411a5ca8c1e11cf02688a33d9ef6fcace5f6a2'}

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


def _crt_profile():
    path = pathlib.Path(__file__).parent / "fixtures/historical/crt_compatibility.py"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != _CRT_PROFILE_SHA256:
        raise AssertionError("historical CRT verifier source drift")
    name = "tools.glslcpp.frontend._historical_crt_compatibility"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {name: module}):
        exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def _glyph_profile():
    path = (pathlib.Path(__file__).parent /
            "fixtures/historical/glyph_map_nonnegative_int_shift_profile.py")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != _GLYPH_PROFILE_SHA256:
        raise AssertionError("historical Glyph Map verifier source drift")
    name = "tools.glslcpp.frontend._historical_glyph_map_profile"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
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


def _historical_effects_fixed_array_proof():
    """Load the exact 0ed Effects proof logic from the published baseline."""
    path = (pathlib.Path(__file__).parent
            / "fixtures/historical/effects_fixed_array_proof.py")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != _EFFECTS_FIXED_ARRAY_PROOF_SHA256:
        raise AssertionError("historical Effects fixed-array proof drift")
    namespace = dict(vars(fixed_array_in_parameter_proof))
    exec(compile(raw, str(path), "exec"), namespace)
    return namespace["_prove_effects"]


@contextlib.contextmanager
def historical_authority(spec: dict):
    """Select the immutable old corpus and its exact source authenticators."""
    if spec.get("revision") != corpus_census.HISTORICAL_REVISION:
        raise ValueError("historical reconstruction requires an explicit historical slice")
    for name in ("manifest.json", "metadata.json", "pending.json"):
        corpus_census.historical_document(name)
    glitch = _glitch_profile()
    crt = _crt_profile()
    glyph = _glyph_profile()
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

    def retain_effects_helpers(program, source_hash, profile):
        # The frozen artifacts emitted the authenticated unreachable helper.
        mutable_global_array_profile.authenticated_effects_emission_omission(
            program, source_hash, profile)
        return None

    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(
            emit_typed_cpp, "authenticated_effects_emission_omission",
            side_effect=retain_effects_helpers))
        # The frozen Surface milestone used its recorded Mat3 ABI. Its GLSL
        # source is unchanged, but the current port fixes matrix ingress.
        stack.enter_context(mock.patch.object(
            emit_typed_cpp, "_DOUBLE_CUBEMAP_BASIS_SOURCES", {}))
        stack.enter_context(mock.patch.object(emit_typed_cpp, "OSD_GLYPH_INDEX_TRUNCATES", False))
        stack.enter_context(mock.patch.object(emit_typed_cpp, "CURRENT_AUTHORITY_VALUE_COPIES", False))
        # The frozen milestones predate every authority 7f47340 lowering.
        stack.enter_context(emit_typed_cpp.authority_before_7f47340())
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
                module, "authenticate_crt_metal_sine", crt.authenticate_crt_metal_sine))
            stack.enter_context(mock.patch.object(
                module, "authenticate_glyph_map_nonnegative_int_shift",
                glyph.authenticate_glyph_map_nonnegative_int_shift))
        stack.enter_context(mock.patch.object(
            generate_typed_slice, "apply_glitch_mat4_chain", glitch.apply_glitch_mat4_chain))
        stack.enter_context(mock.patch.object(
            generate_typed_slice, "apply_crt_metal_sine", crt.apply_crt_metal_sine))
        stack.enter_context(mock.patch.object(
            generate_typed_slice, "apply_glyph_map_nonnegative_int_shift",
            glyph.apply_glyph_map_nonnegative_int_shift))
        for name, value in _CRT_VOCABULARY.items():
            stack.enter_context(mock.patch.object(generate_typed_slice, name, value))
        for name, value in _NOISE_CONSTANTS.items():
            stack.enter_context(mock.patch.object(noise_frontend_profile, name, value))
        # The historical vector equality was an always-truthy typed array, the
        # refract arms were rewritten to no-ops, and every profile authenticates
        # the 0ed489ec sources.
        stack.enter_context(mock.patch.object(emit_typed_cpp, "CURRENT_AUTHORITY_VECTOR_EQUALITY", False))
        # Before 5b686a4 every authenticated hash_uint body was substituted
        # with the murmur finalizer.
        stack.enter_context(mock.patch.object(emit_typed_cpp, "CURRENT_AUTHORITY_HASH_UINT_BY_BODY", False))
        # The frozen milestones fenced hash returns only in hash12/hash22.
        stack.enter_context(mock.patch.object(emit_typed_cpp, "HASH_PRECISION_FENCE_BY_SHAPE", False))
        stack.enter_context(mock.patch.object(fixed_array_in_parameter_proof, "_COMPATIBILITY_RHS", "noop"))
        for module_name, attribute, keys, value in _pre_5976b7a6_constants():
            module = sys.modules[module_name]
            if keys is None:
                stack.enter_context(mock.patch.object(module, attribute, value))
            else:
                stack.enter_context(mock.patch.dict(getattr(module, attribute), value))
        stack.enter_context(mock.patch.object(
            fixed_array_in_parameter_proof, "_prove_effects",
            _historical_effects_fixed_array_proof()))
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
