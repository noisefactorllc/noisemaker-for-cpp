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

_RAW_BYTES = 21718
_RAW_SHA256 = "704157151a2aa7e0192bd5b3483d5f1a5532a15a6e3f6a3ee0ba93ce70f8a9e4"
_NORMALIZED_BYTES = 17664
_NORMALIZED_SHA256 = "afb1be09867bbbb02f63c115b84ef4fd813d72defc71e2cc7d8891db9113b1b8"
_FUNCTIONS_SHA256 = "ccf3834882fdd6ff45744377d38bd0b729f3e39d6d58c41c14a43095d6c99bcd"
_DECLARATIONS_SHA256 = "cdbe1347d245c1feb13b2eacce960131ec035882a086c40b9af3ff43d2f8664a"
_WHOLE_SHA256 = "57ad82d28eb34f2ea014122b03d2333099123d7b51dfe91629035ef5f41634f9"
_INTERFACE_SHA256 = "45782fb4605e8e140b66a4e6b462408f79488968895dc6e735d66f5de748a21d"
_FUNCTION_INVENTORY_SHA256 = "fd267bcb5cb3035f9a2174bfd29de118a6dca4d990f1d9eea65d432296a05f81"
_BINDING_INVENTORY_SHA256 = "f7700f10ec7dd723ce09e8657e30d0e6aa5ce3a0e34b79cfe1d5bdbb4e3e5730"
_CALL_GRAPH_SHA256 = "3bdb7adbc622ac11f82f0f664ec124c0c0ee5d90a69906b04e60d260340b3224"
_DEFINES = (("LOOP_OFFSET", "int", "10"),)
_RESOURCES = (
    ("inputTex", "tex", "resolution", "tileOffset", "fullResolution", "time",
     "seed", "blendMode", "loopScale", "paletteMode", "paletteOffset",
     "paletteAmp", "paletteFreq", "palettePhase", "animate", "cyclePalette",
     "rotatePalette", "repeatPalette", "levels", "wrap"),
    ("inputTex", "tex"), ("fragColor",), True, False,
)
_LOOP_PROOF = (1, 0, 1, 3, 3, True)
_REACHABLE = (
    99, 100, 101, 102, 103, 104, 106, 107, 108, 109, 110, 111, 112, 113,
    114, 115, 116, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128,
    130, 131, 132, 133, 134, 135, 136,
)
_UNREACHABLE = (105, 117, 129)
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

# id, name, span, declaration hash, initializer hash
_CONST_GLOBALS = (
    (27, "fwdA", "128:1-130:68",
     "74dce1a09d049a190d6c89cf4db8575973d02a843e258216e6514fcdf3ef45a2",
     "66eed42e1d6e1bd109d8485dd42142239d8777b660eb620c4c961d7d4dcfb0f3"),
    (28, "fwdB", "132:1-134:68",
     "2fdfaceae8692f909d4f38787dc27fb87fe90dd5da007e31e3057537cc1aab45",
     "1139aa5910239889f52ecc36079c4063c771912b5c03dd5b8b99590780d855e0"),
    (29, "invB", "136:1-138:66",
     "9eafe1265e350a625ee33b9ab85f37c514df9de2bc3754dc025ffe8d13c50004",
     "69ae48e48329f2f312c0c0942c1bb018d3f65b93d23e1fbe096a73a693caf4d8"),
    (30, "invA", "140:1-142:68",
     "a4627a80a082de5ab9efef54b36ae3d7113a75b4e9759cebd2604b490225eea9",
     "b49ac117760df6c471b33f34813e8eacc3eb7a9b86f09e0d27254a89df6aa668"),
)

