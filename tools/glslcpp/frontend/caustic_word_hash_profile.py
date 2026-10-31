"""Exact float-bit-ingress and scalar word-XOR closure profile for Caustic.

This module does not add a general bit-reinterpretation or scalar bitwise
capability.  It authenticates the one corpus program whose lattice hash may
reinterpret a float's bits and mix three scalar ``uint`` words, and returns the
candidate-owned IR objects consumed independently by the validator and the
emitter.

Unlike Perlin's scalar XOR closure (Task 27), Caustic's XORs are live,
reachable, rendered code: their results reach ``fragColor``.  Native fixtures
must therefore prove real values, not merely that the program compiles.
"""

from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "caustic-float-bits-scalar-word-hash-v1"
CAUSTIC_KEY = "classicNoisedeck/caustic:caustic"

_RAW_BYTES = 15645
_RAW_SHA256 = "161cb6114f312a223d88a5c60a3ecb694a4c8766fca91b3fc47ae92078f2a00d"
_NORMALIZED_BYTES = 7999
_NORMALIZED_SHA256 = "b4a45216e62c5facade77e64925075e736ee3ed0eb7b1798bc777ba1bb714b83"
_FUNCTIONS_SHA256 = "43a0063cf16ebea820084302df1d6c59594485b559267597ad30ac3cddc659a3"
_WHOLE_SHA256 = "b0ffb30caee0d301f54d42892a6e70619fd4cf1e4c19d5fc3f399b3bfc598624"
_INTERFACE_SHA256 = "094c31b573c08cfdf9e3c76e766c4b4ca96a2df12d6a1629f18b141624464b50"

_HOST_ID = 94
_HOST_NAME = "randomFromLatticeWithOffset"
_HOST_SPAN = "164:1-208:2"
_DEFINES = (("NOISE_TYPE", "int", "10"),)
_LOOP_PROOF = (0, 0, 0, 0, 0, True)

# Exactly the four authenticated nodes, in source order. Each row is
# (kind, path, span, result type, node sha, parent kind, child type tuple,
#  child sha tuple). Nothing outside this tuple may be lowered.
#
# The `uvec3 ^ uvec3` at 200:19 is deliberately ABSENT: it is already admitted
# by the pre-existing `uint-vector-bitwise` capability and is not part of this
# closure.
_NODES = (
    ("floatBitsToUint", (13, "e0", 0), "192:21-192:46", "uint",
     "e6b86baf243b38741b4870acfe990ce3b353f18948d38773cc853ab11ce3b6a4",
     "declaration", ("float",),
     ("4c2cc94f5d6f93142124122d1f36a2aa7560bdc88512eb7f27370783eb78dbac",)),
    ("^", (14, "e0", 0, 0), "195:10-195:46", "uint",
     "0ec45e30c890d1177375332f93564f8d12d8bd47805393740503edd290617445",
     "construct", ("uint", "uint"),
     ("2562f15164ab5b9481bb798dc74b9994417976020d5e6e9183421ecead9479a1",
      "4d5400d40220fb6418ef8c6d27997a72862ff40174c4487d8bcdfba8deefacb8")),
    ("^", (14, "e0", 0, 1), "196:10-196:46", "uint",
     "7f98e820b388d74eb98c8296f798d778d63d6bdb8d67e68f9bfae73f74e56e4e",
     "construct", ("uint", "uint"),
     ("b5d7903129b6eb87c8dc28a936ac1d7449031b684a895995a33f608f061bdfc8",
      "b30427f6ce552c15b34104bca4aa23b865ad0939898eb45d4ec5cdcb1545dfff")),
    ("^", (14, "e0", 0, 2), "197:10-197:47", "uint",
     "791b232712de5fe1a3babde2e00799603fbb523421973f9b20888f12e978b8ee",
     "construct", ("uint", "uint"),
     ("6d5b73a65a867110b99a54ab4fd21669eeffbbffe871830809a6cc374f9df688",
      "53bcacbea819782a268357731c1eb75d12b5019586f84dc7d33e163aef6ebcd6")),
)

_ANCESTOR_KINDS = ("decl",)
_INGRESS_ANCESTOR_SPAN = ("192:5-192:47",)
_XOR_ANCESTOR_SPAN = ("194:5-198:7",)

