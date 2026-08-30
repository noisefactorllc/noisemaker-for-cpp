"""Generate the small, schema-locked C++ typed-IR slice from pinned corpus data."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import pathlib
import re
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
    from tools.glslcpp.frontend.historic_palette_profile import (
        PROFILE as HISTORIC_PALETTE_PROFILE,
        apply_historic_palette,
        authenticate_historic_palette)
    from tools.glslcpp.frontend.palette_frontend_profile import (
        PROFILE as PALETTE_FRONTEND_PROFILE,
        apply_palette_frontend,
        authenticate_palette_frontend)
    from tools.glslcpp.frontend.color_lab_frontend_profile import (
        KEY as COLOR_LAB_KEY,
        PROFILE as COLOR_LAB_FRONTEND_PROFILE,
        apply_color_lab_frontend,
        authenticate_color_lab_frontend,
        allowed_row_fields as color_lab_allowed_row_fields)
    from tools.glslcpp.frontend.fractal_frontend_profile import (
        KEY as FRACTAL_KEY,
        PROFILE as FRACTAL_FRONTEND_PROFILE,
        PREPARED_KEYS as FRACTAL_PREPARED_KEYS,
        PREPARED_PROFILES as FRACTAL_PREPARED_PROFILES,
        apply_fractal_frontend,
        authenticate_fractal_frontend,
        authenticate_fractal_metadata)
    from tools.glslcpp.frontend.julia_frontend_profile import (
        KEY as JULIA_KEY, PROFILE as JULIA_FRONTEND_PROFILE,
        KEYS as JULIA_FRONTEND_KEYS, PROFILES as JULIA_FRONTEND_PROFILES,
        ALLOWED_ROW_FIELDS as JULIA_FRONTEND_ALLOWED_ROW_FIELDS,
        apply_julia_frontend, authenticate_julia_frontend)
    from tools.glslcpp.frontend.semantic_types import BOOL, FLOAT
    from tools.glslcpp.frontend.typed_ir import TypedExpression, TypedStatement
    from tools.glslcpp.frontend.loop_proof import (
        COUNTED_FOR_V1_MAX_ENTRYPOINT_CHARGE, COUNTED_FOR_V1_MAX_LEXICAL_PRODUCT,
        COUNTED_FOR_V1_MAX_TRIP_COUNT,
        SOURCE_GLOBAL_LITERAL_INT_CAPABILITY, SOURCE_GLOBAL_LITERAL_INT_KEYS,
        attach_counted_loop_proofs, clear_counted_loop_proofs,
        rebuild_authenticated_counted_loop_proofs,
        summarize_counted_loop_proofs)
    from tools.glslcpp.frontend.local_counter_proof import (
        CAPABILITY as LOCAL_COUNTER_CAPABILITY,
        COMPUTE_RANK_KEY, COMPUTE_RANK_NORMALIZED_SHA256, COMPUTE_RANK_RAW_SHA256,
        attach_discarded_local_counter_proofs)
    from tools.glslcpp.frontend.fixed_nine_table_proof import (
        CAPABILITY as FIXED_NINE_CAPABILITY, SOURCE_LOCKS,
        prove_fixed_nine_local_tables, source_provenance_error)
    from tools.glslcpp.frontend.distortion_frontend_profile import (
        KEY as DISTORTION_FRONTEND_KEY,
        PROFILE as DISTORTION_FRONTEND_PROFILE,
        DISTORTION_FRONTEND_KEYS,
        authenticate_distortion_frontend)
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
        CELLREFRACT_KEY as TASK19_CELLREFRACT_KEY,
        EFFECTS_KEY as TASK19_EFFECTS_KEY,
        KALEIDO_KEY as TASK19_KALEIDO_KEY,
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
    from tools.glslcpp.frontend.linear_srgb_lane_index_profile import (
        KEYS as LINEAR_SRGB_LANE_INDEX_KEYS,
        PROFILES as LINEAR_SRGB_LANE_INDEX_PROFILES,
        apply_linear_srgb_lane_index, authenticate_linear_srgb_lane_index)
    from tools.glslcpp.frontend.reflect_admission_profile import (
        LIGHTING_KEY as REFLECT_ADMISSION_KEY,
        PROFILE as REFLECT_ADMISSION_PROFILE,
        apply_reflect_admission, authenticate_reflect_admission)
    from tools.glslcpp.frontend.perlin_scalar_uint_xor_profile import (
        PERLIN_KEY, PROFILE as PERLIN_SCALAR_UINT_XOR_PROFILE,
        apply_perlin_scalar_uint_xor,
        authenticate_perlin_scalar_uint_xor)
    from tools.glslcpp.frontend.scalar_uint_xor_profile import (
        KALEIDO_INGRESS_KEY as KALEIDO_FLOAT_BITS_INGRESS_KEY,
        NOISE_INGRESS_KEY as NOISE_FLOAT_BITS_INGRESS_KEY,
        PROFILE as SCALAR_UINT_XOR_PROFILE, SCALAR_UINT_XOR_KEYS,
        apply_scalar_uint_xor, authenticate_kaleido_float_bits_ingress,
        authenticate_noise_float_bits_ingress,
        authenticate_scalar_uint_xor)
    from tools.glslcpp.frontend.bitwise_scalar_int_ops_profile import (
        KEYS as BITWISE_SCALAR_INT_OPS_KEYS,
        PROFILES as BITWISE_SCALAR_INT_OPS_PROFILES,
        apply_bitwise_scalar_int_ops, authenticate_bitwise_scalar_int_ops,
        authenticate_bitwise_scalar_int_ops_transition)
    from tools.glslcpp.frontend.bit_effects_profile import (
        KEY as BIT_EFFECTS_KEY,
        PROFILE as BIT_EFFECTS_PROFILE,
        PREPARED_KEYS as BIT_EFFECTS_PREPARED_KEYS,
        PREPARED_PROFILES as BIT_EFFECTS_PREPARED_PROFILES,
        apply_bit_effects_frontend,
        authenticate_bit_effects_frontend)
    from tools.glslcpp.frontend.osd_frontend_profile import (
        KEY as OSD_KEY,
        PROFILE as OSD_FRONTEND_PROFILE,
        PREPARED_KEYS as OSD_PREPARED_KEYS,
        PREPARED_PROFILES as OSD_PREPARED_PROFILES,
        apply_osd_frontend,
        authenticate_osd_frontend)
    from tools.glslcpp.frontend.moodscape_frontend_profile import (
        KEY as MOODSCAPE_KEY,
        PROFILE as MOODSCAPE_FRONTEND_PROFILE,
        PREPARED_KEYS as MOODSCAPE_PREPARED_KEYS,
        PREPARED_PROFILES as MOODSCAPE_PREPARED_PROFILES,
        apply_moodscape_frontend,
        authenticate_moodscape_projection)
    from tools.glslcpp.frontend.noise_frontend_profile import (
        KEY as NOISE_FRONTEND_KEY,
        PROFILE as NOISE_FRONTEND_PROFILE,
        apply_noise_frontend,
        authenticate_noise_projection,
        authenticate_noise_runtime)
    from tools.glslcpp.frontend.spooky_ticker_frontend_profile import (
        KEY as SPOOKY_TICKER_KEY,
        PROFILE as SPOOKY_TICKER_FRONTEND_PROFILE,
        PREPARED_KEYS as SPOOKY_TICKER_PREPARED_KEYS,
        PREPARED_PROFILES as SPOOKY_TICKER_PREPARED_PROFILES,
        authenticate_spooky_ticker_frontend)
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
    from tools.glslcpp.frontend.edge_bvec3_contour_profile import (
        EDGE_KEY, PROFILE as EDGE_BVEC3_CONTOUR_PROFILE,
        apply_edge_bvec3_contour, authenticate_edge_bvec3_contour,
        authenticate_edge_center_splat)
    from tools.glslcpp.frontend.glitch_mat4_chain_profile import (
        EFFECTS_KEY as GLITCH_MAT4_CHAIN_EFFECTS_KEY,
        EFFECTS_PROFILE as EFFECTS_MAT4_CHAIN_PROFILE,
        GLITCH_KEY, PROFILE as GLITCH_MAT4_CHAIN_PROFILE,
        REQUIRED_COMPANION_PROFILES as GLITCH_MAT4_CHAIN_COMPANIONS,
        apply_glitch_mat4_chain, authenticate_glitch_mat4_chain)
    GLITCH_MAT4_CHAIN_KEYS = frozenset(
        {GLITCH_KEY, GLITCH_MAT4_CHAIN_EFFECTS_KEY})
    GLITCH_MAT4_CHAIN_PROFILES = {
        GLITCH_KEY: GLITCH_MAT4_CHAIN_PROFILE,
        GLITCH_MAT4_CHAIN_EFFECTS_KEY: EFFECTS_MAT4_CHAIN_PROFILE}
    from tools.glslcpp.frontend.emboss_color_style_profile import (
        EMBOSS_KEY, PROFILE as EMBOSS_COLOR_STYLE_PROFILE,
        apply_emboss_color_style, authenticate_emboss_color_style)
    from tools.glslcpp.frontend.shape_mixer_builtin_profile import (
        PROFILE as SHAPE_MIXER_BUILTIN_PROFILE, SHAPE_MIXER_KEY,
        apply_shape_mixer_builtin_closure,
        authenticate_shape_mixer_builtin_closure)
    from tools.glslcpp.frontend.caustic_word_hash_profile import (
        CAUSTIC_KEY, PROFILE as CAUSTIC_WORD_HASH_PROFILE,
        apply_caustic_word_hash, authenticate_caustic_word_hash)
    from tools.glslcpp.frontend.scanline_error_float_bits_ingress_profile import (
        PROFILE as SCANLINE_ERROR_FLOAT_BITS_INGRESS_PROFILE,
        SCANLINE_ERROR_KEY, apply_scanline_error_float_bits_ingress,
        authenticate_scanline_error_float_bits_ingress)
    from tools.glslcpp.frontend.shapes_float_bits_ingress_profile import (
        PROFILE as SHAPES_FLOAT_BITS_INGRESS_PROFILE,
        SHAPES_FLOAT_BITS_INGRESS_KEYS, SHAPES_KEY,
        apply_shapes_float_bits_ingress,
        authenticate_shapes_float_bits_ingress)
    from tools.glslcpp.frontend.grime_float_bits_ingress_profile import (
        PROFILE as GRIME_FLOAT_BITS_INGRESS_PROFILE,
        GRIME_FLOAT_BITS_INGRESS_KEYS, GRIME_KEY,
        apply_grime_float_bits_ingress,
        authenticate_grime_float_bits_ingress)
    from tools.glslcpp.frontend.shapes_rvalue_assign_profile import (
        PROFILE as SHAPES_RVALUE_ASSIGN_PROFILE,
        SHAPES_RVALUE_ASSIGN_KEYS,
        apply_shapes_rvalue_assign, authenticate_shapes_rvalue_assign)
    from tools.glslcpp.frontend.cross_lane_assignment_profile import (
        CROSS_LANE_KEY, PROFILE as CROSS_LANE_ASSIGNMENT_PROFILE,
        apply_cross_lane_assignment, authenticate_cross_lane_assignment)
    from tools.glslcpp.frontend.mandelbrot_sequential_dz_assignment_profile import (
        KEY as MANDELBROT_SEQUENTIAL_DZ_KEY,
        PROFILE as MANDELBROT_SEQUENTIAL_DZ_PROFILE,
        apply_mandelbrot_sequential_dz_assignment,
        authenticate_mandelbrot_sequential_dz_assignment)
    from tools.glslcpp.frontend.mutable_global_frame_profile import (
        MUTABLE_GLOBAL_FRAME_KEYS,
        NOISE_KEY as MUTABLE_GLOBAL_FRAME_NOISE_KEY,
        PROFILES as MUTABLE_GLOBAL_FRAME_PROFILES,
        REQUIRED_COMPANION_PROFILES as MUTABLE_GLOBAL_FRAME_COMPANIONS,
        SHAPE_KEY as MUTABLE_GLOBAL_FRAME_SHAPE_KEY,
        allowed_row_fields as mutable_global_frame_allowed_row_fields,
        apply_mutable_global_frame, authenticate_mutable_global_frame,
        frame_contract as mutable_global_frame_contract)
    from tools.glslcpp.frontend.noise_runtime_define_profile import (
        DYNAMIC_DEFINES as NOISE_DYNAMIC_DEFINES,
        KEY as NOISE_RUNTIME_DEFINE_KEY,
        PROFILE as NOISE_RUNTIME_DEFINE_PROFILE,
        dynamic_frame_contract,
        is_dynamic_program,
        transform_source as transform_noise_source)
    from tools.glslcpp.frontend.testpattern_profile import (
        KEY as TESTPATTERN_KEY,
        PROFILE as TESTPATTERN_PROFILE,
        authenticate_testpattern_frontend,
        preflight_testpattern_bindings,
        allowed_row_fields as testpattern_allowed_row_fields)
    from tools.glslcpp.frontend.remap_profile import (
        KEY as REMAP_KEY,
        PROFILE as REMAP_PROFILE,
        ALLOWED_ROW_FIELDS as REMAP_ALLOWED_ROW_FIELDS,
        authenticate_remap_frontend,
        preflight_remap_bindings)
    from tools.glslcpp.frontend.mutable_global_array_profile import (
        CELLREFRACT_KEY as MUTABLE_GLOBAL_ARRAY_CELLREFRACT_KEY,
        EFFECTS_KEY as MUTABLE_GLOBAL_ARRAY_EFFECTS_KEY,
        KALEIDO_KEY as MUTABLE_GLOBAL_ARRAY_KALEIDO_KEY,
        MUTABLE_GLOBAL_ARRAY_KEYS,
        PROFILES as MUTABLE_GLOBAL_ARRAY_PROFILES,
        REQUIRED_COMPANION_PROFILES as MUTABLE_GLOBAL_ARRAY_COMPANIONS,
        allowed_row_fields as mutable_global_array_allowed_row_fields,
        apply_mutable_global_array, authenticate_mutable_global_array,
        frame_contract as mutable_global_array_contract,
        store_census as mutable_global_array_store_census)
    from tools.glslcpp.frontend.const_global_table_profile import (
        CONST_GLOBAL_TABLE_KEYS,
        NORMAL_MAP_KEY as CONST_GLOBAL_TABLE_NORMAL_MAP_KEY,
        PROFILES as CONST_GLOBAL_TABLE_PROFILES,
        REQUIRED_COMPANION_PROFILES as CONST_GLOBAL_TABLE_COMPANIONS,
        allowed_row_fields as const_global_table_allowed_row_fields,
        apply_const_global_tables, authenticate_const_global_table_reads,
        authenticate_const_global_tables,
        table_contract as const_global_table_contract)
    from tools.glslcpp.frontend.varying_uv_profile import (
        VARYING_UV_KEYS,
        PROFILES as VARYING_UV_PROFILES,
        allowed_row_fields as varying_uv_allowed_row_fields,
        apply_varying_uv, authenticate_varying_uv,
        varying_uv_contract)
    from tools.glslcpp.frontend.glyph_map_nonnegative_int_shift_profile import (
        GLYPH_MAP_KEY, PROFILE as GLYPH_MAP_NONNEGATIVE_INT_SHIFT_PROFILE,
        apply_glyph_map_nonnegative_int_shift,
        authenticate_glyph_map_nonnegative_int_shift)
    from tools.glslcpp.frontend.curl_vector_math_profile import (
        CURL_KEY, PROFILE as CURL_VECTOR_MATH_PROFILE,
        apply_curl_vector_math, authenticate_curl_vector_math)
    from tools.glslcpp.frontend.derivative_admission_profile import (
        DERIVATIVE_ADMISSION_KEYS, PROFILE as DERIVATIVE_ADMISSION_PROFILE,
        apply_derivative_admission, authenticate_derivative_admission)
    from tools.glslcpp.frontend.posterize_round_profile import (
        POSTERIZE_KEY, PROFILE as POSTERIZE_ROUND_PROFILE,
        apply_posterize_round_admission, authenticate_posterize_round_admission)
    from tools.glslcpp.frontend.ceil_admission_profile import (
        CEIL_ADMISSION_KEYS, authenticate_ceil_admission)
    from tools.glslcpp.frontend.as_u32_round_profile import (
        AS_U32_ROUND_KEYS, PROFILE as AS_U32_ROUND_PROFILE,
        apply_as_u32_round_admission, authenticate_as_u32_round_admission)
    from tools.glslcpp.frontend.waves_any_notequal_profile import (
        WAVES_KEY, PROFILE as WAVES_ANY_NOTEQUAL_PROFILE,
        apply_waves_any_notequal_admission, authenticate_waves_any_notequal_admission)
    from tools.glslcpp.frontend.inout_vec3_swap_profile import (
        WATERCOLOR_KEY as INOUT_VEC3_SWAP_KEY,
        PROFILE as INOUT_VEC3_SWAP_PROFILE,
        apply_inout_vec3_swap_admission, authenticate_inout_vec3_swap_admission)
    from tools.glslcpp.frontend.out_inout_admission_profile import (
        LIGHTLEAK_KEY as OUT_INOUT_ADMISSION_LIGHTLEAK_KEY,
        LIGHTLEAK_PROFILE as OUT_INOUT_ADMISSION_LIGHTLEAK_PROFILE,
        MANDELBROT_KEY as OUT_INOUT_ADMISSION_MANDELBROT_KEY,
        MANDELBROT_PROFILE as OUT_INOUT_ADMISSION_MANDELBROT_PROFILE,
        NEWTON_KEY as OUT_INOUT_ADMISSION_NEWTON_KEY,
        NEWTON_PROFILE as OUT_INOUT_ADMISSION_NEWTON_PROFILE,
        OUT_INOUT_ADMISSION_KEYS,
        allowed_row_fields as out_inout_admission_allowed_row_fields,
        apply_out_inout_admission, authenticate_out_inout_admission)
    from tools.glslcpp.frontend.log_admission_profile import (
        MANDELBROT_KEY as LOG_ADMISSION_MANDELBROT_KEY,
        MANDELBROT_PROFILE as LOG_ADMISSION_MANDELBROT_PROFILE,
        apply_log_admission, authenticate_log_admission)
    from tools.glslcpp.frontend.struct_declaration_profile import (
        NEWTON_KEY as STRUCT_DECLARATION_NEWTON_KEY,
        NEWTON_PROFILE as STRUCT_DECLARATION_NEWTON_PROFILE,
        STRUCT_DECLARATION_KEYS,
        allowed_row_fields as struct_declaration_allowed_row_fields,
        apply_struct_declaration, authenticate_struct_declaration)
    from tools.glslcpp.frontend.texture_lod_admission_profile import (
        PARALLAX_KEY as TEXTURE_LOD_ADMISSION_PARALLAX_KEY,
        PARALLAX_PROFILE as TEXTURE_LOD_ADMISSION_PROFILE,
        TEXTURE_LOD_ADMISSION_KEYS,
        allowed_row_fields as texture_lod_admission_allowed_row_fields,
        apply_texture_lod_admission, authenticate_texture_lod_admission)
    from tools.glslcpp.frontend.runtime_loop_bound_profile import (
        BLUR_KEYS,
        NOISE_KEY as RUNTIME_LOOP_BOUND_NOISE_KEY,
        PROFILE as RUNTIME_LOOP_BOUND_PROFILE,
        RUNTIME_LOOP_BOUND_KEYS, STATS_KEY, TETRA_KEY,
        apply_runtime_loop_bound, validate_blur_metadata,
        validate_noise_metadata, validate_tetra_metadata)
    from tools.glslcpp.frontend.gabor_effective_depth_profile import (
        GABOR_KEY, PROFILE as GABOR_EFFECTIVE_DEPTH_PROFILE,
        authenticate_gabor_effective_depth,
        validate_gabor_effective_depth_contract, validate_gabor_metadata)
    from tools.glslcpp.frontend.median_frontend_profile import (
        KEY as MEDIAN_KEY, PROFILE as MEDIAN_FRONTEND_PROFILE,
        authenticate_median_frontend)
    from tools.glslcpp.frontend.texture_frontend_profile import (
        KEY as TEXTURE_FRONTEND_KEY,
        PROFILE as TEXTURE_FRONTEND_PROFILE,
        authenticate_texture_frontend,
        apply_texture_frontend)
    from tools.glslcpp.frontend.dither_frontend_profile import (
        KEY as DITHER_KEY,
        PROFILE as DITHER_FRONTEND_PROFILE,
        apply_dither_frontend,
        authenticate_dither_frontend)
    from tools.glslcpp.generate_kernels import GeneratorError, _validate_output_name
else:
    from . import check_corpus, check_semantics
    from .emit_typed_cpp import TypedEmissionError, render_typed_cpp
    from .frontend import parse_program
    from .frontend.historic_palette_profile import (
        PROFILE as HISTORIC_PALETTE_PROFILE,
        apply_historic_palette,
        authenticate_historic_palette)
    from .frontend.palette_frontend_profile import (
        PROFILE as PALETTE_FRONTEND_PROFILE,
        apply_palette_frontend,
        authenticate_palette_frontend)
    from .frontend.color_lab_frontend_profile import (
        KEY as COLOR_LAB_KEY,
        PROFILE as COLOR_LAB_FRONTEND_PROFILE,
        apply_color_lab_frontend,
        authenticate_color_lab_frontend,
        allowed_row_fields as color_lab_allowed_row_fields)
    from .frontend.fractal_frontend_profile import (
        KEY as FRACTAL_KEY,
        PROFILE as FRACTAL_FRONTEND_PROFILE,
        PREPARED_KEYS as FRACTAL_PREPARED_KEYS,
        PREPARED_PROFILES as FRACTAL_PREPARED_PROFILES,
        apply_fractal_frontend,
        authenticate_fractal_frontend,
        authenticate_fractal_metadata)
    from .frontend.julia_frontend_profile import (
        KEY as JULIA_KEY, PROFILE as JULIA_FRONTEND_PROFILE,
        KEYS as JULIA_FRONTEND_KEYS, PROFILES as JULIA_FRONTEND_PROFILES,
        ALLOWED_ROW_FIELDS as JULIA_FRONTEND_ALLOWED_ROW_FIELDS,
        apply_julia_frontend, authenticate_julia_frontend)
    from .frontend.semantic_types import BOOL, FLOAT
    from .frontend.typed_ir import TypedExpression, TypedStatement
    from .frontend.loop_proof import (
        COUNTED_FOR_V1_MAX_ENTRYPOINT_CHARGE, COUNTED_FOR_V1_MAX_LEXICAL_PRODUCT,
        COUNTED_FOR_V1_MAX_TRIP_COUNT,
        SOURCE_GLOBAL_LITERAL_INT_CAPABILITY, SOURCE_GLOBAL_LITERAL_INT_KEYS,
        attach_counted_loop_proofs, clear_counted_loop_proofs,
        rebuild_authenticated_counted_loop_proofs,
        summarize_counted_loop_proofs)
    from .frontend.local_counter_proof import (
        CAPABILITY as LOCAL_COUNTER_CAPABILITY,
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
        CELLREFRACT_KEY as TASK19_CELLREFRACT_KEY,
        EFFECTS_KEY as TASK19_EFFECTS_KEY,
        KALEIDO_KEY as TASK19_KALEIDO_KEY,
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
    from .frontend.linear_srgb_lane_index_profile import (
        KEYS as LINEAR_SRGB_LANE_INDEX_KEYS,
        PROFILES as LINEAR_SRGB_LANE_INDEX_PROFILES,
        apply_linear_srgb_lane_index, authenticate_linear_srgb_lane_index)
    from .frontend.reflect_admission_profile import (
        LIGHTING_KEY as REFLECT_ADMISSION_KEY,
        PROFILE as REFLECT_ADMISSION_PROFILE,
        apply_reflect_admission, authenticate_reflect_admission)
    from .frontend.perlin_scalar_uint_xor_profile import (
        PERLIN_KEY, PROFILE as PERLIN_SCALAR_UINT_XOR_PROFILE,
        apply_perlin_scalar_uint_xor,
        authenticate_perlin_scalar_uint_xor)
    from .frontend.scalar_uint_xor_profile import (
        KALEIDO_INGRESS_KEY as KALEIDO_FLOAT_BITS_INGRESS_KEY,
        NOISE_INGRESS_KEY as NOISE_FLOAT_BITS_INGRESS_KEY,
        PROFILE as SCALAR_UINT_XOR_PROFILE, SCALAR_UINT_XOR_KEYS,
        apply_scalar_uint_xor, authenticate_kaleido_float_bits_ingress,
        authenticate_noise_float_bits_ingress,
        authenticate_scalar_uint_xor)
    from .frontend.bitwise_scalar_int_ops_profile import (
        KEYS as BITWISE_SCALAR_INT_OPS_KEYS,
        PROFILES as BITWISE_SCALAR_INT_OPS_PROFILES,
        apply_bitwise_scalar_int_ops, authenticate_bitwise_scalar_int_ops,
        authenticate_bitwise_scalar_int_ops_transition)
    from .frontend.bit_effects_profile import (
        KEY as BIT_EFFECTS_KEY,
        PROFILE as BIT_EFFECTS_PROFILE,
        PREPARED_KEYS as BIT_EFFECTS_PREPARED_KEYS,
        PREPARED_PROFILES as BIT_EFFECTS_PREPARED_PROFILES,
        apply_bit_effects_frontend,
        authenticate_bit_effects_frontend)
    from .frontend.osd_frontend_profile import (
        KEY as OSD_KEY,
        PROFILE as OSD_FRONTEND_PROFILE,
        PREPARED_KEYS as OSD_PREPARED_KEYS,
        PREPARED_PROFILES as OSD_PREPARED_PROFILES,
        apply_osd_frontend,
        authenticate_osd_frontend)
    from .frontend.moodscape_frontend_profile import (
        KEY as MOODSCAPE_KEY,
        PROFILE as MOODSCAPE_FRONTEND_PROFILE,
        PREPARED_KEYS as MOODSCAPE_PREPARED_KEYS,
        PREPARED_PROFILES as MOODSCAPE_PREPARED_PROFILES,
        apply_moodscape_frontend,
        authenticate_moodscape_projection)
    from .frontend.noise_frontend_profile import (
        KEY as NOISE_FRONTEND_KEY,
        PROFILE as NOISE_FRONTEND_PROFILE,
        apply_noise_frontend,
        authenticate_noise_projection,
        authenticate_noise_runtime)
    from .frontend.spooky_ticker_frontend_profile import (
        KEY as SPOOKY_TICKER_KEY,
        PROFILE as SPOOKY_TICKER_FRONTEND_PROFILE,
        PREPARED_KEYS as SPOOKY_TICKER_PREPARED_KEYS,
        PREPARED_PROFILES as SPOOKY_TICKER_PREPARED_PROFILES,
        authenticate_spooky_ticker_frontend)
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
    from .frontend.edge_bvec3_contour_profile import (
        EDGE_KEY, PROFILE as EDGE_BVEC3_CONTOUR_PROFILE,
        apply_edge_bvec3_contour, authenticate_edge_bvec3_contour,
        authenticate_edge_center_splat)
    from .frontend.glitch_mat4_chain_profile import (
        EFFECTS_KEY as GLITCH_MAT4_CHAIN_EFFECTS_KEY,
        EFFECTS_PROFILE as EFFECTS_MAT4_CHAIN_PROFILE,
        GLITCH_KEY, PROFILE as GLITCH_MAT4_CHAIN_PROFILE,
        REQUIRED_COMPANION_PROFILES as GLITCH_MAT4_CHAIN_COMPANIONS,
        apply_glitch_mat4_chain, authenticate_glitch_mat4_chain)
    GLITCH_MAT4_CHAIN_KEYS = frozenset(
        {GLITCH_KEY, GLITCH_MAT4_CHAIN_EFFECTS_KEY})
    GLITCH_MAT4_CHAIN_PROFILES = {
        GLITCH_KEY: GLITCH_MAT4_CHAIN_PROFILE,
        GLITCH_MAT4_CHAIN_EFFECTS_KEY: EFFECTS_MAT4_CHAIN_PROFILE}
    from .frontend.emboss_color_style_profile import (
        EMBOSS_KEY, PROFILE as EMBOSS_COLOR_STYLE_PROFILE,
        apply_emboss_color_style, authenticate_emboss_color_style)
    from .frontend.shape_mixer_builtin_profile import (
        PROFILE as SHAPE_MIXER_BUILTIN_PROFILE, SHAPE_MIXER_KEY,
        apply_shape_mixer_builtin_closure,
        authenticate_shape_mixer_builtin_closure)
    from .frontend.caustic_word_hash_profile import (
        CAUSTIC_KEY, PROFILE as CAUSTIC_WORD_HASH_PROFILE,
        apply_caustic_word_hash, authenticate_caustic_word_hash)
    from .frontend.scanline_error_float_bits_ingress_profile import (
        PROFILE as SCANLINE_ERROR_FLOAT_BITS_INGRESS_PROFILE,
        SCANLINE_ERROR_KEY, apply_scanline_error_float_bits_ingress,
        authenticate_scanline_error_float_bits_ingress)
    from .frontend.shapes_float_bits_ingress_profile import (
        PROFILE as SHAPES_FLOAT_BITS_INGRESS_PROFILE,
        SHAPES_FLOAT_BITS_INGRESS_KEYS, SHAPES_KEY,
        apply_shapes_float_bits_ingress,
        authenticate_shapes_float_bits_ingress)
    from .frontend.grime_float_bits_ingress_profile import (
        PROFILE as GRIME_FLOAT_BITS_INGRESS_PROFILE,
        GRIME_FLOAT_BITS_INGRESS_KEYS, GRIME_KEY,
        apply_grime_float_bits_ingress,
        authenticate_grime_float_bits_ingress)
    from .frontend.shapes_rvalue_assign_profile import (
        PROFILE as SHAPES_RVALUE_ASSIGN_PROFILE,
        SHAPES_RVALUE_ASSIGN_KEYS,
        apply_shapes_rvalue_assign, authenticate_shapes_rvalue_assign)
    from .frontend.cross_lane_assignment_profile import (
        CROSS_LANE_KEY, PROFILE as CROSS_LANE_ASSIGNMENT_PROFILE,
        apply_cross_lane_assignment, authenticate_cross_lane_assignment)
    from .frontend.mandelbrot_sequential_dz_assignment_profile import (
        KEY as MANDELBROT_SEQUENTIAL_DZ_KEY,
        PROFILE as MANDELBROT_SEQUENTIAL_DZ_PROFILE,
        apply_mandelbrot_sequential_dz_assignment,
        authenticate_mandelbrot_sequential_dz_assignment)
    from .frontend.mutable_global_frame_profile import (
        MUTABLE_GLOBAL_FRAME_KEYS,
        NOISE_KEY as MUTABLE_GLOBAL_FRAME_NOISE_KEY,
        PROFILES as MUTABLE_GLOBAL_FRAME_PROFILES,
        REQUIRED_COMPANION_PROFILES as MUTABLE_GLOBAL_FRAME_COMPANIONS,
        SHAPE_KEY as MUTABLE_GLOBAL_FRAME_SHAPE_KEY,
        allowed_row_fields as mutable_global_frame_allowed_row_fields,
        apply_mutable_global_frame, authenticate_mutable_global_frame,
        frame_contract as mutable_global_frame_contract)
    from .frontend.noise_runtime_define_profile import (
        DYNAMIC_DEFINES as NOISE_DYNAMIC_DEFINES,
        KEY as NOISE_RUNTIME_DEFINE_KEY,
        PROFILE as NOISE_RUNTIME_DEFINE_PROFILE,
        dynamic_frame_contract,
        is_dynamic_program,
        transform_source as transform_noise_source)
    from .frontend.testpattern_profile import (
        KEY as TESTPATTERN_KEY,
        PROFILE as TESTPATTERN_PROFILE,
        authenticate_testpattern_frontend,
        preflight_testpattern_bindings,
        allowed_row_fields as testpattern_allowed_row_fields)
    from .frontend.remap_profile import (
        KEY as REMAP_KEY,
        PROFILE as REMAP_PROFILE,
        ALLOWED_ROW_FIELDS as REMAP_ALLOWED_ROW_FIELDS,
        authenticate_remap_frontend,
        preflight_remap_bindings)
    from .frontend.mutable_global_array_profile import (
        CELLREFRACT_KEY as MUTABLE_GLOBAL_ARRAY_CELLREFRACT_KEY,
        EFFECTS_KEY as MUTABLE_GLOBAL_ARRAY_EFFECTS_KEY,
        KALEIDO_KEY as MUTABLE_GLOBAL_ARRAY_KALEIDO_KEY,
        MUTABLE_GLOBAL_ARRAY_KEYS,
        PROFILES as MUTABLE_GLOBAL_ARRAY_PROFILES,
        REQUIRED_COMPANION_PROFILES as MUTABLE_GLOBAL_ARRAY_COMPANIONS,
        allowed_row_fields as mutable_global_array_allowed_row_fields,
        apply_mutable_global_array, authenticate_mutable_global_array,
        frame_contract as mutable_global_array_contract,
        store_census as mutable_global_array_store_census)
    from .frontend.const_global_table_profile import (
        CONST_GLOBAL_TABLE_KEYS,
        NORMAL_MAP_KEY as CONST_GLOBAL_TABLE_NORMAL_MAP_KEY,
        PROFILES as CONST_GLOBAL_TABLE_PROFILES,
        REQUIRED_COMPANION_PROFILES as CONST_GLOBAL_TABLE_COMPANIONS,
        allowed_row_fields as const_global_table_allowed_row_fields,
        apply_const_global_tables, authenticate_const_global_table_reads,
        authenticate_const_global_tables,
        table_contract as const_global_table_contract)
    from .frontend.varying_uv_profile import (
        VARYING_UV_KEYS,
        PROFILES as VARYING_UV_PROFILES,
        allowed_row_fields as varying_uv_allowed_row_fields,
        apply_varying_uv, authenticate_varying_uv,
        varying_uv_contract)
    from .frontend.glyph_map_nonnegative_int_shift_profile import (
        GLYPH_MAP_KEY, PROFILE as GLYPH_MAP_NONNEGATIVE_INT_SHIFT_PROFILE,
        apply_glyph_map_nonnegative_int_shift,
        authenticate_glyph_map_nonnegative_int_shift)
    from .frontend.curl_vector_math_profile import (
        CURL_KEY, PROFILE as CURL_VECTOR_MATH_PROFILE,
        apply_curl_vector_math, authenticate_curl_vector_math)
    from .frontend.derivative_admission_profile import (
        DERIVATIVE_ADMISSION_KEYS, PROFILE as DERIVATIVE_ADMISSION_PROFILE,
        apply_derivative_admission, authenticate_derivative_admission)
    from .frontend.posterize_round_profile import (
        POSTERIZE_KEY, PROFILE as POSTERIZE_ROUND_PROFILE,
        apply_posterize_round_admission, authenticate_posterize_round_admission)
    from .frontend.ceil_admission_profile import (
        CEIL_ADMISSION_KEYS, authenticate_ceil_admission)
    from .frontend.as_u32_round_profile import (
        AS_U32_ROUND_KEYS, PROFILE as AS_U32_ROUND_PROFILE,
        apply_as_u32_round_admission, authenticate_as_u32_round_admission)
    from .frontend.waves_any_notequal_profile import (
        WAVES_KEY, PROFILE as WAVES_ANY_NOTEQUAL_PROFILE,
        apply_waves_any_notequal_admission, authenticate_waves_any_notequal_admission)
    from .frontend.inout_vec3_swap_profile import (
        WATERCOLOR_KEY as INOUT_VEC3_SWAP_KEY,
        PROFILE as INOUT_VEC3_SWAP_PROFILE,
        apply_inout_vec3_swap_admission, authenticate_inout_vec3_swap_admission)
    from .frontend.out_inout_admission_profile import (
        LIGHTLEAK_KEY as OUT_INOUT_ADMISSION_LIGHTLEAK_KEY,
        LIGHTLEAK_PROFILE as OUT_INOUT_ADMISSION_LIGHTLEAK_PROFILE,
        MANDELBROT_KEY as OUT_INOUT_ADMISSION_MANDELBROT_KEY,
        MANDELBROT_PROFILE as OUT_INOUT_ADMISSION_MANDELBROT_PROFILE,
        NEWTON_KEY as OUT_INOUT_ADMISSION_NEWTON_KEY,
        NEWTON_PROFILE as OUT_INOUT_ADMISSION_NEWTON_PROFILE,
        OUT_INOUT_ADMISSION_KEYS,
        allowed_row_fields as out_inout_admission_allowed_row_fields,
        apply_out_inout_admission, authenticate_out_inout_admission)
    from .frontend.log_admission_profile import (
        MANDELBROT_KEY as LOG_ADMISSION_MANDELBROT_KEY,
        MANDELBROT_PROFILE as LOG_ADMISSION_MANDELBROT_PROFILE,
        apply_log_admission, authenticate_log_admission)
    from .frontend.struct_declaration_profile import (
        NEWTON_KEY as STRUCT_DECLARATION_NEWTON_KEY,
        NEWTON_PROFILE as STRUCT_DECLARATION_NEWTON_PROFILE,
        STRUCT_DECLARATION_KEYS,
        allowed_row_fields as struct_declaration_allowed_row_fields,
        apply_struct_declaration, authenticate_struct_declaration)
    from .frontend.texture_lod_admission_profile import (
        PARALLAX_KEY as TEXTURE_LOD_ADMISSION_PARALLAX_KEY,
        PARALLAX_PROFILE as TEXTURE_LOD_ADMISSION_PROFILE,
        TEXTURE_LOD_ADMISSION_KEYS,
        allowed_row_fields as texture_lod_admission_allowed_row_fields,
        apply_texture_lod_admission, authenticate_texture_lod_admission)
    from .frontend.runtime_loop_bound_profile import (
        BLUR_KEYS,
        NOISE_KEY as RUNTIME_LOOP_BOUND_NOISE_KEY,
        PROFILE as RUNTIME_LOOP_BOUND_PROFILE,
        RUNTIME_LOOP_BOUND_KEYS, STATS_KEY, TETRA_KEY,
        apply_runtime_loop_bound, validate_blur_metadata,
        validate_noise_metadata, validate_tetra_metadata)
    from .frontend.gabor_effective_depth_profile import (
        GABOR_KEY, PROFILE as GABOR_EFFECTIVE_DEPTH_PROFILE,
        authenticate_gabor_effective_depth,
        validate_gabor_effective_depth_contract, validate_gabor_metadata)
    from .frontend.median_frontend_profile import (
        KEY as MEDIAN_KEY, PROFILE as MEDIAN_FRONTEND_PROFILE,
        authenticate_median_frontend)
    from .frontend.texture_frontend_profile import (
        KEY as TEXTURE_FRONTEND_KEY,
        PROFILE as TEXTURE_FRONTEND_PROFILE,
        authenticate_texture_frontend,
        apply_texture_frontend)
    from .frontend.dither_frontend_profile import (
        KEY as DITHER_KEY,
        PROFILE as DITHER_FRONTEND_PROFILE,
        apply_dither_frontend,
        authenticate_dither_frontend)
    from .generate_kernels import GeneratorError, _validate_output_name


def _same_object_sequence(actual, expected) -> bool:
    """Return true only when two sequences contain the identical objects."""
    return (len(actual) == len(expected)
            and all(left is right for left, right in zip(actual, expected)))


def _program_owned_object_ids(program) -> set[int]:
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
        program) -> tuple[TypedExpression, ...]:
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
    "uvec2", "uvec3", "uvec4", "mat2", "mat3", "sampler2D", "void",
)
APPROVED_BINARY_OPERATORS = (
    "!=", "%", "&", "&&", "*", "+", "-", "/", "<", "<=", "==", ">", ">=", ">>", "^", "|", "||",
)
APPROVED_ASSIGNMENT_OPERATORS = ("*=", "+=", "-=", "/=", "=", "^=")

GRAIN_KEY = "filter/grain:grain"
# Shapes' one admitted define pair. `LOOP_A_OFFSET=40` (square) /
# `LOOP_B_OFFSET=30` (diamond) is a default-only typed factory; no alternate
# variant is admitted, so this is a literal, not a lookup.
_SHAPES_DEFINES = {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30}
# `synth/shape`'s one admitted define pair. Numerically identical to
# `_SHAPES_DEFINES` and deliberately a SEPARATE constant: they are different
# programs, and sharing one literal would let a change to either silently move
# the other.
_SHAPE_DEFINES = {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30}
_NOISE_DEFINES = {"LOOP_OFFSET": 300, "NOISE_TYPE": 10}
_CLASSIC_NOISE_DEFINES = {
    "COLOR_MODE": 6,
    "LOOP_OFFSET": 300,
    "METRIC": 0,
    "NOISE_TYPE": 10,
    "REFRACT_MODE": 2,
}
_MUTABLE_GLOBAL_FRAME_DEFINES = {
    MUTABLE_GLOBAL_FRAME_NOISE_KEY: _NOISE_DEFINES,
    MUTABLE_GLOBAL_FRAME_SHAPE_KEY: _SHAPE_DEFINES,
}
_RUNTIME_LOOP_BOUND_DEFINES = {
    key: (_NOISE_DEFINES if key == RUNTIME_LOOP_BOUND_NOISE_KEY else {})
    for key in RUNTIME_LOOP_BOUND_KEYS
}
# The mutable-global array carriers' exact admitted defines, PER KEY since
# the kaleido row (never a hardcoded dict shared by the whole family -- the
# `_CONST_GLOBAL_TABLE_DEFINES` lesson): at `KERNEL=0` the convolution-kernel
# branches are stripped, which is what makes the five mutable globals
# write-only -- the property the whole closure is frozen against.
# cellRefract: `SHAPE=1` selects the polar shape arm. kaleido: `DIRECTION=2`
# / `LOOP_OFFSET=10` / `METRIC=0` pin the kaleidoscope arm, the circles
# offset chain (kept as constant `if` guards) and the euclidean metric.
_MUTABLE_GLOBAL_ARRAY_DEFINES = {
    MUTABLE_GLOBAL_ARRAY_CELLREFRACT_KEY: {"KERNEL": 0, "SHAPE": 1},
    MUTABLE_GLOBAL_ARRAY_KALEIDO_KEY: {"DIRECTION": 2, "KERNEL": 0,
                                       "LOOP_OFFSET": 10, "METRIC": 0},
    MUTABLE_GLOBAL_ARRAY_EFFECTS_KEY: {"EFFECT": 0, "FLIP": 0},
}
# Per-key exact defines for the const-global nine-table carriers, never a
# hardcoded `{}` shared by the whole family: `linear_srgb_lane_index_profile`
# carried exactly such a hardcoded value and had to become a per-key lock when
# a second key arrived. `.get(key)` returns None for an unlisted future
# carrier, which fails the drift census closed rather than passing silently.
_CONST_GLOBAL_TABLE_DEFINES = {CONST_GLOBAL_TABLE_NORMAL_MAP_KEY: {}}
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
        if key == NOISE_RUNTIME_DEFINE_KEY:
            if item.get("runtime_define_profile") != NOISE_RUNTIME_DEFINE_PROFILE:
                raise GeneratorError(
                    f"{key}: exact runtime-define profile required")
        elif "runtime_define_profile" in item:
            raise GeneratorError(
                f"{key}: runtime-define profile on foreign key")
        expected = ({"curl_vector_math_profile", "defines", "program_key"}
                    if key == CURL_KEY else
                    {"defines", "gabor_effective_depth_profile", "program_key"}
                    if key == GABOR_KEY else
                    {"defines", "program_key",
                     "scanline_error_float_bits_ingress_profile"}
                    if key == SCANLINE_ERROR_KEY else
                    {"defines", "glyph_map_nonnegative_int_shift_profile",
                     "program_key"}
                    if key == GLYPH_MAP_KEY else
                    {"defines", "edge_bvec3_contour_profile", "program_key"}
                    if key == EDGE_KEY else
                    {"defines", "emboss_color_style_profile", "program_key"}
                    if key == EMBOSS_KEY else
                    {"defines", "program_key", "scalar_uint_xor_profile",
                     "shape_mixer_builtin_profile"}
                    if key == SHAPE_MIXER_KEY else
                    {"defines", "glitch_mat4_chain_profile", "program_key"}
                    if key == GLITCH_KEY else
                    {"caustic_word_hash_profile", "defines", "program_key"}
                    if key == CAUSTIC_KEY else
                    {"defines", "extrude_bvec2_relational_reduction_profile",
                     "program_key"}
                    if key == EXTRUDE_KEY else
                    {"defines", "focus_blur_borrowed_sampler_profile", "program_key"}
                    if key == FOCUS_BLUR_KEY else
                    {"defines", "distortion_frontend_profile", "program_key"}
                    if key == DISTORTION_FRONTEND_KEY else
                    {"defines", "rotate_mat2_return_profile", "program_key"}
                    if key == ROTATE_KEY else
                    {"defines", "perlin_scalar_uint_xor_profile", "program_key"}
                    if key == PERLIN_KEY else
                    {"as_u32_round_profile", "defines", "program_key",
                     "scalar_uint_xor_profile"}
                    if key == GRAIN_KEY else
                    {"defines", "bitwise_scalar_int_ops_profile", "program_key"}
                    if key in BITWISE_SCALAR_INT_OPS_KEYS else
                    {"bit_effects_frontend_profile", "defines", "program_key"}
                    if key in BIT_EFFECTS_PREPARED_KEYS else
                    {"defines", "osd_frontend_profile", "program_key"}
                    if key in OSD_PREPARED_KEYS else
                    {"defines", "noise_frontend_profile", "program_key"}
                    if key == NOISE_FRONTEND_KEY else
                    {"defines", "moodscape_frontend_profile", "program_key"}
                    if key in MOODSCAPE_PREPARED_KEYS else
                    {"defines", "program_key",
                     "spooky_ticker_frontend_profile"}
                    if key in SPOOKY_TICKER_PREPARED_KEYS else
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
                    # Shapes needs its own arm ahead of the shared
                    # linear-sRGB arm: it is the only member of that cluster
                    # that also carries the reused scalar-XOR carrier and its
                    # own float-bit ingress carrier. The shared arm below
                    # would reject those two extra keys.
                    {"defines", "linear_srgb_lane_index_profile",
                     "program_key", "scalar_uint_xor_profile",
                     "shapes_float_bits_ingress_profile",
                     "shapes_rvalue_assign_profile"}
                    if key == SHAPES_KEY else
                    # Design S7.2 row 20 -- companion exactness. The set comes
                    # from the profile module's own ALLOWLIST accessor, never
                    # from a denylist naming sibling profiles: `set(item) !=
                    # expected` below is exact set equality, so an allowlist
                    # discharges "every other profile absent" exhaustively and
                    # cannot go stale as profile fields are added elsewhere in
                    # the tree.
                    (set(mutable_global_frame_allowed_row_fields(key))
                     | {"runtime_define_profile"})
                    if key == NOISE_RUNTIME_DEFINE_KEY else
                    set(testpattern_allowed_row_fields(key))
                    if key == TESTPATTERN_KEY else
                    set(REMAP_ALLOWED_ROW_FIELDS[key])
                    if key == REMAP_KEY else
                    set(mutable_global_frame_allowed_row_fields(key))
                    if key in MUTABLE_GLOBAL_FRAME_KEYS else
                    # Same allowlist-by-accessor discipline as the frame arm
                    # above: `set(item) != expected` below is exact set
                    # equality, so the closure's own ALLOWED_ROW_FIELDS
                    # discharges "every other profile absent" exhaustively.
                    set(mutable_global_array_allowed_row_fields(key))
                    if key in MUTABLE_GLOBAL_ARRAY_KEYS else
                    # Same allowlist-by-accessor discipline as the two arms
                    # above: the varying-uv closure's own ALLOWED_ROW_FIELDS
                    # is the universal two fields plus exactly `varying_profile`
                    # -- pure expression lowering, no companion carrier.
                    set(varying_uv_allowed_row_fields(key))
                    if key in VARYING_UV_KEYS else
                    # Same allowlist-by-accessor discipline as the three arms
                    # above: the textureLod admission closure's own
                    # ALLOWED_ROW_FIELDS is the universal two fields plus
                    # exactly `texture_lod_admission_profile` -- the counted-
                    # for seed carrier rides the loop-proof dict key, not a
                    # row field, so this row stays minimal.
                    set(texture_lod_admission_allowed_row_fields(key))
                    if key in TEXTURE_LOD_ADMISSION_KEYS else
                    {"defines", "linear_srgb_lane_index_profile", "program_key"}
                    if key in LINEAR_SRGB_LANE_INDEX_KEYS else
                    {"defines", "derivative_admission_profile",
                     "posterize_round_profile", "program_key"}
                    if key == POSTERIZE_KEY else
                    # ORDERING HAZARD (design amendment S14). This arm MUST
                    # stay ahead of the `key in AS_U32_ROUND_KEYS` arm
                    # immediately below: `filter/normalMap:normalMap` is a
                    # member of AS_U32_ROUND_KEYS, so that arm would otherwise
                    # claim this row and reject `const_global_table_profile`
                    # with the generic "typed slice programs are invalid",
                    # naming the wrong mechanism. Same placement rule as
                    # SHAPES_KEY's arm ahead of the shared linear-sRGB arm.
                    # The set comes from the closure's own ALLOWLIST accessor,
                    # never from a second spelling here.
                    set(const_global_table_allowed_row_fields(key))
                    if key in CONST_GLOBAL_TABLE_KEYS else
                    {"defines", "as_u32_round_profile", "program_key"}
                    if key in AS_U32_ROUND_KEYS else
                    {"defines", "ceil_admission_profile", "program_key"}
                    if key in CEIL_ADMISSION_KEYS else
                    {"defines", "derivative_admission_profile",
                     "waves_any_notequal_profile", "program_key"}
                    if key == WAVES_KEY else
                    {"defines", "derivative_admission_profile", "program_key"}
                    if key in DERIVATIVE_ADMISSION_KEYS else
                    {"defines", "reflect_admission_profile", "program_key"}
                    if key == REFLECT_ADMISSION_KEY else
                    {"defines", "inout_vec3_swap_profile", "program_key"}
                    if key == INOUT_VEC3_SWAP_KEY else
                    set(JULIA_FRONTEND_ALLOWED_ROW_FIELDS[key])
                    if key in JULIA_FRONTEND_KEYS else
                    set(struct_declaration_allowed_row_fields(key))
                    if key in STRUCT_DECLARATION_KEYS else
                    {"defines", "log_admission_profile",
                     "out_inout_admission_profile", "program_key"}
                    if key == MANDELBROT_SEQUENTIAL_DZ_KEY else
                    set(out_inout_admission_allowed_row_fields(key))
                    if key in OUT_INOUT_ADMISSION_KEYS else
                    {"defines", "program_key", "runtime_loop_bound_profile"}
                    if key in RUNTIME_LOOP_BOUND_KEYS else
                    {"defines", "cross_lane_assignment_profile", "program_key"}
                    if key == CROSS_LANE_KEY else
                    {"defines", "historic_palette_profile", "program_key"}
                    if key == "filter/historicPalette:historicPalette" else
                    {"defines", "palette_frontend_profile", "program_key"}
                    if key == "filter/palette:palette" else
                    {"defines", "median_frontend_profile", "program_key"}
                    if key == MEDIAN_KEY else
                    {"defines", "program_key", "texture_frontend_profile"}
                    if key == TEXTURE_FRONTEND_KEY else
                    {"defines", "dither_frontend_profile", "program_key"}
                    if key == DITHER_KEY else
                    set(color_lab_allowed_row_fields(key))
                    if key == COLOR_LAB_KEY else
                    {"defines", "fractal_frontend_profile", "program_key"}
                    if key in FRACTAL_PREPARED_KEYS else
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
    scalar_uint_xor_profiles = [
        (item["program_key"], item.get("scalar_uint_xor_profile"),
         item["defines"])
        for item in programs if "scalar_uint_xor_profile" in item]
    bitwise_profiles = [
        (item["program_key"], item.get("bitwise_scalar_int_ops_profile"),
         item["defines"])
        for item in programs if "bitwise_scalar_int_ops_profile" in item]
    bit_effects_profiles = [
        (item["program_key"], item.get("bit_effects_frontend_profile"),
         item["defines"])
        for item in programs if "bit_effects_frontend_profile" in item]
    osd_profiles = [
        (item["program_key"], item.get("osd_frontend_profile"),
         item["defines"])
        for item in programs if "osd_frontend_profile" in item]
    moodscape_profiles = [
        (item["program_key"], item.get("moodscape_frontend_profile"),
         item["defines"])
        for item in programs if "moodscape_frontend_profile" in item]
    spooky_ticker_profiles = [
        (item["program_key"], item.get("spooky_ticker_frontend_profile"),
         item["defines"])
        for item in programs if "spooky_ticker_frontend_profile" in item]
    caustic_profiles = [
        (item["program_key"], item.get("caustic_word_hash_profile"),
         item["defines"])
        for item in programs if "caustic_word_hash_profile" in item]
    scanline_error_profiles = [
        (item["program_key"],
         item.get("scanline_error_float_bits_ingress_profile"), item["defines"])
        for item in programs
        if "scanline_error_float_bits_ingress_profile" in item]
    shapes_float_bits_ingress_profiles = [
        (item["program_key"],
         item.get("shapes_float_bits_ingress_profile"), item["defines"])
        for item in programs
        if "shapes_float_bits_ingress_profile" in item]
    grime_float_bits_ingress_profiles = [
        (item["program_key"],
         item.get("grime_float_bits_ingress_profile"), item["defines"])
        for item in programs
        if "grime_float_bits_ingress_profile" in item]
    shapes_rvalue_assign_profiles = [
        (item["program_key"],
         item.get("shapes_rvalue_assign_profile"), item["defines"])
        for item in programs
        if "shapes_rvalue_assign_profile" in item]
    cross_lane_assignment_profiles = [
        (item["program_key"], item.get("cross_lane_assignment_profile"), item["defines"])
        for item in programs if "cross_lane_assignment_profile" in item]
    mutable_global_frame_profiles = [
        (item["program_key"],
         item.get("mutable_global_frame_profile"), item["defines"])
        for item in programs
        if "mutable_global_frame_profile" in item]
    mutable_global_array_profiles = [
        (item["program_key"],
         item.get("mutable_global_array_profile"), item["defines"])
        for item in programs
        if "mutable_global_array_profile" in item]
    varying_uv_profiles = [
        (item["program_key"],
         item.get("varying_profile"), item["defines"])
        for item in programs
        if "varying_profile" in item]
    texture_lod_admission_profiles = [
        (item["program_key"],
         item.get("texture_lod_admission_profile"), item["defines"])
        for item in programs
        if "texture_lod_admission_profile" in item]
    const_global_table_profiles = [
        (item["program_key"],
         item.get("const_global_table_profile"), item["defines"])
        for item in programs
        if "const_global_table_profile" in item]
    glyph_map_profiles = [
        (item["program_key"],
         item.get("glyph_map_nonnegative_int_shift_profile"), item["defines"])
        for item in programs
        if "glyph_map_nonnegative_int_shift_profile" in item]
    edge_profiles = [
        (item["program_key"], item.get("edge_bvec3_contour_profile"),
         item["defines"])
        for item in programs if "edge_bvec3_contour_profile" in item]
    glitch_profiles = [
        (item["program_key"], item.get("glitch_mat4_chain_profile"),
         item["defines"])
        for item in programs if "glitch_mat4_chain_profile" in item]
    emboss_profiles = [
        (item["program_key"], item.get("emboss_color_style_profile"),
         item["defines"])
        for item in programs if "emboss_color_style_profile" in item]
    shape_mixer_profiles = [
        (item["program_key"], item.get("shape_mixer_builtin_profile"),
         item["defines"])
        for item in programs if "shape_mixer_builtin_profile" in item]
    rotate_profiles = [
        (item["program_key"], item.get("rotate_mat2_return_profile"),
         item["defines"])
        for item in programs if "rotate_mat2_return_profile" in item]
    focus_profiles = [
        (item["program_key"], item.get("focus_blur_borrowed_sampler_profile"),
         item["defines"])
        for item in programs if "focus_blur_borrowed_sampler_profile" in item]
    distortion_profiles = [
        (item["program_key"], item.get("distortion_frontend_profile"),
         item["defines"])
        for item in programs if "distortion_frontend_profile" in item]
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
    linear_srgb_profiles = [
        (item["program_key"], item.get("linear_srgb_lane_index_profile"),
         item["defines"])
        for item in programs if "linear_srgb_lane_index_profile" in item]
    derivative_profiles = [
        (item["program_key"], item.get("derivative_admission_profile"),
         item["defines"])
        for item in programs if "derivative_admission_profile" in item]
    reflect_profiles = [
        (item["program_key"], item.get("reflect_admission_profile"),
         item["defines"])
        for item in programs if "reflect_admission_profile" in item]
    runtime_loop_profiles = [
        (item["program_key"], item.get("runtime_loop_bound_profile"), item["defines"])
        for item in programs if "runtime_loop_bound_profile" in item]
    testpattern_profiles = [
        (item["program_key"], item.get("testpattern_profile"), item["defines"])
        for item in programs if "testpattern_profile" in item]
    remap_profiles = [
        (item["program_key"], item.get("remap_profile"), item["defines"])
        for item in programs if "remap_profile" in item]
    gabor_effective_depth_profiles = [
        (item["program_key"], item.get("gabor_effective_depth_profile"),
         item["defines"])
        for item in programs if "gabor_effective_depth_profile" in item]
    historic_palette_profiles = [
        (item["program_key"], item.get("historic_palette_profile"),
         item["defines"])
        for item in programs if "historic_palette_profile" in item]
    palette_frontend_profiles = [
        (item["program_key"], item.get("palette_frontend_profile"),
         item["defines"])
        for item in programs if "palette_frontend_profile" in item]
    color_lab_frontend_profiles = [
        (item["program_key"], item.get("color_lab_frontend_profile"),
         item["defines"])
        for item in programs if "color_lab_frontend_profile" in item]
    median_frontend_profiles = [
        (item["program_key"], item.get("median_frontend_profile"),
         item["defines"])
        for item in programs if "median_frontend_profile" in item]
    texture_frontend_profiles = [
        (item["program_key"], item.get("texture_frontend_profile"),
         item["defines"])
        for item in programs if "texture_frontend_profile" in item]
    dither_frontend_profiles = [
        (item["program_key"], item.get("dither_frontend_profile"),
         item["defines"])
        for item in programs if "dither_frontend_profile" in item]
    julia_frontend_profiles = [
        (item["program_key"], item.get("julia_frontend_profile"),
         item["defines"])
        for item in programs if "julia_frontend_profile" in item]
    if (keys != sorted(set(keys)) or len(keys) != 211
            or _sha256(("\n".join(keys) + "\n").encode("utf-8"))
            != "29a148b26cfe4f550ac82325810655eb0e5ffad2c3a4e5241e42600bac9f76c1"
            or lane_profiles != [(key, LITERAL_VEC3_LANE_INDEX_PROFILE)
                                 for key in LITERAL_VEC3_LANE_INDEX_KEYS]
            or smooth_profiles != [
                (SMOOTH_EDGE_KEY, SMOOTH_EDGE_LUMA_WEIGHTS_PROFILE, {})]
            or perlin_profiles != [
                (PERLIN_KEY, PERLIN_SCALAR_UINT_XOR_PROFILE,
                 {"DIMENSIONS": 2})]
            or scalar_uint_xor_profiles != [
                # kaleido reuses the frozen carrier verbatim as the REQUIRED
                # companion of its mutable-global array row and sorts first
                # of the six carriers.
                (MUTABLE_GLOBAL_ARRAY_KALEIDO_KEY, SCALAR_UINT_XOR_PROFILE,
                 _MUTABLE_GLOBAL_ARRAY_DEFINES[
                     MUTABLE_GLOBAL_ARRAY_KALEIDO_KEY]),
                (SHAPE_MIXER_KEY, SCALAR_UINT_XOR_PROFILE,
                 {"LOOP_OFFSET": 10}),
                # Shapes reuses the existing carrier verbatim and sorts
                # between Shape Mixer and Grain.
                (SHAPES_KEY, SCALAR_UINT_XOR_PROFILE, _SHAPES_DEFINES),
                (GRAIN_KEY, SCALAR_UINT_XOR_PROFILE, {}),
                (NOISE_FLOAT_BITS_INGRESS_KEY, SCALAR_UINT_XOR_PROFILE,
                 _NOISE_DEFINES),
                # `synth/shape` reuses the same frozen carrier verbatim and
                # sorts last of the five.
                (MUTABLE_GLOBAL_FRAME_SHAPE_KEY, SCALAR_UINT_XOR_PROFILE,
                 _SHAPE_DEFINES)]
            or bitwise_profiles != [
                (key, BITWISE_SCALAR_INT_OPS_PROFILES[key], {})
                for key in BITWISE_SCALAR_INT_OPS_KEYS]
            or bit_effects_profiles != [
                (BIT_EFFECTS_KEY, BIT_EFFECTS_PROFILE, {
                    "COLOR_SCHEME": 20, "FORMULA": 0, "INTERP": 0,
                    "MASK_COLOR_SCHEME": 1, "MASK_FORMULA": 10, "MODE": 1})]
            or osd_profiles != [(OSD_KEY, OSD_FRONTEND_PROFILE, {})]
            or moodscape_profiles not in ([], [
                (MOODSCAPE_KEY, MOODSCAPE_FRONTEND_PROFILE,
                 {"COLOR_MODE": 2, "NOISE_TYPE": 10})])
            or spooky_ticker_profiles != [
                (SPOOKY_TICKER_KEY, SPOOKY_TICKER_FRONTEND_PROFILE, {})]
            or caustic_profiles != [
                (CAUSTIC_KEY, CAUSTIC_WORD_HASH_PROFILE, {"NOISE_TYPE": 10})]
            or scanline_error_profiles != [
                (SCANLINE_ERROR_KEY,
                 SCANLINE_ERROR_FLOAT_BITS_INGRESS_PROFILE, {})]
            or glyph_map_profiles != [
                (GLYPH_MAP_KEY, GLYPH_MAP_NONNEGATIVE_INT_SHIFT_PROFILE, {})]
            or edge_profiles != [
                (EDGE_KEY, EDGE_BVEC3_CONTOUR_PROFILE, {})]
            or emboss_profiles != [
                (EMBOSS_KEY, EMBOSS_COLOR_STYLE_PROFILE, {"STYLE": 0})]
            or shape_mixer_profiles != [
                (SHAPE_MIXER_KEY, SHAPE_MIXER_BUILTIN_PROFILE,
                 {"LOOP_OFFSET": 10})]
            or rotate_profiles != [
                (ROTATE_KEY, ROTATE_MAT2_RETURN_PROFILE, {})]
            or focus_profiles != [
                (FOCUS_BLUR_KEY, FOCUS_BLUR_BORROWED_SAMPLER_PROFILE, {})]
            or distortion_profiles not in ([],
                [(DISTORTION_FRONTEND_KEY, DISTORTION_FRONTEND_PROFILE, {})])
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
            or linear_srgb_profiles != [
                # Per-key exact defines, not a hardcoded `{}`: the three
                # original members are define-free, Shapes is admitted only
                # at its exact 40/30 default pair.
                (key, LINEAR_SRGB_LANE_INDEX_PROFILES[key],
                 _SHAPES_DEFINES if key == SHAPES_KEY else {})
                for key in LINEAR_SRGB_LANE_INDEX_KEYS]
            or derivative_profiles != [
                (key, DERIVATIVE_ADMISSION_PROFILE,
                 {"MODE": 0, "PATTERN": 0} if key == "filter/halftone:halftone" else
                 {"STYLE": 2, "WRAP": 0} if key == "filter/pondRipples:pondRipples" else
                 {"MODE": 0} if key == "filter/stipple:stipple" else {})
                for key in sorted(DERIVATIVE_ADMISSION_KEYS)]
            or reflect_profiles != [
                (REFLECT_ADMISSION_KEY, REFLECT_ADMISSION_PROFILE, {})]
            or runtime_loop_profiles != [
                (key, RUNTIME_LOOP_BOUND_PROFILE,
                 _RUNTIME_LOOP_BOUND_DEFINES[key])
                for key in sorted(RUNTIME_LOOP_BOUND_KEYS)]
                or gabor_effective_depth_profiles != [
                    (GABOR_KEY, GABOR_EFFECTIVE_DEPTH_PROFILE, {})]
                or historic_palette_profiles != [
                    ("filter/historicPalette:historicPalette",
                     HISTORIC_PALETTE_PROFILE, {})]
                or palette_frontend_profiles != [
                    ("filter/palette:palette", PALETTE_FRONTEND_PROFILE, {})]
            or color_lab_frontend_profiles != [
                    (COLOR_LAB_KEY, COLOR_LAB_FRONTEND_PROFILE, {})]
            or median_frontend_profiles != [
                (MEDIAN_KEY, MEDIAN_FRONTEND_PROFILE, {"RADIUS": 2})]
            or texture_frontend_profiles != [
                (TEXTURE_FRONTEND_KEY, TEXTURE_FRONTEND_PROFILE, {"MODE": 3})]):
        raise GeneratorError("typed slice literal vec3 lane profile drift")
    # Deliberately its own check with its own message rather than another
    # clause in the 14-clause `or` chain above, which reports every one of
    # its failures under the name of its last clause ("literal vec3 lane
    # profile drift") and so points at the wrong mechanism.
    if shapes_float_bits_ingress_profiles != [
            (SHAPES_KEY, SHAPES_FLOAT_BITS_INGRESS_PROFILE, _SHAPES_DEFINES)]:
        raise GeneratorError(
            "typed slice Shapes float-bit ingress profile drift")
    # Its own NAMED census for the same reason as the Shapes one directly
    # above: folded into the big `or` chain it would report every grime
    # ingress failure as "literal vec3 lane profile drift".
    if grime_float_bits_ingress_profiles != [
            (key, GRIME_FLOAT_BITS_INGRESS_PROFILE, {})
            for key in sorted(GRIME_FLOAT_BITS_INGRESS_KEYS)]:
        raise GeneratorError(
            "typed slice grime float-bit ingress profile drift")
    if shapes_rvalue_assign_profiles != [
            (SHAPES_KEY, SHAPES_RVALUE_ASSIGN_PROFILE, _SHAPES_DEFINES)]:
        raise GeneratorError(
            "typed slice Shapes rvalue-assign profile drift")
    # Its own check with its own message, for the same reason as the two
    # above: a clause in the 14-clause `or` chain would report this mechanism's
    # failures as "typed slice literal vec3 lane profile drift" and point at
    # the wrong closure entirely.
    if cross_lane_assignment_profiles != [
            (CROSS_LANE_KEY, CROSS_LANE_ASSIGNMENT_PROFILE, {})]:
        raise GeneratorError("typed slice cross-lane assignment profile drift")
    if mutable_global_frame_profiles != [
            (key, MUTABLE_GLOBAL_FRAME_PROFILES[key],
             _MUTABLE_GLOBAL_FRAME_DEFINES[key])
            for key in sorted(MUTABLE_GLOBAL_FRAME_KEYS)]:
        raise GeneratorError(
            "typed slice mutable-global frame profile drift")
    if testpattern_profiles != [
            (TESTPATTERN_KEY, TESTPATTERN_PROFILE, {})]:
        raise GeneratorError("typed slice Test Pattern frontend profile drift")
    if remap_profiles != [(REMAP_KEY, REMAP_PROFILE, {})]:
        raise GeneratorError("typed slice Remap frontend profile drift")
    # Its own NAMED census with its own message since the effects row
    # (design §4.5): a clause in the big `or` chain above would report this
    # mechanism's failures as "typed slice literal vec3 lane profile drift"
    # and send the reader to the wrong closure entirely. effects (row 188)
    # is the module's second key, with its own per-key profile string.
    if glitch_profiles != [
            # Row order: effects (ordinal 5) sorts immediately ahead of
            # glitch -- adjacent to the program whose carrier family it
            # joined.
            (GLITCH_MAT4_CHAIN_EFFECTS_KEY, EFFECTS_MAT4_CHAIN_PROFILE,
             _MUTABLE_GLOBAL_ARRAY_DEFINES[GLITCH_MAT4_CHAIN_EFFECTS_KEY]),
            (GLITCH_KEY, GLITCH_MAT4_CHAIN_PROFILE, {})]:
        raise GeneratorError(
            "typed slice Glitch mat4 chain profile drift")
    # Its own named census with its own message, for the same reason as the
    # three above: a clause in the big `or` chain would report this
    # mechanism's failures as "typed slice literal vec3 lane profile drift"
    # and send the reader to the wrong closure entirely.
    if mutable_global_array_profiles != [
            (key, MUTABLE_GLOBAL_ARRAY_PROFILES[key],
             _MUTABLE_GLOBAL_ARRAY_DEFINES.get(key))
            for key in sorted(MUTABLE_GLOBAL_ARRAY_KEYS)]:
        raise GeneratorError(
            "typed slice mutable-global array profile drift")
    # Its own NAMED census with its own message, for the same reason as the
    # four above: folded into the big `or` chain it would report every
    # varying-uv failure as "typed slice literal vec3 lane profile drift"
    # and send the reader to the wrong closure entirely.
    if varying_uv_profiles != [
            (key, VARYING_UV_PROFILES[key], {})
            for key in sorted(VARYING_UV_KEYS)]:
        raise GeneratorError(
            "typed slice varying-uv profile drift")
    # Its own NAMED census with its own message, for the same reason as the
    # five above: folded into the big `or` chain it would report every
    # textureLod-admission failure as "typed slice literal vec3 lane profile
    # drift" and send the reader to the wrong closure entirely.
    if texture_lod_admission_profiles != [
            (TEXTURE_LOD_ADMISSION_PARALLAX_KEY,
             TEXTURE_LOD_ADMISSION_PROFILE, {})]:
        raise GeneratorError(
            "typed slice textureLod admission profile drift")
    # Its own NAMED census with its own message, for the same reason as the
    # three above (design amendment S14): folded into the big `or` chain it
    # would report every const-global nine-table failure as "typed slice
    # literal vec3 lane profile drift" and send the reader to the wrong
    # closure entirely.
    if const_global_table_profiles != [
            (key, CONST_GLOBAL_TABLE_PROFILES[key],
             _CONST_GLOBAL_TABLE_DEFINES.get(key))
            for key in sorted(CONST_GLOBAL_TABLE_KEYS)]:
        raise GeneratorError(
            "typed slice const-global nine-table profile drift")
    profiles = [(item["program_key"], item.get("gather_sorted_round_profile"))
                for item in programs if "gather_sorted_round_profile" in item]
    if profiles != [(GATHER_SORTED_KEY, GATHER_SORTED_ROUND_PROFILE)]:
        raise GeneratorError("typed slice Gather Sorted round profile drift")
    posterize_round_profiles = [
        (item["program_key"], item.get("posterize_round_profile"))
        for item in programs if "posterize_round_profile" in item]
    if posterize_round_profiles != [(POSTERIZE_KEY, POSTERIZE_ROUND_PROFILE)]:
        raise GeneratorError("typed slice Posterize round admission profile drift")
    as_u32_round_profiles = [
        (item["program_key"], item.get("as_u32_round_profile"))
        for item in programs if "as_u32_round_profile" in item]
    ceil_profiles = [
        (item["program_key"], item.get("ceil_admission_profile"))
        for item in programs if "ceil_admission_profile" in item]
    if as_u32_round_profiles != [
            (key, AS_U32_ROUND_PROFILE) for key in sorted(AS_U32_ROUND_KEYS)
            if key in {item["program_key"] for item in programs}]:
        raise GeneratorError("typed slice as_u32 round admission profile drift")
    if ceil_profiles != [
            (key, "ceil-admission-v1") for key in sorted(CEIL_ADMISSION_KEYS)
            if key in {item["program_key"] for item in programs}]:
        raise GeneratorError("typed slice ceil admission profile drift")
    waves_any_notequal_profiles = [
        (item["program_key"], item.get("waves_any_notequal_profile"))
        for item in programs if "waves_any_notequal_profile" in item]
    if waves_any_notequal_profiles != [(WAVES_KEY, WAVES_ANY_NOTEQUAL_PROFILE)]:
        raise GeneratorError("typed slice Waves any/notEqual admission profile drift")
    inout_vec3_swap_profiles = [
        (item["program_key"], item.get("inout_vec3_swap_profile"))
        for item in programs if "inout_vec3_swap_profile" in item]
    out_inout_admission_profiles = [
        (item["program_key"], item.get("out_inout_admission_profile"),
         item["defines"])
        for item in programs if "out_inout_admission_profile" in item]
    log_admission_profiles = [
        (item["program_key"], item.get("log_admission_profile"),
         item["defines"])
        for item in programs if "log_admission_profile" in item]
    struct_declaration_profiles = [
        (item["program_key"], item.get("struct_declaration_profile"),
         item["defines"])
        for item in programs if "struct_declaration_profile" in item]
    if inout_vec3_swap_profiles != [(INOUT_VEC3_SWAP_KEY, INOUT_VEC3_SWAP_PROFILE)]:
        raise GeneratorError("typed slice Inout vec3 swap admission profile drift")
    if out_inout_admission_profiles != [
            (OUT_INOUT_ADMISSION_LIGHTLEAK_KEY,
             OUT_INOUT_ADMISSION_LIGHTLEAK_PROFILE, {}),
            (JULIA_KEY, "out-inout-admission-julia-v1", {}),
            (OUT_INOUT_ADMISSION_MANDELBROT_KEY,
             OUT_INOUT_ADMISSION_MANDELBROT_PROFILE, {}),
            (OUT_INOUT_ADMISSION_NEWTON_KEY,
             OUT_INOUT_ADMISSION_NEWTON_PROFILE, {})]:
        raise GeneratorError("typed slice out/inout admission profile drift")
    if log_admission_profiles != [
            (LOG_ADMISSION_MANDELBROT_KEY,
             LOG_ADMISSION_MANDELBROT_PROFILE, {})]:
        raise GeneratorError("typed slice log admission profile drift")
    if struct_declaration_profiles != [
            (JULIA_KEY, "struct-declaration-julia-v1", {}),
            (STRUCT_DECLARATION_NEWTON_KEY,
             STRUCT_DECLARATION_NEWTON_PROFILE, {})]:
        raise GeneratorError("typed slice struct declaration profile drift")
    if julia_frontend_profiles != [
            (JULIA_KEY, JULIA_FRONTEND_PROFILE, {})]:
        raise GeneratorError("typed slice Julia frontend profile drift")
    if historic_palette_profiles != [
            ("filter/historicPalette:historicPalette",
             HISTORIC_PALETTE_PROFILE, {})]:
        raise GeneratorError("typed slice Historic Palette profile drift")
    if palette_frontend_profiles != [
            ("filter/palette:palette", PALETTE_FRONTEND_PROFILE, {})]:
        raise GeneratorError("typed slice Palette profile drift")
    if color_lab_frontend_profiles != [
            (COLOR_LAB_KEY, COLOR_LAB_FRONTEND_PROFILE, {})]:
        raise GeneratorError("typed slice ColorLab frontend profile drift")
    if median_frontend_profiles != [
            (MEDIAN_KEY, MEDIAN_FRONTEND_PROFILE, {"RADIUS": 2})]:
        raise GeneratorError("typed slice Median frontend profile drift")
    if texture_frontend_profiles != [
            (TEXTURE_FRONTEND_KEY, TEXTURE_FRONTEND_PROFILE, {"MODE": 3})]:
        raise GeneratorError("typed slice Texture frontend profile drift")
    if dither_frontend_profiles != [
            (DITHER_KEY, DITHER_FRONTEND_PROFILE, {})]:
        raise GeneratorError("typed slice Dither frontend profile drift")
    if keys.count(DEGAUSS_KEY) != 1 or keys.count(CRT_KEY) != 1:
        raise GeneratorError("Task 22 CRT publication boundary drift")
    for item in programs:
        defines = item["defines"]
        if not isinstance(defines, dict) or any(not isinstance(name, str) or not isinstance(value, int)
                                                for name, value in defines.items()):
            raise GeneratorError(f"{item['program_key']}: invalid default-define contract")
    expected_defines = {
        BIT_EFFECTS_KEY: {
            "COLOR_SCHEME": 20, "FORMULA": 0, "INTERP": 0,
            "MASK_COLOR_SCHEME": 1, "MASK_FORMULA": 10, "MODE": 1},
        CAUSTIC_KEY: {"NOISE_TYPE": 10},
        MOODSCAPE_KEY: {"COLOR_MODE": 2, "NOISE_TYPE": 10},
        NOISE_FRONTEND_KEY: _CLASSIC_NOISE_DEFINES,
        CURL_KEY: {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True},
        EXTRUDE_KEY: {"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0},
        EMBOSS_KEY: {"STYLE": 0},
        SHAPE_MIXER_KEY: {"LOOP_OFFSET": 10},
        SHAPES_KEY: _SHAPES_DEFINES,
        MUTABLE_GLOBAL_FRAME_SHAPE_KEY: _SHAPE_DEFINES,
        MUTABLE_GLOBAL_FRAME_NOISE_KEY: _NOISE_DEFINES,
        # Per-key since the kaleido row (the review's second
        # `_MUTABLE_GLOBAL_ARRAY_DEFINES` consumption site): the dict merge
        # below fails closed against a key the constants table forgot.
        **_MUTABLE_GLOBAL_ARRAY_DEFINES,
        "filter/hatch:hatch": {"MODE": 0},
        "filter/lensFlare:lensFlare": {"LENS_TYPE": 0},
            "filter/lowPoly:lowPoly": {"LP_BORDER": 0, "LP_LIGHT": 0},
            MEDIAN_KEY: {"RADIUS": 2},
        "filter/mosaicTiles:mosaicTiles": {"MODE": 0},
        "filter/morphology:morphA": {"SHAPE": 0},
        "filter/morphology:morphB": {"SHAPE": 0},
        "filter/oilPaint:oilFlatten": {"MODE": 1},
        "filter/oilPaint:oilPost": {"MODE": 1},
        "filter/relief:rlBlurH": {"MODE": 0},
        "filter/relief:rlBlurV": {"MODE": 0},
        "filter/relief:rlShade": {"MODE": 0},
        "filter/scatter:scatterSmooth": {"MODE": 0},
        "filter/scatter:scatterJitter": {"MODE": 0},
        "filter/strokes:stkPost": {"MODE": 0},
        "filter/strokes:stkSmear": {"MODE": 0},
        TEXTURE_FRONTEND_KEY: {"MODE": 3},
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
        "struct FactoryRoute {", "  std::string_view key;",
        "  std::string_view canonical_factory;",
        "  std::string_view emitted_factory;",
        "  std::string_view route_kind;",
        "  std::string_view source_sha256;",
        "  std::string_view typed_abi_sha256;",
        "  // The compile-define contract and the values baked into the emitted",
        "  // kernel. A `default-only` program cannot honour any other value.",
        "  std::string_view define_contract;",
        "  std::string_view defines;",
        "  // Out-of-plan anchors for the ordered binding ABI, one per section.",
        "  std::string_view sampler_abi_sha256;",
        "  std::string_view uniform_abi_sha256;",
        "  std::string_view output_abi_sha256;",
        "  std::string_view output_extent_sha256;",
        "  std::string_view compile_define_abi_sha256;",
        "  BoundKernel (*bind)(const glsl::Bindings&);", "};", "",
        "[[nodiscard]] std::span<const KernelFactory> catalog() noexcept;",
        "[[nodiscard]] BoundKernel bind(std::string_view key, const glsl::Bindings& bindings);",
        "[[nodiscard]] std::span<const FactoryRoute> canonical_routes() noexcept;",
        "[[nodiscard]] const FactoryRoute* find_canonical(std::string_view key,",
        "                                                     std::string_view canonical_factory) noexcept;",
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


def _typed_abi(typed) -> dict[str, Any]:
    """Serialize the interface consumed by ``render_typed_cpp``.

    This is intentionally produced in the same loop that validates and emits
    the typed program. Downstream admission code must consume this record
    rather than re-derive an ABI from source text or generated C++.
    """
    declarations = {item.symbol.name: item for item in typed.declarations}
    uniforms = []
    for name in typed.resources.uniforms:
        declaration = declarations.get(name)
        if declaration is None:
            raise GeneratorError(f"{typed.key}: typed ABI declaration missing for {name}")
        uniforms.append({"name": name, "type": declaration.type.display()})
    return {
        "uniforms": uniforms,
        "samplers": list(typed.resources.samplers),
        "outputs": list(typed.resources.outputs),
        "uses_texture": bool(typed.resources.uses_texture),
        "uses_derivatives": bool(typed.resources.uses_derivatives),
    }


def _typed_abi_sha256(typed_abi: dict[str, Any]) -> str:
    """Hash the canonical serialized typed ABI used by compatibility admission."""
    # The typed manifest is serialized with sort_keys=True.  Hashing the same
    # canonical bytes here keeps this descriptor identical to the compatibility
    # generator's authenticated typed_abi_sha256 after a clean regeneration.
    return _sha256((json.dumps(typed_abi, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def _define_token(value: Any) -> str:
    """Canonical text for one baked compile-define value."""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return repr(value)


def _baked_defines(item: dict[str, Any]) -> str:
    """The compile-define values baked into the emitted kernel, canonically ordered.

    The executor compares a requested effect parameter against these; a
    `default-only` program cannot honour any other value, so a mismatch has to
    fail closed instead of rendering the baked program with wrong bytes.
    """
    defines = item.get("defines") or {}
    return ";".join(f"{name}={_define_token(defines[name])}" for name in sorted(defines))


def _binding_abi_sections(row: dict[str, Any] | None, defines: list[dict[str, str]]) -> dict[str, str]:
    """Per-section digests of one canonical compatibility row's ordered ABI.

    This is the out-of-plan anchor: the executor re-derives the same sections
    from the value-owned admission and compares them here, so a reordered or
    retyped ABI inside a plan cannot authenticate. The grammar is mirrored in
    `src/effects/registry.cpp`, `src/graph/executor.cpp`, and
    `tools/dsl/js_frontend_oracle.mjs`; `tests/test_binding_abi_digest.py`
    binds all four together.
    """
    def token(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(int(value)) if float(value).is_integer() else repr(value)
        return str(value)

    def bindings(name: str) -> str:
        out = [f"{name}\x1e"]
        for entry in (row or {}).get(name, []) or []:
            for field in ("name", "type", "source", "source_name", "resource", "cpp_type"):
                out.append(f"{token(entry.get(field, ''))}\x1f")
        out.append("\x1e")
        return "".join(out)

    extent = ((row or {}).get("output_abi") or {}).get("extent") or {}
    outputs = ["outputs\x1e"]
    for entry in (row or {}).get("outputs", []) or []:
        outputs.append(f"{token(entry.get('slot', 0))}\x1f")
        for field in ("physical_name", "logical_route", "cpp_type"):
            outputs.append(f"{token(entry.get(field, ''))}\x1f")
    outputs.append("\x1e")
    define_bytes = ["defines\x1e"]
    for entry in defines:
        define_bytes.append(f"{entry['name']}\x1f{entry['cpp_type']}\x1f{entry['source']}\x1f")
    define_bytes.append("\x1e")
    sections = {
        "sampler_abi_sha256": bindings("samplers"),
        "uniform_abi_sha256": bindings("uniforms"),
        "output_abi_sha256": "".join(outputs),
        "output_extent_sha256": "extent\x1e"
                                f"{token(extent.get('width'))}\x1f"
                                f"{token(extent.get('height'))}\x1f"
                                f"{token(extent.get('format'))}\x1f\x1e",
        "compile_define_abi_sha256": "".join(define_bytes),
    }
    return {name: _sha256(value.encode("utf-8")) for name, value in sections.items()}


def _custom_adapter_defines(row: dict[str, Any] | None) -> list[dict[str, str]]:
    """The custom adapter's compile defines, exactly as the registry projects them."""
    if row is None or (((row.get("factory") or {}).get("route") or {}).get("kind")) != "custom_adapter":
        return []
    uniform_names = {entry.get("name", "") for entry in row.get("uniforms", []) or []}
    result = []
    for entry in ((row["factory"]["route"].get("binding_abi") or {}).get("uniforms") or []):
        name = entry.get("name", "")
        if not name or name in uniform_names:
            continue
        result.append({"name": name, "cpp_type": entry.get("cpp_type", ""),
                       "source": entry.get("source", "")})
    return result


