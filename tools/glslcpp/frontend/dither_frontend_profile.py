"""Prepared, source-bound frontend admission for ``filter/dither``.

The dither shader is deliberately admission-only for now. Its three
counted-for loops still need a typed lowering contract. This profile freezes
the exact source, interface, function census, aggregate declarations, and
integer/array nodes that the future landing must consume; it does not relax
the shared validator or emitter.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass

from .typed_ir import TypedExpression, TypedProgram

KEY = "filter/dither:dither"
PROFILE = "dither-frontend-admission-v1"
KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = (KEY,)
PREPARED_PROFILES = {KEY: PROFILE}
DITHER_FRONTEND_KEYS = frozenset(PREPARED_PROFILES)
ALLOWED_ROW_FIELDS = {KEY: frozenset({"defines", "program_key", "dither_frontend_profile"})}
REQUIRED_COMPANION_PROFILES = {KEY: ()}

RAW_BYTES = 19391
RAW_SHA256 = "a966f1746213c8206c5cb57a88cafd8033eb8f8cb08b207209eb31479a11abdb"
NORMALIZED_BYTES = 15250
NORMALIZED_SHA256 = "eb8300add593991110a6c1d38989831a647a91cb3ece27d5487d52fafc8e6395"
FUNCTIONS_SHA256 = "e1fb1370d80e8f99de35a6ee087151e157883137ac0e00b6f8d6be01185dea96"
WHOLE_SHA256 = "0da56ec1dd88dc6d883bc7084b84e58680d06490f3dc33a333965529d00614b9"
INTERFACE_SHA256 = "97bf8c57cdc4647510782dd426a282ac3e8f0258fa8b7ae9e8e2a169ba8dc940"

SOURCE_UNIFORMS = (
    ("inputTex", "sampler2D"), ("tileOffset", "vec2"), ("fullResolution", "vec2"),
    ("ditherType", "int"), ("threshold", "float"), ("matrixScale", "float"),
    ("renderScale", "float"), ("palette", "int"), ("levels", "int"),
    ("time", "float"), ("mixAmount", "float"),
)
RUNTIME_UNIFORM_ABI = (
    ("tileOffset", "Vec2"), ("fullResolution", "Vec2"), ("ditherType", "int32"),
    ("threshold", "float"), ("matrixScale", "float"), ("renderScale", "float"),
    ("palette", "int32"), ("levels", "int32"), ("time", "float"), ("mixAmount", "float"),
)
SAMPLER_RUNTIME_ABI = ("inputTex", "sampler2D", "const Surface&")
ARRAY_DECLARATIONS = (
    ("DOT_MATRIX", "vec3[4]"), ("AMBER", "vec3[4]"), ("PICO8", "vec3[16]"),
    ("C64", "vec3[16]"), ("CGA", "vec3[4]"), ("ZX_SPECTRUM", "vec3[15]"),
    ("APPLE_II", "vec3[16]"), ("EGA", "vec3[16]"), ("FS_ERR_W", "int"),
)
LOOP_PROOF = (3, 3, 1, 15, 30, True)
EXPECTED_EXPR_KINDS = {"literal": 656, "id": 417, "binary": 324, "construct": 138,
                       "declaration": 61, "swizzle": 51, "call": 34, "assign": 32,
                       "builtin": 27, "index": 24, "unary": 7, "post": 6, "conditional": 3}
EXPECTED_OPERATORS = {"/": 113, "==": 87, "+": 45, "*": 35, "-": 24, "=": 24,
                      "<": 9, "+=": 7, "++": 6, "&": 6, ">=": 4, "%": 2,
                      "&&": 2, "<=": 1, "!": 1, ">": 1, "^=": 1, ">>": 1}


@dataclass(frozen=True, slots=True)
class FrontendProof:
    program_key: str
    sampler: tuple[str, str, str]
    aggregate_declarations: tuple[tuple[str, str], ...]
    loop_records: tuple["LoopRecord", ...]
    array_records: tuple["ArrayRecord", ...]
    array_parameters: tuple["ArrayParameterRecord", ...]
    index_records: tuple["IndexRecord", ...]
    bitwise_records: tuple["BitwiseRecord", ...]
    consumed_objects: tuple[object, ...]
    conversion_records: tuple["ConversionRecord", ...] = ()
    pcg_order_records: tuple["PCGOrderRecord", ...] = ()
    f32_materialization_records: tuple["F32MaterializationRecord", ...] = ()
    parameter_copy_records: tuple["ParameterCopyRecord", ...] = ()
    target_aliases: tuple["TargetAliasRecord", ...] = ()
    source_references: tuple["SourceReferenceRecord", ...] = ()
    carrier_edges: tuple["CarrierEdgeRecord", ...] = ()
    unique_consumed_objects: tuple[object, ...] = ()
    authority_eager_records: tuple["AuthorityRecord", ...] = ()
    authority_pooled_records: tuple["AuthorityRecord", ...] = ()
    f32_store_view: tuple[str, ...] = ()
    live_program: object | None = None

    @property
    def bitwise_nodes(self) -> tuple[TypedExpression, ...]:
        return tuple(item.node for item in self.bitwise_records)

    @property
    def indexed_nodes(self) -> tuple[TypedExpression, ...]:
        return tuple(item.node for item in self.index_records)

    @property
    def authority_eager_count(self) -> int:
        return sum(item.cardinality for item in self.authority_eager_records)

    @property
    def authority_pooled_count(self) -> int:
        return sum(item.cardinality for item in self.authority_pooled_records)

    @property
    def authority_err_row_lanes(self) -> int:
        return sum(item.cardinality for item in self.authority_pooled_records
                   if item.record_id == "MAT-ERRROW-INIT")

    @property
    def authority_eager(self) -> tuple["AuthorityRecord", ...]:
        return self.authority_eager_records

    @property
    def authority_pooled(self) -> tuple["AuthorityRecord", ...]:
        return self.authority_pooled_records

    @property
    def emitted_dither_f32_store_view(self) -> tuple[str, ...]:
        return self.f32_store_view


@dataclass(frozen=True, slots=True)
class LoopRecord:
    record_id: str
    function_name: str
    span: str
    node_sha256: str
    induction_symbol_id: int
    induction_name: str
    induction_type: str
    induction_span: str
    induction_sha256: str
    start_text: str
    bound_text: str
    comparison: str
    update: str
    node: object
    initialization: TypedExpression
    condition: TypedExpression
    increment: TypedExpression
    body: object
    proof: object


@dataclass(frozen=True, slots=True)
class ArrayRecord:
    record_id: str
    symbol_id: int
    symbol_name: str
    type_name: str
    extent: int
    span: str
    node_sha256: str
    node: object
    initializer: TypedExpression | None
    statement: object | None


@dataclass(frozen=True, slots=True)
class ArrayParameterRecord:
    record_id: str
    function_id: int
    function_name: str
    symbol_id: int
    symbol_name: str
    type_name: str
    span: str
    node_sha256: str
    node: object


@dataclass(frozen=True, slots=True)
class IndexRecord:
    record_id: str
    root_symbol_id: int
    root_name: str
    root_type: str
    span: str
    result_type: str
    node_sha256: str
    index_type: str
    index_span: str
    index_sha256: str
    node: TypedExpression


@dataclass(frozen=True, slots=True)
class BitwiseRecord:
    record_id: str
    operator: str
    span: str
    type_name: str
    node_sha256: str
    node: TypedExpression


@dataclass(frozen=True, slots=True)
class ConversionRecord:
    record_id: str
    function_name: str
    span: str
    raw_anchor: str
    node_kind: str
    type_name: str
    authority_anchor: str
    operation: str
    node_sha256: str
    node: TypedExpression
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PCGOrderRecord:
    record_id: str
    function_name: str
    span: str
    raw_anchor: str
    node_kind: str
    type_name: str
    operator: str
    authority_anchor: str
    node_sha256: str
    node: TypedExpression


@dataclass(frozen=True, slots=True)
class F32MaterializationRecord:
    record_id: str
    function_name: str
    span: str
    raw_anchor: str
    node_kind: str
    type_name: str
    authority_anchor: str
    kind: str
    role: str
    node_sha256: str
    node: TypedExpression | None
    ref_to: str | None = None

    @property
    def binding_kind(self) -> str:
        """Compatibility alias for callers that use the longer field name."""
        return self.kind


@dataclass(frozen=True, slots=True)
class ParameterCopyRecord:
    record_id: str
    function_name: str
    parameter_name: str
    symbol_id: int
    span: str
    raw_anchor: str
    type_name: str
    authority_anchor: str
    node_sha256: str
    node: object


@dataclass(frozen=True, slots=True)
class TargetAliasRecord:
    target_id: str
    span: str
    raw_anchor: str
    node_kind: str
    type_name: str
    symbol_id: int | None
    node_sha256: str
    node: object


@dataclass(frozen=True, slots=True)
class SourceReferenceRecord:
    referrer: str
    ref_to: str
    reason: str


@dataclass(frozen=True, slots=True)
class CarrierEdgeRecord:
    referrer: str
    carrier: str
    operation: str


@dataclass(frozen=True, slots=True)
class AuthorityRecord:
    record_id: str
    authority_anchor: str
    shape: str
    cardinality: int
    role: str


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = value.span
    return f"{span.start_line}:{span.start_column}-{span.end_line}:{span.end_column}"


# These are intentionally source-facing ledgers, rather than counts derived
# from the current AST.  Authentication below resolves every row to a live
# immutable semantic object and checks its digest, symbol, type, and span.
LOOP_LEDGER = (
    ("L-PAL-4", "findClosest4", "372:5-378:6", "b24f48f3214a1b58dab81aff5118b42009d1c0e8dc1b421d611fa5fd676f5ede", 150, "i", "int", "372:14-372:19", "759623cdf1a036778ed5326579d707263edadc827e5b64d0290fcdb472d1bf28", "1", "4", "<", "++"),
    ("L-PAL-15", "findClosest15", "387:5-393:6", "fb3f2b6f9258236f3d7544ff1181818f532d952bfd17ffc7d687e3a7b81952c6", 142, "i", "int", "387:14-387:19", "fe77003669ce8dba7f0bb20106c00fe722543f54d4febae9a07547f66bf79b46", "1", "15", "<", "++"),
    ("L-PAL-16", "findClosest16", "402:5-408:6", "d2f0d087f0dc7704bfcb30c7fb9f51e331e34cab8a3d0dc93c713154d2ca2fe6", 146, "i", "int", "402:14-402:19", "ca979da785ee68d20efab9d7d36a47aa2dcbe2b59c0aa9ed239923eb158a29c4", "1", "16", "<", "++"),
    ("L-ERR-SEED", "errorDiffusion", "521:5-523:6", "0c24c7587ac51411383d97601e2eca3a5a0b93885c3f7e1697d906f2fd7bbb5d", 127, "i", "int", "521:14-521:19", "ae93ef5aed26b9d885d4ab63061f022564bf07eb95df3f8217cb9d8a88413f48", "0", "FS_ERR_W", "<", "++"),
    ("L-ERR-ROWS", "errorDiffusion", "526:5-553:6", "d3313a10444e7227e68b5c7913eed133d4a52bfc155b5051c5609b3c42dea599", 129, "r", "int", "526:14-526:31", "87ebf94dd6ad70bbf5773ce0e680edcfccbc921445f39f010cae1f2261d56df7", "-FS_APRON_MAX", "ly", "<=", "++"),
    ("L-ERR-COLS", "errorDiffusion", "533:9-543:10", "9d2c4e41e7741e673236a56a533bc0376e8277e21cb4bd5f9b8be8c609943fef", 133, "c", "int", "533:18-533:35", "47274611ae799c0be5c47d621bb8263e3e67a252b4a8b09923ff16e2a2f9221b", "-FS_APRON_MAX", "FS_BLOCK+FS_RPAD", "<", "++"),
)

ARRAY_LEDGER = (
    ("A-DOT_MATRIX", 52, "DOT_MATRIX", "vec3[4]", 4, "239:1-244:3", "c1e18435c57c130b84f8ad56e3c7be8751b3662bd21e21a7d1d3a1c88476a474", None),
    ("A-AMBER", 53, "AMBER", "vec3[4]", 4, "247:1-252:3", "071cc05cd72f204e5b7f5ed1e77d9014546effa28cee4185175aaa2fdd34d515", None),
    ("A-PICO8", 54, "PICO8", "vec3[16]", 16, "255:1-272:3", "bfcae89ca0082282356d2f2ecf08c27f2c3c26f0ebff8333bef0c4ea7ce650a9", None),
    ("A-C64", 55, "C64", "vec3[16]", 16, "275:1-292:3", "b37f17e60953acc10b0c938889e693ba235a4c79bcb4e10e66695a74ca477b40", None),
    ("A-CGA", 56, "CGA", "vec3[4]", 4, "295:1-300:3", "714ceed16f508baf801d70bb8619731d242e5ab0ca3f23048ad98396ebe0739f", None),
    ("A-ZX_SPECTRUM", 57, "ZX_SPECTRUM", "vec3[15]", 15, "303:1-319:3", "ada905793c6d7cb44dd4ae0150cfa541bfefd6fcb2011d5eb9bdb97aff6be9cf", None),
    ("A-APPLE_II", 58, "APPLE_II", "vec3[16]", 16, "322:1-339:3", "23c461f80c4b82b9068361f9f4262fa1b1916983d9be4fb79141fa46c939738d", None),
    ("A-EGA", 59, "EGA", "vec3[16]", 16, "342:1-359:3", "15340b7d7e2b83cd48f4b4f5213cc90c5c612f6b8f82db46582f35e77df42f13", None),
    ("A-FS_ERR_W", 78, "FS_ERR_W", "int", 18, "462:1-462:60", "31be025d7033431610fcd026d523c3e8111f2dc1463c335b957e8fca8f91a7c4", None),
    ("A-ERR_ROW", 126, "errRow", "vec3[18]", 18, "520:10-520:26", "a0daacde171cc10818a2857d308bf0cd86b67c9f801fd91951d9587c348f8677", "eaf962ddfa105bcb1a933e5c109de8c283748c8fe4c152a3965534a748f98ecb"),
)

ARRAY_PARAMETER_LEDGER = (
    # The Task33 prose digest for AP-PAL-4 does not hash any live object in
    # this pinned semantic tree; this is the digest of its actual Symbol.
    ("AP-PAL-4", 95, "findClosest4", 63, "pal", "vec3[4]", "368:31-368:42", "d84c8308725523775fb1df09da78d73ead82fa16b6250129505ae3a645852200"),
    ("AP-PAL-15", 93, "findClosest15", 65, "pal", "vec3[15]", "383:32-383:44", "543bbd8740898b593c22285843f47a30ec13cba31304fbec2ec3d0da39608c21"),
    ("AP-PAL-16", 94, "findClosest16", 67, "pal", "vec3[16]", "398:32-398:44", "2a5f61c198c6db2c9cd1ea84f221feeb3ca082b80fd6224788ee155032a2430c"),
)

INDEX_LEDGER = (
    ("E01", 126, "errRow", "vec3[18]", "522:9-522:18", "vec3", "4d0e0762183fcc46c60777356beed7a1fae22c42119724f9b7ca1706426a5073"),
    ("E02", 126, "errRow", "vec3[18]", "536:38-536:66", "vec3", "8ba8573c0f97a33d6fc0e484c68cf1d4bfe02148d23f6e0268845a0bb495cfe5"),
    ("E03", 126, "errRow", "vec3[18]", "539:17-539:41", "vec3", "03417ad9f483944b16eaaa3016246a068d573d9d8ae94efc72cc6c8b0bade5b1"),
    ("E04", 126, "errRow", "vec3[18]", "540:17-540:45", "vec3", "a259fcfec3057afd952f6f344987df1a59648d502600c35e37773cec7daf09c8"),
    ("E05", 126, "errRow", "vec3[18]", "547:29-547:53", "vec3", "7436a7ff504f7b1042e72bc3f728f5b29293ba0b73933e5dc159969fe3b39646"),
    ("E06", 126, "errRow", "vec3[18]", "548:37-548:61", "vec3", "b0369c3e869cfbfa2911a658dc4ca75643040ee72e2c52facb1b4d34ba5c876e"),
    ("E07", 126, "errRow", "vec3[18]", "549:37-549:61", "vec3", "e407558f76dfc2b1eaee3afdddc6bdd468de8a65cf50ae64e8b23fc2e700b094"),
    ("E08", 126, "errRow", "vec3[18]", "550:37-550:61", "vec3", "3b02e64fa248e121ef49d6a28e70de9b5744655031713a71ba8a6a5907b61aec"),
    ("P15-1", 65, "pal", "vec3[15]", "384:20-384:26", "vec3", "879814f610ca7f20ee0b1ff77a5c84fc796be7c4535db51b607597a043e5b110"),
    ("P15-2", 65, "pal", "vec3[15]", "385:42-385:48", "vec3", "9ab1fbd14be6ab3eb7e4f750062c525094fe6caf42da22bdfc83fca265b7400b"),
    ("P15-3", 65, "pal", "vec3[15]", "388:43-388:49", "vec3", "d81e52d7bfa357c4ab16c1d038793865e4957e3d5ba6e4afd49fe395d0e42fd9"),
    ("P15-4", 65, "pal", "vec3[15]", "391:23-391:29", "vec3", "2d0b2fcecc4078b3bdf167c3e0a35c28f29aea012b6ace05acb3c714ef39aa3b"),
    ("P16-1", 67, "pal", "vec3[16]", "399:20-399:26", "vec3", "fdbbd02c99ebedb83d0deb4cadcf29b857a86e306741d5fec6d2645058dc6d01"),
    ("P16-2", 67, "pal", "vec3[16]", "400:42-400:48", "vec3", "3739a3e8bfd4373ad897f5a968f2d3802aee16d5163a86bec73aee73ff01cb4f"),
    ("P16-3", 67, "pal", "vec3[16]", "403:43-403:49", "vec3", "00ac40001b5d661f249b8c072467d6ada185137c5fa5e246dcf4773ee2d3fa1d"),
    ("P16-4", 67, "pal", "vec3[16]", "406:23-406:29", "vec3", "cba30e570f06cd1a59fddbe22925b1d44df66813d9921dbd438e6ab5abf10e38"),
    ("P4-1", 63, "pal", "vec3[4]", "369:20-369:26", "vec3", "58d777666abd75055bd0f4a7e0e980375df829834318e212144e026835adcb83"),
    ("P4-2", 63, "pal", "vec3[4]", "370:42-370:48", "vec3", "980f3363bf4a965a90dd4ee991a099e77316a2e83b0575522d94afa0a5a1a76f"),
    ("P4-3", 63, "pal", "vec3[4]", "373:43-373:49", "vec3", "2c5d1ca1c67a16f362a0756b4c41487e207fc644dd23588d157522b7505432c8"),
    ("P4-4", 63, "pal", "vec3[4]", "376:23-376:29", "vec3", "a0fce1b9936d9b5e3c9f9df1699590518e0cbbd4fdc918a3bc919c1c8ee37495"),
    ("B2-outer", 31, "bayer2x2", "mat4", "204:16-204:38", "float", "ae626cfbab7ced25062201de745c332a09a038bf73eb172464b4dd75caead43a"),
    ("B2-inner", 31, "bayer2x2", "mat4", "204:16-204:31", "vec4", "cc9b23eee7dafbca473cf121d56896212e81cf5a027eba9f9f47a40eaf58f33d"),
    ("B4-outer", 32, "bayer4x4", "mat4", "206:16-206:38", "float", "c29257c21b28aa53f4d22e1d8afd141e405db994158e89ee00edfcc23d0020b2"),
    ("B4-inner", 32, "bayer4x4", "mat4", "206:16-206:31", "vec4", "cef37dfa821857e74288d36c1322d1bcab95191c491873fc3d610103f26b8252"),
)

BITWISE_LEDGER = (
    ("U01", "%", "510:37-510:89", "uint", "f2cce8900d168e73cff02f795e97f672a70a6e871a0056872bfa5c9b726290f8"),
    ("U02", "%", "511:37-511:89", "uint", "14bfd0edeffa7c0a288326387558b2797de9f76f2587f5da4cfddfde5816cba4"),
    ("I01", "&", "57:9-57:14", "int", "2368af02caf5410d6a24a71cc663e0081b0a6148a50532fb021703394713a18b"),
    ("I02", "&", "58:9-58:14", "int", "72173aa02d3a3f52d8ba9587c5a3fe857f8d996c2a1f2a03add9cd193e8196c6"),
    ("B01", "&", "204:25-204:30", "int", "7398bf0ecd3d2a8e9f0caeb4f861e3ab0c282d42278c42eb26909fed98570c21"),
    ("B02", "&", "204:32-204:37", "int", "856e8e838f1ba0e934e9bd7f9ac6d49bdea91ebcf59d1af76b651658208cfc9a"),
    ("B03", "&", "206:25-206:30", "int", "deef10ea7534c3ce8a15570627c231480bbfbfb0d2b7920da070b1960735cfb7"),
    ("B04", "&", "206:32-206:37", "int", "ad29621302a76d26e5a691cfb02e6da4d1dcaf750c887a385ec664e1d94299cf"),
    ("U03", ">>", "155:10-155:18", "uvec3", "f99da63efeb2774448f97e1993a422c937ba1dcef9d6970492c29905830a373e"),
)

# The prepared landing ledgers below intentionally describe source-bound
# identity and authority placement separately.  They are not emitter policy:
# each node is resolved from the live TypedProgram before it can be consumed.
CONVERSION_LEDGER = (
    ("C01", "getDitherThreshold", "200:13-200:31", "R:206", "construct", "int", "10891", "ToInt32(F32(scaledCoord[0]))", ()),
    ("C02", "getDitherThreshold", "201:13-201:31", "R:207", "construct", "int", "10892", "ToInt32(F32(scaledCoord[1]))", ()),
    ("C03", "hash", "165:9-165:56", "R:171", "construct", "uint", "10865-10866", "hash-x carrier/branch/U32", ("AP01",)),
    ("C04", "hash", "166:9-166:56", "R:172", "construct", "uint", "10865-10866", "hash-y carrier/branch/U32", ("AP01",)),
    ("C05", "fsSeedNoise", "490:25-490:48", "R:496", "construct", "uint", "11051", "F32(blockOrigin.x)+1|0->U32", ("MAT-BLOCK-ORIGIN",)),
    ("C06", "fsSeedNoise", "490:50-490:73", "R:496", "construct", "uint", "11051", "F32(blockOrigin.y)+1|0->U32", ("MAT-BLOCK-ORIGIN",)),
    ("C07", "fsSeedNoise", "490:75-490:89", "R:496", "construct", "uint", "11051", "Number(lane)+1|0->U32", ("PARAM-LANE-NUMBER",)),
    ("C08", "errorDiffusion", "509:34-509:57", "R:515", "construct", "uint", "11063,11066", "F32(blockOrigin.x)+1|0->U32", ("MAT-BLOCK-ORIGIN",)),
    ("C09", "errorDiffusion", "509:59-509:82", "R:515", "construct", "uint", "11063,11066", "F32(blockOrigin.y)+1|0->U32", ("MAT-BLOCK-ORIGIN",)),
    ("C10", "errorDiffusion", "510:33-510:90", "R:516", "construct", "int", "11067-11068", "ToInt32(U32 remainder)", ()),
    ("C11", "errorDiffusion", "511:33-511:90", "R:517", "construct", "int", "11067-11068", "ToInt32(U32 remainder)", ()),
    ("C12", "errorDiffusion", "510:52-510:89", "R:516", "construct", "uint", "11067", "ToUint32(denominator)", ()),
    ("C13", "errorDiffusion", "511:52-511:89", "R:517", "construct", "uint", "11068", "ToUint32(denominator)", ()),
    ("C14", "fsFetchCell", "497:20-497:41", "R:503", "construct", "ivec2", "11056", "ToInt32(F32(floor(pGlobal)))", ()),
    ("C15", "fsFetchCell", "497:44-497:61", "R:503", "construct", "ivec2", "11056", "ToInt32(F32(tileOffset))", ()),
    ("C16", "errorDiffusion", "503:18-503:54", "R:509", "construct", "ivec2", "11062", "ToInt32(F32(floor(globalCoord/cellSize)))", ()),
    ("C17", "errorDiffusion", "504:11-504:53", "R:510", "declaration", "ivec2", "11063", "F32(cell)/F32(4)|0*4|0", ("C17-PARENT", "C17-DIV", "C17-MUL")),
    ("C18", "errorDiffusion", "504:11-504:53", "R:510", "declaration", "ivec2", "11063", "F32(cell)/F32(4)|0*4|0", ("C17-PARENT", "C17-DIV", "C17-MUL")),
    ("C19", "errorDiffusion", "535:54-535:65", "R:541", "construct", "ivec2", "11085", "ToInt32(c),ToInt32(r)", ()),
    ("C20", "fsFetchCell", "498:28-498:36", "R:504", "construct", "ivec2", "11057", "integer zero lower clamp", ()),
    ("C21", "fsSeedNoise", "490:19-490:90", "R:496", "construct", "uvec3", "11051", "ordered x,y,lane U32", ("C05", "C06", "C07")),
    ("C22", "errorDiffusion", "509:28-509:96", "R:515", "construct", "uvec3", "11066", "ordered x,y,constant U32", ("C08", "C09")),
    ("C23", "hash", "164:19-168:6", "R:170-174", "construct", "uvec3", "10866", "ordered x,y,zero U32", ("C03", "C04")),
    ("C24", "errorDiffusion", "557:37-557:59", "R:563", "construct", "ivec2", "11108", "F32(gl_FragCoord.xy)->ToInt32", ()),
    ("C25", "hash", "169:12-169:22", "R:175", "construct", "float", "10867", "hash output Number/f32 boundary", ()),
    ("C26", "hash", "169:25-169:43", "R:175", "construct", "float", "10867", "exact 2^32 denominator provenance", ()),
    ("C27", "fsSeedNoise", "491:22-491:40", "R:497", "construct", "float", "11052", "exact 2^32 denominator", ()),
    ("C28", "fsQuantize", "468:26-468:39", "R:474", "construct", "float", "11039", "Number levels coercion", ()),
    ("C29", "fsScale", "481:22-481:35", "R:487", "construct", "float", "11046", "Number levels coercion", ()),
    ("C30", "main", "581:52-581:65", "R:587", "construct", "float", "11123", "Number levels coercion", ()),
)

PCG_ORDER_LEDGER = (
    ("P01", "pcg", "151:5-151:35", "R:157", "assign", "uvec3", "=", "10864"),
    ("P02", "pcg", "152:5-152:21", "R:158", "assign", "uint", "+=", "10865"),
    ("P03", "pcg", "153:5-153:21", "R:159", "assign", "uint", "+=", "10865"),
    ("P04", "pcg", "154:5-154:21", "R:160", "assign", "uint", "+=", "10865"),
    ("P05", "pcg", "155:5-155:18", "R:161", "assign", "uvec3", "^=", "10866"),
    ("P06", "pcg", "156:5-156:21", "R:162", "assign", "uint", "+=", "10866"),
    ("P07", "pcg", "157:5-157:21", "R:163", "assign", "uint", "+=", "10866"),
    ("P08", "pcg", "158:5-158:21", "R:164", "assign", "uint", "+=", "10866"),
)

F32_MATERIALIZATION_LEDGER = (
    ("F01", "dotPattern", "174:10-174:24", "R:180", "declaration", "vec2", "10871", "source_ast", "f32_store"),
    ("F02", "dotPattern", "175:10-175:28", "R:181", "declaration", "vec2", "10872", "source_ast", "regular_array_intermediate"),
    ("F03", "dotPattern", "176:11-176:37", "R:182", "declaration", "float", "10873", "source_ast", "regular_array_intermediate"),
    ("F04", "crosshatchPattern", "188:10-188:24", "R:194", "declaration", "vec2", "10883", "source_ast", "f32_store"),
    ("F05", "crosshatchPattern", "189:11-189:52", "R:195", "declaration", "float", "10884", "source_ast", "number_only_guard"),
    ("F06", "crosshatchPattern", "190:11-190:52", "R:196", "declaration", "float", "10885", "source_ast", "number_only_guard"),
    ("F07", "linePattern", "182:11-182:27", "R:188", "declaration", "float", "10878", "source_ast", "number_only_guard"),
    ("F08", "getDitherThreshold", "199:10-199:49", "R:205", "declaration", "vec2", "10890", "source_ast", "f32_store"),
    ("F09", "getDitherThreshold", "220:21-220:47", "R:226", "binary", "vec2", "10912", "source_ast", "f32_store"),
    ("F10", "quantizeWithDither", "229:10-229:52", "R:235", "declaration", "vec3", "10925", "source_ast", "f32_store"),
    ("F11", "quantizeWithDither", "230:12-230:53", "R:236", "binary", "vec3", "10926", "source_ast", "f32_store"),
    ("F12", "colorDistance", "363:10-363:22", "R:369", "declaration", "vec3", "10940", "source_ast", "f32_store"),
    ("F13", "ditherWithPalette", "439:10-439:64", "R:445", "declaration", "vec3", "11027", "source_ast", "f32_store"),
    ("F14", "ditherWithPalette", "440:5-440:41", "R:446", "assign", "vec3", "11028-11029", "source_adapter", "f32_return"),
    ("F15", "fsQuantize", "472:16-472:52", "R:478", "binary", "vec3", "11040", "source_ast", "f32_store"),
    ("F16", "fsSeedNoise", "491:12-491:46", "R:497", "binary", "vec3", "11052", "source_ast", "f32_store"),
    ("F17", "fsFetchCell", "496:10-496:49", "R:502", "declaration", "vec2", "11055", "source_ast", "f32_store"),
    ("F18", "fsFetchCell", "497:11-497:61", "R:503", "declaration", "ivec2", "11056-11057", "source_adapter", "adapter"),
    ("F19", "fsFetchCell", "498:5-498:50", "R:504", "assign", "ivec2", "11057", "source_adapter", "adapter"),
    ("F20", "errorDiffusion", "514:10-514:44", "R:520", "declaration", "vec3", "11070", "source_ast", "f32_store"),
    ("F21", "errorDiffusion", "520:10-520:26", "R:526", "declaration", "vec3[18]", "11071", "source_ast", "f32_store"),
    ("F22", "errorDiffusion", "522:9-522:60", "R:528", "assign", "vec3", "11073", "source_adapter", "diffusion_store"),
    ("F23", "errorDiffusion", "525:10-525:29", "R:531", "declaration", "vec3", "11075", "source_ast", "f32_store"),
    ("F24", "errorDiffusion", "531:14-531:90", "R:537", "declaration", "vec3", "11080", "source_ast", "regular_array_intermediate"),
    ("F25", "errorDiffusion", "532:14-532:30", "R:538", "declaration", "vec3", "11082", "source_ast", "f32_store"),
    ("F26", "errorDiffusion", "535:22-535:85", "R:541", "declaration", "vec3", "11085", "source_adapter", "f32_return"),
    ("F27", "errorDiffusion", "536:22-536:95", "R:542", "declaration", "vec3", "11086", "source_ast", "f32_store"),
    ("F28", "errorDiffusion", "537:22-537:45", "R:543", "declaration", "vec3", "11087", "source_ast", "regular_array_intermediate"),
    ("F29", "errorDiffusion", "538:17-538:46", "R:544", "assign", "vec3", "11088", "source_adapter", "diffusion_store"),
    ("F30", "errorDiffusion", "539:17-539:63", "R:545", "assign", "vec3", "11089", "source_adapter", "diffusion_store"),
    ("F31", "errorDiffusion", "540:17-540:73", "R:546", "assign", "vec3", "11090", "source_adapter", "diffusion_store"),
    ("F32", "errorDiffusion", "541:17-541:42", "R:547", "assign", "vec3", "11091", "source_adapter", "diffusion_store"),
    ("F33", "errorDiffusion", "547:18-547:53", "R:553", "declaration", "vec3", "11095", "source_adapter", "diffusion_store"),
    ("F34", "errorDiffusion", "548:26-548:61", "R:554", "assign", "vec3", "11097", "source_adapter", "diffusion_store"),
    ("F35", "errorDiffusion", "549:26-549:61", "R:555", "assign", "vec3", "11100", "source_adapter", "diffusion_store"),
    ("F36", "errorDiffusion", "550:26-550:61", "R:556", "assign", "vec3", "11103", "source_adapter", "diffusion_store"),
    ("F37", "errorDiffusion", "551:13-551:42", "R:557", "assign", "vec3", "11105", "source_adapter", "diffusion_store"),
    ("F38", "errorDiffusion", "557:10-557:67", "R:563", "declaration", "vec3", "11108", "source_ast", "f32_store"),
    ("F39", "errorDiffusion", "558:10-558:51", "R:564", "declaration", "vec3", "11109", "source_ast", "f32_store"),
    ("F40", "main", "563:11-563:45", "R:569", "declaration", "ivec2", "11113", "runtime_adapter", "f32_return"),
    ("F41", "main", "564:10-564:46", "R:570", "declaration", "vec2", "11114", "source_ast", "f32_store"),
    ("F42", "main", "566:10-566:39", "R:572", "declaration", "vec4", "11115", "runtime_adapter", "f32_return"),
    ("F43", "main", "569:10-569:52", "R:575", "declaration", "vec2", "11116", "source_ast", "f32_store"),
    ("F44", "main", "574:9-574:81", "R:580", "assign", "vec3", "11119", "source_adapter", "diffusion_store"),
    ("F45", "main", "581:13-581:90", "R:587", "assign", "vec3", "11123", "source_ast", "f32_store"),
    ("F46", "main", "584:13-584:83", "R:590", "assign", "vec3", "11125", "source_ast", "f32_store"),
    ("F47", "main", "589:5-589:47", "R:595", "assign", "vec3", "11128", "source_ast", "f32_store"),
    ("F48", "main", "591:5-591:38", "R:597", "assign", "vec4", "11129", "source_ast", "f32_return"),
    ("F49", "runtime.writeColor", "155-160", "src/csl/glsl-runtime.js:155-160", "runtime", "Float32Array[4]", "writeColor", "runtime_adapter", "f32_return"),
)

PARAMETER_COPY_LEDGER = (
    ("AP01", "hash", "p", 36, "163:12-163:18", "R:169", "vec2", "10865"),
    ("AP02", "dotPattern", "uv", 37, "173:18-173:25", "R:179", "vec2", "10870"),
    ("AP03", "linePattern", "uv", 39, "181:19-181:26", "R:187", "vec2", "10877"),
    ("AP04", "crosshatchPattern", "uv", 41, "187:25-187:32", "R:193", "vec2", "10882"),
    ("AP05", "getDitherThreshold", "pixelCoord", 43, "197:26-197:41", "R:203", "vec2", "10889"),
    ("AP06", "quantizeWithDither", "color", 46, "227:25-227:35", "R:233", "vec3", "10923"),
    ("AP07", "colorDistance", "a", 60, "362:21-362:27", "R:368", "vec3", "10938"),
    ("AP08", "colorDistance", "b", 61, "362:29-362:35", "R:368", "vec3", "10939"),
    ("AP09", "findClosest4", "color", 62, "368:19-368:29", "R:374", "vec3", "10944"),
    ("AP10", "findClosest4", "pal", 63, "368:31-368:42", "R:374", "vec3[4]", "10945"),
    ("AP11", "findClosest15", "color", 64, "383:20-383:30", "R:389", "vec3", "10958"),
    ("AP12", "findClosest15", "pal", 65, "383:32-383:44", "R:389", "vec3[15]", "10959"),
    ("AP13", "findClosest16", "color", 66, "398:20-398:30", "R:404", "vec3", "10972"),
    ("AP14", "findClosest16", "pal", 67, "398:32-398:44", "R:404", "vec3[16]", "10973"),
    ("AP15", "findClosestPaletteColor", "color", 68, "412:30-412:40", "R:418", "vec3", "10986"),
    ("AP16", "ditherWithPalette", "color", 70, "437:24-437:34", "R:443", "vec3", "11026"),
    ("AP17", "fsQuantize", "v", 79, "466:17-466:23", "R:472", "vec3", "11037"),
    ("AP18", "errorDiffusion", "globalCoord", 85, "502:21-502:37", "R:508", "vec2", "11061"),
)

F32_STORE_VIEW = ("F01", "F04", "F08", "F09", "F10", "F11", "F12", "F13", "F14", "F15", "F16", "F17", "F20", "F21", "F22", "F23", "F25", "F26", "F27", "F29", "F30", "F31", "F32", "F33", "F34", "F35", "F36", "F37", "F38", "F39", "F40", "F41", "F42", "F43", "F44", "F45", "F46", "F47", "F48", "F49")

EAGER_AUTHORITY_LEDGER = (
    ("MAT-FRAGCOLOR", "10648", "Float32Array[4]", 1, "f32_store"),
    ("MAT-BAYER2", "10667", "Float32Array[16]", 1, "f32_store"),
    ("MAT-BAYER4", "10668", "Float32Array[16]", 1, "f32_store"),
    ("MAT-PALETTE-DOT", "10929", "Float32Array[3]", 4, "f32_store"),
    ("MAT-PALETTE-AMBER", "10930", "Float32Array[3]", 4, "f32_store"),
    ("MAT-PALETTE-PICO8", "10931", "Float32Array[3]", 16, "f32_store"),
    ("MAT-PALETTE-C64", "10932", "Float32Array[3]", 16, "f32_store"),
    ("MAT-PALETTE-CGA", "10933", "Float32Array[3]", 4, "f32_store"),
    ("MAT-PALETTE-ZX", "10934", "Float32Array[3]", 15, "f32_store"),
    ("MAT-PALETTE-APPLE", "10935", "Float32Array[3]", 16, "f32_store"),
    ("MAT-PALETTE-EGA", "10936", "Float32Array[3]", 16, "f32_store"),
)
POOLED_SINGLE_IDS = ("MAT-P-DOT", "MAT-P-CROSS", "MAT-SCALED-COORD", "MAT-NOISE-HASH-ARG", "MAT-QUANT-DITHERED", "MAT-QUANT-FLOOR", "MAT-COLOR-DIFF", "MAT-LUMA-WEIGHTS", "MAT-MONO-RESULT", "MAT-PALETTE-DITHERED", "MAT-FSQUANT-FLOOR", "MAT-FS-SEED-NOISE", "MAT-FETCH-PGLOBAL", "MAT-FETCH-CLAMP-HIGH", "MAT-FETCH-RGB", "MAT-CELL-QUOTIENT-ARG", "MAT-BLOCK-ORIGIN", "MAT-FS-BIAS", "MAT-CARRIED", "MAT-DIAG", "MAT-DIFFUSION-V", "MAT-FRAG-COORD-VEC", "MAT-OWN-SRC-RGB", "MAT-OWN-V", "MAT-MAIN-UV", "MAT-MAIN-GLOBAL", "MAT-MAIN-RESULT", "MAT-MAIN-INPUT-QUANT", "MAT-MAIN-INPUT-PALETTE", "MAT-MAIN-MIX")
F32_EXCLUDED = ("F02", "F03", "F05", "F06", "F07", "F18", "F19", "F24", "F28")

SOURCE_REFERENCE_LEDGER = (
    ("C17", "C17-PARENT", "shared live declaration"),
    ("C17", "C17-DIV", "shared live division child"),
    ("C17", "C17-MUL", "shared live multiply child"),
    ("C18", "C17-PARENT", "shared live declaration"),
    ("C18", "C17-DIV", "shared live division child"),
    ("C18", "C17-MUL", "shared live multiply child"),
    ("C21", "C05", "ordered uvec3 x child"), ("C21", "C06", "ordered uvec3 y child"),
    ("C21", "C07", "ordered uvec3 lane child"), ("C22", "C08", "ordered jitter x child"),
    ("C22", "C09", "ordered jitter y child"), ("C23", "C03", "ordered hash x child"),
    ("C23", "C04", "ordered hash y child"), ("F18", "C14", "pLocal floor child"),
    ("F18", "C15", "pLocal tile child"), ("F19", "C20", "lower clamp child"),
    ("F21", "A-ERR_ROW", "existing errRow declaration"), ("F38", "C24", "own fetch child"),
    ("F49", "F48", "runtime writeColor consumes final source result"),
    ("AP10", "AP-PAL-4", "shared array parameter symbol"),
    ("AP12", "AP-PAL-15", "shared array parameter symbol"),
    ("AP14", "AP-PAL-16", "shared array parameter symbol"),
    ("F-PAL-1", "A-DOT_MATRIX", "ordered eager palette children"),
    ("F-PAL-2", "A-AMBER", "ordered eager palette children"),
    ("F-PAL-3", "A-PICO8", "ordered eager palette children"),
    ("F-PAL-4", "A-C64", "ordered eager palette children"),
    ("F-PAL-5", "A-CGA", "ordered eager palette children"),
    ("F-PAL-6", "A-ZX_SPECTRUM", "ordered eager palette children"),
    ("F-PAL-7", "A-APPLE_II", "ordered eager palette children"),
    ("F-PAL-8", "A-EGA", "ordered eager palette children"),
)
CARRIER_EDGE_LEDGER = (
    ("C03", "AP01", "f32_parameter_copy"), ("C04", "AP01", "f32_parameter_copy"),
    ("C05", "MAT-BLOCK-ORIGIN", "f32_lane_read"), ("C06", "MAT-BLOCK-ORIGIN", "f32_lane_read"),
    ("C07", "PARAM-LANE-NUMBER", "direct_number"), ("C08", "MAT-BLOCK-ORIGIN", "f32_lane_read"),
    ("C09", "MAT-BLOCK-ORIGIN", "f32_lane_read"),
)


def _source_nodes_by_span(program: TypedProgram) -> dict[str, tuple[object, ...]]:
    found: dict[str, list[object]] = {}
    def add(node: object) -> None:
        span = getattr(node, "span", None)
        if span is not None:
            found.setdefault(_span(node), []).append(node)
    def expression(node: TypedExpression) -> None:
        add(node)
        for child in node.children:
            expression(child)
    def statement(node: object) -> None:
        for item in node.expressions:
            expression(item)
        for child in node.children:
            statement(child)
    for declaration in program.declarations:
        add(declaration)
        if declaration.initializer is not None:
            expression(declaration.initializer)
    for function in program.functions:
        add(function.signature)
        for parameter in function.signature.parameters:
            add(parameter)
        for item in function.body:
            statement(item)
    return {key: tuple(value) for key, value in found.items()}


def _one_source_node(nodes: dict[str, tuple[object, ...]], span: str,
                     record_id: str) -> object:
    values = nodes.get(span, ())
    if len(values) != 1:
        raise _fail(f"source identity missing or ambiguous: {record_id}")
    return values[0]


def _node_function_name(program: TypedProgram, target: object) -> str | None:
    def expression(node: TypedExpression) -> bool:
        if node is target:
            return True
        return any(expression(child) for child in node.children)
    def statement(node: object) -> bool:
        return any(expression(item) for item in node.expressions) or any(
            statement(child) for child in node.children)
    for function in program.functions:
        if any(statement(item) for item in function.body):
            return function.name
    return None


def _conversion_records(program: TypedProgram, nodes: dict[str, tuple[object, ...]]) -> tuple[ConversionRecord, ...]:
    records = []
    for row in CONVERSION_LEDGER:
        record_id, function_name, span, raw_anchor, node_kind, type_name, authority, operation, refs = row
        node = _one_source_node(nodes, span, record_id)
        if (node.kind, node.type.display()) != (node_kind, type_name) \
                or _node_function_name(program, node) != function_name:
            raise _fail(f"conversion node kind/type mismatch: {record_id}")
        records.append(ConversionRecord(record_id, function_name, span, raw_anchor,
                                         node_kind, type_name, authority, operation,
                                         _sha(node), node, refs))
    return tuple(records)


def _pcg_order_records(program: TypedProgram, nodes: dict[str, tuple[object, ...]]) -> tuple[PCGOrderRecord, ...]:
    records = []
    for row in PCG_ORDER_LEDGER:
        record_id, function_name, span, raw_anchor, node_kind, type_name, operator, authority = row
        node = _one_source_node(nodes, span, record_id)
        if ((node.kind, node.type.display(), node.operator) != (node_kind, type_name, operator)
                or _node_function_name(program, node) != function_name):
            raise _fail(f"PCG assignment identity mismatch: {record_id}")
        records.append(PCGOrderRecord(record_id, function_name, span, raw_anchor,
                                      node_kind, type_name, operator, authority,
                                      _sha(node), node))
    return tuple(records)


def _f32_materialization_records(program: TypedProgram, nodes: dict[str, tuple[object, ...]]) -> tuple[F32MaterializationRecord, ...]:
    records = []
    for row in F32_MATERIALIZATION_LEDGER:
        record_id, function_name, span, raw_anchor, node_kind, type_name, authority, binding_kind, role = row
        if record_id == "F49":
            node = None
            digest = "9d21bac49e0cfdc0ddc2dfa25fb38a402b0f3e8c82e5a6a885b340986f7653fb"
            ref_to = "F48"
        else:
            node = _one_source_node(nodes, span, record_id)
            if ((node.kind, node.type.display()) != (node_kind, type_name)
                    or _node_function_name(program, node) != function_name):
                raise _fail(f"F32 node kind/type mismatch: {record_id}")
            digest = _sha(node)
            ref_to = None
        records.append(F32MaterializationRecord(record_id, function_name, span, raw_anchor,
                                                node_kind, type_name, authority, binding_kind,
                                                role, digest, node, ref_to))
    return tuple(records)


def _parameter_copy_records(program: TypedProgram) -> tuple[ParameterCopyRecord, ...]:
    records = []
    for row in PARAMETER_COPY_LEDGER:
        record_id, function_name, parameter_name, symbol_id, span, raw_anchor, type_name, authority = row
        function = next((item for item in program.functions if item.name == function_name), None)
        node = next((item for item in function.signature.parameters
                     if item.id == symbol_id and item.name == parameter_name), None) if function else None
        if node is None or node.type.display() != type_name or _span(node) != span:
            raise _fail(f"parameter copy identity mismatch: {record_id}")
        records.append(ParameterCopyRecord(record_id, function_name, parameter_name, symbol_id,
                                           span, raw_anchor, type_name, authority, _sha(node), node))
    return tuple(records)


def _authority_records() -> tuple[tuple[AuthorityRecord, ...], tuple[AuthorityRecord, ...]]:
    eager = tuple(AuthorityRecord(*row) for row in EAGER_AUTHORITY_LEDGER)
    pooled = [AuthorityRecord(record_id, "canonicalFactory48", "PooledFloat32Array", 1, "f32_store")
              for record_id in POOLED_SINGLE_IDS]
    pooled.extend(AuthorityRecord("MAT-ERRROW-INIT", "11071", "PooledFloat32Array[3]", 1, "f32_store")
                  for _ in range(18))
    return eager, tuple(pooled)


def _target_aliases(nodes: dict[str, tuple[object, ...]], array_records: tuple[ArrayRecord, ...]) -> tuple[TargetAliasRecord, ...]:
    parent = _one_source_node(nodes, "504:11-504:53", "C17-PARENT")
    division = _one_source_node(nodes, "504:26-504:41", "C17-DIV")
    multiply = _one_source_node(nodes, "504:26-504:53", "C17-MUL")
    err_row = next(item.node for item in array_records if item.record_id == "A-ERR_ROW")
    return (
        TargetAliasRecord("C17-PARENT", "504:11-504:53", "R:510", "declaration", "ivec2", 118, _sha(parent), parent),
        TargetAliasRecord("C17-DIV", "504:26-504:41", "R:510", "binary", "ivec2", 117, _sha(division), division),
        TargetAliasRecord("C17-MUL", "504:26-504:53", "R:510", "binary", "ivec2", 118, _sha(multiply), multiply),
        TargetAliasRecord("A-ERR_ROW", "520:10-520:26", "R:526", "declaration", "vec3[18]", 126, _sha(err_row), err_row),
    )


def _unique_consumed_objects(base: tuple[object, ...], conversions: tuple[ConversionRecord, ...],
                             pcg: tuple[PCGOrderRecord, ...], f32: tuple[F32MaterializationRecord, ...],
                             copies: tuple[ParameterCopyRecord, ...], aliases: tuple[TargetAliasRecord, ...]) -> tuple[object, ...]:
    values = list(base)
    def add(value: object) -> None:
        if not any(value is existing for existing in values):
            values.append(value)
    for record in conversions:
        add(record.node)
    for alias in aliases:
        if alias.target_id in {"C17-DIV", "C17-MUL"}:
            add(alias.node)
    for record in pcg:
        add(record.node)
    for record in f32:
        if record.node is not None and record.record_id != "F21":
            add(record.node)
    for record in copies:
        if record.record_id not in {"AP10", "AP12", "AP14"}:
            add(record.node)
    return tuple(values)


def _validate_expanded_ledgers(proof: FrontendProof, program: TypedProgram) -> None:
    if proof.live_program is not program:
        raise _fail("expanded proof is not bound to the live TypedProgram")
    nodes = _source_nodes_by_span(program)
    expected_conversions = _conversion_records(program, nodes)
    expected_pcg = _pcg_order_records(program, nodes)
    expected_f32 = _f32_materialization_records(program, nodes)
    expected_copies = _parameter_copy_records(program)
    expected_aliases = _target_aliases(nodes, proof.array_records)
    expected_eager, expected_pooled = _authority_records()
    expected_unique = _unique_consumed_objects(proof.consumed_objects, expected_conversions,
                                               expected_pcg, expected_f32, expected_copies,
                                               expected_aliases)
    if not proof.conversion_records or len(proof.conversion_records) != 30:
        raise _fail("conversion ledger cardinality mismatch")
    if not proof.pcg_order_records or len(proof.pcg_order_records) != 8:
        raise _fail("PCG order ledger cardinality mismatch")
    if not proof.f32_materialization_records or len(proof.f32_materialization_records) != 49:
        raise _fail("F32 materialization ledger cardinality mismatch")
    if not proof.parameter_copy_records or len(proof.parameter_copy_records) != 18:
        raise _fail("parameter-copy ledger cardinality mismatch")
    if (proof.conversion_records != expected_conversions
            or any(actual.node is not expected.node
                   for actual, expected in zip(proof.conversion_records, expected_conversions))):
        raise _fail("conversion ledger identity, order, or operation mismatch")
    if (proof.pcg_order_records != expected_pcg
            or any(actual.node is not expected.node
                   for actual, expected in zip(proof.pcg_order_records, expected_pcg))):
        raise _fail("PCG assignment identity or order mismatch")
    if (proof.f32_materialization_records != expected_f32
            or any(actual.node is not expected.node
                   for actual, expected in zip(proof.f32_materialization_records, expected_f32)
                   if expected.node is not None)):
        raise _fail("F32 materialization identity, kind, role, or order mismatch")
    if (proof.parameter_copy_records != expected_copies
            or any(actual.node is not expected.node
                   for actual, expected in zip(proof.parameter_copy_records, expected_copies))):
        raise _fail("parameter-copy identity or order mismatch")
    if (proof.target_aliases != expected_aliases
            or any(actual.node is not expected.node
                   for actual, expected in zip(proof.target_aliases, expected_aliases))):
        raise _fail("declared reference-target identity mismatch")
    expected_refs = tuple(SourceReferenceRecord(*row) for row in SOURCE_REFERENCE_LEDGER)
    if proof.source_references != expected_refs:
        raise _fail("source reference edge mismatch")
    expected_carriers = tuple(CarrierEdgeRecord(*row) for row in CARRIER_EDGE_LEDGER)
    if proof.carrier_edges != expected_carriers:
        raise _fail("carrier edge mismatch")
    if proof.authority_eager_records != expected_eager:
        raise _fail("eager authority census mismatch")
    if proof.authority_pooled_records != expected_pooled:
        raise _fail("pooled authority census mismatch")
    if proof.f32_store_view != F32_STORE_VIEW:
        raise _fail("derived F32 store view mismatch")
    derived = tuple(item.record_id for item in proof.f32_materialization_records
                    if item.role in {"f32_store", "f32_return", "diffusion_store"})
    if derived != F32_STORE_VIEW or tuple(item.record_id for item in proof.f32_materialization_records
                                         if item.role not in {"f32_store", "f32_return", "diffusion_store"}) != F32_EXCLUDED:
        raise _fail("F32 store view role derivation mismatch")
    if (len(proof.unique_consumed_objects) != 153
            or len(proof.unique_consumed_objects) != len(expected_unique)
            or any(actual is not expected
                   for actual, expected in zip(proof.unique_consumed_objects, expected_unique))
            or len({id(item) for item in proof.unique_consumed_objects}) != 153):
        raise _fail("unique consumption ledger is incomplete, reordered, cloned, or double-counted")
    if proof.f32_materialization_records[-1].binding_kind != "runtime_adapter":
        raise _fail("F49 binding kind mismatch")
    if proof.f32_materialization_records[-1].role != "f32_return":
        raise _fail("F49 role mismatch")
    if proof.f32_materialization_records[-1].ref_to != "F48":
        raise _fail("F49 reference mismatch")
    if len(proof.unique_consumed_objects) != len({id(item) for item in proof.unique_consumed_objects}):
        raise _fail("unique consumption aliases an identity")


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source, program.declarations,
                 program.functions, program.resources, program.body_status,
                 program.local_type_names, program.structs, program.uniform_blocks,
                 program.interface_symbols, program.builtin_symbols,
                 program.counted_loop_proof, program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources, program.local_type_names,
                 program.structs, program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _walk_statements(value):
    yield value
    for child in value.children:
        yield from _walk_statements(child)


def _expressions(program: TypedProgram):
    values = []
    for declaration in program.declarations:
        if declaration.initializer is not None:
            values.extend(_walk_expression(declaration.initializer))
    for function in program.functions:
        for statement in function.body:
            values.extend(_walk_statement(statement))
    return tuple(values)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _loop_records(program: TypedProgram) -> tuple[LoopRecord, ...]:
    by_span = {}
    by_function = {}
    for function in program.functions:
        for statement in function.body:
            for node in _walk_statements(statement):
                if node.kind == "for":
                    by_span[_span(node)] = node
                    by_function[_span(node)] = function.name
    records = []
    for row in LOOP_LEDGER:
        (record_id, function_name, span, digest, induction_id, induction_name,
         induction_type, induction_span, induction_digest, start_text, bound_text,
         comparison, update) = row
        node = by_span.get(span)
        if node is None or by_function.get(span) != function_name:
            raise _fail(f"loop ledger object missing: {record_id}")
        if len(node.children) != 2 or len(node.expressions) != 2:
            raise _fail(f"loop shape mismatch: {record_id}")
        initialization = node.children[0].expressions[0]
        condition, increment = node.expressions
        induction = initialization.symbol
        if (induction is None or induction.id != induction_id
                or induction.name != induction_name
                or induction.type.display() != induction_type
                or _span(induction) != induction_span
                or _sha(initialization) != induction_digest
                or _sha(node) != digest):
            raise _fail(f"loop identity mismatch: {record_id}")
        if condition.operator != comparison or increment.operator != update:
            raise _fail(f"loop control mismatch: {record_id}")
        proof = node.loop_proof
        if record_id.startswith("L-PAL"):
            if proof is None or proof.induction_symbol_id != induction_id:
                raise _fail(f"bounded loop proof missing: {record_id}")
        elif proof is not None:
            raise _fail(f"unproved loop unexpectedly admitted: {record_id}")
        records.append(LoopRecord(
            record_id, function_name, span, digest, induction_id, induction_name,
            induction_type, induction_span, induction_digest, start_text, bound_text,
            comparison, update, node, initialization, condition, increment,
            node.children[1], proof))
    return tuple(records)


def _array_records(program: TypedProgram) -> tuple[ArrayRecord, ...]:
    declarations = {item.symbol.id: item for item in program.declarations}
    local = None
    for function in program.functions:
        for statement in function.body:
            for node in _walk_statements(statement):
                for expression in node.expressions:
                    for candidate in _walk_expression(expression):
                        if (candidate.kind == "declaration" and candidate.symbol is not None
                                and candidate.symbol.id == 126):
                            local = (candidate, node)
    records = []
    for row in ARRAY_LEDGER:
        record_id, symbol_id, symbol_name, type_name, extent, span, digest, statement_digest = row
        if record_id == "A-ERR_ROW":
            if local is None:
                raise _fail("errRow declaration missing")
            node, statement = local
            initializer = None
        else:
            declaration = declarations.get(symbol_id)
            if declaration is None:
                raise _fail(f"array declaration missing: {record_id}")
            node, initializer, statement = declaration, declaration.initializer, None
        records.append(ArrayRecord(record_id, symbol_id, symbol_name, type_name, extent,
                                   span, digest, node, initializer, statement))
    return tuple(records)


def _array_parameter_records(program: TypedProgram) -> tuple[ArrayParameterRecord, ...]:
    functions = {function.signature.id: function for function in program.functions}
    records = []
    for row in ARRAY_PARAMETER_LEDGER:
        record_id, function_id, function_name, symbol_id, symbol_name, type_name, span, digest = row
        function = functions.get(function_id)
        if function is None or function.name != function_name:
            raise _fail(f"array parameter function missing: {record_id}")
        node = next((item for item in function.signature.parameters
                     if item.id == symbol_id), None)
        if node is None:
            raise _fail(f"array parameter symbol missing: {record_id}")
        records.append(ArrayParameterRecord(record_id, function_id, function_name,
                                            symbol_id, symbol_name, type_name, span,
                                            digest, node))
    return tuple(records)


def _index_records(program: TypedProgram) -> tuple[IndexRecord, ...]:
    by_digest = { _sha(item): item for item in _expressions(program)
                  if item.kind == "index" }
    records = []
    for row in INDEX_LEDGER:
        (record_id, root_symbol_id, root_name, root_type, span, result_type,
         digest) = row
        node = by_digest.get(digest)
        if node is None:
            raise _fail(f"indexed node missing: {record_id}")
        if len(node.children) != 2:
            raise _fail(f"indexed node shape mismatch: {record_id}")
        root = node.children[0]
        while root.kind == "index":
            if len(root.children) != 2:
                raise _fail(f"nested indexed node shape mismatch: {record_id}")
            root = root.children[0]
        if (root.symbol_id != root_symbol_id or root.symbol is None
                or root.symbol.name != root_name
                or root.type.display() != root_type):
            raise _fail(f"indexed root mismatch: {record_id}")
        records.append(IndexRecord(
            record_id, root_symbol_id, root_name, root_type, span, result_type,
            digest, node.children[1].type.display(), _span(node.children[1]),
            _sha(node.children[1]), node))
    return tuple(records)


def _bitwise_records(program: TypedProgram) -> tuple[BitwiseRecord, ...]:
    by_digest = {_sha(item): item for item in _expressions(program)
                 if item.kind == "binary" and item.operator in {"&", "%", "^=", ">>"}}
    records = []
    for row in BITWISE_LEDGER:
        record_id, operator, span, type_name, digest = row
        node = by_digest.get(digest)
        if node is None:
            raise _fail(f"bitwise node missing: {record_id}")
        records.append(BitwiseRecord(record_id, operator, span, type_name, digest, node))
    return tuple(records)


def validate_dither_proof_ledgers(proof: FrontendProof,
                                  program: TypedProgram | None = None) -> None:
    """Reject forged, reordered, cloned, or partially consumed proof ledgers.

    The live program is an explicit validation boundary.  A proof carries
    semantic objects, so validating its scalar metadata alone would allow a
    complete ``deepcopy`` of the proof to masquerade as the authenticated
    source tree.
    """
    if not isinstance(program, TypedProgram):
        raise _fail("live TypedProgram is required for proof validation")
    if not isinstance(proof, FrontendProof) or proof.program_key != KEY:
        raise _fail("proof record type or program key mismatch")
    if tuple(item.record_id for item in proof.loop_records) != tuple(item[0] for item in LOOP_LEDGER):
        raise _fail("loop ledger order or cardinality mismatch")
    if tuple(item.record_id for item in proof.array_records) != tuple(item[0] for item in ARRAY_LEDGER):
        raise _fail("array ledger order or cardinality mismatch")
    if tuple(item.record_id for item in proof.array_parameters) != tuple(item[0] for item in ARRAY_PARAMETER_LEDGER):
        raise _fail("array parameter ledger order or cardinality mismatch")
    if tuple(item.record_id for item in proof.index_records) != tuple(item[0] for item in INDEX_LEDGER):
        raise _fail("index ledger order or cardinality mismatch")
    if tuple(item.record_id for item in proof.bitwise_records) != tuple(item[0] for item in BITWISE_LEDGER):
        raise _fail("bitwise ledger order or cardinality mismatch")

    live_records = (
        _loop_records(program), _array_records(program),
        _array_parameter_records(program), _index_records(program),
        _bitwise_records(program),
    )
    proof_records = (proof.loop_records, proof.array_records,
                     proof.array_parameters, proof.index_records,
                     proof.bitwise_records)
    for live, candidate in zip(live_records, proof_records):
        if any(actual.node is not expected.node for actual, expected in zip(candidate, live)):
            raise _fail("proof ledger is not bound to the live TypedProgram")

    for record, expected in zip(proof.loop_records, LOOP_LEDGER):
        if (_span(record.node) != record.span or _sha(record.node) != record.node_sha256
                or (record.record_id, record.function_name, record.span,
                    record.node_sha256, record.induction_symbol_id, record.induction_name,
                    record.induction_type, record.induction_span, record.induction_sha256,
                    record.start_text, record.bound_text, record.comparison, record.update)
                != expected):
            raise _fail(f"loop record identity mismatch: {record.record_id}")
        if (len(record.node.children) != 2
                or record.node.children[1] is not record.body
                or record.initialization is not record.node.children[0].expressions[0]
                or record.condition is not record.node.expressions[0]
                or record.increment is not record.node.expressions[1]):
            raise _fail(f"loop object consumption mismatch: {record.record_id}")
        if record.record_id.startswith("L-PAL"):
            if record.proof is not record.node.loop_proof:
                raise _fail(f"bounded loop proof identity mismatch: {record.record_id}")
        elif record.proof is not None:
            raise _fail(f"unproved loop proof must be None: {record.record_id}")

    for record, expected in zip(proof.array_records, ARRAY_LEDGER):
        if (record.record_id, record.symbol_id, record.symbol_name, record.type_name,
            record.extent, record.span, record.node_sha256) != expected[:7]:
            raise _fail(f"array record identity mismatch: {record.record_id}")
        if (_span(record.node) != record.span or _sha(record.node) != record.node_sha256
                or record.node.symbol.id != record.symbol_id
                or record.node.symbol.name != record.symbol_name
                or record.node.symbol.type.display() != record.type_name):
            raise _fail(f"array node identity mismatch: {record.record_id}")
        if record.record_id == "A-ERR_ROW":
            if record.statement is None or _sha(record.statement) != expected[7] or record.initializer is not None:
                raise _fail("errRow declaration/lifetime mismatch")
        elif record.initializer is not record.node.initializer:
            raise _fail(f"array initializer object mismatch: {record.record_id}")
        elif record.initializer is None or record.initializer.kind != "construct":
            if record.record_id != "A-FS_ERR_W" or record.initializer is None:
                raise _fail(f"array initializer mismatch: {record.record_id}")
        elif len(record.initializer.children) != record.extent:
            raise _fail(f"array extent mismatch: {record.record_id}")

    for record, expected in zip(proof.array_parameters, ARRAY_PARAMETER_LEDGER):
        if (record.record_id, record.function_id, record.function_name, record.symbol_id,
            record.symbol_name, record.type_name, record.span, record.node_sha256) != expected:
            raise _fail(f"array parameter identity mismatch: {record.record_id}")
        if (_sha(record.node) != record.node_sha256 or record.node.id != record.symbol_id
                or record.node.name != record.symbol_name
                or record.node.type.display() != record.type_name
                or _span(record.node) != record.span
                or record.node.storage != "parameter"):
            raise _fail(f"array parameter node mismatch: {record.record_id}")

    for record, expected in zip(proof.index_records, INDEX_LEDGER):
        if (record.record_id, record.root_symbol_id, record.root_name, record.root_type,
            record.span, record.result_type, record.node_sha256) != expected:
            raise _fail(f"index record identity mismatch: {record.record_id}")
        root = record.node.children[0]
        while root.kind == "index":
            root = root.children[0]
        if (_span(record.node) != record.span or _sha(record.node) != record.node_sha256
                or record.node.kind != "index" or record.node.type.display() != record.result_type
                or record.index_type != record.node.children[1].type.display()
                or record.index_span != _span(record.node.children[1])
                or record.index_sha256 != _sha(record.node.children[1])
                or root.symbol_id != record.root_symbol_id
                or root.symbol is None or root.symbol.name != record.root_name
                or root.type.display() != record.root_type):
            raise _fail(f"index node identity mismatch: {record.record_id}")

    for record, expected in zip(proof.bitwise_records, BITWISE_LEDGER):
        if (record.record_id, record.operator, record.span, record.type_name,
            record.node_sha256) != expected:
            raise _fail(f"bitwise record identity mismatch: {record.record_id}")
        if (_span(record.node) != record.span or _sha(record.node) != record.node_sha256
                or record.node.kind != "binary" or record.node.operator != record.operator
                or record.node.type.display() != record.type_name):
            raise _fail(f"bitwise node identity mismatch: {record.record_id}")

    record_nodes = tuple(item.node for item in (
        *proof.loop_records, *proof.array_records, *proof.array_parameters,
        *proof.index_records, *proof.bitwise_records))
    if len(record_nodes) != len({id(item) for item in record_nodes}):
        raise _fail("object identity ledger is not disjoint")
    expected_consumed = record_nodes
    if (len(proof.consumed_objects) != len(expected_consumed)
            or any(actual is not expected for actual, expected
                   in zip(proof.consumed_objects, expected_consumed))
            or len({id(item) for item in proof.consumed_objects}) != len(proof.consumed_objects)):
        raise _fail("consumption ledger is incomplete, reordered, or cloned")
    _validate_expanded_ledgers(proof, program)


def authenticate_dither_frontend(program: TypedProgram, source_hash: str | None,
                                 profile: str | None) -> FrontendProof:
    if program.key != KEY:
        raise _fail("selected key is not filter/dither:dither")
    if profile != PROFILE:
        raise _fail("exact prepared profile required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (source_hash != RAW_SHA256 or len(raw) != RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or _sha(program.functions) != FUNCTIONS_SHA256
            or _whole(program) != WHOLE_SHA256
            or _interface(program) != INTERFACE_SHA256):
        raise _fail("source, function, whole-program, or interface lock mismatch")
    if program.body_status != "analyzed" or program.preprocessor_defines != ():
        raise _fail("analyzed body or preprocessor census mismatch")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block drift")
    proof = program.counted_loop_proof
    if proof is None or (proof.loop_count, proof.unproved_loop_count,
                         proof.max_effective_depth, proof.max_lexical_product,
                         proof.entrypoint_charge, proof.call_graph_acyclic) != LOOP_PROOF:
        raise _fail("counted-loop census mismatch")
    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives)
            != (tuple(name for name, _ in SOURCE_UNIFORMS), ("inputTex",),
                ("fragColor",), True, False)):
        raise _fail("resource or binding signature mismatch")
    if len(program.declarations) != 45 or len(program.functions) != 21:
        raise _fail("declaration/function cardinality mismatch")
    arrays = tuple((item.symbol.name, item.type.display()) for item in program.declarations
                   if "[" in item.type.display())
    if arrays != ARRAY_DECLARATIONS[:-1]:
        raise _fail("aggregate declaration census mismatch")
    if (program.declarations[-1].symbol.name, program.declarations[-1].type.display()) != ARRAY_DECLARATIONS[-1]:
        raise _fail("FS_ERR_W declaration identity mismatch")
    expressions = _expressions(program)
    if Counter(item.kind for item in expressions) != Counter(EXPECTED_EXPR_KINDS):
        raise _fail("expression-kind cardinality mismatch")
    if Counter(item.operator for item in expressions if item.operator is not None) != Counter(EXPECTED_OPERATORS):
        raise _fail("operator cardinality mismatch")
    bitwise = tuple(item for item in expressions
                    if item.kind == "binary" and item.operator in {"&", "%", "^=", ">>"})
    indexed = tuple(item for item in expressions if item.kind == "index")
    if len(bitwise) != 9 or len(indexed) != 24:
        raise _fail("integer or aggregate indexing census mismatch")
    loop_records = _loop_records(program)
    array_records = _array_records(program)
    array_parameters = _array_parameter_records(program)
    index_records = _index_records(program)
    bitwise_records = _bitwise_records(program)
    consumed = tuple(item.node for item in (
        *loop_records, *array_records, *array_parameters,
        *index_records, *bitwise_records))
    if len({id(item) for item in consumed}) != len(consumed):
        raise _fail("object identity ledger is not disjoint")
    source_nodes = _source_nodes_by_span(program)
    conversion_records = _conversion_records(program, source_nodes)
    pcg_order_records = _pcg_order_records(program, source_nodes)
    f32_materialization_records = _f32_materialization_records(program, source_nodes)
    parameter_copy_records = _parameter_copy_records(program)
    target_aliases = _target_aliases(source_nodes, array_records)
    source_references = tuple(SourceReferenceRecord(*row) for row in SOURCE_REFERENCE_LEDGER)
    carrier_edges = tuple(CarrierEdgeRecord(*row) for row in CARRIER_EDGE_LEDGER)
    authority_eager_records, authority_pooled_records = _authority_records()
    unique_consumed_objects = _unique_consumed_objects(
        consumed, conversion_records, pcg_order_records, f32_materialization_records,
        parameter_copy_records, target_aliases)
    f32_store_view = tuple(item.record_id for item in f32_materialization_records
                           if item.role in {"f32_store", "f32_return", "diffusion_store"})
    result = FrontendProof(KEY, SAMPLER_RUNTIME_ABI,
                           arrays + (ARRAY_DECLARATIONS[-1],), loop_records,
                           array_records, array_parameters, index_records,
                           bitwise_records, consumed, conversion_records,
                           pcg_order_records, f32_materialization_records,
                           parameter_copy_records, target_aliases,
                           source_references, carrier_edges, unique_consumed_objects,
                           authority_eager_records, authority_pooled_records,
                           f32_store_view, program)
    validate_dither_proof_ledgers(result, program)
    return result


def apply_dither_frontend(program: TypedProgram, source_hash: str | None,
                          profile: str | None) -> TypedProgram:
    authenticate_dither_frontend(program, source_hash, profile)
    return program


__all__ = ("KEY", "PROFILE", "KEYS", "PROFILES", "PREPARED_KEYS", "PREPARED_PROFILES",
           "DITHER_FRONTEND_KEYS", "ALLOWED_ROW_FIELDS", "REQUIRED_COMPANION_PROFILES",
           "SOURCE_UNIFORMS", "RUNTIME_UNIFORM_ABI", "SAMPLER_RUNTIME_ABI",
           "ARRAY_DECLARATIONS", "LOOP_PROOF", "LOOP_LEDGER", "ARRAY_LEDGER",
           "ARRAY_PARAMETER_LEDGER", "INDEX_LEDGER", "BITWISE_LEDGER", "FrontendProof",
           "LoopRecord", "ArrayRecord", "ArrayParameterRecord", "IndexRecord",
           "BitwiseRecord", "ConversionRecord", "PCGOrderRecord", "F32MaterializationRecord",
           "ParameterCopyRecord", "TargetAliasRecord", "SourceReferenceRecord",
           "CarrierEdgeRecord", "AuthorityRecord", "CONVERSION_LEDGER", "PCG_ORDER_LEDGER",
           "F32_MATERIALIZATION_LEDGER", "PARAMETER_COPY_LEDGER", "F32_STORE_VIEW",
           "authenticate_dither_frontend", "validate_dither_proof_ledgers",
           "apply_dither_frontend")
