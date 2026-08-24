"""Typed-IR-only C++ emitter for the deliberately small native slice."""

from __future__ import annotations

from dataclasses import dataclass, field
import dataclasses
import hashlib
import math
import struct

from .frontend.loop_proof import (
    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY, SOURCE_GLOBAL_LITERAL_INT_KEYS,
    attach_counted_loop_proofs, authenticate_source_global_literal_int,
    rebuild_authenticated_counted_loop_proofs, summarize_counted_loop_proofs)
from .frontend.local_counter_proof import (
    COMPUTE_RANK_KEY, COMPUTE_RANK_NORMALIZED_SHA256, COMPUTE_RANK_RAW_SHA256,
    attach_discarded_local_counter_proofs)
from .frontend.fixed_nine_table_proof import (
    CAPABILITY as FIXED_NINE_CAPABILITY, SOURCE_LOCKS,
    prove_fixed_nine_local_tables, source_provenance_error)
from .frontend.fixed_grid_counter_store_proof import (
    SOURCE_LOCKS as FIXED_GRID_SOURCE_LOCKS,
    prove_fixed_grid_counter_store,
    source_provenance_error as fixed_grid_source_provenance_error)
from .frontend.fixed_array_in_parameter_proof import (
    REFRACT_KEY,
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
from .frontend.perlin_scalar_uint_xor_profile import (
    PERLIN_KEY, PROFILE as PERLIN_SCALAR_UINT_XOR_PROFILE,
    authenticate_perlin_scalar_uint_xor)
from .frontend.rotate_mat2_return_profile import (
    PROFILE as ROTATE_MAT2_RETURN_PROFILE, ROTATE_KEY,
    authenticate_rotate_mat2_return)
from .frontend.caustic_word_hash_profile import (
    CAUSTIC_KEY, authenticate_caustic_word_hash)
from .frontend.curl_vector_math_profile import (
    CURL_KEY, authenticate_curl_vector_math)
from .frontend.extrude_bvec2_relational_reduction_profile import (
    EXTRUDE_KEY, authenticate_extrude_bvec2_relational_reduction)
from .frontend.focus_blur_borrowed_sampler_profile import (
    FOCUS_BLUR_KEY, PROFILE as FOCUS_BLUR_BORROWED_SAMPLER_PROFILE,
    authenticate_focus_blur_borrowed_sampler_parameters)
from .frontend.derivative_admission_profile import (
    DERIVATIVE_ADMISSION_KEYS, authenticate_derivative_admission)


class TypedEmissionError(ValueError):
    """A fail-closed emission diagnostic with immutable typed-IR location."""


def _error(program: TypedProgram | str, value: object, message: str) -> TypedEmissionError:
    key = program.key if isinstance(program, TypedProgram) else program
    span = getattr(value, "span", None)
    line = getattr(span, "start_line", 1)
    column = getattr(span, "start_column", 1)
    return TypedEmissionError(f"{key}:{line}:{column}: {message}")


_TYPES = {
    "void": "void", "float": "float", "int": "std::int32_t", "uint": "std::uint32_t",
    "bool": "bool", "vec2": "glsl::Vec2", "vec3": "glsl::Vec3", "vec4": "glsl::Vec4",
    "ivec2": "glsl::IVec2", "ivec3": "glsl::IVec3", "ivec4": "glsl::IVec4",
    "uvec2": "glsl::UVec2", "uvec3": "glsl::UVec3", "uvec4": "glsl::UVec4",
    "mat2": "glsl::Mat2",
}
# Identifiers the emitter itself binds inside every generated pixel function
# and helper signature. A GLSL local or parameter with one of these names would
# shadow them and either change meaning silently or fail to compile — e.g. a
# local `state` shadowing `const State& state` makes helper calls pass the
# wrong type. Ten corpus programs declare a local named `state`.
_RESERVED_IDENTIFIERS = frozenset({"state", "context", "output", "kernel_base"})


def _safe_identifier(name: str, symbol_id: object) -> str:
    """Mangle only names that would shadow an emitter-bound identifier."""
    if name in _RESERVED_IDENTIFIERS:
        return f"{name}_glsl_{symbol_id}"
    return name


_BINARY_OPERATORS = frozenset({"!=", "%", "&&", "*", "+", "-", "/", "<", "<=", "==", ">", ">=", ">>", "^", "||"})
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
    gather_sorted_round_profile: str | None = None
    literal_vec3_lane_index_profile: str | None = None
    smooth_edge_luma_weights_profile: str | None = None
    perlin_scalar_uint_xor_profile: str | None = None
    rotate_mat2_return_profile: str | None = None
    focus_blur_borrowed_sampler_profile: str | None = None
    extrude_bvec2_relational_reduction_profile: str | None = None
    caustic_word_hash_profile: str | None = None
    curl_vector_math_profile: str | None = None
    grade_luma_weights_profile: str | None = None
    grade_index_expression_profile: str | None = None
    derivative_admission_profile: str | None = None
    uniforms: dict[int, object] = field(init=False)
    outputs: dict[int, object] = field(init=False)
    source_globals: dict[int, object] = field(init=False)
    source_global_dependencies: dict[int, tuple[int, ...]] = field(init=False)
    source_global_bounds: tuple[tuple[int, int, str, object], ...] = field(init=False)
    function_names: dict[int, str] = field(init=False)
    ordinary_array_return_signatures: set[int] = field(init=False)
    mutated_symbol_ids: set[int] = field(init=False)
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
    authorized_rotate_helper: object | None = field(init=False, default=None)
    authorized_rotate_expressions: tuple[TypedExpression, ...] = field(
        init=False, default=())
    emitted_rotate_helper_count: int = field(init=False, default=0)
    emitted_rotate_expressions: list[TypedExpression] = field(
        init=False, default_factory=list)
    authorized_focus_blur_proof: object | None = field(init=False, default=None)
    authorized_extrude_proof: object | None = field(init=False, default=None)
    authorized_caustic_proof: object | None = field(init=False, default=None)
    authorized_curl_proof: object | None = field(init=False, default=None)
    emitted_curl_nodes: list[object] = field(init=False, default_factory=list)
    authorized_derivative_proof: object | None = field(init=False, default=None)
    emitted_derivative_nodes: list[object] = field(init=False, default_factory=list)
    emitted_caustic_nodes: list[object] = field(init=False, default_factory=list)
    emitted_extrude_nodes: list[object] = field(init=False, default_factory=list)
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

    def __post_init__(self) -> None:
        self.authorized_round_parent = None
        self.authorized_round = None
        self.authorized_literal_vec3_lane_sites = ()
        self.authorized_custom_comparer_predicate = None
        self.authorized_smooth_edge_luma_weights_declaration = None
        self.authorized_perlin_scalar_uint_xors = ()
        self.emitted_perlin_scalar_uint_xors = []
        self.authorized_rotate_helper = None
        self.authorized_rotate_expressions = ()
        self.emitted_rotate_helper_count = 0
        self.emitted_rotate_expressions = []
        self.authorized_focus_blur_proof = None
        self.authorized_extrude_proof = None
        self.authorized_caustic_proof = None
        self.authorized_curl_proof = None
        self.emitted_curl_nodes = []
        self.emitted_caustic_nodes = []
        self.emitted_extrude_nodes = []
        self.emitted_focus_blur_parameter_sites = []
        self.emitted_focus_blur_uses = []
        self.emitted_focus_blur_calls = []
        self.authorized_grade_luma_weights_declaration = None
        self.authorized_grade_index_sites = ()
        self.emitted_grade_index_sites = []
        self.authorized_derivative_proof = None
        self.emitted_derivative_nodes = []
        literal_source_key = literal_vec3_lane_selected_source_key(self.program)
        if self.program.body_status != "analyzed":
            raise _error(self.program, self.program, "typed body analysis is required")
        if self.numeric_literal_contract not in {"glsl-f32", "source-double"}:
            raise _error(self.program, self.program, "unsupported numeric literal contract")
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
                    or self.derivative_admission_profile is not None):
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
                    or self.derivative_admission_profile is not None):
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
                    or self.derivative_admission_profile is not None):
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
                    or self.derivative_admission_profile is not None):
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
                    or self.derivative_admission_profile is not None):
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
                    or self.derivative_admission_profile is not None):
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
                    or self.derivative_admission_profile is not None):
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
                    or self.grade_index_expression_profile is not None):
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
        self.function_names = {item.signature.id: item.name for item in self.program.functions}
        self.ordinary_array_return_signatures = {
            item.signature.id for item in self.program.functions
            if self._function_returns_integral_call_map(item)
        }
        self.mutated_symbol_ids = set()
        for function in self.program.functions:
            for statement in function.body:
                self._collect_mutated_symbols(statement)
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
            source_global_bounds=self.source_global_bounds)

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

    def _validate_counted_loops(self) -> None:
        try:
            recomputed, summary = rebuild_authenticated_counted_loop_proofs(
                self.program, self.source_global_literal_int_profile)
        except ValueError as error:
            raise _error(self.program, self.program, str(error)) from error
        if len(recomputed) != len(self.program.functions):
            raise _error(self.program, self.program, "malformed counted-for proof functions")

        def statement(actual: TypedStatement, expected: TypedStatement) -> None:
            if (actual.kind != expected.kind or actual.loop_proof != expected.loop_proof
                    or len(actual.children) != len(expected.children)):
                raise _error(self.program, actual, "malformed counted-for proof")
            proof = actual.loop_proof
            if proof is not None and (
                    proof.trip_count > 128 or proof.lexical_depth > 3
                    or proof.effective_depth > 3 or proof.lexical_product > 4096
                    or proof.entrypoint_charge > 4096
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
        if (summary.unproved_loop_count
                or summary.max_effective_depth > 3
                or summary.max_lexical_product > 4096
                or summary.entrypoint_charge > 4096):
            if summary.loop_count or summary.unproved_loop_count:
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
        if self.program.key == REFRACT_KEY:
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
            if declaration.symbol.id in admitted_literal_ints:
                self.source_global_dependencies[declaration.symbol.id] = ()
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
            initializer = (declaration.initializer.literal
                           if declaration.type.display() == "int"
                           else self.expression(declaration.initializer))
            lines.append(
                f"{indent}const {self.local_type(declaration.type)} {declaration.symbol.name} = "
                f"{initializer};")
        return lines

    def type(self, value: object) -> str:
        name = value.display()
        try:
            return _TYPES[name]
        except KeyError as error:
            raise _error(self.program, value, f"unsupported typed type {name}") from error

    def local_type(self, value: object) -> str:
        # Canonical scalar temporaries retain JavaScript Number precision;
        # constructors, builtins, calls, uniforms, and outputs remain the
        # explicit GLSL float32 consumption/storage boundaries.
        return "double" if value.display() == "float" else self.type(value)

    def function_type(self, value: object) -> str:
        return "double" if value.display() == "float" else self.type(value)

    def function_parameter_type(self, function: object, ordinal: int,
                                parameter: object) -> str:
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
        if symbol.id in self.uniforms:
            if symbol.type.kind == "sampler":
                return f"*state.{symbol.name}"
            return f"state.{symbol.name}"
        if symbol.id in self.locals:
            return self.locals[symbol.id]
        raise _error(self.program, expression, f"unmapped typed symbol {symbol.name}")

    def _proved_array(self, symbol_id: int | None):
        proof = self.program.fixed_nine_table_proof
        return next((item for item in proof.arrays if item.symbol_id == symbol_id),
                    None) if proof is not None else None

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

    def expression(self, value: TypedExpression) -> str:
        focus = getattr(self, "authorized_focus_blur_proof", None)
        if focus is not None:
            if any(value is item for item in focus.sampler_uses):
                self.emitted_focus_blur_uses.append(value)
            if any(value is item for item in focus.calls):
                self.emitted_focus_blur_calls.append(value)
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
            if display == "uint" and len(value.children) == 1 and value.children[0].type.display() == "float":
                return f"glsl::detail::float_to_uint32({self.expression(value.children[0])})"
            if display == "mat2":
                if len(value.children) != 4 or any(child.type.display() != "float" for child in value.children):
                    raise _error(self.program, value, "unsupported mat2 constructor")
                arguments = [self.expression(child) for child in value.children]
                return ("glsl::Mat2(glsl::Vec2(" + ", ".join(arguments[:2]) + "), "
                        "glsl::Vec2(" + ", ".join(arguments[2:]) + "))")
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
            return f"{self.type(value.constructor_type)}(" + ", ".join(self.expression(x) for x in value.children) + ")"
        if value.kind == "swizzle":
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
        if value.kind == "index":
            if task20 := self._task20_index(value, "rvalue"):
                return task20
            if (task19 := self._task19_index(value)) is not None:
                return task19
            if self._task18_literal_read(value):
                return (f"{self.expression(value.children[0])}"
                        f"[{value.children[1].literal_value}]")
            if not self._proved_index(value) and not self._proved_grade_index(value):
                raise _error(self.program, value, "unsupported typed expression index")
            return f"{self.expression(value.children[0])}[{self.expression(value.children[1])}]"
        if value.kind == "binary":
            if value.operator not in _BINARY_OPERATORS:
                raise _error(self.program, value, f"unsupported binary operator {value.operator}")
            if len(value.children) != 2:
                raise _error(self.program, value, "malformed typed binary expression")
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
            folded = self.folded_float_literal(value)
            if folded is not None:
                return folded
            left_type = value.children[0].type.display()
            right_type = value.children[1].type.display()
            if value.operator == ">>":
                if left_type not in {"uvec2", "uvec3", "uvec4"} or right_type != "uint":
                    raise _error(self.program, value, "unsupported binary operator >>")
                return (f"glsl::shift_right({self.expression(value.children[0])}, "
                        f"{self.expression(value.children[1])})")
            if value.operator == "^":
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
                if (left_type not in {"uvec2", "uvec3", "uvec4"}
                        or right_type != left_type):
                    raise _error(self.program, value, "unsupported binary operator ^")
                return (f"glsl::bitwise_xor({self.expression(value.children[0])}, "
                        f"{self.expression(value.children[1])})")
            if value.operator == "%" and (left_type not in {"int", "uint"} or right_type != left_type):
                raise _error(self.program, value, "unsupported binary operator %")
            if "mat" in left_type or "mat" in right_type:
                if value.operator != "*" or left_type != "mat2" or right_type != "vec2":
                    raise _error(self.program, value, "unsupported matrix binary expression")
            left = self.expression(value.children[0])
            right = self.expression(value.children[1])
            if value.operator == "%":
                return f"glsl::integer_mod({left}, {right})"
            # JavaScript canonical kernels retain scalar arithmetic in Number
            # precision until the typed local/assignment/builtin boundary. The
            # C++ spelling makes that storage rule explicit instead of allowing
            # native float operator chaining to narrow each intermediate.
            if value.type.display() == "float":
                return f"(static_cast<double>({left}) {value.operator} static_cast<double>({right}))"
            vector_with_boundary = (value.type.display() in {"vec2", "vec3", "vec4"}
                                    and self._contains_vector_value_boundary(value))
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
                raise _error(self.program, value, f"unsupported unary operator {value.operator}")
            if len(value.children) != 1:
                raise _error(self.program, value, "malformed typed unary expression")
            folded = self.folded_float_literal(value)
            if folded is not None:
                return folded
            return f"({value.operator}{self.expression(value.children[0])})"
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
            if value.kind == "builtin":
                if value.callee == "mod":
                    argument_types = tuple(child.type.display() for child in value.children)
                    if argument_types not in {("float", "float"), ("vec2", "float"), ("vec2", "vec2")}:
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
                if value.callee == "textureSize":
                    if not arguments: raise _error(self.program, value, "textureSize arity")
                    return f"texture_size({arguments[0]})"
                if value.callee == "round":
                    raise _error(self.program, value, "unsupported builtin round")
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
                    proof = self.authorized_caustic_proof
                    if proof is None or value is not proof.ingress:
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    if len(arguments) != 1:
                        raise _error(self.program, value, "floatBitsToUint arity")
                    self.emitted_caustic_nodes.append(value)
                    # Delegates to the existing, tested bit-reinterpretation
                    # helper. Must NOT be confused with float_to_uint32, which
                    # is GLSL numeric conversion (truncate + wrap).
                    return f"noisemaker::float_bits_to_uint({arguments[0]})"
                if value.callee in {"all", "lessThanEqual"}:
                    # Emitted only for the exact nodes this emitter itself
                    # authenticated. `bvec2` and these two builtins are absent
                    # from _TYPES/_BUILTIN_NAMES so no other program can reach
                    # them.
                    proof = self.authorized_extrude_proof
                    nodes = (() if proof is None else
                             (*proof.reductions, *proof.relationals))
                    if not any(value is item for item in nodes):
                        raise _error(self.program, value,
                                     f"unsupported builtin {value.callee}")
                    self.emitted_extrude_nodes.append(value)
                    if value.callee == "all":
                        if len(arguments) != 1:
                            raise _error(self.program, value, "all arity")
                        return f"glsl::all({arguments[0]})"
                    if len(arguments) != 2:
                        raise _error(self.program, value, "lessThanEqual arity")
                    return f"glsl::lessThanEqual({arguments[0]}, {arguments[1]})"
                if value.callee in {"dFdx", "dFdy", "fwidth"}:
                    # Emitted only for the exact nodes this emitter itself
                    # authenticated. Every generated pixel/helper function
                    # already takes `const glsl::PixelContext& context`, so
                    # lowering is a direct call -- no plumbing needed at any
                    # call depth.
                    proof = self.authorized_derivative_proof
                    nodes = (() if proof is None else proof.nodes)
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
            prefix = "state, context" + (", " if arguments else "")
            return f"{self.function_names[value.signature_id]}(" + prefix + ", ".join(arguments) + ")"
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

    def statement(self, value: TypedStatement, indent: str = "  ",
                  loop_depth: int = 0) -> list[str]:
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
            if (value.loop_proof is None or len(value.expressions) != 2
                    or len(value.children) != 2):
                raise _error(self.program, value, "malformed counted-for statement")
            initializer, body = value.children
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
            initial = self.expression(declaration.children[0])
            condition = self.expression(value.expressions[0])
            lines = [
                f"{indent}for ([[maybe_unused]] {self.local_type(declaration.type)} "
                f"{name} = {initial}; {condition}; ++{name}) {{"
            ]
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
                if declaration.type.kind == "array":
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
                    lines.append(
                        f"{indent}[[maybe_unused]] std::array<{array.native_element_type}, 9> "
                        f"{emitted_name}{{}};")
                    continue
                initializer = self.expression(declaration.children[0]) if declaration.children else "{}"
                declaration_type = self.local_type(declaration.type)
                if (declaration.children
                        and declaration.type.display() in {"vec2", "vec3", "vec4"}
                        and self._ordinary_return_scalar_map_chain(declaration.children[0])
                        and declaration.symbol_id not in self.mutated_symbol_ids):
                    declaration_type = f"glsl::FloatExpr<{declaration.type.display()[-1]}>"
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
            if len(value.expressions) != 1 or value.expressions[0].kind != "assign":
                raise _error(self.program, value, "only typed assignments are admitted")
            assignment = value.expressions[0]
            if assignment.operator not in _ASSIGNMENT_OPERATORS:
                raise _error(self.program, assignment,
                             f"unsupported assignment operator {assignment.operator}")
            target, swizzle = self.lvalue(assignment.children[0])
            right = self.expression(assignment.children[1])
            operation = assignment.operator
            if operation == "^=":
                target_type = assignment.children[0].type.display()
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
            if loop_depth > 0:
                raise _error(self.program, value, "return inside proved counted-for loop")
            if len(value.expressions) == 0: return [f"{indent}return;"]
            if len(value.expressions) != 1: raise _error(self.program, value, "unsupported return")
            expression = self.expression(value.expressions[0])
            if self.current_function_signature_id in self.ordinary_array_return_signatures:
                lanes = value.expressions[0].type.display()[-1]
                expression = f"glsl::FloatExpr<{lanes}>({self.type(value.expressions[0].type)}({expression}))"
            return [f"{indent}return {expression};"]
        raise _error(self.program, value, f"unsupported typed statement {value.kind}")

    def function(self, function) -> list[str]:
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
        parameters = ", ".join(["[[maybe_unused]] const State& state",
                                "[[maybe_unused]] const glsl::PixelContext& context", *(
            f"[[maybe_unused]] {self.function_parameter_type(function, ordinal, parameter)} "
            f"{_safe_identifier(parameter.name, parameter.id)}"
            for ordinal, parameter in enumerate(function.parameters))])
        return_type = (f"glsl::FloatExpr<{function.return_type.display()[-1]}>"
                       if function.signature.id in self.ordinary_array_return_signatures
                       else self.function_type(function.return_type))
        lines = [f"[[nodiscard]] {return_type} {function.name}({parameters}) noexcept {{"]
        lines.extend(self.source_global_locals(function.body))
        for statement in function.body: lines.extend(self.statement(statement))
        lines.append("}")
        self.current_function_name = None
        self.current_function_signature_id = None
        return lines

    def function_declaration(self, function) -> str:
        if (function.return_type.kind == "matrix"
                and function is not getattr(self, "authorized_rotate_helper", None)):
            raise _error(self.program, function,
                         "unauthenticated matrix-return function declaration")
        parameters = ", ".join(["[[maybe_unused]] const State& state",
                                "[[maybe_unused]] const glsl::PixelContext& context", *(
            f"[[maybe_unused]] {self.function_parameter_type(function, ordinal, parameter)} "
            f"{_safe_identifier(parameter.name, parameter.id)}"
            for ordinal, parameter in enumerate(function.parameters))])
        return_type = (f"glsl::FloatExpr<{function.return_type.display()[-1]}>"
                       if function.signature.id in self.ordinary_array_return_signatures
                       else self.function_type(function.return_type))
        return f"[[nodiscard]] {return_type} {function.name}({parameters}) noexcept;"

    def render_body(self, namespace: str, factory: str) -> list[str]:
        uniforms = [item.symbol for item in self.program.declarations if item.symbol.storage == "uniform"]
        lines = [f"namespace {namespace} {{"]
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
        lines.append("struct State final : KernelState {")
        constructor = ", ".join(
            f"const Surface* {symbol.name}_value" if symbol.type.kind == "sampler" else f"{self.uniform_type(symbol.type)} {symbol.name}_value"
            for symbol in uniforms)
        initializer = ", ".join(f"{symbol.name}({symbol.name}_value)" for symbol in uniforms)
        suffix = f" : {initializer}" if initializer else ""
        lines.append(f"  State({constructor}){suffix} {{}}")
        for symbol in uniforms:
            type_name = "const Surface*" if symbol.type.kind == "sampler" else self.uniform_type(symbol.type)
            lines.append(f"  {type_name} {symbol.name};")
        lines.extend(["};", "", "[[nodiscard]] glsl::Vec4 sample_texture(const Surface& surface, const glsl::Vec2& uv) noexcept {",
                      "  const Rgba sample = sample_nearest_bottom_left(surface, uv[0], uv[1]);",
                      "  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);", "}",
                      "[[nodiscard]] glsl::Vec4 fetch_texel(const Surface& surface, const glsl::IVec2& coord) noexcept {",
                      "  const Rgba sample = texel_fetch_bottom_left(surface, coord[0], coord[1]);",
                      "  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);", "}",
                      "[[nodiscard]] glsl::IVec2 texture_size(const Surface& surface) noexcept {",
                      "  return glsl::IVec2(static_cast<std::int32_t>(surface.width()), static_cast<std::int32_t>(surface.height()));", "}"])
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
        lines.extend(["", "void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {",
                      "  const auto& state = static_cast<const State&>(kernel_base);", "  (void)state;", "  (void)context;"])
        lines.extend(self.source_global_locals(main.body))
        for statement in main.body: lines.extend(self.statement(statement))
        lines.extend(["}", "}  // namespace " + namespace, "",
                      f"BoundKernel {factory}(const glsl::Bindings& bindings) {{"])
        arguments = []
        for symbol in uniforms:
            if symbol.type.kind == "sampler": arguments.append(f"&bindings.texture(\"{symbol.name}\")")
            elif symbol.type.display() == "float": arguments.append(f"bindings.get_number(\"{symbol.name}\")")
            else: arguments.append(f"bindings.get<{self.type(symbol.type)}>(\"{symbol.name}\")")
        uses_derivatives_arg = ", true" if self.program.resources.uses_derivatives else ""
        lines.extend([f"  const auto state = std::make_shared<{namespace}::State>(" + ", ".join(arguments) + ");",
                      "  (void)bindings;",
                      "  return BoundKernel(state, &" + namespace + "::pixel" + uses_derivatives_arg + ");", "}"])
        return lines


def render_typed_cpp(program: TypedProgram, program_key: str, source_hash: str,
                     namespace: str = "typed_kernel", factory: str = "bind_typed",
                     *, numeric_literal_contract: str = "glsl-f32",
                     compatibility_transform: str | None = None,
                     custom_comparer_profile: str | None = None,
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
                     derivative_admission_profile: str | None = None) -> str:
    """Render one typed program; raw parser mappings are intentionally rejected."""
    if not isinstance(program, TypedProgram):
        raise _error(program_key, program, "typed program required; raw AST is forbidden")
    if program.key != program_key:
        raise _error(program, program, "program key mismatch")
    emitter = _Emitter(program, source_hash, numeric_literal_contract,
                       compatibility_transform,
                       custom_comparer_profile,
                       source_global_literal_int_profile,
                       gather_sorted_round_profile,
                       literal_vec3_lane_index_profile,
                       smooth_edge_luma_weights_profile,
                       perlin_scalar_uint_xor_profile,
                       rotate_mat2_return_profile,
                       focus_blur_borrowed_sampler_profile,
                       extrude_bvec2_relational_reduction_profile,
                       caustic_word_hash_profile,
                       curl_vector_math_profile,
                       grade_luma_weights_profile,
                       grade_index_expression_profile,
                       derivative_admission_profile)
    lines = [f"// Typed IR program: {program_key}", f"// Source SHA-256: {source_hash}"]
    lines.extend(emitter.render_body(namespace, factory))
    if (emitter.authorized_perlin_scalar_uint_xors
            and tuple(emitter.emitted_perlin_scalar_uint_xors)
            != emitter.authorized_perlin_scalar_uint_xors):
        raise _error(program, program,
                     "authenticated scalar uint XOR emission mismatch")
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
    if emitter.authorized_grade_index_sites and (
            len(emitter.emitted_grade_index_sites)
            != len(emitter.authorized_grade_index_sites)
            or any(not any(value is item for item in emitter.emitted_grade_index_sites)
                   for value in emitter.authorized_grade_index_sites)):
        raise _error(program, program,
                     "authenticated Grade index expression emission mismatch")
    if emitter.authorized_derivative_proof is not None:
        expected = emitter.authorized_derivative_proof.nodes
        emitted = emitter.emitted_derivative_nodes
        if len(emitted) != len(expected) or any(
                not any(value is item for item in emitted) for value in expected):
            raise _error(program, program, "authenticated Derivative emission mismatch")
    if program.key == GATHER_SORTED_KEY and gather_sorted_round_profile is None:
        raise _error(program, program,
                     "exact Gather Sorted round profile carrier required")
    return "\n".join(lines) + "\n"
