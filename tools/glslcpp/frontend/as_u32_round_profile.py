"""Closed identity profile for the byte-identical ``as_u32`` helper's one
``round`` site, shared verbatim across several filter programs:

```glsl
uint as_u32(float value) {
    return uint(max(round(value), 0.0));
}
```

Structurally parallel to ``gather_sorted_round_profile.py`` /
``posterize_round_profile.py`` (same exhaustive per-program identity
fingerprint: raw/normalized source, function inventory, whole-program and
interface hashes, the exact statement/parent/argument spans and hashes for
the one owned ``round`` node), but keyed by a dict of per-``program_key``
frozen profiles -- following ``loop_proof.py``'s
``_SOURCE_GLOBAL_LITERAL_INT_PROFILES`` precedent -- since the helper body is
shared verbatim across multiple programs rather than being a one-off like
Gather Sorted's or Posterize's. Adds no new capability token: `round` was
already in the frozen 44-entry vocabulary's admission surface via those two
existing profiles: `authorized_round`/`authorized_posterize_round`
special-cased builtin-name check in ``generate_typed_slice.py``; this profile
supplies additional authorized round nodes to that same check, keyed by
identity, never touching ``used.add`` or ``APPROVED_CAPABILITIES``.

Verified against the real compiled JS reference
(``../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js``): every
carrier's ``as_u32`` compiles to ``function as_u32(value) { return
max(round(value), 0)|0; }``, where ``round`` is the shared runtime's
``round: unary(Math.round)`` (``src/csl/glsl-runtime.js:350``), narrowed to
f32 immediately on return (``#unary``: ``F32(operation(value))``,
``glsl-runtime.js:163-168``), before ``max``/``|0`` (ToInt32) ever see it.
``as_u32`` is called only with non-negative inputs at every currently-carried
program's call site (image resolution components, always >= 0 by
construction) -- ``Math.round(x) === Math.floor(x + 0.5)`` for every
non-negative IEEE754 double in the domain actually reached (image
resolutions, nowhere near the 2**52 boundary where the identity could
theoretically diverge), matching ``glsl::round`` = ``floor(x + 0.5)``
(``numeric.hpp``/``glsl_runtime.hpp``) exactly. The well-known
``Math.round(-0.5) == -0`` tie-break hazard that makes `round` genuinely
risky elsewhere in this project (see the Posterize profile's own docstring,
and the operator's own standing note that a `Math.round` tie-break bug was
one of exactly three genuine parity defects found project-wide) does not
apply here precisely because the domain is provably non-negative at every
carried call site -- this is a real, checked argument, not an assumption:
each new key added here must independently re-verify its own call site
against the real generated JS before being added.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "as-u32-round-admission-v1"

# Per-program_key frozen identity. Every field is computed directly from the
# real typed IR (never hand-computed) -- see
# docs/port-engineering/global-admission/impl2/compute_as_u32_round_profile.py
# and its output as_u32_profiles.json.
_PROFILES: dict[str, dict[str, object]] = {
    "filter/grain:grain": {
        "raw_bytes": 8796,
        "raw_sha256": "6edf8deec35e2fa3a32fc150c2be8cb6d71a9356c1c7a3cff5bd3c6c7df764f0",
        "normalized_bytes": 8592,
        "normalized_sha256": "b667ff2a2ba0a9620220cd4821651fccfed930fd385dd1cadb3d1f91eb7ac09d",
        "functions_sha256": "3197ffd53c0eb8500732d7e9da6d5eacf159d363e05fbde1d66693372a406886",
        "whole_program_sha256": "5889e908ebe6309561c2c40d05258d033814c67ff18a5cef5ebcec5ce1e68c22",
        "interface_sha256": "1462c07fce4755c6862e77d5ae5c3795490d4408ab4287e4e1235299aff71672",
        "as_u32_id": 53,
        "as_u32_span": "30:1-32:2",
        "function_inventory": (
            (53, "as_u32", "uint", 1, 1, "30:1-32:2"),
            (54, "blend_cubic", "float", 5, 10, "74:1-85:2"),
            (55, "clamp01", "float", 1, 1, "34:1-36:2"),
            (56, "interpolation_weight", "float", 2, 2, "64:1-72:2"),
            (57, "main", "void", 0, 17, "226:1-264:2"),
            (58, "pcg3d", "uvec3", 1, 9, "38:1-48:2"),
            (59, "periodic_value", "float", 2, 1, "60:1-62:2"),
            (60, "random_from_cell_3d", "float", 2, 3, "50:1-58:2"),
            (61, "sample_bicubic_layer", "float", 4, 5, "87:1-122:2"),
            (62, "sample_grain_noise", "float", 4, 5, "213:1-224:2"),
            (63, "sample_raw_value_noise", "float", 6, 18, "124:1-176:2"),
            (64, "sample_value_noise", "float", 6, 7, "178:1-211:2"),
        ),
        "return_stmt_span": "31:5-31:41",
        "return_stmt_sha256": "daa1030c3fab80716fed35f1bc3c561a208d4013f47dec0dbab56b4ff5cdd115",
        "uint_construct_span": "31:12-31:40",
        "uint_construct_sha256": "ccdc6015d56d4988e86cda78251579ad77785543215a6848e135b017d580c7f7",
        "max_call_span": "31:17-31:39",
        "max_call_sha256": "6309c90a9351cab80dbe0fa581c44ada76fafb00ce6d697e4cfd6e3a5aab9a6f",
        "max_sibling_sha256": "253aaff7daca1dc4fa062c1d5ea973f09f5fc65dc1ecda6972bdc83749cf5b49",
        "round_span": "31:21-31:33",
        "round_sha256": "5cf7930ddd5b9a346ccf79ce51bae15e1cd9f80b8b3e37750714b6ddab4cb5f2",
        "round_argument_sha256": "8cc70d7ac94bb86c0a5e69176a6279ec30acb8c534621df6f818f38e5f47d4af",
        "round_signature_id": -38,
        "bindings": (
            (1, "PI", "float", "const", False),
            (2, "TAU", "float", "const", False),
            (3, "UINT32_TO_FLOAT", "float", "const", False),
            (4, "CHANNEL_COUNT", "uint", "const", False),
            (5, "INTERPOLATION_CONSTANT", "uint", "const", False),
            (6, "INTERPOLATION_LINEAR", "uint", "const", False),
            (7, "INTERPOLATION_COSINE", "uint", "const", False),
            (8, "INTERPOLATION_BICUBIC", "uint", "const", False),
            (9, "BASE_SEED", "uint", "const", False),
            (10, "inputTex", "sampler2D", "uniform", False),
            (11, "resolution", "vec2", "uniform", False),
            (12, "tileOffset", "vec2", "uniform", False),
            (13, "fullResolution", "vec2", "uniform", False),
            (14, "renderScale", "float", "uniform", False),
            (15, "alpha", "float", "uniform", False),
            (16, "time", "float", "uniform", False),
            (17, "pause", "float", "uniform", False),
            (18, "fragColor", "vec4", "output", True),
        ),
        "resources": (
            ("inputTex", "resolution", "tileOffset", "fullResolution",
             "renderScale", "alpha", "time", "pause"),
            ("inputTex",), ("fragColor",), True, False,
        ),
        "defines": (),
    },
    "filter/snow:snow": {
        "raw_bytes": 2982,
        "raw_sha256": "ae057787cc101755743c17b4cdf46b51d70ed8b9896fed9535a058c8b252f48a",
        "normalized_bytes": 2895,
        "normalized_sha256": "0f82254f75e282ccb6f0412d3b8c71bd6716627f0d5fc32366dc9bf5824ce8bf",
        "functions_sha256": "d5d514208acbe1a5cc53374f97374fb4cdd4201b3be4e7246f4a03a4f80b6c6e",
        "whole_program_sha256": "745f56096763615df28caecb8955f61a6366676101e54eaed704f45d4a1efec1",
        "interface_sha256": "f947ad7d6c9eff3374434411d82cb4d7488b125bcc5e37d0aa747853c5fe855a",
        "as_u32_id": 26,
        "as_u32_span": "25:1-27:2",
        "function_inventory": (
            (26, "as_u32", "uint", 1, 1, "25:1-27:2"),
            (27, "clamp_01", "float", 1, 1, "29:1-31:2"),
            (28, "main", "void", 0, 16, "76:1-101:2"),
            (29, "normalized_sine", "float", 1, 1, "33:1-35:2"),
            (30, "periodic_value", "float", 2, 1, "37:1-39:2"),
            (31, "snow_fract_vec3", "vec3", 1, 1, "41:1-43:2"),
            (32, "snow_hash", "float", 1, 6, "45:1-52:2"),
            (33, "snow_noise", "float", 4, 11, "54:1-74:2"),
        ),
        "return_stmt_span": "26:5-26:41",
        "return_stmt_sha256": "b82b455fc44a0b1d91a2d8a1495d0ddafb8d7898ab7bee6e506e9547d8908d1b",
        "uint_construct_span": "26:12-26:40",
        "uint_construct_sha256": "20993f6cb69a34490367faa24d88dee38f36faf5c0a213a3c31e976e8b1b116e",
        "max_call_span": "26:17-26:39",
        "max_call_sha256": "b8795fea78170f471b6de42101385bebe70f0c2d5e8e508331f63b67be55fc03",
        "max_sibling_sha256": "7f5d4d7e9e16ecde7e0a52a1a9fdf2e3d9c2ec1512827a4376461b6acf44c4b8",
        "round_span": "26:21-26:33",
        "round_sha256": "d668503252a585328b459bebdcea34507628f154714e6d360e2f1f5c727f6fa3",
        "round_argument_sha256": "cdc8f4cffdefc9b290fb37f9071a9226a37d19a7f4bb48ec48fcf76501ded8c4",
        "round_signature_id": -38,
        "bindings": (
            (1, "CHANNEL_COUNT", "uint", "const", False),
            (2, "TAU", "float", "const", False),
            (3, "TIME_SEED_OFFSETS", "vec3", "const", False),
            (4, "STATIC_SEED", "vec3", "const", False),
            (5, "LIMITER_SEED", "vec3", "const", False),
            (6, "inputTex", "sampler2D", "uniform", False),
            (7, "resolution", "vec2", "uniform", False),
            (8, "tileOffset", "vec2", "uniform", False),
            (9, "fullResolution", "vec2", "uniform", False),
            (10, "alpha", "float", "uniform", False),
            (11, "time", "float", "uniform", False),
            (12, "pause", "float", "uniform", False),
            (13, "density", "float", "uniform", False),
            (14, "fragColor", "vec4", "output", True),
        ),
        "resources": (
            ("inputTex", "resolution", "tileOffset", "fullResolution",
             "alpha", "time", "pause", "density"),
            ("inputTex",), ("fragColor",), True, False,
        ),
        "defines": (),
    },
    "filter/fxaa:fxaa": {
        "raw_bytes": 4938,
        "raw_sha256": "088449aa1fd5855489d3ce0c6ed2986b9b128fa93ace5817dbeafeff92a7bdf0",
        "normalized_bytes": 4638,
        "normalized_sha256": "8b677bf978565cfea36e421aa8f55abf05decfaa4c2d035ccfe79f46531c6237",
        "functions_sha256": "c0d8e37e893205785e4f0f1c3e894a9f4571f6671bded8de2d6e4806642ff615",
        "whole_program_sha256": "ef6488fe42615c7e1ed8c9b61931228908fccd6f65776d8b885fa529edf5bca7",
        "interface_sha256": "b97eaa429e9283eb4811cd46843db89bc465f0d1834587c9273d26065c9293a3",
        "as_u32_id": 21,
        "as_u32_span": "21:1-23:2",
        "function_inventory": (
            (21, "as_u32", "uint", 1, 1, "21:1-23:2"),
            (22, "load_texel", "vec4", 2, 3, "54:1-58:2"),
            (23, "luminance_from_rgb", "float", 1, 1, "60:1-62:2"),
            (24, "main", "void", 0, 36, "71:1-166:2"),
            (25, "reflect_coord", "int", 2, 6, "36:1-52:2"),
            (26, "sanitized_channelCount", "uint", 1, 4, "25:1-34:2"),
            (27, "weight_from_luma", "float", 2, 1, "64:1-66:2"),
        ),
        "return_stmt_span": "22:5-22:41",
        "return_stmt_sha256": "56acdad4dd4942b699ede8b3a28bd0db096e6646060b75efa2b3d91db402c1ac",
        "uint_construct_span": "22:12-22:40",
        "uint_construct_sha256": "822c3ea60fba535dd041614f3a72affe05ec4a03190bd10064e8e3fc9cde59ef",
        "max_call_span": "22:17-22:39",
        "max_call_sha256": "15c4a9dce90446128a472af35818156ccc49057ce86ba263a77345c9773d471d",
        "max_sibling_sha256": "af30c942e0edca1555491b569ecc6ac02f45cdd05ba445d1374dc8f51e7cba2d",
        "round_span": "22:21-22:33",
        "round_sha256": "806edd5e5d80a4cb89af54bac7175e1407e641ada573634d5099bec3dc58adbe",
        "round_argument_sha256": "492adb2c242efd8dcf4c1f1258f99cf69abc269070284d82f15893acb62fbb17",
        "round_signature_id": -38,
        # fxaa carries a SECOND round site, in `sanitized_channelCount`, which
        # is NOT reachable from main() at the authorized defines (verified by a
        # call-graph walk). It is frozen by identity here rather than waved
        # through: the whole-program census below still demands that the set of
        # round nodes match EXACTLY this authorized set, so an unnoticed third
        # site remains a hard failure.
        "extra_rounds": (
            ("26:23-26:43",
             "793df7e1205c3b1174f8da0c5fccb3ee9cee6b9c5163260d2a1c4ee647409fb1",
             "609ad7fda6cdc4873d898c5c375f0e853785f4a61757b9980c1a422a8c13c4f5"),
        ),
        "bindings": (
            (1, "CHANNEL_COUNT", "uint", "const", False),
            (2, "EPSILON", "float", "const", False),
            (3, "LUMA_WEIGHTS", "vec3", "const", False),
            (4, "inputTex", "sampler2D", "uniform", False),
            (5, "resolution", "vec2", "uniform", False),
            (6, "tileOffset", "vec2", "uniform", False),
            (7, "fullResolution", "vec2", "uniform", False),
            (8, "strength", "float", "uniform", False),
            (9, "sharpness", "float", "uniform", False),
            (10, "threshold", "float", "uniform", False),
            (20, "fragColor", "vec4", "output", True),
        ),
        "resources": (
            ("inputTex", "resolution", "tileOffset", "fullResolution",
             "strength", "sharpness", "threshold"),
            ("inputTex",), ("fragColor",), True, False,
        ),
        "defines": (),
    },
    "filter/normalMap:normalMap": {
        "raw_bytes": 4017,
        "raw_sha256": "384312e50972f75dbebd4080cd76d1c2554a439eb36746f2e351d63a03a271cb",
        "normalized_bytes": 4001,
        "normalized_sha256": "65a598d7765460203cf38a91883de40bedcb7e135dbbdac2cd90663353567025",
        "functions_sha256": "793a4e48595b07c795e6f7c70e5b40e2618d7eac3af52aa26b3cde569b60a48b",
        "whole_program_sha256": "f73f464481e6fd42cca04a70301c55a6650637a229f232fb9cb5100d90a68777",
        "interface_sha256": "8fd3e2fea274678d41892ce91bab3bea20732755282ba50a421cc2b252303fc5",
        "as_u32_id": 24,
        "as_u32_span": "33:1-35:2",
        "function_inventory": (
            (24, "as_u32", "uint", 1, 1, "33:1-35:2"),
            (25, "cbrt_safe", "float", 1, 3, "70:1-76:2"),
            (26, "clamp01", "float", 1, 1, "37:1-39:2"),
            (27, "compute_reference_value", "float", 2, 2, "108:1-111:2"),
            (28, "main", "void", 0, 19, "113:1-154:2"),
            (29, "oklab_l_component", "float", 1, 10, "78:1-92:2"),
            (30, "sanitize_channelCount", "uint", 1, 4, "41:1-50:2"),
            (31, "srgb_to_linear", "float", 1, 2, "63:1-68:2"),
            (32, "value_map_component", "float", 2, 5, "94:1-106:2"),
            (33, "wrap_coord", "int", 2, 4, "52:1-61:2"),
        ),
        "return_stmt_span": "34:5-34:41",
        "return_stmt_sha256": "1b7de60a75be179496c970edf55b4afd5e6c1807d92eed39679517331931b602",
        "uint_construct_span": "34:12-34:40",
        "uint_construct_sha256": "12a20bc90d1e0bb994942e200cb92e34b9f55eb1b68013d6570adab87b33229c",
        "max_call_span": "34:17-34:39",
        "max_call_sha256": "f94b11f429f23166939c0fa3d9aa8b81a88fdff301ada76652e09754f15d2b58",
        "max_sibling_sha256": "dbc1e9b9227fa0f282b19b3f91c2e5037f4623c23f71285ce49b0745d4c9061e",
        "round_span": "34:21-34:33",
        "round_sha256": "40ff3c42eb0e35985e5c0ceae373f0532e51aefa0ba9728f6d021891773e1ac0",
        "round_argument_sha256": "aa3ff01762fa67878f7cfa8aeb83632130b48b0b6a59c150faef18ff795df70d",
        "round_signature_id": -38,
        "bindings": (
            (1, "CHANNEL_COUNT", "uint", "const", False),
            (2, "CHANNEL_CAP", "uint", "const", False),
            (3, "tileOffset", "vec2", "uniform", False),
            (4, "fullResolution", "vec2", "uniform", False),
            (5, "inputTex", "sampler2D", "uniform", False),
            (6, "size", "vec4", "uniform", False),
            (7, "motion", "vec4", "uniform", False),
            (8, "fragColor", "vec4", "output", True),
            (9, "SOBEL_OFFSETS", "ivec2[9]", "const", False),
            (10, "SOBEL_X_KERNEL", "float[9]", "const", False),
            (11, "SOBEL_Y_KERNEL", "float[9]", "const", False),
        ),
        "resources": (
            ("tileOffset", "fullResolution", "inputTex", "size", "motion"),
            ("inputTex",), ("fragColor",), True, False,
        ),
        "defines": (),
    },
}

AS_U32_ROUND_KEYS = frozenset(_PROFILES)

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

__all__ = ("PROFILE", "AS_U32_ROUND_KEYS",
           "authenticate_as_u32_round_admission",
           "apply_as_u32_round_admission")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_program_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _walk_statement(value: TypedStatement):
    yield value
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_as_u32_round_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedExpression | None:
    """Return the exact authenticated ``round`` node for ``program.key``, or
    ``None`` if ``program.key`` is not one of the profile's carriers."""
    expected = _PROFILES.get(program.key)
    if expected is None:
        if profile is not None:
            raise _fail("program key is not an admitted as_u32-round carrier")
        return None
    if profile != PROFILE:
        raise _fail("exact profile carrier required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (source_hash != expected["raw_sha256"]
            or len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != expected["normalized_sha256"]
            or program.preprocessor_defines != expected["defines"]
            or program.body_status != "analyzed"):
        raise _fail("source, key, define, or body profile mismatch")
    if (_sha(program.functions) != expected["functions_sha256"]
            or _whole_program_fingerprint(program) != expected["whole_program_sha256"]
            or _interface_fingerprint(program) != expected["interface_sha256"]):
        raise _fail("function, whole-program, or interface profile mismatch")
    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    functions_sorted = tuple(sorted(program.functions, key=lambda item: item.id))
    if tuple((item.id, item.name, item.return_type.display(), len(item.parameters),
              len(item.body), _span(item)) for item in functions_sorted) != expected["function_inventory"]:
        raise _fail("function inventory mismatch")
    as_u32 = next((item for item in functions_sorted if item.id == expected["as_u32_id"]), None)
    if as_u32 is None or as_u32.name != "as_u32" or _span(as_u32) != expected["as_u32_span"]:
        raise _fail("as_u32 identity mismatch")
    if len(as_u32.body) != 1:
        raise _fail("as_u32 body shape mismatch")

    statement = as_u32.body[0]
    if (statement.kind != "return" or len(statement.expressions) != 1
            or _span(statement) != expected["return_stmt_span"]
            or _sha(statement) != expected["return_stmt_sha256"]):
        raise _fail("return statement profile mismatch")
    uint_construct = statement.expressions[0]
    if (uint_construct.kind != "construct" or uint_construct.type.display() != "uint"
            or len(uint_construct.children) != 1
            or _span(uint_construct) != expected["uint_construct_span"]
            or _sha(uint_construct) != expected["uint_construct_sha256"]):
        raise _fail("uint(...) construct profile mismatch")
    max_call = uint_construct.children[0]
    if (max_call.kind != "builtin" or max_call.callee != "max"
            or max_call.type.display() != "float" or len(max_call.children) != 2
            or _span(max_call) != expected["max_call_span"]
            or _sha(max_call) != expected["max_call_sha256"]
            or _sha(max_call.children[1]) != expected["max_sibling_sha256"]):
        raise _fail("round-consuming max profile mismatch")
    round_value = max_call.children[0]
    if (round_value.kind != "builtin" or round_value.callee != "round"
            or round_value.signature_id != expected["round_signature_id"]
            or round_value.type.display() != "float"
            or round_value.category != "rvalue"
            or len(round_value.children) != 1
            or round_value.children[0].type.display() != "float"
            or _span(round_value) != expected["round_span"]
            or _sha(round_value) != expected["round_sha256"]
            or _sha(round_value.children[0]) != expected["round_argument_sha256"]):
        raise _fail("round site or argument profile mismatch")

    # Census the WHOLE program: an extra round site anywhere else is a hard
    # failure, not an unnoticed extra -- exactly this carrier's one site.
    all_rounds: list[TypedExpression] = []
    for function in functions_sorted:
        for item in function.body:
            for value in _walk_statement(item):
                if (isinstance(value, TypedExpression) and value.kind == "builtin"
                        and value.callee == "round"):
                    all_rounds.append(value)
    # The authorized set is the primary as_u32 site plus any explicitly frozen
    # extras (see "extra_rounds"). Still an EXACT match: a round node that is
    # not in this set is a hard failure, as before.
    extras = expected.get("extra_rounds", ())
    if len(all_rounds) != 1 + len(extras):
        raise _fail("expected exactly the owned round site(s)")
    if all_rounds[0] is not round_value and round_value not in all_rounds:
        raise _fail("primary round site is not owned")
    remaining = [item for item in all_rounds if item is not round_value]
    if len(remaining) != len(extras):
        raise _fail("owned round site census mismatch")
    for value, (span, node_sha, arg_sha) in zip(
            sorted(remaining, key=_span), sorted(extras, key=lambda e: e[0])):
        if (value.category != "rvalue" or len(value.children) != 1
                or _span(value) != span or _sha(value) != node_sha
                or _sha(value.children[0]) != arg_sha):
            raise _fail("frozen extra round site mismatch")

    bindings = tuple(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable)
        for item in program.declarations)
    if bindings != expected["bindings"]:
        raise _fail("binding profile mismatch")
    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != expected["resources"]):
        raise _fail("resource profile mismatch")

    # Return the FULL authorized set: the primary as_u32 site first, then any
    # frozen extras. Callers check membership, so an unauthorized round node
    # still fails closed.
    return (round_value, *remaining)


def apply_as_u32_round_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate and return the same immutable program object."""
    authenticate_as_u32_round_admission(program, source_hash, profile)
    return program
