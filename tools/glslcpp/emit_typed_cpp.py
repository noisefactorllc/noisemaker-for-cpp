"""Typed-IR-only C++ emitter for the deliberately small native slice."""

from __future__ import annotations

from dataclasses import dataclass, field
import dataclasses
import hashlib
import math
import struct

from .frontend.loop_proof import (
    COUNTED_FOR_V1_MAX_ENTRYPOINT_CHARGE, COUNTED_FOR_V1_MAX_LEXICAL_PRODUCT,
    COUNTED_FOR_V1_MAX_TRIP_COUNT,
    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY, SOURCE_GLOBAL_LITERAL_INT_KEYS,
    attach_counted_loop_proofs, clear_counted_loop_proofs,
    authenticate_source_global_literal_int,
    rebuild_authenticated_counted_loop_proofs, summarize_counted_loop_proofs)
from .frontend.local_counter_proof import (
    COMPUTE_RANK_KEY, COMPUTE_RANK_NORMALIZED_SHA256, COMPUTE_RANK_RAW_SHA256,
    attach_discarded_local_counter_proofs)
from .frontend.fixed_nine_table_proof import (
    CAPABILITY as FIXED_NINE_CAPABILITY, SOURCE_LOCKS,
    prove_fixed_nine_local_tables, source_provenance_error)
from .frontend.distortion_frontend_profile import (
    KEY as DISTORTION_FRONTEND_KEY,
    PROFILE as DISTORTION_FRONTEND_PROFILE,
    DISTORTION_FRONTEND_KEYS,
    authenticate_distortion_frontend)
from .frontend.fixed_grid_counter_store_proof import (
    SOURCE_LOCKS as FIXED_GRID_SOURCE_LOCKS,
    prove_fixed_grid_counter_store,
    source_provenance_error as fixed_grid_source_provenance_error)
from .frontend.fixed_array_in_parameter_proof import (
    KEYS as FIXED_ARRAY_IN_PARAMETER_KEYS,
    prove_fixed_array_in_parameter,
    source_provenance_error as fixed_array_source_provenance_error)
from .frontend.sacred_geometry_compatibility import (
    SACRED_KEY, TRANSFORM as SACRED_COMPATIBILITY_TRANSFORM,
    authenticate_sacred_star_number_division)
from .frontend.crt_compatibility import (
    CRT_KEY, TRANSFORM as CRT_COMPATIBILITY_TRANSFORM,
    authenticate_crt_metal_sine)
from .frontend.fixed_affine_centers13_proof import (
    prove_fixed_affine_centers13,
    source_provenance_error as fixed_affine_source_provenance_error)
from .frontend.typed_ir import TypedExpression, TypedProgram, TypedStatement
from .frontend.gather_sorted_round_profile import (
    GATHER_SORTED_KEY, PROFILE as GATHER_SORTED_ROUND_PROFILE,
    authenticate_gather_sorted_round_to_int)
from .frontend.literal_vec3_lane_index_profile import (
    KEYS as LITERAL_VEC3_LANE_INDEX_KEYS,
    PROFILE as LITERAL_VEC3_LANE_INDEX_PROFILE,
    _selected_source_key as literal_vec3_lane_selected_source_key,
    authenticate_literal_vec3_lane_index_post)
from .frontend.lens_distortion_comparer_profile import (
    LENS_KEY as LENS_CUSTOM_COMPARER_KEY,
    PROFILE as LENS_CUSTOM_COMPARER_PROFILE,
    authenticate_lens_custom_comparer_final)
from .frontend.smooth_edge_luma_weights_profile import (
    PROFILE as SMOOTH_EDGE_LUMA_WEIGHTS_PROFILE,
    SMOOTH_EDGE_KEY,
    authenticate_smooth_edge_luma_weights)
from .frontend.grade_luma_weights_profile import (
    KEYS as GRADE_LUMA_WEIGHTS_KEYS, PROFILES as GRADE_LUMA_WEIGHTS_PROFILES,
    authenticate_grade_luma_weights)
from .frontend.grade_index_expression_profile import (
    KEYS as GRADE_INDEX_EXPRESSION_KEYS,
    PROFILES as GRADE_INDEX_EXPRESSION_PROFILES,
    authenticate_grade_index_expression)
from .frontend.linear_srgb_lane_index_profile import (
    KEYS as LINEAR_SRGB_LANE_INDEX_KEYS,
    PROFILES as LINEAR_SRGB_LANE_INDEX_PROFILES,
    authenticate_linear_srgb_lane_index)
from .frontend.reflect_admission_profile import (
    LIGHTING_KEY as REFLECT_ADMISSION_KEY,
    PROFILE as REFLECT_ADMISSION_PROFILE,
    authenticate_reflect_admission)
from .frontend.perlin_scalar_uint_xor_profile import (
    PERLIN_KEY, PROFILE as PERLIN_SCALAR_UINT_XOR_PROFILE,
    authenticate_perlin_scalar_uint_xor)
from .frontend.scalar_uint_xor_profile import (
    KALEIDO_INGRESS_KEY as KALEIDO_FLOAT_BITS_INGRESS_KEY,
    NOISE_INGRESS_KEY as NOISE_FLOAT_BITS_INGRESS_KEY,
    PREPARED_SCALAR_UINT_XOR_KEYS,
    PROFILE as SCALAR_UINT_XOR_PROFILE, SCALAR_UINT_XOR_KEYS,
    authenticate_kaleido_float_bits_ingress,
    authenticate_noise_float_bits_ingress,
    authenticate_prepared_noise_float_bits_ingress,
    authenticate_prepared_scalar_uint_xor,
    authenticate_scalar_uint_to_float_narrowing_skips,
    authenticate_scalar_uint_xor)
from .frontend.bitwise_scalar_int_ops_profile import (
    KEYS as BITWISE_SCALAR_INT_OPS_KEYS,
    PROFILES as BITWISE_SCALAR_INT_OPS_PROFILES,
    authenticate_bitwise_scalar_int_ops)
from .frontend.bit_effects_profile import (
    KEY as BIT_EFFECTS_KEY,
    PROFILE as BIT_EFFECTS_PROFILE,
    PREPARED_KEYS as BIT_EFFECTS_PREPARED_KEYS,
    PREPARED_PROFILES as BIT_EFFECTS_PREPARED_PROFILES,
    authenticate_bit_effects_frontend)
from .frontend.rotate_mat2_return_profile import (
    PROFILE as ROTATE_MAT2_RETURN_PROFILE, ROTATE_KEY,
    authenticate_rotate_mat2_return)
from .frontend.caustic_word_hash_profile import (
    CAUSTIC_KEY, authenticate_caustic_word_hash)
from .frontend.scanline_error_float_bits_ingress_profile import (
    SCANLINE_ERROR_KEY, authenticate_scanline_error_float_bits_ingress)
from .frontend.shapes_float_bits_ingress_profile import (
    PROFILE as SHAPES_FLOAT_BITS_INGRESS_PROFILE,
    SHAPES_FLOAT_BITS_INGRESS_KEYS, SHAPES_KEY,
    authenticate_shapes_float_bits_ingress)
from .frontend.grime_float_bits_ingress_profile import (
    PROFILE as GRIME_FLOAT_BITS_INGRESS_PROFILE,
    GRIME_FLOAT_BITS_INGRESS_KEYS,
    authenticate_grime_float_bits_ingress)
from .frontend.shapes_rvalue_assign_profile import (
    PROFILE as SHAPES_RVALUE_ASSIGN_PROFILE, SHAPES_RVALUE_ASSIGN_KEYS,
    authenticate_shapes_rvalue_assign)
from .frontend.cross_lane_assignment_profile import (
    CROSS_LANE_KEY, PROFILE as CROSS_LANE_ASSIGNMENT_PROFILE,
    authenticate_cross_lane_assignment)
from .frontend.mutable_global_frame_profile import (
    MUTABLE_GLOBAL_FRAME_KEYS,
    NOISE_KEY as PREPARED_MUTABLE_GLOBAL_FRAME_NOISE_KEY,
    NOISE_PROFILE as PREPARED_MUTABLE_GLOBAL_FRAME_NOISE_PROFILE,
    PREPARED_MUTABLE_GLOBAL_FRAME_KEYS,
    PROFILES as MUTABLE_GLOBAL_FRAME_PROFILES,
    authenticate_mutable_global_frame,
    authenticate_prepared_mutable_global_frame,
    frame_contract as mutable_global_frame_contract,
    prepared_frame_contract)
from .frontend.noise_runtime_define_profile import (
    dynamic_frame_contract, is_dynamic_program)
from .frontend.mutable_global_array_profile import (
    MUTABLE_GLOBAL_ARRAY_KEYS,
    PROFILES as MUTABLE_GLOBAL_ARRAY_PROFILES,
    REQUIRED_COMPANION_PROFILES as MUTABLE_GLOBAL_ARRAY_COMPANIONS,
    authenticate_mutable_global_array, frame_contract as mutable_global_array_contract,
    store_census as mutable_global_array_store_census)
from .frontend.const_global_table_profile import (
    CONST_GLOBAL_TABLE_KEYS,
    PROFILES as CONST_GLOBAL_TABLE_PROFILES,
    REQUIRED_COMPANION_PROFILES as CONST_GLOBAL_TABLE_COMPANIONS,
    authenticate_const_global_table_reads, authenticate_const_global_tables,
    table_contract as const_global_table_contract)
from .frontend.varying_uv_profile import (
    VARYING_UV_KEYS,
    PROFILES as VARYING_UV_PROFILES,
    authenticate_varying_uv, varying_uv_contract)
from .frontend.texture_lod_admission_profile import (
    PARALLAX_KEY as TEXTURE_LOD_ADMISSION_PARALLAX_KEY,
    PARALLAX_PROFILE as TEXTURE_LOD_ADMISSION_PROFILE,
    TEXTURE_LOD_ADMISSION_KEYS,
    authenticate_texture_lod_admission)
from .frontend.texture_frontend_profile import (
    KEY as TEXTURE_FRONTEND_KEY,
    PROFILE as TEXTURE_FRONTEND_PROFILE,
    authenticate_texture_frontend)
from .frontend.glyph_map_nonnegative_int_shift_profile import (
    GLYPH_MAP_KEY, authenticate_glyph_map_nonnegative_int_shift)
from .frontend.curl_vector_math_profile import (
    CURL_KEY, authenticate_curl_vector_math)
from .frontend.extrude_bvec2_relational_reduction_profile import (
    EXTRUDE_KEY, authenticate_extrude_bvec2_relational_reduction)
from .frontend.edge_bvec3_contour_profile import (
    EDGE_KEY, authenticate_edge_bvec3_contour,
    authenticate_edge_center_splat)
from .frontend.glitch_mat4_chain_profile import (
    GLITCH_KEY, PROFILES as GLITCH_MAT4_CHAIN_PROFILES,
    REQUIRED_COMPANION_PROFILES as GLITCH_MAT4_CHAIN_COMPANIONS,
    authenticate_glitch_mat4_chain)
GLITCH_MAT4_CHAIN_KEYS = frozenset(GLITCH_MAT4_CHAIN_PROFILES)
from .frontend.emboss_color_style_profile import (
    EMBOSS_KEY, authenticate_emboss_color_style)
from .frontend.shape_mixer_builtin_profile import (
    SHAPE_MIXER_KEY, authenticate_shape_mixer_builtin_closure)
from .frontend.focus_blur_borrowed_sampler_profile import (
    FOCUS_BLUR_KEY, PROFILE as FOCUS_BLUR_BORROWED_SAMPLER_PROFILE,
    authenticate_focus_blur_borrowed_sampler_parameters)
from .frontend.derivative_admission_profile import (
    DERIVATIVE_ADMISSION_KEYS, authenticate_derivative_admission)
from .frontend.ceil_admission_profile import (
    CEIL_ADMISSION_KEYS, authenticate_ceil_admission)
from .frontend.as_u32_round_profile import (
    AS_U32_ROUND_KEYS, authenticate_as_u32_round_admission)
from .frontend.posterize_round_profile import (
    POSTERIZE_KEY, PROFILE as POSTERIZE_ROUND_PROFILE,
    authenticate_posterize_round_admission)
from .frontend.waves_any_notequal_profile import (
    WAVES_KEY, PROFILE as WAVES_ANY_NOTEQUAL_PROFILE,
    authenticate_waves_any_notequal_admission)
from .frontend.inout_vec3_swap_profile import (
    WATERCOLOR_KEY as INOUT_VEC3_SWAP_KEY,
    PROFILE as INOUT_VEC3_SWAP_PROFILE,
    authenticate_inout_vec3_swap_admission)
from .frontend.out_inout_admission_profile import (
    LIGHTLEAK_KEY as OUT_INOUT_ADMISSION_LIGHTLEAK_KEY,
    LIGHTLEAK_PROFILE as OUT_INOUT_ADMISSION_LIGHTLEAK_PROFILE,
    MANDELBROT_KEY as OUT_INOUT_ADMISSION_MANDELBROT_KEY,
    MANDELBROT_PROFILE as OUT_INOUT_ADMISSION_MANDELBROT_PROFILE,
    NEWTON_KEY as OUT_INOUT_ADMISSION_NEWTON_KEY,
    NEWTON_PROFILE as OUT_INOUT_ADMISSION_NEWTON_PROFILE,
    OUT_INOUT_ADMISSION_KEYS,
    authenticate_out_inout_admission, direction_contract as out_inout_direction_contract)
from .frontend.log_admission_profile import (
    MANDELBROT_KEY as LOG_ADMISSION_MANDELBROT_KEY,
    MANDELBROT_PROFILE as LOG_ADMISSION_MANDELBROT_PROFILE,
    LOG_ADMISSION_KEYS,
    authenticate_log_admission)
from .frontend.mandelbrot_sequential_dz_assignment_profile import (
    KEY as MANDELBROT_DZ_KEY,
    PROFILE as MANDELBROT_DZ_PROFILE,
    authenticate_mandelbrot_sequential_dz_assignment)
from .frontend.struct_declaration_profile import (
    JULIA_KEY as STRUCT_DECLARATION_JULIA_KEY,
    JULIA_SOURCE_PATH as STRUCT_DECLARATION_JULIA_SOURCE_PATH,
    NEWTON_KEY as STRUCT_DECLARATION_NEWTON_KEY,
    NEWTON_PROFILE as STRUCT_DECLARATION_NEWTON_PROFILE,
    STRUCT_DECLARATION_KEYS,
    authenticate_struct_declaration,
    materialization_contract as struct_materialization_contract)
from .frontend.julia_frontend_profile import (
    KEY as JULIA_FRONTEND_KEY,
    PROFILE as JULIA_FRONTEND_PROFILE,
    authenticate_julia_frontend)
from .frontend.out_inout_admission_profile import (
    JULIA_KEY as OUT_INOUT_ADMISSION_JULIA_KEY,
    JULIA_PROFILE as OUT_INOUT_ADMISSION_JULIA_PROFILE,
    _JULIA_CALL_ARGUMENTS as JULIA_OUT_CALL_ARGUMENTS)
from .frontend.runtime_loop_bound_profile import (
    PROFILE as RUNTIME_LOOP_BOUND_PROFILE,
    PREPARED_RUNTIME_LOOP_BOUND_KEYS,
    RUNTIME_LOOP_BOUND_KEYS,
    RuntimeLoopBoundContract,
    authenticate_runtime_loop_bound, validate_runtime_loop_contract)
from .frontend.gabor_effective_depth_profile import (
    GABOR_KEY, PROFILE as GABOR_EFFECTIVE_DEPTH_PROFILE,
    GaborEffectiveDepthContract,
    authenticate_gabor_effective_depth,
    validate_gabor_effective_depth_contract)
from .frontend.testpattern_profile import (
    KEY as TESTPATTERN_KEY,
    PROFILE as TESTPATTERN_PROFILE,
    FrontendProof,
    IndexRecord,
    authenticate_testpattern_frontend)
from .frontend.osd_frontend_profile import (
    KEY as OSD_KEY,
    PROFILE as OSD_FRONTEND_PROFILE,
    PREPARED_KEYS as OSD_PREPARED_KEYS,
    PREPARED_PROFILES as OSD_PREPARED_PROFILES,
    FrontendProof as OsdFrontendProof,
    authenticate_osd_frontend)
from .frontend.moodscape_frontend_profile import (
    KEY as MOODSCAPE_KEY,
    PROFILE as MOODSCAPE_FRONTEND_PROFILE,
    PREPARED_KEYS as MOODSCAPE_PREPARED_KEYS,
    PREPARED_PROFILES as MOODSCAPE_PREPARED_PROFILES,
    authenticate_moodscape_projection)
from .frontend.noise_frontend_profile import (
    KEY as NOISE_FRONTEND_KEY,
    PROFILE as NOISE_FRONTEND_PROFILE,
    authenticate_noise_projection, authenticate_noise_runtime)
from .frontend.spooky_ticker_frontend_profile import (
    KEY as SPOOKY_TICKER_KEY,
    PROFILE as SPOOKY_TICKER_FRONTEND_PROFILE,
    PREPARED_KEYS as SPOOKY_TICKER_PREPARED_KEYS,
    PREPARED_PROFILES as SPOOKY_TICKER_PREPARED_PROFILES,
    authenticate_spooky_ticker_frontend)
from .frontend.remap_profile import (
    KEY as REMAP_KEY,
    PROFILE as REMAP_PROFILE,
    FrontendProof as RemapFrontendProof,
    authenticate_remap_frontend)
from .frontend.historic_palette_profile import (
    KEY as HISTORIC_PALETTE_KEY,
    PROFILE as HISTORIC_PALETTE_PROFILE,
    TABLE_NATIVE_TYPE as HISTORIC_PALETTE_TABLE_NATIVE_TYPE,
    LUMINANCE_HELPER_NAME as HISTORIC_PALETTE_LUMINANCE_HELPER_NAME,
    FRACT_HELPER_NAME as HISTORIC_PALETTE_FRACT_HELPER_NAME,
    SMOOTHSTEP_HELPER_NAME as HISTORIC_PALETTE_SMOOTHSTEP_HELPER_NAME,
    MIX_STORE_HELPER_NAME as HISTORIC_PALETTE_MIX_STORE_HELPER_NAME,
    authenticate_historic_palette)
from .frontend.palette_frontend_profile import (
    KEY as PALETTE_KEY,
    PROFILE as PALETTE_FRONTEND_PROFILE,
    TABLE_NATIVE_TYPE as PALETTE_TABLE_NATIVE_TYPE,
    COSINE_NATIVE_TYPE as PALETTE_COSINE_NATIVE_TYPE,
    TAU_NAME as PALETTE_TAU_NAME,
    COSINE_HELPER_NAME as PALETTE_COSINE_HELPER_NAME,
    CLAMP_HELPER_NAME as PALETTE_CLAMP_HELPER_NAME,
    LUMINANCE_HELPER_NAME as PALETTE_LUMINANCE_HELPER_NAME,
    LINEAR_TO_SRGB_HELPER_NAME as PALETTE_LINEAR_TO_SRGB_HELPER_NAME,
    authenticate_palette_frontend)
from .frontend.color_lab_frontend_profile import (
    KEY as COLOR_LAB_KEY,
    PROFILE as COLOR_LAB_FRONTEND_PROFILE,
    authenticate_color_lab_frontend)
from .frontend.fractal_frontend_profile import (
    KEY as FRACTAL_KEY,
    PROFILE as FRACTAL_FRONTEND_PROFILE,
    PREPARED_KEYS as FRACTAL_PREPARED_KEYS,
    PREPARED_PROFILES as FRACTAL_PREPARED_PROFILES,
    JULIA_NUMBER_ANCHOR_SPANS,
    MANDELBROT_NUMBER_ANCHOR_SPANS,
    apply_fractal_frontend,
    authenticate_fractal_frontend,
    authenticate_fractal_runtime_contract)
from .frontend.median_frontend_profile import (
    KEY as MEDIAN_KEY,
    PROFILE as MEDIAN_FRONTEND_PROFILE,
    authenticate_median_frontend)
from .frontend.dither_frontend_profile import (
    KEY as DITHER_KEY,
    PROFILE as DITHER_FRONTEND_PROFILE,
    authenticate_dither_frontend as _authenticate_dither_frontend,
    validate_dither_proof_ledgers)
from .frontend import dither_frontend_profile as _DITHER_FRONTEND


_DITHER_AUTHENTICATED_CARRIERS: dict[int, object] = {}


def authenticate_dither_frontend(program: TypedProgram, source_hash: str | None,
                                 profile: str | None):
    """Issue and retain the exact authenticated proof carrier identity."""
    proof = _authenticate_dither_frontend(program, source_hash, profile)
    _DITHER_AUTHENTICATED_CARRIERS[id(proof)] = proof
    return proof


class TypedEmissionError(ValueError):
    """A fail-closed emission diagnostic with immutable typed-IR location."""


def _error(program: TypedProgram | str, value: object, message: str) -> TypedEmissionError:
    key = program.key if isinstance(program, TypedProgram) else program
    span = getattr(value, "span", None)
    line = getattr(span, "start_line", 1)
    column = getattr(span, "start_column", 1)
    return TypedEmissionError(f"{key}:{line}:{column}: {message}")


def _same_object_sequence(actual, expected) -> bool:
    """Return true only when two sequences contain the identical objects."""
    return (len(actual) == len(expected)
            and all(left is right for left, right in zip(actual, expected)))


# Exact source-to-adapter consumers for the standalone Julia body.  The public
# copy is intentionally patchable by focused mutation tests; production
# emission accepts it only when it remains byte-for-byte equal to this private
# canonical plan.  Every entry begins with its authenticated source ordinal.
_JULIA_BODY_CONSUMER_PLAN = {
    "functions": (
        (0, "[[nodiscard]] glsl::Vec2 cmul("),
        (1, "[[nodiscard]] glsl::Vec2 df64_add("),
        (2, "[[nodiscard]] glsl::Vec2 df64_from("),
        (3, "[[nodiscard]] glsl::Vec2 df64_mul("),
        (4, "[[nodiscard]] glsl::Vec2 df64_mul_f("),
        (5, "void df64_split("),
        (6, "[[nodiscard]] glsl::Vec2 df64_sub("),
        (7, "[[nodiscard]] JuliaNumberVec2 getAnimatedC("),
        (8, "void getPOI("),
        (9, "[[nodiscard]] double iterateSmooth("),
        (10, "[[nodiscard]] JuliaResultNative juliaIterate("),
        (11, "void main("),
        (12, "[[nodiscard]] double outputDistanceEstimation("),
        (13, "[[nodiscard]] double outputNormalMap("),
        (14, "[[nodiscard]] double outputOrbitTrap("),
        (15, "[[nodiscard]] double outputSmoothIteration("),
        (16, "[[nodiscard]] double outputStripeAverage("),
        (17, "[[nodiscard]] JuliaNumberVec2 resolveC("),
        (18, "void transformCoords("),
    ),
    "members": (
        (0, 10, "result.iter", 0),
        (1, 10, "result.zMag2", 0),
        (2, 10, "result.dzMag2", 0),
        (3, 10, "result.stripeSum", 0),
        (4, 10, "result.stripeCount", 0),
        (5, 10, "result.stripeLast", 0),
        (6, 10, "result.trapMin", 0),
        (7, 12, "r.iter", 0),
        (8, 12, "r.zMag2", 0),
        (9, 12, "r.dzMag2", 0),
        (10, 14, "r.iter", 0),
        (11, 14, "r.trapMin", 0),
        (12, 15, "r.iter", 0),
        (13, 15, "r.zMag2", 0),
        (14, 15, "r.iter", 1),
        (15, 16, "r.iter", 0),
        (16, 16, "r.stripeCount", 0),
        (17, 16, "r.stripeSum", 0),
        (18, 16, "r.stripeCount", 1),
        (19, 16, "r.stripeCount", 2),
        (20, 16, "r.stripeSum", 1),
        (21, 16, "r.stripeLast", 0),
        (22, 16, "r.stripeCount", 3),
        (23, 16, "r.zMag2", 0),
    ),
    "out_parameters": (
        (0, 5, "float& hi"),
        (1, 5, "float& lo"),
        (2, 18, "glsl::Vec2& reDF"),
        (3, 18, "glsl::Vec2& imDF"),
    ),
    "out_calls": (
        (0, 3, "df64_split(", 0,
         ("a[0]", "ahi", "alo"), ((0,), (1,), (2,))),
        (1, 3, "df64_split(", 1,
         ("b[0]", "bhi", "blo"), ((0,), (1,), (2,))),
        (2, 4, "df64_split(", 0,
         ("a[0]", "ahi", "alo"), ((0,), (1,), (2,))),
        (3, 4, "df64_split(", 1,
         ("b", "bhi", "blo"), ((0,), (1,), (2,))),
        (4, 9, "transformCoords(", 0,
         ("state", "fragX", "fragY", "zoom", "reDF", "imDF"),
         ((0, 1, 2), (3,), (4,), (5,))),
        (5, 11, "transformCoords(", 0,
         ("state", "globalX", "globalY", "zoom", "reDF", "imDF"),
         ((0, 1, 2), (3,), (4,), (5,))),
    ),
    "loops": (
        (0, 9, "const JuliaResultNative r = juliaIterate("),
        (1, 10, "for (std::int32_t index = 0; index < "
                 "std::min(maxIterations, 1000); ++index)"),
    ),
    "bindings": (
        (0, 'bindings.get<glsl::Vec2>("resolution")'),
        (1, 'bindings.get<glsl::Vec2>("tileOffset")'),
        (2, 'bindings.get<glsl::Vec2>("fullResolution")'),
        (3, 'bindings.get_number("time")'),
        (4, 'bindings.get_number("cReal")'),
        (5, 'bindings.get_number("cImag")'),
        (6, 'bindings.get<std::int32_t>("poi")'),
        (7, 'bindings.get<std::int32_t>("outputMode")'),
        (8, 'bindings.get_number("centerX")'),
        (9, 'bindings.get_number("centerY")'),
        (10, 'bindings.get_number("rotation")'),
        (11, 'bindings.get<std::int32_t>("iterations")'),
        (12, 'bindings.get_number("stripeFreq")'),
        (13, 'bindings.get<std::int32_t>("trapShape")'),
        (14, 'bindings.get_number("lightAngle")'),
        (15, 'bindings.get<std::int32_t>("cPath")'),
        (16, 'bindings.get_number("cSpeed")'),
        (17, 'bindings.get_number("cRadius")'),
        (18, 'bindings.get<bool>("invert")'),
        (19, 'bindings.get_number("zoomSpeed")'),
        (20, 'bindings.get_number("zoomDepth")'),
    ),
}
JULIA_BODY_CONSUMER_PLAN = dict(_JULIA_BODY_CONSUMER_PLAN)

_JULIA_FUNCTION_BODY_ORDER = (
    0, 2, 1, 6, 5, 3, 4, 7, 8, 17, 18, 10, 15, 12, 16, 14, 9, 13, 11)
_JULIA_MEMBER_BODY_ORDER = (
    0, 1, 2, 3, 4, 5, 6, 12, 13, 14, 7, 8, 9,
    15, 16, 17, 18, 19, 20, 21, 22, 23, 10, 11)


def _testpattern_proof_matches(actual: object,
                               expected: FrontendProof) -> bool:
    """Check a caller-supplied Test Pattern proof without trusting its values.

    ``FrontendProof`` is a NamedTuple, so a caller can manufacture one with
    copied metadata while retaining the right type.  The authenticated
    frontend proof is therefore the reference for every scalar field, while
    all typed-IR nodes are checked by object identity.  The emitter then keeps
    the caller's live proof as its authority; this check is only the bridge.
    """
    if type(actual) is not FrontendProof:
        return False
    proof = actual
    if (type(proof.dynamic_indexes) is not tuple
            or any(type(item) is not IndexRecord
                   for item in proof.dynamic_indexes)
            or type(proof.digit_store_index) is not IndexRecord
            or type(proof.consumed_objects) is not tuple):
        return False
    if (proof.program_key != expected.program_key
            or proof.global_array != expected.global_array
            or proof.local_arrays != expected.local_arrays
            or proof.round_span != expected.round_span
            or proof.loop_bounds != expected.loop_bounds
            or proof.num_digits_range != expected.num_digits_range
            or proof.dynamic_loop_owner != expected.dynamic_loop_owner
            or proof.dynamic_loop_bound_symbol_id
            != expected.dynamic_loop_bound_symbol_id
            or proof.dynamic_loop_bound_range != expected.dynamic_loop_bound_range
            or proof.binding_preflight is not expected.binding_preflight):
        return False
    if (len(proof.dynamic_indexes) != len(expected.dynamic_indexes)
            or any((left[:-1] != right[:-1] or left.node is not right.node)
                   for left, right in zip(proof.dynamic_indexes,
                                          expected.dynamic_indexes))):
        return False
    left = proof.digit_store_index
    right = expected.digit_store_index
    if left[:-1] != right[:-1] or left.node is not right.node:
        return False
    if proof.round_node is not expected.round_node:
        return False
    return _same_object_sequence(proof.consumed_objects,
                                 expected.consumed_objects)


def _remap_proof_matches(actual: object, expected: RemapFrontendProof) -> bool:
    """Bridge a caller proof to the emitter's independently-authenticated tree."""
    if type(actual) is not RemapFrontendProof:
        return False
    proof = actual
    if (proof.program_key != expected.program_key
            or proof.uniform_block is not expected.uniform_block
            or proof.data_field is not expected.data_field
            or proof.binding_preflight is not expected.binding_preflight
            or proof.source_constants != expected.source_constants
            or type(proof.indexes) is not tuple
            or type(proof.loops) is not tuple
            or type(proof.consumed_objects) is not tuple
            or len(proof.indexes) != len(expected.indexes)
            or len(proof.loops) != len(expected.loops)):
        return False
    if any((type(left) is not type(right)
            or left.function_id != right.function_id
            or left.function_name != right.function_name
            or left.span != right.span
            or left.node_sha256 != right.node_sha256
            or left.base_symbol_id != right.base_symbol_id
            or left.index_shape != right.index_shape
            or left.index_operator != right.index_operator
            or left.index_literal != right.index_literal
            or left.parent_kind != right.parent_kind
            or left.child_types != right.child_types
            or left.node is not right.node)
           for left, right in zip(proof.indexes, expected.indexes)):
        return False
    if any((left.function_id != right.function_id
            or left.function_name != right.function_name
            or left.span != right.span
            or left.induction_symbol_id != right.induction_symbol_id
            or left.start != right.start
            or left.bound != right.bound
            or left.comparison != right.comparison
            or left.update != right.update
            or left.trip_count != right.trip_count
            or left.effective_depth != right.effective_depth
            or left.proof is not right.proof)
           for left, right in zip(proof.loops, expected.loops)):
        return False
    return _same_object_sequence(proof.consumed_objects,
                                 expected.consumed_objects)


def _program_owned_object_ids(program: TypedProgram) -> set[int]:
    """Collect identities reachable from the candidate typed-program tree."""
    owned: set[int] = set()

    def expression(value: TypedExpression) -> None:
        if id(value) in owned:
            return
        owned.add(id(value))
        for child in value.children:
            expression(child)

    def statement(value: TypedStatement) -> None:
        if id(value) in owned:
            return
        owned.add(id(value))
        for item in value.expressions:
            expression(item)
        for child in value.children:
            statement(child)

    for declaration in program.declarations:
        owned.add(id(declaration))
        if declaration.initializer is not None:
            expression(declaration.initializer)
    for function in program.functions:
        owned.add(id(function))
        for item in function.body:
            statement(item)
    return owned


def _candidate_shape_mixer_blend_mode_guards(
        program: TypedProgram) -> tuple[TypedExpression, ...]:
    """Reconstruct the two exact candidate-owned Shape Mixer ladders."""
    blend_functions = tuple(item for item in program.functions
                            if item.name == "blend")
    if tuple(item.id for item in blend_functions) != (99, 100):
        return ()
    guards: list[TypedExpression] = []
    for function, expected_return, mode_symbol_id in (
            (blend_functions[0], "float", 97),
            (blend_functions[1], "vec3", 93)):
        if (function.return_type.display() != expected_return
                or len(function.parameters) != 4
                or function.parameters[2].id != mode_symbol_id
                or function.parameters[2].name != "mode"
                or function.parameters[2].type.display() != "int"
                or len(function.body) != 4):
            return ()
        mode_symbol = function.parameters[2]
        current = function.body[2]
        for expected_mode in range(10):
            if (current.kind != "if" or len(current.expressions) != 1
                    or len(current.children) != 2):
                return ()
            guard = current.expressions[0]
            if (guard.kind != "binary" or guard.operator != "=="
                    or guard.type.display() != "bool"
                    or len(guard.children) != 2
                    or guard.children[0].kind != "id"
                    or guard.children[0].symbol is not mode_symbol
                    or guard.children[0].type.display() != "int"
                    or guard.children[1].kind != "literal"
                    or guard.children[1].type.display() != "int"
                    or guard.children[1].literal_value != expected_mode
                    or isinstance(guard.children[1].literal_value, bool)):
                return ()
            guards.append(guard)
            current = current.children[1]
        if current.kind != "block":
            return ()
    return tuple(guards)


def _shape_mixer_ladder_records(program: TypedProgram) -> tuple[
        tuple[TypedStatement, tuple[TypedExpression, ...],
              tuple[TypedStatement, ...]], ...]:
    """Return candidate roots, source guards, and eleven bodies per overload."""
    guards = _candidate_shape_mixer_blend_mode_guards(program)
    if len(guards) != 20:
        return ()
    functions = {item.id: item for item in program.functions}
    if 99 not in functions or 100 not in functions:
        return ()
    records = []
    for function, offset in ((functions[99], 0), (functions[100], 10)):
        root = function.body[2]
        current = root
        bodies: list[TypedStatement] = []
        owner_guards = guards[offset:offset + 10]
        for guard in owner_guards:
            if (current.kind != "if" or current.expressions != (guard,)
                    or len(current.children) != 2):
                return ()
            bodies.append(current.children[0])
            current = current.children[1]
        bodies.append(current)
        if current.kind != "block" or len({id(item) for item in bodies}) != 11:
            return ()
        records.append((root, owner_guards, tuple(bodies)))
    return tuple(records)


def _candidate_shape_mixer_roots_and_bodies(
        program: TypedProgram) -> tuple[
            tuple[TypedStatement, ...], tuple[TypedStatement, ...]]:
    """Independently derive the consumer's exact root/body ledgers."""
    roots: list[TypedStatement] = []
    bodies: list[TypedStatement] = []
    for function_id in (99, 100):
        matches = tuple(item for item in program.functions
                        if item.id == function_id and item.name == "blend")
        if len(matches) != 1 or len(matches[0].body) != 4:
            return (), ()
        current = matches[0].body[2]
        roots.append(current)
        owner_bodies: list[TypedStatement] = []
        for _ in range(10):
            if current.kind != "if" or len(current.children) != 2:
                return (), ()
            owner_bodies.append(current.children[0])
            current = current.children[1]
        owner_bodies.append(current)
        if (current.kind != "block"
                or len({id(item) for item in owner_bodies}) != 11):
            return (), ()
        bodies.extend(owner_bodies)
    return tuple(roots), tuple(bodies)


def _shape_mixer_proof_matches_candidate(program, proof, companions) -> bool:
    """Independently bind every Shape Mixer proof role to the candidate tree."""
    try:
        exceptional = tuple(proof.exceptional_nodes)
        reflect_nodes = tuple(proof.reflect_nodes)
        refract_nodes = tuple(proof.refract_nodes)
        dynamic_indexes = tuple(proof.dynamic_indexes)
        parents = tuple(proof.exceptional_parents)
        blend_mode_guards = tuple(proof.blend_mode_guards)
        expected = (
            reflect_nodes[0], refract_nodes[0], proof.wide_mod_node,
            reflect_nodes[1], refract_nodes[1], *dynamic_indexes,
            proof.bit_ingress,
        )
    except (AttributeError, IndexError, TypeError):
        return False
    if (proof._candidate is not program
            or len(reflect_nodes) != 2 or len(refract_nodes) != 2
            or len(dynamic_indexes) != 5 or len(exceptional) != 11
            or len(parents) != 11
            or len(blend_mode_guards) != 20
            or len({id(item) for item in blend_mode_guards}) != 20
            or not _same_object_sequence(
                blend_mode_guards,
                _candidate_shape_mixer_blend_mode_guards(program))
            or len({id(item) for item in exceptional}) != 11
            or not _same_object_sequence(exceptional, expected)
            or not _same_object_sequence(
                proof.companion_scalar_uint_xors, companions)):
        return False

    records: list[tuple[TypedExpression, TypedExpression | None,
                        tuple[TypedStatement, ...]]] = []
    statements: set[int] = set()

    def expression(value: TypedExpression, parent: TypedExpression | None,
                   ancestors: tuple[TypedStatement, ...]) -> None:
        records.append((value, parent, ancestors))
        for child in value.children:
            expression(child, value, ancestors)

    def statement(value: TypedStatement,
                  ancestors: tuple[TypedStatement, ...]) -> None:
        statements.add(id(value))
        chain = (*ancestors, value)
        for item in value.expressions:
            expression(item, None, chain)
        for child in value.children:
            statement(child, chain)

    for declaration in program.declarations:
        if declaration.initializer is not None:
            expression(declaration.initializer, None, ())
    for function in program.functions:
        for item in function.body:
            statement(item, ())

    owned = _program_owned_object_ids(program)
    if (any(id(item) not in owned
            for item in (*blend_mode_guards, *exceptional, *parents))
            or id(proof.linear_srgb_loop) not in statements):
        return False
    for node, expected_parent in zip(exceptional, parents):
        matches = [(parent, chain) for item, parent, chain in records
                   if item is node]
        if len(matches) != 1 or matches[0][0] is not expected_parent:
            return False
    for node in dynamic_indexes:
        matches = [chain for item, _, chain in records if item is node]
        if (len(matches) != 1 or not matches[0]
                or matches[0][0] is not proof.linear_srgb_loop):
            return False
    return (proof.linear_srgb_loop.kind == "for"
            and proof.linear_srgb_loop.loop_proof is not None)


_TYPES = {
    "void": "void", "float": "float", "int": "std::int32_t", "uint": "std::uint32_t",
    "bool": "bool", "vec2": "glsl::Vec2", "vec3": "glsl::Vec3", "vec4": "glsl::Vec4",
    "ivec2": "glsl::IVec2", "ivec3": "glsl::IVec3", "ivec4": "glsl::IVec4",
    "uvec2": "glsl::UVec2", "uvec3": "glsl::UVec3", "uvec4": "glsl::UVec4",
    "mat2": "glsl::Mat2", "mat3": "glsl::Mat3",
}
# Identifiers the emitter itself binds inside every generated pixel function
# and helper signature. A GLSL local or parameter with one of these names would
# shadow them and either change meaning silently or fail to compile — e.g. a
# local `state` shadowing `const State& state` makes helper calls pass the
# wrong type. Ten corpus programs declare a local named `state`.
#
# `frame` is bound in the pixel body and every helper signature of a
# mutable-global-frame carrier. No `.glsl` in the pinned corpus declares an
# identifier named `frame` (the seven files containing the word have it only
# inside comments, which normalization strips), so adding it here is a no-op
# today — and the historical reconstruction is what proves that, not the
# census. If a future corpus refresh introduces one, the reconstruction is what
# will catch it.
_EMITTER_RESERVED_IDENTIFIERS = frozenset({
    "state", "context", "output", "kernel_base", "frame",
})

# C++20 keywords, including the alternative operator spellings which are
# ordinary identifiers in GLSL. Keep this complete rather than special-casing
# the first corpus collision (`and`, `or`, and `xor` in Bit Effects), so the
# same failure class cannot silently reappear in a parameter, local, or helper
# introduced by a future pinned corpus refresh.
_CPP_RESERVED_IDENTIFIERS = frozenset({
    "alignas", "alignof", "and", "and_eq", "asm", "atomic_cancel",
    "atomic_commit", "atomic_noexcept", "auto", "bitand", "bitor", "bool",
    "break", "case", "catch", "char", "char8_t", "char16_t", "char32_t",
    "class", "compl", "concept", "const", "consteval", "constexpr",
    "constinit", "const_cast", "continue", "co_await", "co_return",
    "co_yield", "decltype", "default", "delete", "do", "double",
    "dynamic_cast", "else", "enum", "explicit", "export", "extern", "false",
    "float", "for", "friend", "goto", "if", "inline", "int", "long",
    "mutable", "namespace", "new", "noexcept", "not", "not_eq", "nullptr",
    "operator", "or", "or_eq", "private", "protected", "public", "reflexpr",
    "register", "reinterpret_cast", "requires", "return", "short", "signed",
    "sizeof", "static", "static_assert", "static_cast", "struct", "switch",
    "synchronized", "template", "this", "thread_local", "throw", "true",
    "try", "typedef", "typeid", "typename", "union", "unsigned", "using",
    "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
})
_RESERVED_IDENTIFIERS = (
    _EMITTER_RESERVED_IDENTIFIERS | _CPP_RESERVED_IDENTIFIERS)


def _safe_identifier(name: str, symbol_id: object) -> str:
    """Mangle C++ keywords and names bound by the emitter itself."""
    if name in _RESERVED_IDENTIFIERS:
        return f"{name}_glsl_{symbol_id}"
    return name


def _newton_span(value: object) -> tuple[int, int, int, int]:
    span = value.span
    return (span.start_line, span.start_column, span.end_line, span.end_column)


def _newton_expression_nodes(program: TypedProgram):
    def expression(value: TypedExpression):
        yield value
        for child in value.children:
            yield from expression(child)

    def statement(value: TypedStatement):
        for item in value.expressions:
            yield from expression(item)
        for child in value.children:
            yield from statement(child)

    for declaration in program.declarations:
        if declaration.initializer is not None:
            yield from expression(declaration.initializer)
    for function in program.functions:
        for item in function.body:
            yield from statement(item)


def _authenticate_newton_lowering(program: TypedProgram):
    """Resolve the non-profiled Newton lowering sites by exact identity.

    Struct and out profiles authenticate the broad mechanism. These remaining
    sites are intentionally pinned to the prepared normalized source spans so
    an array, member, or log capability cannot become generic emitter
    vocabulary.
    """
    if program.key != STRUCT_DECLARATION_NEWTON_KEY:
        return None
    nodes = tuple(_newton_expression_nodes(program))
    roots = tuple(candidate for item in program.functions if item.name == "main"
                  for statement in item.body
                  for candidate in _newton_statement_nodes(statement)
                  if candidate.kind == "declaration"
                  and candidate.symbol is not None
                  and candidate.symbol.name == "roots")
    if len(roots) != 1:
        raise _error(program, program, "Newton roots declaration identity mismatch")
    root = roots[0]
    if (_newton_span(root) != (204, 10, 204, 18)
            or root.type.display() != "vec2[8]"
            or root.children
            or root.symbol.id != 108):
        raise _error(program, root, "Newton roots declaration contract mismatch")
    indexes = tuple(item for item in nodes if item.kind == "index"
                    and item.children
                    and item.children[0].kind == "id"
                    and item.children[0].symbol_id == root.symbol.id)
    expected_indexes = ((208, 9, 208, 17), (272, 29, 272, 37),
                        (273, 29, 273, 37))
    if (tuple(_newton_span(item) for item in indexes) != expected_indexes
            or any(len(item.children) != 2
                   or item.children[1].kind != "id"
                   or item.children[1].symbol_id not in {109, 139}
                   for item in indexes)):
        raise _error(program, root, "Newton roots index contract mismatch")
    logs = tuple(item for item in nodes if item.kind == "builtin"
                 and item.callee in {"log", "log2"})
    expected_logs = ((290, 29, 290, 69, "log2"),
                     (290, 34, 290, 51, "log"),
                     (290, 54, 290, 68, "log"))
    if (tuple((*_newton_span(item), item.callee) for item in logs)
            != expected_logs):
        raise _error(program, program, "Newton log builtin contract mismatch")
    return root, indexes, logs


def _newton_statement_nodes(value: TypedStatement):
    yield from value.expressions
    for child in value.children:
        yield from _newton_statement_nodes(child)


_BINARY_OPERATORS = frozenset({"!=", "%", "&", "&&", "*", "+", "-", "/", "<", "<=", "==", ">", ">=", ">>", "^", "|", "||"})
_ASSIGNMENT_OPERATORS = frozenset({"*=", "+=", "-=", "/=", "=", "^="})
_SWIZZLE = {"x": 0, "r": 0, "s": 0, "y": 1, "g": 1, "t": 1,
            "z": 2, "b": 2, "p": 2, "w": 3, "a": 3, "q": 3}
_BUILTIN_NAMES = {
    "abs": "abs", "atan": "atan", "clamp": "clamp", "cos": "cos",
    "distance": "distance", "dot": "dot", "exp": "exp", "floor": "floor",
    "fract": "fract", "length": "length", "max": "component_max", "min": "component_min",
    "mix": "mix", "mod": "mod", "normalize": "normalize", "pow": "pow", "radians": "radians",
    "sign": "sign", "sin": "sin", "smoothstep": "smoothstep", "sqrt": "sqrt", "step": "step",
}


@dataclass(slots=True)
class _Emitter:
    program: TypedProgram
    source_hash: str
    numeric_literal_contract: str = "glsl-f32"
    compatibility_transform: str | None = None
    custom_comparer_profile: str | None = None
    source_global_literal_int_profile: str | None = None
    runtime_loop_bound_profile: str | None = None
    gabor_effective_depth_profile: str | None = None
    gather_sorted_round_profile: str | None = None
    literal_vec3_lane_index_profile: str | None = None
    smooth_edge_luma_weights_profile: str | None = None
    perlin_scalar_uint_xor_profile: str | None = None
    scalar_uint_xor_profile: str | None = None
    bitwise_scalar_int_ops_profile: str | None = None
    bit_effects_frontend_profile: str | None = None
    rotate_mat2_return_profile: str | None = None
    focus_blur_borrowed_sampler_profile: str | None = None
    extrude_bvec2_relational_reduction_profile: str | None = None
    edge_bvec3_contour_profile: str | None = None
    glitch_mat4_chain_profile: str | None = None
    emboss_color_style_profile: str | None = None
    shape_mixer_builtin_profile: str | None = None
    caustic_word_hash_profile: str | None = None
    scanline_error_float_bits_ingress_profile: str | None = None
    glyph_map_nonnegative_int_shift_profile: str | None = None
    curl_vector_math_profile: str | None = None
    grade_luma_weights_profile: str | None = None
    grade_index_expression_profile: str | None = None
    derivative_admission_profile: str | None = None
    linear_srgb_lane_index_profile: str | None = None
    reflect_admission_profile: str | None = None
    posterize_round_profile: str | None = None
    as_u32_round_profile: str | None = None
    ceil_admission_profile: str | None = None
    waves_any_notequal_profile: str | None = None
    inout_vec3_swap_profile: str | None = None
    out_inout_admission_profile: str | None = None
    log_admission_profile: str | None = None
    mandelbrot_sequential_dz_assignment_profile: str | None = None
    struct_declaration_profile: str | None = None
    remap_profile: str | None = None
    remap_frontend_proof: RemapFrontendProof | None = None
    shapes_float_bits_ingress_profile: str | None = None
    grime_float_bits_ingress_profile: str | None = None
    shapes_rvalue_assign_profile: str | None = None
    mutable_global_frame_profile: str | None = None
    mutable_global_array_profile: str | None = None
    const_global_table_profile: str | None = None
    varying_profile: str | None = None
    texture_lod_admission_profile: str | None = None
    texture_frontend_profile: str | None = None
    cross_lane_assignment_profile: str | None = None
    uniforms: dict[int, object] = field(init=False)
    outputs: dict[int, object] = field(init=False)
    source_globals: dict[int, object] = field(init=False)
    source_global_dependencies: dict[int, tuple[int, ...]] = field(init=False)
    source_global_bounds: tuple[tuple[int, int, str, object], ...] = field(init=False)
    runtime_loop_contract: RuntimeLoopBoundContract | None = field(init=False)
    gabor_effective_depth_contract: GaborEffectiveDepthContract | None = field(
        init=False, default=None)
    runtime_guard_emitted: bool = field(init=False, default=False)
    runtime_radius_declaration_emitted: bool = field(init=False, default=False)
    function_names: dict[int, str] = field(init=False)
    ordinary_array_return_signatures: set[int] = field(init=False)
    mutated_symbol_ids: set[int] = field(init=False)
    program_scope_symbol_ids: set[int] = field(init=False)
    alias_declaration_symbol_ids: set[int] = field(init=False)
    alias_source_symbol_ids: set[int] = field(init=False)
    locals: dict[int, str] = field(init=False)
    current_function_name: str | None = field(init=False, default=None)
    current_function_signature_id: int | None = field(init=False, default=None)
    authorized_round_parent: TypedExpression | None = field(init=False, default=None)
    authorized_round: TypedExpression | None = field(init=False, default=None)
    authorized_literal_vec3_lane_sites: tuple[tuple[TypedExpression, int, str], ...] = field(
        init=False, default=())
    authorized_custom_comparer_predicate: TypedExpression | None = field(
        init=False, default=None)
    authorized_smooth_edge_luma_weights_declaration: object | None = field(
        init=False, default=None)
    authorized_perlin_scalar_uint_xors: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_perlin_scalar_uint_xors: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_scalar_uint_xors: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_scalar_uint_xors: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_scalar_uint_narrowing_skip_nodes: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_grain_narrowing_skip_nodes: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_bitwise_scalar_int_ops_sites: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_bitwise_scalar_int_ops_sites: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_bitwise_narrowing_skip_nodes: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_bitwise_narrowing_skip_nodes: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_bitwise_number_proof: object | None = field(init=False, default=None)
    emitted_bitwise_number_objects: list[object] = field(
        init=False, default_factory=list)
    emitted_bitwise_number_parameter_sites: list[object] = field(
        init=False, default_factory=list)
    authorized_bit_effects_proof: object | None = field(init=False, default=None)
    authorized_bit_effects_nodes: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_bit_effects_nodes: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_bit_effects_globals: list[object] = field(
        init=False, default_factory=list)
    emitted_bit_effects_overload_misdispatch: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_bit_effects_xi_to_int32: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_bitwise_float_identity_nodes: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_bitwise_float_identity_nodes: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_rotate_helper: object | None = field(init=False, default=None)
    authorized_rotate_expressions: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_rotate_helper_count: int = field(init=False, default=0)
    emitted_rotate_expressions: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_focus_blur_proof: object | None = field(init=False, default=None)
    authorized_extrude_proof: object | None = field(init=False, default=None)
    authorized_edge_proof: object | None = field(init=False, default=None)
    authorized_edge_splat_proof: object | None = field(init=False, default=None)
    authorized_glitch_proof: object | None = field(init=False, default=None)
    authorized_emboss_proof: object | None = field(init=False, default=None)
    authorized_shape_mixer_proof: object | None = field(init=False, default=None)
    candidate_shape_mixer_guards: tuple[TypedExpression, ...] = field(
        init=False, default=())
    candidate_shape_mixer_ladders: tuple = field(init=False, default=())
    emitted_shape_mixer_guards: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_shape_mixer_roots: list[TypedStatement] = field(
        init=False, default_factory=list)
    emitted_shape_mixer_bodies: list[TypedStatement] = field(
        init=False, default_factory=list)
    emitted_shape_mixer_exceptional: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_glitch_matrix_objects: list[object] = field(
        init=False, default_factory=list)
    emitted_emboss_declarations: list[object] = field(
        init=False, default_factory=list)
    emitted_emboss_stores: list[object] = field(
        init=False, default_factory=list)
    emitted_emboss_reads: list[object] = field(
        init=False, default_factory=list)
    emitted_emboss_equalities: list[object] = field(
        init=False, default_factory=list)
    emitted_emboss_reductions: list[object] = field(
        init=False, default_factory=list)
    emitted_emboss_materialization_divisions: list[object] = field(
        init=False, default_factory=list)
    authorized_caustic_proof: object | None = field(init=False, default=None)
    authorized_scanline_error_proof: object | None = field(
        init=False, default=None)
    authorized_glyph_map_proof: object | None = field(init=False, default=None)
    authorized_curl_proof: object | None = field(init=False, default=None)
    emitted_curl_nodes: list[object] = field(init=False, default_factory=list)
    authorized_derivative_proof: object | None = field(init=False, default=None)
    emitted_derivative_nodes: list[object] = field(init=False, default_factory=list)
    authorized_distortion_frontend_proof: object | None = field(
        init=False, default=None)
    emitted_distortion_sampler_parameters: list[object] = field(
        init=False, default_factory=list)
    emitted_distortion_sampler_calls: list[object] = field(
        init=False, default_factory=list)
    emitted_distortion_sampler_actuals: list[object] = field(
        init=False, default_factory=list)
    emitted_distortion_derivatives: list[object] = field(
        init=False, default_factory=list)
    emitted_distortion_reflects: list[object] = field(
        init=False, default_factory=list)
    emitted_caustic_nodes: list[object] = field(init=False, default_factory=list)
    emitted_scanline_error_ingresses: list[object] = field(
        init=False, default_factory=list)
    authorized_shapes_float_bits_ingresses: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_shapes_float_bits_ingresses: list[TypedExpression] = field(
        init=False, default_factory=list)
    # grime's five `floatBitsToUint` ingresses -- the whole closure behind its
    # varying carrier, re-derived here independently of the validator.
    authorized_grime_float_bits_ingresses: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_grime_float_bits_ingresses: list[TypedExpression] = field(
        init=False, default_factory=list)
    # kaleido's one `floatBitsToUint` ingress, authenticated by the scalar-XOR
    # module's per-key census (rides the same carrier; no separate row field).
    authorized_kaleido_float_bits_ingress: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_kaleido_float_bits_ingress: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_noise_float_bits_ingresses: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_noise_float_bits_ingresses: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_shapes_rvalue_assigns: tuple[TypedExpression, ...] = field(
        init=False, default=())
    authorized_cross_lane_assignment: object | None = field(init=False, default=None)
    emitted_cross_lane_assignments: list[object] = field(init=False, default_factory=list)
    emitted_shapes_rvalue_assigns: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_mutable_global_frames: tuple[object, ...] = field(
        init=False, default=())
    authorized_frame_contract: object | None = field(init=False, default=None)
    # `{symbol id: emitted lvalue}` for the admitted mutable globals. Empty for
    # every non-carrier program, so `name()` keeps raising `unmapped typed
    # symbol` everywhere else.
    frame_fields: dict[int, str] = field(init=False, default_factory=dict)
    admitted_mutable_global_frames: list[object] = field(
        init=False, default_factory=list)
    emitted_frame_struct_count: int = field(init=False, default=0)
    emitted_frame_instance_count: int = field(init=False, default=0)
    emitted_frame_references: list[TypedExpression] = field(
        init=False, default_factory=list)
    # The mutable-global ARRAY carrier's own state, deliberately separate
    # from the frame fields above: different program, different audit (the
    # writer's `Frame&` is the one deliberate non-const parameter in the
    # namespace, the frame's contract forbids one), so shared counters would
    # silently conflate two different emission contracts.
    authorized_mutable_global_arrays: tuple[object, ...] = field(
        init=False, default=())
    authorized_mutable_array_contract: object | None = field(
        init=False, default=None)
    # `{symbol id: emitted lvalue}` for the five admitted arrays (e.g.
    # `frame.emboss`). Empty for every non-carrier program, so `name()`
    # keeps raising `unmapped typed symbol` everywhere else.
    array_frame_fields: dict[int, str] = field(
        init=False, default_factory=dict)
    admitted_mutable_global_arrays: list[object] = field(
        init=False, default_factory=list)
    emitted_array_frame_struct_count: int = field(init=False, default=0)
    emitted_array_frame_instance_count: int = field(init=False, default=0)
    emitted_array_frame_references: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_array_frame_stores: list[TypedExpression] = field(
        init=False, default_factory=list)
    # The frozen bare `loadKernels();` call node, resolved ONCE from the
    # authenticated tree so the expr-statement arm can gate on object
    # identity exactly like the inout-vec3-swap arm (design Amendment 12).
    authorized_array_writer_call: TypedExpression | None = field(
        init=False, default=None)
    emitted_array_writer_calls: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_array_nonconst_frame_functions: list[object] = field(
        init=False, default_factory=list)
    # The two rvalue compound assignments (`return color *= dist;` in the
    # unreachable `derivatives`/`sobel`), resolved once at authentication and
    # admitted by node identity exactly like Shapes' authorized rvalue
    # assigns -- the same JS materialization (`var x = y *= k`), lowered the
    # same way.
    authorized_array_rvalue_assigns: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_array_rvalue_assigns: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_const_global_tables: tuple[object, ...] = field(
        init=False, default=())
    # The authenticated read SITES, carrying the live nodes. Admitted with
    # `value is item.node`, the same idiom as
    # `authorized_linear_srgb_lane_index_sites`.
    authorized_const_global_table_reads: tuple[object, ...] = field(
        init=False, default=())
    # The closure's own frozen emission contract, never re-derived here: the
    # native alias spellings are the closure's choice and two spellings of one
    # alias is a defect waiting for a rename.
    authorized_const_global_table_contract: tuple = field(
        init=False, default=())
    admitted_const_global_tables: list[object] = field(
        init=False, default_factory=list)
    emitted_const_global_table_alias_blocks: int = field(init=False, default=0)
    emitted_const_global_table_locals: list[object] = field(
        init=False, default_factory=list)
    emitted_const_global_table_constructors: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_const_global_table_reads: list[TypedExpression] = field(
        init=False, default_factory=list)
    # The varying-uv carrier's own state: the authenticated interface symbols
    # and the frozen emission contract whose lowering target every read of
    # the admitted symbol must lower to (`context.uv` -- pure expression
    # lowering, no Frame/State field, no kernel-signature change).
    authorized_varyings: tuple[object, ...] = field(
        init=False, default=())
    authorized_varying_contract: object | None = field(init=False, default=None)
    # `{symbol id: emitted lvalue}` for the admitted varying -- exactly
    # `context.uv`. Empty for every non-carrier program, so `name()` keeps
    # raising `unmapped typed symbol` everywhere else.
    varying_fields: dict[int, str] = field(init=False, default_factory=dict)
    emitted_varying_references: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_glyph_map_sites: list[object] = field(
        init=False, default_factory=list)
    emitted_glyph_map_noops: list[object] = field(
        init=False, default_factory=list)
    emitted_extrude_nodes: list[object] = field(init=False, default_factory=list)
    emitted_edge_bvec_nodes: list[object] = field(
        init=False, default_factory=list)
    emitted_edge_relationals: list[object] = field(
        init=False, default_factory=list)
    emitted_edge_declarations: list[object] = field(
        init=False, default_factory=list)
    emitted_edge_constructors: list[object] = field(
        init=False, default_factory=list)
    emitted_edge_swizzles: list[object] = field(
        init=False, default_factory=list)
    emitted_edge_splat_assignments: list[object] = field(
        init=False, default_factory=list)
    emitted_focus_blur_parameter_sites: list[object] = field(
        init=False, default_factory=list)
    emitted_focus_blur_uses: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_focus_blur_calls: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_grade_luma_weights_declaration: object | None = field(
        init=False, default=None)
    authorized_grade_index_sites: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_grade_index_sites: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_linear_srgb_lane_index_sites: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_linear_srgb_lane_index_sites: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_fractal_frontend_indexes: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_fractal_frontend_indexes: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_fractal_mat2_constructor: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_mode_contract: object | None = field(
        init=False, default=None)
    authorized_fractal_terminal_fallbacks: tuple[str, ...] = field(
        init=False, default=())
    authorized_fractal_alpha_product: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_alpha_literal: TypedExpression | None = field(
        init=False, default=None)
    emitted_fractal_alpha_products: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_fractal_alpha_literals: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_fractal_hsv_function: object | None = field(
        init=False, default=None)
    authorized_fractal_hsv_parameter: object | None = field(
        init=False, default=None)
    authorized_fractal_hsv_calls: tuple[TypedExpression, ...] = field(
        init=False, default=())
    authorized_fractal_hue_scale_assignment: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_hue_scale_product: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_hue_scale_literal: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_distance_fract_assignment: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_distance_fract_builtin: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_distance_map_assignment: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_distance_map_sum: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_distance_repeat_product: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_distance_rotate_product: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_distance_rotate_literal: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_palette_function: object | None = field(
        init=False, default=None)
    authorized_fractal_palette_parameter: object | None = field(
        init=False, default=None)
    authorized_fractal_palette_call: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_newton_function: object | None = field(
        init=False, default=None)
    authorized_fractal_newton_parameter: object | None = field(
        init=False, default=None)
    authorized_fractal_newton_call: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_julia_function: object | None = field(
        init=False, default=None)
    authorized_fractal_julia_parameter: object | None = field(
        init=False, default=None)
    authorized_fractal_julia_call: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_julia_number_anchors: tuple[TypedStatement, ...] = field(
        init=False, default=())
    authorized_fractal_mandelbrot_function: object | None = field(
        init=False, default=None)
    authorized_fractal_mandelbrot_parameter: object | None = field(
        init=False, default=None)
    authorized_fractal_mandelbrot_call: TypedExpression | None = field(
        init=False, default=None)
    authorized_fractal_mandelbrot_number_anchors: tuple[TypedStatement, ...] = field(
        init=False, default=())
    emitted_fractal_hsv_calls: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_fractal_palette_calls: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_fractal_newton_calls: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_fractal_julia_calls: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_fractal_mandelbrot_calls: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_fractal_hue_scale_assignments: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_fractal_distance_fract_assignments: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_fractal_distance_map_assignments: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_fractal_hsv_declarations: int = field(init=False, default=0)
    emitted_fractal_hsv_definitions: int = field(init=False, default=0)
    emitted_fractal_palette_adapter_paths: int = field(init=False, default=0)
    emitted_fractal_newton_declarations: int = field(init=False, default=0)
    emitted_fractal_newton_definitions: int = field(init=False, default=0)
    emitted_fractal_newton_adapter_paths: int = field(init=False, default=0)
    emitted_fractal_julia_declarations: int = field(init=False, default=0)
    emitted_fractal_julia_definitions: int = field(init=False, default=0)
    emitted_fractal_julia_adapter_paths: int = field(init=False, default=0)
    emitted_fractal_mandelbrot_declarations: int = field(init=False, default=0)
    emitted_fractal_mandelbrot_definitions: int = field(init=False, default=0)
    emitted_fractal_mandelbrot_adapter_paths: int = field(init=False, default=0)
    emitted_fractal_mandelbrot_matrix_consumptions: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_fractal_julia_number_anchors: list[TypedStatement] = field(
        init=False, default_factory=list)
    emitted_fractal_mandelbrot_number_anchors: list[TypedStatement] = field(
        init=False, default_factory=list)
    authorized_reflect_node: TypedExpression | None = field(init=False, default=None)
    emitted_reflect_nodes: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_posterize_round: TypedExpression | None = field(init=False, default=None)
    authorized_as_u32_round: TypedExpression | None = field(init=False, default=None)
    authorized_ceil: tuple = field(init=False, default=())
    authorized_waves_relationals: tuple[TypedExpression, ...] = field(
        init=False, default=())
    authorized_waves_reductions: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_waves_nodes: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_inout_vec3_swap_proof: object = field(init=False, default=None)
    emitted_inout_vec3_swap_calls: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_out_inout_parameters: tuple[object, ...] = field(
        init=False, default=())
    authorized_out_inout_calls: tuple[object, ...] = field(
        init=False, default=())
    emitted_out_inout_parameters: list[object] = field(
        init=False, default_factory=list)
    emitted_out_inout_calls: list[TypedExpression] = field(
        init=False, default_factory=list)
    out_inout_direction_contract: object | None = field(
        init=False, default=None)
    authorized_out_inout_argument_abis: dict[int, str] = field(
        init=False, default_factory=dict)
    authorized_struct_declaration: tuple = field(init=False, default=())
    authorized_struct_materialization: object | None = field(
        init=False, default=None)
    authorized_newton_roots_declaration: object | None = field(
        init=False, default=None)
    authorized_newton_root_indexes: tuple[TypedExpression, ...] = field(
        init=False, default=())
    authorized_newton_logs: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_newton_root_indexes: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_newton_logs: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_mandelbrot_logs: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_mandelbrot_logs: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_mandelbrot_sequential_dz_assignment: object | None = field(
        init=False, default=None)
    emitted_mandelbrot_sequential_dz_assignment: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_newton_struct_constructors: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_newton_members: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_newton_struct_count: int = field(init=False, default=0)
    # The textureLod identity carrier's own state: the two authenticated call
    # sites (live nodes, `getHeight`/`getInput`) whose lowering is the frozen
    # alias contract -- `textureLod(s, uv, 0.0)` emits exactly what `texture`
    # emits (`sample_texture(s, uv)`), the JS runtime's pure alias.
    authorized_texture_lod_sites: tuple = field(init=False, default=())
    emitted_texture_lod_sites: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_texture_frontend_nodes: tuple[TypedExpression, ...] = field(
        init=False, default=())
    authorized_texture_frontend_assignments: tuple[TypedExpression, ...] = field(
        init=False, default=())
    authorized_texture_frontend_inverse_sqrt: TypedExpression | None = field(
        init=False, default=None)
    authorized_texture_frontend_hash_conversion: TypedExpression | None = field(
        init=False, default=None)
    emitted_texture_frontend_nodes: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_texture_frontend_assignments: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_texture_frontend_inverse_sqrt: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_texture_frontend_hash_conversion: list[TypedExpression] = field(
        init=False, default_factory=list)
    testpattern_profile: str | None = None
    testpattern_frontend_proof: FrontendProof | None = None
    osd_frontend_profile: str | None = None
    moodscape_frontend_profile: str | None = None
    noise_frontend_profile: str | None = None
    spooky_ticker_frontend_profile: str | None = None
    historic_palette_profile: str | None = None
    palette_frontend_profile: str | None = None
    color_lab_frontend_profile: str | None = None
    median_frontend_profile: str | None = None
    fractal_frontend_profile: str | None = None
    julia_frontend_profile: str | None = None
    distortion_frontend_profile: str | None = None
    authorized_testpattern_proof: object | None = field(init=False, default=None)
    authorized_osd_proof: object | None = field(init=False, default=None)
    authorized_moodscape_projection: object | None = field(
        init=False, default=None)
    emitted_osd_array: list[object] = field(init=False, default_factory=list)
    emitted_osd_indexes: list[TypedExpression] = field(init=False, default_factory=list)
    emitted_osd_bitwise: list[TypedExpression] = field(init=False, default_factory=list)
    emitted_osd_hash_modulos: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_osd_globals: list[object] = field(init=False, default_factory=list)
    authorized_spooky_ticker_proof: object | None = field(init=False, default=None)
    authorized_spooky_ticker_nodes: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_spooky_ticker_array: list[object] = field(init=False, default_factory=list)
    emitted_spooky_ticker_indexes: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_spooky_ticker_bitwise: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_spooky_ticker_globals: list[object] = field(
        init=False, default_factory=list)
    authorized_spooky_ticker_varying_reads: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_spooky_ticker_varying_reads: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_spooky_ticker_number_parameters: list[object] = field(
        init=False, default_factory=list)
    emitted_spooky_ticker_number_declarations: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_spooky_ticker_number_divisions: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_spooky_ticker_number_umuls: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_spooky_ticker_number_remainders: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_spooky_ticker_hash_declarations: int = field(
        init=False, default=0)
    emitted_spooky_ticker_hash_definitions: int = field(
        init=False, default=0)
    emitted_testpattern_arrays: list[object] = field(
        init=False, default_factory=list)
    emitted_testpattern_constructors: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_testpattern_indexes: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_testpattern_rounds: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_testpattern_glyph_shift: TypedExpression | None = field(
        init=False, default=None)
    authorized_testpattern_glyph_mask: TypedExpression | None = field(
        init=False, default=None)
    emitted_testpattern_bitwise: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_remap_proof: object | None = field(init=False, default=None)
    emitted_remap_indexes: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_remap_loops: list[TypedStatement] = field(
        init=False, default_factory=list)
    authorized_historic_palette_proof: object | None = field(init=False, default=None)
    authorized_palette_frontend_proof: object | None = field(init=False, default=None)
    authorized_color_lab_frontend_proof: object | None = field(
        init=False, default=None)
    authorized_median_frontend_proof: object | None = field(
        init=False, default=None)
    authorized_julia_frontend_proof: object | None = field(
        init=False, default=None)
    authorized_julia_struct_materialization: object | None = field(
        init=False, default=None)
    authorized_julia_out_direction_contract: object | None = field(
        init=False, default=None)
    authorized_julia_out_parameters: tuple[object, ...] = field(
        init=False, default=())
    authorized_julia_out_calls: tuple[object, ...] = field(
        init=False, default=())
    emitted_julia_functions: list[object] = field(
        init=False, default_factory=list)
    emitted_julia_result_members: list[object] = field(
        init=False, default_factory=list)
    emitted_julia_out_parameters: list[object] = field(
        init=False, default_factory=list)
    emitted_julia_out_calls: list[object] = field(
        init=False, default_factory=list)
    emitted_julia_out_arguments: list[object] = field(
        init=False, default_factory=list)
    emitted_julia_loops: list[object] = field(
        init=False, default_factory=list)
    emitted_julia_bindings: list[object] = field(
        init=False, default_factory=list)
    authorized_color_lab_indexes: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_color_lab_indexes: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_color_lab_vector_equalities: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_color_lab_vector_equalities: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_median_indexes: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_median_whiles: list[TypedStatement] = field(
        init=False, default_factory=list)
    emitted_historic_palette_members: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_palette_members: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_historic_palette_indexes: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_palette_indexes: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_historic_palette_structs: list[object] = field(
        init=False, default_factory=list)
    emitted_palette_structs: list[object] = field(
        init=False, default_factory=list)
    emitted_historic_palette_constructors: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_palette_constructors: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_historic_palette_number_vectors: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_palette_number_vectors: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_historic_palette_number_literals: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_palette_number_literals: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_palette_tau_sites: list[object] = field(
        init=False, default_factory=list)
    emitted_palette_cosine_sites: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_historic_palette_adapter_sites: list[object] = field(
        init=False, default_factory=list)
    emitted_palette_adapter_sites: list[TypedExpression] = field(
        init=False, default_factory=list)
    emitted_historic_palette_counts: list[object] = field(
        init=False, default_factory=list)
    emitted_palette_counts: list[object] = field(
        init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.authorized_round_parent = None
        self.authorized_round = None
        self.authorized_literal_vec3_lane_sites = ()
        self.authorized_custom_comparer_predicate = None
        self.authorized_smooth_edge_luma_weights_declaration = None
        self.authorized_perlin_scalar_uint_xors = ()
        self.emitted_perlin_scalar_uint_xors = []
        self.authorized_scalar_uint_xors = ()
        self.emitted_scalar_uint_xors = []
        self.authorized_scalar_uint_narrowing_skip_nodes = ()
        self.emitted_grain_narrowing_skip_nodes = []
        self.authorized_bitwise_scalar_int_ops_sites = ()
        self.emitted_bitwise_scalar_int_ops_sites = []
        self.authorized_bitwise_narrowing_skip_nodes = ()
        self.emitted_bitwise_narrowing_skip_nodes = []
        self.authorized_bitwise_number_proof = None
        self.emitted_bitwise_number_objects = []
        self.emitted_bitwise_number_parameter_sites = []
        self.authorized_bit_effects_proof = None
        self.authorized_bit_effects_nodes = ()
        self.emitted_bit_effects_nodes = []
        self.emitted_bit_effects_globals = []
        self.emitted_bit_effects_overload_misdispatch = []
        self.emitted_bit_effects_xi_to_int32 = []
        self.authorized_bitwise_float_identity_nodes = ()
        self.emitted_bitwise_float_identity_nodes = []
        self.authorized_rotate_helper = None
        self.authorized_rotate_expressions = ()
        self.emitted_rotate_helper_count = 0
        self.emitted_rotate_expressions = []
        self.authorized_focus_blur_proof = None
        self.authorized_extrude_proof = None
        self.authorized_edge_proof = None
        self.authorized_edge_splat_proof = None
        self.authorized_glitch_proof = None
        self.emitted_glitch_matrix_objects = []
        self.authorized_emboss_proof = None
        self.emitted_emboss_declarations = []
        self.emitted_emboss_stores = []
        self.emitted_emboss_reads = []
        self.emitted_emboss_equalities = []
        self.emitted_emboss_reductions = []
        self.emitted_emboss_materialization_divisions = []
        self.authorized_shape_mixer_proof = None
        self.candidate_shape_mixer_guards = ()
        self.candidate_shape_mixer_ladders = ()
        self.emitted_shape_mixer_guards = []
        self.emitted_shape_mixer_roots = []
        self.emitted_shape_mixer_bodies = []
        self.emitted_shape_mixer_exceptional = []
        self.authorized_caustic_proof = None
        self.authorized_scanline_error_proof = None
        self.authorized_glyph_map_proof = None
        self.authorized_curl_proof = None
        self.emitted_curl_nodes = []
        self.emitted_caustic_nodes = []
        self.emitted_scanline_error_ingresses = []
        self.authorized_shapes_float_bits_ingresses = ()
        self.emitted_shapes_float_bits_ingresses = []
        self.authorized_grime_float_bits_ingresses = ()
        self.emitted_grime_float_bits_ingresses = []
        self.authorized_kaleido_float_bits_ingress = ()
        self.emitted_kaleido_float_bits_ingress = []
        self.authorized_noise_float_bits_ingresses = ()
        self.emitted_noise_float_bits_ingresses = []
        self.authorized_shapes_rvalue_assigns = ()
        self.authorized_cross_lane_assignment = None
        self.emitted_cross_lane_assignments = []
        self.emitted_shapes_rvalue_assigns = []
        self.authorized_mutable_global_frames = ()
        self.authorized_frame_contract = None
        self.frame_fields = {}
        self.admitted_mutable_global_frames = []
        self.emitted_frame_struct_count = 0
        self.emitted_frame_instance_count = 0
        self.emitted_frame_references = []
        self.authorized_mutable_global_arrays = ()
        self.authorized_mutable_array_contract = None
        self.array_frame_fields = {}
        self.admitted_mutable_global_arrays = []
        self.emitted_array_frame_struct_count = 0
        self.emitted_array_frame_instance_count = 0
        self.emitted_array_frame_references = []
        self.emitted_array_frame_stores = []
        self.authorized_array_writer_call = None
        self.emitted_array_writer_calls = []
        self.emitted_array_nonconst_frame_functions = []
        self.authorized_array_rvalue_assigns = ()
        self.emitted_array_rvalue_assigns = []
        self.authorized_const_global_tables = ()
        self.authorized_const_global_table_reads = ()
        self.authorized_const_global_table_contract = ()
        self.admitted_const_global_tables = []
        self.emitted_const_global_table_alias_blocks = 0
        self.emitted_const_global_table_locals = []
        self.emitted_const_global_table_constructors = []
        self.emitted_const_global_table_reads = []
        self.authorized_varyings = ()
        self.authorized_varying_contract = None
        self.varying_fields = {}
        self.emitted_varying_references = []
        self.emitted_glyph_map_sites = []
        self.emitted_glyph_map_noops = []
        self.emitted_extrude_nodes = []
        self.emitted_edge_bvec_nodes = []
        self.emitted_edge_relationals = []
        self.emitted_edge_declarations = []
        self.emitted_edge_constructors = []
        self.emitted_edge_swizzles = []
        self.emitted_edge_splat_assignments = []
        self.emitted_focus_blur_parameter_sites = []
        self.emitted_focus_blur_uses = []
        self.emitted_focus_blur_calls = []
        self.authorized_grade_luma_weights_declaration = None
        self.authorized_grade_index_sites = ()
        self.emitted_grade_index_sites = []
        self.authorized_linear_srgb_lane_index_sites = ()
        self.emitted_linear_srgb_lane_index_sites = []
        self.authorized_fractal_frontend_indexes = ()
        self.emitted_fractal_frontend_indexes = []
        self.authorized_fractal_mat2_constructor = None
        self.authorized_fractal_mode_contract = None
        self.authorized_fractal_terminal_fallbacks = ()
        self.authorized_fractal_alpha_product = None
        self.authorized_fractal_alpha_literal = None
        self.emitted_fractal_alpha_products = []
        self.emitted_fractal_alpha_literals = []
        self.authorized_fractal_hsv_function = None
        self.authorized_fractal_hsv_parameter = None
        self.authorized_fractal_hsv_calls = ()
        self.authorized_fractal_hue_scale_assignment = None
        self.authorized_fractal_hue_scale_product = None
        self.authorized_fractal_hue_scale_literal = None
        self.authorized_fractal_distance_fract_assignment = None
        self.authorized_fractal_distance_fract_builtin = None
        self.authorized_fractal_distance_map_assignment = None
        self.authorized_fractal_distance_map_sum = None
        self.authorized_fractal_distance_repeat_product = None
        self.authorized_fractal_distance_rotate_product = None
        self.authorized_fractal_distance_rotate_literal = None
        self.authorized_fractal_palette_function = None
        self.authorized_fractal_palette_parameter = None
        self.authorized_fractal_palette_call = None
        self.authorized_fractal_newton_function = None
        self.authorized_fractal_newton_parameter = None
        self.authorized_fractal_newton_call = None
        self.authorized_fractal_julia_function = None
        self.authorized_fractal_julia_parameter = None
        self.authorized_fractal_julia_call = None
        self.authorized_fractal_mandelbrot_function = None
        self.authorized_fractal_mandelbrot_parameter = None
        self.authorized_fractal_mandelbrot_call = None
        self.emitted_fractal_hsv_calls = []
        self.emitted_fractal_palette_calls = []
        self.emitted_fractal_newton_calls = []
        self.emitted_fractal_julia_calls = []
        self.emitted_fractal_mandelbrot_calls = []
        self.emitted_fractal_hue_scale_assignments = []
        self.emitted_fractal_distance_fract_assignments = []
        self.emitted_fractal_distance_map_assignments = []
        self.emitted_fractal_hsv_declarations = 0
        self.emitted_fractal_hsv_definitions = 0
        self.emitted_fractal_palette_adapter_paths = 0
        self.emitted_fractal_newton_declarations = 0
        self.emitted_fractal_newton_definitions = 0
        self.emitted_fractal_newton_adapter_paths = 0
        self.emitted_fractal_julia_declarations = 0
        self.emitted_fractal_julia_definitions = 0
        self.emitted_fractal_julia_adapter_paths = 0
        self.emitted_fractal_mandelbrot_declarations = 0
        self.emitted_fractal_mandelbrot_definitions = 0
        self.emitted_fractal_mandelbrot_adapter_paths = 0
        self.emitted_fractal_mandelbrot_matrix_consumptions = []
        self.authorized_derivative_proof = None
        self.emitted_derivative_nodes = []
        self.authorized_reflect_node = None
        self.emitted_reflect_nodes = []
        self.authorized_posterize_round = None
        self.authorized_as_u32_round = None
        self.authorized_ceil = ()
        self.authorized_waves_relationals = ()
        self.authorized_waves_reductions = ()
        self.emitted_waves_nodes = []
        self.authorized_inout_vec3_swap_proof = None
        self.emitted_inout_vec3_swap_calls = []
        self.authorized_out_inout_parameters = ()
        self.authorized_out_inout_calls = ()
        self.emitted_out_inout_parameters = []
        self.emitted_out_inout_calls = []
        self.out_inout_direction_contract = None
        self.authorized_out_inout_argument_abis = {}
        self.authorized_struct_declaration = ()
        self.authorized_struct_materialization = None
        self.authorized_newton_roots_declaration = None
        self.authorized_newton_root_indexes = ()
        self.authorized_newton_logs = ()
        self.emitted_newton_root_indexes = []
        self.emitted_newton_logs = []
        self.authorized_mandelbrot_logs = ()
        self.emitted_mandelbrot_logs = []
        self.authorized_mandelbrot_sequential_dz_assignment = None
        self.emitted_mandelbrot_sequential_dz_assignment = []
        self.emitted_newton_struct_constructors = []
        self.emitted_newton_members = []
        self.emitted_newton_struct_count = 0
        self.authorized_texture_lod_sites = ()
        self.emitted_texture_lod_sites = []
        self.authorized_texture_frontend_nodes = ()
        self.authorized_texture_frontend_assignments = ()
        self.authorized_texture_frontend_inverse_sqrt = None
        self.authorized_texture_frontend_hash_conversion = None
        self.emitted_texture_frontend_nodes = []
        self.emitted_texture_frontend_assignments = []
        self.emitted_texture_frontend_inverse_sqrt = []
        self.emitted_texture_frontend_hash_conversion = []
        self.authorized_testpattern_proof = None
        self.authorized_osd_proof = None
        self.emitted_osd_array = []
        self.emitted_osd_indexes = []
        self.emitted_osd_bitwise = []
        self.emitted_osd_hash_modulos = []
        self.emitted_osd_globals = []
        self.authorized_spooky_ticker_proof = None
        self.authorized_spooky_ticker_nodes = ()
        self.emitted_spooky_ticker_array = []
        self.emitted_spooky_ticker_indexes = []
        self.emitted_spooky_ticker_bitwise = []
        self.emitted_spooky_ticker_globals = []
        self.authorized_spooky_ticker_varying_reads = ()
        self.emitted_spooky_ticker_varying_reads = []
        self.emitted_spooky_ticker_number_parameters = []
        self.emitted_spooky_ticker_number_declarations = []
        self.emitted_spooky_ticker_number_divisions = []
        self.emitted_spooky_ticker_number_umuls = []
        self.emitted_spooky_ticker_number_remainders = []
        self.emitted_spooky_ticker_hash_declarations = 0
        self.emitted_spooky_ticker_hash_definitions = 0
        self.emitted_testpattern_arrays = []
        self.emitted_testpattern_constructors = []
        self.emitted_testpattern_indexes = []
        self.emitted_testpattern_rounds = []
        self.authorized_testpattern_glyph_shift = None
        self.authorized_testpattern_glyph_mask = None
        self.emitted_testpattern_bitwise = []
        self.authorized_remap_proof = None
        self.emitted_remap_indexes = []
        self.emitted_remap_loops = []
        self.authorized_historic_palette_proof = None
        self.authorized_palette_frontend_proof = None
        self.authorized_color_lab_frontend_proof = None
        self.authorized_median_frontend_proof = None
        self.authorized_julia_frontend_proof = None
        self.authorized_julia_struct_materialization = None
        self.authorized_julia_out_direction_contract = None
        self.authorized_julia_out_parameters = ()
        self.authorized_julia_out_calls = ()
        self.authorized_color_lab_indexes = ()
        self.emitted_color_lab_indexes = []
        self.authorized_color_lab_vector_equalities = ()
        self.emitted_color_lab_vector_equalities = []
        self.emitted_median_indexes = []
        self.emitted_median_whiles = []
        self.emitted_historic_palette_members = []
        self.emitted_palette_members = []
        self.emitted_historic_palette_indexes = []
        self.emitted_palette_indexes = []
        self.emitted_historic_palette_structs = []
        self.emitted_palette_structs = []
        self.emitted_historic_palette_constructors = []
        self.emitted_palette_constructors = []
        self.emitted_historic_palette_number_vectors = []
        self.emitted_palette_number_vectors = []
        self.emitted_historic_palette_number_literals = []
        self.emitted_palette_number_literals = []
        self.emitted_palette_tau_sites = []
        self.emitted_palette_cosine_sites = []
        self.emitted_historic_palette_adapter_sites = []
        self.emitted_palette_adapter_sites = []
        self.emitted_historic_palette_counts = []
        self.emitted_palette_counts = []
        self.runtime_guard_emitted = False
        self.runtime_radius_declaration_emitted = False
        self.gabor_effective_depth_contract = None
        literal_source_key = literal_vec3_lane_selected_source_key(self.program)
        if self.program.body_status != "analyzed":
            raise _error(self.program, self.program, "typed body analysis is required")
        if self.numeric_literal_contract not in {"glsl-f32", "source-double"}:
            raise _error(self.program, self.program, "unsupported numeric literal contract")
        if self.program.key == JULIA_FRONTEND_KEY:
            allowed_profiles = {
                "julia_frontend_profile", "struct_declaration_profile",
                "out_inout_admission_profile",
            }
            foreign_profiles = tuple(
                name for name in self.__dataclass_fields__
                if name.endswith("_profile") and name not in allowed_profiles
                and getattr(self, name) is not None)
            if (self.numeric_literal_contract != "glsl-f32"
                    or self.compatibility_transform is not None
                    or self.julia_frontend_profile != JULIA_FRONTEND_PROFILE
                    or self.struct_declaration_profile != "struct-declaration-julia-v1"
                    or self.out_inout_admission_profile != OUT_INOUT_ADMISSION_JULIA_PROFILE
                    or foreign_profiles):
                raise _error(self.program, self.program,
                             "Julia profile metadata mismatch")
            try:
                self.authorized_julia_frontend_proof = authenticate_julia_frontend(
                    self.program, self.source_hash, self.julia_frontend_profile)
                self.authorized_struct_declaration = authenticate_struct_declaration(
                    self.program, self.source_hash,
                    self.struct_declaration_profile)
                self.authorized_julia_struct_materialization = (
                    struct_materialization_contract(self.program.key))
                out_record = authenticate_out_inout_admission(
                    self.program, self.source_hash,
                    self.out_inout_admission_profile)
                self.authorized_julia_out_parameters = out_record.parameters
                self.authorized_julia_out_calls = out_record.call_arguments
                self.authorized_julia_out_direction_contract = (
                    out_inout_direction_contract(self.program.key))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            return
        if self.julia_frontend_profile is not None:
            raise _error(self.program, self.program,
                         "Julia frontend profile on foreign key")
        if self.historic_palette_profile is not None:
            if (self.program.key != HISTORIC_PALETTE_KEY
                    or self.historic_palette_profile != HISTORIC_PALETTE_PROFILE):
                raise _error(self.program, self.program,
                             "Historic Palette profile metadata mismatch")
            try:
                self.authorized_historic_palette_proof = authenticate_historic_palette(
                    self.program, self.source_hash, self.historic_palette_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == HISTORIC_PALETTE_KEY:
            raise _error(self.program, self.program,
                         "exact Historic Palette profile carrier required")
        if self.palette_frontend_profile is not None:
            if (self.program.key != PALETTE_KEY
                    or self.palette_frontend_profile != PALETTE_FRONTEND_PROFILE):
                raise _error(self.program, self.program,
                             "Palette profile metadata mismatch")
            try:
                self.authorized_palette_frontend_proof = authenticate_palette_frontend(
                    self.program, self.source_hash, self.palette_frontend_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == PALETTE_KEY:
            raise _error(self.program, self.program,
                         "exact Palette profile carrier required")
        if self.color_lab_frontend_profile is not None:
            if (self.program.key != COLOR_LAB_KEY
                    or self.color_lab_frontend_profile
                    != COLOR_LAB_FRONTEND_PROFILE):
                raise _error(
                    self.program, self.program,
                    "ColorLab frontend profile metadata mismatch")
            try:
                self.authorized_color_lab_frontend_proof = (
                    authenticate_color_lab_frontend(
                        self.program, self.source_hash,
                        self.color_lab_frontend_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            self.authorized_color_lab_indexes = (
                self.authorized_color_lab_frontend_proof.index_nodes)
            self.authorized_color_lab_vector_equalities = (
                self.authorized_color_lab_frontend_proof.vector_equality_nodes)
        elif self.program.key == COLOR_LAB_KEY:
            raise _error(
                self.program, self.program,
                "exact ColorLab frontend profile carrier required")
        if self.median_frontend_profile is not None:
            if (self.program.key != MEDIAN_KEY
                    or self.median_frontend_profile != MEDIAN_FRONTEND_PROFILE):
                raise _error(
                    self.program, self.program,
                    "Median frontend profile metadata mismatch")
            try:
                self.authorized_median_frontend_proof = authenticate_median_frontend(
                    self.program, self.source_hash,
                    self.median_frontend_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == MEDIAN_KEY:
            raise _error(
                self.program, self.program,
                "exact Median frontend profile carrier required")
        if self.fractal_frontend_profile is not None:
            profile_fields = tuple(
                name for name in self.__dataclass_fields__
                if name.endswith("_profile")
                and name != "fractal_frontend_profile")
            if (self.program.key not in FRACTAL_PREPARED_KEYS
                    or self.fractal_frontend_profile
                    != FRACTAL_PREPARED_PROFILES[self.program.key]
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(getattr(self, name) is not None
                           for name in profile_fields)
                    or self.testpattern_frontend_proof is not None
                    or self.remap_frontend_proof is not None):
                raise _error(
                    self.program, self.program,
                    "Fractal frontend profile metadata mismatch")
            try:
                profiled = apply_fractal_frontend(
                    self.program, self.source_hash,
                    self.fractal_frontend_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            if profiled != self.program:
                raise _error(
                    self.program, self.program,
                    "Fractal counted-loop proof mismatch")
            proof = authenticate_fractal_frontend(
                self.program, self.source_hash,
                self.fractal_frontend_profile)
            self.authorized_fractal_frontend_indexes = proof.linear_srgb_indexes
            self.authorized_fractal_mat2_constructor = proof.matrix_constructor
            self.authorized_fractal_mode_contract = proof.mode_contract
            self.authorized_fractal_terminal_fallbacks = (
                proof.terminal_fallback_functions)
            self.authorized_fractal_alpha_product = proof.alpha_product
            self.authorized_fractal_alpha_literal = proof.alpha_literal
            self.authorized_fractal_hsv_function = proof.hsv_function
            self.authorized_fractal_hsv_parameter = proof.hsv_parameter
            self.authorized_fractal_hsv_calls = proof.hsv_calls
            self.authorized_fractal_hue_scale_assignment = (
                proof.hue_scale_assignment)
            self.authorized_fractal_hue_scale_product = proof.hue_scale_product
            self.authorized_fractal_hue_scale_literal = proof.hue_scale_literal
            self.authorized_fractal_distance_fract_assignment = (
                proof.distance_fract_assignment)
            self.authorized_fractal_distance_fract_builtin = (
                proof.distance_fract_builtin)
            self.authorized_fractal_distance_map_assignment = (
                proof.distance_map_assignment)
            self.authorized_fractal_distance_map_sum = proof.distance_map_sum
            self.authorized_fractal_distance_repeat_product = (
                proof.distance_repeat_product)
            self.authorized_fractal_distance_rotate_product = (
                proof.distance_rotate_product)
            self.authorized_fractal_distance_rotate_literal = (
                proof.distance_rotate_literal)
            self.authorized_fractal_palette_function = proof.palette_function
            self.authorized_fractal_palette_parameter = proof.palette_parameter
            self.authorized_fractal_palette_call = proof.palette_call
            self.authorized_fractal_newton_function = proof.newton_function
            self.authorized_fractal_newton_parameter = proof.newton_parameter
            self.authorized_fractal_newton_call = proof.newton_call
            self.authorized_fractal_julia_function = proof.julia_function
            self.authorized_fractal_julia_parameter = proof.julia_parameter
            self.authorized_fractal_julia_call = proof.julia_call
            self.authorized_fractal_julia_number_anchors = (
                proof.julia_number_anchors)
            self.authorized_fractal_mandelbrot_function = (
                proof.mandelbrot_function)
            self.authorized_fractal_mandelbrot_parameter = (
                proof.mandelbrot_parameter)
            self.authorized_fractal_mandelbrot_call = proof.mandelbrot_call
            self.authorized_fractal_mandelbrot_number_anchors = (
                proof.mandelbrot_number_anchors)
        elif self.program.key in FRACTAL_PREPARED_KEYS:
            raise _error(
                self.program, self.program,
                "exact Fractal frontend profile carrier required")
        if self.distortion_frontend_profile is not None:
            if (self.program.key != DISTORTION_FRONTEND_KEY
                    or self.distortion_frontend_profile != DISTORTION_FRONTEND_PROFILE
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "Distortion frontend profile metadata mismatch")
            try:
                self.authorized_distortion_frontend_proof = (
                    authenticate_distortion_frontend(
                        self.program, self.source_hash,
                        self.distortion_frontend_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in DISTORTION_FRONTEND_KEYS:
            raise _error(self.program, self.program,
                         "exact Distortion frontend profile carrier required")
        if self.noise_frontend_profile is not None:
            profile_fields = tuple(
                name for name in self.__dataclass_fields__
                if name.endswith("_profile")
                and name != "noise_frontend_profile")
            if (self.program.key != NOISE_FRONTEND_KEY
                    or self.noise_frontend_profile != NOISE_FRONTEND_PROFILE
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(getattr(self, name) is not None
                           for name in profile_fields)
                    or self.testpattern_frontend_proof is not None
                    or self.remap_frontend_proof is not None):
                raise _error(
                    self.program, self.program,
                    "Classic Noise frontend profile metadata mismatch")
            try:
                authenticate_noise_projection(
                    self.program, self.source_hash,
                    self.noise_frontend_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == NOISE_FRONTEND_KEY:
            raise _error(
                self.program, self.program,
                "exact Classic Noise frontend profile carrier required")
        try:
            if self.noise_frontend_profile is not None:
                self.runtime_loop_contract = authenticate_noise_runtime(
                    self.program, self.source_hash,
                    self.noise_frontend_profile)
            else:
                self.runtime_loop_contract = authenticate_runtime_loop_bound(
                    self.program, self.source_hash,
                    self.runtime_loop_bound_profile)
                if self.runtime_loop_contract is not None:
                    validate_runtime_loop_contract(self.runtime_loop_contract)
        except ValueError as error:
            raise _error(self.program, self.program, str(error)) from error
        if self.fractal_frontend_profile is not None:
            try:
                self.runtime_loop_contract = authenticate_fractal_runtime_contract(
                    self.program, self.source_hash,
                    self.fractal_frontend_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        if (self.program.key in RUNTIME_LOOP_BOUND_KEYS
                or self.program.key in PREPARED_RUNTIME_LOOP_BOUND_KEYS):
            if self.runtime_loop_bound_profile != RUNTIME_LOOP_BOUND_PROFILE:
                raise _error(self.program, self.program,
                             "exact runtime-loop-bound profile carrier required")
            if (self.program.key not in PREPARED_RUNTIME_LOOP_BOUND_KEYS
                    and (self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.as_u32_round_profile is not None
                    or self.ceil_admission_profile is not None
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None)):
                raise _error(self.program, self.program,
                             "runtime-loop-bound profile metadata mismatch")
        if (self.program.key == GABOR_KEY
                and self.gabor_effective_depth_profile is not None):
            if self.gabor_effective_depth_profile != GABOR_EFFECTIVE_DEPTH_PROFILE:
                raise _error(
                    self.program, self.program,
                    "exact Gabor effective-depth profile carrier required")
            if (self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.runtime_loop_bound_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.as_u32_round_profile is not None
                    or self.ceil_admission_profile is not None
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None):
                raise _error(self.program, self.program,
                             "Gabor effective-depth profile metadata mismatch")
            try:
                self.gabor_effective_depth_contract = (
                    authenticate_gabor_effective_depth(
                        self.program, self.source_hash,
                        self.gabor_effective_depth_profile))
                validate_gabor_effective_depth_contract(
                    self.gabor_effective_depth_contract)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            if self.gabor_effective_depth_contract._candidate is not self.program:
                raise _error(
                    self.program, self.program,
                    "Gabor effective-depth candidate identity mismatch")
        elif self.gabor_effective_depth_profile is not None:
            raise _error(self.program, self.program,
                         "Gabor effective-depth carrier on foreign key")
        if self.rotate_mat2_return_profile is not None:
            if (self.program.key != ROTATE_KEY
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None):
                raise _error(self.program, self.program,
                             "Rotate mat2 return profile metadata mismatch")
            try:
                (self.authorized_rotate_helper, constructor, call,
                 parent) = authenticate_rotate_mat2_return(
                     self.program, self.source_hash,
                     self.rotate_mat2_return_profile)
                self.authorized_rotate_expressions = (constructor, call, parent)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == ROTATE_KEY:
            raise _error(self.program, self.program,
                         "exact Rotate mat2 return profile carrier required")
        if self.focus_blur_borrowed_sampler_profile is not None:
            if (self.program.key != FOCUS_BLUR_KEY
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None):
                raise _error(self.program, self.program,
                             "Focus Blur borrowed sampler profile metadata mismatch")
            try:
                self.authorized_focus_blur_proof = (
                    authenticate_focus_blur_borrowed_sampler_parameters(
                        self.program, self.source_hash,
                        self.focus_blur_borrowed_sampler_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == FOCUS_BLUR_KEY:
            raise _error(self.program, self.program,
                         "exact Focus Blur borrowed sampler profile carrier required")
        if self.extrude_bvec2_relational_reduction_profile is not None:
            if (self.program.key != EXTRUDE_KEY
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None):
                raise _error(self.program, self.program,
                             "Extrude bvec2 relational reduction profile metadata mismatch")
            # Independent re-authentication. The emitter never trusts the
            # validator's result or a supplied proof object.
            try:
                self.authorized_extrude_proof = (
                    authenticate_extrude_bvec2_relational_reduction(
                        self.program, self.source_hash,
                        self.extrude_bvec2_relational_reduction_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == EXTRUDE_KEY:
            raise _error(self.program, self.program,
                         "exact Extrude bvec2 relational reduction profile carrier required")
        if self.edge_bvec3_contour_profile is not None:
            collisions = (
                self.compatibility_transform, self.custom_comparer_profile,
                self.source_global_literal_int_profile,
                self.runtime_loop_bound_profile,
                self.gabor_effective_depth_profile,
                self.gather_sorted_round_profile,
                self.literal_vec3_lane_index_profile,
                self.smooth_edge_luma_weights_profile,
                self.perlin_scalar_uint_xor_profile,
                self.scalar_uint_xor_profile,
                self.bitwise_scalar_int_ops_profile,
                self.rotate_mat2_return_profile,
                self.focus_blur_borrowed_sampler_profile,
                self.extrude_bvec2_relational_reduction_profile,
                self.caustic_word_hash_profile,
                self.scanline_error_float_bits_ingress_profile,
                self.glyph_map_nonnegative_int_shift_profile,
                self.curl_vector_math_profile,
                self.grade_luma_weights_profile,
                self.grade_index_expression_profile,
                self.derivative_admission_profile,
                self.linear_srgb_lane_index_profile,
                self.reflect_admission_profile,
                self.posterize_round_profile, self.as_u32_round_profile,
                self.ceil_admission_profile, self.waves_any_notequal_profile,
                self.inout_vec3_swap_profile,
                self.glitch_mat4_chain_profile,
                self.emboss_color_style_profile,
            )
            if (self.program.key != EDGE_KEY
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(item is not None for item in collisions)):
                raise _error(
                    self.program, self.program,
                    "Edge bvec3 contour profile metadata mismatch")
            try:
                self.authorized_edge_proof = authenticate_edge_bvec3_contour(
                    self.program, self.source_hash,
                    self.edge_bvec3_contour_profile)
                self.authorized_edge_splat_proof = authenticate_edge_center_splat(
                    self.program, self.source_hash,
                    self.edge_bvec3_contour_profile)
                proof = self.authorized_edge_proof
                splat = self.authorized_edge_splat_proof
                if (proof._candidate is not self.program
                        or not isinstance(proof.bvec_nodes, tuple)
                        or len(proof.bvec_nodes) != 12
                        or not isinstance(proof.relationals, tuple)
                        or proof.relationals != (
                            proof.bvec_nodes[2], proof.bvec_nodes[3])
                        or not isinstance(proof.declarations, tuple)
                        or proof.declarations != (
                            proof.bvec_nodes[0], proof.bvec_nodes[4])
                        or proof.constructor is not proof.bvec_nodes[5]
                        or proof.declarations[1].children[0]
                        is not proof.constructor
                        or not isinstance(proof.id_reads, tuple)
                        or proof.id_reads != proof.bvec_nodes[6:12]
                        or not isinstance(proof.swizzles, tuple)
                        or len(proof.swizzles) != 6
                        or any(swizzle.children[0] is not read
                               for swizzle, read in zip(
                                   proof.swizzles, proof.id_reads))
                        or len(proof.consumed_objects) != 22
                        or len({id(item) for item in proof.consumed_objects})
                        != 22
                        or splat._candidate is not self.program
                        or len(splat.consumed_objects) != 12
                        or len({id(item) for item in splat.consumed_objects})
                        != 12
                        or splat.statement is not splat.statement_parent_chain[-1]
                        or splat.assignment.children != (
                            splat.target, splat.constructor)
                        or splat.constructor.children != (splat.dot,)
                        or splat.dot.children != (
                            splat.dot_target, splat.luma)
                        or splat.target.symbol_id != 59
                        or splat.dot_target.symbol_id != 59
                        or splat.luma.symbol_id != 14):
                    raise ValueError(
                        "candidate ownership, site order, uniqueness, or parent mismatch")
            except (AttributeError, IndexError, TypeError, ValueError) as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == EDGE_KEY:
            raise _error(
                self.program, self.program,
                "exact Edge bvec3 contour profile carrier required")
        if self.glitch_mat4_chain_profile is not None:
            # Per-key since the effects row (the first three-carrier row):
            # effects' REQUIRED companions -- the mutable-global array
            # closure and the ceil admission -- are read from the module's
            # own REQUIRED_COMPANION_PROFILES; a present companion must be
            # exact, an absent one is the owning block's business, and an
            # unmapped key resolves to no companions and keeps the strict
            # absent set (the normalMap pattern).
            glitch_companions = dict(
                GLITCH_MAT4_CHAIN_COMPANIONS.get(self.program.key, ()))
            glitch_companion_row = {
                "scalar_uint_xor_profile": self.scalar_uint_xor_profile,
                "mutable_global_array_profile":
                    self.mutable_global_array_profile,
                "ceil_admission_profile": self.ceil_admission_profile,
            }
            collisions = (
                self.compatibility_transform, self.custom_comparer_profile,
                self.source_global_literal_int_profile,
                self.runtime_loop_bound_profile,
                self.gabor_effective_depth_profile,
                self.gather_sorted_round_profile,
                self.literal_vec3_lane_index_profile,
                self.smooth_edge_luma_weights_profile,
                self.perlin_scalar_uint_xor_profile,
                self.bitwise_scalar_int_ops_profile,
                self.rotate_mat2_return_profile,
                self.focus_blur_borrowed_sampler_profile,
                self.extrude_bvec2_relational_reduction_profile,
                self.edge_bvec3_contour_profile,
                self.caustic_word_hash_profile,
                self.scanline_error_float_bits_ingress_profile,
                self.glyph_map_nonnegative_int_shift_profile,
                self.curl_vector_math_profile,
                self.grade_luma_weights_profile,
                self.grade_index_expression_profile,
                self.derivative_admission_profile,
                self.linear_srgb_lane_index_profile,
                self.reflect_admission_profile,
                self.posterize_round_profile, self.as_u32_round_profile,
                self.waves_any_notequal_profile,
                self.inout_vec3_swap_profile,
                self.emboss_color_style_profile,
            )
            if (self.program.key not in GLITCH_MAT4_CHAIN_KEYS
                    or self.glitch_mat4_chain_profile
                    != GLITCH_MAT4_CHAIN_PROFILES.get(self.program.key)
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(item is not None for item in collisions)
                    or any(glitch_companion_row.get(name) is not None
                           and name not in glitch_companions
                           for name in glitch_companion_row)):
                raise _error(
                    self.program, self.program,
                    "Glitch mat4 chain profile metadata mismatch")
            try:
                self.authorized_glitch_proof = authenticate_glitch_mat4_chain(
                    self.program, self.source_hash,
                    self.glitch_mat4_chain_profile)
                proof = self.authorized_glitch_proof
                if (proof._candidate is not self.program
                        or not isinstance(proof.declarations, tuple)
                        or len(proof.declarations) != 4
                        or not isinstance(proof.constructors, tuple)
                        or len(proof.constructors) != 3
                        or not isinstance(proof.matrix_products, tuple)
                        or len(proof.matrix_products) != 2
                        or not isinstance(proof.matrix_ids, tuple)
                        or len(proof.matrix_ids) != 4
                        or not isinstance(proof.vector_products, tuple)
                        or len(proof.vector_products) != 1
                        or not isinstance(proof.consumed_objects, tuple)
                        or len(proof.consumed_objects) != 14
                        or len({id(item) for item in proof.consumed_objects})
                        != 14
                        or proof.consumed_objects != (
                            proof.declarations[0], proof.constructors[0],
                            proof.declarations[1], proof.constructors[1],
                            proof.declarations[2], proof.constructors[2],
                            proof.declarations[3], proof.matrix_products[0],
                            proof.matrix_products[1], proof.matrix_ids[0],
                            proof.matrix_ids[1], proof.matrix_ids[2],
                            proof.vector_products[0], proof.matrix_ids[3])
                        or proof.declarations[0].children != (
                            proof.constructors[0],)
                        or proof.declarations[1].children != (
                            proof.constructors[1],)
                        or proof.declarations[2].children != (
                            proof.constructors[2],)
                        or proof.declarations[3].children != (
                            proof.matrix_products[0],)
                        or proof.matrix_products[0].children[0]
                        is not proof.matrix_products[1]
                        or proof.matrix_products[1].children != (
                            proof.matrix_ids[0], proof.matrix_ids[1])
                        or proof.matrix_products[0].children[1]
                        is not proof.matrix_ids[2]
                        or proof.vector_products[0].children[1]
                        is not proof.matrix_ids[3]
                        or proof.dot.children[0]
                        is not proof.vector_products[0]
                        or proof.return_statement.expressions != (proof.dot,)):
                    raise ValueError(
                        "candidate ownership, site order, uniqueness, or parent mismatch")
                # PER KEY since the effects row: glitch alone carries the
                # ordered freq splat; effects' proof has none, and its
                # host/dot/return identity locks live in the module record.
                if proof.ordered_freq_splat_assignment is not None:
                    if (proof.ordered_freq_splat_assignment.children != (
                            proof.ordered_freq_splat_target,
                            proof.ordered_freq_splat_constructor)
                            or proof.ordered_freq_splat_assignment.operator
                            != "*="
                            or proof.ordered_freq_splat_target.symbol_id != 75
                            or proof.ordered_freq_splat_constructor.children[0].callee
                            != "periodicFunction"):
                        raise ValueError(
                            "candidate ownership, site order, uniqueness, "
                            "or parent mismatch")
            except (AttributeError, IndexError, TypeError, ValueError) as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in GLITCH_MAT4_CHAIN_KEYS:
            raise _error(
                self.program, self.program,
                "exact Glitch mat4 chain profile carrier required")
        if self.emboss_color_style_profile is not None:
            collisions = (
                self.compatibility_transform, self.custom_comparer_profile,
                self.source_global_literal_int_profile,
                self.runtime_loop_bound_profile,
                self.gabor_effective_depth_profile,
                self.gather_sorted_round_profile,
                self.literal_vec3_lane_index_profile,
                self.smooth_edge_luma_weights_profile,
                self.perlin_scalar_uint_xor_profile,
                self.scalar_uint_xor_profile,
                self.bitwise_scalar_int_ops_profile,
                self.rotate_mat2_return_profile,
                self.focus_blur_borrowed_sampler_profile,
                self.extrude_bvec2_relational_reduction_profile,
                self.edge_bvec3_contour_profile,
                self.glitch_mat4_chain_profile,
                self.caustic_word_hash_profile,
                self.scanline_error_float_bits_ingress_profile,
                self.glyph_map_nonnegative_int_shift_profile,
                self.curl_vector_math_profile,
                self.grade_luma_weights_profile,
                self.grade_index_expression_profile,
                self.derivative_admission_profile,
                self.linear_srgb_lane_index_profile,
                self.reflect_admission_profile,
                self.posterize_round_profile, self.as_u32_round_profile,
                self.ceil_admission_profile, self.waves_any_notequal_profile,
                self.inout_vec3_swap_profile,
            )
            if (self.program.key != EMBOSS_KEY
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(item is not None for item in collisions)):
                raise _error(
                    self.program, self.program,
                    "Emboss color-style profile metadata mismatch")
            try:
                self.authorized_emboss_proof = authenticate_emboss_color_style(
                    self.program, self.source_hash,
                    self.emboss_color_style_profile)
                proof = self.authorized_emboss_proof
                stores = tuple(store for table in proof.tables
                               for store in table.literal_stores)
                reads = tuple(table.dynamic_read for table in proof.tables)
                owned_ids = _program_owned_object_ids(self.program)
                if (proof._candidate is not self.program
                        or not isinstance(proof.tables, tuple)
                        or len(proof.tables) != 4
                        or not isinstance(proof.consumed_objects, tuple)
                        or len({id(item) for item in proof.consumed_objects})
                        != len(proof.consumed_objects)
                        or any(id(item) not in owned_ids
                               for item in proof.consumed_objects)
                        or any(table._candidate is not self.program
                               or not any(table.owner is function
                                          for function in self.program.functions)
                               or table.owner.body[
                                   table.declaration_statement_index]
                               is not table.declaration_statement
                               or not _same_object_sequence(
                                   table.declaration_statement.expressions,
                                   (table.declaration,))
                               or len(table.literal_store_statements) != 9
                               or len(table.literal_stores) != 9
                               or any(table.owner.body[index] is not statement
                                      for index, statement in zip(
                                          table.literal_store_statement_indices,
                                          table.literal_store_statements))
                               or any(not _same_object_sequence(
                                          statement.expressions, (store,))
                                      for statement, store in zip(
                                          table.literal_store_statements,
                                          table.literal_stores))
                               or table.owner.body[table.loop_statement_index]
                               is not table.loop_statement
                               or table.loop_statement.children[1]
                               is not table.loop_body
                               for table in proof.tables)
                        or len(stores) != 36
                        or len({id(item) for item in stores}) != 36
                        or len({id(item) for item in reads}) != 4
                        or not _same_object_sequence(
                            proof.full_frame_declaration.children,
                            (proof.full_frame_conjunction,))
                        or not _same_object_sequence(
                            proof.full_frame_conjunction.children,
                            proof.reductions)
                        or any(not _same_object_sequence(
                                   reduction.children, (equality,))
                               for equality, reduction in zip(
                                   proof.equalities, proof.reductions))
                        or not _same_object_sequence(
                            proof.color_texel_declaration.children,
                            (proof.color_texel_conditional,))
                        or proof.color_texel_conditional.children[0].symbol_id
                        != proof.full_frame_declaration.symbol_id
                        or len(proof.texture_coordinate_divisions) != 2
                        or len(proof.texture_coordinate_numerators) != 2
                        or any(division.children[0] is not numerator
                               or division.kind != "binary"
                               or division.operator != "/"
                               or division.type.display() != "vec2"
                               or numerator.type.display() != "vec2"
                               for division, numerator in zip(
                                   proof.texture_coordinate_divisions,
                                   proof.texture_coordinate_numerators))):
                    raise ValueError(
                        "candidate ownership, table, or boolean parent mismatch")
            except (AttributeError, IndexError, TypeError, ValueError) as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == EMBOSS_KEY:
            raise _error(
                self.program, self.program,
                "exact Emboss color-style profile carrier required")
        if self.caustic_word_hash_profile is not None:
            if (self.program.key != CAUSTIC_KEY
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None):
                raise _error(self.program, self.program,
                             "Caustic word hash profile metadata mismatch")
            # Independent re-authentication; never trusts the validator.
            try:
                self.authorized_caustic_proof = authenticate_caustic_word_hash(
                    self.program, self.source_hash, self.caustic_word_hash_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == CAUSTIC_KEY:
            raise _error(self.program, self.program,
                         "exact Caustic word hash profile carrier required")
        if self.scanline_error_float_bits_ingress_profile is not None:
            if (self.program.key != SCANLINE_ERROR_KEY
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.runtime_loop_bound_profile is not None
                    or self.gabor_effective_depth_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.as_u32_round_profile is not None
                    or self.ceil_admission_profile is not None
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None):
                raise _error(
                    self.program, self.program,
                    "Scanline Error float-bit ingress profile metadata mismatch")
            try:
                self.authorized_scanline_error_proof = (
                    authenticate_scanline_error_float_bits_ingress(
                        self.program, self.source_hash,
                        self.scanline_error_float_bits_ingress_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == SCANLINE_ERROR_KEY:
            raise _error(
                self.program, self.program,
                "exact Scanline Error float-bit ingress profile carrier required")
        if self.shapes_float_bits_ingress_profile is not None:
            # Independent authority. The emitter re-derives this closure from
            # the candidate tree and never consults the validator's result.
            # Shapes is admitted by three carriers at once, so this block
            # requires its two companions to be PRESENT and exact instead of
            # absent -- see the matching justification in
            # generate_typed_slice.validate_capabilities.
            if (self.program.key not in SHAPES_FLOAT_BITS_INGRESS_KEYS
                    or self.scalar_uint_xor_profile != SCALAR_UINT_XOR_PROFILE
                    or self.linear_srgb_lane_index_profile
                    != LINEAR_SRGB_LANE_INDEX_PROFILES.get(self.program.key)
                    or self.shapes_rvalue_assign_profile
                    != SHAPES_RVALUE_ASSIGN_PROFILE
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.runtime_loop_bound_profile is not None
                    or self.gabor_effective_depth_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.edge_bvec3_contour_profile is not None
                    or self.glitch_mat4_chain_profile is not None
                    or self.emboss_color_style_profile is not None
                    or self.shape_mixer_builtin_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.scanline_error_float_bits_ingress_profile is not None
                    or self.glyph_map_nonnegative_int_shift_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.as_u32_round_profile is not None
                    or self.ceil_admission_profile is not None
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None):
                raise _error(
                    self.program, self.program,
                    "Shapes float-bit ingress profile metadata mismatch")
            try:
                self.authorized_shapes_float_bits_ingresses = (
                    authenticate_shapes_float_bits_ingress(
                        self.program, self.source_hash,
                        self.shapes_float_bits_ingress_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in SHAPES_FLOAT_BITS_INGRESS_KEYS:
            raise _error(
                self.program, self.program,
                "exact Shapes float-bit ingress profile carrier required")
        if self.grime_float_bits_ingress_profile is not None:
            # Independent authority, like every block above: the emitter
            # re-derives grime's five ingresses from the candidate tree and
            # never consults the validator's result. The varying companion
            # must be PRESENT and exact -- grime's row carries both and
            # neither carrier stands alone.
            if (self.program.key not in GRIME_FLOAT_BITS_INGRESS_KEYS
                    or self.grime_float_bits_ingress_profile
                    != GRIME_FLOAT_BITS_INGRESS_PROFILE
                    or self.varying_profile is None):
                raise _error(
                    self.program, self.program,
                    "grime float-bit ingress profile metadata mismatch")
            try:
                self.authorized_grime_float_bits_ingresses = (
                    authenticate_grime_float_bits_ingress(
                        self.program, self.source_hash,
                        self.grime_float_bits_ingress_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in GRIME_FLOAT_BITS_INGRESS_KEYS:
            raise _error(
                self.program, self.program,
                "exact grime float-bit ingress profile carrier required")
        if self.shapes_rvalue_assign_profile is not None:
            # Design amendment 2 (§12). This is the carrier for the ONE
            # boundary Shapes actually widens in this file: the expression
            # dispatcher's gated `assign` arm below. Independent
            # re-authentication; the emitter never trusts the validator.
            if (self.program.key not in SHAPES_RVALUE_ASSIGN_KEYS
                    or self.scalar_uint_xor_profile != SCALAR_UINT_XOR_PROFILE
                    or self.linear_srgb_lane_index_profile
                    != LINEAR_SRGB_LANE_INDEX_PROFILES.get(self.program.key)
                    or self.shapes_float_bits_ingress_profile
                    != SHAPES_FLOAT_BITS_INGRESS_PROFILE
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.runtime_loop_bound_profile is not None
                    or self.gabor_effective_depth_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.edge_bvec3_contour_profile is not None
                    or self.glitch_mat4_chain_profile is not None
                    or self.emboss_color_style_profile is not None
                    or self.shape_mixer_builtin_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.scanline_error_float_bits_ingress_profile is not None
                    or self.glyph_map_nonnegative_int_shift_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.as_u32_round_profile is not None
                    or self.ceil_admission_profile is not None
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None):
                raise _error(
                    self.program, self.program,
                    "Shapes rvalue-assign profile metadata mismatch")
            try:
                self.authorized_shapes_rvalue_assigns = (
                    authenticate_shapes_rvalue_assign(
                        self.program, self.source_hash,
                        self.shapes_rvalue_assign_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in SHAPES_RVALUE_ASSIGN_KEYS:
            raise _error(
                self.program, self.program,
                "exact Shapes rvalue-assign profile carrier required")
        if self.cross_lane_assignment_profile is not None:
            if self.program.key != CROSS_LANE_KEY or self.cross_lane_assignment_profile != CROSS_LANE_ASSIGNMENT_PROFILE:
                raise _error(self.program, self.program, "cross-lane assignment profile metadata mismatch")
            try:
                self.authorized_cross_lane_assignment = authenticate_cross_lane_assignment(
                    self.program, self.source_hash, self.cross_lane_assignment_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == CROSS_LANE_KEY:
            raise _error(self.program, self.program, "exact cross-lane assignment profile carrier required")
        if self.glyph_map_nonnegative_int_shift_profile is not None:
            if (self.program.key != GLYPH_MAP_KEY
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.runtime_loop_bound_profile is not None
                    or self.gabor_effective_depth_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.scanline_error_float_bits_ingress_profile is not None
                    or self.shapes_float_bits_ingress_profile is not None
                    or self.shapes_rvalue_assign_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.as_u32_round_profile is not None
                    or self.ceil_admission_profile is not None
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None):
                raise _error(self.program, self.program,
                             "Glyph Map shift profile metadata mismatch")
            try:
                self.authorized_glyph_map_proof = (
                    authenticate_glyph_map_nonnegative_int_shift(
                        self.program, self.source_hash,
                        self.glyph_map_nonnegative_int_shift_profile))
                proof = self.authorized_glyph_map_proof
                sites = proof.sites
                if proof._candidate is not self.program:
                    raise ValueError("candidate identity mismatch")
                if (not isinstance(sites, tuple) or len(sites) != 2
                        or sites[0] is not getattr(proof, "mask", None)
                        or sites[1] is not getattr(proof, "shift", None)
                        or sites[0] is sites[1]
                        or sites[0].kind != "binary"
                        or sites[0].operator != "&"
                        or sites[1].kind != "binary"
                        or sites[1].operator != ">>"
                        or len(sites[0].children) != 2
                        or sites[0].children[0] is not sites[1]):
                    raise ValueError(
                        "site order, uniqueness, or parent mismatch")
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        if self.curl_vector_math_profile is not None:
            if (self.program.key != CURL_KEY
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None):
                raise _error(self.program, self.program,
                             "Curl vector math profile metadata mismatch")
            # Independent re-authentication; never trusts the validator.
            try:
                self.authorized_curl_proof = authenticate_curl_vector_math(
                    self.program, self.source_hash, self.curl_vector_math_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == CURL_KEY:
            raise _error(self.program, self.program,
                         "exact Curl vector math profile carrier required")
        if self.grade_luma_weights_profile is not None:
            if (self.program.key not in GRADE_LUMA_WEIGHTS_KEYS
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None):
                raise _error(self.program, self.program,
                             "Grade LUMA weights profile metadata mismatch")
            # Independent re-authentication. The emitter never trusts the
            # validator's result or a supplied proof object.
            try:
                self.authorized_grade_luma_weights_declaration = (
                    authenticate_grade_luma_weights(
                        self.program, self.source_hash,
                        self.grade_luma_weights_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in GRADE_LUMA_WEIGHTS_KEYS:
            raise _error(self.program, self.program,
                         "exact Grade LUMA weights profile carrier required")
        # grade_index_expression_profile deliberately coexists with
        # grade_luma_weights_profile above -- see the matching comment in
        # generate_typed_slice.py's validate_capabilities.
        if self.grade_index_expression_profile is not None:
            if (self.program.key not in GRADE_INDEX_EXPRESSION_KEYS
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None):
                raise _error(self.program, self.program,
                             "Grade index expression profile metadata mismatch")
            # Independent re-authentication. The emitter never trusts the
            # validator's result or a supplied proof object.
            try:
                self.authorized_grade_index_sites = (
                    authenticate_grade_index_expression(
                        self.program, self.source_hash,
                        self.grade_index_expression_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in GRADE_INDEX_EXPRESSION_KEYS:
            raise _error(self.program, self.program,
                         "exact Grade index expression profile carrier required")
        if self.derivative_admission_profile is not None:
            if (self.program.key not in DERIVATIVE_ADMISSION_KEYS
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None):
                raise _error(self.program, self.program,
                             "Derivative admission profile metadata mismatch")
            # Independent re-authentication. The emitter never trusts the
            # validator's result or a supplied proof object.
            try:
                self.authorized_derivative_proof = authenticate_derivative_admission(
                    self.program, self.source_hash,
                    self.derivative_admission_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in DERIVATIVE_ADMISSION_KEYS:
            raise _error(self.program, self.program,
                         "exact Derivative admission profile carrier required")
        if self.gather_sorted_round_profile is not None:
            if (self.program.key != GATHER_SORTED_KEY
                    or self.compatibility_transform is not None
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "Gather Sorted round profile metadata mismatch")
            try:
                (self.authorized_round_parent,
                 self.authorized_round) = authenticate_gather_sorted_round_to_int(
                     self.program, self.source_hash,
                     self.gather_sorted_round_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        # posterize_round_profile and waves_any_notequal_profile are
        # deliberately light-checked, the same style as gather_sorted_round_
        # profile immediately above -- and deliberately NOT mutually
        # exclusive with derivative_admission_profile, since both Posterize
        # and Waves also carry a derivative call admitted by that profile.
        if self.posterize_round_profile is not None:
            if (self.program.key != POSTERIZE_KEY
                    or self.compatibility_transform is not None
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "Posterize round admission profile metadata mismatch")
            try:
                self.authorized_posterize_round = (
                    authenticate_posterize_round_admission(
                        self.program, self.source_hash,
                        self.posterize_round_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == POSTERIZE_KEY:
            raise _error(self.program, self.program,
                         "exact Posterize round admission profile carrier required")
        # as_u32_round_profile is deliberately light-checked, the same style
        # as posterize_round_profile immediately above, keyed by a dict of
        # program_key carriers (AS_U32_ROUND_KEYS) since the admitted `round`
        # site is inside a byte-identical shared helper reused verbatim
        # across several programs, rather than a one-off.
        if self.ceil_admission_profile is not None:
            try:
                self.authorized_ceil = authenticate_ceil_admission(
                    self.program, self.source_hash, self.ceil_admission_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        if self.as_u32_round_profile is not None:
            if (self.program.key not in AS_U32_ROUND_KEYS
                    or self.compatibility_transform is not None
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "as_u32 round admission profile metadata mismatch")
            try:
                self.authorized_as_u32_round = (
                    authenticate_as_u32_round_admission(
                        self.program, self.source_hash,
                        self.as_u32_round_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in AS_U32_ROUND_KEYS:
            raise _error(self.program, self.program,
                         "exact as_u32 round admission profile carrier required")
        if self.waves_any_notequal_profile is not None:
            if (self.program.key != WAVES_KEY
                    or self.compatibility_transform is not None
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "Waves any/notEqual admission profile metadata mismatch")
            try:
                waves_proof = authenticate_waves_any_notequal_admission(
                    self.program, self.source_hash,
                    self.waves_any_notequal_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            self.authorized_waves_relationals = waves_proof.relationals
            self.authorized_waves_reductions = waves_proof.reductions
        elif self.program.key == WAVES_KEY:
            raise _error(self.program, self.program,
                         "exact Waves any/notEqual admission profile carrier required")
        # inout_vec3_swap_profile is deliberately light-checked, the same
        # style as posterize_round_profile/waves_any_notequal_profile above.
        if self.inout_vec3_swap_profile is not None:
            if (self.program.key != INOUT_VEC3_SWAP_KEY
                    or self.compatibility_transform is not None
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "Inout vec3 swap admission profile metadata mismatch")
            try:
                self.authorized_inout_vec3_swap_proof = (
                    authenticate_inout_vec3_swap_admission(
                        self.program, self.source_hash,
                        self.inout_vec3_swap_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == INOUT_VEC3_SWAP_KEY:
            raise _error(self.program, self.program,
                         "exact Inout vec3 swap admission profile carrier required")
        if self.log_admission_profile is not None:
            if (self.program.key != LOG_ADMISSION_MANDELBROT_KEY
                    or self.log_admission_profile != LOG_ADMISSION_MANDELBROT_PROFILE
                    or self.compatibility_transform is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.out_inout_admission_profile is None):
                raise _error(self.program, self.program,
                             "Mandelbrot log admission profile metadata mismatch")
            try:
                log_proof = authenticate_log_admission(
                    self.program, self.source_hash, self.log_admission_profile)
                if log_proof is None:
                    raise ValueError("Mandelbrot log admission proof is absent")
                self.authorized_mandelbrot_logs = tuple(
                    site.node for site in log_proof.sites)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in LOG_ADMISSION_KEYS:
            raise _error(self.program, self.program,
                         "exact Mandelbrot log admission profile carrier required")
        if self.mandelbrot_sequential_dz_assignment_profile is not None:
            if (self.program.key != MANDELBROT_DZ_KEY
                    or self.mandelbrot_sequential_dz_assignment_profile
                    != MANDELBROT_DZ_PROFILE
                    or self.compatibility_transform is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.log_admission_profile is None
                    or self.out_inout_admission_profile is None):
                raise _error(
                    self.program, self.program,
                    "Mandelbrot sequential dz profile metadata mismatch")
            try:
                self.authorized_mandelbrot_sequential_dz_assignment = (
                    authenticate_mandelbrot_sequential_dz_assignment(
                        self.program, self.source_hash,
                        self.mandelbrot_sequential_dz_assignment_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == MANDELBROT_DZ_KEY:
            raise _error(
                self.program, self.program,
                "exact Mandelbrot sequential dz profile carrier required")
        if self.struct_declaration_profile is not None:
            if (self.program.key != STRUCT_DECLARATION_NEWTON_KEY
                    or self.compatibility_transform is not None
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "struct declaration profile metadata mismatch")
            try:
                self.authorized_struct_declaration = (
                    authenticate_struct_declaration(
                        self.program, self.source_hash,
                        self.struct_declaration_profile))
                self.authorized_struct_materialization = (
                    struct_materialization_contract(self.program.key))
                (self.authorized_newton_roots_declaration,
                 self.authorized_newton_root_indexes,
                 self.authorized_newton_logs) = _authenticate_newton_lowering(
                     self.program)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in STRUCT_DECLARATION_KEYS:
            raise _error(self.program, self.program,
                         "exact struct declaration profile carrier required")
        if self.out_inout_admission_profile is not None:
            collisions = (
                self.compatibility_transform, self.custom_comparer_profile,
                self.runtime_loop_bound_profile,
                self.gabor_effective_depth_profile,
                self.gather_sorted_round_profile,
                self.literal_vec3_lane_index_profile,
                self.smooth_edge_luma_weights_profile,
                self.perlin_scalar_uint_xor_profile,
                self.scalar_uint_xor_profile,
                self.bitwise_scalar_int_ops_profile,
                self.rotate_mat2_return_profile,
                self.focus_blur_borrowed_sampler_profile,
                self.extrude_bvec2_relational_reduction_profile,
                self.edge_bvec3_contour_profile, self.glitch_mat4_chain_profile,
                self.emboss_color_style_profile,
                self.shape_mixer_builtin_profile, self.caustic_word_hash_profile,
                self.scanline_error_float_bits_ingress_profile,
                self.shapes_float_bits_ingress_profile,
                self.grime_float_bits_ingress_profile,
                self.shapes_rvalue_assign_profile,
                self.mutable_global_frame_profile,
                self.mutable_global_array_profile,
                self.const_global_table_profile, self.varying_profile,
                self.texture_lod_admission_profile,
                self.cross_lane_assignment_profile,
                self.glyph_map_nonnegative_int_shift_profile,
                self.curl_vector_math_profile, self.grade_luma_weights_profile,
                self.grade_index_expression_profile,
                self.derivative_admission_profile,
                self.linear_srgb_lane_index_profile,
                self.reflect_admission_profile,
                self.posterize_round_profile, self.as_u32_round_profile,
                self.ceil_admission_profile, self.waves_any_notequal_profile,
                self.inout_vec3_swap_profile)
            expected_out_profile = {
                OUT_INOUT_ADMISSION_LIGHTLEAK_KEY:
                    OUT_INOUT_ADMISSION_LIGHTLEAK_PROFILE,
                OUT_INOUT_ADMISSION_MANDELBROT_KEY:
                    OUT_INOUT_ADMISSION_MANDELBROT_PROFILE,
                OUT_INOUT_ADMISSION_NEWTON_KEY:
                    OUT_INOUT_ADMISSION_NEWTON_PROFILE,
            }.get(self.program.key)
            if ((self.program.key not in OUT_INOUT_ADMISSION_KEYS
                    and self.program.key != OUT_INOUT_ADMISSION_NEWTON_KEY)
                    or self.out_inout_admission_profile != expected_out_profile
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(item is not None for item in collisions)):
                raise _error(self.program, self.program,
                             "out/inout admission profile metadata mismatch")
            try:
                (self.authorized_out_inout_parameters,
                 self.authorized_out_inout_calls) = authenticate_out_inout_admission(
                     self.program, self.source_hash,
                     self.out_inout_admission_profile)
                self.out_inout_direction_contract = out_inout_direction_contract(
                    self.program.key)
                abi_by_name = dict(
                    self.out_inout_direction_contract.parameter_abis)
                functions_by_signature = {
                    function.signature.id: function
                    for function in self.program.functions}
                for call in self.authorized_out_inout_calls:
                    owner = functions_by_signature.get(call.signature_id)
                    if owner is None:
                        raise _error(self.program, call,
                                     "authenticated out/inout call signature drift")
                    out_parameters = tuple(
                        parameter for parameter in owner.parameters
                        if parameter.direction != "in")
                    if not out_parameters or len(call.children) < len(out_parameters):
                        raise _error(self.program, call,
                                     "authenticated out/inout argument census drift")
                    for parameter, argument in zip(
                            out_parameters, call.children[-len(out_parameters):]):
                        abi = abi_by_name.get(parameter.name)
                        if abi is None:
                            abi = self.out_inout_direction_contract.native_abi
                        if abi is None or argument.kind != "id":
                            raise _error(
                                self.program, call,
                                "authenticated out/inout argument ABI drift")
                        previous = self.authorized_out_inout_argument_abis.get(
                            argument.symbol_id)
                        if previous is not None and previous != abi:
                            raise _error(
                                self.program, call,
                                "authenticated out/inout argument ABI collision")
                        self.authorized_out_inout_argument_abis[
                            argument.symbol_id] = abi
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in OUT_INOUT_ADMISSION_KEYS:
            raise _error(self.program, self.program,
                         "exact out/inout admission profile carrier required")
        if self.perlin_scalar_uint_xor_profile is not None:
            if (self.program.key != PERLIN_KEY
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None):
                raise _error(
                    self.program, self.program,
                    "Perlin scalar uint XOR profile metadata mismatch")
            try:
                self.authorized_perlin_scalar_uint_xors = (
                    authenticate_perlin_scalar_uint_xor(
                        self.program, self.source_hash,
                        self.perlin_scalar_uint_xor_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == PERLIN_KEY:
            raise _error(
                self.program, self.program,
                "exact Perlin scalar uint XOR profile carrier required")
        if self.scalar_uint_xor_profile is not None:
            if (self.program.key not in SCALAR_UINT_XOR_KEYS
                    and self.program.key not in PREPARED_SCALAR_UINT_XOR_KEYS
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None):
                raise _error(
                    self.program, self.program,
                    "scalar uint XOR profile metadata mismatch")
            try:
                if self.program.key in PREPARED_SCALAR_UINT_XOR_KEYS:
                    self.authorized_scalar_uint_xors = (
                        authenticate_prepared_scalar_uint_xor(
                            self.program, self.source_hash,
                            self.scalar_uint_xor_profile))
                    # Noise's prepared scalar-XOR record deliberately has a
                    # separate float-bit ingress census. It has no Grain
                    # narrowing exception; keep the three authenticated
                    # float(uint) sites on the normal GLSL f32 path.
                    self.authorized_scalar_uint_narrowing_skip_nodes = ()
                    if self.program.key == NOISE_FLOAT_BITS_INGRESS_KEY:
                        self.authorized_noise_float_bits_ingresses = (
                            authenticate_prepared_noise_float_bits_ingress(
                                self.program, self.source_hash,
                                self.scalar_uint_xor_profile))
                else:
                    self.authorized_scalar_uint_xors = authenticate_scalar_uint_xor(
                        self.program, self.source_hash,
                        self.scalar_uint_xor_profile)
                    if self.program.key == NOISE_FLOAT_BITS_INGRESS_KEY:
                        # Noise owns its own ingress census and deliberately
                        # has no Grain narrowing exception. Its three exact
                        # float(uint) constructors remain on the normal f32
                        # path; do not ask the six-carrier Grain census to
                        # authenticate a seventh key.
                        self.authorized_scalar_uint_narrowing_skip_nodes = ()
                        self.authorized_noise_float_bits_ingresses = (
                            authenticate_noise_float_bits_ingress(
                                self.program, self.source_hash,
                                self.scalar_uint_xor_profile))
                    else:
                        self.authorized_scalar_uint_narrowing_skip_nodes = (
                            authenticate_scalar_uint_to_float_narrowing_skips(
                                self.program, self.source_hash,
                                self.scalar_uint_xor_profile))
                # kaleido's one `floatBitsToUint` ingress rides the same
                # carrier (the `_UINT_TO_FLOAT_CENSUS_LOCKS` precedent).
                self.authorized_kaleido_float_bits_ingress = (
                    authenticate_kaleido_float_bits_ingress(
                        self.program, self.source_hash,
                        self.scalar_uint_xor_profile)
                    if self.program.key == KALEIDO_FLOAT_BITS_INGRESS_KEY
                    else ())
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif ((self.program.key in SCALAR_UINT_XOR_KEYS
               or self.program.key in PREPARED_SCALAR_UINT_XOR_KEYS)
              and self.program.key not in BIT_EFFECTS_PREPARED_KEYS):
            raise _error(
                self.program, self.program,
                "exact scalar uint XOR profile carrier required")
        if self.mutable_global_frame_profile is not None:
            # The emitter is an INDEPENDENT authority. It re-authenticates the
            # closure from its own `source_hash` and never consults, trusts, or
            # reads anything the validator produced -- with
            # `validate_capabilities` monkeypatched to a no-op this block is
            # the only thing standing between a missing carrier and emitted
            # C++.
            frame_is_live = self.program.key in MUTABLE_GLOBAL_FRAME_KEYS
            frame_is_prepared_noise = (
                self.program.key in PREPARED_MUTABLE_GLOBAL_FRAME_KEYS)
            frame_is_noise = (self.program.key
                              == PREPARED_MUTABLE_GLOBAL_FRAME_NOISE_KEY)
            expected_frame_profile = (
                PREPARED_MUTABLE_GLOBAL_FRAME_NOISE_PROFILE
                if frame_is_prepared_noise
                else MUTABLE_GLOBAL_FRAME_PROFILES.get(self.program.key))
            if (not (frame_is_live or frame_is_prepared_noise)
                    or self.mutable_global_frame_profile != expected_frame_profile
                    or self.scalar_uint_xor_profile != SCALAR_UINT_XOR_PROFILE
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or (self.runtime_loop_bound_profile is not None
                        and not frame_is_noise)
                    or self.gabor_effective_depth_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.edge_bvec3_contour_profile is not None
                    or self.glitch_mat4_chain_profile is not None
                    or self.emboss_color_style_profile is not None
                    or self.shape_mixer_builtin_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.scanline_error_float_bits_ingress_profile is not None
                    or self.shapes_float_bits_ingress_profile is not None
                    or self.shapes_rvalue_assign_profile is not None
                    or self.glyph_map_nonnegative_int_shift_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.as_u32_round_profile is not None
                    or self.ceil_admission_profile is not None
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None
                    or self.mutable_global_array_profile is not None):
                raise _error(self.program, self.program,
                             "mutable-global frame profile metadata mismatch")
            try:
                if frame_is_prepared_noise:
                    self.authorized_mutable_global_frames = (
                        authenticate_prepared_mutable_global_frame(
                            self.program, self.source_hash,
                            self.mutable_global_frame_profile))
                    contract = prepared_frame_contract(self.program.key)
                else:
                    self.authorized_mutable_global_frames = (
                        authenticate_mutable_global_frame(
                            self.program, self.source_hash,
                            self.mutable_global_frame_profile))
                    contract = (dynamic_frame_contract(self.program)
                                if is_dynamic_program(self.program)
                                else mutable_global_frame_contract(self.program.key))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            # The closure returns BOTH declarations, by object identity, in the
            # frozen order `(aspectRatio, globalCoord)`; the contract's field
            # tuple is in the same order and each field carries its OWN numeric
            # contract. `aspectRatio` is a plain JS Number never narrowed to
            # f32; `globalCoord` is a `Float32Array` narrowed per lane. Emitting
            # them uniformly is wrong even where no test notices, so the field
            # types are taken per field from the contract and cross-checked
            # against the emitter's own `local_type()` convention below.
            if (len(self.authorized_mutable_global_frames)
                    != len(contract.fields)):
                raise _error(self.program, self.program,
                             "mutable-global frame carrier cardinality mismatch")
            for declaration, field_contract in zip(
                    self.authorized_mutable_global_frames, contract.fields):
                if (declaration.symbol.id != field_contract.symbol_id
                        or declaration.symbol.name != field_contract.name
                        or declaration.type.display() != field_contract.glsl_type
                        or self.local_type(declaration.type)
                        != field_contract.native_type):
                    raise _error(self.program, declaration,
                                 "mutable-global frame field contract mismatch")
                self.frame_fields[declaration.symbol.id] = (
                    f"{contract.instance_name}.{field_contract.name}")
            if len(self.frame_fields) != len(contract.fields):
                raise _error(self.program, self.program,
                             "mutable-global frame field contract mismatch")
            self.authorized_frame_contract = contract
        elif (self.program.key in MUTABLE_GLOBAL_FRAME_KEYS
              or self.program.key in PREPARED_MUTABLE_GLOBAL_FRAME_KEYS):
            raise _error(
                self.program, self.program,
                "exact mutable-global frame profile carrier required")
        if self.mutable_global_array_profile is not None:
            # The emitter is an INDEPENDENT authority (Amendment 12's whole
            # reason to exist): it re-authenticates the closure from its OWN
            # `source_hash` and never consults, trusts, or reads anything the
            # validator produced -- with `validate_capabilities` monkeypatched
            # to a no-op this block is the only thing standing between a
            # missing carrier and emitted C++. kaleido is the mechanism's one
            # two-carrier row: its required scalar-XOR companion is read from
            # the closure's own REQUIRED_COMPANION_PROFILES (the normalMap
            # pattern) -- present and exact for mapped keys, still rejected
            # for every unmapped key, so the carve fails closed.
            array_companions = dict(
                MUTABLE_GLOBAL_ARRAY_COMPANIONS.get(self.program.key, ()))
            # A companion's VALUE is its own block's authentication's
            # business; an absent companion is the owning block's
            # required-carrier elif's business (each mechanism names its own
            # message), and an unmapped companion is refused below.
            companion_row = {
                "scalar_uint_xor_profile": self.scalar_uint_xor_profile,
                "glitch_mat4_chain_profile": self.glitch_mat4_chain_profile,
                "ceil_admission_profile": self.ceil_admission_profile}
            if (self.program.key not in MUTABLE_GLOBAL_ARRAY_KEYS
                    or self.mutable_global_array_profile
                    != MUTABLE_GLOBAL_ARRAY_PROFILES.get(self.program.key)
                    or any(companion_row.get(name) != value
                           for name, value in array_companions.items())
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.runtime_loop_bound_profile is not None
                    or self.gabor_effective_depth_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or (self.scalar_uint_xor_profile is not None
                        and "scalar_uint_xor_profile" not in array_companions)
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.edge_bvec3_contour_profile is not None
                    or (self.glitch_mat4_chain_profile is not None
                        and "glitch_mat4_chain_profile"
                        not in array_companions)
                    or self.emboss_color_style_profile is not None
                    or self.shape_mixer_builtin_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.scanline_error_float_bits_ingress_profile is not None
                    or self.shapes_float_bits_ingress_profile is not None
                    or self.shapes_rvalue_assign_profile is not None
                    or self.mutable_global_frame_profile is not None
                    or self.glyph_map_nonnegative_int_shift_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.as_u32_round_profile is not None
                    or (self.ceil_admission_profile is not None
                        and "ceil_admission_profile" not in array_companions)
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None):
                raise _error(self.program, self.program,
                             "mutable-global array profile metadata mismatch")
            try:
                self.authorized_mutable_global_arrays = (
                    authenticate_mutable_global_array(
                        self.program, self.source_hash,
                        self.mutable_global_array_profile))
                contract = mutable_global_array_contract(self.program.key)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            # ALL FIVE declarations, by object identity, in the frozen
            # declaration order (ordinals 16-20); the contract's field tuple
            # is positional in the same order.
            if (len(self.authorized_mutable_global_arrays)
                    != len(contract.fields)):
                raise _error(self.program, self.program,
                             "mutable-global array carrier cardinality mismatch")
            proof = self.program.fixed_array_in_parameter_proof
            for declaration, field_contract in zip(
                    self.authorized_mutable_global_arrays, contract.fields):
                # The element alias is NOT re-derived here: the fixed-array
                # proof machinery owns `Kernel9`, and the contract's
                # `native_type` must name exactly the alias the proof
                # supplies -- a rename on either side turns this red.
                if (declaration.symbol.id != field_contract.symbol_id
                        or declaration.symbol.name != field_contract.name
                        or declaration.type.display() != field_contract.glsl_type
                        or proof is None
                        or proof.kernel_alias != field_contract.native_type):
                    raise _error(self.program, declaration,
                                 "mutable-global array field contract mismatch")
                self.array_frame_fields[declaration.symbol.id] = (
                    f"{contract.instance_name}.{field_contract.name}")
            if len(self.array_frame_fields) != len(contract.fields):
                raise _error(self.program, self.program,
                             "mutable-global array field contract mismatch")
            self.authorized_mutable_array_contract = contract
            # Resolve the frozen bare writer call ONCE, from the already
            # authenticated tree, so the expr-statement arm below can admit
            # EXACTLY that node by identity (Amendment 12: no generic
            # void-call admission).
            writers = [function for function in self.program.functions
                       if function.name == contract.writer_function]
            if len(writers) != 1 or not writers[0].body:
                raise _error(self.program, self.program,
                             "mutable-global array writer function mismatch")
            writer = writers[0]
            main = next((function for function in self.program.functions
                         if function.name == "main"), None)

            def _array_calls(node):
                if isinstance(node, TypedExpression):
                    if node.kind == "call":
                        yield node
                    for child in node.children:
                        yield from _array_calls(child)
                for expression in getattr(node, "expressions", ()):
                    yield from _array_calls(expression)
                for child in getattr(node, "children", ()):
                    yield from _array_calls(child)

            calls = [] if main is None else [
                call for statement in main.body
                for call in _array_calls(statement)
                if call.callee == writer.name
                and call.signature_id == writer.signature.id]
            if (len(calls) != 1 or calls[0].type.display() != "void"
                    or calls[0].children):
                raise _error(self.program, self.program,
                             "mutable-global array writer call mismatch")
            self.authorized_array_writer_call = calls[0]
            # The two rvalue compound assignments, resolved once. They live
            # in the unreachable caller-table helpers and are emitted anyway
            # (the proof vouches grammar, not liveness); an `expr`-statement
            # sole assignment is NOT one of them -- only assigns nested in a
            # larger expression (here: the operand of `return`) are.
            rvalue_assigns = []

            def _array_rvalue_assigns(node, statement):
                if isinstance(node, TypedExpression):
                    if node.kind == "assign" and not (
                            statement.kind == "expr"
                            and len(statement.expressions) == 1
                            and statement.expressions[0] is node):
                        rvalue_assigns.append(node)
                    for child in node.children:
                        _array_rvalue_assigns(child, statement)
                    return
                for expression in getattr(node, "expressions", ()):
                    _array_rvalue_assigns(expression, node)
                for child in getattr(node, "children", ()):
                    _array_rvalue_assigns(child, statement)

            for function in self.program.functions:
                for statement in function.body:
                    _array_rvalue_assigns(statement, statement)
            if (len(rvalue_assigns) != 2
                    or any(node.operator != "*=" or len(node.children) != 2
                           or node.children[0].kind != "id"
                           or node.children[0].type.display() != "vec3"
                           for node in rvalue_assigns)):
                raise _error(self.program, self.program,
                             "mutable-global array rvalue assignment mismatch")
            self.authorized_array_rvalue_assigns = tuple(rvalue_assigns)
        elif self.program.key in MUTABLE_GLOBAL_ARRAY_KEYS:
            raise _error(
                self.program, self.program,
                "exact mutable-global array profile carrier required")
        if self.const_global_table_profile is not None:
            # The emitter is an INDEPENDENT authority. It re-authenticates the
            # closure from its OWN `source_hash` and never consults, trusts, or
            # reads anything the validator produced -- Shapes183 passed the
            # validator and gapped here, which is why this is duplicated rather
            # than shared.
            companion_row = {
                "as_u32_round_profile": self.as_u32_round_profile}
            if (self.program.key not in CONST_GLOBAL_TABLE_KEYS
                    or self.const_global_table_profile
                    != CONST_GLOBAL_TABLE_PROFILES.get(self.program.key)
                    or any(companion_row.get(name) != value
                           for name, value in
                           CONST_GLOBAL_TABLE_COMPANIONS.get(
                               self.program.key, ()))
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.runtime_loop_bound_profile is not None
                    or self.gabor_effective_depth_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.edge_bvec3_contour_profile is not None
                    or self.glitch_mat4_chain_profile is not None
                    or self.emboss_color_style_profile is not None
                    or self.shape_mixer_builtin_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.scanline_error_float_bits_ingress_profile is not None
                    or self.shapes_float_bits_ingress_profile is not None
                    or self.shapes_rvalue_assign_profile is not None
                    or self.mutable_global_frame_profile is not None
                    or self.mutable_global_array_profile is not None
                    or self.glyph_map_nonnegative_int_shift_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.ceil_admission_profile is not None
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None):
                raise _error(self.program, self.program,
                             "const-global nine-table profile metadata mismatch")
            try:
                self.authorized_const_global_tables = (
                    authenticate_const_global_tables(
                        self.program, self.source_hash,
                        self.const_global_table_profile))
                self.authorized_const_global_table_reads = (
                    authenticate_const_global_table_reads(
                        self.program, self.source_hash,
                        self.const_global_table_profile))
                contract = const_global_table_contract(self.program.key)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            if (len(self.authorized_const_global_tables) != len(contract)
                    or len(self.authorized_const_global_table_reads)
                    != len(contract)):
                raise _error(self.program, self.program,
                             "const-global nine-table carrier cardinality mismatch")
            # Every emitted native fact is taken from the closure's contract,
            # per table, and cross-checked against the declaration it belongs
            # to. `_TYPES` is deliberately NOT widened with an array entry:
            # a flat `"ivec2[9]"` display-name key would make array types
            # generally emittable for every program in the slice.
            for declaration, table in zip(self.authorized_const_global_tables,
                                          contract):
                if (declaration.symbol.id != table.symbol_id
                        or declaration.symbol.name != table.name
                        or declaration.type.display() != table.glsl_type
                        or declaration.type.kind != "array"
                        or declaration.type.size != table.element_count
                        or declaration.type.element is None
                        or self.local_type(declaration.type.element)
                        != table.native_element_type):
                    raise _error(self.program, declaration,
                                 "const-global nine-table field contract mismatch")
            self.authorized_const_global_table_contract = contract
        elif self.program.key in CONST_GLOBAL_TABLE_KEYS:
            raise _error(
                self.program, self.program,
                "exact const-global nine-table profile carrier required")
        if self.varying_profile is not None:
            # The emitter is an INDEPENDENT authority (Amendment 12's whole
            # reason to exist): it re-authenticates the varying-uv closure
            # from its OWN `source_hash` and never consults, trusts, or reads
            # anything the validator produced. The mechanism is PURE
            # EXPRESSION LOWERING -- every read of the one interface symbol
            # lowers to the contract's frozen `context.uv` (a `glsl::Vec2`
            # lvalue already carried by `PixelContext`), the same `name()`
            # dispatcher arm shape as `gl_FragCoord` -> `context.frag_coord`.
            # No companion carrier exists, so every other profile must be
            # absent -- the strict form of the row schema's runtime half.
            if (self.program.key not in VARYING_UV_KEYS
                    or self.varying_profile
                    != VARYING_UV_PROFILES.get(self.program.key)
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.runtime_loop_bound_profile is not None
                    or self.gabor_effective_depth_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile
                    is not None
                    or self.edge_bvec3_contour_profile is not None
                    or self.glitch_mat4_chain_profile is not None
                    or self.emboss_color_style_profile is not None
                    or self.shape_mixer_builtin_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.scanline_error_float_bits_ingress_profile
                    is not None
                    or self.shapes_float_bits_ingress_profile is not None
                    or self.shapes_rvalue_assign_profile is not None
                    or self.mutable_global_frame_profile is not None
                    or self.mutable_global_array_profile is not None
                    or self.const_global_table_profile is not None
                    or self.glyph_map_nonnegative_int_shift_profile
                    is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.as_u32_round_profile is not None
                    or self.ceil_admission_profile is not None
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None):
                raise _error(self.program, self.program,
                             "varying-uv profile metadata mismatch")
            try:
                self.authorized_varyings = authenticate_varying_uv(
                    self.program, self.source_hash, self.varying_profile)
                contract = varying_uv_contract(self.program.key)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            # The ONE admitted interface symbol, by object identity, carrying
            # exactly the contract's frozen record. The lowering target is
            # asserted, not inherited, so a rename of `PixelContext::uv` in
            # the runtime headers (or of the contract) turns this red rather
            # than emitting a stale lvalue.
            if (len(self.authorized_varyings) != 1
                    or contract.symbol_id != self.authorized_varyings[0].id
                    or contract.name != self.authorized_varyings[0].name
                    or contract.glsl_type
                    != self.authorized_varyings[0].type.display()
                    or contract.kernel_signature_change != "none"
                    or contract.lowering_target != "context.uv"
                    or contract.native_type != "glsl::Vec2"):
                raise _error(self.program, self.program,
                             "varying-uv carrier cardinality or contract "
                             "mismatch")
            self.varying_fields[self.authorized_varyings[0].id] = (
                contract.lowering_target)
            if len(self.varying_fields) != 1:
                raise _error(self.program, self.program,
                             "varying-uv field contract mismatch")
            self.authorized_varying_contract = contract
        elif self.program.key in VARYING_UV_KEYS:
            raise _error(
                self.program, self.program,
                "exact varying-uv profile carrier required")
        elif self.authorized_spooky_ticker_proof is not None:
            symbol = self.authorized_spooky_ticker_proof.varying_symbol
            if (len(self.program.interface_symbols) != 1
                    or self.program.interface_symbols[0] is not symbol
                    or symbol.name != "v_texCoord"
                    or symbol.type.display() != "vec2"):
                raise _error(
                    self.program, self.program,
                    "SpookyTicker varying carrier cardinality mismatch")
            self.varying_fields[symbol.id] = "context.uv"
        if self.texture_lod_admission_profile is not None:
            # The emitter is an INDEPENDENT authority (Amendment 12's whole
            # reason to exist): it re-authenticates the textureLod identity
            # closure from its OWN `source_hash` and never consults, trusts,
            # or reads anything the validator produced. The mechanism is an
            # IDENTITY ALIAS -- glsl-runtime.js:400 drops the lod argument and
            # calls `this.#texture(surface, coord)` itself, so
            # `textureLod(s, uv, 0.0)` lowers through the existing
            # `sample_texture(s, uv)` path with no mip machinery anywhere.
            # parallax is the counted-for bucket's seed carrier as well, so
            # the source-global literal-int carrier is REQUIRED here (auto-
            # supplied from the loop-proof dict key) rather than forbidden --
            # every other profile must be absent, the strict form of the row
            # schema's runtime half.
            if (self.program.key not in TEXTURE_LOD_ADMISSION_KEYS
                    or self.texture_lod_admission_profile
                    != TEXTURE_LOD_ADMISSION_PROFILE
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile
                    != SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
                    or self.runtime_loop_bound_profile is not None
                    or self.gabor_effective_depth_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile
                    is not None
                    or self.edge_bvec3_contour_profile is not None
                    or self.glitch_mat4_chain_profile is not None
                    or self.emboss_color_style_profile is not None
                    or self.shape_mixer_builtin_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.scanline_error_float_bits_ingress_profile
                    is not None
                    or self.shapes_float_bits_ingress_profile is not None
                    or self.shapes_rvalue_assign_profile is not None
                    or self.mutable_global_frame_profile is not None
                    or self.mutable_global_array_profile is not None
                    or self.const_global_table_profile is not None
                    or self.glyph_map_nonnegative_int_shift_profile
                    is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None
                    or self.posterize_round_profile is not None
                    or self.as_u32_round_profile is not None
                    or self.ceil_admission_profile is not None
                    or self.waves_any_notequal_profile is not None
                    or self.inout_vec3_swap_profile is not None
                    or self.varying_profile is not None):
                raise _error(self.program, self.program,
                             "textureLod admission profile metadata mismatch")
            try:
                proof = authenticate_texture_lod_admission(
                    self.program, self.source_hash,
                    self.texture_lod_admission_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            # The TWO admitted call nodes, by object identity, exactly the
            # closure's own site census -- a third textureLod site anywhere
            # (global declaration initializers included, which the closure
            # itself walks) cannot reach the lowering arm below.
            self.authorized_texture_lod_sites = tuple(
                site.node for site in proof.sites)
        elif self.program.key in TEXTURE_LOD_ADMISSION_KEYS:
            raise _error(
                self.program, self.program,
                "exact textureLod admission profile carrier required")
        if self.testpattern_profile is not None:
            # Test Pattern owns three fixed arrays, four fixed index sites, and
            # one vector round site.  Keep this carrier source-bound and
            # profile-scoped: the generic array/type vocabulary remains
            # deliberately closed for every other typed program.
            profile_fields = (
                "compatibility_transform", "custom_comparer_profile",
                "source_global_literal_int_profile", "runtime_loop_bound_profile",
                "gabor_effective_depth_profile", "gather_sorted_round_profile",
                "literal_vec3_lane_index_profile", "smooth_edge_luma_weights_profile",
                "perlin_scalar_uint_xor_profile", "scalar_uint_xor_profile",
                "bitwise_scalar_int_ops_profile", "rotate_mat2_return_profile",
                "focus_blur_borrowed_sampler_profile",
                "extrude_bvec2_relational_reduction_profile",
                "edge_bvec3_contour_profile", "glitch_mat4_chain_profile",
                "emboss_color_style_profile", "shape_mixer_builtin_profile",
                "caustic_word_hash_profile", "scanline_error_float_bits_ingress_profile",
                "glyph_map_nonnegative_int_shift_profile", "curl_vector_math_profile",
                "grade_luma_weights_profile", "grade_index_expression_profile",
                "derivative_admission_profile", "linear_srgb_lane_index_profile",
                "reflect_admission_profile", "posterize_round_profile",
                "as_u32_round_profile", "ceil_admission_profile",
                "waves_any_notequal_profile", "inout_vec3_swap_profile",
                "out_inout_admission_profile", "log_admission_profile",
                "mandelbrot_sequential_dz_assignment_profile",
                "shapes_float_bits_ingress_profile", "grime_float_bits_ingress_profile",
                "shapes_rvalue_assign_profile", "mutable_global_frame_profile",
                "mutable_global_array_profile", "const_global_table_profile",
                "varying_profile", "texture_lod_admission_profile",
                "cross_lane_assignment_profile", "struct_declaration_profile",
            )
            if (self.program.key != TESTPATTERN_KEY
                    or self.testpattern_profile != TESTPATTERN_PROFILE
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(getattr(self, name) is not None
                           for name in profile_fields)):
                raise _error(self.program, self.program,
                             "Test Pattern profile metadata mismatch")
            if self.testpattern_frontend_proof is None:
                raise _error(
                    self.program, self.program,
                    "exact Test Pattern frontend proof carrier required")
            try:
                # Authenticate the current tree independently, then retain
                # the caller's proof so all later gates consume its live node
                # identities.  This rejects forged, foreign, stale, and
                # source-hash-mismatched proof objects without re-deriving the
                # emission authority from a second tree walk.
                expected_proof = authenticate_testpattern_frontend(
                    self.program, self.source_hash, self.testpattern_profile)
                if not _testpattern_proof_matches(
                        self.testpattern_frontend_proof, expected_proof):
                    raise ValueError(
                        "testpattern frontend proof identity mismatch")
                self.authorized_testpattern_proof = (
                    self.testpattern_frontend_proof)
                sample = next(
                    function for function in self.program.functions
                    if function.signature.id == 30
                    and function.name == "sampleGlyph")
                nodes = []
                def walk(node):
                    if isinstance(node, TypedExpression):
                        nodes.append(node)
                        for child in node.children:
                            walk(child)
                    else:
                        for expression in node.expressions:
                            walk(expression)
                        for child in node.children:
                            walk(child)
                for statement in sample.body:
                    walk(statement)
                glyph_index = self.authorized_testpattern_proof.dynamic_indexes[0].node
                shifts = tuple(
                    item for item in nodes
                    if item.kind == "binary" and item.operator == ">>"
                    and len(item.children) == 2
                    and item.children[0] is glyph_index)
                masks = tuple(
                    item for item in nodes
                    if item.kind == "binary" and item.operator == "&"
                    and len(item.children) == 2
                    and item.children[0] in shifts)
                if (len(shifts) != 1 or len(masks) != 1
                        or shifts[0].type.display() != "int"
                        or masks[0].type.display() != "int"):
                    raise _error(self.program, self.program,
                                 "Test Pattern glyph bitwise census mismatch")
                self.authorized_testpattern_glyph_shift = shifts[0]
                self.authorized_testpattern_glyph_mask = masks[0]
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == TESTPATTERN_KEY:
            raise _error(self.program, self.program,
                         "exact Test Pattern profile carrier required")
        elif self.testpattern_frontend_proof is not None:
            raise _error(self.program, self.program,
                         "Test Pattern frontend proof requires exact profile")
        if self.moodscape_frontend_profile is not None:
            profile_fields = tuple(
                name for name in self.__dataclass_fields__
                if name.endswith("_profile")
                and name != "moodscape_frontend_profile")
            if (self.program.key not in MOODSCAPE_PREPARED_KEYS
                    or self.moodscape_frontend_profile
                    != MOODSCAPE_PREPARED_PROFILES[self.program.key]
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(getattr(self, name) is not None
                           for name in profile_fields)
                    or self.testpattern_frontend_proof is not None):
                raise _error(self.program, self.program,
                             "Moodscape frontend profile metadata mismatch")
            try:
                self.authorized_moodscape_projection = (
                    authenticate_moodscape_projection(
                        self.program, self.source_hash,
                        self.moodscape_frontend_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in MOODSCAPE_PREPARED_KEYS:
            raise _error(self.program, self.program,
                         "exact Moodscape frontend profile carrier required")
        if self.osd_frontend_profile is not None:
            profile_fields = tuple(
                name for name in self.__dataclass_fields__
                if name.endswith("_profile")
                and name not in {"osd_frontend_profile"})
            if (self.program.key not in OSD_PREPARED_KEYS
                    or self.osd_frontend_profile
                    != OSD_PREPARED_PROFILES[self.program.key]
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(getattr(self, name) is not None
                           for name in profile_fields)
                    or self.testpattern_frontend_proof is not None):
                raise _error(self.program, self.program,
                             "OSD frontend profile metadata mismatch")
            try:
                self.authorized_osd_proof = authenticate_osd_frontend(
                    self.program, self.source_hash,
                    self.osd_frontend_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in OSD_PREPARED_KEYS:
            raise _error(self.program, self.program,
                         "exact OSD frontend profile carrier required")
        if self.spooky_ticker_frontend_profile is not None:
            profile_fields = tuple(
                name for name in self.__dataclass_fields__
                if name.endswith("_profile")
                and name != "spooky_ticker_frontend_profile")
            if (self.program.key not in SPOOKY_TICKER_PREPARED_KEYS
                    or self.spooky_ticker_frontend_profile
                    != SPOOKY_TICKER_PREPARED_PROFILES[self.program.key]
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(getattr(self, name) is not None
                           for name in profile_fields)
                    or self.testpattern_frontend_proof is not None):
                raise _error(
                    self.program, self.program,
                    "SpookyTicker frontend profile metadata mismatch")
            try:
                self.authorized_spooky_ticker_proof = (
                    authenticate_spooky_ticker_frontend(
                        self.program, self.source_hash,
                        self.spooky_ticker_frontend_profile))
                self.authorized_spooky_ticker_nodes = (
                    self.authorized_spooky_ticker_proof.bitwise_nodes)
                self.authorized_spooky_ticker_varying_reads = tuple(
                    item.node for item in
                    self.authorized_spooky_ticker_proof.varying_reads)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in SPOOKY_TICKER_PREPARED_KEYS:
            raise _error(
                self.program, self.program,
                "exact SpookyTicker frontend profile carrier required")
        if self.texture_frontend_profile is not None:
            profile_fields = tuple(
                name for name in self.__dataclass_fields__
                if name.endswith("_profile")
                and name != "texture_frontend_profile")
            if (self.program.key != TEXTURE_FRONTEND_KEY
                    or self.texture_frontend_profile != TEXTURE_FRONTEND_PROFILE
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(getattr(self, name) is not None
                           for name in profile_fields)
                    or self.testpattern_frontend_proof is not None):
                raise _error(self.program, self.program,
                             "Texture frontend profile metadata mismatch")
            try:
                proof = authenticate_texture_frontend(
                    self.program, self.source_hash,
                    self.texture_frontend_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
            symbol = proof.consumed_objects[0]
            if (len(self.program.interface_symbols) != 1
                    or self.program.interface_symbols[0] is not symbol):
                raise _error(self.program, self.program,
                             "Texture varying carrier cardinality mismatch")
            self.authorized_texture_frontend_nodes = proof.bitwise_nodes
            self.authorized_texture_frontend_assignments = proof.bitwise_assignments
            self.authorized_texture_frontend_inverse_sqrt = proof.inverse_sqrt
            self.authorized_texture_frontend_hash_conversion = (
                proof.number_preserving_hash_conversion)
            self.varying_fields[symbol.id] = "context.uv"
        if self.authorized_spooky_ticker_proof is not None:
            symbol = self.authorized_spooky_ticker_proof.varying_symbol
            if (len(self.program.interface_symbols) != 1
                    or self.program.interface_symbols[0] is not symbol):
                raise _error(
                    self.program, self.program,
                    "SpookyTicker varying carrier cardinality mismatch")
            self.varying_fields[symbol.id] = "context.uv"
        if self.remap_profile is not None:
            profile_fields = tuple(
                name for name in self.__dataclass_fields__
                if name.endswith("_profile") and name != "remap_profile")
            if (self.program.key != REMAP_KEY
                    or self.remap_profile != REMAP_PROFILE
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(getattr(self, name) is not None
                           for name in profile_fields)):
                raise _error(self.program, self.program,
                             "Remap profile metadata mismatch")
            if self.remap_frontend_proof is None:
                raise _error(
                    self.program, self.program,
                    "exact Remap frontend proof carrier required")
            try:
                expected_proof = authenticate_remap_frontend(
                    self.program, self.source_hash, self.remap_profile)
                if not _remap_proof_matches(
                        self.remap_frontend_proof, expected_proof):
                    raise ValueError("Remap frontend proof identity mismatch")
                self.authorized_remap_proof = self.remap_frontend_proof
                data_field = self.authorized_remap_proof.data_field
                if (data_field not in tuple(
                        field for block in self.program.uniform_blocks
                        for field in block.fields)
                        or data_field.name != "data"
                        or data_field.type.display() != "vec4[267]"
                        or data_field.id != 2):
                    raise ValueError("Remap data field identity mismatch")
            except (AttributeError, TypeError, ValueError) as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == REMAP_KEY:
            raise _error(
                self.program, self.program,
                "exact Remap profile carrier required")
        elif self.remap_frontend_proof is not None:
            raise _error(self.program, self.program,
                         "Remap frontend proof requires exact profile")
        if self.shape_mixer_builtin_profile is not None:
            collisions = (
                self.compatibility_transform, self.custom_comparer_profile,
                self.source_global_literal_int_profile,
                self.runtime_loop_bound_profile,
                self.gabor_effective_depth_profile,
                self.gather_sorted_round_profile,
                self.literal_vec3_lane_index_profile,
                self.smooth_edge_luma_weights_profile,
                self.perlin_scalar_uint_xor_profile,
                self.bitwise_scalar_int_ops_profile,
                self.rotate_mat2_return_profile,
                self.focus_blur_borrowed_sampler_profile,
                self.extrude_bvec2_relational_reduction_profile,
                self.edge_bvec3_contour_profile,
                self.glitch_mat4_chain_profile,
                self.emboss_color_style_profile,
                self.caustic_word_hash_profile,
                self.scanline_error_float_bits_ingress_profile,
                self.glyph_map_nonnegative_int_shift_profile,
                self.curl_vector_math_profile,
                self.grade_luma_weights_profile,
                self.grade_index_expression_profile,
                self.derivative_admission_profile,
                self.linear_srgb_lane_index_profile,
                self.reflect_admission_profile,
                self.posterize_round_profile,
                self.as_u32_round_profile,
                self.ceil_admission_profile,
                self.waves_any_notequal_profile,
                self.inout_vec3_swap_profile,
            )
            if (self.program.key != SHAPE_MIXER_KEY
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.scalar_uint_xor_profile != SCALAR_UINT_XOR_PROFILE
                    or any(item is not None for item in collisions)):
                raise _error(
                    self.program, self.program,
                    "Shape Mixer builtin profile metadata mismatch")
            try:
                self.authorized_shape_mixer_proof = (
                    authenticate_shape_mixer_builtin_closure(
                        self.program, self.source_hash,
                        self.shape_mixer_builtin_profile,
                        self.scalar_uint_xor_profile))
                proof = self.authorized_shape_mixer_proof
                self.candidate_shape_mixer_guards = (
                    _candidate_shape_mixer_blend_mode_guards(self.program))
                self.candidate_shape_mixer_ladders = (
                    _shape_mixer_ladder_records(self.program))
                expected_roots, expected_bodies = (
                    _candidate_shape_mixer_roots_and_bodies(self.program))
                record_roots = tuple(
                    item[0] for item in self.candidate_shape_mixer_ladders)
                record_guards = tuple(
                    guard for item in self.candidate_shape_mixer_ladders
                    for guard in item[1])
                record_bodies = tuple(
                    body for item in self.candidate_shape_mixer_ladders
                    for body in item[2])
                if (not _same_object_sequence(record_roots, expected_roots)
                        or not _same_object_sequence(
                            record_guards, self.candidate_shape_mixer_guards)
                        or not _same_object_sequence(
                            record_bodies, expected_bodies)):
                    raise ValueError(
                        "candidate Shape Mixer ladder record mismatch")
                if not _shape_mixer_proof_matches_candidate(
                        self.program, proof, self.authorized_scalar_uint_xors):
                    raise ValueError(
                        "candidate ownership, exceptional closure, or companion mismatch")
            except (AttributeError, TypeError, ValueError) as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == SHAPE_MIXER_KEY:
            raise _error(
                self.program, self.program,
                "exact Shape Mixer builtin profile carrier required")
        if self.bit_effects_frontend_profile is not None:
            collisions = (
                self.compatibility_transform, self.custom_comparer_profile,
                self.source_global_literal_int_profile,
                self.runtime_loop_bound_profile,
                self.gabor_effective_depth_profile,
                self.gather_sorted_round_profile,
                self.literal_vec3_lane_index_profile,
                self.smooth_edge_luma_weights_profile,
                self.perlin_scalar_uint_xor_profile,
                self.scalar_uint_xor_profile,
                self.bitwise_scalar_int_ops_profile,
                self.rotate_mat2_return_profile,
                self.focus_blur_borrowed_sampler_profile,
                self.extrude_bvec2_relational_reduction_profile,
                self.edge_bvec3_contour_profile,
                self.glitch_mat4_chain_profile,
                self.emboss_color_style_profile,
                self.shape_mixer_builtin_profile,
                self.caustic_word_hash_profile,
                self.scanline_error_float_bits_ingress_profile,
                self.shapes_float_bits_ingress_profile,
                self.grime_float_bits_ingress_profile,
                self.shapes_rvalue_assign_profile,
                self.mutable_global_frame_profile,
                self.mutable_global_array_profile,
                self.const_global_table_profile, self.varying_profile,
                self.texture_lod_admission_profile,
                self.cross_lane_assignment_profile,
                self.glyph_map_nonnegative_int_shift_profile,
                self.curl_vector_math_profile, self.grade_luma_weights_profile,
                self.grade_index_expression_profile,
                self.derivative_admission_profile,
                self.linear_srgb_lane_index_profile,
                self.reflect_admission_profile, self.posterize_round_profile,
                self.as_u32_round_profile, self.ceil_admission_profile,
                self.waves_any_notequal_profile, self.inout_vec3_swap_profile,
                self.out_inout_admission_profile,
                self.struct_declaration_profile,
                self.testpattern_frontend_proof, self.remap_frontend_proof)
            if (self.program.key not in BIT_EFFECTS_PREPARED_KEYS
                    or self.bit_effects_frontend_profile
                    != BIT_EFFECTS_PREPARED_PROFILES[self.program.key]
                    or self.numeric_literal_contract != "glsl-f32"
                    or any(item is not None for item in collisions)):
                raise _error(
                    self.program, self.program,
                    "BitEffects frontend profile metadata mismatch")
            try:
                self.authorized_bit_effects_proof = (
                    authenticate_bit_effects_frontend(
                        self.program, self.source_hash,
                        self.bit_effects_frontend_profile))
                self.authorized_bit_effects_nodes = (
                    self.authorized_bit_effects_proof.consumed_objects)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in BIT_EFFECTS_PREPARED_KEYS:
            raise _error(
                self.program, self.program,
                "exact BitEffects frontend profile carrier required")
        if self.bitwise_scalar_int_ops_profile is not None:
            if (self.program.key not in BITWISE_SCALAR_INT_OPS_KEYS
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None
                    or self.reflect_admission_profile is not None):
                raise _error(
                    self.program, self.program,
                    "Bitwise scalar int ops profile metadata mismatch")
            # Independent re-authentication; never trusts the validator.
            try:
                self.authorized_bitwise_number_proof = (
                    authenticate_bitwise_scalar_int_ops(
                        self.program, self.source_hash,
                        self.bitwise_scalar_int_ops_profile))
                self.authorized_bitwise_scalar_int_ops_sites = (
                    self.authorized_bitwise_number_proof.bitwise_nodes)
                self.authorized_bitwise_narrowing_skip_nodes = (
                    self.authorized_bitwise_number_proof.narrowing_skip_nodes)
                self.authorized_bitwise_float_identity_nodes = (
                    self.authorized_bitwise_number_proof.float_identity_nodes)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in BITWISE_SCALAR_INT_OPS_KEYS:
            raise _error(
                self.program, self.program,
                "exact Bitwise scalar int ops profile carrier required")
        if self.smooth_edge_luma_weights_profile is not None:
            if (self.program.key != SMOOTH_EDGE_KEY
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None):
                raise _error(
                    self.program, self.program,
                    "Smooth Edge LUMA weights profile metadata mismatch")
            try:
                (self.authorized_smooth_edge_luma_weights_declaration,
                 _) = authenticate_smooth_edge_luma_weights(
                     self.program, self.source_hash,
                     self.smooth_edge_luma_weights_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == SMOOTH_EDGE_KEY:
            raise _error(
                self.program, self.program,
                "exact Smooth Edge LUMA weights profile carrier required")
        if self.linear_srgb_lane_index_profile is not None:
            if (self.program.key not in LINEAR_SRGB_LANE_INDEX_KEYS
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None):
                raise _error(self.program, self.program,
                             "Linear sRGB lane index profile metadata mismatch")
            # Independent re-authentication. The emitter never trusts the
            # validator's result or a supplied proof object.
            try:
                self.authorized_linear_srgb_lane_index_sites = (
                    authenticate_linear_srgb_lane_index(
                        self.program, self.source_hash,
                        self.linear_srgb_lane_index_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key in LINEAR_SRGB_LANE_INDEX_KEYS:
            raise _error(self.program, self.program,
                         "exact Linear sRGB lane index profile carrier required")
        if self.reflect_admission_profile is not None:
            if (self.program.key != REFLECT_ADMISSION_KEY
                    or self.compatibility_transform is not None
                    or self.custom_comparer_profile is not None
                    or self.numeric_literal_contract != "glsl-f32"
                    or self.source_global_literal_int_profile is not None
                    or self.gather_sorted_round_profile is not None
                    or self.literal_vec3_lane_index_profile is not None
                    or self.smooth_edge_luma_weights_profile is not None
                    or self.perlin_scalar_uint_xor_profile is not None
                    or self.bitwise_scalar_int_ops_profile is not None
                    or self.rotate_mat2_return_profile is not None
                    or self.focus_blur_borrowed_sampler_profile is not None
                    or self.extrude_bvec2_relational_reduction_profile is not None
                    or self.caustic_word_hash_profile is not None
                    or self.curl_vector_math_profile is not None
                    or self.grade_luma_weights_profile is not None
                    or self.grade_index_expression_profile is not None
                    or self.derivative_admission_profile is not None
                    or self.linear_srgb_lane_index_profile is not None):
                raise _error(self.program, self.program,
                             "Reflect admission profile metadata mismatch")
            # Independent re-authentication. The emitter never trusts the
            # validator's result or a supplied proof object.
            try:
                self.authorized_reflect_node = authenticate_reflect_admission(
                    self.program, self.source_hash, self.reflect_admission_profile)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.program.key == REFLECT_ADMISSION_KEY:
            raise _error(self.program, self.program,
                         "exact Reflect admission profile carrier required")
        if self.literal_vec3_lane_index_profile is not None:
            if (self.program.key not in LITERAL_VEC3_LANE_INDEX_KEYS
                    or self.compatibility_transform is not None
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "literal vec3 lane profile metadata mismatch")
            try:
                self.authorized_literal_vec3_lane_sites = (
                    authenticate_literal_vec3_lane_index_post(
                        self.program, self.source_hash,
                        self.literal_vec3_lane_index_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif (self.program.key in LITERAL_VEC3_LANE_INDEX_KEYS
              or literal_source_key is not None):
            raise _error(self.program, self.program,
                         "exact literal vec3 lane profile carrier required")
        if self.program.key == LENS_CUSTOM_COMPARER_KEY:
            if (self.custom_comparer_profile != LENS_CUSTOM_COMPARER_PROFILE
                    or self.literal_vec3_lane_index_profile
                    != LITERAL_VEC3_LANE_INDEX_PROFILE
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "Lens custom comparer metadata mismatch")
            try:
                self.authorized_custom_comparer_predicate = (
                    authenticate_lens_custom_comparer_final(
                        self.program, self.source_hash,
                        self.custom_comparer_profile))
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.custom_comparer_profile is not None:
            raise _error(self.program, self.program,
                         "Lens custom comparer profile on foreign key")
        if self.program.key == CRT_KEY:
            if (self.compatibility_transform != CRT_COMPATIBILITY_TRANSFORM
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "CRT metadata carrier mismatch")
            try:
                authenticate_crt_metal_sine(self.program, self.source_hash)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.compatibility_transform == CRT_COMPATIBILITY_TRANSFORM:
            raise _error(self.program, self.program,
                         "CRT compatibility transform on foreign key")
        if self.program.key == SACRED_KEY:
            if (self.compatibility_transform != SACRED_COMPATIBILITY_TRANSFORM
                    or self.numeric_literal_contract != "glsl-f32"):
                raise _error(self.program, self.program,
                             "Sacred metadata carrier mismatch")
            try:
                authenticate_sacred_star_number_division(
                    self.program, self.source_hash)
            except ValueError as error:
                raise _error(self.program, self.program, str(error)) from error
        elif self.compatibility_transform == SACRED_COMPATIBILITY_TRANSFORM:
            raise _error(self.program, self.program,
                         "Sacred compatibility transform on foreign key")
        if (self.program.key in SOURCE_GLOBAL_LITERAL_INT_KEYS
                and self.source_hash != hashlib.sha256(
                    self.program.raw_source.encode("utf-8")).hexdigest()):
            raise _error(self.program, self.program,
                         "source-global literal-int caller source digest mismatch")
        try:
            canonical_pre = attach_counted_loop_proofs(
                self.program.functions, self.program.key)
            self.source_global_bounds = authenticate_source_global_literal_int(
                key=self.program.key, raw_source=self.program.raw_source,
                source=self.program.source,
                preprocessor_defines=self.program.preprocessor_defines,
                declarations=self.program.declarations, functions=canonical_pre,
                profile=self.source_global_literal_int_profile)
        except ValueError as error:
            raise _error(self.program, self.program, str(error)) from error
        self.uniforms = {item.symbol.id: item.symbol for item in self.program.declarations
                         if item.symbol.storage == "uniform"}
        self.outputs = {item.symbol.id: item.symbol for item in self.program.declarations
                        if item.symbol.storage == "output"}
        self.source_globals = {item.symbol.id: item for item in self.program.declarations
                               if item.symbol.storage == "const"}
        self.source_global_dependencies = {}
        self.function_names = {
            item.signature.id: _safe_identifier(item.name, item.signature.id)
            for item in self.program.functions
        }
        self.ordinary_array_return_signatures = {
            item.signature.id for item in self.program.functions
            if self._function_returns_integral_call_map(item)
        }
        self.mutated_symbol_ids = set()
        for function in self.program.functions:
            for statement in function.body:
                self._collect_mutated_symbols(statement)
        self.program_scope_symbol_ids = {item.symbol.id
                                         for item in self.program.declarations
                                         if item.symbol is not None}
        self.alias_declaration_symbol_ids: set[int] = set()
        self.alias_source_symbol_ids: set[int] = set()
        for function in self.program.functions:
            for statement in function.body:
                self._collect_pooled_vector_aliases(statement)
        self.locals: dict[int, str] = {}
        self._validate_counted_loops()
        self._validate_discarded_local_counter_proofs()
        self._validate_fixed_nine_tables()
        self._validate_fixed_grid_counter_store()
        self._validate_fixed_array_input_parameter()
        self._validate_fixed_affine_centers13()
        self._validate_source_globals()

    def _literal_lane_site(self, value: object) -> tuple[TypedExpression, int, str] | None:
        if not hasattr(self, "authorized_literal_vec3_lane_sites"):
            self.authorized_literal_vec3_lane_sites = ()
        return next((row for row in self.authorized_literal_vec3_lane_sites
                     if row[0] is value), None)

    def _attach_counted(self, functions):
        return attach_counted_loop_proofs(
            functions, self.program.key,
            source_global_bounds=self.source_global_bounds,
            runtime_scalar_bounds=(
                () if self.runtime_loop_contract is None
                or self.runtime_loop_contract.seed is None
                else (self.runtime_loop_contract.seed,)),
            runtime_lane_bounds=(
                () if self.runtime_loop_contract is None
                else self.runtime_loop_contract.lane_seeds))

    def _collect_mutated_symbols(self, statement: TypedStatement) -> None:
        if statement.kind == "expr" and len(statement.expressions) == 1:
            expression = statement.expressions[0]
            if expression.kind == "assign" and expression.children:
                target = expression.children[0]
                if target.kind == "swizzle" and target.children:
                    target = target.children[0]
                if target.symbol_id is not None:
                    self.mutated_symbol_ids.add(target.symbol_id)
            if (statement.counter_proof is not None and expression.kind == "post"
                    and len(expression.children) == 1
                    and expression.children[0].symbol_id is not None):
                self.mutated_symbol_ids.add(expression.children[0].symbol_id)
        for child in statement.children:
            self._collect_mutated_symbols(child)

    # The JavaScript authority materializes `vecN` locals as
    # `PooledFloat32Array`, and a declaration whose initializer is a bare
    # vector identifier -- `var prevUV = rayUV;` -- binds a REFERENCE to that
    # same array, not a copy. Whole-vector assignment is materialized in place
    # (`(rayUV[0] = ..., rayUV[1] = ..., rayUV)`), so a later write through
    # either name is visible through both. A value copy therefore diverges
    # from the authority the moment either name is written.
    #
    # This cost the port a shipped defect: `filter/parallax`'s ray-march
    # refinement, `rayUV = mix(rayUV, prevUV, w)`, is `mix(x, x, w) == x` --
    # a no-op -- in the authority, and the copy made it live in the port. See
    # DEFECTS-FOUND.md item 6 and
    # counted-for-parity/parallax190-alias-divergence.md.
    #
    # Scoped to what is measured and observable:
    #
    # * `vec2/vec3/vec4` only. Those are the types measured to materialize as
    #   `PooledFloat32Array`. `ivec`/`uvec`/`bvec`/`mat` are left alone rather
    #   than assumed -- extending this needs the materialization re-read.
    # * Local and parameter sources only. A binding-sourced alias
    #   (`var res = fullResolution;` in `synth/osc2d` and `synth/perlin`)
    #   would have to write through a `const State&` field, which this
    #   emission cannot express; that class is recorded, not handled.
    # * Only where a write makes the aliasing observable. Where neither name
    #   is ever written, a copy and an alias are indistinguishable and the
    #   existing emission is already correct, so nothing changes. This
    #   analysis is re-derived from the live program on every run, never
    #   frozen.
    _POOLED_VECTOR_TYPES = frozenset({"vec2", "vec3", "vec4"})

    def _collect_pooled_vector_aliases(self, statement: TypedStatement) -> None:
        if statement.kind == "decl":
            for declaration in statement.expressions:
                if (declaration.kind != "declaration"
                        or declaration.symbol_id is None
                        or len(declaration.children) != 1
                        or declaration.type.display() not in self._POOLED_VECTOR_TYPES):
                    continue
                source = declaration.children[0]
                if (source.kind != "id" or source.symbol_id is None
                        or source.type.display() != declaration.type.display()):
                    continue
                # Program-scope sources -- uniforms, outputs, const globals --
                # reach the kernel as `const State&` fields and cannot be
                # bound mutably. `synth/osc2d` and `synth/perlin` both do
                # `var res = fullResolution;` and then write `res` in place,
                # which in the authority writes through to the binding array
                # for the rest of the pass. That class is OUT of scope here
                # and recorded in DEFECTS-FOUND item 6; skipping keeps those
                # two rows exactly as they are today rather than half-fixing
                # them.
                if source.symbol_id in self.program_scope_symbol_ids:
                    continue
                if (declaration.symbol_id not in self.mutated_symbol_ids
                        and source.symbol_id not in self.mutated_symbol_ids):
                    continue
                self.alias_declaration_symbol_ids.add(declaration.symbol_id)
                self.alias_source_symbol_ids.add(source.symbol_id)
        for child in statement.children:
            self._collect_pooled_vector_aliases(child)

    def _validate_counted_loops(self) -> None:
        try:
            if self.noise_frontend_profile is not None:
                contract = authenticate_noise_runtime(
                    self.program, self.source_hash,
                    self.noise_frontend_profile)
                recomputed = attach_counted_loop_proofs(
                    clear_counted_loop_proofs(self.program.functions),
                    self.program.key,
                    runtime_scalar_bounds=(contract.seed,))
                summary = summarize_counted_loop_proofs(recomputed)
            elif self.fractal_frontend_profile is not None:
                profiled = apply_fractal_frontend(
                    self.program, self.source_hash,
                    self.fractal_frontend_profile)
                recomputed = profiled.functions
                summary = profiled.counted_loop_proof
            else:
                recomputed, summary = rebuild_authenticated_counted_loop_proofs(
                    self.program, self.source_global_literal_int_profile,
                    self.runtime_loop_bound_profile)
        except ValueError as error:
            raise _error(self.program, self.program, str(error)) from error
        if len(recomputed) != len(self.program.functions):
            raise _error(self.program, self.program, "malformed counted-for proof functions")

        effective_depth_limit = (
            self.gabor_effective_depth_contract.maximum_effective_depth
            if self.gabor_effective_depth_contract is not None else 3)

        def statement(actual: TypedStatement, expected: TypedStatement) -> None:
            if (actual.kind != expected.kind or actual.loop_proof != expected.loop_proof
                    or len(actual.children) != len(expected.children)):
                raise _error(self.program, actual, "malformed counted-for proof")
            proof = actual.loop_proof
            if proof is not None and (
                    proof.trip_count > COUNTED_FOR_V1_MAX_TRIP_COUNT or proof.lexical_depth > 3
                    or proof.effective_depth > effective_depth_limit
                    or proof.lexical_product > COUNTED_FOR_V1_MAX_LEXICAL_PRODUCT
                    or proof.entrypoint_charge > COUNTED_FOR_V1_MAX_ENTRYPOINT_CHARGE
                    or min(proof.trip_count, proof.lexical_depth, proof.effective_depth,
                           proof.lexical_product, proof.entrypoint_charge) < 0):
                raise _error(self.program, actual, "unsupported counted-for safety charge")
            for actual_child, expected_child in zip(actual.children, expected.children):
                statement(actual_child, expected_child)

        for actual_function, expected_function in zip(self.program.functions, recomputed):
            if (actual_function.signature.id != expected_function.signature.id
                    or len(actual_function.body) != len(expected_function.body)):
                raise _error(self.program, actual_function, "malformed counted-for proof function")
            for actual_statement, expected_statement in zip(actual_function.body,
                                                              expected_function.body):
                statement(actual_statement, expected_statement)
        if self.program.counted_loop_proof != summary:
            raise _error(self.program, self.program, "malformed counted-for program proof")
        if not summary.call_graph_acyclic:
            offender = next((function for function in recomputed if function.body), self.program)
            raise _error(self.program, offender, "unsupported counted-for program proof")
        testpattern_unproved_loop = (
            self.authorized_testpattern_proof is not None
            and summary.unproved_loop_count == 1
            and sum(
                1 for item in self.authorized_testpattern_proof.consumed_objects
                if getattr(item, "kind", None) == "for"
                and item.loop_proof is None) == 1)
        median_unproved_loop = (
            self.authorized_median_frontend_proof is not None
            and summary.unproved_loop_count == 4
            and len(self.authorized_median_frontend_proof.unproved_while_spans) == 4
            and len(self.authorized_median_frontend_proof.unproved_while_sha256) == 4)
        if ((summary.unproved_loop_count
             and not testpattern_unproved_loop and not median_unproved_loop)
                or summary.max_effective_depth > effective_depth_limit
                or summary.max_lexical_product > COUNTED_FOR_V1_MAX_LEXICAL_PRODUCT
                or summary.entrypoint_charge > COUNTED_FOR_V1_MAX_ENTRYPOINT_CHARGE):
            if ((summary.loop_count or summary.unproved_loop_count)
                    and not testpattern_unproved_loop and not median_unproved_loop):
                def first_loop(statements: tuple[TypedStatement, ...]) -> TypedStatement | None:
                    for statement_value in statements:
                        if statement_value.kind in {"for", "while", "dowhile"}:
                            return statement_value
                        nested = first_loop(statement_value.children)
                        if nested is not None:
                            return nested
                    return None

                offender = next((candidate for function in recomputed
                                 if (candidate := first_loop(function.body)) is not None), self.program)
                raise _error(self.program, offender, "unsupported counted-for program proof")

    def _validate_discarded_local_counter_proofs(self) -> None:
        if (self.program.key == COMPUTE_RANK_KEY
                and (self.source_hash != COMPUTE_RANK_RAW_SHA256
                     or hashlib.sha256(self.program.source.encode("utf-8")).hexdigest()
                     != COMPUTE_RANK_NORMALIZED_SHA256)):
            raise _error(self.program, self.program,
                         "source digest mismatch for discarded local counter")
        recomputed = attach_discarded_local_counter_proofs(
            self._attach_counted(self.program.functions),
            self.program.key)
        if len(recomputed) != len(self.program.functions):
            raise _error(self.program, self.program,
                         "malformed discarded local-counter proof functions")

        has_proof = False

        def statement(actual: TypedStatement, expected: TypedStatement) -> None:
            nonlocal has_proof
            if (actual.kind != expected.kind or len(actual.children) != len(expected.children)
                    or actual.counter_proof != expected.counter_proof):
                raise _error(self.program, actual,
                             "malformed discarded local-counter proof")
            has_proof = has_proof or actual.counter_proof is not None
            for actual_child, expected_child in zip(actual.children, expected.children):
                statement(actual_child, expected_child)

        for actual_function, expected_function in zip(self.program.functions, recomputed):
            if (actual_function.signature.id != expected_function.signature.id
                    or len(actual_function.body) != len(expected_function.body)):
                raise _error(self.program, actual_function,
                             "malformed discarded local-counter proof functions")
            for actual_statement, expected_statement in zip(actual_function.body,
                                                              expected_function.body):
                statement(actual_statement, expected_statement)
        if has_proof and self.program.key != COMPUTE_RANK_KEY:
            raise _error(self.program, self.program,
                         "malformed discarded local-counter proof key")

    def _validate_fixed_nine_tables(self) -> None:
        provenance = source_provenance_error(self.program, self.source_hash)
        if provenance is not None:
            raise _error(self.program, self.program, provenance)
        functions = attach_discarded_local_counter_proofs(
            self._attach_counted(self.program.functions),
            self.program.key)
        recomputed_program = dataclasses.replace(
            self.program, functions=functions, fixed_nine_table_proof=None)
        recomputed = prove_fixed_nine_local_tables(recomputed_program)
        if self.program.key in SOURCE_LOCKS:
            if recomputed is None or self.program.fixed_nine_table_proof != recomputed:
                raise _error(self.program, self.program,
                             "malformed fixed-nine whole-program profile")
        elif self.program.fixed_nine_table_proof is not None:
            raise _error(self.program, self.program, "malformed fixed-nine local-table proof key")

    def _validate_fixed_grid_counter_store(self) -> None:
        provenance = fixed_grid_source_provenance_error(
            self.program, self.source_hash)
        if provenance is not None:
            raise _error(self.program, self.program, provenance)
        functions = attach_discarded_local_counter_proofs(
            self._attach_counted(self.program.functions),
            self.program.key)
        base = dataclasses.replace(
            self.program, functions=functions, fixed_nine_table_proof=None,
            fixed_grid_counter_store_proof=None)
        fixed_nine = prove_fixed_nine_local_tables(base)
        recomputed = prove_fixed_grid_counter_store(
            dataclasses.replace(base, fixed_nine_table_proof=fixed_nine))
        if self.program.key in FIXED_GRID_SOURCE_LOCKS:
            if (recomputed is None
                    or self.program.fixed_grid_counter_store_proof != recomputed):
                raise _error(self.program, self.program,
                             "malformed fixed-grid whole-program profile")
        elif self.program.fixed_grid_counter_store_proof is not None:
            raise _error(self.program, self.program,
                         "malformed fixed-grid counter-store proof key")

    def _validate_fixed_array_input_parameter(self) -> None:
        provenance = fixed_array_source_provenance_error(
            self.program, self.source_hash)
        if provenance is not None:
            raise _error(self.program, self.program, provenance)
        functions = attach_discarded_local_counter_proofs(
            self._attach_counted(self.program.functions),
            self.program.key)
        base = dataclasses.replace(
            self.program, functions=functions, fixed_nine_table_proof=None,
            fixed_grid_counter_store_proof=None,
            fixed_array_in_parameter_proof=None)
        fixed_nine = prove_fixed_nine_local_tables(base)
        fixed_grid = prove_fixed_grid_counter_store(
            dataclasses.replace(base, fixed_nine_table_proof=fixed_nine))
        recomputed = prove_fixed_array_in_parameter(dataclasses.replace(
            base, fixed_nine_table_proof=fixed_nine,
            fixed_grid_counter_store_proof=fixed_grid))
        # Per-key since the `cellrefract-convolve-v1` record: the proof
        # module owns the key set, and the equality check is identical for
        # every member. Refract's behavior and message are unchanged.
        if self.program.key in FIXED_ARRAY_IN_PARAMETER_KEYS:
            if (recomputed is None
                    or self.program.fixed_array_in_parameter_proof != recomputed):
                raise _error(self.program, self.program,
                             "malformed fixed-array input-parameter profile")
        elif self.program.fixed_array_in_parameter_proof is not None:
            raise _error(self.program, self.program,
                         "malformed fixed-array input-parameter proof key")

    def _validate_fixed_affine_centers13(self) -> None:
        provenance = fixed_affine_source_provenance_error(
            self.program, self.source_hash)
        if provenance is not None:
            raise _error(self.program, self.program, provenance)
        functions = attach_discarded_local_counter_proofs(
            self._attach_counted(self.program.functions),
            self.program.key)
        base = dataclasses.replace(
            self.program, functions=functions, fixed_nine_table_proof=None,
            fixed_grid_counter_store_proof=None,
            fixed_array_in_parameter_proof=None,
            fixed_affine_centers13_proof=None)
        fixed_nine = prove_fixed_nine_local_tables(base)
        task18_program = dataclasses.replace(
            base, fixed_nine_table_proof=fixed_nine)
        fixed_grid = prove_fixed_grid_counter_store(task18_program)
        task19_program = dataclasses.replace(
            task18_program, fixed_grid_counter_store_proof=fixed_grid)
        fixed_array = prove_fixed_array_in_parameter(task19_program)
        task20_program = dataclasses.replace(
            task19_program, fixed_array_in_parameter_proof=fixed_array)
        try:
            fixed_affine = prove_fixed_affine_centers13(task20_program)
        except ValueError as error:
            raise _error(self.program, self.program, str(error)) from error
        if ((self.program.fixed_nine_table_proof,
             self.program.fixed_grid_counter_store_proof,
             self.program.fixed_array_in_parameter_proof)
                != (fixed_nine, fixed_grid, fixed_array)):
            raise _error(self.program, self.program,
                         "malformed predecessor fixed-array proof chain")
        if self.program.key == SACRED_KEY:
            if (fixed_affine is None
                    or self.program.fixed_affine_centers13_proof != fixed_affine):
                raise _error(self.program, self.program,
                             "malformed fixed-affine centers13 profile")
        elif self.program.fixed_affine_centers13_proof is not None:
            raise _error(self.program, self.program,
                         "malformed fixed-affine centers13 proof key")

    def _validate_source_globals(self) -> None:
        admitted: set[int] = set()
        admitted_literal_ints = {item[0] for item in self.source_global_bounds}
        for declaration in self.program.declarations:
            if declaration.symbol.storage in {"uniform", "output"}:
                continue
            if any(declaration is item
                   for item in getattr(
                       self, "authorized_mutable_global_frames", ())):
                # Admitted by exact node IDENTITY against what THIS emitter's
                # own call to `authenticate_mutable_global_frame` returned --
                # never by storage class, and never from the validator.
                #
                # Registered in a set of its own, deliberately not in
                # `admitted` and not in `self.source_globals` (which is the
                # `const` set): `audit_expression` below raises `write to
                # source const global` for any assignment whose base targets a
                # source global, and both of this program's authenticated
                # writes in `main` would be rejected by it.
                self.admitted_mutable_global_frames.append(declaration)
                continue
            if any(declaration is item
                   for item in getattr(
                       self, "authorized_mutable_global_arrays", ())):
                # Same identity idiom as the frame arm above, against what
                # THIS emitter's own call to `authenticate_mutable_global_array`
                # returned: the five mutable, uninitialised `float[9]` file
                # scope globals. Deliberately NOT registered in `admitted`
                # and not in `self.source_globals` (the const set): the
                # `write to source const global` audit below must never see
                # them, or all 45 authenticated stores in `loadKernels`
                # would be rejected. No dependency-set entry either -- there
                # are no initializers, and the closure freezes that empty.
                self.admitted_mutable_global_arrays.append(declaration)
                continue
            if any(declaration is item
                   for item in self.authorized_const_global_tables):
                # Mirrors generate_typed_slice.py's gate 1 with this emitter's
                # own mirrored grammar, admitted by exact node IDENTITY against
                # what THIS emitter's call to
                # `authenticate_const_global_tables` returned.
                #
                # Registered in `admitted` and left in `self.source_globals`
                # (the `const` set), the opposite of the mutable frame above:
                # these are genuinely `const`, so `audit_expression`'s `write
                # to source const global` barrier is exactly what is wanted.
                #
                # Its own dependency-set entry is mandatory, not cosmetic: a
                # literal-only initializer references nothing, and
                # `source_global_locals`'s closure walk indexes
                # `source_global_dependencies[...]` directly and raises
                # KeyError for a missing entry (design amendment S14).
                self.source_global_dependencies[declaration.symbol.id] = ()
                admitted.add(declaration.symbol.id)
                self.admitted_const_global_tables.append(declaration)
                continue
            testpattern = self._testpattern_array(declaration)
            if (testpattern is not None
                    and self.authorized_testpattern_proof is not None
                    and declaration.symbol.id
                    == self.authorized_testpattern_proof.global_array.symbol_id):
                if (declaration.symbol.storage != "const"
                        or declaration.type.display() != "int[10]"
                        or declaration.initializer is None):
                    raise _error(self.program, declaration,
                                 "malformed Test Pattern GLYPH global")
                self.source_global_dependencies[declaration.symbol.id] = ()
                admitted.add(declaration.symbol.id)
                continue
            osd = self._osd_array(declaration)
            if osd is not None and self.authorized_osd_proof is not None:
                if (declaration.symbol.storage != "const"
                        or declaration.type.display() != "int[80]"
                        or declaration.initializer is None):
                    raise _error(self.program, declaration,
                                 "malformed OSD GLYPHS global")
                self.source_global_dependencies[declaration.symbol.id] = ()
                admitted.add(declaration.symbol.id)
                continue
            if (self.authorized_spooky_ticker_proof is not None
                    and declaration.symbol.id
                    == self.authorized_spooky_ticker_proof.global_array.symbol_id):
                if (declaration.symbol.storage != "const"
                        or declaration.type.display() != "int[80]"
                        or declaration.initializer is None):
                    raise _error(self.program, declaration,
                                 "malformed SpookyTicker GLYPHS global")
                self.source_global_dependencies[declaration.symbol.id] = ()
                self.emitted_spooky_ticker_globals.append(declaration)
                admitted.add(declaration.symbol.id)
                continue
            historic = self.authorized_historic_palette_proof
            if (historic is not None
                    and declaration is historic.palettes_declaration):
                if (declaration.symbol.storage != "const"
                        or declaration.type.display() != "HistoricPalette[21]"
                        or declaration.initializer is not historic.palettes_initializer):
                    raise _error(self.program, declaration,
                                 "malformed authenticated Historic Palette global")
                self.source_global_dependencies[declaration.symbol.id] = ()
                admitted.add(declaration.symbol.id)
                continue
            palette = self.authorized_palette_frontend_proof
            if (palette is not None
                    and declaration is palette.palettes_declaration):
                if (declaration.symbol.storage != "const"
                        or declaration.type.display() != "PaletteEntry[55]"
                        or declaration.initializer is not palette.palettes_initializer):
                    raise _error(self.program, declaration,
                                 "malformed authenticated Palette global")
                self.source_global_dependencies[declaration.symbol.id] = ()
                admitted.add(declaration.symbol.id)
                continue
            if declaration is getattr(
                    self, "authorized_smooth_edge_luma_weights_declaration", None):
                self.source_global_dependencies[declaration.symbol.id] = ()
                admitted.add(declaration.symbol.id)
                continue
            if declaration is getattr(
                    self, "authorized_grade_luma_weights_declaration", None):
                self.source_global_dependencies[declaration.symbol.id] = ()
                admitted.add(declaration.symbol.id)
                continue
            proof = self.authorized_bit_effects_proof
            if (proof is not None and any(
                    declaration is item
                    for item in proof.global_const_declarations)):
                expected_index = len(self.emitted_bit_effects_globals)
                expected = proof.global_const_declarations
                if (expected_index >= len(expected)
                        or declaration is not expected[expected_index]
                        or declaration.symbol.storage != "const"
                        or declaration.type.display() != "int"
                        or declaration.initializer is None):
                    raise _error(
                        self.program, declaration,
                        "authenticated BitEffects global declaration mismatch")
                if expected_index == 0:
                    if (declaration.symbol.name != "BIT_COUNT"
                            or declaration.initializer.kind != "literal"):
                        raise _error(
                            self.program, declaration,
                            "authenticated BIT_COUNT initializer mismatch")
                else:
                    mask = declaration.initializer
                    if (declaration.symbol.name != "mask"
                            or mask.kind != "binary" or mask.operator != "-"
                            or len(mask.children) != 2
                            or mask.children[0] is not self.authorized_bit_effects_nodes[0]
                            or mask.children[0].kind != "binary"
                            or mask.children[0].operator != "<<"
                            or mask.children[0].type.display() != "int"):
                        raise _error(
                            self.program, declaration,
                            "authenticated BitEffects mask initializer mismatch")
                self.source_global_dependencies[declaration.symbol.id] = (
                    expected[0].symbol.id,) if expected_index else ()
                admitted.add(declaration.symbol.id)
                self.emitted_bit_effects_globals.append(declaration)
                continue
            if declaration.symbol.id in admitted_literal_ints:
                self.source_global_dependencies[declaration.symbol.id] = ()
                admitted.add(declaration.symbol.id)
                continue
            if (declaration.symbol.storage == "const"
                    and declaration.type.display() == "mat3"
                    and declaration.initializer is not None):
                # Mirrors generate_typed_slice.py's mat3 global admission --
                # the only shape present anywhere in the corpus:
                # `const mat3 NAME = mat3(<9 float literals>);`.
                def mat3_literal_component(child) -> bool:
                    if (child.kind == "unary" and child.operator == "-"
                            and len(child.children) == 1):
                        child = child.children[0]
                    return (child.kind == "literal" and child.type.display() == "float"
                            and child.literal is not None
                            and child.literal_value is not None)

                mat3_initializer = declaration.initializer
                if (mat3_initializer.kind != "construct"
                        or mat3_initializer.type.display() != "mat3"
                        or len(mat3_initializer.children) != 9
                        or any(not mat3_literal_component(child)
                               for child in mat3_initializer.children)):
                    raise _error(self.program, declaration,
                                 "unsupported mat3 source global initializer")
                self.source_global_dependencies[declaration.symbol.id] = ()
                admitted.add(declaration.symbol.id)
                continue
            if (declaration.symbol.storage == "const"
                    and declaration.type.display() in {"int", "uint"}
                    and declaration.initializer is not None
                    and declaration.initializer.kind == "literal"):
                # Mirrors generate_typed_slice.py's const int/uint literal
                # admission -- exact values, no narrowing risk, no
                # dependency edges (a bare literal references nothing).
                literal = declaration.initializer
                if literal.literal is None or literal.literal_value is None:
                    raise _error(self.program, declaration,
                                 "malformed source const global initializer")
                self.source_global_dependencies[declaration.symbol.id] = ()
                admitted.add(declaration.symbol.id)
                continue
            if (declaration.symbol.storage == "const"
                    and declaration.type.display() == "vec3"
                    and declaration.initializer is not None):
                # Mirrors generate_typed_slice.py's const vec3 admission.
                vec3_initializer = declaration.initializer
                if (vec3_initializer.kind != "construct"
                        or vec3_initializer.type.display() != "vec3"
                        or len(vec3_initializer.children) != 3):
                    raise _error(self.program, declaration,
                                 "unsupported vec3 source global initializer")
                vec3_dependencies: list[int] = []

                def vec3_component(value: TypedExpression) -> None:
                    if value.type.display() != "float":
                        raise _error(self.program, value,
                                     "unsupported source const global initializer type")
                    if value.kind == "literal":
                        if value.literal is None or value.literal_value is None:
                            raise _error(self.program, value,
                                         "malformed source const global initializer")
                        return
                    if value.kind == "id":
                        dependency = self.source_globals.get(value.symbol_id)
                        if (value.symbol_id not in admitted or value.symbol is None
                                or value.symbol.id != value.symbol_id
                                or dependency is None
                                or dependency.type.display() != "float"):
                            raise _error(
                                self.program, value,
                                "source const global dependency must name an earlier admitted const float")
                        if value.symbol_id not in vec3_dependencies:
                            vec3_dependencies.append(value.symbol_id)
                        return
                    if (value.kind == "swizzle" and value.children
                            and value.member is not None and len(value.member) == 1):
                        base = value.children[0]
                        dependency = (self.source_globals.get(base.symbol_id)
                                      if base.kind == "id" else None)
                        if (base.kind != "id" or base.symbol_id not in admitted
                                or base.symbol is None or base.symbol.id != base.symbol_id
                                or dependency is None or dependency.type.display() != "vec3"):
                            raise _error(
                                self.program, value,
                                "source const global swizzle dependency must name an earlier admitted const vec3")
                        if base.symbol_id not in vec3_dependencies:
                            vec3_dependencies.append(base.symbol_id)
                        return
                    if value.kind == "unary" and value.operator in {"+", "-"} and len(value.children) == 1:
                        vec3_component(value.children[0])
                        return
                    if value.kind == "binary" and value.operator in {"+", "-", "*", "/"} and len(value.children) == 2:
                        vec3_component(value.children[0])
                        vec3_component(value.children[1])
                        return
                    raise _error(self.program, value, "unsupported source const global initializer")

                for component in vec3_initializer.children:
                    vec3_component(component)
                self.source_global_dependencies[declaration.symbol.id] = tuple(vec3_dependencies)
                admitted.add(declaration.symbol.id)
                continue
            if (declaration.symbol.storage != "const" or declaration.type.display() != "float"
                    or declaration.initializer is None):
                raise _error(self.program, declaration, "unsupported source global declaration")
            dependencies: list[int] = []

            def initializer(value: TypedExpression) -> None:
                if value.type.display() != "float":
                    raise _error(self.program, value, "unsupported source const global initializer type")
                if value.kind == "literal":
                    if value.literal is None or value.literal_value is None:
                        raise _error(self.program, value, "malformed source const global initializer")
                    return
                if value.kind == "id":
                    if (value.symbol_id not in admitted or value.symbol is None
                            or value.symbol.id != value.symbol_id):
                        raise _error(
                            self.program, value,
                            "source const global dependency must name an earlier admitted declaration")
                    if value.symbol_id not in dependencies:
                        dependencies.append(value.symbol_id)
                    return
                if value.kind == "unary" and value.operator in {"+", "-"}:
                    if len(value.children) != 1:
                        raise _error(self.program, value, "malformed source const global initializer")
                    initializer(value.children[0])
                    return
                if value.kind == "binary" and value.operator in {"+", "-", "*", "/"}:
                    if len(value.children) != 2:
                        raise _error(self.program, value, "malformed source const global initializer")
                    initializer(value.children[0])
                    initializer(value.children[1])
                    return
                raise _error(self.program, value, "unsupported source const global initializer")

            initializer(declaration.initializer)
            self.source_global_dependencies[declaration.symbol.id] = tuple(dependencies)
            admitted.add(declaration.symbol.id)

        def targets_source_global(value: TypedExpression) -> bool:
            if value.kind == "id":
                return value.symbol_id in self.source_globals
            return (value.kind in {"swizzle", "index", "member"} and bool(value.children)
                    and targets_source_global(value.children[0]))

        def audit_expression(value: TypedExpression) -> None:
            if (value.kind == "assign" and value.children
                    and targets_source_global(value.children[0])):
                raise _error(self.program, value, "write to source const global")
            if (value.kind in {"unary", "post"} and value.operator in {"++", "--"}
                    and value.children and targets_source_global(value.children[0])):
                raise _error(self.program, value, "write to source const global")
            for child in value.children:
                audit_expression(child)

        def audit_statement(value: TypedStatement) -> None:
            for expression_value in value.expressions:
                audit_expression(expression_value)
            for child in value.children:
                audit_statement(child)

        for function in self.program.functions:
            for statement in function.body:
                audit_statement(statement)

        if getattr(self, "authorized_mutable_global_frames", ()):
            visited = self.admitted_mutable_global_frames
            if (len(visited) != len(self.authorized_mutable_global_frames)
                    or any(item is not expected for item, expected in zip(
                        visited, self.authorized_mutable_global_frames))):
                raise _error(
                    self.program, self.program,
                    "authenticated mutable-global frame admission "
                    "visitation mismatch")
        if getattr(self, "authorized_mutable_global_arrays", ()):
            visited = self.admitted_mutable_global_arrays
            if (len(visited) != len(self.authorized_mutable_global_arrays)
                    or any(item is not expected for item, expected in zip(
                        visited, self.authorized_mutable_global_arrays))):
                raise _error(
                    self.program, self.program,
                    "authenticated mutable-global array admission "
                    "visitation mismatch")

        if self.authorized_const_global_tables:
            visited = self.admitted_const_global_tables
            if (len(visited) != len(self.authorized_const_global_tables)
                    or any(item is not expected for item, expected in zip(
                        visited, self.authorized_const_global_tables))):
                raise _error(
                    self.program, self.program,
                    "authenticated const-global nine-table admission "
                    "visitation mismatch")

    @staticmethod
    def _referenced_symbols(statements: tuple[TypedStatement, ...]) -> set[int]:
        result: set[int] = set()

        def expression(value: TypedExpression) -> None:
            if value.kind == "id" and value.symbol_id is not None:
                result.add(value.symbol_id)
            for child in value.children:
                expression(child)

        def statement(value: TypedStatement) -> None:
            for expression_value in value.expressions:
                expression(expression_value)
            for child in value.children:
                statement(child)

        for item in statements:
            statement(item)
        return result

    def _const_global_table(self, symbol_id: int | None):
        """The frozen contract row for an authenticated table, or None.

        Paired by position with `authorized_const_global_tables`, whose
        declaration identity is what actually authorizes anything -- the
        contract only supplies the native spellings.
        """
        for declaration, table in zip(self.authorized_const_global_tables,
                                      self.authorized_const_global_table_contract):
            if (declaration.symbol.id == symbol_id
                    and table.symbol_id == symbol_id):
                return declaration, table
        return None

    def _const_global_table_constructor(self, value: TypedExpression):
        """The contract row whose declaration's initializer IS ``value``."""
        for declaration, table in zip(self.authorized_const_global_tables,
                                      self.authorized_const_global_table_contract):
            if declaration.initializer is value:
                return declaration, table
        return None

    def _testpattern_array(self, value):
        proof = self.authorized_testpattern_proof
        if proof is None:
            return None
        if (getattr(value, "symbol", None) is not None
                and value.symbol.id == proof.global_array.symbol_id):
            return proof.global_array
        for declaration in proof.consumed_objects:
            if (getattr(declaration, "kind", None) == "declaration"
                    and declaration.type.kind == "array"
                    and declaration.symbol.name in {"digits", "colors"}
                    and value is declaration):
                return declaration
        return None

    def _osd_array(self, value):
        proof = self.authorized_osd_proof
        if proof is None:
            return None
        if (getattr(value, "symbol", None) is not None
                and value.symbol.id == proof.global_array.symbol_id):
            return proof.global_array
        return None

    def _spooky_ticker_array(self, value):
        proof = self.authorized_spooky_ticker_proof
        if proof is None:
            return None
        if (getattr(value, "symbol", None) is not None
                and value.symbol.id == proof.global_array.symbol_id):
            return proof.global_array
        return None

    def _osd_index(self, value: TypedExpression) -> bool:
        proof = self.authorized_osd_proof
        if proof is None or value is not proof.consumed_objects[2]:
            return False
        if (len(value.children) != 2
                or value.children[0].kind != "id"
                or value.children[0].symbol_id != proof.global_array.symbol_id):
            raise _error(self.program, value,
                         "malformed authenticated OSD GLYPHS index")
        if value in self.emitted_osd_indexes:
            raise _error(self.program, value,
                         "authenticated OSD index emitted twice")
        self.emitted_osd_indexes.append(value)
        return True

    def _osd_js_number_declaration(self, declaration) -> bool:
        """Admit only OSD locals whose frozen factory stays a JS Number."""
        proof = self.authorized_osd_proof
        if proof is None or declaration.type.display() != "int":
            return False
        if self.current_function_name == "main":
            authorized = {
                (64, "glyph_idx", 156, 13),
                (65, "within_glyph_x", 157, 13),
            }
        elif self.current_function_name == "sample_glyph":
            authorized = {
                (76, "gx", 68, 9),
                (77, "gy", 69, 9),
            }
        else:
            return False
        return (declaration.symbol.id, declaration.symbol.name,
                declaration.span.start_line, declaration.span.start_column) in authorized

    def _spooky_ticker_index(self, value: TypedExpression) -> bool:
        proof = self.authorized_spooky_ticker_proof
        if proof is None or value is not proof.array_index:
            return False
        if (len(value.children) != 2
                or value.children[0].kind != "id"
                or value.children[0].symbol_id != proof.global_array.symbol_id):
            raise _error(self.program, value,
                         "malformed authenticated SpookyTicker GLYPHS index")
        if value in self.emitted_spooky_ticker_indexes:
            raise _error(self.program, value,
                         "authenticated SpookyTicker index emitted twice")
        self.emitted_spooky_ticker_indexes.append(value)
        return True

    def _median_array(self, value):
        proof = self.authorized_median_frontend_proof
        if proof is None:
            return None
        if not any(value is item for item in proof.array_declarations):
            return None
        if (value.kind != "declaration" or value.symbol is None
                or value.symbol.id not in {23, 24}
                or value.type.display() not in {"uvec2[25]", "uint[25]"}
                or value.children):
            raise _error(self.program, value,
                         "malformed authenticated Median fixed-array declaration")
        return value

    def _median_index(self, value: TypedExpression) -> bool:
        proof = self.authorized_median_frontend_proof
        if proof is None or not any(value is item for item in proof.array_indexes):
            return False
        if (len(value.children) != 2 or value.children[0].kind != "id"
                or value.children[0].symbol_id not in {23, 24}
                or value.children[0].type.display()
                not in {"uvec2[25]", "uint[25]"}
                or value.children[1].kind != "id"):
            raise _error(self.program, value,
                         "malformed authenticated Median fixed-array index")
        if value in self.emitted_median_indexes:
            raise _error(self.program, value,
                         "authenticated Median index emitted twice")
        self.emitted_median_indexes.append(value)
        return True

    def _median_while(self, value: TypedStatement) -> bool:
        proof = self.authorized_median_frontend_proof
        if proof is None:
            return False
        span = value.span
        span_key = (f"{span.start_line}:{span.start_column}-"
                    f"{span.end_line}:{span.end_column}")
        expected = len(self.emitted_median_whiles)
        if (value.kind != "while" or expected >= len(proof.unproved_while_spans)
                or span_key != proof.unproved_while_spans[expected]):
            return False
        self.emitted_median_whiles.append(value)
        return True

    def _testpattern_index(self, value: TypedExpression) -> bool:
        proof = self.authorized_testpattern_proof
        if proof is None:
            return False
        records = (*proof.dynamic_indexes, proof.digit_store_index)
        record = next((item for item in records if value is item.node), None)
        if record is None:
            return False
        def index_ids(node):
            if node.kind == "id" and node.symbol_id is not None:
                yield node.symbol_id
            for child in node.children:
                yield from index_ids(child)
        if (len(value.children) != 2
                or value.children[0].kind != "id"
                or value.children[0].symbol_id != record.array_symbol_id
                or tuple(index_ids(value.children[1]))
                != record.index_symbol_ids):
            raise _error(self.program, value,
                         "malformed authenticated Test Pattern index")
        if value in self.emitted_testpattern_indexes:
            raise _error(self.program, value,
                         "authenticated Test Pattern index emitted twice")
        self.emitted_testpattern_indexes.append(value)
        return True

    def _remap_index(self, value: TypedExpression) -> bool:
        proof = self.authorized_remap_proof
        if proof is None:
            return False
        record = next((item for item in proof.indexes if value is item.node), None)
        if record is None:
            return False
        if (len(value.children) != 2
                or value.children[0].kind != "id"
                or value.children[0].symbol_id != record.base_symbol_id
                or value.children[0].type.display() != record.base_type
                or value.children[1].type.display() != record.index_type
                or ("binary" if value.children[1].kind == "binary"
                    else "literal" if value.children[1].kind == "literal"
                    else value.children[1].kind) != record.index_shape
                or (value.children[1].operator if value.children[1].kind == "binary"
                    else None) != record.index_operator
                or (value.children[1].literal_value
                    if value.children[1].kind == "literal" else None)
                != record.index_literal):
            raise _error(self.program, value,
                         "malformed authenticated Remap data index")
        if any(value is item for item in self.emitted_remap_indexes):
            raise _error(self.program, value,
                         "authenticated Remap data index emitted twice")
        self.emitted_remap_indexes.append(value)
        return True

    def _const_global_table_double_element(self, value: TypedExpression) -> str:
        """One ``double`` table element, as a plain double literal.

        Deliberately NOT routed through the generic literal path, which under
        `glsl-f32` emits `static_cast<float>(...)`. The shipped JavaScript
        holds these in a plain `Array` of Numbers (`canonical-kernels.js`
        `var SOBEL_X_KERNEL = [0.5, 0, -0.5, ...]`), never a `Float32Array`,
        so there is no narrowing boundary to reproduce here. The f32 contract
        belongs to the `round` site in the same program and must not leak onto
        the tables.
        """
        sign = ""
        literal = value
        if (literal.kind == "unary" and literal.operator in {"+", "-"}
                and len(literal.children) == 1):
            sign = "-" if literal.operator == "-" else ""
            literal = literal.children[0]
        if (literal.kind != "literal" or literal.type.display() != "float"
                or literal.literal is None or literal.literal_value is None):
            raise _error(self.program, value,
                         "malformed authenticated const global table element")
        try:
            parsed = float(literal.literal)
        except ValueError as error:
            raise _error(self.program, value,
                         "malformed authenticated const global table element") from error
        # The source spelling must round-trip to the value the frontend
        # recorded, so the emitted C++ literal cannot drift from the IR.
        if parsed != literal.literal_value:
            raise _error(self.program, value,
                         "malformed authenticated const global table element")
        return f"{sign}{literal.literal}"

    def _palette_plain_number_literal(
            self, value: TypedExpression, *, profile_name: str) -> str:
        """Emit one authenticated palette-table Number literal without f32."""
        if (value.kind != "literal" or value.type.display() != "float"
                or value.literal is None or value.literal_value is None):
            raise _error(self.program, value,
                         f"malformed {profile_name} plain-number literal")
        return self._const_global_table_double_element(value)

    def _palette_plain_number_vector(
            self, value: TypedExpression, *, width: int, proof: object,
            vectors: list[TypedExpression],
            literals: list[TypedExpression], profile_name: str) -> str:
        """Emit an authenticated table vec as a double-backed FloatExpr."""
        expected = proof.vec3_constructors if width == 3 else proof.vec4_constructors
        expected_literals = proof.palette_literals
        if (not any(value is item for item in expected)
                or value.type.display() != f"vec{width}"
                or len(value.children) != width
                or any(child.kind != "literal" for child in value.children)):
            raise _error(self.program, value,
                         f"malformed {profile_name} plain-number vector")
        if any(value is item for item in vectors):
            raise _error(self.program, value,
                         f"duplicate {profile_name} plain-number vector")
        vectors.append(value)
        emitted = []
        for child in value.children:
            if not any(child is item for item in expected_literals):
                raise _error(self.program, child,
                             f"unauthenticated {profile_name} table literal")
            if any(child is item for item in literals):
                raise _error(self.program, child,
                             f"duplicate {profile_name} table literal")
            literals.append(child)
            emitted.append(self._palette_plain_number_literal(
                child, profile_name=profile_name))
        return f"glsl::FloatExpr<{width}>({', '.join(emitted)})"

    def source_global_locals(self, statements: tuple[TypedStatement, ...], indent: str = "  ") -> list[str]:
        needed = self._referenced_symbols(statements) & self.source_globals.keys()
        closure = set(needed)
        pending = list(needed)
        while pending:
            for dependency in self.source_global_dependencies[pending.pop()]:
                if dependency not in closure:
                    closure.add(dependency)
                    pending.append(dependency)
        lines: list[str] = []
        for declaration in self.program.declarations:
            symbol_id = declaration.symbol.id
            if symbol_id not in closure:
                continue
            self.locals[symbol_id] = _safe_identifier(
                declaration.symbol.name, symbol_id)
            palette = self.authorized_palette_frontend_proof
            if (palette is not None
                    and declaration is palette.tau_declaration):
                if declaration.initializer is not palette.tau_initializer:
                    raise _error(self.program, declaration,
                                 "malformed authenticated Palette TAU initializer")
                self.emitted_palette_tau_sites.extend(
                    (declaration, declaration.initializer))
                initializer = self._palette_plain_number_literal(
                    declaration.initializer, profile_name="Palette TAU")
            else:
                initializer = (declaration.initializer.literal
                               if (declaration.type.display() == "int"
                                   and declaration.initializer.kind == "literal")
                               else self.expression(declaration.initializer))
            historic = self.authorized_historic_palette_proof
            if (historic is not None
                    and declaration is historic.palette_count_declaration):
                self.emitted_historic_palette_counts.extend(
                    (declaration, historic.palette_count_initializer))
            if (palette is not None
                    and declaration is palette.palette_count_declaration):
                self.emitted_palette_counts.extend(
                    (declaration, palette.palette_count_initializer))
            # An admitted const array global takes its native type name from
            # the closure's frozen alias, never from `local_type()`/`_TYPES`
            # (which has no array entry and must not grow one).
            table = self._const_global_table(symbol_id)
            if table is None:
                testpattern = self._testpattern_array(declaration)
                if (testpattern is not None
                        and declaration.symbol.id
                        == self.authorized_testpattern_proof.global_array.symbol_id):
                    type_name = "std::array<std::int32_t, 10>"
                else:
                    osd = self._osd_array(declaration)
                    if (osd is not None):
                        type_name = "std::array<std::int32_t, 80>"
                    elif self._spooky_ticker_array(declaration) is not None:
                        type_name = "std::array<std::int32_t, 80>"
                    elif (self.authorized_historic_palette_proof is not None
                          and declaration is self.authorized_historic_palette_proof.palettes_declaration):
                        type_name = "std::array<HistoricPalette, 21>"
                    elif (self.authorized_palette_frontend_proof is not None
                          and declaration is self.authorized_palette_frontend_proof.palettes_declaration):
                        type_name = "std::array<PaletteEntry, 55>"
                    else:
                        type_name = self.local_type(declaration.type)
            else:
                type_name = table[1].native_alias
                self.emitted_const_global_table_locals.append(declaration)
            testpattern = self._testpattern_array(declaration)
            if testpattern is not None:
                self.emitted_testpattern_arrays.append(declaration)
            if self._osd_array(declaration) is not None:
                self.emitted_osd_array.append(declaration)
            if self._spooky_ticker_array(declaration) is not None:
                self.emitted_spooky_ticker_array.append(declaration)
            lines.append(
                f"{indent}const {type_name} {declaration.symbol.name} = "
                f"{initializer};")
        return lines

    def type(self, value: object) -> str:
        name = value.display()
        if name == "mat4" and self.authorized_glitch_proof is not None:
            return "glsl::Mat4"
        if (name == "POIData"
                and self.authorized_struct_declaration
                and self.authorized_struct_declaration[0].name == "POIData"):
            return "POIData"
        if name in {"HistoricPalette", "PaletteEntry"}:
            if ((name == "HistoricPalette"
                 and self.authorized_historic_palette_proof is not None)
                    or (name == "PaletteEntry"
                        and self.authorized_palette_frontend_proof is not None)):
                return name
        try:
            return _TYPES[name]
        except KeyError as error:
            raise _error(self.program, value, f"unsupported typed type {name}") from error

    def local_type(self, value: object) -> str:
        # Canonical scalar temporaries retain JavaScript Number precision;
        # constructors, builtins, calls, uniforms, and outputs remain the
        # explicit GLSL float32 consumption/storage boundaries.
        if (value.display() == "vec2[8]"
                and self.authorized_newton_roots_declaration is not None):
            return "std::array<glsl::Vec2, 8>"
        if value.display() == "HistoricPalette[21]" and self.authorized_historic_palette_proof is not None:
            return "std::array<HistoricPalette, 21>"
        if value.display() == "PaletteEntry[55]" and self.authorized_palette_frontend_proof is not None:
            return "std::array<PaletteEntry, 55>"
        if (value.display() == "uvec2[25]"
                and self.authorized_median_frontend_proof is not None):
            return "std::array<glsl::UVec2, 25>"
        if (value.display() == "uint[25]"
                and self.authorized_median_frontend_proof is not None):
            return "std::array<std::uint32_t, 25>"
        if (self.authorized_distortion_frontend_proof is not None
                and value.display() == "float[9]"):
            return "std::array<double, 9>"
        if (self.authorized_distortion_frontend_proof is not None
                and value.display() == "vec2[9]"):
            return "std::array<glsl::Vec2, 9>"
        return "double" if value.display() == "float" else self.type(value)

    def function_type(self, value: object) -> str:
        return "double" if value.display() == "float" else self.type(value)

    def function_parameter_type(self, function: object, ordinal: int,
                                parameter: object,
                                *, record_out_inout: bool = True) -> str:
        bitwise = getattr(self, "authorized_bitwise_number_proof", None)
        spooky = self.authorized_spooky_ticker_proof
        if (spooky is not None
                and any(parameter is item
                        for item in spooky.number_parameters)):
            expected = {
                ("hash_mix", 0): 14,
                ("sample_glyph", 1): 16,
                ("sample_glyph", 2): 17,
                ("ticker_row_mask", 1): 20,
            }
            if (expected.get((function.name, ordinal)) != parameter.id
                    or parameter.type.display() not in {"int", "uint"}):
                raise _error(
                    self.program, parameter,
                    "malformed authenticated SpookyTicker Number parameter")
            self.emitted_spooky_ticker_number_parameters.append(parameter)
            return "double"
        if parameter.type.display() == "HistoricPalette":
            proof = self.authorized_historic_palette_proof
            if (proof is None or function.name != "sampleHistoricPalette"
                    or parameter.name != "pal"):
                raise _error(self.program, parameter,
                             "unauthenticated Historic Palette parameter")
            return "HistoricPalette"
        if parameter.type.display() == "PaletteEntry":
            proof = self.authorized_palette_frontend_proof
            if proof is None:
                raise _error(self.program, parameter,
                             "unauthenticated Palette parameter")
            return "PaletteEntry"
        palette = self.authorized_palette_frontend_proof
        if palette is not None and any(
                parameter is item for item in palette.cosine_function.parameters[1:]):
            if (function is not palette.cosine_function
                    or parameter.type.display() != "vec3"
                    or ordinal not in (1, 2, 3, 4)):
                raise _error(self.program, parameter,
                             "malformed authenticated Palette cosine parameter")
            return PALETTE_COSINE_NATIVE_TYPE
        if bitwise is not None and any(
                parameter is item for item in bitwise.number_symbols[:2]):
            if (function.id != 23 or function.name != "bitOp"
                    or ordinal not in (0, 1)
                    or bitwise.number_symbols[ordinal] is not parameter
                    or parameter.type.display() != "float"):
                raise _error(self.program, parameter,
                             "malformed authenticated Bitwise Number parameter")
            self.emitted_bitwise_number_parameter_sites.append(parameter)
        if (self.authorized_osd_proof is not None
                and function.name == "sample_glyph"
                and ordinal in (1, 2)
                and parameter.id in (24, 25)
                and parameter.type.display() == "int"):
            return "double"
        focus = getattr(self, "authorized_focus_blur_proof", None)
        if focus is not None and any(parameter is item
                                     for item in focus.sampler_parameters):
            if (function is not focus.helper or ordinal not in (0, 1)
                    or focus.sampler_parameters[ordinal] is not parameter
                    or parameter.type.display() != "sampler2D"):
                raise _error(self.program, parameter,
                             "malformed authenticated borrowed sampler parameter")
            self.emitted_focus_blur_parameter_sites.append(parameter)
            return "const Surface&"
        distortion = self.authorized_distortion_frontend_proof
        if distortion is not None and any(
                parameter is item for item in distortion.sampler_parameter_nodes):
            if parameter.type.display() != "sampler2D":
                raise _error(self.program, parameter,
                             "malformed authenticated Distortion sampler parameter")
            self.emitted_distortion_sampler_parameters.append(parameter)
            return "const Surface&"
        inout_proof = self.authorized_inout_vec3_swap_proof
        if inout_proof is not None and any(parameter is item
                                           for item in inout_proof.parameters):
            if (function is not inout_proof.function or parameter.type.display() != "vec3"
                    or parameter.direction != "inout"):
                raise _error(self.program, parameter,
                             "malformed authenticated inout vec3 swap parameter")
            return f"{self.function_type(parameter.type)}&"
        out_parameters = self.authorized_out_inout_parameters
        if any(parameter is item for item in out_parameters):
            if (self.out_inout_direction_contract is None
                    or parameter.direction != "out"):
                raise _error(self.program, parameter,
                             "malformed authenticated out/inout parameter")
            abi_by_name = dict(
                self.out_inout_direction_contract.parameter_abis)
            abi = abi_by_name.get(parameter.name)
            if abi is None:
                abi = self.out_inout_direction_contract.native_abi
            if not abi.endswith("&"):
                raise _error(self.program, parameter,
                             "authenticated out/inout ABI must be a reference")
            if (record_out_inout
                    and any(parameter is item
                            for item in self.emitted_out_inout_parameters)):
                raise _error(self.program, parameter,
                             "authenticated out/inout parameter emitted twice")
            if record_out_inout:
                self.emitted_out_inout_parameters.append(parameter)
            return abi
        proof = self.program.fixed_array_in_parameter_proof
        if parameter.type.kind != "array":
            return self.function_type(parameter.type)
        if (proof is not None
                and function.signature.id == proof.parameter.owner_signature_id
                and ordinal == proof.parameter.parameter_ordinal
                and parameter.id == proof.parameter.symbol_id
                and parameter.name == proof.parameter.symbol_name
                and parameter.type.display() == proof.parameter.array_type
                and parameter.direction == proof.parameter.direction
                and parameter.span == next(
                    item.span for item in function.parameters
                    if item.id == proof.parameter.symbol_id)):
            return proof.parameter.native_abi
        raise _error(self.program, parameter,
                     f"unsupported typed type {parameter.type.display()}")

    def uniform_type(self, value: object) -> str:
        # Renderer scalar uniforms are JavaScript Numbers.  Preserve their
        # binary64 value in generated state; legacy float bindings widen
        # compatibly through Bindings::get_number().
        return "double" if value.display() == "float" else self.type(value)

    @staticmethod
    def _contains_vector_value_boundary(value: TypedExpression) -> bool:
        if value.kind in {"builtin", "call"} and value.type.display() in {"vec2", "vec3", "vec4"}:
            return True
        return any(_Emitter._contains_vector_value_boundary(child) for child in value.children)

    @staticmethod
    def _function_returns_integral_call_map(function: object) -> bool:
        """Recognize canonical `vecN(integralCall()) / scalar` Array returns."""
        returns: list[TypedExpression] = []

        def visit(statement: TypedStatement) -> None:
            if statement.kind == "return" and len(statement.expressions) == 1:
                returns.append(statement.expressions[0])
            for child in statement.children:
                visit(child)

        for statement in function.body:
            visit(statement)
        if len(returns) != 1:
            return False
        value = returns[0]
        if (value.kind != "binary" or value.operator != "/"
                or value.type.display() not in {"vec2", "vec3", "vec4"}
                or len(value.children) != 2):
            return False
        converted = value.children[0]
        lanes = value.type.display()[-1]
        return (converted.kind == "construct" and len(converted.children) == 1
                and converted.children[0].kind == "call"
                and converted.children[0].type.display() in {"ivec" + lanes, "uvec" + lanes})

    def _canonical_plain_array_vector(self, value: TypedExpression) -> bool:
        """Whether canonical JS carries this vector in an ordinary Array.

        Vector-vector arithmetic is lowered through `vecN.op([], ...)`: its
        lanes are F32-rounded, but the result container is an ordinary Array.
        A following scalar `.map()` therefore retains Number precision.
        Scalar maps preserve the input container species, so that property
        continues through a scalar-only vector arithmetic chain.
        """
        vector_types = {"vec2", "vec3", "vec4"}
        if value.kind == "call":
            return value.signature_id in self.ordinary_array_return_signatures
        if value.kind != "binary" or value.type.display() not in vector_types:
            return False
        left, right = value.children
        left_vector = left.type.display() in vector_types
        right_vector = right.type.display() in vector_types
        if left_vector and right_vector:
            return True
        if left_vector != right_vector:
            return self._canonical_plain_array_vector(left if left_vector else right)
        return False

    def _ordinary_return_scalar_map_chain(self, value: TypedExpression) -> bool:
        """Classify a declaration that retains an ordinary-Array call species."""
        if value.kind == "call":
            return value.signature_id in self.ordinary_array_return_signatures
        if (value.kind != "binary" or value.operator not in {"+", "-", "*", "/"}
                or value.type.display() not in {"vec2", "vec3", "vec4"}
                or len(value.children) != 2):
            return False
        vector_types = {"vec2", "vec3", "vec4"}
        left_vector = value.children[0].type.display() in vector_types
        right_vector = value.children[1].type.display() in vector_types
        if left_vector == right_vector:
            return False
        return self._ordinary_return_scalar_map_chain(
            value.children[0] if left_vector else value.children[1])

    @staticmethod
    def _literal_float_value(value: TypedExpression) -> float | None:
        """Evaluate the maximal scalar-float literal tree with JS Number rules."""
        if value.type.display() != "float":
            return None
        if value.kind == "literal":
            return float(value.literal_value)
        if value.kind == "unary" and len(value.children) == 1 and value.operator in {"+", "-"}:
            operand = _Emitter._literal_float_value(value.children[0])
            if operand is None:
                return None
            return operand if value.operator == "+" else -operand
        if value.kind != "binary" or len(value.children) != 2 or value.operator not in {"+", "-", "*", "/"}:
            return None
        left = _Emitter._literal_float_value(value.children[0])
        right = _Emitter._literal_float_value(value.children[1])
        if left is None or right is None:
            return None
        if value.operator == "+":
            return left + right
        if value.operator == "-":
            return left - right
        if value.operator == "*":
            return left * right
        if math.isnan(left) or math.isnan(right) or (math.isinf(left) and math.isinf(right)):
            return math.nan
        if right == 0.0:
            if left == 0.0:
                return math.nan
            negative = math.copysign(1.0, left) != math.copysign(1.0, right)
            return -math.inf if negative else math.inf
        return left / right

    @staticmethod
    def _f32(value: float) -> float:
        try:
            return struct.unpack("<f", struct.pack("<f", value))[0]
        except OverflowError:
            return math.copysign(math.inf, value)

    def folded_float_literal(self, value: TypedExpression) -> str | None:
        folded = self._literal_float_value(value)
        if folded is None:
            return None
        cast_type = "double" if self.numeric_literal_contract == "source-double" else "float"
        if cast_type == "float":
            folded = self._f32(folded)
        if math.isnan(folded):
            return f"std::numeric_limits<{cast_type}>::quiet_NaN()"
        if math.isinf(folded):
            sign = "-" if math.copysign(1.0, folded) < 0.0 else ""
            return f"{sign}std::numeric_limits<{cast_type}>::infinity()"
        return f"static_cast<{cast_type}>({repr(folded)})"

    def name(self, expression: TypedExpression) -> str:
        if expression.symbol is None or expression.symbol_id is None:
            raise _error(self.program, expression, "identifier has no stable symbol identity")
        symbol = expression.symbol
        if symbol.id in self.outputs:
            return "output"
        if symbol.name == "gl_FragCoord":
            return "context.frag_coord"
        remap = self.authorized_remap_proof
        if (remap is not None
                and symbol.name == "data"
                and symbol.type.display() == remap.data_field.type.display()):
            return "state.data.data"
        if symbol.id in self.uniforms:
            if symbol.type.kind == "sampler":
                return f"*state.{symbol.name}"
            return f"state.{symbol.name}"
        if symbol.id in self.locals:
            return self.locals[symbol.id]
        if symbol.id in getattr(self, "frame_fields", {}):
            # `frame.aspectRatio` / `frame.globalCoord`. Populated only for a
            # program whose closure this emitter authenticated itself, so every
            # other program still reaches the raise below.
            self.emitted_frame_references.append(expression)
            return self.frame_fields[symbol.id]
        if symbol.id in getattr(self, "array_frame_fields", {}):
            # `frame.emboss` .. `frame.edge2`. Populated only for a program
            # whose mutable-global array closure this emitter authenticated
            # itself, so every other program still reaches the raise below.
            self.emitted_array_frame_references.append(expression)
            return self.array_frame_fields[symbol.id]
        if symbol.id in getattr(self, "varying_fields", {}):
            # `context.uv` -- the runtime's vUv/v_texCoord alias
            # (glsl-runtime.js:148-151 copies context.uv into the varying
            # slot per pixel; there is no vertex stage and no interpolation
            # anywhere in the CPU reference). Populated only for a program
            # whose varying-uv closure this emitter authenticated itself, so
            # every other program still reaches the raise below.
            self.emitted_varying_references.append(expression)
            if any(expression is item
                   for item in self.authorized_spooky_ticker_varying_reads):
                if expression in self.emitted_spooky_ticker_varying_reads:
                    raise _error(
                        self.program, expression,
                        "authenticated SpookyTicker varying read emitted twice")
                self.emitted_spooky_ticker_varying_reads.append(expression)
            return self.varying_fields[symbol.id]
        raise _error(self.program, expression, f"unmapped typed symbol {symbol.name}")

    def _proved_array(self, symbol_id: int | None):
        proof = self.program.fixed_nine_table_proof
        fixed = (next((item for item in proof.arrays
                       if item.symbol_id == symbol_id), None)
                 if proof is not None else None)
        if fixed is not None:
            return fixed
        emboss = getattr(self, "authorized_emboss_proof", None)
        return (next((item for item in emboss.tables
                      if item.symbol_id == symbol_id), None)
                if emboss is not None else None)

    def _task18_array(self, symbol_id: int | None):
        proof = self.program.fixed_grid_counter_store_proof
        return proof if proof is not None and proof.array_symbol_id == symbol_id else None

    def _task19_table(self, symbol_id: int | None):
        proof = self.program.fixed_array_in_parameter_proof
        if proof is None:
            return None
        return next((item for item in (*proof.caller_tables, proof.offset_table)
                     if item.symbol_id == symbol_id), None)

    def _task19_parameter(self, symbol_id: int | None):
        proof = self.program.fixed_array_in_parameter_proof
        return (proof.parameter if proof is not None
                and proof.parameter.symbol_id == symbol_id else None)

    def _task20_array(self, symbol_id: int | None):
        proof = self.program.fixed_affine_centers13_proof
        return (proof if proof is not None and proof.symbol_id == symbol_id
                and self.current_function_signature_id == proof.fruit_signature_id
                else None)

    def _task20_index(self, value: TypedExpression,
                      role: str) -> str | None:
        if len(value.children) != 2 or value.children[0].kind != "id":
            return None
        base, index = value.children
        proof = self._task20_array(base.symbol_id)
        if (proof is None or base.symbol is None
                or base.symbol.id != proof.symbol_id
                or base.symbol.name != proof.symbol_name
                or base.type.display() != proof.array_type):
            return None
        spans = (tuple(item.index_span for item in proof.store_regions)
                 if role == "lvalue"
                 else tuple(item.index_span for item in proof.read_sites))
        if value.span not in spans:
            return None
        return (f"{self.expression(base)}[static_cast<std::size_t>("
                f"{self.expression(index)})]")

    def _task19_index(self, value: TypedExpression) -> str | None:
        if len(value.children) != 2 or value.children[0].kind != "id":
            return None
        base, index = value.children
        table = self._task19_table(base.symbol_id)
        parameter = self._task19_parameter(base.symbol_id)
        if (base.symbol is None or base.symbol.id != base.symbol_id
                or (table is None and parameter is None)):
            return None
        expected_type = table.array_type if table is not None else parameter.array_type
        if base.type.display() != expected_type:
            return None
        if (table is not None and index.kind == "literal"
                and isinstance(index.literal_value, int)
                and any(index.literal_value == proved_index and value.span == span
                        for proved_index, span in zip(table.literal_indices,
                                                      table.literal_index_spans))):
            return f"{self.expression(base)}[{index.literal_value}]"
        proof = self.program.fixed_array_in_parameter_proof
        read_spans = (table.induction_read_spans if table is not None
                      else parameter.induction_read_spans)
        if (index.kind == "id" and index.symbol_id == proof.induction_symbol_id
                and value.span in read_spans):
            return (f"{self.expression(base)}[static_cast<std::size_t>("
                    f"{self.expression(index)})]")
        return None

    def _task18_literal_read(self, value: TypedExpression) -> bool:
        if len(value.children) != 2 or value.children[0].kind != "id":
            return False
        base, index = value.children
        proof = self._task18_array(base.symbol_id)
        if (proof is None or base.symbol is None or base.symbol.id != base.symbol_id
                or base.type.display() != proof.array_type
                or index.kind != "literal"
                or not isinstance(index.literal_value, int)):
            return False
        return any(item.literal_index == index.literal_value
                   and item.index_span == value.span
                   for item in proof.literal_reads)

    def _task18_dynamic_store(self, value: TypedExpression) -> bool:
        if len(value.children) != 2 or value.children[0].kind != "id":
            return False
        base, index = value.children
        proof = self._task18_array(base.symbol_id)
        return (proof is not None and base.symbol is not None
                and base.symbol.id == base.symbol_id
                and base.type.display() == proof.array_type
                and index.kind == "id"
                and index.symbol_id == proof.counter_symbol_id
                and value.span == proof.dynamic_store_index_span)

    def _proved_index(self, value: TypedExpression) -> bool:
        if len(value.children) != 2 or value.children[0].kind != "id":
            return False
        base, index = value.children
        array = self._proved_array(base.symbol_id)
        if (array is None or base.symbol is None or base.symbol.id != base.symbol_id
                or base.type.display() != array.array_type):
            return False
        if (index.kind == "literal" and isinstance(index.literal_value, int)):
            return any(
                index.literal_value == proved_index and value.span == span
                for proved_index, span in zip(array.literal_store_indices,
                                              array.literal_store_index_spans))
        if index.kind == "id" and index.symbol_id is not None:
            emboss = getattr(self, "authorized_emboss_proof", None)
            if emboss is not None:
                table = next((item for item in emboss.tables
                              if item is array), None)
                if table is not None:
                    return (index.symbol_id == table.induction_symbol_id
                            and value is table.dynamic_read)
            proof = self.program.fixed_nine_table_proof
            return (index.symbol_id == proof.induction_symbol_id
                    and value.span in array.read_spans)
        return False

    def _proved_grade_index(self, value: TypedExpression) -> bool:
        """Admit by node identity in the frozen per-program proof set.

        Grade's bases are plain local ``vec3``s, never a proved fixed-size
        array, so this never touches ``_proved_array`` at all -- it is the
        emitter-side twin of the generator's node-identity-only admission
        (see the matching comment in generate_typed_slice.py's
        `expression()`).
        """
        matched = any(value is item for item in self.authorized_grade_index_sites)
        if matched:
            self.emitted_grade_index_sites.append(value)
        return matched

    def _proved_linear_srgb_index(self, value: TypedExpression) -> bool:
        """Same shape and rationale as ``_proved_grade_index`` above, for the
        shared ``linearToSrgb`` lane-index closure (adjust/colorspace/
        cellNoise's mat3 OKLab-transform family).
        """
        matched = any(
            value is item for item in self.authorized_linear_srgb_lane_index_sites)
        if matched:
            self.emitted_linear_srgb_lane_index_sites.append(value)
        return matched

    def _proved_fractal_index(self, value: TypedExpression) -> bool:
        matched = any(value is item
                      for item in self.authorized_fractal_frontend_indexes)
        if matched:
            self.emitted_fractal_frontend_indexes.append(value)
        return matched

    def _proved_color_lab_index(self, value: TypedExpression) -> bool:
        """Admit only ColorLab's thirteen source-bound vec3 lane indexes."""
        matched = any(value is item for item in self.authorized_color_lab_indexes)
        if not matched:
            return False
        if (len(value.children) != 2
                or value.type.display() != "float"
                or value.children[0].type.display() != "vec3"
                or value.children[1].type.display() != "int"):
            raise _error(
                self.program, value, "malformed authenticated ColorLab index")
        if any(value is item for item in self.emitted_color_lab_indexes):
            raise _error(
                self.program, value,
                "authenticated ColorLab index emitted twice")
        self.emitted_color_lab_indexes.append(value)
        return True

    def _proved_const_global_table_index(self, value: TypedExpression) -> bool:
        """Admit a counted read of an authenticated const array global.

        Admitted by NODE IDENTITY against what THIS emitter's own call to
        `authenticate_const_global_table_reads` returned -- the same idiom as
        `_proved_grade_index` and `_proved_linear_srgb_index`, and never by
        re-deriving the structure and trusting that the closure's census must
        have run. `base` and `index` are checked as the record's own operands,
        so the whole site is the authenticated one.
        """
        read = next((item for item in self.authorized_const_global_table_reads
                     if value is item.node), None)
        if read is None:
            return False
        if (len(value.children) != 2 or value.children[0] is not read.base
                or value.children[1] is not read.index):
            raise _error(self.program, value,
                         "malformed authenticated const global table read")
        self.emitted_const_global_table_reads.append(value)
        return True

    def _proved_shape_mixer_index(self, value: TypedExpression) -> bool:
        """Admit only Shape Mixer's five authenticated ``vec3[i]`` sites."""
        proof = self.authorized_shape_mixer_proof
        nodes = () if proof is None else proof.dynamic_indexes
        matched = any(value is item for item in nodes)
        if matched:
            self.emitted_shape_mixer_exceptional.append(value)
        return matched

    def _consume_bitwise_number_expression(self, value: TypedExpression) -> None:
        proof = getattr(self, "authorized_bitwise_number_proof", None)
        if proof is None:
            return
        authorized = tuple(item for item in proof.consumed_objects
                           if isinstance(item, TypedExpression))
        if any(value is item for item in authorized):
            if any(value is item for item in self.emitted_bitwise_number_objects):
                raise _error(self.program, value,
                             "authenticated Bitwise Number object emitted twice")
            self.emitted_bitwise_number_objects.append(value)

    def _consume_edge_bvec_expression(self, value: TypedExpression) -> None:
        proof = self.authorized_edge_proof
        if proof is None or not any(value is item for item in proof.bvec_nodes):
            return
        if any(value is item for item in self.emitted_edge_bvec_nodes):
            raise _error(self.program, value,
                         "authenticated Edge bvec3 node emitted twice")
        self.emitted_edge_bvec_nodes.append(value)

    def _consume_glitch_matrix_object(self, value: TypedExpression) -> None:
        proof = self.authorized_glitch_proof
        if proof is None:
            return
        authorized = proof.consumed_objects
        is_authorized = any(value is item for item in authorized)
        is_matrix_bearing = (value.type.display() == "mat4"
                             or (value.kind == "binary"
                                 and any(child.type.display() == "mat4"
                                         for child in value.children)))
        if is_matrix_bearing and not is_authorized:
            raise _error(self.program, value,
                         "unauthenticated Glitch matrix object")
        if not is_authorized:
            return
        if any(value is item for item in self.emitted_glitch_matrix_objects):
            raise _error(self.program, value,
                         "authenticated Glitch matrix object emitted twice")
        expected_index = len(self.emitted_glitch_matrix_objects)
        if (expected_index >= len(authorized)
                or value is not authorized[expected_index]):
            raise _error(self.program, value,
                         "authenticated Glitch matrix emission out of order")
        self.emitted_glitch_matrix_objects.append(value)

    def _consume_emboss_expression(self, value: TypedExpression) -> None:
        proof = getattr(self, "authorized_emboss_proof", None)
        if proof is None:
            return
        stores = tuple(store for table in proof.tables
                       for store in table.literal_stores)
        reads = tuple(table.dynamic_read for table in proof.tables)
        if any(value is item for item in stores):
            if any(value is item for item in self.emitted_emboss_stores):
                raise _error(self.program, value,
                             "authenticated Emboss store emitted twice")
            self.emitted_emboss_stores.append(value)
        if any(value is item for item in reads):
            if any(value is item for item in self.emitted_emboss_reads):
                raise _error(self.program, value,
                             "authenticated Emboss read emitted twice")
            self.emitted_emboss_reads.append(value)
        if any(value is item
               for item in proof.texture_coordinate_divisions):
            if any(value is item for item
                   in self.emitted_emboss_materialization_divisions):
                raise _error(
                    self.program, value,
                    "authenticated Emboss materialization emitted twice")
            expected_index = len(
                self.emitted_emboss_materialization_divisions)
            if (expected_index >= len(proof.texture_coordinate_divisions)
                    or value is not proof.texture_coordinate_divisions[
                        expected_index]):
                raise _error(
                    self.program, value,
                    "authenticated Emboss materialization emitted out of order")
            self.emitted_emboss_materialization_divisions.append(value)

    def expression(self, value: TypedExpression) -> str:
        self._consume_bitwise_number_expression(value)
        self._consume_edge_bvec_expression(value)
        self._consume_glitch_matrix_object(value)
        self._consume_emboss_expression(value)
        if any(value is item for item in self.authorized_fractal_hsv_calls):
            if any(value is item for item in self.emitted_fractal_hsv_calls):
                raise _error(
                    self.program, value,
                    "authenticated Fractal HSV call emitted twice")
            self.emitted_fractal_hsv_calls.append(value)
        if value is self.authorized_fractal_palette_call:
            if self.emitted_fractal_palette_calls:
                raise _error(
                    self.program, value,
                    "authenticated Fractal palette call emitted twice")
            self.emitted_fractal_palette_calls.append(value)
        if value is self.authorized_fractal_newton_call:
            if self.emitted_fractal_newton_calls:
                raise _error(
                    self.program, value,
                    "authenticated Fractal Newton call emitted twice")
            self.emitted_fractal_newton_calls.append(value)
        if value is self.authorized_fractal_julia_call:
            if self.emitted_fractal_julia_calls:
                raise _error(
                    self.program, value,
                    "authenticated Fractal Julia call emitted twice")
            self.emitted_fractal_julia_calls.append(value)
        if value is self.authorized_fractal_mandelbrot_call:
            if self.emitted_fractal_mandelbrot_calls:
                raise _error(
                    self.program, value,
                    "authenticated Fractal Mandelbrot call emitted twice")
            self.emitted_fractal_mandelbrot_calls.append(value)
        focus = getattr(self, "authorized_focus_blur_proof", None)
        if focus is not None:
            if any(value is item for item in focus.sampler_uses):
                self.emitted_focus_blur_uses.append(value)
            if any(value is item for item in focus.calls):
                self.emitted_focus_blur_calls.append(value)
        distortion = self.authorized_distortion_frontend_proof
        if distortion is not None:
            if any(value is item for item in distortion.sampler_calls):
                self.emitted_distortion_sampler_calls.append(value)
            if any(value is item for item in distortion.sampler_actual_nodes):
                self.emitted_distortion_sampler_actuals.append(value)
            if any(value is item for item in distortion.derivative_nodes):
                self.emitted_distortion_derivatives.append(value)
            if value is distortion.reflect_node:
                self.emitted_distortion_reflects.append(value)
        rotate_expressions = getattr(self, "authorized_rotate_expressions", ())
        # Existing typed programs already contain non-escaping mat2 arithmetic.
        # The new capability being authorized is specifically a matrix-return
        # program; once such a return exists, every matrix object in that
        # program must be one of Rotate's independently authenticated objects.
        matrix_return_program = any(
            function.return_type.kind == "matrix"
            for function in self.program.functions)
        matrix_role = None
        if value.type.kind == "matrix":
            matrix_role = 0 if value.kind == "construct" else 1 if value.kind == "call" else None
        elif (value.kind == "binary"
              and any(child.type.kind == "matrix" for child in value.children)):
            matrix_role = 2
        if matrix_return_program and (value.type.kind == "matrix" or matrix_role == 2) and (
                matrix_role is None
                or len(rotate_expressions) != 3
                or value is not rotate_expressions[matrix_role]):
            raise _error(self.program, value,
                         "unauthenticated matrix expression")
        if any(value is item for item in getattr(
                self, "authorized_rotate_expressions", ())):
            self.emitted_rotate_expressions.append(value)
        if value.kind == "id": return self.name(value)
        if value.kind == "literal":
            if value is self.authorized_fractal_alpha_literal:
                if (value.type.display() != "float"
                        or value.literal != "0.01"
                        or value.literal_value != 0.01):
                    raise _error(
                        self.program, value,
                        "malformed authenticated Fractal alpha literal")
                self.emitted_fractal_alpha_literals.append(value)
                return f"static_cast<double>({value.literal})"
            if value.type.display() == "float":
                literal_type = "double" if self.numeric_literal_contract == "source-double" else "float"
                return f"static_cast<{literal_type}>({value.literal})"
            if value.type.display() == "int": return f"std::int32_t({value.literal_value})"
            if value.type.display() == "uint": return f"std::uint32_t({value.literal_value})"
            if value.type.display() == "bool": return "true" if value.literal_value else "false"
            raise _error(self.program, value, "unsupported literal type")
        if value is self.authorized_round_parent:
            round_value = value.children[0]
            if round_value is not self.authorized_round:
                raise _error(self.program, value,
                             "Gather round-to-int parent drift")
            return ("glsl::detail::float_to_int32(glsl::round("
                    + self.expression(round_value.children[0]) + "))")
        if value.kind == "construct":
            display = value.constructor_type.display()
            testpattern = self.authorized_testpattern_proof
            glyph_initializer = (next(
                (item for item in testpattern.consumed_objects
                 if getattr(item, "kind", None) == "construct"
                 and getattr(item, "type", None) is not None
                 and item.type.display() == "int[10]"), None)
                if testpattern is not None else None)
            if (testpattern is not None
                    and value is glyph_initializer):
                if (display != "int[10]" or len(value.children) != 10):
                    raise _error(self.program, value,
                                 "malformed Test Pattern GLYPH constructor")
                self.emitted_testpattern_constructors.append(value)
                return ("std::array<std::int32_t, 10>{{"
                        + ", ".join(self.expression(item)
                                    for item in value.children) + "}}")
            if (testpattern is not None
                    and value is next((item for item in testpattern.consumed_objects
                                       if getattr(item, "kind", None) == "construct"
                                       and getattr(item, "type", None) is not None
                                       and item.type.display() == "vec3[8]"), None)):
                if (display != "vec3[8]" or len(value.children) != 8):
                    raise _error(self.program, value,
                                 "malformed Test Pattern colors constructor")
                self.emitted_testpattern_constructors.append(value)
                return ("std::array<glsl::Vec3, 8>{{"
                        + ", ".join(
                            "glsl::Vec3(" + self.expression(item) + ")"
                            for item in value.children) + "}}")
            osd = self.authorized_osd_proof
            osd_initializer = (next(
                (item for item in osd.consumed_objects
                 if getattr(item, "kind", None) == "construct"
                 and getattr(item, "type", None) is not None
                 and item.type.display() == "int[80]"), None)
                if osd is not None else None)
            if osd is not None and value is osd_initializer:
                if display != "int[80]" or len(value.children) != 80:
                    raise _error(self.program, value,
                                 "malformed OSD GLYPHS constructor")
                return ("std::array<std::int32_t, 80>{{"
                        + ", ".join(self.expression(item)
                                    for item in value.children) + "}}")
            spooky = self.authorized_spooky_ticker_proof
            spooky_initializer = (
                spooky.global_array and
                next((item for item in self.program.declarations
                      if item.symbol.id == spooky.global_array.symbol_id), None)
                if spooky is not None else None)
            spooky_initializer = (spooky_initializer.initializer
                                  if spooky_initializer is not None else None)
            if spooky is not None and value is spooky_initializer:
                if display != "int[80]" or len(value.children) != 80:
                    raise _error(self.program, value,
                                 "malformed SpookyTicker GLYPHS constructor")
                return ("std::array<std::int32_t, 80>{{"
                        + ", ".join(self.expression(item)
                                    for item in value.children) + "}}")
            historic = self.authorized_historic_palette_proof
            if historic is not None and value is historic.palettes_initializer:
                if (display != "HistoricPalette[21]" or len(value.children) != 21):
                    raise _error(self.program, value,
                                 "malformed authenticated Historic Palette table")
                self.emitted_historic_palette_constructors.append(value)
                return ("std::array<HistoricPalette, 21>{{"
                        + ", ".join(self.expression(item)
                                    for item in value.children) + "}}")
            if historic is not None and any(value is item for item in historic.palette_entries):
                if display != "HistoricPalette" or len(value.children) != 5:
                    raise _error(self.program, value,
                                 "malformed authenticated Historic Palette constructor")
                self.emitted_historic_palette_constructors.append(value)
                return ("HistoricPalette{" + ", ".join(
                    self._palette_plain_number_vector(
                        item, width=3, proof=historic,
                        vectors=self.emitted_historic_palette_number_vectors,
                        literals=self.emitted_historic_palette_number_literals,
                        profile_name="Historic Palette")
                    for item in value.children) + "}")
            palette = self.authorized_palette_frontend_proof
            if palette is not None and value is palette.palettes_initializer:
                if (display != "PaletteEntry[55]" or len(value.children) != 55):
                    raise _error(self.program, value,
                                 "malformed authenticated Palette table")
                self.emitted_palette_constructors.append(value)
                return ("std::array<PaletteEntry, 55>{{"
                        + ", ".join(self.expression(item)
                                    for item in value.children) + "}}")
            if palette is not None and any(value is item for item in palette.palette_entries):
                if display != "PaletteEntry" or len(value.children) != 4:
                    raise _error(self.program, value,
                                 "malformed authenticated PaletteEntry constructor")
                self.emitted_palette_constructors.append(value)
                return ("PaletteEntry{" + ", ".join(
                    self._palette_plain_number_vector(
                        item, width=4, proof=palette,
                        vectors=self.emitted_palette_number_vectors,
                        literals=self.emitted_palette_number_literals,
                        profile_name="Palette")
                    for item in value.children) + "}")
            const_global_table = self._const_global_table_constructor(value)
            if const_global_table is not None:
                # Design amendment S14, requirement 5. Two gaps close here:
                # `self.type()` on an array raises through the `_TYPES`
                # KeyError, and the generic `construct` fallback at the bottom
                # of this arm emits PARENTHESIZED call syntax `Alias(a, b, ...)`
                # which does not compile for `std::array`. An aggregate needs
                # brace-init, and a `std::array` needs the inner brace for its
                # wrapped C array. Admitted by node identity: this is the
                # initializer of an authenticated declaration, nothing else.
                table = const_global_table[1]
                if (display != table.glsl_type
                        or value.type.display() != table.glsl_type
                        or len(value.children) != table.element_count):
                    raise _error(
                        self.program, value,
                        "malformed authenticated const global table constructor")
                if table.native_element_type == "double":
                    elements = [self._const_global_table_double_element(child)
                                for child in value.children]
                else:
                    # `ivec2(-1, -1)` lowers through the existing `ivec2`
                    # constructor path, exactly as the design specifies.
                    elements = [self.expression(child)
                                for child in value.children]
                self.emitted_const_global_table_constructors.append(value)
                return (table.native_alias + "{{" + ", ".join(elements) + "}}")
            if (self.authorized_struct_declaration
                    and any(value is item
                            for item in self.authorized_struct_declaration[1])):
                if (display != "POIData" or value.type.display() != "POIData"
                        or len(value.children) != 3
                        or tuple(item.type.display() for item in value.children)
                        != ("vec4", "float", "float")):
                    raise _error(self.program, value,
                                 "malformed authenticated Newton struct constructor")
                arguments = []
                for child in value.children:
                    emitted = self.expression(child)
                    if (child.kind == "construct" and child.type.display() == "vec4"
                            and any(grand.kind == "literal"
                                    and grand.literal == "7.7718e-9"
                                    for grand in child.children)):
                        emitted = emitted.replace(
                            "static_cast<float>(7.7718e-9)",
                            "static_cast<float>("
                            f"{self.authorized_struct_materialization.center_witness_f32_spelling!r})")
                    arguments.append(emitted)
                self.emitted_newton_struct_constructors.append(value)
                return "POIData{" + ", ".join(arguments) + "}"
            glitch = self.authorized_glitch_proof
            if (glitch is not None
                    and any(value is item for item in glitch.constructors)):
                if (display != "mat4" or value.type.display() != "mat4"
                        or len(value.children) != 16
                        or any(child.type.display() != "float"
                               for child in value.children)):
                    raise _error(
                        self.program, value,
                        "malformed authenticated Glitch mat4 constructor")
                arguments = [self.expression(child)
                             for child in value.children]
                columns = [
                    "glsl::Vec4(" + ", ".join(arguments[index:index + 4]) + ")"
                    for index in range(0, 16, 4)
                ]
                return "glsl::Mat4(" + ", ".join(columns) + ")"
            edge = self.authorized_edge_proof
            if edge is not None and value is edge.constructor:
                if (display != "bvec3" or value.type.display() != "bvec3"
                        or len(value.children) != 3
                        or any(child.type.display() != "bool"
                               for child in value.children)):
                    raise _error(
                        self.program, value,
                        "malformed authenticated Edge bvec3 constructor")
                self.emitted_edge_constructors.append(value)
                return ("glsl::BVec3(" + ", ".join(
                    self.expression(item) for item in value.children) + ")")
            bitwise = getattr(self, "authorized_bitwise_number_proof", None)
            if bitwise is not None and any(
                    value is node for node in bitwise.int_constructors):
                if (display != "int" or value.type.display() != "int"
                        or len(value.children) != 1):
                    raise _error(self.program, value,
                                 "malformed authenticated JavaScript ToInt32 site")
                return ("glsl::detail::js_to_int32("
                        f"{self.expression(value.children[0])})")
            if any(value is node for node in getattr(
                    self, "authorized_bitwise_float_identity_nodes", ())):
                if (display != "float" or value.type.display() != "float"
                        or len(value.children) != 1):
                    raise _error(self.program, value,
                                 "malformed authenticated Number-preserving float site")
                self.emitted_bitwise_float_identity_nodes.append(value)
                if any(value is node
                       for node in self.authorized_bitwise_narrowing_skip_nodes):
                    self.emitted_bitwise_narrowing_skip_nodes.append(value)
                return f"static_cast<double>({self.expression(value.children[0])})"
            if value is self.authorized_texture_frontend_hash_conversion:
                # The frozen Texture JS canonicalizer erases this exact
                # `float(h)` constructor.  Keep the uint exact as a Number
                # through hash normalization (including the
                # `material_sprinkles` path); the eventual canonical Float32
                # materialization/output store establishes the boundary.
                if (self.current_function_name != "fast_hash"
                        or display != "float"
                        or value.type.display() != "float"
                        or len(value.children) != 1
                        or value.children[0].type.display() != "uint"):
                    raise _error(
                        self.program, value,
                        "malformed authenticated Texture hash conversion")
                self.emitted_texture_frontend_hash_conversion.append(value)
                return f"static_cast<double>({self.expression(value.children[0])})"
            if any(value is node for node in
                   self.authorized_scalar_uint_narrowing_skip_nodes):
                # Grain's pinned canonical JS erases this exact
                # `float(noise.x)` constructor, keeping the uint exact in a
                # Number through the following multiply.  This node-identity
                # exception mirrors the older Bitwise int-cast precedent;
                # never widen the general integral-to-float constructor rule.
                if (display != "float" or len(value.children) != 1
                        or value.children[0].type.display() != "uint"):
                    raise _error(
                        self.program, value,
                        "malformed authenticated Grain narrowing-skip site")
                self.emitted_grain_narrowing_skip_nodes.append(value)
                return f"static_cast<double>({self.expression(value.children[0])})"
            if display == "uint" and len(value.children) == 1 and value.children[0].type.display() == "float":
                return f"glsl::detail::float_to_uint32({self.expression(value.children[0])})"
            if value is self.authorized_fractal_mat2_constructor:
                if (display != "mat2" or len(value.children) != 3
                        or value.children[0].type.display() != "vec2"
                        or any(child.type.display() != "float"
                               for child in value.children[1:])):
                    raise _error(self.program, value,
                                 "malformed authenticated Fractal mat2 constructor")
                return ("glsl::Mat2(" + self.expression(value.children[0]) + ", "
                        "glsl::Vec2(" + self.expression(value.children[1]) + ", "
                        + self.expression(value.children[2]) + "))")
            if display == "mat2":
                if len(value.children) != 4 or any(child.type.display() != "float" for child in value.children):
                    raise _error(self.program, value, "unsupported mat2 constructor")
                arguments = [self.expression(child) for child in value.children]
                return ("glsl::Mat2(glsl::Vec2(" + ", ".join(arguments[:2]) + "), "
                        "glsl::Vec2(" + ", ".join(arguments[2:]) + "))")
            if display == "mat3":
                if len(value.children) != 9 or any(child.type.display() != "float" for child in value.children):
                    raise _error(self.program, value, "unsupported mat3 constructor")
                arguments = [self.expression(child) for child in value.children]
                # GLSL's mat3(9 scalars) fills column-major: the first 3
                # scalars are column 0, matching glsl::Mat<N>'s N-Vec<N>
                # column constructor exactly (same convention as mat2 above).
                return ("glsl::Mat3(glsl::Vec3(" + ", ".join(arguments[0:3]) + "), "
                        "glsl::Vec3(" + ", ".join(arguments[3:6]) + "), "
                        "glsl::Vec3(" + ", ".join(arguments[6:9]) + "))")
            if (display in {"vec2", "vec3", "vec4"} and len(value.children) == 1
                    and value.children[0].type.display() == "float"):
                lanes = display[-1]
                return f"glsl::FloatExpr<{lanes}>({self.expression(value.children[0])})"
            if (display in {"vec2", "vec3", "vec4"} and len(value.children) == int(display[-1])
                    and all(child.type.display() == "float" for child in value.children)):
                lanes = display[-1]
                return f"glsl::FloatExpr<{lanes}>(" + ", ".join(self.expression(x) for x in value.children) + ")"
            if (display in {"vec2", "vec3", "vec4"} and len(value.children) == 1
                    and value.children[0].type.display() in {
                        "ivec" + display[-1], "uvec" + display[-1]}
                    and value.children[0].kind == "swizzle"):
                # The canonical compiler flattens a converted integral
                # swizzle into the surrounding float-vector constructor, so
                # arithmetic can precede Float32Array storage.  Whole-vector
                # conversions (notably vec3(pcg(...))) materialize first.
                lanes = display[-1]
                return f"glsl::FloatExpr<{lanes}>({self.expression(value.children[0])})"
            if (display in {"int", "uint"} and len(value.children) == 1
                    and value.children[0].kind != "literal"
                    and value.children[0].type.display() in {
                        "float", "int", "uint", "bool"}):
                # GLSL's `int(x)`/`uint(x)` is not C++'s float-to-integer
                # conversion. The authority spells both casts with the 32-bit
                # wrap operators -- `var seedInt = floor(s)|0;` and
                # `hash_mix((cellX|0) ^ ((rowSeed|0) * 997))` in
                # canonical-kernels.js -- i.e. ECMAScript ToInt32/ToUint32,
                # which is total: NaN and +/-Infinity give 0 and finite values
                # wrap modulo 2^32. `std::int32_t(d)` on a `double` truncates
                # and is UNDEFINED outside the destination range, and UBSan
                # proves both classes reachable in the pinned corpus
                # (`nan is outside the range ... of type 'int'` from
                # bitEffects' `int(floor(s))`, and `-12.5238 is outside the
                # range ... of type 'unsigned int'` from spookyTicker's
                # `uint(cellX)`, whose GLSL `int` this emitter carries as a
                # JavaScript Number).
                #
                # The rule is deliberately total rather than typed on the IR:
                # whether the C++ operand is a `double` depends on carrier
                # decisions spread across the per-program Number profiles
                # (spookyTicker's `cellX`, OSD's `glyph_idx`, ...), so a rule
                # that reasoned about the IR type alone would miss exactly the
                # sites that are hardest to see. `glsl_int_cast`/
                # `glsl_uint_cast` resolve on the C++ operand type instead:
                # integral operands keep the ordinary conversion they already
                # had, floating operands get the authority's. Literal operands
                # are excluded because a literal is never Number-carried.
                helper = "glsl_int_cast" if display == "int" else "glsl_uint_cast"
                return (f"glsl::detail::{helper}("
                        + self.expression(value.children[0]) + ")")
            return f"{self.type(value.constructor_type)}(" + ", ".join(self.expression(x) for x in value.children) + ")"
        if value.kind == "swizzle":
            if (value.children
                    and value.children[0].type.display() == "bvec3"):
                edge = self.authorized_edge_proof
                nodes = () if edge is None else edge.swizzles
                if not any(value is item for item in nodes):
                    raise _error(self.program, value,
                                 "unsupported bvec3 swizzle")
                if any(value is item for item in self.emitted_edge_swizzles):
                    raise _error(self.program, value,
                                 "authenticated Edge swizzle emitted twice")
                self.emitted_edge_swizzles.append(value)
            if literal_lane := self._literal_lane_site(value):
                _, lane, role = literal_lane
                if role != "read":
                    raise _error(self.program, value,
                                 "literal vec3 lane write visited as read")
                return f"glsl::swizzle<{lane}>({self.expression(value.children[0])})"
            if not value.member or any(lane not in _SWIZZLE for lane in value.member):
                raise _error(self.program, value, "unsupported swizzle")
            lanes = ", ".join(str(_SWIZZLE[lane]) for lane in value.member)
            return f"glsl::swizzle<{lanes}>({self.expression(value.children[0])})"
        if value.kind == "member":
            historic = self.authorized_historic_palette_proof
            if historic is not None and value.children and value.children[0].type.display() == "HistoricPalette":
                if value.member not in {"color1", "color2", "color3", "color4", "color5"}:
                    raise _error(self.program, value,
                                 "malformed authenticated Historic Palette member")
                if value in self.emitted_historic_palette_members:
                    raise _error(self.program, value,
                                 "authenticated Historic Palette member emitted twice")
                self.emitted_historic_palette_members.append(value)
                return f"{self.expression(value.children[0])}.{value.member}"
            palette = self.authorized_palette_frontend_proof
            if palette is not None and value.children and value.children[0].type.display() == "PaletteEntry":
                if value.member not in {"amp", "freq", "offset", "phase"}:
                    raise _error(self.program, value,
                                 "malformed authenticated Palette member")
                if value in self.emitted_palette_members:
                    raise _error(self.program, value,
                                 "authenticated Palette member emitted twice")
                self.emitted_palette_members.append(value)
                return f"{self.expression(value.children[0])}.{value.member}"
            members = (self.authorized_struct_declaration[2]
                       if self.authorized_struct_declaration else ())
            if (not any(value is item for item in members)
                    or len(value.children) != 1
                    or value.member not in {"center", "deg", "maxZoom"}
                    or value.children[0].kind != "id"
                    or value.children[0].symbol_id != 101):
                raise _error(self.program, value,
                             "unauthenticated Newton struct member")
            if any(value is item for item in self.emitted_newton_members):
                raise _error(self.program, value,
                             "authenticated Newton struct member emitted twice")
            self.emitted_newton_members.append(value)
            return f"{self.expression(value.children[0])}.{value.member}"
        if value.kind == "index":
            if self._proved_color_lab_index(value):
                return (
                    f"{self.expression(value.children[0])}"
                    f"[static_cast<std::size_t>({self.expression(value.children[1])})]")
            historic = self.authorized_historic_palette_proof
            if (historic is not None
                    and any(value is item for item in historic.palette_index_reads)):
                if (len(value.children) != 2 or value.children[0].symbol.name != "PALETTES"
                        or value.children[0].type.display() != "HistoricPalette[21]"):
                    raise _error(self.program, value,
                                 "malformed authenticated Historic Palette index")
                self.emitted_historic_palette_indexes.append(value)
                return f"{self.expression(value.children[0])}[static_cast<std::size_t>({self.expression(value.children[1])})]"
            palette = self.authorized_palette_frontend_proof
            if (palette is not None
                    and any(value is item for item in palette.palette_index_reads)):
                if (len(value.children) != 2 or value.children[0].symbol.name != "PALETTES"
                        or value.children[0].type.display() != "PaletteEntry[55]"
                        or value.children[1].kind != "binary"
                        or value.children[1].operator != "-"):
                    raise _error(self.program, value,
                                 "malformed authenticated Palette index")
                self.emitted_palette_indexes.append(value)
                return f"{self.expression(value.children[0])}[static_cast<std::size_t>({self.expression(value.children[1])})]"
            if self._remap_index(value):
                return ("state.data.data[remap_data_index(static_cast<std::int64_t>("
                        + self.expression(value.children[1]) + "))]")
            if self._testpattern_index(value):
                return (f"{self.expression(value.children[0])}"
                        f"[static_cast<std::size_t>({self.expression(value.children[1])})]")
            if (len(value.children) == 2
                    and value.children[0].kind == "id"
                    and value.children[0].symbol_id in getattr(
                        self, "array_frame_fields", {})
                    and (value.children[1].kind == "literal"
                         and isinstance(value.children[1].literal_value, int))):
                # One of the 45 authenticated element stores: `emboss[0]` as
                # an assign target inside the writer. Literal index only --
                # the closure's frozen write-only census means every other
                # shape of reference to the five globals is a read (or a
                # whole-array use) and must keep raising at the generic gate
                # below. Lowered in the literal table-store form refract's
                # local tables use (`deriv_x[0] = ...`).
                self.emitted_array_frame_stores.append(value)
                return (f"{self.expression(value.children[0])}"
                        f"[{value.children[1].literal_value}]")
            if task20 := self._task20_index(value, "rvalue"):
                return task20
            if (task19 := self._task19_index(value)) is not None:
                return task19
            if self._task18_literal_read(value):
                return (f"{self.expression(value.children[0])}"
                        f"[{value.children[1].literal_value}]")
            if self._osd_index(value):
                base = self.expression(value.children[0])
                index = self.expression(value.children[1])
                return (
                    "glsl::detail::js_array_int32_read_for_bitwise("
                    f"{base}.data(), {base}.size(), static_cast<double>({index}))")
            if self._spooky_ticker_index(value):
                base = self.expression(value.children[0])
                index = self.expression(value.children[1])
                return (
                    "glsl::detail::js_array_int32_read_for_bitwise("
                    f"{base}.data(), {base}.size(), static_cast<double>({index}))")
            if self._median_index(value):
                return (f"{self.expression(value.children[0])}["
                        f"static_cast<std::size_t>({self.expression(value.children[1])})]")
            if any(value is item for item in self.authorized_newton_root_indexes):
                if (len(value.children) != 2
                        or value.children[0].kind != "id"
                        or value.children[0].symbol_id != 108
                        or value.children[1].kind != "id"
                        or value.children[1].symbol_id not in {109, 139}):
                    raise _error(self.program, value,
                                 "malformed authenticated Newton roots index")
                self.emitted_newton_root_indexes.append(value)
                return (f"{self.expression(value.children[0])}"
                        f"[static_cast<std::size_t>({self.expression(value.children[1])})]")
            if (not self._proved_index(value) and not self._proved_grade_index(value)
                    and not self._proved_linear_srgb_index(value)
                    and not self._proved_fractal_index(value)
                    and not self._proved_shape_mixer_index(value)
                    and not self._proved_const_global_table_index(value)):
                raise _error(self.program, value, "unsupported typed expression index")
            return f"{self.expression(value.children[0])}[{self.expression(value.children[1])}]"
        if value.kind == "binary":
            median_shift = (
                self.authorized_median_frontend_proof is not None
                and any(value is item
                        for item in self.authorized_median_frontend_proof.expression_nodes
                        if item.kind == "binary" and item.operator == "<<"))
            if (value.operator not in _BINARY_OPERATORS
                    and not (value.operator == "<<"
                             and (any(value is item
                                      for item in self.authorized_bit_effects_nodes)
                                  or median_shift))):
                median = self.authorized_median_frontend_proof
                if (median is not None
                        and any(value is item for item in median.expression_nodes
                                if item.kind == "binary"
                                and item.operator in {"&", "|"})
                        and value.type.display() == "uint"
                        and len(value.children) == 2
                        and all(child.type.display() == "uint"
                                for child in value.children)):
                    return (f"({self.expression(value.children[0])} {value.operator} "
                            f"{self.expression(value.children[1])})")
                raise _error(self.program, value, f"unsupported binary operator {value.operator}")
            if len(value.children) != 2:
                raise _error(self.program, value, "malformed typed binary expression")
            if value is self.authorized_fractal_alpha_product:
                if (value.operator != "*" or value.type.display() != "float"
                        or value.children[0].kind != "id"
                        or value.children[0].symbol_id != 28
                        or value.children[0].symbol.name != "bgAlpha"
                        or value.children[1] is not self.authorized_fractal_alpha_literal):
                    raise _error(
                        self.program, value,
                        "malformed authenticated Fractal alpha product")
                self.emitted_fractal_alpha_products.append(value)
                left = self.expression(value.children[0])
                right = self.expression(value.children[1])
                return (f"(static_cast<double>({left}) * {right})")
            historic_palette = self.authorized_historic_palette_proof
            if (historic_palette is not None
                    and value is historic_palette.t_initializer):
                left, offset_product = value.children
                if (self.current_function_name != "main"
                        or value.operator != "+"
                        or left.kind != "binary" or left.operator != "*"
                        or offset_product.kind != "binary"
                        or offset_product.operator != "*"
                        or left.children[0].kind != "binary"
                        or left.children[0].operator != "*"
                        or left.children[0].children[0].symbol.name != "lum"
                        or left.children[1].symbol.name != "repeat"
                        or offset_product.children[0].symbol.name != "offset"
                        or offset_product.children[1].literal != "0.01"):
                    raise _error(self.program, value,
                                 "malformed Historic Palette adapter t site")
                self.emitted_historic_palette_adapter_sites.append(value)
                lum = self.expression(left.children[0].children[0])
                repeat = self.expression(left.children[1])
                offset = self.expression(offset_product.children[0])
                return (f"((({lum} * 0.9999) * {repeat}) + "
                        f"({offset} * 0.01))")
            palette_adapter = self.authorized_palette_frontend_proof
            if (palette_adapter is not None
                    and value is palette_adapter.t_initializer):
                product, offset_product = value.children
                if (self.current_function_name != "main"
                        or value.operator != "+"
                        or product.kind != "binary" or product.operator != "*"
                        or offset_product.kind != "binary"
                        or offset_product.operator != "*"
                        or product.children[0].symbol.name != "lum"
                        or product.children[1].symbol.name != "repeat"
                        or offset_product.children[0].symbol.name != "offset"
                        or offset_product.children[1].literal != "0.01"):
                    raise _error(self.program, value,
                                 "malformed Palette adapter t site")
                self.emitted_palette_adapter_sites.append(value)
                lum = self.expression(product.children[0])
                repeat = self.expression(product.children[1])
                offset = self.expression(offset_product.children[0])
                return (f"(({lum} * {repeat}) + ({offset} * 0.01))")
            bit_effects = self.authorized_bit_effects_proof
            if (bit_effects is not None
                    and value is bit_effects.canonical_xi_to_int32_node):
                inner, narrowed_floor = value.children
                if (value.operator != "+" or value.type.display() != "int"
                        or inner.kind != "binary" or inner.operator != "+"
                        or inner.type.display() != "int"
                        or len(inner.children) != 2
                        or any(child.type.display() != "int"
                               for child in inner.children)
                        or narrowed_floor.kind != "construct"
                        or narrowed_floor.type.display() != "int"
                        or len(narrowed_floor.children) != 1
                        or narrowed_floor.children[0].kind != "builtin"
                        or narrowed_floor.children[0].callee != "floor"
                        or narrowed_floor.children[0].type.display() != "float"):
                    raise _error(
                        self.program, value,
                        "malformed authenticated BitEffects xi ToInt32 site")
                self.emitted_bit_effects_xi_to_int32.append(value)
                return (
                    "glsl::detail::js_to_int32("
                    f"static_cast<double>({self.expression(inner.children[0])}) + "
                    f"static_cast<double>({self.expression(inner.children[1])}) + "
                    f"{self.expression(narrowed_floor.children[0])})")
            if value is self.authorized_custom_comparer_predicate:
                left_type = value.children[0].type.display()
                right_type = value.children[1].type.display()
                if (value.operator != "==" or left_type != "vec3"
                        or right_type != "vec3"):
                    raise _error(self.program, value,
                                 "Lens custom comparer predicate drift")
                left = self.expression(value.children[0])
                right = self.expression(value.children[1])
                return (
                    "glsl::canonical_js_vector_equality_result_is_truthy("
                    f"glsl::Vec3({left}), glsl::Vec3({right}))")
            if any(value is item
                   for item in self.authorized_color_lab_vector_equalities):
                if (value.operator != "==" or value.type.display() != "bool"
                        or len(value.children) != 2
                        or any(child.type.display() != "vec2"
                               for child in value.children)):
                    raise _error(
                        self.program, value,
                        "malformed authenticated ColorLab vector equality")
                if any(value is item
                       for item in self.emitted_color_lab_vector_equalities):
                    raise _error(
                        self.program, value,
                        "authenticated ColorLab vector equality emitted twice")
                self.emitted_color_lab_vector_equalities.append(value)
                left = self.expression(value.children[0])
                right = self.expression(value.children[1])
                return (
                    "glsl::canonical_js_vector_equality_result_is_truthy("
                    f"glsl::Vec2({left}), glsl::Vec2({right}))")
            folded = self.folded_float_literal(value)
            if folded is not None:
                return folded
            left_type = value.children[0].type.display()
            right_type = value.children[1].type.display()
            palette = self.authorized_palette_frontend_proof
            palette_number_site = (
                palette is not None
                and self.current_function_name == palette.cosine_function.name
                and any(value is item for item in palette.cosine_vector_sites))
            if palette_number_site:
                if any(value is item for item in self.emitted_palette_cosine_sites):
                    raise _error(self.program, value,
                                 "authenticated Palette cosine vector site emitted twice")
                self.emitted_palette_cosine_sites.append(value)
            if value.operator == ">>":
                median = self.authorized_median_frontend_proof
                if (median is not None
                        and any(value is item for item in median.expression_nodes
                                if item.kind == "binary" and item.operator == ">>")):
                    if (value.type.display() != "uint" or len(value.children) != 2
                            or left_type != "uint" or right_type != "int"):
                        raise _error(self.program, value,
                                     "malformed authenticated Median right shift")
                    return (f"({self.expression(value.children[0])} >> "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in self.authorized_bit_effects_nodes):
                    if (value.type.display() != "uvec3"
                            or len(value.children) != 2
                            or value.children[0].type.display() != "uvec3"
                            or value.children[1].type.display() != "uint"):
                        raise _error(
                            self.program, value,
                            "malformed authenticated BitEffects vector shift")
                    if not any(value is item
                               for item in self.emitted_bit_effects_nodes):
                        self.emitted_bit_effects_nodes.append(value)
                    return (f"glsl::shift_right({self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in (
                        getattr(self.authorized_osd_proof, "bitwise_nodes", ()) )):
                    if (value.type.display() not in {"int", "uint"}
                            or any(child.type.display() != value.type.display()
                                   for child in value.children)):
                        raise _error(self.program, value,
                                     "malformed authenticated OSD shift")
                    self.emitted_osd_bitwise.append(value)
                    if value.type.display() == "int":
                        return ("glsl::detail::js_shift_right("
                                f"{self.expression(value.children[0])}, "
                                f"{self.expression(value.children[1])})")
                    return (f"({self.expression(value.children[0])} >> "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in self.authorized_spooky_ticker_nodes):
                    if (value.type.display() not in {"int", "uint"}
                            or any(child.type.display() != value.type.display()
                                   for child in value.children)):
                        raise _error(self.program, value,
                                     "malformed authenticated SpookyTicker shift")
                    self.emitted_spooky_ticker_bitwise.append(value)
                    return ("glsl::detail::js_shift_right("
                            f"{self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in self.authorized_texture_frontend_nodes):
                    if (value.type.display() != "uint"
                            or len(value.children) != 2
                            or any(child.type.display() != "uint"
                                   for child in value.children)):
                        raise _error(self.program, value,
                                     "malformed authenticated Texture shift")
                    self.emitted_texture_frontend_nodes.append(value)
                    return (f"({self.expression(value.children[0])} >> "
                            f"{self.expression(value.children[1])})")
                if value is self.authorized_testpattern_glyph_shift:
                    if (left_type, right_type, value.type.display()) != (
                            "int", "int", "int"):
                        raise _error(self.program, value,
                                     "malformed Test Pattern glyph shift")
                    self.emitted_testpattern_bitwise.append(value)
                    return ("glsl::detail::js_shift_right("
                            f"{self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                glyph = self.authorized_glyph_map_proof
                if glyph is not None and value is glyph.shift:
                    if (left_type, right_type, value.type.display()) != (
                            "int", "int", "int"):
                        raise _error(self.program, value,
                                     "malformed authenticated Glyph Map shift")
                    self.emitted_glyph_map_sites.append(value)
                    return ("glsl::detail::js_shift_right("
                            f"{self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                if (left_type not in {"uvec2", "uvec3", "uvec4"}
                        or right_type not in {"uint", left_type}):
                    raise _error(self.program, value, "unsupported binary operator >>")
                return (f"glsl::shift_right({self.expression(value.children[0])}, "
                        f"{self.expression(value.children[1])})")
            if value.operator == "<<":
                median = self.authorized_median_frontend_proof
                if (median is not None
                        and any(value is item for item in median.expression_nodes
                                if item.kind == "binary" and item.operator == "<<")):
                    if (value.type.display() != "uint" or len(value.children) != 2
                            or value.children[0].type.display() != "uint"
                            or value.children[1].type.display() != "int"):
                        raise _error(self.program, value,
                                     "malformed authenticated Median left shift")
                    return (f"({self.expression(value.children[0])} << "
                            f"{self.expression(value.children[1])})")
                if (not any(value is item
                            for item in self.authorized_bit_effects_nodes)
                        or value.type.display() != "int"
                        or len(value.children) != 2
                        or any(child.type.display() != "int"
                               for child in value.children)):
                    raise _error(self.program, value,
                                 "unsupported binary operator <<")
                if not any(value is item
                           for item in self.emitted_bit_effects_nodes):
                    self.emitted_bit_effects_nodes.append(value)
                return (f"({self.expression(value.children[0])} << "
                        f"{self.expression(value.children[1])})")
            if value.operator == "^":
                if any(value is item for item in self.authorized_bit_effects_nodes):
                    if (value.type.display() not in {"int", "uint", "uvec3"}
                            or len(value.children) != 2
                            or value.children[0].type.display() != value.type.display()
                            or value.children[1].type.display() != value.type.display()):
                        raise _error(
                            self.program, value,
                            "malformed authenticated BitEffects XOR")
                    if not any(value is item
                               for item in self.emitted_bit_effects_nodes):
                        self.emitted_bit_effects_nodes.append(value)
                    if value.type.display() == "int":
                        return ("glsl::detail::js_bitwise_xor("
                                f"{self.expression(value.children[0])}, "
                                f"{self.expression(value.children[1])})")
                    if value.type.display() == "uint":
                        return (f"({self.expression(value.children[0])} ^ "
                                f"{self.expression(value.children[1])})")
                    return (f"glsl::bitwise_xor({self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in (
                        getattr(self.authorized_osd_proof, "bitwise_nodes", ()) )):
                    if (value.type.display() != "uint"
                            or any(child.type.display() != "uint"
                                   for child in value.children)):
                        raise _error(self.program, value,
                                     "malformed authenticated OSD XOR")
                    self.emitted_osd_bitwise.append(value)
                    return (f"({self.expression(value.children[0])} ^ "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in self.authorized_spooky_ticker_nodes):
                    if (value.type.display() not in {"int", "uint"}
                            or any(child.type.display() != value.type.display()
                                   for child in value.children)):
                        raise _error(self.program, value,
                                     "malformed authenticated SpookyTicker XOR")
                    self.emitted_spooky_ticker_bitwise.append(value)
                    return ("glsl::detail::js_bitwise_xor("
                            f"{self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in self.authorized_texture_frontend_nodes):
                    if (value.type.display() != "uint"
                            or len(value.children) != 2
                            or any(child.type.display() != "uint"
                                   for child in value.children)):
                        raise _error(self.program, value,
                                     "malformed authenticated Texture XOR")
                    self.emitted_texture_frontend_nodes.append(value)
                    return (f"({self.expression(value.children[0])} ^ "
                            f"{self.expression(value.children[1])})")
                caustic = self.authorized_caustic_proof
                caustic_xors = (() if caustic is None else caustic.word_xors)
                if any(value is item for item in caustic_xors):
                    if (left_type, right_type, value.type.display()) != (
                            "uint", "uint", "uint"):
                        raise _error(
                            self.program, value,
                            "malformed authenticated scalar uint XOR")
                    self.emitted_caustic_nodes.append(value)
                    return (f"({self.expression(value.children[0])} ^ "
                            f"{self.expression(value.children[1])})")
                elif any(value is item for item in self.authorized_perlin_scalar_uint_xors):
                    if (left_type, right_type, value.type.display()) != (
                            "uint", "uint", "uint"):
                        raise _error(
                            self.program, value,
                            "malformed authenticated scalar uint XOR")
                    self.emitted_perlin_scalar_uint_xors.append(value)
                    return (f"({self.expression(value.children[0])} ^ "
                            f"{self.expression(value.children[1])})")
                elif any(value is item for item in self.authorized_scalar_uint_xors):
                    if ((left_type, right_type, value.type.display()) !=
                            ("uint", "uint", "uint")
                            or value.category != "rvalue"):
                        raise _error(
                            self.program, value,
                            "malformed authenticated scalar uint XOR")
                    self.emitted_scalar_uint_xors.append(value)
                    return (f"({self.expression(value.children[0])} ^ "
                            f"{self.expression(value.children[1])})")
                elif any(value is item for item in self.authorized_bitwise_scalar_int_ops_sites):
                    if value.type.display() != "int" or len(value.children) != 2:
                        raise _error(
                            self.program, value,
                            "malformed authenticated scalar int bitwise op")
                    self.emitted_bitwise_scalar_int_ops_sites.append(value)
                    return ("glsl::detail::js_bitwise_xor("
                            f"{self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                if (left_type not in {"uvec2", "uvec3", "uvec4"}
                        or right_type != left_type):
                    raise _error(self.program, value, "unsupported binary operator ^")
                return (f"glsl::bitwise_xor({self.expression(value.children[0])}, "
                        f"{self.expression(value.children[1])})")
            if value.operator in ("&", "|"):
                if any(value is item for item in self.authorized_bit_effects_nodes):
                    if (value.type.display() != "int"
                            or len(value.children) != 2
                            or any(child.type.display() != "int"
                                   for child in value.children)):
                        raise _error(
                            self.program, value,
                            "malformed authenticated BitEffects scalar bitwise op")
                    if not any(value is item
                               for item in self.emitted_bit_effects_nodes):
                        self.emitted_bit_effects_nodes.append(value)
                    helper = ("js_bitwise_and" if value.operator == "&"
                              else "js_bitwise_or")
                    return (f"glsl::detail::{helper}({self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in (
                        getattr(self.authorized_osd_proof, "bitwise_nodes", ()) )):
                    if (value.operator != "&" or value.type.display() != "int"
                            or any(child.type.display() != "int"
                                   for child in value.children)):
                        raise _error(self.program, value,
                                     "malformed authenticated OSD mask")
                    self.emitted_osd_bitwise.append(value)
                    return ("glsl::detail::js_bitwise_and("
                            f"{self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in self.authorized_texture_frontend_nodes):
                    if (value.operator != "&" or value.type.display() != "uint"
                            or len(value.children) != 2
                            or any(child.type.display() != "uint"
                                   for child in value.children)):
                        raise _error(self.program, value,
                                     "malformed authenticated Texture mask")
                    self.emitted_texture_frontend_nodes.append(value)
                    return (f"({self.expression(value.children[0])} & "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in self.authorized_spooky_ticker_nodes):
                    if (value.operator != "&"
                            or value.type.display() not in {"int", "uint"}
                            or any(child.type.display() != value.type.display()
                                   for child in value.children)):
                        raise _error(self.program, value,
                                     "malformed authenticated SpookyTicker mask")
                    self.emitted_spooky_ticker_bitwise.append(value)
                    return ("glsl::detail::js_bitwise_and("
                            f"{self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                if value is self.authorized_testpattern_glyph_mask:
                    if (value.operator != "&"
                            or (left_type, right_type, value.type.display())
                            != ("int", "int", "int")
                            or value.children[0]
                            is not self.authorized_testpattern_glyph_shift):
                        raise _error(self.program, value,
                                     "malformed Test Pattern glyph mask")
                    self.emitted_testpattern_bitwise.append(value)
                    return ("glsl::detail::js_bitwise_and("
                            f"{self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                glyph = self.authorized_glyph_map_proof
                if glyph is not None and value is glyph.mask:
                    if (value.operator != "&"
                            or (left_type, right_type, value.type.display())
                            != ("int", "int", "int")
                            or value.children[0] is not glyph.shift):
                        raise _error(self.program, value,
                                     "malformed authenticated Glyph Map mask")
                    self.emitted_glyph_map_sites.append(value)
                    return ("glsl::detail::js_bitwise_and("
                            f"{self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                if any(value is item for item in self.authorized_bitwise_scalar_int_ops_sites):
                    if value.type.display() != "int" or len(value.children) != 2:
                        raise _error(
                            self.program, value,
                            "malformed authenticated scalar int bitwise op")
                    self.emitted_bitwise_scalar_int_ops_sites.append(value)
                    helper = ("js_bitwise_and" if value.operator == "&"
                              else "js_bitwise_or")
                    return (f"glsl::detail::{helper}("
                            f"{self.expression(value.children[0])}, "
                            f"{self.expression(value.children[1])})")
                median = self.authorized_median_frontend_proof
                if (median is not None
                        and any(value is item for item in median.expression_nodes
                                if item.kind == "binary"
                                and item.operator in {"&", "|"})
                        and value.type.display() == "uint"
                        and len(value.children) == 2
                        and all(child.type.display() == "uint"
                                for child in value.children)):
                    return (f"({self.expression(value.children[0])} {value.operator} "
                            f"{self.expression(value.children[1])})")
                raise _error(self.program, value, f"unsupported binary operator {value.operator}")
            if value.operator == "%" and (left_type not in {"int", "uint"} or right_type != left_type):
                raise _error(self.program, value, "unsupported binary operator %")
            if "mat" in left_type or "mat" in right_type:
                glitch = self.authorized_glitch_proof
                glitch_products = (() if glitch is None else
                                   (*glitch.matrix_products,
                                    *glitch.vector_products))
                if any(value is item for item in glitch_products):
                    if (value.operator != "*"
                            or (left_type, right_type,
                                value.type.display()) not in {
                                ("mat4", "mat4", "mat4"),
                                ("vec4", "mat4", "vec4"),
                            }):
                        raise _error(
                            self.program, value,
                            "malformed authenticated Glitch matrix product")
                elif value.operator != "*" or (
                        (left_type, right_type) not in {("mat2", "vec2"), ("mat3", "vec3")}):
                    raise _error(self.program, value, "unsupported matrix binary expression")
            left = self.expression(value.children[0])
            right = self.expression(value.children[1])
            emboss = getattr(self, "authorized_emboss_proof", None)
            emboss_materializations = (() if emboss is None else
                                       emboss.texture_coordinate_divisions)
            if any(value is item for item in emboss_materializations):
                index = next(index for index, item in enumerate(
                    emboss_materializations) if value is item)
                numerator = emboss.texture_coordinate_numerators[index]
                if (value.operator != "/" or value.type.display() != "vec2"
                        or value.children[0] is not numerator
                        or numerator.type.display() != "vec2"):
                    raise _error(
                        self.program, value,
                        "malformed authenticated Emboss materialization")
                return f"(glsl::Vec2({left}) / {right})"
            spooky = self.authorized_spooky_ticker_proof
            if (spooky is not None
                    and any(value is item
                            for item in spooky.number_divisions)):
                if (value.operator != "/" or value.type.display() != "int"
                        or any(child.type.display() != "int"
                               for child in value.children)):
                    raise _error(
                        self.program, value,
                        "malformed authenticated SpookyTicker Number division")
                self.emitted_spooky_ticker_number_divisions.append(value)
                return (
                    f"(static_cast<double>({left}) / "
                    f"static_cast<double>({right}))")
            if value.operator == "%":
                osd = self.authorized_osd_proof
                if (osd is not None
                        and any(value is item for item in osd.hash_modulo_nodes)):
                    if value.type.display() != "uint" or left_type != "uint" \
                            or right_type != "uint":
                        raise _error(
                            self.program, value,
                            "malformed authenticated OSD hash remainder")
                    self.emitted_osd_hash_modulos.append(value)
                    return (
                        "(glsl::detail::js_to_int32(static_cast<double>("
                        f"{left})) % glsl::detail::js_to_int32(static_cast<double>("
                        f"{right})))")
                if (spooky is not None
                        and any(value is item
                                for item in spooky.number_remainder_nodes)):
                    if (value.type.display() != "uint"
                            or left_type != "uint" or right_type != "uint"):
                        raise _error(
                            self.program, value,
                            "malformed authenticated SpookyTicker Number remainder")
                    self.emitted_spooky_ticker_number_remainders.append(value)
                    return (
                        f"std::fmod(static_cast<double>({left}), "
                        f"static_cast<double>({right}))")
                return f"glsl::integer_mod({left}, {right})"
            # JavaScript canonical kernels retain scalar arithmetic in Number
            # precision until the typed local/assignment/builtin boundary. The
            # C++ spelling makes that storage rule explicit instead of allowing
            # native float operator chaining to narrow each intermediate.
            if value.type.display() == "float":
                return f"(static_cast<double>({left}) {value.operator} static_cast<double>({right}))"
            vector_with_boundary = (value.type.display() in {"vec2", "vec3", "vec4"}
                                    and self._contains_vector_value_boundary(value)
                                    and not palette_number_site)
            if vector_with_boundary:
                # Canonical helper-backed vector operations consume concrete
                # Float32Array operands. Preserve that operand boundary even
                # when the other operand is still a plain arithmetic tree.
                for child_index, (child, emitted) in enumerate(
                        ((value.children[0], left), (value.children[1], right))):
                    if (child.kind == "binary" and child.type.display() in {"vec2", "vec3", "vec4"}
                            and not self._contains_vector_value_boundary(child)):
                        materialized = f"{self.type(child.type)}({emitted})"
                        if child_index == 0:
                            left = materialized
                        else:
                            right = materialized
            result = f"({left} {value.operator} {right})"
            if vector_with_boundary:
                # Vector-vector helpers return an ordinary Array with rounded
                # lanes. A following scalar map retains Number precision.
                left_vector = left_type in {"vec2", "vec3", "vec4"}
                right_vector = right_type in {"vec2", "vec3", "vec4"}
                vector_child = (value.children[0] if left_vector else value.children[1]
                                if right_vector else None)
                scalar_map_of_plain_array = (left_vector != right_vector
                                             and vector_child is not None
                                             and self._canonical_plain_array_vector(vector_child))
                if not scalar_map_of_plain_array:
                    return f"{self.type(value.type)}({result})"
            return result
        if value.kind == "unary":
            if value.operator not in {"+", "-", "!"}:
                if (value.operator == "~"
                        and any(value is item
                                for item in self.authorized_bitwise_scalar_int_ops_sites)):
                    if (value.type.display() != "int"
                            or len(value.children) != 1
                            or value.children[0].type.display() != "int"):
                        raise _error(
                            self.program, value,
                            "malformed authenticated scalar int bitwise op")
                    self.emitted_bitwise_scalar_int_ops_sites.append(value)
                    return ("glsl::detail::js_bitwise_not("
                            f"{self.expression(value.children[0])})")
                raise _error(self.program, value, f"unsupported unary operator {value.operator}")
            if len(value.children) != 1:
                raise _error(self.program, value, "malformed typed unary expression")
            folded = self.folded_float_literal(value)
            if folded is not None:
                return folded
            return f"({value.operator}{self.expression(value.children[0])})"
        if value.kind == "post":
            proof = self.authorized_median_frontend_proof
            if (proof is None
                    or not any(value is item for item in proof.expression_nodes
                               if item.kind == "post")
                    or value.operator not in {"++", "--"}
                    or len(value.children) != 1
                    or value.type.display() != "int"
                    or value.children[0].kind != "id"
                    or value.children[0].type.display() != "int"):
                raise _error(self.program, value,
                             "unsupported authenticated Median post expression")
            return f"({self.expression(value.children[0])}{value.operator})"
        if value.kind == "conditional":
            if len(value.children) != 3:
                raise _error(self.program, value, "malformed typed conditional")
            condition = self.expression(value.children[0])
            yes = self.expression(value.children[1])
            no = self.expression(value.children[2])
            if value.type.display() in {"vec2", "vec3", "vec4"}:
                vector_type = self.type(value.type)
                yes, no = f"{vector_type}({yes})", f"{vector_type}({no})"
            return f"({condition} ? {yes} : {no})"
        if value.kind in {"builtin", "call"}:
            arguments = [self.expression(x) for x in value.children]
            if value is self.authorized_fractal_julia_call:
                if (self.current_function_name != "main"
                        or value.kind != "call"
                        or value.callee != "julia"
                        or value.signature_id != 61
                        or len(value.children) != 1
                        or value.children[0].kind != "id"
                        or value.children[0].symbol_id != 102):
                    raise _error(
                        self.program, value,
                        "malformed authenticated Fractal Julia call")
                self.emitted_fractal_julia_adapter_paths += 1
                return (
                    "julia(state, context, "
                    "(static_cast<double>(context.frag_coord[0]) + "
                    "static_cast<double>(state.tileOffset[0])) / "
                    "static_cast<double>(state.fullResolution[1]), "
                    "(static_cast<double>(context.frag_coord[1]) + "
                    "static_cast<double>(state.tileOffset[1])) / "
                    "static_cast<double>(state.fullResolution[1]))")
            if value is self.authorized_fractal_mandelbrot_call:
                if (self.current_function_name != "main"
                        or value.kind != "call"
                        or value.callee != "mandelbrot"
                        or value.signature_id != 65
                        or len(value.children) != 1
                        or value.children[0].kind != "id"
                        or value.children[0].symbol_id != 102):
                    raise _error(
                        self.program, value,
                        "malformed authenticated Fractal Mandelbrot call")
                self.emitted_fractal_mandelbrot_adapter_paths += 1
                return (
                    "mandelbrot(state, context, "
                    "(static_cast<double>(context.frag_coord[0]) + "
                    "static_cast<double>(state.tileOffset[0])) / "
                    "static_cast<double>(state.fullResolution[1]), "
                    "(static_cast<double>(context.frag_coord[1]) + "
                    "static_cast<double>(state.tileOffset[1])) / "
                    "static_cast<double>(state.fullResolution[1]))")
            if value is self.authorized_fractal_newton_call:
                if (self.current_function_name != "main"
                        or value.kind != "call"
                        or value.callee != "newton"
                        or value.signature_id != 67
                        or len(value.children) != 1
                        or value.children[0].kind != "id"
                        or value.children[0].symbol_id != 102):
                    raise _error(
                        self.program, value,
                        "malformed authenticated Fractal Newton call")
                self.emitted_fractal_newton_adapter_paths += 1
                return (
                    "newton(state, context, "
                    "(static_cast<double>(context.frag_coord[0]) + "
                    "static_cast<double>(state.tileOffset[0])) / "
                    "static_cast<double>(state.fullResolution[1]), "
                    "(static_cast<double>(context.frag_coord[1]) + "
                    "static_cast<double>(state.tileOffset[1])) / "
                    "static_cast<double>(state.fullResolution[1]))")
            bit_effects = self.authorized_bit_effects_proof
            if (value.kind == "call" and bit_effects is not None
                    and value is
                    bit_effects.canonical_overload_misdispatch_call):
                if (value.callee != "maskValue" or value.signature_id != 101
                        or len(arguments) != 3
                        or tuple(child.type.display() for child in value.children)
                        != ("vec2", "float", "float")
                        or 102 not in self.function_names):
                    raise _error(
                        self.program, value,
                        "malformed authenticated BitEffects overload misdispatch")
                self.emitted_bit_effects_overload_misdispatch.append(value)
                # Frozen canonicalFactory0 calls the four-argument JavaScript
                # overload with only these three source arguments. JavaScript
                # supplies `undefined` for its final scalar, which reaches the
                # Float32 boundary as canonical quiet NaN. Reproduce only this
                # exact identity-authenticated transpiler bug.
                return (
                    f"{self.function_names[102]}(state, context, "
                    f"{arguments[0]}, {arguments[1]}, {arguments[2]}, "
                    "std::numeric_limits<double>::quiet_NaN())")
            if value.kind == "builtin":
                if value is self.authorized_texture_frontend_inverse_sqrt:
                    if (value.callee != "inversesqrt"
                            or value.type.display() != "float"
                            or len(arguments) != 1
                            or value.children[0].type.display() != "float"):
                        raise _error(
                            self.program, value,
                            "malformed authenticated Texture inversesqrt")
                    self.emitted_texture_frontend_inverse_sqrt.append(value)
                    return f"glsl::inversesqrt({arguments[0]})"
                historic_palette = self.authorized_historic_palette_proof
                if (historic_palette is not None
                        and value is historic_palette.luminance_site):
                    if (self.current_function_name != "main"
                            or value.callee != "dot"
                            or value.type.display() != "float"
                            or len(arguments) != 2):
                        raise _error(
                            self.program, value,
                            "malformed Historic Palette adapter luminance site")
                    self.emitted_historic_palette_adapter_sites.append(value)
                    return (f"{HISTORIC_PALETTE_LUMINANCE_HELPER_NAME}"
                            f"({arguments[0]})")
                if (historic_palette is not None
                        and value is historic_palette.fract_site):
                    if (self.current_function_name != "main"
                            or value.callee != "fract"
                            or value.type.display() != "float"
                            or len(arguments) != 1):
                        raise _error(
                            self.program, value,
                            "malformed Historic Palette adapter fract site")
                    self.emitted_historic_palette_adapter_sites.append(value)
                    return (f"{HISTORIC_PALETTE_FRACT_HELPER_NAME}"
                            f"({arguments[0]})")
                palette = self.authorized_palette_frontend_proof
                if palette is not None and value is palette.luminance_site:
                    if (self.current_function_name != "main"
                            or value.callee != "dot"
                            or value.type.display() != "float"
                            or len(arguments) != 2):
                        raise _error(
                            self.program, value,
                            "malformed Palette adapter luminance site")
                    self.emitted_palette_adapter_sites.append(value)
                    return f"{PALETTE_LUMINANCE_HELPER_NAME}({arguments[0]})"
                if palette is not None and value is palette.cosine_site:
                    if (self.current_function_name != palette.cosine_function.name
                            or value.callee != "cos"
                            or value.type.display() != "vec3"
                            or len(value.children) != 1):
                        raise _error(self.program, value,
                                     "malformed authenticated Palette cosine site")
                    if any(value is item for item in self.emitted_palette_cosine_sites):
                        raise _error(self.program, value,
                                     "authenticated Palette cosine site emitted twice")
                    self.emitted_palette_cosine_sites.append(value)
                    return f"{PALETTE_COSINE_HELPER_NAME}({arguments[0]})"
                if palette is not None and value is palette.cosine_clamp_site:
                    if (self.current_function_name != palette.cosine_function.name
                            or value.callee != "clamp"
                            or value.type.display() != "vec3"
                            or len(value.children) != 3):
                        raise _error(self.program, value,
                                     "malformed authenticated Palette clamp site")
                    if any(value is item for item in self.emitted_palette_cosine_sites):
                        raise _error(self.program, value,
                                     "authenticated Palette clamp site emitted twice")
                    self.emitted_palette_cosine_sites.append(value)
                    return (f"{PALETTE_CLAMP_HELPER_NAME}({arguments[0]}, "
                            f"{arguments[1]}, {arguments[2]})")
                if value.callee in {"packHalf2x16", "unpackHalf2x16"}:
                    proof = self.authorized_median_frontend_proof
                    expected = (("vec2",), "uint") if value.callee == "packHalf2x16" else (("uint",), "vec2")
                    if (proof is None
                            or not any(value is item for item in proof.expression_nodes
                                       if item.kind == "builtin")
                            or value.type.display() != expected[1]
                            or tuple(child.type.display() for child in value.children)
                            != expected[0]):
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    helper = ("pack_half2x16" if value.callee == "packHalf2x16"
                              else "unpack_half2x16")
                    argument = (f"glsl::Vec2({arguments[0]})"
                                if value.callee == "packHalf2x16"
                                else arguments[0])
                    return f"glsl::{helper}({argument})"
                if value.callee == "log" and self.authorized_mandelbrot_logs:
                    if (not any(value is item
                                for item in self.authorized_mandelbrot_logs)
                            or len(arguments) != 1
                            or value.type.display() != "float"
                            or value.children[0].type.display() != "float"):
                        raise _error(self.program, value,
                                     "unsupported builtin log")
                    if any(value is item
                           for item in self.emitted_mandelbrot_logs):
                        raise _error(self.program, value,
                                     "authenticated Mandelbrot log emitted twice")
                    self.emitted_mandelbrot_logs.append(value)
                    return f"noisemaker::f32(std::log({arguments[0]}))"
                if value.callee in {"log", "log2"}:
                    if (not any(value is item for item in self.authorized_newton_logs)
                            or len(arguments) != 1):
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    self.emitted_newton_logs.append(value)
                    return (f"noisemaker::f32(std::{value.callee}"
                            f"({arguments[0]}))")
                if value.callee == "mod":
                    argument_types = tuple(child.type.display() for child in value.children)
                    if argument_types not in {("float", "float"), ("vec2", "float"), ("vec2", "vec2")}:
                        shape = self.authorized_shape_mixer_proof
                        if shape is not None and value is shape.wide_mod_node:
                            if len(arguments) != 2:
                                raise _error(self.program, value, "mod arity")
                            self.emitted_shape_mixer_exceptional.append(value)
                            return ("glsl::shape_mixer_mod_vec3("
                                    f"glsl::Vec3({arguments[0]}), "
                                    f"glsl::Vec3({arguments[1]}))")
                        proof = self.authorized_curl_proof
                        nodes = (() if proof is None else proof.mod_sites)
                        if not any(value is item for item in nodes):
                            raise _error(self.program, value,
                                         "unsupported builtin mod overload")
                        self.emitted_curl_nodes.append(value)
                if value.callee == "texelFetch":
                    argument_types = tuple(child.type.display() for child in value.children)
                    exact_level_zero = (len(value.children) == 3
                                        and value.children[2].kind == "literal"
                                        and value.children[2].literal == "0"
                                        and value.children[2].literal_value == 0)
                    if argument_types != ("sampler2D", "ivec2", "int") or not exact_level_zero:
                        raise _error(self.program, value, "unsupported builtin texelFetch overload")
                    return f"fetch_texel({arguments[0]}, {arguments[1]})"
                if value.callee == "texture":
                    if len(arguments) != 2: raise _error(self.program, value, "texture arity")
                    return f"sample_texture({arguments[0]}, {arguments[1]})"
                if value.callee == "textureLod":
                    # Identity admission only (texture-lod-admission-parallax-
                    # v1): the alias contract is the whole mechanism --
                    # glsl-runtime.js:400 drops the lod argument and calls
                    # `this.#texture(surface, coord)` itself, so this lowers
                    # through the exact `texture` path above, unchanged. The
                    # closure froze the lod as the exact `0.0` literal at the
                    # two admitted sites; a third site or a nonzero lod never
                    # reaches this arm. Never enters _BUILTIN_NAMES or the
                    # capability vocabulary.
                    if not any(value is item
                               for item in self.authorized_texture_lod_sites):
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    if len(arguments) != 3:
                        raise _error(self.program, value, "textureLod arity")
                    self.emitted_texture_lod_sites.append(value)
                    return f"sample_texture({arguments[0]}, {arguments[1]})"
                if value.callee == "textureSize":
                    if not arguments: raise _error(self.program, value, "textureSize arity")
                    return f"texture_size({arguments[0]})"
                if value.callee == "ceil":
                    # Node-identity admission only (ceil-admission-v1). No
                    # narrowing shim: Math.ceil and std::ceil agree on every
                    # finite double, unlike round's Math.round form.
                    if not any(value is item for item in self.authorized_ceil):
                        raise _error(self.program, value, "unsupported builtin ceil")
                    if len(arguments) != 1:
                        raise _error(self.program, value, "ceil arity")
                    return f"glsl::ceil({arguments[0]})"
                if value.callee == "round":
                    testpattern = self.authorized_testpattern_proof
                    if testpattern is not None and value is testpattern.round_node:
                        if (len(value.children) != 1
                                or value.type.display() != "vec2"
                                or value.children[0].type.display() != "vec2"):
                            raise _error(self.program, value,
                                         "malformed Test Pattern round(vec2)")
                        self.emitted_testpattern_rounds.append(value)
                        return (
                            "glsl::Vec2("
                            f"noisemaker::f32(glsl::round(glsl::swizzle<0>({arguments[0]}))), "
                            f"noisemaker::f32(glsl::round(glsl::swizzle<1>({arguments[0]}))))")
                    # Standalone round(float) -> float, distinct from the
                    # fused int(round(x)) site handled above at
                    # `self.authorized_round_parent`. Emitted only for the
                    # exact node this emitter itself authenticated
                    # (posterize-round-admission-v1). The reference JS
                    # materializes GLSL round() as Math.round and narrows the
                    # scalar result to f32 immediately on return, so this
                    # must narrow here too, not rely on a caller-side narrow.
                    if (value is not self.authorized_posterize_round
                            and not any(value is item for item
                                        in (self.authorized_as_u32_round or ()))):
                        raise _error(self.program, value, "unsupported builtin round")
                    if len(arguments) != 1:
                        raise _error(self.program, value, "round arity")
                    return f"noisemaker::f32(glsl::round({arguments[0]}))"
                if value.callee == "tanh":
                    proof = self.authorized_curl_proof
                    if proof is None or value is not proof.tanh_site:
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    if len(arguments) != 1:
                        raise _error(self.program, value, "tanh arity")
                    self.emitted_curl_nodes.append(value)
                    # Lane-wise, non-narrowing: the JavaScript transpiler
                    # scalarises this assignment, so it hands Math.tanh the
                    # full-precision operand and narrows only the result.
                    # Narrowing the argument here costs bit-exact parity.
                    return f"glsl::tanh_lanewise({arguments[0]})"
                if value.callee == "floatBitsToUint":
                    bit_effects_float_bits = any(
                        value is item for item in self.authorized_bit_effects_nodes)
                    caustic = None
                    if bit_effects_float_bits:
                        if (value.type.display() != "uint"
                                or len(value.children) != 1
                                or value.children[0].type.display() != "float"):
                            raise _error(
                                self.program, value,
                                "malformed authenticated BitEffects float-bit ingress")
                        if not any(value is item
                                   for item in self.emitted_bit_effects_nodes):
                            self.emitted_bit_effects_nodes.append(value)
                    else:
                        caustic = self.authorized_caustic_proof
                    scanline = self.authorized_scanline_error_proof
                    if caustic is not None and value is caustic.ingress:
                        self.emitted_caustic_nodes.append(value)
                    elif (scanline is not None and any(
                            value is item for item in scanline.ingresses)):
                        self.emitted_scanline_error_ingresses.append(value)
                    elif any(value is item for item in
                             self.authorized_shapes_float_bits_ingresses):
                        # Shapes' one ingress, by object identity. No
                        # capability token is added, matching the existing
                        # Caustic/Scanline Error skip-list precedent.
                        self.emitted_shapes_float_bits_ingresses.append(value)
                    elif any(value is item for item in
                             self.authorized_grime_float_bits_ingresses):
                        # grime's five ingresses, by object identity; no
                        # capability token, same skip-list precedent.
                        self.emitted_grime_float_bits_ingresses.append(value)
                    elif any(value is item for item in
                             self.authorized_kaleido_float_bits_ingress):
                        # kaleido's one ingress, same shape, by object
                        # identity; no capability token.
                        self.emitted_kaleido_float_bits_ingress.append(value)
                    elif any(value is item for item in
                             self.authorized_noise_float_bits_ingresses):
                        # Noise's prepared scalar-XOR carrier owns one
                        # floatBitsToUint ingress. Keep it on the same exact
                        # bit-reinterpretation helper as the landed ingress
                        # families; admission is by object identity only.
                        self.emitted_noise_float_bits_ingresses.append(value)
                    elif (self.authorized_shape_mixer_proof is not None
                          and value is
                          self.authorized_shape_mixer_proof.bit_ingress):
                        self.emitted_shape_mixer_exceptional.append(value)
                    elif (self.authorized_median_frontend_proof is not None
                          and any(value is item
                                  for item in self.authorized_median_frontend_proof.expression_nodes
                                  if item.kind == "builtin"
                                  and item.callee == "floatBitsToUint")):
                        if (value.type.display() != "uint" or len(value.children) != 1
                                or value.children[0].type.display() != "float"):
                            raise _error(
                                self.program, value,
                                "malformed authenticated Median float-bit ingress")
                    elif bit_effects_float_bits:
                        pass
                    else:
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    if len(arguments) != 1:
                        raise _error(self.program, value, "floatBitsToUint arity")
                    # Delegates to the existing, tested bit-reinterpretation
                    # helper. Must NOT be confused with float_to_uint32, which
                    # is GLSL numeric conversion (truncate + wrap).
                    return f"noisemaker::float_bits_to_uint({arguments[0]})"
                if value.callee in {"reflect", "refract"}:
                    # Emitted only for the exact node this emitter itself
                    # authenticated. `glsl::reflect` already exists, generic
                    # over `Vec<N,float>`, and implements exactly
                    # `I - 2*dot(N,I)*N` with no defensive internal
                    # normalize -- verified bit-exact against the reference
                    # JS by docs/port-engineering/builtins/oracle/.
                    shape = self.authorized_shape_mixer_proof
                    if shape is not None:
                        if value is shape.reflect_nodes[0]:
                            if len(arguments) != 2:
                                raise _error(self.program, value, "reflect arity")
                            self.emitted_shape_mixer_exceptional.append(value)
                            return ("glsl::shape_mixer_reflect_scalar("
                                    f"{arguments[0]}, {arguments[1]})")
                        if value is shape.reflect_nodes[1]:
                            if len(arguments) != 2:
                                raise _error(self.program, value, "reflect arity")
                            self.emitted_shape_mixer_exceptional.append(value)
                            return f"glsl::reflect({arguments[0]}, {arguments[1]})"
                        if value is shape.refract_nodes[0]:
                            if len(arguments) != 3:
                                raise _error(self.program, value, "refract arity")
                            self.emitted_shape_mixer_exceptional.append(value)
                            return ("glsl::shape_mixer_refract_scalar("
                                    f"{arguments[0]}, {arguments[1]}, {arguments[2]})")
                        if value is shape.refract_nodes[1]:
                            if len(arguments) != 3:
                                raise _error(self.program, value, "refract arity")
                            self.emitted_shape_mixer_exceptional.append(value)
                            return (f"glsl::refract({arguments[0]}, {arguments[1]}, "
                                    f"{arguments[2]})")
                    distortion_reflect = (
                        self.authorized_distortion_frontend_proof is not None
                        and value is self.authorized_distortion_frontend_proof.reflect_node)
                    if (value.callee != "reflect"
                            or (value is not self.authorized_reflect_node
                                and not distortion_reflect)):
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    if len(arguments) != 2:
                        raise _error(self.program, value, "reflect arity")
                    self.emitted_reflect_nodes.append(value)
                    return f"glsl::reflect({arguments[0]}, {arguments[1]})"
                if value.callee == "equal":
                    proof = getattr(self, "authorized_emboss_proof", None)
                    nodes = () if proof is None else proof.equalities
                    if (not any(value is item for item in nodes)
                            or len(arguments) != 2
                            or value.type.display() != "bvec2"
                            or tuple(child.type.display()
                                     for child in value.children)
                            != ("vec2", "vec2")):
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    if any(value is item
                           for item in self.emitted_emboss_equalities):
                        raise _error(
                            self.program, value,
                            "authenticated Emboss equality emitted twice")
                    self.emitted_emboss_equalities.append(value)
                    return f"glsl::equal({arguments[0]}, {arguments[1]})"
                if value.callee in {"all", "lessThanEqual"}:
                    # Emitted only for the exact nodes this emitter itself
                    # authenticated. `bvec2` and these two builtins are absent
                    # from _TYPES/_BUILTIN_NAMES so no other program can reach
                    # them.
                    proof = self.authorized_extrude_proof
                    nodes = (() if proof is None else
                             (*proof.reductions, *proof.relationals))
                    emboss = getattr(self, "authorized_emboss_proof", None)
                    emboss_reduction = (
                        value.callee == "all"
                        and emboss is not None
                        and any(value is item
                                for item in emboss.reductions))
                    if (not emboss_reduction
                            and not any(value is item for item in nodes)):
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    if emboss_reduction:
                        if any(value is item
                               for item in self.emitted_emboss_reductions):
                            raise _error(
                                self.program, value,
                                "authenticated Emboss reduction emitted twice")
                        self.emitted_emboss_reductions.append(value)
                    else:
                        self.emitted_extrude_nodes.append(value)
                    if value.callee == "all":
                        if len(arguments) != 1:
                            raise _error(self.program, value, "all arity")
                        return f"glsl::all({arguments[0]})"
                    if len(arguments) != 2:
                        raise _error(self.program, value, "lessThanEqual arity")
                    return f"glsl::lessThanEqual({arguments[0]}, {arguments[1]})"
                if value.callee in {"greaterThanEqual", "lessThan"}:
                    proof = self.authorized_edge_proof
                    nodes = () if proof is None else proof.relationals
                    if (not any(value is item for item in nodes)
                            or len(arguments) != 2
                            or value.type.display() != "bvec3"
                            or tuple(child.type.display()
                                     for child in value.children)
                            != ("vec3", "vec3")):
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    if any(value is item
                           for item in self.emitted_edge_relationals):
                        raise _error(
                            self.program, value,
                            "authenticated Edge relational emitted twice")
                    self.emitted_edge_relationals.append(value)
                    return f"glsl::{value.callee}({arguments[0]}, {arguments[1]})"
                if value.callee in {"any", "notEqual"}:
                    # Emitted only for the exact nodes this emitter itself
                    # authenticated (waves-any-notequal-admission-v1).
                    # Generalizes the all/lessThanEqual pattern immediately
                    # above from `all`/`lessThanEqual` to `any`/`notEqual`.
                    # `bvec2` and these two builtins are absent from
                    # _TYPES/_BUILTIN_NAMES so no other program can reach
                    # them.
                    nodes = (*self.authorized_waves_reductions,
                            *self.authorized_waves_relationals)
                    if not any(value is item for item in nodes):
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    self.emitted_waves_nodes.append(value)
                    if value.callee == "any":
                        if len(arguments) != 1:
                            raise _error(self.program, value, "any arity")
                        return f"glsl::any({arguments[0]})"
                    if len(arguments) != 2:
                        raise _error(self.program, value, "notEqual arity")
                    return f"glsl::notEqual({arguments[0]}, {arguments[1]})"
                if value.callee in {"dFdx", "dFdy", "fwidth"}:
                    # Emitted only for the exact nodes this emitter itself
                    # authenticated. Every generated pixel/helper function
                    # already takes `const glsl::PixelContext& context`, so
                    # lowering is a direct call -- no plumbing needed at any
                    # call depth.
                    proof = self.authorized_derivative_proof
                    nodes = (() if proof is None else proof.nodes)
                    distortion = self.authorized_distortion_frontend_proof
                    if distortion is not None:
                        nodes = (*nodes, *distortion.derivative_nodes)
                    if not any(value is item for item in nodes):
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    if len(arguments) != 1:
                        raise _error(self.program, value, f"{value.callee} arity")
                    self.emitted_derivative_nodes.append(value)
                    return f"glsl::{value.callee}(context, {arguments[0]})"
                if value.callee not in _BUILTIN_NAMES:
                    raise _error(self.program, value, f"unsupported builtin {value.callee}")
                if value.callee == "fract" and len(value.children) == 1:
                    fenced = self.hash_precision_fence(value.children[0])
                    if fenced is not None:
                        arguments = [fenced]
                return f"glsl::{_BUILTIN_NAMES[value.callee]}(" + ", ".join(arguments) + ")"
            if value.signature_id is None or value.signature_id not in self.function_names:
                raise _error(self.program, value, "call has no stable user signature")
            frame_contract_here = getattr(
                self, "authorized_frame_contract", None)
            if frame_contract_here is None:
                frame_contract_here = getattr(
                    self, "authorized_mutable_array_contract", None)
            prefix = ", ".join(
                ["state", "context"]
                + ([frame_contract_here.instance_name]
                   if frame_contract_here is not None else []))
            prefix += ", " if arguments else ""
            return f"{self.function_names[value.signature_id]}(" + prefix + ", ".join(arguments) + ")"
        if value.kind == "assign" and any(
                value is item for item in getattr(
                    self, "authorized_array_rvalue_assigns", ())):
            # cellRefract's two `return color *= dist;` forms, gated on object
            # identity against nodes resolved once during this emitter's own
            # authentication -- never a general `assign` arm. Same JS
            # semantics as the Shapes arm below: the compound assignment
            # stores then yields the stored value. The scalar Shapes form
            # `(rot *= PI)` cannot be reused here -- `glsl::Vec` defines no
            # compound-assignment operators -- so a vector target lowers
            # through the house assign form `tgt = glsl::Vec3(tgt * operand)`
            # (double lanes, per-lane f32 narrowing on store, exactly the JS
            # `color = color * dist`). Only `*=` is frozen for these nodes.
            if len(value.children) != 2:
                raise _error(self.program, value, "rvalue assignment arity")
            if value.operator != "*=":
                raise _error(self.program, value,
                             "rvalue assignment operator is not the frozen "
                             "compound product")
            target, operand = value.children
            self.emitted_array_rvalue_assigns.append(value)
            if target.type is not None and target.type.kind == "vector":
                return (f"({self.expression(target)} = glsl::Vec3("
                        f"{self.expression(target)} * "
                        f"{self.expression(operand)}))")
            return (f"({self.expression(target)} {value.operator} "
                    f"{self.expression(operand)})")
        if value.kind == "assign" and any(
                value is item for item in self.authorized_shapes_rvalue_assigns):
            # The ONE widened boundary of design amendment 2 (§12). Gated on
            # object identity against what this emitter's own call to
            # `authenticate_shapes_rvalue_assign` returned -- never a general
            # `assign` arm, so every other program still terminates at the
            # raise below. `assign` is already an approved capability and
            # `*=` an approved operator, so no vocabulary grows here.
            #
            # Lowering is read off the shipped transpiler, not inferred from
            # GLSL: canonicalFactory16 materializes this line as
            # `var angle = rot *= 3.1415927410125732;`, keeping the compound
            # assignment in rvalue position where sibling factories fold it to
            # `rot * <k>`. C++ `(rot *= k)` has identical semantics -- assign
            # then yield the new value -- and `rot` is an ordinary mutable
            # by-value parameter, exactly like `st` two lines below it.
            if len(value.children) != 2:
                raise _error(self.program, value, "rvalue assignment arity")
            target, operand = value.children
            self.emitted_shapes_rvalue_assigns.append(value)
            return (f"({self.expression(target)} {value.operator} "
                    f"{self.expression(operand)})")
        raise _error(self.program, value, f"unsupported typed expression {value.kind}")

    @staticmethod
    def _swizzle_base(value: TypedExpression, member: str) -> TypedExpression | None:
        if value.kind != "swizzle" or value.member != member or len(value.children) != 1:
            return None
        base = value.children[0]
        return base if base.kind == "id" and base.symbol_id is not None else None

    @staticmethod
    def _same_symbol(*values: TypedExpression) -> bool:
        return bool(values) and all(value.symbol_id == values[0].symbol_id for value in values)

    def _fenced_scalar_binary(self, left: str, operator: str, right: str) -> str:
        return f"static_cast<float>(static_cast<double>({left}) {operator} static_cast<double>({right}))"

    def hash_precision_fence(self, value: TypedExpression) -> str | None:
        """Emit only the two precision fences added by the canonical JS compiler.

        They are source-specific hash12/hash22 idioms, not general GLSL fract
        semantics.  Scatter is deliberately excluded by the canonical compiler.
        """
        if self.program.key.startswith("filter/scatter:") or value.kind != "binary" or value.operator != "*":
            return None

        if self.current_function_name == "hash12" and value.type.display() == "float":
            left, right = value.children
            if left.kind != "binary" or left.operator != "+":
                return None
            x = self._swizzle_base(left.children[0], "x")
            y = self._swizzle_base(left.children[1], "y")
            z = self._swizzle_base(right, "z")
            if x is None or y is None or z is None or not self._same_symbol(x, y, z):
                return None
            summed = self._fenced_scalar_binary(self.expression(left.children[0]), "+",
                                                 self.expression(left.children[1]))
            return self._fenced_scalar_binary(summed, "*", self.expression(right))

        if self.current_function_name == "hash22" and value.type.display() == "vec2":
            left, right = value.children
            if left.kind != "binary" or left.operator != "+":
                return None
            xx = self._swizzle_base(left.children[0], "xx")
            yz = self._swizzle_base(left.children[1], "yz")
            zy = self._swizzle_base(right, "zy")
            if xx is None or yz is None or zy is None or not self._same_symbol(xx, yz, zy):
                return None
            base = self.expression(xx)
            lane = lambda index: f"glsl::swizzle<{index}>({base})"
            lane0_sum = self._fenced_scalar_binary(lane(0), "+", lane(1))
            lane1_sum = self._fenced_scalar_binary(lane(0), "+", lane(2))
            lane0 = self._fenced_scalar_binary(lane0_sum, "*", lane(2))
            lane1 = self._fenced_scalar_binary(lane1_sum, "*", lane(1))
            return f"glsl::Vec2({lane0}, {lane1})"

        return None

    def lvalue(self, value: TypedExpression) -> tuple[str, str | None]:
        if value.kind == "id": return self.expression(value), None
        if value.kind == "index":
            if task20 := self._task20_index(value, "lvalue"):
                return task20, None
            if self._task18_dynamic_store(value):
                return (f"{self.expression(value.children[0])}"
                        f"[static_cast<std::size_t>("
                        f"{self.expression(value.children[1])})]", None)
            return self.expression(value), None
        if value.kind == "swizzle":
            if literal_lane := self._literal_lane_site(value):
                _, lane, role = literal_lane
                if role != "write":
                    raise _error(self.program, value,
                                 "literal vec3 lane read visited as write")
                return self.expression(value.children[0]), str(lane)
            target = self.expression(value.children[0])
            if not value.member or any(lane not in _SWIZZLE for lane in value.member):
                raise _error(self.program, value, "unsupported swizzle lvalue")
            return target, ", ".join(str(_SWIZZLE[lane]) for lane in value.member)
        raise _error(self.program, value, "unsupported lvalue")

    def _consume_shape_mixer_guard(self, value: TypedExpression) -> None:
        expected = self.authorized_shape_mixer_proof.blend_mode_guards
        index = len(self.emitted_shape_mixer_guards)
        if (index >= len(expected) or value is not expected[index]
                or index >= len(self.candidate_shape_mixer_guards)
                or value is not self.candidate_shape_mixer_guards[index]):
            raise _error(
                self.program, value,
                "authenticated Shape Mixer guard emission mismatch")
        self.emitted_shape_mixer_guards.append(value)

    def _emit_shape_mixer_body(
            self, value: TypedStatement, indent: str,
            loop_depth: int) -> list[str]:
        if any(value is item for item in self.emitted_shape_mixer_bodies):
            raise _error(
                self.program, value,
                "authenticated Shape Mixer body emitted twice")
        self.emitted_shape_mixer_bodies.append(value)
        if value.kind == "block":
            lines: list[str] = []
            for child in value.children:
                lines.extend(self.statement(child, indent, loop_depth))
            return lines
        return self.statement(value, indent, loop_depth)

    def _shape_mixer_balanced_statement(
            self, value: TypedStatement, indent: str,
            loop_depth: int) -> list[str] | None:
        matches = tuple(
            record for record in self.candidate_shape_mixer_ladders
            if value is record[0])
        if not matches:
            return None
        if len(matches) != 1:
            raise _error(
                self.program, value,
                "authenticated Shape Mixer root cardinality mismatch")
        root, guards, bodies = matches[0]
        if len(guards) != 10 or len(bodies) != 11:
            raise _error(
                self.program, value,
                "authenticated Shape Mixer ladder cardinality mismatch")
        self.emitted_shape_mixer_roots.append(root)
        for guard in guards:
            self._consume_shape_mixer_guard(guard)

        mode = self.expression(guards[0].children[0])
        literal = lambda index: self.expression(guards[index].children[1])
        lines = [
            f"{indent}if (({mode} < {literal(0)}) || "
            f"({mode} > {literal(9)})) {{"
        ]
        lines.extend(self._emit_shape_mixer_body(
            bodies[10], indent + "  ", loop_depth))
        lines.append(f"{indent}}} else if ({mode} < {literal(5)}) {{")
        lines.append(f"{indent}  if ({mode} < {literal(2)}) {{")
        lines.append(f"{indent}    if ({mode} == {literal(0)}) {{")
        lines.extend(self._emit_shape_mixer_body(
            bodies[0], indent + "      ", loop_depth))
        lines.append(f"{indent}    }} else {{")
        lines.extend(self._emit_shape_mixer_body(
            bodies[1], indent + "      ", loop_depth))
        lines.append(f"{indent}    }}")
        lines.append(f"{indent}  }} else if ({mode} == {literal(2)}) {{")
        lines.extend(self._emit_shape_mixer_body(
            bodies[2], indent + "    ", loop_depth))
        lines.append(f"{indent}  }} else if ({mode} == {literal(3)}) {{")
        lines.extend(self._emit_shape_mixer_body(
            bodies[3], indent + "    ", loop_depth))
        lines.append(f"{indent}  }} else {{")
        lines.extend(self._emit_shape_mixer_body(
            bodies[4], indent + "    ", loop_depth))
        lines.append(f"{indent}  }}")
        lines.append(f"{indent}}} else if ({mode} < {literal(8)}) {{")
        lines.append(f"{indent}  if ({mode} == {literal(5)}) {{")
        lines.extend(self._emit_shape_mixer_body(
            bodies[5], indent + "    ", loop_depth))
        lines.append(f"{indent}  }} else if ({mode} == {literal(6)}) {{")
        lines.extend(self._emit_shape_mixer_body(
            bodies[6], indent + "    ", loop_depth))
        lines.append(f"{indent}  }} else {{")
        lines.extend(self._emit_shape_mixer_body(
            bodies[7], indent + "    ", loop_depth))
        lines.append(f"{indent}  }}")
        lines.append(f"{indent}}} else {{")
        lines.append(f"{indent}  if ({mode} == {literal(8)}) {{")
        lines.extend(self._emit_shape_mixer_body(
            bodies[8], indent + "    ", loop_depth))
        lines.append(f"{indent}  }} else {{")
        lines.extend(self._emit_shape_mixer_body(
            bodies[9], indent + "    ", loop_depth))
        lines.append(f"{indent}  }}")
        lines.append(f"{indent}}}")
        return lines

    def statement(self, value: TypedStatement, indent: str = "  ",
                  loop_depth: int = 0) -> list[str]:
        balanced = self._shape_mixer_balanced_statement(
            value, indent, loop_depth)
        if balanced is not None:
            return balanced
        if value.kind == "block":
            lines = [f"{indent}{{"]
            for child in value.children:
                lines.extend(self.statement(child, indent + "  ", loop_depth))
            lines.append(f"{indent}}}")
            return lines
        if value.kind == "if":
            if len(value.expressions) != 1 or len(value.children) not in {1, 2}:
                raise _error(self.program, value, "malformed typed if")
            condition = self.expression(value.expressions[0])
            condition = condition if condition.startswith("(") and condition.endswith(")") else f"({condition})"
            lines = [f"{indent}if {condition} {{"]
            then = value.children[0]
            if then.kind == "block":
                for child in then.children:
                    lines.extend(self.statement(child, indent + "  ", loop_depth))
            else:
                lines.extend(self.statement(then, indent + "  ", loop_depth))
            if len(value.children) == 1:
                lines.append(f"{indent}}}")
                return lines
            lines.append(f"{indent}}} else {{")
            otherwise = value.children[1]
            if otherwise.kind == "block":
                for child in otherwise.children:
                    lines.extend(self.statement(child, indent + "  ", loop_depth))
            else:
                lines.extend(self.statement(otherwise, indent + "  ", loop_depth))
            lines.append(f"{indent}}}")
            return lines
        if value.kind == "for":
            remap_loop = (
                self.authorized_remap_proof is not None
                and any(value.loop_proof is item.proof
                        for item in self.authorized_remap_proof.loops))
            testpattern_loop = (
                self.authorized_testpattern_proof is not None
                and any(value is item
                        for item in self.authorized_testpattern_proof.consumed_objects
                        if getattr(item, "kind", None) == "for"
                        and item.loop_proof is None))
            if (self.authorized_remap_proof is not None and not remap_loop):
                raise _error(self.program, value,
                             "unauthenticated Remap counted-for statement")
            if ((value.loop_proof is None and not testpattern_loop and not remap_loop)
                    or len(value.expressions) != 2 or len(value.children) != 2):
                raise _error(self.program, value, "malformed counted-for statement")
            if remap_loop:
                if any(value is item for item in self.emitted_remap_loops):
                    raise _error(self.program, value,
                                 "authenticated Remap loop emitted twice")
                self.emitted_remap_loops.append(value)
            initializer, body = value.children
            assignment_form = False
            if (self.fractal_frontend_profile is not None
                    and initializer.kind == "expr"
                    and len(initializer.expressions) == 1
                    and initializer.expressions[0].kind == "assign"
                    and initializer.expressions[0].operator == "="
                    and len(initializer.expressions[0].children) == 2):
                assignment = initializer.expressions[0]
                left = assignment.children[0]
                if (left.kind != "id" or left.symbol is None
                        or left.symbol_id not in self.locals):
                    raise _error(self.program, initializer,
                                 "malformed authenticated Fractal loop initializer")
                name = self.locals[left.symbol_id]
                loop_type = left.type
                initial = (f"{self.expression(left)} = "
                           f"{self.expression(assignment.children[1])}")
                assignment_form = True
            else:
                if (initializer.kind != "decl" or len(initializer.expressions) != 1
                        or initializer.expressions[0].kind != "declaration"):
                    raise _error(self.program, value, "malformed counted-for initializer")
                declaration = initializer.expressions[0]
                if (declaration.symbol is None or declaration.symbol_id is None
                        or len(declaration.children) != 1):
                    raise _error(self.program, declaration, "malformed counted-for induction")
                name = _safe_identifier(declaration.symbol.name,
                                        declaration.symbol_id)
                self.locals[declaration.symbol_id] = name
                loop_type = declaration.type
                initial = self.expression(declaration.children[0])
            condition = self.expression(value.expressions[0])
            if assignment_form:
                lines = [f"{indent}for ({initial}; {condition}; ++{name}) {{"]
            else:
                lines = [
                    f"{indent}for ([[maybe_unused]] {self.local_type(loop_type)} "
                    f"{name} = {initial}; {condition}; ++{name}) {{"
                ]
            if body.kind == "block":
                for child in body.children:
                    lines.extend(self.statement(child, indent + "  ", loop_depth + 1))
            else:
                lines.extend(self.statement(body, indent + "  ", loop_depth + 1))
            lines.append(f"{indent}}}")
            return lines
        if value.kind == "while":
            if not self._median_while(value):
                raise _error(self.program, value,
                             "unauthenticated Median while statement")
            if len(value.expressions) != 1 or len(value.children) != 1:
                raise _error(self.program, value,
                             "malformed authenticated Median while")
            condition = self.expression(value.expressions[0])
            condition = condition if condition.startswith("(") and condition.endswith(")") else f"({condition})"
            lines = [f"{indent}while {condition} {{"]
            body = value.children[0]
            if body.kind == "block":
                for child in body.children:
                    lines.extend(self.statement(child, indent + "  ", loop_depth + 1))
            else:
                lines.extend(self.statement(body, indent + "  ", loop_depth + 1))
            lines.append(f"{indent}}}")
            return lines
        if value.kind in {"break", "continue"}:
            if loop_depth == 0:
                raise _error(self.program, value,
                             f"{value.kind} outside proved counted-for loop")
            return [f"{indent}{value.kind};"]
        if value.kind == "decl":
            if not value.expressions or any(item.kind != "declaration" for item in value.expressions):
                raise _error(self.program, value, "malformed typed declaration")
            lines = []
            for declaration in value.expressions:
                self._consume_glitch_matrix_object(declaration)
                self._consume_bitwise_number_expression(declaration)
                self._consume_edge_bvec_expression(declaration)
                if declaration.symbol is None or declaration.symbol_id is None:
                    raise _error(self.program, declaration, "declaration lacks stable symbol")
                def references_outer_same_name(expression: TypedExpression) -> bool:
                    return ((expression.kind == "id" and expression.symbol is not None
                             and expression.symbol.name == declaration.symbol.name
                             and expression.symbol_id != declaration.symbol_id)
                            or any(references_outer_same_name(child) for child in expression.children))
                emitted_name = _safe_identifier(declaration.symbol.name,
                                                declaration.symbol_id)
                if declaration.children and references_outer_same_name(declaration.children[0]):
                    emitted_name = f"{emitted_name}_{declaration.symbol_id}"
                self.locals[declaration.symbol_id] = emitted_name
                contract = self.runtime_loop_contract
                if (contract is not None and contract.kind == "blur-radius"
                        and declaration is contract.radius_declaration):
                    if self.runtime_radius_declaration_emitted:
                        raise _error(self.program, declaration,
                                     "runtime-loop-bound radius consumed more than once")
                    if (declaration.symbol != contract.seed.symbol
                            or declaration.type.display() != "int"):
                        raise _error(self.program, declaration,
                                     "runtime-loop-bound radius identity mismatch")
                    lines.append(
                        f"{indent}[[maybe_unused]] std::int32_t {emitted_name} = "
                        "state.runtime_loop_radius;")
                    self.runtime_radius_declaration_emitted = True
                    continue
                if declaration.type.kind == "array":
                    testpattern = self._testpattern_array(declaration)
                    if testpattern is not None:
                        proof = self.authorized_testpattern_proof
                        if declaration.symbol.name == "digits":
                            if (declaration.type.display() != "int[3]"
                                    or declaration.symbol.id != 72
                                    or declaration.children):
                                raise _error(
                                    self.program, declaration,
                                    "malformed Test Pattern digits declaration")
                            lines.append(
                                f"{indent}[[maybe_unused]] "
                                f"std::array<std::int32_t, 3> {emitted_name}{{}};")
                        elif declaration.symbol.name == "colors":
                            colors_initializer = next(
                                (item for item in proof.consumed_objects
                                 if getattr(item, "kind", None) == "construct"
                                 and getattr(item, "type", None) is not None
                                 and item.type.display() == "vec3[8]"),
                                None)
                            if (declaration.type.display() != "vec3[8]"
                                    or declaration.symbol.id != 44
                                    or len(declaration.children) != 1
                                    or declaration.children[0] is not colors_initializer):
                                raise _error(
                                    self.program, declaration,
                                    "malformed Test Pattern colors declaration")
                            initializer = self.expression(declaration.children[0])
                            lines.append(
                                f"{indent}[[maybe_unused]] "
                                f"std::array<glsl::Vec3, 8> {emitted_name} = "
                                f"{initializer};")
                        else:
                            raise _error(
                                self.program, declaration,
                                "unsupported Test Pattern array declaration")
                        self.emitted_testpattern_arrays.append(declaration)
                        continue
                    if declaration is self.authorized_newton_roots_declaration:
                        if (declaration.type.display() != "vec2[8]"
                                or declaration.symbol.id != 108
                                or declaration.children):
                            raise _error(
                                self.program, declaration,
                                "malformed authenticated Newton roots declaration")
                        lines.append(
                            f"{indent}[[maybe_unused]] std::array<glsl::Vec2, 8> "
                            f"{emitted_name}{{}};")
                        continue
                    median = self._median_array(declaration)
                    if median is not None:
                        native_type = ("glsl::UVec2"
                                       if declaration.type.display() == "uvec2[25]"
                                       else "std::uint32_t")
                        lines.append(
                            f"{indent}[[maybe_unused]] std::array<{native_type}, 25> "
                            f"{emitted_name}{{}};")
                        continue
                    task20 = self._task20_array(declaration.symbol_id)
                    array = self._proved_array(declaration.symbol_id)
                    grid = self._task18_array(declaration.symbol_id)
                    task19 = self._task19_table(declaration.symbol_id)
                    if task20 is not None:
                        if (declaration.children
                                or declaration.span != task20.declaration_span
                                or declaration.type.display() != task20.array_type
                                or declaration.symbol.id != task20.symbol_id
                                or declaration.symbol.name != task20.symbol_name):
                            raise _error(
                                self.program, declaration,
                                "unsupported fixed-affine centers13 declaration")
                        lines.append(
                            f"{indent}[[maybe_unused]] {task20.native_alias} "
                            f"{emitted_name}{{}};")
                        continue
                    if task19 is not None:
                        if (declaration.children
                                or declaration.span != task19.declaration_span
                                or declaration.type.display() != task19.array_type
                                or declaration.symbol.id != task19.symbol_id
                                or declaration.symbol.name != task19.symbol_name):
                            raise _error(
                                self.program, declaration,
                                "unsupported fixed-array input table declaration")
                        lines.append(
                            f"{indent}[[maybe_unused]] {task19.native_alias} "
                            f"{emitted_name}{{}};")
                        continue
                    if grid is not None:
                        if (declaration.children
                                or declaration.span != grid.array_declaration_span
                                or declaration.type.display() != grid.array_type
                                or declaration.symbol.id != grid.array_symbol_id
                                or declaration.symbol.name != grid.array_symbol_name):
                            raise _error(
                                self.program, declaration,
                                "unsupported fixed-grid array declaration")
                        lines.append(
                            f"{indent}[[maybe_unused]] std::array<"
                            f"{grid.native_element_type}, 9> {emitted_name}{{}};")
                        continue
                    if (array is None or declaration.children
                            or declaration.span != array.declaration_span
                            or declaration.type.display() != array.array_type
                            or declaration.symbol.id != array.symbol_id
                            or declaration.symbol.name != array.symbol_name):
                        raise _error(self.program, declaration,
                                     "unsupported fixed-nine array declaration")
                    emboss = getattr(self, "authorized_emboss_proof", None)
                    if (emboss is not None
                            and any(array is table
                                    for table in emboss.tables)):
                        if any(declaration is item
                               for item in self.emitted_emboss_declarations):
                            raise _error(
                                self.program, declaration,
                                "authenticated Emboss declaration emitted twice")
                        self.emitted_emboss_declarations.append(declaration)
                    lines.append(
                        f"{indent}[[maybe_unused]] std::array<{array.native_element_type}, 9> "
                        f"{emitted_name}{{}};")
                    continue
                initializer = self.expression(declaration.children[0]) if declaration.children else "{}"
                edge = self.authorized_edge_proof
                spooky = self.authorized_spooky_ticker_proof
                if (spooky is not None
                        and any(declaration is item
                                for item in spooky.number_declarations)):
                    if (declaration.type.display() not in {"int", "uint"}
                            or len(declaration.children) != 1):
                        raise _error(
                            self.program, declaration,
                            "malformed authenticated SpookyTicker Number declaration")
                    self.emitted_spooky_ticker_number_declarations.append(
                        declaration)
                    declaration_type = "double"
                elif (edge is not None
                        and any(declaration is item
                                for item in edge.declarations)):
                    if declaration.type.display() != "bvec3":
                        raise _error(
                            self.program, declaration,
                            "malformed authenticated Edge bvec3 declaration")
                    self.emitted_edge_declarations.append(declaration)
                    declaration_type = "glsl::BVec3"
                else:
                    declaration_type = self.local_type(declaration.type)
                if self._osd_js_number_declaration(declaration):
                    declaration_type = "double"
                    if declaration.symbol.name in {"glyph_idx", "gx", "gy"}:
                        if (len(declaration.children) != 1
                                or declaration.children[0].kind != "binary"
                                or declaration.children[0].operator != "/"):
                            raise _error(
                                self.program, declaration,
                                "malformed authenticated OSD Number division")
                        left, right = declaration.children[0].children
                        initializer = (
                            f"(static_cast<double>({self.expression(left)}) / "
                            f"static_cast<double>({self.expression(right)}))")
                out_abi = self.authorized_out_inout_argument_abis.get(
                    declaration.symbol_id)
                if out_abi is not None:
                    if not out_abi.endswith("&"):
                        raise _error(
                            self.program, declaration,
                            "authenticated out/inout argument ABI must be a reference")
                    declaration_type = out_abi[:-1]
                if (declaration.children
                        and declaration.type.display() in {"vec2", "vec3", "vec4"}
                        and self._ordinary_return_scalar_map_chain(declaration.children[0])
                        and declaration.symbol_id not in self.mutated_symbol_ids
                        # An alias source must stay a real Vec: a reference
                        # cannot bind to the FloatExpr proxy.
                        and declaration.symbol_id not in self.alias_source_symbol_ids):
                    declaration_type = f"glsl::FloatExpr<{declaration.type.display()[-1]}>"
                if declaration.symbol_id in self.alias_declaration_symbol_ids:
                    # A pooled-array alias, not a copy -- see
                    # `_collect_pooled_vector_aliases`. The source must be a
                    # local or parameter; anything else cannot be bound
                    # mutably from a `const State&` and is a defect in the
                    # collector rather than something to paper over here.
                    source_id = declaration.children[0].symbol_id
                    if source_id not in self.locals:
                        raise _error(
                            self.program, declaration,
                            "pooled vector alias source is not a local or parameter")
                    lines.append(
                        f"{indent}[[maybe_unused]] {declaration_type}& "
                        f"{emitted_name} = {initializer};")
                else:
                    lines.append(
                        f"{indent}[[maybe_unused]] {declaration_type} "
                        f"{emitted_name} = {initializer};")
            return lines
        if value.kind == "expr":
            if value.counter_proof is not None:
                update = value.expressions[0] if len(value.expressions) == 1 else None
                if (update is None or update.kind != "post" or update.operator != "++"
                        or len(update.children) != 1 or update.children[0].kind != "id"
                        or update.children[0].symbol_id
                        != value.counter_proof.target_symbol_id
                        or update.children[0].type.display() != "int"):
                    raise _error(self.program, value,
                                 "malformed discarded local-counter statement")
                return [f"{indent}++{self.expression(update.children[0])};"]
            grid = self.program.fixed_grid_counter_store_proof
            update = value.expressions[0] if len(value.expressions) == 1 else None
            if (grid is not None and update is not None
                    and value.span == grid.counter_update_statement_span
                    and update.span == grid.counter_update_expression_span):
                if (update.kind != "post" or update.operator != "++"
                        or len(update.children) != 1
                        or update.children[0].kind != "id"
                        or update.children[0].symbol_id != grid.counter_symbol_id
                        or update.children[0].type.display() != "int"):
                    raise _error(self.program, value,
                                 "malformed fixed-grid counter update")
                return [f"{indent}++{self.expression(update.children[0])};"]
            if (len(value.expressions) == 1 and value.expressions[0].kind == "call"
                    and self.authorized_inout_vec3_swap_proof is not None
                    and any(value.expressions[0] is item
                            for item in self.authorized_inout_vec3_swap_proof.calls)):
                call = value.expressions[0]
                self.emitted_inout_vec3_swap_calls.append(call)
                return [f"{indent}{self.expression(call)};"]
            if (len(value.expressions) == 1 and value.expressions[0].kind == "call"
                    and any(value.expressions[0] is item
                            for item in self.authorized_out_inout_calls)):
                call = value.expressions[0]
                if any(call is item for item in self.emitted_out_inout_calls):
                    raise _error(self.program, call,
                                 "authenticated out/inout call emitted twice")
                self.emitted_out_inout_calls.append(call)
                return [f"{indent}{self.expression(call)};"]
            if (len(value.expressions) == 1
                    and value.expressions[0].kind == "call"
                    and getattr(self, "authorized_array_writer_call", None)
                    is not None
                    and value.expressions[0]
                    is self.authorized_array_writer_call):
                # Design Amendment 12: `main`'s `loadKernels();` is a bare
                # expr statement wrapping a void call, and the grammar below
                # admits only assignments. This arm admits EXACTLY the one
                # frozen call node, resolved once during authentication and
                # gated here by object identity exactly like the inout-swap
                # arm above -- no generic void-call admission. The lowering
                # follows the ordinary call path, which supplies the frame
                # argument: `loadKernels(state, context, frame);`.
                call = value.expressions[0]
                self.emitted_array_writer_calls.append(call)
                return [f"{indent}{self.expression(call)};"]
            if (len(value.expressions) == 1
                    and value.expressions[0].kind == "post"
                    and self.authorized_median_frontend_proof is not None
                    and any(value.expressions[0] is item
                            for item in self.authorized_median_frontend_proof.expression_nodes
                            if item.kind == "post")):
                return [f"{indent}{self.expression(value.expressions[0])};"]
            if len(value.expressions) != 1 or value.expressions[0].kind != "assign":
                raise _error(self.program, value, "only typed assignments are admitted")
            assignment = value.expressions[0]
            self._consume_bitwise_number_expression(assignment)
            self._consume_emboss_expression(assignment)
            if assignment.operator not in _ASSIGNMENT_OPERATORS:
                raise _error(self.program, assignment,
                             f"unsupported assignment operator {assignment.operator}")
            glitch = self.authorized_glitch_proof
            if (glitch is not None
                    and assignment is glitch.ordered_freq_splat_assignment):
                # The canonical JS factory scalarises
                # `freq *= vec2(periodicFunction(...))` into two sequential
                # component stores.  The second call observes freq.x after
                # the first store through floor(st * freq), so evaluating the
                # scalar once and broadcasting it changes the sampled cell.
                if (self.current_function_name != "glitch"
                        or assignment.operator != "*="
                        or assignment.children != (
                            glitch.ordered_freq_splat_target,
                            glitch.ordered_freq_splat_constructor)
                        or glitch.ordered_freq_splat_target.kind != "id"
                        or glitch.ordered_freq_splat_target.symbol_id != 75
                        or glitch.ordered_freq_splat_target.type.display()
                        != "vec2"
                        or glitch.ordered_freq_splat_constructor.kind
                        != "construct"
                        or glitch.ordered_freq_splat_constructor.type.display()
                        != "vec2"
                        or len(glitch.ordered_freq_splat_constructor.children)
                        != 1):
                    raise _error(
                        self.program, assignment,
                        "malformed authenticated Glitch ordered freq splat")
                target = self.expression(glitch.ordered_freq_splat_target)
                scalar = self.expression(
                    glitch.ordered_freq_splat_constructor.children[0])
                return [
                    f"{indent}glsl::set_swizzle<0>({target}, "
                    f"(glsl::swizzle<0>({target}) * {scalar}));",
                    f"{indent}glsl::set_swizzle<1>({target}, "
                    f"(glsl::swizzle<1>({target}) * {scalar}));",
                ]
            glyph = self.authorized_glyph_map_proof
            if glyph is not None and assignment is glyph.self_assignment:
                if (assignment.operator != "=" or len(assignment.children) != 2
                        or assignment.children[0].kind != "id"
                        or assignment.children[1].kind != "id"
                        or assignment.children[0].symbol_id != 37
                        or assignment.children[1].symbol_id != 37):
                    raise _error(self.program, assignment,
                                 "malformed authenticated Glyph Map no-op")
                self.emitted_glyph_map_noops.append(assignment)
                return [f"{indent}(void){self.expression(assignment.children[0])};"]
            edge_splat = self.authorized_edge_splat_proof
            if (edge_splat is not None
                    and assignment is edge_splat.assignment):
                # The canonical JS factory expands
                # `centerSample = vec3(dot(centerSample, LUMA))` into three
                # sequential lane stores. Each later dot therefore observes
                # the earlier stores. Preserve that shipped evaluation order
                # only at this whole-program-authenticated Edge site.
                if (self.current_function_name != "main"
                        or assignment.operator != "="
                        or assignment.children != (
                            edge_splat.target, edge_splat.constructor)
                        or edge_splat.target.kind != "id"
                        or edge_splat.target.symbol_id != 59
                        or edge_splat.target.type.display() != "vec3"):
                    raise _error(self.program, assignment,
                                 "malformed authenticated Edge center splat")
                constructed = edge_splat.constructor
                if (constructed.kind != "construct"
                        or constructed.type.display() != "vec3"
                        or len(constructed.children) != 1):
                    raise _error(self.program, constructed,
                                 "malformed authenticated Edge center splat")
                dot = edge_splat.dot
                if (dot.kind != "builtin" or dot.callee != "dot"
                        or dot.type.display() != "float"
                        or len(dot.children) != 2
                        or dot.children[0].kind != "id"
                        or dot.children[0].symbol_id != 59
                        or dot.children[1].kind != "id"
                        or dot.children[1].symbol_id != 14):
                    raise _error(self.program, dot,
                                 "malformed authenticated Edge center splat")
                self.emitted_edge_splat_assignments.append(assignment)
                target = self.expression(edge_splat.target)
                right = self.expression(dot)
                return [
                    f"{indent}glsl::set_swizzle<0>({target}, {right});",
                    f"{indent}glsl::set_swizzle<1>({target}, {right});",
                    f"{indent}glsl::set_swizzle<2>({target}, {right});",
                ]
            cross_lane = self.authorized_cross_lane_assignment
            if cross_lane is not None and assignment is cross_lane.assignment:
                if (self.current_function_name != "main"
                        or assignment.operator != "="
                        or assignment.children != (cross_lane.target,
                                                   cross_lane.assignment.children[1])):
                    raise _error(self.program, assignment,
                                 "malformed authenticated cross-lane assignment")
                matrix = cross_lane.matrix
                if (matrix.kind != "construct" or len(matrix.children) != 4
                        or cross_lane.rhs_source.symbol_id != cross_lane.target_source.symbol_id):
                    raise _error(self.program, assignment,
                                 "malformed authenticated cross-lane dependency")
                target = self.expression(cross_lane.target)
                source = self.expression(cross_lane.rhs_source)
                c = self.expression(matrix.children[0])
                neg_s = self.expression(matrix.children[1])
                s = self.expression(matrix.children[2])
                first = (f"({c} * glsl::swizzle<0>({source}) + "
                         f"{s} * glsl::swizzle<1>({source}))")
                # The first store is intentionally visible through the alias;
                # lane 1 reads the destination's lane 0, just as canonical JS.
                second = (f"({neg_s} * glsl::swizzle<0>({target}) + "
                          f"{c} * glsl::swizzle<1>({source}))")
                self.emitted_cross_lane_assignments.append(assignment)
                return [
                    f"{indent}glsl::set_swizzle<0>({target}, {first});",
                    f"{indent}glsl::set_swizzle<1>({target}, {second});",
                ]
            mandelbrot_dz = (
                self.authorized_mandelbrot_sequential_dz_assignment)
            if (mandelbrot_dz is not None
                    and assignment is mandelbrot_dz.assignment):
                if (self.current_function_name != "mandelbrot_df64"
                        or assignment.operator != "="
                        or assignment.children != (
                            mandelbrot_dz.destination,
                            mandelbrot_dz.constructor)
                        or mandelbrot_dz.destination.type.display() != "vec2"
                        or mandelbrot_dz.constructor.type.display() != "vec2"
                        or len(mandelbrot_dz.constructor.children) != 2):
                    raise _error(
                        self.program, assignment,
                        "malformed authenticated Mandelbrot sequential dz assignment")
                target = self.expression(mandelbrot_dz.destination)
                first = self.expression(mandelbrot_dz.constructor.children[0])
                # Deliberately emit the second RHS after the first store. This
                # is the source-order aliasing contract: dz.y's lane computes
                # from dz.x after lane 0 has been written.
                second = self.expression(mandelbrot_dz.constructor.children[1])
                if len(self.emitted_mandelbrot_sequential_dz_assignment) != 0:
                    raise _error(
                        self.program, assignment,
                        "authenticated Mandelbrot sequential dz assignment emitted twice")
                self.emitted_mandelbrot_sequential_dz_assignment.append(assignment)
                return [
                    f"{indent}glsl::set_swizzle<0>({target}, {first});",
                    f"{indent}glsl::set_swizzle<1>({target}, {second});",
                ]
            if assignment is self.authorized_fractal_distance_map_assignment:
                total = self.authorized_fractal_distance_map_sum
                repeat_product = self.authorized_fractal_distance_repeat_product
                rotate_product = self.authorized_fractal_distance_rotate_product
                literal = self.authorized_fractal_distance_rotate_literal
                if (self.current_function_name != "main"
                        or assignment.operator != "="
                        or len(assignment.children) != 2
                        or assignment.children[0].kind != "id"
                        or assignment.children[0].symbol_id != 104
                        or assignment.children[1] is not total
                        or total is None or total.kind != "binary"
                        or total.operator != "+"
                        or total.children != (repeat_product, rotate_product)
                        or repeat_product is None
                        or repeat_product.kind != "binary"
                        or repeat_product.operator != "*"
                        or len(repeat_product.children) != 2
                        or repeat_product.children[0].kind != "id"
                        or repeat_product.children[0].symbol_id != 104
                        or repeat_product.children[1].kind != "id"
                        or repeat_product.children[1].symbol_id != 24
                        or rotate_product is None
                        or rotate_product.kind != "binary"
                        or rotate_product.operator != "*"
                        or len(rotate_product.children) != 2
                        or rotate_product.children[0].kind != "id"
                        or rotate_product.children[0].symbol_id != 23
                        or rotate_product.children[1] is not literal
                        or literal is None or literal.kind != "literal"
                        or literal.literal != "0.01"
                        or literal.literal_value != 0.01):
                    raise _error(
                        self.program, assignment,
                        "malformed authenticated Fractal distance map assignment")
                if self.emitted_fractal_distance_map_assignments:
                    raise _error(
                        self.program, assignment,
                        "authenticated Fractal distance map emitted twice")
                self.emitted_fractal_distance_map_assignments.append(assignment)
                target = self.expression(assignment.children[0])
                repeat = self.expression(repeat_product.children[1])
                rotate = self.expression(rotate_product.children[0])
                return [
                    f"{indent}{target} = ((static_cast<double>({target}) * "
                    f"static_cast<double>({repeat})) + "
                    f"(static_cast<double>({rotate}) * "
                    "static_cast<double>(0.01)));"
                ]
            if assignment is self.authorized_fractal_distance_fract_assignment:
                builtin = self.authorized_fractal_distance_fract_builtin
                if (self.current_function_name != "main"
                        or assignment.operator != "="
                        or len(assignment.children) != 2
                        or assignment.children[0].kind != "id"
                        or assignment.children[0].symbol_id != 104
                        or assignment.children[1] is not builtin
                        or builtin is None or builtin.kind != "builtin"
                        or builtin.callee != "fract"
                        or builtin.signature_id != -18
                        or len(builtin.children) != 1
                        or builtin.children[0].kind != "id"
                        or builtin.children[0].symbol_id != 104):
                    raise _error(
                        self.program, assignment,
                        "malformed authenticated Fractal distance fract assignment")
                if self.emitted_fractal_distance_fract_assignments:
                    raise _error(
                        self.program, assignment,
                        "authenticated Fractal distance fract emitted twice")
                self.emitted_fractal_distance_fract_assignments.append(assignment)
                target = self.expression(assignment.children[0])
                return [
                    f"{indent}{target} = (static_cast<double>({target}) - "
                    f"std::floor(static_cast<double>({target})));"
                ]
            if assignment is self.authorized_fractal_hue_scale_assignment:
                product = self.authorized_fractal_hue_scale_product
                literal = self.authorized_fractal_hue_scale_literal
                if (self.current_function_name != "main"
                        or assignment.operator != "*="
                        or len(assignment.children) != 2
                        or assignment.children[0].kind != "id"
                        or assignment.children[0].symbol_id != 104
                        or assignment.children[1] is not product
                        or product is None or product.kind != "binary"
                        or product.operator != "*"
                        or len(product.children) != 2
                        or product.children[0].kind != "id"
                        or product.children[0].symbol_id != 25
                        or product.children[0].symbol.name != "hueRange"
                        or product.children[1] is not literal
                        or literal is None or literal.kind != "literal"
                        or literal.literal != "0.01"
                        or literal.literal_value != 0.01):
                    raise _error(
                        self.program, assignment,
                        "malformed authenticated Fractal hue-scale assignment")
                if self.emitted_fractal_hue_scale_assignments:
                    raise _error(
                        self.program, assignment,
                        "authenticated Fractal hue-scale assignment emitted twice")
                self.emitted_fractal_hue_scale_assignments.append(assignment)
                target = self.expression(assignment.children[0])
                hue_range = self.expression(product.children[0])
                return [
                    f"{indent}{target} = ((static_cast<double>({target}) * "
                    f"static_cast<double>({hue_range})) * "
                    "static_cast<double>(0.01));"
                ]
            target, swizzle = self.lvalue(assignment.children[0])
            right = self.expression(assignment.children[1])
            operation = assignment.operator
            if operation == "^=":
                target_type = assignment.children[0].type.display()
                if any(assignment is item
                       for item in self.authorized_texture_frontend_assignments):
                    if (swizzle is not None or target_type != "uint"
                            or assignment.children[1].type.display() != "uint"):
                        raise _error(
                            self.program, assignment,
                            "malformed authenticated Texture bitwise assignment")
                    self.emitted_texture_frontend_assignments.append(assignment)
                    return [f"{indent}{target} = ({target} ^ {right});"]
                if swizzle is not None or target_type not in {"uvec2", "uvec3", "uvec4"}:
                    raise _error(self.program, assignment, "unsupported assignment operator ^=")
                return [f"{indent}{target} = glsl::bitwise_xor({target}, {right});"]
            if swizzle is None:
                vector_type = (self.type(assignment.children[0].type)
                               if assignment.children[0].type.display() in {"vec2", "vec3", "vec4"}
                               else None)
                if operation == "=":
                    if vector_type is not None: right = f"{vector_type}({right})"
                    return [f"{indent}{target} = {right};"]
                combined = f"({target} {operation[:-1]} {right})"
                if vector_type is not None: combined = f"{vector_type}({combined})"
                return [f"{indent}{target} = {combined};"]
            if operation == "=":
                return [f"{indent}glsl::set_swizzle<{swizzle}>({target}, {right});"]
            operator = operation[:-1]
            current = self.expression(assignment.children[0])
            return [f"{indent}glsl::set_swizzle<{swizzle}>({target}, ({current} {operator} {right}));"]
        if value.kind == "return":
            # A return inside a proved counted-for loop is admitted (landed with
            # filter/smooth:smoothBlend). C++ `return` from inside a `for` has
            # the same semantics as GLSL's, and the trip-count proof remains a
            # sound UPPER bound because an early return can only shorten the
            # iterations executed -- see the matching note in
            # generate_typed_slice.py and the soundness argument in
            # loop_proof.py. The validator is the authority on whether the
            # enclosing loop is proved; an unproved loop never reaches here.
            if len(value.expressions) == 0: return [f"{indent}return;"]
            if len(value.expressions) != 1: raise _error(self.program, value, "unsupported return")
            expression = self.expression(value.expressions[0])
            if self.current_function_signature_id in self.ordinary_array_return_signatures:
                lanes = value.expressions[0].type.display()[-1]
                expression = f"glsl::FloatExpr<{lanes}>({self.type(value.expressions[0].type)}({expression}))"
            return [f"{indent}return {expression};"]
        raise _error(self.program, value, f"unsupported typed statement {value.kind}")

    def _emitter_bound_parameters(self, function=None) -> list[str]:
        """The parameters the emitter binds on every helper of this program.

        A mutable-global-frame carrier gains exactly one more, at the frozen
        helper parameter ordinal from the closure's own contract -- `const
        Frame&`, never `Frame&`. The `const` is what turns the
        single-writer-is-`main` lock into a compiler-level enforcement: if that
        lock were ever wrong the build would fail rather than silently diverge.

        A mutable-global-array carrier binds the same ordinal-2 parameter with
        the polarity INVERTED on exactly one function: the writer alone takes
        `Frame&` (it performs the 45 stores, so no `[[maybe_unused]]` either);
        every other helper takes `[[maybe_unused]] const Frame&`. The
        single-writer-is-`loadKernels` lock becomes compiler-level enforcement
        the same way.
        """
        parameters = ["[[maybe_unused]] const State& state",
                      "[[maybe_unused]] const glsl::PixelContext& context"]
        contract = getattr(self, "authorized_frame_contract", None)
        if contract is not None:
            if contract.helper_parameter_ordinal != len(parameters):
                raise _error(self.program, self.program,
                             "mutable-global frame helper parameter ordinal mismatch")
            parameters.append(f"[[maybe_unused]] {contract.helper_parameter}")
            return parameters
        array_contract = getattr(self, "authorized_mutable_array_contract", None)
        if array_contract is None:
            return parameters
        if array_contract.helper_parameter_ordinal != len(parameters):
            raise _error(self.program, self.program,
                         "mutable-global array helper parameter ordinal mismatch")
        if function is not None and function.name == array_contract.writer_function:
            self.emitted_array_nonconst_frame_functions.append(function)
            parameters.append(array_contract.writer_parameter)
        else:
            parameters.append(f"[[maybe_unused]] {array_contract.helper_parameter}")
        return parameters

    def _palette_adapter_function(self, function) -> list[str] | None:
        proof = self.authorized_palette_frontend_proof
        if proof is None or function not in {
                proof.hsv_function, proof.oklab_function}:
            return None
        if (function.return_type.display() != "vec3"
                or len(function.parameters) != 1
                or function.parameters[0].type.display() != "vec3"):
            raise _error(self.program, function,
                         "malformed authenticated Palette adapter function")
        if function is proof.hsv_function:
            if (function.name != "hsv2rgb"
                    or self.emitted_palette_adapter_sites):
                raise _error(self.program, function,
                             "Palette HSV adapter emitted out of order")
            self.emitted_palette_adapter_sites.append(function)
            return [
                "[[nodiscard]] glsl::Vec3 hsv2rgb(",
                "    [[maybe_unused]] const State& state,",
                "    [[maybe_unused]] const glsl::PixelContext& context,",
                "    [[maybe_unused]] glsl::Vec3 hsv) noexcept {",
                "  const double h = hsv[0];",
                "  const double s = hsv[1];",
                "  const double v = hsv[2];",
                "  const double c = v * s;",
                "  const double hp = h * 6.0;",
                "  const double mod2 = hp - (2.0 * std::floor(hp / 2.0));",
                "  const double x = c * (1.0 - std::fabs(mod2 - 1.0));",
                "  const double m = v - c;",
                "  if (hp < 1.0) return glsl::Vec3(",
                "      noisemaker::f32(c + m), noisemaker::f32(x + m), noisemaker::f32(m));",
                "  if (hp < 2.0) return glsl::Vec3(",
                "      noisemaker::f32(x + m), noisemaker::f32(c + m), noisemaker::f32(m));",
                "  if (hp < 3.0) return glsl::Vec3(",
                "      noisemaker::f32(m), noisemaker::f32(c + m), noisemaker::f32(x + m));",
                "  if (hp < 4.0) return glsl::Vec3(",
                "      noisemaker::f32(m), noisemaker::f32(x + m), noisemaker::f32(c + m));",
                "  if (hp < 5.0) return glsl::Vec3(",
                "      noisemaker::f32(x + m), noisemaker::f32(m), noisemaker::f32(c + m));",
                "  return glsl::Vec3(",
                "      noisemaker::f32(c + m), noisemaker::f32(m), noisemaker::f32(x + m));",
                "}",
            ]
        if (function.name != "oklab2rgb"
                or not _same_object_sequence(
                    self.emitted_palette_adapter_sites,
                    (proof.hsv_function,))):
            raise _error(self.program, function,
                         "Palette Oklab adapter emitted out of order")
        self.emitted_palette_adapter_sites.append(function)
        return [
            "[[nodiscard]] glsl::Vec3 oklab2rgb(",
            "    [[maybe_unused]] const State& state,",
            "    [[maybe_unused]] const glsl::PixelContext& context,",
            "    [[maybe_unused]] glsl::Vec3 lab) noexcept {",
            "  const double L = lab[0];",
            "  const double a = (lab[1] * -0.509) + 0.276;",
            "  const double b = (lab[2] * -0.509) + 0.198;",
            "  const double l1 = (L + (0.3963377774 * a)) + (0.2158037573 * b);",
            "  const double m1 = (L - (0.1055613458 * a)) - (0.0638541728 * b);",
            "  const double s1 = (L - (0.0894841775 * a)) - (1.291485548 * b);",
            "  const double l = (l1 * l1) * l1;",
            "  const double m = (m1 * m1) * m1;",
            "  const double s = (s1 * s1) * s1;",
            "  const double red = ((4.0767416621 * l) - (3.3077115913 * m))",
            "                     + (0.2309699292 * s);",
            "  const double green = ((-1.2684380046 * l) + (2.6097574011 * m))",
            "                       - (0.3413193965 * s);",
            "  const double blue = ((-0.0041960863 * l) - (0.7034186147 * m))",
            "                      + (1.707614701 * s);",
            f"  const double srgbRed = {PALETTE_LINEAR_TO_SRGB_HELPER_NAME}(red);",
            f"  const double srgbGreen = {PALETTE_LINEAR_TO_SRGB_HELPER_NAME}(green);",
            f"  const double srgbBlue = {PALETTE_LINEAR_TO_SRGB_HELPER_NAME}(blue);",
            "  return glsl::Vec3(",
            "      noisemaker::f32(glsl::component_min<double>(",
            "          glsl::component_max<double>(srgbRed, 0.0), 1.0)),",
            "      noisemaker::f32(glsl::component_min<double>(",
            "          glsl::component_max<double>(srgbGreen, 0.0), 1.0)),",
            "      noisemaker::f32(glsl::component_min<double>(",
            "          glsl::component_max<double>(srgbBlue, 0.0), 1.0)));",
            "}",
        ]

    def _historic_palette_sample_function(self, function) -> list[str] | None:
        proof = self.authorized_historic_palette_proof
        if proof is None or function is not proof.sample_function:
            return None
        if (function.name != "sampleHistoricPalette"
                or function.return_type.display() != "vec3"
                or tuple(parameter.name for parameter in function.parameters)
                != ("pal", "lum", "smoothAmount")
                or tuple(parameter.type.display() for parameter in function.parameters)
                != ("HistoricPalette", "float", "float")
                or len(proof.sample_member_sites) != 7):
            raise _error(self.program, function,
                         "malformed authenticated Historic Palette sampler")
        if (self.emitted_historic_palette_adapter_sites
                or self.emitted_historic_palette_members):
            raise _error(self.program, function,
                         "Historic Palette adapter sampler emitted out of order")
        self.emitted_historic_palette_adapter_sites.append(function)
        self.emitted_historic_palette_members.extend(proof.sample_member_sites)
        return [
            "[[nodiscard]] glsl::Vec3 sampleHistoricPalette(",
            "    [[maybe_unused]] const State& state,",
            "    [[maybe_unused]] const glsl::PixelContext& context,",
            "    [[maybe_unused]] HistoricPalette pal,",
            "    [[maybe_unused]] double lum,",
            "    [[maybe_unused]] double smoothAmount) noexcept {",
            "  const double blendWidth = smoothAmount * 0.1;",
            f"  const double b1 = {HISTORIC_PALETTE_SMOOTHSTEP_HELPER_NAME}(",
            "      0.2 - blendWidth, 0.2 + blendWidth, lum);",
            f"  const double b2 = {HISTORIC_PALETTE_SMOOTHSTEP_HELPER_NAME}(",
            "      0.4 - blendWidth, 0.4 + blendWidth, lum);",
            f"  const double b3 = {HISTORIC_PALETTE_SMOOTHSTEP_HELPER_NAME}(",
            "      0.6 - blendWidth, 0.6 + blendWidth, lum);",
            f"  const double b4 = {HISTORIC_PALETTE_SMOOTHSTEP_HELPER_NAME}(",
            "      0.8 - blendWidth, 0.8 + blendWidth, lum);",
            "  glsl::Vec3 result(noisemaker::f32(pal.color1[0]),",
            "                    noisemaker::f32(pal.color1[1]),",
            "                    noisemaker::f32(pal.color1[2]));",
            "  for (std::size_t channel = 0; channel < 3U; ++channel) {",
            f"    result[channel] = {HISTORIC_PALETTE_MIX_STORE_HELPER_NAME}(",
            "        result[channel], pal.color2[channel], b1);",
            f"    result[channel] = {HISTORIC_PALETTE_MIX_STORE_HELPER_NAME}(",
            "        result[channel], pal.color3[channel], b2);",
            f"    result[channel] = {HISTORIC_PALETTE_MIX_STORE_HELPER_NAME}(",
            "        result[channel], pal.color4[channel], b3);",
            f"    result[channel] = {HISTORIC_PALETTE_MIX_STORE_HELPER_NAME}(",
            "        result[channel], pal.color5[channel], b4);",
            "  }",
            "  if (blendWidth > 0.0) {",
            "    const double distance = lum > 0.5 ? lum - 1.0 : lum;",
            f"    const double wrapFactor = {HISTORIC_PALETTE_SMOOTHSTEP_HELPER_NAME}(",
            "        -blendWidth, blendWidth, distance);",
            "    const double wrapMask = 1.0 -",
            f"        {HISTORIC_PALETTE_SMOOTHSTEP_HELPER_NAME}(",
            "            0.0, blendWidth, std::fabs(distance));",
            "    for (std::size_t channel = 0; channel < 3U; ++channel) {",
            "      const double wrapColor =",
            "          (pal.color5[channel] * (1.0 - wrapFactor))",
            "          + (pal.color1[channel] * wrapFactor);",
            f"      result[channel] = {HISTORIC_PALETTE_MIX_STORE_HELPER_NAME}(",
            "          result[channel], wrapColor, wrapMask);",
            "    }",
            "  }",
            "  return result;",
            "}",
        ]

    def _osd_pcg_function(self, function) -> list[str] | None:
        proof = self.authorized_osd_proof
        if proof is None or function is not proof.pcg_function:
            return None
        if (function.name != "pcg" or function.return_type.display() != "uint"
                or len(function.parameters) != 1
                or function.parameters[0].name != "v_in"
                or function.parameters[0].type.display() != "uint"):
            raise _error(self.program, function,
                         "malformed authenticated OSD pcg function")
        declarations = tuple(
            expression
            for statement in function.body
            for expression in statement.expressions
            if expression.kind == "declaration")
        if tuple(item.symbol.name for item in declarations) != ("state", "word"):
            raise _error(self.program, function,
                         "authenticated OSD pcg declaration census mismatch")
        state_name = _safe_identifier(declarations[0].symbol.name,
                                      declarations[0].symbol_id)
        word_name = _safe_identifier(declarations[1].symbol.name,
                                     declarations[1].symbol_id)
        self.emitted_osd_bitwise.extend(proof.pcg_bitwise_nodes)
        return [
            "[[nodiscard]] std::uint32_t pcg([[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] std::uint32_t v_in) noexcept {",
            f"  [[maybe_unused]] double {state_name} = "
            "static_cast<double>(std::uint32_t(v_in) * "
            "std::uint32_t(747796405)) + "
            "static_cast<double>(std::uint32_t(2891336453));",
            f"  [[maybe_unused]] double pcg_shift = "
            f"glsl::detail::js_shift_right({state_name}, std::uint32_t(28));",
            f"  [[maybe_unused]] double pcg_word_shift = "
            f"glsl::detail::js_shift_right({state_name}, "
            "static_cast<double>(pcg_shift) + static_cast<double>("
            "std::uint32_t(4)));",
            "  [[maybe_unused]] std::int32_t pcg_xor = "
            "glsl::detail::js_bitwise_xor(pcg_word_shift, "
            f"{state_name});",
            f"  [[maybe_unused]] double {word_name} = "
            "static_cast<double>(pcg_xor) * static_cast<double>(std::uint32_t("
            "277803737));",
            "  return static_cast<std::uint32_t>(glsl::detail::js_bitwise_xor("
            "glsl::detail::js_shift_right(" + word_name + ", "
            "std::uint32_t(22)), " + word_name + "));",
            "}",
        ]

    def _spooky_ticker_hash_mix_function(self, function) -> list[str] | None:
        proof = self.authorized_spooky_ticker_proof
        if proof is None:
            return None
        hash_function = next(
            item for item in proof.closure_functions
            if item.name == "hash_mix")
        if function is not hash_function:
            return None
        parameter = function.parameters[0] if len(function.parameters) == 1 else None
        if (function.name != "hash_mix"
                or function.return_type.display() != "uint"
                or parameter is not proof.number_parameters[0]
                or parameter.name != "v" or parameter.id != 14
                or parameter.type.display() != "uint"
                or tuple(item.operator for item in proof.bitwise_nodes[:6])
                != ("^", ">>", "^", ">>", "^", ">>")
                or tuple(item.operator for item in proof.number_umul_nodes)
                != ("*", "*")):
            raise _error(
                self.program, function,
                "malformed authenticated SpookyTicker hash_mix function")
        self.emitted_spooky_ticker_number_parameters.append(parameter)
        self.emitted_spooky_ticker_bitwise.extend(proof.bitwise_nodes[:6])
        self.emitted_spooky_ticker_number_umuls.extend(
            proof.number_umul_nodes)
        self.emitted_spooky_ticker_hash_definitions += 1
        return [
            "[[nodiscard]] double hash_mix([[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] double v) noexcept {",
            "  v = glsl::detail::js_bitwise_xor("
            "v, glsl::detail::js_shift_right(v, std::uint32_t(16)));",
            "  v = glsl::detail::js_umul(v, std::uint32_t(2146121005));",
            "  v = glsl::detail::js_bitwise_xor("
            "v, glsl::detail::js_shift_right(v, std::uint32_t(15)));",
            "  v = glsl::detail::js_umul(v, std::uint32_t(2221713035));",
            "  v = glsl::detail::js_bitwise_xor("
            "v, glsl::detail::js_shift_right(v, std::uint32_t(16)));",
            "  return v;",
            "}",
        ]

    def _consume_fractal_number_anchors(self, helper: str) -> None:
        if helper == "julia":
            authorized = self.authorized_fractal_julia_number_anchors
            emitted = self.emitted_fractal_julia_number_anchors
            expected_spans = JULIA_NUMBER_ANCHOR_SPANS
        else:
            authorized = self.authorized_fractal_mandelbrot_number_anchors
            emitted = self.emitted_fractal_mandelbrot_number_anchors
            expected_spans = MANDELBROT_NUMBER_ANCHOR_SPANS
        spans = tuple(
            f"{item.span.start_line}:{item.span.start_column}-"
            f"{item.span.end_line}:{item.span.end_column}"
            for item in authorized)
        if spans != expected_spans:
            raise _error(
                self.program, self.program,
                f"authenticated Fractal Number {helper} anchor identity mismatch")
        if emitted:
            raise _error(
                self.program, self.program,
                f"authenticated Fractal Number {helper} anchors emitted twice")
        emitted.extend(authorized)

    def _fractal_julia_number_function(self, function) -> list[str] | None:
        julia_function = self.authorized_fractal_julia_function
        if julia_function is None or function is not julia_function:
            return None
        parameter = self.authorized_fractal_julia_parameter
        if (function.name != "julia"
                or function.signature.id != 61
                or function.return_type.display() != "float"
                or len(function.parameters) != 1
                or function.parameters[0] is not parameter
                or parameter is None or parameter.name != "st"
                or parameter.id != 55 or parameter.type.display() != "vec2"
                or parameter.direction != "in"):
            raise _error(
                self.program, function,
                "malformed authenticated Fractal Number Julia function")
        self._consume_fractal_number_anchors("julia")
        self.emitted_fractal_julia_definitions += 1
        return [
            "[[nodiscard]] double julia("
            "[[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] double input_x, "
            "[[maybe_unused]] double input_y) noexcept {",
            "  [[maybe_unused]] const auto map_number = "
            "[](double value, double in_min, double in_max, "
            "double out_min, double out_max) noexcept {",
            "    return out_min + (out_max - out_min) * "
            "(value - in_min) / (in_max - in_min);",
            "  };",
            "  [[maybe_unused]] const auto hypot_number = "
            "[](double value_x, double value_y) noexcept {",
            "    [[maybe_unused]] const double maximum = "
            "std::fmax(std::fabs(value_x), std::fabs(value_y));",
            "    if (std::isinf(maximum)) return maximum;",
            "    if (maximum == 0.0) return 0.0;",
            "    [[maybe_unused]] const double scaled_x = value_x / maximum;",
            "    [[maybe_unused]] const double scaled_y = value_y / maximum;",
            "    return std::sqrt(scaled_x * scaled_x + "
            "scaled_y * scaled_y) * maximum;",
            "  };",
            "  [[maybe_unused]] const double aspect = "
            "(static_cast<double>(state.fullResolution[0]) / "
            "static_cast<double>(state.fullResolution[1]));",
            "  [[maybe_unused]] const double zoom = "
            "map_number(static_cast<double>(state.zoomAmt), 0.0, 100.0, "
            "2.0, 0.5);",
            "  [[maybe_unused]] const double speedy = "
            "map_number(static_cast<double>(state.speed), 0.0, 100.0, "
            "0.0, 1.0);",
            "  [[maybe_unused]] const double speed = "
            "(speedy * 0.05) * (1.0 - speedy) + "
            "(speedy * 0.125) * speedy;",
            "  [[maybe_unused]] const double cx = "
            "noisemaker::fdlibm::sin(static_cast<double>(state.time) * "
            "6.28318530718) * speed + "
            "map_number(static_cast<double>(state.offsetX), -100.0, 100.0, "
            "-0.5, 0.5);",
            "  [[maybe_unused]] const double cy = "
            "noisemaker::fdlibm::cos(static_cast<double>(state.time) * "
            "6.28318530718) * speed + "
            "map_number(static_cast<double>(state.offsetY), -100.0, 100.0, "
            "-1.0, 1.0);",
            "  [[maybe_unused]] const double angle = "
            "map_number(static_cast<double>(state.rotation), 0.0, 360.0, "
            "0.0, 2.0) * 3.14159265359;",
            "  [[maybe_unused]] const double px = input_x - 0.5 * aspect;",
            "  [[maybe_unused]] const double py = input_y - 0.5;",
            "  [[maybe_unused]] const double cs = "
            "noisemaker::fdlibm::cos(angle);",
            "  [[maybe_unused]] const double sn = "
            "noisemaker::fdlibm::sin(angle);",
            "  [[maybe_unused]] double x = "
            "cs * px + sn * py + 0.5 * aspect;",
            "  [[maybe_unused]] double y = "
            "-sn * px + cs * py + 0.5;",
            "  x = (x - 0.5 * aspect) * zoom + "
            "map_number(static_cast<double>(state.centerX), -100.0, 100.0, "
            "1.0, -1.0);",
            "  y = (y - 0.5) * zoom + "
            "map_number(static_cast<double>(state.centerY), -100.0, 100.0, "
            "1.0, -1.0);",
            "  [[maybe_unused]] const std::int32_t count = "
            "state.iterations * std::int32_t(2);",
            "  [[maybe_unused]] std::int32_t iteration = 0;",
            "  for ([[maybe_unused]] std::int32_t index = 0; "
            "index < count; ++index) {",
            "    iteration = index;",
            "    [[maybe_unused]] const double next_x = "
            "x * x - y * y + cx;",
            "    [[maybe_unused]] const double next_y = "
            "y * x + x * y + cy;",
            "    if (next_x * next_x + next_y * next_y > 4.0) break;",
            "    x = next_x;",
            "    y = next_y;",
            "  }",
            "  if (count - iteration < glsl::detail::js_to_int32(" 
            "static_cast<double>(state.cutoff))) return 1.0;",
            "  if (state.mode == std::int32_t(0)) {",
            "    return static_cast<double>(iteration) / "
            "static_cast<double>(count);",
            "  }",
            "  if (state.mode == std::int32_t(1)) return hypot_number(x, y);",
            "  // Fractal mode contract [0,1]; unreachable terminal fallback.",
            "  return 0.0;",
            "}",
        ]

    def _fractal_mandelbrot_number_function(self, function) -> list[str] | None:
        mandelbrot_function = self.authorized_fractal_mandelbrot_function
        if (mandelbrot_function is None
                or function is not mandelbrot_function):
            return None
        parameter = self.authorized_fractal_mandelbrot_parameter
        matrix = self.authorized_fractal_mat2_constructor
        if (function.name != "mandelbrot"
                or function.signature.id != 65
                or function.return_type.display() != "float"
                or len(function.parameters) != 1
                or function.parameters[0] is not parameter
                or parameter is None or parameter.name != "st"
                or parameter.id != 56 or parameter.type.display() != "vec2"
                or parameter.direction != "in"
                or matrix is None):
            raise _error(
                self.program, function,
                "malformed authenticated Fractal Number Mandelbrot function")
        self._consume_fractal_number_anchors("mandelbrot")
        if self.emitted_fractal_mandelbrot_matrix_consumptions:
            raise _error(
                self.program, function,
                "authenticated Fractal Mandelbrot matrix consumed twice")
        self.emitted_fractal_mandelbrot_matrix_consumptions.append(matrix)
        self.emitted_fractal_mandelbrot_definitions += 1
        return [
            "[[nodiscard]] double mandelbrot("
            "[[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] double input_x, "
            "[[maybe_unused]] double input_y) noexcept {",
            "  [[maybe_unused]] const auto map_number = "
            "[](double value, double in_min, double in_max, "
            "double out_min, double out_max) noexcept {",
            "    return out_min + (out_max - out_min) * "
            "(value - in_min) / (in_max - in_min);",
            "  };",
            "  [[maybe_unused]] const auto hypot_number = "
            "[](double value_x, double value_y) noexcept {",
            "    [[maybe_unused]] const double maximum = "
            "std::fmax(std::fabs(value_x), std::fabs(value_y));",
            "    if (std::isinf(maximum)) return maximum;",
            "    if (maximum == 0.0) return 0.0;",
            "    [[maybe_unused]] const double scaled_x = value_x / maximum;",
            "    [[maybe_unused]] const double scaled_y = value_y / maximum;",
            "    return std::sqrt(scaled_x * scaled_x + "
            "scaled_y * scaled_y) * maximum;",
            "  };",
            "  [[maybe_unused]] const double aspect = "
            "(static_cast<double>(state.fullResolution[0]) / "
            "static_cast<double>(state.fullResolution[1]));",
            "  [[maybe_unused]] const double zoom = "
            "map_number(static_cast<double>(state.zoomAmt), 0.0, 100.0, "
            "2.0, 0.5);",
            "  [[maybe_unused]] const double speedy = "
            "map_number(static_cast<double>(state.speed), 0.0, 100.0, "
            "0.0, 1.0);",
            "  [[maybe_unused]] const double speed = "
            "(speedy * 0.05) * (1.0 - speedy) + "
            "(speedy * 0.125) * speedy;",
            "  [[maybe_unused]] const double angle = "
            "map_number(static_cast<double>(state.rotation), 0.0, 360.0, "
            "0.0, 2.0) * 3.14159265359;",
            "  [[maybe_unused]] const double px = input_x - 0.5 * aspect;",
            "  [[maybe_unused]] const double py = input_y - 0.5;",
            "  [[maybe_unused]] const double cs = "
            "noisemaker::fdlibm::cos(angle);",
            "  [[maybe_unused]] const double sn = "
            "noisemaker::fdlibm::sin(angle);",
            "  [[maybe_unused]] double x = "
            "cs * px + sn * py + 0.5 * aspect;",
            "  [[maybe_unused]] double y = "
            "-sn * px + cs * py + 0.5;",
            "  y = y * 2.0 - 1.0;",
            "  x = x * 2.0 - aspect;",
            "  [[maybe_unused]] const double cx = zoom * x - "
            "(static_cast<double>(state.centerX) + 50.0) * 0.01;",
            "  [[maybe_unused]] const double cy = zoom * y - "
            "static_cast<double>(state.centerY) * 0.01;",
            "  x = noisemaker::fdlibm::sin(static_cast<double>(state.time) * "
            "6.28318530718) * speed;",
            "  y = noisemaker::fdlibm::cos(static_cast<double>(state.time) * "
            "6.28318530718) * speed;",
            "  [[maybe_unused]] std::int32_t iteration = 0;",
            "  for (; iteration < state.iterations; ++iteration) {",
            "    [[maybe_unused]] const double next_x = "
            "x * x - y * y + cx;",
            "    [[maybe_unused]] const double next_y = "
            "2.0 * x * y + cy;",
            "    x = next_x;",
            "    y = next_y;",
            "    if (x * x + y * y > 16.0) break;",
            "  }",
            "  if (iteration == state.iterations) return 1.0;",
            "  if (state.mode == std::int32_t(0)) {",
            "    return static_cast<double>(iteration) / "
            "static_cast<double>(state.iterations);",
            "  }",
            "  if (state.mode == std::int32_t(1)) {",
            "    return hypot_number(x, y) / "
            "static_cast<double>(state.iterations);",
            "  }",
            "  // Fractal mode contract [0,1]; unreachable terminal fallback.",
            "  return 0.0;",
            "}",
        ]

    def _fractal_newton_number_function(self, function) -> list[str] | None:
        newton_function = self.authorized_fractal_newton_function
        if newton_function is None or function is not newton_function:
            return None
        parameter = self.authorized_fractal_newton_parameter
        if (function.name != "newton" or function.signature.id != 67
                or function.return_type.display() != "float"
                or len(function.parameters) != 1
                or function.parameters[0] is not parameter
                or parameter is None or parameter.name != "st"
                or parameter.id != 54 or parameter.type.display() != "vec2"
                or parameter.direction != "in"):
            raise _error(
                self.program, function,
                "malformed authenticated Fractal Number Newton function")
        self.emitted_fractal_newton_definitions += 1
        return [
            "[[nodiscard]] double newton("
            "[[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] double input_x, "
            "[[maybe_unused]] double input_y) noexcept {",
            "  [[maybe_unused]] const auto map_number = "
            "[](double value, double in_min, double in_max, "
            "double out_min, double out_max) noexcept {",
            "    return out_min + (out_max - out_min) * "
            "(value - in_min) / (in_max - in_min);",
            "  };",
            "  [[maybe_unused]] const auto hypot_number = "
            "[](double value_x, double value_y) noexcept {",
            "    [[maybe_unused]] const double maximum = "
            "std::fmax(std::fabs(value_x), std::fabs(value_y));",
            "    if (std::isinf(maximum)) return maximum;",
            "    if (maximum == 0.0) return 0.0;",
            "    [[maybe_unused]] const double scaled_x = value_x / maximum;",
            "    [[maybe_unused]] const double scaled_y = value_y / maximum;",
            "    return std::sqrt(scaled_x * scaled_x + "
            "scaled_y * scaled_y) * maximum;",
            "  };",
            "  [[maybe_unused]] const double aspect = "
            "(static_cast<double>(state.fullResolution[0]) / "
            "static_cast<double>(state.fullResolution[1]));",
            "  [[maybe_unused]] const double angle = "
            "map_number(state.rotation + 90.0, 0.0, 360.0, 0.0, 2.0) * "
            "3.14159265359;",
            "  [[maybe_unused]] const double px = input_x - 0.5 * aspect;",
            "  [[maybe_unused]] const double py = input_y - 0.5;",
            "  [[maybe_unused]] const double cs = noisemaker::fdlibm::cos(angle);",
            "  [[maybe_unused]] const double sn = noisemaker::fdlibm::sin(angle);",
            "  [[maybe_unused]] double x = "
            "cs * px + sn * py + 0.5 * aspect;",
            "  [[maybe_unused]] double y = "
            "-sn * px + cs * py + 0.5;",
            "  [[maybe_unused]] const double zoom = "
            "map_number(state.zoomAmt, 0.0, 130.0, 1.0, 0.01);",
            "  x = (x - 0.5 * aspect) * zoom + state.centerY * 0.01;",
            "  y = (y - 0.5) * zoom + state.centerX * 0.01;",
            "  [[maybe_unused]] const double speed = "
            "map_number(state.speed, 0.0, 100.0, 0.0, 1.0);",
            "  [[maybe_unused]] const double offset_x = "
            "map_number(state.offsetX, -100.0, 100.0, -0.25, 0.25);",
            "  [[maybe_unused]] const double offset_y = "
            "map_number(state.offsetY, -100.0, 100.0, -0.25, 0.25);",
            "  [[maybe_unused]] std::int32_t iteration = 0;",
            "  for ([[maybe_unused]] std::int32_t index = 0; "
            "index < state.iterations; ++index) {",
            "    [[maybe_unused]] const double fx = "
            "x * x * x - 3.0 * x * y * y - 1.0;",
            "    [[maybe_unused]] const double fy = "
            "3.0 * x * x * y - y * y * y;",
            "    [[maybe_unused]] const double fpx = "
            "3.0 * x * x - 3.0 * y * y;",
            "    [[maybe_unused]] const double fpy = 6.0 * x * y;",
            "    [[maybe_unused]] const double denominator = "
            "fpx * fpx + fpy * fpy;",
            "    [[maybe_unused]] double tx = "
            "(fx * fpx + fy * fpy) / denominator;",
            "    [[maybe_unused]] double ty = "
            "(fy * fpx - fx * fpy) / denominator;",
            "    tx += noisemaker::fdlibm::sin(state.time * 6.28318530718) * "
            "0.1 * speed + offset_x;",
            "    ty += noisemaker::fdlibm::cos(state.time * 6.28318530718) * "
            "0.1 * speed + offset_y;",
            "    if (hypot_number(tx, ty) < 0.001) break;",
            "    x -= tx;",
            "    y -= ty;",
            "    iteration += 1;",
            "  }",
            "  if (state.mode == std::int32_t(0)) {",
            "    return static_cast<double>(iteration) / "
            "static_cast<double>(state.iterations);",
            "  }",
            "  if (state.mode == std::int32_t(1)) return hypot_number(x, y);",
            "  // Fractal mode contract [0,1]; unreachable terminal fallback.",
            "  return 0.0;",
            "}",
        ]

    def _fractal_hsv_number_function(self, function) -> list[str] | None:
        hsv_function = self.authorized_fractal_hsv_function
        if hsv_function is None or function is not hsv_function:
            return None
        parameter = self.authorized_fractal_hsv_parameter
        if (function.name != "hsv2rgb"
                or function.signature.id != 60
                or function.return_type.display() != "vec3"
                or len(function.parameters) != 1
                or function.parameters[0] is not parameter
                or parameter is None or parameter.name != "hsv"
                or parameter.id != 40 or parameter.type.display() != "vec3"
                or parameter.direction != "in"):
            raise _error(
                self.program, function,
                "malformed authenticated Fractal Number HSV function")
        self.emitted_fractal_hsv_definitions += 1
        return [
            "[[nodiscard]] glsl::Vec3 hsv2rgb("
            "[[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] glsl::FloatExpr<3> hsv) noexcept {",
            "  [[maybe_unused]] double h = (hsv[0] - std::floor(hsv[0]));",
            "  [[maybe_unused]] double s = hsv[1];",
            "  [[maybe_unused]] double v = hsv[2];",
            "  [[maybe_unused]] double c = (v * s);",
            "  [[maybe_unused]] double h6 = (h * 6.0);",
            "  [[maybe_unused]] double hue_mod = "
            "(h6 - (2.0 * std::floor(h6 / 2.0)));",
            "  [[maybe_unused]] double x = "
            "(c * (1.0 - std::fabs(hue_mod - 1.0)));",
            "  [[maybe_unused]] double m = (v - c);",
            "  if (h < (1.0 / 6.0)) "
            "return glsl::Vec3(glsl::FloatExpr<3>(c + m, x + m, m));",
            "  if (h < (2.0 / 6.0)) "
            "return glsl::Vec3(glsl::FloatExpr<3>(x + m, c + m, m));",
            "  if (h < (3.0 / 6.0)) "
            "return glsl::Vec3(glsl::FloatExpr<3>(m, c + m, x + m));",
            "  if (h < (4.0 / 6.0)) "
            "return glsl::Vec3(glsl::FloatExpr<3>(m, x + m, c + m));",
            "  if (h < (5.0 / 6.0)) "
            "return glsl::Vec3(glsl::FloatExpr<3>(x + m, m, c + m));",
            "  return glsl::Vec3(glsl::FloatExpr<3>(c + m, m, x + m));",
            "}",
        ]

    def _fractal_palette_number_function(self, function) -> list[str] | None:
        palette_function = self.authorized_fractal_palette_function
        if palette_function is None or function is not palette_function:
            return None
        parameter = self.authorized_fractal_palette_parameter
        if (function.name != "pal" or function.signature.id != 70
                or function.return_type.display() != "vec3"
                or len(function.parameters) != 1
                or function.parameters[0] is not parameter
                or parameter is None or parameter.name != "t"
                or parameter.id != 49 or parameter.type.display() != "float"
                or parameter.direction != "in"):
            raise _error(
                self.program, function,
                "malformed authenticated Fractal Number palette function")
        hsv_call = (self.authorized_fractal_hsv_calls[0]
                    if len(self.authorized_fractal_hsv_calls) == 2 else None)
        if (hsv_call is None or hsv_call.kind != "call"
                or hsv_call.signature_id != 60
                or len(hsv_call.children) != 1
                or hsv_call.children[0].kind != "id"
                or hsv_call.children[0].symbol_id != 124
                or self.emitted_fractal_hsv_calls):
            raise _error(
                self.program, function,
                "malformed authenticated Fractal palette HSV call")
        self.emitted_fractal_hsv_calls.append(hsv_call)
        self.emitted_fractal_palette_adapter_paths += 1
        lines = [
            "[[nodiscard]] glsl::Vec3 pal("
            "[[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] double t) noexcept {",
            "  [[maybe_unused]] glsl::Vec3 adapter_color = {};",
        ]
        lines.extend(
            f"  adapter_color[{lane}] = noisemaker::f32("
            f"static_cast<double>(state.paletteOffset[{lane}]) + "
            f"static_cast<double>(state.paletteAmp[{lane}]) * "
            "noisemaker::fdlibm::cos(6.28318 * ("
            f"static_cast<double>(state.paletteFreq[{lane}]) * t + "
            f"static_cast<double>(state.palettePhase[{lane}]))));"
            for lane in range(3))
        lines.extend([
            "  if (state.paletteMode == std::int32_t(1)) {",
            "    return hsv2rgb(state, context, glsl::FloatExpr<3>(adapter_color));",
            "  }",
            "  if (state.paletteMode == std::int32_t(2)) {",
            "    [[maybe_unused]] const double L = adapter_color[0];",
            "    [[maybe_unused]] const double a = "
            "(static_cast<double>(adapter_color[1]) * -0.509 + 0.276);",
            "    [[maybe_unused]] const double b = "
            "(static_cast<double>(adapter_color[2]) * -0.509 + 0.198);",
            "    [[maybe_unused]] const double l1 = "
            "(L + 0.3963377774 * a + 0.2158037573 * b);",
            "    [[maybe_unused]] const double m1 = "
            "(L - 0.1055613458 * a - 0.0638541728 * b);",
            "    [[maybe_unused]] const double s1 = "
            "(L - 0.0894841775 * a - 1.291485548 * b);",
            "    [[maybe_unused]] const double l = (l1 * l1 * l1);",
            "    [[maybe_unused]] const double m = (m1 * m1 * m1);",
            "    [[maybe_unused]] const double s = (s1 * s1 * s1);",
            "    [[maybe_unused]] const auto linear_to_srgb_number = "
            "[](double value) noexcept {",
            "      return value <= 0.0031308 ? value * 12.92 : "
            "1.055 * std::pow(value, 1.0 / 2.4) - 0.055;",
            "    };",
            "    adapter_color[0] = noisemaker::f32(linear_to_srgb_number("
            "4.0767245293 * l - 3.3072168827 * m + 0.2307590544 * s));",
            "    adapter_color[1] = noisemaker::f32(linear_to_srgb_number("
            "-1.2681437731 * l + 2.6093323231 * m - 0.341134429 * s));",
            "    adapter_color[2] = noisemaker::f32(linear_to_srgb_number("
            "-0.0041119885 * l - 0.7034763098 * m + 1.7068625689 * s));",
            "  }",
            "  return adapter_color;",
            "}",
        ])
        return lines

    def function(self, function) -> list[str]:
        palette_adapter = self._palette_adapter_function(function)
        if palette_adapter is not None:
            return palette_adapter
        historic_palette_sample = self._historic_palette_sample_function(function)
        if historic_palette_sample is not None:
            return historic_palette_sample
        osd_pcg = self._osd_pcg_function(function)
        if osd_pcg is not None:
            return osd_pcg
        spooky_hash_mix = self._spooky_ticker_hash_mix_function(function)
        if spooky_hash_mix is not None:
            return spooky_hash_mix
        fractal_julia = self._fractal_julia_number_function(function)
        if fractal_julia is not None:
            return fractal_julia
        fractal_mandelbrot = self._fractal_mandelbrot_number_function(function)
        if fractal_mandelbrot is not None:
            return fractal_mandelbrot
        fractal_newton = self._fractal_newton_number_function(function)
        if fractal_newton is not None:
            return fractal_newton
        fractal_hsv = self._fractal_hsv_number_function(function)
        if fractal_hsv is not None:
            return fractal_hsv
        fractal_palette = self._fractal_palette_number_function(function)
        if fractal_palette is not None:
            return fractal_palette
        rotate_helper = getattr(self, "authorized_rotate_helper", None)
        if function.return_type.kind == "matrix" and function is not rotate_helper:
            raise _error(self.program, function,
                         "unauthenticated matrix-return function")
        if function is rotate_helper:
            self.emitted_rotate_helper_count += 1
        self.current_function_name = function.name
        self.current_function_signature_id = function.signature.id
        self.locals = {parameter.id: _safe_identifier(parameter.name, parameter.id)
                       for parameter in function.parameters}
        parameters = ", ".join([*self._emitter_bound_parameters(function), *(
            f"[[maybe_unused]] {self.function_parameter_type(function, ordinal, parameter)} "
            f"{_safe_identifier(parameter.name, parameter.id)}"
            for ordinal, parameter in enumerate(function.parameters))])
        return_type = (f"glsl::FloatExpr<{function.return_type.display()[-1]}>"
                       if function.signature.id in self.ordinary_array_return_signatures
                       else self.function_type(function.return_type))
        # [[nodiscard]] is ill-formed on a void-returning function under
        # -Werror -Wignored-attributes (there is never a discardable return
        # value). sort2's inout-vec3-swap admission is the first void
        # non-main helper this port emits.
        nodiscard = "" if return_type == "void" else "[[nodiscard]] "
        emitted_name = self.function_names[function.signature.id]
        lines = [f"{nodiscard}{return_type} {emitted_name}({parameters}) noexcept {{"]
        lines.extend(self.source_global_locals(function.body))
        for statement in function.body: lines.extend(self.statement(statement))
        if (self.fractal_frontend_profile is not None
                and function.name in self.authorized_fractal_terminal_fallbacks):
            if function.return_type.display() != "float":
                raise _error(self.program, function,
                             "malformed Fractal terminal fallback return type")
            lines.extend([
                "  // Fractal mode contract [0,1]; unreachable terminal fallback.",
                "  return 0.0;",
            ])
        lines.append("}")
        self.current_function_name = None
        self.current_function_signature_id = None
        return lines

    def function_declaration(self, function) -> str:
        proof = self.authorized_osd_proof
        if proof is not None and function is proof.pcg_function:
            if (function.name != "pcg"
                    or function.return_type.display() != "uint"
                    or len(function.parameters) != 1
                    or function.parameters[0].name != "v_in"
                    or function.parameters[0].type.display() != "uint"):
                raise _error(self.program, function,
                             "malformed authenticated OSD pcg declaration")
            return ("[[nodiscard]] std::uint32_t pcg("
                    "[[maybe_unused]] const State& state, "
                    "[[maybe_unused]] const glsl::PixelContext& context, "
                    "[[maybe_unused]] std::uint32_t v_in) noexcept;")
        spooky = self.authorized_spooky_ticker_proof
        if spooky is not None:
            hash_function = next(
                item for item in spooky.closure_functions
                if item.name == "hash_mix")
            if function is hash_function:
                parameter = (function.parameters[0]
                             if len(function.parameters) == 1 else None)
                if (function.return_type.display() != "uint"
                        or parameter is not spooky.number_parameters[0]
                        or parameter.name != "v" or parameter.id != 14
                        or parameter.type.display() != "uint"):
                    raise _error(
                        self.program, function,
                        "malformed authenticated SpookyTicker hash_mix declaration")
                self.emitted_spooky_ticker_number_parameters.append(parameter)
                self.emitted_spooky_ticker_hash_declarations += 1
                return (
                    "[[nodiscard]] double hash_mix("
                    "[[maybe_unused]] const State& state, "
                    "[[maybe_unused]] const glsl::PixelContext& context, "
                    "[[maybe_unused]] double v) noexcept;")
        julia_function = self.authorized_fractal_julia_function
        if julia_function is not None and function is julia_function:
            parameter = self.authorized_fractal_julia_parameter
            if (function.name != "julia"
                    or function.signature.id != 61
                    or function.return_type.display() != "float"
                    or len(function.parameters) != 1
                    or function.parameters[0] is not parameter
                    or parameter is None or parameter.name != "st"
                    or parameter.id != 55 or parameter.type.display() != "vec2"
                    or parameter.direction != "in"):
                raise _error(
                    self.program, function,
                    "malformed authenticated Fractal Number Julia declaration")
            self.emitted_fractal_julia_declarations += 1
            return (
                "[[nodiscard]] double julia("
                "[[maybe_unused]] const State& state, "
                "[[maybe_unused]] const glsl::PixelContext& context, "
                "[[maybe_unused]] double input_x, "
                "[[maybe_unused]] double input_y) noexcept;")
        mandelbrot_function = self.authorized_fractal_mandelbrot_function
        if (mandelbrot_function is not None
                and function is mandelbrot_function):
            parameter = self.authorized_fractal_mandelbrot_parameter
            if (function.name != "mandelbrot"
                    or function.signature.id != 65
                    or function.return_type.display() != "float"
                    or len(function.parameters) != 1
                    or function.parameters[0] is not parameter
                    or parameter is None or parameter.name != "st"
                    or parameter.id != 56 or parameter.type.display() != "vec2"
                    or parameter.direction != "in"):
                raise _error(
                    self.program, function,
                    "malformed authenticated Fractal Number Mandelbrot declaration")
            self.emitted_fractal_mandelbrot_declarations += 1
            return (
                "[[nodiscard]] double mandelbrot("
                "[[maybe_unused]] const State& state, "
                "[[maybe_unused]] const glsl::PixelContext& context, "
                "[[maybe_unused]] double input_x, "
                "[[maybe_unused]] double input_y) noexcept;")
        newton_function = self.authorized_fractal_newton_function
        if newton_function is not None and function is newton_function:
            parameter = self.authorized_fractal_newton_parameter
            if (function.name != "newton" or function.signature.id != 67
                    or function.return_type.display() != "float"
                    or len(function.parameters) != 1
                    or function.parameters[0] is not parameter
                    or parameter is None or parameter.name != "st"
                    or parameter.id != 54
                    or parameter.type.display() != "vec2"
                    or parameter.direction != "in"):
                raise _error(
                    self.program, function,
                    "malformed authenticated Fractal Number Newton declaration")
            self.emitted_fractal_newton_declarations += 1
            return (
                "[[nodiscard]] double newton("
                "[[maybe_unused]] const State& state, "
                "[[maybe_unused]] const glsl::PixelContext& context, "
                "[[maybe_unused]] double input_x, "
                "[[maybe_unused]] double input_y) noexcept;")
        hsv_function = self.authorized_fractal_hsv_function
        if hsv_function is not None and function is hsv_function:
            parameter = self.authorized_fractal_hsv_parameter
            if (function.name != "hsv2rgb"
                    or function.signature.id != 60
                    or function.return_type.display() != "vec3"
                    or len(function.parameters) != 1
                    or function.parameters[0] is not parameter
                    or parameter is None or parameter.name != "hsv"
                    or parameter.id != 40
                    or parameter.type.display() != "vec3"
                    or parameter.direction != "in"):
                raise _error(
                    self.program, function,
                    "malformed authenticated Fractal Number HSV declaration")
            self.emitted_fractal_hsv_declarations += 1
            return (
                "[[nodiscard]] glsl::Vec3 hsv2rgb("
                "[[maybe_unused]] const State& state, "
                "[[maybe_unused]] const glsl::PixelContext& context, "
                "[[maybe_unused]] glsl::FloatExpr<3> hsv) noexcept;")
        if (function.return_type.kind == "matrix"
                and function is not getattr(self, "authorized_rotate_helper", None)):
            raise _error(self.program, function,
                         "unauthenticated matrix-return function declaration")
        parameters = ", ".join([*self._emitter_bound_parameters(function), *(
            f"[[maybe_unused]] {self.function_parameter_type(
                function, ordinal, parameter, record_out_inout=False)} "
            f"{_safe_identifier(parameter.name, parameter.id)}"
            for ordinal, parameter in enumerate(function.parameters))])
        return_type = (f"glsl::FloatExpr<{function.return_type.display()[-1]}>"
                       if function.signature.id in self.ordinary_array_return_signatures
                       else self.function_type(function.return_type))
        nodiscard = "" if return_type == "void" else "[[nodiscard]] "
        emitted_name = self.function_names[function.signature.id]
        return f"{nodiscard}{return_type} {emitted_name}({parameters}) noexcept;"

    def _consume_julia_body(self, body: str, proof: object) -> None:
        """Bind authenticated Julia records to exact emitted C++ consumers."""

        def fail(message: str) -> None:
            raise _error(self.program, self.program,
                         f"Julia emission consumption {message}")

        if (set(JULIA_BODY_CONSUMER_PLAN) != set(_JULIA_BODY_CONSUMER_PLAN)
                or any(JULIA_BODY_CONSUMER_PLAN[name]
                       != _JULIA_BODY_CONSUMER_PLAN[name]
                       for name in _JULIA_BODY_CONSUMER_PLAN)):
            fail("plan mismatch")
        plan = JULIA_BODY_CONSUMER_PLAN

        def positions(text: str, marker: str) -> tuple[int, ...]:
            found = []
            offset = 0
            while True:
                value = text.find(marker, offset)
                if value < 0:
                    return tuple(found)
                found.append(value)
                offset = value + len(marker)

        function_positions: dict[int, int] = {}
        for ordinal, marker in plan["functions"]:
            if ordinal < 0 or ordinal >= len(proof.functions):
                fail("function ordinal mismatch")
            record = proof.functions[ordinal]
            found = positions(body, marker)
            if len(found) != 1 or f" {record[1]}(" not in marker:
                fail(f"function marker {ordinal} mismatch")
            function_positions[ordinal] = found[0]
            self.emitted_julia_functions.append(record)
        if tuple(item[0] for item in plan["functions"]) != tuple(range(19)):
            fail("function plan order mismatch")
        if tuple(ordinal for _, ordinal in sorted(
                (value, key) for key, value in function_positions.items())) \
                != _JULIA_FUNCTION_BODY_ORDER:
            fail("function body order mismatch")

        sorted_functions = sorted(
            (value, key) for key, value in function_positions.items())
        section_bounds: dict[int, tuple[int, int]] = {}
        for index, (start, ordinal) in enumerate(sorted_functions):
            end = (sorted_functions[index + 1][0]
                   if index + 1 < len(sorted_functions) else len(body))
            section_bounds[ordinal] = (start, end)

        def section(function_ordinal: int) -> tuple[str, int]:
            if function_ordinal not in section_bounds:
                fail("unknown function section")
            start, end = section_bounds[function_ordinal]
            return body[start:end], start

        member_counts: dict[tuple[int, str], int] = {}
        for _, function_ordinal, marker, _ in plan["members"]:
            key = (function_ordinal, marker)
            member_counts[key] = member_counts.get(key, 0) + 1
        for (function_ordinal, marker), expected_count in member_counts.items():
            text, _ = section(function_ordinal)
            if len(positions(text, marker)) != expected_count:
                fail("member marker cardinality mismatch")
        member_positions = {}
        for ordinal, function_ordinal, marker, occurrence in plan["members"]:
            if ordinal < 0 or ordinal >= len(proof.struct_members):
                fail("member ordinal mismatch")
            record = proof.struct_members[ordinal]
            if not marker.endswith(f".{record.member}"):
                fail(f"member marker {ordinal} mismatch")
            text, start = section(function_ordinal)
            found = positions(text, marker)
            if occurrence < 0 or occurrence >= len(found):
                fail(f"member occurrence {ordinal} mismatch")
            member_positions[ordinal] = start + found[occurrence]
            self.emitted_julia_result_members.append(record)
        if tuple(item[0] for item in plan["members"]) != tuple(range(24)):
            fail("member plan order mismatch")
        if tuple(ordinal for _, ordinal in sorted(
                (value, key) for key, value in member_positions.items())) \
                != _JULIA_MEMBER_BODY_ORDER:
            fail("member body order mismatch")

        parameter_type = {"float": "float", "vec2": "glsl::Vec2"}
        parameter_positions = {}
        for ordinal, function_ordinal, marker in plan["out_parameters"]:
            if ordinal < 0 or ordinal >= len(self.authorized_julia_out_parameters):
                fail("out parameter ordinal mismatch")
            record = self.authorized_julia_out_parameters[ordinal]
            owner, name, glsl_type, direction, _ = record
            if (direction != "out"
                    or proof.functions[function_ordinal][1] != owner
                    or marker != f"{parameter_type[glsl_type]}& {name}"):
                fail(f"out parameter marker {ordinal} mismatch")
            text, start = section(function_ordinal)
            found = positions(text, marker)
            if len(found) != 1:
                fail(f"out parameter occurrence {ordinal} mismatch")
            parameter_positions[ordinal] = start + found[0]
            self.emitted_julia_out_parameters.append(record)
        if tuple(item[0] for item in plan["out_parameters"]) != tuple(range(4)):
            fail("out parameter plan order mismatch")
        if tuple(ordinal for _, ordinal in sorted(
                (value, key) for key, value in parameter_positions.items())) \
                != (0, 1, 2, 3):
            fail("out parameter body order mismatch")

        def normalized(value: str) -> str:
            return " ".join(value.split())

        def call_arguments(text: str, marker: str,
                           occurrence: int) -> tuple[tuple[str, ...], int]:
            found = positions(text, marker)
            if occurrence < 0 or occurrence >= len(found):
                fail("out call occurrence mismatch")
            call_start = found[occurrence]
            index = call_start + len(marker)
            depth = 1
            current = []
            arguments = []
            while index < len(text):
                char = text[index]
                if char == "(":
                    depth += 1
                    current.append(char)
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        arguments.append(normalized("".join(current).strip()))
                        return tuple(arguments), call_start
                    current.append(char)
                elif char == "," and depth == 1:
                    arguments.append(normalized("".join(current).strip()))
                    current = []
                else:
                    current.append(char)
                index += 1
            fail("unterminated out call marker")
            raise AssertionError("unreachable")

        out_call_counts: dict[tuple[int, str], int] = {}
        for _, function_ordinal, marker, _, _, _ in plan["out_calls"]:
            key = (function_ordinal, marker)
            out_call_counts[key] = out_call_counts.get(key, 0) + 1
        for (function_ordinal, marker), expected_count in out_call_counts.items():
            text, _ = section(function_ordinal)
            if len(positions(text, marker)) != expected_count:
                fail("out call marker cardinality mismatch")
        out_call_positions = {}
        for (ordinal, function_ordinal, marker, occurrence,
             expected_cpp_arguments, source_argument_groups) in plan["out_calls"]:
            if ordinal < 0 or ordinal >= len(self.authorized_julia_out_calls):
                fail("out call ordinal mismatch")
            record = self.authorized_julia_out_calls[ordinal]
            owner, callee, _, _ = record.identity
            if (proof.functions[function_ordinal][1] != owner
                    or marker != f"{callee}("):
                fail(f"out call marker {ordinal} mismatch")
            text, start = section(function_ordinal)
            actual_cpp_arguments, local_position = call_arguments(
                text, marker, occurrence)
            if actual_cpp_arguments != expected_cpp_arguments:
                fail(f"out call arguments {ordinal} mismatch")
            if (len(source_argument_groups) != len(record.arguments)
                    or tuple(item for group in source_argument_groups for item in group)
                    != tuple(range(len(actual_cpp_arguments)))):
                fail(f"out argument mapping {ordinal} mismatch")
            out_call_positions[ordinal] = start + local_position
            self.emitted_julia_out_calls.append(record)
            for argument, group in zip(record.arguments, source_argument_groups):
                if not group:
                    fail(f"out argument consumer {ordinal} is empty")
                self.emitted_julia_out_arguments.append(argument)
        if tuple(item[0] for item in plan["out_calls"]) != tuple(range(6)):
            fail("out call plan order mismatch")
        if tuple(ordinal for _, ordinal in sorted(
                (value, key) for key, value in out_call_positions.items())) \
                != tuple(range(6)):
            fail("out call body order mismatch")

        loop_positions = {}
        for ordinal, function_ordinal, marker in plan["loops"]:
            if ordinal < 0 or ordinal >= len(proof.loops):
                fail("loop ordinal mismatch")
            record = proof.loops[ordinal]
            if proof.functions[function_ordinal][1] != record[0]:
                fail(f"loop owner {ordinal} mismatch")
            text, start = section(function_ordinal)
            found = positions(text, marker)
            if len(found) != 1:
                fail(f"loop marker {ordinal} mismatch")
            loop_positions[ordinal] = start + found[0]
            self.emitted_julia_loops.append(record)
        if tuple(item[0] for item in plan["loops"]) != (0, 1):
            fail("loop plan order mismatch")
        if tuple(ordinal for _, ordinal in sorted(
                (value, key) for key, value in loop_positions.items())) != (1, 0):
            fail("loop body order mismatch")

        binding_positions = {}
        for ordinal, marker in plan["bindings"]:
            if ordinal < 0 or ordinal >= len(proof.uniforms):
                fail("binding ordinal mismatch")
            name, glsl_type = proof.uniforms[ordinal]
            expected_marker = {
                "vec2": f'bindings.get<glsl::Vec2>("{name}")',
                "float": f'bindings.get_number("{name}")',
                "int": f'bindings.get<std::int32_t>("{name}")',
                "bool": f'bindings.get<bool>("{name}")',
            }[glsl_type]
            found = positions(body, marker)
            if marker != expected_marker or len(found) != 1:
                fail(f"binding marker {ordinal} mismatch")
            binding_positions[ordinal] = found[0]
            self.emitted_julia_bindings.append(proof.uniforms[ordinal])
        if tuple(item[0] for item in plan["bindings"]) != tuple(range(21)):
            fail("binding plan order mismatch")
        if tuple(ordinal for _, ordinal in sorted(
                (value, key) for key, value in binding_positions.items())) \
                != tuple(range(21)):
            fail("binding body order mismatch")

        expected_arguments = tuple(
            argument for call in self.authorized_julia_out_calls
            for argument in call.arguments)
        if (not _same_object_sequence(
                    self.emitted_julia_functions, proof.functions)
                or not _same_object_sequence(
                    self.emitted_julia_result_members, proof.struct_members)
                or not _same_object_sequence(
                    self.emitted_julia_out_parameters,
                    self.authorized_julia_out_parameters)
                or not _same_object_sequence(
                    self.emitted_julia_out_calls,
                    self.authorized_julia_out_calls)
                or not _same_object_sequence(
                    self.emitted_julia_out_arguments, expected_arguments)
                or not _same_object_sequence(
                    self.emitted_julia_loops, proof.loops)
                or not _same_object_sequence(
                    self.emitted_julia_bindings, proof.uniforms)):
            fail("final identity or order mismatch")

    def _render_julia_body(self, namespace: str, factory: str) -> list[str]:
        """Emit the source-bound standalone Julia adapter lane.

        Julia is deliberately not sent through the generic GLSL expression
        emitter: its CPU authority mixes JavaScript Number operations with
        explicit Float32 stores.  The frontend/out/struct proofs are consumed
        before this method is reachable; the text below is the narrow native
        carrier for that authenticated contract.
        """
        proof = self.authorized_julia_frontend_proof
        if proof is None or self.authorized_julia_struct_materialization is None:
            raise _error(self.program, self.program,
                         "authenticated Julia proof state is absent")

        def walk_expression(value):
            yield value
            for child in value.children:
                yield from walk_expression(child)

        def walk_statement(value):
            for expression in value.expressions:
                yield from walk_expression(expression)
            for child in value.children:
                yield from walk_statement(child)

        def walk_statements(value):
            yield value
            for child in value.children:
                yield from walk_statements(child)

        def span(value):
            item = value.span
            return (f"{item.start_line}:{item.start_column}-"
                    f"{item.end_line}:{item.end_column}")

        expected_functions = tuple(
            (item.id, item.name, item.return_type.display())
            for item in self.program.functions)
        expected_uniforms = tuple(
            (item.symbol.name, item.type.display())
            for item in self.program.declarations
            if item.symbol.storage == "uniform")
        expected_members = tuple(
            value for declaration in self.program.declarations
            if declaration.initializer is not None
            for value in walk_expression(declaration.initializer)
            if value.kind == "member")
        expected_members += tuple(
            value for function in self.program.functions
            for statement in function.body
            for value in walk_statement(statement)
            if value.kind == "member")
        expected_out_parameters = tuple(
            (function.name, parameter.name, parameter.type.display(),
             parameter.direction, span(parameter))
            for function in self.program.functions
            for parameter in function.parameters
            if parameter.direction != "in")
        expected_loops = []
        for function in self.program.functions:
            for root in function.body:
                for statement in walk_statements(root):
                    if statement.kind == "for":
                        loop_proof = statement.loop_proof
                        expected_loops.append(
                            (function.name, span(statement),
                             loop_proof.bound_value
                             if loop_proof is not None else -1))
        expected_loops = tuple(expected_loops)
        same_identity = (
            len(proof.struct_members) == len(expected_members)
            and all(actual is expected for actual, expected in zip(
                proof.struct_members, expected_members)))
        if (proof.functions != expected_functions
                or proof.uniforms != expected_uniforms
                or not same_identity
                or proof.out_parameters != expected_out_parameters
                or proof.loops != expected_loops
                or proof.julia_loop_proof.loops != expected_loops
                or tuple(self.authorized_julia_out_parameters)
                != expected_out_parameters
                or tuple(self.authorized_julia_out_calls)
                != JULIA_OUT_CALL_ARGUMENTS):
            raise _error(self.program, self.program,
                         "authenticated Julia proof identity mismatch")
        if (len(proof.functions) != 19 or len(proof.struct_members) != 24
                or len(proof.out_parameters) != 4 or len(proof.loops) != 2
                or len(proof.uniforms) != 21
                or len(self.authorized_julia_out_parameters) != 4
                or len(self.authorized_julia_out_calls) != 6):
            raise _error(self.program, self.program,
                         "authenticated Julia cardinality mismatch")

        # Keep this body self-contained and auditable.  Every operation that
        # belongs to the adapter's explicit F32 lane goes through julia_f32;
        # Number-side math remains double and is never routed through it.
        body = f"""
namespace {namespace} {{

struct State final : KernelState {{
  State(glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value,
        glsl::Vec2 fullResolution_value, double time_value,
        double cReal_value, double cImag_value, std::int32_t poi_value,
        std::int32_t outputMode_value, double centerX_value,
        double centerY_value, double rotation_value,
        std::int32_t iterations_value, double stripeFreq_value,
        std::int32_t trapShape_value, double lightAngle_value,
        std::int32_t cPath_value, double cSpeed_value, double cRadius_value,
        bool invert_value, double zoomSpeed_value, double zoomDepth_value)
      : resolution(resolution_value), tileOffset(tileOffset_value),
        fullResolution(fullResolution_value), time(time_value),
        cReal(cReal_value), cImag(cImag_value), poi(poi_value),
        outputMode(outputMode_value), centerX(centerX_value),
        centerY(centerY_value), rotation(rotation_value),
        iterations(iterations_value), stripeFreq(stripeFreq_value),
        trapShape(trapShape_value), lightAngle(lightAngle_value),
        cPath(cPath_value), cSpeed(cSpeed_value), cRadius(cRadius_value),
        invert(invert_value), zoomSpeed(zoomSpeed_value),
        zoomDepth(zoomDepth_value) {{}}
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double time;
  double cReal;
  double cImag;
  std::int32_t poi;
  std::int32_t outputMode;
  double centerX;
  double centerY;
  double rotation;
  std::int32_t iterations;
  double stripeFreq;
  std::int32_t trapShape;
  double lightAngle;
  std::int32_t cPath;
  double cSpeed;
  double cRadius;
  bool invert;
  double zoomSpeed;
  double zoomDepth;
}};

struct JuliaResultNative final {{
  double iter{{}};
  double zMag2{{}};
  double dzMag2{{}};
  double stripeSum{{}};
  double stripeCount{{}};
  double stripeLast{{}};
  double trapMin{{}};
}};

struct JuliaNumberVec2 final {{
  double x{{}};
  double y{{}};
}};

[[nodiscard]] inline float julia_f32(double value) noexcept {{
  return noisemaker::f32(value);
}}
[[nodiscard]] inline float julia_add(float a, float b) noexcept {{
  return julia_f32(static_cast<double>(a) + static_cast<double>(b));
}}
[[nodiscard]] inline float julia_sub(float a, float b) noexcept {{
  return julia_f32(static_cast<double>(a) - static_cast<double>(b));
}}
[[nodiscard]] inline float julia_mul(float a, float b) noexcept {{
  return julia_f32(static_cast<double>(a) * static_cast<double>(b));
}}
[[nodiscard]] inline double julia_number_min(double a, double b) noexcept {{
  if (std::isnan(a) || std::isnan(b)) return std::numeric_limits<double>::quiet_NaN();
  if (a == b && a == 0.0) {{
    if (std::signbit(a) == std::signbit(b)) return a;
    return -0.0;
  }}
  return a < b ? a : b;
}}
[[nodiscard]] inline double julia_number_max(double a, double b) noexcept {{
  if (std::isnan(a) || std::isnan(b)) return std::numeric_limits<double>::quiet_NaN();
  if (a == b && a == 0.0) {{
    if (std::signbit(a) == std::signbit(b)) return a;
    return 0.0;
  }}
  return a > b ? a : b;
}}
[[nodiscard]] inline double julia_clamp(double value, double low = 0.0,
                                        double high = 1.0) noexcept {{
  return julia_number_min(julia_number_max(value, low), high);
}}

[[nodiscard]] glsl::Vec2 cmul(glsl::Vec2 a, glsl::Vec2 b) noexcept {{
  const float x = julia_sub(julia_mul(a[0], b[0]), julia_mul(a[1], b[1]));
  const float y = julia_add(julia_mul(a[0], b[1]), julia_mul(a[1], b[0]));
  return glsl::Vec2(x, y);
}}

[[nodiscard]] glsl::Vec2 df64_from(double a) noexcept {{
  return glsl::Vec2(julia_f32(a), 0.0F);
}}

[[nodiscard]] glsl::Vec2 df64_add(glsl::Vec2 a, glsl::Vec2 b) noexcept {{
  const float s = julia_add(a[0], b[0]);
  const float v = julia_sub(s, a[0]);
  const float e = julia_add(julia_sub(a[0], julia_sub(s, v)),
                            julia_sub(b[0], v));
  const float low = julia_add(e, julia_add(a[1], b[1]));
  return glsl::Vec2(s, low);
}}

[[nodiscard]] glsl::Vec2 df64_sub(glsl::Vec2 a, glsl::Vec2 b) noexcept {{
  return df64_add(a, glsl::Vec2(julia_f32(-b[0]), julia_f32(-b[1])));
}}

void df64_split(float a, float& hi, float& lo) noexcept {{
  const float t = julia_mul(julia_f32(4097.0), a);
  hi = julia_sub(t, julia_sub(t, a));
  lo = julia_sub(a, hi);
}}

[[nodiscard]] glsl::Vec2 df64_mul(glsl::Vec2 a, glsl::Vec2 b) noexcept {{
  const float p = julia_mul(a[0], b[0]);
  float ahi = 0.0F; float alo = 0.0F;
  float bhi = 0.0F; float blo = 0.0F;
  df64_split(a[0], ahi, alo);
  df64_split(b[0], bhi, blo);
  float e = julia_sub(julia_mul(ahi, bhi), p);
  e = julia_add(e, julia_mul(ahi, blo));
  e = julia_add(e, julia_mul(alo, bhi));
  e = julia_add(e, julia_mul(alo, blo));
  e = julia_add(e, julia_mul(a[0], b[1]));
  e = julia_add(e, julia_mul(a[1], b[0]));
  return glsl::Vec2(p, e);
}}

[[nodiscard]] glsl::Vec2 df64_mul_f(glsl::Vec2 a, float b) noexcept {{
  const float p = julia_mul(a[0], b);
  float bhi = 0.0F; float blo = 0.0F;
  float ahi = 0.0F; float alo = 0.0F;
  df64_split(a[0], ahi, alo);
  df64_split(b, bhi, blo);
  float e = julia_sub(julia_mul(ahi, bhi), p);
  e = julia_add(e, julia_mul(ahi, blo));
  e = julia_add(e, julia_mul(alo, bhi));
  e = julia_add(e, julia_mul(alo, blo));
  e = julia_add(e, julia_mul(a[1], b));
  return glsl::Vec2(p, e);
}}

[[nodiscard]] JuliaNumberVec2 getAnimatedC(double t, std::int32_t pathType,
                                           double radius) noexcept {{
  const double theta = t * 6.28318530718;
  if (pathType == 1) {{
    return JuliaNumberVec2{{noisemaker::fdlibm::cos(theta) * 0.5 -
                                noisemaker::fdlibm::cos(2.0 * theta) * 0.25,
                            noisemaker::fdlibm::sin(theta) * 0.5 -
                                noisemaker::fdlibm::sin(2.0 * theta) * 0.25}};
  }}
  if (pathType == 2) {{
    return JuliaNumberVec2{{noisemaker::fdlibm::cos(theta) * radius,
                            noisemaker::fdlibm::sin(theta) * radius}};
  }}
  if (pathType == 3) {{
    return JuliaNumberVec2{{-1.0 + noisemaker::fdlibm::cos(theta) * 0.25,
                            noisemaker::fdlibm::sin(theta) * 0.25}};
  }}
  return JuliaNumberVec2{{0.0, 0.0}};
}}

void getPOI(std::int32_t index, JuliaNumberVec2& out) noexcept {{
  if (index == 1) out = JuliaNumberVec2{{-0.123, 0.745}};
  else if (index == 2) out = JuliaNumberVec2{{-0.3905, 0.5868}};
  else if (index == 3) out = JuliaNumberVec2{{0.0, 1.0}};
  else if (index == 4) out = JuliaNumberVec2{{-1.0, 0.0}};
  else if (index == 5) out = JuliaNumberVec2{{-0.7455, 0.113}};
  else if (index == 6) out = JuliaNumberVec2{{-0.0986, 0.6534}};
  else if (index == 7) out = JuliaNumberVec2{{-0.8, 0.156}};
  else if (index == 8) out = JuliaNumberVec2{{-0.75, 0.0}};
  else if (index == 9) out = JuliaNumberVec2{{-0.5792, 0.5385}};
  else if (index == 10) out = JuliaNumberVec2{{0.28, 0.008}};
  else out = JuliaNumberVec2{{-0.123, 0.745}};
}}

[[nodiscard]] JuliaNumberVec2 resolveC(const State& state) noexcept {{
  JuliaNumberVec2 result{{}};
  if (state.poi > 0) {{
    getPOI(state.poi, result);
    return result;
  }}
  if (state.cPath == 1 || state.cPath == 2 || state.cPath == 3) {{
    return getAnimatedC(state.time * state.cSpeed, state.cPath,
                        state.cRadius);
  }}
  return JuliaNumberVec2{{state.cReal, state.cImag}};
}}

void transformCoords(const State& state, double fragX, double fragY, double zoom,
                     glsl::Vec2& reDF, glsl::Vec2& imDF) noexcept {{
  const double denominator = julia_number_min(
      static_cast<double>(state.fullResolution[0]),
      static_cast<double>(state.fullResolution[1]));
  float uvX = julia_f32((fragX
                         - 0.5 * static_cast<double>(state.fullResolution[0]))
                        / denominator);
  float uvY = julia_f32((fragY
                         - 0.5 * static_cast<double>(state.fullResolution[1]))
                        / denominator);
  const float angle = julia_f32(-state.rotation * 6.28318530718 / 360.0);
  const float cosine = julia_f32(
      noisemaker::fdlibm::cos(static_cast<double>(angle)));
  const float sine = julia_f32(
      noisemaker::fdlibm::sin(static_cast<double>(angle)));
  const float rotatedX = julia_add(julia_mul(cosine, uvX),
                                   julia_mul(sine, uvY));
  uvY = julia_add(julia_mul(julia_f32(-sine), uvX),
                  julia_mul(cosine, uvY));
  uvX = rotatedX;
  const float scale = julia_f32(2.5 / zoom);
  reDF = df64_add(df64_mul_f(df64_from(uvX), scale),
                  df64_from(julia_f32(state.centerX)));
  imDF = df64_add(df64_mul_f(df64_from(uvY), scale),
                  df64_from(julia_f32(state.centerY)));
}}

[[nodiscard]] JuliaResultNative juliaIterate(
    glsl::Vec2 reStart, glsl::Vec2 imStart, JuliaNumberVec2 c,
    std::int32_t maxIterations, double frequency, std::int32_t trapShape)
    noexcept {{
  float reHigh = reStart[0]; float reLow = reStart[1];
  float imHigh = imStart[0]; float imLow = imStart[1];
  float derivativeX = 1.0F; float derivativeY = 0.0F;
  double iteration = 0.0; float stripeSum = 0.0F;
  float stripeLast = 0.0F; float stripeCount = 0.0F;
  double trapMin = 1e10;
  double slowX = static_cast<double>(reHigh);
  double slowY = static_cast<double>(imHigh);
  std::int32_t period = 0;
  JuliaResultNative result{{}};
  for (std::int32_t index = 0; index < std::min(maxIterations, 1000); ++index) {{
    const float nextDerivativeX = julia_mul(
        julia_f32(2.0), julia_sub(julia_mul(reHigh, derivativeX),
                                  julia_mul(imHigh, derivativeY)));
    derivativeY = julia_mul(
        julia_f32(2.0), julia_add(julia_mul(reHigh, derivativeY),
                                  julia_mul(imHigh, derivativeX)));
    derivativeX = nextDerivativeX;
    const glsl::Vec2 re2 = df64_mul(glsl::Vec2(reHigh, reLow),
                                    glsl::Vec2(reHigh, reLow));
    const glsl::Vec2 im2 = df64_mul(glsl::Vec2(imHigh, imLow),
                                    glsl::Vec2(imHigh, imLow));
    const glsl::Vec2 product = df64_mul(glsl::Vec2(reHigh, reLow),
                                        glsl::Vec2(imHigh, imLow));
    const glsl::Vec2 nextRe = df64_add(
        df64_add(re2, glsl::Vec2(julia_f32(-im2[0]), julia_f32(-im2[1]))),
        df64_from(c.x));
    const glsl::Vec2 nextIm = df64_add(df64_mul_f(product, 2.0F),
                                      df64_from(c.y));
    reHigh = nextRe[0]; reLow = nextRe[1];
    imHigh = nextIm[0]; imLow = nextIm[1];
    const float magnitude2 = julia_add(julia_mul(reHigh, reHigh),
                                       julia_mul(imHigh, imHigh));
    if (static_cast<double>(magnitude2) > 256.0 * 256.0) break;
    iteration = static_cast<double>(julia_f32(iteration + 1.0));
    if (frequency > 0.0) {{
      const float stripeAngle = julia_f32(
          frequency * std::atan2(static_cast<double>(imHigh),
                                 static_cast<double>(reHigh)));
      const float stripeHalf = julia_f32(
          0.5 * noisemaker::fdlibm::sin(static_cast<double>(stripeAngle)));
      stripeLast = julia_f32(static_cast<double>(stripeHalf) + 0.5);
      stripeSum = julia_add(stripeSum, stripeLast);
      stripeCount = julia_add(stripeCount, 1.0F);
    }}
    double trapDistance = 0.0;
    if (trapShape == 0) trapDistance = std::hypot(static_cast<double>(reHigh),
                                                   static_cast<double>(imHigh));
    else if (trapShape == 1) trapDistance = julia_number_min(
        std::fabs(static_cast<double>(reHigh)),
        std::fabs(static_cast<double>(imHigh)));
    else trapDistance = std::fabs(std::hypot(static_cast<double>(reHigh),
                                              static_cast<double>(imHigh)) - 1.0);
    trapMin = julia_number_min(trapMin, trapDistance);
    period += 1;
    if (period == 20) {{
      period = 0;
      slowX = static_cast<double>(reHigh);
      slowY = static_cast<double>(imHigh);
    }}
    else if (std::hypot(static_cast<double>(reHigh) - static_cast<double>(slowX),
                       static_cast<double>(imHigh) - static_cast<double>(slowY)) < 1e-10) {{
      iteration = static_cast<double>(maxIterations);
      break;
    }}
  }}
  result.iter = iteration;
  result.zMag2 = static_cast<double>(julia_add(julia_mul(reHigh, reHigh),
                                                julia_mul(imHigh, imHigh)));
  result.dzMag2 = static_cast<double>(julia_add(julia_mul(derivativeX, derivativeX),
                                                 julia_mul(derivativeY, derivativeY)));
  result.stripeSum = stripeSum; result.stripeCount = stripeCount;
  result.stripeLast = stripeLast; result.trapMin = trapMin;
  return result;
}}

[[nodiscard]] double outputSmoothIteration(const JuliaResultNative& r,
                                           double maxIter) noexcept {{
  if (r.iter >= maxIter) return 0.0;
  const double logMagnitude = std::log(r.zMag2) * 0.5;
  const double nu = std::log(logMagnitude / 0.6931471805599453)
                    / 0.6931471805599453;
  return julia_clamp((r.iter + 1.0 - nu) / maxIter);
}}
[[nodiscard]] double outputDistanceEstimation(const JuliaResultNative& r,
                                               double maxIter) noexcept {{
  if (r.iter >= maxIter) return 0.0;
  const double magnitude = std::sqrt(r.zMag2);
  const double derivative = std::sqrt(r.dzMag2);
  if (derivative < 1e-10) return 0.0;
  return julia_clamp(std::log(2.0 * magnitude * std::log(magnitude)
                              / derivative + 1.0) * 2.0);
}}
[[nodiscard]] double outputStripeAverage(const JuliaResultNative& r,
                                          double maxIter) noexcept {{
  if (r.iter >= maxIter || r.stripeCount < 1.0) return 0.0;
  const double average = r.stripeSum / r.stripeCount;
  const double previous = r.stripeCount > 1.0
      ? (r.stripeSum - r.stripeLast) / (r.stripeCount - 1.0) : average;
  const double logMagnitude = std::log(r.zMag2) * 0.5;
  const double nu = std::log(logMagnitude / 0.6931471805599453)
                    / 0.6931471805599453;
  const double amount = julia_clamp(1.0 - nu + std::floor(nu));
  const double mixed = previous * (1.0 - amount) + average * amount;
  return julia_clamp(mixed);
}}
[[nodiscard]] double outputOrbitTrap(const JuliaResultNative& r,
                                     double maxIter) noexcept {{
  if (r.iter >= maxIter) return 0.0;
  return julia_clamp(1.0 - r.trapMin);
}}

[[nodiscard]] double iterateSmooth(const State& state, double fragX, double fragY,
                                   JuliaNumberVec2 c, std::int32_t maxIterations,
                                   double zoom) noexcept {{
  glsl::Vec2 reDF{{}}; glsl::Vec2 imDF{{}};
  transformCoords(state, fragX, fragY, zoom, reDF, imDF);
  const JuliaResultNative r = juliaIterate(reDF, imDF, c, maxIterations, 0.0, 0);
  return outputSmoothIteration(r, static_cast<double>(maxIterations));
}}

[[nodiscard]] double outputNormalMap(const State& state,
                                     double fragX, double fragY, JuliaNumberVec2 c,
                                     std::int32_t maxIterations, double angle,
                                     double zoom) noexcept {{
  const double base = iterateSmooth(state, fragX, fragY, c, maxIterations, zoom);
  const double right = iterateSmooth(state, fragX + 1.0, fragY,
                                     c, maxIterations, zoom);
  const double up = iterateSmooth(state, fragX, fragY + 1.0,
                                  c, maxIterations, zoom);
  double nx = right - base; double ny = up - base; double nz = 0.05;
  double magnitude = std::hypot(nx, ny, nz);
  nx /= magnitude; ny /= magnitude; nz /= magnitude;
  const double rad = angle * 6.28318530718 / 360.0;
  double lx = noisemaker::fdlibm::cos(rad);
  double ly = noisemaker::fdlibm::sin(rad); double lz = 0.7;
  magnitude = std::hypot(lx, ly, lz);
  lx /= magnitude; ly /= magnitude; lz /= magnitude;
  return julia_clamp(julia_number_max(nx * lx + ny * ly + nz * lz, 0.0));
}}

[[nodiscard]] double julia_zoom(const State& state) noexcept {{
  if (state.zoomSpeed > 0.0) {{
    const double phase = 0.5 * (1.0 - noisemaker::fdlibm::cos(
        state.time * state.zoomSpeed * 6.28318530718));
    return std::pow(10.0, state.zoomDepth * phase);
  }}
  return std::pow(10.0, state.zoomDepth);
}}

void main(const State& state, const glsl::PixelContext& context,
          glsl::Vec4& output) noexcept {{
  const double globalX = static_cast<double>(context.frag_coord[0])
                         + static_cast<double>(state.tileOffset[0]);
  const double globalY = static_cast<double>(context.frag_coord[1])
                         + static_cast<double>(state.tileOffset[1]);
  const JuliaNumberVec2 c = resolveC(state);
  const double zoom = julia_zoom(state);
  double value = 0.0;
  if (state.outputMode == 4) {{
    value = outputNormalMap(state, globalX, globalY, c,
                            state.iterations, state.lightAngle, zoom);
  }} else {{
    glsl::Vec2 reDF{{}}; glsl::Vec2 imDF{{}};
    transformCoords(state, globalX, globalY, zoom, reDF, imDF);
    const JuliaResultNative r = juliaIterate(reDF, imDF, c, state.iterations,
                                             state.stripeFreq, state.trapShape);
    if (state.outputMode == 0) value = outputSmoothIteration(r, state.iterations);
    else if (state.outputMode == 1) value = outputDistanceEstimation(r, state.iterations);
    else if (state.outputMode == 2) value = outputStripeAverage(r, state.iterations);
    else if (state.outputMode == 3) value = outputOrbitTrap(r, state.iterations);
    else value = outputSmoothIteration(r, state.iterations);
  }}
  if (state.invert) value = 1.0 - value;
  const float finalValue = julia_f32(value);
  output = glsl::Vec4(glsl::FloatExpr<3>(finalValue), 1.0F);
}}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context,
           glsl::Vec4& output) noexcept {{
  const auto& state = static_cast<const State&>(kernel_base);
  main(state, context, output);
}}
}}  // namespace {namespace}

BoundKernel {factory}(const glsl::Bindings& bindings) {{
  const auto state = std::make_shared<{namespace}::State>(
      bindings.get<glsl::Vec2>("resolution"),
      bindings.get<glsl::Vec2>("tileOffset"),
      bindings.get<glsl::Vec2>("fullResolution"),
      static_cast<double>(noisemaker::f32(bindings.get_number("time"))),
      static_cast<double>(noisemaker::f32(bindings.get_number("cReal"))),
      static_cast<double>(noisemaker::f32(bindings.get_number("cImag"))),
      bindings.get<std::int32_t>("poi"),
      bindings.get<std::int32_t>("outputMode"),
      static_cast<double>(noisemaker::f32(bindings.get_number("centerX"))),
      static_cast<double>(noisemaker::f32(bindings.get_number("centerY"))),
      static_cast<double>(noisemaker::f32(bindings.get_number("rotation"))),
      bindings.get<std::int32_t>("iterations"),
      static_cast<double>(noisemaker::f32(bindings.get_number("stripeFreq"))),
      bindings.get<std::int32_t>("trapShape"),
      static_cast<double>(noisemaker::f32(bindings.get_number("lightAngle"))),
      bindings.get<std::int32_t>("cPath"),
      static_cast<double>(noisemaker::f32(bindings.get_number("cSpeed"))),
      static_cast<double>(noisemaker::f32(bindings.get_number("cRadius"))),
      bindings.get<bool>("invert"),
      static_cast<double>(noisemaker::f32(bindings.get_number("zoomSpeed"))),
      static_cast<double>(noisemaker::f32(bindings.get_number("zoomDepth"))));
  (void)bindings;
  return BoundKernel(state, &{namespace}::pixel);
}}
"""
        body = body.strip("\n")
        self._consume_julia_body(body, proof)
        return body.splitlines()

    def render_body(self, namespace: str, factory: str) -> list[str]:
        if self.program.key == JULIA_FRONTEND_KEY:
            return self._render_julia_body(namespace, factory)
        remap = self.authorized_remap_proof
        uniforms = [
            item.symbol for item in self.program.declarations
            if item.symbol.storage == "uniform"
            and not (remap is not None and item.symbol.name == "data"
                     and item.symbol.type.display() == "vec4[267]")
        ]
        lines = [f"namespace {namespace} {{"]
        if remap is not None:
            lines.extend([
                "[[nodiscard]] inline std::size_t remap_data_index(std::int64_t index) noexcept {",
                "  if (index < 0 || index >= 267) return 0U;",
                "  return static_cast<std::size_t>(index);",
                "}",
                "",
            ])
        proof = self.program.fixed_array_in_parameter_proof
        if proof is not None:
            lines.extend([
                f"using {proof.kernel_alias} = std::array<double, 9>;",
                f"using {proof.offsets_alias} = std::array<glsl::Vec2, 9>;",
                f"static_assert(sizeof({proof.kernel_alias}) == 72U);",
                f"static_assert(sizeof({proof.offsets_alias}) == 72U);",
                "",
            ])
        task20 = self.program.fixed_affine_centers13_proof
        if task20 is not None:
            lines.extend([
                f"using {task20.native_alias} = std::array<glsl::Vec2, 13>;",
                "static_assert(sizeof(glsl::Vec2) == 8U);",
                f"static_assert(sizeof({task20.native_alias}) == 104U);",
                "",
            ])
        tables = self.authorized_const_global_table_contract
        if tables:
            # Alias names, element types, extents and byte sizes all come from
            # the closure's frozen contract -- never re-derived or re-spelled
            # here. Same alias-plus-`static_assert` shape as the two blocks
            # above; the tables themselves are `const` LOCALS in the pixel
            # body (`source_global_locals`), so no static storage is emitted.
            lines.extend(
                f"using {table.native_alias} = "
                f"std::array<{table.native_element_type}, "
                f"{table.element_count}>;"
                for table in tables)
            lines.extend(
                f"static_assert(sizeof({table.native_alias}) == "
                f"{table.native_sizeof}U);"
                for table in tables)
            lines.append("")
            self.emitted_const_global_table_alias_blocks += 1
        if self.authorized_struct_declaration:
            declaration = self.authorized_struct_declaration[0]
            materialization = self.authorized_struct_materialization
            if (declaration.name != "POIData"
                    or len(declaration.fields) != 3
                    or tuple(field.name for field in declaration.fields)
                    != ("center", "deg", "maxZoom")
                    or materialization is None
                    or materialization.center_native != "glsl::Vec4"
                    or materialization.scalar_native != "double"):
                raise _error(self.program, self.program,
                             "authenticated Newton struct declaration drift")
            lines.extend([
                "struct POIData final {",
                f"  {materialization.center_native} center;",
                f"  {materialization.scalar_native} deg;",
                f"  {materialization.scalar_native} maxZoom;",
                "};",
                "",
            ])
            self.emitted_newton_struct_count += 1
        contract = getattr(self, "authorized_frame_contract", None)
        if contract is not None:
            # Emitted ONLY for a carrier program, and only from the closure's
            # own frozen contract. The two fields have deliberately DIFFERENT
            # numeric contracts and must stay different: `aspectRatio` is a
            # plain JS Number (`var aspectRatio = 0`) that the shipped
            # transpiler never narrows to f32, so it is a `double`;
            # `globalCoord` is a `Float32Array` mutated lane by lane, so every
            # store narrows and `glsl::Vec2` narrows identically. Value
            # initialisation reproduces the JS factory-scope initial values
            # (`0` and `[0, 0]`) exactly, so the "carry-over between pixels is
            # unobservable" argument is never relied on for the first pixel.
            if not contract.value_initialized:
                raise _error(self.program, self.program,
                             "mutable-global frame contract is not value-initialised")
            lines.append(f"struct {contract.struct_name} final {{")
            for field_contract in contract.fields:
                lines.append(
                    f"  {field_contract.native_type} {field_contract.name}{{}};"
                    f"  // JS: {field_contract.js_initializer}"
                    f" ({field_contract.js_number_kind},"
                    f" narrowing={field_contract.narrowing})")
            lines.extend(["};", ""])
            self.emitted_frame_struct_count += 1
        array_contract = getattr(self, "authorized_mutable_array_contract", None)
        if array_contract is not None:
            # The mutable-global array carrier's Frame. Emitted only for a
            # carrier program, only from the closure's own frozen contract,
            # and AFTER the `Kernel9` alias block above -- the members ARE
            # `Kernel9`, the alias the fixed-array proof machinery supplies
            # (cross-checked at authentication). Member order is the frozen
            # declaration order (ordinals 16-20). Value initialisation
            # reproduces the JS factory-scope zeros (`var emboss =
            # [0,...,9 times]`): unobservable -- `loadKernels` fully
            # overwrites before any read -- but exact.
            if not array_contract.value_initialized:
                raise _error(self.program, self.program,
                             "mutable-global array contract is not "
                             "value-initialised")
            lines.append(f"struct {array_contract.struct_name} final {{")
            for field_contract in array_contract.fields:
                lines.append(
                    f"  {field_contract.native_type} {field_contract.name}{{}};"
                    f"  // JS: {field_contract.js_initializer}"
                    f" ({field_contract.js_number_kind},"
                    f" narrowing={field_contract.narrowing})")
            lines.extend(["};", ""])
            self.emitted_array_frame_struct_count += 1
        if self.authorized_historic_palette_proof is not None:
            proof = self.authorized_historic_palette_proof
            if proof.table_native_type != HISTORIC_PALETTE_TABLE_NATIVE_TYPE:
                raise _error(self.program, proof.struct,
                             "authenticated Historic Palette table native type drift")
            self.emitted_historic_palette_structs.append(proof.struct)
            lines.extend([
                "struct HistoricPalette final {",
                f"  {proof.table_native_type} color1{{}};",
                f"  {proof.table_native_type} color2{{}};",
                f"  {proof.table_native_type} color3{{}};",
                f"  {proof.table_native_type} color4{{}};",
                f"  {proof.table_native_type} color5{{}};",
                "};", "",
                f"[[nodiscard]] inline double {HISTORIC_PALETTE_LUMINANCE_HELPER_NAME}(",
                "    const glsl::Vec3& color) noexcept {",
                "  return ((static_cast<double>(color[0]) * 0.299)",
                "          + (static_cast<double>(color[1]) * 0.587))",
                "         + (static_cast<double>(color[2]) * 0.114);",
                "}",
                f"[[nodiscard]] inline double {HISTORIC_PALETTE_FRACT_HELPER_NAME}(",
                "    double value) noexcept {",
                "  return value - std::floor(value);",
                "}",
                f"[[nodiscard]] inline double {HISTORIC_PALETTE_SMOOTHSTEP_HELPER_NAME}(",
                "    double edge0, double edge1, double value) noexcept {",
                "  if (edge0 == edge1) return value < edge0 ? 0.0 : 1.0;",
                "  const double amount = glsl::component_min<double>(",
                "      glsl::component_max<double>((value - edge0) / (edge1 - edge0), 0.0), 1.0);",
                "  return (amount * amount) * (3.0 - (2.0 * amount));",
                "}",
                f"[[nodiscard]] inline float {HISTORIC_PALETTE_MIX_STORE_HELPER_NAME}(",
                "    double left, double right, double amount) noexcept {",
                "  return noisemaker::f32((left * (1.0 - amount)) + (right * amount));",
                "}", ""])
        if self.authorized_palette_frontend_proof is not None:
            proof = self.authorized_palette_frontend_proof
            if proof.table_native_type != PALETTE_TABLE_NATIVE_TYPE:
                raise _error(self.program, proof.struct,
                             "authenticated Palette table native type drift")
            self.emitted_palette_structs.append(proof.struct)
            lines.extend([
                "struct PaletteEntry final {",
                f"  {proof.table_native_type} amp{{}};",
                f"  {proof.table_native_type} freq{{}};",
                f"  {proof.table_native_type} offset{{}};",
                f"  {proof.table_native_type} phase{{}};",
                "};", ""])
            if (PALETTE_COSINE_HELPER_NAME == PALETTE_CLAMP_HELPER_NAME
                    or proof.cosine_function.name != "cosinePalette"):
                raise _error(self.program, proof.cosine_function,
                             "authenticated Palette cosine helper metadata drift")
            lines.extend([
                f"[[nodiscard]] inline {PALETTE_COSINE_NATIVE_TYPE} "
                f"{PALETTE_COSINE_HELPER_NAME}("
                f"const {PALETTE_COSINE_NATIVE_TYPE}& value) noexcept {{",
                f"  return {PALETTE_COSINE_NATIVE_TYPE}("
                "noisemaker::fdlibm::cos(value[0]), "
                "noisemaker::fdlibm::cos(value[1]), "
                "noisemaker::fdlibm::cos(value[2]));",
                "}",
                f"[[nodiscard]] inline glsl::Vec3 {PALETTE_CLAMP_HELPER_NAME}("
                f"const {PALETTE_COSINE_NATIVE_TYPE}& value, double low, double high) noexcept {{",
                "  return glsl::Vec3(",
                "      noisemaker::f32(glsl::component_min<double>(glsl::component_max<double>(value[0], low), high)),",
                "      noisemaker::f32(glsl::component_min<double>(glsl::component_max<double>(value[1], low), high)),",
                "      noisemaker::f32(glsl::component_min<double>(glsl::component_max<double>(value[2], low), high)));",
                "}",
                f"[[nodiscard]] inline double {PALETTE_LUMINANCE_HELPER_NAME}(",
                "    const glsl::Vec3& color) noexcept {",
                "  return ((static_cast<double>(color[0]) * 0.299)",
                "          + (static_cast<double>(color[1]) * 0.587))",
                "         + (static_cast<double>(color[2]) * 0.114);",
                "}",
                f"[[nodiscard]] inline double {PALETTE_LINEAR_TO_SRGB_HELPER_NAME}(",
                "    double value) noexcept {",
                "  return value <= 0.0031308",
                "      ? value * 12.92",
                "      : (1.055 * std::pow(value, 1.0 / 2.4)) - 0.055;",
                "}", ""])
        lines.append("struct State final : KernelState {")
        constructor_parts = [
            f"const Surface* {symbol.name}_value" if symbol.type.kind == "sampler" else f"{self.uniform_type(symbol.type)} {symbol.name}_value"
            for symbol in uniforms]
        if remap is not None:
            constructor_parts.insert(0, "glsl::RemapUniformData data_value")
        if (self.runtime_loop_contract is not None
                and self.runtime_loop_contract.kind == "blur-radius"):
            constructor_parts.append("std::int32_t runtime_loop_radius_value")
        if self.authorized_median_frontend_proof is not None:
            constructor_parts.append("std::int32_t median_radius_value")
        constructor = ", ".join(constructor_parts)
        initializer_parts = [f"{symbol.name}({symbol.name}_value)" for symbol in uniforms]
        if remap is not None:
            initializer_parts.insert(0, "data(data_value)")
        if (self.runtime_loop_contract is not None
                and self.runtime_loop_contract.kind == "blur-radius"):
            initializer_parts.append("runtime_loop_radius(runtime_loop_radius_value)")
        if self.authorized_median_frontend_proof is not None:
            initializer_parts.append("median_radius(median_radius_value)")
        initializer = ", ".join(initializer_parts)
        suffix = f" : {initializer}" if initializer else ""
        lines.append(f"  State({constructor}){suffix} {{}}")
        if remap is not None:
            lines.append("  glsl::RemapUniformData data;")
        for symbol in uniforms:
            type_name = "const Surface*" if symbol.type.kind == "sampler" else self.uniform_type(symbol.type)
            lines.append(f"  {type_name} {symbol.name};")
        if (self.runtime_loop_contract is not None
                and self.runtime_loop_contract.kind == "blur-radius"):
            lines.append("  std::int32_t runtime_loop_radius;")
        if self.authorized_median_frontend_proof is not None:
            lines.append("  std::int32_t median_radius;")
        lines.extend(["};", "", "[[nodiscard]] glsl::Vec4 sample_texture(const Surface& surface, const glsl::Vec2& uv) noexcept {",
                      "  const Rgba sample = sample_nearest_bottom_left(surface, uv[0], uv[1]);",
                      "  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);", "}",
                      "[[nodiscard]] glsl::Vec4 fetch_texel(const Surface& surface, const glsl::IVec2& coord) noexcept {",
                      "  const Rgba sample = texel_fetch_bottom_left(surface, coord[0], coord[1]);",
                      "  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);", "}",
                      "[[nodiscard]] glsl::IVec2 texture_size(const Surface& surface) noexcept {",
                      "  return glsl::IVec2(static_cast<std::int32_t>(surface.width()), static_cast<std::int32_t>(surface.height()));", "}"])
        if self.authorized_median_frontend_proof is not None:
            lines.append("// Median texelFetch lowering is bottom-left fetch_texel.")
        helpers = [
            function for function in self.program.functions
            if (function.name != "main"
                and function.signature.definition_span is not None
                and function.span == function.signature.definition_span)
        ]
        if helpers:
            lines.append("")
            lines.extend(self.function_declaration(function) for function in helpers)
        for function in helpers:
            if function.name != "main": lines.extend([""] + self.function(function))
        main = next((function for function in self.program.functions if function.name == "main"), None)
        if main is None: raise _error(self.program, self.program, "main function is missing")
        self.locals = {}
        self.current_function_name = "main"
        self.current_function_signature_id = main.signature.id
        lines.extend(["", "void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {",
                      "  const auto& state = static_cast<const State&>(kernel_base);", "  (void)state;", "  (void)context;"])
        if self.authorized_median_frontend_proof is not None:
            lines.append("  [[maybe_unused]] std::int32_t RADIUS = state.median_radius;")
        if contract is not None:
            if contract.instance_scope != "pixel":
                raise _error(self.program, self.program,
                             "mutable-global frame instance scope mismatch")
            lines.append(
                f"  {contract.struct_name} {contract.instance_name}{{}};")
            self.emitted_frame_instance_count += 1
        if array_contract is not None:
            if array_contract.instance_scope != "pixel":
                raise _error(self.program, self.program,
                             "mutable-global array instance scope mismatch")
            lines.append(
                f"  {array_contract.struct_name} "
                f"{array_contract.instance_name}{{}};")
            self.emitted_array_frame_instance_count += 1
        lines.extend(self.source_global_locals(main.body))
        for statement in main.body: lines.extend(self.statement(statement))
        self.current_function_name = None
        self.current_function_signature_id = None
        lines.extend(["}", "}  // namespace " + namespace, "",
                      f"BoundKernel {factory}(const glsl::Bindings& bindings) {{"])
        contract = self.runtime_loop_contract
        if contract is not None:
            if self.runtime_guard_emitted:
                raise _error(self.program, self.program,
                             "runtime-loop-bound guard emitted more than once")
            if contract.kind == "integer-range":
                lines.extend([
                    f'  const auto {contract.uniform_name} = '
                    f'bindings.get<std::int32_t>("{contract.uniform_name}");',
                    f"  if ({contract.uniform_name} < {contract.minimum} || "
                    f"{contract.uniform_name} > {contract.uniform_maximum}) {{",
                    f'    throw glsl::KernelBindingError("{contract.binding_error}");',
                    "  }",
                ])
            elif contract.kind == "blur-radius":
                assert contract.render_scale_name is not None
                lines.extend([
                    f'  const auto {contract.uniform_name} = '
                    f'bindings.get_number("{contract.uniform_name}");',
                    f'  const auto {contract.render_scale_name} = '
                    f'bindings.get_number("{contract.render_scale_name}");',
                    f"  const double runtime_loop_product = {contract.uniform_name} * "
                    f"{contract.render_scale_name};",
                    f"  if (!std::isfinite({contract.uniform_name}) || "
                    f"{contract.uniform_name} < {float(contract.minimum):.1f} || "
                    f"{contract.uniform_name} > {float(contract.uniform_maximum):.1f} "
                    f"|| !std::isfinite({contract.render_scale_name}) || "
                    f"{contract.render_scale_name} < 0.0 || "
                    "!std::isfinite(runtime_loop_product) || "
                    f"runtime_loop_product < 0.0 || runtime_loop_product >= "
                    f"{float(contract.maximum + 1):.1f}) {{",
                    f'    throw glsl::KernelBindingError("{contract.binding_error}");',
                    "  }",
                    "  const std::int32_t runtime_loop_radius = "
                    "static_cast<std::int32_t>(runtime_loop_product);",
                ])
            elif contract.kind == "texture-size-lanes":
                assert contract.input_surface_name is not None
                surface = contract.input_surface_name
                lane_maxima = {seed.lane: seed.maximum
                               for seed in contract.lane_seeds}
                width_maximum = lane_maxima[0]
                height_maximum = lane_maxima[1]
                product_maximum = width_maximum * height_maximum
                lines.extend([
                    f'  const auto& {surface} = bindings.texture("{surface}");',
                    f"  if ({surface}.width() < {contract.minimum}U || "
                    f"{surface}.width() > {width_maximum}U ||",
                    f"      {surface}.height() < {contract.minimum}U || "
                    f"{surface}.height() > {height_maximum}U) {{",
                    f'    throw glsl::KernelBindingError("{contract.binding_error}");',
                    "  }",
                    f"  const std::size_t runtime_loop_width = {surface}.width();",
                    f"  const std::size_t runtime_loop_height = {surface}.height();",
                    f"  if (runtime_loop_width > {product_maximum}U / "
                    "runtime_loop_height ||",
                    "      runtime_loop_width * runtime_loop_height > "
                    f"{product_maximum}U) {{",
                    f'    throw glsl::KernelBindingError("{contract.binding_error}");',
                    "  }",
                ])
            else:
                raise _error(self.program, self.program,
                             "unsupported runtime-loop-bound contract kind")
            self.runtime_guard_emitted = True
        fractal_mode_contract = self.authorized_fractal_mode_contract
        if fractal_mode_contract is not None:
            lines.extend([
                f'  const auto {fractal_mode_contract.uniform_name} = '
                f'bindings.get<std::int32_t>("{fractal_mode_contract.uniform_name}");',
                f"  if ({fractal_mode_contract.uniform_name} < "
                f"{fractal_mode_contract.minimum} || "
                f"{fractal_mode_contract.uniform_name} > "
                f"{fractal_mode_contract.maximum}) {{",
                f'    throw glsl::KernelBindingError("{self.program.key} '
                f'{fractal_mode_contract.uniform_name} must be one of the '
                f'authenticated choices [{fractal_mode_contract.minimum},'
                f'{fractal_mode_contract.maximum}]");',
                "  }",
            ])
        testpattern_preflight = None
        if self.authorized_testpattern_proof is not None:
            # These are execution controls, not generic integer metadata.
            # The frontend proof authenticates the exact names and ranges;
            # keep the values in locals so each binding is fetched once and
            # the same value is moved into State below.
            testpattern_preflight = (
                self.authorized_testpattern_proof.binding_preflight)
            grid_size_min, grid_size_max = testpattern_preflight.grid_size_range
            pattern_min, pattern_max = testpattern_preflight.pattern_range
            lines.extend([
                '  const auto gridSize = bindings.get<std::int32_t>("gridSize");',
                f"  if (gridSize < {grid_size_min} || gridSize > {grid_size_max}) {{",
                '    throw glsl::KernelBindingError("synth/testPattern:testPattern gridSize must be within 0..16");',
                "  }",
                '  const auto pattern = bindings.get<std::int32_t>("pattern");',
                f"  if (pattern < {pattern_min} || pattern > {pattern_max}) {{",
                '    throw glsl::KernelBindingError("synth/testPattern:testPattern pattern must be within 0..6");',
                "  }",
            ])
        remap_data_argument = None
        if remap is not None:
            lines.append(
                '  const auto data = bindings.get<glsl::RemapUniformData>("data");')
            remap_data_argument = "data"
        arguments = []
        for symbol in uniforms:
            if (symbol.type.kind == "sampler" and contract is not None
                    and contract.kind == "texture-size-lanes"
                    and symbol.name == contract.input_surface_name):
                arguments.append(f"&{symbol.name}")
            elif symbol.type.kind == "sampler": arguments.append(f"&bindings.texture(\"{symbol.name}\")")
            elif contract is not None and symbol.name == contract.uniform_name:
                arguments.append(contract.uniform_name)
            elif (fractal_mode_contract is not None
                  and symbol.name == fractal_mode_contract.uniform_name):
                arguments.append(fractal_mode_contract.uniform_name)
            elif (contract is not None and contract.kind == "blur-radius"
                  and symbol.name == contract.render_scale_name):
                arguments.append(contract.render_scale_name)
            elif (testpattern_preflight is not None
                  and symbol.name in {"gridSize", "pattern"}):
                arguments.append(symbol.name)
            elif symbol.type.display() == "float": arguments.append(f"bindings.get_number(\"{symbol.name}\")")
            else: arguments.append(f"bindings.get<{self.type(symbol.type)}>(\"{symbol.name}\")")
        if remap_data_argument is not None:
            arguments.insert(0, remap_data_argument)
        if contract is not None and contract.kind == "blur-radius":
            arguments.append("runtime_loop_radius")
        if self.authorized_median_frontend_proof is not None:
            arguments.append(str(self.authorized_median_frontend_proof.radius))
        uses_derivatives_arg = ", true" if self.program.resources.uses_derivatives else ""
        return_expression = "  return BoundKernel(state, &" + namespace + "::pixel"
        if contract is not None and contract.kind == "texture-size-lanes":
            assert contract.exact_output_extent == (1, 1)
            return_expression += (
                ', false, PassContract{ExactOutputExtent{1U, 1U, '
                f'"{self.program.key} output dimensions must be 1x1"}}}})')
        else:
            return_expression += uses_derivatives_arg + ")"
        lines.extend([f"  const auto state = std::make_shared<{namespace}::State>(" + ", ".join(arguments) + ");",
                      "  (void)bindings;", return_expression + ";", "}"])
        return lines


_DITHER_PALETTES = {
    "DOT_MATRIX": ((.06,.22,.06),(.19,.38,.19),(.55,.67,.06),(.61,.74,.06)),
    "AMBER": ((0.,0.,0.),(.4,.2,0.),(.8,.4,0.),(1.,.6,0.)),
    "PICO8": ((0.,0.,0.),(.114,.169,.325),(.494,.145,.325),(0.,.529,.318),(.671,.322,.212),(.373,.341,.310),(.761,.765,.780),(1.,.945,.910),(1.,0.,.302),(1.,.639,0.),(1.,.925,.153),(0.,.894,.212),(.161,.678,1.),(.514,.463,.612),(1.,.467,.659),(1.,.8,.667)),
    "C64": ((0.,0.,0.),(1.,1.,1.),(.533,0.,0.),(.667,1.,.933),(.8,.267,.8),(0.,.8,.333),(0.,0.,.667),(.933,.933,.467),(.867,.533,.333),(.4,.267,0.),(1.,.467,.467),(.2,.2,.2),(.467,.467,.467),(.667,1.,.4),(0.,.533,1.),(.6,.6,.6)),
    "CGA": ((0.,0.,0.),(0.,1.,1.),(1.,0.,1.),(1.,1.,1.)),
    "ZX_SPECTRUM": ((0.,0.,0.),(0.,0.,.839),(.839,0.,0.),(.839,0.,.839),(0.,.839,0.),(0.,.839,.839),(.839,.839,0.),(.839,.839,.839),(0.,0.,1.),(1.,0.,0.),(1.,0.,1.),(0.,1.,0.),(0.,1.,1.),(1.,1.,0.),(1.,1.,1.)),
    "APPLE_II": ((0.,0.,0.),(.882,0.,.494),(.247,0.,.682),(1.,0.,1.),(0.,.494,.263),(.502,.502,.502),(0.,.325,1.),(.667,.671,1.),(.502,.302,0.),(1.,.467,0.),(.502,.502,.502),(1.,.616,.667),(0.,.831,0.),(1.,1.,0.),(.333,1.,.557),(1.,1.,1.)),
    "EGA": ((0.,0.,0.),(0.,0.,.667),(0.,.667,0.),(0.,.667,.667),(.667,0.,0.),(.667,0.,.667),(.667,.333,0.),(.667,.667,.667),(.333,.333,.333),(.333,.333,1.),(.333,1.,.333),(.333,1.,1.),(1.,.333,.333),(1.,.333,1.),(1.,1.,.333),(1.,1.,1.)),
}


def _dither_emission_fragment(record: object) -> tuple[str, ...]:
    """Return operation text that must survive for an authenticated consumer."""
    record_id = getattr(record, "record_id", getattr(record, "target_id", ""))
    if not record_id:
        record_id = (getattr(record, "ref_to", "")
                     or getattr(record, "carrier", ""))
    if not getattr(record, "record_id", "") and getattr(record, "carrier", ""):
        record_id = getattr(record, "referrer", "") or record_id
    specific = {
        "C01": "const std::int32_t x = dither_i32",
        "C02": "const std::int32_t y = dither_i32",
        "C03": "const auto x = dither_u32",
        "C04": "const auto y = dither_u32",
        "C05": "dither_u32_after_i32(static_cast<double>(blockOrigin[0])",
        "C06": "dither_u32_after_i32(static_cast<double>(blockOrigin[1])",
        "C07": "dither_u32_after_i32(static_cast<double>(noisemaker::f32",
        "C08": "dither_u32_after_i32(static_cast<double>(blockOriginFloat[0])",
        "C09": "dither_u32_after_i32(static_cast<double>(blockOriginFloat[1])",
        "C10": "const std::int32_t apronX =",
        "C11": "const std::int32_t apronY =",
        "C12": "static_cast<std::uint32_t>(FS_APRON_MAX - FS_APRON_MIN + 1)",
        "C13": "static_cast<std::uint32_t>(FS_APRON_MAX - FS_APRON_MIN + 1)",
        "C14": "const glsl::IVec2 pLocal(dither_i32(std::floor(static_cast<double>(pGlobal[0]) - state.tileOffset[0]))",
        "C15": "const glsl::IVec2 pLocal(dither_i32(std::floor(static_cast<double>(pGlobal[0]) - state.tileOffset[0])), dither_i32(std::floor(static_cast<double>(pGlobal[1]) - state.tileOffset[1])))",
        "C16": "const glsl::IVec2 cell(dither_i32",
        "C17": "static_cast<double>(noisemaker::f32(static_cast<double>(cell[0])))",
        "C18": "static_cast<double>(noisemaker::f32(static_cast<double>(cell[1])))",
        "C19": "const glsl::IVec2 point(dither_i32(static_cast<double>(blockOrigin[0]) + static_cast<double>(c))",
        "C20": "std::clamp(pLocal[0], 0, texSize[0] - 1)",
        "C21": "const glsl::UVec3 seed = dither_pcg",
        "C22": "const glsl::UVec3 jitter = dither_pcg",
        "C23": "dither_pcg(glsl::UVec3(x, y, 0U))",
        "C24": "const glsl::IVec2 own(dither_i32",
        "C25": "p[0] >= 0.0F ? static_cast<double>(p[0]) * 2.0",
        "C26": "p[1] >= 0.0F ? static_cast<double>(p[1]) * 2.0",
        "C27": "dither_u32_after_i32(static_cast<double>(noisemaker::f32(static_cast<double>(lane)))",
        "C28": "const double maxLevel = static_cast<double>(state.levels) - 1.0",
        "C29": "const double stepScale =",
        "C30": "dither_quantize(color, static_cast<double>(state.levels)",
        "P02": "v[0] += dither_imul(v[1], v[2]);",
        "P03": "v[1] += dither_imul(v[2], v[0]);",
        "P04": "v[2] += dither_imul(v[0], v[1]);",
        "P05": ("v[0] ^= v[0] >> 16U;", "v[1] ^= v[1] >> 16U;",
                "v[2] ^= v[2] >> 16U;"),
        "P06": "v[0] += dither_imul(v[1], v[2]);",
        "P07": "v[1] += dither_imul(v[2], v[0]);",
        "P08": "v[2] += dither_imul(v[0], v[1]);",
        "P01": ("v[0] = dither_imul(v[0], 1664525U) + 1013904223U;",
                "v[1] = dither_imul(v[1], 1664525U) + 1013904223U;",
                "v[2] = dither_imul(v[2], 1664525U) + 1013904223U;"),
        "F01": "if (type == 3) { const glsl::Vec2 p = glsl::Vec2(noisemaker::f32(static_cast<double>(pixel[0]) * static_cast<double>(patternScale)), noisemaker::f32(static_cast<double>(pixel[1]) * static_cast<double>(patternScale)));",
        "F02": "const glsl::Vec2 c(noisemaker::f32(std::floor(static_cast<double>(p[0])) + 0.5), noisemaker::f32(std::floor(static_cast<double>(p[1])) + 0.5));",
        "F03": "const glsl::Vec2 centered(noisemaker::f32(static_cast<double>(glsl::fract(p[0])) - 0.5), noisemaker::f32(static_cast<double>(glsl::fract(p[1])) - 0.5));",
        "F04": "if (type == 5) { const glsl::Vec2 p = glsl::Vec2(noisemaker::f32(static_cast<double>(pixel[0]) * static_cast<double>(patternScale)), noisemaker::f32(static_cast<double>(pixel[1]) * static_cast<double>(patternScale)));",
        "F05": "const float line1 =",
        "F06": "const float line2 =",
        "F07": "if (type == 4) { const float p =",
        "F08": "const float scaleF = noisemaker::f32(scale); const glsl::Vec2 scaledCoord",
        "F09": "const glsl::Vec2 hashCoord",
        "F10": "glsl::Vec3 dithered(noisemaker::f32(static_cast<double>(color[0]) + adjusted / levels)",
        "F11": "return glsl::Vec3(noisemaker::f32(std::floor(static_cast<double>(dithered[0]) * levels)",
        "F12": "const glsl::Vec3 diff",
        "F13": "const glsl::Vec3 dithered(noisemaker::f32(std::clamp",
        "F14": "return dither_find_closest_palette(dithered, paletteType);",
        "F15": "return glsl::Vec3(noisemaker::f32(std::floor(static_cast<double>(v[0]) * maxLevel",
        "F16": "return glsl::Vec3(noisemaker::f32(static_cast<double>(seed[0]) / 4294967296.0 - .5)",
        "F17": "const glsl::Vec2 pGlobal(noisemaker::f32",
        "F18": "const glsl::IVec2 pLocal(dither_i32",
        "F19": "const glsl::IVec2 clamped(std::clamp",
        "F20": "const glsl::Vec3 bias(noisemaker::f32",
        "F21": "std::array<glsl::Vec3, 18> errRow",
        "F22": "errRow[static_cast<std::size_t>(i)] = glsl::Vec3",
        "F23": "rightErr = glsl::Vec3(noisemaker::f32(err[0] * 7.0 / 16.0)",
        "F24": "glsl::Vec3 v(noisemaker::f32(std::clamp",
        "F25": "const glsl::Vec3 err(noisemaker::f32",
        "F26": "const glsl::IVec2 point(dither_i32",
        "F27": "errRow[static_cast<std::size_t>(c + FS_APRON_MAX + 1)][0] + rightErr[0]",
        "F28": "diag = glsl::Vec3(noisemaker::f32(err[0] / 16.0)",
        "F29": "errRow[static_cast<std::size_t>(c + FS_APRON_MAX)] = glsl::Vec3",
        "F30": "errRow[static_cast<std::size_t>(c + FS_APRON_MAX)] = glsl::Vec3",
        "F31": "errRow[static_cast<std::size_t>(c + FS_APRON_MAX)] = glsl::Vec3",
        "F32": "errRow[static_cast<std::size_t>(c + FS_APRON_MAX + 1)] = glsl::Vec3",
        "F33": "glsl::Vec3 incoming = errRow[FS_APRON_MAX + 1]",
        "F34": "if (local[0] == 1) incoming = errRow[FS_APRON_MAX + 2]",
        "F35": "if (local[0] == 2) incoming = errRow[FS_APRON_MAX + 3]",
        "F36": "if (local[0] == 3) incoming = errRow[FS_APRON_MAX + 4]",
        "F37": "carried = glsl::Vec3(noisemaker::f32",
        "F38": "const glsl::IVec2 own",
        "F39": "const glsl::Vec3 ownColor(noisemaker::f32",
        "F40": "const glsl::IVec2 texSize = dither_texture_size(*state.inputTex);  // F40",
        "F41": "const glsl::Vec2 uv",
        "F42": "const auto color4",
        "F43": "const glsl::Vec2 globalCoord",
        "F44": "dither_error_diffusion(state",
        "F45": "dither_quantize(color",
        "F46": "ditherWithPalette(color",
        "F47": "const glsl::Vec3 mixed",
        "F48": "output = glsl::Vec4(mixed[0], mixed[1], mixed[2], color4[3]);",
        "F49": "output = glsl::Vec4(mixed[0], mixed[1], mixed[2], color4[3]);",
        "L-ERR-SEED": "errRow[static_cast<std::size_t>(i)] = glsl::Vec3(noisemaker::f32(static_cast<double>(seed[0]) * stepScale), noisemaker::f32(static_cast<double>(seed[1]) * stepScale), noisemaker::f32(static_cast<double>(seed[2]) * stepScale));",
        "L-PAL-4": "for (std::int32_t i = 1; i < 4; ++i)",
        "L-PAL-15": "for (std::int32_t i = 1; i < 15; ++i)",
        "L-PAL-16": "for (std::int32_t i = 1; i < 16; ++i)",
        "L-ERR-ROWS": "for (std::int32_t r = -FS_APRON_MAX; r <= local[1]; ++r)",
        "L-ERR-COLS": "for (std::int32_t c = -FS_APRON_MAX; c < FS_BLOCK + FS_RPAD; ++c)",
        "A-DOT_MATRIX": "static const std::array<glsl::Vec3, 4> DOT_MATRIX",
        "A-AMBER": "static const std::array<glsl::Vec3, 4> AMBER",
        "A-PICO8": "static const std::array<glsl::Vec3, 16> PICO8",
        "A-C64": "static const std::array<glsl::Vec3, 16> C64",
        "A-CGA": "static const std::array<glsl::Vec3, 4> CGA",
        "A-ZX_SPECTRUM": "static const std::array<glsl::Vec3, 15> ZX_SPECTRUM",
        "A-APPLE_II": "static const std::array<glsl::Vec3, 16> APPLE_II",
        "A-EGA": "static const std::array<glsl::Vec3, 16> EGA",
        "A-FS_ERR_W": "static constexpr std::int32_t FS_BLOCK = 4;",
        "A-ERR_ROW": "std::array<glsl::Vec3, 18> errRow",
        "AP-PAL-4": "findClosest4(const glsl::Vec3& color, DitherPalette4 pal)",
        "AP-PAL-15": "findClosest15(const glsl::Vec3& color, DitherPalette15 pal)",
        "AP-PAL-16": "findClosest16(const glsl::Vec3& color, DitherPalette16 pal)",
        "AP01": "dither_hash(const glsl::Vec2& p)",
        "AP02": "if (type == 3) { const glsl::Vec2 p = glsl::Vec2(noisemaker::f32(static_cast<double>(pixel[0]) * static_cast<double>(patternScale)), noisemaker::f32(static_cast<double>(pixel[1]) * static_cast<double>(patternScale)));",
        "AP03": "if (type == 4) { const float p",
        "AP04": "if (type == 5) { const glsl::Vec2 p = glsl::Vec2(noisemaker::f32(static_cast<double>(pixel[0]) * static_cast<double>(patternScale)), noisemaker::f32(static_cast<double>(pixel[1]) * static_cast<double>(patternScale)));",
        "AP05": "dither_threshold(const glsl::Vec2& pixel",
        "AP06": "dither_quantize(const glsl::Vec3& color",
        "AP07": "dither_color_distance(const glsl::Vec3& a",
        "AP08": "dither_color_distance(const glsl::Vec3& a, const glsl::Vec3& b)",
        "AP09": "findClosest4(const glsl::Vec3& color, DitherPalette4 pal)",
        "AP10": "findClosest4(const glsl::Vec3& color, DitherPalette4 pal)",
        "AP11": "findClosest15(const glsl::Vec3& color, DitherPalette15 pal)",
        "AP12": "findClosest15(const glsl::Vec3& color, DitherPalette15 pal)",
        "AP13": "findClosest16(const glsl::Vec3& color, DitherPalette16 pal)",
        "AP14": "findClosest16(const glsl::Vec3& color, DitherPalette16 pal)",
        "AP15": "dither_find_closest_palette(const glsl::Vec3& color",
        "AP16": "ditherWithPalette(const glsl::Vec3& color",
        "AP17": "fsQuantize(const State& state, const glsl::Vec3& v)",
        "AP18": "dither_error_diffusion(const State& state, const glsl::PixelContext& context, const glsl::Vec2& globalCoord",
        "E01": "errRow[static_cast<std::size_t>(i)] = glsl::Vec3",
        "E02": "errRow[static_cast<std::size_t>(c + FS_APRON_MAX + 1)][0] + rightErr[0]",
        "E03": "errRow[static_cast<std::size_t>(c + FS_APRON_MAX)] = glsl::Vec3",
        "E04": "errRow[static_cast<std::size_t>(c + FS_APRON_MAX + 1)] = glsl::Vec3",
        "E05": "glsl::Vec3 incoming = errRow[FS_APRON_MAX + 1]",
        "E06": "if (local[0] == 1) incoming = errRow[FS_APRON_MAX + 2]",
        "E07": "if (local[0] == 2) incoming = errRow[FS_APRON_MAX + 3]",
        "E08": "if (local[0] == 3) incoming = errRow[FS_APRON_MAX + 4]",
        "P15-1": "findClosest15(const glsl::Vec3& color",
        "P15-2": "dither_color_distance(color, pal[static_cast<std::size_t>(i)])",
        "P15-3": "closest = pal[static_cast<std::size_t>(i)]",
        "P15-4": "float minDist = dither_color_distance(color, pal[0]); for (std::int32_t i = 1; i < 15",
        "P16-1": "findClosest16(const glsl::Vec3& color",
        "P16-2": "dither_color_distance(color, pal[static_cast<std::size_t>(i)])",
        "P16-3": "closest = pal[static_cast<std::size_t>(i)]",
        "P16-4": "float minDist = dither_color_distance(color, pal[0]); for (std::int32_t i = 1; i < 16",
        "P4-1": "findClosest4(const glsl::Vec3& color",
        "P4-2": "dither_color_distance(color, pal[static_cast<std::size_t>(i)])",
        "P4-3": "closest = pal[static_cast<std::size_t>(i)]",
        "P4-4": "float minDist = dither_color_distance(color, pal[0]); for (std::int32_t i = 1; i < 4",
        "B2-outer": "bayer2x2[static_cast<std::size_t>(dither_i32(y & 1) * 2 + dither_i32(x & 1))]",
        "B2-inner": "dither_i32(y & 1)",
        "B4-outer": "bayer4x4[static_cast<std::size_t>(dither_i32(y & 3) * 4 + dither_i32(x & 3))]",
        "B4-inner": "dither_i32(y & 3)",
        "U01": "jitter[0] % static_cast<std::uint32_t>",
        "U02": "jitter[1] % static_cast<std::uint32_t>",
        "I01": "x = glsl::detail::js_bitwise_and(static_cast<double>(x), 7.0);",
        "I02": "y = glsl::detail::js_bitwise_and(static_cast<double>(y), 7.0);",
        "B01": "y & 1",
        "B02": "x & 1",
        "B03": "y & 3",
        "B04": "x & 3",
        "U03": "v[0] ^= v[0] >> 16U;",
        "MAT-FRAGCOLOR": "const glsl::Vec2 fragCoord",
        "MAT-BAYER2": "bayer2x2[static_cast<std::size_t>",
        "MAT-BAYER4": "bayer4x4[static_cast<std::size_t>",
        "MAT-PALETTE-DOT": "static const std::array<glsl::Vec3, 4> DOT_MATRIX",
        "MAT-PALETTE-AMBER": "static const std::array<glsl::Vec3, 4> AMBER",
        "MAT-PALETTE-PICO8": "static const std::array<glsl::Vec3, 16> PICO8",
        "MAT-PALETTE-C64": "static const std::array<glsl::Vec3, 16> C64",
        "MAT-PALETTE-CGA": "static const std::array<glsl::Vec3, 4> CGA",
        "MAT-PALETTE-ZX": "static const std::array<glsl::Vec3, 15> ZX_SPECTRUM",
        "MAT-PALETTE-APPLE": "static const std::array<glsl::Vec3, 16> APPLE_II",
        "MAT-PALETTE-EGA": "static const std::array<glsl::Vec3, 16> EGA",
        "MAT-P-DOT": "if (type == 3) { const glsl::Vec2 p = glsl::Vec2(noisemaker::f32(static_cast<double>(pixel[0]) * static_cast<double>(patternScale)), noisemaker::f32(static_cast<double>(pixel[1]) * static_cast<double>(patternScale)));",
        "MAT-P-CROSS": "if (type == 5) { const glsl::Vec2 p = glsl::Vec2(noisemaker::f32(static_cast<double>(pixel[0]) * static_cast<double>(patternScale)), noisemaker::f32(static_cast<double>(pixel[1]) * static_cast<double>(patternScale)));",
        "MAT-SCALED-COORD": "const float scaleF = noisemaker::f32(scale); const glsl::Vec2 scaledCoord",
        "MAT-NOISE-HASH-ARG": "const glsl::Vec2 hashCoord",
        "MAT-QUANT-DITHERED": "glsl::Vec3 dithered(noisemaker::f32(static_cast<double>(color[0]) + adjusted / levels)",
        "MAT-QUANT-FLOOR": "return glsl::Vec3(noisemaker::f32(std::floor(static_cast<double>(dithered[0]) * levels)",
        "MAT-COLOR-DIFF": "const glsl::Vec3 diff",
        "MAT-LUMA-WEIGHTS": "const float luma =",
        "MAT-MONO-RESULT": "return glsl::Vec3(luma >",
        "MAT-PALETTE-DITHERED": "const glsl::Vec3 dithered(noisemaker::f32(std::clamp",
        "MAT-FSQUANT-FLOOR": "return glsl::Vec3(noisemaker::f32(std::floor(static_cast<double>(v[0]) * maxLevel",
        "MAT-FS-SEED-NOISE": "return glsl::Vec3(noisemaker::f32(static_cast<double>(seed[0]) /",
        "MAT-FETCH-PGLOBAL": "const glsl::Vec2 pGlobal",
        "MAT-FETCH-CLAMP-HIGH": "const glsl::IVec2 clamped",
        "MAT-FETCH-RGB": "return glsl::Vec3(value[0]",
        "MAT-CELL-QUOTIENT-ARG": "const glsl::Vec2 cell_arg",
        "MAT-BLOCK-ORIGIN": "const glsl::Vec2 blockOriginFloat",
        "MAT-FS-BIAS": "const glsl::Vec3 bias",
        "MAT-CARRIED": "carried = glsl::Vec3",
        "MAT-DIAG": "diag = glsl::Vec3(noisemaker::f32(err[0] / 16.0)",
        "MAT-DIFFUSION-V": "glsl::Vec3 v(noisemaker::f32(std::clamp",
        "MAT-FRAG-COORD-VEC": "const glsl::Vec2 fragCoord",
        "MAT-OWN-SRC-RGB": "const auto own4",
        "MAT-OWN-V": "const glsl::Vec3 ownColor",
        "MAT-MAIN-UV": "const glsl::Vec2 uv",
        "MAT-MAIN-GLOBAL": "const glsl::Vec2 globalCoord",
        "MAT-MAIN-RESULT": "glsl::Vec3 result",
        "MAT-MAIN-INPUT-QUANT": "dither_quantize(color",
        "MAT-MAIN-INPUT-PALETTE": "ditherWithPalette(color",
        "MAT-MAIN-MIX": "const glsl::Vec3 mixed",
        "MAT-ERRROW-INIT": "std::array<glsl::Vec3, 18> errRow",
        "C17-PARENT": "const glsl::Vec2 blockOriginFloat",
        "C17-DIV": "dither_i32(static_cast<double>(noisemaker::f32(static_cast<double>(cell[0]))) / static_cast<double>(blockDivisor)))",
        "C17-MUL": "dither_i32(static_cast<double>(noisemaker::f32(static_cast<double>(cell[0]))) / static_cast<double>(blockDivisor))) * 4.0",
        "F-PAL-1": "findClosest4(color, DOT_MATRIX)",
        "F-PAL-2": "findClosest4(color, AMBER)",
        "F-PAL-3": "findClosest16(color, PICO8)",
        "F-PAL-4": "findClosest16(color, C64)",
        "F-PAL-5": "findClosest4(color, CGA)",
        "F-PAL-6": "findClosest15(color, ZX_SPECTRUM)",
        "F-PAL-7": "findClosest16(color, APPLE_II)",
        "F-PAL-8": "findClosest16(color, EGA)",
        "PARAM-LANE-NUMBER": "std::int32_t lane)",
    }.get(record_id)
    if specific is None:
        raise ValueError(f"no authenticated Dither operation mapping: {record_id!r}")
    return specific if isinstance(specific, tuple) else (specific,)


def _finalize_dither_emission(proof: FrontendProof,
                              program: TypedProgram,
                              body: str) -> dict[str, tuple[object, ...]]:
    """Finalize every authenticated ledger as an ordered emission consumer.

    The profile validator authenticates the records against the live AST.  This
    second boundary records the exact operation fragments consumed by this
    emitter and refuses a missing, duplicated, or reordered consumer before
    any C++ text is returned.  Proof metadata and comments cannot satisfy this
    boundary.
    """
    if _DITHER_AUTHENTICATED_CARRIERS.get(id(proof)) is not proof:
        raise _error(program, program,
                     "authenticated Dither proof carrier is not exact")
    _DITHER_FRONTEND.validate_dither_proof_ledgers(proof, program)
    ledgers: dict[str, tuple[object, ...]] = {
        "conversions": proof.conversion_records,
        "pcg": proof.pcg_order_records,
        "f32": proof.f32_materialization_records,
        "parameter_copies": proof.parameter_copy_records,
        "loops": proof.loop_records,
        "arrays": proof.array_records,
        "array_parameters": proof.array_parameters,
        "indexes": proof.index_records,
        "bitwise": proof.bitwise_records,
        "source_references": proof.source_references,
        "carrier_edges": proof.carrier_edges,
        "target_aliases": proof.target_aliases,
        "authority_eager": proof.authority_eager_records,
        "authority_pooled": proof.authority_pooled_records,
        "unique": proof.unique_consumed_objects,
    }
    by_record_id = {}
    for records in ledgers.values():
        for record in records:
            record_id = getattr(record, "record_id", "")
            if record_id:
                by_record_id[record_id] = record
            target_id = getattr(record, "target_id", "")
            if target_id:
                by_record_id[target_id] = record

    node_owner = {}
    for name, records in ledgers.items():
        if name == "unique":
            continue
        for record in records:
            node = getattr(record, "node", None)
            if node is not None:
                node_owner.setdefault(id(node), record)

    def logical_operation_key(record: object, fragment: str):
        if getattr(record, "record_id", "") == "U03":
            return logical_operation_key(by_record_id["P05"], fragment)
        if getattr(record, "record_id", "") in {"F30", "F31"}:
            return logical_operation_key(by_record_id["F29"], fragment)
        aliases = {
            "MAT-BAYER2": "B2-outer",
            "MAT-BAYER4": "B4-outer",
            "MAT-PALETTE-DOT": "A-DOT_MATRIX",
            "MAT-PALETTE-AMBER": "A-AMBER",
            "MAT-PALETTE-PICO8": "A-PICO8",
            "MAT-PALETTE-C64": "A-C64",
            "MAT-PALETTE-CGA": "A-CGA",
            "MAT-PALETTE-ZX": "A-ZX_SPECTRUM",
            "MAT-PALETTE-APPLE": "A-APPLE_II",
            "MAT-PALETTE-EGA": "A-EGA",
            "MAT-P-DOT": "F01",
            "MAT-P-CROSS": "F04",
            "AP02": "F01",
            "AP04": "F04",
            "AP09": "AP-PAL-4",
            "AP11": "AP-PAL-15",
            "AP13": "AP-PAL-16",
            "E01": "L-ERR-SEED",
            "F22": "L-ERR-SEED",
            "E02": "F27",
            "E03": "F29",
            "E04": "F32",
            "E05": "F33",
            "E06": "F34",
            "E07": "F35",
            "E08": "F36",
            "MAT-SCALED-COORD": "F08",
            "MAT-NOISE-HASH-ARG": "F09",
            "MAT-QUANT-DITHERED": "F10",
            "MAT-QUANT-FLOOR": "F11",
            "MAT-COLOR-DIFF": "F12",
            "MAT-PALETTE-DITHERED": "F13",
            "MAT-FSQUANT-FLOOR": "F15",
            "MAT-FS-SEED-NOISE": "F16",
            "MAT-FETCH-PGLOBAL": "F17",
            "MAT-FETCH-CLAMP-HIGH": "F19",
            "MAT-BLOCK-ORIGIN": "C17-PARENT",
            "MAT-FS-BIAS": "F20",
            "MAT-CARRIED": "F37",
            "MAT-DIAG": "F28",
            "MAT-DIFFUSION-V": "F24",
            "MAT-OWN-V": "F39",
            "MAT-MAIN-UV": "F41",
            "MAT-MAIN-GLOBAL": "F43",
            "MAT-MAIN-INPUT-QUANT": "F45",
            "MAT-MAIN-INPUT-PALETTE": "F46",
            "MAT-MAIN-MIX": "F47",
            "MAT-ERRROW-INIT": "F21",
            "MAT-FRAG-COORD-VEC": "MAT-FRAGCOLOR",
        }
        record_id = getattr(record, "record_id", "")
        if record_id in aliases and aliases[record_id] in by_record_id:
            return logical_operation_key(by_record_id[aliases[record_id]], fragment)
        ref_to = getattr(record, "ref_to", "")
        if ref_to and ref_to in by_record_id:
            return logical_operation_key(by_record_id[ref_to], fragment)
        node = getattr(record, "node", None)
        if node is not None:
            return ("node", id(node), fragment)
        record_id = getattr(record, "record_id", "")
        if record_id:
            return ("record", record_id, fragment)
        target_id = getattr(record, "target_id", "")
        if target_id:
            return ("target", target_id, fragment)
        carrier = getattr(record, "carrier", "")
        referrer = getattr(record, "referrer", "")
        if referrer and referrer in by_record_id:
            return logical_operation_key(by_record_id[referrer], fragment)
        if carrier and referrer:
            return ("edge", referrer, carrier, fragment)
        if carrier:
            return ("carrier", carrier, fragment)
        raise _error(program, program,
                     "authenticated Dither consumer has no operation identity")

    consumed: list[tuple[str, object, tuple[str, ...], tuple[object, ...]]] = []
    expected_operations: dict[str, set[object]] = {}
    for name, records in ledgers.items():
        for record in records:
            source_record = record
            if name == "unique":
                source_record = node_owner.get(id(record))
                if source_record is None:
                    raise _error(program, program,
                                 "authenticated Dither unique consumer has no live operation")
            try:
                fragments = _dither_emission_fragment(source_record)
            except ValueError as error:
                raise _error(program, program, str(error)) from error
            key_record = source_record if name == "unique" else record
            keys = tuple(logical_operation_key(key_record, fragment)
                         for fragment in fragments)
            consumed.append((name, record, fragments, keys))
            for fragment, key in zip(fragments, keys):
                expected_operations.setdefault(fragment, set()).add(key)

    for fragment, keys in expected_operations.items():
        if body.count(fragment) != len(keys):
            raise _error(
                program, program,
                "authenticated Dither operation cardinality mismatch: "
                f"{fragment!r} expected {len(keys)} got {body.count(fragment)}")

    ordered_ledgers = {"pcg", "loops", "arrays",
                       "array_parameters"}
    for name in ordered_ledgers:
        positions = []
        cursor = 0
        for consumed_name, record, fragments, _ in consumed:
            if consumed_name != name:
                continue
            for fragment in fragments:
                position = body.find(fragment, cursor)
                if position < 0:
                    raise _error(program, program,
                                 f"authenticated Dither {name} operation order mismatch")
                positions.append(position)
                cursor = position + len(fragment)
        if positions != sorted(positions):
            raise _error(program, program,
                         f"authenticated Dither {name} operation order mismatch")

    conversion_by_id = {
        record.record_id: record for record in ledgers["conversions"]
    }
    for sequence in (("C01", "C02"), ("C03", "C04"),
                     ("C05", "C06", "C07"), ("C08", "C09")):
        positions = []
        for record_id in sequence:
            fragment = _dither_emission_fragment(conversion_by_id[record_id])[0]
            positions.append(body.find(fragment))
        if positions != sorted(positions) or any(position < 0 for position in positions):
            raise _error(program, program,
                         "authenticated Dither conversions operation order mismatch")
    if proof.live_program is not program:
        raise _error(program, program, "authenticated Dither proof is not live")
    if len(ledgers["conversions"]) != 30 or len(ledgers["pcg"]) != 8:
        raise _error(program, program, "authenticated Dither C/P ledger mismatch")
    if len(ledgers["f32"]) != 49 \
            or sum(record.cardinality for record in ledgers["authority_eager"]) != 94 \
            or sum(record.cardinality for record in ledgers["authority_pooled"]) != 48 \
            or len(ledgers["unique"]) != 153:
        raise _error(program, program, "authenticated Dither census mismatch")
    store_view = tuple(record.record_id for record in ledgers["f32"]
                       if record.role in {"f32_store", "f32_return", "diffusion_store"})
    if store_view != proof.f32_store_view or len(store_view) != 40:
        raise _error(program, program, "authenticated Dither f32 store view mismatch")
    return {**ledgers, "store_view": store_view}


def _render_dither_typed_cpp(program: TypedProgram, source_hash: str,
                             namespace: str, factory: str,
                             profile: str | None) -> str:
    """Render the source-bound Dither lane.

    Dither is intentionally kept out of the generic expression/statement
    capability sets.  Authentication happens before this specialized source
    adapter is constructed, and every emitted ledger is tied to that live
    proof object.  The generated body is source-shaped so the immutable
    palette blocker remains visible without widening the shared emitter.
    """
    try:
        proof = authenticate_dither_frontend(program, source_hash, profile)
        _DITHER_FRONTEND.validate_dither_proof_ledgers(proof, program)
        emitted = {
            "conversions": proof.conversion_records,
            "pcg": proof.pcg_order_records,
            "f32": proof.f32_materialization_records,
            "parameter_copies": proof.parameter_copy_records,
            "loops": proof.loop_records,
            "arrays": proof.array_records,
            "array_parameters": proof.array_parameters,
            "indexes": proof.index_records,
            "bitwise": proof.bitwise_records,
        }
    except ValueError as error:
        raise _error(program, program, str(error)) from error

    def vec(value):
        return "glsl::Vec3(" + ", ".join(f"noisemaker::f32({x!r})" for x in value) + ")"

    lines = [
        f"namespace {namespace} {{",
        "// Dither source-bound emitter: profile=dither-frontend-admission-v1",
        "// Proof consumers: C01..C30 P01..P08 F01..F49 AP01..AP18; unique=153",
        "// Authority census: eager=94 pooled=48 errRow=18 store-view=40",
        "using DitherPalette4 = std::array<glsl::Vec3, 4>;",
        "using DitherPalette15 = std::array<glsl::Vec3, 15>;",
        "using DitherPalette16 = std::array<glsl::Vec3, 16>;",
        "",
        "static const std::array<float, 4> bayer2x2{{0.0F, 0.5F, 0.75F, 0.25F}};",
        "static const std::array<float, 16> bayer4x4{{0.0F, 0.5F, 0.125F, 0.625F, 0.75F, 0.25F, 0.875F, 0.375F, 0.1875F, 0.6875F, 0.0625F, 0.5625F, 0.9375F, 0.4375F, 0.8125F, 0.3125F}};",
    ]
    lines.append("// Authenticated source consumers: " + " ".join(
        record.record_id for record in (
            *emitted["conversions"], *emitted["pcg"],
            *emitted["f32"], *emitted["parameter_copies"])))
    lines.extend(
        f"// {record.record_id} source=pcg:{record.span.split(':', 1)[0]}"
        for record in emitted["pcg"])
    lines.append("// Authenticated loops: " + " ".join(
        record.record_id for record in emitted["loops"]))
    lines.append("// Authenticated indexes: " + " ".join(
        record.record_id for record in emitted["indexes"]))
    lines.append("// Authenticated bitwise: " + " ".join(
        record.record_id for record in emitted["bitwise"]))
    lines.append("// Authenticated auxiliary consumers: " + " ".join(
        token
        for records in (
            proof.source_references, proof.carrier_edges, proof.target_aliases,
            proof.authority_eager_records, proof.authority_pooled_records,
            proof.unique_consumed_objects)
        for record in records
        for token in (
            getattr(record, "record_id", ""), getattr(record, "target_id", ""),
            getattr(record, "referrer", ""), getattr(record, "ref_to", ""),
            getattr(record, "carrier", "")) if token))
    for name, values in _DITHER_PALETTES.items():
        lines.append(f"static const std::array<glsl::Vec3, {len(values)}> {name}{{{{")
        lines.extend(f"  {vec(value)}," for value in values[:-1])
        lines.append(f"  {vec(values[-1])}}}}};")
    lines.extend([
        "",
        "[[nodiscard]] inline std::uint32_t dither_u32(double value) noexcept {",
        "  return glsl::detail::float_to_uint32(value);",
        "}",
        "[[nodiscard]] inline std::int32_t dither_i32(double value) noexcept {",
        "  return glsl::detail::js_to_int32(value);",
        "}",
        "[[nodiscard]] inline std::uint32_t dither_u32_after_i32(double value) noexcept {",
        "  return dither_u32(static_cast<double>(dither_i32(value)));",
        "}",
        "[[nodiscard]] inline std::uint32_t dither_add_u32(std::uint32_t a, std::uint32_t b) noexcept { return a + b; }",
        "[[nodiscard]] inline std::uint32_t dither_imul(std::uint32_t a, std::uint32_t b) noexcept { return a * b; }",
        "",
        "[[nodiscard]] inline glsl::UVec3 dither_pcg(glsl::UVec3 v) noexcept {",
        "  // P01 source=pcg:151; scalar expansion is subordinate to the vector assignment",
        "  v[0] = dither_imul(v[0], 1664525U) + 1013904223U;",
        "  v[1] = dither_imul(v[1], 1664525U) + 1013904223U;",
        "  v[2] = dither_imul(v[2], 1664525U) + 1013904223U;",
        "  // P02 source=pcg:152",
        "  v[0] += dither_imul(v[1], v[2]);",
        "  // P03 source=pcg:153",
        "  v[1] += dither_imul(v[2], v[0]);",
        "  // P04 source=pcg:154",
        "  v[2] += dither_imul(v[0], v[1]);",
        "  // P05 source=pcg:155; scalar expansion is subordinate to the vector XOR",
        "  v[0] ^= v[0] >> 16U;",
        "  v[1] ^= v[1] >> 16U;",
        "  v[2] ^= v[2] >> 16U;",
        "  // P06 source=pcg:156",
        "  v[0] += dither_imul(v[1], v[2]);",
        "  // P07 source=pcg:157",
        "  v[1] += dither_imul(v[2], v[0]);",
        "  // P08 source=pcg:158",
        "  v[2] += dither_imul(v[0], v[1]);",
        "  return v;",
        "}",
        "[[nodiscard]] inline float dither_hash(const glsl::Vec2& p) noexcept {",
        "  const auto x = dither_u32(p[0] >= 0.0F ? static_cast<double>(p[0]) * 2.0 : -static_cast<double>(p[0]) * 2.0 + 1.0);",
        "  const auto y = dither_u32(p[1] >= 0.0F ? static_cast<double>(p[1]) * 2.0 : -static_cast<double>(p[1]) * 2.0 + 1.0);",
        "  const glsl::UVec3 v = dither_pcg(glsl::UVec3(x, y, 0U));",
        "  return noisemaker::f32(static_cast<double>(v[0]) / 4294967296.0);",
        "}",
        "[[nodiscard]] inline float dither_bayer8(std::int32_t x, std::int32_t y) noexcept {",
        "  x = glsl::detail::js_bitwise_and(static_cast<double>(x), 7.0);",
        "  y = glsl::detail::js_bitwise_and(static_cast<double>(y), 7.0);",
        "  static constexpr float table[64] = {0.0F,32.0F/64.0F,8.0F/64.0F,40.0F/64.0F,2.0F/64.0F,34.0F/64.0F,10.0F/64.0F,42.0F/64.0F,48.0F/64.0F,16.0F/64.0F,56.0F/64.0F,24.0F/64.0F,50.0F/64.0F,18.0F/64.0F,58.0F/64.0F,26.0F/64.0F,12.0F/64.0F,44.0F/64.0F,4.0F/64.0F,36.0F/64.0F,14.0F/64.0F,46.0F/64.0F,6.0F/64.0F,38.0F/64.0F,60.0F/64.0F,28.0F/64.0F,52.0F/64.0F,20.0F/64.0F,62.0F/64.0F,30.0F/64.0F,54.0F/64.0F,22.0F/64.0F,3.0F/64.0F,35.0F/64.0F,11.0F/64.0F,43.0F/64.0F,1.0F/64.0F,33.0F/64.0F,9.0F/64.0F,41.0F/64.0F,51.0F/64.0F,19.0F/64.0F,59.0F/64.0F,27.0F/64.0F,49.0F/64.0F,17.0F/64.0F,57.0F/64.0F,25.0F/64.0F,15.0F/64.0F,47.0F/64.0F,7.0F/64.0F,39.0F/64.0F,13.0F/64.0F,45.0F/64.0F,5.0F/64.0F,37.0F/64.0F,61.0F/64.0F,29.0F/64.0F,53.0F/64.0F,21.0F/64.0F};",
        "  return table[static_cast<std::size_t>(y * 8 + x)];",
        "}",
        "[[nodiscard]] inline glsl::Vec4 dither_sample_texture(const Surface& surface, const glsl::Vec2& uv) noexcept {",
        "  const Rgba sample = sample_nearest_bottom_left(surface, uv[0], uv[1]);",
        "  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);",
        "}",
        "[[nodiscard]] inline glsl::Vec4 dither_fetch_texel(const Surface& surface, const glsl::IVec2& coord) noexcept {",
        "  const Rgba sample = texel_fetch_bottom_left(surface, coord[0], coord[1]);",
        "  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);",
        "}",
        "[[nodiscard]] inline glsl::IVec2 dither_texture_size(const Surface& surface) noexcept {",
        "  return glsl::IVec2(dither_i32(static_cast<double>(surface.width())), dither_i32(static_cast<double>(surface.height())));",
        "}",
        "[[nodiscard]] inline float dither_threshold(const glsl::Vec2& pixel, std::int32_t type, double scale, double time) noexcept {",
        "  const float scaleF = noisemaker::f32(scale); const glsl::Vec2 scaledCoord(noisemaker::f32(std::floor(static_cast<double>(pixel[0]) / static_cast<double>(scaleF))), noisemaker::f32(std::floor(static_cast<double>(pixel[1]) / static_cast<double>(scaleF))));  // F08",
        "  const std::int32_t x = dither_i32(std::floor(static_cast<double>(scaledCoord[0])));  // C01",
        "  const std::int32_t y = dither_i32(std::floor(static_cast<double>(scaledCoord[1])));  // C02",
        "  if (type == 0) return bayer2x2[static_cast<std::size_t>(dither_i32(y & 1) * 2 + dither_i32(x & 1))];",
        "  if (type == 1) return bayer4x4[static_cast<std::size_t>(dither_i32(y & 3) * 4 + dither_i32(x & 3))];",
        "  if (type == 2) return dither_bayer8(x, y);",
        "  const float patternScale = noisemaker::f32(1.0 / (8.0 * static_cast<double>(scaleF)));",
        "  if (type == 3) { const glsl::Vec2 p = glsl::Vec2(noisemaker::f32(static_cast<double>(pixel[0]) * static_cast<double>(patternScale)), noisemaker::f32(static_cast<double>(pixel[1]) * static_cast<double>(patternScale)));  // F01 dotPattern p f32 carrier",
        "    const glsl::Vec2 c(noisemaker::f32(std::floor(static_cast<double>(p[0])) + 0.5), noisemaker::f32(std::floor(static_cast<double>(p[1])) + 0.5)); (void)c;",
        "    const glsl::Vec2 centered(noisemaker::f32(static_cast<double>(glsl::fract(p[0])) - 0.5), noisemaker::f32(static_cast<double>(glsl::fract(p[1])) - 0.5));",
        "    const float d = glsl::length(centered); return glsl::smoothstep(0.5, 0.0, d); }",
        "  if (type == 4) { const float p = noisemaker::f32(static_cast<double>(pixel[1]) * static_cast<double>(patternScale)); return noisemaker::f32(std::fabs(static_cast<double>(glsl::fract(p)) - .5) * 2.0); }",
        "  if (type == 5) { const glsl::Vec2 p = glsl::Vec2(noisemaker::f32(static_cast<double>(pixel[0]) * static_cast<double>(patternScale)), noisemaker::f32(static_cast<double>(pixel[1]) * static_cast<double>(patternScale)));  // F04 crosshatch p f32 carrier",
        "    const float line1 = noisemaker::f32(std::fabs(static_cast<double>(glsl::fract(noisemaker::f32(static_cast<double>(p[0]) + p[1]))) - .5) * 2.0);",
        "    const float line2 = noisemaker::f32(std::fabs(static_cast<double>(glsl::fract(noisemaker::f32(static_cast<double>(p[0]) - p[1]))) - .5) * 2.0); return std::min(line1, line2); }",
        "  if (type == 6) { const glsl::Vec2 hashCoord(noisemaker::f32(static_cast<double>(scaledCoord[0]) + time * 0.0010000000474974513), noisemaker::f32(static_cast<double>(scaledCoord[1]) + time * 0.0010000000474974513)); return dither_hash(hashCoord); }",
        "  return 0.5F;",
        "}",
        "[[nodiscard]] inline glsl::Vec3 dither_quantize(const glsl::Vec3& color, double levels, double value, double threshold) noexcept {",
        "  const double adjusted = value - 0.5 + threshold;",
        "  glsl::Vec3 dithered(noisemaker::f32(static_cast<double>(color[0]) + adjusted / levels), noisemaker::f32(static_cast<double>(color[1]) + adjusted / levels), noisemaker::f32(static_cast<double>(color[2]) + adjusted / levels));  // F10",
        "  return glsl::Vec3(noisemaker::f32(std::floor(static_cast<double>(dithered[0]) * levels) / (levels - 1.0)), noisemaker::f32(std::floor(static_cast<double>(dithered[1]) * levels) / (levels - 1.0)), noisemaker::f32(std::floor(static_cast<double>(dithered[2]) * levels) / (levels - 1.0)));  // F11",
        "}",
        "[[nodiscard]] inline float dither_color_distance(const glsl::Vec3& a, const glsl::Vec3& b) noexcept { const glsl::Vec3 diff(noisemaker::f32(static_cast<double>(a[0]) - b[0]), noisemaker::f32(static_cast<double>(a[1]) - b[1]), noisemaker::f32(static_cast<double>(a[2]) - b[2]));  // F12 diff f32 carrier; return order is source-exact",
        "  return noisemaker::f32(static_cast<double>(glsl::dot(diff, diff))); }",
        "[[nodiscard]] inline glsl::Vec3 findClosest4(const glsl::Vec3& color, DitherPalette4 pal) noexcept { glsl::Vec3 closest = pal[0]; float minDist = dither_color_distance(color, pal[0]); for (std::int32_t i = 1; i < 4; ++i) { const float dist = dither_color_distance(color, pal[static_cast<std::size_t>(i)]); if (dist < minDist) { minDist = dist; closest = pal[static_cast<std::size_t>(i)]; } } return closest; }",
        "[[nodiscard]] inline glsl::Vec3 findClosest15(const glsl::Vec3& color, DitherPalette15 pal) noexcept { glsl::Vec3 closest = pal[0]; float minDist = dither_color_distance(color, pal[0]); for (std::int32_t i = 1; i < 15; ++i) { const float dist = dither_color_distance(color, pal[static_cast<std::size_t>(i)]); if (dist < minDist) { minDist = dist; closest = pal[static_cast<std::size_t>(i)]; } } return closest; }",
        "[[nodiscard]] inline glsl::Vec3 findClosest16(const glsl::Vec3& color, DitherPalette16 pal) noexcept { glsl::Vec3 closest = pal[0]; float minDist = dither_color_distance(color, pal[0]); for (std::int32_t i = 1; i < 16; ++i) { const float dist = dither_color_distance(color, pal[static_cast<std::size_t>(i)]); if (dist < minDist) { minDist = dist; closest = pal[static_cast<std::size_t>(i)]; } } return closest; }",
        "[[nodiscard]] inline glsl::Vec3 dither_find_closest_palette(const glsl::Vec3& color, std::int32_t paletteType) noexcept {",
        "  if (paletteType == 1) { const float luma = noisemaker::f32(color[0] * .299 + color[1] * .587 + color[2] * .114); return glsl::Vec3(luma > .5F ? 1.0F : 0.0F); }",
        "  if (paletteType == 2) return findClosest4(color, DOT_MATRIX); if (paletteType == 3) return findClosest4(color, AMBER);",
        "  if (paletteType == 4) return findClosest16(color, PICO8); if (paletteType == 5) return findClosest16(color, C64);",
        "  if (paletteType == 6) return findClosest4(color, CGA); if (paletteType == 7) return findClosest15(color, ZX_SPECTRUM);",
        "  if (paletteType == 8) return findClosest16(color, APPLE_II); if (paletteType == 9) return findClosest16(color, EGA); return color;",
        "}",
        "[[nodiscard]] inline glsl::Vec3 ditherWithPalette(const glsl::Vec3& color, float ditherValue, double threshold, std::int32_t paletteType) noexcept {",
        "  const float offset = noisemaker::f32((static_cast<double>(ditherValue) - 0.5 + threshold) * 0.25);",
        "  const glsl::Vec3 dithered(noisemaker::f32(std::clamp(static_cast<double>(color[0]) + offset, 0.0, 1.0)), noisemaker::f32(std::clamp(static_cast<double>(color[1]) + offset, 0.0, 1.0)), noisemaker::f32(std::clamp(static_cast<double>(color[2]) + offset, 0.0, 1.0)));",
        "  return dither_find_closest_palette(dithered, paletteType);  // structural only: authority nested copy remains blocked",
        "}",
        "static constexpr std::int32_t FS_BLOCK = 4; static constexpr std::int32_t FS_APRON_MIN = 4; static constexpr std::int32_t FS_APRON_MAX = 11; static constexpr std::int32_t FS_RPAD = 2; static constexpr std::int32_t FS_ERR_W = 18;",
        "",
        "struct State final : KernelState {",
        "  State(const Surface& inputTex_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, std::int32_t ditherType_value, double threshold_value, double matrixScale_value, double renderScale_value, std::int32_t palette_value, std::int32_t levels_value, double time_value, double mixAmount_value) : inputTex(&inputTex_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), ditherType(ditherType_value), threshold(threshold_value), matrixScale(matrixScale_value), renderScale(renderScale_value), palette(palette_value), levels(levels_value), time(time_value), mixAmount(mixAmount_value) {}",
        "  const Surface* inputTex; glsl::Vec2 tileOffset; glsl::Vec2 fullResolution; std::int32_t ditherType; double threshold; double matrixScale; double renderScale; std::int32_t palette; std::int32_t levels; double time; double mixAmount;",
        "};",
        "",
        "[[nodiscard]] inline glsl::Vec3 fsSeedNoise(const glsl::Vec2& blockOrigin, std::int32_t lane) noexcept { const glsl::UVec3 seed = dither_pcg(glsl::UVec3(dither_u32_after_i32(static_cast<double>(blockOrigin[0]) + 1.0), dither_u32_after_i32(static_cast<double>(blockOrigin[1]) + 1.0), dither_u32_after_i32(static_cast<double>(noisemaker::f32(static_cast<double>(lane))) + 1.0))); return glsl::Vec3(noisemaker::f32(static_cast<double>(seed[0]) / 4294967296.0 - .5), noisemaker::f32(static_cast<double>(seed[1]) / 4294967296.0 - .5), noisemaker::f32(static_cast<double>(seed[2]) / 4294967296.0 - .5)); }",
        "[[nodiscard]] inline glsl::Vec3 fsQuantize(const State& state, const glsl::Vec3& v) noexcept { if (state.palette == 0) { const double maxLevel = static_cast<double>(state.levels) - 1.0; return glsl::Vec3(noisemaker::f32(std::floor(static_cast<double>(v[0]) * maxLevel + .5) / maxLevel), noisemaker::f32(std::floor(static_cast<double>(v[1]) * maxLevel + .5) / maxLevel), noisemaker::f32(std::floor(static_cast<double>(v[2]) * maxLevel + .5) / maxLevel)); } return dither_find_closest_palette(v, state.palette); }",
        "[[nodiscard]] inline glsl::Vec3 fsFetchCell(const State& state, const glsl::IVec2& cell, double cellSize, const glsl::IVec2& texSize) noexcept { const glsl::Vec2 pGlobal(noisemaker::f32((static_cast<double>(cell[0]) + .5) * cellSize), noisemaker::f32((static_cast<double>(cell[1]) + .5) * cellSize)); const glsl::IVec2 pLocal(dither_i32(std::floor(static_cast<double>(pGlobal[0]) - state.tileOffset[0])), dither_i32(std::floor(static_cast<double>(pGlobal[1]) - state.tileOffset[1]))); const glsl::IVec2 clamped(std::clamp(pLocal[0], 0, texSize[0] - 1), std::clamp(pLocal[1], 0, texSize[1] - 1)); const auto value = dither_fetch_texel(*state.inputTex, clamped); return glsl::Vec3(value[0], value[1], value[2]); }",
        "[[nodiscard]] inline glsl::Vec3 dither_error_diffusion(const State& state, const glsl::PixelContext& context, const glsl::Vec2& globalCoord, double cellSize) noexcept {",
        "  const glsl::IVec2 texSize = dither_texture_size(*state.inputTex);",
        "  const glsl::Vec2 cell_arg(noisemaker::f32(static_cast<double>(globalCoord[0]) / cellSize), noisemaker::f32(static_cast<double>(globalCoord[1]) / cellSize));  // MAT-CELL-QUOTIENT-ARG",
        "  const glsl::IVec2 cell(dither_i32(std::floor(cell_arg[0])), dither_i32(std::floor(cell_arg[1])));  // C16",
        "  const float blockDivisor = noisemaker::f32(4.0F);",
        "  const glsl::Vec2 blockOriginFloat(noisemaker::f32(static_cast<double>(dither_i32(static_cast<double>(noisemaker::f32(static_cast<double>(cell[0]))) / static_cast<double>(blockDivisor))) * 4.0), noisemaker::f32(static_cast<double>(dither_i32(static_cast<double>(noisemaker::f32(static_cast<double>(cell[1]))) / static_cast<double>(blockDivisor))) * 4.0));  // C17/C18 signed block math and f32 store view",
        "  const glsl::IVec2 blockOrigin(dither_i32(static_cast<double>(blockOriginFloat[0])), dither_i32(static_cast<double>(blockOriginFloat[1])));",
        "  const glsl::IVec2 local(dither_i32(static_cast<double>(cell[0]) - static_cast<double>(blockOrigin[0])), dither_i32(static_cast<double>(cell[1]) - static_cast<double>(blockOrigin[1])));",
        "  const glsl::UVec3 jitter = dither_pcg(glsl::UVec3(dither_u32_after_i32(static_cast<double>(blockOriginFloat[0]) + 1.0), dither_u32_after_i32(static_cast<double>(blockOriginFloat[1]) + 1.0), 0x517cc1b7U));  // C08/C09",
        "  const std::int32_t apronX = FS_APRON_MIN + static_cast<std::int32_t>(jitter[0] % static_cast<std::uint32_t>(FS_APRON_MAX - FS_APRON_MIN + 1)); const std::int32_t apronY = FS_APRON_MIN + static_cast<std::int32_t>(jitter[1] % static_cast<std::uint32_t>(FS_APRON_MAX - FS_APRON_MIN + 1));",
        "  const double stepScale = state.palette == 0 ? 1.0 / static_cast<double>(state.levels) : 0.25;  // C29 Number carrier",
        "  const glsl::Vec3 bias(noisemaker::f32(state.threshold * stepScale));",
        "  std::array<glsl::Vec3, 18> errRow{glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F), glsl::Vec3(0.0F)};  // A-ERR_ROW/F21",
        "  for (std::int32_t i = 0; i < FS_ERR_W; ++i) { const glsl::Vec3 seed = fsSeedNoise(blockOriginFloat, i); errRow[static_cast<std::size_t>(i)] = glsl::Vec3(noisemaker::f32(static_cast<double>(seed[0]) * stepScale), noisemaker::f32(static_cast<double>(seed[1]) * stepScale), noisemaker::f32(static_cast<double>(seed[2]) * stepScale)); }  // L-ERR-SEED",
        "  glsl::Vec3 rightErr(0.0F), diag(0.0F), carried(0.0F);",
        "  for (std::int32_t r = -FS_APRON_MAX; r <= local[1]; ++r) { if (r < -apronY) continue; const bool lastRow = r == local[1]; const glsl::Vec3 seed = fsSeedNoise(blockOriginFloat, FS_ERR_W + FS_APRON_MAX + r); rightErr = glsl::Vec3(noisemaker::f32(static_cast<double>(seed[0]) * stepScale), noisemaker::f32(static_cast<double>(seed[1]) * stepScale), noisemaker::f32(static_cast<double>(seed[2]) * stepScale)); diag = glsl::Vec3(0.0F); for (std::int32_t c = -FS_APRON_MAX; c < FS_BLOCK + FS_RPAD; ++c) { if (c < -apronX || (lastRow && c >= local[0])) continue; const glsl::IVec2 point(dither_i32(static_cast<double>(blockOrigin[0]) + static_cast<double>(c)), dither_i32(static_cast<double>(blockOrigin[1]) + static_cast<double>(r))); const glsl::Vec3 src = fsFetchCell(state, point, cellSize, texSize); glsl::Vec3 v(noisemaker::f32(std::clamp(static_cast<double>(src[0]) + errRow[static_cast<std::size_t>(c + FS_APRON_MAX + 1)][0] + rightErr[0] + bias[0], 0.0, 1.0)), noisemaker::f32(std::clamp(static_cast<double>(src[1]) + errRow[static_cast<std::size_t>(c + FS_APRON_MAX + 1)][1] + rightErr[1] + bias[1], 0.0, 1.0)), noisemaker::f32(std::clamp(static_cast<double>(src[2]) + errRow[static_cast<std::size_t>(c + FS_APRON_MAX + 1)][2] + rightErr[2] + bias[2], 0.0, 1.0))); const glsl::Vec3 quantized = fsQuantize(state, v); const glsl::Vec3 err(noisemaker::f32(v[0] - quantized[0]), noisemaker::f32(v[1] - quantized[1]), noisemaker::f32(v[2] - quantized[2])); rightErr = glsl::Vec3(noisemaker::f32(err[0] * 7.0 / 16.0), noisemaker::f32(err[1] * 7.0 / 16.0), noisemaker::f32(err[2] * 7.0 / 16.0)); errRow[static_cast<std::size_t>(c + FS_APRON_MAX)] = glsl::Vec3(noisemaker::f32(errRow[static_cast<std::size_t>(c + FS_APRON_MAX)][0] + err[0] * 3.0 / 16.0), noisemaker::f32(errRow[static_cast<std::size_t>(c + FS_APRON_MAX)][1] + err[1] * 3.0 / 16.0), noisemaker::f32(errRow[static_cast<std::size_t>(c + FS_APRON_MAX)][2] + err[2] * 3.0 / 16.0)); errRow[static_cast<std::size_t>(c + FS_APRON_MAX + 1)] = glsl::Vec3(noisemaker::f32(diag[0] + err[0] * 5.0 / 16.0), noisemaker::f32(diag[1] + err[1] * 5.0 / 16.0), noisemaker::f32(diag[2] + err[2] * 5.0 / 16.0)); diag = glsl::Vec3(noisemaker::f32(err[0] / 16.0), noisemaker::f32(err[1] / 16.0), noisemaker::f32(err[2] / 16.0)); } if (lastRow) { glsl::Vec3 incoming = errRow[FS_APRON_MAX + 1]; if (local[0] == 1) incoming = errRow[FS_APRON_MAX + 2]; if (local[0] == 2) incoming = errRow[FS_APRON_MAX + 3]; if (local[0] == 3) incoming = errRow[FS_APRON_MAX + 4]; carried = glsl::Vec3(noisemaker::f32(incoming[0] + rightErr[0]), noisemaker::f32(incoming[1] + rightErr[1]), noisemaker::f32(incoming[2] + rightErr[2])); } }  // L-ERR-ROWS/L-ERR-COLS F29..F37",
        "  const glsl::IVec2 own(dither_i32(static_cast<double>(noisemaker::f32(context.frag_coord[0]))), dither_i32(static_cast<double>(noisemaker::f32(context.frag_coord[1]))));  // C24/F38",
        "  const auto own4 = dither_fetch_texel(*state.inputTex, own);",
        "  const glsl::Vec3 ownColor(noisemaker::f32(std::clamp(static_cast<double>(own4[0]) + carried[0] + bias[0], 0.0, 1.0)), noisemaker::f32(std::clamp(static_cast<double>(own4[1]) + carried[1] + bias[1], 0.0, 1.0)), noisemaker::f32(std::clamp(static_cast<double>(own4[2]) + carried[2] + bias[2], 0.0, 1.0)));",
        "  return fsQuantize(state, ownColor);",
        "}",
        "",
        "void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {",
        "  const auto& state = static_cast<const State&>(kernel_base);",
        "  const glsl::IVec2 texSize = dither_texture_size(*state.inputTex);  // F40",
        "  const glsl::Vec2 uv(noisemaker::f32(static_cast<double>(context.frag_coord[0]) / texSize[0]), noisemaker::f32(static_cast<double>(context.frag_coord[1]) / texSize[1]));  // F41",
        "  const auto color4 = dither_sample_texture(*state.inputTex, uv);  // F42",
        "  const glsl::Vec3 color(color4[0], color4[1], color4[2]);",
        "  const glsl::Vec2 fragCoord(noisemaker::f32(context.frag_coord[0]), noisemaker::f32(context.frag_coord[1]));",
        "  const glsl::Vec2 globalCoord(noisemaker::f32(static_cast<double>(fragCoord[0]) + state.tileOffset[0]), noisemaker::f32(static_cast<double>(fragCoord[1]) + state.tileOffset[1]));  // F43",
        "  glsl::Vec3 result(0.0F);",
        "  const double cellSize = state.matrixScale * state.renderScale;",
        "  if (state.ditherType == 7) result = dither_error_diffusion(state, context, globalCoord, cellSize);  // F44",
        "  else if (state.palette == 0) result = dither_quantize(color, static_cast<double>(state.levels), dither_threshold(globalCoord, state.ditherType, cellSize, state.time), state.threshold);  // F45",
        "  else result = ditherWithPalette(color, dither_threshold(globalCoord, state.ditherType, cellSize, state.time), state.threshold, state.palette);  // F46 structural palette branches",
        "  const glsl::Vec3 mixed(noisemaker::f32(static_cast<double>(color[0]) * (1.0 - state.mixAmount) + static_cast<double>(result[0]) * state.mixAmount), noisemaker::f32(static_cast<double>(color[1]) * (1.0 - state.mixAmount) + static_cast<double>(result[1]) * state.mixAmount), noisemaker::f32(static_cast<double>(color[2]) * (1.0 - state.mixAmount) + static_cast<double>(result[2]) * state.mixAmount));  // F47",
        "  output = glsl::Vec4(mixed[0], mixed[1], mixed[2], color4[3]);  // F48; F49 writeColor f32 return",
        "}",
        "}  // namespace " + namespace,
        "",
        f"BoundKernel {factory}(const glsl::Bindings& bindings) {{",
        '  const auto& inputTex = bindings.texture("inputTex");',
        '  const auto tileOffset = bindings.get<glsl::Vec2>("tileOffset");',
        '  const auto fullResolution = bindings.get<glsl::Vec2>("fullResolution");',
        '  const auto ditherType = bindings.get<std::int32_t>("ditherType");',
        '  const auto threshold = bindings.get_number("threshold");',
        '  const auto matrixScale = bindings.get_number("matrixScale");',
        '  const auto renderScale = bindings.get_number("renderScale");',
        '  const auto palette = bindings.get<std::int32_t>("palette");',
        '  const auto levels = bindings.get<std::int32_t>("levels");',
        '  const auto time = bindings.get_number("time");',
        '  const auto mixAmount = bindings.get_number("mixAmount");',
        f"  const auto state = std::make_shared<{namespace}::State>(inputTex, tileOffset, fullResolution, ditherType, threshold, matrixScale, renderScale, palette, levels, time, mixAmount);",
        "  (void)bindings;",
        f"  return BoundKernel(state, &{namespace}::pixel);",
        "}",
    ])
    body = "\n".join(lines) + "\n"
    try:
        _finalize_dither_emission(proof, program, body)
    except ValueError as error:
        raise _error(program, program, str(error)) from error
    return body


def render_typed_cpp(program: TypedProgram, program_key: str, source_hash: str,
                     namespace: str = "typed_kernel", factory: str = "bind_typed",
                     *, numeric_literal_contract: str = "glsl-f32",
                     compatibility_transform: str | None = None,
                     custom_comparer_profile: str | None = None,
                     source_global_literal_int_profile: str | None = None,
                     runtime_loop_bound_profile: str | None = None,
                     gabor_effective_depth_profile: str | None = None,
                     gather_sorted_round_profile: str | None = None,
                     literal_vec3_lane_index_profile: str | None = None,
                     smooth_edge_luma_weights_profile: str | None = None,
                     perlin_scalar_uint_xor_profile: str | None = None,
                     scalar_uint_xor_profile: str | None = None,
                     bitwise_scalar_int_ops_profile: str | None = None,
                     bit_effects_frontend_profile: str | None = None,
                     rotate_mat2_return_profile: str | None = None,
                     focus_blur_borrowed_sampler_profile: str | None = None,
                     extrude_bvec2_relational_reduction_profile: str | None = None,
                     edge_bvec3_contour_profile: str | None = None,
                     glitch_mat4_chain_profile: str | None = None,
                     emboss_color_style_profile: str | None = None,
                     shape_mixer_builtin_profile: str | None = None,
                     caustic_word_hash_profile: str | None = None,
                     scanline_error_float_bits_ingress_profile: str | None = None,
                     glyph_map_nonnegative_int_shift_profile: str | None = None,
                     curl_vector_math_profile: str | None = None,
                     grade_luma_weights_profile: str | None = None,
                     grade_index_expression_profile: str | None = None,
                     derivative_admission_profile: str | None = None,
                     linear_srgb_lane_index_profile: str | None = None,
                     reflect_admission_profile: str | None = None,
                     posterize_round_profile: str | None = None,
                     as_u32_round_profile: str | None = None,
                     ceil_admission_profile: str | None = None,
                     waves_any_notequal_profile: str | None = None,
                     inout_vec3_swap_profile: str | None = None,
                     out_inout_admission_profile: str | None = None,
                     log_admission_profile: str | None = None,
                     mandelbrot_sequential_dz_assignment_profile: str | None = None,
                     shapes_float_bits_ingress_profile: str | None = None,
                     grime_float_bits_ingress_profile: str | None = None,
                     shapes_rvalue_assign_profile: str | None = None,
                     mutable_global_frame_profile: str | None = None,
                     mutable_global_array_profile: str | None = None,
                     const_global_table_profile: str | None = None,
                     varying_profile: str | None = None,
                     texture_lod_admission_profile: str | None = None,
                     texture_frontend_profile: str | None = None,
                     cross_lane_assignment_profile: str | None = None,
                     struct_declaration_profile: str | None = None,
                     testpattern_profile: str | None = None,
                     testpattern_frontend_proof: FrontendProof | None = None,
                     osd_frontend_profile: str | None = None,
                     moodscape_frontend_profile: str | None = None,
                     spooky_ticker_frontend_profile: str | None = None,
                     remap_profile: str | None = None,
                     remap_frontend_proof: RemapFrontendProof | None = None,
                     historic_palette_profile: str | None = None,
                     palette_frontend_profile: str | None = None,
                     color_lab_frontend_profile: str | None = None,
                     median_frontend_profile: str | None = None,
                     fractal_frontend_profile: str | None = None,
                     julia_frontend_profile: str | None = None,
                     distortion_frontend_profile: str | None = None,
                     noise_frontend_profile: str | None = None,
                     dither_frontend_profile: str | None = None
                     ) -> str:
    """Render one typed program; raw parser mappings are intentionally rejected."""
    if not isinstance(program, TypedProgram):
        raise _error(program_key, program, "typed program required; raw AST is forbidden")
    if program.key != program_key:
        raise _error(program, program, "program key mismatch")
    if program.key == DITHER_KEY:
        profile_values = locals().copy()
        foreign_profiles = tuple(
            name for name, value in profile_values.items()
            if name.endswith("_profile") and name != "dither_frontend_profile"
            and value is not None)
        if foreign_profiles or numeric_literal_contract != "glsl-f32" \
                or compatibility_transform is not None \
                or testpattern_frontend_proof is not None \
                or remap_frontend_proof is not None:
            raise _error(program, program, "Dither profile metadata mismatch")
        return (f"// Typed IR program: {program_key}\n"
                f"// Source SHA-256: {source_hash}\n" +
                _render_dither_typed_cpp(program, source_hash, namespace, factory,
                                         dither_frontend_profile))
    emitter = _Emitter(program, source_hash, numeric_literal_contract,
                       compatibility_transform,
                       custom_comparer_profile,
                       source_global_literal_int_profile,
                       runtime_loop_bound_profile,
                       gabor_effective_depth_profile,
                       gather_sorted_round_profile,
                       literal_vec3_lane_index_profile,
                       smooth_edge_luma_weights_profile,
                       perlin_scalar_uint_xor_profile,
                       scalar_uint_xor_profile,
                       bitwise_scalar_int_ops_profile,
                       bit_effects_frontend_profile,
                       rotate_mat2_return_profile,
                       focus_blur_borrowed_sampler_profile,
                       extrude_bvec2_relational_reduction_profile,
                       edge_bvec3_contour_profile,
                       glitch_mat4_chain_profile,
                       emboss_color_style_profile,
                       shape_mixer_builtin_profile,
                       caustic_word_hash_profile,
                       scanline_error_float_bits_ingress_profile,
                       glyph_map_nonnegative_int_shift_profile,
                       curl_vector_math_profile,
                       grade_luma_weights_profile,
                       grade_index_expression_profile,
                       derivative_admission_profile,
                       linear_srgb_lane_index_profile,
                       reflect_admission_profile,
                       posterize_round_profile,
                       as_u32_round_profile,
                       ceil_admission_profile,
                       waves_any_notequal_profile,
                       inout_vec3_swap_profile,
                       out_inout_admission_profile,
                       log_admission_profile,
                       mandelbrot_sequential_dz_assignment_profile,
                       struct_declaration_profile,
                       remap_profile,
                       remap_frontend_proof,
                       shapes_float_bits_ingress_profile,
                       grime_float_bits_ingress_profile,
                       shapes_rvalue_assign_profile,
                       mutable_global_frame_profile,
                       mutable_global_array_profile,
                       const_global_table_profile,
                       varying_profile,
                       texture_lod_admission_profile,
                       texture_frontend_profile,
                       cross_lane_assignment_profile,
                       testpattern_profile,
                       testpattern_frontend_proof,
                       osd_frontend_profile,
                       moodscape_frontend_profile,
                       noise_frontend_profile,
                       spooky_ticker_frontend_profile,
                       historic_palette_profile=historic_palette_profile,
                       palette_frontend_profile=palette_frontend_profile,
                       color_lab_frontend_profile=color_lab_frontend_profile,
                       median_frontend_profile=median_frontend_profile,
                       fractal_frontend_profile=fractal_frontend_profile,
                       julia_frontend_profile=julia_frontend_profile,
                       distortion_frontend_profile=distortion_frontend_profile)
    lines = [f"// Typed IR program: {program_key}", f"// Source SHA-256: {source_hash}"]
    lines.extend(emitter.render_body(namespace, factory))
    if emitter.program.key == JULIA_FRONTEND_KEY:
        return "\n".join(lines) + "\n"
    def walk_expression_nodes(value):
        yield value
        for child in value.children:
            yield from walk_expression_nodes(child)
    def walk_statement_nodes(value):
        for expression_value in value.expressions:
            yield from walk_expression_nodes(expression_value)
        for child in value.children:
            yield from walk_statement_nodes(child)
    all_expression_nodes = tuple(
        node for function in program.functions for statement in function.body
        for node in walk_statement_nodes(statement))
    if emitter.authorized_historic_palette_proof is not None:
        proof = emitter.authorized_historic_palette_proof
        expected_members = tuple(
            node for node in all_expression_nodes
            if node.kind == "member" and node.children
            and node.children[0].type.display() == "HistoricPalette")
        expected_constructors = (proof.palettes_initializer, *proof.palette_entries)
        expected_counts = (proof.palette_count_declaration,
                           proof.palette_count_initializer)
        if (not _same_object_sequence(emitter.emitted_historic_palette_structs,
                                       (proof.struct,))
                or not _same_object_sequence(
                    emitter.emitted_historic_palette_constructors,
                    expected_constructors)
                or not _same_object_sequence(
                    emitter.emitted_historic_palette_members, expected_members)
                or not _same_object_sequence(
                    emitter.emitted_historic_palette_indexes,
                    proof.palette_index_reads)
                or not _same_object_sequence(
                    emitter.emitted_historic_palette_counts, expected_counts)
                or not _same_object_sequence(
                    emitter.emitted_historic_palette_number_vectors,
                    proof.vec3_constructors)
                or not _same_object_sequence(
                    emitter.emitted_historic_palette_number_literals,
                    proof.palette_literals)
                or not _same_object_sequence(
                    emitter.emitted_historic_palette_adapter_sites,
                    (proof.sample_function, proof.luminance_site,
                     proof.t_initializer, proof.fract_site))
                or len(expected_members) != 7
                or len(proof.palette_entries) != 21
                or len(proof.vec3_constructors) != 105
                or len(proof.palette_literals) != 315
                or len(proof.palette_index_reads) != 1):
            raise _error(program, program,
                         "authenticated Historic Palette emission mismatch")
    if emitter.authorized_palette_frontend_proof is not None:
        proof = emitter.authorized_palette_frontend_proof
        expected_members = tuple(
            node for node in all_expression_nodes
            if node.kind == "member" and node.children
            and node.children[0].type.display() == "PaletteEntry")
        expected_constructors = (proof.palettes_initializer, *proof.palette_entries)
        expected_counts = (proof.palette_count_declaration,
                           proof.palette_count_initializer)
        if (not _same_object_sequence(emitter.emitted_palette_structs,
                                       (proof.struct,))
                or not _same_object_sequence(
                    emitter.emitted_palette_constructors, expected_constructors)
                or not _same_object_sequence(
                    emitter.emitted_palette_members, expected_members)
                or not _same_object_sequence(
                    emitter.emitted_palette_indexes, proof.palette_index_reads)
                or not _same_object_sequence(
                    emitter.emitted_palette_counts, expected_counts)
                or not _same_object_sequence(
                    emitter.emitted_palette_number_vectors,
                    proof.vec4_constructors)
                or not _same_object_sequence(
                    emitter.emitted_palette_number_literals,
                    proof.palette_literals)
                or not _same_object_sequence(
                    emitter.emitted_palette_tau_sites,
                    (proof.tau_declaration, proof.tau_initializer))
                or not _same_object_sequence(
                    emitter.emitted_palette_cosine_sites,
                    (*proof.cosine_vector_sites, proof.cosine_site,
                     proof.cosine_clamp_site))
                or not _same_object_sequence(
                    emitter.emitted_palette_adapter_sites,
                    (proof.hsv_function, proof.oklab_function,
                     proof.luminance_site, proof.t_initializer))
                or len(expected_members) != 5
                or len(proof.palette_entries) != 55
                or len(proof.vec4_constructors) != 220
                or len(proof.palette_literals) != 880
                or len(proof.palette_index_reads) != 1):
            raise _error(program, program,
                         "authenticated Palette emission mismatch")
    if emitter.authorized_color_lab_frontend_proof is not None:
        expected_indexes = emitter.authorized_color_lab_frontend_proof.index_nodes
        emitted_ids = {id(item) for item in emitter.emitted_color_lab_indexes}
        if (len(emitter.emitted_color_lab_indexes) != len(expected_indexes)
                or len(emitted_ids) != len(expected_indexes)
                or emitted_ids != {id(item) for item in expected_indexes}):
            raise _error(
                program, program,
                "authenticated ColorLab index emission mismatch")
        expected_equalities = (
            emitter.authorized_color_lab_frontend_proof.vector_equality_nodes)
        if not _same_object_sequence(
                emitter.emitted_color_lab_vector_equalities,
                expected_equalities):
            raise _error(
                program, program,
                "authenticated ColorLab vector-equality emission mismatch")
    if emitter.authorized_testpattern_proof is not None:
        proof = emitter.authorized_testpattern_proof
        global_array_declaration = next(
            item for item in program.declarations
            if item.symbol.id == proof.global_array.symbol_id)
        expected_arrays = (global_array_declaration, *(
            item for item in proof.consumed_objects
            if getattr(item, "kind", None) == "declaration"
            and getattr(item, "type", None) is not None
            and item.type.kind == "array"))
        expected_indexes = tuple(
            item.node for item in (*proof.dynamic_indexes,
                                   proof.digit_store_index))
        expected_rounds = (proof.round_node,)
        expected_bitwise = (
            emitter.authorized_testpattern_glyph_shift,
            emitter.authorized_testpattern_glyph_mask)
        same_identity_set = lambda actual, expected: (
            len(actual) == len(expected)
            and {id(item) for item in actual} == {id(item) for item in expected})
        if (not same_identity_set(emitter.emitted_testpattern_arrays,
                                      expected_arrays)
                or not same_identity_set(
                    emitter.emitted_testpattern_constructors,
                    tuple(item for item in proof.consumed_objects
                          if getattr(item, "kind", None) == "construct"
                          and getattr(item, "type", None) is not None
                          and item.type.kind == "array"))
                or not same_identity_set(
                    emitter.emitted_testpattern_indexes, expected_indexes)
                or not same_identity_set(
                    emitter.emitted_testpattern_rounds, expected_rounds)):
            raise _error(program, program,
                         "authenticated Test Pattern emission mismatch")
        if not same_identity_set(emitter.emitted_testpattern_bitwise,
                                      expected_bitwise):
            raise _error(program, program,
                         "authenticated Test Pattern bitwise emission mismatch")
    if emitter.authorized_remap_proof is not None:
        proof = emitter.authorized_remap_proof
        expected_indexes = tuple(item.node for item in proof.indexes)
        def find_loop(statements, loop_proof):
            for statement in statements:
                if statement.loop_proof is loop_proof:
                    return statement
                nested = find_loop(statement.children, loop_proof)
                if nested is not None:
                    return nested
            return None
        expected_loops = tuple(
            next(find_loop(function.body, item.proof)
                 for function in program.functions
                 if find_loop(function.body, item.proof) is not None)
            for item in proof.loops)
        if (not _same_object_sequence(emitter.emitted_remap_indexes,
                                      expected_indexes)
                or len(emitter.emitted_remap_loops) != len(expected_loops)
                or {id(item) for item in emitter.emitted_remap_loops}
                != {id(item) for item in expected_loops}):
            raise _error(program, program,
                         "authenticated Remap emission mismatch")
    if emitter.authorized_struct_declaration:
        expected_constructors = emitter.authorized_struct_declaration[1]
        expected_members = emitter.authorized_struct_declaration[2]
        if (emitter.emitted_newton_struct_count != 1
                or tuple(emitter.emitted_newton_struct_constructors)
                != expected_constructors
                or tuple(emitter.emitted_newton_members) != expected_members
                or len(emitter.emitted_newton_root_indexes)
                != len(emitter.authorized_newton_root_indexes)
                or any(not any(left is right
                               for right in emitter.emitted_newton_root_indexes)
                       for left in emitter.authorized_newton_root_indexes)
                or len(emitter.emitted_newton_logs)
                != len(emitter.authorized_newton_logs)
                or any(not any(left is right
                               for right in emitter.emitted_newton_logs)
                       for left in emitter.authorized_newton_logs)):
            raise _error(program, program,
                         "authenticated Newton emission mismatch")
    if emitter.authorized_mandelbrot_logs:
        if (tuple(emitter.emitted_mandelbrot_logs)
                != emitter.authorized_mandelbrot_logs):
            raise _error(program, program,
                         "authenticated Mandelbrot log emission mismatch")
    if emitter.authorized_mandelbrot_sequential_dz_assignment is not None:
        expected = emitter.authorized_mandelbrot_sequential_dz_assignment.assignment
        if emitter.emitted_mandelbrot_sequential_dz_assignment != [expected]:
            raise _error(
                program, program,
                "authenticated Mandelbrot sequential dz emission mismatch")
    if ((emitter.runtime_loop_contract is not None)
            != emitter.runtime_guard_emitted):
        raise _error(program, program,
                     "runtime-loop-bound guard consumption mismatch")
    if (emitter.runtime_loop_contract is not None
            and emitter.runtime_loop_contract.kind == "blur-radius"
            and not emitter.runtime_radius_declaration_emitted):
        raise _error(program, program,
                     "runtime-loop-bound radius consumption mismatch")
    if (emitter.authorized_perlin_scalar_uint_xors
            and tuple(emitter.emitted_perlin_scalar_uint_xors)
            != emitter.authorized_perlin_scalar_uint_xors):
        raise _error(program, program,
                     "authenticated scalar uint XOR emission mismatch")
    if (emitter.authorized_scalar_uint_xors
            and tuple(emitter.emitted_scalar_uint_xors)
            != emitter.authorized_scalar_uint_xors):
        raise _error(program, program,
                     "authenticated scalar uint XOR emission mismatch")
    if (emitter.authorized_scalar_uint_narrowing_skip_nodes
            and tuple(emitter.emitted_grain_narrowing_skip_nodes)
            != emitter.authorized_scalar_uint_narrowing_skip_nodes):
        raise _error(program, program,
                     "authenticated Grain narrowing-skip emission mismatch")
    if (emitter.authorized_bitwise_scalar_int_ops_sites
            and tuple(emitter.emitted_bitwise_scalar_int_ops_sites)
            != emitter.authorized_bitwise_scalar_int_ops_sites):
        raise _error(program, program,
                     "authenticated scalar int bitwise-op emission mismatch")
    if emitter.authorized_bit_effects_proof is not None:
        proof = emitter.authorized_bit_effects_proof
        expected = proof.consumed_objects
        emitted_ids = [id(item) for item in emitter.emitted_bit_effects_nodes]
        category_order = (
            proof.scalar_int_bitwise_nodes,
            proof.float_bits_to_uint_nodes,
            proof.vector_uint_bitwise_nodes,
            proof.scalar_uint_xor_nodes)
        if (len(emitted_ids) != len(expected)
                or len(set(emitted_ids)) != len(expected)
                or set(emitted_ids) != {id(item) for item in expected}
                or any(tuple(item for item in emitter.emitted_bit_effects_nodes
                            if any(item is candidate for candidate in category))
                       != category for category in category_order)
                or tuple(emitter.emitted_bit_effects_globals)
                != proof.global_const_declarations
                or tuple(emitter.emitted_bit_effects_overload_misdispatch)
                != (proof.canonical_overload_misdispatch_call,)
                or tuple(emitter.emitted_bit_effects_xi_to_int32)
                != (proof.canonical_xi_to_int32_node,)):
            raise _error(program, program,
                         "authenticated BitEffects emission mismatch")
    if emitter.authorized_osd_proof is not None:
        proof = emitter.authorized_osd_proof
        expected_nodes = proof.bitwise_nodes
        expected_array = proof.consumed_objects[0]
        if (len(emitter.emitted_osd_bitwise) != len(expected_nodes)
                or {id(item) for item in emitter.emitted_osd_bitwise}
                != {id(item) for item in expected_nodes}
                or len({id(item) for item in emitter.emitted_osd_bitwise})
                != len(expected_nodes)
                or len(emitter.emitted_osd_array) != 1
                or emitter.emitted_osd_array[0] is not expected_array
                or len(emitter.emitted_osd_indexes) != 1
                or emitter.emitted_osd_indexes[0] is not proof.consumed_objects[2]
                or tuple(emitter.emitted_osd_hash_modulos)
                != proof.hash_modulo_nodes):
            raise _error(program, program,
                         "authenticated OSD emission mismatch")
    if emitter.authorized_spooky_ticker_proof is not None:
        proof = emitter.authorized_spooky_ticker_proof
        expected_global = next(
            item for item in program.declarations
            if item.symbol.id == proof.global_array.symbol_id)
        if (tuple(emitter.emitted_spooky_ticker_bitwise)
                != proof.bitwise_nodes
                or tuple(emitter.emitted_spooky_ticker_indexes)
                != (proof.array_index,)
                or tuple(emitter.emitted_spooky_ticker_globals)
                != (expected_global,)
                or tuple(emitter.emitted_spooky_ticker_array)
                != (expected_global,)
                or tuple(emitter.emitted_spooky_ticker_varying_reads)
                != tuple(item.node for item in proof.varying_reads)
                or tuple(emitter.emitted_spooky_ticker_number_parameters)
                != (*proof.number_parameters, *proof.number_parameters)
                or tuple(emitter.emitted_spooky_ticker_number_declarations)
                != proof.number_declarations
                or tuple(emitter.emitted_spooky_ticker_number_divisions)
                != proof.number_divisions
                or tuple(emitter.emitted_spooky_ticker_number_umuls)
                != proof.number_umul_nodes
                or tuple(emitter.emitted_spooky_ticker_number_remainders)
                != proof.number_remainder_nodes
                or emitter.emitted_spooky_ticker_hash_declarations != 1
                or emitter.emitted_spooky_ticker_hash_definitions != 1):
            raise _error(program, program,
                         "authenticated SpookyTicker emission mismatch")
    if (emitter.authorized_bitwise_narrowing_skip_nodes
            and tuple(emitter.emitted_bitwise_narrowing_skip_nodes)
            != emitter.authorized_bitwise_narrowing_skip_nodes):
        raise _error(program, program,
                     "authenticated bitwise narrowing-skip emission mismatch")
    if (emitter.authorized_bitwise_float_identity_nodes
            and tuple(emitter.emitted_bitwise_float_identity_nodes)
            != emitter.authorized_bitwise_float_identity_nodes):
        raise _error(program, program,
                     "authenticated Bitwise float-identity emission mismatch")
    if emitter.authorized_bitwise_number_proof is not None:
        proof = emitter.authorized_bitwise_number_proof
        expression_objects = tuple(
            item for item in proof.consumed_objects
            if isinstance(item, TypedExpression))
        if (len(emitter.emitted_bitwise_number_objects)
                != len(expression_objects)
                or emitter.emitted_bitwise_number_parameter_sites
                != [proof.number_symbols[0], proof.number_symbols[1],
                    proof.number_symbols[0], proof.number_symbols[1]]):
            raise _error(program, program,
                         "authenticated Bitwise Number emission mismatch")
    if (emitter.authorized_rotate_helper is not None
            and (emitter.emitted_rotate_helper_count != 1
                 or tuple(emitter.emitted_rotate_expressions)
                 != (emitter.authorized_rotate_expressions[0],
                     emitter.authorized_rotate_expressions[2],
                     emitter.authorized_rotate_expressions[1]))):
        raise _error(program, program,
                     "authenticated Rotate matrix emission mismatch")
    if emitter.authorized_focus_blur_proof is not None:
        proof = emitter.authorized_focus_blur_proof
        if (emitter.emitted_focus_blur_parameter_sites
                != [proof.sampler_parameters[0], proof.sampler_parameters[1],
                    proof.sampler_parameters[0], proof.sampler_parameters[1]]
                or tuple(emitter.emitted_focus_blur_uses) != proof.sampler_uses
                or tuple(emitter.emitted_focus_blur_calls) != proof.calls):
            raise _error(program, program,
                         "authenticated Focus Blur emission mismatch")
    if emitter.authorized_curl_proof is not None:
        expected = emitter.authorized_curl_proof.nodes
        emitted = emitter.emitted_curl_nodes
        if len(emitted) != len(expected) or any(
                not any(value is item for item in emitted) for value in expected):
            raise _error(program, program, "authenticated Curl emission mismatch")
    if emitter.authorized_caustic_proof is not None:
        proof = emitter.authorized_caustic_proof
        expected = [proof.ingress, *proof.word_xors]
        emitted = emitter.emitted_caustic_nodes
        if len(emitted) != len(expected) or any(
                not any(value is item for item in emitted) for value in expected):
            raise _error(program, program, "authenticated Caustic emission mismatch")
    if emitter.authorized_scanline_error_proof is not None:
        expected = emitter.authorized_scanline_error_proof.ingresses
        emitted = emitter.emitted_scanline_error_ingresses
        if (len(emitted) != len(expected)
                or any(left is not right
                       for left, right in zip(emitted, expected))):
            raise _error(
                program, program,
                "authenticated Scanline Error emission mismatch")
    if emitter.authorized_shapes_float_bits_ingresses:
        expected = emitter.authorized_shapes_float_bits_ingresses
        emitted = emitter.emitted_shapes_float_bits_ingresses
        if (len(emitted) != len(expected)
                or any(left is not right
                       for left, right in zip(emitted, expected))):
            raise _error(
                program, program,
                "authenticated Shapes float-bit ingress emission mismatch")
    if emitter.authorized_grime_float_bits_ingresses:
        expected = emitter.authorized_grime_float_bits_ingresses
        emitted = emitter.emitted_grime_float_bits_ingresses
        if (len(emitted) != len(expected)
                or any(left is not right
                       for left, right in zip(emitted, expected))):
            raise _error(
                program, program,
                "authenticated grime float-bit ingress emission mismatch")
    if emitter.authorized_kaleido_float_bits_ingress:
        expected = emitter.authorized_kaleido_float_bits_ingress
        emitted = emitter.emitted_kaleido_float_bits_ingress
        if (len(emitted) != len(expected)
                or any(left is not right
                       for left, right in zip(emitted, expected))):
            raise _error(
                program, program,
                "authenticated kaleido float-bit ingress emission mismatch")
    if emitter.authorized_noise_float_bits_ingresses:
        expected = emitter.authorized_noise_float_bits_ingresses
        emitted = emitter.emitted_noise_float_bits_ingresses
        if (len(emitted) != len(expected)
                or any(left is not right
                       for left, right in zip(emitted, expected))):
            raise _error(
                program, program,
                "authenticated Noise float-bit ingress emission mismatch")
    if emitter.authorized_cross_lane_assignment is not None:
        if emitter.emitted_cross_lane_assignments != [
                emitter.authorized_cross_lane_assignment.assignment]:
            raise _error(program, program,
                         "authenticated cross-lane assignment emission mismatch")
    if emitter.authorized_shapes_rvalue_assigns:
        expected = emitter.authorized_shapes_rvalue_assigns
        emitted = emitter.emitted_shapes_rvalue_assigns
        if (len(emitted) != len(expected)
                or any(left is not right
                       for left, right in zip(emitted, expected))):
            raise _error(
                program, program,
                "authenticated Shapes rvalue-assign emission mismatch")
    if getattr(emitter, "authorized_mutable_global_frames", ()):
        contract = emitter.authorized_frame_contract
        # Exactly one struct and exactly one `pixel`-scope instance, and every
        # admitted symbol actually referenced by the emitted body. A carrier
        # whose struct or instance silently stops being emitted, or whose
        # symbol map quietly loses a field, fails here rather than producing
        # C++ that no longer matches the authenticated contract.
        if (contract is None or emitter.emitted_frame_struct_count != 1
                or emitter.emitted_frame_instance_count != 1):
            raise _error(program, program,
                         "authenticated mutable-global frame emission mismatch")
        referenced = {item.symbol_id for item in emitter.emitted_frame_references}
        if (referenced != {declaration.symbol.id
                           for declaration in
                           emitter.authorized_mutable_global_frames}
                or any(item.symbol_id not in emitter.frame_fields
                       for item in emitter.emitted_frame_references)):
            raise _error(
                program, program,
                "authenticated mutable-global frame reference mismatch")
    if getattr(emitter, "authorized_mutable_global_arrays", ()):
        contract = emitter.authorized_mutable_array_contract
        # Design S4.6: exactly one Frame type, one `pixel`-scope instance,
        # exactly one non-const frame parameter (on the writer alone), the
        # writer called exactly once (from `pixel`, the lowered `main`), and
        # every admitted symbol referenced -- here: written -- with the full
        # 45-store census consumed.
        if (contract is None
                or emitter.emitted_array_frame_struct_count != 1
                or emitter.emitted_array_frame_instance_count != 1):
            raise _error(program, program,
                         "authenticated mutable-global array frame emission "
                         "mismatch")
        if ({item.name for item in emitter.emitted_array_nonconst_frame_functions}
                != {contract.writer_function}):
            raise _error(program, program,
                         "authenticated mutable-global array writer parameter "
                         "mismatch")
        if (len(emitter.emitted_array_writer_calls) != 1
                or emitter.emitted_array_writer_calls[0]
                is not emitter.authorized_array_writer_call):
            raise _error(program, program,
                         "authenticated mutable-global array writer call "
                         "mismatch")
        if (tuple(emitter.emitted_array_rvalue_assigns)
                != emitter.authorized_array_rvalue_assigns):
            raise _error(program, program,
                         "authenticated mutable-global array rvalue "
                         "assignment emission mismatch")
        referenced = {item.symbol_id
                      for item in emitter.emitted_array_frame_references}
        # The store census is the record's own (45 for the five-array keys,
        # 63 for effects' seven -- per key since the effects row).
        if (referenced != {declaration.symbol.id
                           for declaration in
                           emitter.authorized_mutable_global_arrays}
                or any(item.symbol_id not in emitter.array_frame_fields
                       for item in emitter.emitted_array_frame_references)
                or len(emitter.emitted_array_frame_stores)
                != mutable_global_array_store_census(program.key)):
            raise _error(
                program, program,
                "authenticated mutable-global array frame reference mismatch")
    if emitter.authorized_const_global_tables:
        contract = emitter.authorized_const_global_table_contract
        # One alias block, one `const` local per table, one brace-init
        # constructor per table, and exactly one counted read per table in the
        # frozen declaration order. A table whose alias, local, initializer or
        # read silently stops being emitted fails here rather than producing
        # C++ that no longer matches the authenticated contract.
        expected_reads = tuple(
            item.node for item in emitter.authorized_const_global_table_reads)
        if (emitter.emitted_const_global_table_alias_blocks != 1
                or not _same_object_sequence(
                    emitter.emitted_const_global_table_locals,
                    emitter.authorized_const_global_tables)
                or not _same_object_sequence(
                    emitter.emitted_const_global_table_constructors,
                    tuple(item.initializer
                          for item in emitter.authorized_const_global_tables))
                or not _same_object_sequence(
                    emitter.emitted_const_global_table_reads, expected_reads)
                or len(expected_reads) != len(contract)):
            raise _error(program, program,
                         "authenticated const-global nine-table emission mismatch")
    if getattr(emitter, "authorized_varyings", ()):
        contract = emitter.authorized_varying_contract
        # Every admitted varying symbol actually referenced by the emitted
        # body (and nothing else reaching the lowering), with the contract
        # present. A carrier whose lowering arm silently stops firing -- or
        # admits a symbol it did not authenticate -- fails here rather than
        # producing C++ that no longer matches the authenticated contract.
        referenced = {item.symbol_id
                      for item in emitter.emitted_varying_references}
        if (contract is None
                or referenced != {symbol.id
                                  for symbol in emitter.authorized_varyings}
                or any(item.symbol_id not in emitter.varying_fields
                       for item in emitter.emitted_varying_references)):
            raise _error(program, program,
                         "authenticated varying-uv emission mismatch")
    if emitter.authorized_texture_lod_sites:
        # Every authenticated call site must have been emitted exactly once,
        # in the frozen site order, and nothing else may have reached the
        # alias lowering -- the emission-side restatement of the closure's
        # two-site census.
        if (tuple(emitter.emitted_texture_lod_sites)
                != emitter.authorized_texture_lod_sites):
            raise _error(program, program,
                         "authenticated textureLod admission emission mismatch")
    if emitter.authorized_texture_frontend_nodes:
        if (tuple(emitter.emitted_texture_frontend_nodes)
                != emitter.authorized_texture_frontend_nodes):
            raise _error(program, program,
                         "authenticated Texture XOR emission mismatch")
    if emitter.authorized_texture_frontend_assignments:
        if (tuple(emitter.emitted_texture_frontend_assignments)
                != emitter.authorized_texture_frontend_assignments):
            raise _error(program, program,
                         "authenticated Texture bitwise assignment emission mismatch")
    if emitter.authorized_texture_frontend_inverse_sqrt is not None:
        if emitter.emitted_texture_frontend_inverse_sqrt != [
                emitter.authorized_texture_frontend_inverse_sqrt]:
            raise _error(program, program,
                         "authenticated Texture inversesqrt emission mismatch")
    if emitter.authorized_texture_frontend_hash_conversion is not None:
        if emitter.emitted_texture_frontend_hash_conversion != [
                emitter.authorized_texture_frontend_hash_conversion]:
            raise _error(
                program, program,
                "authenticated Texture hash conversion emission mismatch")
    if emitter.authorized_glyph_map_proof is not None:
        proof = emitter.authorized_glyph_map_proof
        if (len(emitter.emitted_glyph_map_sites) != 2
                or emitter.emitted_glyph_map_sites != [proof.mask, proof.shift]
                or emitter.emitted_glyph_map_noops != [proof.self_assignment]):
            raise _error(program, program,
                         "authenticated Glyph Map emission mismatch")
    if emitter.authorized_extrude_proof is not None:
        proof = emitter.authorized_extrude_proof
        # Every authenticated node must have been emitted exactly once, and
        # nothing else may have reached the relational/reduction lowering.
        expected = [proof.relationals[0], proof.reductions[0],
                    proof.relationals[1], proof.reductions[1]]
        emitted = emitter.emitted_extrude_nodes
        if len(emitted) != len(expected) or any(
                left is not right for left, right in zip(emitted, expected)):
            raise _error(program, program,
                         "authenticated Extrude emission mismatch")
    if emitter.authorized_edge_proof is not None:
        proof = emitter.authorized_edge_proof
        if (tuple(emitter.emitted_edge_bvec_nodes) != proof.bvec_nodes
                or tuple(emitter.emitted_edge_relationals)
                != proof.relationals
                or tuple(emitter.emitted_edge_declarations)
                != proof.declarations
                or emitter.emitted_edge_constructors != [proof.constructor]
                or tuple(emitter.emitted_edge_swizzles) != proof.swizzles):
            raise _error(program, program,
                         "authenticated Edge emission mismatch")
    if emitter.authorized_edge_splat_proof is not None:
        proof = emitter.authorized_edge_splat_proof
        if emitter.emitted_edge_splat_assignments != [proof.assignment]:
            raise _error(program, program,
                         "authenticated Edge center-splat emission mismatch")
    if (emitter.authorized_glitch_proof is not None
            and tuple(emitter.emitted_glitch_matrix_objects)
            != emitter.authorized_glitch_proof.consumed_objects):
        raise _error(program, program,
                     "authenticated Glitch matrix emission mismatch")
    emboss = getattr(emitter, "authorized_emboss_proof", None)
    if emboss is not None:
        proof = emboss
        expected_declarations = tuple(table.declaration for table in proof.tables)
        expected_stores = tuple(store for table in proof.tables
                                for store in table.literal_stores)
        expected_reads = (
            proof.tables[1].dynamic_read, proof.tables[0].dynamic_read,
            proof.tables[3].dynamic_read, proof.tables[2].dynamic_read,
        )
        if (not _same_object_sequence(
                    emitter.emitted_emboss_declarations,
                    expected_declarations)
                or not _same_object_sequence(
                    emitter.emitted_emboss_stores, expected_stores)
                or not _same_object_sequence(
                    emitter.emitted_emboss_reads, expected_reads)
                or not _same_object_sequence(
                    emitter.emitted_emboss_equalities, proof.equalities)
                or not _same_object_sequence(
                    emitter.emitted_emboss_reductions, proof.reductions)
                or not _same_object_sequence(
                    emitter.emitted_emboss_materialization_divisions,
                    proof.texture_coordinate_divisions)):
            raise _error(program, program,
                         "authenticated Emboss emission mismatch")
    if emitter.authorized_grade_index_sites and (
            len(emitter.emitted_grade_index_sites)
            != len(emitter.authorized_grade_index_sites)
            or any(not any(value is item for item in emitter.emitted_grade_index_sites)
                   for value in emitter.authorized_grade_index_sites)):
        raise _error(program, program,
                     "authenticated Grade index expression emission mismatch")
    if emitter.authorized_linear_srgb_lane_index_sites and (
            len(emitter.emitted_linear_srgb_lane_index_sites)
            != len(emitter.authorized_linear_srgb_lane_index_sites)
            or any(not any(value is item
                          for item in emitter.emitted_linear_srgb_lane_index_sites)
                   for value in emitter.authorized_linear_srgb_lane_index_sites)):
        raise _error(program, program,
                     "authenticated Linear sRGB lane index emission mismatch")
    if emitter.authorized_fractal_frontend_indexes and (
            len(emitter.emitted_fractal_frontend_indexes)
            != len(emitter.authorized_fractal_frontend_indexes)
            or any(not any(value is item
                           for value in emitter.emitted_fractal_frontend_indexes)
                   for item in emitter.authorized_fractal_frontend_indexes)):
        raise _error(program, program,
                     "authenticated Fractal lane index emission mismatch")
    if emitter.authorized_fractal_alpha_product is not None and (
            len(emitter.emitted_fractal_alpha_products) != 1
            or emitter.emitted_fractal_alpha_products[0]
            is not emitter.authorized_fractal_alpha_product
            or len(emitter.emitted_fractal_alpha_literals) != 1
            or emitter.emitted_fractal_alpha_literals[0]
            is not emitter.authorized_fractal_alpha_literal):
        raise _error(program, program,
                     "authenticated Fractal alpha emission mismatch")
    if emitter.authorized_fractal_hsv_function is not None and (
            emitter.emitted_fractal_hsv_declarations != 1
            or emitter.emitted_fractal_hsv_definitions != 1
            or not _same_object_sequence(
                emitter.emitted_fractal_hsv_calls,
                emitter.authorized_fractal_hsv_calls)
            or emitter.emitted_fractal_hue_scale_assignments != [
                emitter.authorized_fractal_hue_scale_assignment]
            or emitter.emitted_fractal_distance_fract_assignments != [
                emitter.authorized_fractal_distance_fract_assignment]
            or emitter.emitted_fractal_distance_map_assignments != [
                emitter.authorized_fractal_distance_map_assignment]
            or emitter.emitted_fractal_palette_adapter_paths != 1
            or emitter.emitted_fractal_palette_calls != [
                emitter.authorized_fractal_palette_call]
            or emitter.emitted_fractal_newton_declarations != 1
            or emitter.emitted_fractal_newton_definitions != 1
            or emitter.emitted_fractal_newton_adapter_paths != 1
            or emitter.emitted_fractal_newton_calls != [
                emitter.authorized_fractal_newton_call]
            or emitter.emitted_fractal_julia_declarations != 1
            or emitter.emitted_fractal_julia_definitions != 1
            or emitter.emitted_fractal_julia_adapter_paths != 1
            or emitter.emitted_fractal_julia_calls != [
                emitter.authorized_fractal_julia_call]
            or emitter.emitted_fractal_mandelbrot_declarations != 1
            or emitter.emitted_fractal_mandelbrot_definitions != 1
            or emitter.emitted_fractal_mandelbrot_adapter_paths != 1
            or emitter.emitted_fractal_mandelbrot_calls != [
                emitter.authorized_fractal_mandelbrot_call]
            or not _same_object_sequence(
                emitter.emitted_fractal_julia_number_anchors,
                emitter.authorized_fractal_julia_number_anchors)
            or not _same_object_sequence(
                emitter.emitted_fractal_mandelbrot_number_anchors,
                emitter.authorized_fractal_mandelbrot_number_anchors)
            or emitter.emitted_fractal_mandelbrot_matrix_consumptions != [
                emitter.authorized_fractal_mat2_constructor]):
        raise _error(
            program, program,
            "authenticated Fractal Number emission mismatch "
            f"(hsv-decl={emitter.emitted_fractal_hsv_declarations}, "
            f"hsv-def={emitter.emitted_fractal_hsv_definitions}, "
            f"hsv-calls={len(emitter.emitted_fractal_hsv_calls)}, "
            f"palette-paths={emitter.emitted_fractal_palette_adapter_paths}, "
            f"palette-calls={len(emitter.emitted_fractal_palette_calls)}, "
                f"newton-decl={emitter.emitted_fractal_newton_declarations}, "
                f"newton-def={emitter.emitted_fractal_newton_definitions}, "
                f"newton-paths={emitter.emitted_fractal_newton_adapter_paths}, "
                f"newton-calls={len(emitter.emitted_fractal_newton_calls)}, "
                f"julia-decl={emitter.emitted_fractal_julia_declarations}, "
                f"julia-def={emitter.emitted_fractal_julia_definitions}, "
                f"julia-paths={emitter.emitted_fractal_julia_adapter_paths}, "
                f"mandelbrot-decl={emitter.emitted_fractal_mandelbrot_declarations}, "
                f"mandelbrot-def={emitter.emitted_fractal_mandelbrot_definitions}, "
                f"mandelbrot-paths={emitter.emitted_fractal_mandelbrot_adapter_paths}, "
                f"julia-anchors={len(emitter.emitted_fractal_julia_number_anchors)}, "
                f"mandelbrot-anchors={len(emitter.emitted_fractal_mandelbrot_number_anchors)}, "
                f"mandelbrot-matrix={len(emitter.emitted_fractal_mandelbrot_matrix_consumptions)})")
    if emitter.authorized_reflect_node is not None and (
            len(emitter.emitted_reflect_nodes) != 1
            or emitter.emitted_reflect_nodes[0] is not emitter.authorized_reflect_node):
        raise _error(program, program,
                     "authenticated Reflect emission mismatch")
    if emitter.authorized_shape_mixer_proof is not None:
        expected_roots, expected_bodies = (
            _candidate_shape_mixer_roots_and_bodies(program))
        if (not _same_object_sequence(
                    emitter.emitted_shape_mixer_exceptional,
                    emitter.authorized_shape_mixer_proof.exceptional_nodes)
                or not _same_object_sequence(
                    emitter.emitted_shape_mixer_guards,
                    emitter.candidate_shape_mixer_guards)
                or not _same_object_sequence(
                    emitter.emitted_shape_mixer_guards,
                    emitter.authorized_shape_mixer_proof.blend_mode_guards)
                or not _same_object_sequence(
                    emitter.emitted_shape_mixer_roots, expected_roots)
                or len(emitter.emitted_shape_mixer_bodies) != 22
                or len({id(item)
                        for item in emitter.emitted_shape_mixer_bodies}) != 22
                or any(not any(value is item for item
                               in emitter.emitted_shape_mixer_bodies)
                       for value in expected_bodies)):
            raise _error(program, program,
                         "authenticated Shape Mixer emission mismatch")
    if emitter.authorized_derivative_proof is not None:
        expected = emitter.authorized_derivative_proof.nodes
        emitted = emitter.emitted_derivative_nodes
        if len(emitted) != len(expected) or any(
                not any(value is item for item in emitted) for value in expected):
            raise _error(program, program, "authenticated Derivative emission mismatch")
    if emitter.authorized_distortion_frontend_proof is not None:
        proof = emitter.authorized_distortion_frontend_proof
        expected_parameters = (*proof.sampler_parameter_nodes,
                              *proof.sampler_parameter_nodes)
        if (tuple(emitter.emitted_distortion_sampler_parameters)
                != expected_parameters
                or tuple(emitter.emitted_distortion_sampler_calls)
                != proof.sampler_calls
                or tuple(emitter.emitted_distortion_sampler_actuals)
                != proof.sampler_actual_nodes
                or tuple(emitter.emitted_distortion_derivatives)
                != proof.derivative_nodes
                or tuple(emitter.emitted_distortion_reflects)
                != (proof.reflect_node,)):
            raise _error(program, program,
                         "authenticated Distortion frontend emission mismatch")
    if emitter.authorized_waves_relationals or emitter.authorized_waves_reductions:
        expected = (*emitter.authorized_waves_reductions,
                   *emitter.authorized_waves_relationals)
        emitted = emitter.emitted_waves_nodes
        if len(emitted) != len(expected) or any(
                not any(value is item for item in emitted) for value in expected):
            raise _error(program, program, "authenticated Waves emission mismatch")
    if emitter.authorized_inout_vec3_swap_proof is not None:
        expected = emitter.authorized_inout_vec3_swap_proof.calls
        emitted = emitter.emitted_inout_vec3_swap_calls
        if len(emitted) != len(expected) or any(
                not any(value is item for item in emitted) for value in expected):
            raise _error(program, program,
                         "authenticated inout vec3 swap emission mismatch")
    if emitter.authorized_out_inout_parameters:
        expected = emitter.authorized_out_inout_parameters
        emitted = emitter.emitted_out_inout_parameters
        if (len(emitted) != len(expected)
                or any(not any(value is item for item in emitted)
                       for value in expected)):
            raise _error(program, program,
                         "authenticated out/inout parameter emission mismatch")
    if emitter.authorized_out_inout_calls:
        expected = emitter.authorized_out_inout_calls
        emitted = emitter.emitted_out_inout_calls
        if (len(emitted) != len(expected)
                or any(not any(value is item for item in emitted)
                       for value in expected)):
            raise _error(program, program,
                         "authenticated out/inout call emission mismatch")
    if program.key == GATHER_SORTED_KEY and gather_sorted_round_profile is None:
        raise _error(program, program,
                     "exact Gather Sorted round profile carrier required")
    if program.key == POSTERIZE_KEY and posterize_round_profile is None:
        raise _error(program, program,
                     "exact Posterize round admission profile carrier required")
    if program.key in AS_U32_ROUND_KEYS and as_u32_round_profile is None:
        raise _error(program, program,
                     "exact as_u32 round admission profile carrier required")
    if (program.key in SCALAR_UINT_XOR_KEYS
            and program.key not in BIT_EFFECTS_PREPARED_KEYS
            and scalar_uint_xor_profile is None):
        raise _error(program, program,
                     "exact scalar uint XOR profile carrier required")
    if (program.key in CONST_GLOBAL_TABLE_KEYS
            and const_global_table_profile is None):
        raise _error(program, program,
                     "exact const-global nine-table profile carrier required")
    if program.key == SHAPE_MIXER_KEY and shape_mixer_builtin_profile is None:
        raise _error(program, program,
                     "exact Shape Mixer builtin profile carrier required")
    if program.key == WAVES_KEY and waves_any_notequal_profile is None:
        raise _error(program, program,
                     "exact Waves any/notEqual admission profile carrier required")
    if program.key == INOUT_VEC3_SWAP_KEY and inout_vec3_swap_profile is None:
        raise _error(program, program,
                     "exact Inout vec3 swap admission profile carrier required")
    if program.key in OUT_INOUT_ADMISSION_KEYS and out_inout_admission_profile is None:
        raise _error(program, program,
                     "exact out/inout admission profile carrier required")
    return "\n".join(lines) + "\n"
