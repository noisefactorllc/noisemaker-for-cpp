"""Generate the small, schema-locked C++ typed-IR slice from pinned corpus data."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import pathlib
import shutil
import struct
import sys
import tempfile
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from tools.glslcpp import check_corpus, check_semantics
    from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.semantic_types import BOOL, FLOAT
    from tools.glslcpp.frontend.typed_ir import TypedExpression
    from tools.glslcpp.frontend.loop_proof import (
        SOURCE_GLOBAL_LITERAL_INT_CAPABILITY, SOURCE_GLOBAL_LITERAL_INT_KEYS,
        rebuild_authenticated_counted_loop_proofs,
        summarize_counted_loop_proofs)
    from tools.glslcpp.frontend.local_counter_proof import (
        CAPABILITY as LOCAL_COUNTER_CAPABILITY,
        COMPUTE_RANK_KEY, COMPUTE_RANK_NORMALIZED_SHA256, COMPUTE_RANK_RAW_SHA256,
        attach_discarded_local_counter_proofs)
    from tools.glslcpp.frontend.fixed_nine_table_proof import (
        CAPABILITY as FIXED_NINE_CAPABILITY, SOURCE_LOCKS,
        prove_fixed_nine_local_tables, source_provenance_error)
    from tools.glslcpp.frontend.fixed_grid_counter_store_proof import (
        CAPABILITY as FIXED_GRID_CAPABILITY,
        SOURCE_LOCKS as FIXED_GRID_SOURCE_LOCKS,
        prove_fixed_grid_counter_store,
        source_provenance_error as fixed_grid_source_provenance_error)
    from tools.glslcpp.frontend.refract_compatibility import (
        TRANSFORM as REFRACT_COMPATIBILITY_TRANSFORM,
        apply_refract_truthy_vector_noops)
    from tools.glslcpp.frontend.crt_compatibility import (
        CRT_KEY, TRANSFORM as CRT_COMPATIBILITY_TRANSFORM,
        apply_crt_metal_sine, authenticate_crt_metal_sine)
    from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
        CAPABILITY as FIXED_ARRAY_PARAMETER_CAPABILITY,
        REFRACT_KEY,
        attach_fixed_array_in_parameter_proof,
        prove_fixed_array_in_parameter,
        source_provenance_error as fixed_array_source_provenance_error)
    from tools.glslcpp.frontend.sacred_geometry_compatibility import (
        SACRED_KEY, TRANSFORM as SACRED_COMPATIBILITY_TRANSFORM,
        apply_sacred_star_number_division,
        authenticate_sacred_star_number_division)
    from tools.glslcpp.frontend.fixed_affine_centers13_proof import (
        CAPABILITY as FIXED_AFFINE_CENTERS13_CAPABILITY,
        attach_fixed_affine_centers13_proof,
        prove_fixed_affine_centers13,
        source_provenance_error as fixed_affine_source_provenance_error)
    from tools.glslcpp.frontend.semantic import analyze_program
    from tools.glslcpp.frontend.gather_sorted_round_profile import (
        GATHER_SORTED_KEY, PROFILE as GATHER_SORTED_ROUND_PROFILE,
        apply_gather_sorted_round_to_int,
        authenticate_gather_sorted_round_to_int)
    from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
        KEYS as LITERAL_VEC3_LANE_INDEX_KEYS,
        PROFILE as LITERAL_VEC3_LANE_INDEX_PROFILE,
        _selected_source_key as literal_vec3_lane_selected_source_key,
        apply_literal_vec3_lane_index,
        authenticate_literal_vec3_lane_index_post,
        authenticate_literal_vec3_lane_index_transition)
    from tools.glslcpp.frontend.lens_distortion_comparer_profile import (
        LENS_KEY as LENS_CUSTOM_COMPARER_KEY,
        PROFILE as LENS_CUSTOM_COMPARER_PROFILE,
        authenticate_lens_custom_comparer_final,
        authenticate_lens_custom_comparer_pre)
    from tools.glslcpp.frontend.smooth_edge_luma_weights_profile import (
        PROFILE as SMOOTH_EDGE_LUMA_WEIGHTS_PROFILE,
        SMOOTH_EDGE_KEY,
        apply_smooth_edge_luma_weights,
        authenticate_smooth_edge_luma_weights)
    from tools.glslcpp.frontend.grade_luma_weights_profile import (
        KEYS as GRADE_LUMA_WEIGHTS_KEYS, PROFILES as GRADE_LUMA_WEIGHTS_PROFILES,
        apply_grade_luma_weights, authenticate_grade_luma_weights)
    from tools.glslcpp.frontend.grade_index_expression_profile import (
        KEYS as GRADE_INDEX_EXPRESSION_KEYS,
        PROFILES as GRADE_INDEX_EXPRESSION_PROFILES,
        apply_grade_index_expression, authenticate_grade_index_expression)
    from tools.glslcpp.frontend.perlin_scalar_uint_xor_profile import (
        PERLIN_KEY, PROFILE as PERLIN_SCALAR_UINT_XOR_PROFILE,
        apply_perlin_scalar_uint_xor,
        authenticate_perlin_scalar_uint_xor)
    from tools.glslcpp.frontend.rotate_mat2_return_profile import (
        PROFILE as ROTATE_MAT2_RETURN_PROFILE, ROTATE_KEY,
        apply_rotate_mat2_return, authenticate_rotate_mat2_return)
    from tools.glslcpp.frontend.focus_blur_borrowed_sampler_profile import (
        FOCUS_BLUR_KEY, PROFILE as FOCUS_BLUR_BORROWED_SAMPLER_PROFILE,
        apply_focus_blur_borrowed_sampler_parameters,
        authenticate_focus_blur_borrowed_sampler_parameters)
    from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
        EXTRUDE_KEY, PROFILE as EXTRUDE_BVEC2_RELATIONAL_REDUCTION_PROFILE,
        apply_extrude_bvec2_relational_reduction,
        authenticate_extrude_bvec2_relational_reduction)
    from tools.glslcpp.frontend.caustic_word_hash_profile import (
        CAUSTIC_KEY, PROFILE as CAUSTIC_WORD_HASH_PROFILE,
        apply_caustic_word_hash, authenticate_caustic_word_hash)
    from tools.glslcpp.frontend.curl_vector_math_profile import (
        CURL_KEY, PROFILE as CURL_VECTOR_MATH_PROFILE,
        apply_curl_vector_math, authenticate_curl_vector_math)
    from tools.glslcpp.frontend.derivative_admission_profile import (
        DERIVATIVE_ADMISSION_KEYS, PROFILE as DERIVATIVE_ADMISSION_PROFILE,
        apply_derivative_admission, authenticate_derivative_admission)
    from tools.glslcpp.generate_kernels import GeneratorError, _validate_output_name
else:
    from . import check_corpus, check_semantics
    from .emit_typed_cpp import TypedEmissionError, render_typed_cpp
    from .frontend import parse_program
    from .frontend.semantic_types import BOOL, FLOAT
    from .frontend.typed_ir import TypedExpression
    from .frontend.loop_proof import (
        SOURCE_GLOBAL_LITERAL_INT_CAPABILITY, SOURCE_GLOBAL_LITERAL_INT_KEYS,
        rebuild_authenticated_counted_loop_proofs,
        summarize_counted_loop_proofs)
    from .frontend.local_counter_proof import (
        CAPABILITY as LOCAL_COUNTER_CAPABILITY,
        COMPUTE_RANK_KEY, COMPUTE_RANK_NORMALIZED_SHA256, COMPUTE_RANK_RAW_SHA256,
        attach_discarded_local_counter_proofs)
    from .frontend.fixed_nine_table_proof import (
        CAPABILITY as FIXED_NINE_CAPABILITY, SOURCE_LOCKS,
        prove_fixed_nine_local_tables, source_provenance_error)
    from .frontend.fixed_grid_counter_store_proof import (
        CAPABILITY as FIXED_GRID_CAPABILITY,
        SOURCE_LOCKS as FIXED_GRID_SOURCE_LOCKS,
        prove_fixed_grid_counter_store,
        source_provenance_error as fixed_grid_source_provenance_error)
    from .frontend.refract_compatibility import (
        TRANSFORM as REFRACT_COMPATIBILITY_TRANSFORM,
        apply_refract_truthy_vector_noops)
    from .frontend.crt_compatibility import (
        CRT_KEY, TRANSFORM as CRT_COMPATIBILITY_TRANSFORM,
        apply_crt_metal_sine, authenticate_crt_metal_sine)
    from .frontend.fixed_array_in_parameter_proof import (
        CAPABILITY as FIXED_ARRAY_PARAMETER_CAPABILITY,
        REFRACT_KEY,
        attach_fixed_array_in_parameter_proof,
        prove_fixed_array_in_parameter,
        source_provenance_error as fixed_array_source_provenance_error)
    from .frontend.sacred_geometry_compatibility import (
        SACRED_KEY, TRANSFORM as SACRED_COMPATIBILITY_TRANSFORM,
        apply_sacred_star_number_division,
        authenticate_sacred_star_number_division)
    from .frontend.fixed_affine_centers13_proof import (
        CAPABILITY as FIXED_AFFINE_CENTERS13_CAPABILITY,
        attach_fixed_affine_centers13_proof,
        prove_fixed_affine_centers13,
        source_provenance_error as fixed_affine_source_provenance_error)
    from .frontend.semantic import analyze_program
    from .frontend.gather_sorted_round_profile import (
        GATHER_SORTED_KEY, PROFILE as GATHER_SORTED_ROUND_PROFILE,
        apply_gather_sorted_round_to_int,
        authenticate_gather_sorted_round_to_int)
    from .frontend.literal_vec3_lane_index_profile import (
        KEYS as LITERAL_VEC3_LANE_INDEX_KEYS,
        PROFILE as LITERAL_VEC3_LANE_INDEX_PROFILE,
        _selected_source_key as literal_vec3_lane_selected_source_key,
        apply_literal_vec3_lane_index,
        authenticate_literal_vec3_lane_index_post,
        authenticate_literal_vec3_lane_index_transition)
    from .frontend.lens_distortion_comparer_profile import (
        LENS_KEY as LENS_CUSTOM_COMPARER_KEY,
        PROFILE as LENS_CUSTOM_COMPARER_PROFILE,
        authenticate_lens_custom_comparer_final,
        authenticate_lens_custom_comparer_pre)
    from .frontend.smooth_edge_luma_weights_profile import (
        PROFILE as SMOOTH_EDGE_LUMA_WEIGHTS_PROFILE,
        SMOOTH_EDGE_KEY,
        apply_smooth_edge_luma_weights,
        authenticate_smooth_edge_luma_weights)
    from .frontend.grade_luma_weights_profile import (
        KEYS as GRADE_LUMA_WEIGHTS_KEYS, PROFILES as GRADE_LUMA_WEIGHTS_PROFILES,
        apply_grade_luma_weights, authenticate_grade_luma_weights)
    from .frontend.grade_index_expression_profile import (
        KEYS as GRADE_INDEX_EXPRESSION_KEYS,
        PROFILES as GRADE_INDEX_EXPRESSION_PROFILES,
        apply_grade_index_expression, authenticate_grade_index_expression)
    from .frontend.perlin_scalar_uint_xor_profile import (
        PERLIN_KEY, PROFILE as PERLIN_SCALAR_UINT_XOR_PROFILE,
        apply_perlin_scalar_uint_xor,
        authenticate_perlin_scalar_uint_xor)
    from .frontend.rotate_mat2_return_profile import (
        PROFILE as ROTATE_MAT2_RETURN_PROFILE, ROTATE_KEY,
        apply_rotate_mat2_return, authenticate_rotate_mat2_return)
    from .frontend.focus_blur_borrowed_sampler_profile import (
        FOCUS_BLUR_KEY, PROFILE as FOCUS_BLUR_BORROWED_SAMPLER_PROFILE,
        apply_focus_blur_borrowed_sampler_parameters,
        authenticate_focus_blur_borrowed_sampler_parameters)
    from .frontend.extrude_bvec2_relational_reduction_profile import (
        EXTRUDE_KEY, PROFILE as EXTRUDE_BVEC2_RELATIONAL_REDUCTION_PROFILE,
        apply_extrude_bvec2_relational_reduction,
        authenticate_extrude_bvec2_relational_reduction)
    from .frontend.caustic_word_hash_profile import (
        CAUSTIC_KEY, PROFILE as CAUSTIC_WORD_HASH_PROFILE,
        apply_caustic_word_hash, authenticate_caustic_word_hash)
    from .frontend.curl_vector_math_profile import (
        CURL_KEY, PROFILE as CURL_VECTOR_MATH_PROFILE,
        apply_curl_vector_math, authenticate_curl_vector_math)
    from .frontend.derivative_admission_profile import (
        DERIVATIVE_ADMISSION_KEYS, PROFILE as DERIVATIVE_ADMISSION_PROFILE,
        apply_derivative_admission, authenticate_derivative_admission)
    from .generate_kernels import GeneratorError, _validate_output_name


SCHEMA = 1
EMITTER = "typed-ir-v1"
_ROOT = pathlib.Path(__file__).resolve().parents[2]
_OUTPUTS = ("typed_manifest.json", "typed_slice.cpp")
_TYPED_DIRECTORY = pathlib.PurePosixPath("src/typed_generated")
_CATALOG_HEADER = pathlib.PurePosixPath("include/noisemaker/generated/catalog.hpp")
APPROVED_CAPABILITIES = (
    "assign", "abs", "atan", "blocks", "clamp", "conditional", "cos", "constructors", "distance", "dot", "exp",
    "floor", "fract", "functions", "if", "integer-modulo", "length", "mat2-vector-multiply", "max", "min", "mix", "mod", "multi-declarations", "normalize", "pow",
    "radians", "scalar-vector-arithmetic", "sign", "sin", "smoothstep", "sqrt", "step",
    "swizzles", "texelFetch", "texture", "textureSize", "uint-vector-bitwise", "counted-for-v1",
    LOCAL_COUNTER_CAPABILITY,
    FIXED_NINE_CAPABILITY,
    FIXED_GRID_CAPABILITY,
    FIXED_ARRAY_PARAMETER_CAPABILITY,
    FIXED_AFFINE_CENTERS13_CAPABILITY,
    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
)
_BUILTINS = frozenset(item for item in APPROVED_CAPABILITIES if item not in {
    "assign", "blocks", "conditional", "constructors", "functions", "if", "integer-modulo",
    "mat2-vector-multiply", "multi-declarations", "scalar-vector-arithmetic", "swizzles",
    "uint-vector-bitwise", "counted-for-v1", LOCAL_COUNTER_CAPABILITY,
    FIXED_NINE_CAPABILITY,
    FIXED_GRID_CAPABILITY,
    FIXED_ARRAY_PARAMETER_CAPABILITY,
    FIXED_AFFINE_CENTERS13_CAPABILITY,
    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
})
APPROVED_TYPES = (
    "bool", "float", "int", "uint", "vec2", "vec3", "vec4", "ivec2", "ivec3", "ivec4",
    "uvec2", "uvec3", "uvec4", "mat2", "sampler2D", "void",
)
APPROVED_BINARY_OPERATORS = (
    "!=", "%", "&&", "*", "+", "-", "/", "<", "<=", "==", ">", ">=", ">>", "^", "||",
)
APPROVED_ASSIGNMENT_OPERATORS = ("*=", "+=", "-=", "/=", "=", "^=")

DEGAUSS_KEY = "filter/degauss:degauss"
DEGAUSS_CANONICAL_FACTORY = "canonicalFactory45"
DEGAUSS_CANONICAL_FACTORY_TEXT_SHA256 = "f515a7ac409c98fc420d9fa9a7e460eb37018b34e3be40419191fc7655a29c38"
DEGAUSS_CANONICAL_RUNTIME_SHA256 = "e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56"
DEGAUSS_TAU_F32_BITS = 0x40C90FDB
DEGAUSS_FUNCTIONS_SHA256 = "f68d742e44e341c1332f8c37ac8544aaa8c5bef979e496a27d45ac28ba48f95a"
DEGAUSS_WHOLE_SHA256 = "73e7e3e3b5e0b7ee9b4e1558d51fc14a01e9820c89674a0b5e42e568bec8d13d"
DEGAUSS_INTERFACE_SHA256 = "6ceb3a3a3c7b0263b29d9950790bbe24b186759a4048b593b0a5447b733ae227"
DEGAUSS_FUNCTION_PROFILES = (
    (52, "as_u32", 1, "5b794fbe001df4116421749d5d0378b6088169d370876fc27757e01ba234b387"),
    (53, "clamp01", 1, "4c77ec274b621bf6b9621b72dff5cf2653f468fd08610b13d16d2d4e301c5114"),
    (54, "compute_noise_value", 14, "76e9489c1e667d2906e040ed25e707f5cea3bd15c27eade92078c466fd6b8fdf"),
    (55, "freq_for_shape", 5, "7c20f25c092dbdd8b75891e74a498022a3a68a74dd8c9aa93a1f8f95ce71cdd9"),
    (56, "main", 27, "e7a5c14a35384ba7174f8af83b428fa412b855678b9d626a7b79a9c5779b04d5"),
    (57, "mod289_vec3", 1, "6a515431e7e453f7106fbb56e352302de98d21ff1578db537ea9b24e53aafbb6"),
    (58, "mod289_vec4", 1, "26e443d7caf37c61b0e1b51fd96ce8f7a0a777e5cbf533487c3c13bc996196c9"),
    (59, "normalized_sine", 1, "4056ee25e08f248238b5308b0a724c80885a04df8b3708e2af2c9b8411efe328"),
    (60, "periodic_value", 1, "717462992b550c078e3bcbcfa4693f7cf48716eca4b8bae02549f3a4bc2aa1a5"),
    (61, "permute", 1, "107a98b3f0a23f2129f707ed9092be4cd36e397984b606b0d37ea2db315d174c"),
    (62, "sample_bilinear", 21, "79c10ddc45c358c67f353150276631ba56e4bdcab0d3760d84afe952c3859f9e"),
    (63, "simplex_noise", 46, "79091353afa3432b82c5aece16c4e4e11cf08de40368e05e544c8509b315fc32"),
    (64, "singularity_mask", 9, "8a9cd929ba8eae78b11714183c7afc78c5e2c6c31abf72ba51cd50ed6bf03de8"),
    (65, "taylor_inv_sqrt", 1, "e4fa063d2b026b8ba09a7b0ef42a05ec3564913f1750b997848821faa9412536"),
    (66, "warped_channel_value", 14, "e730903759accd745d885164f16cde91477a91a2c7589685b8017d573030dabb"),
    (67, "wrap_float", 4, "f0915a8e46372c29b4cd2dbbf74f1771242d1ba0496f1f4ef4434cf61c4abe74"),
    (68, "wrap_index", 4, "7c96a9fda62b2c97b48d061a9c90305f6b5799235ebc663045e774e836de29db"),
)
DEGAUSS_ENTRY = {
    "effect_id": "filter/degauss", "program": "degauss",
    "program_key": DEGAUSS_KEY, "status": "generated",
    "source": "sources/filter/degauss/degauss.glsl", "raw_bytes": 10803,
    "raw_sha256": "915f208e47a5bf012a3e0583e03a7ee888b7103d5834b386d32c916b8715050c",
    "normalized_bytes": 10512,
    "normalized_sha256": "7d413b240236506511f405319025281a92eb1108c6193ef26a6d0d7bcbae7560",
    "outputs": ["fragColor"], "varyings": [], "pass_index": 0,
    "pass_name": "main", "runtime_key": DEGAUSS_KEY,
}
DEGAUSS_METADATA_EFFECT = {
    "func": "degauss", "kind": "filter", "namespace": "filter",
    "params": {
        "direction": {"default": 0, "max": 180, "min": -180, "type": "float",
                      "ui": {"control": "slider", "label": "direction"},
                      "uniform": "direction"},
        "displacement": {"default": 0.0625, "max": 0.25, "min": 0, "step": 0.001,
                         "type": "float",
                         "ui": {"control": "slider", "label": "displacement"},
                         "uniform": "displacement"},
        "seed": {"default": 1, "max": 100, "min": 1, "step": 1, "type": "int",
                 "ui": {"control": "slider", "label": "seed"}, "uniform": "seed"},
        "speed": {"default": 1, "max": 2, "min": 0, "step": 0.1, "type": "float",
                  "ui": {"control": "slider", "label": "speed"}, "uniform": "speed"},
    },
    "passes": [{"inputs": {"inputTex": "inputTex"}, "key": DEGAUSS_KEY,
                "name": "main", "outputs": {"fragColor": "outputTex"},
                "program": "degauss",
                "uniforms": {"direction": "direction", "displacement": "displacement",
                             "seed": "seed", "speed": "speed"}}],
    "textures": {},
}

CRT_CANONICAL_FACTORY = "canonicalFactory44"
CRT_CANONICAL_FACTORY_TEXT_SHA256 = "6d65f4984f8749ca7cdfec976e082662d3a7ad614aabb15ce8a168fca7d8e303"
CRT_PUBLIC_FACTORY = "crtFactory"
CRT_PUBLIC_FACTORY_TEXT_SHA256 = "240972f95f908452bf87fc681e360553759f374fa81613adc415a5a7c5eb4bf7"
CRT_PUBLIC_ADAPTER_SHA256 = "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc"
CRT_CANONICAL_RUNTIME_SHA256 = "e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56"
CRT_PI_F32_BITS = 0x40490FDB
CRT_TAU_F32_BITS = 0x40C90FDB
CRT_INV_THREE_F32_BITS = 0x3EAAAAAB
CRT_INV_TAU_F32_BITS = 0x3E22F983
CRT_FUNCTIONS_SHA256 = "1b67fa6d01135e98434bc9e6a4627f0d23565c81fa1e17cbdba10082e23e37a3"
CRT_WHOLE_SHA256 = "7aa853a51316b1122750af1155411a5ca8c1e11cf02688a33d9ef6fcace5f6a2"
CRT_INTERFACE_SHA256 = "9336d2b596c0efd955af699a27c788938c99d0e1e5c6438f66054e15fc135490"
CRT_FUNCTION_PROFILES = (
    (89, "adjust_hue", 5, "e48700fa4c4e07b3f55826d5b45cc919ea3e3ed5c520d0fb762f388892d607d3"),
    (90, "adjust_saturation", 4, "05d846a08395fe65bc96437ce61acb012ba42f905f8b82eed6e4c41cfc4bbe9e"),
    (91, "animated_simplex_value", 8, "352197ac3de92c0139a70f84075bf77cbf585cdbaf7920d9fd5635a4562500e7"),
    (92, "apply_vignette", 2, "f2be0a5b59234e10cb6403d7fa881740929c6a120bba24f54cfabf0364d3eff3"),
    (93, "as_u32", 1, "52db13ad3a1814e7408c7afb86ea6b875af0b89ec4cefbaf9b6078ba7b70cd6f"),
    (94, "blend_cosine", 3, "4dba47b2ab19f66ba1c2e7cb7824e93951ead432702e77ac44e1375d771a6860"),
    (95, "blend_linear", 1, "3c55bf9e312fceaa81ee58684251eb71e53dd972b51ea28c2ead7e65f40d6b2c"),
    (96, "clamp01", 1, "5d20dd2c183bed0c13746cb3ca3b1340aeeefb280a82223bb73e9df82393a7fb"),
    (97, "clamp_index", 3, "f180eb54bf36b9bda58df0be4f5520ec321af37952ffc3372fdd075ed8ac22cf"),
    (98, "compute_lens_offsets", 13, "47332fcd4c91de0b794ebed756eb93e469c6d418e612e6abea0673ad93c62258"),
    (99, "compute_singularity", 5, "51d8463de86bad652cedd483550364be941996653ce3417113620f45bad04c31"),
    (100, "fade", 1, "e292a88053f33c4eadd9bfbe7ede0df78a45922f4f10134574beed4ff119714f"),
    (101, "fade_vec3", 1, "649a934deb2e66089979eadcc97ff9732e0c3617c505707d07f72cdcbacc6cf8"),
    (102, "freq_for_shape", 7, "dad7778bd028bfb3f898099751b2337e45f8254b79f2dede38e8d1fd0a660448"),
    (103, "get_scanline_base_values", 5, "f172e85e6ba08b699b6753cda6e6b1d3a82591c88f7266efd94e22e6a46ac072"),
    (104, "get_scanline_value_interpolated", 3, "1f3f67102c445c517df6e5f0f6e3ac2865cc5a0bad6dfbe24477664c61535667"),
    (105, "hash3", 3, "498c7c564d712125c5d86a6371fc8033ab07499b579291c7fd04eb10066cadf2"),
    (106, "hsv_to_rgb", 15, "43873d4b1e9fa8682543ecb3f4f562c747b49beeae64fbe5e281ec9d6bb98cb0"),
    (107, "lerp", 1, "9d9ecb55ef978a8f50aa2664d1e753245d279ce25810b674f7e4ee1d32714f98"),
    (108, "main", 31, "da62c05d1a013b993bcf4820fd84fb4b7eee640e30fa8df4c226d717fd4fb1e2"),
    (109, "mod289_vec3", 1, "9eef4a5ee9d393857c69b44f28b32f697ba7adf253d8d2bbfcfe08554b3a03b3"),
    (110, "mod289_vec4", 1, "2eadd7753b5e226b3c7e18c91462fb0b56c641203c8e1cafdca9b08a36485fb0"),
    (111, "normalized_sine", 1, "c18a96221435819ea0d4de84dd9702765f1439d0e93309146631d83291f6f5a8"),
    (112, "periodic_value", 1, "8869f721c8c67579e0a669f21dea07cec5352a3a053c6ba28edb655e2522ab52"),
    (113, "permute", 1, "bd33a4e74b18f065bbf132ed4c6d40c137e29fe246ae8577f17bb552c35a0f98"),
    (114, "random_scalar", 1, "9af506d4fd1b6092bc8e5eb5985333598e3e4cfd6a5133c33cb762d635f0a74d"),
    (115, "rgb_to_hsv", 7, "7fddfbe7b05e204b136e5a18150cda42252fc39d9b762f00df8fdb05902a9f47"),
    (116, "sample_scanline_bilinear", 19, "37225bab20e4eca1744dd30dd529de0c5930613d4c7073b354c49abfbc99fcd4"),
    (117, "simplex_noise", 46, "c6fb1af5432cf0cbbf4e2812dca9b1d0935aa4532d23c70a0cf545d4d988a8b5"),
    (118, "simplex_random", 4, "eef49ca4ef3414fc4140bd7ecfcca4d487c02a9c5416b410659d0486c3553819"),
    (119, "singularity_mask", 9, "95b752c42a2327d3a4acc983892aaf9ed8a8c651fcc69b34f87d51023dd128e9"),
    (120, "taylor_inv_sqrt", 1, "e04f914557a482d00efaa82d837e3357aeab07514b8aabecf2ca8ad60ad96ab1"),
    (121, "value_noise_3d", 19, "2cc121f41b402b9c6594f6b02d9fa481ce61ba8573031426aee848f0af5933b1"),
    (122, "wrap_float", 4, "06faad9ae9e7d10ebe30997326fb11ebd0d4a3a77e5358ae750aab25ec2ad8a2"),
    (123, "wrap_unit", 3, "7b081cf2d2412e6c5fe636f06acdb6c47028c38965553c3b606e30a6602f3ef8"),
)
CRT_ENTRY = {
    "effect_id": "filter/crt", "program": "crt", "program_key": CRT_KEY,
    "status": "generated", "source": "sources/filter/crt/crt.glsl",
    "raw_bytes": 19560,
    "raw_sha256": "62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c",
    "normalized_bytes": 18054,
    "normalized_sha256": "acd1c3f05c6d02052592aeb46bbbc49d23e18f4e83530498687903e00b4623fe",
    "outputs": ["fragColor"], "varyings": [], "pass_index": 0,
    "pass_name": "main", "runtime_key": CRT_KEY,
}
CRT_METADATA_EFFECT = {
    "func": "crt", "kind": "filter", "namespace": "filter",
    "params": {
        "alpha": {"default": 0.5, "max": 1, "min": 0, "step": 0.01,
                  "type": "float", "ui": {"control": "slider", "label": "alpha"},
                  "uniform": "alpha", "zero": 0},
        "seed": {"default": 1, "max": 100, "min": 1, "step": 1,
                 "type": "int", "ui": {"control": "slider", "label": "seed"},
                 "uniform": "seed"},
        "speed": {"default": 1, "max": 5, "min": 0, "step": 0.1,
                  "type": "float", "ui": {"control": "slider", "label": "speed"},
                  "uniform": "speed"},
    },
    "passes": [{"inputs": {"inputTex": "inputTex"}, "key": CRT_KEY,
                "name": "main", "outputs": {"fragColor": "outputTex"},
                "program": "crt",
                "uniforms": {"alpha": "alpha", "seed": "seed", "speed": "speed"}}],
    "textures": {},
}


def _sha256(data: bytes) -> str: return hashlib.sha256(data).hexdigest()


def validate_current_vocabulary_degauss(
        typed, entry: dict[str, Any], declared_defines: dict[str, int], *,
        compatibility_transform: str | None,
        numeric_literal_contract: str,
        metadata_effect: dict[str, Any]) -> None:
    """Authenticate the exact current-vocabulary Degauss publication profile."""
    def reject(field: str) -> None:
        raise GeneratorError(f"{DEGAUSS_KEY}: current-vocabulary profile mismatch: {field}")

    if entry != DEGAUSS_ENTRY: reject("corpus entry")
    if typed.key != DEGAUSS_KEY: reject("typed key")
    raw_bytes = typed.raw_source.encode("utf-8")
    normalized_bytes = typed.source.encode("utf-8")
    if (len(raw_bytes) != DEGAUSS_ENTRY["raw_bytes"]
            or _sha256(raw_bytes) != DEGAUSS_ENTRY["raw_sha256"]):
        reject("raw source")
    if (len(normalized_bytes) != DEGAUSS_ENTRY["normalized_bytes"]
            or _sha256(normalized_bytes) != DEGAUSS_ENTRY["normalized_sha256"]):
        reject("normalized source")
    if declared_defines != {} or typed.preprocessor_defines != ():
        reject("defines")
    if compatibility_transform is not None: reject("compatibility transform")
    if numeric_literal_contract != "glsl-f32": reject("numeric literal contract")
    if metadata_effect != DEGAUSS_METADATA_EFFECT: reject("metadata effect")

    functions = tuple(
        (function.signature.id, function.signature.name, len(function.body),
         _sha256(repr(function).encode("utf-8")))
        for function in typed.functions)
    if functions != DEGAUSS_FUNCTION_PROFILES: reject("function profile")
    if _sha256(repr(typed.functions).encode("utf-8")) != DEGAUSS_FUNCTIONS_SHA256:
        reject("function tuple")
    whole = (
        typed.key, typed.source, typed.raw_source, typed.declarations,
        typed.functions, typed.resources, typed.body_status,
        typed.local_type_names, typed.structs, typed.uniform_blocks,
        typed.interface_symbols, typed.builtin_symbols,
        typed.counted_loop_proof, typed.preprocessor_defines,
    )
    if _sha256(repr(whole).encode("utf-8")) != DEGAUSS_WHOLE_SHA256:
        reject("whole program")
    interface = (
        typed.declarations, typed.resources, typed.local_type_names,
        typed.structs, typed.uniform_blocks, typed.interface_symbols,
        typed.builtin_symbols, typed.preprocessor_defines,
    )
    if _sha256(repr(interface).encode("utf-8")) != DEGAUSS_INTERFACE_SHA256:
        reject("interface")

    if any(value is not None for value in (
            typed.fixed_nine_table_proof,
            typed.fixed_grid_counter_store_proof,
            typed.fixed_array_in_parameter_proof,
            typed.fixed_affine_centers13_proof)):
        reject("foreign proof")
    declarations = tuple(
        (declaration.symbol.id, declaration.symbol.name,
         declaration.type.display(), declaration.symbol.storage,
         declaration.symbol.writable, declaration.symbol.direction,
         None if declaration.initializer is None else (
             declaration.initializer.kind, declaration.initializer.literal))
        for declaration in typed.declarations)
    expected_declarations = (
        (1, "TAU", "float", "const", False, "in", ("literal", "6.28318530717958647692")),
        (2, "inputTex", "sampler2D", "uniform", False, "in", None),
        (3, "resolution", "vec2", "uniform", False, "in", None),
        (4, "tileOffset", "vec2", "uniform", False, "in", None),
        (5, "fullResolution", "vec2", "uniform", False, "in", None),
        (6, "time", "float", "uniform", False, "in", None),
        (7, "displacement", "float", "uniform", False, "in", None),
        (8, "speed", "float", "uniform", False, "in", None),
        (9, "seed", "int", "uniform", False, "in", None),
        (10, "direction", "float", "uniform", False, "in", None),
        (11, "fragColor", "vec4", "output", True, "in", None),
    )
    if declarations != expected_declarations: reject("declarations")
    tau_word = struct.unpack("<I", struct.pack(
        "<f", float(declarations[0][-1][1])))[0]
    if tau_word != DEGAUSS_TAU_F32_BITS: reject("TAU f32 word")
    resources = typed.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != (
            ("inputTex", "resolution", "tileOffset", "fullResolution", "time",
             "displacement", "speed", "seed", "direction"),
            ("inputTex",), ("fragColor",), True, False)):
        reject("resources")
    proof = typed.counted_loop_proof
    if ((proof.loop_count, proof.unproved_loop_count, proof.max_effective_depth,
         proof.max_lexical_product, proof.entrypoint_charge,
         proof.call_graph_acyclic) != (0, 0, 0, 0, 0, True)):
        reject("loop proof")


def validate_current_vocabulary_crt(
        typed, entry: dict[str, Any], declared_defines: dict[str, int], *,
        compatibility_transform: str | None,
        numeric_literal_contract: str,
        metadata_effect: dict[str, Any]) -> None:
    """Authenticate the exact transformed public-adapter CRT profile."""
    def reject(field: str) -> None:
        raise GeneratorError(f"{CRT_KEY}: current-vocabulary profile mismatch: {field}")

    if entry != CRT_ENTRY: reject("corpus entry")
    if typed.key != CRT_KEY: reject("typed key")
    raw_bytes = typed.raw_source.encode("utf-8")
    normalized_bytes = typed.source.encode("utf-8")
    if (len(raw_bytes) != CRT_ENTRY["raw_bytes"]
            or _sha256(raw_bytes) != CRT_ENTRY["raw_sha256"]):
        reject("raw source")
    if (len(normalized_bytes) != CRT_ENTRY["normalized_bytes"]
            or _sha256(normalized_bytes) != CRT_ENTRY["normalized_sha256"]):
        reject("normalized source")
    if declared_defines != {} or typed.preprocessor_defines != ():
        reject("defines")
    if compatibility_transform != CRT_COMPATIBILITY_TRANSFORM:
        reject("compatibility transform")
    if numeric_literal_contract != "glsl-f32": reject("numeric literal contract")
    if metadata_effect != CRT_METADATA_EFFECT: reject("metadata effect")
    try:
        authenticate_crt_metal_sine(typed, CRT_ENTRY["raw_sha256"])
    except ValueError as error:
        reject(str(error))

    functions = tuple(
        (function.signature.id, function.signature.name, len(function.body),
         _sha256(repr(function).encode("utf-8")))
        for function in typed.functions)
    if functions != CRT_FUNCTION_PROFILES: reject("function profile")
    if _sha256(repr(typed.functions).encode("utf-8")) != CRT_FUNCTIONS_SHA256:
        reject("function tuple")
    whole = (
        typed.key, typed.source, typed.raw_source, typed.declarations,
        typed.functions, typed.resources, typed.body_status,
        typed.local_type_names, typed.structs, typed.uniform_blocks,
        typed.interface_symbols, typed.builtin_symbols,
        typed.counted_loop_proof, typed.preprocessor_defines,
    )
    if _sha256(repr(whole).encode("utf-8")) != CRT_WHOLE_SHA256:
        reject("whole program")
    interface = (
        typed.declarations, typed.resources, typed.local_type_names,
        typed.structs, typed.uniform_blocks, typed.interface_symbols,
        typed.builtin_symbols, typed.preprocessor_defines,
    )
    if _sha256(repr(interface).encode("utf-8")) != CRT_INTERFACE_SHA256:
        reject("interface")
    if any(value is not None for value in (
            typed.fixed_nine_table_proof,
            typed.fixed_grid_counter_store_proof,
            typed.fixed_array_in_parameter_proof,
            typed.fixed_affine_centers13_proof)):
        reject("foreign proof")

    declarations = tuple(
        (declaration.symbol.id, declaration.symbol.name,
         declaration.type.display(), declaration.symbol.storage,
         declaration.symbol.writable, declaration.symbol.direction,
         None if declaration.initializer is None else (
             declaration.initializer.kind, declaration.initializer.literal))
        for declaration in typed.declarations)
    expected_declarations = (
        (1, "PI", "float", "const", False, "in",
         ("literal", "3.14159265358979323846")),
        (2, "TAU", "float", "const", False, "in",
         ("literal", "6.28318530717958647692")),
        (3, "INV_THREE", "float", "const", False, "in",
         ("literal", "0.3333333333333333")),
        (4, "inputTex", "sampler2D", "uniform", False, "in", None),
        (5, "resolution", "vec2", "uniform", False, "in", None),
        (6, "tileOffset", "vec2", "uniform", False, "in", None),
        (7, "fullResolution", "vec2", "uniform", False, "in", None),
        (8, "time", "float", "uniform", False, "in", None),
        (9, "speed", "float", "uniform", False, "in", None),
        (10, "seed", "int", "uniform", False, "in", None),
        (11, "alpha", "float", "uniform", False, "in", None),
        (12, "renderScale", "float", "uniform", False, "in", None),
        (88, "fragColor", "vec4", "output", True, "in", None),
    )
    if declarations != expected_declarations: reject("declarations")
    literal_words = tuple(struct.unpack(
        "<I", struct.pack("<f", float(declarations[index][-1][1])))[0]
                          for index in range(3))
    if literal_words != (CRT_PI_F32_BITS, CRT_TAU_F32_BITS,
                         CRT_INV_THREE_F32_BITS):
        reject("constant f32 words")
    resources = typed.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != (
            ("inputTex", "resolution", "tileOffset", "fullResolution",
             "time", "speed", "seed", "alpha", "renderScale"),
            ("inputTex",), ("fragColor",), True, False)):
        reject("resources")
    proof = typed.counted_loop_proof
    if ((proof.loop_count, proof.unproved_loop_count, proof.max_effective_depth,
         proof.max_lexical_product, proof.entrypoint_charge,
         proof.call_graph_acyclic) != (0, 0, 0, 0, 0, True)):
        reject("loop proof")

    expressions = []
    def expression(value) -> None:
        expressions.append(value)
        for child in value.children: expression(child)
    def statement(value) -> None:
        for item in value.expressions: expression(item)
        for child in value.children: statement(child)
    main = next((function for function in typed.functions
                 if function.id == 108 and function.name == "main"), None)
    if main is None: reject("main")
    for item in main.body: statement(item)
    locals_by_id = {value.symbol_id: value for value in expressions
                    if value.kind == "declaration"
                    and value.symbol_id in {193, 194, 205}}
    if set(locals_by_id) != {193, 194, 205}: reject("shadow declarations")
    time_local, speed_local, alpha_local = (
        locals_by_id[193], locals_by_id[194], locals_by_id[205])
    if not (time_local.symbol is not None and time_local.symbol.name == "time"
            and time_local.symbol.storage == "local" and time_local.symbol.writable
            and len(time_local.children) == 1
            and time_local.children[0].kind == "id"
            and time_local.children[0].symbol_id == 8):
        reject("time shadow")
    if not (speed_local.symbol is not None and speed_local.symbol.name == "speed"
            and speed_local.symbol.storage == "local" and speed_local.symbol.writable
            and len(speed_local.children) == 1
            and speed_local.children[0].kind == "id"
            and speed_local.children[0].symbol_id == 9):
        reject("speed shadow")
    if not (alpha_local.symbol is not None and alpha_local.symbol.name == "alpha"
            and alpha_local.symbol.storage == "local" and alpha_local.symbol.writable
            and len(alpha_local.children) == 1
            and alpha_local.children[0].kind == "swizzle"
            and alpha_local.children[0].member == "w"
            and len(alpha_local.children[0].children) == 1
            and alpha_local.children[0].children[0].symbol_id == 203):
        reject("alpha shadow")
    if sum(value.kind == "id" and value.symbol_id == 205
           for value in expressions) != 0:
        reject("dead alpha shadow")
    fetches = [value for value in expressions
               if value.kind == "builtin" and value.callee == "texelFetch"]
    expected_fetches = (
        ((475, 21, 475, 87), "8b7cfdce594e15fe0f5ce45a7756cd79b50ba8e257cfc62f1f4d1c4ffd284cd1"),
        ((508, 24, 508, 68), "a29686254b425ea3ec472aed74ba86e04d6b3f29f825f87db4f3c0aca964a129"),
        ((540, 29, 540, 102), "d413d488d1165f5cb19d855488c43f51fd959c550219f7f99d44fe5a3575bbb9"),
        ((563, 30, 563, 104), "37aa35066f86e29fed5f7acddff3c628b00a38eddb323b38d487055f6f3dfa38"),
    )
    actual_fetches = tuple((
        (value.span.start_line, value.span.start_column,
         value.span.end_line, value.span.end_column),
        _sha256(repr(value).encode("utf-8"))) for value in fetches)
    if actual_fetches != expected_fetches: reject("fetch profile")
    if any(value.signature_id != -45 or len(value.children) != 3
           or value.children[0].symbol_id != 4
           or value.children[2].kind != "literal"
           or value.children[2].literal != "0"
           or value.children[2].literal_value != 0 for value in fetches):
        reject("fetch shape")


def _validate_typed_output_name(name: str) -> None:
    """Reuse the Task-5 hardening for C++; admit only this slice's JSON name."""
    if name.endswith(".cpp"):
        _validate_output_name(name)
        return
    if name != "typed_manifest.json" or pathlib.PurePosixPath(name).name != name or "/" in name or "\\" in name or ":" in name:
        raise GeneratorError("typed output name is not approved")


