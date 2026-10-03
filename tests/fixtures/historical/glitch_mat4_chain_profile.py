"""Exact source-authenticated ``mat4`` closure for Glitch.

This profile admits only the candidate-owned matrix nodes in the reviewed
``classicNoisedeck/glitch:glitch`` program.  It does not extend the global
typed vocabulary or authorize matrix syntax for any other program.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "glitch-mat4-chain-v1"
GLITCH_KEY = "classicNoisedeck/glitch:glitch"
EFFECTS_PROFILE = "mat4-bicubic-chain-effects-v1"
EFFECTS_KEY = "classicNoisedeck/effects:effects"

# Per-key registry since the effects row: the module is a whole-program
# freeze per key (NOT the ceil/XOR shared-string form -- each record's
# identity is one program's exact text), so each key carries its own
# profile string. glitch's record, messages and self-hash stay byte-ident.
PROFILES = {GLITCH_KEY: PROFILE, EFFECTS_KEY: EFFECTS_PROFILE}
KEYS = tuple(PROFILES)

# effects' required companion carriers (the normalMap pattern, read by BOTH
# authorities' carrier blocks): the mutable-global array closure and the
# ceil admission are REQUIRED on the effects row, and an unmapped key
# resolves to no companions and keeps the strict absent set.
REQUIRED_COMPANION_PROFILES = {
    EFFECTS_KEY: (("mutable_global_array_profile",
                   "mutable-global-nine-array-effects-v1"),
                  ("ceil_admission_profile", "ceil-admission-v1")),
}

_RAW_BYTES = 7894
_RAW_SHA256 = "13d6350eb21cfb5a7c9f0d0a8fffe8e7495068ca2e082d1520ef14ca5b34c134"
_NORMALIZED_BYTES = 7415
_NORMALIZED_BYTES_SHA256 = "f5692ee8ef38007a7db090a5027da5a48f58bc9529bc6ab12cf17f4ec7a6978e"
_NORMALIZED_IR_SHA256 = "ca3932d19ca01fcc11d1336f4026b5f21622a27eb1e2e7b3d75858b56473a224"
_RAW_IR_SHA256 = "326e44df7aaf2767dbc5848c0dde543f1b45863ecabb8b925e580704327e91ee"
_FUNCTIONS_SHA256 = "0ce0022ffb116a4ea03a82e32c372b52b41f67e42b11d4aca2b067da2fa22e61"
_DECLARATIONS_SHA256 = "3501eee0dc5daa002d085d9a272fb8f39dd387d311f77f09f87f47601d2c50d4"
_WHOLE_SHA256 = "c5cb35d06830b48a1f0cba9b5f493c1aac9ec6fb3eeba2ca15ec6ca6449e1178"
_INTERFACE_SHA256 = "5c67224f53f6b88d52e64fd8e888478c6e43ccceeb2ddd8f68d06e8418dc0b92"
_FUNCTIONS = (
    (33, "bicubic"), (34, "f"), (35, "glitch"), (36, "main"),
    (37, "map"), (38, "offsets"), (39, "pcg"),
    (40, "periodicFunction"), (41, "prng"), (42, "scanlines"),
    (43, "snow"),
)
_CALL_GRAPH = {
    "bicubic": ("f",),
    "f": ("prng",),
    "glitch": ("map", "periodicFunction", "prng"),
    "main": ("glitch", "map", "offsets", "periodicFunction", "scanlines", "snow"),
    "map": (),
    "offsets": ("prng",),
    "pcg": (),
    "periodicFunction": ("map",),
    "prng": ("pcg",),
    "scanlines": ("bicubic", "map", "periodicFunction"),
    "snow": ("map", "prng"),
}
_RESOURCES = (
    ("inputTex", "resolution", "tileOffset", "fullResolution", "time",
     "seed", "aspectLens", "xChonk", "yChonk", "glitchiness",
     "scanlinesAmt", "snowAmt", "vignetteAmt", "aberration", "distortion"),
    ("inputTex",), ("fragColor",), True, False,
)
_LOOP_PROOF = (0, 0, 0, 0, 0, True)
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

# Semantic traversal order.  Each row is path, span, kind, type, operator,
# symbol id/name, and the complete dataclass hash.
_MATRIX_NODES = (
    ((22, "e0"), "76:10-76:114", "declaration", "mat4", None, 67, "Q",
     "aeb1c0c7124e857ca2e4edf71a479122c825b0cdf8ea3094a1dc1e7457a83774"),
    ((22, "e0", 0), "76:14-76:114", "construct", "mat4", None, None, None,
     "a1326331cf69599cb70dbc2a36ab9fb2bc4c88421e0dbf6982f11f07fdb37bc2"),
    ((23, "e0"), "77:10-77:86", "declaration", "mat4", None, 68, "S",
     "27e17bb003c9037ef106bab7bc017d61b2680162c45fab4470567b5667eb652b"),
    ((23, "e0", 0), "77:14-77:86", "construct", "mat4", None, None, None,
     "913e9a68794d9620d5e8cec3f8b95ddff91d07859d2e50f609204b460adc1f8a"),
    ((24, "e0"), "78:10-78:86", "declaration", "mat4", None, 69, "T",
     "af7289001c963a2474b89078cd839d376154952fb5471d4a6c497e83c70bdeb7"),
    ((24, "e0", 0), "78:14-78:86", "construct", "mat4", None, None, None,
     "62bdb8cae37bd37c68d0654386e89bad923a45bcd29b2d4c410fca44a10504f8"),
    ((25, "e0"), "79:10-79:23", "declaration", "mat4", None, 70, "A",
     "0f3fdd51502efb87149169e558eabbe8bbad7cd81615d8cdf5ef6c6182ff8e8a"),
    ((25, "e0", 0), "79:14-79:23", "binary", "mat4", "*", None, None,
     "8161939aa1f8a77bf375a8e3314aa3e6350082c946ccb570f64bc3122aed4cdc"),
    ((25, "e0", 0, 0), "79:14-79:19", "binary", "mat4", "*", None, None,
     "3e284718fa3a665773678a8eadd01369804ebc4ed73d0f2df011f250bd9d19fb"),
    ((25, "e0", 0, 0, 0), "79:14-79:15", "id", "mat4", None, 69, "T",
     "6becac8edbda61945ca70baeca1e226a07d46fd30deaadea49937e832380a8d9"),
    ((25, "e0", 0, 0, 1), "79:18-79:19", "id", "mat4", None, 67, "Q",
     "e58f9cacef2c72a01a9dd592f486d41a9f50a8aa89fc6ccc75d5a26eba81bf26"),
    ((25, "e0", 0, 1), "79:22-79:23", "id", "mat4", None, 68, "S",
     "46fa801397944de336b3a6e56b68f2114fd9ea748fb7b5467429c61f187fdccd"),
    ((30, "e0", 0), "84:16-84:22", "binary", "vec4", "*", None, None,
     "fb107bf7c5d9e3d8b200de426f3f636969a531a9a7086d7c684b9c6fc9c50adb"),
    ((30, "e0", 0, 1), "84:21-84:22", "id", "mat4", None, 70, "A",
     "a8b3867696ed0b82e1cebf5b204ab790d304a9924d20d4e405041a7781ac2282"),
)

# The shipped JS factory scalarises ``freq *= vec2(scalar)`` into two ordered
# component stores.  The second scalar evaluation observes the first lane's
# updated value through ``floor(st * freq)``.  Freeze this one source-owned
# site so the C++ emitter can preserve that observable evaluation order
# without changing vector compound-assignment semantics globally.
_ORDERED_FREQ_SPLAT = (
    (3,),
    "137:5-137:80",
    "fe9595ed956e25d542bdf5860f4909b97016b785d6b11710140607926187274f",
    "137:5-137:79",
    "a86c859f6e5d58c63e9558a070e964f7c77d6553092f03d001a624eb56e51187",
    "137:5-137:9",
    "a33ddfb753151a7a3366bbf89274bf44974ebf3236e92afff024d45c85977f8b",
    "137:13-137:79",
    "a4c107b693b854292c760ac0852ac92d25ec7563a41a3482a0a9fd5a3ce61947",
    "137:18-137:78",
    "8c201ca789555a6f0761a0fec0b23f0393d63bcd1d77e23efcf4c04891a168c3",
)

_PROFILE_SHA256 = "3197412490d41987d5a9c608ef802ec92fd42638b906bc1711bc763cf1423a12"

# --- effects' frozen record (measured; see effects-design.md §§1, 4) ------
# Structurally the same bicubic closure as glitch's (the upstream author
# copied bicubic between the two effects), measured at effects' own spans,
# symbol ids and node hashes. The deltas frozen here: TWO defines (glitch
# freezes none), 28 functions (glitch 11), 21 declarations (glitch 16), a
# nonzero counted-loop proof (glitch's is the zero-loop tuple), a PARTIAL
# reachable set (8 of 28 -- glitch's check demands every function
# reachable), and NO freq splat (glitch's `vec2 *=` site does not exist in
# effects at all; the splat fields are per-key optional below).
_EFFECTS_RAW_BYTES = 21087
_EFFECTS_RAW_SHA256 = "e3b742be53b6b1b0dd5e089a805ff02a931cd14643d0a0abe376bd8044e8ec6c"
_EFFECTS_NORMALIZED_BYTES = 15773
_EFFECTS_NORMALIZED_BYTES_SHA256 = "cce2f30177586f4cdabab1e1741a99d1470f49db79c60dc20df9ddbcac9bdfda"
_EFFECTS_NORMALIZED_IR_SHA256 = "40e03f1684a752143cd83486e34f6c1a92d03e183fd629fa62293ab0e87bd268"
_EFFECTS_RAW_IR_SHA256 = "578fe5db0829dbfe2369dc7a230eb2badb518827093f02235b34ad9693a28afd"
_EFFECTS_FUNCTIONS_SHA256 = "d06fd4218bd7513a5aecd343bc3bb9d83dfb6b8fba011626fd5bb80707d67579"
_EFFECTS_DECLARATIONS_SHA256 = "d70dc9c99d2aa5a1546b8eb5a6f15b7bb8d0db2cc86cc7a51ba37643e3930a2a"
_EFFECTS_WHOLE_SHA256 = "db85c4d2cafed8c07bc03d3e203ec83d099575ade15b5b452a9eeb58bb4940d1"
_EFFECTS_INTERFACE_SHA256 = "feeb85a578bad5296e9c345401f7f1a6055da9aa6f5f476c346137f53cdeef52"
_EFFECTS_DEFINES = (("EFFECT", "int", "0"), ("FLIP", "int", "0"))
_EFFECTS_FUNCTIONS = (
    (65, "bicubic"), (66, "bloom"), (67, "brightnessContrast"),
    (68, "cga"), (69, "convolutionEffect"), (70, "convolve"),
    (71, "derivatives"), (72, "desaturate"), (73, "f"), (74, "hsv2rgb"),
    (75, "loadKernels"), (76, "main"), (77, "map"), (78, "offsets"),
    (79, "outline"), (80, "pcg"), (81, "periodicFunction"),
    (82, "pixellate"), (83, "posterize"), (84, "prng"), (85, "random"),
    (86, "rgb2hsv"), (87, "rotate2D"), (88, "saturate"), (89, "shadow"),
    (90, "sobel"), (91, "subpixel"), (92, "zoomBlur"),
)
_EFFECTS_CALL_GRAPH = {
    "bicubic": ("f",),
    "bloom": ("map",),
    "brightnessContrast": ("map",),
    "cga": ("map",),
    "convolutionEffect": (),
    "convolve": (),
    "derivatives": ("convolve", "desaturate"),
    "desaturate": (),
    "f": ("random",),
    "hsv2rgb": (),
    "loadKernels": (),
    "main": ("brightnessContrast", "loadKernels", "map", "offsets",
             "periodicFunction", "rotate2D", "saturate"),
    "map": (),
    "offsets": (),
    "outline": ("convolve", "desaturate"),
    "pcg": (),
    "periodicFunction": ("map",),
    "pixellate": (),
    "posterize": (),
    "prng": ("pcg",),
    "random": ("pcg",),
    "rgb2hsv": (),
    "rotate2D": ("map",),
    "saturate": ("map",),
    "shadow": ("convolve", "hsv2rgb", "rgb2hsv"),
    "sobel": ("convolve", "desaturate"),
    "subpixel": ("map", "pixellate"),
    "zoomBlur": ("map", "prng"),
}
_EFFECTS_REACHABLE = ("brightnessContrast", "loadKernels", "main", "map",
                      "offsets", "periodicFunction", "rotate2D", "saturate")
_EFFECTS_UNREACHABLE = ("bicubic", "bloom", "cga", "convolutionEffect",
                        "convolve", "derivatives", "desaturate", "f",
                        "hsv2rgb", "outline", "pcg", "pixellate", "posterize",
                        "prng", "random", "rgb2hsv", "shadow", "sobel",
                        "subpixel", "zoomBlur")
_EFFECTS_RESOURCES = (
    ("inputTex", "resolution", "tileOffset", "fullResolution", "renderScale",
     "time", "effectAmt", "scaleAmt", "rotation", "offsetX", "offsetY",
     "intensity", "saturation"),
    ("inputTex",), ("fragColor",), True, False,
)
_EFFECTS_LOOP_PROOF = (4, 0, 2, 48, 0, True)
_EFFECTS_DECLARATION_COUNT = 21
_EFFECTS_HOST = (65, "bicubic")
# Semantic traversal order; same shape as glitch's `_MATRIX_NODES`.
_EFFECTS_MATRIX_NODES = (
    ((22, "e0"), "395:10-395:114", "declaration", "mat4", None, 116, "Q",
     "017b638096111ec6aad0c92416d63a87e190d9077f13e601c7d3db1e8e797092"),
    ((22, "e0", 0), "395:14-395:114", "construct", "mat4", None, None, None,
     "db17c064ba787a783540e8e2ec52a73c20e4d96e9f8abf90677261d97a8ca6da"),
    ((23, "e0"), "396:10-396:86", "declaration", "mat4", None, 117, "S",
     "9e401d7d2b01d5131d098fb29b9022fb2f86d003b6ec6523e16070620439603f"),
    ((23, "e0", 0), "396:14-396:86", "construct", "mat4", None, None, None,
     "d59f66a2726a373ecb0bedc425a2a2eb40213fb100dc1de9796fb5f075782c83"),
    ((24, "e0"), "397:10-397:86", "declaration", "mat4", None, 118, "T",
     "99164f2fc0cfa3b23715807efebca9cedf886afe5b6cc2e9b6f7fa47c1cb5651"),
    ((24, "e0", 0), "397:14-397:86", "construct", "mat4", None, None, None,
     "c32500337be20373b25d1ebe9ef7d190200351d50d857665258cf72873c84089"),
    ((25, "e0"), "398:10-398:23", "declaration", "mat4", None, 119, "A",
     "c2402ca362053d1fdecbc83c5df395355ab3218b5a197375d3692b8c3d3846e8"),
    ((25, "e0", 0), "398:14-398:23", "binary", "mat4", "*", None, None,
     "adc4070594cae6d92564ee06e876be562b3a7c16c33196c345f02a321b74f5ca"),
    ((25, "e0", 0, 0), "398:14-398:19", "binary", "mat4", "*", None, None,
     "93e0f8d423c0b679c3e5de40aa1755b7c2691becbdde0f9b54ae9fba85b3a04a"),
    ((25, "e0", 0, 0, 0), "398:14-398:15", "id", "mat4", None, 118, "T",
     "51c2dd39496f475aaf831877b97b1c8a9d8d7ba9f9b3e2569dae910418463bfb"),
    ((25, "e0", 0, 0, 1), "398:18-398:19", "id", "mat4", None, 116, "Q",
     "2b03c28e472c8816fc94b55fd705a290da1860570dc512140a4828e73a0aa15a"),
    ((25, "e0", 0, 1), "398:22-398:23", "id", "mat4", None, 117, "S",
     "2db3446567dce5e32efa99df90987b3789b2cf90937c62e717b2b6f267ad1937"),
    ((30, "e0", 0), "403:16-403:22", "binary", "vec4", "*", None, None,
     "185c1c5bbac198d9add45fed71ca4682b254bb5e96938520ebe5e35f8f93289f"),
    ((30, "e0", 0, 1), "403:21-403:22", "id", "mat4", None, 119, "A",
     "398fd3b03988dcb584b11736f4eda5dcbe528e86f96686fc73486948416086a2"),
)
# The dot/return route locks: `dot(tv * A, uv)` as the sole expression of
# bicubic's `return` (statement 30).
_EFFECTS_DOT_SPAN = "403:12-403:27"
_EFFECTS_DOT_SECOND_ARGUMENT = "uv"
_EFFECTS_RETURN_SPAN = "403:5-403:28"


def _effects_profile_tuple() -> tuple[object, ...]:
    return (EFFECTS_PROFILE, EFFECTS_KEY, _EFFECTS_RAW_BYTES,
            _EFFECTS_RAW_SHA256, _EFFECTS_NORMALIZED_BYTES,
            _EFFECTS_NORMALIZED_BYTES_SHA256, _EFFECTS_NORMALIZED_IR_SHA256,
            _EFFECTS_RAW_IR_SHA256, _EFFECTS_FUNCTIONS_SHA256,
            _EFFECTS_DECLARATIONS_SHA256, _EFFECTS_WHOLE_SHA256,
            _EFFECTS_INTERFACE_SHA256, _EFFECTS_DEFINES, _EFFECTS_FUNCTIONS,
            tuple(sorted(_EFFECTS_CALL_GRAPH.items())), _EFFECTS_RESOURCES,
            _EFFECTS_LOOP_PROOF, _EFFECTS_DECLARATION_COUNT,
            _EFFECTS_HOST, _EFFECTS_REACHABLE, _EFFECTS_UNREACHABLE,
            _EFFECTS_MATRIX_NODES, _EFFECTS_DOT_SPAN,
            _EFFECTS_DOT_SECOND_ARGUMENT, _EFFECTS_RETURN_SPAN)


_EFFECTS_PROFILE_SHA256 = "fce5d99dec3cb934ee4c02b985813675a070ca72b194248263f70dcb5e291e53"


@dataclass(frozen=True, slots=True)
class GlitchMat4ChainProof:
    _candidate: TypedProgram
    host: TypedFunction
    declarations: tuple[TypedExpression, ...]
    constructors: tuple[TypedExpression, ...]
    matrix_products: tuple[TypedExpression, ...]
    matrix_ids: tuple[TypedExpression, ...]
    vector_products: tuple[TypedExpression, ...]
    dot: TypedExpression
    return_statement: TypedStatement
    # Per-key optional since the effects row: glitch's record keeps its
    # three splat objects; effects carries none (its program has no
    # `vec2 *=` splat at all), and both carrier blocks' re-verification
    # tails treat None as "this key has no splat to check".
    ordered_freq_splat_assignment: TypedExpression | None
    ordered_freq_splat_target: TypedExpression | None
    ordered_freq_splat_constructor: TypedExpression | None

    @property
    def consumed_objects(self) -> tuple[TypedExpression, ...]:
        q, s, t, a = self.declarations
        qc, sc, tc = self.constructors
        outer, inner = self.matrix_products
        t_id, q_id, s_id, a_id = self.matrix_ids
        vector = self.vector_products[0]
        return (q, qc, s, sc, t, tc, a, outer, inner,
                t_id, q_id, s_id, vector, a_id)


__all__ = (
    "PROFILE", "GLITCH_KEY", "EFFECTS_PROFILE", "EFFECTS_KEY",
    "PROFILES", "KEYS", "REQUIRED_COMPANION_PROFILES",
    "GlitchMat4ChainProof",
    "authenticate_glitch_mat4_chain", "apply_glitch_mat4_chain",
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _profile_tuple() -> tuple[object, ...]:
    return (PROFILE, GLITCH_KEY, _RAW_BYTES, _RAW_SHA256,
            _NORMALIZED_BYTES, _NORMALIZED_BYTES_SHA256,
            _NORMALIZED_IR_SHA256, _RAW_IR_SHA256, _FUNCTIONS_SHA256,
            _DECLARATIONS_SHA256, _WHOLE_SHA256, _INTERFACE_SHA256,
            _FUNCTIONS, tuple(sorted(_CALL_GRAPH.items())), _RESOURCES,
            _LOOP_PROOF, _MATRIX_NODES, _ORDERED_FREQ_SPLAT)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression,
                     parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement,
                    path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, expression_path in _walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, expression_path, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def _reachable(graph: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    pending = ["main"]
    visited: set[str] = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        pending.extend(graph.get(name, ()))
    return tuple(sorted(visited))


def authenticate_glitch_mat4_chain(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> GlitchMat4ChainProof:
    """Authenticate one of the frozen bicubic-chain keys and return only
    objects owned by ``program``."""
    if profile == EFFECTS_PROFILE:
        return _authenticate_effects_chain(program, source_hash, profile)
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    if program.key != GLITCH_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or _sha(program.raw_source) != _RAW_IR_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest()
            != _NORMALIZED_BYTES_SHA256
            or _sha(program.source) != _NORMALIZED_IR_SHA256
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _sha(program.declarations) != _DECLARATIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"):
        raise _fail("source, function, declaration, program, or interface mismatch")
    if (program.structs != () or program.uniform_blocks != ()
            or any(getattr(program, field, None) is not None
                   for field in _OPTIONAL_PROOF_FIELDS)):
        raise _fail("unrelated structural or proof carrier is present")

    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != _RESOURCES
            or len(program.declarations) != 16):
        raise _fail("resource or top-level declaration signature mismatch")
    loop = program.counted_loop_proof
    if (loop is None or
            (loop.loop_count, loop.unproved_loop_count,
             loop.max_effective_depth, loop.max_lexical_product,
             loop.entrypoint_charge, loop.call_graph_acyclic) != _LOOP_PROOF):
        raise _fail("zero-loop acyclic proof mismatch")
    if tuple((item.id, item.name) for item in program.functions) != _FUNCTIONS:
        raise _fail("semantic function order mismatch")

    names = {item.id: item.name for item in program.functions}
    graph: dict[str, tuple[str, ...]] = {}
    located: list[tuple[TypedFunction, TypedExpression,
                       TypedExpression | None, tuple[object, ...],
                       tuple[TypedStatement, ...]]] = []
    for function in program.functions:
        function_nodes = []
        for index, statement in enumerate(function.body):
            function_nodes.extend(_walk_statement(statement, (index,)))
        located.extend((function, *record) for record in function_nodes)
        graph[function.name] = tuple(sorted({
            names[item.signature_id] for item, _, _, _ in function_nodes
            if item.kind == "call" and item.signature_id in names
        }))
    if (graph != _CALL_GRAPH
            or _reachable(graph) != tuple(sorted(name for _, name in _FUNCTIONS))):
        raise _fail("call graph or main reachability mismatch")

    glitch = program.functions[2]
    if (glitch.id != 35 or glitch.name != "glitch"
            or len(glitch.body) <= _ORDERED_FREQ_SPLAT[0][0]):
        raise _fail("ordered frequency splat host mismatch")
    splat_statement = glitch.body[_ORDERED_FREQ_SPLAT[0][0]]
    if (splat_statement.kind != "expr"
            or _span(splat_statement) != _ORDERED_FREQ_SPLAT[1]
            or _sha(splat_statement) != _ORDERED_FREQ_SPLAT[2]
            or len(splat_statement.expressions) != 1
            or splat_statement.children):
        raise _fail("ordered frequency splat statement mismatch")
    splat_assignment = splat_statement.expressions[0]
    if (splat_assignment.kind != "assign"
            or splat_assignment.type.display() != "vec2"
            or splat_assignment.operator != "*="
            or _span(splat_assignment) != _ORDERED_FREQ_SPLAT[3]
            or _sha(splat_assignment) != _ORDERED_FREQ_SPLAT[4]
            or len(splat_assignment.children) != 2):
        raise _fail("ordered frequency splat assignment mismatch")
    splat_target, splat_constructor = splat_assignment.children
    if (splat_target.kind != "id"
            or splat_target.type.display() != "vec2"
            or splat_target.symbol_id != 75
            or splat_target.symbol is None
            or splat_target.symbol.name != "freq"
            or _span(splat_target) != _ORDERED_FREQ_SPLAT[5]
            or _sha(splat_target) != _ORDERED_FREQ_SPLAT[6]
            or splat_constructor.kind != "construct"
            or splat_constructor.type.display() != "vec2"
            or _span(splat_constructor) != _ORDERED_FREQ_SPLAT[7]
            or _sha(splat_constructor) != _ORDERED_FREQ_SPLAT[8]
            or len(splat_constructor.children) != 1):
        raise _fail("ordered frequency splat target or constructor mismatch")
    splat_scalar = splat_constructor.children[0]
    if (splat_scalar.kind != "call"
            or splat_scalar.type.display() != "float"
            or splat_scalar.callee != "periodicFunction"
            or splat_scalar.signature_id != 40
            or _span(splat_scalar) != _ORDERED_FREQ_SPLAT[9]
            or _sha(splat_scalar) != _ORDERED_FREQ_SPLAT[10]):
        raise _fail("ordered frequency splat scalar route mismatch")

    matrix_records = []
    for function, item, parent, path, chain in located:
        display = item.type.display()
        is_vector_product = (
            item.kind == "binary" and item.operator == "*"
            and display == "vec4"
            and tuple(child.type.display() for child in item.children)
            == ("vec4", "mat4"))
        if display == "mat4" or is_vector_product:
            matrix_records.append((function, item, parent, path, chain))
    actual = tuple(
        (path, _span(item), item.kind, item.type.display(), item.operator,
         item.symbol_id, None if item.symbol is None else item.symbol.name,
         _sha(item))
        for _, item, _, path, _ in matrix_records)
    if actual != _MATRIX_NODES:
        raise _fail("matrix node closure mismatch")
    if any(function.id != 33 or function.name != "bicubic"
           for function, *_ in matrix_records):
        raise _fail("matrix closure escaped bicubic")

    nodes = tuple(record[1] for record in matrix_records)
    declarations = tuple(item for item in nodes if item.kind == "declaration")
    constructors = tuple(item for item in nodes if item.kind == "construct")
    matrix_products = tuple(
        item for item in nodes
        if item.kind == "binary" and item.type.display() == "mat4")
    matrix_ids = tuple(item for item in nodes if item.kind == "id")
    vector_products = tuple(
        item for item in nodes
        if item.kind == "binary" and item.type.display() == "vec4")
    if (len(declarations) != 4 or len(constructors) != 3
            or len(matrix_products) != 2 or len(matrix_ids) != 4
            or len(vector_products) != 1
            or any(len(item.children) != 16
                   or any(child.type.display() != "float"
                          for child in item.children)
                   for item in constructors)):
        raise _fail("matrix declaration, constructor, product, or id census mismatch")

    q, s, t, a = declarations
    qc, sc, tc = constructors
    outer, inner = matrix_products
    t_id, q_id, s_id, a_id = matrix_ids
    vector = vector_products[0]
    if (q.children != (qc,) or s.children != (sc,) or t.children != (tc,)
            or a.children != (outer,) or outer.children[0] is not inner
            or outer.children[1] is not s_id
            or inner.children != (t_id, q_id)
            or vector.children[1] is not a_id
            or tuple(item.symbol.name for item in
                     (q, s, t, a, t_id, q_id, s_id, a_id))
            != ("Q", "S", "T", "A", "T", "Q", "S", "A")
            or vector.children[0].symbol is None
            or vector.children[0].symbol.name != "tv"):
        raise _fail("left-associated matrix topology or exact symbol route mismatch")

    vector_record = next(record for record in matrix_records
                         if record[1] is vector)
    parent = vector_record[2]
    chain = vector_record[4]
    if (parent is None or parent.kind != "builtin" or parent.callee != "dot"
            or _span(parent) != "84:12-84:27"
            or parent.children[0] is not vector
            or parent.children[1].symbol is None
            or parent.children[1].symbol.name != "uv"
            or len(chain) != 1 or chain[0].kind != "return"
            or _span(chain[0]) != "84:5-84:28"):
        raise _fail("vec4 product dot or return route mismatch")

    proof = GlitchMat4ChainProof(
        program, program.functions[0], declarations, constructors,
        matrix_products, matrix_ids, vector_products, parent, chain[0],
        splat_assignment, splat_target, splat_constructor)
    if (len(proof.consumed_objects) != 14
            or len({id(item) for item in proof.consumed_objects}) != 14
            or proof.consumed_objects != nodes):
        raise _fail("candidate ownership, traversal order, or uniqueness mismatch")
    return proof


def apply_glitch_mat4_chain(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    authenticate_glitch_mat4_chain(program, source_hash, profile)
    return program


def _effects_fail(message: str) -> ValueError:
    return ValueError(f"{EFFECTS_PROFILE}: {message}")


def _authenticate_effects_chain(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> GlitchMat4ChainProof:
    """Authenticate effects' bicubic chain (effects-design §4).

    The same closure shape as glitch's -- 4 mat4 declarations named Q/S/T/A,
    3 constructors (Q's with 16 non-literal float `id` children), the
    left-associated `(T*Q)*S` product, 4 mat4 ids, one `vec4*mat4` product
    whose parent is `dot(..., uv)` as the `return`'s sole expression, all
    inside a function named `bicubic` -- measured at effects' own spans,
    ids and hashes. What differs per key: TWO defines (glitch freezes
    none), 28 functions with a PARTIAL reachable set (8 of 28; glitch
    demands every function reachable), a nonzero counted-loop proof, 21
    declarations, and NO freq splat (the splat fields are None).
    """
    def fail(message: str) -> ValueError:
        return _effects_fail(message)

    if profile != EFFECTS_PROFILE:
        raise fail("exact profile carrier required")
    if _sha(_effects_profile_tuple()) != _EFFECTS_PROFILE_SHA256:
        raise fail("internal frozen profile tuple mismatch")
    if program.key != EFFECTS_KEY or source_hash != _EFFECTS_RAW_SHA256:
        raise fail("selected key and exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _EFFECTS_RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _EFFECTS_RAW_SHA256
            or _sha(program.raw_source) != _EFFECTS_RAW_IR_SHA256
            or len(normalized) != _EFFECTS_NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest()
            != _EFFECTS_NORMALIZED_BYTES_SHA256
            or _sha(program.source) != _EFFECTS_NORMALIZED_IR_SHA256
            or _sha(program.functions) != _EFFECTS_FUNCTIONS_SHA256
            or _sha(program.declarations) != _EFFECTS_DECLARATIONS_SHA256
            or _whole(program) != _EFFECTS_WHOLE_SHA256
            or _interface(program) != _EFFECTS_INTERFACE_SHA256
            or tuple((item.name, item.kind, item.canonical_value)
                     for item in program.preprocessor_defines)
            != _EFFECTS_DEFINES
            or program.body_status != "analyzed"):
        raise fail("source, function, declaration, program, or interface mismatch")
    if (program.structs != () or program.uniform_blocks != ()
            or any(getattr(program, field, None) is not None
                   for field in _OPTIONAL_PROOF_FIELDS
                   if field != "fixed_array_in_parameter_proof")):
        raise fail("unrelated structural or proof carrier is present")

    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives)
            != _EFFECTS_RESOURCES
            or len(program.declarations) != _EFFECTS_DECLARATION_COUNT):
        raise fail("resource or top-level declaration signature mismatch")
    loop = program.counted_loop_proof
    if (loop is None or
            (loop.loop_count, loop.unproved_loop_count,
             loop.max_effective_depth, loop.max_lexical_product,
             loop.entrypoint_charge, loop.call_graph_acyclic)
            != _EFFECTS_LOOP_PROOF):
        raise fail("counted-loop proof mismatch")
    if tuple((item.id, item.name) for item in program.functions) \
            != _EFFECTS_FUNCTIONS:
        raise fail("semantic function order mismatch")

    names = {item.id: item.name for item in program.functions}
    graph: dict[str, tuple[str, ...]] = {}
    located: list[tuple[TypedFunction, TypedExpression,
                       TypedExpression | None, tuple[object, ...],
                       tuple[TypedStatement, ...]]] = []
    for function in program.functions:
        function_nodes = []
        for index, statement in enumerate(function.body):
            function_nodes.extend(_walk_statement(statement, (index,)))
        located.extend((function, *record) for record in function_nodes)
        graph[function.name] = tuple(sorted({
            names[item.signature_id] for item, _, _, _ in function_nodes
            if item.kind == "call" and item.signature_id in names
        }))
    reachable = _reachable(graph)
    if (graph != _EFFECTS_CALL_GRAPH
            or reachable != _EFFECTS_REACHABLE
            or tuple(sorted(set(graph) - set(reachable)))
            != _EFFECTS_UNREACHABLE):
        raise fail("call graph or main reachability mismatch")

    matrix_records = []
    for function, item, parent, path, chain in located:
        display = item.type.display()
        is_vector_product = (
            item.kind == "binary" and item.operator == "*"
            and display == "vec4"
            and tuple(child.type.display() for child in item.children)
            == ("vec4", "mat4"))
        if display == "mat4" or is_vector_product:
            matrix_records.append((function, item, parent, path, chain))
    actual = tuple(
        (path, _span(item), item.kind, item.type.display(), item.operator,
         item.symbol_id, None if item.symbol is None else item.symbol.name,
         _sha(item))
        for _, item, _, path, _ in matrix_records)
    if actual != _EFFECTS_MATRIX_NODES:
        raise fail("matrix node closure mismatch")
    if any((function.id, function.name) != _EFFECTS_HOST
           for function, *_ in matrix_records):
        raise fail("matrix closure escaped bicubic")

    nodes = tuple(record[1] for record in matrix_records)
    declarations = tuple(item for item in nodes if item.kind == "declaration")
    constructors = tuple(item for item in nodes if item.kind == "construct")
    matrix_products = tuple(
        item for item in nodes
        if item.kind == "binary" and item.type.display() == "mat4")
    matrix_ids = tuple(item for item in nodes if item.kind == "id")
    vector_products = tuple(
        item for item in nodes
        if item.kind == "binary" and item.type.display() == "vec4")
    if (len(declarations) != 4 or len(constructors) != 3
            or len(matrix_products) != 2 or len(matrix_ids) != 4
            or len(vector_products) != 1
            or any(len(item.children) != 16
                   or any(child.type.display() != "float"
                          for child in item.children)
                   for item in constructors)):
        raise fail("matrix declaration, constructor, product, or id census mismatch")

    q, s, t, a = declarations
    qc, sc, tc = constructors
    outer, inner = matrix_products
    t_id, q_id, s_id, a_id = matrix_ids
    vector = vector_products[0]
    if (q.children != (qc,) or s.children != (sc,) or t.children != (tc,)
            or a.children != (outer,) or outer.children[0] is not inner
            or outer.children[1] is not s_id
            or inner.children != (t_id, q_id)
            or vector.children[1] is not a_id
            or tuple(item.symbol.name for item in
                     (q, s, t, a, t_id, q_id, s_id, a_id))
            != ("Q", "S", "T", "A", "T", "Q", "S", "A")
            or vector.children[0].symbol is None
            or vector.children[0].symbol.name != "tv"):
        raise fail("left-associated matrix topology or exact symbol route mismatch")

    vector_record = next(record for record in matrix_records
                         if record[1] is vector)
    parent = vector_record[2]
    chain = vector_record[4]
    if (parent is None or parent.kind != "builtin" or parent.callee != "dot"
            or _span(parent) != _EFFECTS_DOT_SPAN
            or parent.children[0] is not vector
            or parent.children[1].symbol is None
            or parent.children[1].symbol.name
            != _EFFECTS_DOT_SECOND_ARGUMENT
            or len(chain) != 1 or chain[0].kind != "return"
            or _span(chain[0]) != _EFFECTS_RETURN_SPAN):
        raise fail("vec4 product dot or return route mismatch")

    host = next(function for function in program.functions
                if (function.id, function.name) == _EFFECTS_HOST)
    proof = GlitchMat4ChainProof(
        program, host, declarations, constructors, matrix_products,
        matrix_ids, vector_products, parent, chain[0], None, None, None)
    if (len(proof.consumed_objects) != 14
            or len({id(item) for item in proof.consumed_objects}) != 14
            or proof.consumed_objects != nodes):
        raise fail("candidate ownership, traversal order, or uniqueness mismatch")
    return proof