_PROFILE_SHA256 = "f97e506b0bd1a5b009e56809e33cfb1015e541a658dd4eff72388419f6244c80"
_FROZEN_PROFILE_TUPLE_REPR = """('caustic-float-bits-scalar-word-hash-v1', 'classicNoisedeck/caustic:caustic', '161cb6114f312a223d88a5c60a3ecb694a4c8766fca91b3fc47ae92078f2a00d', (('NOISE_TYPE', 'int', '10'),), 'glsl-f32', '43a0063cf16ebea820084302df1d6c59594485b559267597ad30ac3cddc659a3', 'b0ffb30caee0d301f54d42892a6e70619fd4cf1e4c19d5fc3f399b3bfc598624', '094c31b573c08cfdf9e3c76e766c4b4ca96a2df12d6a1629f18b141624464b50', 94, (0, 0, 0, 0, 0, True), (('floatBitsToUint', (13, 'e0', 0), '192:21-192:46', 'uint', 'e6b86baf243b38741b4870acfe990ce3b353f18948d38773cc853ab11ce3b6a4', 'declaration', ('float',), ('4c2cc94f5d6f93142124122d1f36a2aa7560bdc88512eb7f27370783eb78dbac',)), ('^', (14, 'e0', 0, 0), '195:10-195:46', 'uint', '0ec45e30c890d1177375332f93564f8d12d8bd47805393740503edd290617445', 'construct', ('uint', 'uint'), ('2562f15164ab5b9481bb798dc74b9994417976020d5e6e9183421ecead9479a1', '4d5400d40220fb6418ef8c6d27997a72862ff40174c4487d8bcdfba8deefacb8')), ('^', (14, 'e0', 0, 1), '196:10-196:46', 'uint', '7f98e820b388d74eb98c8296f798d778d63d6bdb8d67e68f9bfae73f74e56e4e', 'construct', ('uint', 'uint'), ('b5d7903129b6eb87c8dc28a936ac1d7449031b684a895995a33f608f061bdfc8', 'b30427f6ce552c15b34104bca4aa23b865ad0939898eb45d4ec5cdcb1545dfff')), ('^', (14, 'e0', 0, 2), '197:10-197:47', 'uint', '791b232712de5fe1a3babde2e00799603fbb523421973f9b20888f12e978b8ee', 'construct', ('uint', 'uint'), ('6d5b73a65a867110b99a54ab4fd21669eeffbbffe871830809a6cc374f9df688', '53bcacbea819782a268357731c1eb75d12b5019586f84dc7d33e163aef6ebcd6'))))"""