def _factory_route_descriptor(item: dict[str, Any], *, emitted_factory: str | None = None,
                              bind_factory: str | None = None,
                              route_kind: str | None = None,
                              source_sha256: str | None = None,
                              compatibility_row: dict[str, Any] | None = None) -> dict[str, str]:
    """Project one authenticated manifest row into executable route identity."""
    route = item["factory_route"]
    descriptor = {
        "key": item["program_key"],
        "canonical_factory": item["factory"],
        "emitted_factory": emitted_factory or item["emitted_factory"],
        "route_kind": route_kind or route["kind"],
        # This is the pinned shader source identity consumed by PassAdmission,
        # not the generated translation-unit hash stored in factory_route.
        "source_sha256": source_sha256 or item["source_sha256"],
        "typed_abi_sha256": _typed_abi_sha256(item["typed_abi"]),
        "define_contract": item.get("define_contract", ""),
        "defines": _baked_defines(item),
        "bind_factory": bind_factory or item["factory"],
    }
    descriptor.update(_binding_abi_sections(compatibility_row,
                                            _custom_adapter_defines(compatibility_row)))
    return descriptor


def _compatibility_canonical_rows(repository: pathlib.Path) -> dict[str, dict[str, Any]]:
    """The authenticated canonical compatibility rows, keyed by program key.

    Only read here; this generator never writes the compatibility document.
    A repository without the projection (historical generator tests) yields an
    empty map and the ABI anchors degrade to the empty-section digests, which
    the executor still compares.
    """
    path = repository / "src/effects/generated/backend_compatibility.json"
    if not path.is_file():
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    return {row["program_key"]: row for row in document.get("canonical_programs", [])}


