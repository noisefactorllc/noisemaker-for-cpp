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

_RAW_BYTES = 21644
_RAW_SHA256 = "ae511c7398c65a9a8b5adc09d00efda254184da5636abea143685a92363e1a7c"
_NORMALIZED_BYTES = 17774
_NORMALIZED_SHA256 = "516d15fb18681e6a1fde12d362020a346ee930ad58ec3b08981f6ef2d181bee8"
_FUNCTIONS_SHA256 = "44fba2b858584cd9e81c1fe9396f6374b613045bfcd185742d04e0ee6ab9fe05"
_DECLARATIONS_SHA256 = "e68476a90590c6bfdf6a8630f0846e0d16ad3b35ce35362a1d889c6df622a810"
_WHOLE_SHA256 = "8533f8cd7aff64fd1e056aa27dca41883a02e38d778264ace206aa0b8844ea4c"
_INTERFACE_SHA256 = "97a6777022e8c71daab763d7369e9ba078a45175621511b01fc7c78ffcfacea9"
_FUNCTION_INVENTORY_SHA256 = "7ac00d993b42c2c370001901de747900067be29ffd441604e250de67d12411e1"
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
    (28, "fwdA", "127:1-129:68",
     "6b7258f36e1794ca19d8d64220b3df0548c7241ec0390c4a9d69df20087e0ba5",
     "e1c97313ecb2a866fe80ecb6725619ae0ec3747325969ddfd879847521df66d0"),
    (29, "fwdB", "131:1-133:68",
     "d0d68ffc4946c603b68a217ef880133e1af5489de43cefa2f48f431a114662fd",
     "7842b8f874c7bffbf1556d2a625c4ad093dc2afecb6a56a9b8828580999385fb"),
    (30, "invB", "135:1-137:66",
     "c57d309c46fa46030048efc0ba5a1ed1a4dc6a1422a2c9699f24b50225c7e22d",
     "996530fecbf39f7eaeb9b84d5de1c5fc26186062a30daa16f8fdd84ba3d0f574"),
    (31, "invA", "139:1-141:68",
     "875cb6681abd441f9c7a9126e0b94cbcb3fc6ebd0ba3db003b19c9b3080d2f28",
     "fd723ffcb52e0d3d5605ff2eed88cd08b28866032c88135a19b951ab288b7d83"),
)