# Exact current runtime tree. The default tuple above remains unchanged.
_DYNAMIC_DEFINES = (("NOISE_TYPE", "str", "int"),)
_DYNAMIC_NORMALIZED_BYTES = 14783
_DYNAMIC_NORMALIZED_SHA256 = "d99a1b7d2aa67458f6ffa87e6f6521f8fe602fc08b9e28053ec8567c2cb879eb"
_DYNAMIC_HOST_SPAN = "180:1-224:2"
_DYNAMIC_FUNCTION_COUNT = 27
_DYNAMIC_INGRESS_ANCESTOR_SPAN = ("208:5-208:47",)
_DYNAMIC_XOR_ANCESTOR_SPAN = ("210:5-214:7",)
_DYNAMIC_PROFILE_SHA256 = "378633c35bade1b134eefaae5497f64c60c6b3f26aa46f53c4d5176c481e67f5"
_DYNAMIC_FROZEN_PROFILE_TUPLE_REPR = """('caustic-float-bits-scalar-word-hash-v1', 'classicNoisedeck/caustic:caustic', '161cb6114f312a223d88a5c60a3ecb694a4c8766fca91b3fc47ae92078f2a00d', (('NOISE_TYPE', 'str', 'int'),), 'glsl-f32', 'd8d32f6c2e3dbe45d18858abf262a256b6eeb46b04fa06bfd726a7cfd797839a', '0d087d5f016f8009ea7fbf1dc7f80a0d2763656b4e9fea80801ed660984f6fac', '12318d0f302f004fd3dfeac3062f3d2a2c03690275c2485d14f5c522110900aa', 120, (0, 0, 0, 0, 0, True), (('floatBitsToUint', (13, 'e0', 0), '208:21-208:46', 'uint', '76eb921a7e9a5477c2949d65d2c17eb5dc3eaab48015168f83a93c0054ceb08f', 'declaration', ('float',), ('173cd80f191c0d8d4a892a3ec9edca50bfa26d68befb861e6999eefaa2b0a893',)), ('^', (14, 'e0', 0, 0), '211:10-211:46', 'uint', 'e353c388481f3feb7caebad195a6777eb70946f5f7e2c65b4e67dff4c8409344', 'construct', ('uint', 'uint'), ('2b2dae07fb219e922c6b33cccc9c34fe23306c1804bd260e4862480c987d63cc', '5cc579da348ac02af52f5220601b725224e38a430ef4eb7d29cf24806593b9e1')), ('^', (14, 'e0', 0, 1), '212:10-212:46', 'uint', '9d78c3f72dafa6e9aebf1c7ff2671bea1351ff9adc8248e2cdaedc086c63a5fe', 'construct', ('uint', 'uint'), ('44b6b9133fb0f0280fcd107975a336163f2752cb3e94b6a93b163b9cafe04f48', '0d9ab4870cfc3be497a81bae1ee2f04c924ca4de97a07ec76b8a7cb8ea8cf521')), ('^', (14, 'e0', 0, 2), '213:10-213:47', 'uint', '170e029abdad3360d5f4bd1795cefdfeebd7cb1594c74172827fb68715fdf984', 'construct', ('uint', 'uint'), ('6d0582c8f8fb6430a384ca8d1b8fc3b42ab0d1b2348c4314143a64d4d9935eec', 'cd6902ba856fec8e875d7672cea0411fa43ea4553b96b1699bc2c4018b53c4e0'))))"""