# role, owner, path, span, node hash, result, child types, child hashes,
# parent kind/callee/operator/span/hash.
_EXCEPTION_LOCKS = (
    ("scalar-reflect", 99,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "672:17-672:49", "6c44e7a12325dc21c075e5e06b08aee23db609835b9e903fb9eb490c5fe9969e",
     "reflect", "float", ("float", "float"),
     ("ed3a0fdaff776eaec839706d87ee1d2de848851f51a73268cfed2775251946f7",
      "779362a61f0823d241dcd5647ec4c26b4681c6fd3a1dd4588e758e507b8e7bc6"),
     ("assign", None, "=", "672:9-672:49",
      "7eda259a9e49fcb064fffe21a8c238b2a32302b699953bb20361508292ce639f")),
    ("scalar-refract", 99,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "675:17-675:48", "243e10285acd7fc24f0d3d2496c593d390c23bcfdc33b5c4e97aec43dc80fa03",
     "refract", "float", ("float", "float", "float"),
     ("7f993c5dd0fda155b9363d6a072dee6d1e46f1f62a21faa0d6487be0705df7ea",
      "06cd77dbcb15b967aad710b31e32643b2f6ff64db3bdb5397b5e19f7c0a07499",
      "5c160eb9dc3179a8dd240c040ab76da8e652316c31d170599118193052395376"),
     ("assign", None, "=", "675:9-675:48",
      "0ac43ced9b9ccca9338181fa2203b8ee956e3fc4a6cf456c0f60cf335ec3e823")),
    ("wide-mod", 100,
     (2, "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "619:17-619:45", "adbd6c013236568bbd6bf6b0d9300b02219959ec3bbadef1f5931a36612565e8",
     "mod", "vec3", ("vec3", "vec3"),
     ("29e150c2ffb096a54e8e0f8fa565593d975c508003a4c0f6fcfa35394ba01f62",
      "2f6734aa04b429cd5d6e3583ef576dfeefa774acba49b510a6d02dde36ff4d7a"),
     ("assign", None, "=", "619:9-619:45",
      "f65d5394d1b8da4181737b0f616d8fa776c91ae4ad95955c157354443c654e00")),
    ("vector-reflect", 100,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "625:17-625:49", "e7773612b7e390575ae32f1a215ed0bd4f23deeaa668798f9867ae09984a548d",
     "reflect", "vec3", ("vec3", "vec3"),
     ("602670f7df7c1bbf753e1c924a32d81b7af36e6259c8dd8b213653d505c3cae9",
      "2aa1450e8ff4f97147864eec8aff0718e30f2d015ebd2c09f6fc45d6b03c185b"),
     ("assign", None, "=", "625:9-625:49",
      "077422fb0acd71397427a91c310f7414e87c1ed1e1ef1ba58b7e21da08a92b4b")),
    ("vector-refract", 100,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "628:17-628:48", "9719b815cd3a11bde7a013648ffc9c40681b818c2bc85ee22e224719f1eadbe7",
     "refract", "vec3", ("vec3", "vec3", "float"),
     ("5304a2bfdb126e83a38f6d1b516df2491538ad88890e35c6b33bfe62af0775ed",
      "6ef4e75643fcfeb149d81752d02458a0569a9fe47721770bac182327e2830a2b",
      "4a7750e972e28847767d32c2ea2aa2695e9a43dd6fddf274700466d106c675c2"),
     ("assign", None, "=", "628:9-628:48",
      "12774d36a5c9baf9c2cbe95158999b0cda9fc57d8f416400c0934f7bf03fdb92")),
    ("index-read-condition", 109, (1, "s1", "s0", "e0", 0),
     "116:13-116:22", "528b09c525aada465b6c495d8baba229f4505f035bf289dfcc3a633a1df1fe65",
     None, "float", ("vec3", "int"),
     ("058ef5f1f198fb1455e695846d89d39dacad39a0f66f8e8aacca4cf8a1b087b8",
      "3f4d89d253dd20e27927173fed355d5c470187d8510890c14626b521e5fb1539"),
     ("binary", None, "<=", "116:13-116:35",
      "cca0e10150d6f72e917e8e7a2a47e505bd231d367b6dbe0f065ec9ca60d8c0ab")),
    ("index-write-true", 109, (1, "s1", "s0", "s0", "s0", "e0", 0),
     "117:13-117:20", "4f71a469a541118309586ab52d77595abbaf41ec0bce41bbf6e7df5c207a1b38",
     None, "float", ("vec3", "int"),
     ("959f3b61f8764ca883002e7aa8667baf0c76a3b7e8823eebb9ff6c2387d8cc0b",
      "bc943a59e4ebc946b5398059c9c9f7775654f640e4ed31218ca8d98054f9a58d"),
     ("assign", None, "=", "117:13-117:40",
      "0541fe7a6fb4b8452bd3fc2325ff1060f4a762b29c628efb925fe0346c8a71f1")),
    ("index-read-true", 109, (1, "s1", "s0", "s0", "s0", "e0", 1, 0),
     "117:23-117:32", "f83cbc13499fb9ef2b1342876974d5a9d4e506809d79b5b333ee0982249eb86f",
     None, "float", ("vec3", "int"),
     ("f86dde2924b6be610c405e32c2053dc9623c02fe80abb7c495f4ba589b9321b5",
      "f2b5917c807e9fe50f746c455ad5e0d5d514914d855d039dcb7e1b367e2e7b2b"),
     ("binary", None, "*", "117:23-117:40",
      "94d49303e52ff986536446ae8ca4dcd0cf63790d680870e4a5e6e7955c87deba")),
    ("index-write-false", 109, (1, "s1", "s0", "s1", "s0", "e0", 0),
     "119:13-119:20", "cc5ebbdb32112bacf7f25ff10b7a8b4fde6d7e574b0e69e319f58d41a1e16e32",
     None, "float", ("vec3", "int"),
     ("0cc51a9f6b7d593e97c362a38467134c608c742dd28a63101ac3230cff9c6585",
      "6a212ab12934efc9268fa8a9cff2b6af7db80331449b32a97ffef5f2c59f97f0"),
     ("assign", None, "=", "119:13-119:64",
      "19675d914ce8212e1187c79f650bd5428d2df39ca2fd4898cb421c8122dfcc33")),
    ("index-read-false", 109, (1, "s1", "s0", "s1", "s0", "e0", 1, 0, 1, 0),
     "119:35-119:44", "b845e12b17619d5c93857882f43fb929a365ad00aad60ac1e36907845e3df7f8",
     None, "float", ("vec3", "int"),
     ("0daf5f3cd40bdcc3906affdd465b3f6ce01a01ead5f364d870710093d9930872",
      "a2c9c758dd08b900ee5797276b266c1b1ff687e0f01b5b36faae542caec64b5d"),
     ("builtin", "pow", None, "119:31-119:56",
      "91551bc0a0532e051c340db3cfbdabc489885155960b30c9de5d02f999cc5610")),
    ("bit-ingress", 130, (13, "e0", 0),
     "411:21-411:46", "7af407db873fb245128e37a9607f63e96bd7e045949a7c2a0248935d6680c599",
     "floatBitsToUint", "uint", ("float",),
     ("d1bb910d7ab58e994c9645c4fab7d6a800ebf70ef5cd0bc609d737621c56d11c",),
     ("declaration", None, None, "411:10-411:46",
      "c79dfe491df8e5b426b701baa461aa0cfb756367e46e411c052d7e663acacb5c")),
)

_MOD_CENSUS = (
    (99, "666:17-666:36", "57386c1461b5b02e5edcbbfd8cf46f4401a97bc90a449f59ccf8b0e07565127d", "float", ("float", "float")),
    (100, "619:17-619:45", "adbd6c013236568bbd6bf6b0d9300b02219959ec3bbadef1f5931a36612565e8", "vec3", ("vec3", "vec3")),
    (106, "63:30-63:47", "1d61aff76921611ea30dd0ff6efc5dd6b420175736a09417be4ff132de00f6f5", "float", ("float", "float")),
    (112, "733:23-733:47", "f92b2726df02fe6536aced290f04b8484c4664604ff3b8c45bc5437a5fbd7aef", "float", ("float", "float")),
    (112, "735:23-735:47", "e50012329b384d5e9117616f615f9e27b3360b8f615fb17cf8e285a99bc49513", "float", ("float", "float")),
    (131, "99:17-99:42", "47b130c27dc277962836faf0f603e025a80b5a362f2e1754be86b34ece28715e", "float", ("float", "float")),
)

_FUNCTION_ROLE_HASHES = {
    99: "3877ee17ce46cec2f20c00381354e87f362e5c7379bca09c28ea5e1056423349",
    100: "16e713a6356af4f33fdd40a8420e39e39f4e8ed3b2b9f5fd63c6d2d1c413986c",
    109: "c410aa2bfc7f64fc6339a3a1ade05643b9fbea1b2cc014933b440737fe9a18fb",
    112: "d0a9943cd61f90670be71a0d23a6a656d984e72ade41904b54bb292295b2bc03",
    130: "534f686001db15b2a002c5f8715da35f3c3c91a45796881b5e3a43dea742292f",
}

_MAIN_CALLS = (
    ("blend", 99, "723:20-723:56", "8cb85e3e76db3939f67aa8f0ea7dcaa8c3adfc18d5b5bae059f07eaddc343d48", ("float", "float", "int", "float")),
    ("blend", 100, "727:21-727:75", "0b34c9110e3041f59b25df95ce48454e16f9e8c81f068be353e8e522ab0ddf4b", ("vec3", "vec3", "int", "float")),
)
_MAIN_BLEND_ROUTES = (
    (
        99, (14, "e0", 0),
        ("declaration", None, None, "723:11-723:56",
         "c67d51013e89ab97a8d65f073c2e0feb416d2e20fc6265be4800be1eef4b2c5e"),
        (("decl", "723:5-723:57",
          "737cca3871f7dc83d4e1f912ca2c9364b13f2c7de4598f39fb069fa15ee3a115"),),
        ("id", None, "723:49-723:55",
         "9ca7796c68479b86deedae6ba841d6205cede35a59661f4ff073e0593f9cd904",
         "blendy", None),
    ),
    (
        100, (16, "s0", "s0", "e0", 1),
        ("assign", None, "=", "727:9-727:75",
         "179505623121a11be3b5ed75a653e4fd8cb2d8ebe9518767c2180e6699a6132e"),
        (
            ("if", "726:5-748:6",
             "155f4b7a08e0c8a3a46f031655f66e97c90fa41a2a8e24d41c9fc680d442c2e7"),
            ("block", "726:27-740:6",
             "5cf2e33f208cdf7d61dee631b6099ce6894976f12e38b607fb96851ad8f9dfe0"),
            ("expr", "727:9-727:76",
             "220a0bbcac0e6b576c9d6c703c93b1d3fdfc0dfc6d7d327f4ee0af227af0dccc"),
        ),
        ("binary", "*", "727:62-727:74",
         "3bcdd102775bc8e81bdbc6820f23478c49ee12333c2ae17f7815c61dc839977c",
         "blendy", 0.5),
    ),
)
_PALETTE_MODE_FOUR_BRANCH = (
    "726:5-748:6",
    "155f4b7a08e0c8a3a46f031655f66e97c90fa41a2a8e24d41c9fc680d442c2e7",
    "726:9-726:25",
    "49e5b93881f0de308f53586c21a287510aff5bdcb4bf66e52f7bc3d55ceb376c",
    10, "paletteMode", 4,
    "726:27-740:6",
    "5cf2e33f208cdf7d61dee631b6099ce6894976f12e38b607fb96851ad8f9dfe0",
)
_MAIN_TEXTURES = (
    ("texture", "692:19-692:86", "6dc15c260f31e7470eb68ceec26f2f04b9cb9062e6f4d88027c1591a918acb70", 1, "inputTex"),
    ("textureSize", "692:60-692:84", "6d8442ffe638b8437cef6b443835c5547b99335f34cd1e25e06cee2ba80db442", 1, "inputTex"),
    ("texture", "693:19-693:76", "9ad9f361cb820c713757abae57d3ec0097ad2b83fcf30461219734af79c44e89", 2, "tex"),
    ("textureSize", "693:55-693:74", "da94dd43d85ea8f2f7625e4ae3ecf87413a805039d914a27536e6b6a1d48ef70", 2, "tex"),
)
_ALPHA_ASSIGNMENT = (
    "750:5-750:38", "021c2f3eaf428dd4e90410c72b9c2bf16e09652219f64694875fcc1d8f10d73e",
    "750:15-750:38", "f9ea6fad03074a98d8d7c18a9b0d32a023c35c1682ffe3d8cde5ba637238e0b0",
)

_PROFILE_SHA256 = "77695f0cf5178e79e0daa9763a52a1521cde4e2d05a7f9f09f2b91f8930f46aa"


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
            or len(program.declarations) != 25 or len(program.functions) != 38
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
    scalar_mode = next((item for item in by_id[99].parameters
                        if item.id == 97 and item.name == "mode"
                        and item.type.display() == "int"), None)
    vector_mode = next((item for item in by_id[100].parameters
                        if item.id == 93 and item.name == "mode"
                        and item.type.display() == "int"), None)
    if scalar_mode is None or vector_mode is None:
        raise _fail("blend mode parameter mismatch")
    blend_mode_guards = (
        *_authenticate_blend_ladder(by_id[99], scalar_mode),
        *_authenticate_blend_ladder(by_id[100], vector_mode),
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
                linear_loop.loop_proof.trip_count) != (152, 0, 3, "<", "++", 3)):
        raise _fail("linearToSrgb induction loop mismatch")
    expected_bases = (26, 151, 26, 151, 26)
    expected_roles = ("read", "write", "read", "write", "read")
    for node, parent, base_id, role in zip(
            resolved[5:10], parents[5:10], expected_bases, expected_roles):
        computed_role = ("write" if parent.kind == "assign"
                         and parent.children[0] is node else "read")
        base, induction = node.children
        if (computed_role != role or base.kind != "id"
                or base.symbol_id != base_id or base.symbol is None
                or base.symbol.storage not in {"parameter", "local"}
                or induction.kind != "id" or induction.symbol_id != 152
                or induction.symbol is None or induction.symbol.name != "i"
                or induction.symbol.storage != "local"):
            raise _fail("linearToSrgb index role, base, or induction mismatch")

    ingress = resolved[10]
    ingress_parent = parents[10]
    if (len(ingress.children) != 1 or ingress.children[0].kind != "id"
            or ingress.children[0].symbol_id != 201
            or ingress.children[0].symbol is None
            or ingress.children[0].symbol.name != "seedFrac"
            or ingress_parent.kind != "declaration"
            or ingress_parent.symbol is None
            or ingress_parent.symbol.name != "fracBits"):
        raise _fail("bit ingress source or declaration mismatch")
    seed_declarations = tuple(
        item for function, item, _, _, _ in located
        if function.id == 130 and item.kind == "declaration"
        and item.symbol_id == 201)
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