def _compatibility_source_hashes(
        repository: pathlib.Path,
        manifest_programs: list[dict[str, Any]]) -> dict[str, str]:
    """Authenticate the source identity that PassAdmission carries at execute time.

    The typed manifest hashes the pinned corpus source.  The compatibility
    projection additionally records the pinned upstream source after its
    source-lock transform; that ``new_raw_sha256`` is the identity copied into
    a live admission.  Keep a narrow fallback for historical generator tests
    that construct a repository without the compatibility projection.
    """
    path = repository / "src/effects/generated/backend_compatibility.json"
    if not path.is_file():
        return {item["program_key"]: item["source_sha256"]
                for item in manifest_programs}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        rows = document["canonical_programs"]
        if not isinstance(rows, list):
            raise ValueError("canonical_programs is not an array")
        by_key = {row["program_key"]: row for row in rows}
        result = {}
        for item in manifest_programs:
            row = by_key.get(item["program_key"])
            if not isinstance(row, dict) or row.get("old_raw_sha256") != item["source_sha256"]:
                raise ValueError(f"source identity mismatch for {item['program_key']}")
            value = row.get("new_raw_sha256")
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError(f"invalid authenticated source identity for {item['program_key']}")
            result[item["program_key"]] = value
        return result
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise GeneratorError(f"invalid authenticated compatibility source projection: {error}") from error


