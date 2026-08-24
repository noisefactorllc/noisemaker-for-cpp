"""Authenticated runtime-bounded counted-loop contracts.

The carrier is deliberately not a general dynamic-loop permission: exact
source, interface, data-flow and loop identity plus the runtime guard are one
immutable record.  Plain semantic analysis remains profile-free.

``synth/noise:noise`` (counted-for wave 2) is the module's fourth key and the
first *parameter-bounded* record beside tetra with a relaxed loop census:
its ``multires`` helper owns ``for (int i = 1; i <= oct; i++)`` where ``oct``
is the helper's third parameter, passed the ``octaves`` uniform directly at
``main``'s single call site (normalized ``306:17``).  The JS authority
(``canonicalFactory265``, ``canonical-kernels.js:31929``/``36445``;
``Function.prototype.toString`` SHA-256
``392c3be9936855debc0956bc41e4b658896ccdd673674a2ad983101aac521e14``) binds
``var octaves = $bindings["octaves"];`` and calls
``multires(centered, freq, octaves, (seed), blend)`` with the loop
``for (var i = 1; i <= oct; i++) {`` -- ``specs.js`` metadata is
``octaves: i(2, 1, 8)``, so the seed maximum is 8 and the proof attaches
trips 8 / product 8 / charge 8 (whole-program summary ``(1, 0, 1, 8, 8,
True)``).  Where tetra requires *exactly one loop in the program*, this record
requires *exactly one unproved loop*, named by span and node hash -- the
generalization ``classicNoisedeck/noise`` needs, whose two literal 3-trip
sRGB loops sit proved alongside its unproved ``multires`` loop.

The record is live in the typed slice.  The generator validates the exact
``octaves`` metadata before attaching this proof, and the row carries the
runtime profile alongside Noise's mutable-frame and scalar-XOR companions.
Everything behind ``authenticate_runtime_loop_bound`` is mutation-closed.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib

from .typed_ir import Symbol, TypedExpression, TypedProgram, TypedStatement


PROFILE = "runtime-loop-bound-v1"
TETRA_KEY = "filter/tetraColorArray:tetraColorArray"
BLUR_H_KEY = "filter/blur:blurH"
BLUR_V_KEY = "filter/blur:blurV"
BLUR_KEYS = frozenset({BLUR_H_KEY, BLUR_V_KEY})
STATS_KEY = "filter/normalize:statsFinal"
NOISE_KEY = "synth/noise:noise"
# Noise lands atomically with its frame and scalar-XOR companions.
PREPARED_RUNTIME_LOOP_BOUND_KEYS: tuple[str, ...] = ()
RUNTIME_LOOP_BOUND_KEYS = frozenset(
    {TETRA_KEY, STATS_KEY, NOISE_KEY, *BLUR_KEYS})


@dataclass(frozen=True, slots=True)
class RuntimeScalarBoundSeed:
    symbol_id: int
    maximum: int
    provenance: str
    symbol: Symbol

    def __post_init__(self) -> None:
        if self.symbol_id != self.symbol.id:
            raise ValueError(f"{PROFILE}: runtime seed symbol identity mismatch")
        if type(self.maximum) is not int or self.maximum < 0:
            raise ValueError(f"{PROFILE}: runtime seed maximum must be a nonnegative int")


@dataclass(frozen=True, slots=True)
class RuntimeLaneBoundSeed:
    symbol_id: int
    lane: int
    maximum: int
    provenance: str
    symbol: Symbol
    expression: TypedExpression

    def __post_init__(self) -> None:
        child = self.expression.children[0] if len(self.expression.children) == 1 else None
        if (self.symbol_id != self.symbol.id or self.lane not in {0, 1}
                or type(self.maximum) is not int or self.maximum < 0
                or self.expression.kind != "swizzle"
                or self.expression.member != ("x" if self.lane == 0 else "y")
                or child is None or child.kind != "id"
                or child.symbol_id != self.symbol_id or child.symbol != self.symbol):
            raise ValueError(f"{PROFILE}: malformed lane-qualified runtime seed")


@dataclass(frozen=True, slots=True)
class RuntimeLoopBoundContract:
    key: str
    seed: RuntimeScalarBoundSeed | None
    kind: str
    uniform_name: str
    minimum: int | float
    uniform_maximum: int | float
    default: int | float
    binding_error: str
    render_scale_name: str | None = None
    radius_declaration: TypedExpression | None = None
    lane_seeds: tuple[RuntimeLaneBoundSeed, ...] = ()
    input_surface_name: str | None = None
    exact_output_extent: tuple[int, int] | None = None

    @property
    def maximum(self) -> int:
        """One source of truth for both proof reconstruction and the guard."""
        if self.seed is None:
            raise ValueError(f"{PROFILE}: scalar maximum requested for lane contract")
        return self.seed.maximum


_TETRA_EXPECTED = {
    "raw_bytes": 9754,
    "raw_sha256": "68c7cabce311a0a05ba116ce8d34bd5e70e0c09bfb8eab06c93f4f9e01fa5438",
    "normalized_bytes": 7834,
    "normalized_sha256": "588484a8290e24b5f8f7db53a3f76c6f3a839ba1ea274ae7680078534878ba56",
    "defines": (),
    "functions_sha256": "3bd3cdae71998ff69cb87162b99f365290b0acc5989a9001db26d9823e6d096f",
    "whole_program_sha256": "38d2e4d5ae4d41bc1c1d0ec6d419a8fd289c4341d80af0b7fbccb6f3fdbd3b24",
    "interface_sha256": "091124f62bbe39554a2d3937fe35caed7e7a0f931f8ae3e16940c2c87ef3c83e",
    "uniform": (5, "colorCount", "int", "uniform", False, "12:1-12:24"),
    "helper": (70, "sampleColorArray", "236:1-292:2"),
    "parameter": (53, "count", "int", "parameter", True, "in", "236:32-236:41"),
    "call": ("main", "318:26-318:69",
             "ccf225e8f56ca287bca73f8b3b23f989ed03191b4c7f8596ae706fe3e4064131"),
    "call_argument": (5, "colorCount", "318:46-318:56",
                      "6e548e3a55f33fef48c3c33befd71cd231db56d8f05b4ff3cad1b8450a466840"),
    "loop": ("243:5-261:6",
             "48235e4e6793c4c713bb610c58cd1f7193555c995ad25fe7d593a1f65539a013"),
    "metadata": ("int", 2, 6, 8),
}


_BLUR_EXPECTED = {
    BLUR_H_KEY: {
        "raw_bytes": 1120,
        "raw_sha256": "c4283e820b2ade9148358ad4582d350bc7f4a5ccb5fc60f2e1b76bcda58deecc",
        "normalized_bytes": 986,
        "normalized_sha256": "60437dc833b2fe4d2472d4b9f313aba5a21fe9b53f716b49bafbbaeff0c6623b",
        "functions_sha256": "d56132f3d904a1710fc2caf461c577bf13d8ad5746f554d61df449404174476f",
        "whole_program_sha256": "780ca74cceb5ea1de06f60bf83f6850c46df99bb5ce7718abe88629126224836",
        "interface_sha256": "e87d38e8af590a1a73bf9680ba831edcb0bd6d3f4ebd3cbb53f3aef928126b62",
        "axis": (4, "radiusX", "float", "uniform", False, "7:1-7:23"),
        "scale": (5, "renderScale", "float", "uniform", False, "8:1-8:27"),
        "radius": (14, "radius", "int", "local", True, "20:9-20:44"),
        "radius_declaration": ("20:9-20:44", "6b6bdbee4b2e3e8258fd99b1e065aa5f45b6a24a457802f2eae020419e8b4909"),
        "radius_statement": ("20:5-20:45", "708c95b0fb8453ddeed788bb2d7c3dd03eef249daabf7bd2be05978f2b5e60c9"),
        "product": ("20:22-20:43", "9d8419da0cad56b13265e0ebe3f1f87fcd9bd05b68fda904b8684c43bbcbc0f9"),
        "guard": ("21:5-24:6", "2b4dab557d0d189e7422a9571020f8b016fc9b120027e603e018d09e7a825813"),
        "loop": ("33:5-39:6", "ea4cb59ad41ff87649486ced8704dba9a1cb3714896703e0cae429495bd65390"),
    },
    BLUR_V_KEY: {
        "raw_bytes": 1118,
        "raw_sha256": "cc33343032b34e1ede6eed15fbdcb9229ad64484a092b2914065b09fa957fb9b",
        "normalized_bytes": 986,
        "normalized_sha256": "ca8e7dd63026f718a64c9a13971a3ff7d01a55bf5da2bfc51028d49361c6d75d",
        "functions_sha256": "1fd9fedea65bc8b6563fc65687d811888475e022b7419de1e96fc568fe06f58d",
        "whole_program_sha256": "7afff298c6d1c82c60958c92e2e82393a53cb35dbbb080202fc1eb91eedbd305",
        "interface_sha256": "0883101a87988ec54275d0788fe1d3eced98aaa63994c5866dd8cf0c413df0f8",
        "axis": (4, "radiusY", "float", "uniform", False, "7:1-7:23"),
        "scale": (5, "renderScale", "float", "uniform", False, "8:1-8:27"),
        "radius": (14, "radius", "int", "local", True, "20:9-20:44"),
        "radius_declaration": ("20:9-20:44", "8e243fe9b8ef0701690b3f3400cb7b2235512eab754f9aa7a22703399071b86a"),
        "radius_statement": ("20:5-20:45", "8577853356e10144ee776439a13f6e1672283c73b0fc7d6c7a8fecf935fa545d"),
        "product": ("20:22-20:43", "a2b4733a0443c8364dbbff5c20f6ddedf0411ca59df17e09b851cc14acb03ff5"),
        "guard": ("21:5-24:6", "c221a6515e7def02f09d88a1b480bfedb5bd1833f6643a803319575b3c4e7725"),
        "loop": ("33:5-39:6", "b9b03ef4b9ece759d4fcf855a8660d831fc6dde41a310960b03f25718cd3299e"),
    },
}


# Every figure measured against the pinned corpus this session (the
# counted-for design's §2.4 row re-derived; divergences frozen house-style:
# the whole-program digest below is this module's own cleared-function,
# proof-free tuple formula, and `helper`/`parameter` carry `multires`'s
# five-parameter signature with `oct` third).
_NOISE_EXPECTED = {
    "raw_bytes": 18131,
    "raw_sha256": "410a98f0d4ec80acde225cb5366a3bbaf752e5743f99bcd651a2c3cbb6cc3274",
    "normalized_bytes": 8516,
    "normalized_sha256": "5a9c937c83b48e85335f1d69b7a364124a3bcd3e1ece1df85b0d6f7dee929205",
    "defines": (("LOOP_OFFSET", "int", "300"), ("NOISE_TYPE", "int", "10")),
    "functions_sha256":
        "25ff043f2e20a1abc4f66994234c4759d0e1dd2642c8d7b0cc49e1b600adc74c",
    "whole_program_sha256":
        "e14b606b7e383d30b6289bdeef8be808ccee7765c7c641e91ee2280803116eaa",
    "interface_sha256":
        "8327df301a143416b03bdb757d3d287700b89bbf543e16294ec8d94f667bb69f",
    "uniform": (8, "octaves", "int", "uniform", False, "22:1-22:21"),
    "helper": (121, "multires", "246:1-276:2"),
    "parameter": (101, "oct", "int", "parameter", True, "in", "246:35-246:42"),
    "call": ("main", "306:17-306:70",
             "6f2e5f81451b1e5a3ea77783f3a449ad153dc1673bc8d9b69dd2ebed4f83889f"),
    "call_argument": (8, "octaves", "306:42-306:49",
                      "1667eac6e0061019c7c0fd812b59afe1fc535a5627353b65dbb2c27d8b2490e8"),
    "loop": ("250:5-258:6",
             "a55de3a189363eb772bead73b605824a6369aba382aefc0fad6149716ec704f5"),
    "metadata": ("int", 1, 2, 8),
}


_STATS_EXPECTED = {
    "raw_bytes": 959,
    "raw_sha256": "0b8daf6d5a38dc34bbd98800fdd46f9cdfa0b97f00196382023456a0b6eb1dfa",
    "normalized_bytes": 564,
    "normalized_sha256": "d714952d967751c0c510121f5ffad69f4d2767819f4aebf90205f08c6d9ce5bf",
    "defines": (),
    "functions_sha256": "790003dc2f9a2e071ff97197247b36ada1b05c83bfb6502c5070183044ab3d07",
    "whole_program_sha256": "8f9c2b68fdebe857929e8d8cd285f2beb6ac9b8aef6099bb287f3762f7b4caf6",
    "interface_sha256": "6038b57eec2a33e84bb68b610cc1845c4a9ef1d63eaa6c3cb59411dbafc9ad3a",
    "sampler": (1, "inputTex", "sampler2D", "uniform", False, "8:1-8:28"),
    "size_symbol": (5, "inSize", "ivec2", "local", True, "12:11-12:44"),
    "size_declaration": ("12:11-12:44",
                         "16aa5e2ff5e35a6b5858594f2bc45d97a50ef6b51e9854ed4c2c5283ea2ef377"),
    "texture_size": ("12:20-12:44",
                     "05e5cea73772f1c6dcd1cf45ebce168a870e64258c6356af353f1aefaaf6e49f"),
    "outer_loop": ("18:5-26:6",
                   "27105f8ca3d7af7c1da4bf54418a745f931e29a88fad318eaaa1602d9e6c3543"),
    "outer_bound": ("y", "18:25-18:33",
                    "a4b5b1a5358bffd74a8bc2665b78123ba544747035790b9da978e797310f08fc"),
    "inner_loop": ("19:9-25:10",
                   "e98259def49b985c422828042506c5de7a7aea947bd09ad0f647c51611444aec"),
    "inner_bound": ("x", "19:29-19:37",
                    "08b0ec0ca2d8349f29f28269917a2b9a9c92a51ba6954fb817075af5f48d70c8"),
    "fetch": ("20:26-20:62",
              "c909b5bfa5b83cf08c9fa81dbee4b7c31b188674901da8bae5e342f6fe0071ce"),
}


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _clear_statement(value: TypedStatement) -> TypedStatement:
    return replace(value, loop_proof=None,
                   children=tuple(_clear_statement(child) for child in value.children))


def _cleared_functions(program: TypedProgram):
    return tuple(replace(function, body=tuple(_clear_statement(statement)
                                                for statement in function.body))
                 for function in program.functions)


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    yield value
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def validate_runtime_loop_contract(
        contract: RuntimeLoopBoundContract) -> RuntimeLoopBoundContract:
    """Recheck a returned record before either proof or guard consumption."""
    tetra = (contract.seed is not None
             and contract.key == TETRA_KEY and contract.kind == "integer-range"
             and contract.uniform_name == "colorCount"
             and contract.minimum == 2 and contract.uniform_maximum == 8
             and contract.default == 6
             and contract.maximum == 8
             and contract.render_scale_name is None
             and contract.radius_declaration is None
             and contract.seed.provenance
             == "runtime-metadata-uniform-direct-parameter")
    blur = (contract.seed is not None
            and contract.key in BLUR_KEYS and contract.kind == "blur-radius"
            and contract.uniform_name == _BLUR_EXPECTED[contract.key]["axis"][1]
            and contract.minimum == 0 and contract.uniform_maximum == 50
            and contract.default == 5
            and contract.maximum == 63
            and contract.render_scale_name == "renderScale"
            and contract.radius_declaration is not None
            and contract.radius_declaration.symbol == contract.seed.symbol
            and contract.seed.provenance
            == "runtime-binary64-product-checked-radius")
    stats = (contract.seed is None and contract.key == STATS_KEY
             and contract.kind == "texture-size-lanes"
             and contract.uniform_name == "inputTex"
             and contract.minimum == 1 and contract.uniform_maximum == 64
             and contract.default == 1
             and contract.render_scale_name is None
             and contract.radius_declaration is None
             and contract.input_surface_name == "inputTex"
             and contract.exact_output_extent == (1, 1)
             and len(contract.lane_seeds) == 2
             and tuple((item.lane, item.maximum, item.provenance)
                       for item in contract.lane_seeds)
             == ((1, 64, "runtime-texture-size-checked-lane"),
                 (0, 64, "runtime-texture-size-checked-lane")))
    noise = (contract.seed is not None
             and contract.key == NOISE_KEY and contract.kind == "integer-range"
             and contract.uniform_name == "octaves"
             and contract.minimum == 1 and contract.uniform_maximum == 8
             and contract.default == 2
             and contract.maximum == 8
             and contract.render_scale_name is None
             and contract.radius_declaration is None
             and contract.lane_seeds == ()
             and contract.seed.provenance
             == "runtime-metadata-uniform-direct-parameter")
    malformed_scalar = (contract.seed is not None
                        and (contract.seed.symbol_id != contract.seed.symbol.id
                             or type(contract.seed.maximum) is not int
                             or contract.seed.maximum < 0))
    if not (tetra or blur or stats or noise) or malformed_scalar:
        raise _fail("malformed authenticated runtime contract")
    return contract


def validate_tetra_metadata(effect: object) -> None:
    """Validate the authoritative generator metadata against the frozen guard."""
    try:
        record = effect["params"]["colorCount"]  # type: ignore[index]
        actual = (record["type"], record["min"], record["default"], record["max"])
    except (KeyError, TypeError):
        raise _fail("metadata contract mismatch") from None
    if actual != _TETRA_EXPECTED["metadata"]:
        raise _fail("metadata contract mismatch")


def validate_blur_metadata(effect: object) -> None:
    """Validate both authoritative blur axis records against the frozen guard."""
    try:
        rows = effect["params"]  # type: ignore[index]
        actual = tuple((rows[name]["type"], rows[name]["min"],
                        rows[name]["default"], rows[name]["max"],
                        rows[name]["uniform"], rows[name]["zero"])
                       for name in ("radiusX", "radiusY"))
    except (KeyError, TypeError):
        raise _fail("metadata contract mismatch") from None
    expected = (("float", 0, 5, 50, "radiusX", 0),
                ("float", 0, 5, 50, "radiusY", 0))
    if actual != expected:
        raise _fail("metadata contract mismatch")


def validate_noise_metadata(effect: object) -> None:
    """Validate synth/noise's authoritative ``octaves`` metadata record.

    Both authorities agree: the corpus ``metadata.json`` and the shipped
    ``specs.js`` read ``octaves: i(2, 1, 8)`` -- int, minimum 1, default 2,
    maximum 8.  The seed's maximum (8) is this record's, by construction.
    """
    try:
        record = effect["params"]["octaves"]  # type: ignore[index]
        actual = (record["type"], record["min"], record["default"],
                  record["max"])
    except (KeyError, TypeError):
        raise _fail("metadata contract mismatch") from None
    if actual != _NOISE_EXPECTED["metadata"]:
        raise _fail("metadata contract mismatch")


def authenticate_runtime_loop_bound(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> RuntimeLoopBoundContract | None:
    """Return Tetra's immutable proof/guard contract after exact authentication."""
    from .noise_runtime_define_profile import is_dynamic_program, authenticate_runtime_loop
    if is_dynamic_program(program):
        return authenticate_runtime_loop(program, source_hash, profile)
    if program.key not in RUNTIME_LOOP_BOUND_KEYS:
        if program.key not in PREPARED_RUNTIME_LOOP_BOUND_KEYS:
            if profile is not None:
                raise _fail("profile on foreign key")
            return None
        if profile != PROFILE:
            raise _fail("exact profile carrier required")
        return _authenticate_noise(program, source_hash)
    if profile != PROFILE:
        raise _fail("exact profile carrier required")

    if program.key in BLUR_KEYS:
        return _authenticate_blur(program, source_hash)
    if program.key == STATS_KEY:
        return _authenticate_stats(program, source_hash)
    if program.key == NOISE_KEY:
        return _authenticate_noise(program, source_hash)

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if (source_hash != _TETRA_EXPECTED["raw_sha256"]
            or len(raw) != _TETRA_EXPECTED["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != _TETRA_EXPECTED["raw_sha256"]
            or len(normalized) != _TETRA_EXPECTED["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != _TETRA_EXPECTED["normalized_sha256"]
            or defines != _TETRA_EXPECTED["defines"]
            or program.body_status != "analyzed"):
        raise _fail("source or define profile mismatch")

    functions = _cleared_functions(program)
    whole = (program.key, program.source, program.raw_source,
             program.declarations, functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.preprocessor_defines)
    interface = (program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines)
    if (_sha(functions) != _TETRA_EXPECTED["functions_sha256"]
            or _sha(whole) != _TETRA_EXPECTED["whole_program_sha256"]
            or _sha(interface) != _TETRA_EXPECTED["interface_sha256"]):
        raise _fail("interface, function, or call-graph profile mismatch")

    uniform = next((item.symbol for item in program.declarations
                    if item.symbol.id == _TETRA_EXPECTED["uniform"][0]), None)
    if (uniform is None
            or (uniform.id, uniform.name, uniform.type.display(), uniform.storage,
                uniform.writable, _span(uniform)) != _TETRA_EXPECTED["uniform"]):
        raise _fail("uniform profile mismatch")

    helper = next((item for item in functions
                   if item.signature.id == _TETRA_EXPECTED["helper"][0]), None)
    if (helper is None
            or (helper.signature.id, helper.name, _span(helper)) != _TETRA_EXPECTED["helper"]
            or len(helper.parameters) != 3):
        raise _fail("helper profile mismatch")
    parameter = helper.parameters[1]
    if ((parameter.id, parameter.name, parameter.type.display(), parameter.storage,
         parameter.writable, parameter.direction, _span(parameter))
            != _TETRA_EXPECTED["parameter"]):
        raise _fail("helper parameter profile mismatch")

    calls: list[tuple[str, TypedExpression]] = []
    loops: list[TypedStatement] = []
    parameter_assignments = 0
    for function in functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if isinstance(value, TypedStatement) and value.kind in {"for", "while", "dowhile"}:
                    loops.append(value)
                if isinstance(value, TypedExpression):
                    if value.kind == "call" and value.signature_id == helper.signature.id:
                        calls.append((function.name, value))
                    if (value.kind == "assign" and value.children
                            and value.children[0].symbol_id == parameter.id):
                        parameter_assignments += 1
    if len(calls) != 1:
        raise _fail("call-site profile mismatch")
    owner, call = calls[0]
    expected_owner, expected_span, expected_sha = _TETRA_EXPECTED["call"]
    if (owner != expected_owner or _span(call) != expected_span
            or _sha(call) != expected_sha or len(call.children) != 3):
        raise _fail("call-site profile mismatch")
    argument = call.children[1]
    if ((argument.symbol_id, argument.symbol.name if argument.symbol else None,
         _span(argument), _sha(argument)) != _TETRA_EXPECTED["call_argument"]
            or argument.kind != "id" or argument.symbol != uniform):
        raise _fail("call-site profile mismatch")
    if parameter_assignments:
        raise _fail("helper parameter reassignment")
    if len(loops) != 1:
        raise _fail("loop-site profile mismatch")
    loop = loops[0]
    if (_span(loop), _sha(loop)) != _TETRA_EXPECTED["loop"]:
        raise _fail("loop-site profile mismatch")

    seed = RuntimeScalarBoundSeed(parameter.id, 8,
                                  "runtime-metadata-uniform-direct-parameter",
                                  parameter)
    return validate_runtime_loop_contract(RuntimeLoopBoundContract(
        TETRA_KEY, seed, "integer-range", "colorCount", 2, 8, 6,
        f"{TETRA_KEY} colorCount must be in [2,8]"))


def _authenticate_noise(program: TypedProgram,
                        source_hash: str | None) -> RuntimeLoopBoundContract:
    """Authenticate synth/noise's parameter-bounded ``octaves`` contract.

    Same shape as tetra's record with one deliberate generalization: the loop
    census does not require the program to hold exactly one loop -- it
    requires exactly one **unproved** loop, named by span and node hash and
    owned by the seeded helper.  Proved companions (classicNoisedeck/noise's
    two literal 3-trip sRGB loops) are therefore not a blocker for the family.
    """
    expected = _NOISE_EXPECTED
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    functions = _cleared_functions(program)
    whole = (program.key, program.source, program.raw_source,
             program.declarations, functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.preprocessor_defines)
    interface = (program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines)
    if (source_hash != expected["raw_sha256"]
            or len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest()
            != expected["normalized_sha256"]
            or defines != expected["defines"]
            or program.body_status != "analyzed"):
        raise _fail("source or define profile mismatch")
    if (_sha(functions) != expected["functions_sha256"]
            or _sha(whole) != expected["whole_program_sha256"]
            or _sha(interface) != expected["interface_sha256"]):
        raise _fail("interface, function, or call-graph profile mismatch")

    uniform = next((item.symbol for item in program.declarations
                    if item.symbol.id == expected["uniform"][0]), None)
    if (uniform is None
            or (uniform.id, uniform.name, uniform.type.display(), uniform.storage,
                uniform.writable, _span(uniform)) != expected["uniform"]):
        raise _fail("uniform profile mismatch")

    helper = next((item for item in functions
                   if item.signature.id == expected["helper"][0]), None)
    if (helper is None
            or (helper.signature.id, helper.name, _span(helper)) != expected["helper"]
            or len(helper.parameters) != 5):
        raise _fail("helper profile mismatch")
    parameter = helper.parameters[2]
    if ((parameter.id, parameter.name, parameter.type.display(), parameter.storage,
         parameter.writable, parameter.direction, _span(parameter))
            != expected["parameter"]):
        raise _fail("helper parameter profile mismatch")

    calls: list[tuple[str, TypedExpression]] = []
    loops: list[tuple[object, TypedStatement]] = []
    parameter_assignments = 0
    # The census walks the RAW functions, proofs intact: a canonically proved
    # companion (classicNoisedeck/noise's two literal 3-trip sRGB loops) must
    # be recognizable as proved, not counted as a second unproved loop.
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if isinstance(value, TypedStatement) and value.kind in {"for", "while", "dowhile"}:
                    loops.append((function, value))
                if isinstance(value, TypedExpression):
                    if value.kind == "call" and value.signature_id == helper.signature.id:
                        calls.append((function.name, value))
                    if (value.kind == "assign" and value.children
                            and value.children[0].symbol_id == parameter.id):
                        parameter_assignments += 1
    if len(calls) != 1:
        raise _fail("call-site profile mismatch")
    owner, call = calls[0]
    expected_owner, expected_span, expected_sha = expected["call"]
    if (owner != expected_owner or _span(call) != expected_span
            or _sha(call) != expected_sha or len(call.children) != 5):
        raise _fail("call-site profile mismatch")
    argument = call.children[2]
    if ((argument.symbol_id, argument.symbol.name if argument.symbol else None,
         _span(argument), _sha(argument)) != expected["call_argument"]
            or argument.kind != "id" or argument.symbol != uniform):
        raise _fail("call-site profile mismatch")
    if parameter_assignments:
        raise _fail("helper parameter reassignment")
    # The relaxed census: exactly one loop that is unproved or carries THIS
    # record's runtime seed -- the named loop.  Fresh, it must match the
    # frozen span AND node hash; already seeded (re-application, or the
    # emitter authenticating the post-apply tree), its proof must be exactly
    # the contract's eight-trip shape.  Proved companions are admissible.
    named = [(loop_owner, loop) for loop_owner, loop in loops
             if loop.loop_proof is None
             or loop.loop_proof.bound_kind
             == "runtime-metadata-uniform-direct-parameter"]
    if len(named) != 1:
        raise _fail("loop-site profile mismatch")
    loop_owner, loop = named[0]
    if (loop_owner.signature.id != helper.signature.id
            or _span(loop) != expected["loop"][0]):
        raise _fail("loop-site profile mismatch")
    if loop.loop_proof is None:
        if _sha(loop) != expected["loop"][1]:
            raise _fail("loop-site profile mismatch")
    else:
        proof = loop.loop_proof
        if ((proof.start_value, proof.bound_value, proof.comparison,
             proof.update, proof.trip_count, proof.bound_kind)
                != (1, 8, "<=", "++", 8,
                    "runtime-metadata-uniform-direct-parameter")):
            raise _fail("loop-site profile mismatch")

    seed = RuntimeScalarBoundSeed(parameter.id, 8,
                                  "runtime-metadata-uniform-direct-parameter",
                                  parameter)
    return validate_runtime_loop_contract(RuntimeLoopBoundContract(
        NOISE_KEY, seed, "integer-range", "octaves", 1, 8, 2,
        f"{NOISE_KEY} octaves must be in [1,8]"))


def _authenticate_blur(program: TypedProgram,
                       source_hash: str | None) -> RuntimeLoopBoundContract:
    expected = _BLUR_EXPECTED[program.key]
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    functions = _cleared_functions(program)
    whole = (program.key, program.source, program.raw_source,
             program.declarations, functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.preprocessor_defines)
    interface = (program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines)
    if (source_hash != expected["raw_sha256"] or len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != expected["normalized_sha256"]
            or defines != () or program.body_status != "analyzed"):
        raise _fail("source or define profile mismatch")
    if (_sha(functions) != expected["functions_sha256"]
            or _sha(whole) != expected["whole_program_sha256"]
            or _sha(interface) != expected["interface_sha256"]):
        raise _fail("interface, function, or call-graph profile mismatch")

    symbols = {item.symbol.id: item.symbol for item in program.declarations}
    axis = symbols.get(expected["axis"][0])
    scale = symbols.get(expected["scale"][0])
    if axis is None or scale is None:
        raise _fail("uniform profile mismatch")
    for actual, frozen in ((axis, expected["axis"]), (scale, expected["scale"])):
        if ((actual.id, actual.name, actual.type.display(), actual.storage,
             actual.writable, _span(actual)) != frozen):
            raise _fail("uniform profile mismatch")

    main = next((item for item in functions if item.name == "main"), None)
    if main is None or len(functions) != 1:
        raise _fail("interface, function, or call-graph profile mismatch")
    radius_statement = next((item for item in main.body
                             if item.kind == "decl" and item.expressions
                             and item.expressions[0].symbol is not None
                             and item.expressions[0].symbol.name == "radius"), None)
    guard = next((item for item in main.body if item.kind == "if"), None)
    loop = next((item for item in main.body if item.kind == "for"), None)
    if radius_statement is None or guard is None or loop is None:
        raise _fail("declaration, guard, or loop-site profile mismatch")
    radius = radius_statement.expressions[0]
    if ((radius.symbol.id, radius.symbol.name, radius.symbol.type.display(),
         radius.symbol.storage, radius.symbol.writable, _span(radius.symbol))
            != expected["radius"]
            or (_span(radius), _sha(radius)) != expected["radius_declaration"]
            or (_span(radius_statement), _sha(radius_statement))
            != expected["radius_statement"]
            or len(radius.children) != 1 or radius.children[0].kind != "construct"
            or len(radius.children[0].children) != 1):
        raise _fail("declaration profile mismatch")
    product = radius.children[0].children[0]
    if ((product.kind != "binary" or product.operator != "*"
            or (_span(product), _sha(product)) != expected["product"]
            or len(product.children) != 2
            or product.children[0].symbol != axis
            or product.children[1].symbol != scale)):
        raise _fail("declaration profile mismatch")
    if ((_span(guard), _sha(guard)) != expected["guard"]
            or (_span(loop), _sha(loop)) != expected["loop"]):
        raise _fail("guard or loop-site profile mismatch")

    seed = RuntimeScalarBoundSeed(
        radius.symbol.id, 63, "runtime-binary64-product-checked-radius",
        radius.symbol)
    return validate_runtime_loop_contract(RuntimeLoopBoundContract(
        program.key, seed, "blur-radius", axis.name, 0, 50, 5,
        f"{program.key} runtime loop radius must be finite and in [0,63]",
        scale.name, radius))


def _authenticate_stats(program: TypedProgram,
                        source_hash: str | None) -> RuntimeLoopBoundContract:
    expected = _STATS_EXPECTED
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    functions = _cleared_functions(program)
    whole = (program.key, program.source, program.raw_source,
             program.declarations, functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.preprocessor_defines)
    interface = (program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines)
    if (source_hash != expected["raw_sha256"] or len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != expected["normalized_sha256"]
            or defines != expected["defines"] or program.body_status != "analyzed"):
        raise _fail("source or define profile mismatch")
    if (_sha(functions) != expected["functions_sha256"]
            or _sha(whole) != expected["whole_program_sha256"]
            or _sha(interface) != expected["interface_sha256"]):
        raise _fail("interface, function, or call-graph profile mismatch")

    sampler = next((item.symbol for item in program.declarations
                    if item.symbol.id == expected["sampler"][0]), None)
    if (sampler is None
            or (sampler.id, sampler.name, sampler.type.display(), sampler.storage,
                sampler.writable, _span(sampler)) != expected["sampler"]):
        raise _fail("sampler profile mismatch")
    main = next((item for item in functions if item.name == "main"), None)
    if main is None or len(functions) != 1:
        raise _fail("interface, function, or call-graph profile mismatch")
    declarations = [value.expressions[0] for value in main.body
                    if value.kind == "decl" and len(value.expressions) == 1]
    size = next((value for value in declarations
                 if value.symbol is not None and value.symbol.name == "inSize"), None)
    if (size is None or size.symbol is None
            or (size.symbol.id, size.symbol.name, size.symbol.type.display(),
                size.symbol.storage, size.symbol.writable, _span(size.symbol))
            != expected["size_symbol"]
            or (_span(size), _sha(size)) != expected["size_declaration"]
            or len(size.children) != 1):
        raise _fail("texture-size declaration profile mismatch")
    texture_size = size.children[0]
    if ((_span(texture_size), _sha(texture_size)) != expected["texture_size"]
            or texture_size.kind != "builtin" or texture_size.callee != "textureSize"
            or len(texture_size.children) != 2
            or texture_size.children[0].symbol != sampler
            or texture_size.children[1].kind != "literal"
            or texture_size.children[1].literal_value != 0):
        raise _fail("texture-size resource profile mismatch")

    loops = [value for statement in main.body for value in _walk_statement(statement)
             if isinstance(value, TypedStatement) and value.kind == "for"]
    fetches = [value for statement in main.body for value in _walk_statement(statement)
               if isinstance(value, TypedExpression) and value.kind == "builtin"
               and value.callee == "texelFetch"]
    if len(loops) != 2 or len(fetches) != 1:
        raise _fail("loop or fetch profile mismatch")
    outer, inner = loops
    if ((_span(outer), _sha(outer)) != expected["outer_loop"]
            or (_span(inner), _sha(inner)) != expected["inner_loop"]
            or len(outer.expressions) != 2 or len(inner.expressions) != 2):
        raise _fail("loop-site profile mismatch")
    outer_bound = outer.expressions[0].children[1]
    inner_bound = inner.expressions[0].children[1]
    for bound, frozen in ((outer_bound, expected["outer_bound"]),
                          (inner_bound, expected["inner_bound"])):
        if (bound.member, _span(bound), _sha(bound)) != frozen:
            raise _fail("lane-qualified loop bound profile mismatch")
        if (len(bound.children) != 1 or bound.children[0].symbol != size.symbol):
            raise _fail("lane-qualified loop bound profile mismatch")
    fetch = fetches[0]
    if ((_span(fetch), _sha(fetch)) != expected["fetch"]
            or len(fetch.children) != 3 or fetch.children[0].symbol != sampler
            or fetch.children[1].kind != "construct"
            or tuple(child.symbol.name if child.symbol else None
                     for child in fetch.children[1].children) != ("x", "y")
            or fetch.children[2].kind != "literal"
            or fetch.children[2].literal_value != 0):
        raise _fail("texel-fetch profile mismatch")

    lane_seeds = (
        RuntimeLaneBoundSeed(size.symbol.id, 1, 64,
                             "runtime-texture-size-checked-lane",
                             size.symbol, outer_bound),
        RuntimeLaneBoundSeed(size.symbol.id, 0, 64,
                             "runtime-texture-size-checked-lane",
                             size.symbol, inner_bound),
    )
    return validate_runtime_loop_contract(RuntimeLoopBoundContract(
        STATS_KEY, None, "texture-size-lanes", "inputTex", 1, 64, 1,
        f"{STATS_KEY} inputTex dimensions must be in [1,64]",
        lane_seeds=lane_seeds, input_surface_name="inputTex",
        exact_output_extent=(1, 1)))


def apply_runtime_loop_bound(program: TypedProgram, source_hash: str,
                             profile: str | None) -> TypedProgram:
    """Attach only proof derived from the exact authenticated runtime contract."""
    contract = authenticate_runtime_loop_bound(program, source_hash, profile)
    if contract is None:
        return program
    validate_runtime_loop_contract(contract)
    # Local import avoids making the proof builder/profile relationship cyclic.
    from .loop_proof import attach_counted_loop_proofs, summarize_counted_loop_proofs

    functions = attach_counted_loop_proofs(
        program.functions, program.key,
        runtime_scalar_bounds=(() if contract.seed is None else (contract.seed,)),
        runtime_lane_bounds=contract.lane_seeds)
    return replace(program, functions=functions,
                   counted_loop_proof=summarize_counted_loop_proofs(functions))


__all__ = (
    "PROFILE", "TETRA_KEY", "BLUR_H_KEY", "BLUR_V_KEY", "BLUR_KEYS", "STATS_KEY",
    "NOISE_KEY", "RUNTIME_LOOP_BOUND_KEYS", "PREPARED_RUNTIME_LOOP_BOUND_KEYS",
    "RuntimeScalarBoundSeed", "RuntimeLaneBoundSeed", "RuntimeLoopBoundContract",
    "authenticate_runtime_loop_bound", "apply_runtime_loop_bound",
    "validate_runtime_loop_contract", "validate_tetra_metadata",
    "validate_blur_metadata", "validate_noise_metadata",
)