# role, owner, path, span, node hash, result, child types, child hashes,
# parent kind/callee/operator/span/hash.
_EXCEPTION_LOCKS = (
    ("scalar-reflect", 100,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "671:17-671:49", "dd8989bcbe26a04cc4a03e3bc29bfec0784ac6fde2c805bc0102ce0a4fa3f604",
     "reflect", "float", ("float", "float"),
     ("522a7dfbe254b3cf986564f9c07290b6e4edda92f48f2c45176bfc65f6694ade",
      "671607ac43175f9d66aa1b907764add3bf0b9205716b9a62dd31cd6c7a409eac"),
     ("assign", None, "=", "671:9-671:49",
      "ada9a35208b760d0667e84d0f05c25b612b0dfb9d8886c9b26a11080a54f14bd")),
    ("scalar-refract", 100,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "674:17-674:48", "c4873796528d1be3254f6b872670a315d31d0f355d6b1a7e6f5f5da26948a0d1",
     "refract", "float", ("float", "float", "float"),
     ("c9cd5062e05f3c54e360a92c68ec7f027a49e82aff23513cfb91d3eda53cd196",
      "a12d73e2b91fb279a98dbb94e91240990908b27717513bcdeb705cb21cdf5a74",
      "e38d7107d45ef33ff03675a4528bc2b80574a8178392537c8298ba2e2b17642e"),
     ("assign", None, "=", "674:9-674:48",
      "19131fef108aad9d48750ad448b5e4ff85a6fdc31022670412d516f56f00cb36")),
    ("wide-mod", 101,
     (2, "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "618:17-618:45", "90aed381a5fa4f1c4e18a58c45fd44121afc7e6211b1173d71467b816e4f1ce4",
     "mod", "vec3", ("vec3", "vec3"),
     ("ec2d40314d3f58d11c26676c5e95ec42588f0faa9ce2e44e3bda59a468173d19",
      "2e860cac19d695ff7ed08fb5b691c2bdbc42f0a0494ffec78c6ac4d67bf988fa"),
     ("assign", None, "=", "618:9-618:45",
      "ce8ef7a9300a5d31a9198a7847c036efdcae774022e75e8a6b82a7403144faca")),
    ("vector-reflect", 101,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "624:17-624:49", "e27c175b4dd8200c554b908a77f9ecfa00db186334a7b7f4ce35c57afbaa6bc4",
     "reflect", "vec3", ("vec3", "vec3"),
     ("37162c6202a8348d5ba06c76482ac192f34a27c54e960befa99aff21335118b0",
      "ea6cfd52c41ad63836515ddf3b3b970ab8a697255f7d699a97f80170df5954f5"),
     ("assign", None, "=", "624:9-624:49",
      "3e46de39fb3821f5b0b44f42205116f2e2ad467fc806371e0dbc38bea5c7cc3e")),
    ("vector-refract", 101,
     (2, "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s1", "s0", "s0", "e0", 1),
     "627:17-627:48", "6a11283147a42141a598892e24a8eb9a61cc5ff93723f9f672394fb2088b831f",
     "refract", "vec3", ("vec3", "vec3", "float"),
     ("a580e42f35a88ed603061c4bc9ac14eb661456e1c0168e33af5766121c20b7ef",
      "30b05ecfe601b7ad6808ff32ca87faf21417b4ed0e995c8c978576d37bff77ff",
      "ecedbe692546a2b545b76071aea01b5dc69b6c53ce1fb50c686c04b2c675152e"),
     ("assign", None, "=", "627:9-627:48",
      "f14c48c43acb5f10d24addcbcc2bfa9ecc2ecfa5f96b5b79f670793d616ec816")),
    ("index-read-condition", 110, (1, "s1", "s0", "e0", 0),
     "115:13-115:22", "dd9fded42b9a8c03fc18bffb2d1e48cb8272e8f91ef1a57fd09c91f9e83e42a3",
     None, "float", ("vec3", "int"),
     ("40bf31df9593b34669fd572bf96217c6d28d000d43c799b708f48cceb3ee7627",
      "ca5a00d6c53abfe2b2484a2eaf7740044c3b28ebe8158bbc3211d28d32a405b8"),
     ("binary", None, "<=", "115:13-115:35",
      "c4661b88e73191bd24a2384098d9b7aedcf1c98db26a1dacd878ad0ecc5c7fd6")),
    ("index-write-true", 110, (1, "s1", "s0", "s0", "s0", "e0", 0),
     "116:13-116:20", "b0dfaa11cc94aaedef5a56970619364113a041798845a87bcdaa843dff823e3f",
     None, "float", ("vec3", "int"),
     ("ddf7f6480529de632747378e4aee1c01d24afbbd65a859ce7fb7c9ec7ae5984b",
      "76a79669dcdaa74a406b9237b948a2b72c81cb36ae7da177bd67a35b9c70704a"),
     ("assign", None, "=", "116:13-116:40",
      "d8eaa96e42575de232b1564a0195ef4fcfd3f83d4165083a76637ab5d79439fe")),
    ("index-read-true", 110, (1, "s1", "s0", "s0", "s0", "e0", 1, 0),
     "116:23-116:32", "0431c44695f0c1ac8ed9e63c8e45c0c4c15c6070ae87950225a37e0afbe60890",
     None, "float", ("vec3", "int"),
     ("db946d2520f9022f03f60bfc5e424ff7e45aba340b373dc293ac9240d0a1264c",
      "9e31ce8c2b1a156a6eb083c1e751a9f28cd28b677a168787f6858b7c59529eeb"),
     ("binary", None, "*", "116:23-116:40",
      "14fa0ce0c6842d755ff71577be450775ecd27d28eb3b778a85381adaa7fc5716")),
    ("index-write-false", 110, (1, "s1", "s0", "s1", "s0", "e0", 0),
     "118:13-118:20", "29775fb50440f76367af852a81b2dd079f3cbb3676f25c846b4f5e8f27c40f18",
     None, "float", ("vec3", "int"),
     ("2a8976c97ebefb1f6a16f0c33b5c27ed3afacf97319405f1f21c01f79f0682fa",
      "2dc4c0aa435c75bc5ba8755fb58af7c2f9599b7d3fe3877e0c15462c0afd3492"),
     ("assign", None, "=", "118:13-118:64",
      "0f8109a70f9cbd326a853e34468014be9b7b9c6b33faa30bc225e4e24b58a3ea")),
    ("index-read-false", 110, (1, "s1", "s0", "s1", "s0", "e0", 1, 0, 1, 0),
     "118:35-118:44", "2aba42dcad555d42dadaf6349df1b2baf4b1279339bea192700135497c93b6a6",
     None, "float", ("vec3", "int"),
     ("cdb5823c65ffdf27421a0d0474556362fb08e73432934b7a616fb83a31fb7409",
      "5fbece48748ac60bfba699419de19ade6eed4e7350b103f448b6ba6e9f880b57"),
     ("builtin", "pow", None, "118:31-118:56",
      "93c7452a976ea8d814e4f3e6e519016c06f926661a5731fdf0c30d74ecacd531")),
    ("bit-ingress", 131, (13, "e0", 0),
     "410:21-410:46", "72c34a6d99f4532a23d0567cd9376fb1450e9d42bf641d703a90aef658a382d9",
     "floatBitsToUint", "uint", ("float",),
     ("4cc8015ad7890d273ac083c59b7f7ff531ae2bb7a58391005fbcb36da6bc1e64",),
     ("declaration", None, None, "410:10-410:46",
      "70b1fc78f496445812f75f33d043d06c8b6093fc940adbbce3a5db9e1b414701")),
)

_MOD_CENSUS = (
    (100, "665:17-665:36", "dfa3a457f70bf342e4829addd18748adbc4d4ff8d5529ac0b98e1bcd5eac9cdb", "float", ("float", "float")),
    (101, "618:17-618:45", "90aed381a5fa4f1c4e18a58c45fd44121afc7e6211b1173d71467b816e4f1ce4", "vec3", ("vec3", "vec3")),
    (107, "64:30-64:47", "0224b6cf7ae5d2463adb927603afcaef9bdcc70f349f01aca7d080e0c0ccd997", "float", ("float", "float")),
    (113, "732:23-732:47", "a14601769aaccd03028e1c55c9a455baac45013ea10f539c76622c64d091fb9a", "float", ("float", "float")),
    (113, "734:23-734:47", "6590c6e2dd4e3aae6d440a9cf78b68fe03c2238275625a7338f2dfd813b6dc39", "float", ("float", "float")),
    (132, "98:17-98:42", "5511dad2ca77399d2de05aaec6ea94ab5a4859385ebfe96ec3617b8fa58030de", "float", ("float", "float")),
)

_FUNCTION_ROLE_HASHES = {
    100: "53fc99f57894d4dec0ea25a3ef19d8b98e41224e668a7b59bca4c20a06977f7f",
    101: "73f5b914bff1efb2f16dc2523e22da58948f3bd1867b7e28779cbe0cf2fb6d1a",
    110: "3ae72599b7f106d34a32bbe8c768b6297a9eefdf31b20dabb3651d46b728718b",
    113: "2867d7fa050d5d694b3f7629f0fd6ab082715fb83d1ca63f08c41ace109c89da",
    131: "e411dded7d18fcd48a1b3995821e086dd92fc9665bde9d519b9e72616ec51fa6",
}

_MAIN_CALLS = (
    ("blend", 100, "722:20-722:56", "d249578126c1eb28e8df79c30e2471d1300005a9751fac5b056220f5afb9d865", ("float", "float", "int", "float")),
    ("blend", 101, "726:21-726:75", "c97127bf99ddc95309c135ce924ff83a06c532315b1ade7a258d5183ca97e0d9", ("vec3", "vec3", "int", "float")),
)
_MAIN_BLEND_ROUTES = (
    (
        100, (14, "e0", 0),
        ("declaration", None, None, "722:11-722:56",
         "a8974a049aeed8e5739603438dfdfc70ba90522d5b958caed9abe0e76ccb356d"),
        (("decl", "722:5-722:57",
          "c53822f8a32cf4f3c9e0e117cfe8534fa7518a502d8d907a903cbaffccde47cc"),),
        ("id", None, "722:49-722:55",
         "784526e75a6f21bf15c98b04ff4ba7c2556e331eb6eff64d1135763f9b855164",
         "blendy", None),
    ),
    (
        101, (16, "s0", "s0", "e0", 1),
        ("assign", None, "=", "726:9-726:75",
         "62155c47863210204f72413869d65ee26bcd97fba43d9118be1d5652e541ae2a"),
        (
            ("if", "725:5-747:6",
             "1be67f167cd9ab15cac6dc77647a96e4f9c6f4f1562d8d4ca15000599966f932"),
            ("block", "725:27-739:6",
             "8ed829df1cd8bf66f3656d3a5718d8556489856755f2c3b02758eb9359dfbac2"),
            ("expr", "726:9-726:76",
             "499eae947f20d54783d19363ff8609a6b2bcf4459408552b4864ced3b0bb4fc2"),
        ),
        ("binary", "*", "726:62-726:74",
         "18df361c94410bbee6451e0fd70dc35618e66f0bbd1ced1d39e9cec294ff6767",
         "blendy", 0.5),
    ),
)
_PALETTE_MODE_FOUR_BRANCH = (
    "725:5-747:6",
    "1be67f167cd9ab15cac6dc77647a96e4f9c6f4f1562d8d4ca15000599966f932",
    "725:9-725:25",
    "f91eec443b54bd48befaf458f88d3405ebbff1b419a9be47cdfce999668d3f83",
    11, "paletteMode", 4,
    "725:27-739:6",
    "8ed829df1cd8bf66f3656d3a5718d8556489856755f2c3b02758eb9359dfbac2",
)
_MAIN_TEXTURES = (
    ("texture", "691:19-691:86", "4ca661f5275093e6982d34695c9a7442d860138e443fcc8fbc0751d1111a53cc", 2, "inputTex"),
    ("textureSize", "691:60-691:84", "2d5c1e16cda5af5c60ce172108794a558c61786e8b9ce4b8f5eabe8cf1cfd46b", 2, "inputTex"),
    ("texture", "692:19-692:76", "c5e032224af940fed1c1ef990c7a6abffca11e06a68e143a8f32cbc7bcae5bc9", 3, "tex"),
    ("textureSize", "692:55-692:74", "840516f559bdd2f2819bdeabfd97806f772b6c1d0940ebfe941d49b79b32919b", 3, "tex"),
)
_ALPHA_ASSIGNMENT = (
    "749:5-749:38", "e17674d83d21392e8de21b2b913d5beb0d7ee936fd343b847a2c2782545a74c1",
    "749:15-749:38", "fbe53768b9bd95ac4cf4fc2bc7c4c8f8e89cf08d355566f60a05a112f21c2040",
)

_PROFILE_SHA256 = "ed46eca83c5fb098f39a9ff02b8429ac9ce79f89d3d47e6b207798f287068b7f"


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