def _factory_route(repository: pathlib.Path, key: str) -> dict[str, Any]:
    emitted = "bind_" + key.replace("/", "_").replace(":", "_")
    if key != BIT_EFFECTS_KEY:
        return {"kind": "typed_emitter", "factory": emitted,
                "source": "src/typed_generated/typed_slice.cpp"}
    source_path = repository / "src/effects/bit_effects.cpp"
    source = source_path.read_text(encoding="utf-8")
    calls = []
    for match in re.finditer(r"b\.get<([^>]+)>\(\"([^\"]+)\"\)|b\.get_number\(\"([^\"]+)\"\)", source):
        cpp_type, typed_name, number_name = match.groups()
        calls.append({"name": typed_name or number_name,
                      "cpp_type": cpp_type or "double", "source": "custom_adapter"})
    if len(calls) != 20:
        raise GeneratorError(f"{key}: custom factory binding ABI census drift")
    return {
        "kind": "custom_adapter", "factory": "noisemaker::effects::bind_bit_effects",
        "emitted_factory": emitted, "source": source_path.relative_to(repository).as_posix(),
        "source_sha256": _sha256(source_path.read_bytes()),
        "binding_abi": {"uniforms": calls, "samplers": []},
        "output_abi": {"cardinality": 1, "cpp_type": "glsl::Vec4"},
    }


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
                          shapes_float_bits_ingress_profile: str | None = None,
                          grime_float_bits_ingress_profile: str | None = None,
                          shapes_rvalue_assign_profile: str | None = None,
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
                          mutable_global_frame_profile: str | None = None,
                          mutable_global_array_profile: str | None = None,
                          const_global_table_profile: str | None = None,
                          varying_profile: str | None = None,
                          osd_frontend_profile: str | None = None,
                          moodscape_frontend_profile: str | None = None,
                          spooky_ticker_frontend_profile: str | None = None,
                          texture_lod_admission_profile: str | None = None,
                          cross_lane_assignment_profile: str | None = None,
                          testpattern_frontend_proof: object | None = None,
                          remap_frontend_proof: object | None = None,
                          mandelbrot_sequential_dz_assignment_profile: str | None = None,
                          log_admission_profile: str | None = None,
                          struct_declaration_profile: str | None = None,
                          historic_palette_profile: str | None = None,
                          palette_frontend_profile: str | None = None,
                          color_lab_frontend_profile: str | None = None,
                          fractal_frontend_profile: str | None = None,
                          fractal_metadata_effect: dict[str, Any] | None = None,
                          julia_frontend_profile: str | None = None,
                          median_frontend_profile: str | None = None,
                          texture_frontend_profile: str | None = None,
                          distortion_frontend_profile: str | None = None,
                          noise_frontend_profile: str | None = None,
                          dither_frontend_profile: str | None = None) -> None:
    """Prove every emitted typed construct is explicitly approved by this slice."""
    capabilities = tuple(declared)
    literal_source_key = literal_vec3_lane_selected_source_key(typed)
    unknown = sorted(set(capabilities) - set(APPROVED_CAPABILITIES))
    if unknown: raise GeneratorError(f"{typed.key}: unknown capability {unknown[0]}")
    if capabilities != APPROVED_CAPABILITIES:
        raise GeneratorError(f"{typed.key}: typed capability vocabulary mismatch")
    authorized_fractal_frontend_proof = None
    authorized_julia_frontend_proof = None
    authorized_distortion_frontend_proof = None
    authorized_dither_frontend_proof = None
    if dither_frontend_profile is not None:
        profile_values = locals()
        foreign_profiles = tuple(
            name for name, value in profile_values.items()
            if name.endswith("_profile")
            and name != "dither_frontend_profile"
            and value is not None)
        if (typed.key != DITHER_KEY
                or dither_frontend_profile != DITHER_FRONTEND_PROFILE
                or numeric_literal_contract != "glsl-f32"
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or testpattern_frontend_proof is not None
                or remap_frontend_proof is not None
                or foreign_profiles):
            raise GeneratorError(f"{typed.key}: Dither frontend profile metadata mismatch")
        try:
            authorized_dither_frontend_proof = authenticate_dither_frontend(
                typed, source_hash, dither_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == DITHER_KEY:
        raise GeneratorError(f"{typed.key}: exact Dither frontend profile carrier required")
    if distortion_frontend_profile is not None:
        if (typed.key != DISTORTION_FRONTEND_KEY
                or distortion_frontend_profile != DISTORTION_FRONTEND_PROFILE
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: Distortion frontend profile metadata mismatch")
        try:
            authorized_distortion_frontend_proof = authenticate_distortion_frontend(
                typed, source_hash, distortion_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in DISTORTION_FRONTEND_KEYS:
        raise GeneratorError(f"{typed.key}: exact Distortion frontend profile carrier required")
    median_unproved_loop_admitted = False
    authorized_median_frontend_proof = None
    if median_frontend_profile is not None:
        if typed.key != MEDIAN_KEY or median_frontend_profile != MEDIAN_FRONTEND_PROFILE:
            raise GeneratorError(f"{typed.key}: Median frontend profile metadata mismatch")
        try:
            median_proof = authenticate_median_frontend(
                typed, source_hash, median_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        median_unproved_loop_admitted = (
            len(median_proof.unproved_while_spans) == 4
            and len(median_proof.unproved_while_sha256) == 4)
        authorized_median_frontend_proof = median_proof
    elif typed.key == MEDIAN_KEY:
        raise GeneratorError(f"{typed.key}: exact Median frontend profile carrier required")
    dither_unproved_loop_admitted = dither_frontend_profile is not None
    if fractal_frontend_profile is not None:
        profile_values = locals()
        profile_fields = tuple(
            name for name in profile_values
            if name.endswith("_profile") and name != "fractal_frontend_profile")
        if (typed.key not in FRACTAL_PREPARED_KEYS
                or fractal_frontend_profile
                != FRACTAL_PREPARED_PROFILES[typed.key]
                or numeric_literal_contract != "glsl-f32"
                or any(profile_values[name] is not None for name in profile_fields)
                or testpattern_frontend_proof is not None
                or remap_frontend_proof is not None):
            raise GeneratorError(
                f"{typed.key}: Fractal frontend profile metadata mismatch")
        try:
            if fractal_metadata_effect is None:
                raise ValueError("metadata contract mismatch")
            authenticate_fractal_metadata(fractal_metadata_effect)
            authorized_fractal_frontend_proof = authenticate_fractal_frontend(
                typed, source_hash, fractal_frontend_profile)
            profiled = apply_fractal_frontend(
                typed, source_hash, fractal_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        if profiled != typed:
            raise GeneratorError(
                f"{typed.key}: Fractal counted-loop proof mismatch")
    elif typed.key in FRACTAL_PREPARED_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact Fractal frontend profile carrier required")
    if julia_frontend_profile is not None:
        if (typed.key not in JULIA_FRONTEND_KEYS
                or julia_frontend_profile != JULIA_FRONTEND_PROFILES[typed.key]
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: Julia frontend profile metadata mismatch")
        try:
            authorized_julia_frontend_proof = authenticate_julia_frontend(
                typed, source_hash, julia_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in JULIA_FRONTEND_KEYS:
        raise GeneratorError(f"{typed.key}: exact Julia frontend profile carrier required")
    if cross_lane_assignment_profile is not None:
        if typed.key != CROSS_LANE_KEY or cross_lane_assignment_profile != CROSS_LANE_ASSIGNMENT_PROFILE:
            raise GeneratorError(f"{typed.key}: cross-lane assignment profile metadata mismatch")
        try:
            authenticate_cross_lane_assignment(typed, source_hash,
                                               cross_lane_assignment_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == CROSS_LANE_KEY:
        raise GeneratorError(f"{typed.key}: exact cross-lane assignment profile carrier required")
    if mandelbrot_sequential_dz_assignment_profile is not None:
        if (typed.key != MANDELBROT_SEQUENTIAL_DZ_KEY
                or mandelbrot_sequential_dz_assignment_profile
                != MANDELBROT_SEQUENTIAL_DZ_PROFILE):
            raise GeneratorError(
                f"{typed.key}: Mandelbrot sequential-dz profile metadata mismatch")
        try:
            authenticate_mandelbrot_sequential_dz_assignment(
                typed, source_hash, mandelbrot_sequential_dz_assignment_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == MANDELBROT_SEQUENTIAL_DZ_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Mandelbrot sequential-dz profile carrier required")
    if log_admission_profile is not None:
        if (typed.key != LOG_ADMISSION_MANDELBROT_KEY
                or log_admission_profile != LOG_ADMISSION_MANDELBROT_PROFILE
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(
                f"{typed.key}: log admission profile metadata mismatch")
        try:
            log_proof = authenticate_log_admission(
                typed, source_hash, log_admission_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_mandelbrot_logs = tuple(item.node for item in log_proof.sites)
    elif typed.key == LOG_ADMISSION_MANDELBROT_KEY:
        raise GeneratorError(
            f"{typed.key}: exact log admission profile carrier required")
    else:
        authorized_mandelbrot_logs = ()
    visited_mandelbrot_logs: list[TypedExpression] = []
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
    if typed.key in RUNTIME_LOOP_BOUND_KEYS:
        if runtime_loop_bound_profile != RUNTIME_LOOP_BOUND_PROFILE:
            raise GeneratorError(
                f"{typed.key}: exact runtime-loop-bound carrier required")
        if source_hash != _sha256(typed.raw_source.encode("utf-8")):
            raise GeneratorError(
                f"{typed.key}: runtime-loop-bound caller source digest mismatch")
        if (compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or as_u32_round_profile is not None
                or ceil_admission_profile is not None
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None):
            raise GeneratorError(
                f"{typed.key}: runtime-loop-bound profile metadata mismatch")
    elif runtime_loop_bound_profile is not None:
        raise GeneratorError(f"{typed.key}: runtime-loop-bound carrier on foreign key")
    gabor_effective_depth_contract = None
    if typed.key == GABOR_KEY and gabor_effective_depth_profile is not None:
        if gabor_effective_depth_profile != GABOR_EFFECTIVE_DEPTH_PROFILE:
            raise GeneratorError(
                f"{typed.key}: exact Gabor effective-depth profile carrier required")
        if (compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or runtime_loop_bound_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or as_u32_round_profile is not None
                or ceil_admission_profile is not None
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Gabor effective-depth profile metadata mismatch")
        try:
            gabor_effective_depth_contract = authenticate_gabor_effective_depth(
                typed, source_hash, gabor_effective_depth_profile)
            validate_gabor_effective_depth_contract(
                gabor_effective_depth_contract)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        if gabor_effective_depth_contract._candidate is not typed:
            raise GeneratorError(
                f"{typed.key}: Gabor effective-depth candidate identity mismatch")
    elif gabor_effective_depth_profile is not None:
        raise GeneratorError(
            f"{typed.key}: Gabor effective-depth carrier on foreign key")
    authorized_out_inout_parameters: tuple[object, ...] = ()
    authorized_out_inout_calls: tuple[object, ...] = ()
    if out_inout_admission_profile is not None:
        collisions = (
            compatibility_transform, custom_comparer_profile,
            runtime_loop_bound_profile, gabor_effective_depth_profile,
            gather_sorted_round_profile, literal_vec3_lane_index_profile,
            smooth_edge_luma_weights_profile, perlin_scalar_uint_xor_profile,
            scalar_uint_xor_profile, bitwise_scalar_int_ops_profile,
            rotate_mat2_return_profile, focus_blur_borrowed_sampler_profile,
            extrude_bvec2_relational_reduction_profile,
            edge_bvec3_contour_profile, glitch_mat4_chain_profile,
            emboss_color_style_profile, shape_mixer_builtin_profile,
            caustic_word_hash_profile, scanline_error_float_bits_ingress_profile,
            shapes_float_bits_ingress_profile, grime_float_bits_ingress_profile,
            shapes_rvalue_assign_profile, mutable_global_frame_profile,
            mutable_global_array_profile, const_global_table_profile,
            varying_profile, texture_lod_admission_profile,
            cross_lane_assignment_profile, glyph_map_nonnegative_int_shift_profile,
            curl_vector_math_profile, grade_luma_weights_profile,
            grade_index_expression_profile, derivative_admission_profile,
            linear_srgb_lane_index_profile, reflect_admission_profile,
            posterize_round_profile, as_u32_round_profile,
            ceil_admission_profile, waves_any_notequal_profile,
            inout_vec3_swap_profile)
        if (typed.key not in OUT_INOUT_ADMISSION_KEYS
                or out_inout_admission_profile
                != (OUT_INOUT_ADMISSION_NEWTON_PROFILE
                    if typed.key == OUT_INOUT_ADMISSION_NEWTON_KEY
                    else OUT_INOUT_ADMISSION_LIGHTLEAK_PROFILE
                    if typed.key == OUT_INOUT_ADMISSION_LIGHTLEAK_KEY
                    else OUT_INOUT_ADMISSION_MANDELBROT_PROFILE
                    if typed.key != JULIA_KEY else
                    "out-inout-admission-julia-v1")
                or (typed.key == OUT_INOUT_ADMISSION_NEWTON_KEY
                    and struct_declaration_profile
                    != STRUCT_DECLARATION_NEWTON_PROFILE)
                or (typed.key == OUT_INOUT_ADMISSION_MANDELBROT_KEY
                    and (log_admission_profile
                         != LOG_ADMISSION_MANDELBROT_PROFILE
                         or mandelbrot_sequential_dz_assignment_profile
                         != MANDELBROT_SEQUENTIAL_DZ_PROFILE))
                or (typed.key == JULIA_KEY
                    and (julia_frontend_profile != JULIA_FRONTEND_PROFILE
                         or struct_declaration_profile
                         != "struct-declaration-julia-v1"))
                or numeric_literal_contract != "glsl-f32"
                or any(item is not None for item in collisions)):
            raise GeneratorError(
                f"{typed.key}: out/inout admission profile metadata mismatch")
        try:
            out_proof = authenticate_out_inout_admission(
                typed, source_hash, out_inout_admission_profile)
            if typed.key == JULIA_KEY:
                authorized_out_inout_parameters = tuple(
                    item for item in out_proof.consumed_objects
                    if getattr(item, "direction", None) == "out")
                authorized_out_inout_calls = tuple(
                    item for item in out_proof.consumed_objects
                    if getattr(item, "kind", None) == "call")
            else:
                (authorized_out_inout_parameters,
                 authorized_out_inout_calls) = out_proof
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in OUT_INOUT_ADMISSION_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact out/inout admission profile carrier required")
    authorized_struct_declaration = None
    authorized_struct_constructors: tuple[object, ...] = ()
    authorized_struct_members: tuple[object, ...] = ()
    authorized_struct_type = None
    authorized_historic_palette_proof = None
    authorized_palette_frontend_proof = None
    authorized_color_lab_frontend_proof = None
    authorized_color_lab_indexes: tuple[TypedExpression, ...] = ()
    authorized_historic_members: tuple[TypedExpression, ...] = ()
    authorized_palette_members: tuple[TypedExpression, ...] = ()
    visited_historic_members: list[TypedExpression] = []
    visited_palette_members: list[TypedExpression] = []
    visited_historic_indexes: list[TypedExpression] = []
    visited_palette_indexes: list[TypedExpression] = []
    visited_color_lab_indexes: list[TypedExpression] = []
    authorized_median_array_declarations: tuple[TypedExpression, ...] = ()
    authorized_median_array_indexes: tuple[TypedExpression, ...] = ()
    visited_median_array_declarations: list[TypedExpression] = []
    visited_median_array_indexes: list[TypedExpression] = []
    visited_median_whiles: list[TypedStatement] = []
    authorized_newton_roots_declaration = None
    authorized_newton_root_indexes: tuple[TypedExpression, ...] = ()
    authorized_newton_logs: tuple[TypedExpression, ...] = ()
    visited_newton_root_indexes: list[TypedExpression] = []
    visited_newton_logs: list[TypedExpression] = []
    if historic_palette_profile is not None:
        if (typed.key != "filter/historicPalette:historicPalette"
                or historic_palette_profile != HISTORIC_PALETTE_PROFILE):
            raise GeneratorError(f"{typed.key}: Historic Palette profile metadata mismatch")
        try:
            authorized_historic_palette_proof = authenticate_historic_palette(
                typed, source_hash, historic_palette_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == "filter/historicPalette:historicPalette":
        raise GeneratorError(f"{typed.key}: exact Historic Palette profile carrier required")
    if palette_frontend_profile is not None:
        if (typed.key != "filter/palette:palette"
                or palette_frontend_profile != PALETTE_FRONTEND_PROFILE):
            raise GeneratorError(f"{typed.key}: Palette profile metadata mismatch")
        try:
            authorized_palette_frontend_proof = authenticate_palette_frontend(
                typed, source_hash, palette_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == "filter/palette:palette":
        raise GeneratorError(f"{typed.key}: exact Palette profile carrier required")
    if color_lab_frontend_profile is not None:
        if (typed.key != COLOR_LAB_KEY
                or color_lab_frontend_profile != COLOR_LAB_FRONTEND_PROFILE):
            raise GeneratorError(
                f"{typed.key}: ColorLab frontend profile metadata mismatch")
        try:
            authorized_color_lab_frontend_proof = (
                authenticate_color_lab_frontend(
                    typed, source_hash, color_lab_frontend_profile))
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_color_lab_indexes = (
            authorized_color_lab_frontend_proof.index_nodes)
    elif typed.key == COLOR_LAB_KEY:
        raise GeneratorError(
            f"{typed.key}: exact ColorLab frontend profile carrier required")
    if authorized_median_frontend_proof is not None:
        authorized_median_array_declarations = (
            authorized_median_frontend_proof.array_declarations)
        authorized_median_array_indexes = (
            authorized_median_frontend_proof.array_indexes)
    if struct_declaration_profile is not None:
        if (typed.key not in STRUCT_DECLARATION_KEYS
                or struct_declaration_profile
                != ("struct-declaration-julia-v1" if typed.key == JULIA_KEY
                    else STRUCT_DECLARATION_NEWTON_PROFILE)
                or out_inout_admission_profile
                != ("out-inout-admission-julia-v1" if typed.key == JULIA_KEY
                    else OUT_INOUT_ADMISSION_NEWTON_PROFILE)
                or (typed.key == JULIA_KEY
                    and julia_frontend_profile != JULIA_FRONTEND_PROFILE)
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(
                f"{typed.key}: struct declaration profile metadata mismatch")
        try:
            struct_proof = authenticate_struct_declaration(
                typed, source_hash, struct_declaration_profile)
            if typed.key == JULIA_KEY:
                authorized_struct_declaration = typed.structs[0]
                authorized_struct_constructors = tuple(
                    item for item in struct_proof.consumed_objects
                    if getattr(item, "kind", None) == "declaration"
                    and getattr(item, "type", None).display() == "JuliaResult")
                authorized_struct_members = tuple(
                    item for item in struct_proof.consumed_objects
                    if getattr(item, "kind", None) == "member")
            else:
                (authorized_struct_declaration,
                 authorized_struct_constructors,
                 authorized_struct_members) = struct_proof
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_struct_type = authorized_struct_declaration.type
        def newton_expressions(value):
            yield value
            for child in value.children:
                yield from newton_expressions(child)
        def newton_statements(value):
            for expression_value in value.expressions:
                yield from newton_expressions(expression_value)
            for child in value.children:
                yield from newton_statements(child)
        candidates = tuple(
            value for function in typed.functions if function.name == "main"
            for statement_value in function.body
            for value in newton_statements(statement_value)
            if value.kind == "declaration"
            and value.symbol is not None and value.symbol.name == "roots")
        if typed.key != STRUCT_DECLARATION_NEWTON_KEY:
            candidates = (None,)
        if (typed.key == STRUCT_DECLARATION_NEWTON_KEY
                and (len(candidates) != 1
                or candidates[0].type.display() != "vec2[8]"
                or candidates[0].symbol.id != 108)):
            raise GeneratorError(
                f"{typed.key}: Newton roots declaration identity mismatch")
        authorized_newton_roots_declaration = candidates[0]
        nodes = tuple(
            value for function in typed.functions
            for statement_value in function.body
            for value in newton_statements(statement_value))
        authorized_newton_root_indexes = tuple(
            value for value in nodes if value.kind == "index"
            and value.children and value.children[0].kind == "id"
            and value.children[0].symbol_id == 108)
        authorized_newton_logs = tuple(
            value for value in nodes
            if value.kind == "builtin" and value.callee in {"log", "log2"})
        if (typed.key == STRUCT_DECLARATION_NEWTON_KEY
                and (tuple((item.span.start_line, item.span.start_column,
                   item.span.end_line, item.span.end_column)
                  for item in authorized_newton_root_indexes)
                != ((208, 9, 208, 17), (272, 29, 272, 37),
                    (273, 29, 273, 37))
                or tuple((item.span.start_line, item.span.start_column,
                          item.span.end_line, item.span.end_column,
                          item.callee) for item in authorized_newton_logs)
                != ((290, 29, 290, 69, "log2"),
                    (290, 34, 290, 51, "log"),
                    (290, 54, 290, 68, "log")))):
            raise GeneratorError(
                f"{typed.key}: Newton lowering identity mismatch")
    elif typed.key in STRUCT_DECLARATION_KEYS and typed.key != JULIA_KEY:
        raise GeneratorError(
            f"{typed.key}: exact struct declaration profile carrier required")
    authorized_round = None
    authorized_smooth_edge_luma_weights_declaration = None
    authorized_grade_luma_weights_declaration = None
    authorized_grade_index_sites: tuple[TypedExpression, ...] = ()
    visited_grade_index_sites: list[TypedExpression] = []
    authorized_linear_srgb_lane_index_sites: tuple[TypedExpression, ...] = ()
    visited_linear_srgb_lane_index_sites: list[TypedExpression] = []
    authorized_fractal_frontend_indexes: tuple[TypedExpression, ...] = ()
    visited_fractal_frontend_indexes: list[TypedExpression] = []
    authorized_fractal_mat2_constructor = None
    if authorized_fractal_frontend_proof is not None:
        authorized_fractal_frontend_indexes = (
            authorized_fractal_frontend_proof.linear_srgb_indexes)
        authorized_fractal_mat2_constructor = (
            authorized_fractal_frontend_proof.matrix_constructor)
    authorized_reflect_node = None
    authorized_distortion_reflect_node = None
    visited_reflect_nodes: list[TypedExpression] = []
    visited_distortion_reflect_nodes: list[TypedExpression] = []
    authorized_perlin_scalar_uint_xors: tuple[TypedExpression, ...] = ()
    visited_perlin_scalar_uint_xors: list[TypedExpression] = []
    authorized_scalar_uint_xors: tuple[TypedExpression, ...] = ()
    visited_scalar_uint_xors: list[TypedExpression] = []
    authorized_bitwise_scalar_int_ops_sites: tuple[TypedExpression, ...] = ()
    visited_bitwise_scalar_int_ops_sites: list[TypedExpression] = []
    authorized_bitwise_number_proof = None
    visited_bitwise_number_objects: list[object] = []
    authorized_bit_effects_proof = None
    authorized_bit_effects_nodes: tuple[TypedExpression, ...] = ()
    visited_bit_effects_nodes: list[TypedExpression] = []
    visited_bit_effects_globals: list[object] = []
    authorized_rotate_helper = None
    authorized_rotate_expressions: tuple[TypedExpression, ...] = ()
    visited_rotate_expressions: list[TypedExpression] = []
    authorized_focus_blur_proof = None
    authorized_extrude_proof = None
    authorized_edge_proof = None
    authorized_edge_splat_proof = None
    authorized_glitch_proof = None
    authorized_emboss_proof = None
    authorized_shape_mixer_proof = None
    candidate_shape_mixer_guards: tuple[TypedExpression, ...] = ()
    visited_shape_mixer_exceptional: list[TypedExpression] = []
    visited_shape_mixer_guards: list[TypedExpression] = []
    authorized_caustic_proof = None
    authorized_curl_proof = None
    authorized_curl_mod_nodes: tuple[TypedExpression, ...] = ()
    authorized_curl_tanh = None
    visited_curl_nodes: list[TypedExpression] = []
    authorized_derivative_proof = None
    authorized_distortion_derivative_nodes: tuple[TypedExpression, ...] = ()
    authorized_distortion_sampler_parameters: tuple[object, ...] = ()
    authorized_distortion_sampler_actuals: tuple[TypedExpression, ...] = ()
    if authorized_distortion_frontend_proof is not None:
        authorized_distortion_sampler_parameters = (
            authorized_distortion_frontend_proof.sampler_parameter_nodes)
        authorized_distortion_sampler_actuals = (
            authorized_distortion_frontend_proof.sampler_actual_nodes)
        authorized_distortion_derivative_nodes = (
            authorized_distortion_frontend_proof.derivative_nodes)
        authorized_distortion_reflect_node = (
            authorized_distortion_frontend_proof.reflect_node)
    authorized_caustic_scalar_uint_xors: tuple[TypedExpression, ...] = ()
    visited_caustic_scalar_uint_xors: list[TypedExpression] = []
    authorized_caustic_ingress = None
    visited_caustic_ingress: list[TypedExpression] = []
    authorized_scanline_error_ingresses: tuple[TypedExpression, ...] = ()
    visited_scanline_error_ingresses: list[TypedExpression] = []
    authorized_shapes_float_bits_ingresses: tuple[TypedExpression, ...] = ()
    authorized_grime_float_bits_ingresses: tuple[TypedExpression, ...] = ()
    visited_shapes_float_bits_ingresses: list[TypedExpression] = []
    visited_grime_float_bits_ingresses: list[TypedExpression] = []
    authorized_kaleido_float_bits_ingress: tuple[TypedExpression, ...] = ()
    visited_kaleido_float_bits_ingress: list[TypedExpression] = []
    authorized_noise_float_bits_ingress: tuple[TypedExpression, ...] = ()
    visited_noise_float_bits_ingress: list[TypedExpression] = []
    authorized_shapes_rvalue_assigns: tuple[TypedExpression, ...] = ()
    visited_shapes_rvalue_assigns: list[TypedExpression] = []
    authorized_mutable_global_frames: tuple[object, ...] = ()
    # Two ledgers because there are two independent gates (design S2.3 items 1
    # and 2). Each authenticated declaration must be consumed exactly once at
    # each, by object identity, in the frozen order.
    visited_mutable_global_frame_admissions: list[object] = []
    visited_mutable_global_frame_storage: list[object] = []
    authorized_mutable_global_arrays: tuple[object, ...] = ()
    # Three ledgers because there are three independent gates the five
    # authenticated declarations must pass: `reject_type`'s array arm (the
    # five are `float[9]`, a type the const frame never needed), the
    # `admitted_globals` admission loop, and the post-loop storage gate. Each
    # declaration is consumed exactly once at each, by object identity, in the
    # frozen declaration order.
    visited_mutable_global_array_admissions: list[object] = []
    visited_mutable_global_array_types: list[object] = []
    visited_mutable_global_array_storage: list[object] = []
    # The 45 authenticated element stores, as (symbol id, index) pairs. The
    # closure's own locks already froze the exact (base, index, value) triples
    # node by node; this ledger is the walk-side proof that the validator
    # visited exactly those stores and nothing else -- the write-only census
    # restated at the consuming side.
    visited_mutable_global_array_stores: list[tuple[int, int]] = []
    authorized_const_global_tables: tuple[object, ...] = ()
    authorized_dither_globals: tuple[object, ...] = (
        tuple(item for item in typed.declarations
              if item.symbol.storage == "const")
        if authorized_dither_frontend_proof is not None else ())
    authorized_dither_arrays: tuple[object, ...] = (
        tuple(item.node for item in authorized_dither_frontend_proof.array_records)
        + tuple(item.node for item in authorized_dither_frontend_proof.array_parameters)
        if authorized_dither_frontend_proof is not None else ())
    authorized_dither_loops: tuple[object, ...] = (
        tuple(item.node for item in authorized_dither_frontend_proof.loop_records)
        if authorized_dither_frontend_proof is not None else ())
    authorized_dither_indexes: tuple[object, ...] = (
        tuple(item.node for item in authorized_dither_frontend_proof.index_records)
        if authorized_dither_frontend_proof is not None else ())
    authorized_dither_bitwise: tuple[object, ...] = (
        tuple(item.node for item in authorized_dither_frontend_proof.bitwise_records)
        if authorized_dither_frontend_proof is not None else ())
    visited_dither_indexes: list[object] = []
    authorized_testpattern_array_declarations: tuple[object, ...] = ()
    authorized_testpattern_array_constructors: tuple[object, ...] = ()
    authorized_testpattern_global_symbol_id: int | None = None
    authorized_testpattern_shift: object | None = None
    authorized_testpattern_mask: object | None = None
    visited_testpattern_global_admissions: list[object] = []
    visited_testpattern_global_storage: list[object] = []
    visited_testpattern_array_types: list[object] = []
    visited_testpattern_array_constructors: list[object] = []
    visited_testpattern_indexes: list[TypedExpression] = []
    visited_testpattern_round_nodes: list[TypedExpression] = []
    visited_testpattern_dynamic_loops: list[TypedStatement] = []
    visited_testpattern_shifts: list[TypedExpression] = []
    visited_testpattern_masks: list[TypedExpression] = []
    authorized_remap_data_declaration = None
    authorized_remap_indexes: tuple[TypedExpression, ...] = ()
    authorized_remap_loops: tuple[object, ...] = ()
    visited_remap_indexes: list[TypedExpression] = []
    visited_remap_loops: list[TypedStatement] = []
    visited_remap_uniform_blocks: list[object] = []
    if remap_frontend_proof is not None:
        if (typed.key != REMAP_KEY
                or getattr(remap_frontend_proof, "program_key", None)
                != typed.key):
            raise GeneratorError(f"{typed.key}: Remap frontend proof key mismatch")
        authorized_remap_indexes = tuple(item.node for item in remap_frontend_proof.indexes)
        authorized_remap_loops = tuple(item.proof for item in remap_frontend_proof.loops)
        authorized_remap_data_declaration = next(
            (item for item in typed.declarations
             if item.symbol.name == remap_frontend_proof.data_field.name
             and item.type.display() == remap_frontend_proof.data_field.type.display()),
            None)
        if authorized_remap_data_declaration is None:
            raise GeneratorError(f"{typed.key}: Remap data declaration identity mismatch")
    elif typed.key == REMAP_KEY:
        raise GeneratorError(f"{typed.key}: exact Remap frontend proof carrier required")
    authorized_varyings: tuple[object, ...] = ()
    authorized_texture_frontend_nodes: tuple[TypedExpression, ...] = ()
    visited_texture_frontend_nodes: list[TypedExpression] = []
    authorized_texture_frontend_assignments: tuple[TypedExpression, ...] = ()
    visited_texture_frontend_assignments: list[TypedExpression] = []
    authorized_texture_frontend_inverse_sqrt = None
    visited_texture_frontend_inverse_sqrt: list[TypedExpression] = []
    # The two authenticated textureLod call SITES, carrying the live nodes --
    # the walk admits `value is site.node`, the same node-identity idiom as
    # the curl-tanh arm -- and the ledger proving each was visited exactly
    # once (audited after the walk).
    authorized_texture_lod_sites: tuple[object, ...] = ()
    visited_texture_lod_sites: list[TypedExpression] = []
    # One ledger for the one independent gate the authenticated varying
    # symbols must pass (the `interface_symbols` gate): each authenticated
    # symbol consumed exactly once there, by object identity, in the frozen
    # order. Nothing else in the validator consults `interface_symbols` --
    # the `id` nodes referencing the symbol resolve through `body_globals`
    # and pass the expression gates on their own.
    visited_varying_admissions: list[object] = []
    # The authenticated `TABLE[i]` read SITES, carrying the live nodes. The
    # index arm admits `value is item.node`, the same node-identity idiom as
    # `authorized_grade_index_sites`.
    authorized_const_global_table_reads: tuple[object, ...] = ()
    const_global_tables: tuple[object, ...] = ()
    # Three ledgers because there are three independent gates the three
    # authenticated declarations must pass: the `admitted_globals` admission
    # loop, `reject_type`'s array arm, and the post-loop storage gate. Each
    # declaration is consumed exactly once at each, by object identity, in the
    # frozen declaration order. A gate that silently stops consuming is what
    # these exist to name.
    visited_const_global_table_admissions: list[object] = []
    visited_const_global_table_types: list[object] = []
    visited_const_global_table_storage: list[object] = []
    # One entry per authenticated `TABLE[i]` read reached by `expression()`.
    visited_const_global_table_reads: list[TypedExpression] = []
    authorized_glyph_map_sites: tuple[TypedExpression, ...] = ()
    visited_glyph_map_sites: list[TypedExpression] = []
    authorized_extrude_relationals: tuple[TypedExpression, ...] = ()
    authorized_extrude_reductions: tuple[TypedExpression, ...] = ()
    visited_extrude_nodes: list[TypedExpression] = []
    visited_edge_bvec_nodes: list[TypedExpression] = []
    visited_edge_relationals: list[TypedExpression] = []
    visited_edge_swizzles: list[TypedExpression] = []
    visited_edge_splat_expressions: list[TypedExpression] = []
    visited_edge_splat_statements: list[TypedStatement] = []
    visited_glitch_matrix_objects: list[TypedExpression] = []
    visited_emboss_declarations: list[TypedExpression] = []
    visited_emboss_stores: list[TypedExpression] = []
    visited_emboss_reads: list[TypedExpression] = []
    visited_emboss_equalities: list[TypedExpression] = []
    visited_emboss_reductions: list[TypedExpression] = []
    visited_emboss_materialization_divisions: list[TypedExpression] = []
    authorized_posterize_round = None
    authorized_as_u32_round = None
    authorized_ceil = ()
    authorized_waves_relationals: tuple[TypedExpression, ...] = ()
    authorized_waves_reductions: tuple[TypedExpression, ...] = ()
    visited_waves_nodes: list[TypedExpression] = []
    authorized_inout_vec3_swap_proof = None
    visited_inout_vec3_swap_calls: list[TypedExpression] = []
    visited_out_inout_parameters: list[object] = []
    visited_out_inout_calls: list[TypedExpression] = []
    authorized_osd_proof = None
    authorized_osd_nodes: tuple[TypedExpression, ...] = ()
    visited_osd_nodes: list[TypedExpression] = []
    visited_osd_indexes: list[TypedExpression] = []
    visited_osd_globals: list[object] = []
    authorized_spooky_ticker_proof = None
    authorized_spooky_ticker_nodes: tuple[TypedExpression, ...] = ()
    authorized_spooky_ticker_index = None
    authorized_spooky_ticker_varying_reads: tuple[TypedExpression, ...] = ()
    authorized_spooky_ticker_global = None
    authorized_spooky_ticker_constructor = None
    visited_spooky_ticker_nodes: list[TypedExpression] = []
    visited_spooky_ticker_indexes: list[TypedExpression] = []
    visited_spooky_ticker_globals: list[object] = []
    visited_spooky_ticker_varying_reads: list[TypedExpression] = []
    if moodscape_frontend_profile is not None:
        if (typed.key not in MOODSCAPE_PREPARED_KEYS
                or moodscape_frontend_profile
                != MOODSCAPE_PREPARED_PROFILES[typed.key]
                or numeric_literal_contract != "glsl-f32"
                or any(item is not None for item in (
                    compatibility_transform, custom_comparer_profile,
                    source_global_literal_int_profile, runtime_loop_bound_profile,
                    gabor_effective_depth_profile, gather_sorted_round_profile,
                    literal_vec3_lane_index_profile, smooth_edge_luma_weights_profile,
                    perlin_scalar_uint_xor_profile, scalar_uint_xor_profile,
                    bitwise_scalar_int_ops_profile, bit_effects_frontend_profile,
                    osd_frontend_profile, spooky_ticker_frontend_profile,
                    texture_lod_admission_profile, varying_profile,
                    texture_frontend_profile, median_frontend_profile))):
            raise GeneratorError(
                f"{typed.key}: Moodscape frontend profile metadata mismatch")
        try:
            authenticate_moodscape_projection(
                typed, source_hash, moodscape_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in MOODSCAPE_PREPARED_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact Moodscape frontend profile carrier required")
    if noise_frontend_profile is not None:
        if (typed.key != NOISE_FRONTEND_KEY
                or noise_frontend_profile != NOISE_FRONTEND_PROFILE
                or numeric_literal_contract != "glsl-f32"
                or any(item is not None for item in (
                    compatibility_transform, custom_comparer_profile,
                    source_global_literal_int_profile, runtime_loop_bound_profile,
                    gabor_effective_depth_profile, gather_sorted_round_profile,
                    literal_vec3_lane_index_profile, smooth_edge_luma_weights_profile,
                    perlin_scalar_uint_xor_profile, scalar_uint_xor_profile,
                    bitwise_scalar_int_ops_profile, bit_effects_frontend_profile,
                    osd_frontend_profile, moodscape_frontend_profile,
                    spooky_ticker_frontend_profile, texture_lod_admission_profile,
                    varying_profile, texture_frontend_profile, median_frontend_profile))):
            raise GeneratorError(
                f"{typed.key}: Classic Noise frontend profile metadata mismatch")
        if any(name.endswith("_profile")
               and name != "noise_frontend_profile"
               and value is not None
               for name, value in locals().items()):
            raise GeneratorError(
                f"{typed.key}: Classic Noise frontend profile metadata mismatch")
        try:
            authenticate_noise_projection(
                typed, source_hash, noise_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == NOISE_FRONTEND_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Classic Noise frontend profile carrier required")
    authorized_texture_frontend_proof = None
    if osd_frontend_profile is not None:
        if (typed.key not in OSD_PREPARED_KEYS
                or osd_frontend_profile != OSD_PREPARED_PROFILES[typed.key]
                or numeric_literal_contract != "glsl-f32"
                or any(item is not None for item in (
                    compatibility_transform, custom_comparer_profile,
                    source_global_literal_int_profile, runtime_loop_bound_profile,
                    gabor_effective_depth_profile, gather_sorted_round_profile,
                    literal_vec3_lane_index_profile, smooth_edge_luma_weights_profile,
                    perlin_scalar_uint_xor_profile, scalar_uint_xor_profile,
                    bitwise_scalar_int_ops_profile, bit_effects_frontend_profile,
                    testpattern_frontend_proof, remap_frontend_proof))):
            raise GeneratorError(f"{typed.key}: OSD frontend profile metadata mismatch")
        try:
            authorized_osd_proof = authenticate_osd_frontend(
                typed, source_hash, osd_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_osd_nodes = authorized_osd_proof.bitwise_nodes
    elif typed.key in OSD_PREPARED_KEYS:
        raise GeneratorError(f"{typed.key}: exact OSD frontend profile carrier required")
    if texture_frontend_profile is not None:
        if (typed.key != TEXTURE_FRONTEND_KEY
                or texture_frontend_profile != TEXTURE_FRONTEND_PROFILE
                or numeric_literal_contract != "glsl-f32"
                or any(item is not None for item in (
                    compatibility_transform, custom_comparer_profile,
                    source_global_literal_int_profile, runtime_loop_bound_profile,
                    gabor_effective_depth_profile, gather_sorted_round_profile,
                    literal_vec3_lane_index_profile, smooth_edge_luma_weights_profile,
                    perlin_scalar_uint_xor_profile, scalar_uint_xor_profile,
                    bitwise_scalar_int_ops_profile, bit_effects_frontend_profile,
                    varying_profile, osd_frontend_profile,
                    spooky_ticker_frontend_profile, texture_lod_admission_profile,
                    median_frontend_profile))):
            raise GeneratorError(
                f"{typed.key}: Texture frontend profile metadata mismatch")
        try:
            authorized_texture_frontend_proof = authenticate_texture_frontend(
                typed, source_hash, texture_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_varyings = (authorized_texture_frontend_proof.consumed_objects[0],)
        authorized_texture_frontend_nodes = (
            authorized_texture_frontend_proof.bitwise_nodes)
        authorized_texture_frontend_assignments = (
            authorized_texture_frontend_proof.bitwise_assignments)
        authorized_texture_frontend_inverse_sqrt = (
            authorized_texture_frontend_proof.inverse_sqrt)
    elif typed.key == TEXTURE_FRONTEND_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Texture frontend profile carrier required")
    if spooky_ticker_frontend_profile is not None:
        if (typed.key not in SPOOKY_TICKER_PREPARED_KEYS
                or spooky_ticker_frontend_profile
                != SPOOKY_TICKER_PREPARED_PROFILES[typed.key]
                or numeric_literal_contract != "glsl-f32"
                or any(item is not None for item in (
                    compatibility_transform, custom_comparer_profile,
                    source_global_literal_int_profile, runtime_loop_bound_profile,
                    gabor_effective_depth_profile, gather_sorted_round_profile,
                    literal_vec3_lane_index_profile, smooth_edge_luma_weights_profile,
                    perlin_scalar_uint_xor_profile, scalar_uint_xor_profile,
                    bitwise_scalar_int_ops_profile, bit_effects_frontend_profile,
                    osd_frontend_profile, varying_profile,
                    texture_lod_admission_profile))):
            raise GeneratorError(
                f"{typed.key}: SpookyTicker frontend profile metadata mismatch")
        try:
            authorized_spooky_ticker_proof = authenticate_spooky_ticker_frontend(
                typed, source_hash, spooky_ticker_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_spooky_ticker_nodes = (
            authorized_spooky_ticker_proof.bitwise_nodes)
        authorized_spooky_ticker_index = (
            authorized_spooky_ticker_proof.array_index)
        authorized_spooky_ticker_varying_reads = (
            tuple(item.node for item in
                  authorized_spooky_ticker_proof.varying_reads))
        authorized_varyings = (authorized_spooky_ticker_proof.varying_symbol,)
        authorized_spooky_ticker_global = next(
            (item for item in typed.declarations
             if item.symbol is not None
             and item.symbol.id == authorized_spooky_ticker_proof.global_array.symbol_id),
            None)
        authorized_spooky_ticker_constructor = (
            authorized_spooky_ticker_global.initializer
            if authorized_spooky_ticker_global is not None else None)
        if (authorized_spooky_ticker_global is None
                or authorized_spooky_ticker_constructor is None):
            raise GeneratorError(
                f"{typed.key}: SpookyTicker GLYPHS declaration identity mismatch")
    elif typed.key in SPOOKY_TICKER_PREPARED_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact SpookyTicker frontend profile carrier required")
    if testpattern_frontend_proof is not None:
        if (typed.key != TESTPATTERN_KEY
                or getattr(testpattern_frontend_proof, "program_key", None)
                != typed.key):
            raise GeneratorError(
                f"{typed.key}: Test Pattern frontend proof key mismatch")
        authorized_testpattern_global_symbol_id = (
            testpattern_frontend_proof.global_array.symbol_id)
        authorized_testpattern_array_declarations = tuple(
            item for item in testpattern_frontend_proof.consumed_objects
            if getattr(getattr(item, "type", None), "kind", None) == "array"
            and (getattr(item, "kind", None) == "declaration"
                 or getattr(getattr(item, "symbol", None), "id", None)
                 == testpattern_frontend_proof.global_array.symbol_id))
        authorized_testpattern_array_constructors = tuple(
            item for item in testpattern_frontend_proof.consumed_objects
            if getattr(item, "kind", None) == "construct"
            and getattr(getattr(item, "type", None), "kind", None) == "array")
        glyph_index = testpattern_frontend_proof.dynamic_indexes[0].node
        testpattern_nodes: list[TypedExpression] = []
        def collect_testpattern_nodes(value):
            testpattern_nodes.append(value)
            for child in value.children:
                collect_testpattern_nodes(child)
        sample = next(function for function in typed.functions
                      if function.signature.id == 30
                      and function.name == "sampleGlyph")
        for statement_value in sample.body:
            for expression_value in statement_value.expressions:
                collect_testpattern_nodes(expression_value)
        shifts = tuple(value for value in testpattern_nodes
                       if value.kind == "binary" and value.operator == ">>"
                       and len(value.children) == 2
                       and value.children[0] is glyph_index)
        masks = tuple(value for value in testpattern_nodes
                      if value.kind == "binary" and value.operator == "&"
                      and len(value.children) == 2
                      and value.children[0] in shifts)
        if len(shifts) != 1 or len(masks) != 1:
            raise GeneratorError(
                f"{typed.key}: authenticated Test Pattern bitwise census mismatch")
        authorized_testpattern_shift, authorized_testpattern_mask = shifts[0], masks[0]
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
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
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
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
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
    if edge_bvec3_contour_profile is not None:
        collisions = (
            compatibility_transform, custom_comparer_profile,
            source_global_literal_int_profile, runtime_loop_bound_profile,
            gabor_effective_depth_profile, gather_sorted_round_profile,
            literal_vec3_lane_index_profile, smooth_edge_luma_weights_profile,
            perlin_scalar_uint_xor_profile, scalar_uint_xor_profile,
            bitwise_scalar_int_ops_profile, rotate_mat2_return_profile,
            focus_blur_borrowed_sampler_profile,
            extrude_bvec2_relational_reduction_profile,
            caustic_word_hash_profile,
            scanline_error_float_bits_ingress_profile,
            shapes_float_bits_ingress_profile,
            grime_float_bits_ingress_profile,
            shapes_rvalue_assign_profile,
            glyph_map_nonnegative_int_shift_profile, curl_vector_math_profile,
            grade_luma_weights_profile, grade_index_expression_profile,
            derivative_admission_profile, linear_srgb_lane_index_profile,
            reflect_admission_profile, posterize_round_profile,
            as_u32_round_profile, ceil_admission_profile,
            waves_any_notequal_profile, inout_vec3_swap_profile,
            glitch_mat4_chain_profile, emboss_color_style_profile,
        )
        if (typed.key != EDGE_KEY or numeric_literal_contract != "glsl-f32"
                or any(item is not None for item in collisions)):
            raise GeneratorError(
                f"{typed.key}: Edge bvec3 contour profile metadata mismatch")
        try:
            authorized_edge_proof = authenticate_edge_bvec3_contour(
                typed, source_hash, edge_bvec3_contour_profile)
            authorized_edge_splat_proof = authenticate_edge_center_splat(
                typed, source_hash, edge_bvec3_contour_profile)
            proof = authorized_edge_proof
            splat = authorized_edge_splat_proof
            if (proof._candidate is not typed
                    or not isinstance(proof.bvec_nodes, tuple)
                    or len(proof.bvec_nodes) != 12
                    or not isinstance(proof.relationals, tuple)
                    or proof.relationals != (
                        proof.bvec_nodes[2], proof.bvec_nodes[3])
                    or not isinstance(proof.declarations, tuple)
                    or proof.declarations != (
                        proof.bvec_nodes[0], proof.bvec_nodes[4])
                    or proof.constructor is not proof.bvec_nodes[5]
                    or proof.declarations[1].children[0] is not proof.constructor
                    or not isinstance(proof.id_reads, tuple)
                    or proof.id_reads != proof.bvec_nodes[6:12]
                    or not isinstance(proof.swizzles, tuple)
                    or len(proof.swizzles) != 6
                    or any(swizzle.children[0] is not read
                           for swizzle, read in zip(
                               proof.swizzles, proof.id_reads))
                    or len(proof.consumed_objects) != 22
                    or len({id(item) for item in proof.consumed_objects}) != 22
                    or splat._candidate is not typed
                    or len(splat.consumed_objects) != 12
                    or len({id(item) for item in splat.consumed_objects}) != 12
                    or splat.statement is not splat.statement_parent_chain[-1]
                    or splat.assignment.children != (
                        splat.target, splat.constructor)
                    or splat.constructor.children != (splat.dot,)
                    or splat.dot.children != (
                        splat.dot_target, splat.luma)):
                raise ValueError(
                    "candidate ownership, site order, uniqueness, or parent mismatch")
        except (AttributeError, IndexError, TypeError, ValueError) as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == EDGE_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Edge bvec3 contour profile carrier required")
    if glitch_mat4_chain_profile is not None:
        # Per-key since the effects row: the module is a whole-program
        # freeze per key, and effects (the first three-carrier row) names
        # its REQUIRED companions (the mutable-global array closure and the
        # ceil admission) through the module's own
        # REQUIRED_COMPANION_PROFILES -- present and exact for the mapped
        # key, still rejected for every unmapped key, so the carve fails
        # closed rather than widening (the normalMap pattern).
        glitch_companions = dict(
            GLITCH_MAT4_CHAIN_COMPANIONS.get(typed.key, ()))
        glitch_companion_row = {
            "scalar_uint_xor_profile": scalar_uint_xor_profile,
            "mutable_global_array_profile": mutable_global_array_profile,
            "ceil_admission_profile": ceil_admission_profile,
        }
        collisions = (
            compatibility_transform, custom_comparer_profile,
            source_global_literal_int_profile, runtime_loop_bound_profile,
            gabor_effective_depth_profile, gather_sorted_round_profile,
            literal_vec3_lane_index_profile, smooth_edge_luma_weights_profile,
            perlin_scalar_uint_xor_profile,
            bitwise_scalar_int_ops_profile, rotate_mat2_return_profile,
            focus_blur_borrowed_sampler_profile,
            extrude_bvec2_relational_reduction_profile,
            edge_bvec3_contour_profile, caustic_word_hash_profile,
            scanline_error_float_bits_ingress_profile,
            shapes_float_bits_ingress_profile,
            grime_float_bits_ingress_profile,
            shapes_rvalue_assign_profile,
            glyph_map_nonnegative_int_shift_profile, curl_vector_math_profile,
            grade_luma_weights_profile, grade_index_expression_profile,
            derivative_admission_profile, linear_srgb_lane_index_profile,
            reflect_admission_profile, posterize_round_profile,
            as_u32_round_profile,
            waves_any_notequal_profile, inout_vec3_swap_profile,
            emboss_color_style_profile,
        )
        # A companion's VALUE is the owning block's own authentication's
        # business (each mechanism names its own message); this block only
        # refuses companions the closure did not map -- absent companions
        # are the owning block's required-carrier elif's business.
        if (typed.key not in GLITCH_MAT4_CHAIN_KEYS
                or glitch_mat4_chain_profile
                != GLITCH_MAT4_CHAIN_PROFILES.get(typed.key)
                or numeric_literal_contract != "glsl-f32"
                or any(item is not None for item in collisions)
                or any(glitch_companion_row.get(name) is not None
                       and name not in glitch_companions
                       for name in glitch_companion_row)):
            raise GeneratorError(
                f"{typed.key}: Glitch mat4 chain profile metadata mismatch")
        try:
            authorized_glitch_proof = authenticate_glitch_mat4_chain(
                typed, source_hash, glitch_mat4_chain_profile)
            proof = authorized_glitch_proof
            if (proof._candidate is not typed
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
                    or len({id(item) for item in proof.consumed_objects}) != 14
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
                    or proof.dot.children[0] is not proof.vector_products[0]
                    or proof.return_statement.expressions != (proof.dot,)):
                raise ValueError(
                    "candidate ownership, site order, uniqueness, or parent mismatch")
            # The ordered-freq-splat re-verification is PER KEY (glitch
            # alone carries the splat; effects' proof has none, and its
            # host/dot/return identity locks live in the module record).
            if proof.ordered_freq_splat_assignment is not None:
                if (proof.ordered_freq_splat_assignment.children != (
                        proof.ordered_freq_splat_target,
                        proof.ordered_freq_splat_constructor)
                        or proof.ordered_freq_splat_assignment.operator != "*="
                        or proof.ordered_freq_splat_target.symbol_id != 75
                        or proof.ordered_freq_splat_constructor.children[0].callee
                        != "periodicFunction"):
                    raise ValueError(
                        "candidate ownership, site order, uniqueness, or parent mismatch")
        except (AttributeError, IndexError, TypeError, ValueError) as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in GLITCH_MAT4_CHAIN_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact Glitch mat4 chain profile carrier required")
    if emboss_color_style_profile is not None:
        collisions = (
            compatibility_transform, custom_comparer_profile,
            source_global_literal_int_profile, runtime_loop_bound_profile,
            gabor_effective_depth_profile, gather_sorted_round_profile,
            literal_vec3_lane_index_profile, smooth_edge_luma_weights_profile,
            perlin_scalar_uint_xor_profile, scalar_uint_xor_profile,
            bitwise_scalar_int_ops_profile, rotate_mat2_return_profile,
            focus_blur_borrowed_sampler_profile,
            extrude_bvec2_relational_reduction_profile,
            edge_bvec3_contour_profile, glitch_mat4_chain_profile,
            caustic_word_hash_profile, scanline_error_float_bits_ingress_profile,
            shapes_float_bits_ingress_profile,
            grime_float_bits_ingress_profile,
            shapes_rvalue_assign_profile,
            glyph_map_nonnegative_int_shift_profile, curl_vector_math_profile,
            grade_luma_weights_profile, grade_index_expression_profile,
            derivative_admission_profile, linear_srgb_lane_index_profile,
            reflect_admission_profile, posterize_round_profile,
            as_u32_round_profile, ceil_admission_profile,
            waves_any_notequal_profile, inout_vec3_swap_profile,
        )
        if (typed.key != EMBOSS_KEY
                or numeric_literal_contract != "glsl-f32"
                or any(item is not None for item in collisions)):
            raise GeneratorError(
                f"{typed.key}: Emboss color-style profile metadata mismatch")
        try:
            authorized_emboss_proof = authenticate_emboss_color_style(
                typed, source_hash, emboss_color_style_profile)
            proof = authorized_emboss_proof
            stores = tuple(store for table in proof.tables
                           for store in table.literal_stores)
            reads = tuple(table.dynamic_read for table in proof.tables)
            owned_ids = _program_owned_object_ids(typed)
            if (proof._candidate is not typed
                    or not isinstance(proof.tables, tuple)
                    or len(proof.tables) != 4
                    or not isinstance(proof.consumed_objects, tuple)
                    or len({id(item) for item in proof.consumed_objects})
                    != len(proof.consumed_objects)
                    or any(id(item) not in owned_ids
                           for item in proof.consumed_objects)
                    or any(table._candidate is not typed
                           or not any(table.owner is function
                                      for function in typed.functions)
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
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == EMBOSS_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Emboss color-style profile carrier required")
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
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
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
    if scanline_error_float_bits_ingress_profile is not None:
        if (typed.key != SCANLINE_ERROR_KEY
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or runtime_loop_bound_profile is not None
                or gabor_effective_depth_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or as_u32_round_profile is not None
                or ceil_admission_profile is not None
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Scanline Error float-bit ingress profile metadata mismatch")
        try:
            authorized_scanline_error_ingresses = (
                authenticate_scanline_error_float_bits_ingress(
                    typed, source_hash,
                    scanline_error_float_bits_ingress_profile).ingresses)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == SCANLINE_ERROR_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Scanline Error float-bit ingress profile carrier required")
    if shapes_float_bits_ingress_profile is not None:
        # Shapes is the first program admitted by three carriers at once, so
        # unlike every earlier block this one does NOT demand that its two
        # companions be absent -- it demands that they be present and exact.
        # The reused scalar-XOR carrier authenticates the three `uint ^ uint`
        # sites this ingress feeds; the shared linear-sRGB carrier
        # authenticates the five `linearToSrgb` lane indexes. A partially
        # composed row (any one of the three missing, or a companion carrying
        # some other program's profile string) fails closed here, and the
        # symmetric `elif` arms of the other two blocks fail closed when this
        # one is the missing member.
        if (typed.key not in SHAPES_FLOAT_BITS_INGRESS_KEYS
                or scalar_uint_xor_profile != SCALAR_UINT_XOR_PROFILE
                or linear_srgb_lane_index_profile
                != LINEAR_SRGB_LANE_INDEX_PROFILES.get(typed.key)
                or shapes_rvalue_assign_profile != SHAPES_RVALUE_ASSIGN_PROFILE
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or runtime_loop_bound_profile is not None
                or gabor_effective_depth_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or edge_bvec3_contour_profile is not None
                or glitch_mat4_chain_profile is not None
                or emboss_color_style_profile is not None
                or shape_mixer_builtin_profile is not None
                or caustic_word_hash_profile is not None
                or scanline_error_float_bits_ingress_profile is not None
                or glyph_map_nonnegative_int_shift_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or as_u32_round_profile is not None
                or ceil_admission_profile is not None
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Shapes float-bit ingress profile metadata mismatch")
        try:
            authorized_shapes_float_bits_ingresses = (
                authenticate_shapes_float_bits_ingress(
                    typed, source_hash, shapes_float_bits_ingress_profile))
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in SHAPES_FLOAT_BITS_INGRESS_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact Shapes float-bit ingress profile carrier required")
    if grime_float_bits_ingress_profile is not None:
        # grime's ingress rides its varying carrier: the row carries both and
        # neither stands alone, so this arm requires the companion present and
        # exact rather than absent -- the Shapes discipline, one companion.
        if (typed.key not in GRIME_FLOAT_BITS_INGRESS_KEYS
                or grime_float_bits_ingress_profile
                != GRIME_FLOAT_BITS_INGRESS_PROFILE
                or varying_profile != VARYING_UV_PROFILES.get(typed.key)):
            raise GeneratorError(
                f"{typed.key}: grime float-bit ingress profile metadata mismatch")
        try:
            authorized_grime_float_bits_ingresses = (
                authenticate_grime_float_bits_ingress(
                    typed, source_hash, grime_float_bits_ingress_profile))
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in GRIME_FLOAT_BITS_INGRESS_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact grime float-bit ingress profile carrier required")
    if shapes_rvalue_assign_profile is not None:
        # Design amendment 2 (§12). The fourth Shapes carrier, and the only
        # one that widens an EMITTER boundary rather than a validator one:
        # `assign` is already in APPROVED_CAPABILITIES and `*=` already in
        # APPROVED_ASSIGNMENT_OPERATORS, which is exactly why the validator
        # accepted this program while the emitter's expression dispatcher
        # gapped on it. Nothing is added to either frozen vocabulary here.
        # Like the ingress block above, this one requires its companions to be
        # present and exact rather than absent.
        if (typed.key not in SHAPES_RVALUE_ASSIGN_KEYS
                or scalar_uint_xor_profile != SCALAR_UINT_XOR_PROFILE
                or linear_srgb_lane_index_profile
                != LINEAR_SRGB_LANE_INDEX_PROFILES.get(typed.key)
                or shapes_float_bits_ingress_profile
                != SHAPES_FLOAT_BITS_INGRESS_PROFILE
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or runtime_loop_bound_profile is not None
                or gabor_effective_depth_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or edge_bvec3_contour_profile is not None
                or glitch_mat4_chain_profile is not None
                or emboss_color_style_profile is not None
                or shape_mixer_builtin_profile is not None
                or caustic_word_hash_profile is not None
                or scanline_error_float_bits_ingress_profile is not None
                or glyph_map_nonnegative_int_shift_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or as_u32_round_profile is not None
                or ceil_admission_profile is not None
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Shapes rvalue-assign profile metadata mismatch")
        try:
            authorized_shapes_rvalue_assigns = (
                authenticate_shapes_rvalue_assign(
                    typed, source_hash, shapes_rvalue_assign_profile))
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in SHAPES_RVALUE_ASSIGN_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact Shapes rvalue-assign profile carrier required")
    if glyph_map_nonnegative_int_shift_profile is not None:
        if (typed.key != GLYPH_MAP_KEY
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or runtime_loop_bound_profile is not None
                or gabor_effective_depth_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or scanline_error_float_bits_ingress_profile is not None
                or shapes_float_bits_ingress_profile is not None
                or shapes_rvalue_assign_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or as_u32_round_profile is not None
                or ceil_admission_profile is not None
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Glyph Map shift profile metadata mismatch")
        try:
            proof = authenticate_glyph_map_nonnegative_int_shift(
                typed, source_hash, glyph_map_nonnegative_int_shift_profile)
            if proof._candidate is not typed:
                raise ValueError("candidate identity mismatch")
            sites = proof.sites
            if (not isinstance(sites, tuple) or len(sites) != 2
                    or sites[0] is not getattr(proof, "mask", None)
                    or sites[1] is not getattr(proof, "shift", None)
                    or sites[0] is sites[1]
                    or sites[0].kind != "binary" or sites[0].operator != "&"
                    or sites[1].kind != "binary" or sites[1].operator != ">>"
                    or len(sites[0].children) != 2
                    or sites[0].children[0] is not sites[1]):
                raise ValueError("site order, uniqueness, or parent mismatch")
            authorized_glyph_map_sites = sites
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
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
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
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
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
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
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
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
    visited_distortion_derivative_nodes: list[TypedExpression] = []
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
                or grade_index_expression_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
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
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
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
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
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
    if scalar_uint_xor_profile is not None:
        if (typed.key not in SCALAR_UINT_XOR_KEYS
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None):
            raise GeneratorError(
                f"{typed.key}: scalar uint XOR profile metadata mismatch")
        try:
            authorized_scalar_uint_xors = authenticate_scalar_uint_xor(
                typed, source_hash, scalar_uint_xor_profile)
            # kaleido's one `floatBitsToUint` lattice-hash ingress rides the
            # same carrier (the `_UINT_TO_FLOAT_CENSUS_LOCKS` precedent): a
            # per-key census, no separate row field, admitted below by
            # object identity on the Caustic/Scanline/Shapes skip-list.
            authorized_kaleido_float_bits_ingress = (
                authenticate_kaleido_float_bits_ingress(
                    typed, source_hash, scalar_uint_xor_profile)
                if typed.key == KALEIDO_FLOAT_BITS_INGRESS_KEY else ())
            authorized_noise_float_bits_ingress = (
                authenticate_noise_float_bits_ingress(
                    typed, source_hash, scalar_uint_xor_profile)
                if typed.key == NOISE_FLOAT_BITS_INGRESS_KEY else ())
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif (typed.key in SCALAR_UINT_XOR_KEYS
          and typed.key not in BIT_EFFECTS_PREPARED_KEYS):
        raise GeneratorError(
            f"{typed.key}: exact scalar uint XOR profile carrier required")
    if mutable_global_frame_profile is not None:
        # `synth/shape` is admitted by two carriers: this one and the
        # already-frozen scalar-XOR carrier, which must be PRESENT and exact
        # rather than absent. Every other profile must be absent -- the
        # collision list below is the runtime half of design S7.2 row 20, and
        # the slice-row allowlist arm in `load_slice` is the schema half.
        frame_companions = dict(
            MUTABLE_GLOBAL_FRAME_COMPANIONS.get(typed.key, ()))
        companion_row = {
            "runtime_loop_bound_profile": runtime_loop_bound_profile,
            "scalar_uint_xor_profile": scalar_uint_xor_profile,
        }
        if (typed.key not in MUTABLE_GLOBAL_FRAME_KEYS
                or mutable_global_frame_profile
                != MUTABLE_GLOBAL_FRAME_PROFILES.get(typed.key)
                or any(companion_row.get(name) != value
                       for name, value in frame_companions.items())
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or (runtime_loop_bound_profile is not None
                    and "runtime_loop_bound_profile" not in frame_companions)
                or gabor_effective_depth_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or edge_bvec3_contour_profile is not None
                or glitch_mat4_chain_profile is not None
                or emboss_color_style_profile is not None
                or shape_mixer_builtin_profile is not None
                or caustic_word_hash_profile is not None
                or scanline_error_float_bits_ingress_profile is not None
                or shapes_float_bits_ingress_profile is not None
                or shapes_rvalue_assign_profile is not None
                or glyph_map_nonnegative_int_shift_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or as_u32_round_profile is not None
                or ceil_admission_profile is not None
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None
                or mutable_global_array_profile is not None):
            raise GeneratorError(
                f"{typed.key}: mutable-global frame profile metadata mismatch")
        try:
            authorized_mutable_global_frames = (
                authenticate_mutable_global_frame(
                    typed, source_hash, mutable_global_frame_profile))
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        if len(authorized_mutable_global_frames) != len(
                (dynamic_frame_contract(typed).fields
                 if is_dynamic_program(typed)
                 else mutable_global_frame_contract(typed.key).fields)):
            raise GeneratorError(
                f"{typed.key}: mutable-global frame carrier cardinality mismatch")
    elif typed.key in MUTABLE_GLOBAL_FRAME_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact mutable-global frame profile carrier required")
    if mutable_global_array_profile is not None:
        # `classicNoisedeck/cellRefract` is admitted by exactly one carrier:
        # this one. `classicNoisedeck/kaleido:kaleido` is the mechanism's one
        # two-carrier row and `classicNoisedeck/effects:effects` its first
        # THREE-carrier row: their required companions are read from the
        # closure's own REQUIRED_COMPANION_PROFILES (the normalMap pattern)
        # -- present and exact for mapped keys, and still rejected for every
        # unmapped key, so the carve fails closed rather than widening. A
        # companion that is absent is the owning block's required-carrier
        # elif's business (each mechanism names its own message), and a
        # companion's VALUE is its own block's authentication's business.
        # Every other profile must be absent -- this collision list is the
        # runtime half of the row schema, and the slice-row allowlist arm in
        # `load_slice` is the schema half. The fixed-array input-parameter
        # proof is a TypedProgram field auto-attached before validation, not
        # a slice-row profile, so it is not listed here.
        array_companions = dict(
            MUTABLE_GLOBAL_ARRAY_COMPANIONS.get(typed.key, ()))
        companion_row = {"scalar_uint_xor_profile": scalar_uint_xor_profile,
                         "glitch_mat4_chain_profile": glitch_mat4_chain_profile,
                         "ceil_admission_profile": ceil_admission_profile}
        if (typed.key not in MUTABLE_GLOBAL_ARRAY_KEYS
                or mutable_global_array_profile
                != MUTABLE_GLOBAL_ARRAY_PROFILES.get(typed.key)
                or any(companion_row.get(name) != value
                       for name, value in array_companions.items())
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or runtime_loop_bound_profile is not None
                or gabor_effective_depth_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or (scalar_uint_xor_profile is not None
                    and "scalar_uint_xor_profile" not in array_companions)
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or edge_bvec3_contour_profile is not None
                or (glitch_mat4_chain_profile is not None
                    and "glitch_mat4_chain_profile" not in array_companions)
                or emboss_color_style_profile is not None
                or shape_mixer_builtin_profile is not None
                or caustic_word_hash_profile is not None
                or scanline_error_float_bits_ingress_profile is not None
                or shapes_float_bits_ingress_profile is not None
                or shapes_rvalue_assign_profile is not None
                or mutable_global_frame_profile is not None
                or glyph_map_nonnegative_int_shift_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or as_u32_round_profile is not None
                or (ceil_admission_profile is not None
                    and "ceil_admission_profile" not in array_companions)
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None):
            raise GeneratorError(
                f"{typed.key}: mutable-global array profile metadata mismatch")
        try:
            authorized_mutable_global_arrays = (
                authenticate_mutable_global_array(
                    typed, source_hash, mutable_global_array_profile))
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        # ALL admitted declarations, by object identity, in the frozen
        # declaration order (five for the two five-array keys, SEVEN for
        # effects -- the count is the contract's field census, per key since
        # the effects row, never a bare number). The validator's rejection
        # names only the first `float emboss[9];` line; admitting only that
        # one leaves the rest to fail at the unconditional post-loop storage
        # gate.
        if len(authorized_mutable_global_arrays) != len(
                mutable_global_array_contract(typed.key).fields):
            raise GeneratorError(
                f"{typed.key}: mutable-global array carrier cardinality mismatch")
    elif typed.key in MUTABLE_GLOBAL_ARRAY_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact mutable-global array profile carrier required")
    if const_global_table_profile is not None:
        # `filter/normalMap` is admitted by two carriers: this one and the
        # already-frozen as_u32 `round` carrier, which must be PRESENT and
        # exact rather than absent. The required-companion pairs are read from
        # the closure's own REQUIRED_COMPANION_PROFILES rather than spelled a
        # second time here; an unmapped field name resolves to None and fails
        # closed. Every other profile must be absent -- this collision list is
        # the runtime half, and the slice-row allowlist arm in `load_slice` is
        # the schema half.
        companion_row = {"as_u32_round_profile": as_u32_round_profile}
        if (typed.key not in CONST_GLOBAL_TABLE_KEYS
                or const_global_table_profile
                != CONST_GLOBAL_TABLE_PROFILES.get(typed.key)
                or any(companion_row.get(name) != value
                       for name, value in CONST_GLOBAL_TABLE_COMPANIONS.get(
                           typed.key, ()))
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or runtime_loop_bound_profile is not None
                or gabor_effective_depth_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or edge_bvec3_contour_profile is not None
                or glitch_mat4_chain_profile is not None
                or emboss_color_style_profile is not None
                or shape_mixer_builtin_profile is not None
                or caustic_word_hash_profile is not None
                or scanline_error_float_bits_ingress_profile is not None
                or shapes_float_bits_ingress_profile is not None
                or shapes_rvalue_assign_profile is not None
                or mutable_global_frame_profile is not None
                or mutable_global_array_profile is not None
                or glyph_map_nonnegative_int_shift_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or ceil_admission_profile is not None
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None):
            raise GeneratorError(
                f"{typed.key}: const-global nine-table profile metadata mismatch")
        try:
            authorized_const_global_tables = authenticate_const_global_tables(
                typed, source_hash, const_global_table_profile)
            authorized_const_global_table_reads = (
                authenticate_const_global_table_reads(
                    typed, source_hash, const_global_table_profile))
            const_global_tables = const_global_table_contract(typed.key)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        # ALL of them, by object identity, in the frozen declaration order.
        # Admitting only the first leaves `21:1` and `27:1` to fail at the next
        # iteration of the same loop, and the rejection would name only `15:1`.
        if (len(authorized_const_global_tables) != len(const_global_tables)
                or len(authorized_const_global_table_reads)
                != len(const_global_tables)):
            raise GeneratorError(
                f"{typed.key}: const-global nine-table carrier cardinality mismatch")
    elif typed.key in CONST_GLOBAL_TABLE_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact const-global nine-table profile carrier required")
    if varying_profile is not None:
        # `filter/wobble:wobble` is admitted by exactly one carrier: this one.
        # Varying admission is PURE EXPRESSION LOWERING -- the JavaScript
        # runtime hardcodes the materialization (`beginPixel` aliases the
        # pixel context's uv into the `vUv`/`v_texCoord` slots element by
        # element, per pixel; there is no vertex stage and no interpolation
        # anywhere in the CPU reference), so the emitted C++ needs no
        # capability token, no State/Frame field, and no kernel-signature
        # change. Every other profile must be absent -- this collision list
        # is the runtime half of the row schema, and the slice-row allowlist
        # arm in `load_slice` is the schema half.
        if (typed.key not in VARYING_UV_KEYS
                or varying_profile != VARYING_UV_PROFILES.get(typed.key)
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or runtime_loop_bound_profile is not None
                or gabor_effective_depth_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or edge_bvec3_contour_profile is not None
                or glitch_mat4_chain_profile is not None
                or emboss_color_style_profile is not None
                or shape_mixer_builtin_profile is not None
                or caustic_word_hash_profile is not None
                or scanline_error_float_bits_ingress_profile is not None
                or shapes_float_bits_ingress_profile is not None
                or shapes_rvalue_assign_profile is not None
                or mutable_global_frame_profile is not None
                or mutable_global_array_profile is not None
                or const_global_table_profile is not None
                or glyph_map_nonnegative_int_shift_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or ceil_admission_profile is not None
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None):
            raise GeneratorError(
                f"{typed.key}: varying-uv profile metadata mismatch")
        try:
            authorized_varyings = authenticate_varying_uv(
                typed, source_hash, varying_profile)
            varying_contract = varying_uv_contract(typed.key)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        # The ONE admitted interface symbol, by object identity, matching the
        # contract's own symbol record -- the closure froze the symbol's id,
        # name, type, storage and whole-file span, and a mismatch here is a
        # contract/lock divergence the tests must name.
        if (len(authorized_varyings) != 1
                or varying_contract.symbol_id
                != authorized_varyings[0].id):
            raise GeneratorError(
                f"{typed.key}: varying-uv carrier cardinality mismatch")
    elif typed.key in VARYING_UV_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact varying-uv profile carrier required")
    authorized_texture_lod_proof = None
    if texture_lod_admission_profile is not None:
        # `filter/parallax:parallax` is admitted by exactly one carrier: this
        # one. The textureLod admission is an IDENTITY ALIAS -- the JavaScript
        # authority drops the lod argument entirely (glsl-runtime.js:400:
        # `textureLod: (surface, coord) => this.#texture(surface, coord)`), so
        # the lowering rides the existing `texture` path unchanged and no mip
        # machinery exists anywhere. The program is also the counted-for
        # bucket's seed carrier, so the source-global literal-int carrier is
        # REQUIRED (auto-supplied from the loop-proof dict key, the same
        # Task-23 shape the five fingerprint-only profiles above ride) rather
        # than forbidden; every other profile must be absent -- the strict
        # form of the row schema's runtime half.
        if (typed.key not in TEXTURE_LOD_ADMISSION_KEYS
                or texture_lod_admission_profile
                != TEXTURE_LOD_ADMISSION_PROFILE
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile
                != SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
                or runtime_loop_bound_profile is not None
                or gabor_effective_depth_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or edge_bvec3_contour_profile is not None
                or glitch_mat4_chain_profile is not None
                or emboss_color_style_profile is not None
                or shape_mixer_builtin_profile is not None
                or caustic_word_hash_profile is not None
                or scanline_error_float_bits_ingress_profile is not None
                or shapes_float_bits_ingress_profile is not None
                or shapes_rvalue_assign_profile is not None
                or mutable_global_frame_profile is not None
                or mutable_global_array_profile is not None
                or const_global_table_profile is not None
                or glyph_map_nonnegative_int_shift_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None
                or posterize_round_profile is not None
                or as_u32_round_profile is not None
                or ceil_admission_profile is not None
                or waves_any_notequal_profile is not None
                or inout_vec3_swap_profile is not None
                or varying_profile is not None):
            raise GeneratorError(
                f"{typed.key}: textureLod admission profile metadata mismatch")
        try:
            authorized_texture_lod_proof = authenticate_texture_lod_admission(
                typed, source_hash, texture_lod_admission_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        # The TWO admitted call nodes, by object identity, exactly the
        # closure's own site census (`getHeight` 24:26 / `getInput` 30:12) --
        # a third textureLod site anywhere, global declaration initializers
        # included (the closure itself walks them), dies at the builtin arm.
        authorized_texture_lod_sites = tuple(
            site.node for site in authorized_texture_lod_proof.sites)
        if len(authorized_texture_lod_sites) != 2:
            raise GeneratorError(
                f"{typed.key}: textureLod admission carrier cardinality "
                "mismatch")
    elif typed.key in TEXTURE_LOD_ADMISSION_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact textureLod admission profile carrier required")
    if shape_mixer_builtin_profile is not None:
        collisions = (
            compatibility_transform, custom_comparer_profile,
            source_global_literal_int_profile, runtime_loop_bound_profile,
            gabor_effective_depth_profile, gather_sorted_round_profile,
            literal_vec3_lane_index_profile, smooth_edge_luma_weights_profile,
            perlin_scalar_uint_xor_profile, bitwise_scalar_int_ops_profile,
            rotate_mat2_return_profile, focus_blur_borrowed_sampler_profile,
            extrude_bvec2_relational_reduction_profile,
            edge_bvec3_contour_profile, glitch_mat4_chain_profile,
            emboss_color_style_profile, caustic_word_hash_profile,
            scanline_error_float_bits_ingress_profile,
            shapes_float_bits_ingress_profile,
            grime_float_bits_ingress_profile,
            shapes_rvalue_assign_profile,
            glyph_map_nonnegative_int_shift_profile, curl_vector_math_profile,
            grade_luma_weights_profile, grade_index_expression_profile,
            derivative_admission_profile, linear_srgb_lane_index_profile,
            reflect_admission_profile, posterize_round_profile,
            as_u32_round_profile, ceil_admission_profile,
            waves_any_notequal_profile, inout_vec3_swap_profile,
        )
        if (typed.key != SHAPE_MIXER_KEY
                or numeric_literal_contract != "glsl-f32"
                or scalar_uint_xor_profile != SCALAR_UINT_XOR_PROFILE
                or any(item is not None for item in collisions)):
            raise GeneratorError(
                f"{typed.key}: Shape Mixer builtin profile metadata mismatch")
        try:
            authorized_shape_mixer_proof = (
                authenticate_shape_mixer_builtin_closure(
                    typed, source_hash, shape_mixer_builtin_profile,
                    scalar_uint_xor_profile))
            proof = authorized_shape_mixer_proof
            candidate_shape_mixer_guards = (
                _candidate_shape_mixer_blend_mode_guards(typed))
            if not _shape_mixer_proof_matches_candidate(
                    typed, proof, authorized_scalar_uint_xors):
                raise ValueError(
                    "candidate ownership, exceptional closure, or companion mismatch")
        except (AttributeError, TypeError, ValueError) as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == SHAPE_MIXER_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Shape Mixer builtin profile carrier required")
    if bit_effects_frontend_profile is not None:
        collisions = (
            compatibility_transform, custom_comparer_profile,
            source_global_literal_int_profile, runtime_loop_bound_profile,
            gabor_effective_depth_profile, gather_sorted_round_profile,
            literal_vec3_lane_index_profile, smooth_edge_luma_weights_profile,
            perlin_scalar_uint_xor_profile, scalar_uint_xor_profile,
            bitwise_scalar_int_ops_profile, rotate_mat2_return_profile,
            focus_blur_borrowed_sampler_profile,
            extrude_bvec2_relational_reduction_profile,
            edge_bvec3_contour_profile, glitch_mat4_chain_profile,
            emboss_color_style_profile, shape_mixer_builtin_profile,
            caustic_word_hash_profile, scanline_error_float_bits_ingress_profile,
            shapes_float_bits_ingress_profile, grime_float_bits_ingress_profile,
            shapes_rvalue_assign_profile, mutable_global_frame_profile,
            mutable_global_array_profile, const_global_table_profile,
            varying_profile, texture_lod_admission_profile,
            cross_lane_assignment_profile, glyph_map_nonnegative_int_shift_profile,
            curl_vector_math_profile, grade_luma_weights_profile,
            grade_index_expression_profile, derivative_admission_profile,
            linear_srgb_lane_index_profile, reflect_admission_profile,
            posterize_round_profile, as_u32_round_profile,
            ceil_admission_profile, waves_any_notequal_profile,
            inout_vec3_swap_profile, out_inout_admission_profile,
            struct_declaration_profile, testpattern_frontend_proof,
            remap_frontend_proof)
        if (typed.key not in BIT_EFFECTS_PREPARED_KEYS
                or bit_effects_frontend_profile
                != BIT_EFFECTS_PREPARED_PROFILES[typed.key]
                or numeric_literal_contract != "glsl-f32"
                or any(item is not None for item in collisions)):
            raise GeneratorError(
                f"{typed.key}: BitEffects frontend profile metadata mismatch")
        try:
            authorized_bit_effects_proof = authenticate_bit_effects_frontend(
                typed, source_hash, bit_effects_frontend_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_bit_effects_nodes = authorized_bit_effects_proof.consumed_objects
    elif typed.key in BIT_EFFECTS_PREPARED_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact BitEffects frontend profile carrier required")
    if bitwise_scalar_int_ops_profile is not None:
        if (typed.key not in BITWISE_SCALAR_INT_OPS_KEYS
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
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Bitwise scalar int ops profile metadata mismatch")
        try:
            authorized_bitwise_number_proof = authenticate_bitwise_scalar_int_ops(
                typed, source_hash, bitwise_scalar_int_ops_profile)
            authorized_bitwise_scalar_int_ops_sites = (
                authorized_bitwise_number_proof.bitwise_nodes)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in BITWISE_SCALAR_INT_OPS_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact Bitwise scalar int ops profile carrier required")
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
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None
                or reflect_admission_profile is not None):
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
    if linear_srgb_lane_index_profile is not None:
        if (typed.key not in LINEAR_SRGB_LANE_INDEX_KEYS
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Linear sRGB lane index profile metadata mismatch")
        try:
            authorized_linear_srgb_lane_index_sites = authenticate_linear_srgb_lane_index(
                typed, source_hash, linear_srgb_lane_index_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in LINEAR_SRGB_LANE_INDEX_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact Linear sRGB lane index profile carrier required")
    if reflect_admission_profile is not None:
        if (typed.key != REFLECT_ADMISSION_KEY
                or compatibility_transform is not None
                or custom_comparer_profile is not None
                or numeric_literal_contract != "glsl-f32"
                or source_global_literal_int_profile is not None
                or gather_sorted_round_profile is not None
                or literal_vec3_lane_index_profile is not None
                or smooth_edge_luma_weights_profile is not None
                or perlin_scalar_uint_xor_profile is not None
                or bitwise_scalar_int_ops_profile is not None
                or rotate_mat2_return_profile is not None
                or focus_blur_borrowed_sampler_profile is not None
                or extrude_bvec2_relational_reduction_profile is not None
                or caustic_word_hash_profile is not None
                or curl_vector_math_profile is not None
                or grade_luma_weights_profile is not None
                or grade_index_expression_profile is not None
                or derivative_admission_profile is not None
                or linear_srgb_lane_index_profile is not None):
            raise GeneratorError(
                f"{typed.key}: Reflect admission profile metadata mismatch")
        try:
            authorized_reflect_node = authenticate_reflect_admission(
                typed, source_hash, reflect_admission_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == REFLECT_ADMISSION_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Reflect admission profile carrier required")
    if gather_sorted_round_profile is not None:
        if (typed.key != GATHER_SORTED_KEY or compatibility_transform is not None
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: Gather Sorted round profile metadata mismatch")
        try:
            _, authorized_round = authenticate_gather_sorted_round_to_int(
                typed, source_hash, gather_sorted_round_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    # posterize_round_profile and waves_any_notequal_profile are deliberately
    # light-checked (own key/compatibility_transform/numeric_literal_contract
    # only), the same style as gather_sorted_round_profile and
    # literal_vec3_lane_index_profile immediately above -- and deliberately
    # NOT mutually exclusive with derivative_admission_profile, since both
    # Posterize and Waves also carry a derivative call admitted by that
    # profile. Grade's LUMA-weights/index-expression pair is the precedent
    # for two profiles legitimately coexisting on one program key.
    if posterize_round_profile is not None:
        if (typed.key != POSTERIZE_KEY or compatibility_transform is not None
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: Posterize round admission profile metadata mismatch")
        try:
            authorized_posterize_round = authenticate_posterize_round_admission(
                typed, source_hash, posterize_round_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == POSTERIZE_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Posterize round admission profile carrier required")
    # as_u32_round_profile is deliberately light-checked, the same style as
    # posterize_round_profile immediately above, keyed by a dict of
    # program_key carriers (AS_U32_ROUND_KEYS) since the admitted `round`
    # site is inside a byte-identical shared helper reused verbatim across
    # several programs, rather than a one-off.
    if as_u32_round_profile is not None:
        if (typed.key not in AS_U32_ROUND_KEYS or compatibility_transform is not None
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: as_u32 round admission profile metadata mismatch")
        try:
            authorized_as_u32_round = authenticate_as_u32_round_admission(
                typed, source_hash, as_u32_round_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in AS_U32_ROUND_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact as_u32 round admission profile carrier required")
    # ceil: node-identity admission only. Adds no capability token; the frozen
    # 44-entry vocabulary is untouched. Math.ceil and std::ceil agree on every
    # finite double, so unlike `round` this needs no bespoke narrowing shim.
    if ceil_admission_profile is not None:
        if (typed.key not in CEIL_ADMISSION_KEYS or compatibility_transform is not None
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: ceil admission profile metadata mismatch")
        try:
            authorized_ceil = authenticate_ceil_admission(
                typed, source_hash, ceil_admission_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key in CEIL_ADMISSION_KEYS:
        raise GeneratorError(
            f"{typed.key}: exact ceil admission profile carrier required")
    if waves_any_notequal_profile is not None:
        if (typed.key != WAVES_KEY or compatibility_transform is not None
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: Waves any/notEqual admission profile metadata mismatch")
        try:
            authorized_waves_proof = authenticate_waves_any_notequal_admission(
                typed, source_hash, waves_any_notequal_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
        authorized_waves_relationals = authorized_waves_proof.relationals
        authorized_waves_reductions = authorized_waves_proof.reductions
    elif typed.key == WAVES_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Waves any/notEqual admission profile carrier required")
    # inout_vec3_swap_profile is deliberately light-checked, the same style as
    # posterize_round_profile/waves_any_notequal_profile immediately above --
    # it never coexists with any other profile on this program key, so no
    # broader mutual-exclusion list is needed.
    if inout_vec3_swap_profile is not None:
        if (typed.key != INOUT_VEC3_SWAP_KEY or compatibility_transform is not None
                or numeric_literal_contract != "glsl-f32"):
            raise GeneratorError(f"{typed.key}: Inout vec3 swap admission profile metadata mismatch")
        try:
            authorized_inout_vec3_swap_proof = authenticate_inout_vec3_swap_admission(
                typed, source_hash, inout_vec3_swap_profile)
        except ValueError as error:
            raise GeneratorError(f"{typed.key}: {error}") from error
    elif typed.key == INOUT_VEC3_SWAP_KEY:
        raise GeneratorError(
            f"{typed.key}: exact Inout vec3 swap admission profile carrier required")
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
        node for function in typed.functions for statement in function.body
        for node in walk_statement_nodes(statement))
    if authorized_historic_palette_proof is not None:
        authorized_historic_members = tuple(
            node for node in all_expression_nodes if node.kind == "member"
            and node.children and node.children[0].type.display() == "HistoricPalette")
        if len(authorized_historic_members) != 7:
            raise GeneratorError(f"{typed.key}: Historic Palette member census drift")
    if authorized_palette_frontend_proof is not None:
        authorized_palette_members = tuple(
            node for node in all_expression_nodes if node.kind == "member"
            and node.children and node.children[0].type.display() == "PaletteEntry")
        if len(authorized_palette_members) != 5:
            raise GeneratorError(f"{typed.key}: Palette member census drift")
    def reject_type(typ, value) -> None:
        if typ.kind == "struct":
            if (authorized_struct_type is typ
                    or (authorized_historic_palette_proof is not None
                        and typ is authorized_historic_palette_proof.struct.type)
                    or (authorized_palette_frontend_proof is not None
                        and typ is authorized_palette_frontend_proof.struct.type)):
                return
            raise GeneratorError(
                f"{location(value)}: unsupported typed type {typ.display()}")
        if typ.kind == "array":
            if any(value is item for item in authorized_dither_globals):
                return
            if any(value is item for item in authorized_dither_arrays):
                return
            if any(getattr(value, "symbol_id", None) == getattr(item, "symbol_id", None)
                   or getattr(value, "symbol_id", None) == getattr(getattr(item, "symbol", None), "id", None)
                   for item in authorized_dither_arrays):
                return
            if value is authorized_newton_roots_declaration:
                return
            if (remap_frontend_proof is not None
                    and value is authorized_remap_data_declaration):
                return
            if any(value is item for item in authorized_testpattern_array_declarations):
                visited_testpattern_array_types.append(value)
                return
            if any(value is item for item in authorized_testpattern_array_constructors):
                return
            if (authorized_osd_proof is not None
                    and value is authorized_osd_proof.consumed_objects[0]):
                return
            if (authorized_osd_proof is not None
                    and any(value is item for item in authorized_osd_proof.consumed_objects
                            if getattr(item, "kind", None) == "construct")):
                return
            if (authorized_spooky_ticker_proof is not None
                    and (value is authorized_spooky_ticker_global
                         or value is authorized_spooky_ticker_constructor)):
                if value is authorized_spooky_ticker_global:
                    # The declaration itself is consumed at the separate
                    # source-global admission/storage gates below.
                    pass
                return
            # Gate 2 of 3: array TYPE admission for a file-scope declaration,
            # by exact node IDENTITY against what this authority's own call to
            # `authenticate_const_global_tables` returned.
            #
            # `proved_array_declarations` below is structurally UNREACHABLE for
            # a file-scope declaration and registering the symbol there does
            # nothing: that arm requires both `value.symbol_id` and
            # `value.kind == "declaration"`, and a `TypedDeclaration` carries
            # only `initializer`, `span`, `symbol` and `type` (verified against
            # the live node, not assumed). Hence a node-identity arm here.
            #
            # Nothing is added to `used`: `ivec2` and `float` are already in
            # the frozen 17-entry type tuple and only the array wrapper is new,
            # so neither frozen vocabulary grows.
            if any(value is item for item in authorized_const_global_tables):
                visited_const_global_table_types.append(value)
                return
            if (authorized_historic_palette_proof is not None
                    and any(value is item for item in (
                        authorized_historic_palette_proof.palettes_declaration,
                        authorized_historic_palette_proof.palettes_initializer))):
                return
            if (authorized_palette_frontend_proof is not None
                    and any(value is item for item in (
                        authorized_palette_frontend_proof.palettes_declaration,
                        authorized_palette_frontend_proof.palettes_initializer))):
                return
            if any(value is item for item in authorized_median_array_declarations):
                visited_median_array_declarations.append(value)
                return
            # Gate 1 of 3 for the mutable-global array carrier: array TYPE
            # admission for the five file-scope `float[9]` declarations, by
            # exact node IDENTITY against what this authority's own call to
            # `authenticate_mutable_global_array` returned. The const tables
            # need this same arm; the shape frame did not because `float` and
            # `vec2` are already in the frozen type vocabulary and `float[9]`
            # is not. Nothing is added to `used`: `float` is already an
            # approved type and it is the storage class, not the type, being
            # admitted here.
            if any(value is item for item in authorized_mutable_global_arrays):
                visited_mutable_global_array_types.append(value)
                return
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
        if any(value is item for item in authorized_dither_globals):
            return
        if typ.display() == "bvec2":
            # `bvec2` is deliberately absent from APPROVED_TYPES. It is admitted
            # only as the result type of an exact authenticated Extrude
            # relational node (consumed immediately by its paired `all`) or
            # an exact authenticated Waves relational node (consumed
            # immediately by its paired `any`). Type admission is a separate
            # authority from builtin admission, so both must independently
            # agree.
            if any(value is item for item in authorized_extrude_relationals):
                return
            if any(value is item for item in authorized_waves_relationals):
                return
            if (authorized_emboss_proof is not None
                    and any(value is item
                            for item in authorized_emboss_proof.equalities)):
                return
            raise GeneratorError(f"{location(value)}: unsupported typed type {typ.display()}")
        if typ.display() == "bvec3":
            nodes = (() if authorized_edge_proof is None
                     else authorized_edge_proof.bvec_nodes)
            if any(value is item for item in nodes):
                return
            raise GeneratorError(
                f"{location(value)}: unsupported typed type {typ.display()}")
        if typ.display() == "mat4":
            nodes = (() if authorized_glitch_proof is None
                     else authorized_glitch_proof.consumed_objects)
            if any(value is item for item in nodes):
                return
            raise GeneratorError(
                f"{location(value)}: unsupported typed type {typ.display()}")
        if typ.display() not in APPROVED_TYPES or typ.kind in {"array", "struct"}:
            raise GeneratorError(f"{location(value)}: unsupported typed type {typ.display()}")

    try:
        if noise_frontend_profile is not None:
            noise_contract = authenticate_noise_runtime(
                typed, source_hash, noise_frontend_profile)
            recomputed_functions = attach_counted_loop_proofs(
                clear_counted_loop_proofs(typed.functions), typed.key,
                runtime_scalar_bounds=(noise_contract.seed,))
            recomputed_program_proof = summarize_counted_loop_proofs(
                recomputed_functions)
        elif fractal_frontend_profile is not None:
            profiled = apply_fractal_frontend(
                typed, source_hash, fractal_frontend_profile)
            recomputed_functions = profiled.functions
            recomputed_program_proof = profiled.counted_loop_proof
        elif julia_frontend_profile is not None:
            profiled = apply_julia_frontend(
                typed, source_hash, julia_frontend_profile)
            recomputed_functions = profiled.functions
            recomputed_program_proof = profiled.counted_loop_proof
        else:
            recomputed_functions, recomputed_program_proof = (
                rebuild_authenticated_counted_loop_proofs(
                    typed, source_global_literal_int_profile,
                    runtime_loop_bound_profile))
    except ValueError as error:
        raise GeneratorError(f"{typed.key}: {error}") from error
    if len(recomputed_functions) != len(typed.functions):
        raise GeneratorError(f"{typed.key}: malformed counted-for proof functions")

    effective_depth_limit = (
        gabor_effective_depth_contract.maximum_effective_depth
        if gabor_effective_depth_contract is not None else 3)

    def audit_loop_proofs(actual, expected) -> None:
        if actual.kind != expected.kind or len(actual.children) != len(expected.children):
            raise GeneratorError(f"{location(actual)}: malformed counted-for proof structure")
        if actual.loop_proof != expected.loop_proof:
            raise GeneratorError(f"{location(actual)}: malformed counted-for proof")
        proof = actual.loop_proof
        if proof is not None:
            max_trip_count = (1000 if typed.key == JULIA_KEY
                              else COUNTED_FOR_V1_MAX_TRIP_COUNT)
            if (proof.trip_count > max_trip_count or proof.lexical_depth > 3
                    or proof.effective_depth > effective_depth_limit
                    or proof.lexical_product > COUNTED_FOR_V1_MAX_LEXICAL_PRODUCT
                    or proof.entrypoint_charge > COUNTED_FOR_V1_MAX_ENTRYPOINT_CHARGE
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
    if authorized_emboss_proof is not None:
        for table in authorized_emboss_proof.tables:
            proved_array_declarations[table.symbol_id] = (
                table.declaration.span, table.array_type)
            proved_store_indices.update(
                (table.symbol_id,
                 store.children[0].children[1].literal_value,
                 store.children[0].span)
                for store in table.literal_stores)
            proved_read_indices.add((
                table.symbol_id, table.induction_symbol_id,
                table.dynamic_read.span))
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
    elif typed.key in (TASK19_CELLREFRACT_KEY, TASK19_KALEIDO_KEY,
                      TASK19_EFFECTS_KEY):
        # Amendment S13.1: the `cellrefract-convolve-v1` record auto-attaches
        # on the authentic program (the generator attaches it before
        # validation), so the historical `elif` below would have raised the
        # foreign-proof-key error. The registration body is byte-for-byte the
        # refract arm's -- the two records share the `FixedArrayInParameterProof`
        # shape -- and cellRefract's eight caller tables plus the `vec2
        # offset[9]` table all register here. Their unreachability at
        # KERNEL=0 is the proof's own frozen fact, not this arm's concern.
        # The kaleido row (187) joined the same arm: `kaleido-convolve-v1`
        # auto-attaches the same way and registers the same-shaped tables
        # (its `shadow` tables at statements 0/10 included). The effects
        # row (188) joined the same arm: `effects-convolve-v1` auto-attaches
        # the same way and registers the same-shaped tables over SEVEN
        # globals (its own `shadow` tables at 0/10 included) -- the family's
        # first seven-array census, frozen per key in the fixed-array
        # module.
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
    testpattern_dynamic_loop_admitted = False
    if testpattern_frontend_proof is not None:
        if typed.key != TESTPATTERN_KEY:
            raise GeneratorError(
                f"{typed.key}: Test Pattern dynamic-loop proof on foreign key")
        render_functions = [function for function in recomputed_functions
                            if function.signature.id == 29
                            and function.name == "renderNumber"]
        dynamic_loops = [statement for function in render_functions
                         for statement in function.body
                         if statement.kind == "for"
                         and statement.loop_proof is None]
        if (len(dynamic_loops) != 1
                or len(render_functions) != 1
                or getattr(testpattern_frontend_proof,
                           "dynamic_loop_owner", None) != (29, "renderNumber")
                or getattr(testpattern_frontend_proof,
                           "dynamic_loop_bound_range", None) != (1, 3)):
            raise GeneratorError(
                f"{typed.key}: authenticated Test Pattern dynamic-loop proof mismatch")
        testpattern_dynamic_loop_admitted = True
    if (recomputed_program_proof.unproved_loop_count
            or recomputed_program_proof.max_effective_depth > effective_depth_limit
            or recomputed_program_proof.max_lexical_product > COUNTED_FOR_V1_MAX_LEXICAL_PRODUCT
            or recomputed_program_proof.entrypoint_charge > COUNTED_FOR_V1_MAX_ENTRYPOINT_CHARGE):
        # Programs without a loop stay valid after the unconditional call-graph
        # check above; only an actual unproved or over-budget loop reaches here.
        if (recomputed_program_proof.loop_count
                or recomputed_program_proof.unproved_loop_count) \
                and not testpattern_dynamic_loop_admitted \
                and not median_unproved_loop_admitted \
                and not dither_unproved_loop_admitted:
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
        if any(declaration is item
               for item in authorized_mutable_global_frames):
            # Gate 1 of 2. A mutable, uninitialised, file-scope global,
            # admitted by exact node IDENTITY -- never by storage class.
            #
            # Deliberately NOT registered in `admitted_globals`: that is the
            # const set, and the `audit_expression` pass below raises `write to
            # source const global` for every assignment whose base targets a
            # member of it. Both of this program's authenticated writes in
            # `main` would be rejected by it. Nothing is added to `used` either
            # -- `float` and `vec2` are already approved types, and it is the
            # storage class, not the type, being admitted, so neither frozen
            # vocabulary grows.
            visited_mutable_global_frame_admissions.append(declaration)
            continue
        if any(declaration is item
               for item in authorized_mutable_global_arrays):
            # Gate 2 of 3. A mutable, uninitialised, file-scope `float[9]`
            # global, admitted by exact node IDENTITY -- never by storage
            # class, never by type. Like the shape frame above and unlike the
            # const tables below, deliberately NOT registered in
            # `admitted_globals`: that is the const set, and the
            # `write to source const global` audit would reject all 45
            # authenticated stores in `loadKernels` (the Amendment review
            # verified that audit covers only the const set). Nothing is
            # added to `used` -- `float` is already an approved type.
            visited_mutable_global_array_admissions.append(declaration)
            continue
        if any(declaration is item
               for item in authorized_const_global_tables):
            # Gate 1 of 3. A const, literal-initialised, file-scope array
            # global, admitted by exact node IDENTITY -- never by storage class
            # and never by type.
            #
            # DELIBERATELY registered in `admitted_globals`, the opposite of
            # the mutable-global frame decision immediately above. That set is
            # the const set: `audit_expression` below raises `write to source
            # const global` for every assignment, prefix `++`/`--` and postfix
            # `++`/`--` whose base targets a member of it. For a genuinely
            # `const` table that barrier is exactly the wanted behaviour --
            # the frame had to stay out of it only because its own two
            # authenticated writes would have been rejected. This is the
            # validator's independent second barrier; the closure's predicate 5
            # is the first, and it also walks global initializers, which this
            # one does not.
            #
            # Nothing is added to `used`: see the note in `reject_type`.
            admitted_globals[declaration.symbol.id] = declaration
            visited_const_global_table_admissions.append(declaration)
            continue
        if (authorized_historic_palette_proof is not None
                and declaration is authorized_historic_palette_proof.palettes_declaration):
            admitted_globals[declaration.symbol.id] = declaration
            continue
        if any(declaration is item for item in authorized_dither_globals):
            admitted_globals[declaration.symbol.id] = declaration
            continue
        if (authorized_palette_frontend_proof is not None
                and declaration is authorized_palette_frontend_proof.palettes_declaration):
            admitted_globals[declaration.symbol.id] = declaration
            continue
        if (authorized_testpattern_global_symbol_id is not None
                and declaration.symbol.id == authorized_testpattern_global_symbol_id):
            admitted_globals[declaration.symbol.id] = declaration
            visited_testpattern_global_admissions.append(declaration)
            continue
        if (authorized_osd_proof is not None
                and declaration is authorized_osd_proof.consumed_objects[0]):
            admitted_globals[declaration.symbol.id] = declaration
            visited_osd_globals.append(declaration)
            continue
        if (authorized_spooky_ticker_proof is not None
                and declaration is authorized_spooky_ticker_global):
            admitted_globals[declaration.symbol.id] = declaration
            visited_spooky_ticker_globals.append(declaration)
            continue
        if authorized_bit_effects_proof is not None and any(
                declaration is item
                for item in authorized_bit_effects_proof.global_const_declarations):
            expected_index = len(visited_bit_effects_globals)
            expected = authorized_bit_effects_proof.global_const_declarations
            if (expected_index >= len(expected)
                    or declaration is not expected[expected_index]
                    or declaration.symbol.storage != "const"
                    or declaration.type.display() != "int"
                    or declaration.initializer is None):
                raise GeneratorError(
                    f"{location(declaration)}: authenticated BitEffects global declaration mismatch")
            if expected_index == 0:
                if (declaration.symbol.name != "BIT_COUNT"
                        or declaration.initializer.kind != "literal"):
                    raise GeneratorError(
                        f"{location(declaration)}: authenticated BIT_COUNT initializer mismatch")
            else:
                mask = declaration.initializer
                if (declaration.symbol.name != "mask"
                        or mask.kind != "binary" or mask.operator != "-"
                        or len(mask.children) != 2
                        or mask.children[0] is not authorized_bit_effects_proof.scalar_int_bitwise_nodes[0]
                        or mask.children[0].kind != "binary"
                        or mask.children[0].operator != "<<"
                        or mask.children[0].type.display() != "int"):
                    raise GeneratorError(
                        f"{location(declaration)}: authenticated BitEffects mask initializer mismatch")
                visited_bit_effects_nodes.append(mask.children[0])
            visited_bit_effects_globals.append(declaration)
            admitted_globals[declaration.symbol.id] = declaration
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
        if (storage == "const" and declaration.type.display() == "mat3"
                and declaration.initializer is not None):
            # The only mat3-global shape present anywhere in the corpus:
            # `const mat3 NAME = mat3(<9 float literals>);` -- deliberately
            # narrow (no computed/nested initializer, unlike the const-float
            # grammar below), matching the mat3 construct-validator check.
            # See docs/port-engineering/global-admission/global-admission-design.md S4.1.
            def mat3_literal_component(child) -> bool:
                # Accept a plain float literal, or a unary `-` applied to
                # one (GLSL negative literal components, e.g. -1.2681437731,
                # parse as unary-minus-of-literal, not a signed literal
                # token).
                if (child.kind == "unary" and child.operator == "-"
                        and len(child.children) == 1):
                    child = child.children[0]
                return (child.kind == "literal" and child.type == FLOAT
                        and child.literal is not None and child.literal_value is not None)

            initializer = declaration.initializer
            if (initializer.kind != "construct" or initializer.type.display() != "mat3"
                    or len(initializer.children) != 9
                    or any(not mat3_literal_component(child)
                           for child in initializer.children)):
                raise GeneratorError(
                    f"{location(declaration)}: unsupported mat3 global initializer")
            admitted_globals[declaration.symbol.id] = declaration
            continue
        if (storage == "const" and declaration.type.display() in {"int", "uint"}
                and declaration.initializer is not None
                and declaration.initializer.kind == "literal"):
            # General const-scalar-literal admission for int/uint globals,
            # deliberately narrower than the const-float grammar below: a
            # bare literal only, no id-reference/arithmetic composition (no
            # shipped program in this family needs it). Exact-integer
            # values, so there is no narrowing risk at all (unlike float).
            # See docs/port-engineering/global-admission/global-admission-design.md.
            literal = declaration.initializer
            if literal.literal is None or literal.literal_value is None:
                raise GeneratorError(f"{location(declaration)}: malformed global initializer literal")
            admitted_globals[declaration.symbol.id] = declaration
            continue
        if (storage == "const" and declaration.type.display() == "vec3"
                and declaration.initializer is not None):
            # General const-vec3 admission: `const vec3 NAME = vec3(<3
            # float-valued components>);` where each component is a float
            # literal, arithmetic (+-*/) of float literals/earlier-admitted
            # const floats, or a single-lane swizzle of an earlier-admitted
            # const vec3 global (the `TIME_SEED_LINE = BASE_SEED_LINE.x +
            # 97.0`-shaped seed-derivation idiom shared by several filter
            # programs). No accumulated arithmetic risk: every float
            # component narrows identically in GLSL and the emitted C++
            # (single value.literal spelling or one lane read), matching the
            # const-float grammar's narrowing analysis.
            vec3_initializer = declaration.initializer
            if (vec3_initializer.kind != "construct"
                    or vec3_initializer.type.display() != "vec3"
                    or len(vec3_initializer.children) != 3):
                raise GeneratorError(
                    f"{location(declaration)}: unsupported vec3 global initializer")

            def vec3_float_component(value) -> None:
                if value.type.display() != "float":
                    raise GeneratorError(
                        f"{location(value)}: unsupported global initializer type {value.type.display()}")
                if value.kind == "literal":
                    if value.literal is None or value.literal_value is None:
                        raise GeneratorError(f"{location(value)}: malformed global initializer literal")
                    return
                if value.kind == "id":
                    dependency = admitted_globals.get(value.symbol_id)
                    if (dependency is None or value.symbol is None
                            or value.symbol.id != value.symbol_id
                            or dependency.symbol.id != value.symbol_id
                            or dependency.type.display() != "float"):
                        raise GeneratorError(
                            f"{location(value)}: global initializer dependency must name an earlier admitted const float")
                    return
                if (value.kind == "swizzle" and value.children
                        and value.member is not None and len(value.member) == 1):
                    base = value.children[0]
                    dependency = admitted_globals.get(base.symbol_id) if base.kind == "id" else None
                    if (base.kind != "id" or dependency is None or base.symbol is None
                            or base.symbol.id != base.symbol_id
                            or dependency.symbol.id != base.symbol_id
                            or dependency.type.display() != "vec3"):
                        raise GeneratorError(
                            f"{location(value)}: global initializer swizzle dependency must name an earlier admitted const vec3")
                    return
                if value.kind == "unary" and value.operator in {"+", "-"} and len(value.children) == 1:
                    vec3_float_component(value.children[0])
                    return
                if value.kind == "binary" and value.operator in {"+", "-", "*", "/"} and len(value.children) == 2:
                    vec3_float_component(value.children[0])
                    vec3_float_component(value.children[1])
                    return
                raise GeneratorError(f"{location(value)}: unsupported global initializer expression {value.kind}")

            for component in vec3_initializer.children:
                vec3_float_component(component)
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
        authorized_historic_struct = (
            authorized_historic_palette_proof is not None
            and len(typed.structs) == 1
            and typed.structs[0] is authorized_historic_palette_proof.struct)
        authorized_palette_struct = (
            authorized_palette_frontend_proof is not None
            and len(typed.structs) == 1
            and typed.structs[0] is authorized_palette_frontend_proof.struct)
        if (not authorized_historic_struct and not authorized_palette_struct
                and (authorized_struct_declaration is None
                     or len(typed.structs) != 1
                     or typed.structs[0] is not authorized_struct_declaration)):
            raise GeneratorError(f"{location(typed.structs[0])}: unsupported struct declaration")
    if typed.uniform_blocks:
        if (remap_frontend_proof is None
                or len(typed.uniform_blocks) != 1
                or typed.uniform_blocks[0] is not remap_frontend_proof.uniform_block):
            raise GeneratorError(f"{location(typed.uniform_blocks[0])}: unsupported uniform block")
        visited_remap_uniform_blocks.append(typed.uniform_blocks[0])
    elif remap_frontend_proof is not None:
        raise GeneratorError(f"{typed.key}: authenticated Remap uniform block is absent")
    if typed.interface_symbols:
        # The varying-uv carrier's admission gate: the program's interface
        # symbols must be EXACTLY the authenticated tuple, by object identity,
        # consumed once each, in the frozen order (the same visitation-ledger
        # discipline as the frame/array/table carriers). A foreign varying, an
        # impostor admission, or a second interface symbol still answers with
        # the unchanged message below -- the boundary every non-carrier
        # varying program keeps hitting.
        if (len(typed.interface_symbols) != len(authorized_varyings)
                or any(symbol is not expected for symbol, expected in zip(
                    typed.interface_symbols, authorized_varyings))):
            raise GeneratorError(f"{location(typed.interface_symbols[0])}: unsupported varying")
        visited_varying_admissions.extend(typed.interface_symbols)
    for declaration in typed.declarations:
        if (testpattern_frontend_proof is not None
                and any(declaration.initializer is item
                        for item in authorized_testpattern_array_constructors)):
            if any(declaration.initializer is item
                   for item in visited_testpattern_array_constructors):
                raise GeneratorError(
                    f"{typed.key}: authenticated Test Pattern array constructor visited twice")
            visited_testpattern_array_constructors.append(declaration.initializer)
        reject_type(declaration.type, declaration)
        if (declaration.type.kind == "matrix"
                and declaration.symbol.id not in admitted_globals):
            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")
        if any(declaration is item
               for item in authorized_mutable_global_frames):
            # Gate 2 of 2. Unconditional and separate from the admission loop
            # above: admitting in the loop alone is not sufficient, which is
            # the same two-site shape the mat3 widening hit.
            visited_mutable_global_frame_storage.append(declaration)
            continue
        if any(declaration is item
               for item in authorized_mutable_global_arrays):
            # Gate 3 of 3. Unconditional and separate from the admission loop
            # above, the same two-site shape the frame and the mat3 widening
            # hit: without this arm the five fall through to the storage
            # check below, whose `global` storage class is exactly what this
            # mechanism exists to admit.
            visited_mutable_global_array_storage.append(declaration)
            continue
        if (authorized_testpattern_global_symbol_id is not None
                and declaration.symbol.id == authorized_testpattern_global_symbol_id):
            visited_testpattern_global_storage.append(declaration)
        if (authorized_osd_proof is not None
                and declaration is authorized_osd_proof.consumed_objects[0]):
            # OSD's GLYPHS table is a const array, so retain the ordinary
            # const storage gate while recording exact identity consumption.
            if declaration not in visited_osd_globals:
                visited_osd_globals.append(declaration)
        if (authorized_spooky_ticker_proof is not None
                and declaration is authorized_spooky_ticker_global
                and declaration not in visited_spooky_ticker_globals):
            visited_spooky_ticker_globals.append(declaration)
        if any(declaration is item
               for item in authorized_const_global_tables):
            # Gate 3 of 3. Deliberately records visitation and then FALLS
            # THROUGH to the storage check below rather than `continue`-ing
            # past it the way the mutable frame must: these three are
            # genuinely `const`, so the unconditional storage gate stays live
            # for them instead of being bypassed by their admission.
            visited_const_global_table_storage.append(declaration)
        if declaration.symbol.storage not in {"uniform", "output", "const"}:
            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")
    if authorized_testpattern_global_symbol_id is not None:
        if (len(visited_testpattern_global_admissions) != 1
                or len(visited_testpattern_global_storage) != 1
                or visited_testpattern_global_admissions[0].symbol.id
                != authorized_testpattern_global_symbol_id
                or visited_testpattern_global_storage[0].symbol.id
                != authorized_testpattern_global_symbol_id):
            raise GeneratorError(
                f"{typed.key}: authenticated Test Pattern global visitation mismatch")
    if authorized_mutable_global_frames:
        # Every authenticated declaration consumed exactly once, by identity,
        # in the frozen order, at EACH of the two independent gates. A gate
        # that silently stops consuming (or consumes something twice) is the
        # failure this ledger exists to name.
        for label, visited in (
                ("admission", visited_mutable_global_frame_admissions),
                ("storage", visited_mutable_global_frame_storage)):
            if (len(visited) != len(authorized_mutable_global_frames)
                    or any(item is not expected for item, expected in zip(
                        visited, authorized_mutable_global_frames))):
                raise GeneratorError(
                    f"{typed.key}: authenticated mutable-global frame "
                    f"{label} visitation mismatch")
    if authorized_const_global_tables:
        # Same ledger contract at each of the three gates: consumed exactly
        # once, by identity, in the frozen declaration order.
        for label, visited in (
                ("admission", visited_const_global_table_admissions),
                ("type", visited_const_global_table_types),
                ("storage", visited_const_global_table_storage)):
            if (len(visited) != len(authorized_const_global_tables)
                    or any(item is not expected for item, expected in zip(
                        visited, authorized_const_global_tables))):
                raise GeneratorError(
                    f"{typed.key}: authenticated const-global nine-table "
                    f"{label} visitation mismatch")
    if authorized_mutable_global_arrays:
        # Same ledger contract at each of the three gates: consumed exactly
        # once, by object identity, in the frozen declaration order (ordinals 16-20).
        for label, visited in (
                ("admission", visited_mutable_global_array_admissions),
                ("type", visited_mutable_global_array_types),
                ("storage", visited_mutable_global_array_storage)):
            if (len(visited) != len(authorized_mutable_global_arrays)
                    or any(item is not expected for item, expected in zip(
                        visited, authorized_mutable_global_arrays))):
                raise GeneratorError(
                    f"{typed.key}: authenticated mutable-global array "
                    f"{label} visitation mismatch")
    if authorized_varyings:
        # The one-gate ledger contract: the authenticated varying symbol was
        # consumed exactly once, by object identity, at the interface gate. A
        # gate that silently stops consuming (or consumes something twice) is
        # the failure this ledger exists to name.
        if (len(visited_varying_admissions) != len(authorized_varyings)
                or any(item is not expected for item, expected in zip(
                    visited_varying_admissions, authorized_varyings))):
            raise GeneratorError(
                f"{typed.key}: authenticated varying-uv admission "
                "visitation mismatch")
    def expression(value, context: str = "rvalue") -> None:
        if any(value is item for item in authorized_spooky_ticker_varying_reads):
            if any(value is item for item in visited_spooky_ticker_varying_reads):
                raise GeneratorError(
                    f"{typed.key}: authenticated SpookyTicker varying read visited twice")
            expected_index = len(visited_spooky_ticker_varying_reads)
            if (expected_index >= len(authorized_spooky_ticker_varying_reads)
                    or value is not authorized_spooky_ticker_varying_reads[expected_index]):
                raise GeneratorError(
                    f"{typed.key}: authenticated SpookyTicker varying read traversal mismatch")
            visited_spooky_ticker_varying_reads.append(value)
        if any(value is item for item in candidate_shape_mixer_guards):
            expected = authorized_shape_mixer_proof.blend_mode_guards
            index = len(visited_shape_mixer_guards)
            if index >= len(expected) or value is not expected[index]:
                raise GeneratorError(
                    f"{typed.key}: authenticated Shape Mixer guard traversal mismatch")
            visited_shape_mixer_guards.append(value)
        if authorized_emboss_proof is not None:
            declarations = tuple(
                table.declaration for table in authorized_emboss_proof.tables)
            stores = tuple(
                store for table in authorized_emboss_proof.tables
                for store in table.literal_stores)
            reads = tuple(
                table.dynamic_read for table in authorized_emboss_proof.tables)
            if any(value is item for item in declarations):
                if any(value is item for item in visited_emboss_declarations):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Emboss declaration visited twice")
                visited_emboss_declarations.append(value)
            if any(value is item for item in stores):
                if any(value is item for item in visited_emboss_stores):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Emboss store visited twice")
                visited_emboss_stores.append(value)
            if any(value is item for item in reads):
                if any(value is item for item in visited_emboss_reads):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Emboss read visited twice")
                visited_emboss_reads.append(value)
            if any(value is item
                   for item in authorized_emboss_proof.
                   texture_coordinate_divisions):
                if any(value is item for item
                       in visited_emboss_materialization_divisions):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Emboss materialization "
                        "visited twice")
                expected_index = len(
                    visited_emboss_materialization_divisions)
                if (expected_index >= len(authorized_emboss_proof.
                                          texture_coordinate_divisions)
                        or value is not authorized_emboss_proof.
                        texture_coordinate_divisions[expected_index]):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Emboss materialization "
                        "traversal out of order")
                visited_emboss_materialization_divisions.append(value)
        if (authorized_glitch_proof is not None
                and any(value is item
                        for item in authorized_glitch_proof.consumed_objects)):
            if any(value is item for item in visited_glitch_matrix_objects):
                raise GeneratorError(
                    f"{typed.key}: authenticated Glitch matrix object visited twice")
            expected_index = len(visited_glitch_matrix_objects)
            if (expected_index >= len(authorized_glitch_proof.consumed_objects)
                    or value is not
                    authorized_glitch_proof.consumed_objects[expected_index]):
                raise GeneratorError(
                    f"{typed.key}: authenticated Glitch matrix traversal out of order")
            visited_glitch_matrix_objects.append(value)
        if authorized_edge_splat_proof is not None:
            splat_expressions = (
                authorized_edge_splat_proof.assignment,
                authorized_edge_splat_proof.target,
                authorized_edge_splat_proof.constructor,
                authorized_edge_splat_proof.dot,
                authorized_edge_splat_proof.dot_target,
                authorized_edge_splat_proof.luma,
            )
            if any(value is item for item in splat_expressions):
                if any(value is item
                       for item in visited_edge_splat_expressions):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Edge center-splat node visited twice")
                visited_edge_splat_expressions.append(value)
        if (authorized_edge_proof is not None
                and any(value is item
                        for item in authorized_edge_proof.bvec_nodes)):
            if any(value is item for item in visited_edge_bvec_nodes):
                raise GeneratorError(
                    f"{typed.key}: authenticated Edge bvec3 node visited twice")
            visited_edge_bvec_nodes.append(value)
        if authorized_bitwise_number_proof is not None:
            authorized = authorized_bitwise_number_proof.consumed_objects
            if any(value is item for item in authorized):
                if any(value is item for item in visited_bitwise_number_objects):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Bitwise Number object visited twice")
                visited_bitwise_number_objects.append(value)
        if any(value is item for item in authorized_texture_frontend_nodes):
            if any(value is item for item in visited_texture_frontend_nodes):
                raise GeneratorError(
                    f"{typed.key}: authenticated Texture bitwise node visited twice")
            if (value.kind != "binary" or value.type.display() != "uint"
                    or len(value.children) != 2
                    or any(child.type.display() != "uint"
                           for child in value.children)):
                raise GeneratorError(
                    f"{location(value)}: malformed authenticated Texture bitwise node")
            visited_texture_frontend_nodes.append(value)
        if (value.type.kind == "sampler"
                and getattr(value.symbol, "storage", None) != "uniform"
                and authorized_focus_blur_proof is None
                and not any(value is item for item in (
                    *authorized_distortion_sampler_parameters,
                    *authorized_distortion_sampler_actuals))
                and not any(getattr(value, "symbol_id", None)
                            == getattr(item, "id", None)
                            for item in authorized_distortion_sampler_parameters)):
            raise GeneratorError(
                f"{location(value)}: unsupported sampler expression")
        if any(value is item for item in authorized_rotate_expressions):
            visited_rotate_expressions.append(value)
        reject_type(value.type, value)
        if value.kind == "construct":
            used.add("constructors")
            if any(value is item for item in authorized_testpattern_array_constructors):
                if any(value is item for item in visited_testpattern_array_constructors):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Test Pattern array constructor visited twice")
                visited_testpattern_array_constructors.append(value)
            if value.type.kind == "matrix":
                if value is authorized_fractal_mat2_constructor:
                    if (value.type.display() != "mat2"
                            or len(value.children) != 3
                            or value.children[0].type.display() != "vec2"
                            or any(child.type.display() != "float"
                                   for child in value.children[1:])):
                        raise GeneratorError(
                            f"{location(value)}: malformed Fractal mat2 constructor")
                elif (authorized_glitch_proof is not None
                        and any(value is item
                                for item in authorized_glitch_proof.constructors)):
                    if (value.type.display() != "mat4"
                            or len(value.children) != 16
                            or any(child.type.display() != "float"
                                   for child in value.children)):
                        raise GeneratorError(
                            f"{location(value)}: unsupported matrix constructor")
                elif value.type.display() == "mat3":
                    if (len(value.children) != 9
                            or any(child.type.display() != "float"
                                   for child in value.children)):
                        raise GeneratorError(
                            f"{location(value)}: unsupported matrix constructor")
                elif (value.type.display() != "mat2" or len(value.children) != 4
                        or any(child.type.display() != "float" for child in value.children)):
                    raise GeneratorError(f"{location(value)}: unsupported matrix constructor")
                used.add("mat2-vector-multiply")
            elif any(child.type.kind == "matrix" for child in value.children):
                raise GeneratorError(f"{location(value)}: unsupported matrix conversion")
        elif value.kind == "binary":
            dither_bitwise_valid = any(value is item for item in authorized_dither_bitwise)
            if (value.operator not in APPROVED_BINARY_OPERATORS
                    and not (value.operator == "<<"
                             and authorized_median_frontend_proof is not None
                             and any(value is item
                                     for item in authorized_median_frontend_proof.expression_nodes
                                     if item.kind == "binary"
                                     and item.operator == "<<"))):
                raise GeneratorError(f"{location(value)}: unsupported binary operator {value.operator}")
            left, right = value.children
            left_type, right_type = left.type.display(), right.type.display()
            if value.operator == "%":
                if left_type not in {"int", "uint"} or right_type != left_type:
                    raise GeneratorError(f"{location(value)}: unsupported binary operator %")
                used.add("integer-modulo")
            elif value.operator == "<<":
                if (value.type.display() != "uint" or len(value.children) != 2
                        or value.children[0].type.display() != "uint"
                        or value.children[1].type.display() != "int"
                        or not any(value is item
                                   for item in authorized_median_frontend_proof.expression_nodes
                                   if item.kind == "binary" and item.operator == "<<")):
                    raise GeneratorError(
                        f"{location(value)}: malformed authenticated Median left shift")
            elif value.operator == ">>":
                if dither_bitwise_valid:
                    pass
                else:
                    median_shift = (
                        authorized_median_frontend_proof is not None
                        and any(value is item
                                for item in authorized_median_frontend_proof.expression_nodes
                                if item.kind == "binary" and item.operator == ">>"))
                    if median_shift:
                        if (value.type.display() != "uint" or len(value.children) != 2
                                or value.children[0].type.display() != "uint"
                                or value.children[1].type.display() != "int"):
                            raise GeneratorError(
                                f"{location(value)}: malformed authenticated Median right shift")
                        # Exact Median shift sites are source-bound; do not
                        # widen the general vector shift capability.
                        pass
                    # Shift count may be a uint scalar (broadcast) or a same-width
                    # uvec (lane-wise). Both stay inside the existing
                    # `uint-vector-bitwise` capability -- no vocabulary growth.
                    if not median_shift and any(value is item for item in authorized_bit_effects_nodes):
                        if (value.type.display() != "uvec3"
                                or len(value.children) != 2
                                or value.children[0].type.display() != "uvec3"
                                or value.children[1].type.display() != "uint"):
                            raise GeneratorError(
                                f"{location(value)}: malformed authenticated BitEffects vector shift")
                        visited_bit_effects_nodes.append(value)
                    elif any(value is item for item in authorized_osd_nodes):
                        if (value.type.display() not in {"int", "uint"}
                                or any(child.type.display() != value.type.display()
                                       for child in value.children)):
                            raise GeneratorError(
                                f"{location(value)}: malformed authenticated OSD shift")
                        visited_osd_nodes.append(value)
                    elif any(value is item for item in authorized_spooky_ticker_nodes):
                        if (value.type.display() not in {"int", "uint"}
                                or any(child.type.display() != value.type.display()
                                       for child in value.children)):
                            raise GeneratorError(
                                f"{location(value)}: malformed authenticated SpookyTicker shift")
                        visited_spooky_ticker_nodes.append(value)
                    elif any(value is item for item in authorized_texture_frontend_nodes):
                        pass
                    elif value is authorized_testpattern_shift:
                        if (left_type, right_type, value.type.display()) != (
                                "int", "int", "int"):
                            raise GeneratorError(
                                f"{location(value)}: malformed authenticated Test Pattern shift")
                        visited_testpattern_shifts.append(value)
                    elif value is (authorized_glyph_map_sites[1]
                                   if authorized_glyph_map_sites else None):
                        if (left_type, right_type, value.type.display()) != (
                                "int", "int", "int"):
                            raise GeneratorError(
                                f"{location(value)}: malformed authenticated Glyph Map shift")
                        visited_glyph_map_sites.append(value)
                    elif median_shift:
                        pass
                    elif (left_type not in {"uvec2", "uvec3", "uvec4"}
                          or right_type not in {"uint", left_type}):
                        raise GeneratorError(f"{location(value)}: unsupported binary operator >>")
                    else:
                        used.add("uint-vector-bitwise")
            elif value.operator == "^":
                if any(value is item for item in authorized_bit_effects_nodes):
                    if (value.type.display() not in {"int", "uint", "uvec3"}
                            or len(value.children) != 2
                            or value.children[0].type.display() != value.type.display()
                            or value.children[1].type.display() != value.type.display()):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated BitEffects XOR")
                    visited_bit_effects_nodes.append(value)
                elif any(value is item for item in authorized_osd_nodes):
                    if (value.type.display() != "uint"
                            or any(child.type.display() != "uint"
                                   for child in value.children)):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated OSD XOR")
                    visited_osd_nodes.append(value)
                elif any(value is item for item in authorized_spooky_ticker_nodes):
                    if (value.type.display() not in {"int", "uint"}
                            or any(child.type.display() != value.type.display()
                                   for child in value.children)):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated SpookyTicker XOR")
                    visited_spooky_ticker_nodes.append(value)
                elif any(value is item for item in authorized_texture_frontend_nodes):
                    pass
                elif any(value is item
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
                elif any(value is item for item in authorized_scalar_uint_xors):
                    if (left_type, right_type, value.type.display()) != (
                            "uint", "uint", "uint") or value.category != "rvalue":
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated scalar uint XOR")
                    visited_scalar_uint_xors.append(value)
                elif any(value is item for item in authorized_bitwise_scalar_int_ops_sites):
                    # Authenticated post-transform by the exact Task35 v2
                    # proof. Operands are JavaScript Number regions and/or
                    # int32 values; the result remains the ToInt32 boundary.
                    if value.type.display() != "int" or len(value.children) != 2:
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated scalar int bitwise op")
                    visited_bitwise_scalar_int_ops_sites.append(value)
                elif dither_bitwise_valid:
                    pass
                else:
                    if (left_type not in {"uvec2", "uvec3", "uvec4"}
                            or right_type != left_type):
                        raise GeneratorError(
                            f"{location(value)}: unsupported binary operator ^")
                    used.add("uint-vector-bitwise")
            elif value.operator in ("&", "|"):
                # `&`/`|` are not otherwise admitted anywhere (no vector
                # form is shipped, unlike `^`/`>>`); scalar int `&`/`|` are
                # admitted only for the exact nodes authenticated by
                # bitwise-scalar-int-ops-v2, by object identity, adding no
                # capability to the vocabulary -- symmetric with the `^`
                # branch above.
                if any(value is item for item in authorized_bit_effects_nodes):
                    if (value.type.display() != "int"
                            or len(value.children) != 2
                            or any(child.type.display() != "int"
                                   for child in value.children)):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated BitEffects scalar bitwise op")
                    visited_bit_effects_nodes.append(value)
                elif any(value is item for item in authorized_osd_nodes):
                    if (value.operator != "&" or value.type.display() != "int"
                            or any(child.type.display() != "int"
                                   for child in value.children)):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated OSD mask")
                    visited_osd_nodes.append(value)
                elif any(value is item for item in authorized_spooky_ticker_nodes):
                    if (value.type.display() not in {"int", "uint"}
                            or any(child.type.display() != value.type.display()
                                   for child in value.children)):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated SpookyTicker mask")
                    visited_spooky_ticker_nodes.append(value)
                elif any(value is item for item in authorized_texture_frontend_nodes):
                    pass
                elif value is authorized_testpattern_mask:
                    if ((left_type, right_type, value.type.display()) != (
                            "int", "int", "int")
                            or value.children[0] is not authorized_testpattern_shift):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated Test Pattern mask")
                    visited_testpattern_masks.append(value)
                elif value is (authorized_glyph_map_sites[0]
                             if authorized_glyph_map_sites else None):
                    if (value.operator != "&"
                            or (left_type, right_type, value.type.display())
                            != ("int", "int", "int")
                            or value.children[0] is not authorized_glyph_map_sites[1]):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated Glyph Map mask")
                    visited_glyph_map_sites.append(value)
                elif any(value is item for item in authorized_bitwise_scalar_int_ops_sites):
                    if value.type.display() != "int" or len(value.children) != 2:
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated scalar int bitwise op")
                    visited_bitwise_scalar_int_ops_sites.append(value)
                elif (authorized_median_frontend_proof is not None
                      and any(value is item
                              for item in authorized_median_frontend_proof.expression_nodes
                              if item.kind == "binary"
                              and item.operator in {"&", "|"})):
                    if (value.type.display() != "uint"
                            or len(value.children) != 2
                            or any(child.type.display() != "uint"
                                   for child in value.children)):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated Median bitwise op")
                elif dither_bitwise_valid:
                    pass
                else:
                    raise GeneratorError(
                        f"{location(value)}: unsupported binary operator {value.operator}")
            elif left.type.kind == "matrix" or right.type.kind == "matrix":
                glitch_products = (() if authorized_glitch_proof is None else
                                   (*authorized_glitch_proof.matrix_products,
                                    *authorized_glitch_proof.vector_products))
                if any(value is item for item in glitch_products):
                    if (value.operator != "*"
                            or (left_type, right_type,
                                value.type.display()) not in {
                                ("mat4", "mat4", "mat4"),
                                ("vec4", "mat4", "vec4"),
                            }):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated Glitch matrix product")
                elif value.operator != "*" or (
                        (left_type, right_type) not in {("mat2", "vec2"), ("mat3", "vec3")}):
                    raise GeneratorError(f"{location(value)}: unsupported matrix binary expression")
                # Same existing capability token, reused rather than renamed --
                # the 44-entry vocabulary is frozen. mat3*vec3 narrows
                # identically to mat2*vec2 (see global-admission-design.md S6):
                # both narrow to f32 exactly once via glsl::Mat<N>*Vec<N,float>.
                used.add("mat2-vector-multiply")
            used.add("scalar-vector-arithmetic")
        elif value.kind == "conditional": used.add("conditional")
        elif value.kind == "swizzle":
            if (value.children and value.children[0].type.display() == "bvec3"):
                nodes = (() if authorized_edge_proof is None
                         else authorized_edge_proof.swizzles)
                if not any(value is item for item in nodes):
                    raise GeneratorError(
                        f"{location(value)}: unsupported bvec3 swizzle")
                if any(value is item for item in visited_edge_swizzles):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Edge swizzle visited twice")
                visited_edge_swizzles.append(value)
            used.add("swizzles")
        elif value.kind == "call":
            used.add("functions")
            if (authorized_inout_vec3_swap_proof is not None
                    and any(value is item
                            for item in authorized_inout_vec3_swap_proof.calls)):
                visited_inout_vec3_swap_calls.append(value)
            if any(value is item for item in authorized_out_inout_calls):
                if any(value is item for item in visited_out_inout_calls):
                    raise GeneratorError(
                        f"{typed.key}: authenticated out/inout call visited twice")
                visited_out_inout_calls.append(value)
        elif value.kind == "builtin":
            if (authorized_texture_frontend_inverse_sqrt is not None
                    and value is authorized_texture_frontend_inverse_sqrt):
                if (value.callee != "inversesqrt"
                        or value.type.display() != "float"
                        or len(value.children) != 1
                        or value.children[0].type.display() != "float"):
                    raise GeneratorError(
                        f"{location(value)}: malformed authenticated Texture inversesqrt")
                if value in visited_texture_frontend_inverse_sqrt:
                    raise GeneratorError(
                        f"{typed.key}: authenticated Texture inversesqrt visited twice")
                visited_texture_frontend_inverse_sqrt.append(value)
                for child in value.children:
                    expression(child)
                return
            if value.callee in {"packHalf2x16", "unpackHalf2x16"}:
                median_builtin = (
                    authorized_median_frontend_proof is not None
                    and any(value is item
                            for item in authorized_median_frontend_proof.expression_nodes
                            if item.kind == "builtin"))
                expected = (("vec2",), "uint") if value.callee == "packHalf2x16" else (("uint",), "vec2")
                if (not median_builtin
                        or value.type.display() != expected[1]
                        or tuple(child.type.display() for child in value.children)
                        != expected[0]):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                # These exact Median packing sites are source-bound proof
                # carriers and must not widen the shared builtin vocabulary.
                for child in value.children:
                    expression(child)
                return
            if any(value is item for item in authorized_mandelbrot_logs):
                if any(value is item for item in visited_mandelbrot_logs):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Mandelbrot log visited twice")
                visited_mandelbrot_logs.append(value)
            elif any(value is item for item in authorized_newton_logs):
                visited_newton_logs.append(value)
            elif value.callee == "round":
                # Admitted for Gather Sorted's fused int(round(x)) site
                # (authorized_round) and, independently, for Posterize's
                # standalone round(float) site (authorized_posterize_round,
                # authenticated by posterize-round-admission-v1). Both are
                # exact node-identity checks; neither widens the vocabulary.
                if (value is not authorized_round
                        and value is not authorized_posterize_round
                        and not any(value is item for item
                                    in (authorized_as_u32_round or ()))
                        and not (testpattern_frontend_proof is not None
                                 and value is testpattern_frontend_proof.round_node)):
                    raise GeneratorError(f"{location(value)}: unsupported builtin round")
                if (testpattern_frontend_proof is not None
                        and value is testpattern_frontend_proof.round_node):
                    if any(value is item for item in visited_testpattern_round_nodes):
                        raise GeneratorError(
                            f"{typed.key}: authenticated Test Pattern round visited twice")
                    visited_testpattern_round_nodes.append(value)
            elif value.callee == "ceil":
                if not any(value is item for item in authorized_ceil):
                    raise GeneratorError(f"{location(value)}: unsupported builtin ceil")
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
                # Admitted only for candidate-owned nodes authenticated by
                # the exact Caustic or Scanline Error identity profile. It
                # never enters the capability vocabulary.
                if any(value is item for item in authorized_bit_effects_nodes):
                    if (value.type.display() != "uint" or len(value.children) != 1
                            or value.children[0].type.display() != "float"):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated BitEffects float-bit ingress")
                    visited_bit_effects_nodes.append(value)
                elif (authorized_caustic_ingress is not None
                        and value is authorized_caustic_ingress):
                    visited_caustic_ingress.append(value)
                elif any(value is item
                         for item in authorized_scanline_error_ingresses):
                    visited_scanline_error_ingresses.append(value)
                elif any(value is item
                         for item in authorized_shapes_float_bits_ingresses):
                    # Shapes' one `floatBitsToUint(seedFrac)`. Admitted by
                    # object identity only, on the same skip-list precedent
                    # as Caustic/Scanline Error: no `used.add(...)`, so the
                    # frozen 44-entry capability vocabulary is unchanged.
                    visited_shapes_float_bits_ingresses.append(value)
                elif any(value is item
                         for item in authorized_kaleido_float_bits_ingress):
                    # kaleido's one `floatBitsToUint(seedFrac)` -- the same
                    # lattice-hash ingress shape, riding its scalar-XOR
                    # carrier (integration-slice discovery; the design's
                    # copy probe stopped at the fixed-array boundary).
                    # Object identity only, no `used.add(...)`.
                    visited_kaleido_float_bits_ingress.append(value)
                elif any(value is item
                         for item in authorized_noise_float_bits_ingress):
                    visited_noise_float_bits_ingress.append(value)
                elif any(value is item
                         for item in authorized_grime_float_bits_ingresses):
                    # grime's five `floatBitsToUint` sites, the whole closure
                    # behind its varying. Object identity only, on the same
                    # skip-list precedent as Caustic/Scanline Error/Shapes:
                    # no `used.add(...)`, so the frozen capability vocabulary
                    # is unchanged.
                    visited_grime_float_bits_ingresses.append(value)
                elif (authorized_shape_mixer_proof is not None
                      and value is authorized_shape_mixer_proof.bit_ingress):
                    visited_shape_mixer_exceptional.append(value)
                elif (authorized_median_frontend_proof is not None
                      and any(value is item
                              for item in authorized_median_frontend_proof.expression_nodes
                              if item.kind == "builtin"
                              and item.callee == "floatBitsToUint")):
                    if (value.type.display() != "uint" or len(value.children) != 1
                            or value.children[0].type.display() != "float"):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated Median float-bit ingress")
                else:
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
            elif value.callee == "equal":
                nodes = (() if authorized_emboss_proof is None
                         else authorized_emboss_proof.equalities)
                if (not any(value is item for item in nodes)
                        or value.type.display() != "bvec2"
                        or len(value.children) != 2
                        or tuple(child.type.display() for child in value.children)
                        != ("vec2", "vec2")):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                if any(value is item for item in visited_emboss_equalities):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Emboss equality visited twice")
                visited_emboss_equalities.append(value)
            elif value.callee in {"all", "lessThanEqual"}:
                # Admitted only for the exact nodes authenticated by
                # extrude-bvec2-relational-reduction-v1, by object identity.
                # Like `round`, these never enter the capability vocabulary.
                authorized_extrude_nodes = (*authorized_extrude_reductions,
                                            *authorized_extrude_relationals)
                emboss_reduction = (
                    value.callee == "all"
                    and authorized_emboss_proof is not None
                    and any(value is item
                            for item in authorized_emboss_proof.reductions))
                if (not emboss_reduction
                        and not any(value is item
                                    for item in authorized_extrude_nodes)):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                if emboss_reduction:
                    if any(value is item
                           for item in visited_emboss_reductions):
                        raise GeneratorError(
                            f"{typed.key}: authenticated Emboss reduction visited twice")
                    visited_emboss_reductions.append(value)
                else:
                    visited_extrude_nodes.append(value)
            elif value.callee in {"greaterThanEqual", "lessThan"}:
                nodes = (() if authorized_edge_proof is None
                         else authorized_edge_proof.relationals)
                if (not any(value is item for item in nodes)
                        or len(value.children) != 2
                        or value.type.display() != "bvec3"
                        or tuple(child.type.display()
                                 for child in value.children)
                        != ("vec3", "vec3")):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                if any(value is item for item in visited_edge_relationals):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Edge relational visited twice")
                visited_edge_relationals.append(value)
            elif value.callee in {"any", "notEqual"}:
                # Admitted only for the exact nodes authenticated by
                # waves-any-notequal-admission-v1, by object identity.
                # Generalizes Extrude's all/lessThanEqual pattern immediately
                # above from `all`/`lessThanEqual` to `any`/`notEqual`. Like
                # `round`, these never enter the capability vocabulary.
                authorized_waves_nodes = (*authorized_waves_reductions,
                                          *authorized_waves_relationals)
                if not any(value is item for item in authorized_waves_nodes):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                visited_waves_nodes.append(value)
            elif value.callee in {"dFdx", "dFdy", "fwidth"}:
                # Admitted only for the exact nodes authenticated by
                # derivative-admission-v1, by object identity. Like
                # round/tanh/floatBitsToUint/all/lessThanEqual, these never
                # enter the frozen 44-entry capability vocabulary.
                if not any(value is item for item in (
                        *authorized_derivative_nodes,
                        *authorized_distortion_derivative_nodes)):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                visited_derivative_nodes.append(value)
                if any(value is item for item in authorized_distortion_derivative_nodes):
                    if any(value is item for item in visited_distortion_derivative_nodes):
                        raise GeneratorError(
                            f"{typed.key}: authenticated Distortion derivative visited twice")
                    visited_distortion_derivative_nodes.append(value)
            elif value.callee in {"reflect", "refract"}:
                # Admitted only for the exact node authenticated by
                # lighting-reflect-admission-v1, by object identity. Like
                # round/tanh/floatBitsToUint/all/lessThanEqual/the
                # derivative trio, this never enters the frozen 44-entry
                # capability vocabulary.
                shape_geometric = (
                    authorized_shape_mixer_proof is not None
                    and (any(value is item for item in
                             authorized_shape_mixer_proof.reflect_nodes)
                         or any(value is item for item in
                                authorized_shape_mixer_proof.refract_nodes)))
                if shape_geometric:
                    visited_shape_mixer_exceptional.append(value)
                elif (value.callee != "reflect"
                      or (value is not authorized_reflect_node
                          and value is not authorized_distortion_reflect_node)):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                else:
                    if value is authorized_distortion_reflect_node:
                        visited_distortion_reflect_nodes.append(value)
                    else:
                        visited_reflect_nodes.append(value)
            elif value.callee == "textureLod":
                # Admitted only for the exact nodes authenticated by
                # texture-lod-admission-parallax-v1 (the curl-tanh precedent:
                # identity sites from the module's own record). The JS alias
                # drops the lod argument, so the sites lower through the
                # existing `texture` path -- never a vocabulary token, never
                # in _BUILTINS.
                if not any(value is item
                           for item in authorized_texture_lod_sites):
                    raise GeneratorError(
                        f"{location(value)}: unsupported builtin {value.callee}")
                visited_texture_lod_sites.append(value)
            elif value.callee not in _BUILTINS:
                raise GeneratorError(f"{location(value)}: unsupported builtin {value.callee}")
            if value.callee == "mod":
                argument_types = tuple(child.type.display() for child in value.children)
                # The shared overload tuple stays untouched so no other program
                # gains wider mod. Curl's three calls are admitted by object
                # identity only.
                if argument_types not in {("float", "float"), ("vec2", "float"), ("vec2", "vec2")}:
                    shape_wide_mod = (
                        authorized_shape_mixer_proof is not None
                        and value is authorized_shape_mixer_proof.wide_mod_node)
                    if shape_wide_mod:
                        visited_shape_mixer_exceptional.append(value)
                    elif not any(value is item for item in authorized_curl_mod_nodes):
                        raise GeneratorError(f"{location(value)}: unsupported builtin mod overload")
                    else:
                        visited_curl_nodes.append(value)
            if value.callee == "texelFetch":
                argument_types = tuple(child.type.display() for child in value.children)
                exact_level_zero = (len(value.children) == 3
                                    and value.children[2].kind == "literal"
                                    and value.children[2].literal == "0"
                                    and value.children[2].literal_value == 0)
                if argument_types != ("sampler2D", "ivec2", "int") or not exact_level_zero:
                    raise GeneratorError(f"{location(value)}: unsupported builtin texelFetch overload")
            # These are admitted by NODE IDENTITY above, never by a vocabulary
            # token, so they must not enter `used` -- the 44-entry vocabulary is
            # frozen and a 45th entry would invalidate every frozen historical
            # hash in the suite.
            shape_profile_builtin = (
                authorized_shape_mixer_proof is not None
                and any(value is item for item
                        in authorized_shape_mixer_proof.exceptional_nodes))
            if (not shape_profile_builtin
                    and value.callee not in {"round", "all", "equal", "lessThanEqual",
                                    "greaterThanEqual", "lessThan",
                                    "floatBitsToUint", "tanh",
                                    "dFdx", "dFdy", "fwidth", "reflect",
                                    "any", "notEqual", "ceil",
                    "textureLod", "log", "log2"}):
                used.add(value.callee)
        elif value.kind == "unary" and value.operator not in {"+", "-", "!"}:
            if (value.operator == "~"
                    and any(value is item
                            for item in authorized_bitwise_scalar_int_ops_sites)):
                # Authenticated by bitwise-scalar-int-ops-v2, same node-
                # identity, zero-vocabulary-growth pattern as the `^`/`&`/`|`
                # sites above. Emission uses the exact JavaScript ToInt32
                # helper boundary rather than a raw signed C++ operator.
                if (value.type.display() != "int"
                        or len(value.children) != 1
                        or value.children[0].type.display() != "int"):
                    raise GeneratorError(
                        f"{location(value)}: malformed authenticated scalar int bitwise op")
                visited_bitwise_scalar_int_ops_sites.append(value)
            else:
                raise GeneratorError(f"{location(value)}: unsupported unary operator {value.operator}")
        elif value.kind == "index":
            dither_index_valid = any(value is item for item in authorized_dither_indexes)
            color_lab_index_valid = any(
                value is item for item in authorized_color_lab_indexes)
            if color_lab_index_valid:
                if (len(value.children) != 2
                        or value.type.display() != "float"
                        or value.children[0].type.display() != "vec3"
                        or value.children[1].type.display() != "int"):
                    raise GeneratorError(
                        f"{location(value)}: authenticated ColorLab index drift")
                expected_index = len(visited_color_lab_indexes)
                if (expected_index >= len(authorized_color_lab_indexes)
                        or value is not authorized_color_lab_indexes[expected_index]):
                    raise GeneratorError(
                        f"{typed.key}: authenticated ColorLab index traversal mismatch")
                visited_color_lab_indexes.append(value)
            if (len(value.children) != 2
                    or (value.children[0].kind != "id"
                        and not color_lab_index_valid and not dither_index_valid)):
                raise GeneratorError(f"{location(value)}: unsupported typed expression index")
            base, index = value.children
            historic_index_valid = (
                authorized_historic_palette_proof is not None
                and any(value is item
                        for item in authorized_historic_palette_proof.palette_index_reads))
            palette_index_valid = (
                authorized_palette_frontend_proof is not None
                and any(value is item
                        for item in authorized_palette_frontend_proof.palette_index_reads))
            if historic_index_valid or palette_index_valid:
                expected_base = ("HistoricPalette[21]" if historic_index_valid
                                 else "PaletteEntry[55]")
                if (base.symbol is None or base.symbol.name != "PALETTES"
                        or base.type.display() != expected_base
                        or (palette_index_valid and index.kind != "binary")
                        or (palette_index_valid and index.operator != "-")):
                    raise GeneratorError(f"{location(value)}: authenticated palette index drift")
                (visited_historic_indexes if historic_index_valid
                 else visited_palette_indexes).append(value)
                return
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
            # Same shape and same zero-vocabulary-growth rationale as
            # grade_valid above, for the shared `linearToSrgb` lane-index
            # closure carried by the mat3 OKLab-transform family
            # (adjust/colorspace/cellNoise).
            linear_srgb_valid = any(
                value is item for item in authorized_linear_srgb_lane_index_sites)
            fractal_valid = any(
                value is item for item in authorized_fractal_frontend_indexes)
            shape_mixer_valid = (
                authorized_shape_mixer_proof is not None
                and any(value is item for item
                        in authorized_shape_mixer_proof.dynamic_indexes))
            testpattern_valid = (
                testpattern_frontend_proof is not None
                and any(value is item.node for item in (
                    *testpattern_frontend_proof.dynamic_indexes,
                    testpattern_frontend_proof.digit_store_index)))
            osd_valid = (
                authorized_osd_proof is not None
                and value is authorized_osd_proof.consumed_objects[2])
            spooky_ticker_valid = (
                authorized_spooky_ticker_proof is not None
                and value is authorized_spooky_ticker_index)
            remap_valid = (
                remap_frontend_proof is not None
                and any(value is item for item in authorized_remap_indexes))
            median_index_valid = any(
                value is item for item in authorized_median_array_indexes)
            # The const file-scope array counted read, admitted purely by
            # NODE IDENTITY against what this authority's own call to
            # `authenticate_const_global_table_reads` returned -- never by a
            # widened `base_valid` (these globals are in no
            # `proved_array_declarations` entry and cannot be, see
            # `reject_type`), never by storage class, never by re-deriving the
            # structure and trusting that the closure's census must have run,
            # and never by a new `used.add(...)` token: the same shape and the
            # same zero-vocabulary-growth rationale as `grade_valid` above.
            #
            # `base` and `index` are checked as the authenticated record's own
            # operands, so the whole site -- not just its root -- is the one
            # the closure proved.
            const_global_table_read = next(
                (item for item in authorized_const_global_table_reads
                 if value is item.node), None)
            const_global_table_valid = (
                const_global_table_read is not None
                and base is const_global_table_read.base
                and index is const_global_table_read.index
                and context == "rvalue")
            # The 45 authenticated element stores of the mutable-global array
            # writer, admitted by SYMBOL IDENTITY -- `base.symbol` IS the
            # declaration object one of the five authenticated declarations
            # carries, the same never-re-matching idiom as the declaration
            # gates above. Lvalue-only and literal-index-only: the closure's
            # frozen write-only census means every rvalue reference to the
            # five would be a read (or a whole-array argument) and must keep
            # raising below. The exact (base, index, span) triples are the
            # closure's own locks; this arm's ledger re-derives the shape of
            # the census at the consuming side.
            mutable_global_array_store = any(
                base.symbol is item.symbol
                for item in authorized_mutable_global_arrays)
            mutable_global_array_store_valid = (
                mutable_global_array_store and context == "lvalue"
                and index.kind == "literal"
                and isinstance(index.literal_value, int))
            newton_root_index_valid = any(
                value is item for item in authorized_newton_root_indexes)
            if color_lab_index_valid:
                pass
            elif dither_index_valid:
                if value in visited_dither_indexes:
                    raise GeneratorError(
                        f"{typed.key}: authenticated Dither index visited twice")
                visited_dither_indexes.append(value)
            elif grade_valid:
                visited_grade_index_sites.append(value)
            elif linear_srgb_valid:
                visited_linear_srgb_lane_index_sites.append(value)
            elif fractal_valid:
                visited_fractal_frontend_indexes.append(value)
            elif shape_mixer_valid:
                visited_shape_mixer_exceptional.append(value)
            elif testpattern_valid:
                if any(value is item for item in visited_testpattern_indexes):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Test Pattern index visited twice")
                visited_testpattern_indexes.append(value)
            elif osd_valid:
                if any(value is item for item in visited_osd_indexes):
                    raise GeneratorError(
                        f"{typed.key}: authenticated OSD index visited twice")
                visited_osd_indexes.append(value)
            elif spooky_ticker_valid:
                if any(value is item for item in visited_spooky_ticker_indexes):
                    raise GeneratorError(
                        f"{typed.key}: authenticated SpookyTicker index visited twice")
                visited_spooky_ticker_indexes.append(value)
            elif remap_valid:
                if any(value is item for item in visited_remap_indexes):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Remap index visited twice")
                visited_remap_indexes.append(value)
            elif median_index_valid:
                if (len(value.children) != 2
                        or base.kind != "id"
                        or base.symbol_id not in {23, 24}
                        or base.type.display() not in {"uvec2[25]", "uint[25]"}
                        or index.kind != "id"):
                    raise GeneratorError(
                        f"{location(value)}: malformed authenticated Median index")
                if value in visited_median_array_indexes:
                    raise GeneratorError(
                        f"{typed.key}: authenticated Median index visited twice")
                visited_median_array_indexes.append(value)
            elif const_global_table_valid:
                visited_const_global_table_reads.append(value)
            elif mutable_global_array_store_valid:
                visited_mutable_global_array_stores.append(
                    (base.symbol_id, index.literal_value))
            elif newton_root_index_valid:
                visited_newton_root_indexes.append(value)
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
        elif value.kind == "member":
            if authorized_historic_palette_proof is not None and any(
                    value is item for item in authorized_historic_members):
                if value in visited_historic_members:
                    raise GeneratorError(f"{typed.key}: authenticated Historic Palette member visited twice")
                visited_historic_members.append(value)
            elif authorized_palette_frontend_proof is not None and any(
                    value is item for item in authorized_palette_members):
                if value in visited_palette_members:
                    raise GeneratorError(f"{typed.key}: authenticated Palette member visited twice")
                visited_palette_members.append(value)
            elif (not any(value is item for item in
                          (authorized_struct_members or ()) )):
                raise GeneratorError(
                    f"{location(value)}: unsupported struct member expression")
        elif value.kind == "post":
            median_post = (
                authorized_median_frontend_proof is not None
                and any(value is item
                        for item in authorized_median_frontend_proof.expression_nodes
                        if item.kind == "post"))
            julia_period_post = (
                authorized_julia_frontend_proof is not None
                and typed.key == JULIA_KEY
                and any(value is item
                        for item in authorized_julia_frontend_proof.consumed_objects)
                and value.operator == "++"
                and len(value.children) == 1
                and value.type.display() == "int"
                and value.children[0].kind == "id"
                and value.children[0].type.display() == "int"
                and value.children[0].symbol is not None
                and value.children[0].symbol.name == "period"
                and value.span.start_line == 228
                and value.span.start_column == 9)
            if (not (median_post or julia_period_post)
                    or value.operator not in {"++", "--"}
                    or len(value.children) != 1
                    or value.type.display() != "int"
                    or value.children[0].kind != "id"
                    or value.children[0].type.display() != "int"):
                raise GeneratorError(f"{location(value)}: unsupported typed expression post")
        elif value.kind not in {"id", "literal", "declaration", "assign", "unary"}:
            raise GeneratorError(f"{location(value)}: unsupported typed expression {value.kind}")
        if value.kind == "assign":
            # Shapes' one rvalue compound assignment. `assign` is ALREADY an
            # approved capability and `*=` an approved operator, so nothing is
            # added to either frozen vocabulary and no `used.add` beyond the
            # pre-existing one below fires. This records visitation only, so
            # the ledger below can prove the authenticated node was reached
            # exactly once -- the validator's half of the boundary the
            # emitter's gated `assign` arm widens.
            if any(value is item for item in authorized_shapes_rvalue_assigns):
                visited_shapes_rvalue_assigns.append(value)
            if value.operator not in APPROVED_ASSIGNMENT_OPERATORS:
                raise GeneratorError(f"{location(value)}: unsupported assignment operator {value.operator}")
            if value.operator == "^=":
                left, right = value.children
                if any(value is item for item in authorized_texture_frontend_assignments):
                    if (left.kind != "id" or left.type.display() != "uint"
                            or right.type.display() != "uint"):
                        raise GeneratorError(
                            f"{location(value)}: malformed authenticated Texture bitwise assignment")
                    if any(value is item for item in visited_texture_frontend_assignments):
                        raise GeneratorError(
                            f"{typed.key}: authenticated Texture bitwise assignment visited twice")
                    visited_texture_frontend_assignments.append(value)
                elif (left.kind != "id" or left.type.display() not in {"uvec2", "uvec3", "uvec4"}
                      or right.type != left.type):
                    raise GeneratorError(f"{location(value)}: unsupported assignment operator ^=")
                else:
                    used.add("uint-vector-bitwise")
            used.add("assign")
        if value.kind == "index":
            if color_lab_index_valid:
                expression(value.children[0])
            expression(value.children[1])
        elif value.kind == "assign":
            expression(value.children[0], "lvalue")
            expression(value.children[1])
        else:
            for child in value.children: expression(child)
    def statement(value, loop_depth: int = 0) -> None:
        if (authorized_edge_splat_proof is not None
                and any(value is item for item
                        in authorized_edge_splat_proof.statement_parent_chain)):
            if any(value is item for item in visited_edge_splat_statements):
                raise GeneratorError(
                    f"{typed.key}: authenticated Edge center-splat statement visited twice")
            visited_edge_splat_statements.append(value)
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
            remap_loop = (
                remap_frontend_proof is not None
                and any(value.loop_proof is item for item in authorized_remap_loops))
            if remap_frontend_proof is not None and not remap_loop:
                raise GeneratorError(
                    f"{location(value)}: unauthenticated Remap counted loop")
            if remap_loop:
                if any(value is item for item in visited_remap_loops):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Remap loop visited twice")
                visited_remap_loops.append(value)
            testpattern_dynamic_loop = (
                testpattern_frontend_proof is not None
                and value.loop_proof is None
                and any(value is item for item
                        in testpattern_frontend_proof.consumed_objects))
            dither_loop = any(value is item for item in authorized_dither_loops)
            if testpattern_dynamic_loop:
                if any(value is item for item in visited_testpattern_dynamic_loops):
                    raise GeneratorError(
                        f"{typed.key}: authenticated Test Pattern dynamic loop visited twice")
                visited_testpattern_dynamic_loops.append(value)
            if ((value.loop_proof is None
                 and not testpattern_dynamic_loop and not dither_loop)
                    or len(value.expressions) != 2 or len(value.children) != 2):
                raise GeneratorError(f"{location(value)}: unsupported typed statement for")
            used.add("counted-for-v1")
            statement(value.children[0], loop_depth)
            expression(value.expressions[0])
            statement(value.children[1], loop_depth + 1)
            return
        elif value.kind == "while":
            median_while = authorized_median_frontend_proof is not None
            span = value.span
            span_key = (f"{span.start_line}:{span.start_column}-"
                        f"{span.end_line}:{span.end_column}")
            if not median_while:
                raise GeneratorError(f"{location(value)}: unsupported typed statement while")
            expected = len(visited_median_whiles)
            if (expected >= len(authorized_median_frontend_proof.unproved_while_spans)
                    or span_key != authorized_median_frontend_proof.unproved_while_spans[expected]):
                raise GeneratorError(
                    f"{location(value)}: authenticated Median while traversal mismatch")
            visited_median_whiles.append(value)
            if len(value.expressions) != 1 or len(value.children) != 1:
                raise GeneratorError(f"{location(value)}: malformed authenticated Median while")
            used.add("counted-for-v1")
            expression(value.expressions[0])
            statement(value.children[0], loop_depth + 1)
            return
        elif value.kind in {"break", "continue"}:
            if loop_depth == 0:
                raise GeneratorError(f"{location(value)}: unsupported typed statement {value.kind}")
            used.add("counted-for-v1")
            return
        elif value.kind not in {"decl", "expr", "return"}:
            raise GeneratorError(f"{location(value)}: unsupported typed statement {value.kind}")
        # A `return` inside a loop is admitted. Soundness is already argued in
        # loop_proof.py: an early return can only SHORTEN the iterations
        # actually executed relative to the proved upper bound, never extend
        # them, so the trip-count proof remains a sound upper bound. Landed
        # with filter/smooth:smoothBlend, whose SMAA `searchEdge` returns from
        # inside its 32-iteration scan.
        #
        # This is NOT a blanket relaxation: a return inside an UNPROVED loop is
        # still rejected, because the whole-program counted-for proof rejects
        # any program containing an unproved loop before this point. The
        # near-miss barrier was moved to that new boundary accordingly.
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
            if authorized_bitwise_number_proof is not None:
                authorized = authorized_bitwise_number_proof.consumed_objects
                if any(parameter is item for item in authorized):
                    if any(parameter is item
                           for item in visited_bitwise_number_objects):
                        raise GeneratorError(
                            f"{typed.key}: authenticated Bitwise Number parameter visited twice")
                    visited_bitwise_number_objects.append(parameter)
            reject_type(parameter.type, parameter)
            if (parameter.type.kind == "sampler"
                    and (authorized_focus_blur_proof is None
                         or function is not authorized_focus_blur_proof.helper
                         or not any(parameter is item for item in
                                    authorized_focus_blur_proof.sampler_parameters))
                    and not any(parameter is item
                                for item in authorized_distortion_sampler_parameters)):
                raise GeneratorError(
                    f"{location(parameter)}: unsupported sampler parameter")
            if parameter.type.kind == "matrix":
                raise GeneratorError(f"{location(parameter)}: unsupported matrix parameter")
            if parameter.direction != "in":
                if (authorized_inout_vec3_swap_proof is not None
                        and function is authorized_inout_vec3_swap_proof.function
                        and any(parameter is item
                                for item in authorized_inout_vec3_swap_proof.parameters)):
                    pass
                elif any(parameter is item
                         for item in authorized_out_inout_parameters):
                    if any(parameter is item for item in visited_out_inout_parameters):
                        raise GeneratorError(
                            f"{typed.key}: authenticated out/inout parameter visited twice")
                    visited_out_inout_parameters.append(parameter)
                else:
                    raise GeneratorError(
                        f"{typed.key}:{parameter.span.start_line}:{parameter.span.start_column}: "
                        f"unsupported parameter direction {parameter.direction}")
        for statement_value in function.body: statement(statement_value)
    if authorized_historic_palette_proof is not None:
        if (visited_historic_indexes != list(authorized_historic_palette_proof.palette_index_reads)
                or visited_historic_members != list(authorized_historic_members)):
            raise GeneratorError(f"{typed.key}: authenticated Historic Palette traversal mismatch")
    if authorized_palette_frontend_proof is not None:
        if (visited_palette_indexes != list(authorized_palette_frontend_proof.palette_index_reads)
                or visited_palette_members != list(authorized_palette_members)):
            raise GeneratorError(f"{typed.key}: authenticated Palette traversal mismatch")
    if (authorized_color_lab_frontend_proof is not None
            and not _same_object_sequence(
                visited_color_lab_indexes, authorized_color_lab_indexes)):
        raise GeneratorError(
            f"{typed.key}: authenticated ColorLab index traversal mismatch")
    if authorized_median_frontend_proof is not None:
        if (not _same_object_sequence(
                visited_median_array_declarations,
                authorized_median_array_declarations)
                or not _same_object_sequence(
                    visited_median_array_indexes,
                    authorized_median_array_indexes)):
            raise GeneratorError(
                f"{typed.key}: authenticated Median fixed-array traversal mismatch")
        if len(visited_median_whiles) != len(
                authorized_median_frontend_proof.unproved_while_spans):
            raise GeneratorError(
                f"{typed.key}: authenticated Median while traversal mismatch")
    if authorized_osd_proof is not None:
        expected_array = authorized_osd_proof.consumed_objects[0]
        if (len(visited_osd_globals) != 1
                or visited_osd_globals[0] is not expected_array
                or tuple(visited_osd_nodes) != authorized_osd_nodes
                or tuple(visited_osd_indexes)
                != (authorized_osd_proof.consumed_objects[2],)):
            raise GeneratorError(
                f"{typed.key}: authenticated OSD traversal mismatch")
    if authorized_spooky_ticker_proof is not None:
        if (visited_spooky_ticker_globals != [authorized_spooky_ticker_global]
                or tuple(visited_spooky_ticker_nodes)
                != authorized_spooky_ticker_nodes
                or tuple(visited_spooky_ticker_indexes)
                != (authorized_spooky_ticker_index,)
                or tuple(visited_spooky_ticker_varying_reads)
                != authorized_spooky_ticker_varying_reads):
            raise GeneratorError(
                f"{typed.key}: authenticated SpookyTicker traversal mismatch")
    if testpattern_frontend_proof is not None:
        expected_array_declarations = tuple(authorized_testpattern_array_declarations)
        if (len(visited_testpattern_array_types) != 3
                or len({id(item) for item in visited_testpattern_array_types}) != 3
                or any(not any(item is expected
                               for item in visited_testpattern_array_types)
                       for expected in expected_array_declarations)):
            raise GeneratorError(
                f"{typed.key}: authenticated Test Pattern array declaration/type traversal mismatch")
        expected_array_constructors = tuple(authorized_testpattern_array_constructors)
        if (len(visited_testpattern_array_constructors) != 2
                or any(left is not right for left, right in zip(
                    visited_testpattern_array_constructors,
                    expected_array_constructors))):
            raise GeneratorError(
                f"{typed.key}: authenticated Test Pattern array constructor traversal mismatch")
        expected_indexes = tuple(item.node for item in (
            *testpattern_frontend_proof.dynamic_indexes,
            testpattern_frontend_proof.digit_store_index))
        if (len(visited_testpattern_indexes) != 4
                or len({id(item) for item in visited_testpattern_indexes}) != 4
                or any(not any(item is expected for item in visited_testpattern_indexes)
                       for expected in expected_indexes)):
            raise GeneratorError(
                f"{typed.key}: authenticated Test Pattern index traversal mismatch")
        if (tuple(visited_testpattern_round_nodes)
                != (testpattern_frontend_proof.round_node,)):
            raise GeneratorError(
                f"{typed.key}: authenticated Test Pattern round traversal mismatch")
        if (tuple(visited_testpattern_dynamic_loops)
                != tuple(item for item in testpattern_frontend_proof.consumed_objects
                         if getattr(item, "kind", None) == "for"
                         and getattr(item, "loop_proof", None) is None)):
            raise GeneratorError(
                f"{typed.key}: authenticated Test Pattern dynamic-loop traversal mismatch")
        if (tuple(visited_testpattern_shifts)
                != (authorized_testpattern_shift,)
                or tuple(visited_testpattern_masks)
                != (authorized_testpattern_mask,)):
            raise GeneratorError(
                f"{typed.key}: authenticated Test Pattern bitwise traversal mismatch")
    if remap_frontend_proof is not None:
        expected_indexes = tuple(item.node for item in remap_frontend_proof.indexes)
        if (tuple(visited_remap_indexes) != expected_indexes
                or len(visited_remap_uniform_blocks) != 1
                or visited_remap_uniform_blocks[0]
                is not remap_frontend_proof.uniform_block
                or tuple(item.loop_proof for item in visited_remap_loops)
                != authorized_remap_loops):
            raise GeneratorError(
                f"{typed.key}: authenticated Remap traversal mismatch")
    if authorized_out_inout_parameters:
        if (len(visited_out_inout_parameters)
                != len(authorized_out_inout_parameters)
                or any(not any(value is item
                               for item in visited_out_inout_parameters)
                       for value in authorized_out_inout_parameters)):
            raise GeneratorError(
                f"{typed.key}: authenticated out/inout parameter visitation mismatch")
    if authorized_out_inout_calls:
        if (len(visited_out_inout_calls) != len(authorized_out_inout_calls)
                or any(not any(value is item for item in visited_out_inout_calls)
                       for value in authorized_out_inout_calls)):
            raise GeneratorError(
                f"{typed.key}: authenticated out/inout call visitation mismatch")
    if authorized_newton_root_indexes:
        if tuple(visited_newton_root_indexes) != authorized_newton_root_indexes:
            raise GeneratorError(
                f"{typed.key}: authenticated Newton root-index traversal mismatch")
    if authorized_newton_logs:
        if tuple(visited_newton_logs) != authorized_newton_logs:
            raise GeneratorError(
                f"{typed.key}: authenticated Newton log traversal mismatch")
    if authorized_mandelbrot_logs:
        if tuple(visited_mandelbrot_logs) != authorized_mandelbrot_logs:
            raise GeneratorError(
                f"{typed.key}: authenticated Mandelbrot log traversal mismatch")
    if authorized_mutable_global_arrays:
        # The walk-side restatement of the closure's write-only census: the
        # index arm above must have visited exactly the record's element
        # stores (45 for the five-array keys, 63 for effects -- the record's
        # own store census, per key since the effects row) -- every admitted
        # base at exactly the nine indices 0..8 -- and nothing else. A
        # mutated tree never reaches here (the closure's whole-program
        # fingerprint freezes it); this ledger is what names a walk-side arm
        # that over- or under-admits on the authentic tree.
        per_base: dict[int, list[int]] = {}
        for symbol_id, literal_index in visited_mutable_global_array_stores:
            per_base.setdefault(symbol_id, []).append(literal_index)
        if (len(visited_mutable_global_array_stores)
                != mutable_global_array_store_census(typed.key)
                or {key for key in per_base} != {
                    item.symbol.id
                    for item in authorized_mutable_global_arrays}
                or any(sorted(values) != list(range(9))
                       for values in per_base.values())):
            raise GeneratorError(
                f"{typed.key}: authenticated mutable-global array store "
                f"visitation mismatch")
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
    if (authorized_scalar_uint_xors
            and tuple(visited_scalar_uint_xors) != authorized_scalar_uint_xors):
        raise GeneratorError(
            f"{typed.key}: authenticated scalar uint XOR traversal mismatch")
    if (authorized_bitwise_scalar_int_ops_sites
            and tuple(visited_bitwise_scalar_int_ops_sites)
            != authorized_bitwise_scalar_int_ops_sites):
        raise GeneratorError(
            f"{typed.key}: authenticated scalar int bitwise-op traversal mismatch")
    if (authorized_texture_frontend_nodes
            and tuple(visited_texture_frontend_nodes)
            != authorized_texture_frontend_nodes):
        raise GeneratorError(
            f"{typed.key}: authenticated Texture bitwise traversal mismatch")
    if (authorized_texture_frontend_assignments
            and tuple(visited_texture_frontend_assignments)
            != authorized_texture_frontend_assignments):
        raise GeneratorError(
            f"{typed.key}: authenticated Texture bitwise assignment traversal mismatch")
    if (authorized_texture_frontend_inverse_sqrt is not None
            and tuple(visited_texture_frontend_inverse_sqrt)
            != (authorized_texture_frontend_inverse_sqrt,)):
        raise GeneratorError(
            f"{typed.key}: authenticated Texture inversesqrt traversal mismatch")
    if authorized_bit_effects_proof is not None:
        proof = authorized_bit_effects_proof
        expected = proof.consumed_objects
        visited_ids = [id(item) for item in visited_bit_effects_nodes]
        category_order = (
            proof.scalar_int_bitwise_nodes,
            proof.float_bits_to_uint_nodes,
            proof.vector_uint_bitwise_nodes,
            proof.scalar_uint_xor_nodes)
        if (len(visited_ids) != len(expected)
                or len(set(visited_ids)) != len(expected)
                or set(visited_ids) != {id(item) for item in expected}
                or any(tuple(item for item in visited_bit_effects_nodes
                            if any(item is candidate for candidate in category))
                       != category for category in category_order)
                or tuple(visited_bit_effects_globals)
                != proof.global_const_declarations):
            raise GeneratorError(
                f"{typed.key}: authenticated BitEffects traversal mismatch")
    if (authorized_bitwise_number_proof is not None
            and len(visited_bitwise_number_objects)
            != len(authorized_bitwise_number_proof.consumed_objects)):
        raise GeneratorError(
            f"{typed.key}: authenticated Bitwise Number traversal mismatch")
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
    if authorized_texture_lod_proof is not None:
        if (len(visited_texture_lod_sites)
                != len(authorized_texture_lod_sites)
                or any(left is not right for left, right in zip(
                    visited_texture_lod_sites,
                    authorized_texture_lod_sites))):
            raise GeneratorError(
                f"{typed.key}: authenticated textureLod admission traversal "
                "mismatch")
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
    if authorized_scanline_error_ingresses:
        if (len(visited_scanline_error_ingresses)
                != len(authorized_scanline_error_ingresses)
                or any(left is not right for left, right in zip(
                    visited_scanline_error_ingresses,
                    authorized_scanline_error_ingresses))):
            raise GeneratorError(
                f"{typed.key}: authenticated Scanline Error traversal mismatch")
    if authorized_shapes_float_bits_ingresses:
        if (len(visited_shapes_float_bits_ingresses)
                != len(authorized_shapes_float_bits_ingresses)
                or any(left is not right for left, right in zip(
                    visited_shapes_float_bits_ingresses,
                    authorized_shapes_float_bits_ingresses))):
            raise GeneratorError(
                f"{typed.key}: authenticated Shapes float-bit ingress traversal mismatch")
    if authorized_grime_float_bits_ingresses:
        if (len(visited_grime_float_bits_ingresses)
                != len(authorized_grime_float_bits_ingresses)
                or any(left is not right for left, right in zip(
                    visited_grime_float_bits_ingresses,
                    authorized_grime_float_bits_ingresses))):
            raise GeneratorError(
                f"{typed.key}: authenticated grime float-bit ingress traversal mismatch")
    if authorized_kaleido_float_bits_ingress:
        if (len(visited_kaleido_float_bits_ingress)
                != len(authorized_kaleido_float_bits_ingress)
                or any(left is not right for left, right in zip(
                    visited_kaleido_float_bits_ingress,
                    authorized_kaleido_float_bits_ingress))):
            raise GeneratorError(
                f"{typed.key}: authenticated kaleido float-bit ingress traversal mismatch")
    if authorized_noise_float_bits_ingress:
        if (len(visited_noise_float_bits_ingress)
                != len(authorized_noise_float_bits_ingress)
                or any(left is not right for left, right in zip(
                    visited_noise_float_bits_ingress,
                    authorized_noise_float_bits_ingress))):
            raise GeneratorError(
                f"{typed.key}: authenticated Noise float-bit ingress traversal mismatch")
    if authorized_shapes_rvalue_assigns:
        if (len(visited_shapes_rvalue_assigns)
                != len(authorized_shapes_rvalue_assigns)
                or any(left is not right for left, right in zip(
                    visited_shapes_rvalue_assigns,
                    authorized_shapes_rvalue_assigns))):
            raise GeneratorError(
                f"{typed.key}: authenticated Shapes rvalue-assign traversal mismatch")
    if authorized_glyph_map_sites:
        if (len(visited_glyph_map_sites) != 2
                or visited_glyph_map_sites != [
                    authorized_glyph_map_sites[0],
                    authorized_glyph_map_sites[1]]):
            raise GeneratorError(
                f"{typed.key}: authenticated Glyph Map traversal mismatch")
    if authorized_reflect_node is not None and (
            len(visited_reflect_nodes) != 1
            or visited_reflect_nodes[0] is not authorized_reflect_node):
        raise GeneratorError(
            f"{typed.key}: authenticated Reflect traversal mismatch")
    if authorized_distortion_reflect_node is not None and (
            len(visited_distortion_reflect_nodes) != 1
            or visited_distortion_reflect_nodes[0] is not authorized_distortion_reflect_node):
        raise GeneratorError(
            f"{typed.key}: authenticated Distortion reflect traversal mismatch")
    if (authorized_shape_mixer_proof is not None
            and (not _same_object_sequence(
                visited_shape_mixer_exceptional,
                authorized_shape_mixer_proof.exceptional_nodes)
                 or not _same_object_sequence(
                     visited_shape_mixer_guards,
                     candidate_shape_mixer_guards)
                 or not _same_object_sequence(
                     visited_shape_mixer_guards,
                     authorized_shape_mixer_proof.blend_mode_guards))):
        raise GeneratorError(
            f"{typed.key}: authenticated Shape Mixer traversal mismatch")
    if authorized_extrude_proof is not None:
        authorized_nodes = (*authorized_extrude_reductions,
                            *authorized_extrude_relationals)
        if len(visited_extrude_nodes) != len(authorized_nodes) or any(
                not any(value is item for item in visited_extrude_nodes)
                for value in authorized_nodes):
            raise GeneratorError(
                f"{typed.key}: authenticated Extrude traversal mismatch")
    if authorized_edge_proof is not None:
        if (tuple(visited_edge_bvec_nodes)
                != authorized_edge_proof.bvec_nodes
                or tuple(visited_edge_relationals)
                != authorized_edge_proof.relationals
                or tuple(visited_edge_swizzles)
                != authorized_edge_proof.swizzles):
            raise GeneratorError(
                f"{typed.key}: authenticated Edge traversal mismatch")
    if authorized_edge_splat_proof is not None:
        expected_expressions = (
            authorized_edge_splat_proof.assignment,
            authorized_edge_splat_proof.target,
            authorized_edge_splat_proof.constructor,
            authorized_edge_splat_proof.dot,
            authorized_edge_splat_proof.dot_target,
            authorized_edge_splat_proof.luma,
        )
        if (tuple(visited_edge_splat_statements)
                != authorized_edge_splat_proof.statement_parent_chain
                or tuple(visited_edge_splat_expressions)
                != expected_expressions):
            raise GeneratorError(
                f"{typed.key}: authenticated Edge center-splat traversal mismatch")
    if (authorized_glitch_proof is not None
            and tuple(visited_glitch_matrix_objects)
            != authorized_glitch_proof.consumed_objects):
        raise GeneratorError(
            f"{typed.key}: authenticated Glitch matrix traversal mismatch")
    if authorized_emboss_proof is not None:
        expected_declarations = tuple(
            table.declaration for table in authorized_emboss_proof.tables)
        expected_stores = tuple(
            store for table in authorized_emboss_proof.tables
            for store in table.literal_stores)
        expected_reads = (
            authorized_emboss_proof.tables[1].dynamic_read,
            authorized_emboss_proof.tables[0].dynamic_read,
            authorized_emboss_proof.tables[3].dynamic_read,
            authorized_emboss_proof.tables[2].dynamic_read,
        )
        if (not _same_object_sequence(
                    visited_emboss_declarations, expected_declarations)
                or not _same_object_sequence(
                    visited_emboss_stores, expected_stores)
                or not _same_object_sequence(
                    visited_emboss_reads, expected_reads)
                or not _same_object_sequence(
                    visited_emboss_equalities,
                    authorized_emboss_proof.equalities)
                or not _same_object_sequence(
                    visited_emboss_reductions,
                    authorized_emboss_proof.reductions)
                or not _same_object_sequence(
                    visited_emboss_materialization_divisions,
                    authorized_emboss_proof.texture_coordinate_divisions)):
            raise GeneratorError(
                f"{typed.key}: authenticated Emboss traversal mismatch")
    if authorized_waves_relationals or authorized_waves_reductions:
        authorized_waves_all_nodes = (*authorized_waves_reductions,
                                      *authorized_waves_relationals)
        if len(visited_waves_nodes) != len(authorized_waves_all_nodes) or any(
                not any(value is item for item in visited_waves_nodes)
                for value in authorized_waves_all_nodes):
            raise GeneratorError(
                f"{typed.key}: authenticated Waves traversal mismatch")
    if authorized_inout_vec3_swap_proof is not None and (
            len(visited_inout_vec3_swap_calls) != len(authorized_inout_vec3_swap_proof.calls)
            or any(not any(value is item for item in visited_inout_vec3_swap_calls)
                   for value in authorized_inout_vec3_swap_proof.calls)):
        raise GeneratorError(
            f"{typed.key}: authenticated inout vec3 swap traversal mismatch")
    if authorized_grade_index_sites and (
            len(visited_grade_index_sites) != len(authorized_grade_index_sites)
            or any(not any(value is item for item in visited_grade_index_sites)
                   for value in authorized_grade_index_sites)):
        raise GeneratorError(
            f"{typed.key}: authenticated Grade index expression traversal mismatch")
    if authorized_linear_srgb_lane_index_sites and (
            len(visited_linear_srgb_lane_index_sites)
            != len(authorized_linear_srgb_lane_index_sites)
            or any(not any(value is item for item in visited_linear_srgb_lane_index_sites)
                   for value in authorized_linear_srgb_lane_index_sites)):
            raise GeneratorError(
                f"{typed.key}: authenticated Linear sRGB lane index traversal mismatch")
    if authorized_fractal_frontend_indexes and (
            len(visited_fractal_frontend_indexes)
            != len(authorized_fractal_frontend_indexes)
            or any(not any(value is item
                           for value in visited_fractal_frontend_indexes)
                   for item in authorized_fractal_frontend_indexes)):
        raise GeneratorError(
            f"{typed.key}: authenticated Fractal lane index traversal mismatch")
    if authorized_derivative_proof is not None:
        expected = authorized_derivative_proof.nodes
        if len(visited_derivative_nodes) != len(expected) or any(
                not any(value is item for item in visited_derivative_nodes)
                for value in expected):
            raise GeneratorError(
                f"{typed.key}: authenticated Derivative traversal mismatch")
    if authorized_distortion_derivative_nodes and (
            len(visited_distortion_derivative_nodes)
            != len(authorized_distortion_derivative_nodes)
            or any(value is not expected for value, expected in zip(
                visited_distortion_derivative_nodes,
                authorized_distortion_derivative_nodes))
            or len({id(value) for value in visited_distortion_derivative_nodes})
            != len(visited_distortion_derivative_nodes)):
        raise GeneratorError(
            f"{typed.key}: authenticated Distortion derivative traversal mismatch")
    if authorized_const_global_table_reads:
        # Every authenticated read node reached exactly once, by identity, in
        # the frozen declaration order. A site that stops being traversed, is
        # traversed twice, or arrives out of order fails here.
        expected_reads = [item.node
                          for item in authorized_const_global_table_reads]
        if (len(visited_const_global_table_reads) != len(expected_reads)
                or any(item is not expected for item, expected in zip(
                    visited_const_global_table_reads, expected_reads))):
            raise GeneratorError(
                f"{typed.key}: authenticated const-global nine-table "
                "read traversal mismatch")
    missing = sorted(used - set(capabilities))
    if missing: raise GeneratorError(f"{typed.key}: missing capabilities {', '.join(missing)}")


def generate_outputs(repository: pathlib.Path = _ROOT) -> dict[str, bytes]:
    repository = repository.resolve()
    check_corpus.validate_corpus(repository)
    semantic = check_semantics.semantic_report(repository)
    if semantic["body_success"] != 212: raise GeneratorError("semantic analysis did not cover corpus")
    slice_spec = load_slice(repository)
    if slice_spec["revision"] != check_corpus.REVISION: raise GeneratorError("typed slice revision drift")
    blur_runtime_preflight = any(
        item["program_key"] in BLUR_KEYS
        and item.get("runtime_loop_bound_profile") == RUNTIME_LOOP_BOUND_PROFILE
        for item in slice_spec["programs"])
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
        if (metadata_defines != declared_defines
                and not (key == MEDIAN_KEY
                         and declared_defines == {"RADIUS": 2}
                         and metadata_defines == {"RADIUS": 3})):
            raise GeneratorError(f"{key}: authoritative metadata default defines drift")
        source_global_literal_int_profile = (
            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY
            if key in SOURCE_GLOBAL_LITERAL_INT_KEYS else None)
        dynamic_noise = (
            key == NOISE_RUNTIME_DEFINE_KEY
            and slice_spec["programs"][index].get(
                "runtime_define_profile") == NOISE_RUNTIME_DEFINE_PROFILE)
        parse_source = transform_noise_source(source, key) if dynamic_noise else source
        dynamic_defines = NOISE_DYNAMIC_DEFINES if dynamic_noise else declared_defines
        parsed = parse_program(parse_source, key, dynamic_defines)
        # Keep the immutable authority bytes distinct from the normalized
        # source transform.  The transform is line-preserving, so parser spans
        # continue to refer to the pinned source lines.
        if dynamic_noise:
            parsed["raw_source"] = source
        typed = analyze_program(
            parsed, key,
            source_global_literal_int_profile=source_global_literal_int_profile)
        runtime_loop_bound_profile = slice_spec["programs"][index].get(
            "runtime_loop_bound_profile")
        gabor_effective_depth_profile = slice_spec["programs"][index].get(
            "gabor_effective_depth_profile")
        if key in RUNTIME_LOOP_BOUND_KEYS:
            try:
                if key == TETRA_KEY:
                    validate_tetra_metadata(
                        metadata.get("effects", {}).get("filter/tetraColorArray"))
                elif key in BLUR_KEYS:
                    validate_blur_metadata(
                        metadata.get("effects", {}).get("filter/blur"))
                elif key == RUNTIME_LOOP_BOUND_NOISE_KEY:
                    validate_noise_metadata(
                        metadata.get("effects", {}).get("synth/noise"))
                typed = apply_runtime_loop_bound(
                    typed, source_hash, runtime_loop_bound_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
        elif runtime_loop_bound_profile is not None:
            raise GeneratorError(
                f"{key}: runtime-loop-bound carrier on foreign key")
        if key == GABOR_KEY:
            try:
                validate_gabor_metadata(
                    metadata.get("effects", {}).get("synth/gabor"))
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
        elif gabor_effective_depth_profile is not None:
            raise GeneratorError(
                f"{key}: Gabor effective-depth carrier on foreign key")
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
        testpattern_row_profile = slice_spec["programs"][index].get(
            "testpattern_profile")
        authorized_testpattern_proof = None
        if testpattern_row_profile is not None:
            if key != TESTPATTERN_KEY or testpattern_row_profile != TESTPATTERN_PROFILE:
                raise GeneratorError(
                    f"{key}: Test Pattern frontend profile metadata mismatch")
            try:
                binding_preflight = preflight_testpattern_bindings(typed)
                authorized_testpattern_proof = authenticate_testpattern_frontend(
                    typed, source_hash, testpattern_row_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if authorized_testpattern_proof.binding_preflight is not binding_preflight:
                raise GeneratorError(
                    f"{key}: Test Pattern binding proof identity mismatch")
        elif key == TESTPATTERN_KEY:
            raise GeneratorError(
                f"{key}: exact Test Pattern frontend profile carrier required")
        osd_frontend_profile = slice_spec["programs"][index].get(
            "osd_frontend_profile")
        authorized_osd_proof = None
        if osd_frontend_profile is not None:
            if key != OSD_KEY or osd_frontend_profile != OSD_FRONTEND_PROFILE:
                raise GeneratorError(f"{key}: OSD frontend profile metadata mismatch")
            try:
                authorized_osd_proof = authenticate_osd_frontend(
                    typed, source_hash, osd_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
        elif key == OSD_KEY:
            raise GeneratorError(f"{key}: exact OSD frontend profile carrier required")
        remap_row_profile = slice_spec["programs"][index].get("remap_profile")
        authorized_remap_proof = None
        if remap_row_profile is not None:
            if key != REMAP_KEY or remap_row_profile != REMAP_PROFILE:
                raise GeneratorError(
                    f"{key}: Remap frontend profile metadata mismatch")
            try:
                binding_preflight = preflight_remap_bindings(typed)
                authorized_remap_proof = authenticate_remap_frontend(
                    typed, source_hash, remap_row_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if authorized_remap_proof.binding_preflight is not binding_preflight:
                raise GeneratorError(
                    f"{key}: Remap binding proof identity mismatch")
        elif key == REMAP_KEY:
            raise GeneratorError(
                f"{key}: exact Remap frontend profile carrier required")
        moodscape_frontend_profile = slice_spec["programs"][index].get(
            "moodscape_frontend_profile")
        if moodscape_frontend_profile is not None:
            if (key not in MOODSCAPE_PREPARED_KEYS
                    or moodscape_frontend_profile
                    != MOODSCAPE_PREPARED_PROFILES[key]):
                raise GeneratorError(
                    f"{key}: Moodscape frontend profile metadata mismatch")
            try:
                profiled = apply_moodscape_frontend(
                    typed, source_hash, moodscape_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is typed:
                raise GeneratorError(
                    f"{key}: Moodscape frontend projection did not transform program")
            typed = profiled
        elif key in MOODSCAPE_PREPARED_KEYS:
            raise GeneratorError(
                f"{key}: exact Moodscape frontend profile carrier required")
        noise_frontend_profile = slice_spec["programs"][index].get(
            "noise_frontend_profile")
        if noise_frontend_profile is not None:
            if (key != NOISE_FRONTEND_KEY
                    or noise_frontend_profile != NOISE_FRONTEND_PROFILE):
                raise GeneratorError(
                    f"{key}: Classic Noise frontend profile metadata mismatch")
            try:
                profiled = apply_noise_frontend(
                    typed, source_hash, noise_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is typed:
                raise GeneratorError(
                    f"{key}: Classic Noise frontend projection did not transform program")
            typed = profiled
        elif key == NOISE_FRONTEND_KEY:
            raise GeneratorError(
                f"{key}: exact Classic Noise frontend profile carrier required")
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
        posterize_round_profile = slice_spec["programs"][index].get(
            "posterize_round_profile")
        if posterize_round_profile is not None:
            try:
                profiled = apply_posterize_round_admission(
                    typed, source_hash, posterize_round_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(f"{key}: Posterize round admission identity profile mutated program")
            typed = profiled
        as_u32_round_profile = slice_spec["programs"][index].get(
            "as_u32_round_profile")
        ceil_admission_profile = slice_spec["programs"][index].get(
            "ceil_admission_profile")
        if as_u32_round_profile is not None:
            try:
                profiled = apply_as_u32_round_admission(
                    typed, source_hash, as_u32_round_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(f"{key}: as_u32 round admission identity profile mutated program")
            typed = profiled
        waves_any_notequal_profile = slice_spec["programs"][index].get(
            "waves_any_notequal_profile")
        if waves_any_notequal_profile is not None:
            try:
                profiled = apply_waves_any_notequal_admission(
                    typed, source_hash, waves_any_notequal_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(f"{key}: Waves any/notEqual admission identity profile mutated program")
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
        scalar_uint_xor_profile = slice_spec["programs"][index].get(
            "scalar_uint_xor_profile")
        if scalar_uint_xor_profile is not None:
            try:
                profiled = apply_scalar_uint_xor(
                    typed, source_hash, scalar_uint_xor_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: scalar uint XOR identity profile mutated program")
            typed = profiled
        shape_mixer_builtin_profile = slice_spec["programs"][index].get(
            "shape_mixer_builtin_profile")
        if shape_mixer_builtin_profile is not None:
            try:
                profiled = apply_shape_mixer_builtin_closure(
                    typed, source_hash, shape_mixer_builtin_profile,
                    scalar_uint_xor_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Shape Mixer builtin profile mutated program")
            typed = profiled
        bitwise_scalar_int_ops_profile = slice_spec["programs"][index].get(
            "bitwise_scalar_int_ops_profile")
        if bitwise_scalar_int_ops_profile is not None:
            try:
                profiled = apply_bitwise_scalar_int_ops(
                    typed, source_hash, bitwise_scalar_int_ops_profile)
                authenticate_bitwise_scalar_int_ops_transition(
                    typed, profiled, source_hash,
                    bitwise_scalar_int_ops_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is typed:
                raise GeneratorError(
                    f"{key}: Bitwise scalar int ops v2 profile did not transform program")
            typed = profiled
        bit_effects_frontend_profile = slice_spec["programs"][index].get(
            "bit_effects_frontend_profile")
        if bit_effects_frontend_profile is not None:
            try:
                profiled = apply_bit_effects_frontend(
                    typed, source_hash, bit_effects_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: BitEffects frontend profile mutated program")
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
        distortion_frontend_profile = slice_spec["programs"][index].get(
            "distortion_frontend_profile")
        if distortion_frontend_profile is not None:
            try:
                authenticate_distortion_frontend(
                    typed, source_hash, distortion_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
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
        scanline_error_float_bits_ingress_profile = (
            slice_spec["programs"][index].get(
                "scanline_error_float_bits_ingress_profile"))
        if scanline_error_float_bits_ingress_profile is not None:
            try:
                profiled = apply_scanline_error_float_bits_ingress(
                    typed, source_hash,
                    scanline_error_float_bits_ingress_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Scanline Error float-bit ingress identity profile "
                    "mutated program")
            typed = profiled
        shapes_float_bits_ingress_profile = (
            slice_spec["programs"][index].get(
                "shapes_float_bits_ingress_profile"))
        if shapes_float_bits_ingress_profile is not None:
            try:
                profiled = apply_shapes_float_bits_ingress(
                    typed, source_hash, shapes_float_bits_ingress_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Shapes float-bit ingress identity profile "
                    "mutated program")
            typed = profiled
        grime_float_bits_ingress_profile = (
            slice_spec["programs"][index].get(
                "grime_float_bits_ingress_profile"))
        if grime_float_bits_ingress_profile is not None:
            try:
                profiled = apply_grime_float_bits_ingress(
                    typed, source_hash, grime_float_bits_ingress_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: grime float-bit ingress identity profile "
                    "mutated program")
            typed = profiled
        shapes_rvalue_assign_profile = (
            slice_spec["programs"][index].get(
                "shapes_rvalue_assign_profile"))
        if shapes_rvalue_assign_profile is not None:
            try:
                profiled = apply_shapes_rvalue_assign(
                    typed, source_hash, shapes_rvalue_assign_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Shapes rvalue-assign identity profile "
                    "mutated program")
            typed = profiled
        cross_lane_assignment_profile = slice_spec["programs"][index].get(
            "cross_lane_assignment_profile")
        if cross_lane_assignment_profile is not None:
            try:
                profiled = apply_cross_lane_assignment(
                    typed, source_hash, cross_lane_assignment_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(f"{key}: cross-lane assignment identity profile mutated program")
            typed = profiled
        mutable_global_frame_profile = (
            slice_spec["programs"][index].get(
                "mutable_global_frame_profile"))
        if mutable_global_frame_profile is not None:
            try:
                profiled = apply_mutable_global_frame(
                    typed, source_hash, mutable_global_frame_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: mutable-global frame identity profile "
                    "mutated program")
            typed = profiled
        mutable_global_array_profile = (
            slice_spec["programs"][index].get(
                "mutable_global_array_profile"))
        if mutable_global_array_profile is not None:
            try:
                profiled = apply_mutable_global_array(
                    typed, source_hash, mutable_global_array_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: mutable-global array identity profile "
                    "mutated program")
            typed = profiled
        const_global_table_profile = (
            slice_spec["programs"][index].get(
                "const_global_table_profile"))
        if const_global_table_profile is not None:
            try:
                profiled = apply_const_global_tables(
                    typed, source_hash, const_global_table_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: const-global nine-table identity profile "
                    "mutated program")
            typed = profiled
        varying_profile = (
            slice_spec["programs"][index].get("varying_profile"))
        if varying_profile is not None:
            try:
                profiled = apply_varying_uv(
                    typed, source_hash, varying_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: varying-uv identity profile mutated program")
            typed = profiled
        texture_lod_admission_profile = (
            slice_spec["programs"][index].get(
                "texture_lod_admission_profile"))
        if texture_lod_admission_profile is not None:
            try:
                profiled = apply_texture_lod_admission(
                    typed, source_hash, texture_lod_admission_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: textureLod admission identity profile mutated "
                    "program")
            typed = profiled
        glyph_map_nonnegative_int_shift_profile = (
            slice_spec["programs"][index].get(
                "glyph_map_nonnegative_int_shift_profile"))
        if glyph_map_nonnegative_int_shift_profile is not None:
            try:
                profiled = apply_glyph_map_nonnegative_int_shift(
                    typed, source_hash,
                    glyph_map_nonnegative_int_shift_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Glyph Map shift identity profile mutated program")
            typed = profiled
        edge_bvec3_contour_profile = slice_spec["programs"][index].get(
            "edge_bvec3_contour_profile")
        if edge_bvec3_contour_profile is not None:
            try:
                profiled = apply_edge_bvec3_contour(
                    typed, source_hash, edge_bvec3_contour_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Edge bvec3 contour identity profile mutated program")
            typed = profiled
        glitch_mat4_chain_profile = slice_spec["programs"][index].get(
            "glitch_mat4_chain_profile")
        if glitch_mat4_chain_profile is not None:
            try:
                profiled = apply_glitch_mat4_chain(
                    typed, source_hash, glitch_mat4_chain_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Glitch mat4 chain identity profile mutated program")
            typed = profiled
        emboss_color_style_profile = slice_spec["programs"][index].get(
            "emboss_color_style_profile")
        if emboss_color_style_profile is not None:
            try:
                profiled = apply_emboss_color_style(
                    typed, source_hash, emboss_color_style_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Emboss color-style identity profile mutated program")
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
        linear_srgb_lane_index_profile = slice_spec["programs"][index].get(
            "linear_srgb_lane_index_profile")
        if linear_srgb_lane_index_profile is not None:
            try:
                profiled = apply_linear_srgb_lane_index(
                    typed, source_hash, linear_srgb_lane_index_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Linear sRGB lane index identity profile mutated program")
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
        reflect_admission_profile = slice_spec["programs"][index].get(
            "reflect_admission_profile")
        if reflect_admission_profile is not None:
            try:
                profiled = apply_reflect_admission(
                    typed, source_hash, reflect_admission_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Reflect admission identity profile mutated program")
            typed = profiled
        inout_vec3_swap_profile = slice_spec["programs"][index].get(
            "inout_vec3_swap_profile")
        if inout_vec3_swap_profile is not None:
            try:
                profiled = apply_inout_vec3_swap_admission(
                    typed, source_hash, inout_vec3_swap_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Inout vec3 swap admission identity profile mutated program")
            typed = profiled
        out_inout_admission_profile = slice_spec["programs"][index].get(
            "out_inout_admission_profile")
        if out_inout_admission_profile is not None:
            try:
                profiled = apply_out_inout_admission(
                    typed, source_hash, out_inout_admission_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: out/inout admission identity profile mutated program")
            typed = profiled
        struct_declaration_profile = slice_spec["programs"][index].get(
            "struct_declaration_profile")
        if struct_declaration_profile is not None:
            try:
                profiled = apply_struct_declaration(
                    typed, source_hash, struct_declaration_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: struct declaration identity profile mutated program")
            typed = profiled
        historic_palette_profile = slice_spec["programs"][index].get(
            "historic_palette_profile")
        if historic_palette_profile is not None:
            try:
                profiled = apply_historic_palette(
                    typed, source_hash, historic_palette_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Historic Palette identity profile mutated program")
            typed = profiled
        palette_frontend_profile = slice_spec["programs"][index].get(
            "palette_frontend_profile")
        if palette_frontend_profile is not None:
            try:
                profiled = apply_palette_frontend(
                    typed, source_hash, palette_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Palette identity profile mutated program")
            typed = profiled
        color_lab_frontend_profile = slice_spec["programs"][index].get(
            "color_lab_frontend_profile")
        if color_lab_frontend_profile is not None:
            try:
                profiled = apply_color_lab_frontend(
                    typed, source_hash, color_lab_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: ColorLab identity profile mutated program")
            typed = profiled
        fractal_frontend_profile = slice_spec["programs"][index].get(
            "fractal_frontend_profile")
        fractal_metadata_effect = None
        if fractal_frontend_profile is not None:
            fractal_metadata_effect = metadata.get("effects", {}).get(
                FRACTAL_KEY.rsplit(":", 1)[0])
            try:
                authenticate_fractal_metadata(fractal_metadata_effect)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            try:
                profiled = apply_fractal_frontend(
                    typed, source_hash, fractal_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is typed:
                raise GeneratorError(
                    f"{key}: Fractal frontend profile did not attach loop proof")
            typed = profiled
        elif key in FRACTAL_PREPARED_KEYS:
            raise GeneratorError(
                f"{key}: exact Fractal frontend profile carrier required")
        julia_frontend_profile = slice_spec["programs"][index].get(
            "julia_frontend_profile")
        if julia_frontend_profile is not None:
            try:
                profiled = apply_julia_frontend(
                    typed, source_hash, julia_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Julia frontend identity profile mutated program")
            typed = profiled
        elif key in JULIA_FRONTEND_KEYS:
            raise GeneratorError(
                f"{key}: exact Julia frontend profile carrier required")
        median_frontend_profile = slice_spec["programs"][index].get(
            "median_frontend_profile")
        if median_frontend_profile is not None and key != MEDIAN_KEY:
            raise GeneratorError(
                f"{key}: Median frontend profile carrier on foreign key")
        texture_frontend_profile = slice_spec["programs"][index].get(
            "texture_frontend_profile")
        if texture_frontend_profile is not None:
            try:
                profiled = apply_texture_frontend(
                    typed, source_hash, texture_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Texture frontend identity profile mutated program")
            typed = profiled
        dither_frontend_profile = slice_spec["programs"][index].get(
            "dither_frontend_profile")
        if dither_frontend_profile is not None:
            if key != DITHER_KEY or dither_frontend_profile != DITHER_FRONTEND_PROFILE:
                raise GeneratorError(
                    f"{key}: Dither frontend profile metadata mismatch")
            try:
                profiled = apply_dither_frontend(
                    typed, source_hash, dither_frontend_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Dither frontend identity profile mutated program")
            typed = profiled
        elif key == DITHER_KEY:
            raise GeneratorError(
                f"{key}: exact Dither frontend profile carrier required")
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
        log_admission_profile = slice_spec["programs"][index].get(
            "log_admission_profile")
        if log_admission_profile is not None:
            try:
                profiled = apply_log_admission(
                    typed, source_hash, log_admission_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: log admission identity profile mutated program")
            typed = profiled
        mandelbrot_sequential_dz_assignment_profile = (
            slice_spec["programs"][index].get(
                "mandelbrot_sequential_dz_assignment_profile"))
        if key == MANDELBROT_SEQUENTIAL_DZ_KEY:
            if mandelbrot_sequential_dz_assignment_profile is not None:
                raise GeneratorError(
                    f"{key}: sequential dz profile must not be a row field")
            mandelbrot_sequential_dz_assignment_profile = (
                MANDELBROT_SEQUENTIAL_DZ_PROFILE)
        if mandelbrot_sequential_dz_assignment_profile is not None:
            try:
                profiled = apply_mandelbrot_sequential_dz_assignment(
                    typed, source_hash,
                    mandelbrot_sequential_dz_assignment_profile)
            except ValueError as error:
                raise GeneratorError(f"{key}: {error}") from error
            if profiled is not typed:
                raise GeneratorError(
                    f"{key}: Mandelbrot sequential-dz identity profile mutated program")
            typed = profiled
        validate_capabilities(typed, tuple(slice_spec["capabilities"]),
                              source_hash=source_hash,
                              compatibility_transform=compatibility_transform,
                              custom_comparer_profile=custom_comparer_profile,
                              numeric_literal_contract=literal_contract,
                              source_global_literal_int_profile=source_global_literal_int_profile,
                              runtime_loop_bound_profile=runtime_loop_bound_profile,
                              gabor_effective_depth_profile=gabor_effective_depth_profile,
                              gather_sorted_round_profile=gather_sorted_round_profile,
                              literal_vec3_lane_index_profile=literal_vec3_lane_index_profile,
                              smooth_edge_luma_weights_profile=smooth_edge_luma_weights_profile,
                              perlin_scalar_uint_xor_profile=perlin_scalar_uint_xor_profile,
                              scalar_uint_xor_profile=scalar_uint_xor_profile,
                              bitwise_scalar_int_ops_profile=bitwise_scalar_int_ops_profile,
                              bit_effects_frontend_profile=bit_effects_frontend_profile,
                              rotate_mat2_return_profile=rotate_mat2_return_profile,
                              focus_blur_borrowed_sampler_profile=focus_blur_borrowed_sampler_profile,
                              extrude_bvec2_relational_reduction_profile=extrude_bvec2_relational_reduction_profile,
                              edge_bvec3_contour_profile=edge_bvec3_contour_profile,
                              glitch_mat4_chain_profile=glitch_mat4_chain_profile,
                              emboss_color_style_profile=emboss_color_style_profile,
                              shape_mixer_builtin_profile=shape_mixer_builtin_profile,
                              caustic_word_hash_profile=caustic_word_hash_profile,
                              scanline_error_float_bits_ingress_profile=scanline_error_float_bits_ingress_profile,
                              shapes_float_bits_ingress_profile=shapes_float_bits_ingress_profile,
                              grime_float_bits_ingress_profile=grime_float_bits_ingress_profile,
                              shapes_rvalue_assign_profile=shapes_rvalue_assign_profile,
                              glyph_map_nonnegative_int_shift_profile=glyph_map_nonnegative_int_shift_profile,
                              curl_vector_math_profile=curl_vector_math_profile,
                              grade_luma_weights_profile=grade_luma_weights_profile,
                              grade_index_expression_profile=grade_index_expression_profile,
                              derivative_admission_profile=derivative_admission_profile,
                              linear_srgb_lane_index_profile=linear_srgb_lane_index_profile,
                              reflect_admission_profile=reflect_admission_profile,
                              posterize_round_profile=posterize_round_profile,
                              as_u32_round_profile=as_u32_round_profile,
                              ceil_admission_profile=ceil_admission_profile,
                              waves_any_notequal_profile=waves_any_notequal_profile,
                              inout_vec3_swap_profile=inout_vec3_swap_profile,
                              out_inout_admission_profile=out_inout_admission_profile,
                              struct_declaration_profile=struct_declaration_profile,
                              historic_palette_profile=historic_palette_profile,
                              palette_frontend_profile=palette_frontend_profile,
                              color_lab_frontend_profile=(
                                  color_lab_frontend_profile),
                              fractal_frontend_profile=fractal_frontend_profile,
                              fractal_metadata_effect=fractal_metadata_effect,
                              julia_frontend_profile=julia_frontend_profile,
                              median_frontend_profile=median_frontend_profile,
                              texture_frontend_profile=texture_frontend_profile,
                              dither_frontend_profile=dither_frontend_profile,
                              moodscape_frontend_profile=(
                                  moodscape_frontend_profile),
                              distortion_frontend_profile=distortion_frontend_profile,
                              noise_frontend_profile=noise_frontend_profile,
                              mutable_global_frame_profile=mutable_global_frame_profile,
                              mutable_global_array_profile=mutable_global_array_profile,
                              const_global_table_profile=const_global_table_profile,
                              varying_profile=varying_profile,
                              osd_frontend_profile=osd_frontend_profile,
                              spooky_ticker_frontend_profile=(
                                  slice_spec["programs"][index].get(
                                      "spooky_ticker_frontend_profile")),
                              texture_lod_admission_profile=texture_lod_admission_profile,
                              cross_lane_assignment_profile=cross_lane_assignment_profile,
                              testpattern_frontend_proof=authorized_testpattern_proof,
                              remap_frontend_proof=authorized_remap_proof,
                              mandelbrot_sequential_dz_assignment_profile=(
                                  mandelbrot_sequential_dz_assignment_profile),
                              log_admission_profile=log_admission_profile)
        try:
            bodies.append(render_typed_cpp(typed, key, source_hash,
                                           f"typed_{index}", "bind_" + key.replace("/", "_").replace(":", "_"),
                                           numeric_literal_contract=literal_contract,
                                           compatibility_transform=compatibility_transform,
                                           custom_comparer_profile=custom_comparer_profile,
                                           source_global_literal_int_profile=source_global_literal_int_profile,
                                           runtime_loop_bound_profile=runtime_loop_bound_profile,
                                           gabor_effective_depth_profile=gabor_effective_depth_profile,
                                           gather_sorted_round_profile=gather_sorted_round_profile,
                                           literal_vec3_lane_index_profile=literal_vec3_lane_index_profile,
                                           smooth_edge_luma_weights_profile=smooth_edge_luma_weights_profile,
                                           perlin_scalar_uint_xor_profile=perlin_scalar_uint_xor_profile,
                                           scalar_uint_xor_profile=scalar_uint_xor_profile,
                                           bitwise_scalar_int_ops_profile=bitwise_scalar_int_ops_profile,
                                           bit_effects_frontend_profile=bit_effects_frontend_profile,
                                           rotate_mat2_return_profile=rotate_mat2_return_profile,
                                           focus_blur_borrowed_sampler_profile=focus_blur_borrowed_sampler_profile,
                                           distortion_frontend_profile=distortion_frontend_profile,
                                           noise_frontend_profile=noise_frontend_profile,
                                           extrude_bvec2_relational_reduction_profile=extrude_bvec2_relational_reduction_profile,
                                           edge_bvec3_contour_profile=edge_bvec3_contour_profile,
                                           glitch_mat4_chain_profile=glitch_mat4_chain_profile,
                                           emboss_color_style_profile=emboss_color_style_profile,
                                           shape_mixer_builtin_profile=shape_mixer_builtin_profile,
                                           caustic_word_hash_profile=caustic_word_hash_profile,
                                           scanline_error_float_bits_ingress_profile=scanline_error_float_bits_ingress_profile,
                                           shapes_float_bits_ingress_profile=shapes_float_bits_ingress_profile,
                                           grime_float_bits_ingress_profile=grime_float_bits_ingress_profile,
                                           shapes_rvalue_assign_profile=shapes_rvalue_assign_profile,
                                           glyph_map_nonnegative_int_shift_profile=glyph_map_nonnegative_int_shift_profile,
                                           curl_vector_math_profile=curl_vector_math_profile,
                                           grade_luma_weights_profile=grade_luma_weights_profile,
                                           grade_index_expression_profile=grade_index_expression_profile,
                                           derivative_admission_profile=derivative_admission_profile,
                                           linear_srgb_lane_index_profile=linear_srgb_lane_index_profile,
                                           reflect_admission_profile=reflect_admission_profile,
                                           posterize_round_profile=posterize_round_profile,
                                           as_u32_round_profile=as_u32_round_profile,
                                           ceil_admission_profile=ceil_admission_profile,
                                           waves_any_notequal_profile=waves_any_notequal_profile,
                                           inout_vec3_swap_profile=inout_vec3_swap_profile,
                                           out_inout_admission_profile=out_inout_admission_profile,
                                           struct_declaration_profile=struct_declaration_profile,
                                           historic_palette_profile=historic_palette_profile,
                                           palette_frontend_profile=palette_frontend_profile,
                                           color_lab_frontend_profile=(
                                               color_lab_frontend_profile),
                                           fractal_frontend_profile=fractal_frontend_profile,
                                           julia_frontend_profile=julia_frontend_profile,
                                           median_frontend_profile=median_frontend_profile,
                                           texture_frontend_profile=texture_frontend_profile,
                                           dither_frontend_profile=dither_frontend_profile,
                                           moodscape_frontend_profile=(
                                               moodscape_frontend_profile),
                                           mutable_global_frame_profile=mutable_global_frame_profile,
                                           mutable_global_array_profile=mutable_global_array_profile,
                                           const_global_table_profile=const_global_table_profile,
                                           varying_profile=varying_profile,
                                           osd_frontend_profile=osd_frontend_profile,
                                           spooky_ticker_frontend_profile=(
                                               slice_spec["programs"][index].get(
                                                   "spooky_ticker_frontend_profile")),
                                           texture_lod_admission_profile=texture_lod_admission_profile,
                                           cross_lane_assignment_profile=cross_lane_assignment_profile,
                                           testpattern_profile=testpattern_row_profile,
                                           testpattern_frontend_proof=authorized_testpattern_proof,
                                           remap_profile=remap_row_profile,
                                           remap_frontend_proof=authorized_remap_proof,
                                           mandelbrot_sequential_dz_assignment_profile=(
                                               mandelbrot_sequential_dz_assignment_profile),
                                           log_admission_profile=log_admission_profile))
        except TypedEmissionError as error: raise GeneratorError(str(error)) from error
        factory_route = _factory_route(repository, key)
        manifest_program = {
            "capabilities": slice_spec["capabilities"],
            "define_contract": (
                "runtime-int" if dynamic_noise
                else ("default-only" if declared_defines else "none")),
            "compatibility_transform": compatibility_transform or "none",
            "defines": declared_defines,
            "factory": factory_route["factory"],
            "emitted_factory": factory_route.get("emitted_factory", factory_route["factory"]),
            "factory_route": factory_route,
            "numeric_literal_contract": literal_contract,
            "output": "typed_slice.cpp", "program_key": key,
            "source": entry["source"], "source_sha256": source_hash,
            "typed_abi": _typed_abi(typed),
        }
        if dynamic_noise:
            manifest_program["runtime_define_profile"] = NOISE_RUNTIME_DEFINE_PROFILE
        if noise_frontend_profile is not None:
            manifest_program["noise_frontend_profile"] = noise_frontend_profile
        if custom_comparer_profile is not None:
            manifest_program["custom_comparer_profile"] = custom_comparer_profile
        if fractal_frontend_profile is not None:
            manifest_program["fractal_frontend_profile"] = (
                fractal_frontend_profile)
        if julia_frontend_profile is not None:
            manifest_program["julia_frontend_profile"] = (
                julia_frontend_profile)
        if dither_frontend_profile is not None:
            manifest_program["dither_frontend_profile"] = (
                dither_frontend_profile)
        if testpattern_row_profile is not None:
            manifest_program["testpattern_profile"] = testpattern_row_profile
        if remap_row_profile is not None:
            manifest_program["remap_profile"] = remap_row_profile
        if moodscape_frontend_profile is not None:
            manifest_program["moodscape_frontend_profile"] = (
                moodscape_frontend_profile)
        spooky_ticker_row_profile = slice_spec["programs"][index].get(
            "spooky_ticker_frontend_profile")
        if spooky_ticker_row_profile is not None:
            manifest_program["spooky_ticker_frontend_profile"] = (
                spooky_ticker_row_profile)
        if runtime_loop_bound_profile is not None:
            manifest_program["runtime_loop_bound_profile"] = (
                runtime_loop_bound_profile)
        if gabor_effective_depth_profile is not None:
            manifest_program["gabor_effective_depth_profile"] = (
                gabor_effective_depth_profile)
        if smooth_edge_luma_weights_profile is not None:
            manifest_program["smooth_edge_luma_weights_profile"] = (
                smooth_edge_luma_weights_profile)
        if perlin_scalar_uint_xor_profile is not None:
            manifest_program["perlin_scalar_uint_xor_profile"] = (
                perlin_scalar_uint_xor_profile)
        if scalar_uint_xor_profile is not None:
            manifest_program["scalar_uint_xor_profile"] = (
                scalar_uint_xor_profile)
        # The shared as_u32 round profile authenticates every current carrier
        # during loading/emission, but it became a manifest field only with the
        # new Grain row. Keep historical FXAA/Snow manifest serialization byte
        # identical while preserving their required profile authority.
        if key == GRAIN_KEY and as_u32_round_profile is not None:
            manifest_program["as_u32_round_profile"] = (
                as_u32_round_profile)
        if bitwise_scalar_int_ops_profile is not None:
            manifest_program["bitwise_scalar_int_ops_profile"] = (
                bitwise_scalar_int_ops_profile)
        if bit_effects_frontend_profile is not None:
            manifest_program["bit_effects_frontend_profile"] = (
                bit_effects_frontend_profile)
        if osd_frontend_profile is not None:
            manifest_program["osd_frontend_profile"] = osd_frontend_profile
        if rotate_mat2_return_profile is not None:
            manifest_program["rotate_mat2_return_profile"] = (
                rotate_mat2_return_profile)
        if focus_blur_borrowed_sampler_profile is not None:
            manifest_program["focus_blur_borrowed_sampler_profile"] = (
                focus_blur_borrowed_sampler_profile)
        if extrude_bvec2_relational_reduction_profile is not None:
            manifest_program["extrude_bvec2_relational_reduction_profile"] = (
                extrude_bvec2_relational_reduction_profile)
        if edge_bvec3_contour_profile is not None:
            manifest_program["edge_bvec3_contour_profile"] = (
                edge_bvec3_contour_profile)
        if glitch_mat4_chain_profile is not None:
            manifest_program["glitch_mat4_chain_profile"] = (
                glitch_mat4_chain_profile)
        if emboss_color_style_profile is not None:
            manifest_program["emboss_color_style_profile"] = (
                emboss_color_style_profile)
        if shape_mixer_builtin_profile is not None:
            manifest_program["shape_mixer_builtin_profile"] = (
                shape_mixer_builtin_profile)
        if caustic_word_hash_profile is not None:
            manifest_program["caustic_word_hash_profile"] = (
                caustic_word_hash_profile)
        if scanline_error_float_bits_ingress_profile is not None:
            manifest_program["scanline_error_float_bits_ingress_profile"] = (
                scanline_error_float_bits_ingress_profile)
        if shapes_float_bits_ingress_profile is not None:
            manifest_program["shapes_float_bits_ingress_profile"] = (
                shapes_float_bits_ingress_profile)
        if shapes_rvalue_assign_profile is not None:
            manifest_program["shapes_rvalue_assign_profile"] = (
                shapes_rvalue_assign_profile)
        if cross_lane_assignment_profile is not None:
            manifest_program["cross_lane_assignment_profile"] = cross_lane_assignment_profile
        if mutable_global_frame_profile is not None:
            manifest_program["mutable_global_frame_profile"] = (
                mutable_global_frame_profile)
        if mutable_global_array_profile is not None:
            manifest_program["mutable_global_array_profile"] = (
                mutable_global_array_profile)
        if const_global_table_profile is not None:
            manifest_program["const_global_table_profile"] = (
                const_global_table_profile)
        if varying_profile is not None:
            manifest_program["varying_profile"] = varying_profile
        if texture_lod_admission_profile is not None:
            manifest_program["texture_lod_admission_profile"] = (
                texture_lod_admission_profile)
        if out_inout_admission_profile is not None:
            manifest_program["out_inout_admission_profile"] = (
                out_inout_admission_profile)
        if struct_declaration_profile is not None:
            manifest_program["struct_declaration_profile"] = (
                struct_declaration_profile)
        if historic_palette_profile is not None:
            manifest_program["historic_palette_profile"] = (
                historic_palette_profile)
        if palette_frontend_profile is not None:
            manifest_program["palette_frontend_profile"] = (
                palette_frontend_profile)
        if color_lab_frontend_profile is not None:
            manifest_program["color_lab_frontend_profile"] = (
                color_lab_frontend_profile)
        if texture_frontend_profile is not None:
            manifest_program["texture_frontend_profile"] = (
                texture_frontend_profile)
        if glyph_map_nonnegative_int_shift_profile is not None:
            manifest_program["glyph_map_nonnegative_int_shift_profile"] = (
                glyph_map_nonnegative_int_shift_profile)
        if curl_vector_math_profile is not None:
            manifest_program["curl_vector_math_profile"] = (
                curl_vector_math_profile)
        if grade_luma_weights_profile is not None:
            manifest_program["grade_luma_weights_profile"] = (
                grade_luma_weights_profile)
        if grade_index_expression_profile is not None:
            manifest_program["grade_index_expression_profile"] = (
                grade_index_expression_profile)
        if linear_srgb_lane_index_profile is not None:
            manifest_program["linear_srgb_lane_index_profile"] = (
                linear_srgb_lane_index_profile)
        if curl_vector_math_profile is not None:
            manifest_program["curl_vector_math_profile"] = (
                curl_vector_math_profile)
        if derivative_admission_profile is not None:
            manifest_program["derivative_admission_profile"] = (
                derivative_admission_profile)
        if reflect_admission_profile is not None:
            manifest_program["reflect_admission_profile"] = (
                reflect_admission_profile)
        manifest_programs.append(manifest_program)
    standard_headers = ["#include <algorithm>", "#include <array>"]
    if blur_runtime_preflight:
        standard_headers.append("#include <cmath>")
    standard_headers.extend([
        "#include <cstdint>", "#include <memory>", "#include <stdexcept>"])
    cpp = ["// Generated by typed GLSL IR emitter. Do not edit.", f"// Revision: {slice_spec['revision']}",
           "#include \"noisemaker/generated/catalog.hpp\"",
           "#include \"noisemaker/effects/bit_effects.hpp\"", "", *standard_headers,
           "", "#include \"noisemaker/sampler.hpp\"", "", "namespace noisemaker::generated {"]
    cpp.extend(bodies)
    factories = [(item["program_key"],
                  "noisemaker::effects::bind_bit_effects"
                  if item["program_key"] == BIT_EFFECTS_KEY else item["factory"])
                 for item in manifest_programs]
    factories.extend((("filter/invert:inv", "bind_filter_invert"), ("synth/solid:solid", "bind_synth_solid")))
    factories.sort()
    admission_source_hashes = _compatibility_source_hashes(repository, manifest_programs)
    compatibility_rows = _compatibility_canonical_rows(repository)
    canonical_routes = sorted(
        (_factory_route_descriptor(
            item,
            bind_factory=("noisemaker::effects::bind_bit_effects"
                          if item["program_key"] == BIT_EFFECTS_KEY
                          else item["factory"]),
            source_sha256=admission_source_hashes[item["program_key"]],
            compatibility_row=compatibility_rows.get(item["program_key"]))
         for item in manifest_programs),
        key=lambda item: item["key"])

    def route_initializer(route: dict[str, str]) -> str:
        return (f'    {{"{route["key"]}", "{route["canonical_factory"]}", '
                f'"{route["emitted_factory"]}", "{route["route_kind"]}", '
                f'"{route["source_sha256"]}", "{route["typed_abi_sha256"]}", '
                f'"{route["define_contract"]}", "{route["defines"]}", '
                f'"{route["sampler_abi_sha256"]}", "{route["uniform_abi_sha256"]}", '
                f'"{route["output_abi_sha256"]}", "{route["output_extent_sha256"]}", '
                f'"{route["compile_define_abi_sha256"]}", '
                f'&{route["bind_factory"]}}},')

    cpp.extend(["", "namespace {", f"constexpr std::array<KernelFactory, {len(factories)}> kCatalog{{{{"])
    cpp.extend(f"    {{\"{key}\", &{factory}}}," for key, factory in factories)
    # The 213 physical rows are retained above as KernelFactory entries, which
    # is what the duplicate-key equivalence proof reads. A second physical
    # FactoryRoute table would carry authenticated anchors that nothing
    # dispatches through and nothing can drift-check, so only the canonical
    # view is emitted.
    cpp.extend(["}};", "",
                f"constexpr std::array<FactoryRoute, {len(canonical_routes)}> kCanonicalRoutes{{{{"])
    cpp.extend(route_initializer(route) for route in canonical_routes)
    cpp.extend(["}};", "}  // namespace", "",
                "std::span<const KernelFactory> catalog() noexcept { return kCatalog; }", "",
                "BoundKernel bind(std::string_view key, const glsl::Bindings& bindings) {",
                "  for (const KernelFactory& factory : kCatalog) if (factory.key == key) return factory.bind(bindings);",
                "  throw std::invalid_argument(\"unknown generated kernel key\");", "}", "",
                "std::span<const FactoryRoute> canonical_routes() noexcept { return kCanonicalRoutes; }", "",
                "const FactoryRoute* find_canonical(std::string_view key,",
                "                                         std::string_view canonical_factory) noexcept {",
                "  for (const FactoryRoute& route : kCanonicalRoutes)",
                "    if (route.key == key && route.canonical_factory == canonical_factory) return &route;",
                "  return nullptr;", "}", "", "}  // namespace noisemaker::generated", ""])
    cpp_bytes = "\n".join(cpp).encode("utf-8")
    output_hash = _sha256(cpp_bytes)
    for entry in manifest_programs:
        entry["output_sha256"] = output_hash
        if entry["factory_route"]["kind"] == "typed_emitter":
            entry["factory_route"]["source_sha256"] = output_hash
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


# The historical-reconstruction memo. Inert unless NOISEMAKER_REGEN_CACHE
# names a directory outside the repository -- see tools/glslcpp/regen_cache.py
# for the measurement that motivates it and the properties that make it safe.
# Installed last so it wraps the finished `generate_outputs`.
try:
    from .regen_cache import install as _install_regen_cache
except ImportError:  # standalone execution, no package context
    try:
        from tools.glslcpp.regen_cache import install as _install_regen_cache
    except ImportError:
        _install_regen_cache = None
if _install_regen_cache is not None:
    _install_regen_cache(sys.modules[__name__])

if __name__ == "__main__": raise SystemExit(main())