_CURRENT_VARIANTS = {10: {'raw_sha256': '9ff29d7f4b4baacb800295540ab1c939f9482dbb1f2f48173819c947334c4fd7',
      'raw_bytes': 15714,
      'normalized_bytes': 7920,
      'normalized_sha256': '8009ac5af751ebdea2f7986a585c874944e6988e7e844598b68080070ff32a6e',
      'frozen': ('caustic-float-bits-scalar-word-hash-v1',
                 'classicNoisedeck/caustic:caustic',
                 '9ff29d7f4b4baacb800295540ab1c939f9482dbb1f2f48173819c947334c4fd7',
                 (('NOISE_TYPE', 'int', '10'),),
                 'glsl-f32',
                 '76fa79f83c464c9b2379b024ab56270728a24607c551cee3fff72028789da169',
                 '3a4bc8cf2700207cc723a9e20a6277ca315705bf43b9c4acdd61c1ad5cb133f5',
                 'dc05bfc7735bd9abd9c659976aa01cf5a752f684d89a3e1ab520c238ff47a2e2',
                 94,
                 (0, 0, 0, 0, 0, True),
                 (('floatBitsToUint',
                   (13, 'e0', 0),
                   '192:21-192:46',
                   'uint',
                   'ade5c761279b2c782c00846c315e39489a49151ae4720ac8f2c2d9400cc13d4f',
                   'declaration',
                   ('float',),
                   ('158f5e4dedfbbb77222077d1acebb752749d0d771423334534d189d9070856c1',)),
                  ('^',
                   (14, 'e0', 0, 0),
                   '195:10-195:46',
                   'uint',
                   'f2739ee698403fee4ee3be740b68d80f7df6abffa962f64925cd40616689831c',
                   'construct',
                   ('uint', 'uint'),
                   ('0b298b125e84b1c712d489a96b4d5a24887d9c2d700688f6a6a0c096b5f279cf',
                    '57dd9737d48215c30ce1240532833f403d798bbfcd47fe790b6387f6a09ec932')),
                  ('^',
                   (14, 'e0', 0, 1),
                   '196:10-196:46',
                   'uint',
                   '51044fe79b47e0c60ec7e724c9e0069831044b9863d31ed27d04c14a8147bc2e',
                   'construct',
                   ('uint', 'uint'),
                   ('757092384ae101ebbb6d620dd56da7dfc272b86667949790000a0330b0697063',
                    'b2e21ecb99e1f38997a12f81cf8397f50923c63490a3f9d395ebe80bba53b9ec')),
                  ('^',
                   (14, 'e0', 0, 2),
                   '197:10-197:47',
                   'uint',
                   '0f31127db4a3b5d9e1230d1813f3624399b20d1976ab9038a051c4f57dbe7756',
                   'construct',
                   ('uint', 'uint'),
                   ('0e071f4f374b037279801785e28b39b275728c2c2ac80c8f1a4871f6390344e4',
                    '431feae2e65feb2dd25788a5b76ca3f89befd6a51f45c605ec1e26cfe3ce1d32')))),
      'profile_sha256': '25d3aacbd1b217d53c911fd8468dc078c67cd601a5826e3491c1d5d250e71d38'},
 'int': {'raw_sha256': '9ff29d7f4b4baacb800295540ab1c939f9482dbb1f2f48173819c947334c4fd7',
         'raw_bytes': 15714,
         'normalized_bytes': 14704,
         'normalized_sha256': '6179233bf409c810df54f8931ccfb84d6c95fdad8be45337391f81e646a2c98d',
         'frozen': ('caustic-float-bits-scalar-word-hash-v1',
                    'classicNoisedeck/caustic:caustic',
                    '9ff29d7f4b4baacb800295540ab1c939f9482dbb1f2f48173819c947334c4fd7',
                    (('NOISE_TYPE', 'str', 'int'),),
                    'glsl-f32',
                    '3ca074327fb5a86540fcd38fc9ed3ed7d40ea2f34ee768462e2ac57c1991690e',
                    '613f55d8d27fbfa1f93393ad95eb177f0588c6d6bf748a4e8745cf3570952b5c',
                    'dce9a3494102253a82a988aa222ab361b59741de95f32efb2d82650175676f3c',
                    120,
                    (0, 0, 0, 0, 0, True),
                    (('floatBitsToUint',
                      (13, 'e0', 0),
                      '208:21-208:46',
                      'uint',
                      '20427c30b329b30f032e2fd98aa226d21c8bb408e822fd5b49888e9471db294c',
                      'declaration',
                      ('float',),
                      ('245523e2d1119071c1c25bdd72c2c0e46f864275afcd435bf5fc114c7ee4ee98',)),
                     ('^',
                      (14, 'e0', 0, 0),
                      '211:10-211:46',
                      'uint',
                      'ee67b787353117b4c6752ce9f4d452b459dddddb53eccdb97eeda58b010f8f68',
                      'construct',
                      ('uint', 'uint'),
                      ('359b02d0099b2c1132277ed10c81ac2c1d25c2f041a480067b91d3900cba4e4f',
                       '5efc0fc5e266c8c4c05ef7b49b078142c5a4ef5275387f5be8cda08d279a2c6d')),
                     ('^',
                      (14, 'e0', 0, 1),
                      '212:10-212:46',
                      'uint',
                      'fda7701e5bc4f97a06da1a4e340706e38c724c071027a5c64f38d9d85a3318c3',
                      'construct',
                      ('uint', 'uint'),
                      ('61d40741374a1836831081b4e40dba592d4553deb4ee9993817701e8f9949df6',
                       'e42030df1d4e02624fb356eb5f9624a9a76c68772dd4cf59c479d605338b1327')),
                     ('^',
                      (14, 'e0', 0, 2),
                      '213:10-213:47',
                      'uint',
                      'd87eddcb0ec12f5af259429e8555e62682c9b0530bc90ab11d1868e2672d7e4f',
                      'construct',
                      ('uint', 'uint'),
                      ('af14d16e00610c493758bfe3786b8402e24d382b63813a4a0da0b68c7f825b24',
                       '11cf02f787bb51d8db7277eefabf7679d692225ce96555d4999361a2f1d2e924')))),
         'profile_sha256': '06cd795df07ea63cb907390833afe073326b84e83fdc49ddbc24d1e09d45e8a3'}}

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class CausticWordHashProof:
    host: TypedFunction
    ingress: TypedExpression
    word_xors: tuple[TypedExpression, TypedExpression, TypedExpression]
    parents: tuple[TypedExpression, ...]
    statement_parent_chains: tuple[tuple[TypedStatement, ...], ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = [self.host, self.ingress, *self.word_xors,
                                *self.parents]
        for chain in self.statement_parent_chains:
            values.extend(chain)
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


__all__ = ("PROFILE", "CAUSTIC_KEY", "CausticWordHashProof",
           "authenticate_caustic_word_hash", "apply_caustic_word_hash")


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
    value = ast.literal_eval(_FROZEN_PROFILE_TUPLE_REPR)
    if not isinstance(value, tuple):
        raise _fail("internal frozen profile tuple is not a tuple")
    return value


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, epath in _walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, epath, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def _is_closure_node(item: TypedExpression) -> bool:
    if item.kind == "builtin" and item.callee == "floatBitsToUint":
        return True
    return (item.kind == "binary" and item.operator == "^"
            and item.type is not None and item.type.display() == "uint")


def authenticate_caustic_word_hash(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> CausticWordHashProof:
    """Authenticate Caustic and return only candidate-owned exact objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    default_frozen = _profile_tuple()
    if _sha(default_frozen) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    dynamic = defines == _DYNAMIC_DEFINES
    if dynamic:
        frozen = ast.literal_eval(_DYNAMIC_FROZEN_PROFILE_TUPLE_REPR)
        if not isinstance(frozen, tuple) or _sha(frozen) != _DYNAMIC_PROFILE_SHA256:
            raise _fail("internal frozen runtime profile tuple mismatch")
        normalized_bytes = _DYNAMIC_NORMALIZED_BYTES
        normalized_sha256 = _DYNAMIC_NORMALIZED_SHA256
        functions_sha256, whole_sha256, interface_sha256 = frozen[5:8]
        host_id = frozen[8]
        nodes = frozen[10]
        host_span = _DYNAMIC_HOST_SPAN
        function_count = _DYNAMIC_FUNCTION_COUNT
        ingress_ancestor_span = _DYNAMIC_INGRESS_ANCESTOR_SPAN
        xor_ancestor_span = _DYNAMIC_XOR_ANCESTOR_SPAN
        expected_uniforms = ("NOISE_TYPE", "time", "seed", "wrap", "resolution",
                             "tileOffset", "fullResolution", "noiseScale", "speed",
                             "hueRotation", "hueRange", "intensity")
    else:
        frozen = default_frozen
        normalized_bytes = _NORMALIZED_BYTES
        normalized_sha256 = _NORMALIZED_SHA256
        functions_sha256, whole_sha256, interface_sha256 = (
            _FUNCTIONS_SHA256, _WHOLE_SHA256, _INTERFACE_SHA256)
        host_id = _HOST_ID
        nodes = _NODES
        host_span = _HOST_SPAN
        function_count = 22
        ingress_ancestor_span = _INGRESS_ANCESTOR_SPAN
        xor_ancestor_span = _XOR_ANCESTOR_SPAN
        expected_uniforms = ("time", "seed", "wrap", "resolution", "tileOffset",
                             "fullResolution", "noiseScale", "speed", "hueRotation",
                             "hueRange", "intensity")
    raw_sha256, raw_bytes = _RAW_SHA256, _RAW_BYTES
    current = _CURRENT_VARIANTS["int" if dynamic else 10]
    if source_hash == current["raw_sha256"]:
        frozen = current["frozen"]
        if _sha(frozen) != current["profile_sha256"]:
            raise _fail("current frozen profile tuple mismatch")
        raw_sha256, raw_bytes = current["raw_sha256"], current["raw_bytes"]
        normalized_bytes = current["normalized_bytes"]
        normalized_sha256 = current["normalized_sha256"]
        functions_sha256, whole_sha256, interface_sha256 = frozen[5:8]
        host_id, nodes = frozen[8], frozen[10]
    if program.key != CAUSTIC_KEY or source_hash != raw_sha256:
        raise _fail("selected key and exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != raw_bytes or hashlib.sha256(raw).hexdigest() != raw_sha256
            or len(normalized) != normalized_bytes
            or hashlib.sha256(normalized).hexdigest() != normalized_sha256
            or defines != frozen[3]
            or program.body_status != "analyzed"
            or _sha(program.functions) != functions_sha256
            or _whole(program) != whole_sha256
            or _interface(program) != interface_sha256):
        raise _fail("source, define, function, whole-program, or interface mismatch")

    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    proof = program.counted_loop_proof
    if (proof is None or
            (proof.loop_count, proof.unproved_loop_count,
             proof.max_effective_depth, proof.max_lexical_product,
             proof.entrypoint_charge, proof.call_graph_acyclic) != frozen[9]):
        raise _fail("loop or call graph profile mismatch")

    if ((program.resources.uniforms, program.resources.samplers,
         program.resources.outputs, program.resources.uses_texture,
         program.resources.uses_derivatives)
            != (expected_uniforms,
                (), ("fragColor",), False, False)):
        raise _fail("resource or binding signature mismatch")

    if len(program.functions) != function_count:
        raise _fail("function cardinality mismatch")
    host = next((item for item in program.functions if item.id == host_id), None)
    if (host is None
            or (host.name, host.return_type.display(), len(host.parameters),
                len(host.body), _span(host))
            != (_HOST_NAME, "vec3", 5, 19, host_span)):
        raise _fail("host function identity mismatch")

    # Census the WHOLE program, so an additional ingress or scalar word XOR
    # anywhere else is a hard failure rather than an unnoticed extra.
    located: list[tuple[str, tuple[object, ...], TypedExpression,
                        TypedExpression | None, tuple[TypedStatement, ...]]] = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement, (index,)):
                if _is_closure_node(item):
                    if function.id != host_id:
                        raise _fail("closure site outside the host function")
                    kind = ("floatBitsToUint" if item.kind == "builtin"
                            else "^")
                    located.append((kind, path, item, parent, chain))

    if len(located) != len(nodes):
        raise _fail(f"closure site cardinality mismatch: {len(located)}")

    actual = tuple(
        (kind, path, _span(item),
         "" if item.type is None else item.type.display(), _sha(item),
         "" if parent is None else parent.kind,
         tuple("" if child.type is None else child.type.display()
               for child in item.children),
         tuple(_sha(child) for child in item.children))
        for kind, path, item, parent, _ in located)
    if actual != nodes:
        raise _fail("closure node identity mismatch")

    ingress = tuple(item for kind, _, item, _, _ in located
                    if kind == "floatBitsToUint")
    word_xors = tuple(item for kind, _, item, _, _ in located if kind == "^")
    if len(ingress) != 1 or len(word_xors) != 3:
        raise _fail("ingress or word XOR cardinality mismatch")

    if len(ingress[0].children) != 1:
        raise _fail("ingress arity mismatch")
    for node in word_xors:
        if len(node.children) != 2:
            raise _fail("word XOR arity mismatch")
        if any(child.type is None or child.type.display() != "uint"
               for child in node.children):
            raise _fail("word XOR operand is not an exact scalar uint")

    parents = tuple(parent for _, _, _, parent, _ in located)
    if any(parent is None for parent in parents):
        raise _fail("closure parent mismatch")

    chains = tuple(chain for _, _, _, _, chain in located)
    if tuple(tuple(item.kind for item in chain)
             for chain in chains) != (_ANCESTOR_KINDS,) * 4:
        raise _fail("closure ancestry kind mismatch")
    spans = tuple(tuple(_span(item) for item in chain) for chain in chains)
    if (spans[0] != ingress_ancestor_span
            or any(span != xor_ancestor_span for span in spans[1:])):
        raise _fail("closure ancestry span mismatch")

    result = CausticWordHashProof(host, ingress[0], word_xors, parents,
                                  (chains[0], chains[1]))
    # host, ingress, three word XORs, two unique parents (the ingress
    # declaration and the single uvec3 `construct` shared by all three XORs),
    # and two unique statements (one `decl` per closure).
    if len(result.consumed_objects) != 9:
        raise _fail(
            f"consumed object cardinality mismatch: {len(result.consumed_objects)}")
    return result


def apply_caustic_word_hash(program: TypedProgram, source_hash: str | None,
                            profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_caustic_word_hash(program, source_hash, profile)
    return program
