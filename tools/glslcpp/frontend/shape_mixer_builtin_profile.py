"""Exact program-owned builtin closure for Shape Mixer.

The canonical JavaScript Shape Mixer contains eleven sites that do not belong
to the globally admitted typed-GLSL vocabulary: four scalar/vector geometric
calls, one ``mod(vec3, vec3)``, one float-bit ingress, and five loop-owned
``vec3[i]`` accesses.  This profile authenticates those exact objects while
composing, rather than duplicating, the existing scalar-uint-XOR authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .scalar_uint_xor_profile import (
    PROFILE as SCALAR_UINT_XOR_PROFILE,
    authenticate_scalar_uint_xor,
)
from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "shape-mixer-builtin-closure-v1"
SHAPE_MIXER_KEY = "classicNoisedeck/shapeMixer:shapeMixer"

_RAW_BYTES = 21721
_RAW_SHA256 = "51bee071387b3498bd9e8abad5ca3b93b3e38100b9a56b8f4abcb177ea9d675b"
_NORMALIZED_BYTES = 17851
_NORMALIZED_SHA256 = "36f5262d84b511775ff69b1afd87d2fe152b0520bd1e43d11f1486544a25e971"
_FUNCTIONS_SHA256 = "4d5a6d975bad8ea45da76519625f9e0117befd61c8ef56e6c6304a652ea234e6"
_DECLARATIONS_SHA256 = "5f58f760f40997486d0300d85e3f9c1d693723502a6b894487529d988e8a1f55"
_WHOLE_SHA256 = "37ede1247f2ff74a9395a82eb076376600d85df56cecb2a546b426654f0e9c0c"
_INTERFACE_SHA256 = "bf71daff66579d830926580982ee7d85115fcbff518a5c72ddc4e49c3c62b338"
_FUNCTION_INVENTORY_SHA256 = "1647bc7c884092edaee7568057cde45a0cef80ae59887c8f91536987ddb44198"
_BINDING_INVENTORY_SHA256 = "9b2d715d6e29a75771d246cc35484388b305e9737188f12f33fa5e334713063f"
_CALL_GRAPH_SHA256 = "062c17809361be5a9a7e73ba678605fc6fab2cf12527c72cce39682c876b5d67"
_DEFINES = (("LOOP_OFFSET", "str", "int"),)
_RESOURCES = (
    ("LOOP_OFFSET", "inputTex", "tex", "resolution", "tileOffset", "fullResolution", "time",
     "seed", "blendMode", "loopScale", "paletteMode", "paletteOffset",
     "paletteAmp", "paletteFreq", "palettePhase", "animate", "cyclePalette",
     "rotatePalette", "repeatPalette", "levels", "wrap"),
    ("inputTex", "tex"), ("fragColor",), True, False,
)
_LOOP_PROOF = (1, 0, 1, 3, 3, True)
_REACHABLE = (100, 101, 102, 103, 104, 105, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 131, 132, 133, 134, 135, 136, 137)
_UNREACHABLE = (106, 118, 130)
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

# id, name, span, declaration hash, initializer hash
_CONST_GLOBALS = (
    (28, "fwdA", "129:1-131:68",
     "a8cefac77a2e94e8c1d3eb4a644ec9a2b1d9b4bebcb678892b56389aed840e91",
     "edf94e2a5a6ba0ac85989263f8987a082a0858982e5b7cec22e86c7efdbf0d79"),
    (29, "fwdB", "133:1-135:68",
     "f61c8246c80aadb71c3285e3ad3943dac854486216e5719c681ab24aa09d16a5",
     "f9aa81bd62c095155e3ed0755dcc58ffa4b3620178e199551dcd309d5992f37e"),
    (30, "invB", "137:1-139:66",
     "58f7f551af30c4eb0aec84d3abbbc16664d0252129108208349fcaa98d5675e0",
     "83656841e37d2966a804eaf48236bda193130c5e72c5695732a15336a03ad882"),
    (31, "invA", "141:1-143:68",
     "0b4e78a7e2f66b92ae8a65fd849361be8245ebc6aa1ee43cb88ecbf58463c493",
     "ae82f11ca9dd1679164fb5967d4c9cce72c6866b6932f4a9231c9b41fc2d4675"),
)

# role, owner, path, span, node hash, result, child types, child hashes,
# parent kind/callee/operator/span/hash.
_EXCEPTION_LOCKS = (
    ("scalar-reflect", 100,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "673:17-673:49", "5045cb75081ad30b37f47829274a4d84b3d5a183d723c696520dccc7c1049a70",
     "reflect", "float", ("float", "float"),
     ("bbdeeacfed7c327534f08ed6f06b7ecf2fbef47b71ac16a3d5f7a7d9a85efe93",
      "5ca405dad16ef9da993bfc788f0b6f8962737bdcf587185af874034898a05266"),
     ("assign", None, "=", "673:9-673:49",
      "62ad97d9ebf87020822c17a5d9b8ad01b8ffc7e971e3d58bd95560eaabadce70")),
    ("scalar-refract", 100,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "676:17-676:48", "7dd97ba627271e0df9304b4faa562056003016a6b856abc9a91fb6837f1a1250",
     "refract", "float", ("float", "float", "float"),
     ("76c95330ab749ecd736f28f96b51d46039581b2865c6088af0ffb35128f88332",
      "eeb20bc0fad0784065cfd2a786c96a0b983cd9e92cd6f610e5a33e4cf756ac3c",
      "742b5ed3f8da69601e8a461b3cae53cb5f00a33d118fe595fe36f77961b9d80d"),
     ("assign", None, "=", "676:9-676:48",
      "8cae58907c20cfe3a86fc71357691219c63a694a4433ab1c4d9d26743c31c20d")),
    ("wide-mod", 101,
     (2, "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "620:17-620:45", "dacf19fda0ee0ed47b9e78e11bd7452c74652e9a99e38f8a517c49259fda664b",
     "mod", "vec3", ("vec3", "vec3"),
     ("ac3e05b8f289c0d5bbbb002f9da1930b8a3abcfeaa2325c361313d62dc89054a",
      "d17e3cdad5c9646979e927ba579f1e4229e32f8c21d16425b9afa815128eacd6"),
     ("assign", None, "=", "620:9-620:45",
      "9f34b46d6e7dd71081767efc522f4e7ed2eedaa8145d7c88b9407d34f935c7c0")),
    ("vector-reflect", 101,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "626:17-626:49", "b18d1b096fd7145f0d97b18653d19762b5d2ad1464a52a2998a0612025c99bae",
     "reflect", "vec3", ("vec3", "vec3"),
     ("9895d0c823929c64078d778b56011b5c443515b6a5ac95bdead542792ccc9a26",
      "ab1b402d371f9558bcb38fa2598b3169cc6f5306c647434be66dfdadc38aae64"),
     ("assign", None, "=", "626:9-626:49",
      "6b63f7e782cd266a221bc116e70d48f0b9a5e03f73df261d8027fec84e22b4a5")),
    ("vector-refract", 101,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "629:17-629:48", "0250c85e308951bec47ecf56433d64663970550edf4d991c2f3f8fcbc41229f0",
     "refract", "vec3", ("vec3", "vec3", "float"),
     ("0271787617cf2d6fc6575cc4c4cf47f8b801e59e7396236deee8e1aef33e2db0",
      "bae59d9eebc0895b033defb52a3facc9cd458eda99aabaf71657acccd73df4c2",
      "63221acf2dd1082ab608e850b776f2d151b548b9bd2b15d462c3b3602e6223af"),
     ("assign", None, "=", "629:9-629:48",
      "1e42706578afe06c92350dbc71cedc3d694e271d048e5b175c8fa210d236478a")),
    ("index-read-condition", 110, (1, "s1", "s0", "e0", 0),
     "117:13-117:22", "7a32adcee60da8a66001a09a0ab8b2e04b6f7a1d2945f2d40524e7848f97e606",
     None, "float", ("vec3", "int"),
     ("11e9842e0beb82382542da9322ac52549e280e3f71d9c290a11535750a235d6e",
      "d83137672b3cc9b68238e423e97e300f542d7476e06a57603468cc5f5bbc6304"),
     ("binary", None, "<=", "117:13-117:35",
      "b6f2a15c14735ae2c83b7a35b61d69ae24ac2a04b6613bee88ec03e0a143ad5f")),
    ("index-write-true", 110, (1, "s1", "s0", "s0", "s0", "e0", 0),
     "118:13-118:20", "e4d1ee42457c08ef1827d6335386ccdd8df9942e27b7dd5a98db7dc2e9df7970",
     None, "float", ("vec3", "int"),
     ("f3afff7a6bd8267ab935dbfde0a56afe558c88951c166e8805011ba35efacd5d",
      "9287b57ccfea499d0ed35a97f73651c5022104946a6db2158cff26028ee3241c"),
     ("assign", None, "=", "118:13-118:40",
      "d198f3ce95b2c7a62eeeb972fe66b628e6f56fca24e8e78d01544a68cf1187df")),
    ("index-read-true", 110, (1, "s1", "s0", "s0", "s0", "e0", 1, 0),
     "118:23-118:32", "111dc670dae564fb17b67faccaa8121a46331d01ace7e7bd12d4b9f9e8dadd5c",
     None, "float", ("vec3", "int"),
     ("572d172fc744ed51b881ef65f7f9084d8ed43b7e767bfbc344f46fb67f403955",
      "a4c209364705bbbd848bbe446d5824461ff7c4475ecf2f58c79b48bc0d0fbb9b"),
     ("binary", None, "*", "118:23-118:40",
      "17f2b775c3f37a33d358be862e463afde0ee376a74cb0efd523e2732e46e4182")),
    ("index-write-false", 110, (1, "s1", "s0", "s1", "s0", "e0", 0),
     "120:13-120:20", "bdff1f0f2cbc55e47e5a4e638ffe9c718c39d0e9e82f719fa49a7e40830448f0",
     None, "float", ("vec3", "int"),
     ("d9ab79002351f46330cae4395ae7e91429e1e14d0ca84a12f9591664d6df7abb",
      "c3fc52fd53e558cd7934757c15a46562c0640fdf98b714ec04b0a3073eb1aa1d"),
     ("assign", None, "=", "120:13-120:64",
      "38d0665016dd4e4695ba42ac1cb67d29eb2a88394b2e1ffb001039aa51e76b80")),
    ("index-read-false", 110, (1, "s1", "s0", "s1", "s0", "e0", 1, 0, 1, 0),
     "120:35-120:44", "b11c80b1d7b7e50433a1ff34e5381cd224aa22b5e08ca2a8d0f070716ffad4f9",
     None, "float", ("vec3", "int"),
     ("7e640399e97a5525dd7acc31f34543fd2cd54339416e123a500291a0c09fe9cd",
      "44eb8ba53e5222c2c7e04b23d2d16a7e91e533a007046ab07edc76a542ae390f"),
     ("builtin", "pow", None, "120:31-120:56",
      "ecaeee7f727d4ae1a347c49dbdd29b422a860920eaaca56c4b43c42878cf9bfb")),
    ("bit-ingress", 131, (13, "e0", 0),
     "412:21-412:46", "94f9ec6d6f5edfd238a9330ec55abd84e2a8e8a3ad663f4ed396a7e0e35a17a4",
     "floatBitsToUint", "uint", ("float",),
     ("47ddc9044daacd00767b4495ef251cc56c72cb4421c5bca0c3f101efd26b5154",),
     ("declaration", None, None, "412:10-412:46",
      "08b57c22f729f4a7df7260dd8612ea5bde30e365672b56312b2ee1599b76a9b7")),
)

_MOD_CENSUS = (
    (100, "667:17-667:36", "a5ecd2110ed420afc076aa7c98dd528615c11466de79abae6497e046690128c2", "float", ("float", "float")),
    (101, "620:17-620:45", "dacf19fda0ee0ed47b9e78e11bd7452c74652e9a99e38f8a517c49259fda664b", "vec3", ("vec3", "vec3")),
    (107, "64:30-64:47", "0224b6cf7ae5d2463adb927603afcaef9bdcc70f349f01aca7d080e0c0ccd997", "float", ("float", "float")),
    (113, "734:23-734:47", "04bffbf18d7143496bb6836f871abbdd48d3cf31a2b31fd9c0fd7b347eef0958", "float", ("float", "float")),
    (113, "736:23-736:47", "2d0822712ebbf6b812d63ec508df30a9da13138e4dcee9914412f6dff191f618", "float", ("float", "float")),
    (132, "100:17-100:42", "3b6d793c0567b2629974b92c0369d2e0b2dd643dac0f97c4d0851ce53152c78a", "float", ("float", "float")),
)

_FUNCTION_ROLE_HASHES = {
    100: "cfcb4370e9f1d6f5df37971771132778c9914b9d3b3787737aa26f5ce06fd733",
    101: "117e1edf127f616a40cb16d7f84ee976553052d4c453f169366b7cf808a8bfbf",
    110: "63f9db2f5acea2a307ea08dffc8edc2a728a42b069b6f92a129f7bfe6df4bc63",
    113: "895f49be047ddb7a4aaf6169aa4d3f74d4706a5cfab8c2a703e82ffd04f95395",
    131: "ff93c17d78c0c3e6a6c1f3dae65bcd4232e6812a510bfbbd037d4e663a5447ce",
}

_MAIN_CALLS = (
    ("blend", 100, "724:20-724:56", "862701a40d0220d8eb6b5a8e80f39b3819bb5f45b55a2ccd79cb871feab50440", ("float", "float", "int", "float")),
    ("blend", 101, "728:21-728:75", "3469d0c48452c2ba134608977cbd76ea1640cece15295aa257e8f293fd859938", ("vec3", "vec3", "int", "float")),
)
_MAIN_BLEND_ROUTES = (
    (
        100, (14, "e0", 0),
        ("declaration", None, None, "724:11-724:56",
         "d54e24d7c0dc88372ef4db9ae8bc3e64efcdf0d965c4a752e7011a4afe498ac2"),
        (("decl", "724:5-724:57",
          "0a0be4cb1e9b681cb812223936936a55feaef4c104d354febe64530bd6501f7a"),),
        ("id", None, "724:49-724:55",
         "07c23010a45401cc267ff2f232648b8a10900f6ec5e95861e6f09ea7114342fa",
         "blendy", None),
    ),
    (
        101, (16, "s0", "s0", "e0", 1),
        ("assign", None, "=", "728:9-728:75",
         "d0343f61fc19a5b41c4f34b0d3e178496e092ac52ecaffed25c1284d149f14d4"),
        (
            ("if", "727:5-749:6",
             "4daf483ddb9d65f86253258f96880d3c5757e880db69ab215da860765e2e02ff"),
            ("block", "727:27-741:6",
             "ef47da46a44cc6a079eda8f7d2af85b6017700c66db93c7232f91e52eca71825"),
            ("expr", "728:9-728:76",
             "2e5145bb87a4d4b8a869b7069430a5cb758805d979e71b77685d2cf1b3eb4a72"),
        ),
        ("binary", "*", "728:62-728:74",
         "f19e4442cca85edb72b467933b52779dda18497a4821c863189f824ebdf87e52",
         "blendy", 0.5),
    ),
)
_PALETTE_MODE_FOUR_BRANCH = (
    "727:5-749:6",
    "4daf483ddb9d65f86253258f96880d3c5757e880db69ab215da860765e2e02ff",
    "727:9-727:25",
    "5838c100a024cc5a6c1cffbd5fcf74743ff7782e846e86b2a6b9af6e77e980c1",
    11, "paletteMode", 4,
    "727:27-741:6",
    "ef47da46a44cc6a079eda8f7d2af85b6017700c66db93c7232f91e52eca71825",
)
_MAIN_TEXTURES = (
    ("texture", "693:19-693:86", "fa191e42669afdc7aef53558c22779adc30d9b65a379f81da6bab86c5f6e21db", 2, "inputTex"),
    ("textureSize", "693:60-693:84", "41a2022bd93069c740e7998eaabcc4081ed943295134a421fc2c399f745c6cb5", 2, "inputTex"),
    ("texture", "694:19-694:76", "fab8f66860f495af2ae9fece5ba816c1b4d3eacd09279df4dd30f4371c4e4c6c", 3, "tex"),
    ("textureSize", "694:55-694:74", "34d3e4c557391ed9be4243a38049e7e0153e0d10e627381ba414d4b94b8c6bf1", 3, "tex"),
)
_ALPHA_ASSIGNMENT = (
    "751:5-751:38", "ac425225e4f3eaa6b250919d43a106c4d594a0ee4d36e1c92115f692b2a810c8",
    "751:15-751:38", "2174d33c86a607bbec07e7b27eaf3c68f819fdf18930ba48b57c9f385fc49a67",
)

_PROFILE_SHA256 = "a7f58e4809c72e7707ef5635f981bd24ea677c1ebd3e063e2d180bcc98ccdcdf"


@dataclass(frozen=True, slots=True)
class ShapeMixerBuiltinProof:
    _candidate: TypedProgram
    blend_mode_guards: tuple[TypedExpression, ...]
    reflect_nodes: tuple[TypedExpression, TypedExpression]
    refract_nodes: tuple[TypedExpression, TypedExpression]
    wide_mod_node: TypedExpression
    dynamic_indexes: tuple[TypedExpression, ...]
    bit_ingress: TypedExpression
    exceptional_nodes: tuple[TypedExpression, ...]
    exceptional_parents: tuple[TypedExpression, ...]
    linear_srgb_loop: TypedStatement
    companion_scalar_uint_xors: tuple[TypedExpression, ...]

    @property
    def consumed_objects(self) -> tuple[TypedExpression, ...]:
        return self.exceptional_nodes


__all__ = (
    "PROFILE", "SHAPE_MIXER_KEY", "ShapeMixerBuiltinProof",
    "authenticate_shape_mixer_builtin_closure",
    "apply_shape_mixer_builtin_closure",
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
    return (
        PROFILE, SHAPE_MIXER_KEY, _RAW_BYTES, _RAW_SHA256,
        _NORMALIZED_BYTES, _NORMALIZED_SHA256, _FUNCTIONS_SHA256,
        _DECLARATIONS_SHA256, _WHOLE_SHA256, _INTERFACE_SHA256,
        _FUNCTION_INVENTORY_SHA256, _BINDING_INVENTORY_SHA256,
        _CALL_GRAPH_SHA256, _DEFINES, _RESOURCES, _LOOP_PROOF,
        _REACHABLE, _UNREACHABLE, _CONST_GLOBALS, _EXCEPTION_LOCKS,
        _MOD_CENSUS, tuple(sorted(_FUNCTION_ROLE_HASHES.items())),
        _MAIN_CALLS, _MAIN_BLEND_ROUTES, _PALETTE_MODE_FOUR_BRANCH,
        _MAIN_TEXTURES, _ALPHA_ASSIGNMENT,
    )


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
        yield from (
            (*record, chain)
            for record in _walk_expression(
                expression, None, (*path, f"e{index}"))
        )
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def _located(program: TypedProgram):
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for record in _walk_statement(statement, (index,)):
                yield function, *record


def _parent_record(parent: TypedExpression | None):
    if parent is None:
        return None
    return (parent.kind, parent.callee, parent.operator, _span(parent), _sha(parent))


def _authenticate_blend_ladder(
        function: TypedFunction, mode_symbol: object) -> tuple[TypedExpression, ...]:
    if len(function.body) != 4:
        raise _fail("blend body topology mismatch")
    factor_statement = function.body[1]
    if (factor_statement.kind != "expr"
            or len(factor_statement.expressions) != 1):
        raise _fail("blend factor inversion statement mismatch")
    assignment = factor_statement.expressions[0]
    if (assignment.kind != "assign" or assignment.operator != "="
            or len(assignment.children) != 2
            or assignment.children[0].kind != "id"
            or assignment.children[0].symbol is None
            or assignment.children[0].symbol.name != "factor"
            or assignment.children[1].kind != "binary"
            or assignment.children[1].operator != "-"
            or tuple(child.literal_value
                     if child.kind == "literal" else None
                     for child in assignment.children[1].children) != (1.0, None)
            or assignment.children[1].children[1].kind != "id"
            or assignment.children[1].children[1].symbol is None
            or assignment.children[1].children[1].symbol.name != "factor"):
        raise _fail("blend factor inversion mismatch")

    current = function.body[2]
    guards: list[TypedExpression] = []
    for expected_mode in range(10):
        if (current.kind != "if" or len(current.expressions) != 1
                or len(current.children) != 2):
            raise _fail("blend branch-ladder topology mismatch")
        condition = current.expressions[0]
        if (condition.kind != "binary" or condition.operator != "=="
                or condition.type.display() != "bool"
                or len(condition.children) != 2
                or condition.children[0].kind != "id"
                or condition.children[0].type.display() != "int"
                or condition.children[0].symbol is not mode_symbol
                or condition.children[1].kind != "literal"
                or condition.children[1].type.display() != "int"
                or condition.children[1].literal_value != expected_mode
                or isinstance(condition.children[1].literal_value, bool)):
            raise _fail("blend mode condition mismatch")
        guards.append(condition)
        current = current.children[1]
    if current.kind != "block":
        raise _fail("blend mode order or fallback mismatch")
    returned = function.body[3]
    if (returned.kind != "return" or len(returned.expressions) != 1
            or returned.expressions[0].kind != "id"
            or returned.expressions[0].symbol is None
            or returned.expressions[0].symbol.name != "color"):
        raise _fail("blend result route mismatch")
    return tuple(guards)


def authenticate_shape_mixer_builtin_closure(
        program: TypedProgram, source_hash: str | None,
        profile: str | None,
        scalar_uint_xor_profile: str | None) -> ShapeMixerBuiltinProof:
    """Authenticate and return exact candidate-owned Shape Mixer objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if scalar_uint_xor_profile != SCALAR_UINT_XOR_PROFILE:
        raise _fail("exact scalar uint XOR profile carrier required")
    if program.key != SHAPE_MIXER_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    resources = program.resources
    resource_tuple = (
        resources.uniforms, resources.samplers, resources.outputs,
        resources.uses_texture, resources.uses_derivatives,
    )
    function_inventory = tuple(
        (item.signature.id, item.name, item.return_type.display(),
         len(item.parameters), len(item.body), _span(item))
        for item in program.functions)
    binding_inventory = tuple(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable)
        for item in program.declarations)
    loop = program.counted_loop_proof
    loop_tuple = None if loop is None else (
        loop.loop_count, loop.unproved_loop_count, loop.max_effective_depth,
        loop.max_lexical_product, loop.entrypoint_charge,
        loop.call_graph_acyclic,
    )
    if (len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _sha(program.declarations) != _DECLARATIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256
            or _sha(function_inventory) != _FUNCTION_INVENTORY_SHA256
            or _sha(binding_inventory) != _BINDING_INVENTORY_SHA256
            or defines != _DEFINES or resource_tuple != _RESOURCES
            or loop_tuple != _LOOP_PROOF or program.body_status != "analyzed"
            or len(program.declarations) != 26 or len(program.functions) != 38
            or program.structs != () or program.uniform_blocks != ()):
        raise _fail("source, define, function, program, or interface mismatch")
    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated structural proof carrier is present")

    globals_actual = tuple(
        (item.symbol.id, item.symbol.name, _span(item), _sha(item),
         None if item.initializer is None else _sha(item.initializer))
        for item in program.declarations if item.symbol.storage == "const")
    if (globals_actual != _CONST_GLOBALS
            or any(item.type.display() != "mat3" for item in program.declarations
                   if item.symbol.storage == "const")):
        raise _fail("const mat3 global closure mismatch")

    companion = authenticate_scalar_uint_xor(
        program, source_hash, scalar_uint_xor_profile)

    located = tuple(_located(program))
    names = {item.id: item.name for item in program.functions}
    calls: dict[int, list[int]] = {item.id: [] for item in program.functions}
    for function, item, _, _, _ in located:
        if item.kind == "call" and item.signature_id in names:
            calls[function.id].append(item.signature_id)
    call_graph = tuple((item.id, tuple(calls[item.id]))
                       for item in program.functions)
    main = [item for item in program.functions if item.name == "main"]
    if len(main) != 1:
        raise _fail("main or call graph mismatch")
    reachable: set[int] = set()
    pending = [main[0].id]
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(calls[current])
    if (_sha(call_graph) != _CALL_GRAPH_SHA256
            or tuple(sorted(reachable)) != _REACHABLE
            or tuple(sorted(set(calls) - reachable)) != _UNREACHABLE):
        raise _fail("call graph or reachability mismatch")

    by_id = {item.id: item for item in program.functions}
    if (any(item_id not in by_id or _sha(by_id[item_id]) != expected
            for item_id, expected in _FUNCTION_ROLE_HASHES.items())):
        raise _fail("role-owning function mismatch")
    scalar_mode = next((item for item in by_id[100].parameters
                        if item.id == 98 and item.name == "mode"
                        and item.type.display() == "int"), None)
    vector_mode = next((item for item in by_id[101].parameters
                        if item.id == 94 and item.name == "mode"
                        and item.type.display() == "int"), None)
    if scalar_mode is None or vector_mode is None:
        raise _fail("blend mode parameter mismatch")
    blend_mode_guards = (
        *_authenticate_blend_ladder(by_id[100], scalar_mode),
        *_authenticate_blend_ladder(by_id[101], vector_mode),
    )

    resolved: list[TypedExpression] = []
    parents: list[TypedExpression] = []
    chains: list[tuple[TypedStatement, ...]] = []
    for lock in _EXCEPTION_LOCKS:
        (role, owner_id, expected_path, expected_span, expected_hash,
         callee, result_type, child_types, child_hashes,
         expected_parent) = lock
        matches = [record for record in located
                   if record[0].id == owner_id and record[3] == expected_path]
        if len(matches) != 1:
            raise _fail(f"{role} owner or expression path mismatch")
        _, node, parent, _, chain = matches[0]
        expected_kind = "index" if role.startswith("index-") else "builtin"
        if (node.kind != expected_kind or node.callee != callee
                or node.type.display() != result_type
                or node.category not in {"rvalue", "lvalue"}
                or _span(node) != expected_span or _sha(node) != expected_hash
                or tuple(child.type.display() for child in node.children)
                != child_types
                or tuple(_sha(child) for child in node.children) != child_hashes
                or _parent_record(parent) != expected_parent):
            raise _fail(f"{role} node, children, or parent mismatch")
        if parent is None:
            raise _fail(f"{role} parent identity mismatch")
        resolved.append(node)
        parents.append(parent)
        chains.append(chain)

    all_reflect = tuple(item for _, item, _, _, _ in located
                        if item.kind == "builtin" and item.callee == "reflect")
    all_refract = tuple(item for _, item, _, _, _ in located
                        if item.kind == "builtin" and item.callee == "refract")
    all_indexes = tuple(item for _, item, _, _, _ in located
                        if item.kind == "index")
    all_ingress = tuple(item for _, item, _, _, _ in located
                        if (item.kind == "builtin"
                            and item.callee == "floatBitsToUint"))
    if (all_reflect != (resolved[0], resolved[3])
            or all_refract != (resolved[1], resolved[4])
            or all_indexes != tuple(resolved[5:10])
            or all_ingress != (resolved[10],)):
        raise _fail("exceptional whole-program census mismatch")

    mod_census = tuple(
        (function.id, _span(item), _sha(item), item.type.display(),
         tuple(child.type.display() for child in item.children))
        for function, item, _, _, _ in located
        if item.kind == "builtin" and item.callee == "mod")
    if mod_census != _MOD_CENSUS:
        raise _fail("complete mod census mismatch")

    linear_loop = chains[5][0] if chains[5] else None
    if (linear_loop is None
            or any(not chain or chain[0] is not linear_loop
                   for chain in chains[5:10])
            or linear_loop.kind != "for" or linear_loop.loop_proof is None
            or (linear_loop.loop_proof.induction_symbol_id,
                linear_loop.loop_proof.start_value,
                linear_loop.loop_proof.bound_value,
                linear_loop.loop_proof.comparison,
                linear_loop.loop_proof.update,
                linear_loop.loop_proof.trip_count) != (153, 0, 3, "<", "++", 3)):
        raise _fail("linearToSrgb induction loop mismatch")
    expected_bases = (27, 152, 27, 152, 27)
    expected_roles = ("read", "write", "read", "write", "read")
    for node, parent, base_id, role in zip(
            resolved[5:10], parents[5:10], expected_bases, expected_roles):
        computed_role = ("write" if parent.kind == "assign"
                         and parent.children[0] is node else "read")
        base, induction = node.children
        if (computed_role != role or base.kind != "id"
                or base.symbol_id != base_id or base.symbol is None
                or base.symbol.storage not in {"parameter", "local"}
                or induction.kind != "id" or induction.symbol_id != 153
                or induction.symbol is None or induction.symbol.name != "i"
                or induction.symbol.storage != "local"):
            raise _fail("linearToSrgb index role, base, or induction mismatch")

    ingress = resolved[10]
    ingress_parent = parents[10]
    if (len(ingress.children) != 1 or ingress.children[0].kind != "id"
            or ingress.children[0].symbol_id != 202
            or ingress.children[0].symbol is None
            or ingress.children[0].symbol.name != "seedFrac"
            or ingress_parent.kind != "declaration"
            or ingress_parent.symbol is None
            or ingress_parent.symbol.name != "fracBits"):
        raise _fail("bit ingress source or declaration mismatch")
    seed_declarations = tuple(
        item for function, item, _, _, _ in located
        if function.id == 131 and item.kind == "declaration"
        and item.symbol_id == 202)
    if (len(seed_declarations) != 1
            or len(seed_declarations[0].children) != 1
            or seed_declarations[0].children[0].kind != "literal"
            or seed_declarations[0].children[0].literal_value != 0.0):
        raise _fail("seedFrac positive-zero source mismatch")
    frac_bits_id = ingress_parent.symbol_id
    if any(sum(1 for child, _, _ in _walk_expression(value)
               if child.kind == "id" and child.symbol_id == frac_bits_id) != 1
           for value in companion):
        raise _fail("bit ingress to scalar-XOR ancestry mismatch")

    main_nodes = tuple(record for record in located if record[0] is main[0])
    main_calls = tuple(
        (item.callee, item.signature_id, _span(item), _sha(item),
         tuple(child.type.display() for child in item.children))
        for _, item, _, _, _ in main_nodes
        if item.kind == "call" and item.callee == "blend")
    if main_calls != _MAIN_CALLS:
        raise _fail("scalar/vector blend call route mismatch")
    blend_records = tuple(record for record in main_nodes
                          if record[1].kind == "call"
                          and record[1].callee == "blend")
    blend_routes = []
    for _, item, parent, path, chain in blend_records:
        factor = item.children[3]
        factor_name = (factor.symbol.name
                       if factor.kind == "id" and factor.symbol is not None
                       else factor.children[0].symbol.name
                       if factor.kind == "binary" and factor.children
                       and factor.children[0].kind == "id"
                       and factor.children[0].symbol is not None else None)
        factor_literal = (factor.children[1].literal_value
                          if factor.kind == "binary"
                          and len(factor.children) == 2
                          and factor.children[1].kind == "literal" else None)
        blend_routes.append((
            item.signature_id, path, _parent_record(parent),
            tuple((statement.kind, _span(statement), _sha(statement))
                  for statement in chain),
            (factor.kind, factor.operator, _span(factor), _sha(factor),
             factor_name, factor_literal),
        ))
    if tuple(blend_routes) != _MAIN_BLEND_ROUTES:
        raise _fail("scalar/vector blend statement or eta ancestry mismatch")

    vector_chain = blend_records[1][4]
    palette_branch = vector_chain[0]
    if (len(vector_chain) != 3 or palette_branch is not main[0].body[16]
            or palette_branch.kind != "if"
            or len(palette_branch.expressions) != 1
            or len(palette_branch.children) != 2
            or vector_chain[1] is not palette_branch.children[0]):
        raise _fail("scalar/vector blend palette ancestry mismatch")
    condition = palette_branch.expressions[0]
    left, right = condition.children if len(condition.children) == 2 else (None, None)
    palette_lock = (
        _span(palette_branch), _sha(palette_branch),
        _span(condition), _sha(condition),
        None if left is None else left.symbol_id,
        None if left is None or left.symbol is None else left.symbol.name,
        None if right is None else right.literal_value,
        _span(palette_branch.children[0]), _sha(palette_branch.children[0]),
    )
    if (condition.kind != "binary" or condition.operator != "=="
            or left is None or left.kind != "id"
            or right is None or right.kind != "literal"
            or palette_lock != _PALETTE_MODE_FOUR_BRANCH):
        raise _fail("scalar/vector blend palette ancestry mismatch")

    texture_roles = tuple(
        (item.callee, _span(item), _sha(item), item.children[0].symbol_id,
         item.children[0].symbol.name if item.children[0].symbol else None)
        for _, item, _, _, _ in main_nodes
        if item.kind == "builtin" and item.callee in {"texture", "textureSize"})
    if texture_roles != _MAIN_TEXTURES:
        raise _fail("two-texture identity mismatch")
    alpha_matches = [
        (item, parent) for _, item, parent, _, _ in main_nodes
        if item.kind == "builtin" and item.callee == "max"
        and _span(item) == _ALPHA_ASSIGNMENT[2]]
    if len(alpha_matches) != 1:
        raise _fail("alpha max cardinality mismatch")
    alpha, alpha_parent = alpha_matches[0]
    if (alpha_parent is None or alpha_parent.kind != "assign"
            or _span(alpha_parent) != _ALPHA_ASSIGNMENT[0]
            or _sha(alpha_parent) != _ALPHA_ASSIGNMENT[1]
            or _sha(alpha) != _ALPHA_ASSIGNMENT[3]
            or tuple(child.member for child in alpha.children) != ("a", "a")
            or tuple(child.children[0].symbol.name for child in alpha.children)
            != ("color1", "color2")):
        raise _fail("alpha provenance mismatch")

    exceptional = tuple(resolved)
    proof = ShapeMixerBuiltinProof(
        program, blend_mode_guards,
        (resolved[0], resolved[3]), (resolved[1], resolved[4]),
        resolved[2], tuple(resolved[5:10]), resolved[10], exceptional,
        tuple(parents), linear_loop, tuple(companion),
    )
    if (len(proof.blend_mode_guards) != 20
            or len({id(item) for item in proof.blend_mode_guards}) != 20
            or len(proof.exceptional_nodes) != 11
            or len({id(item) for item in proof.exceptional_nodes}) != 11
            or len(proof.companion_scalar_uint_xors) != 3
            or any(not any(item is candidate for candidate in companion)
                   for item in proof.companion_scalar_uint_xors)):
        raise _fail("candidate ownership or exceptional closure mismatch")
    return proof


def apply_shape_mixer_builtin_closure(
        program: TypedProgram, source_hash: str | None,
        profile: str | None,
        scalar_uint_xor_profile: str | None) -> TypedProgram:
    authenticate_shape_mixer_builtin_closure(
        program, source_hash, profile, scalar_uint_xor_profile)
    return program