def load_slice(repository: pathlib.Path = _ROOT) -> dict[str, Any]:
    path = repository.resolve() / "tools/glslcpp/typed_slice.json"
    try: data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise GeneratorError(f"invalid typed slice: {error}") from error
    required = {"schema", "revision", "capabilities", "types", "binary_operators", "assignment_operators",
                "compatibility_transforms", "custom_comparer_profiles",
                "numeric_literal_contracts", "programs"}
    if set(data) != required or data["schema"] != SCHEMA or not isinstance(data["revision"], str):
        raise GeneratorError("unsupported typed slice schema")
    if tuple(data["capabilities"]) != APPROVED_CAPABILITIES:
        raise GeneratorError("typed slice capability vocabulary drift")
    if tuple(data["types"]) != APPROVED_TYPES:
        raise GeneratorError("typed slice type vocabulary drift")
    if tuple(data["binary_operators"]) != APPROVED_BINARY_OPERATORS:
        raise GeneratorError("typed slice binary operator vocabulary drift")
    if tuple(data["assignment_operators"]) != APPROVED_ASSIGNMENT_OPERATORS:
        raise GeneratorError("typed slice assignment operator vocabulary drift")
    if data["numeric_literal_contracts"] != {"filter/scatter:scatterJitter": "source-double"}:
        raise GeneratorError("typed slice numeric literal contract drift")
    if data["compatibility_transforms"] != {
            "classicNoisedeck/coalesce:coalesce": "coalesce-uv-alias-v1",
            "classicNoisedeck/refract:refract": REFRACT_COMPATIBILITY_TRANSFORM,
            "filter/corrupt:corrupt": "corrupt-sample-uv-alias-v1",
            CRT_KEY: CRT_COMPATIBILITY_TRANSFORM,
            "mixer/shapeMask:shapeMask": "shape-mask-sequential-lanes-v1",
            "synth/polygon:shape": "polygon-zero-smoothing-v1",
            SACRED_KEY: SACRED_COMPATIBILITY_TRANSFORM}:
        raise GeneratorError("typed slice compatibility transform drift")
    if data["custom_comparer_profiles"] != {
            LENS_CUSTOM_COMPARER_KEY: LENS_CUSTOM_COMPARER_PROFILE}:
        raise GeneratorError("typed slice custom comparer profile drift")
    programs = data["programs"]
    if not isinstance(programs, list) or not programs:
        raise GeneratorError("typed slice programs are invalid")
    for item in programs:
        key = item.get("program_key")
        expected = ({"curl_vector_math_profile", "defines", "program_key"}
                    if key == CURL_KEY else
                    {"defines", "extrude_bvec2_relational_reduction_profile",
                     "program_key"}
                    if key == EXTRUDE_KEY else
                    {"defines", "focus_blur_borrowed_sampler_profile", "program_key"}
                    if key == FOCUS_BLUR_KEY else
                    {"defines", "rotate_mat2_return_profile", "program_key"}
                    if key == ROTATE_KEY else
                    {"defines", "perlin_scalar_uint_xor_profile", "program_key"}
                    if key == PERLIN_KEY else
                    {"defines", "smooth_edge_luma_weights_profile", "program_key"}
                    if key == SMOOTH_EDGE_KEY else
                    {"defines", "gather_sorted_round_profile", "program_key"}
                    if key == GATHER_SORTED_KEY else
                    {"defines", "literal_vec3_lane_index_profile", "program_key"}
                    if key in LITERAL_VEC3_LANE_INDEX_KEYS else
                    {"defines", "grade_luma_weights_profile",
                     "grade_index_expression_profile", "program_key"}
                    if key in GRADE_LUMA_WEIGHTS_KEYS else
                    {"defines", "grade_index_expression_profile", "program_key"}
                    if key in GRADE_INDEX_EXPRESSION_KEYS else
                    {"defines", "derivative_admission_profile", "program_key"}
                    if key in DERIVATIVE_ADMISSION_KEYS else
                    {"defines", "program_key"})
        if set(item) != expected:
            raise GeneratorError("typed slice programs are invalid")
    keys = [item["program_key"] for item in programs]
    lane_profiles = [(item["program_key"], item.get("literal_vec3_lane_index_profile"))
                     for item in programs
                     if "literal_vec3_lane_index_profile" in item]
    smooth_profiles = [
        (item["program_key"], item.get("smooth_edge_luma_weights_profile"),
         item["defines"])
        for item in programs if "smooth_edge_luma_weights_profile" in item]
    perlin_profiles = [
        (item["program_key"], item.get("perlin_scalar_uint_xor_profile"),
         item["defines"])
        for item in programs if "perlin_scalar_uint_xor_profile" in item]
    rotate_profiles = [
        (item["program_key"], item.get("rotate_mat2_return_profile"),
         item["defines"])
        for item in programs if "rotate_mat2_return_profile" in item]
    focus_profiles = [
        (item["program_key"], item.get("focus_blur_borrowed_sampler_profile"),
         item["defines"])
        for item in programs if "focus_blur_borrowed_sampler_profile" in item]
    curl_profiles = [
        (item["program_key"], item.get("curl_vector_math_profile"), item["defines"])
        for item in programs if "curl_vector_math_profile" in item]
    extrude_profiles = [
        (item["program_key"],
         item.get("extrude_bvec2_relational_reduction_profile"), item["defines"])
        for item in programs
        if "extrude_bvec2_relational_reduction_profile" in item]
    grade_luma_profiles = [
        (item["program_key"], item.get("grade_luma_weights_profile"), item["defines"])
        for item in programs if "grade_luma_weights_profile" in item]
    grade_index_profiles = [
        (item["program_key"], item.get("grade_index_expression_profile"),
         item["defines"])
        for item in programs if "grade_index_expression_profile" in item]
    derivative_profiles = [
        (item["program_key"], item.get("derivative_admission_profile"),
         item["defines"])
        for item in programs if "derivative_admission_profile" in item]
    if (keys != sorted(set(keys)) or len(keys) != 154
            or _sha256(("\n".join(keys) + "\n").encode("utf-8"))
            != "611e4bb44c1d5ef45c2ea0c1715c3f879b76f691e9b8a9fea102ff11210c0e77"
            or lane_profiles != [(key, LITERAL_VEC3_LANE_INDEX_PROFILE)
                                 for key in LITERAL_VEC3_LANE_INDEX_KEYS]
            or smooth_profiles != [
                (SMOOTH_EDGE_KEY, SMOOTH_EDGE_LUMA_WEIGHTS_PROFILE, {})]
            or perlin_profiles != [
                (PERLIN_KEY, PERLIN_SCALAR_UINT_XOR_PROFILE,
                 {"DIMENSIONS": 2})]
            or rotate_profiles != [
                (ROTATE_KEY, ROTATE_MAT2_RETURN_PROFILE, {})]
            or focus_profiles != [
                (FOCUS_BLUR_KEY, FOCUS_BLUR_BORROWED_SAMPLER_PROFILE, {})]
            or extrude_profiles != [
                (EXTRUDE_KEY, EXTRUDE_BVEC2_RELATIONAL_REDUCTION_PROFILE,
                 {"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0})]
            or curl_profiles != [
                (CURL_KEY, CURL_VECTOR_MATH_PROFILE,
                 {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True})]
            or grade_luma_profiles != [
                (key, GRADE_LUMA_WEIGHTS_PROFILES[key], {})
                for key in GRADE_LUMA_WEIGHTS_KEYS]
            or grade_index_profiles != [
                (key, GRADE_INDEX_EXPRESSION_PROFILES[key], {})
                for key in GRADE_INDEX_EXPRESSION_KEYS]
            or derivative_profiles != [
                (key, DERIVATIVE_ADMISSION_PROFILE,
                 {"MODE": 0, "PATTERN": 0} if key == "filter/halftone:halftone" else
                 {"STYLE": 2, "WRAP": 0} if key == "filter/pondRipples:pondRipples" else
                 {"MODE": 0} if key == "filter/stipple:stipple" else {})
                for key in sorted(DERIVATIVE_ADMISSION_KEYS)]):
        raise GeneratorError("typed slice literal vec3 lane profile drift")
    profiles = [(item["program_key"], item.get("gather_sorted_round_profile"))
                for item in programs if "gather_sorted_round_profile" in item]
    if profiles != [(GATHER_SORTED_KEY, GATHER_SORTED_ROUND_PROFILE)]:
        raise GeneratorError("typed slice Gather Sorted round profile drift")
    if keys.count(DEGAUSS_KEY) != 1 or keys.count(CRT_KEY) != 1:
        raise GeneratorError("Task 22 CRT publication boundary drift")
    for item in programs:
        defines = item["defines"]
        if not isinstance(defines, dict) or any(not isinstance(name, str) or not isinstance(value, int)
                                                for name, value in defines.items()):
            raise GeneratorError(f"{item['program_key']}: invalid default-define contract")
    expected_defines = {
        CURL_KEY: {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True},
        EXTRUDE_KEY: {"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0},
        "filter/hatch:hatch": {"MODE": 0},
        "filter/lensFlare:lensFlare": {"LENS_TYPE": 0},
        "filter/lowPoly:lowPoly": {"LP_BORDER": 0, "LP_LIGHT": 0},
        "filter/mosaicTiles:mosaicTiles": {"MODE": 0},
        "filter/morphology:morphA": {"SHAPE": 0},
        "filter/morphology:morphB": {"SHAPE": 0},
        "filter/oilPaint:oilPost": {"MODE": 1},
        "filter/relief:rlBlurH": {"MODE": 0},
        "filter/relief:rlBlurV": {"MODE": 0},
        "filter/relief:rlShade": {"MODE": 0},
        "filter/scatter:scatterSmooth": {"MODE": 0},
        "filter/scatter:scatterJitter": {"MODE": 0},
        "filter/strokes:stkPost": {"MODE": 0},
        "filter/strokes:stkSmear": {"MODE": 0},
        "filter/wind:wind": {"METHOD": 1},
        PERLIN_KEY: {"DIMENSIONS": 2},
        "filter/halftone:halftone": {"MODE": 0, "PATTERN": 0},
        "filter/pondRipples:pondRipples": {"STYLE": 2, "WRAP": 0},
        "filter/stipple:stipple": {"MODE": 0},
    }
    actual_defines = {item["program_key"]: item["defines"] for item in programs if item["defines"]}
    if actual_defines != expected_defines:
        raise GeneratorError("typed slice default-define contract drift")
    return data


def render_catalog_header(slice_spec: dict[str, Any]) -> bytes:
    """Render the complete public factory declaration surface we own."""
    factories = [("filter/invert:inv", "bind_filter_invert"),
                 ("synth/solid:solid", "bind_synth_solid")]
    factories.extend(
        (item["program_key"],
         "bind_" + item["program_key"].replace("/", "_").replace(":", "_"))
        for item in slice_spec["programs"])
    factories.sort()
    lines = [
        "// Generated by typed GLSL IR emitter. Do not edit.",
        "#pragma once", "", "#include <span>", "#include <string_view>", "",
        "#include \"noisemaker/kernel.hpp\"", "",
        "namespace noisemaker::generated {", "",
    ]
    lines.extend(
        f"[[nodiscard]] BoundKernel {factory}(const glsl::Bindings& bindings);"
        for _, factory in factories)
    lines.extend([
        "", "struct KernelFactory {", "  std::string_view key;",
        "  BoundKernel (*bind)(const glsl::Bindings&);", "};", "",
        "[[nodiscard]] std::span<const KernelFactory> catalog() noexcept;",
        "[[nodiscard]] BoundKernel bind(std::string_view key, const glsl::Bindings& bindings);",
        "", "}  // namespace noisemaker::generated", "",
    ])
    return "\n".join(lines).encode("utf-8")


def _source_entries(repository: pathlib.Path, slice_spec: dict[str, Any]) -> list[dict[str, Any]]:
    root = check_corpus._corpus_root(repository)
    manifest = check_corpus._load_json(root / "manifest.json", "manifest")
    entries = {item["program_key"]: item for item in check_corpus._validate_manifest(manifest)}
    result = []
    for item in slice_spec["programs"]:
        try: result.append(entries[item["program_key"]])
        except KeyError as error: raise GeneratorError(f"typed allowlist key missing from corpus: {item['program_key']}") from error
    return result


def _defaults(repository: pathlib.Path, key: str) -> dict:
    root = check_corpus._corpus_root(repository)
    metadata = check_corpus._load_json(root / "metadata.json", "metadata")
    return check_semantics._metadata_defaults(metadata, key)


def apply_compatibility_transform(typed, transform_name: str):
    """Apply one schema-locked typed-IR semantic compatibility repair."""
    if transform_name == CRT_COMPATIBILITY_TRANSFORM:
        try:
            return apply_crt_metal_sine(typed)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    if transform_name == SACRED_COMPATIBILITY_TRANSFORM:
        try:
            return apply_sacred_star_number_division(typed)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    if transform_name == REFRACT_COMPATIBILITY_TRANSFORM:
        try:
            return apply_refract_truthy_vector_noops(typed)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    if transform_name == "coalesce-uv-alias-v1":
        matches = 0

        def declarations(statements, name: str):
            result = []
            for statement_value in statements:
                for item in statement_value.expressions:
                    if item.kind == "declaration" and item.symbol is not None and item.symbol.name == name:
                        result.append(item)
                result.extend(declarations(statement_value.children, name))
            return result

        def direct_vec2_copy(declaration, source_id: int | None) -> bool:
            return (declaration is not None and len(declaration.children) == 1
                    and declaration.children[0].kind == "construct"
                    and declaration.children[0].constructor_type is not None
                    and declaration.children[0].constructor_type.display() == "vec2"
                    and len(declaration.children[0].children) == 1
                    and declaration.children[0].children[0].kind == "id"
                    and declaration.children[0].children[0].symbol_id == source_id)

        def alias_chain_blocks(statements, left_id: int, right_id: int, st_id: int) -> int:
            result = 0
            declaration_positions = {}
            for index, statement_value in enumerate(statements):
                for item in statement_value.expressions:
                    if item.kind == "declaration": declaration_positions[item.symbol_id] = index
            if left_id in declaration_positions and right_id in declaration_positions:
                left_index = declaration_positions[left_id]
                right_index = declaration_positions[right_id]
                if left_index < right_index:
                    writes = []
                    forbidden_write = False
                    for statement_value in statements[left_index + 1:right_index]:
                        for item in statement_value.expressions:
                            if item.kind != "assign" or len(item.children) != 2:
                                continue
                            target = item.children[0]
                            if target.kind == "id":
                                target_id, member = target.symbol_id, None
                            elif (target.kind == "swizzle" and len(target.children) == 1
                                  and target.children[0].kind == "id"):
                                target_id, member = target.children[0].symbol_id, target.member
                            else:
                                target_id, member = None, None
                            if target_id in {st_id, right_id}: forbidden_write = True
                            if target_id == left_id: writes.append((item.operator, member))
                    if not forbidden_write and writes == [("+=", "x"), ("+=", "y")]: result += 1
            for statement_value in statements:
                result += alias_chain_blocks(statement_value.children, left_id, right_id, st_id)
            return result

        transformed_functions = []
        for function in typed.functions:
            exact_main = (function.name == "main" and function.return_type.display() == "void"
                          and not function.parameters and function.body)
            exact_cloak = (function.name == "cloak" and function.return_type.display() == "vec4"
                           and tuple(parameter.type.display() for parameter in function.parameters) == ("vec2",)
                           and function.body)
            if not exact_main and not exact_cloak:
                transformed_functions.append(function)
                continue
            if typed.key != "classicNoisedeck/coalesce:coalesce":
                transformed_functions.append(function)
                continue
            st_candidates = declarations(function.body, "st") if exact_main else []
            st_symbol = (st_candidates[0].symbol if exact_main and len(st_candidates) == 1
                         else function.parameters[0] if exact_cloak else None)
            left_candidates = declarations(function.body, "leftUV")
            right_candidates = declarations(function.body, "rightUV")
            left = left_candidates[0] if len(left_candidates) == 1 else None
            right = right_candidates[0] if len(right_candidates) == 1 else None
            st_id = st_symbol.id if st_symbol is not None else None
            if not (direct_vec2_copy(left, st_id) and direct_vec2_copy(right, st_id)
                    and left is not None and left.symbol is not None and right is not None
                    and right.symbol is not None
                    and alias_chain_blocks(function.body, left.symbol.id, right.symbol.id, st_id) == 1):
                transformed_functions.append(function)
                continue
            matches += 1
            right_id = right.symbol_id
            left_symbol = left.symbol

            def expression(value: TypedExpression) -> TypedExpression:
                children = tuple(expression(child) for child in value.children)
                current = dataclasses.replace(value, children=children) if children != value.children else value
                if current.kind != "declaration" or current.symbol_id != right_id:
                    return current
                constructor = current.children[0]
                source = constructor.children[0]
                replacement = dataclasses.replace(source, symbol_id=left_symbol.id,
                                                  symbol=left_symbol, type=left_symbol.type)
                return dataclasses.replace(
                    current, children=(dataclasses.replace(constructor, children=(replacement,)),))

            def statement(value):
                expressions = tuple(expression(item) for item in value.expressions)
                children = tuple(statement(child) for child in value.children)
                return dataclasses.replace(value, expressions=expressions, children=children)

            transformed_functions.append(dataclasses.replace(
                function, body=tuple(statement(item) for item in function.body)))

        transformed = dataclasses.replace(typed, functions=tuple(transformed_functions))
        if matches != 2:
            raise GeneratorError(
                f"{typed.key}: coalesce-uv-alias-v1 expected exactly two structural matches, got {matches}")

        conditional_matches = []
        conditionals = {
            2: ("color2", 0.0, "max"),
            3: ("color2", 1.0, "min"),
            7: ("color2", 1.0, "min"),
            15: ("color1", 1.0, "min"),
        }

        def mode_guard(value, mode_id: int) -> int | None:
            if value.kind != "if" or not value.expressions:
                return None
            guard = value.expressions[0]
            if guard.kind != "binary" or guard.operator != "==" or len(guard.children) != 2:
                return None
            for identifier, literal in ((guard.children[0], guard.children[1]),
                                        (guard.children[1], guard.children[0])):
                if (identifier.kind == "id" and identifier.symbol_id == mode_id
                        and literal.kind == "literal" and isinstance(literal.literal_value, int)):
                    return literal.literal_value
            return None

        def rewrite_blend(function):
            nonlocal conditional_matches
            exact_blend = (function.name == "blend" and function.return_type.display() == "vec3"
                           and tuple(parameter.type.display() for parameter in function.parameters)
                           == ("vec4", "vec4", "int", "float") and function.body)
            if not exact_blend:
                return function
            parameters = {parameter.name: parameter for parameter in function.parameters}
            if set(parameters) != {"color1", "color2", "mode", "factor"}:
                return function
            middle_candidates = declarations(function.body, "middle")
            if len(middle_candidates) != 1 or middle_candidates[0].children:
                return function
            middle = middle_candidates[0].symbol
            if middle is None or middle.type.display() != "vec4":
                return function

            def expression(value: TypedExpression, active_mode: int | None) -> TypedExpression:
                nonlocal conditional_matches
                children = tuple(expression(child, active_mode) for child in value.children)
                current = dataclasses.replace(value, children=children) if children != value.children else value
                expected = conditionals.get(active_mode)
                if (expected is None or current.kind != "assign" or current.operator != "="
                        or len(current.children) != 2 or current.children[0].kind != "id"
                        or current.children[0].symbol_id != middle.id
                        or current.children[1].kind != "conditional"
                        or len(current.children[1].children) != 3):
                    return current
                source_name, constant, false_callee = expected
                source = parameters[source_name]
                condition, true_value, false_value = current.children[1].children
                if (condition.kind != "binary" or condition.operator != "=="
                        or len(condition.children) != 2 or true_value.kind != "id"
                        or true_value.symbol_id != source.id or false_value.kind != "builtin"
                        or false_value.callee != false_callee):
                    return current
                equality_matches = False
                for identifier, constructor in ((condition.children[0], condition.children[1]),
                                                (condition.children[1], condition.children[0])):
                    equality_matches = equality_matches or (
                        identifier.kind == "id" and identifier.symbol_id == source.id
                        and constructor.kind == "construct"
                        and constructor.constructor_type is not None
                        and constructor.constructor_type.display() == "vec4"
                        and len(constructor.children) == 1
                        and constructor.children[0].kind == "literal"
                        and constructor.children[0].literal_value == constant)
                if not equality_matches:
                    return current
                conditional_matches.append((active_mode, source_name, constant, false_callee))
                return dataclasses.replace(current, children=(current.children[0], current.children[0]))

            def statement(value, active_mode: int | None = None):
                guarded_mode = mode_guard(value, parameters["mode"].id)
                child_mode = guarded_mode if guarded_mode is not None else active_mode
                expressions = tuple(expression(item, active_mode) for item in value.expressions)
                children = tuple(statement(child, child_mode) for child in value.children)
                return dataclasses.replace(value, expressions=expressions, children=children)

            return dataclasses.replace(function, body=tuple(statement(item) for item in function.body))

        transformed = dataclasses.replace(
            transformed, functions=tuple(rewrite_blend(function) for function in transformed.functions))
        expected_conditionals = sorted(
            (mode, source_name, constant, false_callee)
            for mode, (source_name, constant, false_callee) in conditionals.items())
        if sorted(conditional_matches) != expected_conditionals:
            matched_modes = sorted(item[0] for item in conditional_matches)
            raise GeneratorError(
                f"{typed.key}: coalesce-uv-alias-v1 expected exact vector-conditional modes "
                f"[2, 3, 7, 15], got {matched_modes}")
        return transformed

    if transform_name == "shape-mask-sequential-lanes-v1":
        triangle_matches = 0
        star_matches = 0

        def declarations(statements, name: str):
            result = []
            for statement_value in statements:
                for item in statement_value.expressions:
                    if item.kind == "declaration" and item.symbol is not None and item.symbol.name == name:
                        result.append(item)
                result.extend(declarations(statement_value.children, name))
            return result

        def is_id(value, symbol) -> bool:
            return value.kind == "id" and value.symbol_id == symbol.id

        def is_literal(value, literal: float) -> bool:
            return value.kind == "literal" and value.literal_value == literal

        def is_swizzle(value, symbol, member: str) -> bool:
            return (value.kind == "swizzle" and value.member == member and len(value.children) == 1
                    and is_id(value.children[0], symbol))

        def exact_triangle_guard(value, p, k) -> bool:
            if value.kind != "if" or not value.expressions:
                return False
            guard = value.expressions[0]
            if guard.kind != "binary" or guard.operator != ">" or len(guard.children) != 2:
                return False
            total, zero = guard.children
            return (is_literal(zero, 0.0) and total.kind == "binary" and total.operator == "+"
                    and len(total.children) == 2 and is_swizzle(total.children[0], p, "x")
                    and total.children[1].kind == "binary" and total.children[1].operator == "*"
                    and len(total.children[1].children) == 2
                    and is_id(total.children[1].children[0], k)
                    and is_swizzle(total.children[1].children[1], p, "y"))

        def split_triangle_assignment(value, p, k):
            if (value.kind != "assign" or value.operator != "=" or len(value.children) != 2
                    or not is_id(value.children[0], p)):
                return None
            quotient = value.children[1]
            if (quotient.kind != "binary" or quotient.operator != "/" or len(quotient.children) != 2
                    or not is_literal(quotient.children[1], 2.0)):
                return None
            constructor = quotient.children[0]
            if (constructor.kind != "construct" or constructor.constructor_type is None
                    or constructor.constructor_type.display() != "vec2" or len(constructor.children) != 2):
                return None
            x_value, y_value = constructor.children
            x_shape = (x_value.kind == "binary" and x_value.operator == "-" and len(x_value.children) == 2
                       and is_swizzle(x_value.children[0], p, "x")
                       and x_value.children[1].kind == "binary" and x_value.children[1].operator == "*"
                       and len(x_value.children[1].children) == 2
                       and is_id(x_value.children[1].children[0], k)
                       and is_swizzle(x_value.children[1].children[1], p, "y"))
            y_shape = (y_value.kind == "binary" and y_value.operator == "-" and len(y_value.children) == 2
                       and y_value.children[0].kind == "binary" and y_value.children[0].operator == "*"
                       and len(y_value.children[0].children) == 2
                       and y_value.children[0].children[0].kind == "unary"
                       and y_value.children[0].children[0].operator == "-"
                       and len(y_value.children[0].children[0].children) == 1
                       and is_id(y_value.children[0].children[0].children[0], k)
                       and is_swizzle(y_value.children[0].children[1], p, "x")
                       and is_swizzle(y_value.children[1], p, "y"))
            if not x_shape or not y_shape:
                return None
            x_lhs = x_value.children[0]
            y_lhs = y_value.children[1]
            x_quotient = dataclasses.replace(quotient, type=x_value.type,
                                             children=(x_value, quotient.children[1]))
            y_quotient = dataclasses.replace(quotient, type=y_value.type,
                                             children=(y_value, quotient.children[1]))
            return (dataclasses.replace(value, type=x_value.type, children=(x_lhs, x_quotient)),
                    dataclasses.replace(value, type=y_value.type, children=(y_lhs, y_quotient)))

        def split_star_assignment(value, p, k, x_template, y_template):
            if (value.kind != "assign" or value.operator != "-=" or len(value.children) != 2
                    or not is_id(value.children[0], p)):
                return None
            product = value.children[1]
            if (product.kind != "binary" or product.operator != "*" or len(product.children) != 2
                    or not is_id(product.children[1], k)):
                return None
            scale = product.children[0]
            if (scale.kind != "binary" or scale.operator != "*" or len(scale.children) != 2
                    or not is_literal(scale.children[0], 2.0)):
                return None
            maximum = scale.children[1]
            if (maximum.kind != "builtin" or maximum.callee != "max" or len(maximum.children) != 2
                    or not is_literal(maximum.children[1], 0.0)):
                return None
            dot = maximum.children[0]
            if (dot.kind != "builtin" or dot.callee != "dot" or len(dot.children) != 2
                    or not is_id(dot.children[0], k) or not is_id(dot.children[1], p)):
                return None
            p_x = dataclasses.replace(x_template, children=(value.children[0],))
            p_y = dataclasses.replace(y_template, children=(value.children[0],))
            k_x = dataclasses.replace(x_template, children=(product.children[1],))
            k_y = dataclasses.replace(y_template, children=(product.children[1],))
            x_product = dataclasses.replace(product, type=scale.type, children=(scale, k_x))
            y_product = dataclasses.replace(product, type=scale.type, children=(scale, k_y))
            return (dataclasses.replace(value, type=scale.type, children=(p_x, x_product)),
                    dataclasses.replace(value, type=scale.type, children=(p_y, y_product)))

        functions = []
        for function in typed.functions:
            if typed.key != "mixer/shapeMask:shapeMask":
                functions.append(function)
                continue
            exact_triangle = (function.name == "sdfTriangle" and function.return_type.display() == "float"
                              and tuple(parameter.type.display() for parameter in function.parameters)
                              == ("vec2", "float") and function.body)
            exact_star = (function.name == "sdfStar5" and function.return_type.display() == "float"
                          and tuple(parameter.type.display() for parameter in function.parameters)
                          == ("vec2", "float") and function.body)
            if exact_triangle:
                p, _r = function.parameters
                k_items = declarations(function.body, "k")
                k = k_items[0].symbol if len(k_items) == 1 else None

                def triangle_block(statements, guarded: bool = False):
                    nonlocal triangle_matches
                    result = []
                    for statement_value in statements:
                        child_guarded = guarded or (k is not None and exact_triangle_guard(statement_value, p, k))
                        rewritten_children = triangle_block(statement_value.children, child_guarded)
                        current = dataclasses.replace(statement_value, children=rewritten_children)
                        split = None
                        if guarded and k is not None and len(current.expressions) == 1:
                            split = split_triangle_assignment(current.expressions[0], p, k)
                        if split is None:
                            result.append(current)
                        else:
                            triangle_matches += 1
                            first = dataclasses.replace(current, expressions=(split[0],))
                            second = dataclasses.replace(current, expressions=(split[1],))
                            result.append(dataclasses.replace(
                                current, kind="block", expressions=(), children=(first, second)))
                    return tuple(result)

                functions.append(dataclasses.replace(function, body=triangle_block(function.body)))
            elif exact_star:
                p, _r = function.parameters
                k1_items = declarations(function.body, "k1")
                k2_items = declarations(function.body, "k2")
                k1 = k1_items[0].symbol if len(k1_items) == 1 else None
                k2 = k2_items[0].symbol if len(k2_items) == 1 else None
                templates = []

                def collect_swizzles(statements):
                    def expression(value):
                        if value.kind == "swizzle" and value.member in {"x", "y"}: templates.append(value)
                        for child in value.children: expression(child)
                    for statement_value in statements:
                        for item in statement_value.expressions: expression(item)
                        collect_swizzles(statement_value.children)

                collect_swizzles(function.body)
                x_template = next((item for item in templates if item.member == "x"), None)
                y_template = next((item for item in templates if item.member == "y"), None)

                def star_block(statements):
                    nonlocal star_matches
                    result = []
                    for statement_value in statements:
                        current = dataclasses.replace(statement_value, children=star_block(statement_value.children))
                        split = None
                        if len(current.expressions) == 1 and x_template is not None and y_template is not None:
                            for k in (k1, k2):
                                if k is not None:
                                    split = split_star_assignment(current.expressions[0], p, k,
                                                                  x_template, y_template)
                                    if split is not None: break
                        if split is None:
                            result.append(current)
                        else:
                            star_matches += 1
                            result.extend((dataclasses.replace(current, expressions=(split[0],)),
                                           dataclasses.replace(current, expressions=(split[1],))))
                    return tuple(result)

                functions.append(dataclasses.replace(function, body=star_block(function.body)))
            else:
                functions.append(function)
        if triangle_matches != 1:
            raise GeneratorError(
                f"{typed.key}: shape-mask-sequential-lanes-v1 expected exactly one triangle match, got {triangle_matches}")
        if star_matches != 2:
            raise GeneratorError(
                f"{typed.key}: shape-mask-sequential-lanes-v1 expected exactly two star matches, got {star_matches}")
        return dataclasses.replace(typed, functions=tuple(functions))

    if transform_name == "corrupt-sample-uv-alias-v1":
        matches = 0
        main_functions = [function for function in typed.functions if function.name == "main" and function.body]

        def declarations(statements, name: str):
            result = []
            for statement_value in statements:
                for item in statement_value.expressions:
                    if item.kind == "declaration" and item.symbol is not None and item.symbol.name == name:
                        result.append(item)
                result.extend(declarations(statement_value.children, name))
            return result

        main = main_functions[0] if len(main_functions) == 1 else None
        bit_signatures = [function.signature.id for function in typed.functions
                          if function.name == "bitCorrupt"
                          and function.return_type.display() == "vec3"
                          and tuple(parameter.type.display() for parameter in function.parameters)
                          == ("vec3", "vec2", "float", "float", "float", "float")]
        bit_signature_id = bit_signatures[0] if len(bit_signatures) == 1 else None
        uv_declarations = declarations(main.body, "uv") if main is not None else []
        sample_declarations = declarations(main.body, "sampleUv") if main is not None else []
        uv = uv_declarations[0] if len(uv_declarations) == 1 else None
        sample = sample_declarations[0] if len(sample_declarations) == 1 else None
        uv_id = uv.symbol_id if uv is not None else None
        sample_symbol = sample.symbol if sample is not None else None
        alias_shape = (sample is not None and sample_symbol is not None and len(sample.children) == 1
                       and sample.children[0].kind == "id" and sample.children[0].symbol_id == uv_id)

        def expression(value: TypedExpression) -> TypedExpression:
            nonlocal matches
            children = tuple(expression(child) for child in value.children)
            current = dataclasses.replace(value, children=children) if children != value.children else value
            if (typed.key != "filter/corrupt:corrupt" or not alias_shape or current.kind != "call"
                    or current.callee != "bitCorrupt" or current.signature_id != bit_signature_id
                    or len(children) != 6
                    or children[1].kind != "id" or children[1].symbol_id != uv_id):
                return current
            matches += 1
            replacement = dataclasses.replace(children[1], symbol_id=sample_symbol.id,
                                              symbol=sample_symbol, type=sample_symbol.type)
            return dataclasses.replace(current, children=(children[0], replacement, *children[2:]))

        def statement(value):
            expressions = tuple(expression(item) for item in value.expressions)
            children = tuple(statement(child) for child in value.children)
            return dataclasses.replace(value, expressions=expressions, children=children)

        main_id = main.signature.id if main is not None else None
        functions = tuple(
            dataclasses.replace(function, body=tuple(statement(item) for item in function.body))
            if function.signature.id == main_id else function
            for function in typed.functions)
        transformed = dataclasses.replace(typed, functions=functions)
        if matches != 1:
            raise GeneratorError(
                f"{typed.key}: corrupt-sample-uv-alias-v1 expected exactly one structural match, got {matches}")
        return transformed

    if transform_name != "polygon-zero-smoothing-v1":
        raise GeneratorError(f"{typed.key}: unsupported compatibility transform {transform_name}")

    matches = 0
    radius_symbols = [item.symbol for item in typed.declarations
                      if item.symbol.storage == "uniform" and item.symbol.name == "radius"]
    smoothing_symbols = [item.symbol for item in typed.declarations
                         if item.symbol.storage == "uniform" and item.symbol.name == "smoothing"]
    main_functions = [function for function in typed.functions if function.name == "main" and function.body]

    def local_symbols(statements, name: str):
        result = []
        for statement_value in statements:
            for item in statement_value.expressions:
                if item.kind == "declaration" and item.symbol is not None and item.symbol.name == name:
                    result.append(item.symbol)
            result.extend(local_symbols(statement_value.children, name))
        return result

    distance_symbols = local_symbols(main_functions[0].body, "d") if len(main_functions) == 1 else []
    radius_id = radius_symbols[0].id if len(radius_symbols) == 1 else None
    smoothing_id = smoothing_symbols[0].id if len(smoothing_symbols) == 1 else None
    distance_id = distance_symbols[0].id if len(distance_symbols) == 1 else None

    def bound_to(value: TypedExpression, symbol_id: int | None) -> bool:
        return (symbol_id is not None and value.kind == "id" and value.symbol is not None
                and value.symbol_id == symbol_id and value.symbol.id == symbol_id)

    def expression(value: TypedExpression) -> TypedExpression:
        nonlocal matches
        children = tuple(expression(child) for child in value.children)
        current = dataclasses.replace(value, children=children) if children != value.children else value
        if typed.key != "synth/polygon:shape" or current.kind != "builtin" or current.callee != "smoothstep" or len(children) != 3:
            return current
        first, second, distance = children
        if (not bound_to(first, radius_id) or second.kind != "binary" or second.operator != "-"
                or len(second.children) != 2 or not bound_to(second.children[0], radius_id)
                or not bound_to(second.children[1], smoothing_id) or not bound_to(distance, distance_id)):
            return current
        matches += 1
        span = current.span
        zero = TypedExpression("literal", FLOAT, span, "rvalue", literal="0.0", literal_value=0.0)
        one = TypedExpression("literal", FLOAT, span, "rvalue", literal="1.0", literal_value=1.0)
        smoothing_zero = TypedExpression("binary", BOOL, span, "rvalue",
                                         children=(second.children[1], zero), operator="==")
        inside = TypedExpression("binary", BOOL, span, "rvalue", children=(distance, first), operator="<=")
        hard_mask = TypedExpression("conditional", FLOAT, span, "rvalue",
                                    children=(inside, one, zero))
        return TypedExpression("conditional", FLOAT, span, "rvalue",
                               children=(smoothing_zero, hard_mask, current))

    def statement(value):
        expressions = tuple(expression(item) for item in value.expressions)
        children = tuple(statement(child) for child in value.children)
        return dataclasses.replace(value, expressions=expressions, children=children)

    main_id = main_functions[0].signature.id if len(main_functions) == 1 else None
    functions = tuple(
        dataclasses.replace(function, body=tuple(statement(item) for item in function.body))
        if function.signature.id == main_id else function
        for function in typed.functions)
    transformed = dataclasses.replace(typed, functions=functions)
    if matches != 1:
        raise GeneratorError(f"{typed.key}: polygon-zero-smoothing-v1 expected exactly one structural match, got {matches}")
    return transformed


def validate_capabilities(typed, declared: tuple[str, ...] | list[str], *,
                          source_hash: str | None = None,
                          compatibility_transform: str | None = None,
                          custom_comparer_profile: str | None = None,
                          numeric_literal_contract: str = "glsl-f32",
                          source_global_literal_int_profile: str | None = None,
                          gather_sorted_round_profile: str | None = None,
                          literal_vec3_lane_index_profile: str | None = None,
                          smooth_edge_luma_weights_profile: str | None = None,
                          perlin_scalar_uint_xor_profile: str | None = None,
                          rotate_mat2_return_profile: str | None = None,
                          focus_blur_borrowed_sampler_profile: str | None = None,
                          extrude_bvec2_relational_reduction_profile: str | None = None,
                          caustic_word_hash_profile: str | None = None,
                          curl_vector_math_profile: str | None = None,
                          grade_luma_weights_profile: str | None = None,
                          grade_index_expression_profile: str | None = None,
                          derivative_admission_profile: str | None = None) -> None:
    """Prove every emitted typed construct is explicitly approved by this slice."""
    capabilities = tuple(declared)
    literal_source_key = literal_vec3_lane_selected_source_key(typed)
    unknown = sorted(set(capabilities) - set(APPROVED_CAPABILITIES))
    if unknown: raise GeneratorError(f"{typed.key}: unknown capability {unknown[0]}")
    if capabilities != APPROVED_CAPABILITIES:
        raise GeneratorError(f"{typed.key}: typed capability vocabulary mismatch")
    if capabilities.count(SOURCE_GLOBAL_LITERAL_INT_CAPABILITY) != 1:
        raise GeneratorError(
            f"{typed.key}: malformed slice-global source-global literal-int capability")
    if typed.key in SOURCE_GLOBAL_LITERAL_INT_KEYS:
        if source_global_literal_int_profile != SOURCE_GLOBAL_LITERAL_INT_CAPABILITY:
            raise GeneratorError(f"{typed.key}: exact source-global literal-int carrier required")
        if source_hash != _sha256(typed.raw_source.encode("utf-8")):
            raise GeneratorError(
                f"{typed.key}: source-global literal-int caller source digest mismatch")
    elif source_global_literal_int_profile is not None:
        raise GeneratorError(f"{typed.key}: source-global literal-int carrier on foreign key")
    authorized_round = None
    authorized_smooth_edge_luma_weights_declaration = None
    authorized_grade_luma_weights_declaration = None
    authorized_grade_index_sites: tuple[TypedExpression, ...] = ()
    visited_grade_index_sites: list[TypedExpression] = []
    authorized_perlin_scalar_uint_xors: tuple[TypedExpression, ...] = ()
    visited_perlin_scalar_uint_xors: list[TypedExpression] = []
    authorized_rotate_helper = None
    authorized_rotate_expressions: tuple[TypedExpression, ...] = ()
    visited_rotate_expressions: list[TypedExpression] = []
    authorized_focus_blur_proof = None
    authorized_extrude_proof = None
    authorized_caustic_proof = None
    authorized_curl_proof = None
    authorized_curl_mod_nodes: tuple[TypedExpression, ...] = ()
    authorized_curl_tanh = None
    visited_curl_nodes: list[TypedExpression] = []
    authorized_derivative_proof = None
    authorized_caustic_scalar_uint_xors: tuple[TypedExpression, ...] = ()
    visited_caustic_scalar_uint_xors: list[TypedExpression] = []
    authorized_caustic_ingress = None
    visited_caustic_ingress: list[TypedExpression] = []
    authorized_extrude_relationals: tuple[TypedExpression, ...] = ()
    authorized_extrude_reductions: tuple[TypedExpression, ...] = ()
    visited_extrude_nodes: list[TypedExpression] = []
    if focus_blur_borrowed_sampler_profile is not None:
        if (typed.key != FOCUS_BLUR_KEY
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or rotate_mat2_return_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Focus Blur borrowed sampler profile metadata mismatch")
        try:
            authorized_focus_blur_proof = (
                authenticate_focus_blur_borrowed_sampler_parameters(
                    typed, source_hash, focus_blur_borrowed_sampler_profile))
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == FOCUS_BLUR_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Focus Blur borrowed sampler profile carrier required")
    if extrude_bvec2_relational_reduction_profile is not None:
        if (typed.key != EXTRUDE_KEY
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Extrude bvec2 relational reduction profile metadata mismatch")
        try:
            authorized_extrude_proof = (
                authenticate_extrude_bvec2_relational_reduction(
                    typed, source_hash, extrude_bvec2_relational_reduction_profile))
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_extrude_relationals = authorized_extrude_proof.relationals
        authorized_extrude_reductions = authorized_extrude_proof.reductions
    elif typed.key == EXTRUDE_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Extrude bvec2 relational reduction profile carrier required")
    if caustic_word_hash_profile is not None:
        if (typed.key != CAUSTIC_KEY
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Caustic word hash profile metadata mismatch")
        try:
            authorized_caustic_proof = authenticate_caustic_word_hash(
                typed, source_hash, caustic_word_hash_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_caustic_scalar_uint_xors = authorized_caustic_proof.word_xors
        authorized_caustic_ingress = authorized_caustic_proof.ingress
    elif typed.key == CAUSTIC_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Caustic word hash profile carrier required")
    if curl_vector_math_profile is not None:
        if (typed.key != CURL_KEY
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Curl vector math profile metadata mismatch")
        try:
            authorized_curl_proof = authenticate_curl_vector_math(
                typed, source_hash, curl_vector_math_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_curl_mod_nodes = authorized_curl_proof.mod_sites
        authorized_curl_tanh = authorized_curl_proof.tanh_site
    elif typed.key == CURL_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Curl vector math profile carrier required")
    if grade_luma_weights_profile is not None:
        if (typed.key not in GRADE_LUMA_WEIGHTS_KEYS
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or derivative_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Grade LUMA weights profile metadata mismatch")
        try:
            authorized_grade_luma_weights_declaration = authenticate_grade_luma_weights(
                typed, source_hash, grade_luma_weights_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in GRADE_LUMA_WEIGHTS_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact Grade LUMA weights profile carrier required")
    # grade_index_expression_profile is deliberately NOT mutually exclusive
    # with grade_luma_weights_profile above: five of the six grade programs
    # need both proofs simultaneously (their own LUMA_WEIGHTS global plus
    # their own srgbToLinear/linearToSrgb lane-index closure); `lut` needs
    # only this one (it has no source global). This is the first pair of
    # profiles in this codebase that legitimately coexist on one key.
    if grade_index_expression_profile is not None:
        if (typed.key not in GRADE_INDEX_EXPRESSION_KEYS
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or derivative_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Grade index expression profile metadata mismatch")
        try:
            authorized_grade_index_sites = authenticate_grade_index_expression(
                typed, source_hash, grade_index_expression_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in GRADE_INDEX_EXPRESSION_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact Grade index expression profile carrier required")
    authorized_derivative_nodes: tuple[TypedExpression, ...] = ()
    visited_derivative_nodes: list[TypedExpression] = []
    if derivative_admission_profile is not None:
        if (typed.key not in DERIVATIVE_ADMISSION_KEYS
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Derivative admission profile metadata mismatch")
        try:
            authorized_derivative_proof = authenticate_derivative_admission(
                typed, source_hash, derivative_admission_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_derivative_nodes = authorized_derivative_proof.nodes
    elif typed.key in DERIVATIVE_ADMISSION_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact Derivative admission profile carrier required")
    if rotate_mat2_return_profile is not None:
        if (typed.key != ROTATE_KEY
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Rotate mat2 return profile metadata mismatch")
        try:
            (authorized_rotate_helper, constructor, call,
             parent) = authenticate_rotate_mat2_return(
                 typed, source_hash, rotate_mat2_return_profile)
            authorized_rotate_expressions = (constructor, call, parent)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == ROTATE_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Rotate mat2 return profile carrier required")
    if perlin_scalar_uint_xor_profile is not None:
        if (typed.key != PERLIN_KEY
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Perlin scalar uint XOR profile metadata mismatch")
        try:
            authorized_perlin_scalar_uint_xors = (
                authenticate_perlin_scalar_uint_xor(
                    typed, source_hash, perlin_scalar_uint_xor_profile))
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == PERLIN_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Perlin scalar uint XOR profile carrier required")
    if smooth_edge_luma_weights_profile is not None:
        if (typed.key != SMOOTH_EDGE_KEY
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Smooth Edge LUMA weights profile metadata mismatch")
        try:
            (authorized_smooth_edge_luma_weights_declaration,
             _) = authenticate_smooth_edge_luma_weights(
                 typed, source_hash, smooth_edge_luma_weights_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == SMOOTH_EDGE_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Smooth Edge LUMA weights profile carrier required")
    if gather_sorted_round_profile is not None:
        if (typed.key != GATHER_SORTED_KEY or compatibility_transform is not None
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: Gather Sorted round profile metadata mismatch")
        try:
            _, authorized_round = authenticate_gather_sorted_round_to_int(
                typed, source_hash, gather_sorted_round_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    if literal_vec3_lane_index_profile is not None:
        if (typed.key not in LITERAL_VEC3_LANE_INDEX_KEYS
                or compatibility_transform is not None
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: literal vec3 lane profile metadata mismatch")
        try:
            authenticate_literal_vec3_lane_index_post(
                typed, source_hash, literal_vec3_lane_index_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    if typed.key == LENS_CUSTOM_COMPARER_KEY:
        if (custom_comparer_profile != LENS_CUSTOM_COMPARER_PROFILE
                or literal_vec3_lane_index_profile != LITERAL_VEC3_LANE_INDEX_PROFILE
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: Lens custom comparer metadata mismatch")
        try:
            authenticate_lens_custom_comparer_final(
                typed, source_hash, custom_comparer_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif custom_comparer_profile is not None:
        raise GeneratorError(f"{typed.key}: Lens custom comparer profile on foreign key")
    if typed.key == CRT_KEY:
        if (compatibility_transform != CRT_COMPATIBILITY_TRANSFORM
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: CRT metadata carrier mismatch")
        try:
            authenticate_crt_metal_sine(typed, source_hash)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif compatibility_transform == CRT_COMPATIBILITY_TRANSFORM:
        raise GeneratorError(f"{typed.key}: CRT compatibility transform on foreign key")
    if typed.key == SACRED_KEY:
        if (compatibility_transform != SACRED_COMPATIBILITY_TRANSFORM
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: Sacred metadata carrier mismatch")
        try:
            authenticate_sacred_star_number_division(typed, source_hash)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif compatibility_transform == SACRED_COMPATIBILITY_TRANSFORM:
        raise GeneratorError(f"{typed.key}: Sacred compatibility transform on foreign key")
    if (typed.key == COMPUTE_RANK_KEY
            and (source_hash != COMPUTE_RANK_RAW_SHA256
                 or _sha256(typed.source.encode("utf-8"))
                 != COMPUTE_RANK_NORMALIZED_SHA256)):
        raise GeneratorError(f"{typed.key}: source digest mismatch for discarded local counter")
    provenance = source_provenance_error(typed, source_hash)
    if provenance is not None:
        raise GeneratorError(f"{typed.key}: {provenance}")
    grid_provenance = fixed_grid_source_provenance_error(typed, source_hash)
    if grid_provenance is not None:
        raise GeneratorError(f"{typed.key}: {grid_provenance}")
    array_parameter_provenance = fixed_array_source_provenance_error(
        typed, source_hash)
    if array_parameter_provenance is not None:
        raise GeneratorError(f"{typed.key}: {array_parameter_provenance}")
    affine_provenance = fixed_affine_source_provenance_error(typed, source_hash)
    if affine_provenance is not None:
        raise GeneratorError(f"{typed.key}: {affine_provenance}")
    used: set[str] = set()
    proved_array_declarations: dict[int, tuple[object, str]] = {}
    proved_array_parameters: dict[int, tuple[object, str, str]] = {}
    proved_array_arguments: set[tuple[int, object, str]] = set()
    proved_store_indices: set[tuple[int, int, object]] = set()
    proved_read_indices: set[tuple[int, int, object]] = set()
    proved_task19_store_indices: set[tuple[int, int, object]] = set()
    proved_task19_read_indices: set[tuple[int, int, object]] = set()
    proved_task20_indices: set[tuple[int, object, str]] = set()
    proved_grid_dynamic_stores: set[tuple[int, int, object]] = set()
    proved_grid_literal_reads: set[tuple[int, int, object]] = set()
    proved_grid_updates: set[tuple[int, object, object]] = set()
    def location(value) -> str:
        return f"{typed.key}:{value.span.start_line}:{value.span.start_column}"
    def reject_type(typ, value) -> None:
        if typ.kind == "array":
            expected = proved_array_declarations.get(getattr(value, "symbol_id", None))
            if (getattr(value, "kind", None) == "declaration" and expected is not None
                    and expected == (value.span, typ.display())):
                return
            parameter = proved_array_parameters.get(getattr(value, "id", None))
            if (getattr(value, "storage", None) == "parameter"
                    and parameter == (value.span, typ.display(), value.direction)):
                used.add(FIXED_ARRAY_PARAMETER_CAPABILITY)
                return
            if (getattr(value, "kind", None) == "id"
                    and (getattr(value, "symbol_id", None), value.span,
                         typ.display()) in proved_array_arguments):
                used.add(FIXED_ARRAY_PARAMETER_CAPABILITY)
                return
            raise GeneratorError(f"{location(value)}: unsupported typed type {typ.display()}")
        if typ.display() == "bvec2":
            # `bvec2` is deliberately absent from APPROVED_TYPES. It is admitted
            # only as the result type of an exact authenticated Extrude
            # relational node, which is immediately consumed by its paired
            # `all`. Type admission is a separate authority from builtin
            # admission, so both must independently agree.
            if any(value is item for item in authorized_extrude_relationals):
                return
            raise GeneratorError(f"{location(value)}: unsupported typed type {typ.display()}")
        if typ.display() not in APPROVED_TYPES or typ.kind in {"array", "struct"}:
            raise GeneratorError(f"{location(value)}: unsupported typed type {typ.display()}")

    try:
        recomputed_functions, recomputed_program_proof = (
            rebuild_authenticated_counted_loop_proofs(
                typed, source_global_literal_int_profile))
    except ValueError as error:
        raise GeneratorError(f"{typed.key}: {error}") from error
    if len(recomputed_functions) != len(typed.functions):
        raise GeneratorError(f"{typed.key}: malformed counted-for proof functions")

    def audit_loop_proofs(actual, expected) -> None:
        if actual.kind != expected.kind or len(actual.children) != len(expected.children):
            raise GeneratorError(f"{location(actual)}: malformed counted-for proof structure")
        if actual.loop_proof != expected.loop_proof:
            raise GeneratorError(f"{location(actual)}: malformed counted-for proof")
        proof = actual.loop_proof
        if proof is not None:
            if (proof.trip_count > 128 or proof.lexical_depth > 3
                    or proof.effective_depth > 3 or proof.lexical_product > 4096
                    or proof.entrypoint_charge > 4096
                    or min(proof.trip_count, proof.lexical_depth, proof.effective_depth,
                           proof.lexical_product, proof.entrypoint_charge) < 0):
                raise GeneratorError(f"{location(actual)}: unsupported counted-for safety charge")
        for actual_child, expected_child in zip(actual.children, expected.children):
            audit_loop_proofs(actual_child, expected_child)

    for actual_function, expected_function in zip(typed.functions, recomputed_functions):
        if (actual_function.signature.id != expected_function.signature.id
                or len(actual_function.body) != len(expected_function.body)):
            raise GeneratorError(f"{location(actual_function)}: malformed counted-for proof function")
        for actual_statement, expected_statement in zip(actual_function.body, expected_function.body):
            audit_loop_proofs(actual_statement, expected_statement)
    recomputed_counter_functions = attach_discarded_local_counter_proofs(
        recomputed_functions, typed.key)
    recomputed_program = dataclasses.replace(
        typed, functions=recomputed_counter_functions,
        fixed_nine_table_proof=None,
        fixed_grid_counter_store_proof=None,
        fixed_array_in_parameter_proof=None,
        fixed_affine_centers13_proof=None)
    recomputed_fixed_nine = prove_fixed_nine_local_tables(recomputed_program)
    if typed.key in SOURCE_LOCKS:
        if (recomputed_fixed_nine is None
                or typed.fixed_nine_table_proof != recomputed_fixed_nine):
            raise GeneratorError(
                f"{typed.key}: malformed fixed-nine whole-program profile")
        for array in recomputed_fixed_nine.arrays:
            proved_array_declarations[array.symbol_id] = (
                array.declaration_span, array.array_type)
            proved_store_indices.update(
                (array.symbol_id, index, span)
                for index, span in zip(array.literal_store_indices,
                                       array.literal_store_index_spans))
            proved_read_indices.update(
                (array.symbol_id, recomputed_fixed_nine.induction_symbol_id, span)
                for span in array.read_spans)
    elif typed.fixed_nine_table_proof is not None:
        raise GeneratorError(f"{typed.key}: malformed fixed-nine local-table proof key")
    recomputed_grid_program = dataclasses.replace(
        recomputed_program, fixed_nine_table_proof=recomputed_fixed_nine)
    recomputed_fixed_grid = prove_fixed_grid_counter_store(recomputed_grid_program)
    if typed.key in FIXED_GRID_SOURCE_LOCKS:
        if (recomputed_fixed_grid is None
                or typed.fixed_grid_counter_store_proof != recomputed_fixed_grid):
            raise GeneratorError(
                f"{typed.key}: malformed fixed-grid whole-program profile")
        proved_array_declarations[recomputed_fixed_grid.array_symbol_id] = (
            recomputed_fixed_grid.array_declaration_span,
            recomputed_fixed_grid.array_type)
        proved_grid_dynamic_stores.add((
            recomputed_fixed_grid.array_symbol_id,
            recomputed_fixed_grid.counter_symbol_id,
            recomputed_fixed_grid.dynamic_store_index_span))
        proved_grid_literal_reads.update(
            (item.array_symbol_id, item.literal_index, item.index_span)
            for item in recomputed_fixed_grid.literal_reads)
        proved_grid_updates.add((
            recomputed_fixed_grid.counter_symbol_id,
            recomputed_fixed_grid.counter_update_expression_span,
            recomputed_fixed_grid.counter_update_statement_span))
    elif typed.fixed_grid_counter_store_proof is not None:
        raise GeneratorError(
            f"{typed.key}: malformed fixed-grid counter-store proof key")
    recomputed_task19_program = dataclasses.replace(
        recomputed_program,
        fixed_nine_table_proof=recomputed_fixed_nine,
        fixed_grid_counter_store_proof=recomputed_fixed_grid)
    recomputed_task19 = prove_fixed_array_in_parameter(recomputed_task19_program)
    if typed.key == REFRACT_KEY:
        if (recomputed_task19 is None
                or typed.fixed_array_in_parameter_proof != recomputed_task19):
            raise GeneratorError(
                f"{typed.key}: malformed fixed-array input-parameter profile")
        for table in (*recomputed_task19.caller_tables,
                      recomputed_task19.offset_table):
            proved_array_declarations[table.symbol_id] = (
                table.declaration_span, table.array_type)
            proved_task19_store_indices.update(
                (table.symbol_id, index, span)
                for index, span in zip(table.literal_indices,
                                       table.literal_index_spans))
            proved_task19_read_indices.update(
                (table.symbol_id, recomputed_task19.induction_symbol_id, span)
                for span in table.induction_read_spans)
        parameter = recomputed_task19.parameter
        parameter_symbol = next(
            item for function in typed.functions
            if function.signature.id == parameter.owner_signature_id
            for ordinal, item in enumerate(function.parameters)
            if ordinal == parameter.parameter_ordinal
            and item.id == parameter.symbol_id)
        proved_array_parameters[parameter.symbol_id] = (
            parameter_symbol.span, parameter.array_type, parameter.direction)
        proved_task19_read_indices.update(
            (parameter.symbol_id, recomputed_task19.induction_symbol_id, span)
            for span in parameter.induction_read_spans)
        proved_array_arguments.update(
            (table.symbol_id, span, table.array_type)
            for table, span in zip(recomputed_task19.caller_tables,
                                   parameter.direct_argument_spans))
    elif typed.fixed_array_in_parameter_proof is not None:
        raise GeneratorError(
            f"{typed.key}: malformed fixed-array input-parameter proof key")
    recomputed_task20_program = dataclasses.replace(
        recomputed_task19_program,
        fixed_array_in_parameter_proof=recomputed_task19)
    try:
        recomputed_task20 = prove_fixed_affine_centers13(recomputed_task20_program)
    except ValueError as error:
        raise GeneratorError(f"{typed.key}: {error}") from error
    if typed.key == SACRED_KEY:
        if (recomputed_task20 is None
                or typed.fixed_affine_centers13_proof != recomputed_task20):
            raise GeneratorError(
                f"{typed.key}: malformed fixed-affine centers13 profile")
        proved_array_declarations[recomputed_task20.symbol_id] = (
            recomputed_task20.declaration_span, recomputed_task20.array_type)
        proved_task20_indices.update(
            (recomputed_task20.symbol_id, item.index_span, "lvalue")
            for item in recomputed_task20.store_regions)
        proved_task20_indices.update(
            (recomputed_task20.symbol_id, item.index_span, "rvalue")
            for item in recomputed_task20.read_sites)
    elif typed.fixed_affine_centers13_proof is not None:
        raise GeneratorError(
            f"{typed.key}: malformed fixed-affine centers13 proof key")

    def audit_counter_proofs(actual, expected) -> None:
        if (actual.kind != expected.kind or len(actual.children) != len(expected.children)
                or actual.counter_proof != expected.counter_proof):
            raise GeneratorError(
                f"{location(actual)}: malformed discarded local-counter proof")
        for actual_child, expected_child in zip(actual.children, expected.children):
            audit_counter_proofs(actual_child, expected_child)

    has_counter_proof = False
    for actual_function, expected_function in zip(typed.functions,
                                                  recomputed_counter_functions):
        if (actual_function.signature.id != expected_function.signature.id
                or len(actual_function.body) != len(expected_function.body)):
            raise GeneratorError(
                f"{location(actual_function)}: malformed discarded local-counter proof functions")
        for actual_statement, expected_statement in zip(actual_function.body,
                                                         expected_function.body):
            audit_counter_proofs(actual_statement, expected_statement)

            def contains_counter(statement) -> bool:
                return (statement.counter_proof is not None
                        or any(contains_counter(child) for child in statement.children))

            has_counter_proof = has_counter_proof or contains_counter(actual_statement)
    if has_counter_proof and typed.key != COMPUTE_RANK_KEY:
        raise GeneratorError(f"{typed.key}: malformed discarded local-counter proof key")
    if typed.counted_loop_proof != recomputed_program_proof:
        raise GeneratorError(f"{typed.key}: malformed counted-for program proof")
    if not recomputed_program_proof.call_graph_acyclic:
        offender = next((function for function in recomputed_functions if function.body), typed)
        raise GeneratorError(
            f"{location(offender)}: unsupported counted-for program proof")
    if (recomputed_program_proof.unproved_loop_count
            or recomputed_program_proof.max_effective_depth > 3
            or recomputed_program_proof.max_lexical_product > 4096
            or recomputed_program_proof.entrypoint_charge > 4096):
        # Programs without a loop stay valid after the unconditional call-graph
        # check above; only an actual unproved or over-budget loop reaches here.
        if recomputed_program_proof.loop_count or recomputed_program_proof.unproved_loop_count:
            def first_loop(statements):
                for statement in statements:
                    if statement.kind in {"for", "while", "dowhile"}:
                        return statement
                    if (nested := first_loop(statement.children)) is not None:
                        return nested
                return None

            offender = next((candidate for function in recomputed_functions
                             if (candidate := first_loop(function.body)) is not None), typed)
            raise GeneratorError(
                f"{location(offender)}: unsupported counted-for program proof")

    admitted_globals: dict[int, object] = {}
    admitted_literal_ints = {
        declaration.symbol.id for declaration in typed.declarations
        if (typed.key in SOURCE_GLOBAL_LITERAL_INT_KEYS
            and declaration.symbol.storage == "const"
            and declaration.type.display() == "int")
    }
    for declaration in typed.declarations:
        storage = declaration.symbol.storage
        if storage in {"uniform", "output"}:
            continue
        if declaration.symbol.id in admitted_literal_ints:
            admitted_globals[declaration.symbol.id] = declaration
            continue
        if declaration is authorized_smooth_edge_luma_weights_declaration:
            admitted_globals[declaration.symbol.id] = declaration
            continue
        if declaration is authorized_grade_luma_weights_declaration:
            admitted_globals[declaration.symbol.id] = declaration
            continue
        if storage != "const" or declaration.type != FLOAT or declaration.initializer is None:
            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")

        def global_initializer(value) -> None:
            if value.type != FLOAT:
                raise GeneratorError(f"{location(value)}: unsupported global initializer type {value.type.display()}")
            if value.kind == "literal":
                if value.literal is None or value.literal_value is None:
                    raise GeneratorError(f"{location(value)}: malformed global initializer literal")
                return
            if value.kind == "id":
                dependency = admitted_globals.get(value.symbol_id)
                if (dependency is None or value.symbol is None
                        or value.symbol.id != value.symbol_id
                        or dependency.symbol.id != value.symbol_id):
                    raise GeneratorError(
                        f"{location(value)}: global initializer dependency must name an earlier admitted const float")
                return
            if value.kind == "unary" and value.operator in {"+", "-"} and len(value.children) == 1:
                global_initializer(value.children[0])
                return
            if value.kind == "binary" and value.operator in {"+", "-", "*", "/"} and len(value.children) == 2:
                global_initializer(value.children[0])
                global_initializer(value.children[1])
                return
            raise GeneratorError(f"{location(value)}: unsupported global initializer expression {value.kind}")

        global_initializer(declaration.initializer)
        admitted_globals[declaration.symbol.id] = declaration

    def targets_admitted_global(value) -> bool:
        if value.kind == "id":
            return value.symbol_id in admitted_globals
        if value.kind in {"swizzle", "index", "member"} and value.children:
            return targets_admitted_global(value.children[0])
        return False

    def audit_expression(value) -> None:
        if (value.kind == "assign" and value.children
                and targets_admitted_global(value.children[0])):
            raise GeneratorError(f"{location(value)}: write to source const global")
        if (value.kind in {"unary", "post"} and value.operator in {"++", "--"}
                and value.children and targets_admitted_global(value.children[0])):
            raise GeneratorError(f"{location(value)}: write to source const global")
        for child in value.children:
            audit_expression(child)

    def audit_statement(value) -> None:
        for expression_value in value.expressions:
            audit_expression(expression_value)
        for child in value.children:
            audit_statement(child)

    for function in typed.functions:
        for statement_value in function.body:
            audit_statement(statement_value)

    if typed.structs:
        raise GeneratorError(f"{location(typed.structs[0])}: unsupported struct declaration")
    if typed.uniform_blocks:
        raise GeneratorError(f"{location(typed.uniform_blocks[0])}: unsupported uniform block")
    if typed.interface_symbols:
        raise GeneratorError(f"{location(typed.interface_symbols[0])}: unsupported varying")
    for declaration in typed.declarations:
        reject_type(declaration.type, declaration)
        if declaration.type.kind == "matrix":
            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")
        if declaration.symbol.storage not in {"uniform", "output", "const"}:
            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")
    def expression(value, context: str = "rvalue") -> None:
        if (value.type.kind == "sampler"
                and getattr(value.symbol, "storage", None) != "uniform"
                and authorized_focus_blur_proof is None):
            raise GeneratorError(
                f"{location(value)}: unsupported sampler expression")
        if any(value is item for item in authorized_rotate_expressions):
            visited_rotate_expressions.append(value)
        reject_type(value.type, value)
        if value.kind == "construct":
            used.add("constructors")
            if value.type.kind == "matrix":
                if (value.type.display() != "mat2" or len(value.children) != 4
                        or any(child.type.display() != "float" for child in value.children)):
                    raise GeneratorError(f"{location(value)}: unsupported matrix constructor")
                used.add("mat2-vector-multiply")
            elif any(child.type.kind == "matrix" for child in value.children):
                raise GeneratorError(f"{location(value)}: unsupported matrix conversion")
        elif value.kind == "binary":
            if value.operator not in APPROVED_BINARY_OPERATORS:
                raise GeneratorError(f"{location(value)}: unsupported binary operator {value.operator}")
            left, right = value.children
            left_type, right_type = left.type.display(), right.type.display()
            if value.operator == "%":
                if left_type not in {"int", "uint"} or right_type != left_type:
                    raise GeneratorError(f"{location(value)}: unsupported binary operator %")
                used.add("integer-modulo")
            elif value.operator == ">>":
                if left_type not in {"uvec2", "uvec3", "uvec4"} or right_type != "uint":
                    raise GeneratorError(f"{location(value)}: unsupported binary operator >>")
                used.add("uint-vector-bitwise")
            elif value.operator == "^":
                if any(value is item
                       for item in authorized_caustic_scalar_uint_xors):
                    # Authenticated by caustic-float-bits-scalar-word-hash-v1.
                    # Like Perlin's, these add no capability to the vocabulary.
                    if (left_type, right_type, value.type.display()) != (
                            "uint", "uint", "uint"):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated scalar uint XOR")
                    visited_caustic_scalar_uint_xors.append(value)
                elif any(value is item for item in authorized_perlin_scalar_uint_xors):
                    if (left_type, right_type, value.type.display()) != (
                            "uint", "uint", "uint"):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated scalar uint XOR")
                    visited_perlin_scalar_uint_xors.append(value)
                else:
                    if (left_type not in {"uvec2", "uvec3", "uvec4"}
                            or right_type != left_type):
                        raise GeneratorError(
                            f"{location(value)}: unsupported binary operator ^")
                    used.add("uint-vector-bitwise")
            elif left.type.kind == "matrix" or right.type.kind == "matrix":
                if value.operator != "*" or left_type != "mat2" or right_type != "vec2":
                    raise GeneratorError(f"{location(value)}: unsupported matrix binary expression")
                used.add("mat2-vector-multiply")
            used.add("scalar-vector-arithmetic")
        elif value.kind == "conditional": used.add("conditional")
        elif value.kind == "swizzle": used.add("swizzles")
        elif value.kind == "call": used.add("functions")
        elif value.kind == "builtin":
            if value.callee == "round":
                if value is not authorized_round:
                    raise GeneratorError(f"{location(value)}: unsupported builtin round")
            elif value.callee == "tanh":
                # Admitted only for the exact node authenticated by
                # curl-vector-math-tanh-wide-mod-v1. Never enters the
                # capability vocabulary and never joins _BUILTINS.
                if (authorized_curl_tanh is None
                        or value is not authorized_curl_tanh):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                visited_curl_nodes.append(value)
            elif value.callee == "floatBitsToUint":
                # Admitted only for the exact node authenticated by
                # caustic-float-bits-scalar-word-hash-v1. Never enters the
                # capability vocabulary.
                if (authorized_caustic_ingress is None
                        or value is not authorized_caustic_ingress):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                visited_caustic_ingress.append(value)
            elif value.callee in {"all", "lessThanEqual"}:
                # Admitted only for the exact nodes authenticated by
                # extrude-bvec2-relational-reduction-v1, by object identity.
                # Like `round`, these never enter the capability vocabulary.
                authorized_extrude_nodes = (*authorized_extrude_reductions,
                                            *authorized_extrude_relationals)
                if not any(value is item for item in authorized_extrude_nodes):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                visited_extrude_nodes.append(value)
            elif value.callee in {"dFdx", "dFdy", "fwidth"}:
                # Admitted only for the exact nodes authenticated by
                # derivative-admission-v1, by object identity. Like
                # round/tanh/floatBitsToUint/all/lessThanEqual, these never
                # enter the frozen 44-entry capability vocabulary.
                if not any(value is item for item in authorized_derivative_nodes):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                visited_derivative_nodes.append(value)
            elif value.callee not in _BUILTINS:
                raise GeneratorError(f"{location(value)}: unsupported builtin {value.callee}")
            if value.callee == "mod":
                argument_types = tuple(child.type.display() for child in value.children)
                # The shared overload tuple stays untouched so no other program
                # gains wider mod. Curl's three calls are admitted by object
                # identity only.
                if argument_types not in {("float", "float"), ("vec2", "float"), ("vec2", "vec2")}:
                    if not any(value is item for item in authorized_curl_mod_nodes):
                        raise GeneratorError(f"{location(value)}: unsupported builtin mod overload")
                    visited_curl_nodes.append(value)
            if value.callee == "texelFetch":
                argument_types = tuple(child.type.display() for child in value.children)
                exact_level_zero = (len(value.children) == 3
                                    and value.children[2].kind == "literal"
                                    and value.children[2].literal == "0"
                                    and value.children[2].literal_value == 0)
                if argument_types != ("sampler2D", "ivec2", "int") or not exact_level_zero:
                    raise GeneratorError(f"{location(value)}: unsupported builtin texelFetch overload")
            if value.callee not in {"round", "all", "lessThanEqual",
                                    "floatBitsToUint", "tanh",
                                    "dFdx", "dFdy", "fwidth"}:
                used.add(value.callee)
        elif value.kind == "unary" and value.operator not in {"+", "-", "!"}:
            raise GeneratorError(f"{location(value)}: unsupported unary operator {value.operator}")
        elif value.kind == "index":
            if len(value.children) != 2 or value.children[0].kind != "id":
                raise GeneratorError(f"{location(value)}: unsupported typed expression index")
            base, index = value.children
            declaration = proved_array_declarations.get(base.symbol_id)
            parameter = proved_array_parameters.get(base.symbol_id)
            base_valid = (base.symbol is not None
                          and base.symbol.id == base.symbol_id
                          and ((declaration is not None
                                and declaration[1] == base.type.display())
                               or (parameter is not None
                                   and parameter[1] == base.type.display())))
            store_valid = (index.kind == "literal"
                           and isinstance(index.literal_value, int)
                           and (base.symbol_id, index.literal_value, value.span)
                           in proved_store_indices)
            read_valid = (index.kind == "id" and index.symbol_id is not None
                          and (base.symbol_id, index.symbol_id, value.span)
                          in proved_read_indices)
            grid_store_valid = (
                context == "lvalue" and index.kind == "id"
                and index.symbol_id is not None
                and (base.symbol_id, index.symbol_id, value.span)
                in proved_grid_dynamic_stores)
            grid_read_valid = (
                context == "rvalue" and index.kind == "literal"
                and isinstance(index.literal_value, int)
                and (base.symbol_id, index.literal_value, value.span)
                in proved_grid_literal_reads)
            task19_store_valid = (
                context == "lvalue" and index.kind == "literal"
                and isinstance(index.literal_value, int)
                and (base.symbol_id, index.literal_value, value.span)
                in proved_task19_store_indices)
            task19_read_valid = (
                context == "rvalue" and index.kind == "id"
                and index.symbol_id is not None
                and (base.symbol_id, index.symbol_id, value.span)
                in proved_task19_read_indices)
            task20_valid = (
                (base.symbol_id, value.span, context) in proved_task20_indices)
            # Grade's lane-indexed local vec3 sites are admitted purely by
            # node identity in the frozen per-program proof set -- never by
            # widening `base_valid` (which requires a proved fixed-size
            # array; grade's bases are plain locals and can never satisfy
            # it) and never by adding a new `used.add(...)` token. This is
            # an explicit skip, symmetric with the existing
            # round/tanh/floatBitsToUint/all+lessThanEqual callee
            # skip-list below: the 44-entry capability vocabulary must not
            # grow for this shape.
            grade_valid = any(value is item for item in authorized_grade_index_sites)
            if grade_valid:
                visited_grade_index_sites.append(value)
            elif not base_valid or not (
                    store_valid or read_valid or grid_store_valid or grid_read_valid
                    or task19_store_valid or task19_read_valid or task20_valid):
                raise GeneratorError(f"{location(value)}: unsupported typed expression index")
            elif task20_valid:
                used.add(FIXED_AFFINE_CENTERS13_CAPABILITY)
            elif task19_store_valid or task19_read_valid:
                used.add(FIXED_ARRAY_PARAMETER_CAPABILITY)
            else:
                used.add(FIXED_GRID_CAPABILITY if grid_store_valid or grid_read_valid
                         else FIXED_NINE_CAPABILITY)
        elif value.kind not in {"id", "literal", "declaration", "assign", "unary"}:
            raise GeneratorError(f"{location(value)}: unsupported typed expression {value.kind}")
        if value.kind == "assign":
            if value.operator not in APPROVED_ASSIGNMENT_OPERATORS:
                raise GeneratorError(f"{location(value)}: unsupported assignment operator {value.operator}")
            if value.operator == "^=":
                left, right = value.children
                if (left.kind != "id" or left.type.display() not in {"uvec2", "uvec3", "uvec4"}
                        or right.type != left.type):
                    raise GeneratorError(f"{location(value)}: unsupported assignment operator ^=")
                used.add("uint-vector-bitwise")
            used.add("assign")
        if value.kind == "index":
            expression(value.children[1])
        elif value.kind == "assign":
            expression(value.children[0], "lvalue")
            expression(value.children[1])
        else:
            for child in value.children: expression(child)
    def statement(value, loop_depth: int = 0) -> None:
        if value.counter_proof is not None:
            if (value.kind != "expr" or len(value.expressions) != 1
                    or value.expressions[0].kind != "post"
                    or value.expressions[0].operator != "++"
                    or len(value.expressions[0].children) != 1
                    or value.expressions[0].children[0].kind != "id"
                    or value.expressions[0].children[0].symbol_id
                    != value.counter_proof.target_symbol_id
                    or value.expressions[0].children[0].type.display() != "int"):
                raise GeneratorError(
                    f"{location(value)}: malformed discarded local-counter statement")
            used.add(LOCAL_COUNTER_CAPABILITY)
            return
        grid_update = value.expressions[0] if (
            value.kind == "expr" and len(value.expressions) == 1) else None
        if (grid_update is not None and grid_update.kind == "post"
                and grid_update.operator == "++" and len(grid_update.children) == 1
                and grid_update.children[0].kind == "id"
                and (grid_update.children[0].symbol_id, grid_update.span, value.span)
                in proved_grid_updates):
            if grid_update.children[0].type.display() != "int":
                raise GeneratorError(
                    f"{location(value)}: malformed fixed-grid counter update")
            used.add(FIXED_GRID_CAPABILITY)
            return
        if value.kind == "block": used.add("blocks")
        elif value.kind == "if": used.add("if")
        elif value.kind == "for":
            if value.loop_proof is None or len(value.expressions) != 2 or len(value.children) != 2:
                raise GeneratorError(f"{location(value)}: unsupported typed statement for")
            used.add("counted-for-v1")
            statement(value.children[0], loop_depth)
            expression(value.expressions[0])
            statement(value.children[1], loop_depth + 1)
            return
        elif value.kind in {"break", "continue"}:
            if loop_depth == 0:
                raise GeneratorError(f"{location(value)}: unsupported typed statement {value.kind}")
            used.add("counted-for-v1")
            return
        elif value.kind not in {"decl", "expr", "return"}:
            raise GeneratorError(f"{location(value)}: unsupported typed statement {value.kind}")
        if value.kind == "return" and loop_depth:
            raise GeneratorError(f"{location(value)}: unsupported loop return")
        if value.kind == "decl" and len(value.expressions) > 1:
            used.add("multi-declarations")
        for expression_value in value.expressions: expression(expression_value)
        for child in value.children: statement(child, loop_depth)
    for function in typed.functions:
        reject_type(function.return_type, function)
        if function.return_type.kind == "sampler":
            raise GeneratorError(
                f"{location(function)}: unsupported sampler return type")
        if (function.return_type.kind == "matrix"
                and function is not authorized_rotate_helper):
            raise GeneratorError(f"{location(function)}: unsupported matrix return type")
        for parameter in function.parameters:
            reject_type(parameter.type, parameter)
            if (parameter.type.kind == "sampler"
                    and (authorized_focus_blur_proof is None
                         or function is not authorized_focus_blur_proof.helper
                         or not any(parameter is item for item in
                                    authorized_focus_blur_proof.sampler_parameters))):
                raise GeneratorError(
                    f"{location(parameter)}: unsupported sampler parameter")
            if parameter.type.kind == "matrix":
                raise GeneratorError(f"{location(parameter)}: unsupported matrix parameter")
            if parameter.direction != "in":
                raise GeneratorError(
                    f"{typed.key}:{parameter.span.start_line}:{parameter.span.start_column}: "
                    f"unsupported parameter direction {parameter.direction}")
        for statement_value in function.body: statement(statement_value)
    if typed.key == GATHER_SORTED_KEY and gather_sorted_round_profile is None:
        raise GeneratorError(
            f"{typed.key}: exact Gather Sorted round profile carrier required")
    if ((typed.key in LITERAL_VEC3_LANE_INDEX_KEYS or literal_source_key is not None)
            and literal_vec3_lane_index_profile is None):
        raise GeneratorError(
            f"{typed.key}: exact literal vec3 lane profile carrier required")
    if (authorized_perlin_scalar_uint_xors
            and tuple(visited_perlin_scalar_uint_xors)
            != authorized_perlin_scalar_uint_xors):
        raise GeneratorError(
            f"{typed.key}: authenticated scalar uint XOR traversal mismatch")
    if (authorized_rotate_expressions
            and tuple(visited_rotate_expressions)
            != (authorized_rotate_expressions[2],
                authorized_rotate_expressions[1],
                authorized_rotate_expressions[0])):
        raise GeneratorError(
            f"{typed.key}: authenticated Rotate matrix traversal mismatch")
    if authorized_focus_blur_proof is not None:
        visited: list[object] = []
        authorized = authorized_focus_blur_proof.consumed_objects
        def consume(value: object) -> None:
            if any(value is item for item in authorized):
                if any(value is item for item in visited):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Focus Blur object visited twice")
                visited.append(value)
        def consume_expression(value: TypedExpression) -> None:
            consume(value)
            for child in value.children: consume_expression(child)
        def consume_statement(value) -> None:
            consume(value)
            for item in value.expressions: consume_expression(item)
            for child in value.children: consume_statement(child)
        for function in typed.functions:
            consume(function)
            for parameter in function.parameters: consume(parameter)
            for item in function.body: consume_statement(item)
        if len(visited) != len(authorized) or any(
                not any(value is item for item in visited) for value in authorized):
            raise GeneratorError(
                f"{typed.key}: authenticated Focus Blur traversal mismatch")
    if authorized_curl_proof is not None:
        expected = authorized_curl_proof.nodes
        if len(visited_curl_nodes) != len(expected) or any(
                not any(value is item for item in visited_curl_nodes)
                for value in expected):
            raise GeneratorError(
                f"{typed.key}: authenticated Curl traversal mismatch")
    if authorized_caustic_proof is not None:
        if (len(visited_caustic_ingress) != 1
                or visited_caustic_ingress[0] is not authorized_caustic_ingress
                or len(visited_caustic_scalar_uint_xors)
                != len(authorized_caustic_scalar_uint_xors)
                or any(not any(value is item
                               for item in visited_caustic_scalar_uint_xors)
                       for value in authorized_caustic_scalar_uint_xors)):
            raise GeneratorError(
                f"{typed.key}: authenticated Caustic traversal mismatch")
    if authorized_extrude_proof is not None:
        authorized_nodes = (*authorized_extrude_reductions,
                            *authorized_extrude_relationals)
        if len(visited_extrude_nodes) != len(authorized_nodes) or any(
                not any(value is item for item in visited_extrude_nodes)
                for value in authorized_nodes):
            raise GeneratorError(
                f"{typed.key}: authenticated Extrude traversal mismatch")
    if authorized_grade_index_sites and (
            len(visited_grade_index_sites) != len(authorized_grade_index_sites)
            or any(not any(value is item for item in visited_grade_index_sites)
                   for value in authorized_grade_index_sites)):
        raise GeneratorError(
            f"{typed.key}: authenticated Grade index expression traversal mismatch")
    if authorized_derivative_proof is not None:
        expected = authorized_derivative_proof.nodes
        if len(visited_derivative_nodes) != len(expected) or any(
                not any(value is item for item in visited_derivative_nodes)
                for value in expected):
            raise GeneratorError(
                f"{typed.key}: authenticated Derivative traversal mismatch")
    missing = sorted(used - set(capabilities))
    if missing: raise GeneratorError(f"{typed.key}: missing capabilities {', '.join(missing)}")


def generate_outputs(repository: pathlib.Path = _ROOT) -> dict[str, bytes]:
    repository = repository.resolve()
    check_corpus.validate_corpus(repository)
    semantic = check_semantics.semantic_report(repository)
    if semantic["body_success"] != 212: raise GeneratorError("semantic analysis did not cover corpus")
    slice_spec = load_slice(repository)
    if slice_spec["revision"] != check_corpus.REVISION: raise GeneratorError("typed slice revision drift")
    root = check_corpus._corpus_root(repository)
    metadata = check_corpus._load_json(root / "metadata.json", "metadata")
    bodies: list[str] = []
    manifest_programs: list[dict[str, Any]] = []
    for index, entry in enumerate(_source_entries(repository, slice_spec)):
        key = entry["program_key"]
        source = (root / entry["source"]).read_text(encoding="utf-8")
        source_hash = _sha256(source.encode("utf-8"))
        if source_hash != entry["raw_sha256"]: raise GeneratorError(f"{key}: pinned source hash mismatch")
        declared_defines = slice_spec["programs"][index]["defines"]
        metadata_defines = _defaults(repository, key)
        if metadata_defines != declared_defines:
            raise GeneratorError(f"{key}: authoritative metadata default defines drift")
        source_global_literal_int_profile = (
            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
            if key in SOURCE_GLOBAL_LITERAL_INT_KEYS else None)
        typed = analyze_program(
            parse_program(source, key, declared_defines), key,
            source_global_literal_int_profile=source_global_literal_int_profile)
        compatibility_transform = slice_spec["compatibility_transforms"].get(key)
        if compatibility_transform is not None:
            typed = apply_compatibility_transform(typed, compatibility_transform)
        custom_comparer_profile = slice_spec["custom_comparer_profiles"].get(key)
        if custom_comparer_profile is not None:
            try:
                authenticate_lens_custom_comparer_pre(
                    typed, source_hash, custom_comparer_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
        typed = attach_fixed_array_in_parameter_proof(typed)
        typed = attach_fixed_affine_centers13_proof(typed)
        literal_contract = slice_spec["numeric_literal_contracts"].get(key, "glsl-f32")
        gather_sorted_round_profile = slice_spec["programs"][index].get(
            "gather_sorted_round_profile")
        if gather_sorted_round_profile is not None:
            try:
                profiled = apply_gather_sorted_round_to_int(
                    typed, source_hash, gather_sorted_round_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(f"{key}: Gather Sorted identity profile mutated program")
            typed = profiled
        literal_vec3_lane_index_profile = slice_spec["programs"][index].get(
            "literal_vec3_lane_index_profile")
        if literal_vec3_lane_index_profile is not None:
            try:
                profiled = apply_literal_vec3_lane_index(
                    typed, source_hash, literal_vec3_lane_index_profile)
                authenticate_literal_vec3_lane_index_transition(
                    typed, profiled, source_hash,
                    literal_vec3_lane_index_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is typed:
                raise GeneratorError(f"{key}: literal vec3 lane profile did not transform program")
            typed = profiled
        smooth_edge_luma_weights_profile = slice_spec["programs"][index].get(
            "smooth_edge_luma_weights_profile")
        if smooth_edge_luma_weights_profile is not None:
            try:
                profiled = apply_smooth_edge_luma_weights(
                    typed, source_hash, smooth_edge_luma_weights_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Smooth Edge LUMA weights identity profile mutated program")
            typed = profiled
        perlin_scalar_uint_xor_profile = slice_spec["programs"][index].get(
            "perlin_scalar_uint_xor_profile")
        if perlin_scalar_uint_xor_profile is not None:
            try:
                profiled = apply_perlin_scalar_uint_xor(
                    typed, source_hash, perlin_scalar_uint_xor_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Perlin scalar uint XOR identity profile mutated program")
            typed = profiled
        rotate_mat2_return_profile = slice_spec["programs"][index].get(
            "rotate_mat2_return_profile")
        if rotate_mat2_return_profile is not None:
            try:
                profiled = apply_rotate_mat2_return(
                    typed, source_hash, rotate_mat2_return_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Rotate mat2 return identity profile mutated program")
            typed = profiled
        focus_blur_borrowed_sampler_profile = slice_spec["programs"][index].get(
            "focus_blur_borrowed_sampler_profile")
        if focus_blur_borrowed_sampler_profile is not None:
            try:
                profiled = apply_focus_blur_borrowed_sampler_parameters(
                    typed, source_hash, focus_blur_borrowed_sampler_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Focus Blur borrowed sampler identity profile mutated program")
            typed = profiled
        curl_vector_math_profile = slice_spec["programs"][index].get(
            "curl_vector_math_profile")
        if curl_vector_math_profile is not None:
            try:
                profiled = apply_curl_vector_math(
                    typed, source_hash, curl_vector_math_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Curl vector math identity profile mutated program")
            typed = profiled
        curl_vector_math_profile = slice_spec["programs"][index].get(
            "curl_vector_math_profile")
        if curl_vector_math_profile is not None:
            try:
                profiled = apply_curl_vector_math(typed, source_hash, curl_vector_math_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(f"{key}: Curl vector math identity profile mutated program")
            typed = profiled
        caustic_word_hash_profile = slice_spec["programs"][index].get(
            "caustic_word_hash_profile")
        if caustic_word_hash_profile is not None:
            try:
                profiled = apply_caustic_word_hash(
                    typed, source_hash, caustic_word_hash_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Caustic word hash identity profile mutated program")
            typed = profiled
        extrude_bvec2_relational_reduction_profile = (
            slice_spec["programs"][index].get(
                "extrude_bvec2_relational_reduction_profile"))
        if extrude_bvec2_relational_reduction_profile is not None:
            try:
                profiled = apply_extrude_bvec2_relational_reduction(
                    typed, source_hash,
                    extrude_bvec2_relational_reduction_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Extrude bvec2 relational reduction identity profile "
                    f"mutated program")
            typed = profiled
        grade_luma_weights_profile = slice_spec["programs"][index].get(
            "grade_luma_weights_profile")
        if grade_luma_weights_profile is not None:
            try:
                profiled = apply_grade_luma_weights(
                    typed, source_hash, grade_luma_weights_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Grade LUMA weights identity profile mutated program")
            typed = profiled
        grade_index_expression_profile = slice_spec["programs"][index].get(
            "grade_index_expression_profile")
        if grade_index_expression_profile is not None:
            try:
                profiled = apply_grade_index_expression(
                    typed, source_hash, grade_index_expression_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Grade index expression identity profile mutated program")
            typed = profiled
        derivative_admission_profile = slice_spec["programs"][index].get(
            "derivative_admission_profile")
        if derivative_admission_profile is not None:
            try:
                profiled = apply_derivative_admission(
                    typed, source_hash, derivative_admission_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Derivative admission identity profile mutated program")
            typed = profiled
        if key == DEGAUSS_KEY:
            validate_current_vocabulary_degauss(
                typed, entry, declared_defines,
                compatibility_transform=compatibility_transform,
                numeric_literal_contract=literal_contract,
                metadata_effect=metadata.get("effects", {}).get("filter/degauss"))
        if key == CRT_KEY:
            validate_current_vocabulary_crt(
                typed, entry, declared_defines,
                compatibility_transform=compatibility_transform,
                numeric_literal_contract=literal_contract,
                metadata_effect=metadata.get("effects", {}).get("filter/crt"))
        validate_capabilities(typed, tuple(slice_spec["capabilities"]),
                              source_hash=source_hash,
                              compatibility_transform=compatibility_transform,
                              custom_comparer_profile=custom_comparer_profile,
                              numeric_literal_contract=literal_contract,
                              source_global_literal_int_profile=source_global_literal_int_profile,
                              gather_sorted_round_profile=gather_sorted_round_profile,
                              literal_vec3_lane_index_profile=literal_vec3_lane_index_profile,
                              smooth_edge_luma_weights_profile=smooth_edge_luma_weights_profile,
                              perlin_scalar_uint_xor_profile=perlin_scalar_uint_xor_profile,
                              rotate_mat2_return_profile=rotate_mat2_return_profile,
                              focus_blur_borrowed_sampler_profile=focus_blur_borrowed_sampler_profile,
                              extrude_bvec2_relational_reduction_profile=extrude_bvec2_relational_reduction_profile,
                              caustic_word_hash_profile=caustic_word_hash_profile,
                              curl_vector_math_profile=curl_vector_math_profile,
                              grade_luma_weights_profile=grade_luma_weights_profile,
                              grade_index_expression_profile=grade_index_expression_profile,
                              derivative_admission_profile=derivative_admission_profile)
        try:
            bodies.append(render_typed_cpp(typed, key, source_hash,
                                           f"typed_{index}", "bind_" + key.replace("/", "_").replace(":", "_"),
                                           numeric_literal_contract=literal_contract,
                                           compatibility_transform=compatibility_transform,
                                           custom_comparer_profile=custom_comparer_profile,
                                           source_global_literal_int_profile=source_global_literal_int_profile,
                                           gather_sorted_round_profile=gather_sorted_round_profile,
                                           literal_vec3_lane_index_profile=literal_vec3_lane_index_profile,
                                           smooth_edge_luma_weights_profile=smooth_edge_luma_weights_profile,
                                           perlin_scalar_uint_xor_profile=perlin_scalar_uint_xor_profile,
                                           rotate_mat2_return_profile=rotate_mat2_return_profile,
                                           focus_blur_borrowed_sampler_profile=focus_blur_borrowed_sampler_profile,
                                           extrude_bvec2_relational_reduction_profile=extrude_bvec2_relational_reduction_profile,
                                           caustic_word_hash_profile=caustic_word_hash_profile,
                                           curl_vector_math_profile=curl_vector_math_profile,
                                           grade_luma_weights_profile=grade_luma_weights_profile,
                                           grade_index_expression_profile=grade_index_expression_profile,
                                           derivative_admission_profile=derivative_admission_profile))
        except TypedEmissionError as error: raise GeneratorError(str(error)) from error
        manifest_program = {
            "capabilities": slice_spec["capabilities"],
            "define_contract": "default-only" if declared_defines else "none",
            "compatibility_transform": compatibility_transform or "none",
            "defines": declared_defines,
            "factory": "bind_" + key.replace("/", "_").replace(":", "_"),
            "numeric_literal_contract": literal_contract,
            "output": "typed_slice.cpp", "program_key": key,
            "source": entry["source"], "source_sha256": source_hash,
        }
        if custom_comparer_profile is not None:
            manifest_program["custom_comparer_profile"] = custom_comparer_profile
        if smooth_edge_luma_weights_profile is not None:
            manifest_program["smooth_edge_luma_weights_profile"] = (
                smooth_edge_luma_weights_profile)
        if perlin_scalar_uint_xor_profile is not None:
            manifest_program["perlin_scalar_uint_xor_profile"] = (
                perlin_scalar_uint_xor_profile)
        if rotate_mat2_return_profile is not None:
            manifest_program["rotate_mat2_return_profile"] = (
                rotate_mat2_return_profile)
        if focus_blur_borrowed_sampler_profile is not None:
            manifest_program["focus_blur_borrowed_sampler_profile"] = (
                focus_blur_borrowed_sampler_profile)
        if extrude_bvec2_relational_reduction_profile is not None:
            manifest_program["extrude_bvec2_relational_reduction_profile"] = (
                extrude_bvec2_relational_reduction_profile)
        if caustic_word_hash_profile is not None:
            manifest_program["caustic_word_hash_profile"] = (
                caustic_word_hash_profile)
        if curl_vector_math_profile is not None:
            manifest_program["curl_vector_math_profile"] = (
                curl_vector_math_profile)
        if grade_luma_weights_profile is not None:
            manifest_program["grade_luma_weights_profile"] = (
                grade_luma_weights_profile)
        if grade_index_expression_profile is not None:
            manifest_program["grade_index_expression_profile"] = (
                grade_index_expression_profile)
        if curl_vector_math_profile is not None:
            manifest_program["curl_vector_math_profile"] = (
                curl_vector_math_profile)
        if derivative_admission_profile is not None:
            manifest_program["derivative_admission_profile"] = (
                derivative_admission_profile)
        manifest_programs.append(manifest_program)
    cpp = ["// Generated by typed GLSL IR emitter. Do not edit.", f"// Revision: {slice_spec['revision']}",
           "#include \"noisemaker/generated/catalog.hpp\"", "", "#include <array>", "#include <cstdint>", "#include <memory>", "#include <stdexcept>",
           "", "#include \"noisemaker/sampler.hpp\"", "", "namespace noisemaker::generated {"]
    cpp.extend(bodies)
    factories = [(item["program_key"], item["factory"]) for item in manifest_programs]
    factories.extend((("filter/invert:inv", "bind_filter_invert"), ("synth/solid:solid", "bind_synth_solid")))
    factories.sort()
    cpp.extend(["", "namespace {", f"constexpr std::array<KernelFactory, {len(factories)}> kCatalog{{{{"])
    cpp.extend(f"    {{\"{key}\", &{factory}}}," for key, factory in factories)
    cpp.extend(["}};", "}  // namespace", "",
                "std::span<const KernelFactory> catalog() noexcept { return kCatalog; }", "",
                "BoundKernel bind(std::string_view key, const glsl::Bindings& bindings) {",
                "  for (const KernelFactory& factory : kCatalog) if (factory.key == key) return factory.bind(bindings);",
                "  throw std::invalid_argument(\"unknown generated kernel key\");", "}", "", "}  // namespace noisemaker::generated", ""])
    cpp_bytes = "\n".join(cpp).encode("utf-8")
    output_hash = _sha256(cpp_bytes)
    for entry in manifest_programs: entry["output_sha256"] = output_hash
    manifest = {"emitter": EMITTER, "programs": manifest_programs, "revision": slice_spec["revision"], "schema": SCHEMA,
                "typed_slice_sha256": output_hash}
    return {str(_TYPED_DIRECTORY / "typed_manifest.json"): (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            str(_TYPED_DIRECTORY / "typed_slice.cpp"): cpp_bytes}


def _target_directory(repository: pathlib.Path) -> pathlib.Path:
    target = repository / _TYPED_DIRECTORY
    if target.is_symlink() or target.parent.is_symlink():
        raise GeneratorError("typed generated tree contains a symlink")
    if target.exists() and not target.is_dir():
        raise GeneratorError("typed generated output path is not a directory")
    return target


def _validate_owned_tree(directory: pathlib.Path, expected: set[str]) -> None:
    if not directory.exists(): return
    if directory.is_symlink() or not directory.is_dir():
        raise GeneratorError("typed generated output path is invalid")
    actual: set[str] = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_symlink(): raise GeneratorError("typed generated tree contains a symlink")
            if not entry.is_file(follow_symlinks=False): raise GeneratorError("typed generated tree contains an unexpected entry")
            actual.add(entry.name)
    if actual != expected:
        raise GeneratorError(f"typed generated file set drift: expected {sorted(expected)}, got {sorted(actual)}")


def _remove_owned_temporary(path: pathlib.Path, parent: pathlib.Path, prefix: str) -> None:
    if path.parent != parent or not path.name.startswith(prefix) or path.is_symlink():
        raise GeneratorError("refusing to remove an unowned typed generator temporary directory")
    if path.exists(): shutil.rmtree(path)


def check_outputs(repository: pathlib.Path = _ROOT) -> None:
    repository = repository.resolve()
    outputs = generate_outputs(repository)
    target = _target_directory(repository)
    _validate_owned_tree(target, set(_OUTPUTS))
    for relative, content in outputs.items():
        candidate = target / pathlib.PurePosixPath(relative).name
        if candidate.read_bytes() != content:
            raise GeneratorError(f"typed generated output drift: {relative}")
    slice_path = repository / "tools/glslcpp/typed_slice.json"
    if slice_path.exists():
        catalog = repository / _CATALOG_HEADER
        if (catalog.is_symlink() or not catalog.is_file()
                or catalog.read_bytes() != render_catalog_header(load_slice(repository))):
            raise GeneratorError(f"typed generated output drift: {_CATALOG_HEADER}")


def write_outputs(repository: pathlib.Path = _ROOT) -> None:
    repository = repository.resolve(); outputs = generate_outputs(repository)
    target = _target_directory(repository)
    _validate_owned_tree(target, set(_OUTPUTS))
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = pathlib.Path(tempfile.mkdtemp(prefix=".typed-glslcpp-stage-", dir=target.parent))
    backup = pathlib.Path(tempfile.mkdtemp(prefix=".typed-glslcpp-backup-", dir=target.parent))
    _remove_owned_temporary(backup, target.parent, ".typed-glslcpp-backup-")
    had_target = target.exists()
    moved_target = False
    try:
        for relative, content in outputs.items():
            name = pathlib.PurePosixPath(relative).name; _validate_typed_output_name(name)
            (stage / name).write_bytes(content)
        if had_target:
            os.replace(target, backup)
            moved_target = True
        try:
            os.replace(stage, target)
        except BaseException:
            if moved_target:
                try: os.replace(backup, target)
                except BaseException as restore_error:
                    raise GeneratorError("typed generated tree swap failed and rollback could not restore backup") from restore_error
            raise
        else:
            if moved_target: _remove_owned_temporary(backup, target.parent, ".typed-glslcpp-backup-")
    finally:
        if stage.exists(): _remove_owned_temporary(stage, target.parent, ".typed-glslcpp-stage-")
        if backup.exists() and not moved_target: _remove_owned_temporary(backup, target.parent, ".typed-glslcpp-backup-")
    slice_path = repository / "tools/glslcpp/typed_slice.json"
    if slice_path.exists():
        catalog = repository / _CATALOG_HEADER
        if catalog.is_symlink() or catalog.parent.is_symlink():
            raise GeneratorError("typed catalog header path contains a symlink")
        catalog.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".catalog.hpp.typed-glslcpp-", dir=catalog.parent)
        temporary = pathlib.Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(render_catalog_header(load_slice(repository)))
            os.replace(temporary, catalog)
        finally:
            if temporary.exists(): temporary.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True); mode.add_argument("--check", action="store_true"); mode.add_argument("--write", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        if arguments.write: write_outputs()
        else: check_outputs()
    except (GeneratorError, OSError, TypedEmissionError, ValueError) as error:
        print(f"generate_typed_slice: {error}", file=sys.stderr); return 1
    program_count = len(load_slice()["programs"])
    print(f"generate_typed_slice: typed slice ok ({program_count} programs)"); return 0


if __name__ == "__main__": raise SystemExit(main())
